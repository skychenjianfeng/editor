'use client'

import {
  applySceneGraphToEditor,
  Editor,
  getSavedSceneDocument,
  type SaveStatus,
  type SceneGraph,
  type SidebarTab,
  useScene,
  useViewer,
  ViewerToolbarLeft,
} from '@pascal-app/editor'
import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react'
import type { AccountUser } from '@/lib/account-store'
import {
  AnalysisApiError,
  type AnalysisSubmitOutcome,
  createAnalysisJob,
} from '@/lib/analysis-jobs/client'
import { getProjectRevision, RevisionApiError } from '@/lib/struct/revision-client'
import type { RestoreRevisionResponse } from '@/lib/struct/revision-restore'
import { EditorViewerToolbarRight } from '../viewer-toolbar'
import { AxisGridTool } from './axis-grid-tool'
import { useStructCommands } from './command-defs'
import { CommandLine } from './command-line'
import { Ribbon } from './ribbon'
import { StructAnalysisJobsDialog } from './struct-analysis-jobs-dialog'
import { StructAnalysisModelDialog } from './struct-analysis-model-dialog'
import { StructAnalysisResultsPanel } from './struct-analysis-results-panel'
import { StructAxisEditDialog } from './struct-axis-edit-dialog'
import { StructAxisInspector } from './struct-axis-inspector'
import { StructAxisNamingDialog } from './struct-axis-naming-dialog'
import { StructAxisTransformDialog } from './struct-axis-transform-dialog'
import { StructBeamDialog } from './struct-beam-dialog'
import { StructCanvasControls } from './struct-canvas-controls'
import { StructColumnDialog } from './struct-column-dialog'
import { StructDrawingOutputDialog } from './struct-drawing-output-dialog'
import { StructHud } from './struct-hud'
import { StructIfcImportDialog } from './struct-ifc-import-dialog'
import { StructLevelParamsDialog } from './struct-level-params-dialog'
import { StructLoadPanel } from './struct-load-panel'
import { StructMemberEditDialog } from './struct-member-edit-dialog'
import { StructMemberInspector } from './struct-member-inspector'
import { StructMemberLayoutDialog } from './struct-member-layout-dialog'
import { StructMemberPlacementBar } from './struct-member-placement-bar'
import { StructNodeContextMenu } from './struct-node-context-menu'
import { StructNodeEditDialog } from './struct-node-edit-dialog'
import { StructNodeElevationDialog } from './struct-node-elevation-dialog'
import { StructNodeInspector } from './struct-node-inspector'
import { StructNodePlaceDialog } from './struct-node-place-dialog'
import { StructRevisionHistoryDialog } from './struct-revision-history-dialog'
import { StructSlabInspector } from './struct-slab-inspector'
import { syncSectionLibraryFromScene, useStructStore } from './struct-store'
import { StructWallDialog } from './struct-wall-dialog'

const SIDEBAR_TABS: (SidebarTab & { component: React.ComponentType })[] = [
  {
    id: 'site',
    label: '场景',
    component: () => null,
  },
]

const PROJECT_ID = 'struct-prototype'

type StructShellProps = {
  analysisRevision: number
  currentUser: AccountUser
  onLoad?: () => Promise<SceneGraph | null>
  onSave?: (graph: SceneGraph, options?: { keepalive?: boolean }) => Promise<void>
  onAnalysisRevisionChange?: (revision: number) => void
  onRevisionRestored?: (record: RestoreRevisionResponse) => Promise<void> | void
  projectId?: string
  projectName?: string
  projectCode?: string
  notice?: ReactNode
}

