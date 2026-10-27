"""满堂脚手架验算：水平杆抗弯与挠度、立杆稳定与构造、地基承载力。

依据：JGJ 130-2011《建筑施工扣件式钢管脚手架安全技术规范》。
本模块按第 5.3 节引用的第 5.2 节公式计算，并采用第 6.8 节及附录 C
表 C-1 的满堂脚手架参数。未覆盖的构造与连接验算在 standards.gaps
和 assumptions 中明确列出。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

MODULE_KEY = "full-hall-scaffold"
STANDARD = "JGJ 130-2011"

DEFAULTS: dict[str, Any] = {
    "h": 1.5,
    "la": 1.2,
    "lb": 1.2,
    "H": 12.0,
    "lengthX": 6.0,
    "lengthY": 6.0,
    "dead": 0.35,
    "live": 2.0,
    "gk": 0.1770,
    "railLoad": 0.17,
    "netLoad": 0.01,
    "w0": 0.25,
    "muZ": 1.0,
    "muS": 0.80,
    "A_mm2": 506.0,
    "I_mm4": 127100.0,
    "W_mm3": 5260.0,
    "i_mm": 15.9,
    "E": 206000.0,
    "f": 205.0,
    "fg": 120.0,
    "baseArea": 0.25,
    "foundationReduction": 1.0,
    "couplerRc": 8.0,
    "verticalBraceSpacing": 6.0,
    "verticalBraceCoverageComplete": True,
    "horizontalBraceSpacing": 8.0,
    "horizontalBraceLayoutComplete": True,
    "braceWidth": 6.0,
    "braceAngle": 50.0,
    "tieHorizontalSpacing": 6.0,
    "tieVerticalSpacing": 4.0,
    "tieArrangementComplete": True,
    "ladderInstalled": True,
    "ladderStepSpacing": 300.0,
    "boardSupportSpacing": 0.6,
    "boardFullCoverageAndFixed": True,
}

# JGJ 130-2011 附录 C 表 C-1：方阵立杆间距、步距对应的计算长度系数 μ。
_MU_C1: dict[int, dict[int, float]] = {
    180: {120: 2.176, 100: 2.079, 90: 2.017},
    150: {130: 2.569, 120: 2.505, 100: 2.377, 90: 2.335},
    120: {130: 3.011, 120: 2.971, 100: 2.825, 90: 2.758},
    90: {100: 3.571, 90: 3.482},
}

# JGJ 130-2011 表 6.8.1：常用敞开式满堂脚手架最大允许高度。
_H681: dict[int, dict[int, tuple[float, float]]] = {
    180: {120: (17.0, 9.0), 100: (30.0, 24.0), 90: (36.0, 36.0)},
    150: {130: (18.0, 9.0), 120: (23.0, 16.0), 100: (36.0, 31.0), 90: (36.0, 36.0)},
    120: {130: (20.0, 13.0), 120: (24.0, 19.0), 100: (36.0, 32.0), 90: (36.0, 36.0)},
    90: {100: (36.0, 33.0), 90: (36.0, 36.0)},
}

_PHI_TABLE: dict[int, float] = {
    int(key): float(value)
    for key, value in json.loads(
        Path(__file__).with_name("phi_table.json").read_text(encoding="utf-8")
    ).items()
}


def param_spec() -> dict[str, Any]:
    def num(
        key: str,
        label: str,
        unit: str,
        default: float,
        lo: float,
        hi: float,
        step: float,
        clause: str,
    ) -> dict[str, Any]:
        return {
            "key": key,
            "label": label,
            "type": "number",
            "unit": unit,
            "default": default,
            "min": lo,
            "max": hi,
            "step": step,
            "clause": clause,
        }

    def boolean(
        key: str,
        label: str,
        default: bool,
        clause: str,
    ) -> dict[str, Any]:
        return {
            "key": key,
            "label": label,
            "type": "boolean",
            "unit": "—",
            "default": default,
            "min": 0,
            "max": 1,
            "step": 1,
            "clause": clause,
        }

    return {
        "module": MODULE_KEY,
        "title": "满堂脚手架",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "geometry",
                "title": "架体尺寸",
                "fields": [
                    num("h", "步距 h", "m", 1.5, 0.9, 1.8, 0.3, "JGJ 130-2011 5.3.4、表6.8.1"),
                    num("la", "立杆纵距 la", "m", 1.2, 0.9, 1.3, 0.1, "JGJ 130-2011 表6.8.1"),
                    num("lb", "立杆横距 lb", "m", 1.2, 0.9, 1.3, 0.1, "JGJ 130-2011 表6.8.1"),
                    num("H", "搭设高度 H", "m", 12.0, 3.0, 36.0, 0.5, "JGJ 130-2011 6.8.2"),
                    num("lengthX", "架体 X 向长度", "m", 6.0, 1.8, 60.0, 0.3, "JGJ 130-2011 2.1.5、附录C表C-1"),
                    num("lengthY", "架体 Y 向长度", "m", 6.0, 1.8, 60.0, 0.3, "JGJ 130-2011 2.1.5、附录C表C-1"),
                ],
            },
            {
                "key": "load",
                "title": "荷载与风参数",
                "fields": [
                    num("dead", "脚手板自重标准值", "kN/m²", 0.35, 0.10, 0.60, 0.05, "JGJ 130-2011 4.2.1"),
                    num("live", "施工均布荷载标准值", "kN/m²", 2.0, 2.0, 3.0, 0.5, "JGJ 130-2011 表4.2.2"),
                    num("gk", "立杆每米结构自重标准值 gk", "kN/m", 0.1770, 0.05, 0.50, 0.0001, "JGJ 130-2011 附录A表A.0.2"),
                    num("railLoad", "栏杆与挡脚板自重标准值", "kN/m", 0.17, 0.10, 0.30, 0.01, "JGJ 130-2011 表4.2.1-2"),
                    num("netLoad", "密目式安全立网自重标准值", "kN/m²", 0.01, 0.01, 0.10, 0.01, "JGJ 130-2011 4.2.1"),
                    num("w0", "基本风压 w0", "kN/m²", 0.25, 0.0, 0.90, 0.05, "JGJ 130-2011 4.2.5"),
                    num("muZ", "风压高度变化系数 μz", "—", 1.0, 0.50, 2.50, 0.01, "JGJ 130-2011 4.2.5"),
                    num("muS", "风荷载体型系数 μs", "—", 0.80, 0.0, 2.0, 0.05, "JGJ 130-2011 4.2.6"),
                ],
            },
            {
                "key": "section",
                "title": "钢管截面与材料",
                "fields": [
                    num("A_mm2", "钢管截面积 A", "mm²", 506.0, 100.0, 2000.0, 1.0, "JGJ 130-2011 附录B表B.0.1"),
                    num("I_mm4", "截面惯性矩 I", "mm⁴", 127100.0, 10000.0, 2000000.0, 100.0, "JGJ 130-2011 附录B表B.0.1"),
                    num("W_mm3", "截面模量 W", "mm³", 5260.0, 1000.0, 50000.0, 10.0, "JGJ 130-2011 附录B表B.0.1"),
                    num("i_mm", "截面回转半径 i", "mm", 15.9, 5.0, 30.0, 0.1, "JGJ 130-2011 附录B表B.0.1"),
                    num("E", "弹性模量 E", "N/mm²", 206000.0, 200000.0, 210000.0, 1000.0, "JGJ 130-2011 表5.1.6"),
                    num("f", "抗弯、抗压强度设计值 f", "N/mm²", 205.0, 100.0, 400.0, 5.0, "JGJ 130-2011 表5.1.6"),
                ],
            },
            {
                "key": "foundation",
                "title": "地基承载力",
                "fields": [
                    num("fg", "地基承载力特征值 fg", "kPa", 120.0, 20.0, 300.0, 5.0, "JGJ 130-2011 5.5.1、5.5.2"),
                    num("baseArea", "立杆基础底面积 A", "m²", 0.25, 0.05, 1.0, 0.01, "JGJ 130-2011 5.5.1"),
                    num("foundationReduction", "地基承载力折减系数", "—", 1.0, 0.4, 1.0, 0.1, "JGJ 130-2011 5.5.2"),
                ],
            },
            {
                "key": "connection_and_construction",
                "title": "扣件与构造",
                "fields": [
                    num("couplerRc", "扣件抗滑承载力设计值 Rc", "kN", 8.0, 1.0, 40.0, 0.5, "JGJ 130-2011 5.1.7、5.2.5"),
                    num("verticalBraceSpacing", "竖向剪刀撑间距", "m", 6.0, 6.0, 8.0, 0.5, "JGJ 130-2011 6.8.4"),
                    boolean(
                        "verticalBraceCoverageComplete",
                        "外周及内部覆盖且由底至顶连续",
                        True,
                        "JGJ 130-2011 6.8.4",
                    ),
                    num("horizontalBraceSpacing", "水平剪刀撑竖向间隔", "m", 8.0, 1.0, 8.0, 0.5, "JGJ 130-2011 6.8.4"),
                    boolean(
                        "horizontalBraceLayoutComplete",
                        "水平剪刀撑顶部及H≥8m时底部连续布置",
                        True,
                        "JGJ 130-2011 6.8.4",
                    ),
                    num("braceWidth", "剪刀撑宽度", "m", 6.0, 6.0, 8.0, 0.5, "JGJ 130-2011 6.8.4"),
                    num("braceAngle", "剪刀撑与地面夹角", "°", 50.0, 45.0, 60.0, 1.0, "JGJ 130-2011 6.8.4、6.6.2"),
                    num("tieHorizontalSpacing", "连墙或等效张拉水平间距", "m", 6.0, 6.0, 9.0, 0.5, "JGJ 130-2011 6.8.6"),
                    num("tieVerticalSpacing", "连墙或等效张拉竖向间距", "m", 4.0, 4.0, 6.0, 0.5, "JGJ 130-2011 6.8.6"),
                    boolean(
                        "tieArrangementComplete",
                        "外周及内部连墙或等效钢丝绳张拉完整",
                        True,
                        "JGJ 130-2011 6.8.6",
                    ),
                    boolean("ladderInstalled", "已设置满堂架爬梯", True, "JGJ 130-2011 6.8.9"),
                    num("ladderStepSpacing", "爬梯踏步间距", "mm", 300.0, 50.0, 500.0, 10.0, "JGJ 130-2011 6.8.9"),
                    num("boardSupportSpacing", "操作层脚手板支承水平杆间距", "m", 0.6, 0.1, 2.0, 0.05, "JGJ 130-2011 6.8.10"),
                    boolean(
                        "boardFullCoverageAndFixed",
                        "脚手板铺满、铺稳并可靠固定",
                        True,
                        "JGJ 130-2011 6.8.10、6.2.4",
                    ),
                ],
            },
        ],
    }


def _merged(params: dict[str, Any]) -> dict[str, Any]:
    merged = dict(DEFAULTS)
    for key, value in (params or {}).items():
        if key in merged:
            merged[key] = value
    bool_keys = {
        "verticalBraceCoverageComplete",
        "horizontalBraceLayoutComplete",
        "tieArrangementComplete",
        "ladderInstalled",
        "boardFullCoverageAndFixed",
    }
    p: dict[str, Any] = {}
    for key, value in merged.items():
        if key in bool_keys:
            if isinstance(value, bool):
                p[key] = value
            elif str(value).strip().lower() in {"1", "true", "yes", "是"}:
                p[key] = True
            elif str(value).strip().lower() in {"0", "false", "no", "否"}:
                p[key] = False
            else:
                raise ValueError(f"{key} 必须为布尔值")
        else:
            p[key] = float(value)
    positive_keys = (
        "h",
        "la",
        "lb",
        "H",
        "lengthX",
        "lengthY",
        "A_mm2",
        "I_mm4",
        "W_mm3",
        "i_mm",
        "E",
        "f",
        "fg",
        "baseArea",
        "couplerRc",
        "verticalBraceSpacing",
        "horizontalBraceSpacing",
        "braceWidth",
        "braceAngle",
        "tieHorizontalSpacing",
        "tieVerticalSpacing",
        "ladderStepSpacing",
        "boardSupportSpacing",
    )
    for key in positive_keys:
        if p[key] <= 0:
            raise ValueError(f"{key} 必须大于 0")
    if p["lengthX"] + 1e-9 < p["la"] or p["lengthY"] + 1e-9 < p["lb"]:
        raise ValueError("架体长度不得小于一个立杆间距")
    if p["foundationReduction"] <= 0 or p["foundationReduction"] > 1.0:
        raise ValueError("地基承载力折减系数应在 (0, 1] 范围内")
    return p


def _key(value: float) -> int:
    return int(round(value * 100))


def _mu_c1(h: float, spacing: float) -> float:
    h_key = _key(h)
    spacing_key = _key(spacing)
    try:
        return _MU_C1[h_key][spacing_key]
    except KeyError as exc:
        raise ValueError(
            "附录C表C-1未给出该步距/方阵立杆间距组合，"
            f"当前 h={h:.2f}m，间距={spacing:.2f}m"
        ) from exc


def _phi_value(lam: float) -> float:
    if lam > 250.0:
        return 7320.0 / lam**2
    return _PHI_TABLE[max(0, min(250, int(round(lam))))]


def _k_53_4(height: float) -> float:
    if height <= 20.0:
        return 1.155
    if height <= 30.0:
        return 1.191
    return 1.204


def _max_height_68_1(h: float, spacing: float, live: float) -> float | None:
    if not 1.7 <= h <= 1.8:
        h_key = _key(h)
    else:
        h_key = 180
    spacing_key = _key(spacing)
    heights = _H681.get(h_key, {}).get(spacing_key)
    if heights is None:
        return None
    if live <= 2.0 + 1e-9:
        return heights[0]
    if live <= 3.0 + 1e-9:
        return heights[1]
    return None


def _item(
    no: int,
    key: str,
    item: str,
    value: float,
    limit: float,
    unit: str,
    clause: str,
    control: bool,
    detail: str,
    ok: bool | None = None,
) -> dict[str, Any]:
    return {
        "no": no,
        "key": key,
        "item": item,
        "value": round(value, 2),
        "limit": round(limit, 2),
        "unit": unit,
        "ratio": round(value / limit if limit else 0.0, 3),
        "ok": (value <= limit + 1e-9) if ok is None else ok,
        "clause": clause,
        "control": control,
        "detail": detail,
    }


def run(params: dict[str, Any]) -> dict[str, Any]:
    p = _merged(params)
    if abs(p["la"] - p["lb"]) > 1e-9:
        raise ValueError("附录C表C-1仅适用于 la=lb 的方阵立杆间距")

    spacing = p["la"]
    mu = _mu_c1(p["h"], spacing)
    k_stability = _k_53_4(p["H"])
    lambda_check = mu * p["h"] * 1000.0 / p["i_mm"]
    lambda_stability = k_stability * mu * p["h"] * 1000.0 / p["i_mm"]
    phi = _phi_value(lambda_stability)

    tributary_width = p["lb"] / 2.0
    q_ledger_design = (
        1.2 * p["dead"] * tributary_width
        + 1.4 * p["live"] * tributary_width
    )
    q_ledger_service = (p["dead"] + p["live"]) * tributary_width
    span_mm = p["la"] * 1000.0
    ledger_moment = 0.1 * q_ledger_design * p["la"] ** 2
    ledger_stress = ledger_moment * 1e6 / p["W_mm3"]
    ledger_deflection = (
        0.00677
        * q_ledger_service
        * span_mm**4
        / (p["E"] * p["I_mm4"])
    )
    ledger_deflection_limit = min(p["la"] * 1000.0 / 150.0, 10.0)

    ng1 = p["gk"] * p["H"]
    working_area = p["la"] * p["lb"]
    ng2 = (
        p["dead"] * working_area
        + p["railLoad"] * p["la"]
        + p["netLoad"] * working_area
    )
    nq = p["live"] * working_area
    n_no_wind = 1.2 * (ng1 + ng2) + 1.4 * nq
    n_wind = 1.2 * (ng1 + ng2) + 0.9 * 1.4 * nq

    wk = p["muZ"] * p["muS"] * p["w0"]
    mw = 0.9 * 1.4 * wk * p["la"] * p["h"] ** 2 / 10.0
    sigma_no_wind = n_no_wind * 1000.0 / (phi * p["A_mm2"])
    sigma_wind = (
        n_wind * 1000.0 / (phi * p["A_mm2"])
        + mw * 1e6 / p["W_mm3"]
    )
    upright_stress = max(sigma_no_wind, sigma_wind)

    spans_x = max(0, int(math.floor(p["lengthX"] / p["la"] + 1e-9)))
    spans_y = max(0, int(math.floor(p["lengthY"] / p["lb"] + 1e-9)))
    rows_x = spans_x + 1
    rows_y = spans_y + 1
    min_spans_required = 5 if abs(spacing - 0.9) < 1e-9 else 4
    min_spans_actual = min(spans_x, spans_y)
    aspect_ratio = p["H"] / min(p["lengthX"], p["lengthY"])
    max_design_height = _max_height_68_1(p["h"], spacing, p["live"])

    lambda_ok = lambda_check <= 250.0 + 1e-9
    rows_ok = rows_x >= 3 and rows_y >= 3
    spans_ok = min_spans_actual >= min_spans_required
    height_ok = p["H"] <= 36.0 + 1e-9
    aspect_ok = aspect_ratio <= 3.0 + 1e-9
    design_height_ok = (
        max_design_height is not None
        and p["H"] <= max_design_height + 1e-9
    )
    construct_ok = (
        lambda_ok
        and rows_ok
        and spans_ok
        and height_ok
        and aspect_ok
        and design_height_ok
    )
    construct_detail = (
        f"λ={lambda_check:.1f}≤250；纵横排数 {rows_x}×{rows_y}≥3×3；"
        f"最少跨数 {min_spans_actual}≥{min_spans_required}；"
        f"H/min(Lx,Ly)={aspect_ratio:.2f}≤3；"
        + (
            f"表6.8.1允许高度 {max_design_height:.1f}m"
            if max_design_height is not None
            else "荷载/步距/间距组合未列入表6.8.1"
        )
    )

    nk = ng1 + ng2 + nq
    fg_effective = p["fg"] * p["foundationReduction"]
    base_pressure = nk / p["baseArea"]
    r_coupler = 1.1 * q_ledger_design * p["la"]

    vertical_brace_ok = (
        6.0 - 1e-9 <= p["verticalBraceSpacing"] <= 8.0 + 1e-9
        and p["verticalBraceCoverageComplete"]
    )
    horizontal_brace_ok = p["horizontalBraceLayoutComplete"] and (
        p["H"] < 8.0 - 1e-9
        or p["horizontalBraceSpacing"] <= 8.0 + 1e-9
    )
    brace_width_ok = 6.0 - 1e-9 <= p["braceWidth"] <= 8.0 + 1e-9
    brace_angle_ok = 45.0 - 1e-9 <= p["braceAngle"] <= 60.0 + 1e-9
    brace_ok = (
        vertical_brace_ok
        and horizontal_brace_ok
        and brace_width_ok
        and brace_angle_ok
    )
    brace_detail = (
        f"竖向间距 {p['verticalBraceSpacing']:.1f}m；"
        f"外周/内部覆盖或由底至顶连续：{'是' if p['verticalBraceCoverageComplete'] else '否'}；"
        + (
            f"H<8m，仅要求顶部连续水平剪刀撑：{'已满足' if horizontal_brace_ok else '未满足'}；"
            if p["H"] < 8.0 - 1e-9
            else (
                f"H≥8m，水平剪刀撑间隔 {p['horizontalBraceSpacing']:.1f}m≤8m，"
                f"底/顶连续布置：{'是' if p['horizontalBraceLayoutComplete'] else '否'}；"
            )
        )
        + f"宽度 {p['braceWidth']:.1f}m（6～8m）；夹角 {p['braceAngle']:.0f}°（45～60°）"
    )

    tie_required = aspect_ratio > 2.0 + 1e-9
    tie_spacing_ok = (
        6.0 - 1e-9 <= p["tieHorizontalSpacing"] <= 9.0 + 1e-9
        and 4.0 - 1e-9 <= p["tieVerticalSpacing"] <= 6.0 + 1e-9
    )
    tie_ok = (
        not tie_required
        or (p["tieArrangementComplete"] and tie_spacing_ok)
    )
    if tie_required:
        tie_detail = (
            f"高宽比 {aspect_ratio:.2f}>2，需外周及内部水平6～9m、竖向4～6m"
            f"设置连墙件或等效钢丝绳张拉；当前 {p['tieHorizontalSpacing']:.1f}m×"
            f"{p['tieVerticalSpacing']:.1f}m，布置完整："
            f"{'是' if p['tieArrangementComplete'] else '否'}"
        )
    else:
        tie_detail = (
            f"高宽比 {aspect_ratio:.2f}≤2，按6.8.6不强制设置连墙件；"
            "如设置仍应满足构造与承载力要求"
        )

    ladder_step_ok = p["ladderStepSpacing"] <= 300.0 + 1e-9
    ladder_ok = p["ladderInstalled"] and ladder_step_ok
    board_support_limit = p["la"] / 2.0
    board_support_ok = p["boardSupportSpacing"] <= board_support_limit + 1e-9
    ladder_board_ok = (
        ladder_ok and board_support_ok and p["boardFullCoverageAndFixed"]
    )
    ladder_board_detail = (
        f"爬梯{'已设置' if p['ladderInstalled'] else '未设置'}，"
        f"踏步 {p['ladderStepSpacing']:.1f}mm≤300mm；"
        f"操作层支承水平杆 {p['boardSupportSpacing']:.2f}m≤la/2={board_support_limit:.2f}m；"
        f"脚手板铺满并固定：{'是' if p['boardFullCoverageAndFixed'] else '否'}"
    )

    results = [
        _item(
            1,
            "ledger_bending",
            "水平杆抗弯",
            ledger_stress,
            p["f"],
            "N/mm²",
            "JGJ 130-2011 5.2.1、5.2.2、5.2.4、5.3.5",
            True,
            "纵向水平杆按三跨连续梁，M=0.1qla²，σ=M/W",
        ),
        _item(
            2,
            "ledger_deflection",
            "水平杆挠度",
            ledger_deflection,
            ledger_deflection_limit,
            "mm",
            "JGJ 130-2011 5.1.8、5.2.3、5.2.4、5.3.5",
            False,
            "三跨连续梁 v=0.00677qla⁴/(EI)≤min(la/150,10mm)",
        ),
        _item(
            3,
            "upright_stability",
            "立杆稳定",
            upright_stress,
            p["f"],
            "N/mm²",
            "JGJ 130-2011 5.2.6、5.2.7、5.2.9、5.3.1～5.3.4",
            True,
            "取 N/(φA) 与 N/(φA)+Mw/W 的不利值",
        ),
        _item(
            4,
            "upright_slenderness_construction",
            "立杆长细比与步距构造",
            lambda_check,
            250.0,
            "—",
            "JGJ 130-2011 5.1.9、5.3.4、6.8.1、6.8.2、6.8.6、附录C表C-1",
            True,
            construct_detail,
            ok=construct_ok,
        ),
        _item(
            5,
            "foundation_bearing",
            "立杆地基承载力",
            base_pressure,
            fg_effective,
            "kPa",
            "JGJ 130-2011 5.5.1、5.5.2",
            True,
            "pk=Nk/A≤fg·折减系数",
        ),
        _item(
            6,
            "coupler_slip",
            "水平杆连接扣件抗滑",
            r_coupler,
            p["couplerRc"],
            "kN",
            "JGJ 130-2011 5.1.7、5.2.5",
            True,
            "按三跨连续梁内支座反力系数取 R=1.1q_design·la；"
            "q_design=1.2Gk+1.4Qk，受荷宽度取 lb/2",
        ),
        _item(
            7,
            "brace_configuration",
            "剪刀撑布置与几何构造",
            1.0 if brace_ok else 0.0,
            1.0,
            "—",
            "JGJ 130-2011 6.8.4、6.8.5、6.6.2",
            True,
            brace_detail,
            ok=brace_ok,
        ),
        _item(
            8,
            "tie_requirement",
            "高宽比连墙或等效张拉要求",
            1.0 if tie_ok else 0.0,
            1.0,
            "—",
            "JGJ 130-2011 6.8.6",
            True,
            tie_detail,
            ok=tie_ok,
        ),
        _item(
            9,
            "ladder_board_configuration",
            "爬梯与操作层脚手板构造",
            1.0 if ladder_board_ok else 0.0,
            1.0,
            "—",
            "JGJ 130-2011 6.8.9、6.8.10、6.2.4",
            True,
            ladder_board_detail,
            ok=ladder_board_ok,
        ),
    ]

    return {
        "run_id": "local",
        "module": MODULE_KEY,
        "params": p,
        "verified": False,
        "standard": STANDARD,
        "standards": {
            "applied": [
                {
                    "code": STANDARD,
                    "name": "建筑施工扣件式钢管脚手架安全技术规范",
                    "clauses": [
                        "4.2.1",
                        "4.2.2",
                        "4.2.5",
                        "4.2.6",
                        "5.1.6",
                        "5.1.7",
                        "5.1.8",
                        "5.1.9",
                        "5.2.1",
                        "5.2.2",
                        "5.2.3",
                        "5.2.4",
                        "5.2.5",
                        "5.2.6",
                        "5.2.7",
                        "5.2.9",
                        "5.3.1",
                        "5.3.2",
                        "5.3.4",
                        "5.3.5",
                        "5.5.1",
                        "5.5.2",
                        "6.8.1",
                        "6.8.2",
                        "6.8.3",
                        "6.8.4",
                        "6.8.5",
                        "6.8.6",
                        "6.8.7",
                        "6.8.8",
                        "6.8.9",
                        "6.8.10",
                        "6.2.4",
                        "6.6.2",
                        "附录A表A.0.2",
                        "附录A表A.0.6",
                        "附录B表B.0.1",
                        "附录C表C-1",
                    ],
                }
            ],
            "missing": [],
            "complete": False,
            "gaps": [
                "6.8.3中水平杆长度不宜小于3跨、6.8.5中旋转扣件中心至主节点不宜大于150mm未自动校核。",
                "6.8.6仅校核连墙件或等效钢丝绳的布置，不校核连墙件连接承载力、预埋件承载力及钢丝绳张力。",
                "6.8.7中2、3跨满堂脚手架按第6.4节设置连墙件的细化要求未自动判别。",
                "6.8.8局部集中荷载及其局部加固未自动验算。",
                "6.8.1仅覆盖该表列出的常用敞开式满堂脚手架尺寸；超出表格工况时本模块给出构造失败，不推定安全。",
                "附录C表C-1仅覆盖 la=lb 的方阵立杆间距，且仅支持表列步距/间距组合。",
                "gk 由参数输入，默认值对应 h=1.5m、la=lb=1.2m 的附录A表A.0.2表值；改变尺寸时应按表更新。",
                "风压高度变化系数 μz 由用户按 GB 50009 取用后输入，本模块不根据地面粗糙度和高度自动插值。",
            ],
        },
        "summary": {
            "total": len(results),
            "failed": sum(1 for result in results if not result["ok"]),
            "control_failed": sum(
                1 for result in results if not result["ok"] and result["control"]
            ),
        },
        "results": results,
        "derived": {
            "q_ledger_design_kN_m": round(q_ledger_design, 3),
            "q_ledger_service_kN_m": round(q_ledger_service, 3),
            "M_ledger_kNm": round(ledger_moment, 3),
            "sigma_ledger_N_mm2": round(ledger_stress, 2),
            "v_ledger_mm": round(ledger_deflection, 3),
            "v_limit_mm": round(ledger_deflection_limit, 2),
            "mu": mu,
            "k_stability": k_stability,
            "lambda_check": round(lambda_check, 1),
            "lambda_stability": round(lambda_stability, 1),
            "phi": round(phi, 4),
            "Ng1_kN": round(ng1, 3),
            "Ng2_kN": round(ng2, 3),
            "NQ_kN": round(nq, 3),
            "N_no_wind_kN": round(n_no_wind, 3),
            "N_wind_kN": round(n_wind, 3),
            "wk_kN_m2": round(wk, 3),
            "Mw_kNm": round(mw, 3),
            "sigma_no_wind_N_mm2": round(sigma_no_wind, 2),
            "sigma_wind_N_mm2": round(sigma_wind, 2),
            "Nk_kN": round(nk, 3),
            "fg_effective_kPa": round(fg_effective, 2),
            "pk_kPa": round(base_pressure, 2),
            "max_design_height_m": max_design_height,
            "aspect_ratio": round(aspect_ratio, 2),
            "min_span_count": min_spans_actual,
            "upright_rows_x": rows_x,
            "upright_rows_y": rows_y,
            "R_coupler_kN": round(r_coupler, 3),
            "brace_layout_ok": brace_ok,
            "tie_required": tie_required,
            "tie_layout_ok": tie_ok,
            "ladder_board_layout_ok": ladder_board_ok,
        },
        "assumptions": [
            "按JGJ 130-2011 6.8.2假定仅设置一个施工层，未叠加多层同时作业荷载。",
            "纵向水平杆按三跨连续梁计算，跨度取la，受荷宽度按相邻半跨取lb/2；横向水平杆的独立抗弯与挠度另需在完整架体分析中复核。",
            "立杆轴向力按一榀满堂架中立杆负荷面积la·lb计算，并计入一个施工层脚手板、栏杆挡脚板和安全网自重。",
            "立杆稳定按5.2.6-1、5.2.6-2取不利值；计算长度按5.3.4的l0=kμh，μ取附录C表C-1。",
            "风荷载按5.2.9计算Mw；当w0输入为0时，组合风荷载项自动退化为不组合风荷载情形。",
            "地基验算采用荷载标准组合Nk，并按5.5.2通过foundationReduction输入回填土0.4或经试验/经验确定的折减。",
            "扣件抗滑采用传力假设R=1.1q_design·la：纵向水平杆按三跨连续梁，内支座反力系数取1.1，"
            "受荷宽度取lb/2；规范5.2.5仅规定R≤Rc，该系数属于本模块的计算假定。",
            "剪刀撑、连墙或等效钢丝绳、爬梯及脚手板的覆盖与固定由现场核验后的声明式输入判定；"
            "布尔值为true表示相应构造已完整实施，不是软件几何识别结果。",
            "6.8.4提到的旋转扣件固定及6.8.5的150mm偏心限值仍需在专项方案和现场验收中核对。",
            "表6.8.1中立杆间距不小于1.2m且施工荷载不小于3kN/m²时，应现场设置防滑扣件；"
            "couplerRc由用户按单/双扣件及实际防滑构造取值。",
            "计算结果标记verified=false，尚需与项目专项施工方案或品茗计算书样本对照复核。",
        ],
    }
