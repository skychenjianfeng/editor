import { Outlet } from 'react-router-dom'
import { WorkspaceHeader } from '../WorkspaceHeader'
import { WorkspaceSidebar } from './WorkspaceSidebar'

export function WorkspaceLayout() {
  return (
    <div className="min-h-screen bg-[#f4f5f6]">
      <WorkspaceHeader />
      <div className="mx-auto flex w-full max-w-[1660px]">
        <aside className="hidden w-[232px] shrink-0 lg:block">
          <WorkspaceSidebar className="sticky top-14 h-[calc(100vh-3.5rem)]" />
        </aside>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
