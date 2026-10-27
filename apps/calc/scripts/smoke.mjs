import { chromium } from 'playwright-core'

const url = process.env.CALC_URL ?? 'http://localhost:5179/'
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

try {
  await page.goto(url, { waitUntil: 'domcontentloaded' })
  await page.getByText('安全计算工作台').first().waitFor({ timeout: 15000 })
  await page.getByText('扣件式脚手架').first().waitFor()

  await page.getByRole('button', { name: '平面', exact: true }).click()
  await page.getByText('剪刀撑', { exact: true }).click()
  await page.getByText('仅不满足').click()

  await page.screenshot({ path: 'smoke-1440.png', fullPage: false })
  console.log('smoke ok: header / module tree / view switch / layer toggle / filter')
} finally {
  await browser.close()
}
