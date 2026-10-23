'use client'

import {
  type AnyNodeId,
  resolveStructuralSlabTopElevation,
  runAsSingleSceneHistoryStep,
  type StructuralDimension,
  StructuralNode,
  structuralSlabNetArea,
} from '@pascal-app/core'
import {
  type CommandAction,
  executeCommandAction,
  resolveCommandAction,
  resolveCommandUnavailableReason,
  runRedo,
  runUndo,
  useCommandPalette,
  useCommandRegistry,
  useEditor,
  useFloorplanMode,
  useScene,
  useStructPreferences,
  useViewer,
} from '@pascal-app/editor'
import { collectStructuralGridAxes, collectStructuralGridIntersections } from '@pascal-app/nodes'
import {
  Activity,
  Anchor,
  ArrowDownToLine,
  Box,
  Boxes,
  Columns3,
  Compass,
  Component,
  Copy,
  Download,
  Eraser,
  Eye,
  EyeOff,
  FileSpreadsheet,
  Frame,
  Gauge,
  GitCompare,
  Grid2x2,
  Grid3x3,
  Keyboard,
  Layers,
  Link2,
  List,
  Lock,
  Maximize2,
  MirrorRectangular,
  Move,
  MoveDiagonal,
  MoveHorizontal,
  MoveVertical,
  Play,
  Redo2,
  RotateCcw,
  Ruler,
  Scan,
  Scissors,
  Sigma,
  Square,
  SquarePen,
  Table2,
  Tags,
  Target,
  Trash,
  Triangle,
  Undo2,
  Unlink,
  Upload,
  Weight,
  Wind,
} from 'lucide-react'
import { useEffect } from 'react'
import type { AnalysisResultViewMode } from '@/lib/analysis-jobs/client'
import { runAxisCleanup } from '@/lib/struct/axis-cleaning'
import { generateAxisDimensions } from '@/lib/struct/axis-dimensions'
import { exportAxesToDxfDownload, importAxesFromDxf, pickDxfFile } from '@/lib/struct/axis-dxf'
import { splitAxisAtIntersections } from '@/lib/struct/axis-split'
import { runAxisExtend, runAxisMerge, runAxisTrim } from '@/lib/struct/axis-transform'
import { addMemberLineLoad } from '@/lib/struct/load-editing'
import { deleteMembers, setMemberReleases } from '@/lib/struct/member-editing'
import {
  assertMembersUnlocked,
  hasLockedMembers,
  LOCKED_MEMBER_MESSAGE,
} from '@/lib/struct/member-lock-guard'
import {
  alignNodes,
  descendNodesToLowerLevel,
  mergeStructuralNodes,
  setNodesLocked,
} from '@/lib/struct/node-editing'
import { splitNumberArgs } from '@/lib/struct/parser'
import { readStructProjectMetaFromNodes } from '@/lib/struct/project-store'
import { generateRoomSlabs } from '@/lib/struct/slab-layout'
import { hideStructuralObjects, showStructuralObjects } from '@/lib/struct/visibility-commands'
import { addStructuralWallOpening } from '@/lib/struct/wall-editing'
import { YJK_PLANNED_COMMANDS } from './command-defs-yjk'
import { type AxisGridMode, useAxisGridStore } from './model/axis-grid-store'
import {
  hasSelectedLineLoadMember,
  selectedLineLoadMembers,
  selectedStructuralMemberIds,
} from './struct-selection'
import {
  type MemberType,
  toBeamPlacementConfig,
  toColumnPlacementConfig,
  toNodePlacementConfig,
  useStructStore,
} from './struct-store'
import { runStructViewCommand } from './view-commands'

const DEFAULT_SECTION = 'H400×200×8×13'

const PLANNED_STRUCT_COMMAND_IDS = new Set([
  'analysis.generate',
  'analysis.modal',
  'analysis.buckling',
  'draw.elevation',
  'draw.detail',
  'draw.bom',
  'draw.dwg',
  'load.dead',
  'load.live',
  'load.wind',
  'load.seismic',
  'load.point',
  'load.area',
  'view.labels',
])

function asPlannedCommand(action: CommandAction): CommandAction {
  return {
    ...action,
    badge: '规划中',
    usage: action.usage?.startsWith('规划中')
      ? action.usage
      : `规划中：${action.usage ?? resolveLabel(action.label)}`,
    when: () => false,
    execute: () => {
      throw new Error(`${resolveLabel(action.label)} 尚未实现`)
    },
    executeWithArgs: undefined,
  }
}

const MEMBER_LABEL: Record<MemberType, string> = {
  beam: '梁',
  column: '柱',
  truss: '桁架',
  brace: '支撑',
}

function resolveLabel(label: CommandAction['label']): string {
  return typeof label === 'function' ? label() : label
}

const FIRST_BATCH_ALIASES: Readonly<Record<string, readonly string[]>> = {
  'tool.commands': ['cmd', 'commands', '_commands'],
  'view.top': ['plan', '_plan'],
  'view.front': ['front'],
  'view.left': ['left'],
  'view.iso': ['iso'],
  'view.fit': ['fit'],
  'edit.hide': ['hide'],
  'edit.show': ['show'],
  'query.measure': ['measure', 'm'],
}

function addFirstBatchAliases(action: CommandAction): CommandAction {
  const aliases = FIRST_BATCH_ALIASES[action.id]
  if (!aliases) return action
  const existing = action.aliases ?? []
  return {
    ...action,
    aliases: [...existing, ...aliases.filter((alias) => !existing.includes(alias))],
  }
}

export function resolveUnavailableReason(command: CommandAction | undefined): string {
  if (!command) return '命令未注册'
  return resolveCommandUnavailableReason(command) ?? '当前选择或工程状态不满足执行条件'
}

function clearStructEditorContext() {
  useStructStore.getState().closeAllPanels()
  useAxisGridStore.getState().setOpen(false)
  useEditor.getState().setTool(null)
}

function addExecutionContext(action: CommandAction): CommandAction {
  if (action.preserveEditorContext === true) return action
  const existing = action.beforeExecute
  return {
    ...action,
    beforeExecute: () => {
      existing?.()
      clearStructEditorContext()
    },
  }
}

function addMember(type: MemberType, length: number, section = DEFAULT_SECTION) {
  const store = useStructStore.getState()
  const member = store.addMember({ type, length, section })
  store.selectMember(member.id)
  store.pushLog(`${MEMBER_LABEL[type]} ${member.id} 已创建：L=${length} mm，截面 ${section}`, 'ok')
  return member
}

function addLoad(name: string, value = 4.2) {
  const store = useStructStore.getState()
  const load = store.addLoad({ case: name, value })
  store.pushLog(`荷载 ${load.id} 已施加：${name} = ${value} kN/m`, 'ok')
  return load
}

function addSelectedUniformLineLoad(value: number) {
  const scene = useScene.getState()
  const selection = useViewer.getState().selection.selectedIds
  const member = selectedLineLoadMembers(scene.nodes, selection)[0]
  if (!member) throw new Error('请先选择梁或墙')
  assertMembersUnlocked(scene.nodes, [member.id])
  const meta = readStructProjectMetaFromNodes(scene.nodes)
  const caseId = meta?.loadCases[0]?.id
  if (!caseId) throw new Error('当前工程没有可用荷载工况')
  const load = addMemberLineLoad(member.id, {
    caseId,
    type: 'uniform',
    direction: 'y',
    coordinateSystem: 'global',
    qStart: value,
    qEnd: value,
    startRatio: 0,
    endRatio: 1,
  })
  useStructStore.getState().pushLog(`线荷载 ${load.id} 已施加：${value} kN/m`, 'ok')
  return load
}

function openAxisGrid(mode: AxisGridMode) {
  const levelId = useViewer.getState().selection.levelId
  if (!levelId) {
    logResult('轴网', '请先选择楼层')
    return
  }
  const toolMode =
    mode === 'arc' ? 'arc' : mode === 'ortho' || mode === 'rectangle' ? 'rectangle' : 'line'
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useEditor.getState().setToolDefaults('structural-grid', { mode: toolMode })
  useEditor.getState().setTool('structural-grid')
  useAxisGridStore.getState().openMode(mode, levelId)
}

function openStructuralGridTool(mode: 'line' | 'rectangle' | 'arc') {
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useEditor.getState().setToolDefaults('structural-grid', { mode })
  useEditor.getState().setTool('structural-grid')
}

function openNodePlaceDialog() {
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useStructStore.getState().openNodePlaceDialog()
  const state = useStructStore.getState()
  useEditor.getState().setToolDefaults('structural-node', {
    ...toNodePlacementConfig({
      labelPrefix: state.nodeLabelPrefix,
      labelStart: state.nodeLabelStart,
      elevationOffset: state.nodeElevationOffset,
      markerRadiusMm: state.nodeMarkerRadiusMm,
      support: state.nodeSupport,
      showLabel: state.nodeShowLabel,
      locked: state.nodeLocked,
    }),
  })
  useEditor.getState().setTool('structural-node')
  logResult('节点布置', '已进入布置，可直接在画布点选')
}

function openNodeElevation(mode: 'single' | 'two' | 'three') {
  useStructStore.getState().openNodeElevationDialog(mode)
  logResult(
    '上节点高',
    mode === 'single'
      ? '已打开单点模式'
      : mode === 'two'
        ? '已打开两点坡度模式'
        : '已打开三点斜面模式',
  )
}

function openStructuralMemberTool(
  memberType: 'beam' | 'column' | 'brace' | 'truss' | 'wall',
  extraDefaults: Record<string, unknown> = {},
) {
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useEditor.getState().setToolDefaults('structural-member', { memberType, ...extraDefaults })
  useEditor.getState().setTool('structural-member')
}

