import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { WorkspaceSettingsPage } from './WorkspaceSettingsPage'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('WorkspaceSettingsPage', () => {
  it('shows read-only account and workspace boundaries', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ user_id: 1, email: 'engineer@example.com', display_name: '张工' }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    )
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })

    render(
      <QueryClientProvider client={client}>
        <WorkspaceSettingsPage />
      </QueryClientProvider>,
    )

    expect(screen.getByRole('heading', { name: '系统设置' })).toBeInTheDocument()
    expect(await screen.findByText('engineer@example.com')).toBeInTheDocument()
    expect(screen.getByText('玄构天枢')).toBeInTheDocument()
    expect(screen.getByText('数据归属')).toBeInTheDocument()
    expect(screen.getByText('会话说明')).toBeInTheDocument()
    expect(
      screen.getByText('登录状态由 Session Cookie 维护，写请求受 CSRF 保护；退出后需重新登录。'),
    ).toBeInTheDocument()
    expect(screen.getByText('地区只作为项目属性，不切换当前计算规范。')).toBeInTheDocument()
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()
  })
})
