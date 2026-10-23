# StructWeb 当前实现事实

版本：2026-10-23

性质：当前代码与文档快照的事实记录，不是目标方案，不是完成度声明。

维护规则：能由代码 manifest 生成的事实，不手工维护；本文件只记录无法自动提取的边界与证据。

## 1. 状态词汇

| 状态 | 含义 |
|---|---|
| `implemented` | 有代码、有可观察副作用、有测试或运行记录 |
| `partial` | 主链路已实现，但关键边界或下游闭环仍缺失 |
| `demo` | 有界面或日志，但不产生真实工程结果 |
| `target` | 目标能力，尚未实现 |
| `unverified` | 代码或第三方能力存在，但未做本项目验收 |

任何“已采用”“已支持”“已完成”的表述，必须能落到 `implemented` 或 `unverified`，不能用 `demo` 冒充。

## 2. 当前事实

| 项目 | 事实 | 状态 | 证据 |
|---|---|---|---|
| 宿主工作区 | `/struct` 仍挂载 Pascal `Editor`，项目 ID 固定为 `struct-prototype` | `demo` | `apps/editor/components/struct/struct-shell.tsx` |
| 新建结构工程 | `/struct/new` 提供已批准稿单页起模流程；创建后进入 `/struct/[projectId]`，工程元数据与场景按工程 ID 写入本机 localStorage，刷新可恢复；参数化门式刚架生成普通轴网/节点/构件，4 项工程工厂测试与浏览器创建/刷新验收通过 | `implemented` | `struct-new-project-page.tsx`、`struct-project-workspace.tsx`、`lib/struct/project-store.ts`、`scripts/verify-struct-project-creation.mjs` |
| IFC 导入 | “文件 → 导入 IFC”已接入浏览器端 WebIFC，支持 IFC2X3 与 IFC4；默认创建新的独立 StructWeb 工程，不覆盖当前工程。可参数化对象沿用 converter 映射的 Pascal 节点，无法参数化对象为 `imported-mesh`，可选中、2D/3D 显示、移动、改名、显隐、删除，并只读显示 IFC 元数据。第一阶段 `imported-mesh`/IFC 内容不进入结构构件统计或 analysis-model 参数化映射 | `partial` | `scripts/verify-struct-ifc-import.mjs`；2026-10-23 真实浏览器验收 |
| 结构数据 | 结构场景、revision/model hash 与分析结果集已持久化；协作式项目权限仍未实现 | `partial` | 结构场景 API、`apps/editor/lib/analysis-jobs/`、`services/analysis-worker/` |
| 新模型层 | `axis-grid-store.ts` 已由 `struct-shell`、Ribbon 和轴网工具引用；通用 `model/types.ts`、`geometry.ts`、`model-store.ts` 仍未接入主场景 | `demo` | `apps/editor/components/struct/model/`、`struct-shell.tsx`、`command-defs.tsx` |
| 命令注册 | 当前注册表 74 个现有命令 ID；轴网、节点、构件、尺寸、DXF、支座、分析组装等命令已接入真实工具 | `demo` | `apps/editor/components/struct/command-defs.tsx` |
| 命令文档 | 文档写 380 条，约 36 条“已实现”、19 条“部分”、325 条“待实现” | 文档事实 | `v6/STRUCT_MODEL_COMMANDS.md` |
| 命令状态审计 | 146 条：74 现有 + 72 planned；现有 44 partial、29 placeholder、1 demo-timer、0 unknown | `generated` | `COMMAND_STATUS.md`、`scripts/struct-command-status.ts` |
| 结构领域包 | 13 个测试通过；含单位、schema、校验、编译、轴线网格 | `implemented` | `packages/struct-domain` |
| 轴网工具 | 可生成正交/直线/斜交/圆弧/辅助轴线，按单点/两点/三点设置上节点高；支持归并、形成网点、平移/旋转/镜像、撤销/重做、保存本地草稿；同步到主场景使用一次场景事务 | `implemented` | `apps/editor/components/struct/axis-grid-tool.tsx`、`apps/editor/lib/struct/axis-grid-sync.ts`；11 个领域测试 + 9 个 store/sync 测试 |
| 轴网画布入口 | “在 2D 画布直接画”切换到专家 2D、激活 `structural-grid` 楼层工具；支持两次点选，轴网绘制中按 X/Y 锁定、再次按键释放 | `implemented` | `axis-grid-tool.tsx`、`packages/nodes/src/structural-grid/floorplan-tool.tsx`；浏览器实测提示 `Start grid axis`，两次点选后 Elements 8→9 |
| 2D 视觉基线 | 结构轴线默认红色，画板默认 CAD 深灰色，栅格随间距设置变化 | `implemented` | `floorplan.ts`、`floorplan-tool.tsx`、`floorplan-panel.tsx`；单元测试与浏览器截图核对 |
| 结构捕捉 | 捕捉优先级为结构节点 → 轴线端点 → 轴线中点 → 轴网交点 → 垂足 → 轴线；命中时显示节点/端点/中点/交点/垂足/轴线标签 | `implemented` | `packages/nodes/src/structural-grid/coordination.ts`、`floorplan-tool.tsx`；15 个捕捉/轴网测试通过 |
| 轴网快速输入 | 支持列数 × 行数、X/Y 间距和原点坐标生成 N×M 轴网 | `implemented` | `axis-grid-store.ts`、`axis-grid-tool.tsx`；浏览器实测 4×3、12 节点、17 轴线 |
| 轴网参数入口 | 只有 `grid.ortho` 打开轴网参数面板（开间/进深、起始轴号 X/Y、预览后插入当前楼层）；`grid.linear` / `grid.rectangle` / `grid.arc` / `grid.radialGrid` / `grid.skew` / `grid.aux` 直接进入 2D 画布绘制，不弹面板 | `implemented` | `axis-grid-tool.tsx`、`axis-grid-store.ts`、`command-defs.tsx`、`structural-grid/floorplan-tool.tsx`；浏览器实测正交弹面板，其余入口无面板 |
| 2D 画布控制 | 3D/2D/分屏切换、500/250/100/50 mm 栅格、旋转锁定和解锁、画轴网入口 | `implemented` | `apps/editor/components/struct/struct-canvas-controls.tsx`、`floorplan-panel.tsx`；浏览器实测控件状态 |
| 3D/2D 旋转保持 | 从 3D-only 切到 2D-only 时不再用隐藏 3D 相机姿态覆盖 2D 画布旋转；分屏仍保留联动 | `implemented` | `floorplan-panel.tsx` 的 `isViewVisible(VIEW_3D)` 门禁；包与编辑器类型检查通过 |
| Ribbon 布局 | 模型页签 9 组、组装页签 4 组，节点组 6×2、轴线网格 5×2；荷载输入移到荷载页签；文件组已移出模型页签 | `implemented` | `apps/editor/components/struct/ribbon-config.ts`、`ribbon.tsx`；浏览器实测页签为模型/组装/荷载/分析/结果/施工图 |
| 轴网主场景同步 | 浏览器实测生成 7 条轴线后，2D 场景出现 7 个 `Structural Grid`，一次 Undo 全部回退 | `implemented` | 2026-10-19 本地 `/struct` 浏览器验收 |
| 分析命令 | 前处理与线性静力主链路为真实实现：“开始分析”提交冻结 revision/hash 的作业，完成后回填变形、弯矩、剪力、轴力、反力和结果表；模态、屈曲与完整设计验算仍为 `target`，钢构件强度利用率见下一行 | `partial` | `analysis-model.ts`、`analysis-jobs/`、`struct-analysis-jobs-dialog.tsx`、`command-defs.tsx`；生产 evidence `artifacts/struct-analysis-closed-loop-d01-linear-20261022-185658/evidence.json` |
| 钢构件强度利用率 | H 型钢与圆钢管，GB 50017-2017 第4.4.1/6.1.1/6.1.3/7.1.1/7.1.2/8.1.1条，11站包络，CheckSet 固定 incomplete；不覆盖净截面、稳定、局部稳定、挠度、扭转、疲劳和连接 | `implemented` | `services/analysis-worker/steel_strength.py`、`struct-analysis-stress-ratio.tsx`、`command-defs.tsx`；`artifacts/struct-analysis-closed-loop-mvkkjkev-2f2c43/evidence.json` |
| 分析模型组装 | `analysis.assemble`：把结构节点、构件、截面、材料、支座组装为分析模型；导出节点/构件/支座、转角与偏心、端释放、总长/总重及错误/提示清单；可导出 `analysis-model.json` | `implemented` | `analysis-model.ts`、`struct-analysis-model-dialog.tsx`；3 项测试 + 浏览器 41 节点/1 构件检查与 JSON 导出 |
| 编辑命令 | 复制、移动、镜像、阵列等只写日志，不改变模型 | `demo` | `command-defs.tsx` 的 `edit.*`、`member.*` |
| 分析服务 | 分析 API + Docker Python worker 已实现线性静力作业队列、PyNite 3.2.0 适配、result-set 持久化、stale 判定与 staged 钢构件强度 CheckSet；不包含模态、屈曲或完整设计验算 | `implemented` | `apps/editor/lib/analysis-jobs/`、`services/analysis-worker/`；115 项 worker pytest 与生产 D01/D05 evidence |
| CAD | 未发现 `/api/cad/*`、MxDraw sidecar、DXF 版本表 | `target` | 工作仓库无 CAD 服务 |
| 认证 | 单管理员共享密码，主体固定为 `admin`；不是项目级授权或多租户 | `demo` | `apps/editor/lib/self-host-auth.ts` |
| 场景持久化 | 通用 `SceneStore` 支持场景、revision 和事件；SQLite 实现存在 | `implemented` | `apps/editor/lib/scene-store-server.ts`、`packages/mcp/src/storage/sqlite-scene-store.ts` |
| 结构工程持久化 | 结构工程场景 revision/model hash、分析作业与结果集已落库；项目级协作权限仍未落地 | `partial` | 场景 API、`analysis_jobs`/`analysis_results` SQLite 表、生产 D01 evidence |
| 结构页本地保存 | `/struct` 使用 Editor autosave 写入浏览器 localStorage（`pascal-editor-scene`）；关闭“节点数骤降拦截”，删除节点/轴线/构件后约 1 s 自动保存；Ctrl+S 立即 flush；底部命令行显示待保存/保存中/已保存/保存失败 | `implemented` | `struct-shell.tsx`、`command-line.tsx`；浏览器实测删除后刷新不恢复、创建节点后立即 Ctrl+S 落盘 |
| 二维平面图 | 现有平面图是 SVG + React 图层，不是 PixiJS | `implemented` | `packages/editor/src/components/viewer/floorplan-preview.tsx`、`editor-2d/` |
| 三维视口 | `viewer` 已创建 `THREE.WebGPURenderer`，并有 WebGL 回退 | `unverified` | `packages/viewer/src/components/viewer/index.tsx` |
| Line2 | 未发现 `Line2`/`LineSegments2` 结构杆件渲染；WebGPU 兼容性未验证 | `unverified` | 全仓库无结构杆件 Line2 实现 |
| PixiJS | 未安装 | `target` | 根与 `apps/editor` 的 `package.json` 均无 `pixi.js` |
| 结构节点定义 | 已有 `structural-grid` 节点，含轴线、轴号、捕捉、平面图渲染 | `implemented` | `packages/nodes/src/structural-grid/` |
| 结构节点实体 | 新增 `structural-node`，包含坐标、编号、支座状态和平面实心圆点；轴网同步会为每个交点生成节点 | `implemented` | `packages/core/src/schema/nodes/structural-node.ts`、`packages/nodes/src/structural-node/`、`axis-grid-sync.ts` |
| 节点布置（YJK 模式） | `node.new` 先打开节点布置面板：编号前缀/起始编号、上节点高（相对层底）、节点半径、支座、显示编号、布置后锁定；点“开始布置”后画布连续点布，编号自动跳过已占用值；后续柱/梁点选布置会跟随节点标高 | `implemented` | `struct-node-place-dialog.tsx`、`struct-store.ts`、`structural-node/floorplan-tool.tsx`、`struct-member-placement-bar.tsx`；浏览器实测 Z10/Z11、上节点高 1.200 m、R120 mm、铰支，1.2 m 节点上柱长 1.3 m |
| 上节点高（YJK 模式） | `node.topElevation*` 打开独立面板：单点设置选中/全楼层节点；两点按两端高差形成坡度并插值同一轴线中间节点；三点形成斜面，可应用三点或全楼层，也可使用选择点当前标高 | `implemented` | `struct-node-elevation-dialog.tsx`、`node-editing.ts`；4 项场景测试 + 4743 浏览器实测 1.2 m |
| 节点属性上节点高 | 节点属性面板新增“上节点高 (m，相对层底)”字段，可直接改单个节点标高 | `implemented` | `struct-node-inspector.tsx`；浏览器实测 1.2 |
| 节点等分 | 选中轴线后，轴属性面板可“按数量”或“按间距”沿轴线生成节点；包含端点、自动跳过已有节点并按 N 编号 | `implemented` | `struct-axis-inspector.tsx`、`node-editing.ts`；浏览器实测 2 等分生成 1 个中间节点、跳过 2 个端点 |
| 层间节点归并 | 节点编辑表可选择目标楼层，将其他楼层节点按平面容差对齐到目标楼层最近节点，保留各自标高；锁定/无匹配节点跳过 | `implemented` | `struct-node-edit-dialog.tsx`、`node-editing.ts`；场景测试对齐 1 个、跳过 1 个 |
| 节点集中荷载 | `structural-node` 新增 `loads`：工况 + Fx/Fy/Fz/Mx/My/Mz；节点属性面板可添加/编辑/删除；分析模型导出节点荷载并统计 `nodeLoadCount` | `implemented` | `structural-node.ts`、`struct-node-inspector.tsx`、`analysis-model.ts`；分析模型测试 + 4743 浏览器实测 live/Fx=10 |
| 弹性支座 | 支座类型新增 `elastic`；节点可设 3 个平动刚度 Kx/Ky/Kz（kN/m）与 3 个转动刚度 Krx/Kry/Krz（kN·m/rad）；分析模型导出刚度并统计 `elasticSupportCount`，刚度全 0 时给警告 | `implemented` | `structural-node.ts`、`struct-node-inspector.tsx`、`analysis-model.ts`；分析模型测试 + 4743 浏览器实测 |
| 主从节点 | 节点可指定同层主节点与受约束自由度 Ux/Uy/Uz/Rx/Ry/Rz；分析模型导出主从关系和 `masterSlaveCount`，校验主节点缺失、自指、循环和空自由度 | `implemented` | `structural-node.ts`、`struct-node-inspector.tsx`、`analysis-model.ts`；分析模型测试 + 4743 浏览器实测 |
| 节点右键菜单 | 选中结构节点后右键提供复制并放置、移动、隐藏、支座和删除；菜单在画布内触发并阻止默认右键菜单 | `implemented` | `struct-node-context-menu.tsx`；浏览器实测菜单包含完整操作项 |
| 轴线交点节点 | 单线、矩形、三点圆弧提交时自动为端点和与已有轴线的交点生成 `structural-node`；“形成交点”可补齐已有轴线交点 | `implemented` | `structural-grid/coordination.ts`、`structural-grid/floorplan-tool.tsx`、`command-defs.tsx`；交点测试通过 |
| 轴线显示与轴号 | 轴线默认不显示起终点轴号；选中轴线可编辑轴号、起终点显示开关，并可批量按竖向数字/横向字母重编号 | `implemented` | `structural-grid.ts`、`struct-axis-inspector.tsx`、`axis-numbering.ts`；浏览器实测批量编号后显示 E |
| 轴线几何编辑 | 选中轴线出现起终点手柄，可拖动端点；拖拽中 Shift 锁水平/竖直、Alt 绕过捕捉；属性面板可直接输入起点/终点 X/Y，实时显示长度与角度，并提供水平、竖直、交换端点 | `implemented` | `structural-grid/floorplan-affordance.ts`、`structural-grid/geometry.ts`、`struct-axis-inspector.tsx`；浏览器实测端点由 (15,0) 拖到 (15,6.03)，一次 Undo 回退 |
| 轴网编辑表 | `grid.edit` 打开当前楼层/全楼轴网表，逐条修改轴号与起终点坐标，应用时合并为一次场景事务；`grid.editScope` 切换范围 | `implemented` | `struct-axis-edit-dialog.tsx`、`struct-store.ts`；浏览器实测改终点 Y 为 12 后长度 19.209 m，Undo 一次回退 |
| 清理网点 | `grid.clean` 删除零长度轴线、完全重复轴线，以及不再落在任何轴线上的自动生成节点；用户手工节点不删除 | `implemented` | `structural-grid/node-sync.ts`、`lib/struct/axis-cleaning.ts`；浏览器实测删除零长度轴线，单元测试 4 项 |
| 轴线打断 | `grid.split` 与属性面板“打断”在与其他轴线的交点处把所选轴拆成多段，所有分段保持原轴号，打断后自动选中第一段；无交点时只提示不改模型 | `implemented` | `lib/struct/axis-split.ts`、`structural-grid/geometry.ts`；浏览器实测 0–15 m 轴在 x=6、12 处断为 3 段 |
| 轴线命名 | `grid.name` 打开命名面板：竖轴数字/横轴字母、全部数字、全部字母三种规则；起始值、前后缀、跳过 I/O/Z、竖轴右起、横轴上起、保留附加轴号；应用前逐条预览当前轴号→新轴号 | `implemented` | `struct-axis-naming-dialog.tsx`、`axis-numbering.ts`；单元测试 11 项 + 浏览器实测 |
| 命名合并轴段 | 命名按“共线且相接”合并逻辑轴线（含斜交轴），正交轴网与打断产生的分段共用同一个轴号，不会把同一条轴编成 1、2、3 | `implemented` | `axis-numbering.ts` 的 `collectLogicalAxes`；11 项命名测试 |
| 场景更新契约 | 批量改名改为场景要求的 `{ id, data: { label } }`；端点拖动中的节点位置同样改为 `{ id, data: { position } }`，修复“应用命名”报错不生效和拖动节点更新异常 | `implemented` | `struct-axis-naming-dialog.tsx`、`structural-grid/floorplan-affordance.ts`；浏览器应用 5 条轴线/8 个轴段并一次 Undo 回退 |
| 命令行焦点 | 命令执行后输入框自动失焦，`Esc`/`X`/`Y` 回到画布工具，不再被命令输入框吞掉 | `implemented` | `command-line.tsx` |
| 轴线变换 | `grid.transform` 支持移动、复制、偏移（法向）、旋转（角度+基点）、镜像（竖线 X / 横线 Y）；作用于选中轴线，未选中时作用于当前楼层全部轴线；移动类变换在同一事务内带动生成的端点节点、引用构件端点与板 polygon/holes | `implemented` | `struct-axis-transform-dialog.tsx`、`lib/struct/axis-transform.ts`；12 项场景测试含一次 Undo 和锁定对象阻止 |
| 轴线延伸 | `grid.extend` 把轴线两端延伸到最近的相邻轴线交点；实际移动端点时与手工端点编辑共用 `applyAxisEndpointPatchesInScene`，同步受管节点、引用梁墙端点和板边界；锁定依赖使整次操作不改模型 | `implemented` | `lib/struct/axis-transform.ts`、`packages/nodes/src/structural-grid/floorplan-affordance.ts`；场景测试验证板/节点/梁同步 |
| 轴线合并 | `grid.merge` 只合并共线且几何路径连续的分段；路径未改变时保留板边界和节点位置。存在几何间隙时阻止桥接，不写模型 | `implemented` | `lib/struct/axis-transform.ts`；相接路径板边界不变与间隙阻止测试 |
| 轴线修剪 | `grid.trim` 把轴线两端修剪到最外侧的内部交点，并在与手工端点编辑相同的单事务 helper 中更新受管节点、引用梁墙端点和板 polygon/holes；无关板顶点不动，锁定依赖整次阻止 | `implemented` | `geometry.ts`、`axis-transform.ts`、`structural-grid/floorplan-affordance.ts`；浏览器实测轴 0–6→1–5、节点/梁/板同步且刷新保持 |
| 轴线尺寸标注 | `grid.dimensions` 生成第一道分段、第二道分段（≥4 轴时每两跨）与总尺寸，横竖两个方向各三道；重复执行替换旧标注；新增 `structural-dimension` 节点并复用建筑尺寸几何（延长线、箭头/斜线、文字） | `implemented` | `axis-dimensions.ts`、`structural-dimension/`；2 项场景测试 + 浏览器生成 8 段尺寸 |
| 气泡偏移与引线 | 轴线可设置气泡法向偏移、沿线偏移、文字角度；偏移时自动绘制引线，文字按角度旋转 | `implemented` | `structural-grid.ts`、`structural-grid/floorplan.ts`、`struct-axis-inspector.tsx` |
| 轴线锁定/图层/线型 | 轴线可锁定，锁定后拖动、变换、延伸、修剪、合并与删除均跳过；可设图层名与点划/虚线/实线三种线型 | `implemented` | `structural-grid.ts`、`floorplan-affordance.ts`、`axis-transform.ts`；锁定跳过测试 |
| 径向圆弧轴网 | `grid.radialGrid` 打开参数化圆弧轴网：圆心、半径组、角度范围、分段数，生成径向轴 + 环向弧（`createPolarGrid`） | `implemented` | `cmd-defs`、`axis-grid-tool.tsx`、`struct-domain/axis-grid.ts` |
| 节点编辑表 | `node.edit` 打开节点表：编号前缀/起始/排序、逐条坐标/支座/半径、归并容差、清理孤立节点、显示全部节点 | `implemented` | `struct-node-edit-dialog.tsx`、`node-editing.ts`；3 项场景测试 |
| 节点锁定 | 节点新增 `locked` 字段；锁定后属性输入、右键移动/隐藏/支座/删除、批量支座、平移/复制、归并与孤立清理全部跳过；`node.lock` 与右键菜单可批量锁定/解锁 | `implemented` | `structural-node.ts`、`struct-node-inspector.tsx`、`struct-node-context-menu.tsx`、`node-editing.ts` |
| 节点批量平移/复制 | 节点编辑表新增 ΔX/ΔY/ΔZ，支持对选中节点（未选中则全楼层）平移或复制，复制自动分配新编号 | `implemented` | `struct-node-edit-dialog.tsx`、`translateNodes`；2 项场景测试 + 浏览器平移 41 个节点并 Undo |
| 节点统计 | 节点表头部实时显示总数、自由/铰/固/滚数量、锁定数与当前容差下的重复数 | `implemented` | `nodeStatistics`；场景测试 |
| 多选支座 | 支座命令对全部选中的结构节点生效，锁定节点自动跳过 | `implemented` | `setStructuralSupport` |
| 节点下传 | `node.down` 把选中节点（未选中则全楼层）复制到下一层相同平面位置；下传点打断梁墙时按原构件参数 t 排序分段，梯形/部分线载逐段插值并生成独立 load id，仅外端保留原释放，内部连接为 rigid | `implemented` | `node-editing.ts`、`member-editing.ts`、`command-defs.tsx`；非等值荷载总量守恒、内部 rigid、外端释放与无悬空引用测试 |
| 节点对齐 | `node.alignX` / `node.alignZ` 把选中节点对齐到第一个节点的 X 或 Y（平面 Z），锁定节点跳过 | `implemented` | `node-editing.ts`；场景测试 |
| 归并范围 | 选中两个及以上节点时，`node.merge` 只归并所选节点；未选中时仍作用于整层 | `implemented` | `mergeStructuralNodes(..., ids)`；场景测试 |
| 轴网拼接 | `grid.stitch` 按源基点、目标基点与角度拼接选中轴网，默认保留原轴网，可改为移动 | `implemented` | `axis-transform.ts`、`geometry.ts`；拼接几何测试 + 浏览器面板 |
| DXF 导入导出 | 导出包含轴线（LINE + 轴号 TEXT）和尺寸链（延长线、尺寸线、45° 斜线、尺寸文字，尺寸层）；导入支持 LINE、ARC（按 15° 折线化）、LWPOLYLINE、`INSERT` 块（含缩放/旋转，块内实体不重复计入）、轴号 TEXT 就近匹配，导入后自动在端点与交点生成结构节点 | `implemented` | `axis-dxf.ts`、`struct-axis-edit-dialog.tsx`；8 项 DXF 测试 + 浏览器导出下载、导入 12 条轴线并 Undo |
| 轴线节点跟随 | 轴线端点移动时，网格工具生成的节点随端点移动；编辑后与其它轴线的新交点自动补节点；普通结构节点不受影响 | `implemented` | `structural-grid/node-sync.ts`；`bun test src/structural-grid` 29 项通过 |
| 节点大小 | 新节点支持默认半径设置，画布控制条显示 `节点 ... mm`；节点属性可单独调整半径 | `implemented` | `use-struct-preferences.ts`、`structural-node/floorplan-tool.tsx`、`struct-node-inspector.tsx`；浏览器实测节点大小控件 |
| 结构构件定义 | `structural-member`：梁/柱/支撑/桁架，3D 两端点、截面、材料、截面转角、竖向/水平偏心、i/j 端释放；柱在 2D 按实际截面画矩形/圆形 footprint，3D 按宽度/直径生成 box/cylinder；两点节点捕捉布置 + 属性面板 | `implemented` | `structural-member.ts`、`structural-member/section.ts`、`structural-member/renderer.tsx`、`structural-member/floorplan.ts`；7 项截面/布置测试 + 浏览器圆柱 D600/C35 实测 |
| 结构板定义 | `structural-slab`：polygon、板厚默认 120 mm、板顶标高缺省跟随层顶、材料默认 C30；平面矩形两对角点与多边形连续点选，顶点复用结构节点/轴线捕捉；2D 轮廓+`h=120` 板厚标注，3D 按轮廓向下挤出实体；属性面板可改板厚/材料/标高并逐点编辑轮廓 | `implemented` | `structural-slab.ts`、`structural-slab/floorplan-tool.tsx`、`structural-slab/geometry.ts`、`struct-slab-inspector.tsx`；6 项节点测试 + 浏览器矩形/5 点多边形布置，截图 `docs/struct-slab-3d.png` |
| 房间生成楼板 | 按 YJK-MODEL 2022.1 第六节做法，以结构墙/主梁为房间边界，闭合房间一次生成一块 `structural-slab`；手工板按形心优先保留，匹配的自动板只刷新轮廓并保留洞口/板厚/材料，失效自动板删除 | `implemented` | `slab-layout.ts`；4 项场景测试 + 浏览器画 4 道墙生成 1 块房间板，截图 `docs/struct-slab-yjk-3d.png` |
| 板洞 | 选中板后可布置矩形洞（两对角点）或圆形洞（圆心+半径点）；洞口写入 `holes`，2D 轮廓按 evenodd 挖洞、3D ExtrudeGeometry 生成真实孔洞；重复生成楼板和板查询保留/报告洞口 | `implemented` | `structural-slab/floorplan-tool.tsx`、`structural-slab/geometry.ts`、`struct-slab-inspector.tsx`；3 项板洞测试 + 浏览器矩形洞/圆洞各 1 个 |
| 板净面积与查询 | 板属性、构件统计、分析模型均按 `毛面积 - 洞口面积` 计算净面积；`slab.query` 报告板厚、材料、板顶、净面积、洞口数和自动/手工来源 | `implemented` | `structural-slab.ts`、`member-editing.ts`、`analysis-model.ts`；浏览器查询 2 个洞口，分析导出净面积 |
| 板面荷载 | 每块板可设恒载 `qD`、活载 `qL`（kN/m²）、自动计自重和导荷方式（自动/对边/梯形三角/周边）；构件统计与分析模型导出恒载、活载、板自重及合计；板厚 0 保留荷载但 2D 仅画虚线导荷轮廓、3D 不生成板体。导荷方式目前只记录/导出，尚未分配到周边梁墙 | `implemented` | `structural-slab.ts`、`struct-slab-inspector.tsx`、`analysis-model.ts`；浏览器设置 1.5/2.0 kN/m²、验证厚 0 仅导荷与 JSON 荷载合计 |
| 构件编辑表 | `member.edit`：类型/截面/材料/i-j 端释放逐条编辑；批量截面、材料、释放、平移/复制、镜像、阵列、旋转（基点+角度）、偏移（法向）、打断、共线合并；打断与节点下传共用线载守恒分段 helper；统计总数、分类数量、总长 | `implemented` | `struct-member-edit-dialog.tsx`、`member-editing.ts`；14 项场景测试 |
| 沿轴布置 | `member.alongAxis`：批量布梁/布柱；范围支持全楼层、仅选中对象、窗口矩形（X/Y 最小最大）；可选标高、柱高、截面、材料；同端点同类型构件自动跳过 | `implemented` | `member-layout.ts`、`struct-member-layout-dialog.tsx`；3 项场景测试 |
| 柱布置（YJK 模式） | `member.column` 先打开“柱截面定义 + 布置参数”面板：截面类型（矩形/圆形混凝土、H 型钢、箱形钢、圆钢管）、尺寸、材料、截面库；布置参数含层高、基底标高、沿轴偏心、偏轴偏心、轴转角、柱底高。柱底跟随所点节点标高；点“开始布置”后在节点上连续点布，同一节点重放替换原柱 | `implemented` | `struct-column-dialog.tsx`、`struct-store.ts`、`structural-member/floorplan-tool.tsx`、`column-layout.ts`；8 项测试 + 浏览器 1.2 m 节点上柱长 1.3 m、D600/D700 两柱 |
| 梁布置（YJK 模式） | `member.beam` 先打开“梁截面定义 + 布置参数”面板：截面类型（矩形/T 形混凝土、H 型钢、箱形钢、圆钢管）、尺寸、材料、截面库；布置参数含偏轴距离、梁顶标高 1/2（相对节点/层顶）、轴转角。点“开始布置”后两节点成梁，梁端点跟随节点标高；也支持按全部/选中轴线批量布置（批量仍按层顶） | `implemented` | `struct-beam-dialog.tsx`、`struct-store.ts`、`member-layout.ts`、`structural-member/floorplan-tool.tsx`；6 项布置/截面测试 + 浏览器 T 形 600×800×300×120/C35 布梁 |
| 构件节点捕捉 | 柱布置接受当前楼层内低于层顶的节点，柱底取节点标高并自动生成柱顶节点；梁点选布置按两端节点标高加梁顶标高 1/2，梁批量布置按层顶节点分段并补节点 | `implemented` | `column-layout.ts`、`member-layout.ts`、`structural-member/floorplan-tool.tsx`；节点落位与上节点高测试 |
| 墙构件 | `member.wall`：墙作为杆系族中的墙类型，沿轴线从基底标高建到层顶，带墙厚与墙高；2D 灰线+标注，3D 按长度×墙高×墙厚生成墙板；构件表可改类型/材料/厚度 | `implemented` | `structural-member.ts`、`structural-member/renderer.tsx`、`member-layout.ts`、`struct-member-layout-dialog.tsx`；1 项布置测试 |
| 楼层参数（组装） | `level.params` 在“组装”页签统一设置各楼层层高与基底标高，一次保存全部楼层 | `implemented` | `struct-level-params-dialog.tsx`、`ribbon-config.ts` |
| 柱点选布置 | “开始布置”后画布点选节点逐根布柱：捕捉 0.6 m 内节点，柱高取该楼层层高，点完继续放置下一根；同一节点再次布置时替换已有柱（YJK 的“一节点一柱”） | `implemented` | `structural-member/floorplan-tool.tsx` |
| 梁布置交互 | 面板“开始布置”后画布点选：两节点成梁并链式连续；点轴线取最近两节点间一跨；梁顶标高 1/2 分别作用在起点/终点，支持偏轴距离与轴转角；悬停节点/轴线高亮脉冲 | `implemented` | `structural-member/floorplan-tool.tsx` |
| 墙点选布置 | `member.wall` 画布两点连续布墙，墙高取层高、墙厚默认 200 mm | `implemented` | `structural-member/floorplan-tool.tsx` |
| 构件放置条 | 柱显示“柱截面”条，梁显示“梁截面”条，可直接切换各自截面库中的定义与材料，并打开“截面定义…”面板；节点显示“节点”条（编号/上节点高/半径/支座），可打开“节点参数…”；墙/支撑/桁架仍用通用“放置类型”条 | `implemented` | `struct-member-placement-bar.tsx`、`struct-store.ts`、`use-struct-preferences.ts` |
| 构件批量编辑 | 构件表支持截面/材料/端释放、平移/复制、镜像、阵列、旋转、偏移、打断、共线合并 | `implemented` | `struct-member-edit-dialog.tsx`、`member-editing.ts`；5 项测试 |
| 截面材料库 | HN/HW/HM（GB/T 11263 名义尺寸）、方管、圆钢管、混凝土矩形、圆柱、T 形混凝土共 14 个预设；Q235~Q420、C30~C40、6061-T6 材料；柱/梁面板支持任意尺寸输入；按名义尺寸计算 A/Ix/Iy/重量（未计圆角） | `implemented` | `section-library.ts`、`struct-column-dialog.tsx`、`struct-beam-dialog.tsx`；8 项测试 |
| 分析模型组装 | 节点+构件+板+截面+材料+支座前处理检查，导出 analysis-model.json（含转角/偏心/端释放与 slabs 的轮廓/洞口/板厚/板顶标高/毛面积/净面积/房间来源） | `implemented` | `analysis-model.ts`、`struct-analysis-model-dialog.tsx`；4 项测试 + 浏览器仅含板模型 JSON 导出 |
| 三维主题 | 新增 `graphite` 深灰主题，背景 `#2b3038` 与 2D 画板一致；结构页签持续校正主题，避免被持久化覆盖 | `implemented` | `packages/viewer/src/lib/scene-themes.ts`、`struct-shell.tsx`；刷新截图取像素验证 |
| 场地处理 | 结构工程启动时把 Site 节点设为不可见，保留根节点与楼层树；场地不参与本项目功能 | `implemented` | `struct-shell.tsx`；3D 场地三角面隐藏 |
| Ribbon 排版 | 有 columns 的分组按列数计算宽度（每列 60px），小按钮 30px 高、56px 宽，两行完整显示；Ribbon 内容高 92px；构件组 10×2 | `implemented` | `ribbon.tsx`、`ribbon-config.ts`；浏览器截图核对 |
| 建模命令切换 | 任意命令执行前统一关闭旧弹窗、轴网面板和旧绘制工具；梁/柱/节点面板打开即进入画布布置，不再需要“开始布置”；面板参数修改继续即时同步 | `implemented` | `struct-store.ts`、`command-defs.tsx`、三个布置面板；浏览器验证梁→柱→构件编辑→墙切换均关闭旧面板 |
| 梁 2D 截面宽度 | 梁平面由粗线改为真实米制梁带：按截面 `b/h` 和转角投影宽度，支持 `offsetZ` 正左法向偏心；带填充 polygon、独立轮廓、透明命中线和截面文字 | `implemented` | `structural-member/floorplan.ts`；4 项测试 + 浏览器 DOM 实测 HN400×200 宽 `0.200 m` |

