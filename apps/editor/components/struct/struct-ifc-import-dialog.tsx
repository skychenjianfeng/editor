'use client'

import type { SceneGraph } from '@pascal-app/editor'
import { convertIfcToPascal } from '@pascal-app/ifc-converter'
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  FileUp,
  Layers3,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useId, useRef, useState } from 'react'
import {
  type IfcGraphSummary,
  type IfcProjectImport,
  prepareIfcProjectImport,
} from '@/lib/struct/ifc-import'
import { createCloudStructProject } from '@/lib/struct/project-cloud'
import { useStructStore } from './struct-store'

export type IfcImportViewState =
  | { phase: 'idle' }
  | { phase: 'reading' | 'converting'; fileName: string; message: string; percent: number }
  | { phase: 'review'; fileName: string; projectName: string; summary: IfcGraphSummary }
  | { phase: 'creating'; fileName: string; projectName: string; summary: IfcGraphSummary }
  | { phase: 'error'; fileName: string | null; message: string }

export type IfcImportDialogViewProps = {
  state: IfcImportViewState
  onChooseFile: () => void
  onDropFile: (file: File) => void
  onProjectNameChange: (projectName: string) => void
  onConfirm: () => void
  onCancel: () => void
  onRetry: () => void
}

export type IfcGraphValidation =
  | { ok: true; renderableNodeCount: number }
  | {
      ok: false
      reason: 'empty' | 'no-renderable-geometry'
      message: string
    }

type UnknownRecord = Record<string, unknown>

function record(value: unknown): UnknownRecord | null {
  return value !== null && typeof value === 'object' ? (value as UnknownRecord) : null
}

function finitePositive(value: unknown): boolean {
  return typeof value === 'number' && Number.isFinite(value) && value > 0
}

function pointPair(value: unknown): [number, number] | null {
  if (!Array.isArray(value) || value.length < 2) return null
  const [first, second] = value
  return typeof first === 'number' &&
    Number.isFinite(first) &&
    typeof second === 'number' &&
    Number.isFinite(second)
    ? [first, second]
    : null
}

function drawablePolygon(value: unknown): boolean {
  return (
    Array.isArray(value) && value.length >= 3 && value.every((point) => pointPair(point) !== null)
  )
}

function drawableImportedMesh(node: UnknownRecord): boolean {
  const primitives = Array.isArray(node.primitives) ? node.primitives : []
  return primitives.some((value) => {
    const primitive = record(value)
    if (!primitive) return false
    const positions = Array.isArray(primitive.positions) ? primitive.positions : []
    const indices = Array.isArray(primitive.indices) ? primitive.indices : []
    return positions.length >= 9 && indices.length >= 3
  })
}

function isRenderableNode(value: unknown): boolean {
  const node = record(value)
  if (!node) return false

  switch (node.type) {
    case 'imported-mesh':
      return drawableImportedMesh(node)
    case 'wall': {
      const start = pointPair(node.start)
      const end = pointPair(node.end)
      return (
        start !== null &&
        end !== null &&
        Math.hypot(end[0] - start[0], end[1] - start[1]) > 1e-6 &&
        finitePositive(node.thickness) &&
        finitePositive(node.height)
      )
    }
    case 'slab':
    case 'zone':
    case 'ceiling':
      return drawablePolygon(node.polygon)
    case 'column':
      return finitePositive(node.height) && finitePositive(node.radius)
    case 'block': {
      const topology = record(node.topology)
      const vertices = Array.isArray(topology?.vertices) ? topology.vertices : []
      const faces = Array.isArray(topology?.faces) ? topology.faces : []
      return (
        vertices.length >= 3 &&
        faces.some((value) => {
          const face = record(value)
          return Array.isArray(face?.vertexIds) && face.vertexIds.length >= 3
        })
      )
    }
    case 'roof':
    case 'roof-segment':
      return Array.isArray(node.children) && node.children.length > 0
    default:
      return false
  }
}

export function validateIfcConversionGraph(graph: SceneGraph): IfcGraphValidation {
  const nodeCount = Object.keys(graph.nodes).length
  if (nodeCount === 0) {
    return {
      ok: false,
      reason: 'empty',
      message: 'IFC 转换结果为空，未生成任何工程节点',
    }
  }

  const renderableNodeCount = Object.keys(graph.nodes).filter((id) =>
    isRenderableNode(graph.nodes[id]),
  ).length
  if (renderableNodeCount === 0) {
    return {
      ok: false,
      reason: 'no-renderable-geometry',
      message: 'IFC 中没有可渲染几何，已停止创建工程',
    }
  }

  return { ok: true, renderableNodeCount }
}

export function isIfcFileName(fileName: string): boolean {
  return /\.ifc$/i.test(fileName.trim())
}

function defaultProjectName(fileName: string): string {
  return fileName.replace(/\.ifc$/i, '').trim() || 'IFC 导入工程'
}

