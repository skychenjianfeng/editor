import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  ArrowRight,
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
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  deleteProject,
  PROJECT_STATUSES,
  type ProjectRecord,
  type ProjectStatus,
  useProjects,
} from '../../api/projects'
import { type ProjectCreateIntent, ProjectFormDialog } from '../ProjectFormDialog'
import { ProjectTable } from '../ProjectTable'
import { Alert, AlertDescription, AlertTitle } from '../ui/alert'
import { Button } from '../ui/button'
import { Skeleton } from '../ui/skeleton'

const metricCards = [
  { key: 'all', label: '全部项目', icon: FolderPlus, tone: 'text-[#52525b] bg-[#f4f4f5]' },
  { key: 'calculating', label: '计算中', icon: Calculator, tone: 'text-[#176b55] bg-[#e7f3ee]' },
  { key: 'schemes', label: '计算方案', icon: Layers3, tone: 'text-[#3f566f] bg-[#edf1f7]' },
  { key: 'completed', label: '已完成', icon: CheckCircle2, tone: 'text-[#8a5800] bg-[#fff7e6]' },
] as const

const EMPTY_PROJECTS: ProjectRecord[] = []

export function ProjectWorkspacePanel({ variant }: { variant: 'overview' | 'management' }) {
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

  const filteredProjects = projects.data?.projects
  const globalProjects = allProjects.data?.projects
  const metrics = useMemo(
    () =>
      globalProjects
        ? {
            all: globalProjects.length,
            calculating: globalProjects.filter((project) => project.status === 'calculating')
              .length,
            schemes: globalProjects.reduce((total, project) => total + project.scheme_count, 0),
            completed: globalProjects.filter((project) => project.status === 'completed').length,
          }
        : undefined,
    [globalProjects],
  )
  const overviewProjects = useMemo(
    () =>
      [...(filteredProjects ?? EMPTY_PROJECTS)]
        .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))
        .slice(0, 8),
    [filteredProjects],
  )
  const visibleProjects =
    variant === 'overview' ? overviewProjects : (filteredProjects ?? EMPTY_PROJECTS)
  const hasFilters = Boolean(search || status)
  const isRefreshing = projects.isFetching || allProjects.isFetching

  let managementSummary = ''
  if (variant === 'management') {
    if (allProjects.isError) {
      managementSummary = '项目总数读取失败'
    } else if (allProjects.isPending || !globalProjects) {
      managementSummary = '正在读取项目总数…'
    } else {
      managementSummary = `共 ${globalProjects.length} 个项目`
    }

    if (hasFilters) {
      const filteredSummary = projects.isError
        ? '当前筛选读取失败'
        : projects.isPending || !filteredProjects
          ? '正在读取当前筛选结果…'
          : `当前筛选 ${filteredProjects.length} 个`
      managementSummary = `${managementSummary} · ${filteredSummary}`
    }
  }

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
    <>
      <motion.div
        initial={reducedMotion ? false : { opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
      >
        {variant === 'overview' && (
          <section aria-label="项目指标" className="mt-6">
            {allProjects.isError ? (
              <Alert variant="destructive" className="bg-white">
                <AlertCircle />
                <AlertTitle>项目指标加载失败</AlertTitle>
                <AlertDescription className="flex items-center justify-between gap-4">
                  <span>
                    {allProjects.error instanceof Error
                      ? allProjects.error.message
                      : '全局项目数据暂时不可用。'}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void allProjects.refetch()}
                    aria-label="重试项目指标"
                  >
                    重试
                  </Button>
                </AlertDescription>
              </Alert>
            ) : allProjects.isPending || !metrics ? (
              <div
                role="status"
                aria-label="项目指标加载中"
                className="grid grid-cols-2 gap-3 xl:grid-cols-4"
              >
                {metricCards.map((card) => (
                  <div
                    key={card.key}
                    className="rounded-lg border bg-white p-4 shadow-[0_1px_2px_rgba(24,24,27,0.03)]"
                  >
                    <div className="text-[11px] font-medium text-[#71717a]">{card.label}</div>
                    <Skeleton className="mt-2 h-8 w-16 sm:h-9" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
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
              </div>
            )}
          </section>
        )}

        <section className={variant === 'overview' ? 'mt-7' : 'mt-5'}>
          <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-base font-semibold tracking-tight">
                {variant === 'overview' ? '最近项目' : '项目列表'}
              </h2>
              <p className="mt-1 text-xs text-[#71717a]">
                {variant === 'overview' ? '按更新时间展示最近 8 个项目。' : managementSummary}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {variant === 'overview' && (
                <Button asChild variant="outline" size="sm">
                  <Link to="/workspace/projects">
                    查看全部项目
                    <ArrowRight />
                  </Link>
                </Button>
              )}
              <Button
                size="lg"
                onClick={openNewProject}
                className="bg-[#176b55] text-white hover:bg-[#125744]"
              >
                <Plus />
                新建项目
              </Button>
            </div>
          </div>

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
                if (hasFilters) void allProjects.refetch()
              }}
              disabled={isRefreshing}
            >
              <RefreshCw className={isRefreshing ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">刷新</span>
            </Button>
          </div>

          <ProjectTable
            projects={visibleProjects}
            loading={projects.isPending}
            error={projects.error instanceof Error ? projects.error : null}
            hasFilters={hasFilters}
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
      </motion.div>

      <ProjectFormDialog
        open={formOpen}
        onOpenChange={(open) => {
          setFormOpen(open)
          if (!open) setEditingProject(undefined)
        }}
        project={editingProject}
        onCreated={handleCreated}
      />
    </>
  )
}
