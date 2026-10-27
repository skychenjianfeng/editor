# 工作台左侧目录 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为玄构天枢工作台增加桌面左侧目录、移动抽屉、工作台总览、项目管理、系统设置与回收站入口。

**Architecture:** 用嵌套路由和 `WorkspaceLayout` 共享页头、目录与内容容器；抽取 `ProjectWorkspacePanel` 复用项目查询、筛选、CRUD 和项目表，工作台总览与项目管理只提供不同页面说明和展示密度。

**Tech Stack:** React 19、TypeScript、Vite、React Router、TanStack Query/Table、shadcn Nova、Lucide、Motion、Vitest、Playwright。

## Global Constraints

- 品牌保持“玄构天枢”。
- 目录项固定为：工作台、项目管理、系统设置、回收站。
- 路由固定为：`/workspace`、`/workspace/projects`、`/workspace/settings`、`/workspace/recycle-bin`。
- 桌面目录宽 232px；移动端使用抽屉，不常驻。
- 项目数据继续由 TanStack Query 管理，不复制到 Zustand。
- 不新增后端模型、迁移或接口。
- 不实现软删除、恢复、彻底删除或可编辑系统设置。
- 计算页 `/projects/:projectId/calc` 和计算逻辑保持不变。
- 所有新增图标使用 Lucide；动画使用 `motion/react` 并尊重 reduced motion。
- 不得使用 `git add -A`，不得提交无关脏文件。

---

### Task 1: 工作台路由外壳与目录

**Files:**
- Create: `apps/calc/src/components/workspace/WorkspaceSidebar.tsx`
- Create: `apps/calc/src/components/workspace/WorkspaceLayout.tsx`
- Create: `apps/calc/src/components/workspace/WorkspaceLayout.test.tsx`
- Create as route placeholders: `apps/calc/src/pages/ProjectManagementPage.tsx`
- Create as route placeholders: `apps/calc/src/pages/WorkspaceSettingsPage.tsx`
- Create as route placeholders: `apps/calc/src/pages/RecycleBinPage.tsx`
- Modify: `apps/calc/src/pages/WorkspacePage.tsx`
- Modify: `apps/calc/src/components/WorkspaceHeader.tsx`
- Modify: `apps/calc/src/App.tsx`
- Test: `apps/calc/src/App.test.tsx`

**Interfaces:**
- Produces: `WorkspaceLayout(): JSX.Element`
- Produces: `WorkspaceSidebar(props: { onNavigate?: () => void; className?: string }): JSX.Element`
- Modifies: `WorkspaceHeader(props: { onOpenDirectory?: () => void })`

- [ ] **Step 1: 写目录与嵌套路由 RED 测试**

在 `WorkspaceLayout.test.tsx` 使用 `QueryClientProvider` 和 `MemoryRouter`：

```typescript
it('shows all directory entries and marks the active route', () => {
  renderLayout('/workspace/projects')

  expect(screen.getByRole('navigation', { name: '工作台目录' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: '工作台' })).toHaveAttribute('href', '/workspace')
  expect(screen.getByRole('link', { name: '项目管理' })).toHaveAttribute(
    'href',
    '/workspace/projects',
  )
  expect(screen.getByRole('link', { name: '系统设置' })).toHaveAttribute(
    'href',
    '/workspace/settings',
  )
  expect(screen.getByRole('link', { name: '回收站' })).toHaveAttribute(
    'href',
    '/workspace/recycle-bin',
  )
  expect(screen.getByRole('link', { name: '项目管理' })).toHaveAttribute(
    'aria-current',
    'page',
  )
})
```

在 `App.test.tsx` 增加匿名访问 `/workspace/settings` 仍回登录页的断言。

- [ ] **Step 2: 运行 RED**

```powershell
npm --prefix apps/calc test -- src/components/workspace/WorkspaceLayout.test.tsx src/App.test.tsx
```

Expected: FAIL，原因为 `WorkspaceLayout`、`WorkspaceSidebar` 不存在，`/workspace/settings` 尚无嵌套路由。

- [ ] **Step 3: 实现目录项与共享外壳**

`WorkspaceSidebar` 的目录配置：

```typescript
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
```

要求：

- `<nav aria-label="工作台目录">`。
- `NavLink` 选中态使用深墨绿背景和白色文字。
- `aria-current="page"` 由 React Router 输出。
- 点击链接调用可选的 `onNavigate`。
- 统一 `className` 可覆盖移动抽屉样式。

