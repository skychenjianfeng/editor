# 登录、项目工作台与计算页真实浏览器验收

## 验收信息

- 日期：2026-10-27
- 分支：`feat/auth-project-workspace`
- 验收基线：`48ab3c4`（`feat(calc): harden authentication boundary`）
- 浏览器修复提交：`9fb89a6`（`fix(calc): resolve auth workspace browser issues`）
- 浏览器：本机 Google Chrome，Playwright 同步 API，`headless=True`
- 运行时：Windows PowerShell、Python 3.13.2、Node.js v24.14.0、npm 11.9.0、Vite v8.3.5
- 前端：`http://localhost:5179`
- 后端：`http://127.0.0.1:8001`
- 数据库：唯一临时 SQLite `artifacts/auth-workspace-qa/qa-20261027-214233.sqlite3`；迁移后启动服务，验收结束后删除

## 浏览器闭环

使用两个仅在脚本内存中生成账号完成以下步骤：

1. 匿名访问 `/workspace`，跳转到 `/login?next=%2Fworkspace`。
2. 在 390x844 注册账号 A，开放注册成功后进入空工作台。
3. 新建“上海 / 筹备中”项目并使用“创建并进入”，进入
   `/projects/<uuid>/calc`；项目上下文条显示项目名、上海和筹备中。
4. 等待扣件式脚手架计算完成，打开“方案”并保存方案；返回工作台后方案数为 1，
   最近计算不再显示“尚未计算”。
5. 刷新 `/workspace`，会话和项目均保留。
6. 将项目状态编辑为“计算中”，行内状态更新；搜索命中、状态筛选、无结果空态和
   “清除筛选”均通过。
7. 账号 A 退出，注册账号 B；B 的工作台为空且看不到 A 的项目。
8. B 退出后再次用 A 登录 `/workspace`，A 的项目仍存在。
9. 检查 Cookie：`sessionid.httpOnly=true`、`csrftoken.httpOnly=false`，
   二者 `sameSite=Lax`。仅记录属性，不记录 Cookie 值。
10. 通过“更多操作 → 删除项目 → 确认删除”删除 A 的项目，二次确认后项目消失。

最终验收项目 ID：`b9474e07-a655-4209-b042-ec42bf8a7faa`。

## 响应式与可操作性

首次真实浏览器运行在 390x844 计算页测得 `documentElement.scrollWidth=635`、
`body.scrollWidth=635`，根因是计算页顶栏桌面操作组未收缩。修复后顶栏自身可横向滚动，
桌面密度和全部操作保留，页面根节点不再溢出。对应 `TopBar` 回归测试先 RED、修复后 GREEN。

| 页面与视口 | HTML scrollWidth | Body scrollWidth | Viewport | 横向溢出 |
| --- | ---: | ---: | ---: | --- |
| 注册页 390x844 | 390 | 390 | 390 | 否 |
| 空工作台 1440x900 | 1440 | 1440 | 1440 | 否 |
| 含项目工作台 1440x900 | 1440 | 1440 | 1440 | 否 |
| 计算页 1440x900 | 1440 | 1440 | 1440 | 否 |
| 工作台 390x844 | 390 | 390 | 390 | 否 |
| 计算页 390x844 | 390 | 390 | 390 | 否 |

390px 注册表单可提交，工作台“新建项目”对话框可打开并用 Escape 关闭，计算页
“方案”对话框可打开并用 Escape 关闭；桌面与移动端均保留全部功能。

## 运行错误与网络

- 应用 console error：0
- `pageerror`：0
- 失败 API 请求：0
- API 4xx（除预期匿名校验）：0
- API 5xx：0
- 明确允许的匿名 `GET /api/v1/auth/me` 401：2 次；分别来自两条显式未登录访问
  `/workspace` 的流程。浏览器为这两次预期响应生成的 401 resource 日志已单独归为
  `expected_console_401`，不计入应用 console error。
- 修复 favicon 404 后，目标页面无其他资源 console error。

浏览器结果文件：
`E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\auth_workspace_e2e_result.json`

## 截图证据

- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\login-1440.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\register-390.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\workspace-empty-1440.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\project-created-1440.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\calc-project-1440.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\scheme-saved-1440.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\workspace-updated-1440.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\workspace-390.png`
- `E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\shots\calc-390.png`

最终服务的标准输出、错误输出和迁移日志保存在
`E:\Civil-Engineering\PmStudio\artifacts\auth-workspace-qa\`，文件名带
`20261027-214233` 时间戳。

## 自动化回归

前端：

- `npm --prefix apps/calc test`：13 个测试文件通过，30 个测试通过。
- `npm --prefix apps/calc run check-types`：通过，0 个 TypeScript 错误。
- `npm --prefix apps/calc run build`：通过；主 JS chunk 871.79 kB
  （gzip 275.73 kB），Vite 保留大于 500 kB 的 chunk 体积警告。

后端（`services/calc-api`）：

- `python -m pytest -q`：296 个测试通过，7 条来自 `ezdxf/pyparsing` 的上游弃用警告。
- `python manage.py check`：通过，0 issues。
- `python manage.py makemigrations --check`：通过，`No changes detected`。

## 验收收口

使用唯一临时 SQLite
`artifacts/auth-workspace-qa/qa-smoke-20261027-214821-582.sqlite3`，迁移后启动
Django `127.0.0.1:8001` 和 Vite `127.0.0.1:5179`。ready 检测实际轮询了
匿名 `GET /api/v1/auth/me`（401）和 `GET /login`（200，含 `id="root"`），
未只检查端口。当前次命令与结果：

```powershell
$env:CALC_URL = 'http://127.0.0.1:5179'
npm --prefix apps/calc run test:e2e
```

```text
smoke ok: login=200 root=present workspace-fallback=200 redirect=/login?next=/workspace anonymous-me=401
```

同一临时服务上依次得到：

- `npm --prefix apps/calc test`：13 个测试文件、30 个测试通过。
- `npm --prefix apps/calc run check-types`：通过。
- `npm --prefix apps/calc run build`：通过；主 JS chunk 871.79 kB
  （gzip 275.73 kB），仍只有 Vite 的大 chunk 警告。

可重复的真实浏览器脚本为
`E:\Civil-Engineering\PmStudio\scripts\verify-calc-auth-workspace.py`。脚本接受
`--base-url`（默认 `http://127.0.0.1:5179`），不启动服务，只使用内存随机账号。
本次在相同临时服务上执行并通过，生成唯一结果
`artifacts/auth-workspace-qa/auth_workspace_e2e_1793108972-dd22f940_result.json`
和 `artifacts/auth-workspace-qa/shots/verify-1793108972-dd22f940/` 下的截图。
本次执行仍是原有 30 项前端与 296 项后端边界的补充浏览器回归，不另增或重复统计测试数。

## 清理与边界

- 只终止本次启动的 Django/Vite 进程树。
- 本次唯一临时 SQLite 已删除；未读写 `services/calc-api/db.sqlite3`。
- 截图、E2E 结果和日志保留；未保留账号、密码、Cookie 或 Token。
- 登录/注册当前没有分布式限流。
- TLS/HSTS 由部署代理负责，本次本地 HTTP 验收不验证生产代理配置。
- 地区目前只是项目属性，不切换计算规范；不改变现有公式、结果或 `verified` 状态。
- 本次未实现邮件验证、找回密码、团队共享和角色权限。