function errorMessage(cause: unknown, fallback: string): string {
  return cause instanceof Error && cause.message.trim() ? cause.message : fallback
}

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(Number.isFinite(value) ? value : 0)))
}

export function StructIfcImportDialog() {
  const open = useStructStore((state) => state.ifcImportOpen)
  const closeIfcImport = useStructStore((state) => state.closeIfcImport)
  const router = useRouter()
  const [state, setState] = useState<IfcImportViewState>({ phase: 'idle' })
  const runIdRef = useRef(0)
  const lastFileRef = useRef<File | null>(null)
  const convertedGraphRef = useRef<SceneGraph | null>(null)
  const preparedRef = useRef<IfcProjectImport | null>(null)
  const creatingRef = useRef(false)

  const reset = useCallback(() => {
    runIdRef.current += 1
    creatingRef.current = false
    lastFileRef.current = null
    convertedGraphRef.current = null
    preparedRef.current = null
    setState({ phase: 'idle' })
  }, [])

  useEffect(() => {
    if (open) return
    reset()
  }, [open, reset])

  const cancel = () => {
    if (creatingRef.current) return
    reset()
    closeIfcImport()
  }

  const processFile = async (file: File) => {
    if (!isIfcFileName(file.name)) {
      runIdRef.current += 1
      creatingRef.current = false
      lastFileRef.current = file
      convertedGraphRef.current = null
      preparedRef.current = null
      setState({
        phase: 'error',
        fileName: file.name,
        message: '仅支持 .ifc 文件，未创建工程',
      })
      return
    }

    const runId = ++runIdRef.current
    creatingRef.current = false
    lastFileRef.current = file
    convertedGraphRef.current = null
    preparedRef.current = null
    setState({
      phase: 'reading',
      fileName: file.name,
      message: '正在读取 IFC 文件…',
      percent: 0,
    })

    try {
      const buffer = await file.arrayBuffer()
      if (runId !== runIdRef.current) return
      setState({
        phase: 'converting',
        fileName: file.name,
        message: '正在初始化 IFC 转换器…',
        percent: 0,
      })
      const converted = (await convertIfcToPascal(
        new Uint8Array(buffer),
        (message, percent) => {
          if (runId !== runIdRef.current) return
          setState({
            phase: 'converting',
            fileName: file.name,
            message,
            percent: clampPercent(percent),
          })
        },
        { wasmPath: '/' },
      )) as SceneGraph
      if (runId !== runIdRef.current) return

      const name = defaultProjectName(file.name)
      const prepared = prepareIfcProjectImport({
        graph: converted,
        projectName: name,
        sourceFile: file.name,
      })
      const validation = validateIfcConversionGraph(prepared.graph)
      if (!validation.ok) {
        preparedRef.current = null
        convertedGraphRef.current = null
        setState({ phase: 'error', fileName: file.name, message: validation.message })
        return
      }

      convertedGraphRef.current = converted
      preparedRef.current = prepared
      setState({
        phase: 'review',
        fileName: file.name,
        projectName: name,
        summary: prepared.summary,
      })
    } catch (cause) {
      if (runId !== runIdRef.current) return
      preparedRef.current = null
      convertedGraphRef.current = null
      setState({
        phase: 'error',
        fileName: file.name,
        message: errorMessage(cause, 'IFC 转换失败，未创建工程'),
      })
    }
  }

  const createProject = async (prepared: IfcProjectImport) => {
    if (creatingRef.current) return
    const runId = ++runIdRef.current
    creatingRef.current = true
    preparedRef.current = prepared
    setState({
      phase: 'creating',
      fileName: prepared.summary.sourceFile,
      projectName: prepared.meta.name,
      summary: prepared.summary,
    })

    try {
      await createCloudStructProject(prepared.meta, prepared.graph)
      if (runId !== runIdRef.current) return
      creatingRef.current = false
      setState({ phase: 'idle' })
      closeIfcImport()
      router.push(`/struct/${encodeURIComponent(prepared.meta.id)}`)
    } catch (cause) {
      if (runId !== runIdRef.current) return
      creatingRef.current = false
      setState({
        phase: 'error',
        fileName: prepared.summary.sourceFile,
        message: errorMessage(cause, '工程创建失败，请检查网络后重试'),
      })
    }
  }

  const confirm = () => {
    if (creatingRef.current || state.phase !== 'review') return
    const converted = convertedGraphRef.current
    const projectName = state.projectName.trim()
    if (!converted || !projectName) return

    const prepared = prepareIfcProjectImport({
      graph: converted,
      projectName,
      sourceFile: state.fileName,
    })
    const validation = validateIfcConversionGraph(prepared.graph)
    if (!validation.ok) {
      setState({
        phase: 'error',
        fileName: state.fileName,
        message: validation.message,
      })
      return
    }
    void createProject(prepared)
  }

  const retry = () => {
    if (creatingRef.current) return
    const prepared = preparedRef.current
    const file = lastFileRef.current
    reset()
    if (prepared) {
      void createProject(prepared)
      return
    }
    if (file) void processFile(file)
  }

  if (!open) return null

  return (
    <IfcImportDialogView
      onCancel={cancel}
      onChooseFile={() => {
        if (state.phase === 'error') {
          runIdRef.current += 1
          preparedRef.current = null
          convertedGraphRef.current = null
          setState({ phase: 'idle' })
        }
      }}
      onConfirm={confirm}
      onDropFile={(file) => void processFile(file)}
      onProjectNameChange={(projectName) =>
        setState((current) => (current.phase === 'review' ? { ...current, projectName } : current))
      }
      onRetry={retry}
      state={state}
    />
  )
}