`WorkspaceLayout.tsx`：

```typescript
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
```

`WorkspaceHeader` 保持桌面品牌与用户菜单，并预留移动菜单按钮：

```typescript
export function WorkspaceHeader({
  onOpenDirectory,
}: {
  onOpenDirectory?: () => void
}) {
  // 在品牌前渲染 lg:hidden 菜单按钮；没有回调时不渲染。
}
```

`App.tsx` 改为嵌套路由：

```typescript
<Route element={<AuthGate />}>
  <Route path="/workspace" element={<WorkspaceLayout />}>
    <Route index element={<WorkspacePage />} />
    <Route path="projects" element={<ProjectManagementPage />} />
    <Route path="settings" element={<WorkspaceSettingsPage />} />
    <Route path="recycle-bin" element={<RecycleBinPage />} />
  </Route>
  <Route path="/projects/:projectId/calc" element={<CalcWorkspacePage />} />
</Route>
```

Task 1 先创建三个目标页面的最小占位实现，并让 `WorkspacePage` 只返回内容主体、不再自带 `WorkspaceHeader`，使新路由可编译且不会出现双页头；Task 2 再补完整页面内容。

- [ ] **Step 4: 运行 GREEN**

```powershell
npm --prefix apps/calc test -- src/components/workspace/WorkspaceLayout.test.tsx src/App.test.tsx
```

Expected: PASS。

- [ ] **Step 5: 提交**

```powershell
git add -- apps/calc/src/components/workspace/WorkspaceSidebar.tsx apps/calc/src/components/workspace/WorkspaceLayout.tsx apps/calc/src/components/workspace/WorkspaceLayout.test.tsx apps/calc/src/components/WorkspaceHeader.tsx apps/calc/src/App.tsx apps/calc/src/App.test.tsx
git commit -m "feat(calc): add workspace directory shell"
```

---

### Task 2: 工作台总览、项目管理、设置与回收站

**Files:**
- Create: `apps/calc/src/components/workspace/ProjectWorkspacePanel.tsx`
- Modify: `apps/calc/src/pages/WorkspacePage.tsx`
- Create: `apps/calc/src/pages/ProjectManagementPage.tsx`
- Create: `apps/calc/src/pages/ProjectManagementPage.test.tsx`
- Create: `apps/calc/src/pages/WorkspaceSettingsPage.tsx`
- Create: `apps/calc/src/pages/RecycleBinPage.tsx`
- Modify: `apps/calc/src/pages/WorkspacePage.test.tsx`
- Create: `apps/calc/src/pages/WorkspaceSettingsPage.test.tsx`
- Create: `apps/calc/src/pages/RecycleBinPage.test.tsx`

**Interfaces:**
- Consumes: `ProjectRecord`、`useProjects`、`ProjectFormDialog`、`ProjectTable`
- Produces: `ProjectWorkspacePanel(props: { variant: 'overview' | 'management' })`
- Produces: `WorkspacePage(): JSX.Element`
- Produces: `ProjectManagementPage(): JSX.Element`
- Produces: `WorkspaceSettingsPage(): JSX.Element`
- Produces: `RecycleBinPage(): JSX.Element`

- [ ] **Step 1: 写页面 RED 测试**

工作台总览测试保留并断言：

```typescript
expect(screen.getByText('最近项目')).toBeInTheDocument()
expect(screen.getByRole('link', { name: '查看全部项目' })).toHaveAttribute(
  'href',
  '/workspace/projects',
)
```

新增项目管理测试：

```typescript
it('shows the full project management page', async () => {
  renderProjectManagement()
  expect(screen.getByRole('heading', { name: '项目管理' })).toBeInTheDocument()
  expect(await screen.findByText('滨江研发楼改造')).toBeInTheDocument()
  expect(screen.getByLabelText('搜索项目')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: '新建项目' })).toBeInTheDocument()
})
```

测试辅助函数与现有工作台测试一致，使用 `QueryClientProvider`、`MemoryRouter` 和 mock fetch 返回 `projects`：

```typescript
function renderProjectManagement() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/workspace/projects']}>
        <Routes>
          <Route path="/workspace/projects" element={<ProjectManagementPage />} />
          <Route path="/projects/:projectId/calc" element={<div>项目计算页</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
```

