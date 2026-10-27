import { AlertCircle, ArrowLeft, FolderKanban, LoaderCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Group, Panel, Separator } from 'react-resizable-panels'
import { Link, useParams } from 'react-router-dom'
import {
  downloadDrawing,
  downloadReport,
  downloadResultsCsv,
  useGeometry,
  useParamSpec,
  useRunCalc,
  type View,
} from '../api/calc'
import { type ProjectRecord, useProject } from '../api/projects'
import { BatchDialog } from '../components/BatchDialog'
import { Canvas, type Layers } from '../components/Canvas'
import { ModuleTree } from '../components/ModuleTree'
import { ParamsPanel } from '../components/ParamsPanel'
import { ResultsTable } from '../components/ResultsTable'
import { RunHistoryDialog } from '../components/RunHistoryDialog'
import { SchemeDialog } from '../components/SchemeDialog'
import { StatusBadge } from '../components/StatusBadge'
import { TopBar } from '../components/TopBar'
import { Button } from '../components/ui/button'

const vHandle = 'w-px bg-[color:var(--color-line)] transition-colors hover:bg-[#3e63dd]'
const hHandle = 'h-px bg-[color:var(--color-line)] transition-colors hover:bg-[#3e63dd]'

function ProjectContextBar({ project }: { project: ProjectRecord }) {
  return (
    <div className="flex min-h-10 shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-[#27473e] bg-[#102a24] px-3 py-1.5 text-[11.5px] text-white">
      <Link
        to="/workspace"
        className="flex items-center gap-1 rounded px-1.5 py-1 text-white/75 hover:bg-white/10 hover:text-white focus-visible:ring-2 focus-visible:ring-lime-200 focus-visible:outline-none"
      >
        <ArrowLeft className="size-3.5" />
        返回项目工作台
      </Link>
      <span className="hidden h-4 w-px bg-white/15 sm:block" />
      <span className="flex min-w-0 items-center gap-1.5 font-medium">
        <FolderKanban className="size-3.5 text-[#bef264]" />
        <span className="max-w-[min(42vw,320px)] truncate">{project.name}</span>
      </span>
      <span className="rounded bg-white/10 px-1.5 py-0.5 text-white/65">{project.region}</span>
      <StatusBadge status={project.status} className="border-white/20" />
      <span className="text-white/55">{project.scheme_count} 个方案</span>
      {project.failed_control_count > 0 && (
        <span className="text-[#fecaca]">{project.failed_control_count} 个控制项不满足</span>
      )}
    </div>
  )
}

function CalcWorkspaceSkeleton() {
  return (
    <main role="status" className="grid min-h-screen place-items-center bg-[#f7f7f8]">
      <div className="flex items-center gap-2 text-sm text-[#52525b]">
        <LoaderCircle className="size-4 animate-spin text-[#176b55]" />
        正在载入项目计算工作区…
      </div>
    </main>
  )
}

