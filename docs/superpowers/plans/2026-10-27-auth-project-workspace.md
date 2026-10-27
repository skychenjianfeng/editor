# 登录、项目工作台与计算页入口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `apps/calc` 增加开放注册、会话登录、用户级项目工作台，并在新建项目时绑定地区，随后进入现有计算工作区。

**Architecture:** Django 内置用户、Session Cookie 和 CSRF 负责认证；`CalcRun` 与 `ScaffoldProject` 增加 owner，所有现有 API 默认要求登录并按 owner 隔离。React SPA 增加 BrowserRouter：`/login`、`/register`、`/workspace`、`/projects/:projectId/calc`。工作台负责项目 CRUD，现有计算器改为项目上下文内的页面。

**Tech Stack:** Django、Django REST Framework、pytest-django、React 19、TypeScript、Vite、React Router、TanStack Query、TanStack Table、React Hook Form、Zod、shadcn/ui Nova、Lucide、Motion、Tailwind CSS v4。

## Global Constraints

- 开放邮箱/密码注册，不要求邮件验证。
- 账号、项目、方案和计算记录必须按用户隔离。
- 地区只在项目创建/编辑时保存，当前计算规则不随地区切换。
- 项目状态固定为 `preparing / calculating / completed`，默认 `preparing`。
- 项目地区固定为：全国、上海、江苏、浙江、北京、山东、广东、湖北、福建、重庆。
- Session Cookie 使用 `HttpOnly`、`SameSite=Lax`；CSRF Cookie 可由前端读取并发送 `X-CSRFToken`。
- 开发和生产均通过同域 `/api` 代理，避免跨域凭证 Cookie。
- 所有现有计算端点和导出端点都要求登录。
- 不修改脚手架模块的公式、默认参数、结果数量或 `verified` 状态。
- 不使用 Zustand 复制服务端项目、用户或方案状态。
- 所有新增前端图标使用 Lucide；动画使用 Motion；表单使用 React Hook Form + Zod。
- 先写失败测试，再写生产代码。
- 不得使用 `git add -A`，不得提交无关的既有未提交改动。

---

### Task 1: Django 注册、登录、退出与 CSRF

**Files:**
- Create: `services/calc-api/api/auth_views.py`
- Create: `services/calc-api/tests/test_auth_api.py`
- Modify: `services/calc-api/calcapi/settings.py`
- Modify: `services/calc-api/calcapi/middleware.py`
- Modify: `services/calc-api/api/urls.py`

**Interfaces:**
- Consumes: Django `User`、`login`、`logout`、`authenticate`、`validate_password`。
- Produces:
  - `GET /api/v1/auth/csrf`
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
  - Current user JSON：`{"user_id": number, "email": string, "display_name": string}`

- [ ] **Step 1: 写认证 RED 测试**

```python
# services/calc-api/tests/test_auth_api.py
import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def browser_client():
    return Client(enforce_csrf_checks=True)


def csrf_post(client, path, payload):
    client.get("/api/v1/auth/csrf")
    token = client.cookies["csrftoken"].value
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


@pytest.mark.django_db
def test_register_me_logout_and_login(browser_client):
    registered = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {
            "email": "  User@Example.com ",
            "password": "Strong-pass-2026",
            "password_confirm": "Strong-pass-2026",
        },
    )
    assert registered.status_code == 201
    assert registered.json()["email"] == "user@example.com"

    me = browser_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"

    logged_out = csrf_post(browser_client, "/api/v1/auth/logout", {})
    assert logged_out.status_code == 204
    assert browser_client.get("/api/v1/auth/me").status_code == 401

    logged_in = csrf_post(
        browser_client,
        "/api/v1/auth/login",
        {"email": "user@example.com", "password": "Strong-pass-2026"},
    )
    assert logged_in.status_code == 200


@pytest.mark.django_db
def test_register_rejects_duplicate_email_and_mismatched_password(browser_client):
    payload = {
        "email": "duplicate@example.com",
        "password": "Strong-pass-2026",
        "password_confirm": "Strong-pass-2026",
    }
    assert csrf_post(browser_client, "/api/v1/auth/register", payload).status_code == 201

    mismatch = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {
            "email": "mismatch@example.com",
            "password": "Strong-pass-2026",
            "password_confirm": "different",
        },
    )
    assert mismatch.status_code == 400
    assert "password" in mismatch.json()["errors"]

    duplicate = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {**payload, "email": "DUPLICATE@example.com"},
    )
    assert duplicate.status_code == 400
    assert "email" in duplicate.json()["errors"]


@pytest.mark.django_db
def test_login_does_not_reveal_unknown_email(browser_client):
    get_user_model().objects.create_user(
        username="known@example.com",
        email="known@example.com",
        password="Strong-pass-2026",
    )
    wrong_password = csrf_post(
        browser_client,
        "/api/v1/auth/login",
        {"email": "known@example.com", "password": "wrong"},
    )
    unknown_email = csrf_post(
        browser_client,
        "/api/v1/auth/login",
        {"email": "unknown@example.com", "password": "wrong"},
    )
    assert wrong_password.status_code == unknown_email.status_code == 400
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


def test_register_without_csrf_is_rejected(browser_client):
    response = browser_client.post(
        "/api/v1/auth/register",
        data=json.dumps(
            {
                "email": "csrf@example.com",
                "password": "Strong-pass-2026",
                "password_confirm": "Strong-pass-2026",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 403
```

