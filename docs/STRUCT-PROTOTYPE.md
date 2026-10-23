# StructWeb 建模 Ribbon + 命令系统原型

> 说明：本文记录早期 Ribbon/命令原型；结构节点、构件、板与柱布置的当前实现状态见 `docs/design/web-fea/CURRENT_STATE.md`。

路由：`/struct`

在 Pascal Editor 之上加了一层“桌面 CAD 式”外壳，演示三件事：

1. Ribbon 由配置驱动（页签 → 分组 → 命令按钮），梁被选中后出现上下文页签「梁」。
2. 一份命令表同时驱动 Ribbon、⌘K 命令面板、键盘快捷键和命令行。
3. CAD 命令行支持别名、`_` 前缀、缺参数逐项提示、历史、Tab 补全和 `?` 帮助。

## 运行

```powershell
cd E:\Civil-Engineering\StructWeb-Prototype
bun install --ignore-scripts
bunx turbo run build --filter=@pascal-app/core --filter=@pascal-app/viewer --filter=@pascal-app/nodes --filter=@pascal-app/geometry-script --filter=@pascal-app/ifc-converter --filter=@pascal-app/mcp
cd apps/editor
bunx next dev -p 3010
```

打开 `http://localhost:3010/struct`。

说明：3000 端口已被本机的「规范管理后台」占用，原型固定用 3010。

新建结构工程使用 `http://localhost:3010/struct/new`。创建后进入
`/struct/<projectId>`；工程元数据和场景按工程 ID 保存到服务端 SQLite，
同时在浏览器保留本机缓存。刷新、换浏览器或重新登录后仍可从云端打开同一工程；
旧版本机工程会显示为“本机草稿 / 待上传”。原 `/struct/prototype` 继续作为示例工程入口。

## Revision 历史、对比与恢复

云端工程每次创建、保存、工程信息更新、重命名和恢复都会形成不可变的 revision。
Ribbon 的「模型 → 检查与工具 → 版本历史 / 工程对比」可打开当前工程历史：

- 历史列表按 revision 倒序分页，显示真实作者、时间、变更类型和模型计数；列表不携带完整 graph。
- 单次预览通过 revision detail API 显式读取 graph，并进入 Editor 只读版本预览。退出预览会恢复当前模型，不触发 autosave，也不增加 revision。
- 任意两个历史 revision 可比较 14 类结构化差异：工程信息、楼层、轴网、节点、构件、板、截面、材料、工况、组合及四类荷载。
- 恢复是 append-only：服务端校验 `If-Match: "<currentRevision>"`，成功时创建 `current + 1` 的新 revision，不更新或删除旧快照。缺少前置条件返回 `428`，版本过期返回 `409`，损坏或工程 ID 不匹配的历史图返回 `422`。
- revision list/detail/compare/restore 都必须登录并按 owner 隔离；访问其他用户工程统一返回中性 `404 { "error": "not_found" }`。
- 分析 ResultSet 绑定 `projectId@revision`。恢复会改变当前 revision，因此旧结果由结果 API 自动判定为 `stale=true`、`staleReason="revision_changed"`，UI 保留只读结果并禁用报告/导出。

本地完整验收使用临时 SQLite、临时 PyNite worker 和真实 Playwright：

```powershell
node scripts/verify-struct-revision-history.mjs
```

证据写入 `artifacts/struct-revision-history-<runId>/evidence.json`。调试脚本本身时可复用现有 Next build：

```powershell
$env:STRUCTWEB_SKIP_ACCEPTANCE_BUILD='1'
node scripts/verify-struct-revision-history.mjs
```

正式验收仍应运行不带跳过参数的完整命令。

## 工程表格与区域粘贴

节点编辑表和构件编辑表已接入稳定实体 ID、区域选择和虚拟化工程网格：

- 行 ID 直接使用 `structural-node_*` / `structural-member_*` 实体 ID；表格选择同步到现有画布选择桥。
- 支持 TSV 与带引号 CSV，包括 CRLF、UTF-8 BOM、转义引号和单元格内换行；单次粘贴限制为 2 MiB、5,000 行、200 列。
- 节点长度接受 `m`/`mm` 并统一存为米，半径列使用毫米；空白单元格表示跳过，不会写成零。
- 粘贴先进入预览，逐单元格显示行列、实体和列错误；锁定行、非法单位、越界或不支持枚举都会使整批零写入。
- 合法批次通过一个场景事务提交，`Ctrl/Cmd+Z` 可一次撤销；构件 i/j 节点和长度列为只读。
- 超过 100 行时仅渲染可见行，虚拟化不改变全量校验、稳定 rowId 或选择。

浏览器验收使用临时 SQLite、真实 Next 生产构建和 Playwright，不触碰生产数据库：

