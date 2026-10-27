import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RegisterPage } from './RegisterPage'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  document.cookie = 'csrftoken=; Max-Age=0; Path=/'
})

function renderRegister() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/register?next=%2Fprojects%2Fproject-1%2Fcalc']}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<div>登录页已打开</div>} />
          <Route path="/workspace" element={<div>工作台已打开</div>} />
          <Route path="/projects/:projectId/calc" element={<div>注册后计算页</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('RegisterPage', () => {
  it('validates matching passwords before submitting', async () => {
    const fetchMock = vi.fn(async () => new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    renderRegister()
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'new@example.com' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'Strong-pass-2026' } })
    fireEvent.change(screen.getByLabelText('确认密码'), { target: { value: 'different' } })
    fireEvent.click(screen.getByRole('button', { name: '注册' }))

    expect(await screen.findByText('两次输入的密码不一致')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('maps an existing-email error to the email field', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
        if (String(input).endsWith('/auth/csrf')) return new Response('{}', { status: 200 })
        return new Response(
          JSON.stringify({ detail: '注册信息有误', errors: { email: ['该邮箱已注册'] } }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          },
        )
      }),
    )

    renderRegister()
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'existing@example.com' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'Strong-pass-2026' } })
    fireEvent.change(screen.getByLabelText('确认密码'), { target: { value: 'Strong-pass-2026' } })
    fireEvent.click(screen.getByRole('button', { name: '注册' }))

    expect(await screen.findByText('该邮箱已注册')).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.getByLabelText('邮箱')).toHaveAttribute('aria-invalid', 'true'),
    )
  })

  it('registers and follows the safe next route', async () => {
    document.cookie = 'csrftoken=register-token; Path=/'
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      if (String(input).endsWith('/auth/csrf')) return new Response('{}', { status: 200 })
      return new Response(
        JSON.stringify({ user_id: 7, email: 'new@example.com', display_name: 'new@example.com' }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      )
    })
    vi.stubGlobal('fetch', fetchMock)

    renderRegister()
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'new@example.com' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'Strong-pass-2026' } })
    fireEvent.change(screen.getByLabelText('确认密码'), { target: { value: 'Strong-pass-2026' } })
    fireEvent.click(screen.getByRole('button', { name: '注册' }))

    expect(await screen.findByText('注册后计算页')).toBeInTheDocument()
    const registerCall = fetchMock.mock.calls.find(([input]) =>
      String(input).endsWith('/auth/register'),
    ) as [RequestInfo | URL, RequestInit] | undefined
    expect(new Headers(registerCall?.[1]?.headers).get('X-CSRFToken')).toBe('register-token')
    expect(JSON.parse(String(registerCall?.[1]?.body))).toEqual({
      email: 'new@example.com',
      password: 'Strong-pass-2026',
      password_confirm: 'Strong-pass-2026',
    })
  })
})
