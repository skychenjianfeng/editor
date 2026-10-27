# 玄构天枢品牌与本地开发登录 QA

日期：2026-10-27

范围：Task 1–2 的品牌替换与开发环境登录预填，基于提交 `aefed981`、`94372f4`。本记录不包含账号、密码、Cookie 或 Token。

## 结论

全部必需检查通过。产品界面统一显示“玄构天枢”；本地开发登录页预填非空；真实系统 Chrome 中点击登录后进入 `/workspace`；项目工作台和项目计算页均显示新品牌；生产构建未包含本地演示邮箱或密码。上述登录、品牌和临时项目清理流程已固化到 `apps/calc/scripts/smoke.mjs`，可直接复跑。

## 品牌替换

- 新增共享品牌常量：品牌名为“玄构天枢”，品牌标记为“玄”。
- 登录页、注册页、项目工作台页头、计算工作台顶栏和页面标题统一使用新品牌。
- favicon 使用“玄”替换旧品牌标记，同时保留原 SVG 数据 URI 与配色。
- 路由、认证、计算业务、项目编号及“品茗”业务名称未被本次品牌替换改动。

## 开发登录预填

- 登录页仅在 Vite 开发模式、且邮箱和密码两项本地配置都非空时预填。
- 生产分支使用空默认值，不读取本地演示配置。
- 本地演示账号仅存在于 Git 忽略的 `apps/calc/.env.local` 和当前默认本地 SQLite 中。
- `CALC_EXPECT_DEV_LOGIN=1` 是 smoke 的显式验收开关；未设置时保持匿名 smoke 行为。
- 开启后，smoke 先确认预填非空，再点击登录，等待 `/workspace` 并断言品牌；随后通过真实计算 API 创建唯一 QA 项目，进入其计算页断言品牌，并在 `finally` 中删除该项目。
- smoke 不打印预填值、密码、Cookie 或 Token。

## 全量验证

```powershell
npm --prefix apps/calc test
npm --prefix apps/calc run check-types
npm --prefix apps/calc run build
```

| 检查 | 结果 |
|---|---|
| `npm --prefix apps/calc test` | 通过；16 个测试文件、41 项测试 |
| `npm --prefix apps/calc run check-types` | 通过 |
| `npm --prefix apps/calc run build` | 通过；2745 个模块完成转换 |
| `python -m pytest -q` | 通过；296 项测试 |
| `python manage.py check` | 通过；0 个问题 |
| `python manage.py makemigrations --check` | 通过；`No changes detected` |

生产构建仅有单个 JS chunk 超过 500 kB 的非阻断性 Vite 提示，不影响本任务功能或凭据剥离结论。

## 浏览器验收

普通无开关 CI 验收：

```powershell
$env:CALC_URL='http://localhost:5179'
Remove-Item Env:CALC_EXPECT_DEV_LOGIN -ErrorAction SilentlyContinue
npm --prefix apps/calc run test:e2e
```

结果：通过，保持登录页返回 200、匿名访问工作台回退到登录页，以及匿名认证接口返回 401。

开发登录与品牌复跑：

```powershell
$env:CALC_URL='http://localhost:5179'
$env:CALC_EXPECT_DEV_LOGIN='1'
npm --prefix apps/calc run test:e2e
```

结果：通过。smoke 使用真实系统 Chrome（`channel: 'chrome'`, `headless: true`）完成：

- 预填邮箱和密码均非空，但未读取或记录其值。
- 点击“登录”后 URL 进入 `/workspace`。
- 项目工作台可见“玄构天枢”。
- 通过 `POST /api/v1/projects` 创建唯一 QA 项目，URL 进入 `/projects/<项目 ID>/calc`。
- 项目计算页可见“玄构天枢”。
- `finally` 通过 `DELETE /api/v1/projects/<项目 ID>` 删除 QA 项目，退出后不残留临时数据。

本地截图证据位于 Task 3 工作目录的 `.superpowers/sdd/2026-10-27-xuangou-brand-dev-login/`，按任务提交范围不纳入 Git：

| 截图 | 字节数 | SHA-256 |
|---|---:|---|
| `task-3-workspace.png` | 46187 | `647645CD2ADE4BE4FEB61C290B1051C4E2F9B501F291F5845966DDD74D645E99` |
| `task-3-calc.png` | 106403 | `344E614FA97ABBF08641B201BC97349890A7F5DC178CEA69FE69F547BEA30389` |

## 生产凭据剥离

构建完成后，将 `apps/calc/.env.local` 中键名含 `EMAIL` 或 `PASSWORD` 的本地值逐项与 `apps/calc/dist` 全部产物做精确文本匹配：

- 检查键数：2。
- `dist_email_found`：`false`。
- `dist_password_found`：`false`。
- `dist_brand_present`：`true`。
- `env_local_git_ignored`：`true`。

扫描过程只输出布尔结果，不输出配置值。

## 隐私边界

- 仓库文档、测试日志、截图记录和报告均不包含邮箱、密码、Cookie、Token 或环境文件内容。
- 本地演示配置继续保存在 Git 忽略的 `apps/calc/.env.local`，不随提交或生产构建分发。
- 本次提交只包含本 QA 文档，不包含应用源码、构建产物、本地配置或截图。
