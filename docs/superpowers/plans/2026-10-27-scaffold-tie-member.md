# 独立连墙件计算模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 新增 `scaffold-tie-member` 独立模块，按 JGJ 130-2011 完成连墙件计算、四视图和 DOCX 导出，同时保持现有九模块行为不变。

**Architecture:** 新增一个只负责连墙件参数、公式和结果的内核文件；复用扣件式模块的钢管截面、风压高度系数、体型系数和稳定系数函数。模块通过现有 `ModuleDef` 注册，几何通过专用 drawing 模块分派，报告复用通用 DOCX 并增加专用图题和参数中文标签。

**Tech Stack:** Python 3、pytest、Django REST framework、matplotlib、ezdxf、python-docx、React/Vite。

## Global Constraints

- 计算基准固定为 JGJ 130-2011，不得混入 CECS 699-2020 的 1.5 风荷载系数。
- `Nlw=1.4*wk*Aw`；`N0=2kN`（单排）或 `3kN`（双排）。
- `Nl<=Nv`；扣件连接另校核 `Nl<=8.0kN`。
- 双排悬挑且高度大于 50m 时覆盖面积限值为 27m²，其余为 40m²。
- `layout=单排` 只能配 `scaffoldType=单排`；`layout=双排` 只能配双排落地或双排悬挑。
- GB 55023-2022 第 4.4.6 条为强制性条文，连墙件必须为可拉压的刚性构件；`软拉硬撑` 在任何高度均不允许。
- 新模块 `verified=false`，不得声称已通过品茗 oracle。
- 不修改现有扣件式模块的默认结果数量和数值。
- 所有新增生产代码必须先有失败测试。
- 不提交工作区中与本功能无关的现有改动。

### 2026-10-27 主管复核修订

- [x] 保留首版已完成内核、注册、四视图、计算书、覆盖记录和端到端验收的历史事实。
- [x] 修正双排默认结果中与工况无关的单排高度行；非单排不再输出 `single_row_height`。
- [x] 将高度阈值型 `soft_tie_height` 改为强制构造项 `rigid_tie_construction`，软拉硬撑在任何高度均失败。
- [x] 增加 `layout` 与 `scaffoldType` 双向一致性校验。
- [x] 通用计算书将首步设置与刚性构造输出为“满足要求/不满足要求”，连墙件图题使用“计算图”。

---

### Task 1: 连墙件内核

**Files:**
- Create: `services/calc-api/calc_core/scaffold_tie_member.py`
- Create: `services/calc-api/tests/test_scaffold_tie_member.py`
- Modify: `services/calc-api/calc_core/scaffold_fastener.py`

**Interfaces:**
- Consumes: `scaffold_fastener.phi_value(lam: float) -> float`、`muz_value(z: float, terrain: str) -> float`、`mus_value(enclosure: str, backdrop: str, phi: float) -> float`
- Produces:
  - `MODULE_KEY = "scaffold-tie-member"`
  - `DEFAULTS: dict[str, Any]`
  - `param_spec() -> dict[str, Any]`
  - `run(params: dict[str, Any]) -> dict[str, Any]`
  - `scaffold_fastener.section_properties(steel: str) -> tuple[float, float, float, float]`

- [x] **Step 1: 写内核失败测试**

