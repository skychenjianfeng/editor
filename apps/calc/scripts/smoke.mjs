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
let qaProjectName
let qaProjectNeedsCleanup = false
let successMessage

async function cleanupQaProject() {
  if (!qaProjectNeedsCleanup) return

  let projectId = qaProjectId
  if (!projectId && qaProjectName) {
    const searchResponse = await context.request.get(
      appUrl(`/api/v1/projects?limit=200&search=${encodeURIComponent(qaProjectName)}`),
    )
    if (searchResponse.status() !== 200) {
      throw new Error(
        `cleanup GET /api/v1/projects returned ${searchResponse.status()}`,
      )
    }
    const searchBody = await searchResponse.json()
    const matches = searchBody.projects.filter((project) => project.name === qaProjectName)
    if (matches.length > 1) {
      throw new Error(`cleanup found ${matches.length} projects with the unique QA name`)
    }
    projectId = matches[0]?.project_id
  }

  if (!projectId) return
  const deleteResponse = await context.request.delete(
    appUrl(`/api/v1/projects/${projectId}`),
    { headers: { 'X-CSRFToken': await csrfToken() } },
  )
  if (deleteResponse.status() !== 204 && deleteResponse.status() !== 404) {
    throw new Error(`cleanup DELETE /api/v1/projects returned ${deleteResponse.status()}`)
  }
  qaProjectNeedsCleanup = false
}

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
    const desktopNavigation = page.getByRole('navigation', {
      name: '工作台目录',
      exact: true,
    })
    await desktopNavigation.waitFor()
    const desktopNavigationBox = await desktopNavigation.boundingBox()
    if (
      !desktopNavigationBox ||
      Math.abs(desktopNavigationBox.width - 232) > 1
    ) {
      throw new Error(
        `desktop directory width was ${desktopNavigationBox?.width ?? 'missing'}px, expected 232px ±1px`,
      )
    }
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

    await page.getByRole('link', { name: '项目管理', exact: true }).click()
    await waitForWorkspaceRoute('/workspace/projects', '项目管理', '项目管理')

    qaProjectName = `QA 玄构天枢 ${Date.now()} ${randomUUID().slice(0, 8)}`
    qaProjectNeedsCleanup = true
    await page.getByRole('button', { name: '新建项目', exact: true }).click()
    const createDialog = page.getByRole('dialog', { name: '新建项目', exact: true })
    await createDialog.waitFor()
    await createDialog.getByLabel('项目名称').fill(qaProjectName)
    await createDialog.getByLabel('项目地区').selectOption('全国')
    await createDialog.getByLabel('项目状态').selectOption('preparing')
    const createResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === 'POST' &&
        new URL(response.url()).pathname === '/api/v1/projects',
    )
    await createDialog.getByRole('button', { name: '仅创建', exact: true }).click()
    const createResponse = await createResponsePromise
    if (createResponse.status() !== 201) {
      throw new Error(
        `UI create POST /api/v1/projects returned ${createResponse.status()}`,
      )
    }
    const createdProject = await createResponse.json()
    if (typeof createdProject.project_id !== 'string') {
      throw new Error('created QA project did not include project_id')
    }
    qaProjectId = createdProject.project_id
    await createDialog.waitFor({ state: 'detached', timeout: 15_000 })

    const createdRow = page.getByRole('row').filter({ hasText: qaProjectName })
    await createdRow.waitFor()
    await createdRow.getByText('全国', { exact: true }).waitFor()
    await createdRow.getByText('筹备中', { exact: true }).waitFor()

    await createdRow
      .getByRole('button', { name: `更多操作 ${qaProjectName}`, exact: true })
      .click()
    await page.getByRole('menuitem', { name: '编辑项目', exact: true }).click()
    const editDialog = page.getByRole('dialog', { name: '编辑项目', exact: true })
    await editDialog.waitFor()
    await editDialog.getByLabel('项目地区').selectOption('上海')
    await editDialog.getByLabel('项目状态').selectOption('calculating')
    const updateResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === 'PATCH' &&
        new URL(response.url()).pathname === `/api/v1/projects/${qaProjectId}`,
    )
    await editDialog.getByRole('button', { name: '保存修改', exact: true }).click()
    const updateResponse = await updateResponsePromise
    if (updateResponse.status() !== 200) {
      throw new Error(
        `UI edit PATCH /api/v1/projects returned ${updateResponse.status()}`,
      )
    }
    const updatedProject = await updateResponse.json()
    if (updatedProject.region !== '上海' || updatedProject.status !== 'calculating') {
      throw new Error('updated QA project did not reflect the requested values')
    }
    await editDialog.waitFor({ state: 'detached', timeout: 15_000 })

    const readResponsePromise = page.waitForResponse(
      (response) => {
        const url = new URL(response.url())
        return (
          response.request().method() === 'GET' &&
          url.pathname === '/api/v1/projects' &&
          url.searchParams.get('search') === qaProjectName
        )
      },
    )
    await page.getByLabel('搜索项目').fill(qaProjectName)
    await readResponsePromise
    const editedRow = page.getByRole('row').filter({ hasText: qaProjectName })
    await editedRow.waitFor()
    await editedRow.getByText('上海', { exact: true }).waitFor()
    await editedRow.getByText('计算中', { exact: true }).waitFor()

    await editedRow
      .getByRole('button', { name: `进入计算 ${qaProjectName}`, exact: true })
      .click()
    const expectedCalcPath = `/projects/${qaProjectId}/calc`
    await page.waitForURL((url) => url.pathname === expectedCalcPath, {
      timeout: 15_000,
    })
    await waitForBrand(expectedCalcPath)

    await page.goBack({ waitUntil: 'networkidle' })
    await waitForWorkspaceRoute('/workspace/projects', '项目管理', '项目管理')
    const rowForDeletion = page.getByRole('row').filter({ hasText: qaProjectName })
    await rowForDeletion.waitFor()
    await rowForDeletion
      .getByRole('button', { name: `更多操作 ${qaProjectName}`, exact: true })
      .click()
    await page.getByRole('menuitem', { name: '删除项目', exact: true }).click()
    const deleteDialog = page.getByRole('alertdialog')
    await deleteDialog.waitFor()
    const deleteResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === 'DELETE' &&
        new URL(response.url()).pathname === `/api/v1/projects/${qaProjectId}`,
    )
    await deleteDialog.getByRole('button', { name: '确认删除', exact: true }).click()
    const deleteResponse = await deleteResponsePromise
    if (deleteResponse.status() !== 204) {
      throw new Error(
        `UI delete DELETE /api/v1/projects returned ${deleteResponse.status()}`,
      )
    }
    qaProjectNeedsCleanup = false
    qaProjectId = undefined
    await deleteDialog.waitFor({ state: 'detached', timeout: 15_000 })
    await rowForDeletion.waitFor({ state: 'detached', timeout: 15_000 })

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

    await mobileDirectory
      .getByRole('button', { name: 'Close', exact: true })
      .click()
    await mobileDirectory.waitFor({ state: 'detached', timeout: 15_000 })
    await page.getByRole('heading', { name: '项目工作台', exact: true }).waitFor()

    await page.getByRole('button', { name: '打开工作台目录', exact: true }).click()
    await mobileDirectory.waitFor()
    await page.keyboard.press('Escape')
    await mobileDirectory.waitFor({ state: 'detached', timeout: 15_000 })
    await page.getByRole('heading', { name: '项目工作台', exact: true }).waitFor()

    await page.getByRole('button', { name: '打开工作台目录', exact: true }).click()
    await mobileDirectory.waitFor()
    await mobileDirectory.getByRole('link', { name: '系统设置', exact: true }).click()
    await page.waitForURL((url) => url.pathname === '/workspace/settings', {
      timeout: 15_000,
    })
    await page.getByRole('heading', { name: '系统设置', exact: true }).waitFor()
    await mobileDirectory.waitFor({ state: 'detached', timeout: 15_000 })
    await assertNoHorizontalOverflow('mobile /workspace/settings')
    assertBrowserClean()

    successMessage =
      'smoke ok: dev-login=prefilled routes=4 active=desktop desktop-nav=232px mobile-close=button+escape+navigation viewport=1440+390 overflow=none console-errors=0 qa-project=ui-crud+calc+ui-deleted cleanup=finally'
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

    successMessage =
      'smoke ok: login=200 root=present workspace-fallback=200 redirect=/login?next=/workspace anonymous-me=401'
  }
} finally {
  try {
    await cleanupQaProject()
  } finally {
    await browser.close()
  }
}

if (successMessage) console.log(successMessage)
