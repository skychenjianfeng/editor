import { chromium } from 'playwright-core'

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
  }

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
} finally {
  await browser.close()
}
