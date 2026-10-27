"""型钢悬挑脚手架验算：悬挑梁抗弯、挠度、锚固抗拉、抗剪与抗倾覆。

依据：JGJ 130-2011《建筑施工扣件式钢管脚手架安全技术规范》。
"""

from __future__ import annotations

from typing import Any

MODULE_KEY = "cantilever-scaffold"
STANDARD = "JGJ 130-2011"

DEFAULTS: dict[str, Any] = {
    "q": 5.0,              # 等效均布设计线荷载 kN/m
    "L": 1.5,              # 悬挑长度 m
    "W_mm3": 141000.0,     # 截面模量 mm^3（I16 工字钢量级）
    "phiB": 0.9,           # 整体稳定系数示例值，须按 GB 50017 复核
    "I_mm4": 11300000.0,   # 截面惯性矩 mm^4（I16 工字钢量级）
    "E": 206000.0,         # 弹性模量 N/mm^2
    "f": 205.0,            # 抗弯强度设计值 N/mm^2
    "anchorN": 2.0,        # U 形环受拉截面数
    "anchorAs": 314.0,     # 单个受拉截面面积 mm^2
    "anchorFy": 210.0,     # 锚固钢筋抗拉强度设计值 N/mm^2
    "webArea": 960.0,      # 腹板抗剪面积 mm^2
    "tauAllow": 125.0,     # 允许剪应力 N/mm^2
    "armLength": 1.2,      # 锚固力臂 m
    "K": 1.5,              # 抗倾覆安全系数
}


def param_spec() -> dict[str, Any]:
    def num(key: str, label: str, unit: str, default: float, lo: float, hi: float, step: float, clause: str):
        return {
            "key": key, "label": label, "type": "number", "unit": unit,
            "default": default, "min": lo, "max": hi, "step": step, "clause": clause,
        }

    return {
        "module": MODULE_KEY,
        "title": "型钢悬挑脚手架",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "load",
                "title": "荷载参数",
                "fields": [
                    num("q", "等效均布设计线荷载 q", "kN/m", 5.0, 0.1, 50.0, 0.1, "JGJ 130-2011 5.6.2"),
                ],
            },
            {
                "key": "section",
                "title": "悬挑梁参数",
                "fields": [
                    num("L", "悬挑长度 L", "m", 1.5, 0.2, 5.0, 0.1, "JGJ 130-2011 5.6.5"),
                    num("W_mm3", "截面模量 W", "mm³", 141000.0, 1000.0, 5000000.0, 1000.0, "JGJ 130-2011 5.6.3"),
                    num(
                        "phiB", "整体稳定系数 φ_b", "—", 0.9, 0.01, 1.0, 0.01,
                        "GB 50017-2017（示例值，待复核）",
                    ),
                    num("I_mm4", "截面惯性矩 I", "mm⁴", 11300000.0, 100000.0, 1000000000.0, 100000.0, "JGJ 130-2011 5.6.5"),
                    num("E", "弹性模量 E", "N/mm²", 206000.0, 200000.0, 210000.0, 1000.0, "JGJ 130-2011 5.6.5"),
                    num("f", "抗弯强度设计值 f", "N/mm²", 205.0, 100.0, 400.0, 5.0, "JGJ 130-2011 5.6.3"),
                ],
            },
            {
                "key": "anchor",
                "title": "锚固与抗剪参数",
                "fields": [
                    num("anchorN", "U 形环受拉截面数 n", "个", 2.0, 1.0, 4.0, 1.0, "JGJ 130-2011 5.6.6"),
                    num("anchorAs", "单截面面积 As", "mm²", 314.0, 10.0, 2000.0, 1.0, "JGJ 130-2011 5.6.6"),
                    num("anchorFy", "锚固钢筋抗拉强度 fy", "N/mm²", 210.0, 100.0, 500.0, 10.0, "JGJ 130-2011 5.6.6"),
                    num("webArea", "腹板抗剪面积 A_web", "mm²", 960.0, 10.0, 10000.0, 10.0, "JGJ 130-2011 第5章（待复核）"),
                    num("tauAllow", "允许剪应力 τ_allow", "N/mm²", 125.0, 10.0, 300.0, 5.0, "JGJ 130-2011 第5章（待复核）"),
                    num("armLength", "锚固力臂 d", "m", 1.2, 0.1, 5.0, 0.1, "JGJ 130-2011 第5章（待复核）"),
                    num("K", "抗倾覆安全系数 K", "—", 1.5, 1.0, 3.0, 0.1, "JGJ 130-2011 第5章（待复核）"),
                ],
            },
        ],
    }


def _merged(params: dict[str, Any]) -> dict[str, float]:
    p = dict(DEFAULTS)
    for k, v in (params or {}).items():
        if k in p:
            p[k] = v
    return {k: float(v) for k, v in p.items()}


def _item(no, key, item, value, limit, unit, clause, control, detail, ok=None):
    return {
        "no": no, "key": key, "item": item, "value": round(value, 2),
        "limit": round(limit, 2), "unit": unit,
        "ratio": round(value / limit if limit else 0.0, 3),
        "ok": (value <= limit + 1e-9) if ok is None else ok,
        "clause": clause, "control": control, "detail": detail,
    }


