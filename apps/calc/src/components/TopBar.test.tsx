import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { TopBar } from './TopBar'

afterEach(cleanup)

describe('TopBar', () => {
  it('显示真实模块名与计算结果总数', () => {
    const { container } = render(
      <TopBar
        dirty={false}
        moduleTitle="高处作业吊篮"
        schemeName="北立面吊篮"
        total={24}
        onRun={vi.fn()}
        onHistory={vi.fn()}
        onSchemes={vi.fn()}
      />,
    )

    expect(screen.getByText('高处作业吊篮')).toBeInTheDocument()
    expect(screen.getByText('北立面吊篮')).toBeInTheDocument()
    expect(screen.getByText('已计算 · 24 项')).toBeInTheDocument()
    expect(screen.getByText('本地 API')).toBeInTheDocument()
    expect(screen.queryByText(/12ms/)).not.toBeInTheDocument()
    expect(container.querySelector('header')).toHaveClass('overflow-x-auto')
  })
})
