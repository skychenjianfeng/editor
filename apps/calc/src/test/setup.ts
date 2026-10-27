import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'
import { results } from '../mock/data'

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = globalThis.ResizeObserver ?? (ResizeObserverStub as never)

if (!globalThis.DOMRect) {
  globalThis.DOMRect = class {
    x = 0
    y = 0
    width = 0
    height = 0
    top = 0
    right = 0
    bottom = 0
    left = 0
    toJSON() {
      return this
    }
  } as never
}

const runPayload = {
  run_id: 'test',
  module: 'scaffold-fastener',
  verified: false,
  standard: 'JGJ 130-2011',
  params: { h: 1.8, la: 1.5, lb: 0.9 },
  summary: {
    total: results.length,
    failed: results.filter((r) => !r.ok).length,
    control_failed: 1,
  },
  results: results.map((r, i) => ({
    no: r.no,
    key: `k${i}`,
    item: r.item,
    value: Number(r.value),
    limit: Number(r.limit),
    unit: '',
    ratio: r.ratio,
    ok: r.ok,
    clause: r.clause,
    control: Boolean(r.control),
    detail: r.detail ?? '',
  })),
  derived: {},
  assumptions: [],
}

const geometryPayload = {
  view: 'elevation',
  units: 'mm',
  bounds: { minX: -1400, minY: -1200, maxX: 9400, maxY: 24600 },
  layers: [
    {
      id: 'upright',
      name: '立杆',
      color: '#e5484d',
      items: [{ type: 'line', x1: 0, y1: 0, x2: 0, y2: 24000 }],
    },
    {
      id: 'level',
      name: '水平杆',
      color: '#e5484d',
      items: [{ type: 'line', x1: 0, y1: 0, x2: 9000, y2: 0 }],
    },
    {
      id: 'brace',
      name: '剪刀撑',
      color: '#3e63dd',
      items: [{ type: 'line', x1: 0, y1: 0, x2: 1500, y2: 1800 }],
    },
    {
      id: 'dim',
      name: '尺寸标注',
      color: '#30a46c',
      items: [{ type: 'text', text: '24000', x: 0, y: 0, size: 200, rotation: 0 }],
    },
  ],
}

const specPayload = {
  module: 'scaffold-fastener',
  title: '扣件式脚手架',
  standard: 'JGJ 130-2011',
  verified: false,
  groups: [
    {
      key: 'basic',
      title: '基本参数',
      fields: [
        { key: 'h', label: '步距 h', type: 'number', unit: 'm', default: 1.8, step: 0.1 },
        { key: 'la', label: '立杆纵距 la', type: 'number', unit: 'm', default: 1.5, step: 0.1 },
        { key: 'lb', label: '立杆横距 lb', type: 'number', unit: 'm', default: 0.9, step: 0.1 },
      ],
    },
  ],
}

globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
  const url = String(input)
  const body = url.includes('/geometry')
    ? geometryPayload
    : url.includes('/catalog/param-spec')
      ? specPayload
      : url.includes('/catalog/modules')
        ? {
            modules: [
              {
                key: 'scaffold-fastener',
                title: '扣件式脚手架',
                standard: 'JGJ 130-2011',
                verified: false,
              },
              {
                key: 'scaffold-fastener-pinming',
                title: '扣件式脚手架（品茗双立杆）',
                standard: 'JGJ 130-2011',
                verified: false,
                category: '落地与满堂',
              },
            ],
          }
        : url.includes('/runs?')
          ? { runs: [] }
          : runPayload
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}) as never
