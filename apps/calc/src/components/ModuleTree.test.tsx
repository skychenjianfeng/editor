import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ProjectRecord } from '../api/projects'
import { ModuleTree } from './ModuleTree'

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

const REGIONS = ['全国', '上海', '浙江', '广东', '江苏', '山东', '重庆', '北京', '湖北', '福建']
const CATEGORIES = [
  '常用验算',
  '落地式脚手架',
  '爬架临时支撑平台',
  '吊篮工程',
  '移动操作平台',
  '井道操作平台',
  '斜道',
  '操作平台、卸料平台',
  '施工升降机卸料平台',
  '工具式脚手架',
  '防护棚',
  '型钢悬挑脚手架',
  '花篮螺栓悬挑架',
]

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function renderTree(
  overrides: Partial<{
    schemeName: string
    onSelect: (key: string) => void
    onSchemes: () => void
  }> = {},
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  const onSelect = overrides.onSelect ?? vi.fn()
  const onSchemes = overrides.onSchemes ?? vi.fn()

  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ModuleTree
          project={project}
          active="scaffold-fastener"
          schemeName={overrides.schemeName}
          onSelect={onSelect}
          onSchemes={onSchemes}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )

  return { onSelect, onSchemes }
}

describe('ModuleTree', () => {
  it('renders all ten regions with the project region highlighted', async () => {
    renderTree()
    const regionGroup = screen.getByRole('region', {
      name: '项目地区（创建项目时确定）',
    })
    expect(
      Array.from(regionGroup.querySelectorAll(':scope > span')).map(
        (element) => element.textContent,
      ),
    ).toEqual(REGIONS)
    expect(within(regionGroup).getByText('上海')).toHaveAttribute('aria-current', 'true')
    expect(within(regionGroup).getByText('全国')).not.toHaveAttribute('aria-current')
    expect(within(regionGroup).queryByRole('button')).not.toBeInTheDocument()

    await screen.findByText('扣件式脚手架（品茗双立杆）')
  })

  it('renders every catalog category and marks new categories', async () => {
    renderTree()
    await screen.findByText('扣件式脚手架（品茗双立杆）')

    for (const category of CATEGORIES) {
      expect(screen.getByText(category, { selector: 'span' })).toBeInTheDocument()
    }
    expect(screen.getAllByText('新增')).toHaveLength(2)
    expect(screen.getAllByText('骨架版').length).toBeGreaterThan(0)
  })

  it('selects available modules but never selects planned modules', async () => {
    const { onSelect } = renderTree()
    const available = await screen.findByRole('button', {
      name: /扣件式脚手架（品茗双立杆）/,
    })
    fireEvent.click(available)
    expect(onSelect).toHaveBeenCalledWith('scaffold-fastener-pinming')

    const planned = screen.getByRole('button', {
      name: /双排外竹脚手架，待接入/,
    })
    expect(planned).toBeDisabled()
    expect(planned).toHaveAttribute('aria-disabled', 'true')
    fireEvent.click(planned)
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('searches module titles, standards and category titles', async () => {
    const { onSelect } = renderTree()
    const search = screen.getByLabelText('搜索计算模块')
    await screen.findByText('扣件式脚手架（品茗双立杆）')

    fireEvent.change(search, { target: { value: '品茗' } })
    expect(screen.getByRole('button', { name: /扣件式脚手架（品茗双立杆）/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^连墙件计算/ })).not.toBeInTheDocument()

    fireEvent.change(search, { target: { value: 'JGJ 128-2010' } })
    expect(screen.getByRole('button', { name: /门式脚手架/ })).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /扣件式脚手架（品茗双立杆）/ }),
    ).not.toBeInTheDocument()

    fireEvent.change(search, { target: { value: '防护棚' } })
    expect(screen.getByText('防护棚', { selector: 'span' })).toBeInTheDocument()
    const planned = screen.getByRole('button', { name: /防护棚\(扣件式\)，待接入/ })
    expect(planned).toBeDisabled()
    fireEvent.click(planned)
    expect(onSelect).not.toHaveBeenCalled()

    fireEvent.change(search, { target: { value: '不存在的模块' } })
    expect(screen.getByText('未找到脚手架模块')).toBeInTheDocument()
  })

  it('collapses project, module, and category nodes', async () => {
    renderTree()
    await screen.findByText('扣件式脚手架（品茗双立杆）')

    fireEvent.click(screen.getByRole('button', { name: '收起防护棚' }))
    expect(screen.queryByRole('button', { name: /防护棚\(扣件式\)/ })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '收起计算模块' }))
    expect(screen.getByRole('button', { name: '展开计算模块' })).toBeInTheDocument()
    expect(screen.queryByLabelText('搜索计算模块')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '收起项目目录' }))
    expect(screen.getByRole('button', { name: '展开项目目录' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /打开计算方案/ })).not.toBeInTheDocument()
  })

  it('preserves project, scheme, return and new-scheme behavior', () => {
    const { onSchemes } = renderTree({ schemeName: '南立面方案' })

    expect(screen.getByRole('complementary', { name: '工作台目录' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '返回项目工作台：滨江研发楼改造' })).toHaveAttribute(
      'href',
      '/workspace',
    )
    const schemeButton = screen.getByRole('button', {
      name: /打开计算方案：南立面方案，2 个方案/,
    })
    fireEvent.click(schemeButton)
    fireEvent.click(screen.getByRole('button', { name: '新建方案' }))
    expect(onSchemes).toHaveBeenCalledTimes(2)
  })
})
