# StructWeb B10 Member Property Editing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add focused single-member endpoint, elevation, axis-angle and end-release editing without moving shared nodes.

**Architecture:** A new member-property editing service plans node reuse/creation and one member update as one scene transaction. A focused Inspector subcomponent owns the local draft and axis-angle pick mode; existing rendering and persisted schema stay unchanged.

**Tech Stack:** TypeScript, React, Zustand scene store, Zod schemas, Bun tests, Playwright Chromium, Docker on port 4743.

## Global Constraints

- B10 is P2 in the current audit.
- Editing a member endpoint must not move or delete its previous shared structural node.
- Endpoints within 50 mm of an existing same-level node must reuse that node.
- Wall Y values remain controlled by wall base and wall-top fields from B06.
- A member referenced by any `structural-slab.boundaryMemberIds` cannot have endpoints edited.
- Locked member, target node, or participating slab blocks the whole operation before any scene mutation.
- Endpoint, section rotation, start/end release and wall datum edits apply as one undo step.
- Do not change `StructuralMember` schema, scene persistence format, 2D renderer or 3D renderer.
- Do not deploy until automated tests and type checks pass.
- Preserve all unrelated uncommitted and untracked workspace changes.
- Worker processes must not run Git write commands or deploy.

---

### Task 1: Add a Transactional Member Property Editing Service

**Files:**

- Create: `apps/editor/lib/struct/member-property-editing.ts`
- Create: `apps/editor/lib/struct/member-property-editing.test.ts`
- Reference: `apps/editor/lib/struct/member-topology.ts`
- Reference: `apps/editor/lib/struct/member-topology.test.ts`
- Reference: `packages/nodes/src/structural-member/topology.ts`

**Interfaces:**

- Consumes: `buildStructuralMemberTopology`, `runAsSingleSceneHistoryStep`, `useScene`, `StructuralMemberSchema`.
- Produces:

```ts
export type StructuralMemberPropertyDraft = Pick<
  StructuralMember,
  | 'start'
  | 'end'
  | 'rotation'
  | 'releaseStart'
  | 'releaseEnd'
  | 'wallBaseElevation'
  | 'wallTopStart'
  | 'wallTopEnd'
>

export type StructuralMemberPropertyPlan = {
  memberId: AnyNodeId
  memberPatch: Partial<StructuralMember>
  createdNodes: StructuralNode[]
  reusedNodeIds: AnyNodeId[]
}

export function planStructuralMemberProperties(
  nodes: Readonly<Record<string, AnyNode>>,
  memberId: AnyNodeId,
  draft: StructuralMemberPropertyDraft,
): StructuralMemberPropertyPlan

export function updateStructuralMemberProperties(
  memberId: AnyNodeId,
  draft: StructuralMemberPropertyDraft,
): StructuralMemberPropertyPlan
```

- [ ] **Step 1: Write failing service tests**

Create `member-property-editing.test.ts` using the existing scene fixture style from `member-topology.test.ts`. Add tests with these exact expectations:

```ts
test('detaches only the edited member from a shared endpoint node', () => {
  // Arrange two beams sharing node N1 at [0, 0, 0].
  // Move only beam A start to [1, 0, 0].
  // Assert beam A has a new/found N2, while N1 and beam B remain unchanged.
})

test('reuses an unlocked node within 50 mm', () => {
  // Existing target node at [2.02, 0, 0].
  // Draft endpoint is [2, 0, 0].
  // Assert reusedNodeIds contains the existing node and createdNodes is empty.
})

test('creates one node for an empty target position', () => {
  // Draft endpoint at [3.5, 0, 1.2] has no nearby node.
  // Assert one created node and matching nodeI/nodeJ.
})

test('rejects a slab-boundary member before mutating the scene', () => {
  // Slab.boundaryMemberIds contains the edited member.
  // Assert plan throws '构件属于楼板边界'.
  // Assert scene nodes and temporal pastStates are unchanged.
})

test('rejects locked current member and locked target node', () => {
  // Assert locked member throws '构件已锁定'.
  // Lock the 50 mm target node and assert '目标节点已锁定'.
})

test('rejects coincident endpoints and non-finite coordinates', () => {
  // Assert duplicate endpoints and NaN throw validation errors.
})

test('applies endpoints, rotation and releases as one history step', () => {
  // Record pastStates length before update.
  // Update endpoint, rotation=30, releaseStart=pinned, releaseEnd=fixed.
  // Assert all values changed and pastStates increased by exactly one.
})

test('round-trips through project local scene save and reopen', () => {
  // Use the same project-store fixture pattern as wall-editing.test.ts.
  // Assert start/end/nodeI/nodeJ/rotation/release fields survive reopen.
})
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
bun test apps/editor/lib/struct/member-property-editing.test.ts
```