```python
# services/calc-api/tests/test_scaffold_tie_member.py
import pytest

from calc_core import scaffold_tie_member as tie


def _result(payload, key):
    return next(row for row in payload["results"] if row["key"] == key)


def test_param_spec_contract():
    spec = tie.param_spec()
    assert spec["module"] == "scaffold-tie-member"
    assert spec["title"] == "连墙件计算"
    assert spec["verified"] is False
    fields = {
        field["key"]
        for group in spec["groups"]
        for field in group["fields"]
    }
    assert {
        "layout",
        "scaffoldType",
        "H",
        "h",
        "la",
        "tieVerticalSpacing",
        "tieHorizontalSpacing",
        "tieLength",
        "connectionType",
        "tieNv",
        "tieNetArea",
        "wind",
        "terrain",
    } <= fields


def test_default_payload_uses_jgj_wind_factor_and_axial_force_sum():
    payload = tie.run({})
    d = payload["derived"]
    assert payload["module"] == "scaffold-tie-member"
    assert payload["verified"] is False
    assert d["N0_kN"] == pytest.approx(3.0)
    assert d["Nlw_kN"] == pytest.approx(
        1.4 * d["wk_kN_m2"] * d["Aw_m2"], abs=0.05
    )
    assert d["Nl_kN"] == pytest.approx(
        d["Nlw_kN"] + d["N0_kN"], abs=0.05
    )
    assert payload["summary"]["total"] == len(payload["results"])
    assert payload["summary"]["total"] == 10


def test_spacing_and_height_drive_result_keys():
    payload = tie.run({})
    keys = {row["key"] for row in payload["results"]}
    assert {
        "tie_strength",
        "tie_stability",
        "tie_connection",
        "tie_coupler_slip",
        "tie_vertical_spacing",
        "tie_horizontal_spacing",
        "tie_area",
        "tie_offset",
        "tie_first_step",
        "rigid_tie_construction",
    } == keys


def test_wind_pressure_increases_axial_force():
    low = tie.run({"wind": 0.2})
    high = tie.run({"wind": 0.4})
    assert high["derived"]["Nl_kN"] > low["derived"]["Nl_kN"]


def test_net_area_and_tie_length_increase_stresses():
    wide = tie.run({"tieNetArea": 600.0, "tieLength": 0.8})
    narrow = tie.run({"tieNetArea": 300.0, "tieLength": 1.6})
    assert (
        _result(narrow, "tie_strength")["value"]
        > _result(wide, "tie_strength")["value"]
    )
    assert (
        _result(narrow, "tie_stability")["value"]
        > _result(wide, "tie_stability")["value"]
    )


def test_non_coupler_connection_omits_coupler_slip():
    payload = tie.run({"connectionType": "螺栓连接"})
    keys = {row["key"] for row in payload["results"]}
    assert "tie_coupler_slip" not in keys


@pytest.mark.parametrize(
    ("overrides", "key"),
    [
        ({"tieVerticalSpacing": 5.5}, "tie_vertical_spacing"),
        ({"tieHorizontalSpacing": 5.5}, "tie_horizontal_spacing"),
        ({"tieOffset": 350.0}, "tie_offset"),
        ({"tieFromFirstStep": "否"}, "tie_first_step"),
        (
            {"H": 30.0, "layout": "单排", "scaffoldType": "单排"},
            "single_row_height",
        ),
        (
            {"H": 30.0, "connectionType": "软拉硬撑"},
            "rigid_tie_construction",
        ),
        (
            {"H": 20.0, "connectionType": "软拉硬撑"},
            "rigid_tie_construction",
        ),
    ],
)
def test_construction_rules_fail(overrides, key):
    assert _result(tie.run(overrides), key)["ok"] is False


def test_cantilever_high_area_limit_is_27_square_metres():
    payload = tie.run(
        {
            "H": 55.0,
            "scaffoldType": "双排悬挑",
            "tieVerticalSpacing": 6.5,
            "tieHorizontalSpacing": 4.5,
        }
    )
    result = _result(payload, "tie_area")
    assert result["limit"] == pytest.approx(27.0)
    assert result["ok"] is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"steel": "unknown"},
        {"layout": "三排"},
        {"scaffoldType": "落地"},
        {"connectionType": "未知连接"},
        {"H": 0.0},
        {"tieNv": 0.0},
        {"wind": -0.1},
    ],
)
def test_invalid_parameters_raise_value_error(overrides):
    with pytest.raises(ValueError):
        tie.run(overrides)
```

