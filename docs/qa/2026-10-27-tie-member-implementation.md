# 独立连墙件计算模块实施验收记录

日期：2026-10-27  
分支：`feat/scaffold-tie-member`  
模块 key：`scaffold-tie-member`

## 规范与计算边界

- 主计算依据：JGJ 130-2011《建筑施工扣件式钢管脚手架安全技术规范》。
- 构造依据：GB 55023-2022《施工脚手架通用规范》。
- 风压高度变化系数：GB 50009-2012《建筑结构荷载规范》表 8.2.1。
- 风荷载轴力固定采用 JGJ 130-2011 式 5.2.13：`Nlw = 1.4 × wk × Aw`，不混用 CECS 699-2020 的 1.5 分项系数。
- 连墙件轴力：`Nl = Nlw + N0`，单排 `N0=2.0 kN`，双排 `N0=3.0 kN`。
- 扣件连接抗滑限值：`Rc=8.0 kN`；非扣件连接不输出扣件抗滑结果。
- 覆盖面积限值：一般 40m²；双排悬挑且高度大于 50m 时为 27m²。
- 工况一致性：`layout=单排` 只能配 `scaffoldType=单排`；`layout=双排` 只能配双排落地或双排悬挑，矛盾组合抛出 `ValueError`。
- 刚性构造：GB 55023-2022 第 4.4.6 条为强制性条文，连墙件必须是可拉压的刚性构件；`软拉硬撑` 在任何高度均判定失败。JGJ 130-2011 的仅大于 24m 限制不作为通过依据。
- 构造边界：单排高度不超过 24m；`single_row_height` 仅在单排工况输出；连墙件偏离主节点不超过 300mm；必须从底层第一步纵向水平杆设置。
- 竖向间距一般不超过 3 步；双排悬挑且 `H>50m` 时按表 6.4.2 收紧为不超过 2 步（正文第 39 页）。水平间距不超过 3 跨。
- 稳定系数仅使用 JGJ 130-2011 附录 A 表 A.0.6 的 `λ=0～250` 范围（正文第 71～72 页）；`λ>250` 直接抛出包含 `250` 的 `ValueError`，不使用端点值截断。
- `tieNetArea=0` 时按毛截面计算；`tieNetArea>0` 时必须不大于该钢管毛截面 `A`，否则抛出 `ValueError`。
- 连接承载力 `Nv` 由用户按实际节点构造提供；本模块不替代预埋件、焊缝、螺栓群或建筑结构本体设计。

## TDD 与任务测试

| Task | RED 证据 | GREEN 证据 |
| --- | --- | --- |
| 1 连墙件内核 | 测试收集失败：`ImportError: cannot import name 'scaffold_tie_member' from 'calc_core'` | `20 passed in 0.04s` |
| 2 注册与套件 | `3 failed, 13 passed`：模块未注册、`KeyError`、套件仍为 9 模块 | `16 passed, 7 warnings in 5.72s` |
| 3 四视图 | `4 failed, 15 passed`：通用方框缺少“建筑墙面”专用内容 | `19 passed, 7 warnings in 1.11s` |
| 4 报告图与标签 | `3 failed, 15 passed`：图题 key 缺失、0 张专用图、参数键未中文化 | `19 passed, 7 warnings in 8.36s` |
| 主管复核修复 | `13 failed, 38 passed`：旧 key、单排高度误输出、软拉硬撑低于 24m 未拦截、单双排矛盾未校验、布尔语义和图题错误 | `51 passed, 7 warnings` |
| 规范边界补正 | `4 failed, 29 passed`：高悬挑仍按 3 步、λ=5m 被端点截断、净截面超毛截面未拒绝 | `33 passed in 0.05s` |

Task 2 的套件测试在提交时尚未包含 Task 4 的专用图，因此该阶段曾临时限定通用“必须有图”断言；Task 4 完成后已恢复为对所有 10 个模块强制要求内嵌图。Task 4 另有专用测试强制连墙件恰好生成“正立面 + 平面”两张 PNG。