Expected: FAIL because `member-property-editing.ts` does not exist.

- [ ] **Step 3: Implement planning and validation**

In `member-property-editing.ts`, implement the following flow:

```ts
function memberOrThrow(nodes, memberId): StructuralMember {
  const node = nodes[memberId]
  if (node?.type !== 'structural-member') throw new Error('所选结构构件不存在')
  return node
}

function assertNoBoundaryDependency(nodes, memberId): void {
  const slab = Object.values(nodes).find(
    (node) =>
      node.type === 'structural-slab' &&
      node.boundaryMemberIds.includes(memberId),
  )
  if (slab) {
    throw new Error(`构件属于楼板 ${slab.id} 的边界，请先重新生成或解除板边界依赖`)
  }
}

function assertFinitePoint(point: StructuralMember['start']): void {
  if (!point.every(Number.isFinite)) throw new Error('构件端点坐标必须是有限数值')
}
```

Plan with one seed:

```ts
const seed = {
  ...member,
  start: draft.start,
  end: draft.end,
  startNodeId: member.nodeI ?? undefined,
  endNodeId: member.nodeJ ?? undefined,
  rotation: draft.rotation,
  releaseStart: draft.releaseStart,
  releaseEnd: draft.releaseEnd,
  wallBaseElevation: draft.wallBaseElevation,
  wallTopStart: draft.wallTopStart,
  wallTopEnd: draft.wallTopEnd,
}
const topology = buildStructuralMemberTopology({
  nodes,
  levelId: member.parentId ?? '',
  members: [seed],
})
const built = topology.members[0]
if (!built) throw new Error('构件端点更新失败')
```

Before returning:

- Reject locked current member.
- Reject coincident `nodeI`/`nodeJ`.
- Reject length below 0.01 m.
- Reject if either reused node exists and is locked.
- Parse `{ ...member, ...memberPatch }` with `StructuralMemberSchema`.
- Include the original member unchanged fields in `memberPatch` so wall validation sees a complete candidate.

- [ ] **Step 4: Implement the single scene transaction**

```ts
const scene = useScene.getState()
const plan = planStructuralMemberProperties(scene.nodes, memberId, draft)
runAsSingleSceneHistoryStep(useScene, () => {
  useScene.getState().applyNodeChanges({
    create: plan.createdNodes.map((node) => ({
      node,
      parentId: node.parentId as AnyNodeId,
    })),
    update: [{ id: memberId, data: plan.memberPatch }],
  })
})
return plan
```

Do not call `updateStructuralMemberEndpoints` and then separately write rotation/releases; that risks separate history steps. Use the topology plan and one `applyNodeChanges` call.

- [ ] **Step 5: Run focused tests**

```powershell
bun test apps/editor/lib/struct/member-property-editing.test.ts apps/editor/lib/struct/member-topology.test.ts apps/editor/lib/struct/wall-editing.test.ts
```

Expected: all tests pass.

- [ ] **Step 6: Run type and format checks**

```powershell
bunx biome check --write apps/editor/lib/struct/member-property-editing.ts apps/editor/lib/struct/member-property-editing.test.ts
bunx biome check apps/editor/lib/struct/member-property-editing.ts apps/editor/lib/struct/member-property-editing.test.ts
bun run --cwd apps/editor check-types
```

Expected: exit code 0.

---

### Task 2: Build the Focused Inspector Editor and Axis-Angle Mode

**Files:**

- Create: `apps/editor/components/struct/struct-member-property-editor.tsx`
- Modify: `apps/editor/components/struct/struct-member-inspector.tsx`
- Modify: `apps/editor/components/struct/struct-store.ts`
- Modify: `apps/editor/components/struct/command-defs.tsx`
- Modify: `apps/editor/components/struct/command-selection.test.ts`
- Reference: `packages/nodes/src/structural-grid/geometry.ts`
- Reference: `apps/editor/components/struct/struct-axis-inspector.tsx`

