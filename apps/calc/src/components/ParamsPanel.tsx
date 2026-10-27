import { ChevronDown, RotateCcw, Search } from 'lucide-react'
import { useState } from 'react'
import { paramGroups as fallbackGroups } from '../mock/data'

type Field = {
  key: string
  label: string
  type: 'number' | 'select' | 'boolean'
  unit?: string
  step?: number
  options?: string[]
  default?: unknown
}

export function ParamsPanel({
  groups,
  params,
  onUpdate,
}: {
  groups?: { key?: string; title: string; fields: Field[] }[]
  params: Record<string, unknown>
  onUpdate: (k: string, v: unknown) => void
}) {
  const source = groups?.length ? groups : fallbackGroups
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const fieldCount = source.reduce((count, group) => count + group.fields.length, 0)

  return (
    <section className="flex h-full flex-col border-r border-[color:var(--color-line)] bg-[color:var(--color-panel)]">
      <div className="flex h-9 items-center gap-2 border-b border-[color:var(--color-line)] px-3">
        <span className="text-[11px] font-semibold tracking-wider text-[color:var(--color-ink-3)]">
          参数
        </span>
        <div className="ml-auto flex items-center gap-2 text-[color:var(--color-ink-3)]">
          <Search className="h-3 w-3" />
          <RotateCcw className="h-3 w-3" />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {source.map((g, groupIndex) => {
          const expanded = open[g.title] ?? groupIndex === 0
          return (
            <div key={g.title} className="border-b border-[color:var(--color-line)]">
              <button
                onClick={() => setOpen((o) => ({ ...o, [g.title]: !expanded }))}
                className="flex h-8 w-full items-center gap-1.5 px-3 text-[12px] font-medium hover:bg-black/[0.02]"
              >
                <ChevronDown
                  className={`h-3 w-3 text-[color:var(--color-ink-3)] transition-transform ${
                    expanded ? '' : '-rotate-90'
                  }`}
                />
                {g.title}
              </button>
              {expanded && (
                <div className="px-3 pb-2">
                  {g.fields.map((f, idx) => {
                    const value = params[f.key] ?? ''
                    return (
                      <div
                        key={`${g.title}-${f.key}-${idx}`}
                        className="mb-1.5 flex items-center gap-2"
                      >
                        <label className="w-[96px] shrink-0 text-[11.5px] text-[color:var(--color-ink-2)]">
                          {f.label}
                        </label>
                        <div className="relative flex-1">
                          {f.type === 'boolean' ? (
                            <button
                              type="button"
                              role="switch"
                              aria-checked={Boolean(value)}
                              aria-label={f.label}
                              onClick={() => onUpdate(f.key, !value)}
                              className={`flex h-7 w-full items-center justify-between rounded border px-2 text-[11.5px] ${
                                value
                                  ? 'border-[#97d7b2] bg-[#edfcf4] text-[#1a7f4b]'
                                  : 'border-[#f5c2c4] bg-[#fff5f5] text-[#c62a2f]'
                              }`}
                            >
                              <span>{value ? '已确认' : '未确认'}</span>
                              <span
                                className={`h-3.5 w-6 rounded-full p-0.5 transition-colors ${
                                  value ? 'bg-[#30a46c]' : 'bg-[#c62a2f]/45'
                                }`}
                              >
                                <span
                                  className={`block h-2.5 w-2.5 rounded-full bg-white transition-transform ${
                                    value ? 'translate-x-2.5' : ''
                                  }`}
                                />
                              </span>
                            </button>
                          ) : f.type === 'select' ? (
                            <select
                              value={String(value)}
                              onChange={(e) => onUpdate(f.key, e.target.value)}
                              className="h-7 w-full rounded border border-[color:var(--color-line)] bg-white px-1.5 pr-6 text-[12px] outline-none focus:border-[#3e63dd]"
                            >
                              {f.options?.map((o) => (
                                <option key={o}>{o}</option>
                              ))}
                            </select>
                          ) : (
                            <input
                              type="number"
                              step={f.step}
                              value={Number(value)}
                              onChange={(e) => onUpdate(f.key, Number(e.target.value))}
                              className="tnum h-7 w-full rounded border border-[color:var(--color-line)] bg-white px-1.5 pr-10 text-[12px] outline-none focus:border-[#3e63dd]"
                            />
                          )}
                          {f.unit && f.type !== 'boolean' && (
                            <span className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 text-[10px] text-[color:var(--color-ink-3)]">
                              {f.unit}
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="flex h-8 items-center justify-between border-t border-[color:var(--color-line)] px-3 text-[11px] text-[color:var(--color-ink-3)]">
        <span>共 {fieldCount} 项参数</span>
        <span className="cursor-pointer hover:text-[color:var(--color-ink-2)]">显示高级</span>
      </div>
    </section>
  )
}
