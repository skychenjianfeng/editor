import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { homedir, tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { chromium } from 'playwright-core'

const BASE = (process.env.STRUCTWEB_BASE_URL ?? 'http://localhost:3010').replace(/\/$/, '')
const runId = process.env.STRUCTWEB_RUN_ID ?? String(Date.now())
const screenshotDir = resolve('.tmp', `ifc-acceptance-${runId}`)
const screenshots = {
  ifc2x3Review: join(screenshotDir, 'ifc2x3-review.png'),
  ifc2x3Panel: join(screenshotDir, 'ifc2x3-panel.png'),
  ifc2x3Reloaded: join(screenshotDir, 'ifc2x3-reloaded.png'),
  ifc4Workspace: join(screenshotDir, 'ifc4-workspace.png'),
  invalidFile: join(screenshotDir, 'invalid-file-alert.png'),
  corruptFile: join(screenshotDir, 'corrupt-file-alert.png'),
}
const account = {
  displayName: 'StructWeb IFC 验收账号',
  email: `structweb-ifc-acceptance-${runId}@example.test`,
  password: `IfcAcceptance-${runId}-123`,
}
const baselineName = `IFC 验收基线 ${runId}`
const ifc2x3Fixture = resolve('apps/ifc-converter/public/test-ifc-files/01-duplex.ifc')
const ifc4Fixture = resolve('apps/ifc-converter/public/test-ifc-files/10-sample-house.ifc')
const corruptFixtureDir = mkdtempSyncCompat()
const corruptFixture = join(corruptFixtureDir, `01-duplex-corrupt-${runId}.ifc`)
const nativeGeometryTypes = new Set([
  'wall',
  'slab',
  'zone',
  'ceiling',
  'column',
  'block',
  'roof',
  'roof-segment',
])
const knownMissingAsset = /(?:nature-icon|streetscape-icon)/i

mkdirSync(screenshotDir, { recursive: true })
writeFileSync(corruptFixture, readFileSync(ifc2x3Fixture).subarray(0, 64))

const report = {
  importedProjectId: null,
  baselineProjectId: null,
  nodeCount: 0,
  importedMeshCount: 0,
  levelCount: 0,
  renamedNodeId: null,
  persistedAfterReload: false,
  baselineUnchanged: false,
  invalidFileBlocked: false,
  corruptFileBlocked: false,
  ifc2x3Imported: false,
  ifc4Imported: false,
  consoleErrors: [],
}

function check(condition, message) {
  if (!condition) throw new Error(message)
}

function mkdtempSyncCompat() {
  const directory = join(
    tmpdir(),
    `structweb-ifc-corrupt-${Date.now()}-${Math.random().toString(36).slice(2)}`,
  )
  mkdirSync(directory, { recursive: true })
  return directory
}

function projectIdFromUrl(url) {
  return new URL(url).pathname.split('/').at(-1)
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue)
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value)
        .filter((key) => key !== 'updatedAt')
        .sort()
        .map((key) => [key, stableValue(value[key])]),
    )
  }
  return value
}

function graphSignature(graph) {
  check(graph && typeof graph === 'object', 'graph signature requires a project graph')
  return JSON.stringify(stableValue(graph))
}

function graphCounts(graph) {
  const nodes = Object.values(graph?.nodes ?? {})
  return {
    nodeCount: nodes.length,
    importedMeshCount: nodes.filter((node) => node?.type === 'imported-mesh').length,
    levelCount: nodes.filter((node) => node?.type === 'level').length,
    nativeGeometryCount: nodes.filter((node) => nativeGeometryTypes.has(node?.type)).length,
    types: [...new Set(nodes.map((node) => node?.type).filter(Boolean))].sort(),
  }
}

