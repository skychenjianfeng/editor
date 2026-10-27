# 工作台左侧目录：移动抽屉与浏览器验收

## 验收信息

- 日期：2026-10-28
- 分支：`feat/auth-project-workspace`
- 前端：`http://localhost:5179`
- 后端：`http://127.0.0.1:8001`
- 浏览器：本机 Google Chrome，Playwright，headless
- 数据：使用当前默认数据库与 Git 忽略的 `apps/calc/.env.local`；验收创建的唯一项目在脚本结束时删除
- 范围：工作台目录路由、桌面选中态、移动抽屉、横向溢出、项目 CRUD 与计算页入口；未改后端或计算逻辑

## 目录与路由

开发登录 smoke 依次进入并验证以下四个路由：

| 目录项 | URL | 页面证据 |
| --- | --- | --- |
| 工作台 | `/workspace` | 标题“项目工作台” |
| 项目管理 | `/workspace/projects` | 标题“项目管理” |
| 系统设置 | `/workspace/settings` | 标题“系统设置” |
| 回收站 | `/workspace/recycle-bin` | 标题“回收站”、“回收站尚未启用”空态 |

四条路由均核对 URL；桌面 1440x900 下每进入一条路由，对应目录链接的
`aria-current` 为 `page`。现有 `WorkspaceLayout.test.tsx` 的两个测试继续覆盖目录项、
当前路由标记，以及移动抽屉打开后点击“系统设置”切页并关闭。

## 响应式检查

- 1440x900：登录后的 `/workspace` 根页无横向溢出，桌面目录可见。
- 390x844：显示“打开工作台目录”按钮；点击后出现名称为“工作台目录”的 dialog。
- 移动抽屉左边缘与视口对齐，宽度不超过 `86vw`。
- 在抽屉内点击“系统设置”后进入 `/workspace/settings`，标题出现，dialog 从 DOM 移除。
- 390x844 下抽屉关闭、抽屉打开及设置页均满足
  `max(html.scrollWidth, body.scrollWidth) <= window.innerWidth`，无根页面横向溢出。
- 开发登录目标流程的浏览器 `console error` 为 0，`pageerror` 为 0。
- 普通无开关 smoke 保持原行为；匿名访问 `/workspace` 的预期 401 仍是正常校验结果，
  不当作目标页面应用错误计数。

## CRUD 与计算入口回归

浏览器 smoke 通过真实登录会话完成：

1. `POST /api/v1/projects` 创建临时项目。
2. `GET /api/v1/projects/:id` 读取项目。
3. `PATCH /api/v1/projects/:id` 将地区更新为“上海”、状态更新为“计算中”，并核对响应。
4. 打开 `/projects/:id/calc`，核对 HTTP 200、最终 URL 和品牌标识，确认计算页入口未回归。
5. 脚本结束时通过 `DELETE /api/v1/projects/:id` 删除临时项目并核对 204。

本次未执行新的计算，也未改变公式、方案或结果契约。

## 自动化结果

- `npm --prefix apps/calc test`：20 个测试文件、53 个测试全部通过。
- `npm --prefix apps/calc run check-types`：通过，无 TypeScript 错误。
- `npm --prefix apps/calc run build`：通过；主 JS chunk 913.54 kB（gzip 288.59 kB），
  Vite 仍报告大于 500 kB 的既存 chunk 体积警告。
- 开发登录 smoke：
  `smoke ok: dev-login=prefilled routes=4 active=desktop mobile-drawer=open+close viewport=1440+390 overflow=none console-errors=0 qa-project=crud+calc+deleted`
- 普通 smoke：
  `smoke ok: login=200 root=present workspace-fallback=200 redirect=/login?next=/workspace anonymous-me=401`

## 功能边界

- “系统设置”当前是只读信息页，不持久化新的设置项。
- “回收站”当前只有明确空态；尚不支持恢复已删除项目，删除项目仍为永久移除。
- 本次验收不覆盖团队共享、角色权限、生产 TLS/HSTS 或邮件流程。