- [ ] **Step 2: 运行测试确认 RED**

```powershell
cd services/calc-api
python -m pytest tests/test_auth_api.py -q
```

Expected: FAIL because auth routes and session middleware do not exist.

- [ ] **Step 3: 配置 Django 认证**

在 `settings.py`：

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "calc_runs",
]

MIDDLEWARE = [
    "calcapi.middleware.DevCorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [
    value for value in os.environ.get("CALC_CSRF_TRUSTED_ORIGINS", "").split(",") if value
]
```

删除 `"UNAUTHENTICATED_USER": None`，让未登录用户为 Django `AnonymousUser`。

- [ ] **Step 4: 实现认证接口**

`auth_views.py` 使用 `@method_decorator(csrf_protect, name="dispatch")` 保护注册、登录和退出；`/auth/csrf` 使用 `@method_decorator(ensure_csrf_cookie, name="get")`。

注册流程：

```python
email = str(data.get("email") or "").strip().lower()
password = str(data.get("password") or "")
confirm = str(data.get("password_confirm") or "")
if not email or "@" not in email:
    errors["email"] = ["请输入有效邮箱"]
if password != confirm:
    errors["password"] = ["两次输入的密码不一致"]
if User.objects.filter(username__iexact=email).exists():
    errors["email"] = ["该邮箱已注册"]
user = User(username=email, email=email)
validate_password(password, user=user)
user.set_password(password)
user.save()
login(request, user)
```

密码校验异常转换为 `{"detail": "注册信息有误", "errors": {"password": [...]}}`。

登录使用 `authenticate(username=email, password=password)`；失败统一返回：

```json
{"detail": "邮箱或密码错误"}
```

在 `api/urls.py` 注册五个认证路由。

- [ ] **Step 5: 更新 CORS**

`DevCorsMiddleware` 必须：

- `Access-Control-Allow-Credentials: true`
- 只回显允许的精确 Origin
- 允许 `Content-Type, X-CSRFToken`
- 允许 `GET, POST, PATCH, DELETE, OPTIONS`
- OPTIONS 直接返回 204

- [ ] **Step 6: 运行认证测试确认 GREEN**

```powershell
python -m pytest tests/test_auth_api.py -q
```

Expected: all auth tests PASS.

- [ ] **Step 7: 提交**

```powershell
git add services/calc-api/api/auth_views.py services/calc-api/tests/test_auth_api.py services/calc-api/calcapi/settings.py services/calc-api/calcapi/middleware.py services/calc-api/api/urls.py
git commit -m "feat(calc): add session authentication"
```

---

### Task 2: 用户归属、地区、状态与项目进度

**Files:**
- Create: `services/calc-api/calc_runs/migrations/0003_auth_project_workspace.py`
- Create: `services/calc-api/tests/test_owner_scope_api.py`
- Modify: `services/calc-api/calc_runs/models.py`
- Modify: `services/calc-api/calc_runs/serializers.py`
- Modify: `services/calc-api/api/views.py`
- Modify: `services/calc-api/tests/test_project_contract.py`
- Modify: `services/calc-api/tests/test_persistence_contract.py`

**Interfaces:**
- Consumes: Task 1 的登录会话和 `IsAuthenticated`。
- Produces:
  - `CalcRun.owner -> auth.User`
  - `ScaffoldProject.owner -> auth.User`
  - `ScaffoldProject.region: str`
  - `ScaffoldProject.status: "preparing" | "calculating" | "completed"`
  - Project metadata：`status_label`、`scheme_count`、`last_calculated_at`、`failed_control_count`

- [ ] **Step 1: 写 owner 隔离和项目字段 RED 测试**

```python
# services/calc-api/tests/test_owner_scope_api.py
import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from calc_runs.models import CalcRun, ScaffoldProject


@pytest.fixture
def users():
    User = get_user_model()
    return (
        User.objects.create_user("one@example.com", "one@example.com", "Strong-pass-2026"),
        User.objects.create_user("two@example.com", "two@example.com", "Strong-pass-2026"),
    )


