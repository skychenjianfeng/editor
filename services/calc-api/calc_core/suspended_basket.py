"""高处作业吊篮验算：平台、悬挂机构、钢丝绳、支承点及安全装置。

主依据：GB/T 19155-2017《高处作业吊篮》。
补充依据：JGJ 202-2010《建筑施工工具式脚手架安全技术规范》。
"""

from __future__ import annotations

from typing import Any

MODULE_KEY = "suspended-basket"
STANDARD = "GB/T 19155-2017"

DEFAULTS: dict[str, Any] = {
    "ratedLoad": 630.0,          # kg，平台额定载重量 R1
    "platformWeight": 450.0,     # kg，平台及附属件自重 Swp
    "platformSpan": 6.0,         # m，平台吊点间距/受弯计算跨度 L
    "beamCount": 2.0,            # 根，共同受力的纵向主梁数
    "beamW": 90000.0,            # mm^3，单根主梁净截面抵抗矩 Wn
    "beamI": 12000000.0,         # mm^4，单根主梁毛截面惯性矩 Ix
    "beamE": 206000.0,           # N/mm^2，弹性模量 E
    "steelYield": 235.0,         # N/mm^2，屈服强度 σs
    "steelUltimate": 375.0,      # N/mm^2，抗拉强度 σb
    "hoistLimitLoad": 630.0,     # kg，起升机构极限工作载荷 Wll
    "outerLength": 1.5,          # m，配重悬挂支架外侧长度 Lo
    "innerLength": 4.5,          # m，配重悬挂支架内侧长度 Li
    "frameWeight": 350.0,        # kg，配重悬挂支架质量 Swr
    "frameCgDistance": 1.8,      # m，支点到支架重心距离 Lb
    "counterWeight": 600.0,      # kg，实际配重质量 Mw
    "stabilityFactor": 3.0,      # GB/T 19155-2017 6.5.5.3 要求 Cwr≥3
    "wireBreakForce": 80.0,      # kN，单根工作钢丝绳最小破断拉力 F0
    "wireRopeCount": 2.0,        # 根，承受悬挂载荷的工作钢丝绳数 Nr
    "wireSelfWeight": 20.0,      # kg，工作钢丝绳自重
    "wireMinSafety": 12.0,       # 双作用钢丝绳悬挂系统 GB/T 19155 限值
    "jgjDeadLoad": 4.61,         # kN，JGJ 吊篮及钢丝绳自重标准值 Gk
    "jgjConstructionLoad": 6.18, # kN，JGJ 施工活荷载标准值 Qk
    "jgjWindLoad": 2.0,          # kN，JGJ 吊篮风荷载标准值 Qwk
    "supportPointDesignReaction": 20.0,  # kN，最不利支承点设计反力
    "supportPointMinCapacity": 30.0,     # kN，各支承点最小设计承载力
    "backupDeviceInstalled": True,
    "backupDeviceMechanicalAutomatic": True,
    "backupDeviceTestableReset": True,
    "backupDeviceCalibrationValid": True,
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
            "clause": clause,
        }

    return {
        "module": MODULE_KEY,
        "title": "高处作业吊篮",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "platform",
                "title": "吊篮平台与主梁",
                "fields": [
                    num(
                        "ratedLoad",
                        "额定载重量 R1",
                        "kg",
                        630.0,
                        120.0,
                        3000.0,
                        10.0,
                        "GB/T 19155-2017 6.3.4、6.4",
                    ),
                    num(
                        "platformWeight",
                        "平台及附属件自重 Swp",
                        "kg",
                        450.0,
                        50.0,
                        2000.0,
                        10.0,
                        "GB/T 19155-2017 6.4",
                    ),
                    num(
                        "platformSpan",
                        "吊点间距/计算跨度 L",
                        "m",
                        6.0,
                        1.0,
                        12.0,
                        0.1,
                        "GB/T 19155-2017 6.4；JGJ 202-2010 4.3.1",
                    ),
                    num(
                        "beamCount",
                        "共同受力主梁数",
                        "根",
                        2.0,
                        1.0,
                        4.0,
                        1.0,
                        "计算假定",
                    ),
                    num(
                        "beamW",
                        "单根主梁净截面抵抗矩 Wn",
                        "mm³",
                        90000.0,
                        1000.0,
                        5000000.0,
                        1000.0,
                        "JGJ 202-2010 4.3.1-1",
                    ),
                    num(
                        "beamI",
                        "单根主梁惯性矩 Ix",
                        "mm⁴",
                        12000000.0,
                        10000.0,
                        1000000000.0,
                        100000.0,
                        "JGJ 202-2010 4.3.1-3",
                    ),
                    num(
                        "beamE",
                        "主梁弹性模量 E",
                        "N/mm²",
                        206000.0,
                        200000.0,
                        210000.0,
                        1000.0,
                        "JGJ 202-2010 4.3.1-3",
                    ),
                    num(
                        "steelYield",
                        "钢材屈服强度 σs",
                        "N/mm²",
                        235.0,
                        100.0,
                        1000.0,
                        5.0,
                        "GB/T 19155-2017 6.2.1、表3",
                    ),
                    num(
                        "steelUltimate",
                        "钢材抗拉强度 σb",
                        "N/mm²",
                        375.0,
                        100.0,
                        1500.0,
                        5.0,
                        "GB/T 19155-2017 6.2.1、表3",
                    ),
                ],
            },
            {
                "key": "suspension",
                "title": "悬挂机构与配重",
                "fields": [
                    num(
                        "hoistLimitLoad",
                        "起升机构极限工作载荷 Wll",
                        "kg",
                        630.0,
                        120.0,
                        3000.0,
                        10.0,
                        "GB/T 19155-2017 6.3.2、6.5.5.3",
                    ),
                    num(
                        "outerLength",
                        "支架外侧长度 Lo",
                        "m",
                        1.5,
                        0.2,
                        5.0,
                        0.1,
                        "GB/T 19155-2017 6.5.5.3 式(13)",
                    ),
                    num(
                        "innerLength",
                        "支架内侧长度 Li",
                        "m",
                        4.5,
                        0.5,
                        10.0,
                        0.1,
                        "GB/T 19155-2017 6.5.5.3 式(13)",
                    ),
                    num(
                        "frameWeight",
                        "配重悬挂支架质量 Swr",
                        "kg",
                        350.0,
                        20.0,
                        2000.0,
                        10.0,
                        "GB/T 19155-2017 6.5.5.3 式(13)",
                    ),
                    num(
                        "frameCgDistance",
                        "支点至支架重心距离 Lb",
                        "m",
                        1.8,
                        0.0,
                        5.0,
                        0.1,
                        "GB/T 19155-2017 6.5.5.3 式(13)",
                    ),
                    num(
                        "counterWeight",
                        "实际配重质量 Mw",
                        "kg",
                        600.0,
                        0.0,
                        5000.0,
                        10.0,
                        "GB/T 19155-2017 6.5.5.3 式(13)",
                    ),
                    num(
                        "stabilityFactor",
                        "要求稳定系数 Cwr",
                        "—",
                        3.0,
                        1.0,
                        5.0,
                        0.1,
                        "GB/T 19155-2017 6.5.5.3；JGJ 202-2010 表8.2.2",
                    ),
                ],
            },
            {
                "key": "wire_rope",
                "title": "工作钢丝绳",
                "fields": [
                    num(
                        "wireBreakForce",
                        "单根钢丝绳最小破断拉力 F0",
                        "kN",
                        80.0,
                        5.0,
                        1000.0,
                        1.0,
                        "GB/T 19155-2017 6.6.1 式(15)",
                    ),
                    num(
                        "wireRopeCount",
                        "承受悬挂载荷钢丝绳数 Nr",
                        "根",
                        2.0,
                        1.0,
                        8.0,
                        1.0,
                        "GB/T 19155-2017 6.6.2.1",
                    ),
                    num(
                        "wireSelfWeight",
                        "工作钢丝绳总自重",
                        "kg",
                        20.0,
                        1.0,
                        500.0,
                        1.0,
                        "GB/T 19155-2017 6.6.1.1",
                    ),
                    num(
                        "wireMinSafety",
                        "钢丝绳最小安全系数 Zp,min",
                        "—",
                        12.0,
                        8.0,
                        20.0,
                        0.5,
                        "GB/T 19155-2017 6.6.1.3；JGJ 202-2010 5.2.1",
                    ),
                    num(
                        "jgjDeadLoad",
                        "吊篮及钢丝绳自重标准值 Gk",
                        "kN",
                        4.61,
                        0.1,
                        100.0,
                        0.01,
                        "JGJ 202-2010 5.2.2-1",
                    ),
                    num(
                        "jgjConstructionLoad",
                        "施工活荷载标准值 Qk",
                        "kN",
                        6.18,
                        0.0,
                        100.0,
                        0.01,
                        "JGJ 202-2010 5.2.2-1",
                    ),
                    num(
                        "jgjWindLoad",
                        "吊篮风荷载标准值 Qwk",
                        "kN",
                        2.0,
                        0.0,
                        100.0,
                        0.1,
                        "JGJ 202-2010 5.2.2-2、5.2.3",
                    ),
                ],
            },
            {
                "key": "support_point",
                "title": "建筑结构支承点",
                "fields": [
                    num(
                        "supportPointDesignReaction",
                        "最不利支承点设计反力（含水平分量）",
                        "kN",
                        20.0,
                        0.0,
                        1000.0,
                        1.0,
                        "JGJ 202-2010 5.2.5；GB/T 19155-2017 6.5.1.4",
                    ),
                    num(
                        "supportPointMinCapacity",
                        "各支承点最小设计承载力",
                        "kN",
                        30.0,
                        0.0,
                        5000.0,
                        1.0,
                        "JGJ 202-2010 5.2.5、5.2.11；GB/T 19155-2017 6.5.5.1",
                    ),
                ],
            },
            {
                "key": "safety_device",
                "title": "防坠安全装置配置",
                "fields": [
                    boolean(
                        "backupDeviceInstalled",
                        "钢丝绳悬挂系统已设置后备装置",
                        True,
                        "GB/T 19155-2017 8.8.1",
                    ),
                    boolean(
                        "backupDeviceMechanicalAutomatic",
                        "防坠落装置机械自动动作",
                        True,
                        "GB/T 19155-2017 8.8.2.1、8.8.2.7",
                    ),
                    boolean(
                        "backupDeviceTestableReset",
                        "防坠落装置可测试并可复位",
                        True,
                        "GB/T 19155-2017 8.8.2.8",
                    ),
                    boolean(
                        "backupDeviceCalibrationValid",
                        "防坠装置标定在有效期内",
                        True,
                        "GB/T 19155-2017 15.2.7 l)",
                    ),
                ],
            },
        ],
    }


