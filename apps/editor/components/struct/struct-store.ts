'use client'

import {
  type AnyNodeId,
  runAsSingleSceneHistoryStep,
  type StructuralMember,
} from '@pascal-app/core'
import { type SceneGraph, useEditor, useScene, useViewer } from '@pascal-app/editor'
import { create } from 'zustand'
import type { AnalysisResultViewMode } from '@/lib/analysis-jobs/client'
import type { AnalysisJob } from '@/lib/analysis-jobs/job-types'
import { normalizeStructProjectMeta, readStructProjectMeta } from '@/lib/struct/project-store'
import {
  type BeamSection,
  type ColumnSection,
  cloneSectionLibrary,
  DEFAULT_SECTION_LIBRARY,
  haveSameSectionLibrary,
  normalizeBeamSection,
  normalizeColumnSection,
  normalizeSectionLibrary,
  type SectionLibrary,
} from '@/lib/struct/section-definitions'
import { sectionLabel } from '@/lib/struct/section-library'

export type MemberType = 'beam' | 'column' | 'truss' | 'brace'

export type {
  BeamPlacementConfig,
  BeamSection,
  BeamSectionKind,
  ColumnPlacementConfig,
  ColumnSection,
  ColumnSectionKind,
  SectionLibrary,
} from '@/lib/struct/section-definitions'
export {
  BEAM_SECTION_FAMILY,
  BEAM_SECTION_KIND_LABEL,
  COLUMN_SECTION_FAMILY,
  COLUMN_SECTION_KIND_LABEL,
  DEFAULT_BEAM_SECTIONS,
  DEFAULT_COLUMN_SECTIONS,
  toBeamPlacementConfig,
  toColumnPlacementConfig,
} from '@/lib/struct/section-definitions'

export type NodeSupport = 'free' | 'pinned' | 'fixed' | 'roller' | 'elastic'
export type NodeElevationMode = 'single' | 'two' | 'three'

export type NodePlacementConfig = {
  labelPrefix: string
  labelStart: number
  elevationOffset: number
  markerRadius: number
  support: NodeSupport
  showLabel: boolean
  locked: boolean
}

export function toNodePlacementConfig(settings: {
  labelPrefix: string
  labelStart: number
  elevationOffset: number
  markerRadiusMm: number
  support: NodeSupport
  showLabel: boolean
  locked: boolean
}): NodePlacementConfig {
  return {
    labelPrefix: settings.labelPrefix,
    labelStart: settings.labelStart,
    elevationOffset: settings.elevationOffset,
    markerRadius: settings.markerRadiusMm / 1000,
    support: settings.support,
    showLabel: settings.showLabel,
    locked: settings.locked,
  }
}

export type Member = {
  id: string
  type: MemberType
  length: number
  section: string
}

export type Load = {
  id: string
  case: string
  value: number
}

export type LogLevel = 'info' | 'ok' | 'error'

export type LogEntry = {
  id: number
  time: string
  level: LogLevel
  text: string
}

export type StructSelection = { kind: 'member'; id: string } | null
export type LoadPanelView = 'member' | 'cases' | 'combinations'

export type AxisEditScope = 'level' | 'all'
export type AxisTransformPreset = 'move' | 'copy' | 'offset' | 'rotate' | 'mirror' | 'stitch'
export type SectionDeleteResult = { deleted: boolean; reason?: string }