- [x] **Step 2: 运行测试确认 RED**

Run:

```powershell
python -m pytest tests/test_scaffold_tie_member.py -q
```

Expected: FAIL because `calc_core.scaffold_tie_member` does not exist.

- [x] **Step 3: 暴露现有截面函数**

在 `scaffold_fastener.py` 现有 `_section()` 后增加兼容包装，并让 `run()` 继续使用原函数：

```python
def section_properties(steel: str) -> tuple[float, float, float, float]:
    """Public section helper for new modules; does not change fastener results."""
    return _section(steel)
```

- [x] **Step 4: 实现最小内核**

在 `scaffold_tie_member.py` 中实现：

```python
MODULE_KEY = "scaffold-tie-member"

STANDARDS_APPLIED = [
    {"code": "JGJ 130-2011", "name": "建筑施工扣件式钢管脚手架安全技术规范"},
    {"code": "GB 55023-2022", "name": "施工脚手架通用规范"},
    {"code": "GB 50009-2012", "name": "建筑结构荷载规范"},
]

DEFAULTS = {
    "layout": "双排",
    "scaffoldType": "双排落地",
    "H": 24.0,
    "h": 1.8,
    "la": 1.5,
    "lb": 0.9,
    "tieVerticalSpacing": 3.6,
    "tieHorizontalSpacing": 4.5,
    "tieLength": 0.9,
    "steel": "φ48×3.0",
    "connectionType": "扣件连接",
    "tieNv": 12.0,
    "tieNetArea": 0.0,
    "tieOffset": 200.0,
    "tieFromFirstStep": "是",
    "tieArrangement": "菱形",
    "wind": 0.25,
    "terrain": "B",
    "enclosure": "全封闭",
    "backdrop": "全封闭墙",
    "phiWind": 0.8,
}
```

`run()` 使用：

```python
A, _I, i, _W = section_properties(p["steel"])
Ac = p["tieNetArea"] if p["tieNetArea"] > 0 else A
Aw = p["tieVerticalSpacing"] * p["tieHorizontalSpacing"]
muz = muz_value(p["H"], str(p["terrain"]))
mus = mus_value(str(p["enclosure"]), str(p["backdrop"]), p["phiWind"])
wk = muz * mus * p["wind"]
N0 = 2.0 if p["layout"] == "单排" else 3.0
Nlw = 1.4 * wk * Aw
Nl = Nlw + N0
lam = p["tieLength"] * 1000.0 / i
phi = phi_value(lam)
sigma_strength = Nl * 1000.0 / Ac
sigma_stability = Nl * 1000.0 / (phi * A)
tie_steps = p["tieVerticalSpacing"] / p["h"]
tie_bays = p["tieHorizontalSpacing"] / p["la"]
area_limit = 27.0 if p["scaffoldType"] == "双排悬挑" and p["H"] > 50 else 40.0
```

默认双排扣件连接输出 10 条结果；非扣件连接不追加 `tie_coupler_slip`，共 9 条。`single_row_height` 仅在 `layout=单排` 时追加。`rigid_tie_construction` 始终输出，非软拉硬撑通过，软拉硬撑无论高度均失败，detail 明确 GB 55023-2022 第 4.4.6 条比 JGJ 130-2011 仅限制 H>24m 更严。所有构造判定显式传入 `ok=`，不要依赖默认比较方向。

- [x] **Step 5: 运行目标测试确认 GREEN**

```powershell
python -m pytest tests/test_scaffold_tie_member.py -q
```

Expected: all tests PASS.

- [x] **Step 6: 提交**

```powershell
git add services/calc-api/calc_core/scaffold_tie_member.py services/calc-api/calc_core/scaffold_fastener.py services/calc-api/tests/test_scaffold_tie_member.py
git commit -m "feat: add standalone tie member calculation core"
```

---

### Task 2: 注册模块并纳入批量套件

