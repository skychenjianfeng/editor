# StructWeb IFC Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a production IFC import flow to StructWeb that converts IFC2X3/IFC4 into a new editable StructWeb project.

**Architecture:** Reuse `@pascal-app/ifc-converter` in the browser, serve WebIFC WASM from the editor app, normalize the converted scene into a StructWeb project graph, then create a cloud project and open the existing 2D/3D editor. Keep analysis-model and `structural-member` mapping out of phase one.

**Tech Stack:** Next.js 16, React 19, TypeScript, Bun tests, Zustand, `@pascal-app/ifc-converter`, `web-ifc`, Playwright.

## Global Constraints

- IFC2X3 and IFC4 must import.
- Import creates a new StructWeb project and must not modify the currently open project.
- Preserve IFC metadata including `ifcType`, `expressID`, `globalId`, properties and materials.
- Native Pascal nodes remain editable through existing inspector capabilities.
- Unsupported IFC elements remain `imported-mesh` nodes.
- Imported content must not enter structural statistics or analysis-model in phase one.
- Failed conversion must not create an empty or corrupted project.
- Do not add server-side conversion or background queues.
- Use exact file staging lists when committing so unrelated dirty worktree changes are not included.

---

## File Structure

Create:

- `apps/editor/scripts/copy-web-ifc-wasm.mjs` — copy WebIFC binaries into editor public assets.
- `apps/editor/lib/struct/ifc-import.ts` — pure graph normalization, summary and project preparation.
- `apps/editor/lib/struct/ifc-import.test.ts` — graph normalization and project preparation tests.
- `apps/editor/lib/struct/ifc-runtime-assets.test.ts` — verifies required WASM assets are served.
- `apps/editor/components/struct/struct-ifc-import-dialog.tsx` — file picker, drop zone, conversion state, preview and project creation.
- `apps/editor/components/struct/struct-ifc-import-dialog.test.tsx` — dialog state and review UI tests.
- `packages/nodes/src/imported-mesh/source.ts` — normalized IFC source metadata for the inspector.
- `packages/nodes/src/imported-mesh/source.test.ts` — source metadata extraction.
- `packages/nodes/src/imported-mesh/panel.tsx` — imported-mesh inspector panel.
- `packages/nodes/src/imported-mesh/panel.test.tsx` — imported entity presentation and edit affordance.
- `scripts/verify-struct-ifc-import.mjs` — real-browser IFC import/edit/reload acceptance.

Modify:

- `apps/editor/package.json` — dependencies/scripts for converter and WASM assets.
- `apps/editor/next.config.ts` — transpile `@pascal-app/ifc-converter`.
- `bun.lock` — dependency lock after install.
- `apps/editor/components/struct/struct-store.ts` — IFC dialog open state.
- `apps/editor/components/struct/struct-store.test.ts` — dialog state regression.
- `apps/editor/components/struct/command-defs.tsx` — executable `file.ifcImport`.
- `apps/editor/components/struct/ribbon-config.ts` — 文件 tab with import command.
- `apps/editor/components/struct/struct-shell.tsx` — mount import dialog.
- `packages/nodes/src/imported-mesh/definition.ts` — movable capability and custom panel.
- `packages/nodes/src/imported-mesh/definition.test.ts` — capability/panel registration.
- `docs/STRUCT-PROTOTYPE.md` — user workflow and limitations.
- `docs/design/web-fea/CURRENT_STATE.md` — implementation status.
- `docs/design/web-fea/DESIGN_CHANGELOG.md` — feature changelog entry.

---

### Task 1: Add IFC package and WASM runtime assets

**Files:**
- Create: `apps/editor/scripts/copy-web-ifc-wasm.mjs`
- Create: `apps/editor/lib/struct/ifc-runtime-assets.test.ts`
- Modify: `apps/editor/package.json`
- Modify: `apps/editor/next.config.ts`
- Modify: `bun.lock`

**Interfaces:**
- Consumes: `web-ifc` package files `web-ifc.wasm`, `web-ifc-mt.wasm`, `web-ifc-node.wasm`.
- Produces: public URLs `/web-ifc.wasm`, `/web-ifc-mt.wasm`, `/web-ifc-node.wasm`, consumed by `convertIfcToPascal(..., { wasmPath: '/' })`.

- [ ] **Step 1: Add app dependencies and script hooks**

In `apps/editor/package.json`, add:

