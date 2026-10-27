export type Params = {
  h: number
  la: number
  lb: number
  steel: string
  tie: string
  board: string
  dead: number
  live: number
  hBoard: number
  braceW: number
}

export const modules = [
  {
    group: '脚手架体系',
    open: true,
    items: [{ name: '盘扣式脚手架' }, { name: '碗扣式脚手架' }, { name: '三角悬挑架' }],
  },
  {
    group: '防护与平台',
    items: [{ name: '移动式操作平台' }, { name: '型钢悬挑卸料平台' }, { name: '防护棚' }],
  },
]

export type ParamField = {
  key: keyof Params
  label: string
  unit?: string
  type: 'number' | 'select'
  step?: number
  options?: string[]
  limit?: string
}

export const paramGroups: { title: string; fields: ParamField[] }[] = [
  {
    title: '基本参数',
    fields: [
      { key: 'h', label: '步距 h', unit: 'm', type: 'number', step: 0.1, limit: '≤2.0' },
      { key: 'la', label: '立杆纵距 la', unit: 'm', type: 'number', step: 0.1, limit: '≤1.8' },
      { key: 'lb', label: '立杆横距 lb', unit: 'm', type: 'number', step: 0.1, limit: '≤1.5' },
      {
        key: 'steel',
        label: '钢管类型',
        type: 'select',
        options: ['φ48×2.8', 'φ48×3.0', 'φ51×3.0'],
      },
      {
        key: 'tie',
        label: '连墙件布置',
        type: 'select',
        options: ['一步三跨', '两步三跨', '两步两跨'],
      },
      {
        key: 'board',
        label: '脚手板类型',
        type: 'select',
        options: ['竹串片脚手板', '木脚手板', '冲压钢脚手板'],
      },
    ],
  },
  {
    title: '荷载参数',
    fields: [
      { key: 'dead', label: '脚手板自重', unit: 'kN/m²', type: 'number', step: 0.05 },
      {
        key: 'live',
        label: '施工均布活荷载',
        unit: 'kN/m²',
        type: 'number',
        step: 0.5,
        limit: '≤3.0',
      },
    ],
  },
  {
    title: '构造要求',
    fields: [
      { key: 'hBoard', label: '挡脚板高度', unit: 'mm', type: 'number', step: 10 },
      { key: 'braceW', label: '剪刀撑宽度', unit: 'm', type: 'number', step: 0.1 },
    ],
  },
]

export type ResultRow = {
  no: number
  item: string
  value: string
  limit: string
  ratio: number
  ok: boolean
  clause: string
  control?: boolean
  detail?: string
}

export const results: ResultRow[] = [
  {
    no: 1,
    item: '立杆稳定性（组合风荷载）',
    value: '89.2',
    limit: '205',
    ratio: 0.44,
    ok: true,
    clause: 'JGJ 130-2011 5.2.6',
    control: true,
  },
  {
    no: 2,
    item: '立杆长细比 λ',
    value: '142',
    limit: '210',
    ratio: 0.68,
    ok: true,
    clause: 'JGJ 130-2011 5.1.9',
  },
  {
    no: 3,
    item: '连墙件强度',
    value: '4.12',
    limit: '3.20',
    ratio: 1.29,
    ok: false,
    clause: 'JGJ 130-2011 5.2.6',
    control: true,
  },
  {
    no: 4,
    item: '连墙件稳定承载力',
    value: '12.8',
    limit: '8.5',
    ratio: 1.51,
    ok: false,
    clause: 'JGJ 130-2011 5.2.6',
  },
  {
    no: 5,
    item: '纵向水平杆抗弯',
    value: '36.4',
    limit: '205',
    ratio: 0.18,
    ok: true,
    clause: 'JGJ 130-2011 5.2.4',
  },
  {
    no: 6,
    item: '横向水平杆抗弯',
    value: '48.9',
    limit: '205',
    ratio: 0.24,
    ok: true,
    clause: 'JGJ 130-2011 5.2.4',
  },
  {
    no: 7,
    item: '扣件抗滑承载力',
    value: '3.86',
    limit: '8.00',
    ratio: 0.48,
    ok: true,
    clause: 'JGJ 130-2011 5.2.5',
    control: true,
  },
  {
    no: 8,
    item: '立杆地基承载力',
    value: '58.1',
    limit: '140',
    ratio: 0.42,
    ok: true,
    clause: 'JGJ 130-2011 5.3.5',
  },
  {
    no: 9,
    item: '脚手架搭设高度',
    value: '24.0',
    limit: '50.0',
    ratio: 0.48,
    ok: true,
    clause: 'JGJ 130-2011 6.1.2',
  },
  {
    no: 10,
    item: '立杆接长方式',
    value: '对接',
    limit: '—',
    ratio: 0,
    ok: true,
    clause: 'JGJ 130-2011 6.3.5',
  },
]
