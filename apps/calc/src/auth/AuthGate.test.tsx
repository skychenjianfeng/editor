import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthGate, safeNextPath } from './AuthGate'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function renderGate(initialEntry: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/login" element={<div>登录页</div>} />
          <Route element={<AuthGate />}>
            <Route path="/workspace" element={<div>工作台</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AuthGate', () => {
  it('sends anonymous users to login with a protected-path next', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{}', { status: 401 })),
    )

    renderGate('/workspace?status=calculating')

    expect(screen.getByRole('status')).toHaveTextContent('正在恢复会话')
    expect(await screen.findByText('登录页')).toBeInTheDocument()
  })

  it('allows only safe single-slash next paths', () => {
    expect(safeNextPath('/projects/abc/calc')).toBe('/projects/abc/calc')
    expect(safeNextPath('//evil.example')).toBe('/workspace')
    expect(safeNextPath('https://evil.example')).toBe('/workspace')
    expect(safeNextPath('projects/abc')).toBe('/workspace')
    expect(safeNextPath(null)).toBe('/workspace')
  })
})