```json
"predev": "node scripts/copy-web-ifc-wasm.mjs",
"prebuild": "node scripts/copy-web-ifc-wasm.mjs",
"postinstall": "node scripts/copy-web-ifc-wasm.mjs",
"dependencies": {
  "@pascal-app/ifc-converter": "*",
  "web-ifc": "^0.0.78"
}
```

Keep all existing scripts and dependencies.

Add `'@pascal-app/ifc-converter'` to `transpilePackages` in `apps/editor/next.config.ts`.

- [ ] **Step 2: Write the failing asset test**

Create `apps/editor/lib/struct/ifc-runtime-assets.test.ts`:

```ts
import { describe, expect, test } from 'bun:test'
import { existsSync, statSync } from 'node:fs'
import { join } from 'node:path'

const publicDir = join(import.meta.dir, '../../public')

describe('IFC runtime assets', () => {
  test('copies every WebIFC binary into the editor public directory', () => {
    for (const name of ['web-ifc.wasm', 'web-ifc-mt.wasm', 'web-ifc-node.wasm']) {
      const path = join(publicDir, name)
      expect(existsSync(path)).toBe(true)
      expect(statSync(path).size).toBeGreaterThan(0)
    }
  })
})
```

- [ ] **Step 3: Run the asset test and verify it fails**

Run:

```powershell
bun test apps/editor/lib/struct/ifc-runtime-assets.test.ts
```

Expected: FAIL because one or more WASM files are absent.

- [ ] **Step 4: Create the copy script**

Create `apps/editor/scripts/copy-web-ifc-wasm.mjs` by adapting the existing `apps/ifc-converter/scripts/copy-web-ifc-wasm.mjs`. Preserve its upward node_modules search, size-based idempotence and `web-ifc.wasm`, `web-ifc-mt.wasm`, `web-ifc-node.wasm` list. Set:

```js
const publicDir = join(scriptDir, '..', 'public')
```

Print `[editor:ifc] copied <name>` and fail the process if any source/destination copy fails.

- [ ] **Step 5: Install and copy assets**

Run:

```powershell
bun install
bun run --cwd apps/editor predev
```

Expected: installation succeeds and all three WASM files appear under `apps/editor/public/`.

- [ ] **Step 6: Run the asset test and verify it passes**

Run:

```powershell
bun test apps/editor/lib/struct/ifc-runtime-assets.test.ts
bun run --cwd apps/editor check-types
```

Expected: test passes; type check passes.

- [ ] **Step 7: Commit**

```powershell
git add -- apps/editor/package.json apps/editor/next.config.ts apps/editor/scripts/copy-web-ifc-wasm.mjs apps/editor/lib/struct/ifc-runtime-assets.test.ts bun.lock
git commit -m "feat(struct): add IFC runtime assets"
```

---

### Task 2: Normalize converted IFC into a StructWeb project graph

**Files:**
- Create: `apps/editor/lib/struct/ifc-import.ts`
- Create: `apps/editor/lib/struct/ifc-import.test.ts`

**Interfaces:**
- Consumes: `SceneGraph`, `SiteNode`, `BuildingNode`, `LevelNode`, `createStructProjectMeta`, `withStructProjectMetadata`.
- Produces:

```ts
export type IfcGraphSummary = {
  nodeCount: number
  levelCount: number
  importedMeshCount: number
  typeCounts: Record<string, number>
  sourceFile: string
}

export type IfcProjectImport = {
  meta: StructProjectMeta
  graph: SceneGraph
  summary: IfcGraphSummary
}

export function normalizeIfcSceneGraph(graph: SceneGraph): SceneGraph
export function summarizeIfcGraph(graph: SceneGraph, sourceFile: string): IfcGraphSummary
export function prepareIfcProjectImport(input: {
  graph: SceneGraph
  projectName: string
  sourceFile: string
  projectId?: string
  now?: Date
}): IfcProjectImport
```

- [ ] **Step 1: Write failing hierarchy and summary tests**

Create `apps/editor/lib/struct/ifc-import.test.ts` with these tests:

