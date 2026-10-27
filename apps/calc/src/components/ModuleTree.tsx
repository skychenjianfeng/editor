import { ChevronDown, ChevronRight, Plus, Search, SlidersHorizontal } from 'lucide-react'
import { useState } from 'react'
import { useModules } from '../api/calc'
import { modules } from '../mock/data'

export function ModuleTree({
  active,
  onSelect,
}: {
  active: string
  onSelect: (key: string) => void
}) {
  const [q, setQ] = useState('')
  const registered = useModules()
  const available = registered.data?.modules ?? [
    {
      key: 'scaffold-fastener',
      title: '扣件式脚手架',
      standard: 'JGJ 130-2011',
      verified: false,
      category: '落地与满堂',
    },
  ]
  const filtered = available.filter((m) => !q || m.title.includes(q))
  const categories = ['落地与满堂', '悬挑与升降', '工具式与平台'].map((name) => ({
    name,
    modules: filtered.filter((m) => (m.category ?? '其他') === name),
  }))
  const ungrouped = filtered.filter(
    (m) => !categories.some((category) => category.modules.includes(m)),
  )
  if (ungrouped.length) categories.push({ name: '其他', modules: ungrouped })
  return (
    <aside className="flex h-full flex-col border-r border-[color:var(--color-line)] bg-[color:var(--color-panel)]">
      <div className="flex h-9 items-center justify-between border-b border-[color:var(--color-line)] px-3">
        <span className="text-[11px] font-semibold tracking-wider text-[color:var(--color-ink-3)]">
          模块
        </span>
        <div className="flex gap-1">
          <button className="grid h-5 w-5 place-items-center rounded hover:bg-black/5">
            <SlidersHorizontal className="h-3 w-3 text-[color:var(--color-ink-3)]" />
          </button>
          <button className="grid h-5 w-5 place-items-center rounded hover:bg-black/5">
            <Plus className="h-3 w-3 text-[color:var(--color-ink-3)]" />
          </button>
        </div>
      </div>

      <div className="px-2 py-2">
        <div className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] bg-[color:var(--color-shell)] px-2">
          <Search className="h-3 w-3 text-[color:var(--color-ink-3)]" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜索模块 / 工况"
            className="w-full bg-transparent text-[12px] outline-none placeholder:text-[color:var(--color-ink-3)]"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-1.5 pb-3">
        <div className="mb-0.5">
          <div className="flex h-7 items-center gap-1 rounded px-1.5 text-[12px] font-medium text-[color:var(--color-ink-2)]">
            <ChevronDown className="h-3 w-3" />
            已接入
          </div>
          <div className="ml-3 border-l border-[color:var(--color-line)] pl-1">
            {categories
              .filter((category) => category.modules.length > 0)
              .map((category) => (
                <div key={category.name} className="mb-1">
                  <div className="flex h-6 items-center px-2 text-[10px] font-medium tracking-wide text-[color:var(--color-ink-3)]">
                    {category.name}
                  </div>
                  {category.modules.map((m) => (
                    <button
                      key={m.key}
                      onClick={() => onSelect(m.key)}
                      className={`flex h-7 w-full items-center rounded px-2 text-left text-[12px] ${
                        active === m.key
                          ? 'bg-[#eef2ff] font-medium text-[#3e63dd]'
                          : 'text-[color:var(--color-ink-2)] hover:bg-black/[0.03]'
                      }`}
                      title={m.standard}
                    >
                      {m.title}
                      {m.verified === false && (
                        <span className="ml-auto text-[9px] font-normal text-[#3e63dd]/60">
                          骨架版
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              ))}
          </div>
        </div>

        <div className="mt-2 px-1.5 text-[10px] tracking-wider text-[color:var(--color-ink-3)]">
          规划中
        </div>
        {modules.map((m) => (
          <div key={m.group} className="mb-0.5">
            <div className="flex h-7 cursor-default items-center gap-1 rounded px-1.5 text-[12px] font-medium text-[color:var(--color-ink-3)]">
              {m.open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              {m.group}
            </div>
            {m.open && (
              <div className="ml-3 border-l border-[color:var(--color-line)] pl-1">
                {m.items
                  .filter((i) => !q || i.name.includes(q))
                  .filter((i) => !available.some((a) => a.title === i.name))
                  .map((i) => (
                    <div
                      key={i.name}
                      className="flex h-7 cursor-not-allowed items-center rounded px-2 text-[12px] text-[color:var(--color-ink-3)]"
                    >
                      {i.name}
                    </div>
                  ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="border-t border-[color:var(--color-line)] p-2">
        <button className="flex h-7 w-full items-center justify-center gap-1 rounded-md border border-dashed border-[color:var(--color-line)] text-[11px] text-[color:var(--color-ink-3)] hover:border-[#c7c7cd] hover:text-[color:var(--color-ink-2)]">
          <Plus className="h-3 w-3" /> 新建方案
        </button>
      </div>
    </aside>
  )
}
