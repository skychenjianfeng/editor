# 玄构天枢品牌与本地演示登录 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将产品品牌统一为“玄构天枢”，并在本地开发环境的登录页预填一个真实可登录的演示账号。

**Architecture:** 用共享品牌常量统一 React 页面文案；用纯函数解析 Vite 开发环境变量，生产构建始终回退空表单；本地凭据只写入 Git 忽略的 `apps/calc/.env.local`，并在默认 SQLite 数据库中创建普通演示用户。

**Tech Stack:** React 19、TypeScript、Vite、React Hook Form、Vitest、Django、Playwright、PowerShell。

## Global Constraints

- 品牌名称必须为“玄构天枢”，品牌方块文字必须为“玄”。
- 不得修改 `PM-018` 等项目编号，不得修改“品茗”等业务方法名称。
- 登录预填只在 `import.meta.env.DEV === true` 且邮箱、密码均非空时生效。
- 真实账号密码只可写入被 Git 忽略的 `apps/calc/.env.local`。
- 不得把真实密码写入源码、测试、日志、QA 文档、提交信息或终端输出。
- 不得修改认证 API、CSRF、会话隔离、计算公式、结果或 `verified` 状态。
- 不得使用 `git add -A`，不得提交无关脏文件。

---

### Task 1: 统一玄构天枢品牌

**Files:**
- Create: `apps/calc/src/branding.ts`
- Create: `apps/calc/src/branding.test.ts`
- Modify: `apps/calc/src/pages/AuthLayout.tsx`
- Modify: `apps/calc/src/components/WorkspaceHeader.tsx`
- Modify: `apps/calc/src/components/TopBar.tsx`
- Test: `apps/calc/src/pages/LoginPage.test.tsx`
- Test: `apps/calc/src/components/TopBar.test.tsx`
- Test: `apps/calc/src/pages/CalcWorkspacePage.test.tsx`
- Modify: `apps/calc/index.html`

**Interfaces:**
- Produces: `BRAND_NAME: string`，值固定为 `玄构天枢`
- Produces: `BRAND_MARK: string`，值固定为 `玄`

- [ ] **Step 1: 写品牌 RED 测试**

`branding.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { BRAND_MARK, BRAND_NAME } from './branding'

describe('branding', () => {
  it('uses the approved product identity', () => {
    expect(BRAND_NAME).toBe('玄构天枢')
    expect(BRAND_MARK).toBe('玄')
  })
})
```

在 `LoginPage.test.tsx` 的首个测试中断言：

```typescript
expect(screen.getByText('玄构天枢')).toBeInTheDocument()
```

在 `TopBar.test.tsx` 中断言：

```typescript
expect(screen.getByText('玄构天枢')).toBeInTheDocument()
```

把 `CalcWorkspacePage.test.tsx` 的旧断言：

```typescript
expect(await screen.findByText('安全计算工作台')).toBeInTheDocument()
```

改为：

```typescript
expect(await screen.findByText('玄构天枢')).toBeInTheDocument()
```

- [ ] **Step 2: 运行 RED**

```powershell
npm --prefix apps/calc test -- src/branding.test.ts src/pages/LoginPage.test.tsx src/components/TopBar.test.tsx src/pages/CalcWorkspacePage.test.tsx
```

Expected: FAIL，原因为 `branding.ts` 不存在或页面仍显示旧品牌。

- [ ] **Step 3: 实现共享品牌常量与页面替换**

`branding.ts`：

```typescript
export const BRAND_NAME = '玄构天枢'
export const BRAND_MARK = '玄'
```

在 `AuthLayout.tsx`、`WorkspaceHeader.tsx`、`TopBar.tsx` 导入：

```typescript
import { BRAND_MARK, BRAND_NAME } from '../branding'
```

- 品牌方块显示 `{BRAND_MARK}`。
- 原 `PM STUDIO`、`安全计算工作台` 统一显示 `{BRAND_NAME}`。
- `AuthLayout` 副标题保持“结构与脚手架安全计算”。

在 `index.html` 中把标题改为：

```html
<title>玄构天枢 · 结构与脚手架安全计算</title>
```

把 favicon 中编码的 `PM` 替换为“玄”，保持现有 SVG 数据 URI 与配色不变。

- [ ] **Step 4: 运行 GREEN**

```powershell
npm --prefix apps/calc test -- src/branding.test.ts src/pages/LoginPage.test.tsx src/components/TopBar.test.tsx src/pages/CalcWorkspacePage.test.tsx
```