```ts
import { describe, expect, test } from 'bun:test'
import {
  BuildingNode,
  ImportedMeshNode,
  LevelNode,
  SiteNode,
  type AnyNode,
  type AnyNodeId,
} from '@pascal-app/core'
import type { SceneGraph } from '@pascal-app/editor'
import { normalizeIfcSceneGraph, prepareIfcProjectImport, summarizeIfcGraph } from './ifc-import'

describe('IFC import graph preparation', () => {
  test('wraps building roots in an empty root site', () => {
    const building = BuildingNode.parse({ id: 'building_ifc' })
    const level = LevelNode.parse({ id: 'level_ifc', parentId: building.id, level: 0 })
    const graph = {
      nodes: {
        [building.id]: { ...building, children: [level.id] },
        [level.id]: level,
      },
      rootNodeIds: [building.id],
    } as unknown as SceneGraph

    const normalized = normalizeIfcSceneGraph(graph)
    const site = Object.values(normalized.nodes).find((node) => node.type === 'site')

    expect(site?.type).toBe('site')
    expect(site?.type === 'site' ? site.polygon.points : null).toEqual([])
    expect(site?.children).toContain(building.id)
    expect(normalized.rootNodeIds).toEqual([site?.id])
    expect(normalized.nodes[building.id]?.parentId).toBe(site?.id)
  })

  test('creates a root site container for multiple existing sites', () => {
    const first = SiteNode.parse({ id: 'site_first', polygon: { type: 'polygon', points: [] } })
    const second = SiteNode.parse({ id: 'site_second', polygon: { type: 'polygon', points: [] } })
    const graph = {
      nodes: { [first.id]: first, [second.id]: second },
      rootNodeIds: [first.id, second.id],
    } as unknown as SceneGraph

    const normalized = normalizeIfcSceneGraph(graph)
    const root = normalized.nodes[normalized.rootNodeIds[0]!]

    expect(root?.type).toBe('site')
    expect(root?.children).toEqual([first.id, second.id])
    expect(normalized.nodes[first.id]?.parentId).toBe(root?.id)
    expect(normalized.nodes[second.id]?.parentId).toBe(root?.id)
  })

  test('summarizes levels and imported entities', () => {
    const level = LevelNode.parse({ id: 'level_summary', level: 0 })
    const mesh = ImportedMeshNode.parse({
      id: 'imesh_summary',
      parentId: level.id,
      primitives: [],
    })
    const graph = {
      nodes: {
        [level.id]: { ...level, children: [mesh.id] },
        [mesh.id]: mesh,
      },
      rootNodeIds: [level.id],
    } as unknown as SceneGraph

    expect(summarizeIfcGraph(graph, 'model.ifc')).toEqual({
      nodeCount: 2,
      levelCount: 1,
      importedMeshCount: 1,
      typeCounts: { level: 1, 'imported-mesh': 1 },
      sourceFile: 'model.ifc',
    })
  })

  test('adds StructWeb metadata without dropping IFC metadata', () => {
    const site = SiteNode.parse({
      id: 'site_meta',
      polygon: { type: 'polygon', points: [] },
      metadata: { ifcType: 'IFCSITE', globalId: 'guid-site' },
    })
    const input = {
      graph: { nodes: { [site.id]: site }, rootNodeIds: [site.id] } as unknown as SceneGraph,
      projectName: 'Imported House',
      sourceFile: 'house.ifc',
      projectId: 'struct-ifc-house',
      now: new Date('2026-10-23T00:00:00Z'),
    }

    const prepared = prepareIfcProjectImport(input)
    const preparedSite = Object.values(prepared.graph.nodes).find((node) => node.type === 'site')

    expect(prepared.meta.id).toBe('struct-ifc-house')
    expect(prepared.meta.startMode).toBe('import')
    expect(preparedSite?.metadata).toMatchObject({
      ifcType: 'IFCSITE',
      globalId: 'guid-site',
      structProjectId: 'struct-ifc-house',
    })
  })
})
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
bun test apps/editor/lib/struct/ifc-import.test.ts
```

Expected: FAIL because `./ifc-import` does not exist.

- [ ] **Step 3: Implement normalization and project preparation**

Implement `normalizeIfcSceneGraph` with a deep clone, preserving original nodes. Determine usable root sites from `rootNodeIds`; create a `SiteNode` with `polygon: { type: 'polygon', points: [] }` when none or more than one exists. Update root-site children and child `parentId` symmetrically. If a root site exists, keep it and normalize missing children/parent links.

Implement `summarizeIfcGraph` as a single pass over `graph.nodes`.

Implement `prepareIfcProjectImport` as:

