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
const consoleErrors = []
const pageErrors = []

page.on('console', (message) => {
  if (message.type() === 'error') consoleErrors.push(message.text())
})
page.on('pageerror', (error) => pageErrors.push(error.message))

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

async function waitForWorkspaceRoute(path, heading, activeLink) {
  await page.waitForURL((url) => url.pathname === path, { timeout: 15_000 })
  await page.getByRole('heading', { name: heading, exact: true }).waitFor()

  const directory = page.getByRole('navigation', { name: '工作台目录' })
  const active = directory.getByRole('link', { name: activeLink, exact: true })
  if ((await active.getAttribute('aria-current')) !== 'page') {
    throw new Error(`${path} did not mark ${activeLink} as the active directory entry`)
  }
}

async function assertNoHorizontalOverflow(label) {
  const metrics = await page.evaluate(() => ({
    body: document.body.scrollWidth,
    html: document.documentElement.scrollWidth,
    viewport: window.innerWidth,
  }))
  if (Math.max(metrics.body, metrics.html) > metrics.viewport) {
    throw new Error(
      `${label} overflowed horizontally: viewport=${metrics.viewport} html=${metrics.html} body=${metrics.body}`,
    )
  }
}

function assertBrowserClean() {
  if (consoleErrors.length > 0) {
    throw new Error(`browser console errors (${consoleErrors.length}): ${consoleErrors.join(' | ')}`)
  }
  if (pageErrors.length > 0) {
    throw new Error(`browser page errors (${pageErrors.length}): ${pageErrors.join(' | ')}`)
  }
}

let qaProjectId
let devLoginSuccessMessage

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
    await waitForWorkspaceRoute('/workspace', '项目工作台', '工作台')
    await assertNoHorizontalOverflow('desktop /workspace')

    await page.getByRole('link', { name: '项目管理', exact: true }).click()
    await waitForWorkspaceRoute('/workspace/projects', '项目管理', '项目管理')

    await page.getByRole('link', { name: '系统设置', exact: true }).click()
    await waitForWorkspaceRoute('/workspace/settings', '系统设置', '系统设置')

    await page.getByRole('link', { name: '回收站', exact: true }).click()
    await waitForWorkspaceRoute('/workspace/recycle-bin', '回收站', '回收站')
    await page.getByText('回收站尚未启用', { exact: true }).waitFor()

    await page.getByRole('link', { name: '工作台', exact: true }).click()
    await waitForWorkspaceRoute('/workspace', '项目工作台', '工作台')

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

    const updateResponse = await context.request.patch(
      appUrl(`/api/v1/projects/${qaProjectId}`),
      {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': await csrfToken(),
        },
        data: {
          name: projectName,
          region: '上海',
          status: 'calculating',
        },
      },
    )
    if (updateResponse.status() !== 200) {
      throw new Error(`PATCH /api/v1/projects returned ${updateResponse.status()}`)
    }
    const updatedProject = await updateResponse.json()
    if (updatedProject.region !== '上海' || updatedProject.status !== 'calculating') {
      throw new Error('updated QA project did not reflect the requested values')
    }

    const readResponse = await context.request.get(
      appUrl(`/api/v1/projects/${qaProjectId}`),
    )
    if (readResponse.status() !== 200) {
      throw new Error(`GET /api/v1/projects/:id returned ${readResponse.status()}`)
    }
    const readProject = await readResponse.json()
    if (readProject.project_id !== qaProjectId || readProject.status !== 'calculating') {
      throw new Error('read QA project did not match the updated record')
    }

    const calcResponse = await page.goto(appUrl(`/projects/${qaProjectId}/calc`), {
      waitUntil: 'networkidle',
    })
    if (calcResponse?.status() !== 200) {
      throw new Error(`GET project calc returned ${calcResponse?.status() ?? 'no response'}`)
    }
    const expectedCalcPath = `/projects/${qaProjectId}/calc`
    const actualCalcPath = new URL(page.url()).pathname
    if (actualCalcPath !== expectedCalcPath) {
      throw new Error(
        `project calc navigation ended at ${actualCalcPath}, expected ${expectedCalcPath}`,
      )
    }
    await waitForBrand(expectedCalcPath)

    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(appUrl('/workspace'), { waitUntil: 'networkidle' })
    await page.getByRole('heading', { name: '项目工作台', exact: true }).waitFor()
    await assertNoHorizontalOverflow('mobile /workspace')

    await page.getByRole('button', { name: '打开工作台目录', exact: true }).click()
    const mobileDirectory = page.getByRole('dialog', { name: '工作台目录' })
    await mobileDirectory.waitFor()
    const directoryBox = await mobileDirectory.boundingBox()
    if (!directoryBox || Math.abs(directoryBox.x) > 1 || directoryBox.width > 336) {
      throw new Error('mobile directory was not anchored to the left edge within its width limit')
    }
    await assertNoHorizontalOverflow('mobile /workspace with directory open')

    await mobileDirectory.getByRole('link', { name: '系统设置', exact: true }).click()
    await page.waitForURL((url) => url.pathname === '/workspace/settings', {
      timeout: 15_000,
    })
    await page.getByRole('heading', { name: '系统设置', exact: true }).waitFor()
    await mobileDirectory.waitFor({ state: 'detached', timeout: 15_000 })
    await assertNoHorizontalOverflow('mobile /workspace/settings')
    assertBrowserClean()

    devLoginSuccessMessage =
      'smoke ok: dev-login=prefilled routes=4 active=desktop mobile-drawer=open+close viewport=1440+390 overflow=none console-errors=0 qa-project=crud+calc+deleted'
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
      if (devLoginSuccessMessage) console.log(devLoginSuccessMessage)
    }
  } finally {
    await browser.close()
  }
}
