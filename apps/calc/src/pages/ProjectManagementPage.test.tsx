import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
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
})
