import {
  Blocks,
  ChevronDown,
  ChevronRight,
  FolderKanban,
  FolderTree,
  Layers3,
  Plus,
  Search,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { type ModuleCatalog, useModules } from '../api/calc'
import { type ProjectRecord, REGIONS } from '../api/projects'

const FALLBACK_CATALOG: ModuleCatalog = {
  regions: [...REGIONS],
  categories: [
    {
      key: 'ground-scaffold',
      title: '落地式脚手架',
      isNew: false,
      modules: [
        {
          key: 'scaffold-fastener',
          title: '扣件式脚手架',
          standard: 'JGJ 130-2011',
          verified: false,
          available: true,
          status: 'available',
          note: '',
        },
      ],
    },
  ],
  modules: [],
}

function ExpandButton({
  expanded,
  label,
  onClick,
}: {
  expanded: boolean
  label: string
  onClick: () => void
}) {
  const Icon = expanded ? ChevronDown : ChevronRight

  return (
    <button
      type="button"
      aria-expanded={expanded}
      aria-label={label}
      onClick={onClick}
      className="grid h-5 w-5 shrink-0 place-items-center rounded text-[color:var(--color-ink-3)] hover:bg-black/[0.04] hover:text-[color:var(--color-ink-2)]"
    >
      <Icon className="h-3 w-3" />
    </button>
  )
}

export function ModuleTree({
  project,
  active,
  schemeName,
  onSelect,
  onSchemes,
}: {
  project: ProjectRecord
  active: string
  schemeName?: string
  onSelect: (key: string) => void
  onSchemes: () => void
}) {
  const [q, setQ] = useState('')
  const [projectOpen, setProjectOpen] = useState(true)
  const [modulesOpen, setModulesOpen] = useState(true)
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({})
  const registered = useModules()
  const catalog = registered.data ?? FALLBACK_CATALOG
  const normalizedQuery = q.trim()
  const categories = catalog.categories
    .map((category) => {
      const categoryMatches = category.title.includes(normalizedQuery)
      return {
        ...category,
        modules: category.modules.filter(
          (module) =>
            !normalizedQuery ||
            categoryMatches ||
            module.title.includes(normalizedQuery) ||
            module.standard.includes(normalizedQuery),
        ),
      }
    })
    .filter(
      (category) =>
        !normalizedQuery || category.title.includes(normalizedQuery) || category.modules.length > 0,
    )
  const matchedModuleCount = categories.reduce(
    (count, category) => count + category.modules.length,
    0,
  )
  const schemeLabel = schemeName ?? '未保存方案'

  return (
    <aside
      aria-label="工作台目录"
      className="flex h-full flex-col border-r border-[color:var(--color-line)] bg-[color:var(--color-panel)]"
    >
      <div className="flex h-9 items-center gap-1.5 border-b border-[color:var(--color-line)] px-3">
        <FolderTree className="h-3.5 w-3.5 text-[#176b55]" />
        <span className="text-[11px] font-semibold tracking-wider text-[color:var(--color-ink-2)]">
          目录
        </span>
      </div>

      <section
        aria-label="项目地区（创建项目时确定）"
        className="flex flex-wrap gap-1 border-b border-[color:var(--color-line)] px-2.5 py-2"
      >
        {catalog.regions.map((region) => {
          const current = region === project.region
          return (
            <span
              key={region}
              aria-current={current ? 'true' : undefined}
              className={`rounded px-1.5 py-0.5 text-[10px] ${
                current
                  ? 'bg-[#176b55] font-medium text-white'
                  : 'bg-black/[0.035] text-[color:var(--color-ink-3)]'
              }`}
            >
              {region}
            </span>
          )
        })}
      </section>

      <nav aria-label="项目目录" className="min-h-0 flex-1 overflow-y-auto px-1.5 py-2">
        <div className="flex min-h-8 items-center gap-1 rounded-md px-0.5 hover:bg-black/[0.025]">
          <ExpandButton
            expanded={projectOpen}
            label={projectOpen ? '收起项目目录' : '展开项目目录'}
            onClick={() => setProjectOpen((open) => !open)}
          />
          <Link
            to="/workspace"
            aria-label={`返回项目工作台：${project.name}`}
            className="flex min-w-0 flex-1 items-center gap-1.5 rounded px-1 py-1 text-[12px] font-medium text-[color:var(--color-ink)] hover:text-[#176b55] focus-visible:ring-2 focus-visible:ring-[#176b55]/30 focus-visible:outline-none"
          >
            <FolderKanban className="h-3.5 w-3.5 shrink-0 text-[#176b55]" />
            <span className="min-w-0 flex-1 truncate">{project.name}</span>
            <span className="shrink-0 rounded bg-black/[0.045] px-1.5 py-0.5 text-[10px] font-normal text-[color:var(--color-ink-3)]">
              {project.region}
            </span>
          </Link>
        </div>

        {projectOpen && (
          <div className="ml-3 border-l border-[color:var(--color-line)] pl-1">
            <button
              type="button"
              aria-label={`打开计算方案：${schemeLabel}，${project.scheme_count} 个方案`}
              onClick={onSchemes}
              className="my-0.5 flex min-h-8 w-full items-center gap-1.5 rounded px-1.5 text-left text-[12px] text-[color:var(--color-ink-2)] hover:bg-black/[0.03]"
            >
              <Layers3 className="h-3.5 w-3.5 shrink-0 text-[#3f566f]" />
              <span className="min-w-0 flex-1 truncate">{schemeLabel}</span>
              <span className="shrink-0 text-[10px] text-[color:var(--color-ink-3)]">
                {project.scheme_count} 个方案
              </span>
            </button>

            <div className="mt-1">
              <div className="flex min-h-8 items-center gap-1 rounded px-0.5 hover:bg-black/[0.025]">
                <ExpandButton
                  expanded={modulesOpen}
                  label={modulesOpen ? '收起计算模块' : '展开计算模块'}
                  onClick={() => setModulesOpen((open) => !open)}
                />
                <Blocks className="h-3.5 w-3.5 text-[#3f566f]" />
                <span className="text-[12px] font-medium text-[color:var(--color-ink-2)]">
                  计算模块
                </span>
              </div>

              {modulesOpen && (
                <div className="ml-3 border-l border-[color:var(--color-line)] pl-1">
                  <div className="px-1.5 py-1">
                    <div className="flex h-7 items-center gap-1.5 rounded-md border border-[color:var(--color-line)] bg-[color:var(--color-shell)] px-2">
                      <Search className="h-3 w-3 shrink-0 text-[color:var(--color-ink-3)]" />
                      <input
                        aria-label="搜索计算模块"
                        value={q}
                        onChange={(event) => setQ(event.target.value)}
                        placeholder="搜索脚手架模块"
                        className="min-w-0 w-full bg-transparent text-[12px] outline-none placeholder:text-[color:var(--color-ink-3)]"
                      />
                    </div>
                  </div>

                  {categories.map((category) => {
                    const open = openCategories[category.key] ?? true
                    return (
                      <div key={category.key} className="mb-0.5">
                        <div className="flex min-h-7 items-center gap-1 rounded px-0.5 hover:bg-black/[0.025]">
                          <ExpandButton
                            expanded={open}
                            label={open ? `收起${category.title}` : `展开${category.title}`}
                            onClick={() =>
                              setOpenCategories((current) => ({
                                ...current,
                                [category.key]: !open,
                              }))
                            }
                          />
                          <span className="text-[10px] font-medium tracking-wide text-[color:var(--color-ink-3)]">
                            {category.title}
                          </span>
                          {category.isNew && (
                            <span className="rounded bg-[#e8f7ee] px-1 py-px text-[8px] font-medium text-[#176b55]">
                              新增
                            </span>
                          )}
                          <span className="ml-auto pr-1.5 text-[9px] text-[color:var(--color-ink-3)]">
                            {category.modules.length}
                          </span>
                        </div>
                        {open && (
                          <div className="ml-2">
                            {category.modules.map((module) => (
                              <button
                                key={module.key}
                                type="button"
                                aria-label={
                                  module.available
                                    ? `${module.title}${
                                        module.verified === false ? '，骨架版' : ''
                                      }`
                                    : `${module.title}，待接入`
                                }
                                aria-current={
                                  module.available && active === module.key ? 'page' : undefined
                                }
                                aria-disabled={module.available ? undefined : true}
                                disabled={!module.available}
                                onClick={() => {
                                  if (module.available) onSelect(module.key)
                                }}
                                className={`flex min-h-7 w-full items-center rounded px-2 text-left text-[12px] ${
                                  module.available && active === module.key
                                    ? 'bg-[#eef2ff] font-medium text-[#3e63dd]'
                                    : module.available
                                      ? 'text-[color:var(--color-ink-2)] hover:bg-black/[0.03]'
                                      : 'cursor-not-allowed text-[color:var(--color-ink-3)] opacity-70'
                                }`}
                                title={module.standard || module.note}
                              >
                                <span className="min-w-0 flex-1 truncate">{module.title}</span>
                                {module.available && module.verified === false && (
                                  <span className="ml-2 shrink-0 text-[9px] font-normal text-[#3e63dd]/60">
                                    骨架版
                                  </span>
                                )}
                                {!module.available && (
                                  <span className="ml-2 shrink-0 text-[9px] font-normal text-[color:var(--color-ink-3)]">
                                    待接入
                                  </span>
                                )}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {normalizedQuery && matchedModuleCount === 0 && (
                    <div className="px-2 py-3 text-center text-[10px] text-[color:var(--color-ink-3)]">
                      未找到脚手架模块
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </nav>

      <div className="border-t border-[color:var(--color-line)] p-2">
        <button
          type="button"
          onClick={onSchemes}
          className="flex h-7 w-full items-center justify-center gap-1 rounded-md border border-dashed border-[color:var(--color-line)] text-[11px] text-[color:var(--color-ink-3)] hover:border-[#c7c7cd] hover:text-[color:var(--color-ink-2)]"
        >
          <Plus className="h-3 w-3" /> 新建方案
        </button>
      </div>
    </aside>
  )
}