## IFC 导入浏览器验收（2026-10-23）

| 场景 | 观察结果 | 证据 |
|---|---|---|
| IFC2X3 `01-duplex.ifc` | 首次创建返回 255 个节点；经编辑器首次加载与首次 autosave 的正常 graph 规范化后稳定为 253 个节点、79 个 `imported-mesh`、4 层；reload 后不变，改名、显隐和 2D 几何仍保留 | `scripts/verify-struct-ifc-import.mjs` 真实浏览器运行 |
| IFC4 `10-sample-house.ifc` | 创建 55 个节点、26 个 `imported-mesh`、16 个 native geometry、2 层，并进入独立新工程 | `scripts/verify-struct-ifc-import.mjs` 真实浏览器运行 |
| 隔离与异常输入 | 原 baseline graph 不变；无效 `.txt` 与截断损坏的 `.ifc` 均显示错误且不创建工程；相关 console/page errors 为 0 | `scripts/verify-struct-ifc-import.mjs` 真实浏览器运行 |

验收脚本默认连接 `http://localhost:3010`，需已有当前源码服务；也可通过 `STRUCTWEB_BASE_URL` 指定地址。残余限制：`imported-mesh`/IFC 内容目前不进入结构构件统计，也不进入 analysis-model 参数化映射，不能据此推出完整分析模型支持。

