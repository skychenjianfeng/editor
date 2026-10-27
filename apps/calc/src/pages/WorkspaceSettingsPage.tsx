import { Database, MapPinned, MonitorSmartphone, ShieldCheck, UserRound } from 'lucide-react'
import { useCurrentUser } from '../api/auth'
import { BRAND_NAME } from '../branding'

export function WorkspaceSettingsPage() {
  const currentUser = useCurrentUser()

  return (
    <div className="mx-auto w-full max-w-[1120px] px-4 py-7 text-[#18181b] sm:px-6 sm:py-9">
      <section>
        <p className="text-[11px] font-semibold tracking-[0.18em] text-[#176b55]">
          WORKSPACE SETTINGS
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">系统设置</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#71717a]">
          当前为只读信息页，展示账号、品牌以及工作区的数据边界。
        </p>
      </section>

      <section
        aria-labelledby="account-settings-heading"
        className="mt-6 rounded-lg border bg-white"
      >
        <div className="border-b px-5 py-4">
          <h2 id="account-settings-heading" className="text-sm font-semibold">
            账号与品牌
          </h2>
        </div>
        <dl className="divide-y">
          <div className="grid gap-2 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:items-start">
            <dt className="flex items-center gap-2 text-xs font-medium text-[#71717a]">
              <UserRound className="size-4" />
              当前账号
            </dt>
            <dd>
              <div className="text-sm font-medium">
                {currentUser.data?.display_name || (currentUser.isError ? '无法读取' : '正在读取…')}
              </div>
              <div className="mt-1 text-xs text-[#71717a]">
                {currentUser.data?.email || (currentUser.isError ? '请稍后刷新页面重试' : '')}
              </div>
            </dd>
          </div>
          <div className="grid gap-2 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:items-start">
            <dt className="flex items-center gap-2 text-xs font-medium text-[#71717a]">
              <ShieldCheck className="size-4" />
              产品品牌
            </dt>
            <dd className="text-sm font-medium">{BRAND_NAME}</dd>
          </div>
        </dl>
      </section>

      <section
        aria-labelledby="workspace-boundaries-heading"
        className="mt-4 rounded-lg border bg-white"
      >
        <div className="border-b px-5 py-4">
          <h2 id="workspace-boundaries-heading" className="text-sm font-semibold">
            数据与会话边界
          </h2>
        </div>
        <dl className="divide-y">
          <div className="grid gap-2 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:items-start">
            <dt className="flex items-center gap-2 text-xs font-medium text-[#71717a]">
              <Database className="size-4" />
              数据归属
            </dt>
            <dd className="text-sm leading-6 text-[#52525b]">
              项目、方案和计算结果归属于当前登录账号，以服务端记录为准。
            </dd>
          </div>
          <div className="grid gap-2 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:items-start">
            <dt className="flex items-center gap-2 text-xs font-medium text-[#71717a]">
              <MapPinned className="size-4" />
              地区边界
            </dt>
            <dd className="text-sm leading-6 text-[#52525b]">
              地区只作为项目属性，不切换当前计算规范。
            </dd>
          </div>
          <div className="grid gap-2 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:items-start">
            <dt className="flex items-center gap-2 text-xs font-medium text-[#71717a]">
              <MonitorSmartphone className="size-4" />
              会话说明
            </dt>
            <dd className="text-sm leading-6 text-[#52525b]">
              登录状态由当前浏览器会话维护；如需切换账号，请使用页面右上角的账号菜单。
            </dd>
          </div>
        </dl>
      </section>
    </div>
  )
}