type StructStore = {
  tab: string
  members: Member[]
  loads: Load[]
  selection: StructSelection
  displayMode: 'wireframe' | 'shaded'
  analysis: 'idle' | 'running' | 'done'
  analysisJobsOpen: boolean
  analysisResultsOpen: boolean
  analysisResultSetId: string | null
  analysisResultView: AnalysisResultViewMode
  analysisLatestJob: AnalysisJob | null
  activeResult: string | null
  activeSheet: string | null
  loadPanelView: LoadPanelView
  axisEditOpen: boolean
  axisEditScope: AxisEditScope
  axisNamingOpen: boolean
  axisTransformOpen: boolean
  axisTransformPreset: AxisTransformPreset
  nodeEditOpen: boolean
  memberEditOpen: boolean
  memberAxisAnglePickMemberId: string | null
  memberAxisAnglePickOriginTool: string | null
  analysisModelOpen: boolean
  memberLayoutOpen: boolean
  revisionHistoryOpen: boolean
  drawingOutputOpen: boolean
  ifcImportOpen: boolean
  columnDialogOpen: boolean
  columnSections: ColumnSection[]
  activeColumnSectionId: string
  sectionLibraryProjectId: string | null
  columnOffsetX: number
  columnOffsetZ: number
  columnRotation: number
  columnBaseOffset: number
  beamSections: BeamSection[]
  activeBeamSectionId: string
  beamOffsetZ: number
  beamTopOffsetStart: number
  beamTopOffsetEnd: number
  beamRotation: number
  nodePlaceDialogOpen: boolean
  nodeLabelPrefix: string
  nodeLabelStart: number
  nodeElevationOffset: number
  nodeMarkerRadiusMm: number
  nodeSupport: NodeSupport
  nodeShowLabel: boolean
  nodeLocked: boolean
  nodeElevationDialogOpen: boolean
  nodeElevationMode: NodeElevationMode
  beamDialogOpen: boolean
  wallDialogOpen: boolean
  levelParamsOpen: boolean
  log: LogEntry[]
  history: string[]
  setTab: (tab: string) => void
  addMember: (member: Omit<Member, 'id'>) => Member
  addLoad: (load: Omit<Load, 'id'>) => Load
  selectMember: (id: string | null) => void
  clearSelection: () => void
  setDisplayMode: (mode: 'wireframe' | 'shaded') => void
  setAnalysis: (analysis: 'idle' | 'running' | 'done') => void
  recordAnalysisJob: (job: AnalysisJob) => void
  syncAnalysisJobs: (jobs: AnalysisJob[]) => void
  openAnalysisJobs: (job?: AnalysisJob | null) => void
  closeAnalysisJobs: () => void
  setAnalysisResult: (resultSetId: string, view: AnalysisResultViewMode) => void
  openAnalysisResults: (view: AnalysisResultViewMode) => void
  closeAnalysisResults: () => void
  setActiveResult: (result: string | null) => void
  setActiveSheet: (sheet: string | null) => void
  openLoadPanel: (view?: LoadPanelView) => void
  openAxisEdit: () => void
  closeAxisEdit: () => void
  setAxisEditScope: (scope: AxisEditScope) => void
  toggleAxisEditScope: () => void
  openAxisNaming: () => void
  closeAxisNaming: () => void
  openAxisTransform: (mode?: AxisTransformPreset) => void
  closeAxisTransform: () => void
  openNodeEdit: () => void
  closeNodeEdit: () => void
  openMemberEdit: () => void
  closeMemberEdit: () => void
  startMemberAxisAnglePick: (memberId: string) => void
  clearMemberAxisAnglePick: () => void
  finishMemberAxisAnglePick: (memberId: string) => void
  cancelMemberAxisAnglePick: () => void
  openAnalysisModel: () => void
  closeAnalysisModel: () => void
  openMemberLayout: () => void
  closeMemberLayout: () => void
  openRevisionHistory: () => void
  closeRevisionHistory: () => void
  openDrawingOutput: () => void
  closeDrawingOutput: () => void
  openIfcImport: () => void
  closeIfcImport: () => void
  openColumnDialog: () => void
  closeColumnDialog: () => void
  hydrateSectionLibrary: (library: unknown, projectId?: string | null) => void
  createColumnSection: (section: Omit<ColumnSection, 'id' | 'label'>) => ColumnSection
  updateColumnSection: (id: string, patch: Partial<Omit<ColumnSection, 'id' | 'label'>>) => void
  deleteColumnSection: (id: string) => SectionDeleteResult
  setActiveColumnSection: (id: string) => void
  setColumnPlacement: (
    patch: Partial<{
      offsetX: number
      offsetZ: number
      rotation: number
      baseOffset: number
    }>,
  ) => void
  createBeamSection: (section: Omit<BeamSection, 'id' | 'label'>) => BeamSection
  updateBeamSection: (id: string, patch: Partial<Omit<BeamSection, 'id' | 'label'>>) => void
  deleteBeamSection: (id: string) => SectionDeleteResult
  setActiveBeamSection: (id: string) => void
  setBeamPlacement: (
    patch: Partial<{
      offsetZ: number
      topOffsetStart: number
      topOffsetEnd: number
      rotation: number
    }>,
  ) => void
  openNodePlaceDialog: () => void
  closeNodePlaceDialog: () => void
  setNodePlacement: (
    patch: Partial<{
      labelPrefix: string
      labelStart: number
      elevationOffset: number
      markerRadiusMm: number
      support: NodeSupport
      showLabel: boolean
      locked: boolean
    }>,
  ) => void
  openNodeElevationDialog: (mode: NodeElevationMode) => void
  closeNodeElevationDialog: () => void
  openBeamDialog: () => void
  closeBeamDialog: () => void
  openWallDialog: () => void
  closeWallDialog: () => void
  openLevelParams: () => void
  closeLevelParams: () => void
  closeAllPanels: () => void
  pushLog: (text: string, level?: LogLevel) => void
  pushHistory: (text: string) => void
  reset: () => void
}