function assertImportedHierarchy(graph, label) {
  const nodes = graph.nodes ?? {}
  const rootNodes = (graph.rootNodeIds ?? []).map((id) => nodes[id])
  const rootSite = rootNodes.find((node) => node?.type === 'site')
  check(rootSite, `${label} must have a root site`)
  const levels = Object.values(nodes).filter((node) => node?.type === 'level')
  check(levels.length > 0, `${label} must contain at least one level`)
  for (const level of levels) {
    const parent = level.parentId ? nodes[level.parentId] : null
    check(parent?.type === 'building', `${label} level ${level.id} must belong to a building`)
    const site = parent.parentId ? nodes[parent.parentId] : null
    check(site?.type === 'site', `${label} building ${parent.id} must belong to a site`)
  }
}

async function waitFor(page, predicate, message, options = {}) {
  const timeout = options.timeout ?? 120000
  const interval = options.interval ?? 250
  const deadline = Date.now() + timeout
  let lastValue
  while (Date.now() < deadline) {
    try {
      lastValue = await predicate()
      if (lastValue) return lastValue
    } catch (error) {
      lastValue = error
    }
    await page.waitForTimeout(interval)
  }
  throw new Error(`${message}; last value: ${String(lastValue)}`)
}

async function waitForProjectCenter(page) {
  await page.getByRole('heading', { name: '结构工程项目中心' }).waitFor({ timeout: 120000 })
  await page
    .getByTestId('struct-project-card')
    .first()
    .waitFor({ timeout: 120000 })
    .catch(() => {})
}

async function waitForReactControl(page, selector) {
  await page.waitForFunction(
    (target) => {
      const element = document.querySelector(target)
      return Boolean(element && Object.keys(element).some((key) => key.startsWith('__reactProps$')))
    },
    selector,
    { timeout: 120000 },
  )
}

async function registerAccount(page) {
  await page.goto(`${BASE}/register`, { waitUntil: 'domcontentloaded', timeout: 120000 })
  await page.getByTestId('auth-register-name').waitFor({ timeout: 120000 })
  await waitForReactControl(page, '[data-testid="auth-register-submit"]')
  await page.getByTestId('auth-register-name').fill(account.displayName)
  await page.getByTestId('auth-register-email').fill(account.email)
  await page.getByTestId('auth-register-password').fill(account.password)
  await page.getByTestId('auth-register-confirm').fill(account.password)
  await page.getByTestId('auth-register-submit').click()
  await page.waitForURL(`${BASE}/struct`, { timeout: 120000 })
  await waitForProjectCenter(page)
}

async function getCurrentUserId(page) {
  const response = await page.request.get(`${BASE}/api/auth/me`)
  check(response.ok(), `GET /api/auth/me failed with ${response.status()}`)
  const body = await response.json()
  const userId = body.user?.id
  check(typeof userId === 'string' && userId, '/api/auth/me must return the current user id')
  return userId
}

async function listProjects(page) {
  const response = await page.request.get(`${BASE}/api/struct-projects`)
  check(response.ok(), `GET /api/struct-projects failed with ${response.status()}`)
  const body = await response.json()
  check(Array.isArray(body.projects), 'GET /api/struct-projects must return a projects array')
  return body.projects
}

async function getProjectGraph(page, projectId) {
  const response = await page.request.get(
    `${BASE}/api/struct-projects/${encodeURIComponent(projectId)}`,
  )
  if (!response.ok()) {
    throw new Error(
      `GET /api/struct-projects/${projectId} failed with ${response.status()}: ${await response.text()}`,
    )
  }
  const body = await response.json()
  check(body.graph?.nodes, `project ${projectId} API response must include a graph`)
  return body.graph
}

async function readLocalGraph(page, userId, projectId) {
  return page.evaluate(
    ({ ownerId, id }) => {
      const key = `struct-user-cache:${ownerId}:struct-project-scene:${id}`
      const raw = window.localStorage.getItem(key)
      if (!raw) return null
      try {
        return JSON.parse(raw)
      } catch {
        return null
      }
    },
    { ownerId: userId, id: projectId },
  )
}