export function StructShell({
  analysisRevision,
  currentUser,
  onLoad,
  onSave,
  onAnalysisRevisionChange,
  onRevisionRestored,
  projectId = PROJECT_ID,
  projectName = '示例工程 · 门式刚架厂房',
  projectCode = '',
  notice,
}: StructShellProps) {
  useStructCommands()
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [previewGraph, setPreviewGraph] = useState<SceneGraph | null>(null)
  const [previewVersion, setPreviewVersion] = useState<number | null>(null)
  const [restoringRevision, setRestoringRevision] = useState(false)
  const previewReturnGraphRef = useRef<SceneGraph | null>(null)
  const sceneTheme = useViewer((state) => state.sceneTheme)
  const sceneNodes = useScene((state) => state.nodes)
  const analysisJobsOpen = useStructStore((state) => state.analysisJobsOpen)
  const analysisResultsOpen = useStructStore((state) => state.analysisResultsOpen)
  const analysisResultSetId = useStructStore((state) => state.analysisResultSetId)
  const analysisResultView = useStructStore((state) => state.analysisResultView)
  const analysisLatestJob = useStructStore((state) => state.analysisLatestJob)
  const closeAnalysisJobs = useStructStore((state) => state.closeAnalysisJobs)
  const closeAnalysisResults = useStructStore((state) => state.closeAnalysisResults)
  const openAnalysisModel = useStructStore((state) => state.openAnalysisModel)
  const openAnalysisJobs = useStructStore((state) => state.openAnalysisJobs)
  const setAnalysisResult = useStructStore((state) => state.setAnalysisResult)
  const recordAnalysisJob = useStructStore((state) => state.recordAnalysisJob)
  const syncAnalysisJobs = useStructStore((state) => state.syncAnalysisJobs)
  const revisionHistoryOpen = useStructStore((state) => state.revisionHistoryOpen)
  const closeRevisionHistory = useStructStore((state) => state.closeRevisionHistory)
  const drawingOutputOpen = useStructStore((state) => state.drawingOutputOpen)
  const closeDrawingOutput = useStructStore((state) => state.closeDrawingOutput)
  const activeLevelId = useViewer((state) => state.selection.levelId)
  const activeLevel =
    activeLevelId && sceneNodes[activeLevelId]?.type === 'level' ? sceneNodes[activeLevelId] : null
  const activeLevelName =
    activeLevel?.type === 'level' ? activeLevel.name || `楼层 ${activeLevel.level}` : ''
  const getDrawingGraph = useCallback(() => getSavedSceneDocument(), [])
  useEffect(() => {
    if (sceneTheme !== 'graphite') useViewer.getState().setSceneTheme('graphite')
    syncSectionLibraryFromScene(projectId)
  }, [projectId, sceneTheme])

  useEffect(() => {
    if (!revisionHistoryOpen || analysisRevision > 0) return
    closeRevisionHistory()
    useStructStore.getState().pushLog('版本历史：请先上传云端', 'error')
  }, [analysisRevision, closeRevisionHistory, revisionHistoryOpen])

  const openRevisionPreview = async (version: number) => {
    const response = await getProjectRevision(projectId, version, { includeGraph: true })
    const graph = response.revision.graph
    if (!graph) {
      throw new RevisionApiError('历史 revision 未返回可预览模型', {
        kind: 'request_failed',
        status: 200,
        code: 'missing_graph',
      })
    }
    if (previewReturnGraphRef.current === null) {
      previewReturnGraphRef.current = getSavedSceneDocument()
    }
    setPreviewVersion(version)
    setPreviewGraph(graph)
    closeRevisionHistory()
    useStructStore.getState().pushLog(`只读预览 ${projectId}@${version}`, 'info')
  }

  const exitRevisionPreview = () => {
    const returnGraph = previewReturnGraphRef.current
    if (returnGraph) applySceneGraphToEditor(returnGraph)
    previewReturnGraphRef.current = null
    setPreviewVersion(null)
    setPreviewGraph(null)
    useStructStore.getState().pushLog('已返回当前模型', 'info')
  }

  const handoffRestoredRevision = async (response: RestoreRevisionResponse) => {
    previewReturnGraphRef.current = null
    setPreviewVersion(null)
    setRestoringRevision(true)
    // The Editor prop is the autosave pause switch. Let it commit before the
    // authoritative restore graph is applied so this handoff cannot save.
    setPreviewGraph(response.graph)
    await afterEditorPreviewCommit()
    applySceneGraphToEditor(response.graph)
    await onRevisionRestored?.(response)
    setPreviewGraph(null)
    setRestoringRevision(false)
  }

  const submitAnalysis = async (): Promise<AnalysisSubmitOutcome> => {
    try {
      const { job } = await createAnalysisJob(projectId, analysisRevision)
      recordAnalysisJob(job)
      return { kind: 'submitted', job }
    } catch (cause) {
      if (!(cause instanceof AnalysisApiError)) {
        return {
          kind: 'error',
          message: cause instanceof Error ? cause.message : '分析作业提交失败',
        }
      }
      if (cause.kind === 'revision_conflict') {
        return {
          kind: 'revision_conflict',
          currentRevision: cause.currentRevision,
          message: cause.message,
        }
      }
      if (cause.kind === 'diagnostics') {
        return {
          kind: 'diagnostics',
          diagnostics: cause.diagnostics,
          message: cause.message,
        }
      }
      return { kind: 'error', message: cause.message }
    }
  }

  return (
    <div className="struct-shell flex h-screen w-screen flex-col overflow-hidden bg-background">
      <Ribbon currentUser={currentUser} projectName={projectName} />
      {notice}
      <div className="relative min-h-0 flex-1">
        <Editor
          guardAgainstSceneWipe={false}
          isVersionPreviewMode={previewGraph !== null || restoringRevision}
          layoutVersion="v2"
          onLoad={onLoad}
          onSave={onSave}
          onSaveStatusChange={setSaveStatus}
          projectId={projectId}
          projectName={projectName}
          previewScene={previewGraph ?? undefined}
          sidebarTabs={SIDEBAR_TABS}
          viewerToolbarLeft={<ViewerToolbarLeft />}
          viewerToolbarRight={<EditorViewerToolbarRight />}
        />
        {previewGraph && !restoringRevision ? (
          <div
            className="pointer-events-none absolute top-16 left-1/2 z-40 flex -translate-x-1/2 items-center gap-3 rounded-full border border-sky-400/45 bg-sky-950/90 px-3 py-1.5 text-[11px] text-sky-100 shadow-lg"
            data-testid="revision-preview-banner"
            role="status"
          >
            <span className="font-mono">
              只读预览 {projectId}@{previewVersion}
            </span>
            <button
              className="pointer-events-auto min-h-8 rounded-full border border-sky-300/45 px-2.5 font-medium hover:bg-sky-800/70"
              data-testid="revision-preview-close"
              onClick={exitRevisionPreview}
              type="button"
            >
              返回当前模型
            </button>
          </div>
        ) : null}
        <StructCanvasControls />
        <StructHud />
        <StructIfcImportDialog />
        <StructColumnDialog />
        <StructAxisInspector />
        <StructMemberPlacementBar />
        <StructNodeContextMenu />
        <StructNodeInspector />
        <StructNodePlaceDialog />
        <StructNodeElevationDialog />
        <StructMemberInspector />
        <StructSlabInspector />
        <StructMemberEditDialog />
        <StructMemberLayoutDialog />
        <StructNodeEditDialog />
        <StructLevelParamsDialog />
        <AxisGridTool />
        <StructAxisEditDialog />
        <StructBeamDialog />
        <StructWallDialog />
        <StructAnalysisModelDialog
          analysisRevision={analysisRevision}
          onAnalysisRevisionChange={onAnalysisRevisionChange}
          onOpenJobs={openAnalysisJobs}
          onStartAnalysis={submitAnalysis}
          projectId={projectId}
        />
        <StructAnalysisJobsDialog
          currentRevision={analysisRevision}
          initialJob={analysisLatestJob}
          onClose={closeAnalysisJobs}
          onJobsChange={syncAnalysisJobs}
          onOpenPrecheck={openAnalysisModel}
          onOpenResult={(resultSetId) => setAnalysisResult(resultSetId, 'table')}
          onRetryJob={() => submitAnalysis()}
          open={analysisJobsOpen}
          projectId={projectId}
        />
        <StructAnalysisResultsPanel
          onClose={closeAnalysisResults}
          open={analysisResultsOpen}
          resultSetId={analysisResultSetId}
          view={analysisResultView}
        />
        <StructLoadPanel />
        <StructAxisNamingDialog />
        <StructAxisTransformDialog />
        <StructRevisionHistoryDialog
          currentRevision={analysisRevision}
          onClose={closeRevisionHistory}
          onCurrentRevisionChange={onAnalysisRevisionChange}
          onPreview={openRevisionPreview}
          onRevisionRestored={handoffRestoredRevision}
          open={revisionHistoryOpen}
          projectId={projectId}
        />
        <StructDrawingOutputDialog
          getGraph={getDrawingGraph}
          levelId={activeLevelId}
          levelName={activeLevelName}
          onClose={closeDrawingOutput}
          onGenerated={(record) =>
            useStructStore
              .getState()
              .pushLog(`布置图：${record.fileName}（revision ${record.revision}）`, 'ok')
          }
          open={drawingOutputOpen}
          ownerId={currentUser.id}
          projectCode={projectCode}
          projectId={projectId}
          projectName={projectName}
          revision={analysisRevision}
        />
      </div>
      <CommandLine saveStatus={saveStatus} />
    </div>
  )
}

function afterEditorPreviewCommit(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve()
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => window.requestAnimationFrame(() => resolve()))
  })
}
