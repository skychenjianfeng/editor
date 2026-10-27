import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { WorkspaceLayout } from './WorkspaceLayout'

afterEach(cleanup)

function renderLayout(path: string) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false, gcTime: 0 },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/workspace" element={<WorkspaceLayout />}>
            <Route index element={<div>工作台内容</div>} />
            <Route path="projects" element={<div>项目管理内容</div>} />
            <Route path="settings" element={<h1>系统设置</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('WorkspaceLayout', () => {
  it('shows all directory entries and marks the active route', () => {
    renderLayout('/workspace/projects')

    const directory = screen.getByRole('navigation', { name: '工作台目录' })
    expect(within(directory).getByText('工作台目录')).toBeVisible()
    expect(
      within(directory)
        .getAllByRole('link')
        .map((link) => [link.textContent?.trim(), link.getAttribute('href')]),
    ).toEqual([
      ['工作台', '/workspace'],
      ['项目管理', '/workspace/projects'],
      ['系统设置', '/workspace/settings'],
      ['回收站', '/workspace/recycle-bin'],
    ])
    expect(within(directory).getByRole('link', { name: '项目管理' })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })

  it('opens the mobile directory and closes it after navigation', async () => {
    const user = userEvent.setup()
    renderLayout('/workspace')

    const trigger = screen.getByRole('button', { name: '打开工作台目录' })
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(trigger).toHaveAttribute('aria-controls', 'workspace-directory-drawer')

    await user.click(trigger)
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
    const directory = screen.getByRole('dialog', { name: '工作台目录' })
    expect(directory).toHaveAttribute('id', 'workspace-directory-drawer')

    await user.click(within(directory).getByRole('link', { name: '系统设置' }))

    expect(await screen.findByRole('heading', { name: '系统设置' })).toBeInTheDocument()
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: '工作台目录' })).not.toBeInTheDocument(),
    )
  })
})