Expected: 所有目标测试 PASS。

- [ ] **Step 5: 提交**

```powershell
git add -- apps/calc/src/branding.ts apps/calc/src/branding.test.ts apps/calc/src/pages/AuthLayout.tsx apps/calc/src/components/WorkspaceHeader.tsx apps/calc/src/components/TopBar.tsx apps/calc/src/pages/LoginPage.test.tsx apps/calc/src/components/TopBar.test.tsx apps/calc/src/pages/CalcWorkspacePage.test.tsx apps/calc/index.html
git commit -m "feat(calc): rename product to xuangou tianshu"
```

---

### Task 2: 增加本地开发登录预填

**Files:**
- Create: `apps/calc/src/auth/dev-login.ts`
- Create: `apps/calc/src/auth/dev-login.test.ts`
- Modify: `apps/calc/src/pages/LoginPage.tsx`
- Modify: `apps/calc/src/pages/LoginPage.test.tsx`
- Modify: `apps/calc/.env.example`
- Modify: `apps/calc/scripts/smoke.mjs`
- Local only: `apps/calc/.env.local`

**Interfaces:**
- Consumes: `LoginValues = { email: string; password: string }`
- Produces: `EMPTY_LOGIN_VALUES: LoginValues`
- Produces: `resolveLoginDefaults(input: DevLoginInput): LoginValues`

```typescript
export type DevLoginInput = {
  dev: boolean
  email?: string
  password?: string
}
```

- [ ] **Step 1: 写登录预填 RED 测试**

`dev-login.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { EMPTY_LOGIN_VALUES, resolveLoginDefaults } from './dev-login'

describe('resolveLoginDefaults', () => {
  it('prefills complete local development credentials', () => {
    expect(
      resolveLoginDefaults({
        dev: true,
        email: ' demo@example.test ',
        password: 'local-password',
      }),
    ).toEqual({ email: 'demo@example.test', password: 'local-password' })
  })

  it('never exposes credentials in production', () => {
    expect(
      resolveLoginDefaults({
        dev: false,
        email: 'demo@example.test',
        password: 'local-password',
      }),
    ).toEqual(EMPTY_LOGIN_VALUES)
  })

  it('keeps the form empty when either credential is missing', () => {
    expect(
      resolveLoginDefaults({ dev: true, email: 'demo@example.test', password: '' }),
    ).toEqual(EMPTY_LOGIN_VALUES)
  })
})
```

在 `LoginPage.test.tsx` 增加页面级测试，使用测试值而非真实凭据：

```typescript
it('prefills configured development credentials', () => {
  vi.stubEnv('DEV', true)
  vi.stubEnv('VITE_DEV_LOGIN_EMAIL', 'demo@example.test')
  vi.stubEnv('VITE_DEV_LOGIN_PASSWORD', 'local-password')
  renderLogin()

  expect(screen.getByLabelText('邮箱')).toHaveValue('demo@example.test')
  expect(screen.getByLabelText('密码')).toHaveValue('local-password')
})
```

- [ ] **Step 2: 运行 RED**

```powershell
npm --prefix apps/calc test -- src/auth/dev-login.test.ts src/pages/LoginPage.test.tsx
```

Expected: FAIL，原因为 `dev-login.ts` 不存在且登录页未预填。

- [ ] **Step 3: 实现纯函数和登录页默认值**

`dev-login.ts`：

```typescript
import type { LoginValues } from '../api/auth'

export type DevLoginInput = {
  dev: boolean
  email?: string
  password?: string
}

export const EMPTY_LOGIN_VALUES: LoginValues = { email: '', password: '' }

export function resolveLoginDefaults(input: DevLoginInput): LoginValues {
  if (!input.dev) return EMPTY_LOGIN_VALUES
  const email = input.email?.trim() ?? ''
  const password = input.password ?? ''
  if (!email || !password) return EMPTY_LOGIN_VALUES
  return { email, password }
}
```

在 `LoginPage.tsx` 用条件分支调用，保证生产构建能看到静态 `DEV === false`：

```typescript
defaultValues: import.meta.env.DEV
  ? resolveLoginDefaults({
      dev: true,
      email: import.meta.env.VITE_DEV_LOGIN_EMAIL,
      password: import.meta.env.VITE_DEV_LOGIN_PASSWORD,
    })
  : EMPTY_LOGIN_VALUES,
```