@pytest.mark.django_db
def test_project_crud_is_owner_scoped(users):
    first, second = users
    client = Client()
    client.force_login(first)

    created = client.post(
        "/api/v1/projects",
        data=json.dumps(
            {
                "name": "上海项目",
                "region": "上海",
                "status": "calculating",
                "code": "SH-01",
            }
        ),
        content_type="application/json",
    )
    assert created.status_code == 201
    project_id = created.json()["project_id"]
    assert created.json()["region"] == "上海"
    assert created.json()["status"] == "calculating"
    assert created.json()["scheme_count"] == 0

    client.force_login(second)
    assert client.get("/api/v1/projects").json()["projects"] == []
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404
    assert (
        client.patch(
            f"/api/v1/projects/{project_id}",
            data=json.dumps({"name": "越权"}),
            content_type="application/json",
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/projects/{project_id}").status_code == 404


@pytest.mark.django_db
def test_anonymous_project_and_run_requests_return_401():
    client = Client()
    assert client.get("/api/v1/projects").status_code == 401
    assert client.get("/api/v1/runs").status_code == 401


@pytest.mark.django_db
def test_project_progress_is_derived(users):
    user, _ = users
    project = ScaffoldProject.objects.create(
        owner=user,
        name="进度项目",
        region="江苏",
        status="calculating",
    )
    run = CalcRun.objects.create(
        owner=user,
        module="scaffold-fastener",
        title="扣件式脚手架",
        standard="JGJ 130-2011",
        verified=False,
        params={},
        payload={},
        summary={"total": 10, "failed": 2, "control_failed": 1},
    )
    project.schemes.create(
        name="方案一",
        module="scaffold-fastener",
        module_title="扣件式脚手架",
        params={},
        last_run=run,
    )

    client = Client()
    client.force_login(user)
    payload = client.get(f"/api/v1/projects/{project.id}").json()
    assert payload["scheme_count"] == 1
    assert payload["failed_control_count"] == 1
    assert payload["last_calculated_at"] == run.created_at.isoformat()


@pytest.mark.django_db
def test_region_and_status_validation(users):
    client = Client()
    client.force_login(users[0])
    invalid_region = client.post(
        "/api/v1/projects",
        data=json.dumps({"name": "项目", "region": "火星"}),
        content_type="application/json",
    )
    invalid_status = client.post(
        "/api/v1/projects",
        data=json.dumps({"name": "项目", "region": "全国", "status": "unknown"}),
        content_type="application/json",
    )
    assert invalid_region.status_code == 400
    assert invalid_status.status_code == 400
```

更新 `test_project_contract.py`，项目创建 payload 必须显式包含地区；缺少地区必须失败：

```python
{
    "name": "项目一",
    "region": "全国",
    "status": "preparing",
    "code": "",
    "client": "",
    "location": "",
    "designer": "",
    "note": "",
}
```

```python
with pytest.raises(InputValidationError, match="region is required"):
    validate_project_payload({"name": "项目一"})
```

- [ ] **Step 2: 运行测试确认 RED**

```powershell
python -m pytest tests/test_owner_scope_api.py tests/test_project_contract.py tests/test_persistence_contract.py -q
```

Expected: FAIL because owner/region/status fields and user-scoped queries do not exist.

- [ ] **Step 3: 更新模型**

`CalcRun` 与 `ScaffoldProject` 增加：

```python
owner = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    related_name="+",
    on_delete=models.CASCADE,
    db_index=True,
)
```

项目增加：

```python
REGION_CHOICES = (
    ("全国", "全国"),
    ("上海", "上海"),
    ("江苏", "江苏"),
    ("浙江", "浙江"),
    ("北京", "北京"),
    ("山东", "山东"),
    ("广东", "广东"),
    ("湖北", "湖北"),
    ("福建", "福建"),
    ("重庆", "重庆"),
)

STATUS_CHOICES = (
    ("preparing", "筹备中"),
    ("calculating", "计算中"),
    ("completed", "已完成"),
)

region = models.CharField(max_length=20, choices=REGION_CHOICES, default="全国")
status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="preparing")
```

项目 `metadata()` 根据传入 schemes 计算：

```python
runs = [scheme["last_run"] for scheme in (schemes or []) if scheme.get("last_run")]
last_run = max(runs, key=lambda item: item["created_at"], default=None)
data["status_label"] = self.get_status_display()
data["last_calculated_at"] = last_run["created_at"] if last_run else None
data["failed_control_count"] = sum(
    int((scheme.get("last_run") or {}).get("summary", {}).get("control_failed") or 0)
    for scheme in (schemes or [])
)
```

- [ ] **Step 4: 写迁移 0003**

迁移顺序：

1. 创建 `legacy-data@internal.invalid`，`is_active=False`，`password="!"`。
2. 添加 nullable owner、region 默认“全国”、status 默认“preparing”。
3. 把所有无 owner 的 run/project 指给 legacy 用户。
4. 把 owner 改为 non-null。
5. 增加索引。

迁移必须可重复执行，且不在 reverse 时误删仍有关系的 legacy 用户。

- [ ] **Step 5: 更新序列化和 API 所有权**

`PROJECT_FIELDS` 加入 `region`、`status`；枚举错误返回明确字段错误。

项目列表：

```python
records = ScaffoldProject.objects.filter(owner=request.user)
status_value = request.query_params.get("status")
if status_value:
    records = records.filter(status=status_value)
