import { ChevronRight, History, LoaderCircle, RefreshCw, X } from 'lucide-react'
import { useState } from 'react'
import { fetchRunDetail, type RunPayload, type RunRecord, useRuns } from '../api/calc'

type RunHistoryDialogProps = {
  open: boolean
  onClose: () => void
  onLoad: (run: RunPayload) => void
  activeModule?: string
}

function formatTimestamp(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date)
}

function shortRunId(runId: string) {
  return runId.length > 12 ? `${runId.slice(0, 8)}…${runId.slice(-4)}` : runId
}

function errorText(error: unknown) {
  return error instanceof Error ? error.message : String(error)
}

function countValue(value: number | null | undefined) {
  return value ?? 0
}

function HistoryContent({ onClose, onLoad, activeModule }: Omit<RunHistoryDialogProps, 'open'>) {
  const runs = useRuns(50)
  const [scope, setScope] = useState<'all' | 'module'>('all')
  const [loadingRunId, setLoadingRunId] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  const records = runs.data?.runs ?? []
  const visibleRuns =
    scope === 'module' && activeModule
      ? records.filter((record) => record.module === activeModule)
      : records

  async function loadRun(record: RunRecord) {
    setLoadingRunId(record.run_id)
    setLoadError(null)
    try {
      const payload = await fetchRunDetail(record.run_id)
      onLoad(payload)
    } catch (error) {
      setLoadError(errorText(error))
    } finally {
      setLoadingRunId(null)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-[color:var(--color-canvas)]/70 p-6 backdrop-blur-[2px]"
      onClick={onClose}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="run-history-title"
        className="flex max-h-[82vh] w-[860px] flex-col overflow-hidden rounded-lg border border-white/10 bg-[color:var(--color-panel)] text-[color:var(--color-ink)] shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex h-12 shrink-0 items-center gap-2.5 border-b border-[color:var(--color-line)] px-4">
          <History className="h-4 w-4 text-[#3e63dd]" />
          <div>
            <h2 id="run-history-title" className="text-[13px] font-semibold">
              计算历史
            </h2>
            <div className="text-[10px] text-[color:var(--color-ink-3)]">
              最近 50 次运行 · Asia/Shanghai
            </div>
          </div>
          <div className="ml-auto flex items-center gap-1">
            <button
              type="button"
              onClick={() => runs.refetch()}
              disabled={runs.isFetching}
              aria-label="刷新历史"
              className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] px-2 text-[11px] hover:bg-black/[0.03] disabled:cursor-wait disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${runs.isFetching ? 'animate-spin' : ''}`} />
              刷新
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="关闭历史"
              className="grid h-7 w-7 place-items-center rounded-md hover:bg-black/5"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="flex h-10 shrink-0 items-center gap-2 border-b border-[color:var(--color-line)] bg-[color:var(--color-shell)] px-4">
          <div className="flex items-center rounded-md border border-[color:var(--color-line)] bg-white p-0.5">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={`rounded px-2.5 py-1 text-[11px] ${
                scope === 'all'
                  ? 'bg-[color:var(--color-ink)] font-medium text-white'
                  : 'text-[color:var(--color-ink-2)]'
              }`}
            >
              全部
            </button>
            <button
              type="button"
              onClick={() => setScope('module')}
              disabled={!activeModule}
              className={`rounded px-2.5 py-1 text-[11px] disabled:cursor-not-allowed disabled:opacity-40 ${
                scope === 'module'
                  ? 'bg-[color:var(--color-ink)] font-medium text-white'
                  : 'text-[color:var(--color-ink-2)]'
              }`}
            >
              当前模块
            </button>
          </div>
          <span className="text-[10.5px] text-[color:var(--color-ink-3)]">
            {scope === 'module' && activeModule
              ? `${visibleRuns.length} 条当前模块记录`
              : `${visibleRuns.length} 条记录`}
          </span>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-2">
          {runs.isPending ? (
            <div className="grid h-44 place-items-center gap-2 text-[12px] text-[color:var(--color-ink-3)]">
              <LoaderCircle className="h-5 w-5 animate-spin text-[#3e63dd]" />
              正在读取历史记录…
            </div>
          ) : runs.isError ? (
            <div
              role="alert"
              className="m-2 rounded-md border border-[#f5c2c4] bg-[#fff5f5] px-3 py-2 text-[11.5px] text-[#c62a2f]"
            >
              历史记录加载失败：{errorText(runs.error)}
            </div>
          ) : visibleRuns.length === 0 ? (
            <div className="grid h-44 place-items-center text-[12px] text-[color:var(--color-ink-3)]">
              {scope === 'module' && activeModule ? '当前模块暂无历史记录' : '暂无历史记录'}
            </div>
          ) : (
            <div className="space-y-1">
              {loadError && (
                <div
                  role="alert"
                  className="mb-2 rounded-md border border-[#f5c2c4] bg-[#fff5f5] px-3 py-2 text-[11.5px] text-[#c62a2f]"
                >
                  历史详情加载失败：{loadError}
                </div>
              )}
              {visibleRuns.map((record) => {
                const isLoading = loadingRunId === record.run_id
                const loadingAnother = loadingRunId !== null && !isLoading
                const passed = Math.max(0, countValue(record.total) - countValue(record.failed))
                return (
                  <button
                    key={record.run_id}
                    type="button"
                    onClick={() => loadRun(record)}
                    disabled={loadingAnother || isLoading}
                    aria-label={`加载历史记录 ${record.run_id}`}
                    className="grid w-full grid-cols-[132px_minmax(160px,1fr)_110px_190px_92px_24px] items-center gap-3 rounded-md border border-transparent px-3 py-2.5 text-left hover:border-[color:var(--color-line)] hover:bg-black/[0.025] disabled:cursor-wait disabled:opacity-65"
                  >
                    <time
                      dateTime={record.created_at}
                      className="tnum text-[10.5px] text-[color:var(--color-ink-3)]"
                    >
                      {formatTimestamp(record.created_at)}
                    </time>
                    <div className="min-w-0">
                      <div className="truncate text-[12px] font-medium">{record.title}</div>
                      <div className="mt-0.5 truncate font-mono text-[9.5px] text-[color:var(--color-ink-3)]">
                        {record.module}
                      </div>
                    </div>
                    <div className="min-w-0">
                      <div className="truncate text-[10.5px] text-[color:var(--color-ink-2)]">
                        {record.standard}
                      </div>
                      <div
                        className={`mt-0.5 text-[9.5px] ${record.verified ? 'text-[#1a7f4b]' : 'text-[#a35c00]'}`}
                      >
                        {record.verified ? '已核验' : '骨架版'}
                      </div>
                    </div>
                    <div className="tnum flex items-center gap-2 text-[10.5px]">
                      <span className="text-[#1a7f4b]">通过 {passed}</span>
                      <span className="text-[#c62a2f]">失败 {countValue(record.failed)}</span>
                      <span className="text-[color:var(--color-ink-3)]">
                        总项 {countValue(record.total)}
                      </span>
                    </div>
                    <code className="truncate rounded bg-[color:var(--color-shell)] px-1.5 py-1 text-[9.5px] text-[color:var(--color-ink-2)]">
                      {shortRunId(record.run_id)}
                    </code>
                    {isLoading ? (
                      <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[#3e63dd]" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 text-[color:var(--color-ink-3)]" />
                    )}
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

export function RunHistoryDialog({ open, ...props }: RunHistoryDialogProps) {
  if (!open) return null
  return <HistoryContent {...props} />
}