async function waitForSaved(page) {
  const status = page.getByTestId('struct-save-status')
  await status.waitFor({ timeout: 120000 })
  await page.waitForFunction(
    () =>
      document.querySelector('[data-testid="struct-save-status"]')?.textContent?.trim() ===
      '已保存',
    undefined,
    { timeout: 120000 },
  )
}

async function waitForProjectGraph(page, projectId, predicate, message, timeout = 120000) {
  return waitFor(
    page,
    async () => {
      const graph = await getProjectGraph(page, projectId)
      return predicate(graph) ? graph : false
    },
    message,
    { timeout, interval: 300 },
  )
}

async function waitForStableProjectGraph(
  page,
  projectId,
  predicate,
  message,
  timeout = 120000,
  stableMs = 8000,
) {
  let previousSignature = null
  let stableSince = 0
  return waitFor(
    page,
    async () => {
      const graph = await getProjectGraph(page, projectId)
      if (!predicate(graph)) {
        previousSignature = null
        stableSince = 0
        return false
      }
      const signature = graphSignature(graph)
      if (signature !== previousSignature) {
        previousSignature = signature
        stableSince = Date.now()
        return false
      }
      return Date.now() - stableSince >= stableMs ? graph : false
    },
    message,
    { timeout, interval: 300 },
  )
}

async function waitForLocalGraph(page, userId, projectId, predicate, message, timeout = 120000) {
  return waitFor(
    page,
    async () => {
      const graph = await readLocalGraph(page, userId, projectId)
      return graph && predicate(graph) ? graph : false
    },
    message,
    { timeout, interval: 300 },
  )
}

async function waitForWorkspace(page) {
  await page.getByTestId('struct-ribbon').waitFor({ timeout: 120000 })
  await page.locator('canvas').first().waitFor({ state: 'attached', timeout: 120000 })
  await page.waitForFunction(
    () => {
      const canvas = document.querySelector('canvas')
      return Boolean(canvas?.isConnected)
    },
    undefined,
    { timeout: 120000 },
  )
  await waitForSaved(page)
}

async function openIfcImport(page) {
  await page.getByTestId('ribbon-tab-file').click()
  await page.getByTestId('ribbon-cmd-file.ifcImport').click()
  const dialogs = page.getByTestId('struct-ifc-import-dialog')
  await dialogs.waitFor({ timeout: 120000 })
  check((await dialogs.count()) === 1, 'File → Import IFC must open exactly one dialog')
  check((await page.getByRole('dialog').count()) === 1, 'only one modal dialog may be open')
  return dialogs
}

async function uploadIfcAndWaitForReview(page, filePath, fileName) {
  const dialog = await openIfcImport(page)
  const input = dialog.locator('input[type="file"]')
  await input.setInputFiles(filePath)
  await dialog.getByTestId('ifc-import-create').waitFor({ timeout: 120000 })
  const reviewText = await dialog.innerText()
  check(reviewText.includes(fileName), `review must show source file ${fileName}`)
  check(reviewText.includes('节点总数'), 'review must show node count')
  check(reviewText.includes('楼层'), 'review must show level count')
  check(reviewText.includes('导入实体'), 'review must show imported entity count')
  check(
    reviewText.includes('第一阶段不参与结构统计和 analysis-model'),
    'review must state that phase one is excluded from structural statistics and analysis-model',
  )
  return dialog
}

async function createImportedProject(page, dialog) {
  const baselineUrl = page.url()
  const baselineProjectId = projectIdFromUrl(baselineUrl)
  const projectCount = (await listProjects(page)).length
  check(
    page.url() === baselineUrl && projectIdFromUrl(page.url()) === baselineProjectId,
    'IFC review must keep the original project URL',
  )
  check(
    (await listProjects(page)).length === projectCount,
    'IFC review must not create a project before confirmation',
  )
  await dialog.getByTestId('ifc-import-create').click()
  await page.waitForURL(
    (url) =>
      /\/struct\/[^/]+$/.test(url.pathname) &&
      !url.pathname.endsWith('/new') &&
      projectIdFromUrl(url.href) !== baselineProjectId,
    { timeout: 120000 },
  )
  const importedProjectId = projectIdFromUrl(page.url())
  check(importedProjectId !== baselineProjectId, 'IFC import must open a different project')
  await waitForWorkspace(page)
  return importedProjectId
}