records = records.prefetch_related(
    Prefetch(
        "schemes",
        queryset=ScaffoldScheme.objects.select_related("last_run").order_by(
            "-updated_at", "-created_at"
        ),
    )
)
```

创建项目时写 `owner=request.user`。详情、修改、删除统一通过：

```python
ScaffoldProject.objects.filter(owner=request.user).get(id=project_id)
```

方案接口先验证：

```python
project = get_object_or_404(
    ScaffoldProject.objects.filter(owner=request.user),
    id=project_id,
)
```

`RunView` 列表过滤 `owner=request.user`，创建时写 owner；`RunDetailView` 同样过滤。

- [ ] **Step 6: 运行目标测试确认 GREEN**

```powershell
python -m pytest tests/test_owner_scope_api.py tests/test_project_contract.py tests/test_persistence_contract.py -q
```

Expected: all tests PASS.

- [ ] **Step 7: 提交**

```powershell
git add services/calc-api/calc_runs/models.py services/calc-api/calc_runs/serializers.py services/calc-api/calc_runs/migrations/0003_auth_project_workspace.py services/calc-api/api/views.py services/calc-api/tests/test_owner_scope_api.py services/calc-api/tests/test_project_contract.py services/calc-api/tests/test_persistence_contract.py
git commit -m "feat(calc): isolate projects and runs by owner"
```

---

### Task 3: React 路由、认证客户端与登录注册页

**Files:**
- Modify: `apps/calc/package.json`
- Modify: `apps/calc/vite.config.ts`
- Modify: `apps/calc/tsconfig.json`
- Modify: `apps/calc/src/index.css`
- Create: `apps/calc/.env.example`
- Create: `apps/calc/components.json`
- Create: `apps/calc/src/components/ui/button.tsx`
- Create: `apps/calc/src/components/ui/input.tsx`
- Create: `apps/calc/src/components/ui/label.tsx`
- Create: `apps/calc/src/components/ui/card.tsx`
- Create: `apps/calc/src/components/ui/alert.tsx`
- Create: `apps/calc/src/components/ui/skeleton.tsx`
- Create: `apps/calc/src/api/client.ts`
- Create: `apps/calc/src/api/auth.ts`
- Create: `apps/calc/src/auth/AuthGate.tsx`
- Create: `apps/calc/src/pages/AuthLayout.tsx`
- Create: `apps/calc/src/pages/LoginPage.tsx`
- Create: `apps/calc/src/pages/RegisterPage.tsx`
- Create: `apps/calc/src/pages/LoginPage.test.tsx`
- Create: `apps/calc/src/pages/RegisterPage.test.tsx`
- Modify: `apps/calc/src/test/setup.ts`

**Interfaces:**
- Consumes: Task 1 auth endpoints。
- Produces:
  - `apiRequest<T>(path: string, init?: RequestInit): Promise<T>`
  - `apiFetchRaw(path: string, init?: RequestInit): Promise<Response>`
  - `useCurrentUser()`
  - `useLogin()`, `useRegister()`, `useLogout()`
  - `AuthGate` 和前端认证状态恢复能力

- [x] **Step 1: 安装路由、表单与 shadcn 依赖**

```powershell
cd apps/calc
bun add react-router-dom react-hook-form zod @hookform/resolvers @tanstack/react-table @tanstack/react-virtual
bunx shadcn@latest init --defaults --yes
bunx shadcn@latest add button input label card alert skeleton table dialog badge dropdown-menu select textarea alert-dialog sonner
```

如果 shadcn 初始化询问 base color，选择 `neutral`。当前 `mcp__shadcn_ui` 返回的是 shadcn-vue 目录，不能直接复制到 React；使用 CLI 安装 React registry 源码，生成后再核对 import 和依赖。

- [x] **Step 2: 写登录和注册 RED 测试**

```tsx
// apps/calc/src/pages/LoginPage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { LoginPage } from './LoginPage'

