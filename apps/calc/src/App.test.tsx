import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { ProjectRecord } from './api/projects'

const project: ProjectRecord = {
  project_id: '11111111-1111-4111-8111-111111111111',
  name: '滨江研发楼改造',
  code: 'PM-018',
  client: '',
  location: '上海',
  region: '上海',
  status: 'calculating',
  status_label: '计算中',
  scheme_count: 2,
  failed_control_count: 0,
  last_calculated_at: null,
  designer: '',
  note: '',
  created_at: '2026-10-26T00:00:00Z',
  updated_at: '2026-10-27T00:00:00Z',
}

const setupFetch = globalThis.fetch

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function renderApp(path: string, authenticated: boolean) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) {
        return authenticated
          ? new Response(
              JSON.stringify({
                user_id: 1,
                email: 'engineer@example.com',
                display_name: '张工',
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } },
            )
          : new Response(JSON.stringify({ detail: '未登录' }), {
              status: 401,
              headers: { 'Content-Type': 'application/json' },
            })
      }
      if (url.endsWith(`/projects/${project.project_id}`)) {
        return new Response(JSON.stringify(project), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      if (url.includes('/projects?')) {
        return new Response(JSON.stringify({ projects: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return setupFetch(input, init)
    }),
  )

  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false, gcTime: 0 },
    },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('App routes', () => {
  it('redirects anonymous users from protected pages to login', async () => {
    renderApp('/workspace', false)
    expect(await screen.findByRole('button', { name: '登录' })).toBeInTheDocument()
    expect(screen.getByText('欢迎回来')).toBeInTheDocument()
  })

  it('redirects anonymous users from workspace settings to login', async () => {
    renderApp('/workspace/settings', false)
    expect(await screen.findByRole('button', { name: '登录' })).toBeInTheDocument()
    expect(screen.getByText('欢迎回来')).toBeInTheDocument()
  })

  it('redirects authenticated root requests to the project workspace', async () => {
    renderApp('/', true)
    expect(await screen.findByRole('heading', { name: '项目工作台' })).toBeInTheDocument()
  })

  it('renders the calculator only for a project route', async () => {
    renderApp(`/projects/${project.project_id}/calc`, true)
    expect((await screen.findAllByText('滨江研发楼改造')).length).toBeGreaterThanOrEqual(2)
    expect(screen.getByRole('link', { name: '返回项目工作台' })).toBeInTheDocument()
  })
})