**Files:**
- Modify: `services/calc-api/calc_core/modules.py`
- Modify: `services/calc-api/calc_core/scaffold_suite.py`
- Modify: `services/calc-api/tests/test_registry.py`
- Modify: `services/calc-api/tests/test_scaffold_suite.py`

**Interfaces:**
- Consumes: Task 1 的 `scaffold_tie_member.param_spec/run`.
- Produces: registry key `scaffold-tie-member`；`SCAFFOLD_MODULE_KEYS` 共 10 项。

- [x] **Step 1: 先改测试期望为 RED**

在 `test_registry.py` 的精确集合中加入 `"scaffold-tie-member"`，并新增：

```python
def test_tie_member_registered():
    defn = registry.require("scaffold-tie-member")
    assert defn.title == "连墙件计算"
    assert defn.category == "落地与满堂"
    assert defn.standard == "JGJ 130-2011"
    assert defn.verified is False
    assert defn.param_spec()["module"] == "scaffold-tie-member"
    assert defn.run({})["summary"]["total"] >= 10
```

把 `test_scaffold_suite.py` 中的 `9` 改为 `10`，测试名改为 `test_suite_generates_ten_utf8_named_reports_manifest_and_qa`。

- [x] **Step 2: 运行测试确认 RED**

```powershell
python -m pytest tests/test_registry.py tests/test_scaffold_suite.py -q
```

Expected: FAIL because the registry and suite still contain nine modules.

- [x] **Step 3: 注册并更新套件**

在 `modules.py` 导入 `scaffold_tie_member` 并注册：

```python
SCAFFOLD_TIE_MEMBER = registry.register(
    registry.ModuleDef(
        key=scaffold_tie_member.MODULE_KEY,
        title="连墙件计算",
        standard="JGJ 130-2011",
        verified=False,
        param_spec=scaffold_tie_member.param_spec,
        run=scaffold_tie_member.run,
        geometry=_geometry("scaffold-tie-member", "连墙件计算"),
        report=report.build_generic_docx,
        category="落地与满堂",
    )
)
```

在 `SCAFFOLD_MODULE_KEYS` 的扣件式模块之后加入 `"scaffold-tie-member"`，并把模块数量文案从 9 改为 10。

- [x] **Step 4: 运行测试确认 GREEN**

```powershell
python -m pytest tests/test_registry.py tests/test_scaffold_suite.py -q
```

Expected: all tests PASS.

- [x] **Step 5: 提交**

```powershell
git add services/calc-api/calc_core/modules.py services/calc-api/calc_core/scaffold_suite.py services/calc-api/tests/test_registry.py services/calc-api/tests/test_scaffold_suite.py
git commit -m "feat: register tie member in scaffold catalog"
```

---

### Task 3: 连墙件四视图

**Files:**
- Create: `services/calc-api/calc_core/drawing_tie_member.py`
- Create: `services/calc-api/tests/test_drawing_tie_member.py`
- Modify: `services/calc-api/calc_core/drawing.py`
- Modify: `services/calc-api/tests/test_registry.py`

**Interfaces:**
- Consumes: params from Task 1.
- Produces: `build_tie_member_geometry(params: dict[str, Any], view: str) -> dict[str, Any]`.

- [x] **Step 1: 写四视图失败测试**

```python
# services/calc-api/tests/test_drawing_tie_member.py
import pytest

from calc_core import drawing


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize("view", ["elevation", "plan", "side", "section"])
def test_tie_member_has_specialized_geometry(view):
    geometry = drawing.build_geometry_for_module(
        "scaffold-tie-member",
        "连墙件计算",
        {"H": 24.0, "h": 1.8, "la": 1.5, "lb": 0.9, "tieLength": 0.9},
        view,
    )
    assert geometry["view"] == view
    text = "\n".join(
        item["text"]
        for layer in geometry["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    )
    assert "连墙件计算" in text
    assert "参数化示意" in text


def test_tie_member_png_and_dxf_export_are_valid():
    png = drawing.export_png(
        {"H": 24.0},
        "plan",
        module_key="scaffold-tie-member",
        module_title="连墙件计算",
    )
    dxf = drawing.export_dxf(
        {"H": 24.0},
        "elevation",
        module_key="scaffold-tie-member",
        module_title="连墙件计算",
    )
    assert png.startswith(PNG_SIGNATURE)
    assert dxf.startswith(b"0\nSECTION")
```

