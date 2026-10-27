import { LoaderCircle } from 'lucide-react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useCurrentUser } from './api/auth'
import { ApiError } from './api/client'
import { AuthGate } from './auth/AuthGate'
import { WorkspaceLayout } from './components/workspace/WorkspaceLayout'
import { CalcWorkspacePage } from './pages/CalcWorkspacePage'
import { LoginPage } from './pages/LoginPage'
import { ProjectManagementPage } from './pages/ProjectManagementPage'
import { RecycleBinPage } from './pages/RecycleBinPage'
import { RegisterPage } from './pages/RegisterPage'
import { WorkspacePage } from './pages/WorkspacePage'
import { WorkspaceSettingsPage } from './pages/WorkspaceSettingsPage'

function RootRedirect() {
  const currentUser = useCurrentUser()

  if (currentUser.isPending) {
    return (
      <main role="status" className="grid min-h-screen place-items-center bg-[#f7f7f8]">
        <div className="flex items-center gap-2 text-sm text-[#52525b]">
          <LoaderCircle className="size-4 animate-spin text-[#176b55]" />
          正在恢复会话
        </div>
      </main>
    )
  }

  if (currentUser.isError) {
    if (currentUser.error instanceof ApiError && currentUser.error.status !== 401) {
      return (
        <main className="grid min-h-screen place-items-center bg-[#f7f7f8] p-6">
          <div className="rounded-xl border bg-white p-6 text-center">
            <p className="text-sm font-medium">暂时无法连接服务</p>
            <p className="mt-1 text-xs text-[#71717a]">请稍后刷新页面重试。</p>
          </div>
        </main>
      )
    }
    return <Navigate to="/login" replace />
  }

  return <Navigate to="/workspace" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<AuthGate />}>
        <Route path="/workspace" element={<WorkspaceLayout />}>
          <Route index element={<WorkspacePage />} />
          <Route path="projects" element={<ProjectManagementPage />} />
          <Route path="settings" element={<WorkspaceSettingsPage />} />
          <Route path="recycle-bin" element={<RecycleBinPage />} />
        </Route>
        <Route path="/projects/:projectId/calc" element={<CalcWorkspacePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
