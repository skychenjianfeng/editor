import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import App from './App'

let activeClient: QueryClient | null = null

afterEach(() => {
  cleanup()
  activeClient?.clear()
  activeClient = null
})

function renderApp() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false, gcTime: 0 },
    },
  })
  activeClient = client
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
}

describe('S2 计算工作台', () => {
  it('渲染模块树、参数与结果三联', async () => {
    renderApp()
    expect(screen.getByText('安全计算工作台')).toBeInTheDocument()
    expect(screen.getByText('扣件式脚手架')).toBeInTheDocument()
    expect(await screen.findByText('扣件式脚手架（品茗双立杆）')).toBeInTheDocument()
    expect(screen.getByText('立杆纵距 la')).toBeInTheDocument()
    expect(screen.getByText('连墙件强度')).toBeInTheDocument()
  })

  it('仅不满足筛选出 2 行', () => {
    renderApp()
    fireEvent.click(screen.getByText('仅不满足'))
    const rows = screen.getAllByText(/不满足|连墙件强度|连墙件稳定承载力/)
    expect(rows.length).toBeGreaterThanOrEqual(2)
    expect(screen.queryByText('立杆长细比 λ')).not.toBeInTheDocument()
  })

  it('切换平面视图会向后端请求 plan 几何', async () => {
    const fetchMock = globalThis.fetch as unknown as { mock: { calls: unknown[][] } }
    renderApp()
    fireEvent.click(screen.getByText('平面'))
    await waitFor(() => {
      const bodies = fetchMock.mock.calls.map((c) =>
        String((c[1] as RequestInit | undefined)?.body ?? ''),
      )
      expect(bodies.some((b) => b.includes('"view":"plan"'))).toBe(true)
    })
  })

  it('修改步距后重新请求几何', async () => {
    const { container } = renderApp()
    const fetchMock = globalThis.fetch as unknown as { mock: { calls: unknown[][] } }
    const inputs = container.querySelectorAll('input[type="number"]')
    fireEvent.change(inputs[0], { target: { value: '2' } })
    await waitFor(() => {
      const bodies = fetchMock.mock.calls.map((c) =>
        String((c[1] as RequestInit | undefined)?.body ?? ''),
      )
      expect(bodies.some((b) => b.includes('"h":2'))).toBe(true)
    })
  })
})
