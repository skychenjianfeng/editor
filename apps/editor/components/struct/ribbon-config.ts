export type RibbonItem = { commandId: string; size?: 'large' | 'small' }

export type RibbonGroup = {
  id: string
  label: string
  items: RibbonItem[]
  /** Fixed small-button columns. Omit for the auto-wrapping layout. */
  columns?: number
}

export type RibbonTab = { id: string; label: string; groups: RibbonGroup[] }

const small = (commandId: string): RibbonItem => ({ commandId, size: 'small' })
const large = (commandId: string): RibbonItem => ({ commandId, size: 'large' })

/**
 * YJK 模型荷载输入的第二级菜单作为建模 Ribbon 的主干：
 * 轴线网格、构件布置、楼板布置、荷载输入、自定义工况、楼层组装、
 * 空间结构、鉴定加固、预制构件拆分。文件、编辑、视图、检查作为通用组。
 */
export const RIBBON_TABS: RibbonTab[] = [
  {
    id: 'file',
    label: '文件',
    groups: [
      {
        id: 'file.project',
        label: '项目',
        items: [large('file.ifcImport')],
      },
    ],
  },
  {
    id: 'model',
    label: '模型',
    groups: [
      {
        id: 'model.node',
        label: '节点',
        columns: 8,
        items: [
          small('node.new'),
          small('node.edit'),
          small('node.lock'),
          small('node.alignX'),
          small('node.alignZ'),
          small('grid.formNodes'),
          small('node.merge'),
          small('node.topElevation'),
          small('node.topElevationSingle'),
          small('node.topElevationTwo'),
          small('node.topElevationThree'),
          small('support.pinned'),
          small('support.fixed'),
          small('support.roller'),
          small('support.free'),
          small('node.down'),
        ],
      },
      {
        id: 'model.grid',
        label: '轴线网格',
        columns: 8,
        items: [
          small('grid.ortho'),
          small('grid.linear'),
          small('grid.arc'),
          small('grid.radialGrid'),
          small('grid.rectangle'),
          small('grid.skew'),
          small('grid.aux'),
          small('grid.name'),
          small('grid.dimensions'),
          small('grid.clean'),
          small('grid.edit'),
          small('grid.editScope'),
          small('grid.transform'),
          small('grid.extend'),
          small('grid.merge'),
          small('grid.trim'),
        ],
      },
      {
        id: 'model.members',
        label: '构件布置',
        columns: 10,
        items: [
          small('member.beam'),
          small('member.column'),
          small('member.brace'),
          small('member.truss'),
          small('member.edit'),
          small('member.alongAxis'),
          small('member.wall'),
          small('member.partition'),
          small('member.inclinedWall'),
          small('member.wallOpening'),
          small('member.secondaryBeam'),
          small('member.cantilever'),
          small('member.eave'),
          small('member.purlin'),
          small('member.girt'),
          small('member.antiWind'),
          small('member.haunch'),
          small('member.singleTension'),
          small('member.eccentricAlign'),
          small('member.viewEdit'),
        ],
      },
      {
        id: 'model.placement',
        label: '布置方式',
        items: [
          small('member.placementPoint'),
          small('member.placementAxis'),
          small('member.placementEnclosure'),
          small('member.placementWindow'),
          small('member.placementContinuous'),
          small('member.placementLayerBeam'),
          small('member.placementPickParams'),
          small('member.placementPreview'),
        ],
      },
      {
        id: 'model.section',
        label: '截面定义',
        items: [
          small('member.sectionAdd'),
          small('member.sectionModify'),
          small('member.sectionDelete'),
          small('member.sectionDisplay'),
          small('member.sectionClean'),
          small('member.sectionSort'),
          small('member.sectionCurrent'),
          small('member.sectionDedupe'),
          small('member.sectionColor'),
        ],
      },
      {
        id: 'model.params',
        label: '布置参数',
        items: [
          small('member.offsetX'),
          small('member.offsetY'),
          small('member.rotation'),
          small('member.baseElevation'),
          small('member.topElevation1'),
          small('member.topElevation2'),
          small('member.takeAxisAngle'),
          small('member.variableEdge'),
        ],
      },
      {
        id: 'model.edit',
        label: '编辑',
        items: [
          small('edit.copy'),
          small('edit.move'),
          small('edit.rotate'),
          small('edit.mirror'),
          small('edit.array'),
          small('edit.offset'),
          small('edit.extend'),
          small('edit.trim'),
          small('edit.break'),
          small('edit.join'),
          small('edit.align'),
          small('edit.delete'),
          small('edit.hide'),
          small('edit.show'),
        ],
      },
      {
        id: 'model.view',
        label: '视图',
        items: [
          small('view.top'),
          small('view.front'),
          small('view.left'),
          small('view.iso'),
          small('view.rotate'),
          small('view.fit'),
          small('view.window'),
          small('view.restore'),
          small('view.wireframe'),
          small('view.shaded'),
          small('view.labels'),
          small('view.textUp'),
          small('view.textDown'),
          small('view.crop'),
          small('view.cropRestore'),
        ],
      },
      {
        id: 'model.tools',
        label: '检查与工具',
        items: [
          small('analysis.check'),
          small('analysis.calcCheck'),
          small('analysis.overlimit'),
          small('model.compare'),
          small('model.quantity'),
          small('tool.commands'),
          small('help.shortcuts'),
          small('query.measure'),
        ],
      },
    ],
  },
  {
    id: 'assembly',
    label: '组装',
    groups: [
      {
        id: 'assembly.slab',
        label: '楼板布置',
        items: [
          small('slab.generate'),
          small('slab.cast'),
          small('slab.polygon'),
          small('slab.hollow'),
          small('slab.profiled'),
          small('slab.composite'),
          small('slab.capital'),
          small('slab.flat'),
          small('slab.opening'),
          small('slab.openingCircle'),
          small('slab.query'),
        ],
      },
      {
        id: 'assembly.floors',
        label: '楼层组装',
        items: [
          small('level.params'),
          small('floor.standard'),
          small('floor.assemble'),
          small('floor.single'),
          small('floor.project'),
          small('floor.auto'),
          small('floor.deleteStandard'),
          small('floor.insertStandard'),
          small('floor.edit'),
          small('floor.merge'),
        ],
      },
      {
        id: 'assembly.space',
        label: '空间结构',
        items: [
          small('space.axis'),
          small('space.member'),
          small('space.load'),
          small('space.workPlane'),
          small('space.toFloor'),
          small('space.skinLoad'),
          small('space.importCadGrid'),
          small('io.ifc'),
        ],
      },
      {
        id: 'assembly.appraisal',
        label: '鉴定与预制',
        items: [
          small('param.appraisal'),
          small('param.prefab'),
          small('prefab.slab'),
          small('prefab.stair'),
          small('prefab.wall'),
        ],
      },
    ],
  },
  {
    id: 'load',
    label: '荷载',
    groups: [
      {
        id: 'load.input',
        label: '荷载输入',
        items: [
          small('load.dead'),
          small('load.live'),
          small('load.wind'),
          small('load.snow'),
          small('load.crane'),
          small('load.moving'),
          small('load.civilDefense'),
          small('load.point'),
          small('load.line'),
          small('load.area'),
          small('load.case'),
          small('load.combinations'),
          small('load.show'),
          small('load.skin'),
        ],
      },
    ],
  },
  {
    id: 'analysis',
    label: '分析',
    groups: [
      {
        id: 'analysis.prepare',
        label: '检查与生成',
        items: [
          small('analysis.assemble'),
          small('analysis.check'),
          small('analysis.calcCheck'),
          small('analysis.generate'),
          small('analysis.overlimit'),
        ],
      },
      {
        id: 'analysis.solve',
        label: '求解',
        items: [large('analysis.run'), small('analysis.modal'), small('analysis.buckling')],
      },
    ],
  },
  {
    id: 'result',
    label: '结果',
    groups: [
      {
        id: 'result.graphics',
        label: '图形结果',
        items: [
          large('result.deform'),
          large('result.moment'),
          small('result.shear'),
          small('result.axial'),
        ],
      },
      {
        id: 'result.checks',
        label: '指标',
        items: [small('result.ratio'), small('result.reaction')],
      },
      {
        id: 'result.output',
        label: '输出',
        items: [small('result.table')],
      },
    ],
  },
  {
    id: 'drawing',
    label: '施工图',
    groups: [
      {
        id: 'drawing.layout',
        label: '布置',
        items: [large('draw.sheet'), large('draw.elevation'), small('draw.detail')],
      },
      {
        id: 'drawing.output',
        label: '输出',
        items: [small('draw.bom'), small('draw.dwg')],
      },
    ],
  },
]

export const RIBBON_CONTEXT_TAB: RibbonTab = {
  id: 'context.beam',
  label: '梁',
  groups: [
    {
      id: 'context.beam.actions',
      label: '梁',
      items: [
        large('member.beam'),
        small('load.line'),
        small('node.release'),
        small('edit.delete'),
      ],
    },
  ],
}