```powershell
node scripts/verify-struct-bulk-table-paste.mjs
```

证据写入 `artifacts/struct-bulk-table-paste-<runId>/evidence.json`。

## 结构布置图 DXF

「施工图 → 布置 → 图框」现在打开真实图纸输出对话框。首期只输出当前楼层结构布置图，不包含规范验算结论、节点详图或 DWG 转换：

- DXF 使用米制模型转换到毫米，包含 `SW-AXIS`、`SW-NODE`、`SW-MEMBER`、`SW-COLUMN`、`SW-SLAB`、`SW-TEXT`、`SW-TITLE` 图层。
- 标题块记录工程名、编号、revision、当前楼层、单位和模型指纹前 12 位。
- 图纸元数据按用户和工程隔离存放在 `struct-drawing-index:<ownerId>:<projectId>`；DXF 正文存放在浏览器 IndexedDB，不塞入 localStorage。
- 新建、保存或恢复导致 revision/模型指纹变化后，既有图纸标记为“模型已变化，需重新生成”，仍可下载原快照。
- 本机草稿没有服务端 revision，生成按钮保持禁用；DWG、立面、节点详图与材料表继续标为规划中。

浏览器验收：

```powershell
node scripts/verify-struct-drawing-output.mjs
```

证据写入 `artifacts/struct-drawing-output-<runId>/evidence.json`。

## IFC 导入

1. 打开“文件”Ribbon 页签，点击“导入 IFC”。
2. 选择或拖入 `.ifc` 文件。
3. 等待浏览器端 WebIFC 转换完成，检查楼层、节点和导入实体统计。
4. 确认工程名并点击“创建工程”。
5. 导入默认创建新的独立 StructWeb 工程，当前工程不会被覆盖。

第一阶段支持 IFC2X3 和 IFC4 的查看与通用编辑。可参数化对象沿用 converter 映射的 Pascal 节点；无法参数化的对象显示为 `imported-mesh`（界面名称“IFC 导入实体”），可选中、在 2D/3D 中显示、移动、改名、显隐和删除，并只读显示 IFC 元数据。

导入内容目前不进入结构构件统计，也不进入 analysis-model 参数化映射。无效文件或截断损坏的 IFC 文件会显示错误，不创建工程。

IFC2X3 样例 `01-duplex.ifc` 首次创建返回 255 个节点；经编辑器首次加载与首次 autosave 的正常 graph 规范化后，稳定基线为 253 个节点、79 个 `imported-mesh`、4 层。刷新后节点基线不变，改名和显隐保持，2D 几何仍在。IFC4 样例 `10-sample-house.ifc` 创建 55 个节点、26 个 `imported-mesh`、16 个 native geometry、2 层，并进入独立新工程。验收中原 baseline graph 不变；无效 `.txt` 与截断损坏的 `.ifc` 均显示错误且不创建工程；相关 console/page errors 为 0。

浏览器验收命令：

```powershell
node scripts/verify-struct-ifc-import.mjs
```

脚本默认连接 `http://localhost:3010`，需已有当前源码服务；也可通过 `STRUCTWEB_BASE_URL` 指定地址。

## 文件

| 文件 | 作用 |
|---|---|
| `apps/editor/app/struct/page.tsx` | 路由入口 |
| `apps/editor/components/struct/struct-shell.tsx` | Ribbon + Editor + 命令行 + HUD 组合 |
| `apps/editor/app/struct/new/page.tsx` | 新建结构工程入口 |
| `apps/editor/components/struct/struct-new-project-page.tsx` | 工程信息、规范单位、模板参数与起模方式 |
| `apps/editor/app/struct/[projectId]/page.tsx` | 工程级结构建模路由 |
| `apps/editor/components/struct/struct-project-workspace.tsx` | 工程级加载、保存与缺失状态 |
| `apps/editor/lib/struct/project-store.ts` | 工程元数据、参数化起模、场景元数据与本机缓存 |
| `apps/editor/lib/struct/project-cloud.ts` | 云端工程 CRUD 客户端与 409/404 错误映射 |
| `apps/editor/lib/struct/revision-client.ts` | revision 列表、详情、比较与恢复客户端 |
| `apps/editor/components/struct/struct-revision-history-dialog.tsx` | revision 历史、对比、预览和恢复确认 UI |
| `apps/editor/lib/struct/table/` | TSV/CSV 解析、区域模型、节点/构件表格预览与单位校验 |
| `apps/editor/components/struct/table/` | 可访问虚拟工程网格与批量粘贴预览对话框 |
| `apps/editor/lib/struct/drawing-dxf.ts` | 当前楼层结构布置图 DXF 纯生成器 |
| `apps/editor/lib/struct/drawing-index.ts` | 图纸指纹、用户/工程隔离索引与 stale 判定 |
| `apps/editor/components/struct/struct-drawing-output-dialog.tsx` | 布置图生成、历史列表与 DXF 下载 UI |
| `apps/editor/app/api/struct-projects/route.ts` | 云端 StructWeb 工程列表 |
| `apps/editor/app/api/struct-projects/[id]/route.ts` | 云端 StructWeb 工程读取与元数据更新 |
| `apps/editor/components/struct/struct-store.ts` | 原型状态：构件、荷载、分析、结果、日志、历史 |
| `apps/editor/components/struct/command-defs.tsx` | 40+ 条命令、别名、参数、执行逻辑 |
| `apps/editor/components/struct/ribbon-config.ts` | 五个页签与上下文页签的配置 |
| `apps/editor/components/struct/ribbon.tsx` | Ribbon 渲染器，读取命令注册表 |
| `apps/editor/components/struct/command-line.tsx` | 命令行解析、提示、补全、历史 |
| `apps/editor/components/struct/struct-hud.tsx` | 右下角状态 HUD |
| `apps/editor/lib/struct/parser.ts` | 纯函数解析器 |
| `packages/editor/src/store/use-command-registry.ts` | 命令注册表，新增 `aliases` / `usage` / `args` / `executeWithArgs` |