function openStructuralWallTool(wallKind: 'structural' | 'partition' | 'infill', inclined = false) {
  useEditor.getState().setToolDefaults('structural-member', {
    memberType: 'wall',
    wallConfig: {
      wallKind,
      thickness: wallKind === 'partition' ? 0.12 : 0.2,
      wallBaseElevation: null,
      wallTopStart: null,
      wallTopEnd: null,
      inclined,
    },
  })
  useStructStore.getState().openWallDialog()
}

function addSelectedWallOpening() {
  const scene = useScene.getState()
  const wall = (useViewer.getState().selection.selectedIds as AnyNodeId[])
    .map((id) => scene.nodes[id])
    .find((node) => node?.type === 'structural-member' && node.memberType === 'wall')
  if (wall?.type !== 'structural-member') {
    logResult('墙洞', '请先选择一面结构墙')
    return
  }
  try {
    const opening = addStructuralWallOpening(wall.id)
    useViewer.getState().setSelection({ selectedIds: [wall.id] })
    logResult(
      '墙洞',
      `已新增矩形洞口 ${opening.width.toFixed(2)}×${opening.height.toFixed(2)} m，可在墙体属性中修改`,
    )
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '新增墙洞失败'
    useStructStore.getState().pushLog(`墙洞失败：${message}`, 'error')
  }
}

function openStructuralSlabTool(mode: 'rectangle' | 'polygon') {
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useEditor.getState().setToolDefaults('structural-slab', { mode })
  useEditor.getState().setTool('structural-slab')
}

function openStructuralSlabOpening(shape: 'rectangle' | 'circle') {
  const selectedSlab = (useViewer.getState().selection.selectedIds as AnyNodeId[]).find(
    (id) => useScene.getState().nodes[id]?.type === 'structural-slab',
  )
  if (!selectedSlab) {
    logResult('板洞', '请先选择一块结构板')
    return
  }
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useEditor.getState().setToolDefaults('structural-slab', {
    mode: 'opening',
    holeShape: shape,
    slabId: selectedSlab,
  })
  useEditor.getState().setTool('structural-slab')
}

function generateSlabsFromRooms() {
  const levelId = useViewer.getState().selection.levelId
  if (!levelId) {
    logResult('生成楼板', '请先选择楼层')
    return
  }
  const result = generateRoomSlabs(levelId)
  if (result.roomsDetected === 0) {
    logResult('生成楼板', '当前楼层没有由墙或主梁围成的闭合房间')
    return
  }
  if (result.slabIds[0]) {
    useViewer.getState().setSelection({ selectedIds: [result.slabIds[0] as AnyNodeId] })
  }
  logResult(
    '生成楼板',
    result.created > 0 || result.updated > 0
      ? `识别 ${result.roomsDetected} 个房间，生成 ${result.created} 块板、更新 ${result.updated} 块板（${result.totalArea.toFixed(2)} m²）${result.skippedManual > 0 ? `，保留 ${result.skippedManual} 块手工板` : ''}`
      : `识别 ${result.roomsDetected} 个房间，均已有手工板覆盖`,
  )
}

function querySelectedSlab() {
  const scene = useScene.getState()
  const slab = (useViewer.getState().selection.selectedIds as AnyNodeId[])
    .map((id) => scene.nodes[id])
    .find((node) => node?.type === 'structural-slab')
  if (slab?.type !== 'structural-slab') {
    logResult('楼板查询', '请先选择一块结构板')
    return
  }
  const level = slab.parentId ? scene.nodes[slab.parentId as AnyNodeId] : undefined
  const top = resolveStructuralSlabTopElevation(slab, level?.type === 'level' ? level : null)
  const area = structuralSlabNetArea(slab.polygon, slab.holes)
  const transferLabel = {
    auto: '自动',
    opposite: '对边',
    trapezoid: '梯形三角',
    perimeter: '周边',
  }[slab.loadTransfer]
  logResult(
    '楼板查询',
    `${slab.thickness <= 1e-9 ? '无板仅导荷' : `板厚 ${Math.round(slab.thickness * 1000)} mm`} · 材料 ${slab.material} · 板顶 ${top.toFixed(3)} m · qD ${slab.deadLoad.toFixed(2)} / qL ${slab.liveLoad.toFixed(2)} kN/m²（${slab.selfWeight ? '计' : '不计'}自重，${transferLabel}导荷） · 净面积 ${area.toFixed(2)} m² · ${slab.holes.length} 个洞口${slab.autoGenerated ? ' · 房间自动生成' : ' · 手工板'}`,
  )
}

function setStructuralSupport(support: 'free' | 'pinned' | 'fixed' | 'roller') {
  const scene = useScene.getState()
  const ids = (useViewer.getState().selection.selectedIds as AnyNodeId[]).filter(
    (id) => scene.nodes[id]?.type === 'structural-node',
  ) as AnyNodeId[]
  if (ids.length === 0) {
    useStructStore.getState().pushLog('请先选择一个结构节点', 'error')
    return
  }
  const targets = ids
    .map((id) => scene.nodes[id])
    .filter((node): node is StructuralNode => node?.type === 'structural-node' && !node.locked)
  if (targets.length === 0) {
    logResult('节点支座', '所选节点均已锁定')
    return
  }
  runAsSingleSceneHistoryStep(useScene, () => {
    useScene.getState().applyNodeChanges({
      update: targets.map((node) => ({ id: node.id, data: { support } })),
    })
  })
  logResult(
    '节点支座',
    targets.length === 1
      ? `${targets[0]!.label} → ${support}`
      : `${targets.length} 个节点 → ${support}`,
  )
}

function openNodeEdit() {
  useStructStore.getState().openNodeEdit()
  logResult('节点编辑', '已打开节点编辑表')
}

function mergeNodesWithTolerance() {
  const levelId = useViewer.getState().selection.levelId
  const toleranceMm = useStructPreferences.getState().nodeMergeToleranceMm
  const selected = (useViewer.getState().selection.selectedIds as AnyNodeId[]).filter(
    (id) => useScene.getState().nodes[id]?.type === 'structural-node',
  )
  const count = mergeStructuralNodes(
    levelId,
    toleranceMm / 1000,
    selected.length >= 2 ? selected : undefined,
  )
  logResult(
    '节点',
    count > 0
      ? `已按 ${toleranceMm} mm 容差归并 ${count} 个重复节点`
      : `按 ${toleranceMm} mm 容差没有重复节点`,
  )
}

function descendNodes() {
  const levelId = useViewer.getState().selection.levelId
  const ids = (useViewer.getState().selection.selectedIds as AnyNodeId[]).filter(
    (id) => useScene.getState().nodes[id]?.type === 'structural-node',
  )
  const result = descendNodesToLowerLevel(levelId, ids.length > 0 ? ids : undefined)
  if (!result.levelId) {
    logResult('节点下传', '当前楼层已是最底层，无法下传')
    return
  }
  logResult(
    '节点下传',
    `已下传 ${result.created} 个节点，复用 ${result.reused} 个下层节点，拆分 ${result.split} 根梁/墙${
      result.skipped > 0 ? `，跳过 ${result.skipped} 个锁定对象` : ''
    }`,
  )
}

function alignSelection(axis: 'x' | 'z') {
  const ids = (useViewer.getState().selection.selectedIds as AnyNodeId[]).filter(
    (id) => useScene.getState().nodes[id]?.type === 'structural-node',
  )
  if (ids.length < 2) {
    logResult('节点对齐', '请选择至少两个结构节点')
    return
  }
  const count = alignNodes(ids, axis)
  logResult(
    '节点对齐',
    count > 0 ? `已按 ${axis.toUpperCase()} 对齐 ${count + 1} 个节点` : '所选节点已经对齐',
  )
}

function selectedMemberIds(): AnyNodeId[] {
  const scene = useScene.getState()
  return (useViewer.getState().selection.selectedIds as AnyNodeId[]).filter(
    (id) => scene.nodes[id]?.type === 'structural-member',
  )
}

function selectedMembers() {
  const nodes = useScene.getState().nodes
  return selectedMemberIds().flatMap((id) => {
    const node = nodes[id]
    return node?.type === 'structural-member' ? [node] : []
  })
}

function openMemberEdit() {
  const scene = useScene.getState()
  assertMembersUnlocked(
    scene.nodes,
    selectedStructuralMemberIds(
      scene.nodes,
      useViewer.getState().selection.selectedIds as AnyNodeId[],
    ),
  )
  useStructStore.getState().openMemberEdit()
  logResult('构件编辑', '已打开构件编辑表')
}

function takeMemberAxisAngle() {
  const members = selectedMembers()
  if (members.length === 0) throw new Error('未选择结构构件')
  const member = members.find((candidate) => !candidate.locked)
  if (!member) throw new Error('所选结构构件已锁定')
  useStructStore.getState().startMemberAxisAnglePick(member.id)
  logResult('取轴线角', '请在画布选择一根轴线')
}

function openSelectedMemberEdit(action: string, allowLockedSource = false) {
  const scene = useScene.getState()
  const ids = selectedStructuralMemberIds(
    scene.nodes,
    useViewer.getState().selection.selectedIds as AnyNodeId[],
  )
  if (ids.length === 0) {
    useStructStore.getState().pushLog(`${action}失败：未选择结构构件`, 'error')
    return
  }
  if (!allowLockedSource) assertMembersUnlocked(scene.nodes, ids)
  useStructStore.getState().openMemberEdit()
  logResult(action, `已打开构件编辑，目标 ${ids.length} 根构件`)
}

function deleteSelectedMembers() {
  const sceneSelection = useViewer.getState().selection.selectedIds as AnyNodeId[]
  const scene = useScene.getState()
  const ids = selectedStructuralMemberIds(scene.nodes, sceneSelection)
  if (ids.length === 0) {
    useStructStore.getState().pushLog('删除失败：未选择结构构件', 'error')
    return
  }
  assertMembersUnlocked(scene.nodes, ids)
  const deleting = new Set(ids)
  deleteMembers(ids)
  useViewer.getState().setSelection({
    selectedIds: sceneSelection.filter((id) => !deleting.has(id)),
  })
  logResult('删除', `已删除 ${ids.length} 根构件`)
}

