import { FolderKanban, LayoutDashboard, Settings, Trash2 } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '../../lib/utils'

const sections = [
  {
    label: '总览',
    items: [
      { to: '/workspace', label: '工作台', icon: LayoutDashboard, end: true },
      { to: '/workspace/projects', label: '项目管理', icon: FolderKanban },
    ],
  },
  {
    label: '系统',
    items: [
      { to: '/workspace/settings', label: '系统设置', icon: Settings },
      { to: '/workspace/recycle-bin', label: '回收站', icon: Trash2 },
    ],
  },
]

export function WorkspaceSidebar({
  onNavigate,
  className,
}: {
  onNavigate?: () => void
  className?: string
}) {
  return (
    <nav
      aria-label="工作台目录"
      className={cn('overflow-y-auto border-r border-[#e4e4e7] bg-white px-3 py-5', className)}
    >
      <div className="space-y-6">
        {sections.map((section) => (
          <section key={section.label}>
            <h2 className="px-3 text-[10px] font-semibold tracking-[0.16em] text-[#a1a1aa]">
              {section.label}
            </h2>
            <div className="mt-2 space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      cn(
                        'flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-[#123b32] text-white shadow-sm'
                          : 'text-[#52525b] hover:bg-[#f4f5f6] hover:text-[#18181b]',
                      )
                    }
                  >
                    <Icon className="size-4" />
                    <span>{item.label}</span>
                  </NavLink>
                )
              })}
            </div>
          </section>
        ))}
      </div>
    </nav>
  )
}
