import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LoginPage } from './LoginPage'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
  document.cookie = 'csrftoken=; Max-Age=0; Path=/'
})

function renderLogin(next = '/workspace') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/login?next=${encodeURIComponent(next)}`]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<div>注册页已打开</div>} />
          <Route path="/workspace" element={<div>工作台已打开</div>} />
          <Route path="/projects/:projectId/calc" element={<div>项目计算页已打开</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LoginPage', () => {
  it('prefills configured development credentials', () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('VITE_DEV_LOGIN_EMAIL', 'demo@example.test')
    vi.stubEnv('VITE_DEV_LOGIN_PASSWORD', 'local-password')
    renderLogin()

    expect(screen.getByLabelText('邮箱')).toHaveValue('demo@example.test')
    expect(screen.getByLabelText('密码')).toHaveValue('local-password')
  })

  it('keeps the form empty outside development even when credentials are configured', () => {
    vi.stubEnv('DEV', false)
    vi.stubEnv('VITE_DEV_LOGIN_EMAIL', 'demo@example.test')
    vi.stubEnv('VITE_DEV_LOGIN_PASSWORD', 'local-password')
    renderLogin()

    expect(screen.getByLabelText('邮箱')).toHaveValue('')
    expect(screen.getByLabelText('密码')).toHaveValue('')
  })

  it('logs in with CSRF and follows a safe next route', async () => {
    document.cookie = 'csrftoken=login-token; Path=/'
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/csrf')) {
        return new Response('{}', { status: 200 })
      }
      if (url.endsWith('/auth/login')) {
        return new Response(
          JSON.stringify({
            user_id: 1,
            email: 'user@example.com',
            display_name: 'user@example.com',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }
      throw new Error(`unexpected ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLogin('/projects/11111111-1111-4111-8111-111111111111/calc')
    expect(screen.getByText('玄构天枢')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('邮箱'), {
      target: { value: 'user@example.com' },
    })
    fireEvent.change(screen.getByLabelText('密码'), {
      target: { value: 'Strong-pass-2026' },
    })
    fireEvent.click(screen.getByRole('button', { name: '登录' }))

    expect(await screen.findByText('项目计算页已打开')).toBeInTheDocument()
    const loginCall = fetchMock.mock.calls.find(([input]) =>
      String(input).endsWith('/auth/login'),
    ) as [RequestInfo | URL, RequestInit] | undefined
    expect(new Headers(loginCall?.[1]?.headers).get('X-CSRFToken')).toBe('login-token')
    expect(loginCall?.[1]?.credentials).toBe('include')
  })

  it('falls back to the workspace for an unsafe next route', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
        if (String(input).endsWith('/auth/csrf')) return new Response('{}', { status: 200 })
        return new Response(
          JSON.stringify({ user_id: 1, email: 'a@example.com', display_name: 'A' }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        )
      }),
    )

    renderLogin('//evil.example')
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'a@example.com' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'Strong-pass-2026' } })
    fireEvent.click(screen.getByRole('button', { name: '登录' }))

    expect(await screen.findByText('工作台已打开')).toBeInTheDocument()
  })

  it('shows a server authentication error without leaking account existence', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
        if (String(input).endsWith('/auth/csrf')) return new Response('{}', { status: 200 })
        return new Response(JSON.stringify({ detail: '邮箱或密码错误' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )

    renderLogin()
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'missing@example.com' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'wrong-password' } })
    fireEvent.click(screen.getByRole('button', { name: '登录' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('邮箱或密码错误')
    await waitFor(() => expect(screen.getByRole('button', { name: '登录' })).toBeEnabled())
  })
})