function openMemberLayout() {
  useStructStore.getState().openMemberLayout()
  logResult('沿轴布置', '已打开沿轴布置面板')
}

function openColumnDialog() {
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useStructStore.getState().openColumnDialog()
  const state = useStructStore.getState()
  const section =
    state.columnSections.find((item) => item.id === state.activeColumnSectionId) ??
    state.columnSections[0]
  if (!section) return
  useEditor.getState().setToolDefaults('structural-member', {
    memberType: 'column',
    columnConfig: toColumnPlacementConfig(section, {
      offsetX: state.columnOffsetX,
      offsetZ: state.columnOffsetZ,
      rotation: state.columnRotation,
      baseOffset: state.columnBaseOffset,
    }),
  })
  useEditor.getState().setTool('structural-member')
  logResult('柱布置', '已进入布置，可直接在画布点选')
}

function openBeamDialog() {
  useFloorplanMode.getState().setMode('expert')
  useEditor.getState().setViewMode('2d')
  useStructStore.getState().openBeamDialog()
  const state = useStructStore.getState()
  const section =
    state.beamSections.find((item) => item.id === state.activeBeamSectionId) ??
    state.beamSections[0]
  if (!section) return
  useEditor.getState().setToolDefaults('structural-member', {
    memberType: 'beam',
    beamConfig: toBeamPlacementConfig(section, {
      offsetZ: state.beamOffsetZ,
      topOffsetStart: state.beamTopOffsetStart,
      topOffsetEnd: state.beamTopOffsetEnd,
      rotation: state.beamRotation,
    }),
  })
  useEditor.getState().setTool('structural-member')
  logResult('梁布置', '已进入布置，可直接在画布点选')
}

function openLevelParams() {
  useStructStore.getState().openLevelParams()
  logResult('楼层参数', '已打开楼层参数面板')
}

function cleanSurfaceNodes() {
  const scene = useScene.getState()
  const levelId = useViewer.getState().selection.levelId
  const ids = Object.values(scene.nodes)
    .filter(
      (node) =>
        ['slab', 'ceiling', 'roof', 'zone'].includes(node.type) &&
        (!levelId || node.parentId === levelId),
    )
    .map((node) => node.id)
  if (ids.length === 0) {
    logResult('清理面对象', '当前楼层没有板/天花板/屋面/房间对象')
    return
  }
  runAsSingleSceneHistoryStep(useScene, () => {
    for (const id of ids) useScene.getState().deleteNode(id)
  })
  logResult('清理面对象', `已删除 ${ids.length} 个板/天花板/屋面/房间对象`)
}

function openAnalysisModel() {
  useStructStore.getState().openAnalysisModel()
  logResult('分析模型', '已组装模型并打开前处理检查')
}

const NO_ANALYSIS_RESULT = '尚无分析结果；请先完成真实分析作业并取得 ResultSet'

function hasAnalysisResult(): boolean {
  return useStructStore.getState().analysisResultSetId !== null
}

function openAnalysisResult(view: AnalysisResultViewMode) {
  const store = useStructStore.getState()
  if (!store.analysisResultSetId) throw new Error(NO_ANALYSIS_RESULT)
  store.openAnalysisResults(view)
}

function releaseMemberEnds(release: 'pinned' | 'rigid') {
  const ids = selectedMemberIds()
  if (ids.length === 0) {
    logResult('杆端释放', '请先选择结构构件')
    return
  }
  const count = setMemberReleases(ids, release)
  logResult('杆端释放', `${count} 根构件 → ${release === 'pinned' ? '铰接' : '刚接'}`)
}

function toggleNodeLock() {
  const scene = useScene.getState()
  const ids = (useViewer.getState().selection.selectedIds as AnyNodeId[]).filter(
    (id) => scene.nodes[id]?.type === 'structural-node',
  ) as AnyNodeId[]
  if (ids.length === 0) {
    logResult('节点锁定', '请先选择结构节点')
    return
  }
  const targets = ids
    .map((id) => scene.nodes[id])
    .filter((node): node is StructuralNode => node?.type === 'structural-node')
  const lock = !targets.every((node) => node.locked)
  const count = setNodesLocked(ids, lock)
  logResult('节点锁定', `${lock ? '锁定' : '解锁'} ${count} 个节点`)
}

function formStructuralIntersections() {
  const scene = useScene.getState()
  const levelId = useViewer.getState().selection.levelId
  const axes = collectStructuralGridAxes(scene.nodes, levelId)
  const existingNodes = Object.values(scene.nodes).filter(
    (node): node is StructuralNode =>
      node.type === 'structural-node' && (!levelId || node.parentId === levelId),
  )
  const ops = collectStructuralGridIntersections(axes)
    .filter(
      (intersection) =>
        !existingNodes.some(
          (node) =>
            Math.hypot(
              node.position[0] - intersection.point[0],
              node.position[2] - intersection.point[1],
            ) <= 0.05,
        ),
    )
    .map((intersection) =>
      StructuralNode.parse({
        position: [intersection.point[0], 0, intersection.point[1]],
        label: intersection.reference || 'N',
        metadata: { source: 'structweb-axis-intersection' },
      }),
    )
  if (ops.length === 0) {
    logResult('节点', '没有新的轴线交点需要生成')
    return
  }
  runAsSingleSceneHistoryStep(useScene, () => {
    scene.createNodes(ops.map((node) => ({ node, parentId: levelId as AnyNodeId })))
  })
  logResult('节点', `已为 ${ops.length} 个轴线交点生成结构节点`)
}

function cleanStructuralGrid() {
  const levelId = useViewer.getState().selection.levelId
  if (!levelId) {
    logResult('清理网点', '请先选择楼层')
    return
  }
  let result: ReturnType<typeof runAxisCleanup>
  try {
    result = runAxisCleanup([levelId])
  } catch (reason) {
    logResult('清理网点', `清理失败：${reason instanceof Error ? reason.message : String(reason)}`)
    return
  }
  if (result.removedAxes === 0 && result.removedNodes === 0) {
    logResult('清理网点', '当前楼层没有需要清理的零长轴线、重复轴线或失效节点')
    return
  }
  logResult(
    '清理网点',
    `删除 ${result.removedAxes} 条轴线（零长度 ${result.degenerateAxes}、重复 ${result.duplicateAxes}），清理 ${result.removedNodes} 个失效节点`,
  )
}

function openAxisEdit() {
  useStructStore.getState().openAxisEdit()
  logResult('轴网编辑', '已打开当前楼层轴网编辑表')
}

function openAxisNaming() {
  useStructStore.getState().openAxisNaming()
  logResult('轴线命名', '已打开轴线命名面板')
}

function openAxisTransform(mode: 'move' | 'stitch' = 'move') {
  useStructStore.getState().openAxisTransform(mode)
  logResult('轴线变换', mode === 'stitch' ? '已打开轴网拼接面板' : '已打开轴线变换面板')
}

function targetAxisIds(): AnyNodeId[] {
  const scene = useScene.getState()
  const levelId = useViewer.getState().selection.levelId
  const selected = useViewer
    .getState()
    .selection.selectedIds.filter(
      (id) => scene.nodes[id as AnyNodeId]?.type === 'structural-grid',
    ) as AnyNodeId[]
  if (selected.length > 0) return selected
  return collectStructuralGridAxes(scene.nodes, levelId).map((axis) => axis.id)
}

function extendAxes() {
  const ids = targetAxisIds()
  if (ids.length === 0) {
    logResult('轴线延伸', '当前楼层没有轴线')
    return
  }
  const result = runAxisExtend(ids)
  if (result.blocked > 0) {
    logResult('轴线延伸', '相邻构件、节点或板边界已锁定，已阻止延伸')
    return
  }
  if (result.extended === 0) {
    logResult('轴线延伸', '所选轴线两端没有可延伸到的相邻轴线')
    return
  }
  logResult('轴线延伸', `已延伸 ${result.extended} 条轴线到相邻轴线`)
}

function mergeAxes() {
  const ids = targetAxisIds()
  if (ids.length < 2) {
    logResult('轴线合并', '请选择至少两条共线相接的轴线')
    return
  }
  const result = runAxisMerge(ids)
  if (result.blocked > 0) {
    logResult('轴线合并', '所选共线轴线存在几何间隙，已阻止桥接合并')
    return
  }
  if (result.merged === 0) {
    logResult('轴线合并', '所选轴线中没有共线可合并的分段')
    return
  }
  logResult('轴线合并', `合并 ${result.merged} 组轴线，删除 ${result.removed} 条重复分段`)
}

function trimAxes() {
  const ids = targetAxisIds()
  if (ids.length === 0) {
    logResult('轴线修剪', '当前楼层没有轴线')
    return
  }
  const result = runAxisTrim(ids)
  if (result.blocked > 0) {
    logResult('轴线修剪', '相邻构件、节点或板边界已锁定，已阻止修剪')
    return
  }
  if (result.trimmed === 0) {
    logResult('轴线修剪', '所选轴线没有可修剪的内部交点（或已锁定）')
    return
  }
  logResult('轴线修剪', `已修剪 ${result.trimmed} 条轴线到最近交点`)
}

function createAxisDimensions() {
  const levelId = useViewer.getState().selection.levelId
  if (!levelId) {
    logResult('尺寸标注', '请先选择楼层')
    return
  }
  const result = generateAxisDimensions(levelId)
  if (result.created === 0) {
    logResult('尺寸标注', '轴线不足，至少需要两个方向的定位轴线')
    return
  }
  logResult('尺寸标注', `已生成 ${result.created} 段第一道/第二道/总尺寸`)
}