## A04/A08/C07 验收证据（2026-10-21）

| 项 | 状态 | 关闭证据 |
|---|---|---|
| A04 轴线修剪/端点联动 | 关闭 | 单元测试覆盖 trim/extend/transform、板边界、引用梁端、一次 Undo 与锁定阻止；浏览器 `grid.trim` 后轴 `[0,0]–[6,0]→[1,0]–[5,0]`，受管节点、梁两端和板顶点同步，Ctrl+S 刷新保持，无关顶点不动 |
| A08 构件拆分物理一致性 | 关闭 | 非等值梯形载 `1→2` 在 x=3 拆为 `1→1.5`、`1.5→2`，总积分 9；多交点测试另外覆盖 0、2、4、6 三段；各段 load id 独立，内端 rigid、外端仅首尾保留 pinned/fixed，刷新/分析 JSON 无悬空引用 |
| C07 层高与基底 | 关闭 | 浏览器将层高/基底设为 5/1 后，柱、墙、节点、板顶同步；独立板相对基底仍为 2 m，其他楼层不变，Ctrl+S 刷新保持 |

本轮回归与部署事实：

- `bun test packages/nodes/src/structural-grid packages/nodes/src/structural-member`：61/61 通过。
- `bun test apps/editor/lib/struct`：235/235 通过。
- `bun run --cwd packages/nodes build`、`bun run --cwd apps/editor check-types`：退出码 0；修改文件 Biome 检查通过。
- `.\scripts\deploy-structweb.ps1`：退出码 0；镜像 `sha256:6877dfd0f4ebb97bd08a11ba2813ac9fc6e97e626c3605612b243d697f5d4ca9`；应用容器 healthy，4743 三路由均 200。
- 浏览器证据：`artifacts/structweb-a04-c07-a08/2026-10-21T03-55-43-390Z.json`；截图同名 `.png`；三个临时工程均已 DELETE 且 GET 返回不存在；控制台错误、页面错误、失败响应均为 0。
- 本轮部署源码指纹：`54EAFA91480482D7FC00F14717E6AE06DD4EBA8B5C8CC474893216515D216379`（6 个运行时源码文件的 SHA-256 聚合）。

