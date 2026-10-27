# 工作台左侧目录：移动抽屉与浏览器验收

## 验收信息

- 日期：2026-10-28
- 分支：`feat/auth-project-workspace`
- 前端：`http://localhost:5179`
- 后端：`http://127.0.0.1:8001`
- 浏览器：本机 Google Chrome，Playwright，headless
- 数据：使用当前默认数据库与 Git 忽略的 `apps/calc/.env.local`；验收创建的唯一项目在脚本结束时删除
- 范围：工作台目录路由、桌面选中态、移动抽屉、横向溢出、项目管理 UI CRUD
  与计算页入口；未改后端或计算逻辑
- 项目查询固定为最近最多 200 个项目；界面指标与列表摘要均不声称权威全量总数

## 目录与路由

开发登录 smoke 依次进入并验证以下四个路由：

| 目录项 | URL | 页面证据 |
| --- | --- | --- |
| 工作台 | `/workspace` | 标题“项目工作台” |
| 项目管理 | `/workspace/projects` | 标题“项目管理” |
| 系统设置 | `/workspace/settings` | 标题“系统设置” |
| 回收站 | `/workspace/recycle-bin` | 标题“回收站”、“回收站尚未启用”空态 |

四条路由均核对 URL；桌面 1440x900 下每进入一条路由，对应目录链接的
`aria-current` 为 `page`，计算样式背景为 `rgb(18, 59, 50)`、文字为白色。
导航测试断言链接完整有序数组恰为工作台、项目管理、系统设置、回收站及其 href。

## 响应式检查

- 1440x900：登录后的 `/workspace` 根页无横向溢出，桌面目录可见。
- 1440x900：桌面目录 `navigation` 的 Playwright `boundingBox().width` 为 232px，
  自动化允许 1px 的浮点误差。
- 1440x900：桌面目录顶部显示可见“工作台目录”标识，导航本身仍保留同名
  `aria-label`，两者不构成重复 heading。
- 1024x900：项目管理操作列位于项目表格可视区内，行内“进入计算”和“更多操作”
  两个按钮均通过边界断言。
- 390x844：显示“打开工作台目录”按钮；点击后出现名称为“工作台目录”的 dialog。
- 移动按钮使用 `aria-expanded` 反映抽屉状态，`aria-controls` 指向抽屉内容稳定
  `id`；关闭后恢复为 `false`。
- 全部 Dialog 的 overlay 与 content 使用 Tailwind v4 important 类
  `motion-reduce:animate-none!`；生产构建在
  `@media (prefers-reduced-motion:reduce)` 中输出
  `.motion-reduce\:animate-none\!{animation:none!important}`，明确覆盖
  `data-open` / `data-closed` 状态动画。
- 移动抽屉左边缘与视口对齐，宽度不超过 `86vw`。
- 移动抽屉验证三条独立关闭路径：点击 dialog 内可访问名称为 `Close` 的关闭控件；
  按 `Escape`；以及在抽屉内导航到“系统设置”。每条路径均断言 dialog detached，
  导航路径同时断言进入 `/workspace/settings` 且页面标题出现。
- 390x844 下抽屉关闭、抽屉打开及设置页均满足
  `max(html.scrollWidth, body.scrollWidth) <= window.innerWidth`，无根页面横向溢出。
- 开发登录目标流程的浏览器 `console error` 为 0，`pageerror` 为 0。
- 普通无开关 smoke 保持原行为；匿名访问 `/workspace` 的预期 401 仍是正常校验结果，
  不当作目标页面应用错误计数。

## CRUD 与计算入口回归

浏览器 smoke 在 1024x900 的 `/workspace/projects` 通过真实项目管理 UI 完成：

1. 点击“新建项目”，在“新建项目”dialog 填写唯一 QA 项目名称，选择“全国”和
   “筹备中”，点击“仅创建”；等待创建响应、dialog 关闭，核对项目表新行的状态，
   并确认两个操作按钮位于表格可视区内。1024px 紧凑布局按设计隐藏地区等扩展列。
2. 在“搜索项目”输入唯一名称，等待管理页按该条件返回，并核对项目表可见结果。
3. 通过该项目行的“更多操作”菜单打开“编辑项目”dialog，改为“上海”和“计算中”；
   保存后核对 PATCH 响应中的地区与状态，确认 dialog 关闭，并在项目表行中看到
   更新后的状态。
4. 点击该项目行内“进入计算”，核对最终地址为 `/projects/:id/calc` 和品牌标识，
   确认计算页入口未回归；随后返回项目管理页。
5. 在 1024px 通过同一项目行的“更多操作”菜单选择“删除项目”，在确认 alert dialog
   中点击“确认删除”，核对删除响应及该项目行从列表中移除。

临时项目清理位于 smoke 的 `finally`：正常路径以 UI 删除后不再重复删除；若中途失败，
脚本使用响应中记录的唯一项目 ID 清理，若尚未拿到 ID，则按唯一项目名称精确查询后清理。
清理不是 UI CRUD 验收的替代。

本次未执行新的计算，也未改变公式、方案或结果契约。

## 自动化结果

- `npm --prefix apps/calc test`：20 个测试文件、53 个测试全部通过。
- `npm --prefix apps/calc run check-types`：通过，无 TypeScript 错误。
- `npm --prefix apps/calc run build`：通过；主 JS chunk 913.95 kB（gzip 288.70 kB），
  Vite 仍报告大于 500 kB 的既存 chunk 体积警告。
- 开发登录 smoke：
  `smoke ok: dev-login=prefilled routes=4 active=desktop+computed-colors desktop-nav=232px mobile-expanded=aria desktop-directory=true mobile-close=button+escape+navigation viewport=1440+1024+390 overflow=none console-errors=0 qa-project=ui-crud+1024-actions-visible+calc+1024-ui-deleted cleanup=finally`
- 普通 smoke：
  `smoke ok: login=200 root=present workspace-fallback=200 redirect=/login?next=/workspace anonymous-me=401`
- 默认 SQLite 只读复核：`calc_runs_scaffoldproject` 中名称匹配
  `QA 玄构天枢%` 的项目数为 0。

## 功能边界

- “系统设置”当前是只读信息页，不持久化新的设置项。
- 系统设置的会话说明明确：登录状态由 Session Cookie 维护，写请求受 CSRF 保护，
  退出后需重新登录。
- “回收站”当前只有明确空态；尚不支持恢复已删除项目，删除项目仍为永久移除。
- 本次验收不覆盖团队共享、角色权限、生产 TLS/HSTS 或邮件流程。
