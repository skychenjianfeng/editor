import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ProjectRecord, SchemeRecord } from '../api/calc'
import { SchemeDialog } from './SchemeDialog'

const project: ProjectRecord = {
  project_id: '11111111-1111-4111-8111-111111111111',
  name: '示例项目',
  region: '上海',
  status: 'preparing',
  status_label: '筹备中',
  scheme_count: 0,
  failed_control_count: 0,
  last_calculated_at: null,
  code: 'P-01',
  client: '建设单位',
  location: '上海',
  designer: '张工',
  note: '',
  created_at: '2026-10-26T00:00:00Z',
  updated_at: '2026-10-26T00:00:00Z',
}

const scheme: SchemeRecord = {
  scheme_id: '22222222-2222-4222-8222-222222222222',
  project_id: project.project_id,
  name: '北立面',
  module: 'scaffold-fastener',
  module_title: '扣件式脚手架',
  params: { h: 1.8, la: 1.5 },
  last_run_id: null,
  created_at: '2026-10-26T00:00:00Z',
  updated_at: '2026-10-26T00:00:00Z',
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('SchemeDialog', () => {
  it('only lists and saves schemes for the current project', async () => {
    const onOpenScheme = vi.fn()
    const onSaved = vi.fn()
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith(`/projects/${project.project_id}/schemes`)) {
        if (init?.method === 'POST') {
          const body = JSON.parse(String(init.body))
          return new Response(
            JSON.stringify({
              ...scheme,
              ...body,
              scheme_id: '33333333-3333-4333-8333-333333333333',
            }),
            {
              status: 201,
              headers: { 'Content-Type': 'application/json' },
            },
          )
        }
        return new Response(JSON.stringify({ schemes: [scheme] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({}), { status: 404 })
    })
    vi.stubGlobal('fetch', fetchMock)
    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false, gcTime: 0 },
      },
    })

    render(
      <QueryClientProvider client={client}>
        <SchemeDialog
          open
          project={project}
          module="scaffold-fastener"
          moduleTitle="扣件式脚手架"
          params={{ h: 1.8, la: 1.5, lb: 0.9 }}
          lastRunId="44444444-4444-4444-8444-444444444444"
          onClose={vi.fn()}
          onOpenScheme={onOpenScheme}
          onSaved={onSaved}
        />
      </QueryClientProvider>,
    )

    expect(await screen.findByText('北立面')).toBeInTheDocument()
    expect(screen.queryByLabelText('搜索项目')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('新建项目')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('打开'))
    expect(onOpenScheme).toHaveBeenCalledWith(scheme)

    fireEvent.change(screen.getByLabelText('方案名称'), { target: { value: '南立面修订' } })
    fireEvent.click(screen.getByText('保存方案'))

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(([input, init]) => {
        return (
          String(input).endsWith(`/projects/${project.project_id}/schemes`) &&
          init?.method === 'POST'
        )
      })
      expect(post).toBeDefined()
      expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({
        name: '南立面修订',
        module: 'scaffold-fastener',
        params: { h: 1.8, la: 1.5, lb: 0.9 },
        last_run_id: '44444444-4444-4444-8444-444444444444',
      })
    })
    await waitFor(() => expect(onSaved).toHaveBeenCalled())
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/projects?'))).toBe(false)
  })
})
