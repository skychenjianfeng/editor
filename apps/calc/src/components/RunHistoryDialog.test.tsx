import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { RunPayload, RunRecord } from '../api/calc'
import { RunHistoryDialog } from './RunHistoryDialog'

const runId = '5084f043-cba0-40e4-80e7-993d554d7452'

const run: RunRecord = {
  run_id: runId,
  created_at: '2026-10-26T04:00:00+00:00',
  module: 'scaffold-fastener',
  title: '扣件式脚手架',
  standard: 'JGJ 130-2011',
  verified: false,
  summary: { total: 29, failed: 2, control_failed: 1 },
  total: 29,
  failed: 2,
  control_failed: 1,
}

const detail: RunPayload = {
  run_id: runId,
  module: 'scaffold-fastener',
  verified: false,
  standard: 'JGJ 130-2011',
  params: { h: 2.1, la: 1.4, lb: 0.85, H: 30 },
  summary: { total: 29, failed: 2, control_failed: 1 },
  results: [],
  derived: {},
  assumptions: [],
}

let activeClient: QueryClient | null = null

afterEach(() => {
  cleanup()
  activeClient?.clear()
  activeClient = null
  vi.unstubAllGlobals()
})

function renderDialog(runs: RunRecord[], onLoad = vi.fn()) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false, gcTime: 0 },
    },
  })
  activeClient = client
  render(
    <QueryClientProvider client={client}>
      <RunHistoryDialog open activeModule="scaffold-fastener" onClose={vi.fn()} onLoad={onLoad} />
    </QueryClientProvider>,
  )
  return onLoad
}

describe('RunHistoryDialog', () => {
  it('展示历史摘要并在选择后加载完整参数', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      const body = url.includes(`/runs/${runId}`) ? detail : { runs: [run] }
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })
    vi.stubGlobal('fetch', fetchMock)
    const onLoad = renderDialog([run])

    expect(await screen.findByText('扣件式脚手架')).toBeInTheDocument()
    expect(screen.getByText('JGJ 130-2011')).toBeInTheDocument()
    expect(screen.getByText('通过 27')).toBeInTheDocument()
    expect(screen.getByText('失败 2')).toBeInTheDocument()
    expect(screen.getByText('总项 29')).toBeInTheDocument()
    expect(screen.getByText('5084f043…7452')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: `加载历史记录 ${runId}` }))

    await waitFor(() => {
      expect(onLoad).toHaveBeenCalledWith(detail)
    })
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith(`/runs/${runId}`))).toBe(
      true,
    )
    expect(detail.params).toMatchObject({ h: 2.1, la: 1.4, lb: 0.85, H: 30 })
    expect(detail.run_id).toBe(runId)
  })

  it('空列表显示空状态', async () => {
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ runs: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })
    vi.stubGlobal('fetch', fetchMock)
    renderDialog([])

    expect(await screen.findByText('暂无历史记录')).toBeInTheDocument()
  })
})