function exportAxesDxf() {
  const levelId = useViewer.getState().selection.levelId
  const sceneNodes = useScene.getState().nodes
  const axes = collectStructuralGridAxes(sceneNodes, levelId)
  if (axes.length === 0) {
    logResult('DXF 导出', '当前楼层没有轴线')
    return
  }
  const dimensions = Object.values(sceneNodes).filter(
    (node): node is StructuralDimension =>
      node.type === 'structural-dimension' && (!levelId || node.parentId === levelId),
  )
  const count = exportAxesToDxfDownload(axes, dimensions)
  logResult('DXF 导出', `已导出 ${count} 条轴线、${dimensions.length} 段尺寸到 轴线.dxf`)
}

function importAxesDxf() {
  const levelId = useViewer.getState().selection.levelId
  if (!levelId) {
    logResult('DXF 导入', '请先选择楼层')
    return
  }
  pickDxfFile(async (file) => {
    const text = await file.text()
    const result = importAxesFromDxf(text, levelId)
    logResult(
      'DXF 导入',
      result.imported > 0
        ? `已从 ${file.name} 导入 ${result.imported} 条轴线`
        : `未在 ${file.name} 中发现可导入的 LINE 轴线`,
    )
  })
}

function toggleAxisEditScope() {
  const store = useStructStore.getState()
  store.toggleAxisEditScope()
  const scope = useStructStore.getState().axisEditScope
  store.pushLog(`轴网范围：切换为${scope === 'level' ? '当前楼层' : '全楼'}`, 'ok')
}

function splitSelectedAxis() {
  const selectedId = useViewer.getState().selection.selectedIds[0] as AnyNodeId | undefined
  if (!selectedId) {
    logResult('轴线打断', '请先选择一条轴线')
    return
  }
  const result = splitAxisAtIntersections(selectedId)
  if (!result.ok) {
    logResult(
      '轴线打断',
      result.reason === 'missing' ? '所选对象不是轴线' : '所选轴线没有与其他轴线的交点',
    )
    return
  }
  logResult('轴线打断', `已在交点处打断为 ${result.segments} 段轴线`)
}

function logResult(action: string, detail: string) {
  useStructStore.getState().pushLog(`${action}：${detail}`, 'ok')
}

const EDIT_NEEDS_SELECTION = () =>
  selectedMemberIds().length > 0 &&
  !hasLockedMembers(useScene.getState().nodes, selectedMemberIds())
const EDIT_NEEDS_ANY_MEMBER = () => selectedMemberIds().length > 0
const SCENE_SELECTION = () => useViewer.getState().selection.selectedIds.length > 0
const MEMBER_EDIT_AVAILABLE = () =>
  !hasLockedMembers(useScene.getState().nodes, selectedMemberIds())

function editUnavailableReason(): string {
  if (!EDIT_NEEDS_ANY_MEMBER()) return '请先选择结构构件'
  return LOCKED_MEMBER_MESSAGE
}

