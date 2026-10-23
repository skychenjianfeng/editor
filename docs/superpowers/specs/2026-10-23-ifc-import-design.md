# StructWeb IFC 导入与编辑流程设计

## 目标

在 StructWeb 主系统中提供完整的 IFC 文件导入流程：

1. 从文件选择器或拖放区打开 `.ifc` 文件。
2. 在浏览器内解析 IFC2X3 / IFC4，并显示转换进度、构件统计和错误。
3. 转换完成后默认创建一个独立的 StructWeb 工程，不覆盖当前工程。
4. 自动进入现有 2D/3D 工作区，复用现有查看、编辑、撤销、保存和版本能力。

## 非目标

第一阶段不包含：

- 将 IFC 构件映射为 `structural-member`、`structural-node` 或 `structural-grid`。
- IFC 模型参与结构构件统计、结构分析模型或计算。
- 服务端 IFC 转换、异步任务队列或超大型模型分块处理。
- 任意三角网格的布尔运算、拓扑重建或 CAD 级精修。
- 替换已有工程的 IFC 导入模式。

## 用户流程

### 导入入口

- File Ribbon 增加可用的“导入 IFC”命令。
- 新建结构工程页的“导入模型”起模方式在工程创建后进入同一个导入器。
- 导入器支持点击选择文件和拖放文件。
- 默认工程名为 IFC 文件名去掉 `.ifc`；允许用户修改。

### 转换与预览

导入器状态：

1. `idle`：等待文件。
2. `reading`：读取文件。
3. `converting`：初始化 WebIFC WASM 并转换，显示阶段文字和进度。
4. `review`：显示楼层、节点数、类型统计、转换警告和错误。
5. `creating`：创建 StructWeb 工程并保存初始图。
6. `error`：显示可操作的错误；允许重新选择文件。

只有至少包含一个可渲染节点时才允许创建工程。转换过程中允许取消，取消后不得创建或保存工程。

### 创建工程

- 默认创建新的云端 StructWeb 工程，并同时写入本地工程缓存。
- 成功后导航到 `/struct/:projectId`。
- 当前打开的其他工程不修改、不删除、不覆盖。
- 创建后的 IFC 场景就是普通 StructWeb 场景，后续保存和版本恢复沿用现有机制。

## 架构

### 复用

- 文件解析使用 `@pascal-app/ifc-converter` 的 `convertIfcToPascal`。
- WebIFC WASM 资源由新构建脚本复制到 `apps/editor/public/web-ifc/`。
- 工程创建、云端保存和本地缓存复用 `apps/editor/lib/struct/project-*`。
- 3D 渲染、2D 平面图、选择、移动和属性面板复用现有 registry 驱动系统。

### 新模块

#### `apps/editor/lib/struct/ifc-import.ts`

纯业务编排，不直接渲染 UI：

- 验证文件名和空文件。
- 调用 IFC 转换器。
- 规范化转换结果为可创建的 StructWeb `SceneGraph`。
- 确保根 `site`、`building`、`level` 层级存在。
- 写入 `structProject` 工程元数据。
- 返回节点统计、楼层统计、警告和规范化后的图。

#### `apps/editor/components/struct/struct-ifc-import-dialog.tsx`

负责：

- 文件选择、拖放和工程名输入。
- 转换进度和取消。
- 转换结果摘要。
- 创建工程并跳转。
- 错误展示和重试。

#### `apps/editor/scripts/copy-web-ifc-wasm.mjs`

从已安装的 `web-ifc` 包复制 WASM 到编辑器静态资源目录，由 dev/build 前置脚本调用。

### Ribbon 与命令

- 新增实际可执行的 `file.ifcImport` 命令。
- `file.import` 如仍保持规划态，不得伪装为已支持 IFC；IFC 使用独立命令和明确名称。
- 现有 `io.ifc` 仍是导出命令，不改其语义。

## IFC 数据映射

沿用转换器当前能力：

- `IfcSite`、`IfcBuilding`、`IfcBuildingStorey` → Site / Building / Level。
- `IfcWall`、`IfcDoor`、`IfcWindow`、`IfcSlab`、`IfcColumn`、`IfcSpace` → 对应参数化 Pascal 节点。
- IFC 属性集、GlobalId、ExpressID、材料信息保留在节点 metadata。
- 梁、楼梯、幕墙、栏杆、覆盖层及无法恢复参数的构件 → `imported-mesh`。
- 导入实体只用于保真查看和现有通用编辑，不在 UI 中伪装成可计算结构构件。

### 层级规范化

- 转换结果已有唯一根 Site 时继续使用。
- 没有 Site 时创建一个空轮廓 Site。
- 有多个根 Site 时创建一个新的空轮廓根 Site，把它们作为子节点。
- 确保可以被 StructWeb 工程元数据和现有场景加载器接受。

## 编辑行为

转换成功后，以下操作复用当前编辑器：

- 2D/3D 查看和楼层切换。
- 选择、框选、移动、旋转。
- 名称、可见性、材质等已有属性能力。
- 删除和撤销/重做。
- 自动保存、刷新恢复和工程版本历史。

对于参数化节点，使用其现有属性面板。对于 `imported-mesh`：

- 支持选择、移动、旋转、改名、可见性和删除。
- 不承诺支持截面修改、端点参数化或结构计算属性。
- 属性面板必须明确标记为“IFC 导入实体”。

## 错误处理

- 非 `.ifc` 文件：在选择阶段拒绝。
- 空文件或读取失败：不进入转换。
- WASM 初始化失败：说明是解析器资源加载失败，并允许重试。
- IFC 语法不合法或超出 WebIFC 支持范围：显示转换错误，不创建工程。
- 转换结果无可见节点：禁止创建工程。
- 云端创建失败：保留已转换结果以便重试，不跳转。
- 用户取消或离开页面：取消当前转换结果，不写入云端或本地缓存。

## 测试与验收

### 自动测试

- 转换结果规范化：
  - 无 Site 时补齐根 Site；
  - 多 Site 时创建根容器；
  - 写入工程元数据后仍保留 IFC metadata。
- 创建工程：
  - 导入结果创建独立工程；
  - 当前工程数据不变；
  - 本地缓存和云端图一致。
- UI 状态：
  - 文件选择、拖放、非法扩展名；
  - 转换进度、取消、错误、无几何阻止创建；
  - 预览统计正确。
- WebIFC：
  - 使用仓库内 IFC2X3 和 IFC4 fixture 验证真实转换。

### 浏览器验收

使用真实 Chromium 和真实 `.ifc` 文件：

1. 从 File Ribbon 打开 IFC 导入器。
2. 选择或拖入 IFC2X3 与 IFC4 文件。
3. 看到进度、统计和楼层信息。
4. 创建后进入新工程并看到 3D 模型。
5. 切换到 2D，确认模型和楼层可见。
6. 修改一个可编辑实体名称或位置，保存并刷新，修改仍存在。
7. 验证原工程没有被修改。
8. 验证损坏 IFC 不会创建工程。

## 验收标准

- StructWeb 主系统内可直接打开 IFC 并创建新工程。
- IFC2X3 和 IFC4 至少各有一个真实样例通过。
- 导入模型能在 2D/3D 查看。
- 至少一个参数化节点和一个导入实体可被修改并持久化。
- 导入失败不产生空工程或损坏工程。
- 原有 IFC 导出、工程加载和场景编辑测试不回归。