def _merged(params: dict[str, Any]) -> dict[str, Any]:
    p = dict(DEFAULTS)
    for key, value in (params or {}).items():
        if key in p:
            p[key] = value
    merged: dict[str, Any] = {}
    for key, value in p.items():
        if isinstance(DEFAULTS[key], bool):
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "1", "yes", "on"}:
                    merged[key] = True
                elif normalized in {"false", "0", "no", "off"}:
                    merged[key] = False
                else:
                    merged[key] = DEFAULTS[key]
            elif value is None:
                merged[key] = DEFAULTS[key]
            else:
                merged[key] = bool(value)
        else:
            merged[key] = float(value)
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
    ok: bool | None = None,
    ratio: float | None = None,
) -> dict[str, Any]:
    if ratio is None:
        ratio = value / limit if limit else 0.0
    return {
        "no": no,
        "key": key,
        "item": item,
        "value": round(value, 2),
        "limit": round(limit, 2),
        "unit": unit,
        "ratio": round(ratio, 3),
        "ok": (value <= limit + 1e-9) if ok is None else ok,
        "clause": clause,
        "control": control,
        "detail": detail,
    }


def _conformity_item(
    no: int,
    key: str,
    item: str,
    checks: list[tuple[str, bool]],
    clause: str,
    control: bool,
    detail: str,
) -> dict[str, Any]:
    total = len(checks)
    passed = sum(1 for _, ok in checks if ok)
    failed = [label for label, ok in checks if not ok]
    return {
        "no": no,
        "key": key,
        "item": item,
        "value": float(passed),
        "limit": float(total),
        "unit": "通过项/检查项",
        "ratio": round(passed / total if total else 0.0, 3),
        "ok": passed == total,
        "clause": clause,
        "control": control,
        "detail": detail + (f"；未通过：{'、'.join(failed)}" if failed else "；全部符合"),
        "checks": [{"label": label, "ok": ok} for label, ok in checks],
    }


