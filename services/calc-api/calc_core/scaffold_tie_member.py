"""独立连墙件计算内核（JGJ 130-2011）。"""

from __future__ import annotations

import math
from typing import Any

from .scaffold_fastener import (
    F_DESIGN,
    STEEL_SECTIONS,
    mus_value,
    muz_value,
    phi_value,
    section_properties,
)


MODULE_KEY = "scaffold-tie-member"

STANDARDS_APPLIED = [
    {"code": "JGJ 130-2011", "name": "建筑施工扣件式钢管脚手架安全技术规范"},
    {"code": "GB 55023-2022", "name": "施工脚手架通用规范"},
    {"code": "GB 50009-2012", "name": "建筑结构荷载规范"},
]

STANDARDS_MISSING: list[dict[str, str]] = []

STANDARDS_GAPS = [
    "连接承载力 Nv 由用户按实际节点构造输入，首版不设计预埋件、焊缝、螺栓群或建筑结构本体",
    "首版固定采用 JGJ 130-2011 式 5.2.13 的 1.4 风荷载分项系数，不混入 CECS 699-2020 的 1.5",
]

DEFAULTS: dict[str, Any] = {
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

LAYOUTS = ("双排", "单排")
SCAFFOLD_TYPES = ("双排落地", "双排悬挑", "单排")
CONNECTION_TYPES = ("扣件连接", "焊缝连接", "螺栓连接", "膨胀螺栓连接", "软拉硬撑")
TIE_ARRANGEMENTS = ("菱形", "方形", "矩形")
TERRAINS = ("A", "B", "C", "D")
ENCLOSURES = ("全封闭", "半封闭", "敞开")
BACKDROPS = ("全封闭墙", "敞开、框架和开洞墙")


def _num(
    key: str,
    label: str,
    unit: str,
    default: float,
    min_: float,
    max_: float,
    step: float,
    clause: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "type": "number",
        "unit": unit,
        "default": default,
        "min": min_,
        "max": max_,
        "step": step,
        "clause": clause,
    }


def _enum(
    key: str,
    label: str,
    options: list[str],
    default: str,
    *,
    clause: str = "",
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "type": "select",
        "options": options,
        "default": default,
        "clause": clause,
    }


def param_spec() -> dict[str, Any]:
    return {
        "module": MODULE_KEY,
        "title": "连墙件计算",
        "standard": "JGJ 130-2011",
        "standards": {
            "applied": STANDARDS_APPLIED,
            "missing": STANDARDS_MISSING,
            "complete": True,
            "gaps": STANDARDS_GAPS,
        },
        "verified": False,
        "groups": [
            {
                "key": "basic",
                "title": "基本参数",
                "fields": [
                    _enum(
                        "layout",
                        "单/双排",
                        list(LAYOUTS),
                        "双排",
                        clause="JGJ 130-2011 5.2.12",
                    ),
                    _enum(
                        "scaffoldType",
                        "架体类型",
                        list(SCAFFOLD_TYPES),
                        "双排落地",
                        clause="JGJ 130-2011 表 6.4.2",
                    ),
                    _num(
                        "H",
                        "架体高度 H",
                        "m",
                        24.0,
                        1.0,
                        100.0,
                        0.5,
                        "GB 50009-2012 表 8.2.1",
                    ),
                    _num(
                        "h",
                        "步距 h",
                        "m",
                        1.8,
                        0.6,
                        2.0,
                        0.1,
                        "JGJ 130-2011 6.1.2",
                    ),
                    _num(
                        "la",
                        "立杆纵距 la",
                        "m",
                        1.5,
                        0.9,
                        1.8,
                        0.1,
                        "JGJ 130-2011 6.1.2",
                    ),
                    _num(
                        "lb",
                        "立杆横距 lb",
                        "m",
                        0.9,
                        0.6,
                        1.5,
                        0.1,
                        "JGJ 130-2011 6.1.2",
                    ),
                    _num(
                        "tieLength",
                        "连墙件计算长度",
                        "m",
                        0.9,
                        0.1,
                        5.0,
                        0.1,
                        "JGJ 130-2011 5.2.12",
                    ),
                    _enum(
                        "steel",
                        "钢管类型",
                        list(STEEL_SECTIONS),
                        "φ48×3.0",
                        clause="JGJ 130-2011 表 5.1.6",
                    ),
                ],
            },
            {
                "key": "tie",
                "title": "连墙件与构造",
                "fields": [
                    _num(
                        "tieVerticalSpacing",
                        "连墙件竖向间距",
                        "m",
                        3.6,
                        0.6,
                        10.0,
                        0.1,
                        "JGJ 130-2011 表 6.4.2",
                    ),
                    _num(
                        "tieHorizontalSpacing",
                        "连墙件水平间距",
                        "m",
                        4.5,
                        0.9,
                        10.0,
                        0.1,
                        "JGJ 130-2011 表 6.4.2",
                    ),
                    _enum(
                        "connectionType",
                        "连接方式",
                        list(CONNECTION_TYPES),
                        "扣件连接",
                        clause="JGJ 130-2011 5.2.14、5.2.15",
                    ),
                    _num(
                        "tieNv",
                        "连接受拉或受压承载力 Nv",
                        "kN",
                        12.0,
                        0.1,
                        200.0,
                        0.5,
                        "JGJ 130-2011 5.2.14",
                    ),
                    _num(
                        "tieNetArea",
                        "连墙件净截面面积",
                        "mm²",
                        0.0,
                        0.0,
                        5000.0,
                        10.0,
                        "JGJ 130-2011 5.2.12-1（0=按毛截面）",
                    ),
                    _num(
                        "tieOffset",
                        "偏离主节点距离",
                        "mm",
                        200.0,
                        0.0,
                        1000.0,
                        10.0,
                        "JGJ 130-2011 6.4.3",
                    ),
                    _enum(
                        "tieFromFirstStep",
                        "从底层第一步纵向水平杆设置",
                        ["是", "否"],
                        "是",
                        clause="JGJ 130-2011 6.4.3",
                    ),
                    _enum(
                        "tieArrangement",
                        "连墙件布置形式",
                        list(TIE_ARRANGEMENTS),
                        "菱形",
                        clause="方案记录项",
                    ),
                ],
            },
            {
                "key": "wind",
                "title": "风荷载",
                "fields": [
                    _num(
                        "wind",
                        "基本风压 w0",
                        "kN/m²",
                        0.25,
                        0.0,
                        1.5,
                        0.05,
                        "GB 50009-2012 8.1",
                    ),
                    _enum(
                        "terrain",
                        "地面粗糙度",
                        list(TERRAINS),
                        "B",
                        clause="GB 50009-2012 表 8.2.1",
                    ),
                    _enum(
                        "enclosure",
                        "脚手架封闭状况",
                        list(ENCLOSURES),
                        "全封闭",
                        clause="JGJ 130-2011 表 4.2.6",
                    ),
                    _enum(
                        "backdrop",
                        "背靠建筑状况",
                        list(BACKDROPS),
                        "全封闭墙",
                        clause="JGJ 130-2011 表 4.2.6",
                    ),
                    _num(
                        "phiWind",
                        "挡风系数 φ",
                        "—",
                        0.8,
                        0.0,
                        1.0,
                        0.05,
                        "JGJ 130-2011 4.2.7",
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

    numeric_keys = (
        "H",
        "h",
        "la",
        "lb",
        "tieLength",
        "tieNv",
        "tieNetArea",
        "tieOffset",
        "tieVerticalSpacing",
        "tieHorizontalSpacing",
        "wind",
        "phiWind",
    )
    try:
        for key in numeric_keys:
            merged[key] = float(merged[key])
    except (TypeError, ValueError) as error:
        raise ValueError("连墙件数值参数必须为有限数值") from error
    if not all(math.isfinite(float(merged[key])) for key in numeric_keys):
        raise ValueError("连墙件数值参数必须为有限数值")

    for key in (
        "H",
        "h",
        "la",
        "lb",
        "tieLength",
        "tieNv",
        "tieVerticalSpacing",
        "tieHorizontalSpacing",
    ):
        if merged[key] <= 0:
            raise ValueError(f"{key} 必须为正数")
    for key in ("tieNetArea", "tieOffset", "wind", "phiWind"):
        if merged[key] < 0:
            raise ValueError(f"{key} 必须为非负数")
    if merged["phiWind"] > 1.0:
        raise ValueError("phiWind 不得大于 1")

    enums = {
        "layout": LAYOUTS,
        "scaffoldType": SCAFFOLD_TYPES,
        "steel": tuple(STEEL_SECTIONS),
        "connectionType": CONNECTION_TYPES,
        "tieFromFirstStep": ("是", "否"),
        "tieArrangement": TIE_ARRANGEMENTS,
        "terrain": TERRAINS,
        "enclosure": ENCLOSURES,
        "backdrop": BACKDROPS,
    }
    for key, options in enums.items():
        if merged[key] not in options:
            raise ValueError(f"unknown {key}: {merged[key]}")
    if merged["layout"] == "单排" and merged["scaffoldType"] != "单排":
        raise ValueError("layout=单排 只能配 scaffoldType=单排")
    if merged["layout"] == "双排" and merged["scaffoldType"] not in (
        "双排落地",
        "双排悬挑",
    ):
        raise ValueError(
            "layout=双排 只能配 scaffoldType=双排落地/双排悬挑"
        )
    return merged


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
    *,
    ok: bool,
) -> dict[str, Any]:
    ratio = value / limit if limit else 0.0
    return {
        "no": no,
        "key": key,
        "item": item,
        "value": round(float(value), 2),
        "limit": round(float(limit), 2),
        "unit": unit,
        "ratio": round(ratio, 3),
        "ok": bool(ok),
        "clause": clause,
        "control": control,
        "detail": detail,
    }


def run(params: dict[str, Any]) -> dict[str, Any]:
    p = _merged(params)
    area, _inertia, radius, _modulus = section_properties(str(p["steel"]))
    if p["tieNetArea"] > area:
        raise ValueError(
            f"tieNetArea={p['tieNetArea']:.1f}mm² 不得大于 "
            f"{p['steel']} 钢管毛截面面积 A={area:.1f}mm²"
        )
    net_area = p["tieNetArea"] if p["tieNetArea"] > 0 else area

    coverage_area = p["tieVerticalSpacing"] * p["tieHorizontalSpacing"]
    tie_steps = p["tieVerticalSpacing"] / p["h"]
    tie_bays = p["tieHorizontalSpacing"] / p["la"]
    muz = muz_value(p["H"], str(p["terrain"]))
    mus = mus_value(str(p["enclosure"]), str(p["backdrop"]), p["phiWind"])
    wk = muz * mus * p["wind"]
    n0 = 2.0 if p["layout"] == "单排" else 3.0
    nlw = 1.4 * wk * coverage_area
    nl = nlw + n0

    lam = p["tieLength"] * 1000.0 / radius
    if lam > 250.0 + 1e-9:
        raise ValueError(
            f"连墙件长细比 λ={lam:.1f} 超出 JGJ 130-2011 "
            "附录 A 表 A.0.6 的 250 上限，不能按端点值查取 φ"
        )
    phi = phi_value(lam)
    strength_limit = 0.85 * F_DESIGN
    sigma_strength = nl * 1000.0 / net_area
    sigma_stability = nl * 1000.0 / (phi * area)
    area_limit = (
        27.0
        if p["scaffoldType"] == "双排悬挑" and p["H"] > 50.0
        else 40.0
    )
    vertical_spacing_limit = (
        2.0
        if p["scaffoldType"] == "双排悬挑" and p["H"] > 50.0
        else 3.0
    )
    first_step_ok = p["tieFromFirstStep"] == "是"
    single_row = p["layout"] == "单排"
    single_row_ok = not single_row or p["H"] <= 24.0
    soft_tie = p["connectionType"] == "软拉硬撑"

    results = [
        _item(
            1,
            "tie_strength",
            "连墙件强度",
            sigma_strength,
            strength_limit,
            "N/mm²",
            "JGJ 130-2011 5.2.12-1",
            True,
            (
                f"Nl/Ac ≤ 0.85f；Ac={net_area:.1f}mm²，"
                f"{'按用户净截面' if p['tieNetArea'] > 0 else '净截面为0，按毛截面'}"
            ),
            ok=sigma_strength <= strength_limit + 1e-9,
        ),
        _item(
            2,
            "tie_stability",
            "连墙件稳定性",
            sigma_stability,
            strength_limit,
            "N/mm²",
            "JGJ 130-2011 5.2.12-2",
            True,
            (
                f"Nl/(φA) ≤ 0.85f；λ={lam:.1f}≤250，"
                f"按附录 A 表 A.0.6 查取 φ={phi:.3f}"
            ),
            ok=sigma_stability <= strength_limit + 1e-9,
        ),
        _item(
            3,
            "tie_connection",
            "连墙件连接承载力",
            nl,
            p["tieNv"],
            "kN",
            "JGJ 130-2011 5.2.14",
            True,
            "Nl ≤ Nv；Nv 为用户提供的可复核连接承载力设计值",
            ok=nl <= p["tieNv"] + 1e-9,
        ),
    ]
    if p["connectionType"] == "扣件连接":
        results.append(
            _item(
                4,
                "tie_coupler_slip",
                "连墙件扣件抗滑",
                nl,
                8.0,
                "kN",
                "JGJ 130-2011 5.2.15",
                True,
                "Nl ≤ Rc=8.0kN",
                ok=nl <= 8.0 + 1e-9,
            )
        )

    offset_number = len(results) + 1
    results.extend(
        [
            _item(
                offset_number,
                "tie_vertical_spacing",
                "连墙件竖向间距",
                tie_steps,
                vertical_spacing_limit,
                "步",
                "JGJ 130-2011 表 6.4.2",
                True,
                (
                    f"tieVerticalSpacing/h={p['tieVerticalSpacing']:.2f}/"
                    f"{p['h']:.2f}={tie_steps:.2f} ≤ "
                    f"{vertical_spacing_limit:.0f} 步"
                    + (
                        "（双排悬挑且 H>50m）"
                        if vertical_spacing_limit == 2.0
                        else ""
                    )
                ),
                ok=tie_steps <= vertical_spacing_limit + 1e-9,
            ),
            _item(
                offset_number + 1,
                "tie_horizontal_spacing",
                "连墙件水平间距",
                tie_bays,
                3.0,
                "跨",
                "JGJ 130-2011 表 6.4.2",
                True,
                (
                    "tieHorizontalSpacing/la="
                    f"{p['tieHorizontalSpacing']:.2f}/{p['la']:.2f} ≤ 3 跨"
                ),
                ok=tie_bays <= 3.0 + 1e-9,
            ),
            _item(
                offset_number + 2,
                "tie_area",
                "连墙件覆盖面积",
                coverage_area,
                area_limit,
                "m²",
                "JGJ 130-2011 表 6.4.2",
                True,
                (
                    f"Aw={p['tieVerticalSpacing']:.2f}×"
                    f"{p['tieHorizontalSpacing']:.2f} ≤ {area_limit:.0f}m²"
                ),
                ok=coverage_area <= area_limit + 1e-9,
            ),
            _item(
                offset_number + 3,
                "tie_offset",
                "连墙件偏离主节点",
                p["tieOffset"],
                300.0,
                "mm",
                "JGJ 130-2011 6.4.3",
                True,
                "偏离主节点不得超过 300mm",
                ok=p["tieOffset"] <= 300.0 + 1e-9,
            ),
            _item(
                offset_number + 4,
                "tie_first_step",
                "连墙件首步设置",
                1.0 if first_step_ok else 0.0,
                1.0,
                "—",
                "JGJ 130-2011 6.4.3",
                True,
                "应从底层第一步纵向水平杆处设置",
                ok=first_step_ok,
            ),
        ]
    )
    if single_row:
        results.append(
            _item(
                len(results) + 1,
                "single_row_height",
                "单排架体高度",
                p["H"],
                24.0,
                "m",
                "JGJ 130-2011 6.1.2",
                True,
                "单排架体高度不得超过 24m",
                ok=single_row_ok,
            )
        )
    rigid_tie_ok = not soft_tie
    results.append(
        _item(
            len(results) + 1,
            "rigid_tie_construction",
            "连墙件刚性构造",
            1.0 if rigid_tie_ok else 0.0,
            1.0,
            "—",
            "GB 55023-2022 4.4.6",
            True,
            (
                "GB 55023-2022 第4.4.6条强制要求连墙件为可拉压的刚性构件；"
                "当前采用软拉硬撑，任何高度均不满足要求。"
                "JGJ 130-2011 仅限制 H>24m 时不得采用软拉硬撑，"
                "GB 55023-2022 的要求更严。"
                if soft_tie
                else "GB 55023-2022 第4.4.6条强制要求连墙件为可拉压的刚性构件；"
                "当前连接方式不是软拉硬撑，满足刚性构造要求。"
                "JGJ 130-2011 仅限制 H>24m 时不得采用软拉硬撑，"
                "GB 55023-2022 的要求更严。"
            ),
            ok=rigid_tie_ok,
        )
    )

    assumptions = [
        "Nlw=1.4wkAw、Nl=Nlw+N0 按 JGJ 130-2011 式 5.2.13、5.2.12-3；未混入 CECS 699-2020 的 1.5 系数",
        "f=205N/mm²、Rc=8.0kN 取自 JGJ 130-2011；φ 仅按附录 A 表 A.0.6 的 λ=0～250 范围查取，超限直接报错，不截断为端点值",
        "连墙件竖向间距一般不超过 3 步；双排悬挑且 H>50m 时按表 6.4.2 收紧为不超过 2 步",
        "tieNetArea>0 时必须采用不大于钢管毛截面 A 的实际净截面；tieNetArea=0 时按毛截面计算并应在后续复核",
        "μz 按 GB 50009-2012 表 8.2.1 取架体高度 H；μs 按 JGJ 130-2011 封闭状况和背靠建筑规则计算",
        "连墙点覆盖面积仅作布置覆盖范围校核，不替代建筑结构本体、预埋件或连接节点设计",
        "GB 55023-2022 第4.4.6条为强制性条文，连墙件必须是可拉压的刚性构件；软拉硬撑在任何高度均判定不满足，较 JGJ 130-2011 仅限制 H>24m 更严",
        "本模块为 PmStudio 自算结果，verified=false，尚未取得同参数品茗 RTF oracle",
    ]

    return {
        "run_id": "local",
        "module": MODULE_KEY,
        "params": p,
        "verified": False,
        "standard": "JGJ 130-2011",
        "standards": {
            "applied": STANDARDS_APPLIED,
            "missing": STANDARDS_MISSING,
            "complete": True,
            "gaps": STANDARDS_GAPS,
        },
        "summary": {
            "total": len(results),
            "failed": sum(1 for result in results if not result["ok"]),
            "control_failed": sum(
                1
                for result in results
                if not result["ok"] and result["control"]
            ),
        },
        "results": results,
        "derived": {
            "A_mm2": round(area, 1),
            "I_mm4": round(_inertia, 0),
            "i_mm": round(radius, 2),
            "Ac_mm2": round(net_area, 1),
            "Aw_m2": round(coverage_area, 3),
            "tieSteps": round(tie_steps, 3),
            "tieBays": round(tie_bays, 3),
            "muz": round(muz, 3),
            "mus": round(mus, 3),
            "wk_kN_m2": round(wk, 4),
            "N0_kN": n0,
            "Nlw_kN": round(nlw, 3),
            "Nl_kN": round(nl, 3),
            "lambda": round(lam, 1),
            "phi": round(phi, 3),
            "sigma_strength_N_mm2": round(sigma_strength, 2),
            "sigma_stability_N_mm2": round(sigma_stability, 2),
            "f_design_N_mm2": F_DESIGN,
            "strength_limit_N_mm2": strength_limit,
            "tieNv_kN": round(p["tieNv"], 2),
            "areaLimit_m2": area_limit,
        },
        "assumptions": assumptions,
    }