## 已知缺口（2026-10-20）

| 项 | 状态 | 说明 |
|---|---|---|
| 板类型与全房间洞 | `target` | 现浇空心板、压型钢板、叠合板、柱帽、无梁楼盖尚未建立各自的截面/构造模型；全房间洞与板间集中/线荷载尚未接入 |
| 2D 场地边界 | `unverified` | Site 的 3D 表面已隐藏，但 2D 仍有三角形边界显示，来源图层未定位 |
| 自定义截面 | `implemented` | 柱面板支持矩形/圆形混凝土、H 型钢、箱形钢、圆钢管；梁面板支持矩形/T 形混凝土、H 型钢、箱形钢、圆钢管的自定义尺寸；墙仍使用预设列表 |
| YJK 32 类标准截面 | `target` | 当前柱面板覆盖 5 类、梁面板覆盖 5 类常用截面；L 形、十字形、钢管混凝土、格构式等其余类型尚未接入 |
| 上节点高联动 | `partial` | 柱点选/批量布置、梁点选布置已跟随节点标高；梁的按轴线批量布置仍按层顶标高，尚未逐节点插值 |
| 墙洞/隔墙/斜墙 | `target` | Ribbon 仍为规划项 |
| 求解器 | `partial` | PyNite 3.2.0 线性静力作业、组合计算与结果回填已通过生产验收；H/圆钢管 staged 强度利用率已实现（固定 `incomplete`），模态、屈曲、二阶和完整设计验算仍为 `target` |
| 杆端释放/刚接 | `node.release` / `node.rigid` 现在作用于选中构件两端，设为铰接/刚接 | `implemented` | `setMemberReleases`；场景测试 |
| 构件截面/材料库 | 14 个截面预设：HN/HW/HM（按 GB/T 11263-2017 名义尺寸）、□方管、Φ圆钢管、混凝土矩形、圆柱、T 形混凝土；8 种材料：Q235/Q355/Q390/Q420、C30/C35/C40、6061-T6。柱/梁面板可自定义尺寸；按名义尺寸计算 A、Ix、Iy、理论重量（未计圆角，界面注明），构件属性与构件表下拉选择并显示截面特性 | `implemented` | `section-library.ts`、`struct-column-dialog.tsx`、`struct-beam-dialog.tsx`、`struct-member-inspector.tsx`、`struct-member-edit-dialog.tsx`；8 项截面/布置测试 + 浏览器圆柱 D600/C35、T 形梁 600×800×300×120/C35 |
| 分析基准 | 门式刚架解析参考与 PyNite 实际值逐组合比对，覆盖反力、位移、杆端弯矩和平衡残差 | `implemented` | `scripts/verify-struct-analysis-closed-loop.mjs`、生产 D01 evidence、43 项 worker pytest |
| 设计文档 | v8.8 设计稿、PLAN、OPEN_SOURCE_STACK、命令表并存，但版本与实现状态不一致 | 文档事实 | `docs/design/web-fea/` |

## 3. 不能从当前事实推出的结论

- 不能推出“已经有结构建模能力”。当前是可演示壳和建筑场景，不是结构工程模型。
- 不能推出“已经具备完整分析能力”。当前只验收了线性静力、组合和 H/圆钢管 staged 强度利用率；模态、屈曲与完整设计验算仍是目标能力。
- 不能推出“已经支持 PyNite 模态/屈曲/二阶”。第三方 README 不等于本项目验收。
- 不能推出“10 万杆件 60fps”。没有性能基准、硬件口径和浏览器记录。
- 不能推出“可以通过结构工程审查”。虽然已有 revision、model hash、不可变 result-set、stale 保护和固定为 `incomplete` 的强度 `CheckSet`，但后者不覆盖稳定性、挠度、连接、疲劳等内容，也没有正式设计报告。

## 4. 维护方式

1. 命令状态由 `command-defs` 或生成的 manifest 导出，不再手填“已实现”。
2. 每次合并改变结构能力的 PR，必须同步更新本文件对应行。
3. 演示数据、固定结果、mock 作业必须在界面上有醒目标识。
4. 本文件只记录事实；目标、差距和计划写入 `PLAN.md`。