```ts
const meta = createStructProjectMeta(
  {
    ...DEFAULT_STRUCT_PROJECT_DRAFT,
    name: input.projectName.trim() || input.sourceFile.replace(/\.ifc$/i, ''),
    startMode: 'import',
  },
  { id: input.projectId, now: input.now },
)
const normalized = normalizeIfcSceneGraph(input.graph)
const graph = withStructProjectMetadata(normalized, meta)
return { meta, graph, summary: summarizeIfcGraph(graph, input.sourceFile) }
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```powershell
bun test apps/editor/lib/struct/ifc-import.test.ts
bun run --cwd apps/editor check-types
bunx biome check apps/editor/lib/struct/ifc-import.ts apps/editor/lib/struct/ifc-import.test.ts
```

Expected: all pass.

- [ ] **Step 5: Commit**

```powershell
git add -- apps/editor/lib/struct/ifc-import.ts apps/editor/lib/struct/ifc-import.test.ts
git commit -m "feat(struct): prepare IFC project graphs"
```

---

### Task 3: Add IFC import command, Ribbon entry and dialog state

**Files:**
- Modify: `apps/editor/components/struct/struct-store.ts`
- Modify: `apps/editor/components/struct/struct-store.test.ts`
- Modify: `apps/editor/components/struct/command-defs.tsx`
- Modify: `apps/editor/components/struct/ribbon-config.ts`
- Modify: `apps/editor/components/struct/struct-shell.tsx`
- Create: `apps/editor/components/struct/struct-ifc-import-dialog.tsx` with an initial placeholder export in this task

**Interfaces:**
- Consumes: `useStructStore.openIfcImport()`.
- Produces: `ifcImportOpen`, `openIfcImport()`, `closeIfcImport()` and command ID `file.ifcImport`.

- [ ] **Step 1: Write a failing store test**

Append to `apps/editor/components/struct/struct-store.test.ts`:

```ts
test('opens and closes the IFC import workflow from commands', () => {
  const store = useStructStore.getState()
  store.openIfcImport()
  expect(useStructStore.getState().ifcImportOpen).toBe(true)
  store.closeIfcImport()
  expect(useStructStore.getState().ifcImportOpen).toBe(false)
})
```

Ensure the test imports `test` and `useStructStore` using the file's existing conventions.

- [ ] **Step 2: Run the store test and verify it fails**

Run:

```powershell
bun test apps/editor/components/struct/struct-store.test.ts
```

Expected: FAIL because `openIfcImport` is undefined.

- [ ] **Step 3: Add store state and lifecycle**

Add to `StructStore`:

```ts
ifcImportOpen: boolean
openIfcImport: () => void
closeIfcImport: () => void
```

Initial/default/reset values are `false`. `closeAllPanels()` also closes this dialog. Implement:

```ts
openIfcImport: () => set({ ifcImportOpen: true }),
closeIfcImport: () => set({ ifcImportOpen: false }),
```

- [ ] **Step 4: Add the executable command**

Import an appropriate `FileUp` or `Upload` icon in `command-defs.tsx`. Add to `BASE_STRUCT_COMMANDS`:

```tsx
{
  id: 'file.ifcImport',
  label: '导入 IFC',
  group: '文件',
  icon: <Upload className="h-4 w-4" />,
  keywords: ['ifc', 'import', 'open', '导入', 'BIM'],
  aliases: ['ifc', 'import-ifc'],
  usage: '打开 IFC2X3/IFC4 文件并创建一个新的可编辑 StructWeb 工程',
  execute: () => useStructStore.getState().openIfcImport(),
  preserveEditorContext: true,
}
```

Add a `file` tab before the existing model tab in `RIBBON_TABS`:

```ts
{
  id: 'file',
  label: '文件',
  groups: [
    {
      id: 'file.project',
      label: '项目',
      items: [large('file.ifcImport')],
    },
  ],
}
```

- [ ] **Step 5: Mount the dialog shell**

Create the initial `struct-ifc-import-dialog.tsx`:

```tsx
'use client'

import { useStructStore } from './struct-store'