**Interfaces:**

- Consumes: `StructuralMemberPropertyDraft`, `planStructuralMemberProperties`, `updateStructuralMemberProperties`, `axisAngleDegrees`.
- Produces store fields:

```ts
memberAxisAnglePickMemberId: string | null
startMemberAxisAnglePick: (memberId: string) => void
clearMemberAxisAnglePick: () => void
```

- [ ] **Step 1: Add failing command-selection tests**

Add to `command-selection.test.ts`:

```ts
test('member.takeAxisAngle is a real selected-member command', () => {
  // Select one structural member.
  // Assert runStructCommand('member.takeAxisAngle') opens the member inspector
  // and sets memberAxisAnglePickMemberId to that member.
})

test('member.takeAxisAngle explains when no member is selected', () => {
  // Assert the command returns ok:false and the message includes 未选择结构构件.
})
```

- [ ] **Step 2: Run command tests and confirm failure**

```powershell
bun test apps/editor/components/struct/command-selection.test.ts
```

Expected: FAIL because the command is still planned/disabled.

- [ ] **Step 3: Add store state**

Add the pending member ID and actions to `struct-store.ts`. Reset the field in `reset()` and whenever the active project changes.

```ts
memberAxisAnglePickMemberId: string | null
startMemberAxisAnglePick: (memberId) =>
  set({
    memberAxisAnglePickMemberId: memberId,
    memberEditOpen: false,
    columnDialogOpen: false,
    beamDialogOpen: false,
    wallDialogOpen: false,
  }),
clearMemberAxisAnglePick: () =>
  set({ memberAxisAnglePickMemberId: null }),
```

- [ ] **Step 4: Create the focused editor**

`StructMemberPropertyEditor` receives:

```ts
{
  member: StructuralMember
  nodes: Readonly<Record<string, AnyNode>>
  onMessage: (message: string) => void
}
```

Local state:

```ts
const [draft, setDraft] = useState<StructuralMemberPropertyDraft>(
  memberPropertyDraft(member),
)
```

Use `useEffect` keyed on the member ID and persisted geometry fields to reload the draft only when the selected member ID changes or a committed scene value changes.

Render:

- I/J X/Z for every member type.
- I/J Y for beam/column/brace/truss.
- Beam Y labels: `I 端梁顶标高`, `J 端梁顶标高`.
- Column Y labels: `柱底标高`, `柱顶标高`.
- Wall base and left/right top elevation in the same draft block.
- `截面转角`.
- `I 端释放`, `J 端释放`.
- `取轴线角`.
- `应用构件属性`.

Add stable test IDs:

```ts
data-testid="member-property-start-x"
data-testid="member-property-start-y"
data-testid="member-property-start-z"
data-testid="member-property-end-x"
data-testid="member-property-end-y"
data-testid="member-property-end-z"
data-testid="member-property-rotation"
data-testid="member-property-release-start"
data-testid="member-property-release-end"
data-testid="member-property-wall-base"
data-testid="member-property-wall-top-start"
data-testid="member-property-wall-top-end"
data-testid="member-property-take-axis-angle"
data-testid="member-property-apply"
```

- [ ] **Step 5: Implement axis-angle pick behavior**

When `take axis` is clicked:

```ts
useStructStore.getState().startMemberAxisAnglePick(member.id)
onMessage('请在画布选择一根轴线')
```

In a `useEffect`, subscribe to the selected IDs:

```ts
const selectedAxis = selectedIds
  .map((id) => useScene.getState().nodes[id])
  .find((node) => node?.type === 'structural-grid')
if (!pendingMemberId || !selectedAxis) return
setDraft((current) => ({
  ...current,
  rotation: axisAngleDegrees(selectedAxis),
}))
useStructStore.getState().clearMemberAxisAnglePick()
useViewer.getState().setSelection({ selectedIds: [member.id] })
onMessage(`已取轴线角 ${axisAngleDegrees(selectedAxis)}°`)
```

The parent Inspector must keep rendering the pending member while an axis is selected:

