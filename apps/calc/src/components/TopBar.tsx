import { ChevronRight, Download, FolderKanban, History, Play, Table2, Zap } from 'lucide-react'
import { BRAND_MARK, BRAND_NAME } from '../branding'

export function TopBar({
  dirty,
  moduleTitle,
  schemeName,
  total,
  onRun,
  onExport,
  onBatch,
  onHistory,
  onSchemes,
}: {
  dirty: boolean
  moduleTitle?: string
  schemeName?: string
  total?: number
  onRun: () => void
  onExport?: () => void
  onBatch?: () => void
  onHistory: () => void
  onSchemes: () => void
}) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 overflow-x-auto border-b border-[color:var(--color-line)] bg-[color:var(--color-panel)] px-3">
      <div className="flex shrink-0 items-center gap-2 pr-3">
        <div className="grid h-6 w-6 place-items-center rounded bg-[color:var(--color-ink)] text-[10px] font-bold text-white">
          {BRAND_MARK}
        </div>
        <span className="text-[13px] font-semibold tracking-wide">{BRAND_NAME}</span>
      </div>

      <div className="h-4 w-px shrink-0 bg-[color:var(--color-line)]" />

      <nav className="flex shrink-0 items-center gap-1 text-[12px] text-[color:var(--color-ink-2)]">
        <span className="max-w-[180px] truncate rounded px-1.5 py-0.5 hover:bg-black/5">
          {schemeName ?? '未保存方案'}
        </span>
        <ChevronRight className="h-3 w-3 text-[color:var(--color-ink-3)]" />
        <span className="rounded bg-black/5 px-1.5 py-0.5 font-medium text-[color:var(--color-ink)]">
          {moduleTitle ?? '正在加载模块'}
        </span>
      </nav>

      <div className="ml-auto flex shrink-0 items-center gap-2">
        <div
          className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] ${
            dirty ? 'bg-[#fff7e6] text-[#a35c00]' : 'bg-[#edfcf4] text-[#1a7f4b]'
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${dirty ? 'bg-[color:var(--color-warn)]' : 'bg-[#30a46c]'}`}
          />
          {dirty ? '参数已改动 · 待重算' : `已计算${total === undefined ? '' : ` · ${total} 项`}`}
        </div>
        <button
          onClick={onRun}
          className="flex h-7 items-center gap-1.5 rounded-md bg-[color:var(--color-ink)] px-2.5 text-[12px] font-medium text-white hover:bg-black"
        >
          <Play className="h-3.5 w-3.5" /> 重算
        </button>
        <button
          onClick={onExport}
          className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] px-2.5 text-[12px] hover:bg-black/[0.03]"
        >
          <Download className="h-3.5 w-3.5" /> 导出
        </button>
        <button
          onClick={onSchemes}
          className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] px-2.5 text-[12px] hover:bg-black/[0.03]"
        >
          <FolderKanban className="h-3.5 w-3.5" /> 方案
        </button>
        <button
          onClick={onBatch}
          className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] px-2.5 text-[12px] hover:bg-black/[0.03]"
        >
          <Table2 className="h-3.5 w-3.5" /> 批量
        </button>
        <button
          onClick={onHistory}
          className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] px-2.5 text-[12px] hover:bg-black/[0.03]"
        >
          <History className="h-3.5 w-3.5" /> 历史
        </button>
        <div className="ml-1 flex items-center gap-1 rounded-md border border-[color:var(--color-line)] px-2 py-1 text-[11px] text-[color:var(--color-ink-2)]">
          <Zap className="h-3 w-3 text-[color:var(--color-warn)]" />
          <span>本地 API</span>
        </div>
      </div>
    </header>
  )
}
