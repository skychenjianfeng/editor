import { useEffect, useRef, useState } from 'react'
import { Group, Panel, Separator } from 'react-resizable-panels'
import {
  downloadDrawing,
  downloadReport,
  downloadResultsCsv,
  useGeometry,
  useParamSpec,
  useRunCalc,
  type View,
} from './api/calc'
import { BatchDialog } from './components/BatchDialog'
import { Canvas, type Layers } from './components/Canvas'
import { ModuleTree } from './components/ModuleTree'
import { ParamsPanel } from './components/ParamsPanel'
import { ResultsTable } from './components/ResultsTable'
import { RunHistoryDialog } from './components/RunHistoryDialog'
import { SchemeDialog } from './components/SchemeDialog'
import { TopBar } from './components/TopBar'

const vHandle = 'w-px bg-[color:var(--color-line)] transition-colors hover:bg-[#3e63dd]'
const hHandle = 'h-px bg-[color:var(--color-line)] transition-colors hover:bg-[#3e63dd]'

export default function App() {
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
  const [projectContext, setProjectContext] = useState<{
    projectId: string
    projectName: string
  }>()
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
    setParams((p) => ({ ...p, [key]: value }))
    setDirty(true)
  }

  const apiRows = run.data?.results.map((r) => ({
    no: r.no,
    item: r.item,
    value: String(r.value),
    limit: String(r.limit),
    ratio: r.ratio,
    ok: r.ok,
    clause: r.clause,
    control: r.control,
    detail: r.detail,
  }))

  return (
    <div className="flex h-full flex-col bg-[color:var(--color-shell)]">
      <TopBar
        dirty={dirty || run.isPending}
        moduleTitle={spec.data?.title}
        projectName={projectContext?.projectName}
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
        module={module}
        moduleTitle={spec.data?.title}
        params={params}
        lastRunId={run.data?.run_id}
        selectedProjectId={projectContext?.projectId}
        onClose={() => setSchemeOpen(false)}
        onSaved={(project, scheme) => {
          setProjectContext({
            projectId: project.project_id,
            projectName: project.name,
          })
          setSchemeName(scheme.name)
          setSchemeOpen(false)
        }}
        onOpenScheme={(project, scheme) => {
          pendingRestore.current = {
            module: scheme.module,
            params: scheme.params,
          }
          setProjectContext({
            projectId: project.project_id,
            projectName: project.name,
          })
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