同时在 `test_registry.py` 的专用几何参数化列表加入 `"scaffold-tie-member"`。

- [x] **Step 2: 确认 RED**

```powershell
python -m pytest tests/test_drawing_tie_member.py tests/test_registry.py -q
```

Expected: FAIL because the dispatcher still emits generic schematic geometry.

- [x] **Step 3: 实现专用几何并分派**

`drawing_tie_member.py` 提供四个视图：

- `elevation`: wall line、内外立杆、连墙点、`tieVerticalSpacing`、`H`。
- `plan`: wall line、双排立杆、连墙杆和 `tieHorizontalSpacing`。
- `side` / `section`: 墙、连墙杆、内/外立杆、`tieLength`。
- 每个视图至少一条文本 `连墙件计算 · 参数化示意（非施工图）`。

在 `drawing.build_geometry_for_module()` 中加入：

```python
if module_key == "scaffold-tie-member":
    from .drawing_tie_member import build_tie_member_geometry

    return build_tie_member_geometry(params, view)
```

使用现有 `_line/_text/_payload` 等几何契约；不得新增 DXF 无法识别的 item type。

- [x] **Step 4: 确认 GREEN**

```powershell
python -m pytest tests/test_drawing_tie_member.py tests/test_registry.py -q
```

Expected: all tests PASS.

- [x] **Step 5: 提交**

```powershell
git add services/calc-api/calc_core/drawing_tie_member.py services/calc-api/calc_core/drawing.py services/calc-api/tests/test_drawing_tie_member.py services/calc-api/tests/test_registry.py
git commit -m "feat: add tie member drawing views"
```

---

### Task 4: 计算书图和参数中文标签

**Files:**
- Modify: `services/calc-api/calc_core/scaffold_report_figures.py`
- Modify: `services/calc-api/calc_core/report.py`
- Modify: `services/calc-api/tests/test_scaffold_report_figures.py`

**Interfaces:**
- Consumes: Task 1 payload and Task 3 `drawing.export_png`.
- Produces: `build_scaffold_figures("scaffold-tie-member", payload)` 返回正立面和平面两张 PNG。

- [x] **Step 1: 写失败测试**

在 `MODULE_TITLES` 相关测试列表加入 `"scaffold-tie-member"`，并新增：

```python
def test_tie_member_report_has_elevation_and_plan_figures():
    defn = registry.require("scaffold-tie-member")
    payload = defn.run({})
    figures = build_scaffold_figures(defn.key, payload)
    assert len(figures) == 2
    assert "正立面" in figures[0][1]
    assert "平面" in figures[1][1]
    assert all(png.startswith(PNG_SIGNATURE) for png, _ in figures)
```

在通用报告测试中调用新模块，断言参数表包含：

```python
assert "连墙件竖向间距" in "\n".join(
    cell.text for table in doc.tables for row in table.rows for cell in row.cells
)
```

- [x] **Step 2: 确认 RED**

```powershell
python -m pytest tests/test_scaffold_report_figures.py -q
```

Expected: FAIL because the module has no report figures or Chinese parameter mapping.

- [x] **Step 3: 实现图题和标签**

在 `MODULE_TITLES` 加入：

```python
"scaffold-tie-member": "连墙件计算",
```

分支使用：