设置页测试：

```typescript
expect(screen.getByText('系统设置')).toBeInTheDocument()
expect(screen.getByText('engineer@example.com')).toBeInTheDocument()
expect(screen.getByText('地区只作为项目属性，不切换当前计算规范。')).toBeInTheDocument()
expect(screen.queryByRole('switch')).not.toBeInTheDocument()
```

回收站测试：

```typescript
expect(screen.getByRole('heading', { name: '回收站' })).toBeInTheDocument()
expect(screen.getByText('回收站尚未启用')).toBeInTheDocument()
expect(screen.getByRole('link', { name: '返回项目管理' })).toHaveAttribute(
  'href',
  '/workspace/projects',
)
```

- [ ] **Step 2: 运行 RED**

```powershell
npm --prefix apps/calc test -- src/pages/WorkspacePage.test.tsx src/pages/WorkspaceSettingsPage.test.tsx src/pages/RecycleBinPage.test.tsx
```

Expected: FAIL，页面尚未实现。

- [ ] **Step 3: 抽取并实现项目面板**

把现有 `WorkspacePage` 中以下逻辑迁入 `ProjectWorkspacePanel`：

- `useProjects`
- 四项指标
- 搜索/状态筛选
- `ProjectFormDialog`
- `ProjectTable`
- 删除 mutation
- 查询缓存失效

工作台总览：

```typescript
<ProjectWorkspacePanel variant="overview" />
```

项目管理：

```typescript
<ProjectWorkspacePanel variant="management" />
```

`overview`：

- 保留四项指标。
- 项目表显示最近 8 行。
- 显示“最近项目”和“查看全部项目”。

`management`：

- 不显示四项指标。
- 保留完整搜索、状态筛选、刷新和项目表。
- 显示项目总数。

`WorkspaceSettingsPage` 使用 `useCurrentUser()` 和 `BRAND_NAME`，只读展示当前账号、品牌、数据归属、地区边界、会话说明。

`RecycleBinPage` 使用 Lucide `Trash2` 空态，不允许调用删除 API。

- [ ] **Step 4: 运行 GREEN**

```powershell
npm --prefix apps/calc test -- src/pages/WorkspacePage.test.tsx src/pages/WorkspaceSettingsPage.test.tsx src/pages/RecycleBinPage.test.tsx
```

Expected: PASS，原有项目 CRUD 测试继续通过。

- [ ] **Step 5: 提交**

```powershell
git add -- apps/calc/src/components/workspace/ProjectWorkspacePanel.tsx apps/calc/src/pages/WorkspacePage.tsx apps/calc/src/pages/ProjectManagementPage.tsx apps/calc/src/pages/WorkspaceSettingsPage.tsx apps/calc/src/pages/RecycleBinPage.tsx apps/calc/src/pages/WorkspacePage.test.tsx apps/calc/src/pages/WorkspaceSettingsPage.test.tsx apps/calc/src/pages/RecycleBinPage.test.tsx
git commit -m "feat(calc): add workspace sections"
```

---

### Task 3: 移动抽屉、浏览器验收与 PR 更新

**Files:**
- Create: `apps/calc/src/components/workspace/WorkspaceMobileDirectory.tsx`
- Create: `apps/calc/src/components/workspace/WorkspaceMobileDirectory.test.tsx`
- Modify: `apps/calc/src/components/workspace/WorkspaceLayout.tsx`
- Modify: `apps/calc/src/components/WorkspaceHeader.tsx`
- Modify: `apps/calc/scripts/smoke.mjs`
- Create: `docs/qa/2026-10-28-workspace-left-navigation.md`

**Interfaces:**
- Consumes: `WorkspaceSidebar`
- Produces: `WorkspaceMobileDirectory(props: { open: boolean; onOpenChange(open: boolean): void }): JSX.Element`

- [ ] **Step 1: 写移动抽屉 RED 测试**

```typescript
it('opens the directory and closes after navigation', async () => {
  const user = userEvent.setup()
  renderLayout('/workspace')

  await user.click(screen.getByRole('button', { name: '打开工作台目录' }))
  expect(screen.getByRole('dialog', { name: '工作台目录' })).toBeInTheDocument()

  await user.click(screen.getByRole('link', { name: '系统设置' }))
  await waitFor(() =>
    expect(screen.queryByRole('dialog', { name: '工作台目录' })).not.toBeInTheDocument(),
  )
  expect(screen.getByRole('heading', { name: '系统设置' })).toBeInTheDocument()
})
```