export function StructIfcImportDialog() {
  const open = useStructStore((state) => state.ifcImportOpen)
  if (!open) return null
  return <div data-testid="struct-ifc-import-dialog">IFC import</div>
}
```

Import and render `<StructIfcImportDialog />` beside the other Struct dialogs in `struct-shell.tsx`.

- [ ] **Step 6: Run tests and verify they pass**

Run:

```powershell
bun test apps/editor/components/struct/struct-store.test.ts
bun run --cwd apps/editor check-types
bunx biome check apps/editor/components/struct/struct-store.ts apps/editor/components/struct/struct-store.test.ts apps/editor/components/struct/command-defs.tsx apps/editor/components/struct/ribbon-config.ts apps/editor/components/struct/struct-shell.tsx apps/editor/components/struct/struct-ifc-import-dialog.tsx
```

Expected: all pass.

- [ ] **Step 7: Commit**

```powershell
git add -- apps/editor/components/struct/struct-store.ts apps/editor/components/struct/struct-store.test.ts apps/editor/components/struct/command-defs.tsx apps/editor/components/struct/ribbon-config.ts apps/editor/components/struct/struct-shell.tsx apps/editor/components/struct/struct-ifc-import-dialog.tsx
git commit -m "feat(struct): add IFC import command"
```

---

### Task 4: Build the IFC import dialog and conversion workflow

**Files:**
- Modify: `apps/editor/components/struct/struct-ifc-import-dialog.tsx`
- Create: `apps/editor/components/struct/struct-ifc-import-dialog.test.tsx`

**Interfaces:**
- Consumes: `convertIfcToPascal`, `prepareIfcProjectImport`, `createCloudStructProject`.
- Produces: `IfcImportDialogView` with explicit props and `StructIfcImportDialog` production wrapper.

```ts
export type IfcImportViewState =
  | { phase: 'idle' }
  | { phase: 'reading' | 'converting'; fileName: string; message: string; percent: number }
  | { phase: 'review'; fileName: string; projectName: string; summary: IfcGraphSummary }
  | { phase: 'creating'; fileName: string; projectName: string; summary: IfcGraphSummary }
  | { phase: 'error'; fileName: string | null; message: string }
```

- [ ] **Step 1: Write failing presentational tests**

Create `struct-ifc-import-dialog.test.tsx` using the existing react-test-renderer setup pattern:

```tsx
import { describe, expect, test } from 'bun:test'
import { act, create } from 'react-test-renderer'
import { IfcImportDialogView, type IfcImportViewState } from './struct-ifc-import-dialog'

function render(state: IfcImportViewState) {
  let renderer!: ReturnType<typeof create>
  act(() => {
    renderer = create(
      <IfcImportDialogView
        state={state}
        onChooseFile={() => {}}
        onDropFile={() => {}}
        onProjectNameChange={() => {}}
        onConfirm={() => {}}
        onCancel={() => {}}
        onRetry={() => {}}
      />,
    )
  })
  return renderer
}

