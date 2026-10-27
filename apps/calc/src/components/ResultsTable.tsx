import { ChevronDown, ChevronRight, Download, Filter, Info } from 'lucide-react'
import { Fragment, useState } from 'react'
import { results as mockResults, type ResultRow } from '../mock/data'

export function ResultsTable({
  rows: incoming,
  verified,
  standard,
  failed,
  standards,
  onExportDetail,
}: {
  rows?: ResultRow[]
  verified?: boolean
  standard?: string
  failed?: number
  standards?: {
    applied: { code: string }[]
    missing: { code: string }[]
    complete: boolean
    gaps?: string[]
  }
  onExportDetail?: () => void
}) {
  const [onlyFail, setOnlyFail] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(3)
  const source = incoming ?? mockResults
  const rows = onlyFail ? source.filter((r) => !r.ok) : source
  const failCount = failed ?? source.filter((r) => !r.ok).length

  return (
    <section className="flex h-full flex-col border-t border-[color:var(--color-line)] bg-[color:var(--color-panel)]">
      <div className="flex h-9 shrink-0 items-center gap-3 border-b border-[color:var(--color-line)] px-3">
        <span className="text-[12px] font-semibold">计算结果</span>
        <span className="rounded bg-black/5 px-1.5 py-0.5 text-[10px] text-[color:var(--color-ink-2)]">
          {source.length} 项
        </span>
        {standard && (
          <span className="rounded bg-black/5 px-1.5 py-0.5 text-[10px] text-[color:var(--color-ink-3)]">
            {standard}
          </span>
        )}
        {verified === false && (
          <span className="rounded bg-[#fff7e6] px-1.5 py-0.5 text-[10px] font-medium text-[#a35c00]">
            骨架版 · 系数待核对
          </span>
        )}
        {standards && (
          <span
            className={`rounded px-1.5 py-0.5 text-[10px] ${
              standards.missing.length || !standards.complete
                ? 'bg-[#fff7e6] text-[#a35c00]'
                : 'bg-[#edfcf4] text-[#1a7f4b]'
            }`}
            title={
              standards.missing.length
                ? `未覆盖：${standards.missing.map((m) => m.code).join('、')}`
                : standards.gaps?.length
                  ? `适用边界：${standards.gaps.join('；')}`
                  : '规范已覆盖'
            }
          >
            依据 {standards.applied.length} 本
            {standards.missing.length ? ` · 缺 ${standards.missing.length} 本` : ''}
            {!standards.complete ? ' · 待补' : ''}
          </span>
        )}
        {failCount > 0 && (
          <span className="rounded bg-[#fdecec] px-1.5 py-0.5 text-[10px] font-medium text-[#c62a2f]">
            {failCount} 项不满足
          </span>
        )}
        <div className="ml-2 flex items-center gap-0.5 rounded-md bg-[color:var(--color-shell)] p-0.5">
          {[
            ['全部', false],
            ['仅不满足', true],
          ].map(([label, v]) => (
            <button
              key={String(label)}
              onClick={() => setOnlyFail(v as boolean)}
              className={`rounded px-2 py-1 text-[11px] ${onlyFail === v ? 'bg-white font-medium shadow-sm' : 'text-[color:var(--color-ink-2)]'}`}
            >
              {label as string}
            </button>
          ))}
        </div>
        <button className="flex items-center gap-1 rounded px-1.5 py-1 text-[11px] text-[color:var(--color-ink-2)] hover:bg-black/5">
          <Filter className="h-3 w-3" /> 控制项
        </button>
        <button
          onClick={onExportDetail}
          className="ml-auto flex items-center gap-1 rounded px-1.5 py-1 text-[11px] text-[color:var(--color-ink-2)] hover:bg-black/5"
        >
          <Download className="h-3 w-3" /> 导出明细
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full border-collapse text-[11.5px]">
          <thead className="sticky top-0 z-10 bg-[color:var(--color-shell)] text-[10.5px] uppercase tracking-wide text-[color:var(--color-ink-3)]">
            <tr>
              <th className="w-8 border-b border-[color:var(--color-line)] px-2 py-1.5 text-left" />
              <th className="w-10 border-b border-[color:var(--color-line)] px-2 py-1.5 text-left">
                项次
              </th>
              <th className="border-b border-[color:var(--color-line)] px-2 py-1.5 text-left">
                计算项
              </th>
              <th className="w-24 border-b border-[color:var(--color-line)] px-2 py-1.5 text-right">
                计算值
              </th>
              <th className="w-24 border-b border-[color:var(--color-line)] px-2 py-1.5 text-right">
                限值
              </th>
              <th className="w-32 border-b border-[color:var(--color-line)] px-2 py-1.5 text-left">
                利用率
              </th>
              <th className="w-20 border-b border-[color:var(--color-line)] px-2 py-1.5 text-center">
                判定
              </th>
              <th className="w-44 border-b border-[color:var(--color-line)] px-2 py-1.5 text-left">
                规范条文
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <Fragment key={r.no}>
                <tr
                  onClick={() => setExpanded(expanded === r.no ? null : r.no)}
                  className="cursor-default border-b border-[color:var(--color-line)]/70 hover:bg-black/[0.02]"
                >
                  <td className="px-2 py-1.5 text-[color:var(--color-ink-3)]">
                    {expanded === r.no ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )}
                  </td>
                  <td className="tnum px-2 py-1.5 text-[color:var(--color-ink-3)]">{r.no}</td>
                  <td className="px-2 py-1.5">
                    <span className="text-[color:var(--color-ink)]">{r.item}</span>
                    {r.control && (
                      <span className="ml-1.5 rounded bg-black/5 px-1 py-px text-[9px] text-[color:var(--color-ink-3)]">
                        控制项
                      </span>
                    )}
                  </td>
                  <td className="tnum px-2 py-1.5 text-right font-medium">{r.value}</td>
                  <td className="tnum px-2 py-1.5 text-right text-[color:var(--color-ink-2)]">
                    {r.limit}
                  </td>
                  <td className="px-2 py-1.5">
                    <div className="flex items-center gap-1.5">
                      <div className="h-1 w-16 overflow-hidden rounded-full bg-black/10">
                        <div
                          className={`h-full rounded-full ${r.ok ? 'bg-[#30a46c]' : 'bg-[#e5484d]'}`}
                          style={{ width: `${Math.min(100, r.ratio * 100)}%` }}
                        />
                      </div>
                      <span className="tnum text-[10px] text-[color:var(--color-ink-3)]">
                        {(r.ratio * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-2 py-1.5 text-center">
                    <span
                      className={`inline-flex items-center gap-1 rounded px-1.5 py-px text-[10px] font-medium ${
                        r.ok ? 'bg-[#edfcf4] text-[#1a7f4b]' : 'bg-[#fdecec] text-[#c62a2f]'
                      }`}
                    >
                      {r.ok ? '通过' : '不满足'}
                    </span>
                  </td>
                  <td className="px-2 py-1.5 text-[10.5px] text-[color:var(--color-ink-2)]">
                    {r.clause}
                  </td>
                </tr>
                {expanded === r.no && (
                  <tr className="border-b border-[color:var(--color-line)] bg-[#fafafa]">
                    <td />
                    <td colSpan={7} className="px-3 py-3">
                      <div className="grid grid-cols-[1.2fr_1fr] gap-4">
                        <div className="rounded-md border border-[color:var(--color-line)] bg-white p-3">
                          <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium">
                            <Info className="h-3 w-3 text-[#3e63dd]" /> 公式推导
                          </div>
                          <div className="space-y-1 font-mono text-[11px] text-[color:var(--color-ink-2)]">
                            <div>{r.detail ?? 'σ = N / (φ·A) + M_w / W'}</div>
                            <div>
                              {r.item}：{r.value} / 限值 {r.limit}
                            </div>
                            <div>判定：{r.ok ? '通过' : '不满足'}</div>
                          </div>
                        </div>
                        <div className="rounded-md border border-[color:var(--color-line)] bg-white p-3">
                          <div className="mb-2 text-[11px] font-medium">
                            规范条文 · JGJ 130-2011 5.2.6
                          </div>
                          <p className="text-[11px] leading-relaxed text-[color:var(--color-ink-2)]">
                            立杆的稳定性应按本标准式（5.2.6-1）、式（5.2.6-2）计算……
                          </p>
                          <div className="mt-2 flex gap-3 text-[10px] text-[color:var(--color-ink-3)]">
                            <span>页码 P42</span>
                            <span>品茗实测 89.4</span>
                            <span>偏差 0.22%</span>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