```python
elif module_key == "scaffold-tie-member":
    add(
        drawing.export_png(
            params,
            "elevation",
            dark=False,
            module_key=module_key,
            module_title=module_title,
        ),
        "正立面连墙件布置",
    )
    add(
        drawing.export_png(
            params,
            "plan",
            dark=False,
            module_key=module_key,
            module_title=module_title,
        ),
        "平面连墙件布置",
    )
```

在 `report.PARAM_LABELS` 增加新模块全部字段。把 `build_generic_docx()` 参数表从 `[[str(k), str(v)]]` 改为：

```python
include_unit = any(
    PARAM_LABELS.get(key, (key, ""))[1] for key in params
)
rows = []
for key, value in params.items():
    label, unit = PARAM_LABELS.get(key, (key, ""))
    rows.append([label, str(value), unit] if include_unit else [label, str(value)])
header = ["参数", "取值", "单位"] if include_unit else ["参数", "取值"]
```

`tie_first_step`、`rigid_tie_construction` 的计算过程段落必须输出“结果：满足要求”或“结果：不满足要求”，不得显示 `1 ≤ 1`；当 `moduleKey=scaffold-tie-member` 时，图片章节标题使用“三、计算图”。

- [x] **Step 4: 确认 GREEN**

```powershell
python -m pytest tests/test_scaffold_report_figures.py -q
```

Expected: all tests PASS.

- [x] **Step 5: 提交**

```powershell
git add services/calc-api/calc_core/scaffold_report_figures.py services/calc-api/calc_core/report.py services/calc-api/tests/test_scaffold_report_figures.py
git commit -m "feat: add tie member report figures and labels"
```

---

### Task 5: 更新能力差距与实施记录

**Files:**
- Modify: `docs/qa/2026-10-27-scaffold-module-gap.md`
- Modify: `oracle/pinming-cli-probe/scaffold-module-gap.json`
- Create: `docs/qa/2026-10-27-tie-member-implementation.md`

**Interfaces:**
- Consumes: final registry and test evidence.
- Produces: 当前模块数 10、已覆盖 4、部分覆盖 9、未覆盖 68 的一致记录。

- [x] **Step 1: 更新差距数据**

- `PmStudio 当前注册脚手架模块` 改为 10。
- `scaffold-tie-member` 加入模块表。
- `连墙件计算` 状态改为 `covered`，映射到 `scaffold-tie-member`，优先级仍为 P0。
- 汇总改为：已覆盖 4、部分覆盖 9、未覆盖 68。
- JSON 的 `pmstudio_modules` 和对应能力映射同步，不改变模板编码证据。

- [x] **Step 2: 写实施验收记录**

`docs/qa/2026-10-27-tie-member-implementation.md` 写明：

- 规范依据和 1.4/3.0/8.0/40/27/24m/300mm 边界。
- 实际测试文件与数量。
- 四视图、两张报告图、DOCX 行数。
- `verified=false`，尚无品茗同参数 RTF。
- PmStudio 自算结果不是品茗 oracle。

- [x] **Step 3: 校验文档和数据一致性**

```powershell
$j=Get-Content 'oracle/pinming-cli-probe/scaffold-module-gap.json' -Raw | ConvertFrom-Json
@($j.pmstudio_modules).Count
@($j.pinming_capabilities | Where-Object status -eq 'covered').Count
@($j.pinming_capabilities | Where-Object status -eq 'partial').Count
@($j.pinming_capabilities | Where-Object status -eq 'uncovered').Count
```

Expected: `10`、`4`、`9`、`68`；能力总数仍为 81。

- [x] **Step 4: 提交**

```powershell
git add docs/qa/2026-10-27-scaffold-module-gap.md oracle/pinming-cli-probe/scaffold-module-gap.json docs/qa/2026-10-27-tie-member-implementation.md
git commit -m "docs: record tie member implementation coverage"
```

---

### Task 6: 全量与真实接口验收

**Files:**
- Verify only; do not change unrelated existing worktree files.
- Generate: `oracle/platform-suite-20261027/` 第 10 份 DOCX 与更新后的 manifest/QA。