function ProjectLoadError({ onRetry }: { onRetry: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center bg-[#f7f7f8] p-6">
      <div className="w-full max-w-md rounded-xl border bg-white p-6 text-center shadow-sm">
        <div className="mx-auto grid size-11 place-items-center rounded-full bg-[#fff1f1] text-destructive">
          <AlertCircle className="size-5" />
        </div>
        <h1 className="mt-3 text-base font-semibold">项目加载失败</h1>
        <p className="mt-1 text-sm text-[#71717a]">计算页必须依附于当前用户可访问的项目。</p>
        <div className="mt-5 flex justify-center gap-2">
          <Button asChild variant="outline">
            <Link to="/workspace">返回项目工作台</Link>
          </Button>
          <Button onClick={onRetry} className="bg-[#176b55] text-white hover:bg-[#125744]">
            重试
          </Button>
        </div>
      </div>
    </main>
  )
}

function CalcWorkspace({ project }: { project: ProjectRecord }) {
  const [module, setModule] = useState('scaffold-fastener')
  const run = useRunCalc(module)
  const spec = useParamSpec(module)
  const [params, setParams] = useState<Record<string, unknown>>({
    h: 1.8,
    la: 1.5,
    lb: 0.9,
    H: 24,
    steel: 'φ48×3.0',
    tie: '两步三跨',
    board: '竹串片脚手板',
    dead: 0.35,
    live: 2.0,
    wind: 0.25,
    foundation: '混凝土',
    fg: 140,
    baseArea: 0.25,
    hBoard: 180,
    braceW: 6.0,
  })
  const [dirty, setDirty] = useState(false)
  const [view, setView] = useState<View>('elevation')
  const [layers, setLayers] = useState<Layers>({
    upright: true,
    level: true,
    brace: true,
    dim: true,
  })
  const [batchOpen, setBatchOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [schemeOpen, setSchemeOpen] = useState(false)
  const [restoreVersion, setRestoreVersion] = useState(0)
  const [schemeName, setSchemeName] = useState<string>()
  const pendingRestore = useRef<{ module: string; params: Record<string, unknown> } | null>(null)
  const geometry = useGeometry(params, view, module)

  useEffect(() => {
    if (!spec.data?.groups || spec.data.module !== module) return
    const pending = pendingRestore.current
    if (pending?.module === module) {
      pendingRestore.current = null
      setParams(pending.params)
      setDirty(false)
      run.mutate(pending.params)
      return
    }
    const next: Record<string, unknown> = {}
    for (const group of spec.data.groups) {
      for (const field of group.fields) {
        next[String(field.key)] = field.default
      }
    }
    setParams(next)
    setDirty(false)
    run.mutate(next)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [module, spec.data, restoreVersion])

  function update(key: string, value: unknown) {
    setParams((current) => ({ ...current, [key]: value }))
    setDirty(true)
  }

  const apiRows = run.data?.results.map((result) => ({
    no: result.no,
    item: result.item,
    value: String(result.value),
    limit: String(result.limit),
    ratio: result.ratio,
    ok: result.ok,
    clause: result.clause,
    control: result.control,
    detail: result.detail,
  }))

  return (
    <div className="flex h-full min-h-0 flex-col bg-[color:var(--color-shell)]">
      <TopBar
        dirty={dirty || run.isPending}
        moduleTitle={spec.data?.title}
        schemeName={schemeName}
        total={run.data?.summary.total}
        onRun={() => {
          setDirty(false)
          run.mutate(params)
        }}
        onExport={() => downloadReport(params, module, spec.data?.title)}
        onBatch={() => setBatchOpen(true)}
        onHistory={() => setHistoryOpen(true)}
        onSchemes={() => setSchemeOpen(true)}
      />

      <Group orientation="vertical" className="min-h-0 flex-1">
        <Panel defaultSize="56%" minSize="34%">
          <Group orientation="horizontal">
            <Panel defaultSize="15%" minSize="12%" maxSize="22%">
              <ModuleTree
                active={module}
                onSelect={(key) => {
                  setModule(key)
                  setSchemeName(undefined)
                }}
              />
            </Panel>
            <Separator className={vHandle} />
            <Panel defaultSize="23%" minSize="18%" maxSize="32%">
              <ParamsPanel groups={spec.data?.groups as never} params={params} onUpdate={update} />
            </Panel>
            <Separator className={vHandle} />
            <Panel defaultSize="62%" minSize="38%">
              <Canvas
                geometry={geometry.data}
                view={view}
                onView={setView}
                layers={layers}
                onLayers={setLayers}
                onExport={(kind) => downloadDrawing(kind, params, view, module, spec.data?.title)}
              />
            </Panel>
          </Group>
        </Panel>
        <Separator className={hHandle} />
        <Panel defaultSize="44%" minSize="22%">
          <ResultsTable
            rows={apiRows}
            verified={run.data?.verified}
            standard={run.data?.standard}
            failed={run.data?.summary.failed}
            standards={run.data?.standards}
            onExportDetail={() => downloadResultsCsv(params, module, spec.data?.title)}
          />
        </Panel>
      </Group>

      <BatchDialog
        open={batchOpen}
        baseParams={params}
        module={module}
        groups={spec.data?.groups}
        onClose={() => setBatchOpen(false)}
      />
      <RunHistoryDialog
        open={historyOpen}
        activeModule={module}
        onClose={() => setHistoryOpen(false)}
        onLoad={(payload) => {
          pendingRestore.current = { module: payload.module, params: payload.params }
          setDirty(false)
          setHistoryOpen(false)
          setSchemeName(undefined)
          setModule(payload.module)
          setRestoreVersion((version) => version + 1)
        }}
      />
      <SchemeDialog
        open={schemeOpen}
        project={project}
        module={module}
        moduleTitle={spec.data?.title}
        params={params}
        lastRunId={run.data?.run_id}
        onClose={() => setSchemeOpen(false)}
        onSaved={(scheme) => {
          setSchemeName(scheme.name)
          setSchemeOpen(false)
        }}
        onOpenScheme={(scheme) => {
          pendingRestore.current = {
            module: scheme.module,
            params: scheme.params,
          }
          setSchemeName(scheme.name)
          setDirty(false)
          setSchemeOpen(false)
          setModule(scheme.module)
          setRestoreVersion((version) => version + 1)
        }}
      />
    </div>
  )
}

export function CalcWorkspacePage() {
  const { projectId } = useParams()
  const project = useProject(projectId)

  if (project.isPending) return <CalcWorkspaceSkeleton />
  if (project.isError || !project.data) {
    return <ProjectLoadError onRetry={() => void project.refetch()} />
  }

  return (
    <div className="flex h-screen min-h-0 flex-col">
      <ProjectContextBar project={project.data} />
      <div className="min-h-0 flex-1">
        <CalcWorkspace project={project.data} />
      </div>
    </div>
  )
}