describe('IFC import dialog view', () => {
  test('offers only IFC files when idle', () => {
    const renderer = render({ phase: 'idle' })
    const input = renderer.root.findByType('input')
    expect(input.props.accept).toContain('.ifc')
  })

  test('shows conversion progress', () => {
    const renderer = render({
      phase: 'converting',
      fileName: 'house.ifc',
      message: 'Processing walls...',
      percent: 60,
    })
    expect(JSON.stringify(renderer.toJSON())).toContain('60%')
    expect(JSON.stringify(renderer.toJSON())).toContain('Processing walls')
  })

  test('shows review counts and enables create', () => {
    const renderer = render({
      phase: 'review',
      fileName: 'house.ifc',
      projectName: 'House',
      summary: {
        nodeCount: 12,
        levelCount: 2,
        importedMeshCount: 3,
        typeCounts: { wall: 4, slab: 2 },
        sourceFile: 'house.ifc',
      },
    })
    const text = JSON.stringify(renderer.toJSON())
    expect(text).toContain('12')
    expect(text).toContain('2 层')
    expect(text).toContain('3')
  })
})
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
bun test apps/editor/components/struct/struct-ifc-import-dialog.test.tsx
```

Expected: FAIL because the view and state type are absent.

- [ ] **Step 3: Implement the presentational view**

Build `IfcImportDialogView` with:

- Modal overlay and accessible dialog semantics.
- Hidden `<input type="file" accept=".ifc,application/x-step">`.
- Drop handlers accepting only names ending in `.ifc`.
- Project name input in review/creating states.
- Progress bar using `percent`.
- Summary cards for node count, level count and imported-mesh count.
- Type counts displayed as chips.
- Buttons: 选择文件, 取消, 重新选择, 创建工程.
- Error text with `role="alert"`.
- A persistent notice: `第一阶段不参与结构统计和 analysis-model`.

- [ ] **Step 4: Implement the conversion wrapper**

Use a file-sequenced cancellation guard:

```ts
const runIdRef = useRef(0)
const runId = ++runIdRef.current
const result = await convertIfcToPascal(new Uint8Array(buffer), (message, percent) => {
  if (runId === runIdRef.current) {
    setState({ phase: 'converting', fileName: file.name, message, percent })
  }
}, { wasmPath: '/' })
```

After conversion, call `prepareIfcProjectImport`. Reject graphs whose `nodeCount === 0` or which contain no renderable geometry.

On confirm:

```ts
await createCloudStructProject(meta, graph)
router.push(`/struct/${encodeURIComponent(meta.id)}`)
```

On cancel, increment `runIdRef`, close the store dialog and clear conversion state.

- [ ] **Step 5: Run tests and verify they pass**

Run:

```powershell
bun test apps/editor/components/struct/struct-ifc-import-dialog.test.tsx
bun run --cwd apps/editor check-types
bunx biome check apps/editor/components/struct/struct-ifc-import-dialog.tsx apps/editor/components/struct/struct-ifc-import-dialog.test.tsx
```

Expected: all pass.

- [ ] **Step 6: Commit**

```powershell
git add -- apps/editor/components/struct/struct-ifc-import-dialog.tsx apps/editor/components/struct/struct-ifc-import-dialog.test.tsx
git commit -m "feat(struct): add IFC import dialog"
```

---

### Task 5: Make imported IFC fallback entities movable and inspectable

**Files:**
- Create: `packages/nodes/src/imported-mesh/source.ts`
- Create: `packages/nodes/src/imported-mesh/source.test.ts`
- Create: `packages/nodes/src/imported-mesh/parametrics.ts`
- Create: `packages/nodes/src/imported-mesh/panel.tsx`
- Create: `packages/nodes/src/imported-mesh/panel.test.tsx`
- Modify: `packages/nodes/src/imported-mesh/definition.ts`
- Create: `packages/nodes/src/imported-mesh/definition.test.ts`

**Interfaces:**
- Consumes: imported-mesh `metadata` written by the IFC converter.
- Produces: `readIfcSource(metadata)` and a custom inspector labelled `IFC 导入实体`.

```ts
export type IfcSource = {
  ifcType: string | null
  globalId: string | null
  expressId: number | null
  typeName: string | null
  material: string | null
}

export function readIfcSource(metadata: unknown): IfcSource
```

- [ ] **Step 1: Write failing source and definition tests**

In `source.test.ts`:

```ts
import { describe, expect, test } from 'bun:test'
import { readIfcSource } from './source'

test('reads the converter IFC identity', () => {
  expect(
    readIfcSource({
      ifcType: 'IFCBEAM',
      globalId: '0YvctVUKr0kugbFTf53O9L',
      expressID: 42,
      typeName: 'Beam Type',
      material: 'Steel',
    }),
  ).toEqual({
    ifcType: 'IFCBEAM',
    globalId: '0YvctVUKr0kugbFTf53O9L',
    expressId: 42,
    typeName: 'Beam Type',
    material: 'Steel',
  })
})
```

In `definition.test.ts`:

```ts
import { describe, expect, test } from 'bun:test'
import { importedMeshDefinition } from './definition'

