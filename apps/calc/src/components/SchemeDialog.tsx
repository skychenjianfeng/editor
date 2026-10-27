import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  FolderKanban,
  FolderOpen,
  LoaderCircle,
  Plus,
  RefreshCw,
  Save,
  Search,
  Trash2,
  X,
} from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { useEffect, useMemo, useState } from 'react'
import {
  createProject,
  createScheme,
  deleteProject,
  deleteScheme,
  fetchProjects,
  fetchSchemes,
  type ProjectRecord,
  type SchemeRecord,
} from '../api/calc'

type ProjectDraft = {
  name: string
  code: string
  client: string
  location: string
  designer: string
  note: string
}

const EMPTY_PROJECT: ProjectDraft = {
  name: '',
  code: '',
  client: '',
  location: '',
  designer: '',
  note: '',
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function errorText(error: unknown) {
  return error instanceof Error ? error.message : String(error)
}

function projectLabel(project: ProjectRecord) {
  return project.code ? `${project.code} · ${project.name}` : project.name
}

export function SchemeDialog({
  open,
  onClose,
  module,
  moduleTitle,
  params,
  lastRunId,
  selectedProjectId,
  onOpenScheme,
  onSaved,
}: {
  open: boolean
  onClose: () => void
  module: string
  moduleTitle?: string
  params: Record<string, unknown>
  lastRunId?: string
  selectedProjectId?: string
  onOpenScheme: (project: ProjectRecord, scheme: SchemeRecord) => void
  onSaved: (project: ProjectRecord, scheme: SchemeRecord) => void
}) {
  const reducedMotion = useReducedMotion()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [projectId, setProjectId] = useState<string | undefined>(selectedProjectId)
  const [projectFormOpen, setProjectFormOpen] = useState(false)
  const [projectDraft, setProjectDraft] = useState<ProjectDraft>(EMPTY_PROJECT)
  const [schemeName, setSchemeName] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)

  const projects = useQuery({
    queryKey: ['projects', search],
    queryFn: () => fetchProjects(search),
    enabled: open,
  })

  useEffect(() => {
    if (selectedProjectId) {
      setProjectId(selectedProjectId)
      return
    }
    if (!projectId && projects.data?.projects.length) {
      setProjectId(projects.data.projects[0].project_id)
    }
  }, [projectId, projects.data, selectedProjectId])

  const selectedProject = projects.data?.projects.find(
    (project) => project.project_id === projectId,
  )
  const schemes = useQuery({
    queryKey: ['schemes', projectId],
    queryFn: () => fetchSchemes(projectId as string),
    enabled: open && Boolean(projectId),
  })

  useEffect(() => {
    setSchemeName(`${moduleTitle ?? '脚手架'} 方案`)
  }, [moduleTitle])

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: async (project) => {
      setProjectId(project.project_id)
      setProjectFormOpen(false)
      setProjectDraft(EMPTY_PROJECT)
      setActionError(null)
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error) => setActionError(errorText(error)),
  })

  const deleteProjectMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: async () => {
      setProjectId(undefined)
      setActionError(null)
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error) => setActionError(errorText(error)),
  })

  const createSchemeMutation = useMutation({
    mutationFn: (name: string) => {
      if (!projectId) throw new Error('请先选择或新建项目')
      return createScheme(projectId, {
        name,
        module,
        params,
        last_run_id: lastRunId && UUID_PATTERN.test(lastRunId) ? lastRunId : null,
      })
    },
    onSuccess: async (scheme) => {
      if (selectedProject) onSaved(selectedProject, scheme)
      setActionError(null)
      await queryClient.invalidateQueries({ queryKey: ['schemes', projectId] })
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error) => setActionError(errorText(error)),
  })

  const deleteSchemeMutation = useMutation({
    mutationFn: deleteScheme,
    onSuccess: async () => {
      setActionError(null)
      await queryClient.invalidateQueries({ queryKey: ['schemes', projectId] })
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error) => setActionError(errorText(error)),
  })

  const visibleProjects = useMemo(() => projects.data?.projects ?? [], [projects.data])
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-[color:var(--color-canvas)]/70 p-6 backdrop-blur-[2px]"
      onClick={onClose}
    >
      <motion.section
        role="dialog"
        aria-modal="true"
        aria-labelledby="scheme-dialog-title"
        initial={reducedMotion ? false : { opacity: 0, scale: 0.985 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.16, ease: 'easeOut' }}
        className="flex h-[76vh] min-h-[560px] w-[1080px] overflow-hidden rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-panel)] text-[color:var(--color-ink)] shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <aside className="flex w-[310px] shrink-0 flex-col border-r border-[color:var(--color-line)] bg-[color:var(--color-shell)]">
          <header className="flex h-12 items-center gap-2 border-b border-[color:var(--color-line)] px-3">
            <FolderKanban className="h-4 w-4 text-[#3e63dd]" />
            <span id="scheme-dialog-title" className="text-[13px] font-semibold">
              项目与方案
            </span>
            <button
              type="button"
              onClick={onClose}
              aria-label="关闭方案中心"
              className="ml-auto grid h-7 w-7 place-items-center rounded hover:bg-black/5"
            >
              <X className="h-4 w-4" />
            </button>
          </header>
          <div className="flex items-center gap-2 border-b border-[color:var(--color-line)] px-3 py-2">
            <div className="flex h-7 min-w-0 flex-1 items-center gap-1.5 rounded border border-[color:var(--color-line)] bg-white px-2">
              <Search className="h-3 w-3 text-[color:var(--color-ink-3)]" />
              <input
                aria-label="搜索项目"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="搜索项目"
                className="min-w-0 flex-1 bg-transparent text-[11.5px] outline-none"
              />
            </div>
            <button
              type="button"
              aria-label="新建项目"
              onClick={() => setProjectFormOpen((value) => !value)}
              className="grid h-7 w-7 place-items-center rounded border border-[color:var(--color-line)] bg-white hover:bg-black/[0.03]"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>
          {projectFormOpen && (
            <div className="border-b border-[color:var(--color-line)] p-3">
              <input
                aria-label="项目名称"
                value={projectDraft.name}
                onChange={(event) => setProjectDraft({ ...projectDraft, name: event.target.value })}
                placeholder="项目名称（必填）"
                className="mb-1.5 h-7 w-full rounded border border-[color:var(--color-line)] bg-white px-2 text-[11.5px] outline-none focus:border-[#3e63dd]"
              />
              <div className="mb-1.5 grid grid-cols-2 gap-1.5">
                <input
                  aria-label="项目编号"
                  value={projectDraft.code}
                  onChange={(event) =>
                    setProjectDraft({ ...projectDraft, code: event.target.value })
                  }
                  placeholder="项目编号"
                  className="h-7 min-w-0 rounded border border-[color:var(--color-line)] bg-white px-2 text-[11.5px] outline-none"
                />
                <input
                  aria-label="建设单位"
                  value={projectDraft.client}
                  onChange={(event) =>
                    setProjectDraft({ ...projectDraft, client: event.target.value })
                  }
                  placeholder="建设单位"
                  className="h-7 min-w-0 rounded border border-[color:var(--color-line)] bg-white px-2 text-[11.5px] outline-none"
                />
              </div>
              <div className="mb-1.5 grid grid-cols-2 gap-1.5">
                <input
                  aria-label="项目地点"
                  value={projectDraft.location}
                  onChange={(event) =>
                    setProjectDraft({ ...projectDraft, location: event.target.value })
                  }
                  placeholder="项目地点"
                  className="h-7 min-w-0 rounded border border-[color:var(--color-line)] bg-white px-2 text-[11.5px] outline-none"
                />
                <input
                  aria-label="设计人"
                  value={projectDraft.designer}
                  onChange={(event) =>
                    setProjectDraft({ ...projectDraft, designer: event.target.value })
                  }
                  placeholder="设计人"
                  className="h-7 min-w-0 rounded border border-[color:var(--color-line)] bg-white px-2 text-[11.5px] outline-none"
                />
              </div>
              <textarea
                aria-label="项目说明"
                value={projectDraft.note}
                onChange={(event) => setProjectDraft({ ...projectDraft, note: event.target.value })}
                placeholder="项目说明"
                rows={2}
                className="mb-1.5 w-full resize-none rounded border border-[color:var(--color-line)] bg-white px-2 py-1 text-[11.5px] outline-none"
              />
              <button
                type="button"
                disabled={!projectDraft.name.trim() || createProjectMutation.isPending}
                onClick={() => createProjectMutation.mutate(projectDraft)}
                className="flex h-7 w-full items-center justify-center gap-1.5 rounded bg-[color:var(--color-ink)] text-[11.5px] font-medium text-white disabled:opacity-40"
              >
                {createProjectMutation.isPending ? (
                  <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Plus className="h-3.5 w-3.5" />
                )}
                创建项目
              </button>
            </div>
          )}
          <div className="min-h-0 flex-1 overflow-y-auto p-2">
            {projects.isPending ? (
              <div className="grid h-32 place-items-center text-[11.5px] text-[color:var(--color-ink-3)]">
                <LoaderCircle className="h-5 w-5 animate-spin" />
              </div>
            ) : visibleProjects.length === 0 ? (
              <div className="grid h-32 place-items-center px-5 text-center text-[11.5px] leading-relaxed text-[color:var(--color-ink-3)]">
                暂无项目，先创建一个项目
              </div>
            ) : (
              visibleProjects.map((project) => (
                <button
                  type="button"
                  key={project.project_id}
                  onClick={() => setProjectId(project.project_id)}
                  className={`mb-1 w-full rounded-md border px-3 py-2 text-left ${
                    projectId === project.project_id
                      ? 'border-[#b5c4ff] bg-[#eef2ff]'
                      : 'border-transparent hover:border-[color:var(--color-line)] hover:bg-black/[0.025]'
                  }`}
                >
                  <div className="truncate text-[12px] font-medium">{project.name}</div>
                  <div className="mt-0.5 truncate text-[10px] text-[color:var(--color-ink-3)]">
                    {projectLabel(project)} · {project.location || '未填写地点'}
                  </div>
                </button>
              ))
            )}
          </div>
          <div className="border-t border-[color:var(--color-line)] p-2 text-[9.5px] text-[color:var(--color-ink-3)]">
            项目删除会级联删除所属方案
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-12 items-center gap-2 border-b border-[color:var(--color-line)] px-4">
            <div className="min-w-0">
              <div className="truncate text-[13px] font-semibold">
                {selectedProject?.name ?? '选择项目'}
              </div>
              <div className="truncate text-[10px] text-[color:var(--color-ink-3)]">
                {selectedProject
                  ? [selectedProject.code, selectedProject.client, selectedProject.location]
                      .filter(Boolean)
                      .join(' · ') || '未填写项目信息'
                  : '方案依附于工程项目保存'}
              </div>
            </div>
            <div className="ml-auto flex gap-1">
              <button
                type="button"
                aria-label="刷新方案"
                onClick={() => {
                  void projects.refetch()
                  void schemes.refetch()
                }}
                className="grid h-7 w-7 place-items-center rounded border border-[color:var(--color-line)] hover:bg-black/[0.03]"
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${projects.isFetching || schemes.isFetching ? 'animate-spin' : ''}`}
                />
              </button>
              {selectedProject && (
                <button
                  type="button"
                  aria-label="删除项目"
                  onClick={() => {
                    if (window.confirm(`删除项目“${selectedProject.name}”及其全部方案？`)) {
                      deleteProjectMutation.mutate(selectedProject.project_id)
                    }
                  }}
                  className="grid h-7 w-7 place-items-center rounded border border-[#f5c2c4] text-[#c62a2f] hover:bg-[#fff5f5]"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </header>

          <div className="border-b border-[color:var(--color-line)] bg-[color:var(--color-shell)] px-4 py-3">
            <div className="mb-1.5 text-[10px] font-medium tracking-wide text-[color:var(--color-ink-3)]">
              保存当前工况
            </div>
            <div className="flex gap-2">
              <input
                aria-label="方案名称"
                value={schemeName}
                onChange={(event) => setSchemeName(event.target.value)}
                className="h-8 min-w-0 flex-1 rounded border border-[color:var(--color-line)] bg-white px-2.5 text-[12px] outline-none focus:border-[#3e63dd]"
              />
              <button
                type="button"
                disabled={!projectId || !schemeName.trim() || createSchemeMutation.isPending}
                onClick={() => createSchemeMutation.mutate(schemeName.trim())}
                className="flex h-8 items-center gap-1.5 rounded bg-[color:var(--color-ink)] px-3 text-[11.5px] font-medium text-white disabled:opacity-40"
              >
                {createSchemeMutation.isPending ? (
                  <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Save className="h-3.5 w-3.5" />
                )}
                保存方案
              </button>
            </div>
            <div className="mt-1 text-[9.5px] text-[color:var(--color-ink-3)]">
              当前模块：{moduleTitle ?? module}。保存关联本次 run_id；之后可重新打开继续修改。
            </div>
          </div>

          {actionError && (
            <div
              role="alert"
              className="m-3 rounded border border-[#f5c2c4] bg-[#fff5f5] px-3 py-2 text-[11px] text-[#c62a2f]"
            >
              {actionError}
            </div>
          )}

          <div className="min-h-0 flex-1 overflow-y-auto p-3">
            {!projectId ? (
              <div className="grid h-48 place-items-center text-[12px] text-[color:var(--color-ink-3)]">
                请先选择项目
              </div>
            ) : schemes.isPending ? (
              <div className="grid h-48 place-items-center text-[11.5px] text-[color:var(--color-ink-3)]">
                <LoaderCircle className="h-5 w-5 animate-spin" />
              </div>
            ) : schemes.isError ? (
              <div
                role="alert"
                className="rounded border border-[#f5c2c4] bg-[#fff5f5] px-3 py-2 text-[11px] text-[#c62a2f]"
              >
                方案加载失败：{errorText(schemes.error)}
              </div>
            ) : (schemes.data?.schemes.length ?? 0) === 0 ? (
              <div className="grid h-48 place-items-center text-[12px] text-[color:var(--color-ink-3)]">
                当前项目暂无方案
              </div>
            ) : (
              <div className="space-y-1.5">
                {schemes.data?.schemes.map((scheme) => (
                  <div
                    key={scheme.scheme_id}
                    className="flex items-center gap-3 rounded-md border border-[color:var(--color-line)] px-3 py-2.5 hover:bg-black/[0.015]"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[12px] font-medium">{scheme.name}</div>
                      <div className="mt-0.5 truncate text-[10px] text-[color:var(--color-ink-3)]">
                        {scheme.module_title} ·{' '}
                        {new Date(scheme.updated_at).toLocaleString('zh-CN', { hour12: false })}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        if (selectedProject) onOpenScheme(selectedProject, scheme)
                      }}
                      className="flex h-7 items-center gap-1 rounded border border-[color:var(--color-line)] px-2 text-[11px] hover:bg-black/[0.03]"
                    >
                      <FolderOpen className="h-3.5 w-3.5" /> 打开
                    </button>
                    <button
                      type="button"
                      aria-label={`删除方案 ${scheme.name}`}
                      onClick={() => {
                        if (window.confirm(`删除方案“${scheme.name}”？`)) {
                          deleteSchemeMutation.mutate(scheme.scheme_id)
                        }
                      }}
                      className="grid h-7 w-7 place-items-center rounded border border-[#f5c2c4] text-[#c62a2f] hover:bg-[#fff5f5]"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </motion.section>
    </div>
  )
}