const MAX_LOG = 100
const MAX_HISTORY = 50

let logSeq = 0
let memberSeq = 0
let loadSeq = 0

function timestamp(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

function nextDefinitionId(prefix: 'CS' | 'BS', ids: readonly string[]): string {
  let max = 0
  for (const id of ids) {
    if (!id.startsWith(`${prefix}-`)) continue
    const suffix = Number(id.slice(prefix.length + 1))
    if (Number.isInteger(suffix) && suffix > max) max = suffix
  }
  return `${prefix}-${max + 1}`
}

function linkedMembers(sectionId: string, memberType: 'beam' | 'column'): StructuralMember[] {
  return Object.values(useScene.getState().nodes).filter(
    (node): node is StructuralMember =>
      node.type === 'structural-member' &&
      node.memberType === memberType &&
      node.sectionId === sectionId,
  )
}

function sectionLibraryFromState(
  state: Pick<
    StructStore,
    'columnSections' | 'beamSections' | 'activeColumnSectionId' | 'activeBeamSectionId'
  >,
): SectionLibrary {
  return {
    columns: state.columnSections,
    beams: state.beamSections,
    activeColumnSectionId: state.activeColumnSectionId,
    activeBeamSectionId: state.activeBeamSectionId,
  }
}

function commitSectionLibraryScene(
  library: SectionLibrary,
  memberUpdates: Array<{ id: AnyNodeId; data: Partial<StructuralMember> }> = [],
): void {
  const scene = useScene.getState()
  const site = Object.values(scene.nodes).find(
    (node) => node.type === 'site' && node.metadata?.structProject,
  )
  const updates: Array<{ id: AnyNodeId; data: Record<string, unknown> }> = [...memberUpdates]
  if (site) {
    const meta = readStructProjectMeta({
      nodes: scene.nodes,
      rootNodeIds: scene.rootNodeIds,
    } as SceneGraph)
    const nextMeta = meta
      ? normalizeStructProjectMeta({ ...meta, sectionLibrary: library }, meta.id)
      : null
    if (nextMeta) {
      updates.push({
        id: site.id as AnyNodeId,
        data: {
          metadata: {
            ...site.metadata,
            structProject: nextMeta,
            structProjectName: nextMeta.name,
            structuralSystem: nextMeta.structuralSystem,
          },
        },
      })
    }
  }
  if (updates.length === 0) return
  runAsSingleSceneHistoryStep(useScene, () => {
    useScene.getState().applyNodeChanges({ update: updates })
  })
}

const initialState = {
  tab: 'model',
  members: [] as Member[],
  loads: [] as Load[],
  selection: null as StructSelection,
  displayMode: 'shaded' as const,
  analysis: 'idle' as const,
  analysisJobsOpen: false,
  analysisResultsOpen: false,
  analysisResultSetId: null as string | null,
  analysisResultView: 'table' as AnalysisResultViewMode,
  analysisLatestJob: null as AnalysisJob | null,
  activeResult: null,
  activeSheet: null,
  loadPanelView: 'member' as LoadPanelView,
  axisEditOpen: false,
  axisEditScope: 'level' as const,
  axisNamingOpen: false,
  axisTransformOpen: false,
  axisTransformPreset: 'move' as AxisTransformPreset,
  nodeEditOpen: false,
  memberEditOpen: false,
  memberAxisAnglePickMemberId: null as string | null,
  memberAxisAnglePickOriginTool: null as string | null,
  analysisModelOpen: false,
  memberLayoutOpen: false,
  revisionHistoryOpen: false,
  drawingOutputOpen: false,
  ifcImportOpen: false,
  columnDialogOpen: false,
  columnSections: cloneSectionLibrary(DEFAULT_SECTION_LIBRARY).columns,
  activeColumnSectionId: 'CS-3',
  sectionLibraryProjectId: null as string | null,
  columnOffsetX: 0,
  columnOffsetZ: 0,
  columnRotation: 0,
  columnBaseOffset: 0,
  beamSections: cloneSectionLibrary(DEFAULT_SECTION_LIBRARY).beams,
  activeBeamSectionId: 'BS-3',
  beamOffsetZ: 0,
  beamTopOffsetStart: 0,
  beamTopOffsetEnd: 0,
  beamRotation: 0,
  nodePlaceDialogOpen: false,
  nodeLabelPrefix: 'N',
  nodeLabelStart: 1,
  nodeElevationOffset: 0,
  nodeMarkerRadiusMm: 90,
  nodeSupport: 'free' as NodeSupport,
  nodeShowLabel: true,
  nodeLocked: false,
  nodeElevationDialogOpen: false,
  nodeElevationMode: 'single' as NodeElevationMode,
  beamDialogOpen: false,
  wallDialogOpen: false,
  levelParamsOpen: false,
  log: [] as LogEntry[],
  history: [] as string[],
}

export const useStructStore = create<StructStore>((set, get) => ({
  ...initialState,
  setTab: (tab) => set({ tab }),
  addMember: (member) => {
    memberSeq += 1
    const created: Member = { ...member, id: `M-${1000 + memberSeq}` }
    set((s) => ({ members: [...s.members, created] }))
    return created
  },
  addLoad: (load) => {
    loadSeq += 1
    const created: Load = { ...load, id: `L-${200 + loadSeq}` }
    set((s) => ({ loads: [...s.loads, created] }))
    return created
  },
  selectMember: (id) => set({ selection: id ? { kind: 'member', id } : null }),
  clearSelection: () => set({ selection: null }),
  setDisplayMode: (displayMode) => set({ displayMode }),
  setAnalysis: (analysis) => set({ analysis }),
  recordAnalysisJob: (analysisLatestJob) =>
    set({
      analysisLatestJob,
      analysisJobsOpen: true,
      analysisResultsOpen: false,
      analysisModelOpen: false,
      analysis: 'running',
    }),
  syncAnalysisJobs: (jobs) => {
    const active = jobs.some(
      (job) =>
        job.status === 'queued' ||
        job.status === 'validating' ||
        job.status === 'running' ||
        job.status === 'postprocessing',
    )
    set({
      analysisLatestJob: jobs[0] ?? get().analysisLatestJob,
      analysis: active ? 'running' : 'idle',
    })
  },
  openAnalysisJobs: (analysisLatestJob = get().analysisLatestJob) =>
    set({
      analysisJobsOpen: true,
      analysisResultsOpen: false,
      analysisLatestJob,
      analysisModelOpen: false,
      memberEditOpen: false,
      nodeEditOpen: false,
      axisEditOpen: false,
      axisNamingOpen: false,
      axisTransformOpen: false,
    }),
  closeAnalysisJobs: () => set({ analysisJobsOpen: false }),
  setAnalysisResult: (analysisResultSetId, analysisResultView) =>
    set({
      analysisResultSetId,
      analysisResultView,
      analysisResultsOpen: true,
      analysisJobsOpen: false,
      activeResult: {
        table: '结果表',
        deformation: '变形',
        moment: '弯矩',
        shear: '剪力',
        axial: '轴力',
        reaction: '反力',
        stress: '应力比',
      }[analysisResultView],
    }),
  openAnalysisResults: (view) => {
    const resultSetId = get().analysisResultSetId
    if (!resultSetId) return
    get().setAnalysisResult(resultSetId, view)
  },
  closeAnalysisResults: () => set({ analysisResultsOpen: false }),
  setActiveResult: (activeResult) => set({ activeResult }),
  setActiveSheet: (activeSheet) => set({ activeSheet }),
  openLoadPanel: (loadPanelView = 'member') => set({ tab: 'load', loadPanelView }),
  openAxisEdit: () =>
    set({
      axisEditOpen: true,
      axisNamingOpen: false,
      axisTransformOpen: false,
      nodeEditOpen: false,
      memberEditOpen: false,
    }),
  closeAxisEdit: () => set({ axisEditOpen: false }),
  setAxisEditScope: (axisEditScope) => set({ axisEditScope }),
  toggleAxisEditScope: () =>
    set((s) => ({ axisEditScope: s.axisEditScope === 'level' ? 'all' : 'level' })),
  openAxisNaming: () =>
    set({
      axisNamingOpen: true,
      axisEditOpen: false,
      axisTransformOpen: false,
      nodeEditOpen: false,
      memberEditOpen: false,
    }),
  closeAxisNaming: () => set({ axisNamingOpen: false }),
  openAxisTransform: (mode = 'move') =>
    set({
      axisTransformOpen: true,
      axisTransformPreset: mode,
      axisNamingOpen: false,
      axisEditOpen: false,
      nodeEditOpen: false,
      memberEditOpen: false,
    }),
  closeAxisTransform: () => set({ axisTransformOpen: false }),
  openNodeEdit: () =>
    set({
      nodeEditOpen: true,
      axisTransformOpen: false,
      axisNamingOpen: false,
      axisEditOpen: false,
      memberEditOpen: false,
    }),
  closeNodeEdit: () => set({ nodeEditOpen: false }),
  openMemberEdit: () =>
    set({
      memberEditOpen: true,
      nodeEditOpen: false,
      axisTransformOpen: false,
      axisNamingOpen: false,
      axisEditOpen: false,
    }),
  closeMemberEdit: () => set({ memberEditOpen: false }),
  startMemberAxisAnglePick: (memberId) => {
    const member = useScene.getState().nodes[memberId as AnyNodeId]
    if (member?.type !== 'structural-member') throw new Error('所选结构构件不存在')
    if (member.locked) throw new Error('构件已锁定，不能取轴线角')
    useEditor.getState().setTool(null)
    set({
      memberAxisAnglePickMemberId: memberId,
      memberAxisAnglePickOriginTool: useEditor.getState().tool,
      memberEditOpen: false,
      columnDialogOpen: false,
      beamDialogOpen: false,
      wallDialogOpen: false,
    })
    useViewer.getState().setSelection({ selectedIds: [member.id] })
  },
  clearMemberAxisAnglePick: () =>
    set({
      memberAxisAnglePickMemberId: null,
      memberAxisAnglePickOriginTool: null,
    }),
  finishMemberAxisAnglePick: (memberId) => {
    set({
      memberAxisAnglePickMemberId: null,
      memberAxisAnglePickOriginTool: null,
    })
    if (useScene.getState().nodes[memberId as AnyNodeId]?.type === 'structural-member') {
      useViewer.getState().setSelection({ selectedIds: [memberId as AnyNodeId] })
    }
  },
  cancelMemberAxisAnglePick: () => {
    const memberId = get().memberAxisAnglePickMemberId
    set({
      memberAxisAnglePickMemberId: null,
      memberAxisAnglePickOriginTool: null,
    })
    if (
      memberId &&
      useScene.getState().nodes[memberId as AnyNodeId]?.type === 'structural-member'
    ) {
      useViewer.getState().setSelection({ selectedIds: [memberId as AnyNodeId] })
    }
  },
  openAnalysisModel: () =>
    set({
      analysisModelOpen: true,
      analysisJobsOpen: false,
      analysisResultsOpen: false,
      memberEditOpen: false,
      nodeEditOpen: false,
      axisEditOpen: false,
      axisNamingOpen: false,
      axisTransformOpen: false,
    }),
  closeAnalysisModel: () => set({ analysisModelOpen: false }),
  openMemberLayout: () =>
    set({
      memberLayoutOpen: true,
      memberEditOpen: false,
      analysisModelOpen: false,
      nodeEditOpen: false,
    }),
  closeMemberLayout: () => set({ memberLayoutOpen: false }),
  openRevisionHistory: () =>
    set({
      revisionHistoryOpen: true,
      analysisJobsOpen: false,
      analysisResultsOpen: false,
      analysisModelOpen: false,
      memberLayoutOpen: false,
      memberEditOpen: false,
      nodeEditOpen: false,
      axisEditOpen: false,
      axisNamingOpen: false,
      axisTransformOpen: false,
    }),
  closeRevisionHistory: () => set({ revisionHistoryOpen: false }),
  openDrawingOutput: () =>
    set({
      drawingOutputOpen: true,
      revisionHistoryOpen: false,
      analysisJobsOpen: false,
      analysisResultsOpen: false,
      analysisModelOpen: false,
      memberLayoutOpen: false,
      memberEditOpen: false,
      nodeEditOpen: false,
    }),
  closeDrawingOutput: () => set({ drawingOutputOpen: false }),
  openIfcImport: () => {
    get().closeAllPanels()
    set({ ifcImportOpen: true })
  },
  closeIfcImport: () => set({ ifcImportOpen: false }),
  openColumnDialog: () =>
    set({
      columnDialogOpen: true,
      nodePlaceDialogOpen: false,
      memberLayoutOpen: false,
      memberEditOpen: false,
      nodeEditOpen: false,
      wallDialogOpen: false,
    }),
  closeColumnDialog: () => set({ columnDialogOpen: false }),
  hydrateSectionLibrary: (library, projectId = null) => {
    const normalized = normalizeSectionLibrary(library)
    const current = get()
    if (
      current.sectionLibraryProjectId === projectId &&
      haveSameSectionLibrary(sectionLibraryFromState(current), normalized)
    ) {
      return
    }
    set({
      columnSections: normalized.columns,
      beamSections: normalized.beams,
      activeColumnSectionId: normalized.activeColumnSectionId,
      activeBeamSectionId: normalized.activeBeamSectionId,
      sectionLibraryProjectId: projectId,
      memberAxisAnglePickMemberId:
        current.sectionLibraryProjectId === projectId ? current.memberAxisAnglePickMemberId : null,
      memberAxisAnglePickOriginTool:
        current.sectionLibraryProjectId === projectId
          ? current.memberAxisAnglePickOriginTool
          : null,
    })
  },
  createColumnSection: (section) => {
    const state = get()
    const id = nextDefinitionId(
      'CS',
      state.columnSections.map((item) => item.id),
    )
    const created = normalizeColumnSection({
      ...section,
      id,
      label: sectionLabel(section),
    })
    if (!created) throw new Error('柱截面定义不合法')
    set((state) => ({
      columnSections: [...state.columnSections, created],
      activeColumnSectionId: created.id,
    }))
    commitSectionLibraryScene(sectionLibraryFromState(get()))
    return created
  },
  updateColumnSection: (id, patch) => {
    const current = get().columnSections.find((section) => section.id === id)
    if (!current) return
    const candidate = { ...current, ...patch }
    const next = normalizeColumnSection({ ...candidate, label: sectionLabel(candidate) })
    if (!next) {
      get().pushLog('柱截面参数不合法，未应用修改', 'error')
      return
    }
    set((state) => ({
      columnSections: state.columnSections.map((section) => (section.id === id ? next : section)),
    }))
    commitSectionLibraryScene(
      sectionLibraryFromState(get()),
      linkedMembers(id, 'column').map((member) => ({
        id: member.id as AnyNodeId,
        data: { section: next.label, material: next.material },
      })),
    )
  },
  deleteColumnSection: (id) => {
    const state = get()
    const section = state.columnSections.find((item) => item.id === id)
    if (!section) return { deleted: false, reason: '柱截面不存在' }
    if (state.columnSections.length <= 1) {
      const reason = '工程至少需要保留一个柱截面定义'
      get().pushLog(reason, 'error')
      return { deleted: false, reason }
    }
    const referenceCount = linkedMembers(id, 'column').length
    if (referenceCount > 0) {
      const reason = `柱截面 ${section.label} 正在被 ${referenceCount} 根柱引用，不能删除`
      get().pushLog(reason, 'error')
      return { deleted: false, reason }
    }
    const columnSections = state.columnSections.filter((item) => item.id !== id)
    set({
      columnSections,
      activeColumnSectionId:
        state.activeColumnSectionId === id
          ? (columnSections[0]?.id ?? state.activeColumnSectionId)
          : state.activeColumnSectionId,
    })
    commitSectionLibraryScene(sectionLibraryFromState(get()))
    return { deleted: true }
  },
  setActiveColumnSection: (id) => {
    if (!get().columnSections.some((section) => section.id === id)) return
    set({ activeColumnSectionId: id })
    commitSectionLibraryScene(sectionLibraryFromState(get()))
  },
  setColumnPlacement: (patch) => {
    const clamp = (value: number | undefined, current: number, min: number, max: number) => {
      if (value === undefined || !Number.isFinite(value)) return current
      return Math.max(min, Math.min(max, value))
    }
    set((state) => ({
      columnOffsetX: clamp(patch.offsetX, state.columnOffsetX, -5, 5),
      columnOffsetZ: clamp(patch.offsetZ, state.columnOffsetZ, -5, 5),
      columnRotation: clamp(patch.rotation, state.columnRotation, -180, 180),
      columnBaseOffset: clamp(patch.baseOffset, state.columnBaseOffset, -10, 20),
    }))
  },
  createBeamSection: (section) => {
    const state = get()
    const id = nextDefinitionId(
      'BS',
      state.beamSections.map((item) => item.id),
    )
    const created = normalizeBeamSection({
      ...section,
      id,
      label: sectionLabel(section),
    })
    if (!created) throw new Error('梁截面定义不合法')
    set((state) => ({
      beamSections: [...state.beamSections, created],
      activeBeamSectionId: created.id,
    }))
    commitSectionLibraryScene(sectionLibraryFromState(get()))
    return created
  },
  updateBeamSection: (id, patch) => {
    const current = get().beamSections.find((section) => section.id === id)
    if (!current) return
    const candidate = { ...current, ...patch }
    const next = normalizeBeamSection({ ...candidate, label: sectionLabel(candidate) })
    if (!next) {
      get().pushLog('梁截面参数不合法，未应用修改', 'error')
      return
    }
    set((state) => ({
      beamSections: state.beamSections.map((section) => (section.id === id ? next : section)),
    }))
    commitSectionLibraryScene(
      sectionLibraryFromState(get()),
      linkedMembers(id, 'beam').map((member) => ({
        id: member.id as AnyNodeId,
        data: { section: next.label, material: next.material },
      })),
    )
  },
  deleteBeamSection: (id) => {
    const state = get()
    const section = state.beamSections.find((item) => item.id === id)
    if (!section) return { deleted: false, reason: '梁截面不存在' }
    if (state.beamSections.length <= 1) {
      const reason = '工程至少需要保留一个梁截面定义'
      get().pushLog(reason, 'error')
      return { deleted: false, reason }
    }
    const referenceCount = linkedMembers(id, 'beam').length
    if (referenceCount > 0) {
      const reason = `梁截面 ${section.label} 正在被 ${referenceCount} 根梁引用，不能删除`
      get().pushLog(reason, 'error')
      return { deleted: false, reason }
    }
    const beamSections = state.beamSections.filter((item) => item.id !== id)
    set({
      beamSections,
      activeBeamSectionId:
        state.activeBeamSectionId === id
          ? (beamSections[0]?.id ?? state.activeBeamSectionId)
          : state.activeBeamSectionId,
    })
    commitSectionLibraryScene(sectionLibraryFromState(get()))
    return { deleted: true }
  },
  setActiveBeamSection: (id) => {
    if (!get().beamSections.some((section) => section.id === id)) return
    set({ activeBeamSectionId: id })
    commitSectionLibraryScene(sectionLibraryFromState(get()))
  },
  setBeamPlacement: (patch) => {
    const clamp = (value: number | undefined, current: number, min: number, max: number) => {
      if (value === undefined || !Number.isFinite(value)) return current
      return Math.max(min, Math.min(max, value))
    }
    set((state) => ({
      beamOffsetZ: clamp(patch.offsetZ, state.beamOffsetZ, -5, 5),
      beamTopOffsetStart: clamp(patch.topOffsetStart, state.beamTopOffsetStart, -10, 10),
      beamTopOffsetEnd: clamp(patch.topOffsetEnd, state.beamTopOffsetEnd, -10, 10),
      beamRotation: clamp(patch.rotation, state.beamRotation, -180, 180),
    }))
  },
  openNodePlaceDialog: () =>
    set({
      nodePlaceDialogOpen: true,
      columnDialogOpen: false,
      beamDialogOpen: false,
      memberEditOpen: false,
      nodeEditOpen: false,
      wallDialogOpen: false,
    }),
  closeNodePlaceDialog: () => set({ nodePlaceDialogOpen: false }),
  setNodePlacement: (patch) => {
    const clamp = (value: number | undefined, current: number, min: number, max: number) => {
      if (value === undefined || !Number.isFinite(value)) return current
      return Math.max(min, Math.min(max, value))
    }
    set((state) => ({
      nodeLabelPrefix:
        patch.labelPrefix !== undefined
          ? patch.labelPrefix.trim().slice(0, 8) || state.nodeLabelPrefix
          : state.nodeLabelPrefix,
      nodeLabelStart: Math.round(clamp(patch.labelStart, state.nodeLabelStart, 1, 9999)),
      nodeElevationOffset: clamp(patch.elevationOffset, state.nodeElevationOffset, -10, 20),
      nodeMarkerRadiusMm: clamp(patch.markerRadiusMm, state.nodeMarkerRadiusMm, 20, 500),
      nodeSupport: patch.support ?? state.nodeSupport,
      nodeShowLabel: patch.showLabel ?? state.nodeShowLabel,
      nodeLocked: patch.locked ?? state.nodeLocked,
    }))
  },
  openNodeElevationDialog: (mode) =>
    set({
      nodeElevationDialogOpen: true,
      nodeElevationMode: mode,
      nodePlaceDialogOpen: false,
      columnDialogOpen: false,
      beamDialogOpen: false,
      nodeEditOpen: false,
    }),
  closeNodeElevationDialog: () => set({ nodeElevationDialogOpen: false }),
  openBeamDialog: () =>
    set({
      beamDialogOpen: true,
      nodePlaceDialogOpen: false,
      columnDialogOpen: false,
      memberLayoutOpen: false,
      memberEditOpen: false,
      wallDialogOpen: false,
    }),
  closeBeamDialog: () => set({ beamDialogOpen: false }),
  openWallDialog: () =>
    set({
      wallDialogOpen: true,
      beamDialogOpen: false,
      nodePlaceDialogOpen: false,
      columnDialogOpen: false,
      memberLayoutOpen: false,
      memberEditOpen: false,
    }),
  closeWallDialog: () => set({ wallDialogOpen: false }),
  openLevelParams: () => set({ levelParamsOpen: true }),
  closeLevelParams: () => set({ levelParamsOpen: false }),
  closeAllPanels: () =>
    set({
      axisEditOpen: false,
      axisNamingOpen: false,
      axisTransformOpen: false,
      nodeEditOpen: false,
      memberEditOpen: false,
      memberAxisAnglePickMemberId: null,
      memberAxisAnglePickOriginTool: null,
      analysisModelOpen: false,
      analysisJobsOpen: false,
      analysisResultsOpen: false,
      memberLayoutOpen: false,
      revisionHistoryOpen: false,
      drawingOutputOpen: false,
      ifcImportOpen: false,
      columnDialogOpen: false,
      nodePlaceDialogOpen: false,
      nodeElevationDialogOpen: false,
      beamDialogOpen: false,
      wallDialogOpen: false,
      levelParamsOpen: false,
    }),
  pushLog: (text, level = 'info') => {
    logSeq += 1
    const entry: LogEntry = { id: logSeq, time: timestamp(), level, text }
    set((s) => ({ log: [...s.log, entry].slice(-MAX_LOG) }))
  },
  pushHistory: (text) => {
    const trimmed = text.trim()
    if (!trimmed) return
    const history = get().history
    if (history[history.length - 1] === trimmed) return
    set({ history: [...history, trimmed].slice(-MAX_HISTORY) })
  },
  reset: () => {
    const defaults = cloneSectionLibrary(DEFAULT_SECTION_LIBRARY)
    set({
      ...initialState,
      columnSections: defaults.columns,
      beamSections: defaults.beams,
      activeColumnSectionId: defaults.activeColumnSectionId,
      activeBeamSectionId: defaults.activeBeamSectionId,
      sectionLibraryProjectId: null,
      members: [],
      loads: [],
      log: [],
      history: [],
    })
  },
}))

export function currentSectionLibrary(): SectionLibrary {
  return sectionLibraryFromState(useStructStore.getState())
}

export function syncSectionLibraryFromScene(projectId: string): boolean {
  const scene = useScene.getState()
  const meta = readStructProjectMeta({
    nodes: scene.nodes,
    rootNodeIds: scene.rootNodeIds,
  } as SceneGraph)
  if (!meta || meta.id !== projectId) return false
  const current = useStructStore.getState()
  if (
    current.sectionLibraryProjectId === projectId &&
    haveSameSectionLibrary(sectionLibraryFromState(current), meta.sectionLibrary)
  ) {
    return false
  }
  current.hydrateSectionLibrary(meta.sectionLibrary, projectId)
  return true
}
