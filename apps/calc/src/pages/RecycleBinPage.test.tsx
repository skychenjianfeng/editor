import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RecycleBinPage } from './RecycleBinPage'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('RecycleBinPage', () => {
  it('shows the disabled recycle-bin state without calling the delete API', () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter initialEntries={['/workspace/recycle-bin']}>
        <Routes>
          <Route path="/workspace/recycle-bin" element={<RecycleBinPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: '回收站' })).toBeInTheDocument()
    expect(screen.getByText('回收站尚未启用')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '返回项目管理' })).toHaveAttribute(
      'href',
      '/workspace/projects',
    )
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
