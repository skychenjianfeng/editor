import type { ProjectStatus } from '../api/projects'
import { Badge } from './ui/badge'

const styles: Record<ProjectStatus, string> = {
  preparing: 'border-[#f2cf87] bg-[#fff8e7] text-[#8a5800]',
  calculating: 'border-[#75a894] bg-[#e7f3ee] text-[#145943]',
  completed: 'border-[#b7c2d6] bg-[#edf1f7] text-[#45566f]',
}

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  preparing: '筹备中',
  calculating: '计算中',
  completed: '已完成',
}

export function StatusBadge({ status, className }: { status: ProjectStatus; className?: string }) {
  return (
    <Badge variant="outline" className={`${styles[status]} ${className ?? ''}`}>
      <span
        aria-hidden="true"
        className={`size-1.5 rounded-full ${
          status === 'preparing'
            ? 'bg-[#d68a00]'
            : status === 'calculating'
              ? 'bg-[#176b55]'
              : 'bg-[#63758f]'
        }`}
      />
      {STATUS_LABELS[status]}
    </Badge>
  )
}