async function switchTo2d(page) {
  await page.getByRole('button', { name: '2D', exact: true }).click()
  await page.locator('[data-pascal-viewer-2d]').waitFor({ timeout: 120000 })
  await page.locator('svg[data-pascal-floorplan-2d]').waitFor({ timeout: 120000 })
  await page.waitForTimeout(1200)
}

async function importedFloorplanEntries(page) {
  return page.locator(
    'svg[data-pascal-floorplan-2d] g.floorplan-registry-entry[data-node-id^="imesh_"]',
  )
}

async function selectFirstImportedFloorplanEntry(page) {
  const entries = await importedFloorplanEntries(page)
  const entry = entries.first()
  await entry.waitFor({ timeout: 120000 })
  await page.waitForTimeout(500)
  const box = await entry.boundingBox()
  check(box && box.width > 0 && box.height > 0, 'imported-mesh floorplan entry must have a size')
  const metadata = page.getByTestId('imported-mesh-metadata')
  const attemptedResults = []
  for (const [xRatio, yRatio] of [
    [0.05, 0.95],
    [0.95, 0.95],
    [0.05, 0.05],
    [0.95, 0.05],
    [0.5, 0.5],
  ]) {
    await page.mouse.click(box.x + box.width * xRatio, box.y + box.height * yRatio)
    await page.waitForTimeout(500)
    const inspector = page.locator('[data-editor-inspector]').last()
    if (await inspector.isVisible().catch(() => false)) {
      const expand = inspector.getByRole('button', { name: 'Expand panel', exact: true })
      if (await expand.isVisible().catch(() => false)) await expand.click()
    }
    if (await metadata.isVisible().catch(() => false)) {
      await metadata.waitFor({ timeout: 120000 })
      const nameInput = page.getByRole('textbox', { name: '名称', exact: true })
      const inputId = await nameInput.getAttribute('id')
      check(inputId?.endsWith('-name'), 'IFC inspector name input must identify its node')
      return {
        entry,
        inspector,
        metadata,
        nameInput,
        nodeId: inputId.slice(0, -'-name'.length),
      }
    }
    attemptedResults.push({
      point: [xRatio, yRatio],
      inspectorText: await page
        .locator('[data-editor-inspector]')
        .last()
        .innerText()
        .catch(() => ''),
    })
  }
  throw new Error(
    `could not select an imported-mesh node through the 2D floor plan: ${JSON.stringify({
      box,
      attemptedResults,
    })}`,
  )
}

async function assertCanvasAttached(page) {
  const canvases = page.locator('canvas')
  check((await canvases.count()) > 0, 'workspace must mount a canvas')
  const attached = await canvases.first().evaluate((canvas) => canvas.isConnected)
  check(attached, 'workspace canvas must be attached to the document')
}

function collectGraphState(graph) {
  return { graph, ...graphCounts(graph) }
}

const playwrightRoot = join(homedir(), 'AppData', 'Local', 'ms-playwright')
const bundledChromium = existsSync(playwrightRoot)
  ? readdirSync(playwrightRoot)
      .filter((name) => /^chromium-\d+$/.test(name))
      .sort((left, right) => Number(right.split('-')[1]) - Number(left.split('-')[1]))
      .map((name) => join(playwrightRoot, name, 'chrome-win64', 'chrome.exe'))
      .find(existsSync)
  : undefined
check(bundledChromium, 'bundled Playwright Chromium was not found')