describe('imported mesh editing', () => {
  test('is movable and loads its IFC inspector panel', () => {
    expect(importedMeshDefinition.capabilities.movable).toEqual({
      axes: ['x', 'y', 'z'],
      gridSnap: true,
    })
    expect(importedMeshDefinition.parametrics?.customPanel).toBeFunction()
  })
})
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
bun test packages/nodes/src/imported-mesh/source.test.ts packages/nodes/src/imported-mesh/definition.test.ts
```

Expected: FAIL because `source.ts` is absent and imported-mesh is not movable/parametrized.

- [ ] **Step 3: Implement source metadata and definition capabilities**

Implement `readIfcSource` with type guards for string/number/null values. Add:

```ts
capabilities: {
  batchable: perNodeGeometryBatchable,
  selectable: { hitVolume: 'bbox' },
  movable: { axes: ['x', 'y', 'z'], gridSnap: true },
  duplicable: true,
  deletable: true,
  presettable: false,
},
parametrics: {
  groups: [],
  customPanel: () => import('./panel'),
},
```

Keep the hidden presentation and existing geometry/floorplan code.

- [ ] **Step 4: Implement the panel and its failing test**

Write `panel.test.tsx` first, rendering the panel with an `ImportedMeshNode` whose metadata contains `ifcType: 'IFCBEAM'` and asserting serialized output contains `IFC 导入实体`, `IFCBEAM`, `移动`, and `属性为只读` but `名称、显隐、删除` remain editable through the standard inspector.

Then implement `panel.tsx` using existing project panel primitives. Display:

- `IFC 导入实体`
- IFC type
- GlobalId
- ExpressID
- Source type name
- Material
- Short note: `几何按 IFC 保留；截面和结构计算参数暂不可编辑。`

- [ ] **Step 5: Run tests and verify they pass**

Run:

```powershell
bun test packages/nodes/src/imported-mesh
bun run --cwd packages/nodes check-types
bunx biome check packages/nodes/src/imported-mesh
```

Expected: all pass.

- [ ] **Step 6: Commit**

```powershell
git add -- packages/nodes/src/imported-mesh/definition.ts packages/nodes/src/imported-mesh/definition.test.ts packages/nodes/src/imported-mesh/source.ts packages/nodes/src/imported-mesh/source.test.ts packages/nodes/src/imported-mesh/parametrics.ts packages/nodes/src/imported-mesh/panel.tsx packages/nodes/src/imported-mesh/panel.test.tsx
git commit -m "feat(nodes): make IFC meshes inspectable"
```

---

### Task 6: Add real-browser IFC import/edit/reload acceptance

**Files:**
- Create: `scripts/verify-struct-ifc-import.mjs`

**Interfaces:**
- Consumes: running StructWeb URL from `STRUCTWEB_BASE_URL`, default `http://localhost:3010`; bundled IFC fixtures under `apps/ifc-converter/public/test-ifc-files/`.
- Produces: JSON result containing imported project id, node counts, edit persistence, original-project preservation and console errors.

- [ ] **Step 1: Create the browser acceptance script**

Use `playwright-core` and the same bundled Chromium discovery logic as existing `scripts/verify-struct-project-creation.mjs`. The script must:

1. Register a unique temporary account.
2. Create an ordinary baseline project and record its graph signature.
3. Return to the project center, open the 文件 tab, and click `导入 IFC`.
4. Set the hidden file input to `01-duplex.ifc`.
5. Wait for review counts and assert source `.ifc` is shown.
6. Create the project and wait for the new `/struct/:id` route.
7. Assert canvas is attached, `useScene` has nodes, and at least one `imported-mesh` exists.
8. Switch to 2D and assert floorplan SVG contains imported geometry.
9. Select one imported-mesh node through the scene store, update its `name` through the production scene API, and verify it persists.
10. Reload the page and assert the renamed node and graph node count remain.
11. Reopen the baseline project and assert its graph signature is unchanged.
12. Upload `not-an-ifc.txt` and assert no new project is created.
13. Fail on console/page errors except known missing `nature-icon` and `streetscape-icon` assets.

Use this result shape:

```js
console.log(JSON.stringify({
  importedProjectId,
  baselineProjectId,
  nodeCount,
  importedMeshCount,
  levelCount,
  renamedNodeId,
  persistedAfterReload: true,
  baselineUnchanged: true,
  invalidFileBlocked: true,
  consoleErrors,
}, null, 2))
```

- [ ] **Step 2: Run the browser acceptance**

Start the source app in a temporary terminal when no source-current server is running:

```powershell
bun run --cwd apps/editor dev -- -p 3010
node scripts/verify-struct-ifc-import.mjs
```

Expected: JSON success with `persistedAfterReload: true`, `baselineUnchanged: true`, `invalidFileBlocked: true` and zero relevant console errors.

- [ ] **Step 3: Verify the damaged-file path separately**

Create a temporary truncated `.ifc` by taking the first 64 bytes of a bundled fixture. Run the script's invalid path, or add `STRUCTWEB_IFC_CORRUPT_FIXTURE` support that writes the byte prefix to the OS temp directory. Expected: conversion error is shown and no project route is created.

- [ ] **Step 4: Run the full relevant suite**

Run:

```powershell
bun test apps/editor/lib/struct/ifc-import.test.ts apps/editor/lib/struct/ifc-runtime-assets.test.ts apps/editor/components/struct/struct-store.test.ts apps/editor/components/struct/struct-ifc-import-dialog.test.tsx packages/nodes/src/imported-mesh
bun run --cwd apps/editor check-types
bun run --cwd packages/nodes check-types
bunx biome check apps/editor/lib/struct/ifc-import.ts apps/editor/lib/struct/ifc-import.test.ts apps/editor/components/struct/struct-ifc-import-dialog.tsx apps/editor/components/struct/struct-ifc-import-dialog.test.tsx apps/editor/scripts/copy-web-ifc-wasm.mjs scripts/verify-struct-ifc-import.mjs packages/nodes/src/imported-mesh
```

