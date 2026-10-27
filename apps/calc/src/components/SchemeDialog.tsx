import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FolderOpen, LoaderCircle, RefreshCw, Save, Trash2 } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { useEffect, useState } from 'react'
import { createScheme, deleteScheme, fetchSchemes, type SchemeRecord } from '../api/calc'
import { ApiError } from '../api/client'
import type { ProjectRecord } from '../api/projects'
import { StatusBadge } from './StatusBadge'
import { Alert, AlertDescription } from './ui/alert'
import { Button } from './ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { Input } from './ui/input'
import { Skeleton } from './ui/skeleton'

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function errorText(error: unknown) {
  return error instanceof Error ? error.message : String(error)
}

export function SchemeDialog({
  open,
  onClose,
  project,
  module,
  moduleTitle,
  params,
  lastRunId,
  onOpenScheme,
  onSaved,
}: {
  open: boolean
  onClose: () => void
  project: ProjectRecord
  module: string
  moduleTitle?: string
  params: Record<string, unknown>
  lastRunId?: string
  onOpenScheme: (scheme: SchemeRecord) => void
  onSaved: (scheme: SchemeRecord) => void
}) {
  const reducedMotion = useReducedMotion()
  const queryClient = useQueryClient()
  const [schemeName, setSchemeName] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const schemes = useQuery({
    queryKey: ['schemes', project.project_id],
    queryFn: () => fetchSchemes(project.project_id),
    enabled: open,
  })

  useEffect(() => {
    setSchemeName(`${moduleTitle ?? '脚手架'} 方案`)
  }, [moduleTitle, open])

  const createMutation = useMutation({
    mutationFn: (name: string) =>
      createScheme(project.project_id, {
        name,
        module,
        params,
        last_run_id: lastRunId && UUID_PATTERN.test(lastRunId) ? lastRunId : null,
      }),
    onSuccess: async (scheme) => {
      setActionError(null)
      onSaved(scheme)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['schemes', project.project_id] }),
        queryClient.invalidateQueries({ queryKey: ['project', project.project_id] }),
        queryClient.invalidateQueries({ queryKey: ['projects'] }),
      ])
    },
    onError: (error) => setActionError(errorText(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteScheme,
    onSuccess: async () => {
      setActionError(null)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['schemes', project.project_id] }),
        queryClient.invalidateQueries({ queryKey: ['project', project.project_id] }),
        queryClient.invalidateQueries({ queryKey: ['projects'] }),
      ])
    },
    onError: (error) => setActionError(errorText(error)),
  })

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose()}>
      <DialogContent className="max-h-[88vh] overflow-y-auto bg-white p-0 sm:max-w-[760px]">
        <motion.div
          initial={reducedMotion ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.16, ease: 'easeOut' }}
        >
          <DialogHeader className="border-b px-5 py-4">
            <div className="flex items-center gap-3 pr-8">
              <div className="min-w-0">
                <DialogTitle>当前项目方案</DialogTitle>
                <DialogDescription className="mt-1 flex flex-wrap items-center gap-2">
                  <span className="max-w-[320px] truncate font-medium text-[#3f3f46]">
                    {project.name}
                  </span>
                  <span>{project.region}</span>
                  <StatusBadge status={project.status} />
                </DialogDescription>
              </div>
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                className="ml-auto"
                aria-label="刷新方案"
                onClick={() => void schemes.refetch()}
              >
                <RefreshCw className={schemes.isFetching ? 'animate-spin' : ''} />
              </Button>
            </div>
          </DialogHeader>

          <div className="border-b bg-[#fafafa] px-5 py-4">
            <div className="mb-2 text-[11px] font-medium tracking-wide text-[#71717a]">
              保存当前参数
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Input
                aria-label="方案名称"
                value={schemeName}
                onChange={(event) => setSchemeName(event.target.value)}
                className="min-w-0 flex-1 bg-white"
              />
              <Button
                type="button"
                onClick={() => createMutation.mutate(schemeName.trim())}
                disabled={!schemeName.trim() || createMutation.isPending}
                className="bg-[#176b55] text-white hover:bg-[#125744]"
              >
                {createMutation.isPending ? <LoaderCircle className="animate-spin" /> : <Save />}
                保存方案
              </Button>
            </div>
            <p className="mt-2 text-[10px] text-[#a1a1aa]">
              当前模块：{moduleTitle ?? module}
              {lastRunId ? ' · 将关联本次计算结果' : ' · 保存参数草稿'}
            </p>
          </div>

          {(actionError || schemes.error) && (
            <Alert variant="destructive" className="mx-5 mt-4">
              <AlertDescription>
                {actionError ??
                  (schemes.error instanceof ApiError
                    ? schemes.error.detail
                    : `方案加载失败：${errorText(schemes.error)}`)}
              </AlertDescription>
            </Alert>
          )}

          <div className="min-h-56 p-5">
            {schemes.isPending ? (
              <div className="space-y-2" role="status" aria-label="方案加载中">
                {Array.from({ length: 4 }, (_, index) => (
                  <Skeleton key={index} className="h-14 w-full" />
                ))}
              </div>
            ) : schemes.isError ? (
              <div className="grid h-40 place-items-center text-center text-sm text-[#71717a]">
                方案加载失败，请刷新后重试。
              </div>
            ) : (schemes.data?.schemes.length ?? 0) === 0 ? (
              <div className="grid h-40 place-items-center rounded-lg border border-dashed text-center text-sm text-[#71717a]">
                当前项目暂无方案
              </div>
            ) : (
              <div className="space-y-2">
                {schemes.data?.schemes.map((scheme) => (
                  <div
                    key={scheme.scheme_id}
                    className="flex flex-col gap-3 rounded-lg border bg-white px-3 py-3 sm:flex-row sm:items-center"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">{scheme.name}</div>
                      <div className="mt-1 truncate text-[10.5px] text-[#71717a]">
                        {scheme.module_title} ·{' '}
                        {new Date(scheme.updated_at).toLocaleString('zh-CN', { hour12: false })}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => onOpenScheme(scheme)}
                      >
                        <FolderOpen />
                        打开
                      </Button>
                      <Button
                        type="button"
                        variant="destructive"
                        size="icon-sm"
                        aria-label={`删除方案 ${scheme.name}`}
                        disabled={deleteMutation.isPending}
                        onClick={() => {
                          if (window.confirm(`删除方案“${scheme.name}”？`)) {
                            deleteMutation.mutate(scheme.scheme_id)
                          }
                        }}
                      >
                        <Trash2 />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </DialogContent>
    </Dialog>
  )
}
