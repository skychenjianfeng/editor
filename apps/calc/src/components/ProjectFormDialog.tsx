import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, LoaderCircle } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { ApiError } from '../api/client'
import {
  createProject,
  PROJECT_STATUSES,
  type ProjectFormValues,
  type ProjectRecord,
  REGIONS,
  updateProject,
} from '../api/projects'
import { Alert, AlertDescription } from './ui/alert'
import { Button } from './ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'

export type ProjectCreateIntent = 'enter' | 'stay'

const schema = z.object({
  name: z.string().trim().min(1, '项目名称必填').max(200, '项目名称不能超过 200 个字符'),
  region: z.enum(REGIONS, { message: '请选择项目地区' }),
  status: z.enum(['preparing', 'calculating', 'completed']),
  code: z.string().max(100, '项目编号不能超过 100 个字符'),
  client: z.string().max(200, '建设单位不能超过 200 个字符'),
  location: z.string().max(255, '项目地点不能超过 255 个字符'),
  designer: z.string().max(100, '设计人不能超过 100 个字符'),
  note: z.string(),
})

const EMPTY_VALUES: ProjectFormValues = {
  name: '',
  region: '全国',
  status: 'preparing',
  code: '',
  client: '',
  location: '',
  designer: '',
  note: '',
}

function valuesFromProject(project?: ProjectRecord): ProjectFormValues {
  if (!project) return EMPTY_VALUES
  return {
    name: project.name,
    region: project.region,
    status: project.status,
    code: project.code,
    client: project.client,
    location: project.location,
    designer: project.designer,
    note: project.note,
  }
}

export function ProjectFormDialog({
  open,
  onOpenChange,
  project,
  onCreated,
  onUpdated,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  project?: ProjectRecord
  onCreated?: (project: ProjectRecord, intent: ProjectCreateIntent) => void
  onUpdated?: (project: ProjectRecord) => void
}) {
  const reducedMotion = useReducedMotion()
  const queryClient = useQueryClient()
  const editing = Boolean(project)
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY_VALUES,
  })

  useEffect(() => {
    if (open) {
      form.reset(valuesFromProject(project))
    }
  }, [form, open, project])

  const mutation = useMutation({
    mutationFn: async ({
      values,
      intent,
    }: {
      values: ProjectFormValues
      intent: ProjectCreateIntent
    }) => ({
      saved: project
        ? await updateProject(project.project_id, values)
        : await createProject(values),
      intent,
    }),
    onSuccess: async ({ saved, intent }) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['projects'] }),
        queryClient.invalidateQueries({ queryKey: ['project', saved.project_id] }),
      ])
      onOpenChange(false)
      if (editing) onUpdated?.(saved)
      else onCreated?.(saved, intent)
    },
    onError: (error) => {
      if (!(error instanceof ApiError)) {
        form.setError('root.server', { message: '项目保存失败，请稍后重试' })
        return
      }
      for (const field of Object.keys(error.errors) as (keyof ProjectFormValues)[]) {
        const message = error.errors[field]?.[0]
        if (message) form.setError(field, { message })
      }
      form.setError('root.server', { message: error.detail })
    },
  })

  function submit(intent: ProjectCreateIntent) {
    void form.handleSubmit((values) => mutation.mutate({ values, intent }))()
  }

  const pending = mutation.isPending || form.formState.isSubmitting

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto bg-white p-0 sm:max-w-[600px]">
        <motion.div
          initial={reducedMotion ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.16, ease: 'easeOut' }}
        >
          <DialogHeader className="border-b px-5 py-4">
            <DialogTitle>{editing ? '编辑项目' : '新建项目'}</DialogTitle>
            <DialogDescription>
              {editing
                ? '地区与状态只更新项目资料，不改变已有方案参数或计算结果。'
                : '为本次计算建立项目上下文。保存后可在工作台持续跟踪方案进度。'}
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={form.handleSubmit((values) => mutation.mutate({ values, intent: 'stay' }))}
            noValidate
          >
            <div className="space-y-4 px-5 py-4">
              {form.formState.errors.root?.server?.message && (
                <Alert variant="destructive">
                  <AlertCircle />
                  <AlertDescription>{form.formState.errors.root.server.message}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="project-name">
                  项目名称 <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="project-name"
                  aria-label="项目名称"
                  autoFocus
                  aria-invalid={Boolean(form.formState.errors.name)}
                  aria-describedby={form.formState.errors.name ? 'project-name-error' : undefined}
                  {...form.register('name')}
                />
                {form.formState.errors.name && (
                  <p id="project-name-error" className="text-xs text-destructive">
                    {form.formState.errors.name.message}
                  </p>
                )}
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="project-region">
                    项目地区 <span className="text-destructive">*</span>
                  </Label>
                  <select
                    id="project-region"
                    aria-label="项目地区"
                    className="h-8 w-full rounded-lg border border-input bg-white px-2.5 text-sm outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
                    {...form.register('region')}
                  >
                    {REGIONS.map((region) => (
                      <option key={region} value={region}>
                        {region}
                      </option>
                    ))}
                  </select>
                  <p className="text-[11px] leading-4 text-[#71717a]">
                    地区随项目保存，当前计算规则暂不随地区切换。
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="project-status">项目状态</Label>
                  <select
                    id="project-status"
                    aria-label="项目状态"
                    className="h-8 w-full rounded-lg border border-input bg-white px-2.5 text-sm outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
                    {...form.register('status')}
                  >
                    {PROJECT_STATUSES.map((status) => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="project-code">项目编号</Label>
                  <Input id="project-code" {...form.register('code')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-client">建设单位</Label>
                  <Input id="project-client" {...form.register('client')} />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="project-location">项目地点</Label>
                  <Input id="project-location" {...form.register('location')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-designer">设计人</Label>
                  <Input id="project-designer" {...form.register('designer')} />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="project-note">项目说明</Label>
                <Textarea id="project-note" rows={3} {...form.register('note')} />
              </div>
            </div>

            <DialogFooter className="bg-[#fafafa] px-5 py-3">
              <Button
                type="button"
                variant="ghost"
                onClick={() => onOpenChange(false)}
                disabled={pending}
              >
                取消
              </Button>
              {!editing && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => submit('stay')}
                  disabled={pending}
                >
                  仅创建
                </Button>
              )}
              <Button
                type="button"
                onClick={() => submit(editing ? 'stay' : 'enter')}
                disabled={pending}
                aria-busy={pending}
                className="bg-[#176b55] text-white hover:bg-[#125744]"
              >
                {pending && <LoaderCircle className="animate-spin" />}
                {editing ? '保存修改' : '创建并进入'}
              </Button>
            </DialogFooter>
          </form>
        </motion.div>
      </DialogContent>
    </Dialog>
  )
}