const browser = await chromium.launch({ executablePath: bundledChromium, headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const browserErrors = []
let runtimePhase = 'normal'

page.on('console', (message) => {
  if (message.type() !== 'error') return
  browserErrors.push({
    phase: runtimePhase,
    kind: 'console',
    text: message.text(),
    url: message.location().url,
  })
})
page.on('pageerror', (error) => {
  browserErrors.push({
    phase: runtimePhase,
    kind: 'pageerror',
    text: String(error),
    url: page.url(),
  })
})

try {
  check(existsSync(ifc2x3Fixture), `IFC2X3 fixture not found: ${ifc2x3Fixture}`)
  check(existsSync(ifc4Fixture), `IFC4 fixture not found: ${ifc4Fixture}`)

  await registerAccount(page)
  const userId = await getCurrentUserId(page)
  await page.evaluate(() => {
    window.localStorage.setItem('pascal-editor:inspector-expanded', 'true')
  })

  await page.getByTestId('struct-new-project').click()
  await page.waitForURL(`${BASE}/struct/new`, { timeout: 120000 })
  await page.getByRole('heading', { name: '新建结构工程' }).waitFor({ timeout: 120000 })
  await page.locator('#project-name').fill(baselineName)
  await page.locator('#project-code').fill(`IFC-${runId}`)
  await page.getByRole('button', { name: '创建工程', exact: true }).click()
  await page.waitForURL(/\/struct\/struct-/, { timeout: 120000 })
  await waitForWorkspace(page)

  const baselineProjectId = projectIdFromUrl(page.url())
  report.baselineProjectId = baselineProjectId
  const baselineGraph = await waitForStableProjectGraph(
    page,
    baselineProjectId,
    (graph) => Object.keys(graph.nodes ?? {}).length > 0,
    'baseline project graph was not saved',
  )
  const baselineLocalGraph = await waitForLocalGraph(
    page,
    userId,
    baselineProjectId,
    (graph) => Object.keys(graph.nodes ?? {}).length > 0,
    'baseline project graph was not cached locally',
  )
  const baselineSignature = graphSignature(baselineGraph)
  check(
    graphSignature(baselineLocalGraph) === baselineSignature,
    'baseline API and local graph signatures must match after autosave',
  )
  check(
    (await listProjects(page)).length === 1,
    'baseline setup must start with exactly one project',
  )

  let dialog = await uploadIfcAndWaitForReview(page, ifc2x3Fixture, '01-duplex.ifc')
  await page.screenshot({ path: screenshots.ifc2x3Review })
  const ifc2x3ProjectId = await createImportedProject(page, dialog)
  report.importedProjectId = ifc2x3ProjectId
  check(page.url().endsWith(`/struct/${ifc2x3ProjectId}`), 'IFC2X3 must open its new project route')
  await assertCanvasAttached(page)
  const ifc2x3Graph = await waitForStableProjectGraph(
    page,
    ifc2x3ProjectId,
    (graph) => {
      const counts = graphCounts(graph)
      return counts.nodeCount > 0 && counts.levelCount > 0 && counts.importedMeshCount > 0
    },
    'IFC2X3 project graph must contain nodes, levels and imported meshes',
  )
  const ifc2x3LocalGraph = await waitForLocalGraph(
    page,
    userId,
    ifc2x3ProjectId,
    (graph) => graphCounts(graph).importedMeshCount > 0,
    'IFC2X3 local graph must contain imported meshes',
  )
  const ifc2x3State = collectGraphState(ifc2x3Graph)
  check(
    graphCounts(ifc2x3LocalGraph).nodeCount === ifc2x3State.nodeCount,
    'IFC2X3 API and local node counts must match',
  )
  assertImportedHierarchy(ifc2x3Graph, 'IFC2X3 project')
  report.ifc2x3Imported = true

  await switchTo2d(page)
  const ifc2x3Entries = await importedFloorplanEntries(page)
  await ifc2x3Entries.first().waitFor({ timeout: 120000 })
  check(
    (await ifc2x3Entries.count()) > 0,
    'IFC2X3 floor plan must render real imported-mesh geometry',
  )
  const renderedIfc2x3Ids = await ifc2x3Entries.evaluateAll((elements) =>
    elements.map((element) => element.getAttribute('data-node-id')).filter(Boolean),
  )
  check(
    renderedIfc2x3Ids.every((id) => ifc2x3Graph.nodes[id]?.type === 'imported-mesh'),
    'every rendered IFC2X3 imesh group must map to an imported-mesh graph node',
  )

  const selection = await selectFirstImportedFloorplanEntry(page)
  const metadata = selection.metadata
  await page.getByText('IFC 导入实体', { exact: true }).waitFor({ timeout: 120000 })
  check(
    (await metadata.locator('input, textarea, select, [contenteditable="true"]').count()) === 0,
    'IFC source metadata must be read-only',
  )
  check(
    (await page
      .getByText('几何按 IFC 保留；截面和结构计算参数暂不可编辑。', {
        exact: true,
      })
      .count()) === 1,
    'IFC panel must explain which fields remain non-editable',
  )

  const renamedNodeId = selection.nodeId
  check(renamedNodeId?.startsWith('imesh_'), 'selected IFC entity must have an imesh node id')
  report.renamedNodeId = renamedNodeId
  const renamedValue = `IFC 验收梁 ${runId}`
  const nameInput = selection.nameInput
  check(await nameInput.isEnabled(), 'imported-mesh name input must be editable')
  await nameInput.fill(renamedValue)
  await waitForProjectGraph(
    page,
    ifc2x3ProjectId,
    (graph) => graph.nodes[renamedNodeId]?.name === renamedValue,
    'renamed IFC node must autosave to the project graph',
  )
  await waitForLocalGraph(
    page,
    userId,
    ifc2x3ProjectId,
    (graph) => graph.nodes[renamedNodeId]?.name === renamedValue,
    'renamed IFC node must persist to localStorage',
  )

  await selection.inspector.getByRole('button', { name: '隐藏', exact: true }).click()
  await waitForProjectGraph(
    page,
    ifc2x3ProjectId,
    (graph) => graph.nodes[renamedNodeId]?.visible === false,
    'hidden state must autosave to the project graph',
  )
  await waitForLocalGraph(
    page,
    userId,
    ifc2x3ProjectId,
    (graph) => graph.nodes[renamedNodeId]?.visible === false,
    'hidden state must persist to localStorage',
  )
  await selection.inspector.getByRole('button', { name: '显示', exact: true }).click()
  await waitForProjectGraph(
    page,
    ifc2x3ProjectId,
    (graph) => graph.nodes[renamedNodeId]?.visible === true,
    'shown state must autosave to the project graph',
  )
  await waitForLocalGraph(
    page,
    userId,
    ifc2x3ProjectId,
    (graph) => graph.nodes[renamedNodeId]?.visible === true,
    'shown state must persist to localStorage',
  )
  await page.screenshot({ path: screenshots.ifc2x3Panel })

  const moveButton = selection.inspector.getByTestId('imported-mesh-move')
  check(await moveButton.isEnabled(), 'imported-mesh move button must be enabled')
  await moveButton.click()
  await page.locator('[data-hud-title="Move imported mesh"]').waitFor({ timeout: 120000 })
  await page.keyboard.press('Escape')
  await page.waitForFunction(
    () => !document.querySelector('[data-hud-title="Move imported mesh"]'),
    undefined,
    { timeout: 120000 },
  )
  await selectFirstImportedFloorplanEntry(page)

  await waitForSaved(page)
  const beforeReload = await waitForProjectGraph(
    page,
    ifc2x3ProjectId,
    () => true,
    'IFC2X3 graph must be available before reload',
  )
  const beforeReloadCounts = graphCounts(beforeReload)
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 120000 })
  await waitForWorkspace(page)
  const afterReload = await waitForProjectGraph(
    page,
    ifc2x3ProjectId,
    (graph) =>
      graphCounts(graph).nodeCount === beforeReloadCounts.nodeCount &&
      graph.nodes[renamedNodeId]?.name === renamedValue &&
      graph.nodes[renamedNodeId]?.visible === true,
    'IFC2X3 graph edits must persist after reload',
  )
  const afterReloadLocal = await waitForLocalGraph(
    page,
    userId,
    ifc2x3ProjectId,
    (graph) =>
      graphCounts(graph).nodeCount === beforeReloadCounts.nodeCount &&
      graph.nodes[renamedNodeId]?.name === renamedValue &&
      graph.nodes[renamedNodeId]?.visible === true,
    'IFC2X3 reloaded graph must persist locally',
  )
  const afterReloadCounts = graphCounts(afterReload)
  check(
    afterReloadCounts.nodeCount === beforeReloadCounts.nodeCount &&
      afterReloadCounts.importedMeshCount === beforeReloadCounts.importedMeshCount &&
      afterReloadCounts.levelCount === beforeReloadCounts.levelCount,
    'IFC2X3 node, imported-mesh and level counts must survive reload',
  )
  check(
    graphCounts(afterReloadLocal).nodeCount === afterReloadCounts.nodeCount,
    'IFC2X3 API and local node counts must match after reload',
  )
  assertImportedHierarchy(afterReload, 'reloaded IFC2X3 project')
  report.nodeCount = afterReloadCounts.nodeCount
  report.importedMeshCount = afterReloadCounts.importedMeshCount
  report.levelCount = afterReloadCounts.levelCount
  await switchTo2d(page)
  const reloadedEntries = await importedFloorplanEntries(page)
  await reloadedEntries.first().waitFor({ timeout: 120000 })
  check(
    (await reloadedEntries.count()) > 0,
    'IFC2X3 imported geometry must remain in 2D after reload',
  )
  report.persistedAfterReload = true
  await page.screenshot({ path: screenshots.ifc2x3Reloaded })

  await page.getByTestId('struct-project-center-link').click()
  await page.waitForURL(`${BASE}/struct`, { timeout: 120000 })
  await waitForProjectCenter(page)
  const baselineCard = page.locator(
    `[data-testid="struct-project-card"][data-project-id="${baselineProjectId}"]`,
  )
  await baselineCard.waitFor({ timeout: 120000 })
  await baselineCard.getByTestId('struct-project-open').click()
  const openVersionDialog = page.getByTestId('struct-project-open-dialog')
  if (await openVersionDialog.isVisible().catch(() => false)) {
    await openVersionDialog.getByTestId('struct-project-open-cloud').click()
  }
  await page.waitForURL(
    new RegExp(
      `/struct/${baselineProjectId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:\\?source=cloud)?$`,
    ),
    { timeout: 120000 },
  )
  await waitForWorkspace(page)
  const reopenedBaseline = await getProjectGraph(page, baselineProjectId)
  const reopenedBaselineLocal = await waitForLocalGraph(
    page,
    userId,
    baselineProjectId,
    () => true,
    'baseline local graph must be available after import',
  )
  check(
    graphSignature(reopenedBaseline) === baselineSignature,
    'IFC import must not change the baseline project graph',
  )
  check(
    graphSignature(reopenedBaselineLocal) === baselineSignature,
    'IFC import must not change the baseline local cache',
  )
  report.baselineUnchanged = true

  dialog = await uploadIfcAndWaitForReview(page, ifc4Fixture, '10-sample-house.ifc')
  const ifc4ProjectId = await createImportedProject(page, dialog)
  check(ifc4ProjectId !== baselineProjectId, 'IFC4 must not reuse the baseline project')
  check(ifc4ProjectId !== ifc2x3ProjectId, 'IFC4 must create an independent project')
  await assertCanvasAttached(page)
  const ifc4Graph = await waitForStableProjectGraph(
    page,
    ifc4ProjectId,
    (graph) => {
      const counts = graphCounts(graph)
      return (
        counts.nodeCount > 0 &&
        counts.levelCount > 0 &&
        counts.importedMeshCount > 0 &&
        counts.nativeGeometryCount > 0
      )
    },
    'IFC4 project graph must contain levels, imported meshes and native Pascal geometry',
  )
  const ifc4State = graphCounts(ifc4Graph)
  assertImportedHierarchy(ifc4Graph, 'IFC4 project')
  check(ifc4State.importedMeshCount > 0, 'IFC4 graph must retain imported fallback meshes')
  check(ifc4State.nativeGeometryCount > 0, 'IFC4 graph must include native Pascal geometry')
  report.ifc4Imported = true
  await page.screenshot({ path: screenshots.ifc4Workspace })

  const projectCountBeforeInvalid = (await listProjects(page)).length
  const urlBeforeInvalid = page.url()
  dialog = await openIfcImport(page)
  await dialog.locator('input[type="file"]').setInputFiles({
    name: 'not-an-ifc.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('not an IFC file'),
  })
  const invalidAlert = dialog.getByRole('alert')
  await invalidAlert.waitFor({ timeout: 120000 })
  check(
    (await invalidAlert.innerText()).includes('仅支持 .ifc 文件'),
    'invalid extension must show the expected alert',
  )
  check(page.url() === urlBeforeInvalid, 'invalid extension must not change the project URL')
  await page.waitForTimeout(1000)
  check(
    (await listProjects(page)).length === projectCountBeforeInvalid,
    'invalid extension must not create a project',
  )
  await page.screenshot({ path: screenshots.invalidFile })
  report.invalidFileBlocked = true
  await dialog.getByRole('button', { name: '取消', exact: true }).click()

  const projectCountBeforeCorrupt = (await listProjects(page)).length
  const urlBeforeCorrupt = page.url()
  runtimePhase = 'corrupt'
  dialog = await openIfcImport(page)
  await dialog.locator('input[type="file"]').setInputFiles(corruptFixture)
  const corruptAlert = dialog.getByRole('alert')
  await corruptAlert.waitFor({ timeout: 120000 })
  check(
    (await corruptAlert.innerText()).trim().length > 0,
    'corrupt IFC must show a non-empty parse alert',
  )
  check(page.url() === urlBeforeCorrupt, 'corrupt IFC must not change the project URL')
  await page.waitForTimeout(1000)
  check(
    (await listProjects(page)).length === projectCountBeforeCorrupt,
    'corrupt IFC must not create a project',
  )
  await page.screenshot({ path: screenshots.corruptFile })
  report.corruptFileBlocked = true
  await dialog.getByRole('button', { name: '取消', exact: true }).click()
  runtimePhase = 'normal'

  const knownAssetErrors = []
  const corruptParseErrors = []
  for (const error of browserErrors) {
    const searchable = `${error.text} ${error.url}`
    if (knownMissingAsset.test(searchable)) {
      knownAssetErrors.push(error)
      continue
    }
    if (
      error.phase === 'corrupt' &&
      /(?:ifc|web-ifc|parse|parser|schema|step|malformed|unexpected end|invalid model)/i.test(
        searchable,
      )
    ) {
      corruptParseErrors.push(error)
      continue
    }
    report.consoleErrors.push(error)
  }

  report.corruptFixturePath = corruptFixture
  report.ifc4ProjectId = ifc4ProjectId
  report.ifc4NodeCount = ifc4State.nodeCount
  report.ifc4ImportedMeshCount = ifc4State.importedMeshCount
  report.ifc4NativeGeometryCount = ifc4State.nativeGeometryCount
  report.ifc4LevelCount = ifc4State.levelCount
  report.filteredKnownAssetErrors = knownAssetErrors
  report.filteredCorruptParseErrors = corruptParseErrors
  report.screenshots = screenshots
  report.browserConsoleEventCount = browserErrors.length

  check(
    report.consoleErrors.length === 0,
    `unexpected browser console/page errors: ${JSON.stringify(report.consoleErrors)}`,
  )
  console.log(JSON.stringify(report, null, 2))
} catch (cause) {
  report.corruptFixturePath = corruptFixture
  report.screenshots = screenshots
  report.browserConsoleEvents = browserErrors
  report.error = cause instanceof Error ? (cause.stack ?? cause.message) : String(cause)
  console.error(JSON.stringify(report, null, 2))
  process.exitCode = 1
} finally {
  await browser.close()
}