```ts
const pendingId = useStructStore((state) => state.memberAxisAnglePickMemberId)
const effectiveId =
  selectedMemberId ??
  (pendingId ? (pendingId as AnyNodeId) : undefined)
```

- [ ] **Step 6: Integrate the editor into the Inspector**

Mount `StructMemberPropertyEditor` before section/material controls. Remove the old direct `rotation` input and old wall base/top inputs from `struct-member-inspector.tsx`; the new editor owns those fields.

On apply:

```ts
try {
  updateStructuralMemberProperties(member.id, draft)
  setDraft(memberPropertyDraft(useScene.getState().nodes[member.id]))
  onMessage('构件属性已应用')
} catch (error) {
  onMessage(error instanceof Error ? error.message : '构件属性应用失败')
}
```

- [ ] **Step 7: Add a real Ribbon command**

Add a base command in `command-defs.tsx` with ID `member.takeAxisAngle`:

```ts
{
  id: 'member.takeAxisAngle',
  label: '取轴线角',
  group: '构件编辑',
  keywords: ['take', 'axis', 'angle', 'quxian', '取轴线角'],
  execute: () => {
    const id = selectedMemberIds()[0]
    if (!id) {
      logResult('取轴线角', '未选择结构构件')
      return
    }
    useStructStore.getState().openMemberEdit()
    useStructStore.getState().startMemberAxisAnglePick(id)
    logResult('取轴线角', '请在画布选择一根轴线')
  },
}
```

Because `YJK_PLANNED_COMMANDS` filters out IDs already present in base commands, this replaces the disabled placeholder. Update the command test expectation from planned to real.

- [ ] **Step 8: Run focused tests and type checks**

```powershell
bunx biome check --write apps/editor/components/struct/struct-member-property-editor.tsx apps/editor/components/struct/struct-member-inspector.tsx apps/editor/components/struct/struct-store.ts apps/editor/components/struct/command-defs.tsx apps/editor/components/struct/command-selection.test.ts
bun test apps/editor/components/struct/command-selection.test.ts apps/editor/lib/struct/member-property-editing.test.ts apps/editor/lib/struct/wall-editing.test.ts
bun run --cwd apps/editor check-types
```

Expected: exit code 0.

---

### Task 3: Add Browser Acceptance for B10

**Files:**

- Create: `scripts/verify-struct-b10-browser.mjs`
- Create: `artifacts/structweb-b10/<timestamp>.json`
- Create: `artifacts/structweb-b10/<timestamp>-analysis-model.json`

**Interfaces:**

- Consumes the production app at `http://localhost:4743`.
- Produces evidence for shared-node isolation, endpoint persistence, rotation, release, undo/redo, analysis JSON and cleanup.

- [ ] **Step 1: Create a deterministic Playwright scene**

Use the local development account and a temporary project. Construct:

```text
N1 [0, 0, 0]
N2 [6, 0, 0]
N3 [0, 0, 4]
Beam A: N1 -> N2
Beam B: N1 -> N3
Slab: boundaryMemberIds=[beam A]
```

Prefer UI for edits and direct API only for creating the initial deterministic scene if existing project UI cannot create a two-beam shared-node scene quickly.

- [ ] **Step 2: Assert slab-boundary protection**

Select Beam A, change `member-property-start-x` to `0.5`, click apply and assert the error contains `楼板` and `边界`. Re-read the project and assert Beam A and the slab are unchanged.

- [ ] **Step 3: Remove the slab dependency and verify shared-node isolation**

Delete the temporary slab through the scene API with revision control. Reload. Select Beam A, move its I endpoint to `[1, 0, 0]`, apply and assert:

```ts
assert.equal(beamA.nodeI, newNode.id)
assert.deepEqual(newNode.position, [1, 0, 0])
assert.equal(nodes.N1.position[0], 0)
assert.equal(beamB.nodeI, 'N1')
assert.deepEqual(beamB.start, [0, 0, 0])
```

- [ ] **Step 4: Verify edit fields and persistence**

Change:

```ts
rotation = 30
releaseStart = 'pinned'
releaseEnd = 'fixed'
```

