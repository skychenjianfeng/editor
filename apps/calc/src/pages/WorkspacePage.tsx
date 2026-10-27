import { ProjectWorkspacePanel } from '../components/workspace/ProjectWorkspacePanel'

export function WorkspacePage() {
  return (
    <div className="mx-auto w-full max-w-[1480px] px-4 py-7 text-[#18181b] sm:px-6 sm:py-9">
      <section>
        <p className="text-[11px] font-semibold tracking-[0.18em] text-[#176b55]">
          PROJECT WORKSPACE
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">项目工作台</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#71717a]">
          按项目集中管理方案、计算状态和最近结果。地区作为项目属性保存，不改变当前计算规则。
        </p>
      </section>
      <ProjectWorkspacePanel variant="overview" />
    </div>
  )
}
