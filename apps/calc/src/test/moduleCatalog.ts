import type { ModuleCatalog, ModuleInfo } from '../api/calc'
import { REGIONS } from '../api/projects'

function available(key: string, title: string, standard: string, verified = false): ModuleInfo {
  return {
    key,
    title,
    standard,
    verified,
    available: true,
    status: 'available',
    note: '',
  }
}

function planned(key: string, title: string): ModuleInfo {
  return {
    key: `planned:${key}`,
    title,
    standard: '',
    verified: false,
    available: false,
    status: 'planned',
    note: '计算内核待接入',
  }
}

const categories = [
  {
    key: 'common-checks',
    title: '常用验算',
    isNew: false,
    modules: [
      planned('edge-guardrail', '临边防护栏杆'),
      available('scaffold-tie-member', '连墙件计算', 'JGJ 130-2011'),
    ],
  },
  {
    key: 'ground-scaffold',
    title: '落地式脚手架',
    isNew: false,
    modules: [
      available('scaffold-fastener', '扣件式脚手架', 'JGJ 130-2011'),
      available('scaffold-fastener-pinming', '扣件式脚手架（品茗双立杆）', 'JGJ 130-2011'),
      available('door-scaffold', '门式脚手架', 'JGJ 128-2010'),
      planned('double-row-bamboo', '双排外竹脚手架'),
    ],
  },
  {
    key: 'climbing-temporary-support',
    title: '爬架临时支撑平台',
    isNew: true,
    modules: [
      planned('climbing-support-fastener', '爬架临时支撑平台(扣件式)'),
      planned('climbing-support-disk-buckle', '爬架临时支撑平台(盘扣式)'),
    ],
  },
  {
    key: 'suspended-basket',
    title: '吊篮工程',
    isNew: false,
    modules: [
      planned('basket-parapet-clamp', '吊篮（女儿墙卡钳）'),
      available('suspended-basket', '标准吊篮', 'GB/T 19155-2017'),
    ],
  },
  {
    key: 'mobile-operation-platform',
    title: '移动操作平台',
    isNew: false,
    modules: [planned('mobile-platform-fastener', '移动操作平台(扣件式)')],
  },
  {
    key: 'shaft-operation-platform',
    title: '井道操作平台',
    isNew: false,
    modules: [planned('shaft-platform-fastener', '井道操作平台(扣件式)')],
  },
  {
    key: 'ramp',
    title: '斜道',
    isNew: false,
    modules: [planned('ramp-fastener', '斜道(扣件式)')],
  },
  {
    key: 'operation-and-unloading-platform',
    title: '操作平台、卸料平台',
    isNew: false,
    modules: [
      planned('disk-buckle-operation-platform', '盘扣式操作平台'),
      available('ground-operation-platform', '落地式操作平台（自研）', 'JGJ 80-2016'),
      available('cantilever-operation-platform', '悬挑式操作平台（自研）', 'JGJ 80-2016'),
      available('full-hall-scaffold', '满堂脚手架', 'JGJ 130-2011'),
      planned('full-hall-support', '满堂支撑架'),
    ],
  },
  {
    key: 'construction-elevator-platform',
    title: '施工升降机卸料平台',
    isNew: false,
    modules: [planned('elevator-unloading-fastener', '施工升降机卸料平台(扣件式)')],
  },
  {
    key: 'tool-scaffold',
    title: '工具式脚手架',
    isNew: false,
    modules: [
      available('attached-lifting-scaffold', '导轨式附着升降脚手架', 'JGJ 202-2010'),
      planned('all-steel-attached-lifting', '全钢附着升降脚手架'),
    ],
  },
  {
    key: 'protective-shed',
    title: '防护棚',
    isNew: true,
    modules: [
      planned('protective-shed-fastener', '防护棚(扣件式)'),
      planned('protective-shed-disk-buckle', '防护棚(盘扣式)'),
    ],
  },
  {
    key: 'steel-cantilever-scaffold',
    title: '型钢悬挑脚手架',
    isNew: false,
    modules: [
      available('cantilever-scaffold', '型钢悬挑脚手架（扣件式）', 'JGJ 130-2011'),
      planned('cantilever-main-beam-check', '搁置主梁验算'),
    ],
  },
  {
    key: 'turnbuckle-cantilever-scaffold',
    title: '花篮螺栓悬挑架',
    isNew: false,
    modules: [planned('turnbuckle-fastener', '花篮螺栓悬挑架(扣件式)')],
  },
] satisfies ModuleCatalog['categories']

export const moduleCatalog: ModuleCatalog = {
  regions: [...REGIONS],
  categories,
  modules: categories.flatMap((category) => category.modules),
}