For a wall, separately verify only X/Z endpoint inputs render and wall base/top fields remain present. Ctrl+S, fully reload, reselect each member and assert DOM values equal the saved scene and analysis JSON values.

- [ ] **Step 5: Verify axis-angle mode**

Create or select an oblique axis at 30 degrees. Select a beam, click `member.takeAxisAngle`, click the oblique axis, and assert:

```ts
assert.equal(Number(await page.getByTestId('member-property-rotation').inputValue()), 30)
```

Apply, save, reload and assert the angle remains 30.

- [ ] **Step 6: Verify one-step undo and redo**

Record `pastStates.length`. Apply an endpoint/rotation/release change. Assert history increased by one. Press Ctrl+Z and assert all four fields revert together. Press Ctrl+Shift+Z and assert all four fields reapply.

- [ ] **Step 7: Verify error counters and cleanup**

Track:

```ts
page.on('console', ...)
page.on('pageerror', ...)
page.on('requestfailed', ...)
page.on('response', ...)
```

Exclude only the known same-page RSC `net::ERR_ABORTED` during reload. At the end:

- console error = 0.
- pageerror = 0.
- API requestfailed = 0.
- HTTP >= 400 = 0.
- 429 = 0.
- temporary project DELETE = 204.
- project GET after cleanup = 404.

- [ ] **Step 8: Run syntax check**

```powershell
node --check scripts/verify-struct-b10-browser.mjs
```

Expected: exit code 0.

---

### Task 4: Full Verification, Deploy and Audit Update

**Files:**

- Modify: `_StructWeb_YJK_全面缺陷审计_2026-10-20.md`
- Evidence: `artifacts/structweb-b10/<successful-run>.json`

**Interfaces:**

- Consumes successful code tests and browser evidence.
- Produces deployed image on fixed port 4743 and updated B10 status/counts.

- [ ] **Step 1: Run the full related suite**

```powershell
bun run --cwd packages/core build
bun run --cwd packages/nodes build
bun run --cwd apps/editor check-types
bun test packages/core/src/schema/nodes
bun test packages/nodes/src/structural-member packages/nodes/src/structural-node
bun test apps/editor/lib/struct
```

Expected: all exit code 0.

- [ ] **Step 2: Deploy**

```powershell
.\scripts\deploy-structweb.ps1
```

Expected:

- `structweb` healthy.
- `structweb-edge` healthy.
- RestartCount 0.
- `0.0.0.0:4743 -> 80/tcp`.
- `/struct`, `/struct/new`, `/struct/prototype`, `/api/health` return 200.

- [ ] **Step 3: Run browser acceptance**

```powershell
$env:STRUCTWEB_BASE_URL = 'http://localhost:4743'
node scripts/verify-struct-b10-browser.mjs
```

Expected: `pass: true`.

- [ ] **Step 4: Update the audit only after all gates pass**

Change B10 from `仍存在` to `已关闭（2026-10-22复核）` only if:

- Shared-node isolation passed.
- Slab-boundary blocking passed.
- Endpoint, elevation, rotation and release persisted.
- Axis-angle mode passed.
- One-step undo/redo passed.
- Browser errors were zero.
- Temporary project cleanup returned 404.

Update the summary counts by subtracting one P2 from open items and adding one to closed items. Do not change C06, D01 or any unrelated status.

- [ ] **Step 5: Verify the report counts**

```powershell
$rows = Select-String -Path '_StructWeb_YJK_全面缺陷审计_2026-10-20.md' -Pattern '^\| [A-F]\d{2} \|'
$closed = @($rows | Where-Object { $_.Line -match '\| 已关闭' }).Count
$partial = @($rows | Where-Object { $_.Line -match '\| 部分关闭/剩余' }).Count
$open = @($rows | Where-Object { $_.Line -match '\| 仍存在' }).Count
[pscustomobject]@{Closed=$closed;Partial=$partial;Open=$open;Total=$closed+$partial+$open}
```

Expected: 48 total and B10 counted as closed.

## Execution Notes

- Use a worker for code edits and test loops.
- Worker must not call `dsw`, run `git commit`, `git reset`, `git checkout`, or deploy.
- Supervisor keeps the checkpoint at `G:\_codex_backups\StructWeb-pre-B10-20261022-000314`.
- Do not modify unrelated dirty worktree files.
