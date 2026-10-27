import { Clock3, FolderKanban, Menu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { BRAND_MARK, BRAND_NAME } from '../branding'
import { UserMenu } from './UserMenu'

export function WorkspaceHeader({ onOpenDirectory }: { onOpenDirectory?: () => void }) {
  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-[#102a24] text-white shadow-sm">
      <div className="mx-auto flex h-14 max-w-[1480px] items-center gap-5 px-4 sm:px-6">
        {onOpenDirectory ? (
          <button
            type="button"
            aria-label="打开工作台目录"
            onClick={onOpenDirectory}
            className="grid size-8 shrink-0 place-items-center rounded-md text-white/75 outline-none hover:bg-white/10 focus-visible:ring-2 focus-visible:ring-lime-200 lg:hidden"
          >
            <Menu className="size-5" />
          </button>
        ) : null}
        <Link to="/workspace" className="flex items-center gap-2.5">
          <span className="grid size-8 place-items-center rounded-md bg-[#d9f99d] text-[11px] font-black text-[#173c32]">
            {BRAND_MARK}
          </span>
          <span className="text-sm font-semibold tracking-[0.12em]">{BRAND_NAME}</span>
        </Link>
        <div className="hidden h-5 w-px bg-white/15 sm:block" />
        <span className="hidden items-center gap-1.5 text-xs font-medium text-white/65 sm:flex">
          <FolderKanban className="size-3.5" />
          项目工作台
        </span>
        <span className="hidden items-center gap-1.5 text-xs text-white/40 md:flex">
          <Clock3 className="size-3.5" />
          最近计算
        </span>
        <div className="ml-auto">
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