function renderLogin() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/login?next=%2Fworkspace']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/workspace" element={<div>工作台已打开</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LoginPage', () => {
  it('登录成功后进入安全 next 路由', async () => {
    globalThis.fetch = vi.fn(async (input) => {
      const url = String(input)
      if (url.endsWith('/auth/csrf')) {
        return new Response('{}', {
          status: 200,
          headers: { 'Set-Cookie': 'csrftoken=test-token; Path=/' },
        })
      }
      if (url.endsWith('/auth/login')) {
        return new Response(
          JSON.stringify({
            user_id: 1,
            email: 'user@example.com',
            display_name: 'user@example.com',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }
      throw new Error(`unexpected ${url}`)
    }) as never

    renderLogin()
    fireEvent.change(screen.getByLabelText('邮箱'), {
      target: { value: 'user@example.com' },
    })
    fireEvent.change(screen.getByLabelText('密码'), {
      target: { value: 'Strong-pass-2026' },
    })
    fireEvent.click(screen.getByRole('button', { name: '登录' }))
    expect(await screen.findByText('工作台已打开')).toBeInTheDocument()
  })
})
```

Register 测试覆盖确认密码不一致、邮箱已存在和成功注册跳转 `/workspace`。

- [x] **Step 3: 确认前端 RED**

```powershell
bun run test -- src/pages/LoginPage.test.tsx src/pages/RegisterPage.test.tsx
```

Expected: FAIL because pages and router do not exist.

- [x] **Step 4: 实现统一 API 客户端**

`client.ts` 同时导出 `apiRequest` 和 `apiFetchRaw`：

```ts
const BASE = import.meta.env.VITE_CALC_API ?? '/api/v1'

function cookie(name: string) {
  return document.cookie
    .split('; ')
    .find((part) => part.startsWith(`${name}=`))
    ?.split('=')[1]
}

export class ApiError extends Error {
  status: number
  detail: string
  errors: Record<string, string[]>

  constructor(status: number, body: { detail?: string; errors?: Record<string, string[]> }) {
    super(body.detail ?? `请求失败 (${status})`)
    this.status = status
    this.detail = body.detail ?? `请求失败 (${status})`
    this.errors = body.errors ?? {}
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}) {
  const response = await apiFetchRaw(path, init)
  if (response.status === 401) {
    window.dispatchEvent(new Event('calc:unauthorized'))
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(response.status, body)
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

export async function apiFetchRaw(path: string, init: RequestInit = {}) {
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRFToken', decodeURIComponent(cookie('csrftoken') ?? ''))
  }
  if (init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  return fetch(`${BASE}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  })
}

export async function ensureCsrf() {
  await fetch(`${BASE}/auth/csrf`, { credentials: 'include' })
}
```

保留 `ApiError` 的 `detail` 和 `errors` 字段，供表单展示。

- [x] **Step 5: 实现 AuthGate**

`RequireAuth` 通过 `useCurrentUser()`：

- loading：显示骨架页。
- 401：`Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}`。
- 已登录：`Outlet`。

监听 `calc:unauthorized`，使 `['auth','me']` 失效。

登录后的 `next` 只接受以单个 `/` 开头且不以 `//` 开头的站内路径，其他值一律回退 `/workspace`。

- [x] **Step 6: 实现登录和注册页面**

使用 React Hook Form + Zod。登录字段为邮箱、密码；注册字段为邮箱、密码、确认密码。

视觉结构按已确认方案：

- 左栏墨绿工程网格品牌区。
- 右栏白底表单。
- 小屏改为单列。
- 提交中禁用按钮并显示 Spinner。
- API 字段错误映射到对应 input。
- 登录页链接 `/register`，注册页链接 `/login`。

- [x] **Step 7: 配置 Vite 同源代理**

```ts
server: {
  port: 5179,
  strictPort: true,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8001',
      changeOrigin: false,
    },
  },
},
```

`.env.example`：

```text
VITE_CALC_API=/api/v1
```

- [x] **Step 8: 运行测试与构建**

```powershell
bun run test -- src/pages/LoginPage.test.tsx src/pages/RegisterPage.test.tsx
bun run check-types
```

Expected: tests PASS，TypeScript 无错误。

- [x] **Step 9: 提交**

```powershell
git add apps/calc/package.json bun.lock apps/calc/vite.config.ts apps/calc/tsconfig.json apps/calc/src/index.css apps/calc/.env.example apps/calc/components.json apps/calc/src/components/ui apps/calc/src/api/client.ts apps/calc/src/api/auth.ts apps/calc/src/auth/AuthGate.tsx apps/calc/src/pages/AuthLayout.tsx apps/calc/src/pages/LoginPage.tsx apps/calc/src/pages/RegisterPage.tsx apps/calc/src/pages/LoginPage.test.tsx apps/calc/src/pages/RegisterPage.test.tsx apps/calc/src/test/setup.ts
git commit -m "feat(calc): add routed authentication pages"
```

---

### Task 4: 项目工作台与项目 CRUD

**Files:**
- Modify: `apps/calc/src/api/calc.ts`
- Create: `apps/calc/src/api/projects.ts`
- Create: `apps/calc/src/components/UserMenu.tsx`
- Create: `apps/calc/src/components/StatusBadge.tsx`
- Create: `apps/calc/src/components/ProjectFormDialog.tsx`
- Create: `apps/calc/src/components/ProjectTable.tsx`
- Create: `apps/calc/src/components/WorkspaceHeader.tsx`
- Create: `apps/calc/src/pages/WorkspacePage.tsx`
- Create: `apps/calc/src/pages/WorkspacePage.test.tsx`
- Create: `apps/calc/src/components/ProjectFormDialog.test.tsx`
- Modify: `apps/calc/src/index.css`

**Interfaces:**
- Consumes: Task 2 project APIs、Task 3 `apiRequest`。
- Produces:
  - `ProjectStatus = 'preparing' | 'calculating' | 'completed'`
  - `REGIONS`
  - `useProjects(filters)`, `useProject(id)`
  - `createProject`, `updateProject`, `deleteProject`
  - `ProjectFormValues`

- [x] **Step 1: 写工作台 RED 测试**

```tsx
// apps/calc/src/pages/WorkspacePage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { WorkspacePage } from './WorkspacePage'

describe('WorkspacePage', () => {
  it('显示项目地区、状态和自动进度', async () => {
    globalThis.fetch = vi.fn(async () =>
      new Response(
        JSON.stringify({
          projects: [
            {
              project_id: '11111111-1111-4111-8111-111111111111',
              name: '滨江研发楼改造',
              code: 'PM-018',
              client: '建设单位',
              location: '上海',
              region: '上海',
              status: 'calculating',
              status_label: '计算中',
              scheme_count: 8,
              failed_control_count: 1,
              last_calculated_at: '2026-10-27T06:20:00Z',
              updated_at: '2026-10-27T06:20:00Z',
              created_at: '2026-10-26T06:20:00Z',
            },
          ],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    ) as never

    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={['/workspace']}>
          <Routes>
            <Route path="/workspace" element={<WorkspacePage />} />
            <Route
              path="/projects/:projectId/calc"
              element={<div>项目计算页</div>}
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(await screen.findByText('滨江研发楼改造')).toBeInTheDocument()
    expect(screen.getByText('上海')).toBeInTheDocument()
    expect(screen.getByText('计算中')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '进入计算' })).toBeInTheDocument()
  })
})
```

`ProjectFormDialog.test.tsx` 覆盖：

- 地区默认“全国”。
- 清空项目名称不能提交。
- 选择“上海”后提交 payload 含 `region: '上海'`。

- [x] **Step 2: 确认 RED**

```powershell
cd apps/calc
bun run test -- src/pages/WorkspacePage.test.tsx src/components/ProjectFormDialog.test.tsx
```

Expected: FAIL because workspace components do not exist.

- [x] **Step 3: 扩展项目 API**

`ProjectRecord` 增加：

```ts
region: string
status: ProjectStatus
status_label: string
last_calculated_at: string | null
failed_control_count: number
```

`projects.ts` 使用 `apiRequest`，不再直接 fetch。搜索和状态筛选进入 query key：

```ts
export function useProjects(filters: { search: string; status?: ProjectStatus }) {
  const query = new URLSearchParams({ limit: '200' })
  if (filters.search.trim()) query.set('search', filters.search.trim())
  if (filters.status) query.set('status', filters.status)
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => apiRequest<{ projects: ProjectRecord[] }>(`/projects?${query}`),
  })
}
```

- [x] **Step 4: 实现工作台 A 布局**

页面由以下区域组成：

1. 深色顶栏：PM Studio、项目工作台、用户菜单。
2. 标题区：说明和“新建项目”。
3. 四张指标卡：全部、计算中、方案数、已完成。
4. 搜索框、状态筛选、刷新。
5. 项目表：项目、地区、状态、方案数、最近计算、更新时间、操作。

使用 TanStack Table 管理列定义和行模型。搜索/状态筛选写入 URL query，不复制到 Zustand。

项目行：

- Enter 或“进入计算”导航到 `/projects/:projectId/calc`。
- Dropdown Menu 提供编辑和删除。
- 删除打开 AlertDialog，说明会级联删除方案。

- [x] **Step 5: 实现项目表单**

使用 React Hook Form + Zod：

```ts
export const projectSchema = z.object({
  name: z.string().trim().min(1, '项目名称必填'),
  region: z.enum(REGIONS, { message: '请选择项目地区' }),
  status: z.enum(['preparing', 'calculating', 'completed']),
  code: z.string().max(100).default(''),
  client: z.string().max(200).default(''),
  location: z.string().max(255).default(''),
  designer: z.string().max(100).default(''),
  note: z.string().default(''),
})
```

“创建并进入”成功后：

```ts
queryClient.invalidateQueries({ queryKey: ['projects'] })
navigate(`/projects/${project.project_id}/calc`)
```

“仅创建”成功后关闭对话框并停留工作台。

- [x] **Step 6: 实现状态、空态和错误态**

- 筹备中：琥珀 Badge。
- 计算中：墨绿 Badge。
- 已完成：蓝灰 Badge。
- 无项目：显示“新建第一个项目”。
- 搜索无结果：显示“清除筛选”。
- 列表错误：Alert + 重试。
- 加载：稳定表格 Skeleton。

- [x] **Step 7: 运行测试与构建**

```powershell
bun run test -- src/pages/WorkspacePage.test.tsx src/components/ProjectFormDialog.test.tsx
bun run check-types
bun run build
```

Expected: all PASS。

- [x] **Step 8: 提交**

```powershell
git add apps/calc/src/api/calc.ts apps/calc/src/api/projects.ts apps/calc/src/components/UserMenu.tsx apps/calc/src/components/StatusBadge.tsx apps/calc/src/components/ProjectFormDialog.tsx apps/calc/src/components/ProjectTable.tsx apps/calc/src/components/WorkspaceHeader.tsx apps/calc/src/pages/WorkspacePage.tsx apps/calc/src/pages/WorkspacePage.test.tsx apps/calc/src/components/ProjectFormDialog.test.tsx apps/calc/src/index.css
git commit -m "feat(calc): add project workspace"
```

---

### Task 5: 现有计算页接入项目上下文

**Files:**
- Create: `apps/calc/src/pages/CalcWorkspacePage.tsx`
- Create: `apps/calc/src/pages/CalcWorkspacePage.test.tsx`
- Modify: `apps/calc/src/App.tsx`
- Modify: `apps/calc/src/main.tsx`
- Modify: `apps/calc/src/App.test.tsx`
- Modify: `apps/calc/src/components/TopBar.tsx`
- Modify: `apps/calc/src/components/TopBar.test.tsx`
- Modify: `apps/calc/src/components/SchemeDialog.tsx`
- Modify: `apps/calc/src/components/SchemeDialog.test.tsx`
- Modify: `apps/calc/src/api/calc.ts`
- Modify: `apps/calc/src/test/setup.ts`

**Interfaces:**
- Consumes: Task 4 `useProject(projectId)`。
- Produces: `CalcWorkspacePage` 项目上下文条和 `onBack()`。

- [x] **Step 1: 写计算页上下文 RED 测试**

```tsx
// apps/calc/src/pages/CalcWorkspacePage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { CalcWorkspacePage } from './CalcWorkspacePage'

describe('CalcWorkspacePage', () => {
  it('显示项目名称、地区和返回工作台入口', async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter
          initialEntries={['/projects/11111111-1111-4111-8111-111111111111/calc']}
        >
          <Routes>
            <Route
              path="/projects/:projectId/calc"
              element={<CalcWorkspacePage />}
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(await screen.findByText('滨江研发楼改造')).toBeInTheDocument()
    expect(screen.getByText('上海')).toBeInTheDocument()
    expect(screen.getByText('计算中')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '返回项目工作台' })).toBeInTheDocument()
  })
})
```

更新 `SchemeDialog.test.tsx`，断言对话框不再显示项目搜索和项目切换，只调用当前 `projectId` 的方案 API。

- [x] **Step 2: 确认 RED**

```powershell
bun run test -- src/pages/CalcWorkspacePage.test.tsx src/components/SchemeDialog.test.tsx
```

Expected: FAIL because calculation page has no project route/context.

- [x] **Step 3: 把现有计算器移入 `CalcWorkspacePage` 并完成路由**

现有 `App.tsx` 主体移入 `CalcWorkspacePage`：

```tsx
export function CalcWorkspacePage() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const project = useProject(projectId!)

  if (project.isPending) return <CalcWorkspaceSkeleton />
  if (project.isError || !project.data) return <ProjectLoadError />

  return (
    <div className="flex h-full flex-col">
      <ProjectContextBar
        project={project.data}
        onBack={() => navigate('/workspace')}
      />
      <CalcWorkspace project={project.data} />
    </div>
  )
}
```

`CalcWorkspace` 保留原模块、参数、画布、结果、批量、历史和导出状态。

`main.tsx` 使用 BrowserRouter；`App.tsx` 成为最终路由入口：

```tsx
<Routes>
  <Route path="/" element={<RootRedirect />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />
  <Route element={<RequireAuth />}>
    <Route path="/workspace" element={<WorkspacePage />} />
    <Route path="/projects/:projectId/calc" element={<CalcWorkspacePage />} />
  </Route>
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes>
```

`RootRedirect` 已登录时去 `/workspace`，未登录时去 `/login`。原 `App.test.tsx` 的三联、筛选、平面视图和参数修改断言迁入 `CalcWorkspacePage.test.tsx`；`App.test.tsx` 改为只测试未认证进入登录、认证后进入工作台、项目路由渲染计算页。

- [x] **Step 4: 修改 TopBar 与方案入口**

- TopBar 显示项目名、地区、状态和当前方案。
- 删除“未选择项目”行为；项目上下文由路由保证。
- 增加“返回项目工作台”链接。
- “方案”只打开当前项目的方案列表。
- 不在计算页创建或切换项目。

- [x] **Step 5: 将 `api/calc.ts` 切到统一客户端**

所有 fetch 改为 `apiRequest`，保留现有导出下载函数：

```ts
const response = await apiFetchRaw('/report.docx', {
  method: 'POST',
  body: JSON.stringify({ module, params }),
})
```

`apiFetchRaw` 同样附带 Cookie 和 CSRF，但返回原始 `Response` 以支持 Blob 下载。

- [x] **Step 6: 运行目标测试**

```powershell
bun run test -- src/pages/CalcWorkspacePage.test.tsx src/components/TopBar.test.tsx src/components/SchemeDialog.test.tsx
bun run check-types
```

Expected: all PASS。

- [x] **Step 7: 提交**

```powershell
git add apps/calc/src/pages/CalcWorkspacePage.tsx apps/calc/src/pages/CalcWorkspacePage.test.tsx apps/calc/src/App.tsx apps/calc/src/main.tsx apps/calc/src/App.test.tsx apps/calc/src/components/TopBar.tsx apps/calc/src/components/TopBar.test.tsx apps/calc/src/components/SchemeDialog.tsx apps/calc/src/components/SchemeDialog.test.tsx apps/calc/src/api/calc.ts apps/calc/src/test/setup.ts
git commit -m "feat(calc): scope calculator to project"
```

---

### Task 6: 全量回归、安全验收与真实浏览器闭环

**Files:**
- Create: `scripts/verify-calc-auth-workspace.py`
- Create: `docs/qa/2026-10-27-auth-project-workspace.md`
- Modify: `services/calc-api/calcapi/settings.py`
- Modify: `apps/calc/scripts/smoke.mjs`
- Modify: `apps/calc/package.json`

**Interfaces:**
- Consumes: Tasks 1–5。
- Produces: 可重复的后端、前端和浏览器验收证据。

- [x] **Step 1: 允许隔离的临时 SQLite 路径**

在 `settings.py` 的 SQLite 分支使用：

```python
"NAME": os.environ.get("CALC_DB_PATH", str(BASE_DIR / "db.sqlite3")),
```

浏览器验收使用 `$env:TEMP` 下的新 SQLite 文件，避免污染日常数据。

- [x] **Step 2: 写浏览器验收脚本**

`scripts/verify-calc-auth-workspace.py` 使用 Playwright 系统 Chrome：

```python
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.goto(frontend_url, wait_until="networkidle")
    assert "/login" in page.url
    page.get_by_role("link", name="创建账号").click()
    page.get_by_label("邮箱").fill("browser-one@example.com")
    page.get_by_label("密码", exact=True).fill("Browser-pass-2026")
    page.get_by_label("确认密码").fill("Browser-pass-2026")
    page.get_by_role("button", name="注册").click()
    page.wait_for_url("**/workspace")
    page.get_by_role("button", name="新建项目").click()
    page.get_by_label("项目名称").fill("浏览器验收项目")
    page.get_by_label("项目地区").select_option("上海")
    page.get_by_role("button", name="创建并进入").click()
    page.wait_for_url("**/projects/*/calc")
    assert page.get_by_text("浏览器验收项目").is_visible()
    assert page.get_by_text("上海").is_visible()
    page.get_by_role("link", name="返回项目工作台").click()
    page.wait_for_url("**/workspace")
    assert page.get_by_text("浏览器验收项目").is_visible()
    page.reload(wait_until="networkidle")
    assert page.get_by_text("浏览器验收项目").is_visible()
    assert errors == []
    browser.close()
```

脚本还必须用第二个用户验证不可见第一个用户的项目，并截图到 `artifacts/calc-auth-workspace/`。

- [ ] **Step 3: 扩展 smoke 测试**

`apps/calc/scripts/smoke.mjs` 至少检查：

- `/login` 返回 200 且包含应用挂载点。
- `BrowserRouter` 深链 `/workspace` 可由 Vite fallback 加载。
- 未登录时 API 返回 401。

- [x] **Step 4: 后端全量**

```powershell
cd services/calc-api
python -m pytest -q
python manage.py makemigrations --check --dry-run
python manage.py check
```

Expected: all tests PASS；无遗漏迁移；system check 0 issues。

- [ ] **Step 5: 前端全量**

```powershell
cd apps/calc
bun run test
bun run build
bun run test:e2e
```

Expected: 所有 Vitest、build、smoke PASS。

- [x] **Step 6: 真实浏览器闭环**

使用临时数据库启动 Django `127.0.0.1:8001` 和 Vite `127.0.0.1:5179`：

```powershell
$env:CALC_DB_PATH = Join-Path $env:TEMP 'calc-auth-workspace.sqlite3'
python services/calc-api/manage.py migrate
python scripts/verify-calc-auth-workspace.py
```

验收必须覆盖：

1. 未登录跳转注册页。
2. 注册后进入工作台。
3. 新建上海项目并进入计算页。
4. 保存方案。
5. 返回工作台，方案数与最近计算时间更新。
6. 刷新后会话和项目仍存在。
7. 第二个账号看不到第一个账号的数据。
8. 删除测试项目。
9. 桌面 1440px 与手机 390px 均无横向溢出。
10. 零未处理控制台错误和 5xx。

- [x] **Step 7: 文档与清理**

`docs/qa/2026-10-27-auth-project-workspace.md` 记录：

- 精确测试数字。
- 浏览器截图路径。
- 两个用户的隔离证据。
- 地区只作项目字段的边界。
- 未实现邮件验证、找回密码、团队共享。
- 临时服务已停止、临时数据库已清理。

- [x] **Step 8: 最终检查**

```powershell
git diff --check -- services/calc-api apps/calc scripts/verify-calc-auth-workspace.py docs/qa/2026-10-27-auth-project-workspace.md
git status --short
```

Expected: 无空白错误；仅本功能文件进入提交；无关既有改动保持原状。

- [x] **Step 9: 提交**

```powershell
git add services/calc-api/calcapi/settings.py apps/calc/scripts/smoke.mjs apps/calc/package.json scripts/verify-calc-auth-workspace.py docs/qa/2026-10-27-auth-project-workspace.md
git commit -m "test(calc): verify authenticated project workflow"
```
