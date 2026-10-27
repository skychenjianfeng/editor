import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { ProjectRecord } from '../api/projects'
import { CalcWorkspacePage } from './CalcWorkspacePage'

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

const baseFetch = globalThis.fetch

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith(`/projects/${project.project_id}`)) {
        return new Response(JSON.stringify(project), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return baseFetch(input, init)
    }),
  )
})

function renderPage() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false, gcTime: 0 },
    },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/projects/${project.project_id}/calc`]}>
        <Routes>
          <Route path="/workspace" element={<div>项目工作台</div>} />
          <Route path="/projects/:projectId/calc" element={<CalcWorkspacePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('CalcWorkspacePage', () => {
  it('shows project context and the return link', async () => {
    renderPage()
    expect(await screen.findByText('滨江研发楼改造')).toBeInTheDocument()
    expect(screen.getByText('上海')).toBeInTheDocument()
    expect(screen.getByText('计算中')).toBeInTheDocument()
    expect(screen.getByText('2 个方案')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '返回项目工作台' })).toHaveAttribute(
      'href',
      '/workspace',
    )
  })

  it('keeps the module tree, parameters, and results layout', async () => {
    renderPage()
    expect(await screen.findByText('安全计算工作台')).toBeInTheDocument()
    expect(screen.getByText('扣件式脚手架')).toBeInTheDocument()
    expect(await screen.findByText('扣件式脚手架（品茗双立杆）')).toBeInTheDocument()
    expect(screen.getByText('立杆纵距 la')).toBeInTheDocument()
    expect(screen.getByText('连墙件强度')).toBeInTheDocument()
  })

  it('filters the result table to failed rows', async () => {
    renderPage()
    await screen.findByText('连墙件强度')
    fireEvent.click(screen.getByText('仅不满足'))
    const rows = screen.getAllByText(/不满足|连墙件强度|连墙件稳定承载力/)
    expect(rows.length).toBeGreaterThanOrEqual(2)
    expect(screen.queryByText('立杆长细比 λ')).not.toBeInTheDocument()
  })

  it('requests plan geometry when switching the view', async () => {
    const fetchMock = globalThis.fetch as unknown as { mock: { calls: unknown[][] } }
    renderPage()
    await screen.findByText('连墙件强度')
    fireEvent.click(screen.getByText('平面'))
    await waitFor(() => {
      const bodies = fetchMock.mock.calls.map((call) =>
        String((call[1] as RequestInit | undefined)?.body ?? ''),
      )
      expect(bodies.some((body) => body.includes('"view":"plan"'))).toBe(true)
    })
  })

  it('requests new geometry after a parameter change', async () => {
    const { container } = renderPage()
    await screen.findByText('立杆纵距 la')
    const fetchMock = globalThis.fetch as unknown as { mock: { calls: unknown[][] } }
    const inputs = container.querySelectorAll('input[type="number"]')
    fireEvent.change(inputs[0], { target: { value: '2' } })
    await waitFor(() => {
      const bodies = fetchMock.mock.calls.map((call) =>
        String((call[1] as RequestInit | undefined)?.body ?? ''),
      )
      expect(bodies.some((body) => body.includes('"h":2'))).toBe(true)
    })
  })
})