- [ ] **Step 2: 运行 RED**

```powershell
npm --prefix apps/calc test -- src/components/workspace/WorkspaceMobileDirectory.test.tsx
```

Expected: FAIL，移动抽屉不存在。

- [ ] **Step 3: 实现移动抽屉**

使用现有 shadcn `Dialog`，抽屉固定在左侧：

```typescript
<Dialog open={open} onOpenChange={onOpenChange}>
  <DialogContent className="left-0 top-0 h-full w-[280px] max-w-[86vw] translate-x-0 translate-y-0 rounded-none border-r p-0">
    <DialogHeader className="sr-only">
      <DialogTitle>工作台目录</DialogTitle>
      <DialogDescription>工作台主要导航</DialogDescription>
    </DialogHeader>
    <WorkspaceSidebar onNavigate={() => onOpenChange(false)} />
  </DialogContent>
</Dialog>
```

`WorkspaceLayout`：

```typescript
const [navigationOpen, setNavigationOpen] = useState(false)

<WorkspaceHeader onOpenDirectory={() => setNavigationOpen(true)} />
<WorkspaceMobileDirectory
  open={navigationOpen}
  onOpenChange={setNavigationOpen}
/>
```

路由变化时关闭：

```typescript
const location = useLocation()
useEffect(() => {
  setNavigationOpen(false)
}, [location.pathname])
```

- [ ] **Step 4: 扩展 smoke**

开发登录后检查：

```javascript
await page.getByRole('link', { name: '项目管理' }).click()
await page.waitForURL((url) => url.pathname === '/workspace/projects')
await page.getByRole('heading', { name: '项目管理' }).waitFor()

await page.getByRole('link', { name: '系统设置' }).click()
await page.waitForURL((url) => url.pathname === '/workspace/settings')
await page.getByRole('heading', { name: '系统设置' }).waitFor()

await page.getByRole('link', { name: '回收站' }).click()
await page.waitForURL((url) => url.pathname === '/workspace/recycle-bin')
await page.getByText('回收站尚未启用').waitFor()

await page.getByRole('link', { name: '工作台' }).click()
await page.waitForURL((url) => url.pathname === '/workspace')
```

390x844：

```javascript
await page.setViewportSize({ width: 390, height: 844 })
await page.goto(`${baseUrl}/workspace`)
await page.getByRole('button', { name: '打开工作台目录' }).click()
await page.getByRole('dialog', { name: '工作台目录' }).waitFor()
await page.getByRole('dialog').getByRole('link', { name: '系统设置' }).click()
await page.waitForURL((url) => url.pathname === '/workspace/settings')
```

检查根页面无横向溢出。

- [ ] **Step 5: 全量验证**

```powershell
npm --prefix apps/calc test
npm --prefix apps/calc run check-types
npm --prefix apps/calc run build
$env:CALC_URL='http://localhost:5179'
$env:CALC_EXPECT_DEV_LOGIN='1'
npm --prefix apps/calc run test:e2e
```

- [ ] **Step 6: 写 QA 文档**

`docs/qa/2026-10-28-workspace-left-navigation.md` 记录：

- 四个路由。
- 桌面目录选中态。
- 移动抽屉打开、关闭、路由后关闭。
- 1440px 与 390px 无横向溢出。
- 原项目 CRUD 和计算页入口未回归。
- 回收站与系统设置为非持久化边界。

- [ ] **Step 7: 提交并推送**

```powershell
git add -- apps/calc/src/components/workspace/WorkspaceMobileDirectory.tsx apps/calc/src/components/workspace/WorkspaceMobileDirectory.test.tsx apps/calc/src/components/workspace/WorkspaceLayout.tsx apps/calc/src/components/WorkspaceHeader.tsx apps/calc/scripts/smoke.mjs docs/qa/2026-10-28-workspace-left-navigation.md
git commit -m "test(calc): verify workspace directory navigation"
$env:HTTP_PROXY='http://127.0.0.1:10808'
$env:HTTPS_PROXY=$env:HTTP_PROXY
git -c http.proxy=http://127.0.0.1:10808 -c https.proxy=http://127.0.0.1:10808 push --no-verify fork feat/auth-project-workspace
```