**Interfaces:**
- Consumes: Tasks 1-5.
- Produces: 后端、前端、DOCX 和真实 HTTP 验收证据。

- [x] **Step 1: 运行后端全量测试**

```powershell
cd services/calc-api
python -m pytest -q
```

Expected: all tests PASS, no failures.

- [x] **Step 2: 运行迁移与 Django 检查**

```powershell
python manage.py migrate
python manage.py makemigrations --check
python manage.py check
```

Expected: no pending migrations; `check` reports no issues.

- [x] **Step 3: 重新生成 10 份脚手架 DOCX**

```powershell
python -m calc_core.scaffold_suite --output-dir ..\..\oracle\platform-suite-20261027 --qa-path ..\..\docs\qa\2026-10-27-scaffold-suite.md
```

Expected: `generated=10`; manifest 模块数 10、结果总数 113；连墙件报告为 10 条结果、结果表 11 行（含表头）、2 张图。

- [x] **Step 4: 运行前端测试与构建**

```powershell
cd ..\..\apps\calc
bun run test
bun run build
```

Expected: all frontend tests PASS and production build exits 0.

- [x] **Step 5: 真实 HTTP 验证**

若 `127.0.0.1:8001` 服务未运行，使用 `Start-Process ... -WindowStyle Hidden` 启动 `manage.py runserver 127.0.0.1:8001 --noreload`，然后验证：

```powershell
$base='http://127.0.0.1:8001/api/v1'
$catalog=Invoke-RestMethod "$base/catalog/modules"
$spec=Invoke-RestMethod "$base/catalog/param-spec/scaffold-tie-member"
$run=Invoke-RestMethod -Method Post -Uri "$base/runs" -ContentType 'application/json' -Body '{"module":"scaffold-tie-member","params":{}}'
$geo=Invoke-RestMethod -Method Post -Uri "$base/geometry" -ContentType 'application/json' -Body '{"module":"scaffold-tie-member","params":{},"view":"plan"}'
$png=Invoke-WebRequest -Method Post -Uri "$base/export.png" -ContentType 'application/json' -Body '{"module":"scaffold-tie-member","params":{},"view":"elevation"}'
$dxf=Invoke-WebRequest -Method Post -Uri "$base/export.dxf" -ContentType 'application/json' -Body '{"module":"scaffold-tie-member","params":{},"view":"plan"}'
$doc=Invoke-WebRequest -Method Post -Uri "$base/report.docx" -ContentType 'application/json' -Body '{"module":"scaffold-tie-member","params":{}}'
[pscustomobject]@{
  module=($catalog.modules.key -contains 'scaffold-tie-member')
  spec=$spec.module
  run=$run.module
  view=$geo.view
  png=$png.StatusCode
  dxf=$dxf.StatusCode
  docx=$doc.StatusCode
}
```

Expected: `module=True`、`spec=scaffold-tie-member`、`run=scaffold-tie-member`、`view=plan`，PNG/DXF/DOCX 均为 HTTP 200；额外断言 PNG 以 `89 50 4E 47`、DXF 以 `0D 0A` 或 `0A` 分隔的 `0/SECTION`、DOCX 以 `50 4B` 开头。

- [x] **Step 6: 最终检查**

```powershell
git diff --check -- services/calc-api apps/calc docs/qa docs/superpowers oracle/pinming-cli-probe
git status --short
```

Expected: no whitespace errors; only intended tie-member changes are staged or committed. Pre-existing unrelated worktree changes remain untouched.

- [x] **Step 7: 汇总验收**

报告必须给出：

- 后端精确 passed 数。
- 前端测试文件/测试数和构建结果。
- 10 份 DOCX、连墙件结果行数和图片数。
- API、PNG、DXF、DOCX 的实际状态。
- 仍未完成品茗同参数 RTF oracle 的明确边界。
