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
- 构造边界：单排高度不超过 24m；高度大于 24m 禁止软拉硬撑；连墙件偏离主节点不超过 300mm；必须从底层第一步纵向水平杆设置。
- 竖向间距不超过 3 步，水平间距不超过 3 跨。
- 连接承载力 `Nv` 由用户按实际节点构造提供；本模块不替代预埋件、焊缝、螺栓群或建筑结构本体设计。

## TDD 与任务测试

| Task | RED 证据 | GREEN 证据 |
| --- | --- | --- |
| 1 连墙件内核 | 测试收集失败：`ImportError: cannot import name 'scaffold_tie_member' from 'calc_core'` | `20 passed in 0.04s` |
| 2 注册与套件 | `3 failed, 13 passed`：模块未注册、`KeyError`、套件仍为 9 模块 | `16 passed, 7 warnings in 5.72s` |
| 3 四视图 | `4 failed, 15 passed`：通用方框缺少“建筑墙面”专用内容 | `19 passed, 7 warnings in 1.11s` |
| 4 报告图与标签 | `3 failed, 15 passed`：图题 key 缺失、0 张专用图、参数键未中文化 | `19 passed, 7 warnings in 8.36s` |

Task 2 的套件测试在提交时尚未包含 Task 4 的专用图，因此该阶段曾临时限定通用“必须有图”断言；Task 4 完成后已恢复为对所有 10 个模块强制要求内嵌图。Task 4 另有专用测试强制连墙件恰好生成“正立面 + 平面”两张 PNG。

## 出图与计算书

- 四视图：`elevation`、`plan`、`side`、`section`。
- 每张图的标题包含“连墙件计算 · 参数化示意（非施工图）”。
- 正立面表达建筑墙面、内外立杆投影、连墙点和竖向间距。
- 平面表达墙体、内外立杆、水平间距、外伸长度。
- 侧立面/剖面表达墙体、连墙杆、内外立杆和计算长度。
- 通用 DOCX 参数表使用中文标签，并嵌入正立面、平面两张 PNG。
- 结果表行数必须等于 `len(results) + 1`。

## 模块结果

默认双排扣件连接共输出 11 条结果：强度、稳定、连接承载力、扣件抗滑、竖向间距、水平间距、覆盖面积、主节点偏移、首步设置、单排高度、软拉硬撑适用高度。

新模块保持 `verified=false`。当前没有取得同参数品茗“连墙件计算”RTF，因此 PmStudio 自算结果不是品茗 oracle，不能声明已经完成逐项公式对照。

## 最终验收

- 后端全量：`263 passed, 7 warnings in 13.31s`。
- Django：`migrate` 无待应用迁移；`makemigrations --check` 返回 `No changes detected`；`check` 返回 `System check identified no issues (0 silenced).`。
- DOCX 套件：`generated=10 results=114 failed=4`；目录清理后恰好 10 份 DOCX。
- 连墙件 DOCX：11 条结果、12 行结果表（含表头）、2 张内嵌图片；默认参数有 1 个控制项失败（扣件抗滑 `8.87 kN > 8.0 kN`）。
- 前端：6 个测试文件、10 个测试全部通过；`tsc --noEmit && vite build` 成功，2381 个模块完成转换。
- HTTP：`catalog/modules`、`param-spec`、`runs`、`geometry`、`export.png`、`export.dxf`、`report.docx` 均返回 200。
- 文件签名：PNG `89 50 4E 47`；DXF 前 200 字节含 `SECTION`；DOCX `50 4B`。

## 仍未取得的 oracle

尚未取得同参数品茗“连墙件计算”RTF，因此没有逐项 oracle 对算、没有建立容差结论，也没有把模块加入 verified 列表。PmStudio 自算、自动测试通过、DOCX/HTTP 成功都不能替代品茗 oracle 或正式工程审查。
