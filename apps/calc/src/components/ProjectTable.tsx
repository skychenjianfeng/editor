import { createColumnHelper, tableFeatures, useTable } from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import { AlertCircle, ArrowRight, LoaderCircle, MoreHorizontal, Trash2 } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { useMemo, useRef, useState } from 'react'
import type { ProjectRecord } from '../api/projects'
import { StatusBadge } from './StatusBadge'
import { Alert, AlertDescription, AlertTitle } from './ui/alert'
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog'
import { Button } from './ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'
import { Skeleton } from './ui/skeleton'

const features = tableFeatures({})
const columnHelper = createColumnHelper<typeof features, ProjectRecord>()

const ROW_GRID =
  'grid grid-cols-[minmax(0,1fr)_88px_96px] items-center gap-2 md:grid-cols-[minmax(220px,2fr)_100px_110px_80px_150px_150px_140px]'

function formatDate(value: string | null) {
  if (!value) return '尚未计算'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(value))
}

export function ProjectTable({
  projects,
  loading,
  error,
  hasFilters,
  onRetry,
  onClearFilters,
  onEnter,
  onEdit,
  onDelete,
}: {
  projects: ProjectRecord[]
  loading: boolean
  error: Error | null
  hasFilters: boolean
  onRetry: () => void
  onClearFilters: () => void
  onEnter: (project: ProjectRecord) => void
  onEdit: (project: ProjectRecord) => void
  onDelete: (project: ProjectRecord) => Promise<void>
}) {
  const reducedMotion = useReducedMotion()
  const scrollRef = useRef<HTMLDivElement>(null)
  const [deleteTarget, setDeleteTarget] = useState<ProjectRecord>()
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string>()

  const columns = useMemo(
    () =>
      columnHelper.columns([
        columnHelper.display({
          id: 'project',
          header: '项目',
          cell: ({ row }) => (
            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-[#27272a]">{row.original.name}</div>
              <div className="mt-0.5 truncate font-mono text-[10px] text-[#a1a1aa]">
                {row.original.code || '未设置项目编号'}
              </div>
            </div>
          ),
        }),
        columnHelper.accessor('region', {
          header: '地区',
          cell: ({ row }) => <span className="hidden text-xs md:block">{row.original.region}</span>,
        }),
        columnHelper.accessor('status', {
          header: '状态',
          cell: ({ row }) => <StatusBadge status={row.original.status} />,
        }),
        columnHelper.accessor('scheme_count', {
          header: '方案数',
          cell: ({ row }) => (
            <span className="tnum hidden text-sm md:block">{row.original.scheme_count}</span>
          ),
        }),
        columnHelper.display({
          id: 'last-calculated',
          header: '最近计算',
          cell: ({ row }) => (
            <span className="tnum hidden text-xs text-[#71717a] lg:block">
              {formatDate(row.original.last_calculated_at)}
            </span>
          ),
        }),
        columnHelper.display({
          id: 'updated',
          header: '更新时间',
          cell: ({ row }) => (
            <span className="tnum hidden text-xs text-[#71717a] lg:block">
              {formatDate(row.original.updated_at)}
            </span>
          ),
        }),
        columnHelper.display({
          id: 'actions',
          header: '',
          cell: ({ row }) => (
            <div className="flex justify-end gap-1" onClick={(event) => event.stopPropagation()}>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onEnter(row.original)}
                aria-label={`进入计算 ${row.original.name}`}
              >
                <span className="hidden sm:inline">进入计算</span>
                <ArrowRight />
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    size="icon-sm"
                    variant="ghost"
                    aria-label={`更多操作 ${row.original.name}`}
                  >
                    <MoreHorizontal />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-36">
                  <DropdownMenuItem onSelect={() => onEdit(row.original)}>
                    编辑项目
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    variant="destructive"
                    onSelect={() => {
                      setDeleteError(undefined)
                      setDeleteTarget(row.original)
                    }}
                  >
                    <Trash2 />
                    删除项目
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ),
        }),
      ]),
    [onEdit, onEnter],
  )

  const table = useTable({
    features,
    data: projects,
    columns,
    getRowId: (row) => row.project_id,
  })
  const rows = table.getRowModel().rows
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 64,
    overscan: 8,
    initialRect: { width: 1000, height: 440 },
  })
  const measuredRows = virtualizer.getVirtualItems()
  const visibleRows =
    measuredRows.length > 0
      ? measuredRows
      : rows.slice(0, 8).map((_, index) => ({
          index,
          key: index,
          start: index * 64,
          size: 64,
        }))

  async function confirmDelete() {
    if (!deleteTarget) return
    setDeleting(true)
    setDeleteError(undefined)
    try {
      await onDelete(deleteTarget)
      setDeleteTarget(undefined)
    } catch (reason) {
      setDeleteError(reason instanceof Error ? reason.message : '删除失败，请重试')
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div
        role="status"
        aria-label="项目加载中"
        className="overflow-hidden rounded-lg border bg-white"
      >
        {Array.from({ length: 6 }, (_, index) => (
          <div key={index} className={`${ROW_GRID} min-h-16 border-b px-4 py-3 last:border-b-0`}>
            <div className="space-y-2">
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-3 w-20" />
            </div>
            <Skeleton className="hidden h-5 w-14 md:block" />
            <Skeleton className="h-5 w-16" />
            <Skeleton className="hidden h-4 w-8 md:block" />
            <Skeleton className="hidden h-4 w-28 lg:block" />
            <Skeleton className="hidden h-4 w-28 lg:block" />
            <Skeleton className="h-8 w-24 justify-self-end" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive" className="bg-white">
        <AlertCircle />
        <AlertTitle>项目加载失败</AlertTitle>
        <AlertDescription className="flex items-center justify-between gap-4">
          <span>{error.message}</span>
          <Button variant="outline" size="sm" onClick={onRetry}>
            重试
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="grid min-h-72 place-items-center rounded-lg border border-dashed bg-white px-6 text-center">
        <div>
          <div className="mx-auto grid size-11 place-items-center rounded-full bg-[#e7f3ee] text-[#176b55]">
            {hasFilters ? <AlertCircle className="size-5" /> : <ArrowRight className="size-5" />}
          </div>
          <h2 className="mt-3 text-sm font-semibold">
            {hasFilters ? '没有匹配的项目' : '从第一个项目开始'}
          </h2>
          <p className="mt-1 text-xs text-[#71717a]">
            {hasFilters ? '调整搜索词或状态，查看其他项目。' : '新建项目后即可进入计算工作区。'}
          </p>
          {hasFilters && (
            <Button variant="outline" size="sm" className="mt-4" onClick={onClearFilters}>
              清除筛选
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="overflow-hidden rounded-lg border bg-white shadow-[0_1px_2px_rgba(24,24,27,0.03)]">
        <div role="table" aria-label="项目列表" className="min-w-0 text-sm" style={{ minWidth: 0 }}>
          <div
            role="row"
            tabIndex={-1}
            className={`${ROW_GRID} min-h-10 border-b bg-[#f8f9fa] px-4 text-[10px] font-medium tracking-wide text-[#71717a]`}
          >
            {table.getHeaderGroups()[0]?.headers.map((header, index) => (
              <div
                key={header.id}
                role="columnheader"
                tabIndex={-1}
                className={
                  index === 1 || index === 3 || index === 4 || index === 5
                    ? 'hidden md:block'
                    : index === 6
                      ? 'text-right'
                      : ''
                }
              >
                {header.isPlaceholder ? null : <table.FlexRender header={header} />}
              </div>
            ))}
          </div>

          <div
            ref={scrollRef}
            className="max-h-[min(58vh,620px)] overflow-y-auto overflow-x-hidden"
          >
            <div className="relative w-full" style={{ height: virtualizer.getTotalSize() }}>
              {visibleRows.map((virtualRow) => {
                const row = rows[virtualRow.index]
                if (!row) return null
                return (
                  <motion.div
                    key={row.id}
                    role="row"
                    aria-label={`${row.original.name} ${row.original.region} ${row.original.status_label}`}
                    tabIndex={0}
                    initial={reducedMotion ? false : { opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.12 }}
                    onClick={() => onEnter(row.original)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        onEnter(row.original)
                      }
                    }}
                    className={`${ROW_GRID} absolute left-0 w-full cursor-pointer border-b px-4 py-2.5 outline-none hover:bg-[#f7faf8] focus-visible:bg-[#eef7f2] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#176b55]`}
                    style={{
                      height: virtualRow.size,
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    {row.getAllCells().map((cell, index) => (
                      <div
                        key={cell.id}
                        role="cell"
                        className={
                          index === 1 || index === 3 || index === 4 || index === 5
                            ? 'hidden md:block'
                            : ''
                        }
                      >
                        <table.FlexRender cell={cell} />
                      </div>
                    ))}
                  </motion.div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      <AlertDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !deleting) setDeleteTarget(undefined)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>删除“{deleteTarget?.name}”？</AlertDialogTitle>
            <AlertDialogDescription>
              这会同时级联删除该项目下的全部方案。此操作不可撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          {deleteError && (
            <Alert variant="destructive">
              <AlertCircle />
              <AlertDescription>{deleteError}</AlertDescription>
            </Alert>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>取消</AlertDialogCancel>
            <Button
              type="button"
              variant="destructive"
              onClick={() => void confirmDelete()}
              disabled={deleting}
            >
              {deleting && <LoaderCircle className="animate-spin" />}
              {deleting ? '正在删除…' : '确认删除'}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
