import { Download, Play, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { downloadBatchCsv, type ParamField, type ParamGroup, useBatch } from '../api/calc'

function parseList(text: string): number[] {
  return text
    .split(/[,，\s]+/)
    .map((v) => Number(v))
    .filter((v) => Number.isFinite(v) && v > 0)
}

export function BatchDialog({
  open,
  baseParams,
  module,
  groups,
  onClose,
}: {
  open: boolean
  baseParams: Record<string, unknown>
  module: string
  groups?: ParamGroup[]
  onClose: () => void
}) {
  const fields = useMemo(
    () =>
      (groups ?? []).flatMap((group) => group.fields).filter((field) => field.type === 'number'),
    [groups],
  )
  const defaults = useMemo(() => {
    const h = fields.find((field) => field.key === 'h')
    const la = fields.find((field) => field.key === 'la')
    return h && la ? [h, la] : fields.slice(0, 2)
  }, [fields])
  const [selectedA, setSelectedA] = useState<string>()
  const [selectedB, setSelectedB] = useState<string>()
  const [texts, setTexts] = useState<Record<string, string>>({})
  const fieldA = fields.find((field) => field.key === selectedA) ?? defaults[0]
  const fieldB =
    fields.find((field) => field.key === selectedB && field.key !== fieldA?.key) ??
    defaults.find((field) => field.key !== fieldA?.key)
  const batch = useBatch(module)

  function textFor(field?: ParamField) {
    if (!field) return ''
    return texts[field.key] ?? String(baseParams[field.key] ?? field.default ?? '')
  }

  function setText(field: ParamField | undefined, value: string) {
    if (!field) return
    setTexts((current) => ({ ...current, [field.key]: value }))
  }

  const cases = useMemo(() => {
    if (!fieldA || !fieldB) return []
    const valuesA = parseList(textFor(fieldA))
    const valuesB = parseList(textFor(fieldB))
    const list: Record<string, unknown>[] = []
    for (const valueA of valuesA) {
      for (const valueB of valuesB) {
        list.push({ ...baseParams, [fieldA.key]: valueA, [fieldB.key]: valueB })
      }
    }
    return list.slice(0, 200)
  }, [baseParams, fieldA, fieldB, texts])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/35 p-6" onClick={onClose}>
      <div
        className="flex max-h-[86vh] w-[980px] flex-col overflow-hidden rounded-lg border border-[color:var(--color-line)] bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex h-11 items-center gap-3 border-b border-[color:var(--color-line)] px-4">
          <span className="text-[13px] font-semibold">批量工况</span>
          <span className="text-[11px] text-[color:var(--color-ink-3)]">
            参数矩阵 · 最多 200 组
          </span>
          <button
            onClick={onClose}
            className="ml-auto grid h-7 w-7 place-items-center rounded hover:bg-black/5"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="flex items-end gap-3 border-b border-[color:var(--color-line)] px-4 py-3">
          <label className="text-[11px] text-[color:var(--color-ink-2)]">
            <div className="mb-1">字段 A</div>
            <select
              aria-label="矩阵字段A"
              value={fieldA?.key ?? ''}
              onChange={(event) => {
                const next = event.target.value
                setSelectedA(next)
                if (next === fieldB?.key) {
                  setSelectedB(fields.find((field) => field.key !== next)?.key)
                }
              }}
              className="mb-1 h-7 w-44 rounded border border-[color:var(--color-line)] bg-white px-2 text-[12px] outline-none focus:border-[#3e63dd]"
            >
              {fields.map((field) => (
                <option key={field.key} value={field.key}>
                  {field.label}
                  {field.unit ? `（${field.unit}）` : ''}
                </option>
              ))}
            </select>
            <div className="mb-1">{fieldA?.label ?? '—'}（逗号分隔）</div>
            <input
              aria-label={`${fieldA?.label ?? '字段A'}取值列表`}
              value={textFor(fieldA)}
              onChange={(event) => setText(fieldA, event.target.value)}
              className="h-7 w-44 rounded border border-[color:var(--color-line)] px-2 text-[12px] outline-none focus:border-[#3e63dd]"
            />
          </label>
          <label className="text-[11px] text-[color:var(--color-ink-2)]">
            <div className="mb-1">字段 B</div>
            <select
              aria-label="矩阵字段B"
              value={fieldB?.key ?? ''}
              onChange={(event) => {
                const next = event.target.value
                setSelectedB(next)
                if (next === fieldA?.key) {
                  setSelectedA(fields.find((field) => field.key !== next)?.key)
                }
              }}
              className="mb-1 h-7 w-44 rounded border border-[color:var(--color-line)] bg-white px-2 text-[12px] outline-none focus:border-[#3e63dd]"
            >
              {fields.map((field) => (
                <option key={field.key} value={field.key}>
                  {field.label}
                  {field.unit ? `（${field.unit}）` : ''}
                </option>
              ))}
            </select>
            <div className="mb-1">{fieldB?.label ?? '—'}（逗号分隔）</div>
            <input
              aria-label={`${fieldB?.label ?? '字段B'}取值列表`}
              value={textFor(fieldB)}
              onChange={(event) => setText(fieldB, event.target.value)}
              className="h-7 w-44 rounded border border-[color:var(--color-line)] px-2 text-[12px] outline-none focus:border-[#3e63dd]"
            />
          </label>
          <div className="pb-1 text-[11px] text-[color:var(--color-ink-3)]">
            共 {cases.length} 组
          </div>
          <div className="ml-auto flex gap-2">
            <button
              onClick={() => batch.mutate(cases)}
              disabled={!cases.length || batch.isPending}
              className="flex h-7 items-center gap-1.5 rounded-md bg-[color:var(--color-ink)] px-2.5 text-[12px] font-medium text-white disabled:opacity-40"
            >
              <Play className="h-3.5 w-3.5" /> {batch.isPending ? '计算中…' : '开始批量计算'}
            </button>
            <button
              onClick={() => downloadBatchCsv(cases, module)}
              disabled={!cases.length}
              className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] px-2.5 text-[12px] disabled:opacity-40"
            >
              <Download className="h-3.5 w-3.5" /> 导出 CSV
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto">
          {batch.data ? (
            <table className="w-full border-collapse text-[11.5px]">
              <thead className="sticky top-0 bg-[color:var(--color-shell)] text-[10.5px] uppercase tracking-wide text-[color:var(--color-ink-3)]">
                <tr>
                  {[
                    '工况',
                    fieldA?.label ?? '字段 A',
                    fieldB?.label ?? '字段 B',
                    '主导控制项',
                    '计算值（含单位）',
                    '利用率',
                    '不满足项',
                    '结论',
                  ].map((heading) => (
                    <th
                      key={heading}
                      className="border-b border-[color:var(--color-line)] px-2 py-1.5 text-left"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {batch.data.rows.map((r) => (
                  <tr
                    key={r.index}
                    className="border-b border-[color:var(--color-line)]/70 hover:bg-black/[0.02]"
                  >
                    <td className="px-2 py-1.5 font-medium">{r.name}</td>
                    <td className="tnum px-2 py-1.5">
                      {String(r.params[fieldA?.key ?? ''] ?? '—')}
                    </td>
                    <td className="tnum px-2 py-1.5">
                      {String(r.params[fieldB?.key ?? ''] ?? '—')}
                    </td>
                    <td className="px-2 py-1.5">{r.primary_item ?? '—'}</td>
                    <td className="tnum px-2 py-1.5">
                      {r.primary_value === null
                        ? '—'
                        : `${r.primary_value}${r.primary_unit ? ` ${r.primary_unit}` : ''}`}
                    </td>
                    <td className="tnum px-2 py-1.5">
                      {r.primary_ratio === null ? '—' : `${(r.primary_ratio * 100).toFixed(1)}%`}
                    </td>
                    <td className="tnum px-2 py-1.5">{r.failed}</td>
                    <td className="px-2 py-1.5">
                      <span
                        className={`rounded px-1.5 py-px text-[10px] font-medium ${
                          r.ok ? 'bg-[#edfcf4] text-[#1a7f4b]' : 'bg-[#fdecec] text-[#c62a2f]'
                        }`}
                      >
                        {r.ok ? '通过' : '不满足'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="grid h-40 place-items-center text-[12px] text-[color:var(--color-ink-3)]">
              设置矩阵后点击"开始批量计算"
            </div>
          )}
        </div>

        {batch.data && (
          <footer className="flex h-9 items-center gap-4 border-t border-[color:var(--color-line)] px-4 text-[11px] text-[color:var(--color-ink-2)]">
            <span>共 {batch.data.count} 组</span>
            <span className="text-[#c62a2f]">不满足 {batch.data.failed} 组</span>
            <span>控制项不满足 {batch.data.control_failed} 组</span>
          </footer>
        )}
      </div>
    </div>
  )
}