const BASE_STRUCT_COMMANDS: CommandAction[] = [
  {
    id: 'file.ifcImport',
    label: '导入 IFC',
    group: '文件',
    icon: <Upload className="h-4 w-4" />,
    keywords: ['ifc', 'import', 'open', '导入', 'BIM'],
    aliases: ['ifc', 'import-ifc'],
    usage: '打开 IFC2X3/IFC4 文件并创建一个新的可编辑 StructWeb 工程',
    execute: () => useStructStore.getState().openIfcImport(),
  },
  {
    id: 'model.compare',
    label: '版本历史 / 工程对比',
    group: '检查与工具',
    icon: <GitCompare className="h-4 w-4" />,
    keywords: ['revision', 'history', 'snapshot', 'compare', '版本', '历史', '对比'],
    usage: '查看云端工程的不可变 revision 历史、比较差异并只读预览历史模型',
    execute: () => useStructStore.getState().openRevisionHistory(),
  },
  // ── 建模 ──────────────────────────────────────────────────────────────────
  {
    id: 'level.params',
    label: '楼层参数',
    group: '组装',
    icon: <Layers className="h-4 w-4" />,
    keywords: ['level', 'height', 'cenggao', '层高', '楼层'],
    usage: '统一设置各楼层的层高与基底标高',
    execute: openLevelParams,
  },
  {
    id: 'scene.cleanSurfaces',
    label: '清理面对象',
    group: '工具',
    icon: <Eraser className="h-4 w-4" />,
    keywords: ['surface', 'slab', 'ceiling', 'roof', '清理', '板', '天花板', '屋面'],
    usage: '删除当前楼层的板/天花板/屋面/房间对象，用于清除误生成的面',
    execute: cleanSurfaceNodes,
  },
  {
    id: 'member.beam',
    label: '梁',
    group: '建模',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['beam', 'liang', '梁', 'member', '构件'],
    aliases: ['b', 'beam', '_beam'],
    usage: '先定义梁截面类型、尺寸、材料与梁顶标高，再在节点/轴线上布置',
    execute: openBeamDialog,
  },
  {
    id: 'member.column',
    label: '柱',
    group: '建模',
    icon: <MoveVertical className="h-4 w-4" />,
    keywords: ['column', 'zhu', '柱', 'member'],
    aliases: ['c', 'column', '_column'],
    usage: '先定义柱截面类型、尺寸、材料与偏心参数，再在节点上逐根布置',
    execute: openColumnDialog,
  },
  {
    id: 'member.sectionAdd',
    label: '新增截面',
    group: '建模',
    icon: <Columns3 className="h-4 w-4" />,
    keywords: ['section', 'add', 'jiamian', '截面', '新增'],
    usage: '打开柱截面定义，新增/复制截面类型、尺寸与材料',
    execute: openColumnDialog,
  },
  {
    id: 'member.sectionModify',
    label: '修改截面',
    group: '建模',
    icon: <Columns3 className="h-4 w-4" />,
    keywords: ['section', 'modify', 'xiugai', '截面', '修改'],
    usage: '打开柱截面定义，修改当前截面的类型、尺寸与材料',
    execute: openColumnDialog,
  },
  {
    id: 'member.offsetX',
    label: '沿轴偏心',
    group: '建模',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['offset', 'eccentric', 'pianxin', '偏心'],
    usage: '打开柱布置参数，设置沿轴偏心与偏轴偏心',
    execute: openColumnDialog,
  },
  {
    id: 'member.offsetY',
    label: '偏轴偏心',
    group: '建模',
    icon: <MoveVertical className="h-4 w-4" />,
    keywords: ['offset', 'eccentric', 'pianxin', '偏心'],
    usage: '打开柱布置参数，设置沿轴偏心与偏轴偏心',
    execute: openColumnDialog,
  },
  {
    id: 'member.rotation',
    label: '轴转角',
    group: '建模',
    icon: <RotateCcw className="h-4 w-4" />,
    keywords: ['rotation', 'angle', 'zhuanjiao', '转角'],
    usage: '打开柱布置参数，设置截面轴转角',
    execute: openColumnDialog,
  },
  {
    id: 'member.baseElevation',
    label: '柱底高',
    group: '建模',
    icon: <ArrowDownToLine className="h-4 w-4" />,
    keywords: ['elevation', 'base', 'zhudigao', '柱底高'],
    usage: '打开柱布置参数，设置柱底相对层底的高度',
    execute: openColumnDialog,
  },
  {
    id: 'member.topElevation1',
    label: '梁顶标高1',
    group: '建模',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['elevation', 'beam', 'liangding', '梁顶标高'],
    usage: '打开梁布置参数，设置梁左端/下端相对层顶的高差',
    execute: openBeamDialog,
  },
  {
    id: 'member.topElevation2',
    label: '梁顶标高2',
    group: '建模',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['elevation', 'beam', 'liangding', '梁顶标高'],
    usage: '打开梁布置参数，设置梁右端/上端相对层顶的高差',
    execute: openBeamDialog,
  },
  {
    id: 'member.truss',
    label: '桁架',
    group: '建模',
    icon: <Triangle className="h-4 w-4" />,
    keywords: ['truss', 'hengjia', '桁架', 'member'],
    aliases: ['t', 'truss'],
    usage: '在 2D 画布两点布置桁架杆件',
    execute: () => openStructuralMemberTool('truss'),
  },
  {
    id: 'member.brace',
    label: '支撑',
    group: '建模',
    icon: <MoveDiagonal className="h-4 w-4" />,
    keywords: ['brace', 'zhicheng', '支撑', 'member'],
    aliases: ['br', 'brace'],
    usage: '在 2D 画布两点布置支撑',
    execute: () => openStructuralMemberTool('brace'),
  },
  {
    id: 'member.edit',
    label: '构件编辑',
    group: '建模',
    icon: <Table2 className="h-4 w-4" />,
    keywords: ['member', 'edit', 'goujian', '构件', '编辑', '截面', '释放'],
    usage: '打开构件编辑表：类型、截面、材料、杆端释放、批量修改与统计',
    when: MEMBER_EDIT_AVAILABLE,
    whenUnavailable: () => LOCKED_MEMBER_MESSAGE,
    execute: openMemberEdit,
  },
  {
    id: 'member.takeAxisAngle',
    label: '取轴线角',
    group: '构件编辑',
    keywords: ['take', 'axis', 'angle', 'quxian', '取轴线角'],
    when: () => selectedMembers().some((member) => !member.locked),
    whenUnavailable: () => {
      const members = selectedMembers()
      if (members.length === 0) return '未选择结构构件'
      if (members.every((member) => member.locked)) return '所选结构构件已锁定'
      return '请选择未锁定的结构构件'
    },
    execute: takeMemberAxisAngle,
  },
  {
    id: 'member.alongAxis',
    label: '沿轴布置',
    group: '建模',
    icon: <Grid2x2 className="h-4 w-4" />,
    keywords: ['member', 'axis', 'layout', 'yanzhou', '沿轴', '布梁', '布柱'],
    usage: '沿选中轴线批量布梁，或按结构节点批量布柱，标高与截面可选',
    execute: openMemberLayout,
  },
  {
    id: 'member.wall',
    label: '墙',
    group: '建模',
    icon: <Square className="h-4 w-4" />,
    keywords: ['wall', 'qiang', '墙', 'member', '构件'],
    usage: '画布两点连续布置结构墙；布置栏可设墙类型、厚度、墙底和两端墙顶',
    execute: () => openStructuralWallTool('structural'),
  },
  {
    id: 'member.partition',
    label: '隔墙',
    group: '建模',
    icon: <Square className="h-4 w-4" />,
    keywords: ['partition', 'wall', 'geqiang', '隔墙', '砌体'],
    usage: '布置非承重隔墙，默认厚 120 mm，可在布置栏调整墙顶底',
    execute: () => openStructuralWallTool('partition'),
  },
  {
    id: 'member.inclinedWall',
    label: '斜墙',
    group: '建模',
    icon: <MoveVertical className="h-4 w-4" />,
    keywords: ['inclined', 'slope', 'wall', 'xieqiang', '斜墙', '变高墙'],
    usage: '布置左右墙顶不同的梯形斜墙，两端标高可在布置栏调整',
    execute: () => openStructuralWallTool('structural', true),
  },
  {
    id: 'member.wallOpening',
    label: '墙洞',
    group: '建模',
    icon: <SquarePen className="h-4 w-4" />,
    keywords: ['opening', 'hole', 'wall', 'qiangdong', '墙洞', '矩形洞'],
    usage: '先选中一面结构墙，新增可编辑矩形洞口；墙洞参数在墙体属性面板调整',
    when: () => {
      const scene = useScene.getState().nodes
      return (useViewer.getState().selection.selectedIds as AnyNodeId[]).some((id) => {
        const node = scene[id]
        return node?.type === 'structural-member' && node.memberType === 'wall'
      })
    },
    execute: addSelectedWallOpening,
  },
  {
    id: 'slab.generate',
    label: '生成楼板',
    group: '组装',
    icon: <Layers className="h-4 w-4" />,
    keywords: ['slab', 'generate', 'room', '生成楼板', '房间', '楼板生成'],
    aliases: ['slabgen', 'gen'],
    usage: '按墙和主梁围成的闭合房间自动生成楼板，已有手工板优先保留',
    execute: generateSlabsFromRooms,
  },
  {
    id: 'slab.cast',
    label: '现浇板',
    group: '组装',
    icon: <Layers className="h-4 w-4" />,
    keywords: ['slab', 'plate', 'ban', '板', '现浇板', '楼板'],
    aliases: ['slab', 'board'],
    usage: '进入矩形板布置：在 2D 画布点两个对角点',
    execute: () => openStructuralSlabTool('rectangle'),
  },
  {
    id: 'slab.polygon',
    label: '多边形板',
    group: '组装',
    icon: <Layers className="h-4 w-4" />,
    keywords: ['slab', 'polygon', 'duobian', '多边形', '板'],
    aliases: ['pslab', 'polygonslab'],
    usage: '进入多边形板布置：连续点选顶点，Enter 或双击完成',
    execute: () => openStructuralSlabTool('polygon'),
  },
  {
    id: 'slab.opening',
    label: '矩形板洞',
    group: '组装',
    icon: <SquarePen className="h-4 w-4" />,
    keywords: ['slab', 'opening', 'hole', '板洞', '开洞', '矩形洞'],
    aliases: ['hole', 'opening'],
    usage: '先选中一块结构板，再在板上点两个对角点布置矩形洞口',
    execute: () => openStructuralSlabOpening('rectangle'),
  },
  {
    id: 'slab.openingCircle',
    label: '圆形板洞',
    group: '组装',
    icon: <Target className="h-4 w-4" />,
    keywords: ['slab', 'opening', 'circle', '板洞', '圆洞'],
    aliases: ['holecircle'],
    usage: '先选中一块结构板，再点圆心和半径点布置圆形洞口',
    execute: () => openStructuralSlabOpening('circle'),
  },
  {
    id: 'slab.query',
    label: '楼板查询',
    group: '组装',
    icon: <Ruler className="h-4 w-4" />,
    keywords: ['slab', 'query', '楼板查询', '板信息', '面积'],
    aliases: ['slabinfo'],
    usage: '选中结构板后查询板厚、材料、板顶标高、净面积和洞口数量',
    execute: querySelectedSlab,
  },

  // ── 编辑 ──────────────────────────────────────────────────────────────────
  {
    id: 'edit.copy',
    label: '复制',
    group: '建模',
    icon: <Copy className="h-4 w-4" />,
    keywords: ['copy', 'fuzhi', '复制', 'edit'],
    when: EDIT_NEEDS_ANY_MEMBER,
    execute: () => openSelectedMemberEdit('复制', true),
  },
  {
    id: 'edit.move',
    label: '移动',
    group: '建模',
    icon: <Move className="h-4 w-4" />,
    keywords: ['move', 'yidong', '移动', 'edit'],
    when: EDIT_NEEDS_SELECTION,
    whenUnavailable: editUnavailableReason,
    execute: () => openSelectedMemberEdit('移动'),
  },
  {
    id: 'edit.mirror',
    label: '镜像',
    group: '建模',
    icon: <MirrorRectangular className="h-4 w-4" />,
    keywords: ['mirror', 'jingxiang', '镜像', 'edit'],
    when: EDIT_NEEDS_SELECTION,
    whenUnavailable: editUnavailableReason,
    execute: () => openSelectedMemberEdit('镜像'),
  },
  {
    id: 'edit.array',
    label: '阵列',
    group: '建模',
    icon: <Grid2x2 className="h-4 w-4" />,
    keywords: ['array', 'zhenlie', '阵列', 'edit'],
    when: EDIT_NEEDS_SELECTION,
    whenUnavailable: editUnavailableReason,
    execute: () => openSelectedMemberEdit('阵列'),
  },
  {
    id: 'edit.delete',
    label: '删除',
    group: '建模',
    icon: <Trash className="h-4 w-4" />,
    keywords: ['delete', 'remove', 'shanchu', '删除', 'edit'],
    aliases: ['delete', 'remove'],
    when: EDIT_NEEDS_SELECTION,
    whenUnavailable: editUnavailableReason,
    execute: deleteSelectedMembers,
  },
  {
    id: 'edit.hide',
    label: '隐藏',
    group: '建模',
    icon: <EyeOff className="h-4 w-4" />,
    keywords: ['hide', 'yincang', '隐藏', 'edit'],
    aliases: ['hide'],
    usage: '隐藏所选结构对象；未选择当前楼层结构对象时隐藏该楼层全部结构对象',
    when: () => Boolean(useViewer.getState().selection.levelId),
    whenUnavailable: '请先选择楼层',
    execute: hideStructuralObjects,
    preserveEditorContext: false,
  },
  {
    id: 'edit.show',
    label: '恢复显示',
    group: '建模',
    icon: <Eye className="h-4 w-4" />,
    keywords: ['show', 'restore', 'huifu', '恢复显示', 'edit'],
    aliases: ['show'],
    usage: '恢复显示当前楼层全部已隐藏的结构对象',
    when: () => Boolean(useViewer.getState().selection.levelId),
    whenUnavailable: '请先选择楼层',
    execute: showStructuralObjects,
    preserveEditorContext: false,
  },
  {
    id: 'node.support',
    label: '支座',
    group: '建模',
    icon: <Anchor className="h-4 w-4" />,
    keywords: ['support', 'zhizuo', '支座', 'node'],
    when: SCENE_SELECTION,
    execute: () => setStructuralSupport('pinned'),
  },
  {
    id: 'node.new',
    label: '节点',
    group: '建模',
    icon: <Anchor className="h-4 w-4" />,
    keywords: ['node', 'new', 'jiedian', '节点'],
    aliases: ['n', 'node', '_node'],
    usage: '先设置节点编号、上节点高、节点半径与支座，再在画布连续点布',
    execute: openNodePlaceDialog,
  },
  {
    id: 'grid.formNodes',
    label: '形成交点',
    group: '建模',
    icon: <Grid2x2 className="h-4 w-4" />,
    keywords: ['grid', 'intersection', 'form', '形成网点', '交点'],
    usage: '把当前轴网的交点形成结构节点',
    execute: formStructuralIntersections,
  },
  {
    id: 'grid.name',
    label: '轴线命名',
    group: '建模',
    icon: <Tags className="h-4 w-4" />,
    keywords: ['grid', 'name', 'axis', '轴号', '命名'],
    usage: '打开轴线命名面板：编号规则、起始值、前后缀、方向与预览',
    execute: openAxisNaming,
  },
  {
    id: 'grid.clean',
    label: '清理网点',
    group: '建模',
    icon: <Eraser className="h-4 w-4" />,
    keywords: ['grid', 'clean', 'qingli', '清理', '零长', '重复轴线'],
    usage: '删除当前楼层的零长度轴线、完全重复轴线，以及不再落在任何轴线上的自动节点',
    execute: cleanStructuralGrid,
  },
  {
    id: 'grid.edit',
    label: '轴网编辑',
    group: '建模',
    icon: <SquarePen className="h-4 w-4" />,
    keywords: ['grid', 'edit', 'zhouwang', '轴网', '编辑'],
    usage: '打开轴网编辑表，逐条修改轴号、起点和终点坐标',
    execute: openAxisEdit,
  },
  {
    id: 'grid.editScope',
    label: '全楼/局部',
    group: '建模',
    icon: <Layers className="h-4 w-4" />,
    keywords: ['grid', 'scope', 'quanlou', 'jubu', '全楼', '局部'],
    usage: '切换轴网编辑表与清理的范围：当前楼层或全楼',
    execute: toggleAxisEditScope,
  },
  {
    id: 'grid.split',
    label: '轴线打断',
    group: '建模',
    icon: <Scissors className="h-4 w-4" />,
    keywords: ['grid', 'split', 'break', 'dadian', '打断', '轴线打断'],
    usage: '在与其他轴线的交点处把所选轴线拆成多段，所有分段保持原轴号',
    when: () =>
      useScene.getState().nodes[useViewer.getState().selection.selectedIds[0] as AnyNodeId]
        ?.type === 'structural-grid',
    execute: splitSelectedAxis,
  },
  {
    id: 'grid.transform',
    label: '轴线变换',
    group: '建模',
    icon: <Move className="h-4 w-4" />,
    keywords: [
      'grid',
      'transform',
      'move',
      'copy',
      'rotate',
      'mirror',
      '偏移',
      '移动',
      '复制',
      '旋转',
      '镜像',
    ],
    usage: '对选中轴线做移动、复制、偏移、旋转或镜像；未选中时作用于当前楼层',
    execute: () => openAxisTransform('move'),
  },
  {
    id: 'grid.stitch',
    label: '轴网拼接',
    group: '建模',
    icon: <Link2 className="h-4 w-4" />,
    keywords: ['grid', 'stitch', 'pinjie', '拼接'],
    usage: '按源基点、目标基点和角度把选中轴网拼接到目标位置，可选择保留原轴网',
    execute: () => openAxisTransform('stitch'),
  },
  {
    id: 'grid.extend',
    label: '轴线延伸',
    group: '建模',
    icon: <Maximize2 className="h-4 w-4" />,
    keywords: ['grid', 'extend', 'yanshen', '延伸'],
    usage: '把所选轴线两端延伸到最近的相邻轴线',
    execute: extendAxes,
  },
  {
    id: 'grid.merge',
    label: '轴线合并',
    group: '建模',
    icon: <Link2 className="h-4 w-4" />,
    keywords: ['grid', 'merge', 'hebing', '合并'],
    usage: '把共线相接的多段轴线合并为一条',
    execute: mergeAxes,
  },
  {
    id: 'grid.trim',
    label: '轴线修剪',
    group: '建模',
    icon: <Scissors className="h-4 w-4" />,
    keywords: ['grid', 'trim', 'xiujian', '修剪'],
    usage: '把所选轴线两端修剪到最近的内部交点；锁定轴线跳过',
    execute: trimAxes,
  },
  {
    id: 'grid.dimensions',
    label: '尺寸标注',
    group: '建模',
    icon: <Ruler className="h-4 w-4" />,
    keywords: ['grid', 'dimension', 'chicun', '尺寸', '第一道', '第二道', '总尺寸'],
    usage: '为当前楼层生成第一道分段、第二道分段与总尺寸链，重复执行会替换旧标注',
    execute: createAxisDimensions,
  },
  {
    id: 'grid.dxfExport',
    label: '导出 DXF',
    group: '建模',
    icon: <Download className="h-4 w-4" />,
    keywords: ['grid', 'dxf', 'export', 'daochu', '导出'],
    usage: '把当前楼层轴线按图层导出为 DXF（LINE + 轴号 TEXT）',
    execute: exportAxesDxf,
  },
  {
    id: 'grid.dxfImport',
    label: '导入 DXF',
    group: '建模',
    icon: <Upload className="h-4 w-4" />,
    keywords: ['grid', 'dxf', 'import', 'daoru', '导入'],
    usage: '从 DXF 读取 LINE 实体并生成轴线，按图层保留、自动分配轴号',
    execute: importAxesDxf,
  },
  {
    id: 'node.merge',
    label: '节点归并',
    group: '建模',
    icon: <Grid2x2 className="h-4 w-4" />,
    keywords: ['node', 'merge', '归并', '合并节点'],
    usage: '按节点编辑表中的容差归并当前楼层的重复结构节点',
    execute: mergeNodesWithTolerance,
  },
  {
    id: 'node.edit',
    label: '节点编辑',
    group: '建模',
    icon: <Table2 className="h-4 w-4" />,
    keywords: ['node', 'edit', 'table', '节点', '编辑', '编号', '归并'],
    usage: '打开节点编辑表：编号规则、坐标、支座、半径、归并容差与孤立节点清理',
    execute: openNodeEdit,
  },
  {
    id: 'node.lock',
    label: '锁定/解锁',
    group: '建模',
    icon: <Lock className="h-4 w-4" />,
    keywords: ['node', 'lock', 'suoding', '锁定', '解锁'],
    when: SCENE_SELECTION,
    usage: '锁定或解锁所有选中的结构节点；锁定后禁止移动、编辑和删除',
    execute: toggleNodeLock,
  },
  {
    id: 'node.down',
    label: '节点下传',
    group: '建模',
    icon: <ArrowDownToLine className="h-4 w-4" />,
    keywords: ['node', 'down', 'xiachuan', '下传'],
    usage: '把选中节点（未选中则全楼层）复制到下一层相同平面位置',
    execute: descendNodes,
  },
  {
    id: 'node.alignX',
    label: 'X 对齐',
    group: '建模',
    icon: <MoveVertical className="h-4 w-4" />,
    keywords: ['node', 'align', 'duiqi', '对齐', 'X'],
    when: SCENE_SELECTION,
    usage: '把选中节点的 X 坐标对齐到第一个节点',
    execute: () => alignSelection('x'),
  },
  {
    id: 'node.alignZ',
    label: 'Y 对齐',
    group: '建模',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['node', 'align', 'duiqi', '对齐', 'Y'],
    when: SCENE_SELECTION,
    usage: '把选中节点的 Y 坐标对齐到第一个节点',
    execute: () => alignSelection('z'),
  },
  {
    id: 'support.fixed',
    label: '固定支座',
    group: '节点',
    icon: <Anchor className="h-4 w-4" />,
    keywords: ['support', 'fixed', '固结', '固定支座'],
    when: SCENE_SELECTION,
    execute: () => setStructuralSupport('fixed'),
  },
  {
    id: 'support.pinned',
    label: '铰支座',
    group: '节点',
    icon: <Anchor className="h-4 w-4" />,
    keywords: ['support', 'pinned', '铰接', '铰支座'],
    when: SCENE_SELECTION,
    execute: () => setStructuralSupport('pinned'),
  },
  {
    id: 'support.roller',
    label: '滚动支座',
    group: '节点',
    icon: <Anchor className="h-4 w-4" />,
    keywords: ['support', 'roller', '滚动', '滚动支座'],
    when: SCENE_SELECTION,
    execute: () => setStructuralSupport('roller'),
  },
  {
    id: 'support.free',
    label: '释放支座',
    group: '节点',
    icon: <Unlink className="h-4 w-4" />,
    keywords: ['support', 'free', '释放', '无支座'],
    when: SCENE_SELECTION,
    execute: () => setStructuralSupport('free'),
  },
  {
    id: 'node.release',
    label: '释放',
    group: '建模',
    icon: <Unlink className="h-4 w-4" />,
    keywords: ['release', 'shifang', '释放', 'node'],
    usage: '把所选构件的两端设为铰接',
    when: EDIT_NEEDS_SELECTION,
    whenUnavailable: editUnavailableReason,
    execute: () => releaseMemberEnds('pinned'),
  },
  {
    id: 'node.rigid',
    label: '刚接',
    group: '建模',
    icon: <Link2 className="h-4 w-4" />,
    keywords: ['rigid', 'gangjie', '刚接', 'node'],
    usage: '把所选构件的两端设为刚接',
    when: EDIT_NEEDS_SELECTION,
    whenUnavailable: editUnavailableReason,
    execute: () => releaseMemberEnds('rigid'),
  },
  {
    id: 'grid.ortho',
    label: '正交轴网',
    group: '建模',
    icon: <Grid3x3 className="h-4 w-4" />,
    keywords: ['grid', 'ortho', 'zhengjiao', '正交轴网'],
    usage: '打开正交轴网工具：开间 × 进深',
    execute: () => openAxisGrid('ortho'),
  },
  {
    id: 'grid.linear',
    label: '直线轴网',
    group: '建模',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['grid', 'linear', 'zhixian', '直线轴网'],
    usage: '在 2D 画布连续点选绘制单根直线轴',
    execute: () => openStructuralGridTool('line'),
  },
  {
    id: 'grid.arc',
    label: '圆弧轴网',
    group: '建模',
    icon: <Target className="h-4 w-4" />,
    keywords: ['grid', 'arc', 'radial', 'yuanhu', '圆弧轴网'],
    usage: '在 2D 画布用三点绘制圆弧轴',
    execute: () => openStructuralGridTool('arc'),
  },
  {
    id: 'grid.radialGrid',
    label: '径向圆弧轴网',
    group: '建模',
    icon: <Target className="h-4 w-4" />,
    keywords: ['grid', 'radial', 'arc', 'jingxiang', '径向', '圆弧轴网'],
    usage: '在 2D 画布用三点绘制圆弧轴',
    execute: () => openStructuralGridTool('arc'),
  },
  {
    id: 'grid.rectangle',
    label: '矩形轴网',
    group: '建模',
    icon: <Square className="h-4 w-4" />,
    keywords: ['grid', 'rectangle', 'rect', 'juxing', '矩形轴网'],
    usage: '在 2D 画布拖出两条对角点生成矩形轴网',
    execute: () => openStructuralGridTool('rectangle'),
  },
  {
    id: 'grid.skew',
    label: '斜交轴网',
    group: '建模',
    icon: <MoveDiagonal className="h-4 w-4" />,
    keywords: ['grid', 'skew', 'xiejiao', '斜交轴网'],
    usage: '在 2D 画布直接绘制斜向单轴',
    execute: () => openStructuralGridTool('line'),
  },
  {
    id: 'grid.aux',
    label: '辅助轴线',
    group: '建模',
    icon: <Grid2x2 className="h-4 w-4" />,
    keywords: ['grid', 'aux', 'fuzhu', '辅助轴线'],
    usage: '在 2D 画布直接绘制辅助轴线',
    execute: () => openStructuralGridTool('line'),
  },
  {
    id: 'node.topElevation',
    label: '上节点高',
    group: '建模',
    icon: <Ruler className="h-4 w-4" />,
    keywords: ['node', 'elevation', 'top', 'shangjiediangao', '上节点高'],
    usage: '按选中节点设置上节点高，支持单点/两点坡度/三点斜面',
    execute: () => openNodeElevation('single'),
  },
  {
    id: 'node.topElevationSingle',
    label: '单点上节点高',
    group: '建模',
    icon: <Ruler className="h-4 w-4" />,
    keywords: ['node', 'elevation', 'single', '单点', '上节点高'],
    usage: '设置选中节点的上节点高（单点模式）',
    execute: () => openNodeElevation('single'),
  },
  {
    id: 'node.topElevationTwo',
    label: '两点上节点高',
    group: '建模',
    icon: <Ruler className="h-4 w-4" />,
    keywords: ['node', 'elevation', 'two', '两点', '上节点高'],
    usage: '选中两个节点，按两端上节点高形成坡度并插值中间节点',
    execute: () => openNodeElevation('two'),
  },
  {
    id: 'node.topElevationThree',
    label: '三点上节点高',
    group: '建模',
    icon: <Ruler className="h-4 w-4" />,
    keywords: ['node', 'elevation', 'three', '三点', '上节点高'],
    usage: '选中三个节点，按三点上节点高形成斜面并可应用到全楼层',
    execute: () => openNodeElevation('three'),
  },
  {
    id: 'view.wireframe',
    label: '线框',
    group: '建模',
    icon: <Eye className="h-4 w-4" />,
    keywords: ['wireframe', 'xiankuang', '线框', 'view'],
    execute: () => {
      useViewer.getState().setWireframe(true)
      useStructStore.getState().setDisplayMode('wireframe')
      logResult('视图', '切换为线框显示')
    },
    preserveEditorContext: true,
  },
  {
    id: 'view.shaded',
    label: '着色',
    group: '建模',
    icon: <EyeOff className="h-4 w-4" />,
    keywords: ['shaded', 'zhuose', '着色', 'view'],
    execute: () => {
      useViewer.getState().setWireframe(false)
      useViewer.getState().setShading('rendered')
      useStructStore.getState().setDisplayMode('shaded')
      logResult('视图', '切换为着色显示')
    },
    preserveEditorContext: true,
  },
  {
    id: 'view.top',
    label: '平面',
    group: '建模',
    icon: <Grid2x2 className="h-4 w-4" />,
    keywords: ['top', 'plan', 'pingmian', '平面', 'view'],
    execute: () => runStructViewCommand('view.top'),
    preserveEditorContext: true,
  },
  {
    id: 'view.front',
    label: '正面',
    group: '建模',
    icon: <Compass className="h-4 w-4" />,
    keywords: ['front', 'zhengmian', '正面', 'view'],
    execute: () => runStructViewCommand('view.front'),
    preserveEditorContext: true,
  },
  {
    id: 'view.left',
    label: '左侧',
    group: '建模',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['left', 'zuoce', '左侧', 'view'],
    execute: () => runStructViewCommand('view.left'),
    preserveEditorContext: true,
  },
  {
    id: 'view.labels',
    label: '标注',
    group: '建模',
    icon: <Tags className="h-4 w-4" />,
    keywords: ['labels', 'biazhu', '标注', 'view'],
    execute: () => logResult('视图', '构件标注已开启'),
  },
  {
    id: 'view.iso',
    label: '轴测',
    group: '建模',
    icon: <Box className="h-4 w-4" />,
    keywords: ['iso', 'isometric', 'zhouce', '轴测', 'view'],
    execute: () => runStructViewCommand('view.iso'),
    preserveEditorContext: true,
  },
  {
    id: 'view.fit',
    label: '充满全屏',
    group: '建模',
    icon: <Maximize2 className="h-4 w-4" />,
    keywords: ['fit', 'frame', 'chongman', '充满', '全屏', 'view'],
    execute: () => runStructViewCommand('view.fit'),
    preserveEditorContext: true,
  },
  {
    id: 'query.measure',
    label: '测量',
    group: '建模',
    icon: <Ruler className="h-4 w-4" />,
    keywords: ['measure', 'celiang', '测量', 'query'],
    when: () => useViewer.getState().selection.levelId !== null,
    whenUnavailable: '请先选择楼层',
    execute: () => {
      useFloorplanMode.getState().setMode('expert')
      useEditor.getState().setToolDefaults('measurement', { kind: 'distance' })
      useEditor.getState().armToolMode({ mode: 'build', tool: 'measurement' })
    },
  },

  // ── 荷载 ──────────────────────────────────────────────────────────────────
  {
    id: 'load.dead',
    label: '恒载',
    group: '荷载',
    icon: <Weight className="h-4 w-4" />,
    keywords: ['dead', 'hengzai', '恒载', 'load'],
    execute: () => addLoad('恒载 DL'),
  },
  {
    id: 'load.live',
    label: '活载',
    group: '荷载',
    icon: <Activity className="h-4 w-4" />,
    keywords: ['live', 'huozai', '活载', 'load'],
    execute: () => addLoad('活载 LL'),
  },
  {
    id: 'load.wind',
    label: '风载',
    group: '荷载',
    icon: <Wind className="h-4 w-4" />,
    keywords: ['wind', 'fengzai', '风载', 'load'],
    execute: () => addLoad('风载 WL'),
  },
  {
    id: 'load.seismic',
    label: '地震',
    group: '荷载',
    icon: <Layers className="h-4 w-4" />,
    keywords: ['seismic', 'earthquake', 'dizhen', '地震', 'load'],
    execute: () => addLoad('地震 EQ'),
  },
  {
    id: 'load.point',
    label: '点荷载',
    group: '荷载',
    icon: <ArrowDownToLine className="h-4 w-4" />,
    keywords: ['point', 'dianhezai', '点荷载', 'load'],
    execute: () => addLoad('点荷载 PL'),
  },
  {
    id: 'load.line',
    label: '线荷载',
    group: '荷载',
    icon: <MoveHorizontal className="h-4 w-4" />,
    keywords: ['line', 'linear', 'xianhezai', '线荷载', 'load'],
    aliases: ['l', 'line', '_load'],
    usage: 'line <q kN/m>',
    args: [{ name: 'q', label: '线荷载 q (kN/m)', type: 'number' }],
    when: () => {
      const scene = useScene.getState()
      const selection = useViewer.getState().selection.selectedIds
      return (
        hasSelectedLineLoadMember(scene.nodes, selection) &&
        !hasLockedMembers(
          scene.nodes,
          selectedLineLoadMembers(scene.nodes, selection).map((member) => member.id),
        )
      )
    },
    whenUnavailable: () => {
      const scene = useScene.getState()
      const selection = useViewer.getState().selection.selectedIds
      return selectedLineLoadMembers(scene.nodes, selection).length > 0
        ? LOCKED_MEMBER_MESSAGE
        : '请先选择未锁定的梁或墙'
    },
    execute: () => useStructStore.getState().openLoadPanel('member'),
    executeWithArgs: (args) => {
      const raw = (args[0] ?? '').trim()
      const parsed = splitNumberArgs([raw === '' ? '4.2' : raw])
      if (!parsed.ok) {
        throw new Error(`线荷载参数无效：${parsed.invalid}`)
      }
      addSelectedUniformLineLoad(parsed.values[0] ?? 4.2)
    },
  },
  {
    id: 'load.area',
    label: '面荷载',
    group: '荷载',
    icon: <Square className="h-4 w-4" />,
    keywords: ['area', 'surface', 'mianhezai', '面荷载', 'load'],
    execute: () => addLoad('面荷载 AL'),
  },
  {
    id: 'load.combinations',
    label: '荷载组合',
    group: '荷载',
    icon: <Sigma className="h-4 w-4" />,
    keywords: ['combination', 'zuhe', '荷载组合', 'load'],
    execute: () => useStructStore.getState().openLoadPanel('combinations'),
  },
  {
    id: 'load.case',
    label: '荷载工况',
    group: '荷载',
    icon: <Layers className="h-4 w-4" />,
    keywords: ['case', '工况', '荷载工况', 'load'],
    execute: () => useStructStore.getState().openLoadPanel('cases'),
  },
  {
    id: 'load.show',
    label: '显示荷载',
    group: '荷载',
    icon: <Eye className="h-4 w-4" />,
    keywords: ['show', 'display', '显示荷载', 'load'],
    execute: () => useStructStore.getState().openLoadPanel('member'),
  },

  // ── 分析 ──────────────────────────────────────────────────────────────────
  {
    id: 'analysis.assemble',
    label: '组装分析模型',
    group: '分析',
    icon: <Boxes className="h-4 w-4" />,
    keywords: ['analysis', 'assemble', 'zuzhuang', '组装', '前处理'],
    usage: '把节点、构件、截面、材料、支座组装成分析模型并做前处理检查',
    execute: openAnalysisModel,
  },
  {
    id: 'analysis.check',
    label: '模型检查',
    group: '分析',
    icon: <Scan className="h-4 w-4" />,
    keywords: ['check', 'validate', 'moxingjiancha', '模型检查', 'analysis'],
    usage: '检查分析模型的节点连接、支座、重复构件与截面匹配',
    execute: openAnalysisModel,
  },
  {
    id: 'analysis.generate',
    label: '生成数据',
    group: '分析',
    icon: <FileSpreadsheet className="h-4 w-4" />,
    keywords: ['generate', 'shengcheng', '生成数据', 'analysis'],
    execute: () => logResult('生成数据', '已导出 3 个分析工况'),
  },
  {
    id: 'analysis.run',
    label: '开始分析',
    group: '分析',
    icon: <Play className="h-4 w-4" />,
    keywords: ['run', 'solve', 'analysis', 'kaishi', '开始分析'],
    usage: '先打开分析模型组装与前处理检查；通过后提交真实作业',
    execute: openAnalysisModel,
  },
  {
    id: 'analysis.modal',
    label: '模态',
    group: '分析',
    icon: <Activity className="h-4 w-4" />,
    keywords: ['modal', 'mode', 'moshi', '模态', 'analysis'],
    execute: () => logResult('模态分析', '前 6 阶频率已提取'),
  },
  {
    id: 'analysis.buckling',
    label: '屈曲',
    group: '分析',
    icon: <Gauge className="h-4 w-4" />,
    keywords: ['buckling', 'ququ', '屈曲', 'analysis'],
    execute: () => logResult('屈曲分析', '一阶屈曲因子 6.82'),
  },

  // ── 结果 ──────────────────────────────────────────────────────────────────
  {
    id: 'result.deform',
    label: '变形',
    group: '结果',
    icon: <Move className="h-4 w-4" />,
    keywords: ['deformation', 'bianxing', '变形', 'result'],
    when: hasAnalysisResult,
    whenUnavailable: NO_ANALYSIS_RESULT,
    execute: () => openAnalysisResult('deformation'),
  },
  {
    id: 'result.moment',
    label: '弯矩',
    group: '结果',
    icon: <RotateCcw className="h-4 w-4" />,
    keywords: ['moment', 'wanju', '弯矩', 'result'],
    when: hasAnalysisResult,
    whenUnavailable: NO_ANALYSIS_RESULT,
    execute: () => openAnalysisResult('moment'),
  },
  {
    id: 'result.shear',
    label: '剪力',
    group: '结果',
    icon: <Compass className="h-4 w-4" />,
    keywords: ['shear', 'jianli', '剪力', 'result'],
    when: hasAnalysisResult,
    whenUnavailable: NO_ANALYSIS_RESULT,
    execute: () => openAnalysisResult('shear'),
  },
  {
    id: 'result.axial',
    label: '轴力',
    group: '结果',
    icon: <Maximize2 className="h-4 w-4" />,
    keywords: ['axial', 'zhhouli', '轴力', 'result'],
    when: hasAnalysisResult,
    whenUnavailable: NO_ANALYSIS_RESULT,
    execute: () => openAnalysisResult('axial'),
  },
  {
    id: 'result.ratio',
    label: '应力比',
    group: '结果',
    icon: <Gauge className="h-4 w-4" />,
    keywords: ['ratio', 'stress', 'yinglibi', '应力比', 'result'],
    when: hasAnalysisResult,
    whenUnavailable: NO_ANALYSIS_RESULT,
    execute: () => openAnalysisResult('stress'),
  },
  {
    id: 'result.reaction',
    label: '反力',
    group: '结果',
    icon: <Anchor className="h-4 w-4" />,
    keywords: ['reaction', 'fanli', '反力', 'result'],
    when: hasAnalysisResult,
    whenUnavailable: NO_ANALYSIS_RESULT,
    execute: () => openAnalysisResult('reaction'),
  },
  {
    id: 'result.table',
    label: '结果表',
    group: '结果',
    icon: <Table2 className="h-4 w-4" />,
    keywords: ['table', 'jieguobiao', '结果表', 'result'],
    when: hasAnalysisResult,
    whenUnavailable: NO_ANALYSIS_RESULT,
    execute: () => openAnalysisResult('table'),
  },

  // ── 施工图 ────────────────────────────────────────────────────────────────
  {
    id: 'draw.sheet',
    label: '图框',
    group: '施工图',
    icon: <Frame className="h-4 w-4" />,
    keywords: ['sheet', 'frame', 'tukuang', '图框', 'draw'],
    execute: () => {
      useStructStore.getState().openDrawingOutput()
      logResult('施工图', '打开结构布置图输出')
    },
  },
  {
    id: 'draw.elevation',
    label: '立面',
    group: '施工图',
    icon: <Columns3 className="h-4 w-4" />,
    keywords: ['elevation', 'limian', '立面', 'draw'],
    execute: () => {
      useStructStore.getState().setActiveSheet('立面图')
      logResult('施工图', '生成门式刚架立面')
    },
  },
  {
    id: 'draw.detail',
    label: '节点大样',
    group: '施工图',
    icon: <Boxes className="h-4 w-4" />,
    keywords: ['detail', 'jiedian', '节点大样', 'draw'],
    execute: () => {
      useStructStore.getState().setActiveSheet('节点大样')
      logResult('施工图', '生成梁柱节点大样')
    },
  },
  {
    id: 'draw.bom',
    label: '材料表',
    group: '施工图',
    icon: <List className="h-4 w-4" />,
    keywords: ['bom', 'material', 'cailiaobiao', '材料表', 'draw'],
    execute: () => {
      useStructStore.getState().setActiveSheet('材料表')
      logResult('施工图', '生成材料表')
    },
  },
  {
    id: 'draw.dwg',
    label: '导出 DWG',
    group: '施工图',
    icon: <Download className="h-4 w-4" />,
    keywords: ['dwg', 'export', 'daochu', '导出', 'draw'],
    execute: () => {
      useStructStore.getState().setActiveSheet('DWG 导出')
      logResult('施工图', 'DWG 导出任务已提交')
    },
  },

  // ── 通用 ──────────────────────────────────────────────────────────────────
  {
    id: 'edit.undo',
    label: '撤销',
    group: '通用',
    icon: <Undo2 className="h-4 w-4" />,
    keywords: ['undo', 'chexiao', '撤销'],
    shortcut: ['Ctrl+Z'],
    execute: () => {
      const result = runUndo()
      logResult('撤销', result.kind === 'empty' ? '没有可撤销的操作' : '已回退一步')
    },
  },
  {
    id: 'edit.redo',
    label: '重做',
    group: '通用',
    icon: <Redo2 className="h-4 w-4" />,
    keywords: ['redo', 'zhongzuo', '重做'],
    shortcut: ['Ctrl+Shift+Z'],
    execute: () => {
      const result = runRedo()
      logResult('重做', result.kind === 'empty' ? '没有可重做的操作' : '已重做一步')
    },
  },
  {
    id: 'select.all',
    label: '全选',
    group: '通用',
    icon: <Component className="h-4 w-4" />,
    keywords: ['select', 'all', 'quanxuan', '全选'],
    shortcut: ['Ctrl+A'],
    execute: () => {
      const ids = Object.keys(useScene.getState().nodes)
      useViewer.getState().setSelection({ selectedIds: ids })
      logResult('全选', `${ids.length} 个场景节点`)
    },
  },
  {
    id: 'select.clear',
    label: '清空选择',
    group: '通用',
    icon: <Square className="h-4 w-4" />,
    keywords: ['clear', 'selection', 'qingkong', '清空选择'],
    execute: () => {
      useViewer.getState().setSelection({ selectedIds: [] })
      useStructStore.getState().clearSelection()
      logResult('清空选择', '选择已清空')
    },
  },
  {
    id: 'tool.commands',
    label: '命令库',
    group: '通用',
    icon: <Keyboard className="h-4 w-4" />,
    keywords: ['cmd', 'commands', 'command', '命令库'],
    aliases: ['cmd', 'commands', '_commands'],
    execute: () => useCommandPalette.getState().setOpen(true),
    preserveEditorContext: true,
  },
  {
    id: 'help.shortcuts',
    label: '快捷键',
    group: '通用',
    icon: <Keyboard className="h-4 w-4" />,
    keywords: ['help', 'shortcut', 'kuaijiejian', '快捷键'],
    execute: () =>
      logResult(
        '快捷键',
        'F2 命令行 · Ctrl+K 命令面板 · Ctrl+Z 撤销 · Ctrl+Shift+Z 重做 · ↑/↓ 历史 · Tab 补全',
      ),
  },
]