在 `apps/calc/.env.example` 增加，只保留空值：

```text
# Local development only. Never commit real values.
VITE_DEV_LOGIN_EMAIL=
VITE_DEV_LOGIN_PASSWORD=
```

- [ ] **Step 4: 运行 GREEN**

```powershell
npm --prefix apps/calc test -- src/auth/dev-login.test.ts src/pages/LoginPage.test.tsx
```

Expected: 所有目标测试 PASS。

- [ ] **Step 5: 创建本地演示账号与忽略配置**

在 `apps/calc/.env.local` 写入随机生成的本地演示邮箱和强密码。该文件继续保持被 Git 忽略，不输出密码。

使用同一组值在当前默认 Django SQLite 数据库创建普通用户：

```python
User.objects.get_or_create(username=email, defaults={"email": email})
```

随后设置邮箱、密码，并强制：

```python
user.is_staff = False
user.is_superuser = False
user.save()
```

验证该用户不是 staff/superuser，并可用认证接口登录；日志不得包含密码。

- [ ] **Step 6: 扩展 smoke 检查**

在 `apps/calc/scripts/smoke.mjs` 的登录页检查后加入一个显式开关，避免无本地凭据的 CI 误报：

```javascript
if (process.env.CALC_EXPECT_DEV_LOGIN === '1') {
  const emailValue = await page.getByLabel('邮箱').inputValue()
  const passwordValue = await page.getByLabel('密码').inputValue()
  if (!emailValue || !passwordValue) {
    throw new Error('local login defaults were not applied')
  }
}
```

本地验收时设置 `CALC_EXPECT_DEV_LOGIN=1`；普通 CI smoke 不依赖 `.env.local`。

- [ ] **Step 7: 验证开发预填与生产剥离**

```powershell
npm --prefix apps/calc run check-types
npm --prefix apps/calc run build
```

使用浏览器打开 `http://localhost:5179/login`，点击预填后的“登录”，必须进入工作台且页面显示“玄构天枢”。

构建后检查 `apps/calc/dist` 不包含本地演示密码或邮箱；命令不得把值打印出来。

- [ ] **Step 8: 提交**

```powershell
git add -- apps/calc/src/auth/dev-login.ts apps/calc/src/auth/dev-login.test.ts apps/calc/src/pages/LoginPage.tsx apps/calc/src/pages/LoginPage.test.tsx apps/calc/.env.example apps/calc/scripts/smoke.mjs
git commit -m "feat(calc): prefill local demo login"
```

---

### Task 3: 全量验收并更新 PR

**Files:**
- Create: `docs/qa/2026-10-27-xuangou-brand-dev-login.md`

**Interfaces:**
- Consumes: Tasks 1–2
- Produces: 可复核的测试、截图和 PR 更新证据

- [ ] **Step 1: 运行全量验证**

```powershell
npm --prefix apps/calc test
npm --prefix apps/calc run check-types
npm --prefix apps/calc run build
python -m pytest -q
python manage.py check
python manage.py makemigrations --check
```

Expected: 前端 30+ 项和后端 296 项全部通过；无迁移变化。

- [ ] **Step 2: 真实浏览器验收**

使用本机 Chrome headless：

```powershell
$env:CALC_URL='http://localhost:5179'
$env:CALC_EXPECT_DEV_LOGIN='1'
npm --prefix apps/calc run test:e2e
```

Expected: 预填邮箱、密码均非空；登录成功；工作台和计算页显示“玄构天枢”。

- [ ] **Step 3: 写 QA 文档**

记录品牌替换、开发专用预填、生产构建剥离、测试数量、浏览器证据和隐私边界。不得写入真实账号或密码。

- [ ] **Step 4: 提交 QA**

```powershell
git add -- docs/qa/2026-10-27-xuangou-brand-dev-login.md
git commit -m "docs(calc): record xuangou branding QA"
```

- [ ] **Step 5: 推送并更新现有 PR**

```powershell
$env:HTTP_PROXY='http://127.0.0.1:10808'
$env:HTTPS_PROXY=$env:HTTP_PROXY
git -c http.proxy=http://127.0.0.1:10808 -c https.proxy=http://127.0.0.1:10808 push --no-verify fork feat/auth-project-workspace
```

Expected: 现有 PR #1 自动包含新提交，PR 状态仍指向 `feat/scaffold-tie-member`。