Expected: all tests, types and formatting pass.

- [ ] **Step 5: Commit**

```powershell
git add -- scripts/verify-struct-ifc-import.mjs
git commit -m "test(struct): verify IFC import workflow"
```

---

### Task 7: Document the workflow and known limits

**Files:**
- Modify: `docs/STRUCT-PROTOTYPE.md`
- Modify: `docs/design/web-fea/CURRENT_STATE.md`
- Modify: `docs/design/web-fea/DESIGN_CHANGELOG.md`

**Interfaces:**
- Consumes: final import behavior and verification commands.
- Produces: user-facing instructions and implementation status.

- [ ] **Step 1: Update prototype instructions**

In `docs/STRUCT-PROTOTYPE.md`, add a section with:

```markdown
## IFC 导入

1. 打开“文件”Ribbon 页签，点击“导入 IFC”。
2. 选择或拖入 `.ifc` 文件。
3. 等待转换完成，检查楼层、节点和导入实体统计。
4. 确认工程名并点击“创建工程”。
5. 导入会创建独立 StructWeb 工程，当前工程不会被覆盖。

第一阶段支持 IFC2X3/IFC4 的查看和通用编辑；导入内容暂不参与结构统计或 analysis-model。可参数化构件使用原属性面板，其余对象显示为“IFC 导入实体”。
```

Add the browser command:

```powershell
node scripts/verify-struct-ifc-import.mjs
```

- [ ] **Step 2: Update current state and changelog**

In `CURRENT_STATE.md`, record:

- Browser-side IFC2X3/IFC4 import is available.
- Default target is a new StructWeb project.
- Native Pascal parametric mapping follows the converter.
- Imported meshes are movable/selectable/deletable and show source metadata.
- Analysis-model integration is intentionally absent.

Add one dated changelog entry describing the new File → Import IFC flow and verification result.

- [ ] **Step 3: Check documentation**

Run:

```powershell
rg -n "TODO|TBD|待定" docs/STRUCT-PROTOTYPE.md docs/design/web-fea/CURRENT_STATE.md docs/design/web-fea/DESIGN_CHANGELOG.md
git diff --check -- docs/STRUCT-PROTOTYPE.md docs/design/web-fea/CURRENT_STATE.md docs/design/web-fea/DESIGN_CHANGELOG.md
```

Expected: no placeholders and no whitespace errors.

- [ ] **Step 4: Commit**

```powershell
git add -- docs/STRUCT-PROTOTYPE.md docs/design/web-fea/CURRENT_STATE.md docs/design/web-fea/DESIGN_CHANGELOG.md
git commit -m "docs(struct): document IFC import workflow"
```

---

## Final Integration Verification

- [ ] Run all relevant unit and component tests:

```powershell
bun test apps/editor/lib/struct/ifc-import.test.ts apps/editor/lib/struct/ifc-runtime-assets.test.ts apps/editor/components/struct/struct-store.test.ts apps/editor/components/struct/struct-ifc-import-dialog.test.tsx packages/nodes/src/imported-mesh
```

- [ ] Run type checks:

```powershell
bun run --cwd apps/editor check-types
bun run --cwd packages/nodes check-types
```

- [ ] Run quality checks:

```powershell
bunx biome check apps/editor/lib/struct/ifc-import.ts apps/editor/lib/struct/ifc-runtime-assets.test.ts apps/editor/components/struct/struct-ifc-import-dialog.tsx apps/editor/components/struct/struct-ifc-import-dialog.test.tsx apps/editor/components/struct/struct-store.ts apps/editor/components/struct/struct-store.test.ts apps/editor/components/struct/command-defs.tsx apps/editor/components/struct/ribbon-config.ts apps/editor/components/struct/struct-shell.tsx apps/editor/scripts/copy-web-ifc-wasm.mjs packages/nodes/src/imported-mesh scripts/verify-struct-ifc-import.mjs
```

- [ ] Run browser acceptance:

```powershell
node scripts/verify-struct-ifc-import.mjs
```

- [ ] Inspect final status without staging unrelated user work:

```powershell
git status --short
git log -7 --oneline
```

Expected: the feature commits contain only the files listed above; existing unrelated dirty files remain untouched and uncommitted.