export const STRUCT_COMMANDS: CommandAction[] = [
  ...BASE_STRUCT_COMMANDS.map((action) =>
    PLANNED_STRUCT_COMMAND_IDS.has(action.id) ? asPlannedCommand(action) : action,
  )
    .map(addFirstBatchAliases)
    .map(addExecutionContext),
  ...YJK_PLANNED_COMMANDS.filter(
    (planned) => !BASE_STRUCT_COMMANDS.some((base) => base.id === planned.id),
  )
    .map(asPlannedCommand)
    .map(addFirstBatchAliases)
    .map(addExecutionContext),
]

export function resolveStructCommand(idOrAlias: string) {
  const registered = useCommandRegistry.getState().actions
  return resolveCommandAction(registered.length > 0 ? registered : STRUCT_COMMANDS, idOrAlias)
}

/**
 * Single entry point used by the ribbon, command line and command palette.
 * Argument-aware commands use `executeWithArgs`; everything else keeps the
 * zero-argument `execute()` semantics.
 */
export function runStructCommand(
  id: string,
  args: string[] = [],
): { ok: boolean; message: string } {
  const resolution = resolveStructCommand(id)
  if (!resolution.ok) {
    useStructStore.getState().pushLog(resolution.message, 'error')
    return resolution
  }

  const result = executeCommandAction(resolution.action, args)
  if (!result.ok && result.status !== 'unavailable') {
    useStructStore.getState().pushLog(result.message, 'error')
  }
  return { ok: result.ok, message: result.message }
}

export function useStructCommands() {
  useEffect(() => {
    return useCommandRegistry.getState().register(STRUCT_COMMANDS)
  }, [])
}
