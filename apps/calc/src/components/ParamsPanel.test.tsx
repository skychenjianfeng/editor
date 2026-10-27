import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ParamsPanel } from './ParamsPanel'

afterEach(cleanup)

describe('ParamsPanel', () => {
  it('renders boolean construction fields as explicit confirmation switches', () => {
    const onUpdate = vi.fn()
    render(
      <ParamsPanel
        groups={[
          {
            title: '构造检查',
            fields: [
              { key: 'braceInstalled', label: '剪刀撑已设置', type: 'boolean', default: true },
              {
                key: 'braceWidth',
                label: '剪刀撑宽度',
                type: 'number',
                unit: 'm',
                step: 0.1,
                default: 6,
              },
            ],
          },
          {
            title: '其他参数',
            fields: [{ key: 'extra', label: '附加参数', type: 'number', default: 1 }],
          },
        ]}
        params={{ braceInstalled: true, braceWidth: 6, extra: 1 }}
        onUpdate={onUpdate}
      />,
    )

    const toggle = screen.getByRole('switch', { name: '剪刀撑已设置' })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByText('共 3 项参数')).toBeInTheDocument()
    expect(screen.queryByText('附加参数')).not.toBeInTheDocument()

    fireEvent.click(toggle)
    expect(onUpdate).toHaveBeenCalledWith('braceInstalled', false)
  })
})