def run(params: dict[str, Any]) -> dict[str, Any]:
    p = _merged(params)
    gravity = 9.81

    # GB/T 19155-2017 6.4 载荷工况2：1.5R1 + Swp。
    design_load_mass = 1.5 * p["ratedLoad"] + p["platformWeight"]
    design_load_kn = design_load_mass * gravity / 1000.0
    design_line_load = design_load_kn / p["platformSpan"]
    beam_line_load = design_line_load / p["beamCount"]

    # 简支主梁：M=qL²/8，σ=M/W。
    design_moment = beam_line_load * p["platformSpan"] ** 2 / 8.0
    bending_stress = design_moment * 1e6 / p["beamW"]

    stress_ratio = p["steelYield"] / p["steelUltimate"]
    if stress_ratio < 0.7:
        allowable_stress = p["steelYield"] / 1.33
        allowable_stress_detail = "σs/1.33"
    else:
        allowable_stress = (
            0.5 * p["steelYield"] + 0.35 * p["steelUltimate"]
        ) / 1.33
        allowable_stress_detail = "(0.5σs+0.35σb)/1.33"

    # JGJ 202-2010 4.3.1-3 简支梁均布荷载挠度；使用标准值。
    service_load_mass = p["ratedLoad"] + p["platformWeight"]
    service_line_load = (
        service_load_mass * gravity / 1000.0 / p["platformSpan"]
    )
    service_beam_line_load = service_line_load / p["beamCount"]
    service_line_load_n_mm = service_beam_line_load
    span_mm = p["platformSpan"] * 1000.0
    deflection = (
        5.0
        * service_line_load_n_mm
        * span_mm**4
        / (384.0 * p["beamE"] * p["beamI"])
    )
    # 按 GB/T 19155-2017 7.9.1/式(17) 的加载试验变形控制值比较。
    deflection_limit = span_mm / 200.0

    # GB/T 19155-2017 6.5.5.3 式(13)，两侧同除 g，以 kg·m 比较。
    overturn_unit_moment = p["hoistLimitLoad"] * p["outerLength"]
    resisting_moment = (
        p["counterWeight"] * p["innerLength"]
        + p["frameWeight"] * p["frameCgDistance"]
    )
    actual_stability_factor = (
        resisting_moment / overturn_unit_moment
        if overturn_unit_moment
        else 0.0
    )
    required_resisting_moment = p["stabilityFactor"] * overturn_unit_moment
    required_counter_weight = max(
        0.0,
        (
            required_resisting_moment
            - p["frameWeight"] * p["frameCgDistance"]
        )
        / p["innerLength"],
    )

    # GB/T 19155-2017 6.6.1、6.6.2.1：S 计入平台自重、额定载荷和钢丝绳自重。
    wire_static_load_kn = (
        (p["ratedLoad"] + p["platformWeight"] + p["wireSelfWeight"])
        * gravity
        / 1000.0
        / p["wireRopeCount"]
    )
    wire_safety_factor = (
        p["wireBreakForce"] / wire_static_load_kn
        if wire_static_load_kn
        else 0.0
    )

    # JGJ 202-2010 5.2.2～5.2.4：K=9 的风载组合施工核算。
    jgj_q1_kn = (p["jgjDeadLoad"] + p["jgjConstructionLoad"]) / 2.0
    jgj_q2_kn = p["jgjWindLoad"] / 2.0
    jgj_construction_demand_kn = 9.0 * (
        jgj_q1_kn**2 + jgj_q2_kn**2
    ) ** 0.5

    support_point_ok = (
        p["supportPointDesignReaction"]
        <= p["supportPointMinCapacity"] + 1e-9
    )

    safety_device_checks = [
        (
            "钢丝绳悬挂系统已设置后备装置",
            p["backupDeviceInstalled"],
        ),
        (
            "防坠落装置机械自动动作",
            p["backupDeviceMechanicalAutomatic"],
        ),
        (
            "防坠落装置可测试并可复位",
            p["backupDeviceTestableReset"],
        ),
        (
            "防坠装置标定在有效期内",
            p["backupDeviceCalibrationValid"],
        ),
    ]

    results = [
        _item(
            1,
            "platform_bending",
            "吊篮平台主梁抗弯",
            bending_stress,
            allowable_stress,
            "N/mm²",
            "GB/T 19155-2017 6.2.1、6.4；JGJ 202-2010 4.3.1-1",
            True,
            "荷载工况2：1.5R1+Swp；M=qL²/8，σ=ΣM/Wn≤[σ]",
        ),
        _item(
            2,
            "platform_deflection",
            "吊篮平台主梁挠度",
            deflection,
            deflection_limit,
            "mm",
            "GB/T 19155-2017 7.9.1 式(17)；JGJ 202-2010 4.3.1-3",
            False,
            "v=5qkL⁴/(384EIx)，按R1+Swp标准值计算；与试验变形限值a≤L/200比较",
        ),
        _item(
            3,
            "suspension_stability",
            "悬挂机构抗倾覆稳定系数",
            actual_stability_factor,
            p["stabilityFactor"],
            "—",
            "GB/T 19155-2017 6.5.5.3 式(13)；JGJ 202-2010 表8.2.2",
            True,
            "Cwr=(MwLi+SwrLb)/(WllLo)≥3；JGJ 202验收下限2，本模块执行更严的GB限值3",
            ok=actual_stability_factor + 1e-9 >= p["stabilityFactor"],
            ratio=(
                p["stabilityFactor"] / actual_stability_factor
                if actual_stability_factor
                else 999.0
            ),
        ),
        _item(
            4,
            "counterweight_requirement",
            "配重质量需求",
            p["counterWeight"],
            required_counter_weight,
            "kg",
            "GB/T 19155-2017 6.5.5.3 式(13)",
            True,
            "Mw≥(3WllLo-SwrLb)/Li；value为实际配重，limit为要求配重",
            ok=p["counterWeight"] + 1e-9 >= required_counter_weight,
            ratio=(
                required_counter_weight / p["counterWeight"]
                if p["counterWeight"]
                else 999.0
            ),
        ),
        _item(
            5,
            "wire_rope_safety",
            "工作钢丝绳安全系数",
            wire_safety_factor,
            p["wireMinSafety"],
            "—",
            "GB/T 19155-2017 6.6.1.3、6.6.2.1；JGJ 202-2010 5.2.1、5.2.3",
            True,
            "Zp=F0/S≥12；S=(R1+Swp+钢丝绳自重)g/(1000Nr)",
            ok=wire_safety_factor + 1e-9 >= p["wireMinSafety"],
            ratio=(
                p["wireMinSafety"] / wire_safety_factor
                if wire_safety_factor
                else 999.0
            ),
        ),
        _item(
            6,
            "jgj_wire_rope_wind",
            "JGJ动力钢丝绳风载组合",
            jgj_construction_demand_kn,
            p["wireBreakForce"],
            "kN",
            "JGJ 202-2010 5.2.1～5.2.4",
            True,
            "Q1=(Gk+Qk)/2，Q2=Qwk/2，"
            "QD=9√(Q1²+Q2²)≤F0；与GB/T Zp≥12并列，不互相替代",
        ),
        _item(
            7,
            "support_point_capacity",
            "建筑结构支承点承载力",
            p["supportPointDesignReaction"],
            p["supportPointMinCapacity"],
            "kN",
            "JGJ 202-2010 5.2.5、5.2.11；"
            "GB/T 19155-2017 6.5.1.4、6.5.3.1、6.5.5.1",
            True,
            "最不利支承点设计反力≤各支承点最小设计承载力；"
            "规范未给由吊篮总荷载直接展开支承反力的通用公式",
            ok=support_point_ok,
        ),
        _conformity_item(
            8,
            "safety_device_configuration",
            "防坠安全装置配置",
            safety_device_checks,
            "GB/T 19155-2017 8.8.1、8.8.2.1、8.8.2.7、8.8.2.8、15.2.7",
            True,
            "核对后备装置、防坠落装置机械自动动作、可测试复位"
            "和标定有效期；结果为通过项数/检查项数",
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
                {"code": STANDARD, "name": "高处作业吊篮"},
                {
                    "code": "JGJ 202-2010",
                    "name": "建筑施工工具式脚手架安全技术规范",
                },
            ],
            "missing": [],
            "complete": False,
            "gaps": [
                "GB/T 19155-2017 第6.4条给出平台计算载荷，未直接给出简支梁弯矩式；M=qL²/8按结构力学假定，抗弯表达式引用JGJ 202-2010 4.3.1-1。",
                "平台挠度按JGJ 202-2010 4.3.1-3弹性公式计算，限值采用GB/T 19155-2017 7.9.1式(17)的加载试验变形a≤L/200，二者口径不完全等同，正式应用前需复核。",
                "GB/T 19155-2017 6.5.5.3要求配重悬挂支架稳定系数不小于3；JGJ 202-2010表8.2.2验收要求抗倾覆系数不小于2。本模块执行GB/T的3.0设计限值。",
                "工作钢丝绳并行展示两套口径：GB/T 19155-2017 6.6.1的Zp=F0/S≥12，以及JGJ 202-2010 5.2.1～5.2.4的K=9风载组合QD≤F0；两者不相互覆盖或替代。",
                "JGJ 202-2010 5.2.5只要求核算支承点结构强度，未给出由吊篮总荷载展开各支承点反力的通用公式；本模块仅比较用户按实际施工及结构分析提供的设计反力和设计承载力，不替代锚固、局部承压、焊缝、螺栓或建筑结构构件验算。",
                "GB/T 19155-2017 9.4要求工作钢丝绳和安全钢丝绳独立悬挂；本模块未自动核验悬挂点构造和钢丝绳端部强度。",
                "防坠安全装置仅核对GB/T 19155-2017的后备装置、机械自动动作、可测试复位和标定有效期；型式试验、冲击载荷、锁绳速度和现场功能试验仍须按产品资料及附录B执行。",
                "未校核平台局部底板、连接螺栓、焊缝、疲劳以及非工作状态风荷载。",
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
            "designLoadMass_kg": round(design_load_mass, 2),
            "designLoad_kN": round(design_load_kn, 3),
            "designLineLoad_kN_m": round(design_line_load, 3),
            "beamLineLoad_kN_m": round(beam_line_load, 3),
            "designMoment_kNm": round(design_moment, 3),
            "bendingStress_N_mm2": round(bending_stress, 2),
            "allowableStress_N_mm2": round(allowable_stress, 2),
            "allowableStressFormula": allowable_stress_detail,
            "serviceLineLoad_N_mm": round(service_line_load_n_mm, 4),
            "deflection_mm": round(deflection, 3),
            "deflectionLimit_mm": round(deflection_limit, 3),
            "actualStabilityFactor": round(actual_stability_factor, 3),
            "requiredCounterWeight_kg": round(required_counter_weight, 2),
            "jgjAcceptanceMinStabilityFactor": 2.0,
            "wireStaticLoad_kN": round(wire_static_load_kn, 3),
            "wireSafetyFactor": round(wire_safety_factor, 3),
            "jgjQ1_kN": round(jgj_q1_kn, 3),
            "jgjQ2_kN": round(jgj_q2_kn, 3),
            "jgjWindLoad_kN": round(p["jgjWindLoad"], 3),
            "jgjK9RequiredTension_kN": round(jgj_construction_demand_kn, 3),
            "supportPointDesignReaction_kN": round(
                p["supportPointDesignReaction"], 3
            ),
            "supportPointMinCapacity_kN": round(
                p["supportPointMinCapacity"], 3
            ),
        },
        "assumptions": [
            "平台按两根（可输入）纵向主梁平均承担均布荷载，主梁支承在两端吊点，按简支梁计算；未计入偏载、局部底板和护栏作用。",
            "抗弯采用GB/T 19155-2017 6.4载荷工况2（1.5R1+Swp），质量按g=9.81m/s²换算为力。",
            "许用应力按GB/T 19155-2017 6.2.1表3的载荷工况2a/2b安全系数1.33计算，并区分σs/σb<0.7与≥0.7两式。",
            "挠度按额定载重量与平台自重标准值计算，并用GB/T 19155-2017 7.9.1的L/200加载试验变形值作为比较限值；该值不是规范直接给出的长期使用挠度限值。",
            "悬挂机构稳定性按GB/T 19155-2017 6.5.5.3配重悬挂支架刚体平衡模型计算，忽略水平风载、锚固变形和支架弹性变形。",
            "配重需求按Cwr=3反算，实际配重不小于反算值且须按JGJ 202-2010表8.2.2验收；现场不得以未固定或破损配重替代。",
            "工作钢丝绳按GB/T 19155-2017 6.6.1和6.6.2.1计算单根最大工作静拉力；JGJ 202-2010的K=9施工核算仅作为并列下限记录。",
            "JGJ 202-2010风载组合中的Gk、Qk、Qwk直接取输入标准值；默认值仅由本模块现有平台自重、钢丝绳自重和额定载重量换算，正式工程应按专项方案及当地风荷载资料取用。",
            "支承点设计反力及设计承载力应由实际悬挂机构传力、结构分析、锚固构造和相关结构设计规范确定；本模块不把总吊篮荷载均分作为通用支承反力公式。",
            "防坠安全装置配置按GB/T 19155-2017 8.8及15.2.7核对；本模块不采用附着式升降脚手架的钢吊杆条款。",
        ],
    }
