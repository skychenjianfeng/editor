import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { WorkspacePage } from './WorkspacePage'

const projects = [
  {
    project_id: '11111111-1111-4111-8111-111111111111',
    name: '滨江研发楼改造',
    code: 'PM-018',
    client: '建设单位',
    location: '上海',
    region: '上海',
    status: 'calculating',
    status_label: '计算中',
    scheme_count: 8,
    failed_control_count: 1,
    last_calculated_at: '2026-10-27T06:20:00Z',
    updated_at: '2026-10-27T06:20:00Z',
    created_at: '2026-10-26T06:20:00Z',
  },
  {
    project_id: '22222222-2222-4222-8222-222222222222',
    name: '苏州厂房加固',
    code: 'PM-019',
    client: '',
    location: '苏州',
    region: '江苏',
    status: 'completed',
    status_label: '已完成',
    scheme_count: 3,
    failed_control_count: 0,
    last_calculated_at: '2026-10-27T05:20:00Z',
    updated_at: '2026-10-27T05:20:00Z',
    created_at: '2026-10-25T06:20:00Z',
  },
]

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function renderWorkspace(initialEntry = '/workspace') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/workspace" element={<WorkspacePage />} />
          <Route path="/projects/:projectId/calc" element={<div>项目计算页</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('WorkspacePage', () => {
  it('shows project context, derived metrics, and opens a row with Enter', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) {
        return new Response(
          JSON.stringify({ user_id: 1, email: 'engineer@example.com', display_name: '张工' }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }
      return new Response(JSON.stringify({ projects }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })
    vi.stubGlobal('fetch', fetchMock)

    renderWorkspace()

    expect(screen.getByRole('status', { name: '项目指标加载中' })).toBeInTheDocument()
    expect(await screen.findByText('滨江研发楼改造')).toBeInTheDocument()
    expect(screen.getAllByText('上海').length).toBeGreaterThan(0)
    expect(screen.getAllByText('计算中').length).toBeGreaterThan(0)
    expect(screen.getByText('计算方案')).toBeInTheDocument()
    expect(screen.getByText('11')).toBeInTheDocument()
    expect(screen.getByText('PM-018')).toBeInTheDocument()
    expect(screen.getByText('最近项目')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '查看全部项目' })).toHaveAttribute(
      'href',
      '/workspace/projects',
    )

    const row = screen.getByRole('row', { name: /滨江研发楼改造/ })
    fireEvent.keyDown(row, { key: 'Enter' })
    expect(await screen.findByText('项目计算页')).toBeInTheDocument()
  })

  it('shows only the eight most recent projects on the overview', async () => {
    const manyProjects = [1, 10, 2, 9, 3, 8, 4, 7, 5, 6].map((index) => ({
      ...projects[0],
      project_id: `${index}1111111-1111-4111-8111-111111111111`,
      name: `项目 ${index}`,
      code: `PM-${String(index).padStart(3, '0')}`,
      updated_at: new Date(Date.UTC(2026, 9, index)).toISOString(),
    }))
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify({ projects: manyProjects }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }),
      ),
    )

    renderWorkspace()

    expect(await screen.findByText('项目 6')).toBeInTheDocument()
    expect(screen.queryByText('项目 1')).not.toBeInTheDocument()
    expect(
      screen
        .getAllByRole('row')
        .map((row) => row.getAttribute('aria-label'))
        .filter(Boolean),
    ).toEqual([
      '项目 10 上海 计算中',
      '项目 9 上海 计算中',
      '项目 8 上海 计算中',
      '项目 7 上海 计算中',
      '项目 6 上海 计算中',
      '项目 5 上海 计算中',
      '项目 4 上海 计算中',
      '项目 3 上海 计算中',
    ])
  })

  it('shows a retryable metrics error instead of falling back to filtered results', async () => {
    let globalProjectRequests = 0
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = new URL(String(input), 'http://localhost')
        if (url.searchParams.has('search')) {
          return new Response(JSON.stringify({ projects: [projects[0]] }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
        globalProjectRequests += 1
        return new Response(JSON.stringify({ detail: '全局项目读取失败' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )

    renderWorkspace('/workspace?search=%E6%BB%A8%E6%B1%9F')

    expect(await screen.findByText('项目指标加载失败')).toBeInTheDocument()
    expect(screen.getByText('全局项目读取失败')).toBeInTheDocument()
    expect(await screen.findByText('滨江研发楼改造')).toBeInTheDocument()
    expect(screen.queryByText('11')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '重试项目指标' }))

    await waitFor(() => expect(globalProjectRequests).toBeGreaterThan(1))
  })

  it('sends search and status filters to the server query', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) {
        return new Response(
          JSON.stringify({ user_id: 1, email: 'engineer@example.com', display_name: '张工' }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }
      return new Response(JSON.stringify({ projects }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })
    vi.stubGlobal('fetch', fetchMock)

    renderWorkspace()
    await screen.findByText('滨江研发楼改造')
    fireEvent.change(screen.getByLabelText('搜索项目'), { target: { value: '滨江' } })
    fireEvent.change(screen.getByLabelText('状态筛选'), { target: { value: 'calculating' } })

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map(([input]) => String(input))
      expect(
        urls.some(
          (url) =>
            url.includes('/projects?') &&
            url.includes('search=%E6%BB%A8%E6%B1%9F') &&
            url.includes('status=calculating'),
        ),
      ).toBe(true)
    })
  })

  it('distinguishes an empty result from a new workspace', async () => {
    let hasProjects = true
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input)
        if (url.endsWith('/auth/me')) {
          return new Response(
            JSON.stringify({ user_id: 1, email: 'engineer@example.com', display_name: '张工' }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          )
        }
        return new Response(JSON.stringify({ projects: hasProjects ? projects : [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )

    renderWorkspace()
    await screen.findByText('滨江研发楼改造')
    hasProjects = false
    fireEvent.change(screen.getByLabelText('搜索项目'), { target: { value: '不存在' } })

    expect(await screen.findByText('没有匹配的项目')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '清除筛选' })).toBeInTheDocument()
  })
})