def run(params: dict[str, Any]) -> dict[str, Any]:
    p = _merged(params)

    moment = p["q"] * p["L"] ** 2 / 2  # kN·m
    stress = moment * 1e6 / p["W_mm3"]  # N/mm²
    stability_stress = moment * 1e6 / (p["phiB"] * p["W_mm3"])  # N/mm²

    length_mm = p["L"] * 1000.0
    deflection = p["q"] * length_mm**4 / (8 * p["E"] * p["I_mm4"])
    deflection_limit = length_mm / 250.0

    tension = p["q"] * p["L"]  # kN
    anchor_reduction = 0.85 if p["anchorN"] >= 2.0 else 1.0
    anchor_capacity_unreduced = p["anchorN"] * p["anchorAs"] * p["anchorFy"] / 1000.0  # kN
    anchor_capacity = anchor_reduction * anchor_capacity_unreduced  # kN
    if anchor_reduction < 1.0:
        anchor_detail = (
            "T=qL≤0.85·n·As·fy；n≥2，按5.6.7对锚固承载力乘0.85"
        )
    else:
        anchor_detail = "T=qL≤n·As·fy；单点锚固，不折减"

    shear = p["q"] * p["L"]  # kN
    shear_capacity = p["tauAllow"] * p["webArea"] / 1000.0  # kN

    anchor_moment = tension * p["armLength"]  # kN·m
    required_anchor_moment = p["K"] * p["q"] * p["L"] ** 2 / 2  # kN·m

    results = [
        _item(
            1, "cantilever_bending", "悬挑梁抗弯", stress, p["f"], "N/mm²",
            "JGJ 130-2011 5.6.3", True, "M=qL²/2，σ=M/W",
        ),
        _item(
            2, "cantilever_global_stability", "悬挑梁整体稳定", stability_stress, p["f"], "N/mm²",
            "JGJ 130-2011 5.6.4（φ_b 按 GB 50017-2017 输入）", True,
            "M=qL²/2，σ_b=M/(φ_b·W)",
        ),
        _item(
            3, "cantilever_deflection", "悬挑梁挠度", deflection, deflection_limit, "mm",
            "JGJ 130-2011 5.6.5、表5.1.8", False, "v=qL⁴/(8EI)≤L/250",
        ),
        _item(
            4, "anchor_tension", "锚固钢筋（U形环）抗拉", tension, anchor_capacity, "kN",
            "JGJ 130-2011 5.6.6、5.6.7", True, anchor_detail,
        ),
        _item(
            5, "cantilever_shear", "悬挑梁抗剪", shear, shear_capacity, "kN",
            "JGJ 130-2011 第5章（待复核）", True, "V=qL≤τ_allow·A_web",
        ),
        _item(
            6, "anchor_overturning", "锚固抗倾覆", required_anchor_moment, anchor_moment, "kN·m",
            "JGJ 130-2011 第5章（待复核）", True,
            "M_anchor=T·d≥K·qL²/2",
            ok=anchor_moment + 1e-9 >= required_anchor_moment,
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
                {"code": STANDARD, "name": "建筑施工扣件式钢管脚手架安全技术规范"},
            ],
            "missing": [],
            "complete": False,
            "gaps": [
                "JGJ 130-2011 第5章未直接给出悬挑梁抗剪及锚固抗倾覆计算公式，本模块采用简化补充验算，待复核。",
                "未验算型钢悬挑梁下建筑结构混凝土梁（板）的局部受压、结构承载力及锚固负弯矩配筋（5.6.8、5.6.9），待结合 GB 50010 复核。",
                "荷载 q 为沿悬挑梁全长等效均布设计线荷载，未拆分立杆集中力、梁自重及荷载组合。",
            ],
        },
        "summary": {
            "total": len(results),
            "failed": sum(1 for r in results if not r["ok"]),
            "control_failed": sum(1 for r in results if not r["ok"] and r["control"]),
        },
        "results": results,
        "derived": {
            "M_kNm": round(moment, 3),
            "sigma_N_mm2": round(stress, 2),
            "sigma_b_N_mm2": round(stability_stress, 2),
            "v_mm": round(deflection, 3),
            "v_limit_mm": round(deflection_limit, 3),
            "T_kN": round(tension, 3),
            "anchor_capacity_kN": round(anchor_capacity, 2),
            "anchor_capacity_unreduced_kN": round(anchor_capacity_unreduced, 2),
            "anchor_reduction_factor": anchor_reduction,
            "V_kN": round(shear, 3),
            "shear_capacity_kN": round(shear_capacity, 2),
            "M_anchor_kNm": round(anchor_moment, 3),
            "M_required_kNm": round(required_anchor_moment, 3),
        },
        "assumptions": [
            "悬挑梁按固定端悬臂梁计算，q 为均布设计线荷载，L 为悬伸长度。",
            "挠度采用 v=qL⁴/(8EI)，容许值按表 5.1.8 的型钢悬挑梁 L/250 取值。",
            "φ_b 由用户按 GB 50017-2017 取用；默认 0.9 仅为示例值，正式设计须复核。",
            "U 形环抗拉承载力按 n·As·fy 计算；n≥2 时按 5.6.7 乘 0.85，单点不折减。",
            "抗剪与抗倾覆按任务指定的简化公式补充验算。",
        ],
    }