## 命令示例

```text
beam 7500 400 200      # 梁：长度 / 截面高 / 翼缘宽
b 7500                  # 别名，缺省截面 400×200
_beam 8000              # 兼容 CAD 下划线前缀
column 4200             # 柱
line 4.2                # 线荷载 kN/m
l 4.2                   # 别名
?                       # 命令清单
help beam               # 单条命令用法
undo / redo             # 真实调用编辑器撤销 / 重做
select all / clear      # 真实调用编辑器选择
```

命令行快捷键：`F2` 聚焦、`↑/↓` 历史、`Tab` 补全、`Esc` 取消。

## 已验证

- `/struct` 返回 200，Ribbon 5 个页签、模型页 19 个按钮。
- `F2` 聚焦命令行。
- `beam 7500 400 200` 后 HUD 构件数变为 1，日志出现构件编号与截面。
- `beam` 不带参数时逐项提示「长度 / 截面高 / 翼缘宽」，补全后创建构件。
- `_beam 8000` 与 `l 4.2` 分别新增构件和荷载。
- `?` 输出命令清单。
- 切换「荷载」页签，`aria-selected` 为 true。
- `Ctrl+K` 命令面板能搜到「梁」（无头 Chrome 把 Ctrl+K 当作地址栏快捷键，验证脚本改为派发同名 KeyboardEvent，页面只挂载 1 个面板）。
- 选中构件后出现上下文页签「梁」。
- 浏览器控制台 0 错误。
- 解析器 9 项单测全部通过。

布局实测：Ribbon `0–92px`，编辑器画布 `140–868px`，命令行 `869–901px`，互不遮挡。

说明：`/struct` 使用编辑器 v2 布局，命令面板由 v2 的侧栏挂载，原型没有重复挂载。

## 当前边界

- `beam` / `column` / 荷载命令目前写入原型 store 和 HUD，用来验证命令链路；还没有生成真实的 3D 结构构件，也没有接后端求解器。
- `undo` / `redo` / `select all` / `clear` 调用的是编辑器真实 API，其余结构命令是演示实现。
- 编辑器自带的顶部栏仍保留，Ribbon 位于其上方；下一步可以把两者合并成单一顶栏。
- 本原型没有改动画布交互、选择、相机和场景持久化。

## 加一条新命令

在 `command-defs.tsx` 的 `STRUCT_COMMANDS` 里追加：

```tsx
{
  id: 'member.purlin',
  label: '檩条',
  group: '建模',
  keywords: ['purlin', '檩条'],
  aliases: ['p', 'purlin'],
  usage: 'purlin <跨度mm>',
  args: [{ name: 'span', label: '跨度 (mm)', type: 'number' }],
  execute: () => addMember('beam', 6000, 'C200×70×20×2.5'),
  executeWithArgs: (args) => addMember('beam', Number(args[0] ?? 6000), 'C200×70×20×2.5'),
}
```

再在 `ribbon-config.ts` 的目标分组里加 `{ commandId: 'member.purlin' }` 即可同时出现在 Ribbon、⌘K 和命令行。

## 验证脚本

```powershell
node scripts/verify-struct-prototype.mjs
node scripts/verify-struct-layout.mjs
node scripts/verify-struct-slab-yjk.mjs
node scripts/verify-struct-workflow.mjs
node scripts/verify-struct-revision-history.mjs
node scripts/verify-struct-bulk-table-paste.mjs
node scripts/verify-struct-drawing-output.mjs
node scripts/verify-struct-ifc-import.mjs
```

截图输出：`docs/struct-prototype.png`
