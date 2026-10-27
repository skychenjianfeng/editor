import { ProjectWorkspacePanel } from '../components/workspace/ProjectWorkspacePanel'

export function ProjectManagementPage() {
  return (
    <div className="mx-auto w-full max-w-[1480px] px-4 py-7 text-[#18181b] sm:px-6 sm:py-9">
      <section>
        <p className="text-[11px] font-semibold tracking-[0.18em] text-[#176b55]">
          PROJECT MANAGEMENT
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">项目管理</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#71717a]">
          搜索、筛选并维护项目资料；进入任一项目后可继续管理计算方案和结果。
        </p>
      </section>
      <ProjectWorkspacePanel variant="management" />
    </div>
  )
}
