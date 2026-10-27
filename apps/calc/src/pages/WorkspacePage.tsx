import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Calculator,
  CheckCircle2,
  FolderPlus,
  Layers3,
  Plus,
  RefreshCw,
  Search,
  SlidersHorizontal,
} from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  deleteProject,
  PROJECT_STATUSES,
  type ProjectRecord,
  type ProjectStatus,
  useProjects,
} from '../api/projects'
import { type ProjectCreateIntent, ProjectFormDialog } from '../components/ProjectFormDialog'
import { ProjectTable } from '../components/ProjectTable'
import { Button } from '../components/ui/button'
import { WorkspaceHeader } from '../components/WorkspaceHeader'

const metricCards = [
  { key: 'all', label: '全部项目', icon: FolderPlus, tone: 'text-[#52525b] bg-[#f4f4f5]' },
  { key: 'calculating', label: '计算中', icon: Calculator, tone: 'text-[#176b55] bg-[#e7f3ee]' },
  { key: 'schemes', label: '计算方案', icon: Layers3, tone: 'text-[#3f566f] bg-[#edf1f7]' },
  { key: 'completed', label: '已完成', icon: CheckCircle2, tone: 'text-[#8a5800] bg-[#fff7e6]' },
] as const
const EMPTY_PROJECTS: ProjectRecord[] = []

export function WorkspacePage() {
  const navigate = useNavigate()
  const reducedMotion = useReducedMotion()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [formOpen, setFormOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<ProjectRecord>()
  const search = searchParams.get('search') ?? ''
  const rawStatus = searchParams.get('status')
  const status = PROJECT_STATUSES.some((item) => item.value === rawStatus)
    ? (rawStatus as ProjectStatus)
    : undefined

  const projects = useProjects({ search, status })
  const allProjects = useProjects({ search: '' })
  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['projects'] }),
        queryClient.invalidateQueries({ queryKey: ['project'] }),
      ])
    },
  })

  const metricsSource = useMemo(
    () => allProjects.data?.projects ?? projects.data?.projects ?? [],
    [allProjects.data, projects.data],
  )
  const metrics = useMemo(
    () => ({
      all: metricsSource.length,
      calculating: metricsSource.filter((project) => project.status === 'calculating').length,
      schemes: metricsSource.reduce((total, project) => total + project.scheme_count, 0),
      completed: metricsSource.filter((project) => project.status === 'completed').length,
    }),
    [metricsSource],
  )

  function updateFilters(key: 'search' | 'status', value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next, { replace: true })
  }

  function clearFilters() {
    setSearchParams({}, { replace: true })
  }

  function handleCreated(project: ProjectRecord, intent: ProjectCreateIntent) {
    if (intent === 'enter') {
      navigate(`/projects/${project.project_id}/calc`)
    }
  }

  function openNewProject() {
    setEditingProject(undefined)
    setFormOpen(true)
  }

  return (
    <div className="min-h-screen bg-[#f4f5f6] text-[#18181b]">
      <WorkspaceHeader />
      <motion.main
        initial={reducedMotion ? false : { opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        className="mx-auto w-full max-w-[1480px] px-4 py-7 sm:px-6 sm:py-9"
      >
        <section className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[11px] font-semibold tracking-[0.18em] text-[#176b55]">
              PROJECT WORKSPACE
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">项目工作台</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#71717a]">
              按项目集中管理方案、计算状态和最近结果。地区作为项目属性保存，不改变当前计算规则。
            </p>
          </div>
          <Button
            size="lg"
            onClick={openNewProject}
            className="w-full bg-[#176b55] text-white hover:bg-[#125744] sm:w-auto"
          >
            <Plus />
            新建项目
          </Button>
        </section>

        <section aria-label="项目指标" className="mt-6 grid grid-cols-2 gap-3 xl:grid-cols-4">
          {metricCards.map((card, index) => {
            const Icon = card.icon
            const value =
              card.key === 'all'
                ? metrics.all
                : card.key === 'calculating'
                  ? metrics.calculating
                  : card.key === 'schemes'
                    ? metrics.schemes
                    : metrics.completed
            return (
              <motion.div
                key={card.key}
                initial={reducedMotion ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.16, delay: reducedMotion ? 0 : index * 0.035 }}
                className="rounded-lg border bg-white p-4 shadow-[0_1px_2px_rgba(24,24,27,0.03)]"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-[11px] font-medium text-[#71717a]">{card.label}</div>
                    <div className="tnum mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
                      {value}
                    </div>
                  </div>
                  <span className={`grid size-9 place-items-center rounded-lg ${card.tone}`}>
                    <Icon className="size-4" />
                  </span>
                </div>
              </motion.div>
            )
          })}
        </section>

        <section className="mt-7">
          <div className="mb-3 flex flex-col gap-2 rounded-lg border bg-white p-3 sm:flex-row sm:items-center">
            <label className="flex h-9 min-w-0 flex-1 items-center gap-2 rounded-md border bg-[#fafafa] px-3 focus-within:border-[#176b55] focus-within:ring-3 focus-within:ring-[#176b55]/10">
              <Search className="size-4 text-[#a1a1aa]" />
              <span className="sr-only">搜索项目</span>
              <input
                aria-label="搜索项目"
                value={search}
                onChange={(event) => updateFilters('search', event.target.value)}
                placeholder="搜索项目名称、编号、建设单位或地区"
                className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-[#a1a1aa]"
              />
            </label>

            <label className="flex h-9 items-center gap-2 rounded-md border bg-white px-2.5 text-xs text-[#52525b]">
              <SlidersHorizontal className="size-3.5 text-[#71717a]" />
              <span className="sr-only">状态筛选</span>
              <select
                aria-label="状态筛选"
                value={status ?? ''}
                onChange={(event) => updateFilters('status', event.target.value)}
                className="min-w-24 bg-transparent outline-none"
              >
                <option value="">全部状态</option>
                {PROJECT_STATUSES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                void projects.refetch()
                void allProjects.refetch()
              }}
              disabled={projects.isFetching}
            >
              <RefreshCw className={projects.isFetching ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">刷新</span>
            </Button>
          </div>

          <ProjectTable
            projects={projects.data?.projects ?? EMPTY_PROJECTS}
            loading={projects.isPending}
            error={projects.error instanceof Error ? projects.error : null}
            hasFilters={Boolean(search || status)}
            onRetry={() => void projects.refetch()}
            onClearFilters={clearFilters}
            onEnter={(project) => navigate(`/projects/${project.project_id}/calc`)}
            onEdit={(project) => {
              setEditingProject(project)
              setFormOpen(true)
            }}
            onDelete={(project) => deleteMutation.mutateAsync(project.project_id)}
          />
        </section>
      </motion.main>

      <ProjectFormDialog
        open={formOpen}
        onOpenChange={(open) => {
          setFormOpen(open)
          if (!open) setEditingProject(undefined)
        }}
        project={editingProject}
        onCreated={handleCreated}
      />
    </div>
  )
}
