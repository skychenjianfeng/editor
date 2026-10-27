import { ChevronDown, LogOut, UserRound } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useCurrentUser, useLogout } from '../api/auth'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'

export function UserMenu() {
  const navigate = useNavigate()
  const currentUser = useCurrentUser()
  const logout = useLogout()
  const name = currentUser.data?.display_name ?? '工程用户'
  const initial = name.trim().charAt(0).toUpperCase() || 'P'

  async function signOut() {
    await logout.mutateAsync()
    navigate('/login', { replace: true })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-white/75 outline-none hover:bg-white/10 focus-visible:ring-2 focus-visible:ring-lime-200"
        >
          <span className="grid size-7 place-items-center rounded-full bg-[#d9f99d] text-xs font-semibold text-[#173c32]">
            {initial}
          </span>
          <span className="hidden max-w-32 truncate sm:block">{name}</span>
          <ChevronDown className="size-3 opacity-60" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuLabel className="space-y-1">
          <span className="flex items-center gap-1.5 text-[#3f3f46]">
            <UserRound className="size-3.5" />
            当前账号
          </span>
          <span className="block truncate font-normal text-[#71717a]">
            {currentUser.data?.email ?? '正在读取账号'}
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={() => void signOut()}
          disabled={logout.isPending}
          className="gap-2"
        >
          <LogOut className="size-4" />
          {logout.isPending ? '正在退出…' : '退出登录'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