主管复核修复保留上述历史覆盖事实，并新增双向单双排矛盾、软拉硬撑 `H=20m/30m`、非单排结果行、单排 `H=20m/30m`、DOCX 段落布尔语义及“三、计算图”图题测试。

## 出图与计算书

- 四视图：`elevation`、`plan`、`side`、`section`。
- 每张图的标题包含“连墙件计算 · 参数化示意（非施工图）”。
- 正立面表达建筑墙面、内外立杆投影、连墙点和竖向间距。
- 平面表达墙体、内外立杆、水平间距、外伸长度。
- 侧立面/剖面表达墙体、连墙杆、内外立杆和计算长度。
- 通用 DOCX 参数表使用中文标签，并嵌入正立面、平面两张 PNG。
- 连墙件通用 DOCX 图片章节标题为“三、计算图”；`tie_first_step`、`rigid_tie_construction` 输出“结果：满足要求/不满足要求”，不显示数值比较。
- 结果表行数必须等于 `len(results) + 1`。

## 模块结果

默认双排扣件连接共输出 10 条结果：强度、稳定、连接承载力、扣件抗滑、竖向间距、水平间距、覆盖面积、主节点偏移、首步设置、刚性构造。非扣件连接不输出扣件抗滑，共 9 条；单排高度只在单排工况追加。

新模块保持 `verified=false`。当前没有取得同参数品茗“连墙件计算”RTF，因此 PmStudio 自算结果不是品茗 oracle，不能声明已经完成逐项公式对照。

## 最终验收

- 规范边界补正 RED：`4 failed, 29 passed in 0.12s`；失败分别命中高悬挑仍按 3 步、`tieLength=5m` 未报错、净截面超毛截面未拒绝。
- 连墙件目标测试 GREEN：`33 passed in 0.06s`。
- 连墙件/注册/套件/报告相关集：`71 passed, 7 warnings in 13.10s`。
- 后端全量：`278 passed, 7 warnings in 15.01s`。
- Django：`migrate --check` 退出码 0；`makemigrations --check` 返回 `No changes detected`；`check` 返回 `System check identified no issues (0 silenced).`。
- 现有 9 模块默认结果数保持不变：`29/16/6/9/8/9/9/8/9`。
- DOCX 套件：`generated=10 results=113 failed=4`；目录内恰好 10 份 DOCX，manifest 与 QA 已重生成。
- 连墙件 DOCX：10 条结果、11 行结果表（含表头）、2 张内嵌图片，DOCX 为 85006 bytes，SHA256 `21ffed7f7c78b168fc8816832a4b014a3c56e9528edcf22ddc1dfe94a59a8ac5`；默认参数唯一失败仍为扣件抗滑 `8.87 kN > 8.0 kN`。
- 前端：6 个测试文件、10 个测试全部通过；`tsc --noEmit && vite build` 成功，2381 个模块完成转换。
- 真实 HTTP 默认 `runs`：200，10 项结果，唯一失败 `tie_coupler_slip`；新增 assumptions 已含 `λ=0～250` 边界。
- 真实 HTTP 高悬挑 `runs`：200，`tie_vertical_spacing=2.22 > 2.00` 且失败，`tie_area` 仍通过。
- 真实 HTTP 非法输入：`tieLength=5m` 返回 400 且信息含 `250`；`tieNetArea=500mm²` 返回 400 且信息含毛截面约束。
- 真实 HTTP `report.docx`：200，DOCX 文件签名 `PK`，响应 84972 bytes。
- 文件签名：PNG `89 50 4E 47`；DXF 前 200 字节含 `SECTION`；DOCX `50 4B`。

## 仍未取得的 oracle

尚未取得同参数品茗“连墙件计算”RTF，因此没有逐项 oracle 对算、没有建立容差结论，也没有把模块加入 verified 列表。PmStudio 自算、自动测试通过、DOCX/HTTP 成功都不能替代品茗 oracle 或正式工程审查。
