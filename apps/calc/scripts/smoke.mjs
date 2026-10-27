import { randomUUID } from 'node:crypto'
import { chromium } from 'playwright-core'

const BRAND_NAME = '玄构天枢'
const baseUrl = new URL(process.env.CALC_URL ?? 'http://localhost:5179')
baseUrl.pathname = '/'
baseUrl.search = ''
baseUrl.hash = ''

function appUrl(path) {
  return new URL(path, baseUrl).toString()
}

const browser = await chromium.launch({ channel: 'chrome', headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const page = await context.newPage()

async function csrfToken() {
  const response = await context.request.get(appUrl('/api/v1/auth/csrf'))
  if (response.status() !== 200) {
    throw new Error(`GET /api/v1/auth/csrf returned ${response.status()}`)
  }
  const cookie = (await context.cookies(baseUrl.origin)).find(
    (item) => item.name === 'csrftoken',
  )
  if (!cookie?.value) throw new Error('CSRF cookie was not issued')
  return cookie.value
}

async function waitForBrand(location) {
  try {
    await page.getByText(BRAND_NAME, { exact: true }).first().waitFor({
      state: 'visible',
      timeout: 15_000,
    })
  } catch {
    throw new Error(`${location} did not show the expected brand`)
  }
}

let qaProjectId

try {
  const loginResponse = await page.goto(appUrl('/login'), {
    waitUntil: 'domcontentloaded',
  })
  if (loginResponse?.status() !== 200) {
    throw new Error(`GET /login returned ${loginResponse?.status() ?? 'no response'}`)
  }
  await page.locator('#root').waitFor({ state: 'attached', timeout: 15_000 })

  if (process.env.CALC_EXPECT_DEV_LOGIN === '1') {
    const emailValue = await page.getByLabel('邮箱').inputValue()
    const passwordValue = await page.getByLabel('密码').inputValue()
    if (!emailValue || !passwordValue) {
      throw new Error('local login defaults were not applied')
    }

    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.waitForURL((url) => url.pathname === '/workspace', { timeout: 15_000 })
    await waitForBrand('/workspace')

    const projectName = `QA 玄构天枢 ${Date.now()} ${randomUUID().slice(0, 8)}`
    const createResponse = await context.request.post(appUrl('/api/v1/projects'), {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': await csrfToken(),
      },
      data: { name: projectName, region: '全国', status: 'preparing' },
    })
    if (createResponse.status() !== 201) {
      throw new Error(`POST /api/v1/projects returned ${createResponse.status()}`)
    }
    const project = await createResponse.json()
    if (typeof project.project_id !== 'string') {
      throw new Error('created QA project did not include project_id')
    }
    qaProjectId = project.project_id

    const calcResponse = await page.goto(appUrl(`/projects/${qaProjectId}/calc`), {
      waitUntil: 'domcontentloaded',
    })
    if (calcResponse?.status() !== 200) {
      throw new Error(`GET project calc returned ${calcResponse?.status() ?? 'no response'}`)
    }
    await waitForBrand('/projects/:projectId/calc')

    console.log(
      'smoke ok: dev-login=prefilled login=workspace brand=workspace+calc qa-project=created+deleted',
    )
  } else {
    const workspaceResponse = await page.goto(appUrl('/workspace'), {
      waitUntil: 'domcontentloaded',
    })
    if (workspaceResponse?.status() !== 200) {
      throw new Error(
        `GET /workspace returned ${workspaceResponse?.status() ?? 'no response'}`,
      )
    }
    await page.waitForURL(
      (url) => url.pathname === '/login' && url.searchParams.get('next') === '/workspace',
      { timeout: 15_000 },
    )

    const meResponse = await context.request.get(appUrl('/api/v1/auth/me'), {
      failOnStatusCode: false,
    })
    if (meResponse.status() !== 401) {
      throw new Error(`anonymous GET /api/v1/auth/me returned ${meResponse.status()}`)
    }

    console.log(
      'smoke ok: login=200 root=present workspace-fallback=200 redirect=/login?next=/workspace anonymous-me=401',
    )
  }
} finally {
  try {
    if (qaProjectId) {
      const deleteResponse = await context.request.delete(
        appUrl(`/api/v1/projects/${qaProjectId}`),
        { headers: { 'X-CSRFToken': await csrfToken() } },
      )
      if (deleteResponse.status() !== 204) {
        throw new Error(`DELETE /api/v1/projects returned ${deleteResponse.status()}`)
      }
    }
  } finally {
    await browser.close()
  }
}
