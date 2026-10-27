import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ParamGroup } from '../api/calc'
import { BatchDialog } from './BatchDialog'

const groups = [
  {
    title: '吊篮平台与主梁',
    fields: [
      { key: 'ratedLoad', label: '额定载重量 R1', type: 'number', unit: 'kg', default: 630 },
      { key: 'platformSpan', label: '吊点间距/计算跨度 L', type: 'number', unit: 'm', default: 6 },
      { key: 'beamCount', label: '共同受力主梁数', type: 'number', unit: '根', default: 2 },
    ],
  },
] satisfies ParamGroup[]

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('BatchDialog', () => {
  it('按吊篮数字字段生成通用批量请求', async () => {
    const fetchMock = vi.fn(
      async (_input: RequestInfo | URL, _init?: RequestInit) =>
        new Response(
          JSON.stringify({
            count: 1,
            failed: 0,
            control_failed: 0,
            rows: [
              {
                index: 1,
                name: 'C01',
                params: { ratedLoad: 500, platformSpan: 5 },
                module: 'suspended-basket',
                primary_item: '平台主梁抗弯',
                primary_key: 'platform_bending',
                primary_value: 80,
                primary_unit: 'N/mm²',
                primary_ratio: 0.4,
                primary_ok: true,
                failed: 0,
                control_failed: 0,
                ok: true,
              },
            ],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
    )
    vi.stubGlobal('fetch', fetchMock)
    const client = new QueryClient({
      defaultOptions: { mutations: { retry: false, gcTime: 0 } },
    })

    render(
      <QueryClientProvider client={client}>
        <BatchDialog
          open
          module="suspended-basket"
          groups={groups}
          baseParams={{ platformWeight: 450, platformSpan: 6, ratedLoad: 630 }}
          onClose={() => {}}
        />
      </QueryClientProvider>,
    )

    expect(screen.getByLabelText('矩阵字段A')).toHaveValue('ratedLoad')
    expect(screen.getByLabelText('矩阵字段B')).toHaveValue('platformSpan')
    fireEvent.change(screen.getByLabelText('额定载重量 R1取值列表'), {
      target: { value: '500, 600' },
    })
    fireEvent.change(screen.getByLabelText('吊点间距/计算跨度 L取值列表'), {
      target: { value: '5, 6' },
    })
    fireEvent.click(screen.getByText('开始批量计算'))

    await waitFor(() => {
      const batchCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/batches'))
      expect(batchCall).toBeDefined()
      const body = JSON.parse(String(batchCall?.[1]?.body))
      expect(body.module).toBe('suspended-basket')
      expect(body.cases).toHaveLength(4)
      expect(body.cases[0]).toMatchObject({
        platformWeight: 450,
        ratedLoad: 500,
        platformSpan: 5,
      })
    })
  })
})