export function IfcImportDialogView({
  state,
  onChooseFile,
  onDropFile,
  onProjectNameChange,
  onConfirm,
  onCancel,
  onRetry,
}: IfcImportDialogViewProps) {
  const titleId = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const creating = state.phase === 'creating'
  const review = state.phase === 'review' || state.phase === 'creating'
  const progress = state.phase === 'reading' || state.phase === 'converting' ? state.percent : 0

  const chooseFile = () => {
    if (creating) return
    onChooseFile()
    inputRef.current?.click()
  }

  return (
    <section
      aria-labelledby={titleId}
      aria-modal="true"
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      data-testid="struct-ifc-import-dialog"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && !creating) {
          event.preventDefault()
          event.stopPropagation()
          onCancel()
        }
      }}
      role="dialog"
      tabIndex={-1}
    >
      <div className="flex max-h-[88vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl border border-border bg-background shadow-2xl">
        <header className="flex items-start gap-3 border-b border-border px-5 py-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sky-500/10 text-sky-600">
            <FileUp className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold" id={titleId}>
              导入 IFC 工程
            </h2>
            <p className="mt-1 text-[11px] text-muted-foreground">
              支持 IFC2X3 / IFC4，导入后创建一个新的独立 StructWeb 工程。
            </p>
          </div>
          <button
            aria-label="关闭"
            className="ml-auto rounded p-1 text-muted-foreground hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
            disabled={creating}
            onClick={onCancel}
            type="button"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <input
            accept=".ifc,application/x-step"
            aria-label="选择 IFC 文件"
            className="hidden"
            disabled={creating}
            onChange={(event) => {
              const file = event.currentTarget.files?.[0]
              event.currentTarget.value = ''
              if (file) onDropFile(file)
            }}
            ref={inputRef}
            type="file"
          />

          {state.phase === 'idle' ? (
            <div
              className={`flex min-h-56 flex-col items-center justify-center rounded-xl border border-dashed px-6 text-center transition ${
                dragging
                  ? 'border-sky-400 bg-sky-500/10'
                  : 'border-border bg-muted/20 hover:border-sky-300'
              }`}
              onDragLeave={() => setDragging(false)}
              onDragOver={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDrop={(event) => {
                event.preventDefault()
                setDragging(false)
                const file = event.dataTransfer.files[0]
                if (file) onDropFile(file)
              }}
            >
              <UploadCloud className="h-9 w-9 text-sky-500" />
              <div className="mt-3 text-sm font-medium">拖入 IFC 文件</div>
              <div className="mt-1 max-w-sm text-[11px] leading-relaxed text-muted-foreground">
                只接受扩展名为 .ifc 的文件。转换在浏览器内完成，不会覆盖当前工程。
              </div>
              <button
                className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-[11px] font-medium text-white hover:bg-blue-700"
                onClick={chooseFile}
                type="button"
              >
                选择 IFC 文件
              </button>
            </div>
          ) : null}

          {state.phase === 'reading' || state.phase === 'converting' ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/20 px-4 py-3">
                <Loader2 className="h-5 w-5 shrink-0 animate-spin text-sky-600" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-xs font-medium">{state.fileName}</div>
                  <div className="mt-0.5 text-[10px] text-muted-foreground">{state.message}</div>
                </div>
                <div className="font-mono text-sm font-semibold text-sky-600">{state.percent}%</div>
              </div>
              <div
                aria-label="IFC 转换进度"
                aria-valuemax={100}
                aria-valuemin={0}
                aria-valuenow={progress}
                className="h-2 overflow-hidden rounded-full bg-muted"
                data-testid="ifc-import-progress"
                role="progressbar"
              >
                <div
                  className="h-full rounded-full bg-sky-500 transition-[width] duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="rounded-md border border-sky-200/60 bg-sky-50 px-3 py-2 text-[10px] leading-relaxed text-sky-800">
                转换期间可取消；取消或重新选择后，旧转换结果不会覆盖当前状态。
              </div>
            </div>
          ) : null}

          {review ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/20 px-4 py-3">
                <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-xs font-medium">{state.fileName}</div>
                  <div className="mt-0.5 text-[10px] text-muted-foreground">
                    转换完成，请确认工程名称后创建
                  </div>
                </div>
                <span className="rounded bg-emerald-100 px-2 py-1 text-[9px] font-medium text-emerald-700">
                  IFC READY
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <SummaryCard label="节点总数" value={state.summary.nodeCount} />
                <SummaryCard label="楼层" value={`${state.summary.levelCount} 层`} />
                <SummaryCard label="导入实体" value={state.summary.importedMeshCount} />
              </div>

              <div>
                <div className="mb-2 text-[10px] font-medium text-muted-foreground">节点类型</div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(state.summary.typeCounts)
                    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
                    .map(([type, count]) => (
                      <span
                        className="rounded-full border border-border bg-muted/40 px-2 py-1 text-[9px] text-muted-foreground"
                        key={type}
                      >
                        {type} <strong className="font-semibold text-foreground">{count}</strong>
                      </span>
                    ))}
                </div>
              </div>

              <label className="block text-[10px] text-muted-foreground">
                工程名称
                <input
                  className="mt-1 h-9 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/15 disabled:opacity-60"
                  disabled={creating}
                  maxLength={200}
                  onChange={(event) => onProjectNameChange(event.target.value)}
                  value={state.projectName}
                />
              </label>
            </div>
          ) : null}

          {state.phase === 'error' ? (
            <div className="space-y-4">
              <div className="flex items-start gap-3 rounded-lg border border-rose-300/60 bg-rose-50 px-4 py-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
                <div className="min-w-0">
                  <div className="text-xs font-medium text-rose-900">
                    {state.fileName ?? 'IFC 文件'}
                  </div>
                  <div className="mt-1 text-[11px] leading-relaxed text-rose-800" role="alert">
                    {state.message}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>

        <div className="flex items-start gap-2 border-t border-amber-300/50 bg-amber-50 px-5 py-2 text-[10px] leading-relaxed text-amber-900">
          <Layers3 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          第一阶段不参与结构统计和 analysis-model。导入内容用于查看与通用编辑。
        </div>

        <footer className="flex flex-wrap items-center gap-2 border-t border-border bg-muted/15 px-5 py-3">
          <div className="min-w-0 flex-1 text-[9px] text-muted-foreground">
            {review
              ? `来源：${state.fileName}`
              : '当前工程保持不变；只有创建成功后才会进入新工程。'}
          </div>
          {review ? (
            <>
              <button
                className="rounded-md border border-border px-3 py-1.5 text-[11px] hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
                data-testid="ifc-import-reselect"
                disabled={creating}
                onClick={chooseFile}
                type="button"
              >
                重新选择
              </button>
              <button
                className="rounded-md border border-border px-3 py-1.5 text-[11px] hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
                data-testid="ifc-import-cancel"
                disabled={creating}
                onClick={onCancel}
                type="button"
              >
                取消
              </button>
              <button
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-1.5 text-[11px] font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
                data-testid="ifc-import-create"
                disabled={creating || state.projectName.trim().length === 0}
                onClick={onConfirm}
                type="button"
              >
                {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                {creating ? '正在创建…' : '创建工程'}
              </button>
            </>
          ) : state.phase === 'error' ? (
            <>
              <button
                className="rounded-md border border-border px-3 py-1.5 text-[11px] hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
                disabled={creating}
                onClick={chooseFile}
                type="button"
              >
                重新选择
              </button>
              <button
                className="rounded-md border border-border px-3 py-1.5 text-[11px] hover:bg-muted"
                onClick={onCancel}
                type="button"
              >
                取消
              </button>
              <button
                className="rounded-md bg-blue-600 px-4 py-1.5 text-[11px] font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
                data-testid="ifc-import-retry"
                disabled={creating || state.fileName === null}
                onClick={onRetry}
                type="button"
              >
                重试
              </button>
            </>
          ) : state.phase === 'reading' || state.phase === 'converting' ? (
            <button
              className="rounded-md border border-border px-3 py-1.5 text-[11px] hover:bg-muted"
              onClick={onCancel}
              type="button"
            >
              取消转换
            </button>
          ) : (
            <button
              className="rounded-md border border-border px-3 py-1.5 text-[11px] hover:bg-muted"
              onClick={onCancel}
              type="button"
            >
              取消
            </button>
          )}
        </footer>
      </div>
    </section>
  )
}

function SummaryCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/20 px-3 py-2.5">
      <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground">
        <Building2 className="h-3 w-3" />
        {label}
      </div>
      <div className="mt-1 font-mono text-lg font-semibold tabular-nums">{value}</div>
    </div>
  )
}
