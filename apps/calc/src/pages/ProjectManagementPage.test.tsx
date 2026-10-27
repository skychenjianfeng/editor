import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ProjectManagementPage } from './ProjectManagementPage'

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
    designer: '',
    note: '',
  },
  {
    project_id: '22222222-2222-4222-8222-222222222222',
    name: '苏州厂房加固',
    code: 'PM-019',
    client: '建设单位二',
    location: '苏州',
    region: '江苏',
    status: 'completed',
    status_label: '已完成',
    scheme_count: 3,
    failed_control_count: 0,
    last_calculated_at: '2026-10-27T05:20:00Z',
    updated_at: '2026-10-27T05:20:00Z',
    created_at: '2026-10-25T06:20:00Z',
    designer: '',
    note: '',
  },
]

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function renderProjectManagement() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/workspace/projects']}>
        <Routes>
          <Route path="/workspace/projects" element={<ProjectManagementPage />} />
          <Route path="/projects/:projectId/calc" element={<div>项目计算页</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectManagementPage', () => {
  it('shows the full project management page', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify({ projects }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }),
      ),
    )

    renderProjectManagement()

    expect(screen.getByRole('heading', { name: '项目管理' })).toBeInTheDocument()
    expect(await screen.findByText('滨江研发楼改造')).toBeInTheDocument()
    expect(screen.getByLabelText('搜索项目')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '新建项目' })).toBeInTheDocument()
    expect(screen.queryByText('计算方案')).not.toBeInTheDocument()
  })

  it('labels the current project list without claiming a complete total', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = new URL(String(input), 'http://localhost')
        const filteredProjects = url.searchParams.has('search') ? [projects[0]] : projects
        return new Response(JSON.stringify({ projects: filteredProjects }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )

    renderProjectManagement()

    expect(await screen.findByText('当前列表 2 个项目（最近上限 200）')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('搜索项目'), { target: { value: '滨江' } })

    expect(await screen.findByText('当前列表 1 个项目（最近上限 200）')).toBeInTheDocument()
    expect(screen.queryByText(/共 \d+ 个项目/)).not.toBeInTheDocument()
  })
})
