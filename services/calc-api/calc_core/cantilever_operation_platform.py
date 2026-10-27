"""悬挑式操作平台/卸料平台验算。

依据：JGJ 80-2016《建筑施工高处作业安全技术规范》第 6.4 节及附录 C。

本模块提供主梁、次梁、平台板、钢丝绳、锚固连接和构造验算骨架。
JGJ 80-2016 附录 C 给出了次梁、主梁弯曲、钢丝绳和下支承斜撑的验算框架，
但未直接给出焊缝连接、主梁挠度、锚固连接和抗倾覆的通用计算式；相关
结构力学假定均在 ``gaps`` 与 ``assumptions`` 中列明。
"""

from __future__ import annotations

import math
from typing import Any

MODULE_KEY = "cantilever-operation-platform"
STANDARD = "JGJ 80-2016"

# 下列尺寸和截面仅用于展示 pmsc.ini [RaisePlat information] 的默认样例，
# 不构成产品选型或工程推荐值。
DEFAULTS: dict[str, Any] = {
    "platformLength": 3.9,          # m，沿建筑边沿的长度
    "overhangLength": 3.5,          # m，悬挑长度 Lraise
    "anchorLength": 1.5,            # m，室内锚固长度 Lanchor
    "mainBeamCount": 2.0,           # 根，共同受力的主梁数
    "mainBeamW": 108300.0,          # mm^3，16a 槽钢 Wx，样例值
    "mainBeamI": 8660000.0,         # mm^4，16a 槽钢 Ix，样例值
    "mainBeamSelfWeight": 0.172,    # kN/m，16a 槽钢自重，样例值
    "steelE": 206000.0,             # N/mm^2
    "steelStrength": 215.0,         # N/mm^2，Q235 抗弯强度设计值
    "deckAndSecondaryLoad": 0.55,   # kN/m^2，铺板及 12.6 槽钢等折算永久面荷载
    "liveLoad": 5.0,                # kN/m^2，允许堆载标准值，pmsc 样例值
    "deadLoadFactor": 1.2,          # 永久荷载分项系数
    "liveLoadFactor": 1.4,          # 可变荷载分项系数
    "deflectionLimitRatio": 250.0,  # [v]=L/250，模块假定
    "sideCount": 2.0,               # 个，有斜拉钢丝绳的平台侧数
    "frontRopesPerSide": 1.0,       # 根/侧，前道钢丝绳
    "rearRopesPerSide": 1.0,        # 根/侧，后道钢丝绳
    "frontRopeDistance": 3.5,       # m，墙边至前道吊点距离
    "rearRopeDistance": 2.0,        # m，墙边至后道吊点距离
    "frontRopeAngle": 55.0,         # °，前道钢丝绳与平台面夹角
    "rearRopeAngle": 55.0,          # °，后道钢丝绳与平台面夹角
    "frontRopeShare": 0.5,          # 前道承担该侧竖向荷载比例，模块假定
    "rearRopeShare": 0.5,           # 后道承担该侧竖向荷载比例，模块假定
    "wireBreakForce": 200.0,        # kN，6×19、d=18.5mm 钢丝绳最小破断拉力样例
    "wireMinSafety": 8.0,           # JGJ 80-2016 附录 C.0.4 的 [K]
    "wireClampCount": 4.0,          # 个/绳端，JGJ 80-2016 6.4.7 下限
    "anchorCount": 4.0,             # 个，连接件总数
    "anchorTensionCapacity": 40.0,  # kN/个，单个锚固/连接件受拉承载力设计值
    "connectionDesignFactor": 1.5,  # 连接承载力附加安全系数，模块假定
    "supportMomentCapacity": 160.0, # kN·m，后部支承/连接抗倾覆力矩能力
    "rearSupportVerticalCapacity": 80.0,  # kN，后部支承竖向承载能力
    "stabilityFactor": 1.5,         # 抗倾覆安全系数，模块假定
    "secondaryBeamSpan": 3.0,        # m，次梁计算跨度
    "secondaryBeamSpacing": 0.4,     # m，次梁间距/受荷宽度
    "secondaryBeamW": 62100.0,       # mm^3，12.6 槽钢 Wx 样例
    "secondaryBeamF": 215.0,         # N/mm^2，次梁抗弯强度设计值
    "panelSpan": 0.5,                # m，铺板支承跨度
    "panelThickness": 50.0,          # mm，附录C.0.1下限样例
    "panelF": 15.0,                  # N/mm^2，木板抗弯强度设计值样例
    "weldThroat": 6.0,               # mm，焊缝有效喉厚
    "weldEffectiveLength": 100.0,    # mm，单条焊缝有效长度
    "weldStrength": 160.0,           # N/mm^2，角焊缝抗剪强度设计值样例
    "outerSideHigher": True,
    "guardrailFixed": True,
    "guardrailFullyEnclosed": True,
    "liftingRingInstalled": True,
    "loadBearingRingInstalled": True,
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
        "title": "悬挑式操作平台",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "geometry",
                "title": "平台几何与荷载",
                "fields": [
                    num(
                        "platformLength",
                        "平台沿边长度（pmsc 样例，非推荐值）",
                        "m",
                        3.9,
                        0.5,
                        20.0,
                        0.1,
                        "JGJ 80-2016 第6.4节；pmsc.ini 参考",
                    ),
                    num(
                        "overhangLength",
                        "悬挑长度 Lraise（不宜大于5m）",
                        "m",
                        3.5,
                        0.2,
                        8.0,
                        0.1,
                        "JGJ 80-2016 6.4.2",
                    ),
                    num(
                        "anchorLength",
                        "室内锚固长度 Lanchor",
                        "m",
                        1.5,
                        0.1,
                        10.0,
                        0.1,
                        "JGJ 80-2016 6.4.1；pmsc.ini 参考",
                    ),
                    num(
                        "deckAndSecondaryLoad",
                        "铺板及次梁折算永久面荷载（含12.6槽钢样例）",
                        "kN/m²",
                        0.55,
                        0.05,
                        5.0,
                        0.05,
                        "JGJ 80-2016 附录C.0.2（需按实物核定）",
                    ),
                    num(
                        "liveLoad",
                        "允许堆载标准值（pmsc 样例，非推荐值）",
                        "kN/m²",
                        5.0,
                        0.1,
                        20.0,
                        0.1,
                        "JGJ 80-2016 6.4.2；pmsc.ini 参考",
                    ),
                    num(
                        "deadLoadFactor",
                        "永久荷载分项系数",
                        "—",
                        1.2,
                        1.0,
                        2.0,
                        0.05,
                        "GB 50009-2012 荷载基本组合（计算假定）",
                    ),
                    num(
                        "liveLoadFactor",
                        "可变荷载分项系数",
                        "—",
                        1.4,
                        1.0,
                        2.0,
                        0.05,
                        "GB 50009-2012 荷载基本组合（计算假定）",
                    ),
                ],
            },
            {
                "key": "main_beam",
                "title": "主梁参数（16a槽钢样例，非推荐值）",
                "fields": [
                    num(
                        "mainBeamCount",
                        "共同受力主梁数",
                        "根",
                        2.0,
                        1.0,
                        12.0,
                        1.0,
                        "计算假定",
                    ),
                    num(
                        "mainBeamW",
                        "单根主梁净截面抵抗矩 Wx",
                        "mm³",
                        108300.0,
                        1000.0,
                        5000000.0,
                        100.0,
                        "JGJ 80-2016 附录C.0.3；pmsc.ini 参考",
                    ),
                    num(
                        "mainBeamI",
                        "单根主梁惯性矩 Ix",
                        "mm⁴",
                        8660000.0,
                        10000.0,
                        1000000000.0,
                        10000.0,
                        "JGJ 80-2016 附录C.0.3；挠度按结构力学计算",
                    ),
                    num(
                        "mainBeamSelfWeight",
                        "单根主梁自重线荷载",
                        "kN/m",
                        0.172,
                        0.0,
                        5.0,
                        0.001,
                        "JGJ 80-2016 附录C.0.3；pmsc.ini 参考",
                    ),
                    num(
                        "steelE",
                        "钢材弹性模量 E",
                        "N/mm²",
                        206000.0,
                        180000.0,
                        220000.0,
                        1000.0,
                        "JGJ 80-2016 附录A A.0.2-4",
                    ),
                    num(
                        "steelStrength",
                        "主梁抗弯强度设计值 f",
                        "N/mm²",
                        215.0,
                        100.0,
                        400.0,
                        5.0,
                        "JGJ 80-2016 附录A A.0.2-2 注",
                    ),
                    num(
                        "deflectionLimitRatio",
                        "主梁挠度限值分母 [v]=L/n",
                        "—",
                        250.0,
                        100.0,
                        1000.0,
                        10.0,
                        "JGJ 80-2016 未给出专用限值；本模块计算假定",
                    ),
                ],
            },
            {
                "key": "wire_rope",
                "title": "斜拉钢丝绳",
                "fields": [
                    num(
                        "sideCount",
                        "有斜拉钢丝绳的平台侧数",
                        "侧",
                        2.0,
                        1.0,
                        4.0,
                        1.0,
                        "JGJ 80-2016 6.4.3",
                    ),
                    num(
                        "frontRopesPerSide",
                        "每侧前道钢丝绳数",
                        "根",
                        1.0,
                        0.0,
                        4.0,
                        1.0,
                        "JGJ 80-2016 6.4.3",
                    ),
                    num(
                        "rearRopesPerSide",
                        "每侧后道钢丝绳数",
                        "根",
                        1.0,
                        0.0,
                        4.0,
                        1.0,
                        "JGJ 80-2016 6.4.3",
                    ),
                    num(
                        "frontRopeDistance",
                        "墙边至前道吊点距离",
                        "m",
                        3.5,
                        0.2,
                        8.0,
                        0.1,
                        "JGJ 80-2016 6.4.3",
                    ),
                    num(
                        "rearRopeDistance",
                        "墙边至后道吊点距离",
                        "m",
                        2.0,
                        0.1,
                        8.0,
                        0.1,
                        "JGJ 80-2016 6.4.3",
                    ),
                    num(
                        "frontRopeAngle",
                        "前道钢丝绳与平台面夹角 α",
                        "°",
                        55.0,
                        20.0,
                        85.0,
                        1.0,
                        "JGJ 80-2016 附录C.0.4",
                    ),
                    num(
                        "rearRopeAngle",
                        "后道钢丝绳与平台面夹角 α",
                        "°",
                        55.0,
                        20.0,
                        85.0,
                        1.0,
                        "JGJ 80-2016 附录C.0.4",
                    ),
                    num(
                        "frontRopeShare",
                        "前道承担该侧竖向荷载比例",
                        "—",
                        0.5,
                        0.1,
                        0.9,
                        0.05,
                        "计算假定；前后道比例之和应为1",
                    ),
                    num(
                        "rearRopeShare",
                        "后道承担该侧竖向荷载比例",
                        "—",
                        0.5,
                        0.1,
                        0.9,
                        0.05,
                        "计算假定；前后道比例之和应为1",
                    ),
                    num(
                        "wireBreakForce",
                        "单根钢丝绳最小破断拉力 F0（6×19、d=18.5mm样例）",
                        "kN",
                        200.0,
                        10.0,
                        1000.0,
                        1.0,
                        "JGJ 80-2016 附录C.0.4；破断拉力须按产品证明取用",
                    ),
                    num(
                        "wireMinSafety",
                        "钢丝绳安全系数限值 [K]",
                        "—",
                        8.0,
                        8.0,
                        20.0,
                        0.5,
                        "JGJ 80-2016 附录C.0.4",
                    ),
                    num(
                        "wireClampCount",
                        "每绳端钢丝绳卡数量（不得少于4个）",
                        "个",
                        4.0,
                        0.0,
                        12.0,
                        1.0,
                        "JGJ 80-2016 6.4.7",
                    ),
                ],
            },
            {
                "key": "anchor_stability",
                "title": "锚固、连接与抗倾覆",
                "fields": [
                    num(
                        "anchorCount",
                        "锚固/连接件总数",
                        "个",
                        4.0,
                        1.0,
                        40.0,
                        1.0,
                        "JGJ 80-2016 6.4.1、6.4.5",
                    ),
                    num(
                        "anchorTensionCapacity",
                        "单个锚固/连接件受拉承载力设计值",
                        "kN",
                        40.0,
                        1.0,
                        1000.0,
                        1.0,
                        "JGJ 80-2016 6.4.1、6.4.5；须按节点设计或试验取用",
                    ),
                    num(
                        "connectionDesignFactor",
                        "连接承载力附加安全系数",
                        "—",
                        1.5,
                        1.0,
                        3.0,
                        0.1,
                        "计算假定",
                    ),
                    num(
                        "supportMomentCapacity",
                        "后部支承/连接抗倾覆力矩能力",
                        "kN·m",
                        160.0,
                        0.0,
                        5000.0,
                        5.0,
                        "JGJ 80-2016 6.4.1、6.4.5；节点能力须专项核定",
                    ),
                    num(
                        "rearSupportVerticalCapacity",
                        "后部支承竖向承载能力",
                        "kN",
                        80.0,
                        0.0,
                        3000.0,
                        1.0,
                        "JGJ 80-2016 6.4.1、6.4.4；节点能力须专项核定",
                    ),
                    num(
                        "stabilityFactor",
                        "抗倾覆安全系数",
                        "—",
                        1.5,
                        1.0,
                        3.0,
                        0.1,
                        "计算假定",
                    ),
                ],
            },
            {
                "key": "secondary_and_panel",
                "title": "次梁与铺板",
                "fields": [
                    num(
                        "secondaryBeamSpan",
                        "次梁计算跨度",
                        "m",
                        3.0,
                        0.2,
                        10.0,
                        0.1,
                        "JGJ 80-2016 附录C C.0.2",
                    ),
                    num(
                        "secondaryBeamSpacing",
                        "次梁间距（受荷宽度 b）",
                        "m",
                        0.4,
                        0.1,
                        2.0,
                        0.05,
                        "JGJ 80-2016 附录C C.0.2（线荷载形成参数）",
                    ),
                    num(
                        "secondaryBeamW",
                        "单根次梁截面模量 W",
                        "mm³",
                        62100.0,
                        1000.0,
                        5000000.0,
                        100.0,
                        "JGJ 80-2016 附录C C.0.2；按实际型钢截面输入",
                    ),
                    num(
                        "secondaryBeamF",
                        "次梁抗弯强度设计值 f",
                        "N/mm²",
                        215.0,
                        100.0,
                        400.0,
                        5.0,
                        "JGJ 80-2016 附录C C.0.2、附录B B.0.1-3",
                    ),
                    num(
                        "panelSpan",
                        "铺板计算跨度",
                        "m",
                        0.5,
                        0.1,
                        2.0,
                        0.05,
                        "JGJ 80-2016 附录C C.0.1、C.0.2（铺板验算）",
                    ),
                    num(
                        "panelThickness",
                        "铺板厚度（附录C.0.1下限50mm）",
                        "mm",
                        50.0,
                        10.0,
                        100.0,
                        1.0,
                        "JGJ 80-2016 附录C C.0.1",
                    ),
                    num(
                        "panelF",
                        "铺板抗弯强度设计值 f",
                        "N/mm²",
                        15.0,
                        1.0,
                        300.0,
                        1.0,
                        "JGJ 80-2016 附录C C.0.2；按板材实测或产品资料输入",
                    ),
                ],
            },
            {
                "key": "weld_and_guardrail",
                "title": "焊缝连接与防护构造",
                "fields": [
                    num(
                        "weldThroat",
                        "焊缝有效喉厚 he",
                        "mm",
                        6.0,
                        1.0,
                        20.0,
                        0.5,
                        "JGJ 80-2016 6.4.5；焊缝承载力按GB 50017专项验算",
                    ),
                    num(
                        "weldEffectiveLength",
                        "单条焊缝有效长度 lw",
                        "mm",
                        100.0,
                        10.0,
                        2000.0,
                        5.0,
                        "JGJ 80-2016 6.4.5；焊缝承载力按GB 50017专项验算",
                    ),
                    num(
                        "weldStrength",
                        "焊缝抗剪强度设计值 fw",
                        "N/mm²",
                        160.0,
                        10.0,
                        300.0,
                        5.0,
                        "JGJ 80-2016 6.4.5；焊缝承载力按GB 50017专项验算",
                    ),
                    boolean(
                        "outerSideHigher",
                        "平台外侧略高于内侧",
                        True,
                        "JGJ 80-2016 6.4.8",
                    ),
                    boolean(
                        "guardrailFixed",
                        "外侧安装固定防护栏杆",
                        True,
                        "JGJ 80-2016 6.4.8",
                    ),
                    boolean(
                        "guardrailFullyEnclosed",
                        "防护挡板完全封闭",
                        True,
                        "JGJ 80-2016 6.4.8",
                    ),
                    boolean(
                        "liftingRingInstalled",
                        "安装吊运使用专用起重吊环",
                        True,
                        "JGJ 80-2016 6.4.6",
                    ),
                    boolean(
                        "loadBearingRingInstalled",
                        "与建筑物连接固定使用承载吊环",
                        True,
                        "JGJ 80-2016 6.4.6",
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
        "outerSideHigher",
        "guardrailFixed",
        "guardrailFullyEnclosed",
        "liftingRingInstalled",
        "loadBearingRingInstalled",
    }
    p: dict[str, Any] = {
        key: float(value)
        for key, value in merged.items()
        if key not in bool_keys
    }
    for key in bool_keys:
        p[key] = bool(merged[key])

    positive_keys = {
        "platformLength",
        "overhangLength",
        "anchorLength",
        "mainBeamCount",
        "mainBeamW",
        "mainBeamI",
        "steelE",
        "steelStrength",
        "liveLoad",
        "sideCount",
        "wireBreakForce",
        "wireMinSafety",
        "anchorCount",
        "anchorTensionCapacity",
        "stabilityFactor",
        "secondaryBeamSpan",
        "secondaryBeamSpacing",
        "secondaryBeamW",
        "secondaryBeamF",
        "panelSpan",
        "panelThickness",
        "panelF",
        "weldThroat",
        "weldEffectiveLength",
        "weldStrength",
        "deflectionLimitRatio",
    }
    for key in positive_keys:
        if p[key] <= 0:
            raise ValueError(f"{key} 必须大于 0")
    for key in (
        "deckAndSecondaryLoad",
        "deadLoadFactor",
        "liveLoadFactor",
    ):
        if p[key] < 0:
            raise ValueError(f"{key} 不得小于 0")
    if not 0 < p["frontRopeAngle"] < 90 or not 0 < p["rearRopeAngle"] < 90:
        raise ValueError("钢丝绳与平台面夹角应在 (0, 90)° 范围内")
    return p


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


def run(params: dict[str, Any]) -> dict[str, Any]:
    p = _merged(params)

    # 主梁按墙边、后吊点、前吊点形成的多支承区间的最大跨度取包络。
    beam_span = max(
        p["anchorLength"],
        p["rearRopeDistance"],
        p["frontRopeDistance"] - p["rearRopeDistance"],
        0.0,
    )
    tributary_width = p["platformLength"] / max(p["mainBeamCount"], 1.0)
    dead_line = (
        p["deckAndSecondaryLoad"] * tributary_width
        + p["mainBeamSelfWeight"]
    )
    live_line = p["liveLoad"] * tributary_width
    design_line = (
        p["deadLoadFactor"] * dead_line
        + p["liveLoadFactor"] * live_line
    )
    design_moment = design_line * beam_span**2 / 8.0
    bending_stress = design_moment * 1e6 / p["mainBeamW"]
    overhang_ok = p["overhangLength"] <= 5.0 + 1e-9

    service_line = (
        (p["deckAndSecondaryLoad"] + p["liveLoad"]) * tributary_width
        + p["mainBeamSelfWeight"]
    )
    beam_span_mm = beam_span * 1000.0
    deflection = (
        5.0
        * service_line
        * beam_span_mm**4
        / (384.0 * p["steelE"] * p["mainBeamI"])
    )
    deflection_limit = beam_span_mm / p["deflectionLimitRatio"]

    area = p["platformLength"] * p["overhangLength"]
    service_total = (
        (p["deckAndSecondaryLoad"] + p["liveLoad"]) * area
        + p["mainBeamSelfWeight"] * p["mainBeamCount"] * p["overhangLength"]
    )
    per_side = service_total / max(p["sideCount"], 1.0)

    front_count = max(p["frontRopesPerSide"], 1.0)
    rear_count = max(p["rearRopesPerSide"], 1.0)
    front_vertical = per_side * p["frontRopeShare"] / front_count
    rear_vertical = per_side * p["rearRopeShare"] / rear_count
    front_angle = math.radians(p["frontRopeAngle"])
    rear_angle = math.radians(p["rearRopeAngle"])
    front_tension = front_vertical / max(math.sin(front_angle), 1e-6)
    rear_tension = rear_vertical / max(math.sin(rear_angle), 1e-6)
    front_safety = p["wireBreakForce"] / max(front_tension, 1e-9)
    rear_safety = p["wireBreakForce"] / max(rear_tension, 1e-9)
    min_wire_safety = min(front_safety, rear_safety)

    rope_layout_ok = (
        p["sideCount"] >= 2.0
        and p["frontRopesPerSide"] >= 1.0
        and p["rearRopesPerSide"] >= 1.0
    )
    rope_share_ok = abs(
        p["frontRopeShare"] + p["rearRopeShare"] - 1.0
    ) <= 0.01
    clamp_ok = p["wireClampCount"] >= 4.0
    wire_ok = (
        min_wire_safety + 1e-9 >= p["wireMinSafety"]
        and rope_layout_ok
        and rope_share_ok
        and clamp_ok
    )

    horizontal_per_side = (
        front_count * front_tension * math.cos(front_angle)
        + rear_count * rear_tension * math.cos(rear_angle)
    )
    total_horizontal = horizontal_per_side * p["sideCount"]
    anchor_demand = total_horizontal * p["connectionDesignFactor"]
    anchor_capacity = p["anchorCount"] * p["anchorTensionCapacity"]
    anchor_ok = (
        anchor_demand <= anchor_capacity + 1e-9
        and p["anchorLength"] > 0.0
    )

    design_total = (
        p["deadLoadFactor"]
        * (
            p["deckAndSecondaryLoad"] * area
            + p["mainBeamSelfWeight"]
            * p["mainBeamCount"]
            * p["overhangLength"]
        )
        + p["liveLoadFactor"] * p["liveLoad"] * area
    )
    overturn_demand = design_total * p["overhangLength"] / 2.0
    resisting_moment = (
        p["supportMomentCapacity"]
        + p["rearSupportVerticalCapacity"] * p["anchorLength"]
    )
    actual_stability = (
        resisting_moment / overturn_demand
        if overturn_demand > 0.0
        else 999.0
    )
    support_ok = (
        actual_stability + 1e-9 >= p["stabilityFactor"]
        and p["anchorLength"] > 0.0
    )

    secondary_area_design = (
        p["deadLoadFactor"] * p["deckAndSecondaryLoad"]
        + p["liveLoadFactor"] * p["liveLoad"]
    )
    secondary_line_design = secondary_area_design * p["secondaryBeamSpacing"]
    secondary_moment = (
        secondary_line_design * p["secondaryBeamSpan"] ** 2 / 8.0
    )
    secondary_stress = secondary_moment * 1e6 / p["secondaryBeamW"]

    # 铺板按1m宽板带、单跨简支受弯；W由板厚形成。
    panel_line_design = secondary_area_design * 1.0
    panel_moment = panel_line_design * p["panelSpan"] ** 2 / 8.0
    panel_w = 1000.0 * p["panelThickness"] ** 2 / 6.0
    panel_stress = panel_moment * 1e6 / panel_w
    panel_thickness_ok = p["panelThickness"] >= 50.0 - 1e-9

    weld_demand_per_connection = anchor_demand / p["anchorCount"]
    weld_capacity_per_connection = (
        p["weldThroat"]
        * p["weldEffectiveLength"]
        * p["weldStrength"]
        / 1000.0
    )
    weld_shear_ok = (
        weld_demand_per_connection
        <= weld_capacity_per_connection + 1e-9
    )

    guardrail_checks = [
        ("外侧略高于内侧", p["outerSideHigher"]),
        ("固定防护栏杆", p["guardrailFixed"]),
        ("防护挡板完全封闭", p["guardrailFullyEnclosed"]),
        ("起重吊环", p["liftingRingInstalled"]),
        ("承载吊环", p["loadBearingRingInstalled"]),
    ]
    guardrail_ok = all(ok for _, ok in guardrail_checks)
    guardrail_failed = [label for label, ok in guardrail_checks if not ok]

    results = [
        _item(
            1,
            "main_beam_bending",
            "主梁抗弯及悬挑长度构造",
            bending_stress,
            p["steelStrength"],
            "N/mm²",
            "JGJ 80-2016 6.4.2、附录C.0.3；PDF第15、23-24页",
            True,
            (
                f"按最大支承区间L={beam_span:.3f}m计，M=qL²/8，σ=M/Wx≤f；"
                f"悬挑长度{_yes_no(overhang_ok)}5m限制"
            ),
            ok=bending_stress <= p["steelStrength"] + 1e-9 and overhang_ok,
        ),
        _item(
            2,
            "main_beam_deflection",
            "主梁挠度",
            deflection,
            deflection_limit,
            "mm",
            "JGJ 80-2016 附录A A.0.2-4、附录C.0.3；PDF第19、23-24页",
            False,
            (
                "v=5qkL⁴/(384EIx)，采用标准值；"
                "挠度限值采用模块假定L/250，JGJ 80-2016未给专用值"
            ),
        ),
        _item(
            3,
            "wire_rope_capacity",
            "钢丝绳/斜拉承载力",
            min_wire_safety,
            p["wireMinSafety"],
            "—",
            "JGJ 80-2016 6.4.3、6.4.7、附录C.0.4；PDF第15、24页",
            True,
            (
                "K=F0/T≥8；两边各设前后两道，前/后道及每根绳分别计算。"
                f"布置{_yes_no(rope_layout_ok)}，荷载比例{_yes_no(rope_share_ok)}，"
                f"绳卡{int(p['wireClampCount'])}个{_yes_no(clamp_ok)}4个下限"
            ),
            ok=wire_ok,
            ratio=(
                p["wireMinSafety"] / min_wire_safety
                if min_wire_safety > 0.0
                else 999.0
            ),
        ),
        _item(
            4,
            "anchor_connection_capacity",
            "锚固或连接承载力",
            anchor_demand,
            anchor_capacity,
            "kN",
            "JGJ 80-2016 6.4.1、6.4.5；PDF第15页",
            True,
            (
                "按各道斜拉绳水平分量合力计算锚固/连接受拉需求，"
                "并乘附加安全系数；节点群锚、预埋件及主体结构须专项验算"
            ),
            ok=anchor_ok,
        ),
        _item(
            5,
            "overturning_support",
            "抗倾覆与支承构造",
            actual_stability,
            p["stabilityFactor"],
            "—",
            "JGJ 80-2016 6.4.1、6.4.4、6.4.5；PDF第15页",
            True,
            (
                "K=(后部支承力矩+后部竖向承载力×Lanchor)/"
                "(设计总荷载×Lraise/2)≥[K]；"
                f"Lanchor={p['anchorLength']:.2f}m，连接点须设置在主体结构并可靠连接"
            ),
            ok=support_ok,
            ratio=(
                p["stabilityFactor"] / actual_stability
                if actual_stability > 0.0
                else 999.0
            ),
        ),
        _item(
            6,
            "secondary_beam_bending",
            "次梁抗弯",
            secondary_stress,
            p["secondaryBeamF"],
            "N/mm²",
            "JGJ 80-2016 附录C C.0.2；PDF第23-24页",
            True,
            (
                "简化假定次梁为单跨简支梁：q=γG·面恒载·b+γQ·面活载·b，"
                "M=q·L²/8，σ=M/W≤f；b为次梁间距，L为输入的次梁跨度"
            ),
        ),
        _item(
            7,
            "platform_panel_bending",
            "铺板抗弯",
            panel_stress,
            p["panelF"],
            "N/mm²",
            "JGJ 80-2016 附录C C.0.1、C.0.2；PDF第23页",
            True,
            (
                "按1m宽板带、单跨简支板：q=γG·gk+γQ·qk，"
                "M=q·L²/8，W=1000·t²/6，σ=M/W≤f；"
                f"铺板厚度{_yes_no(panel_thickness_ok)}50mm下限"
            ),
            ok=panel_stress <= p["panelF"] + 1e-9 and panel_thickness_ok,
        ),
        _item(
            8,
            "weld_connection",
            "焊缝抗剪连接",
            weld_demand_per_connection,
            weld_capacity_per_connection,
            "kN",
            "JGJ 80-2016 6.4.5；PDF第15页（GB 50017专项验算）",
            True,
            (
                "保守取斜拉绳水平分量附加安全后的群锚总需求平均分配至anchorCount条焊缝；"
                "单条抗剪承载力=he·lw·fw，未计拉剪组合、焊缝群偏心及母材破坏"
            ),
            ok=weld_shear_ok,
        ),
        _item(
            9,
            "guardrail_configuration",
            "防护栏杆及吊环构造",
            1.0 if guardrail_ok else 0.0,
            1.0,
            "—",
            "JGJ 80-2016 6.4.6、6.4.8；PDF第15页",
            True,
            (
                "逐项核对外侧略高、固定防护栏杆、挡板完全封闭、起重吊环及承载吊环；"
                + (
                    "全部满足"
                    if guardrail_ok
                    else "未满足项：" + "、".join(guardrail_failed)
                )
            ),
            ok=guardrail_ok,
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
                    "name": "建筑施工高处作业安全技术规范",
                    "clauses": [
                        "6.4.1",
                        "6.4.2",
                        "6.4.3",
                        "6.4.4",
                        "6.4.5",
                        "6.4.6",
                        "6.4.7",
                        "6.4.8",
                        "6.4.10",
                        "附录C C.0.1",
                        "附录C C.0.2",
                        "附录C C.0.3",
                        "附录C C.0.4",
                        "附录C C.0.5",
                    ],
                    "pages": "PDF第15、23-24页（标准第10、18-19页）",
                },
            ],
            "missing": [],
            "complete": False,
            "gaps": [
                "JGJ 80-2016 附录C给出次梁、主梁弯曲、钢丝绳及下支承斜撑的验算框架，但未直接给出本模块中的主梁挠度、焊缝、锚固连接和抗倾覆通用公式。",
                "主梁挠度采用多支承区间简支梁包络公式v=5qkL⁴/(384EIx)，限值L/250为模块假定；未按连续梁、节点刚度和前后吊点实际变形进行空间分析。",
                "主梁弯曲将墙边、前后吊点之间的最大区间按简支跨包络，M=qL²/8；未直接采用附录C.0.3中带集中力的连续梁弯矩分配，正式应用须按实际吊点位置复核。",
                "第6项将次梁按单跨简支梁包络，线荷载由面荷载乘次梁间距形成；当次梁带悬臂时应按附录C.0.2的Mc公式或连续梁包络另行复核，本模块未自动识别悬臂。",
                "第7项取1m宽板带按简支板验算；铺板W由输入厚度形成，未考虑双向板作用、集中荷载、板材铺向、拼接和固定方式。",
                "第8项只按喉厚、有效长度和抗剪强度验算单条角焊缝，并将群锚总水平需求平均分配；未验算拉剪组合、有效焊缝长度折减、焊缝群偏心、母材强度及预埋件混凝土破坏。",
                "第9项为6.4.6、6.4.8的声明式构造符合项；不校核吊环规格、材质、焊缝、混凝土锚固和栏杆外力承载力。",
                "前后道钢丝绳竖向荷载比例默认各0.5，仅用于逐道独立验算；实际分配受吊点刚度、标高及钢丝绳长度影响，须由专项设计确定。",
                "锚固/连接项只校核斜拉绳水平分量的群锚受拉需求，未覆盖预埋件焊缝、混凝土锥体破坏、边距、抗剪及主体结构局部承载力。",
                "抗倾覆项采用绕建筑边沿的简化力矩平衡，支承力矩能力和后部竖向承载力均为输入值；JGJ 80-2016未给出专用抗倾覆安全系数，1.5为模块假定。",
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
            "mainBeamCalcSpan_m": round(beam_span, 3),
            "mainBeamTributaryWidth_m": round(tributary_width, 3),
            "deadLineLoad_kN_m": round(dead_line, 3),
            "liveLineLoad_kN_m": round(live_line, 3),
            "designLineLoad_kN_m": round(design_line, 3),
            "designMoment_kNm": round(design_moment, 3),
            "bendingStress_N_mm2": round(bending_stress, 2),
            "serviceLineLoad_kN_m": round(service_line, 3),
            "deflection_mm": round(deflection, 3),
            "deflectionLimit_mm": round(deflection_limit, 3),
            "serviceVerticalLoad_kN": round(service_total, 3),
            "perSideVerticalLoad_kN": round(per_side, 3),
            "frontRopeTension_kN": round(front_tension, 3),
            "rearRopeTension_kN": round(rear_tension, 3),
            "frontRopeSafety": round(front_safety, 3),
            "rearRopeSafety": round(rear_safety, 3),
            "minRopeSafety": round(min_wire_safety, 3),
            "totalHorizontalTieForce_kN": round(total_horizontal, 3),
            "anchorDemandDesign_kN": round(anchor_demand, 3),
            "anchorCapacity_kN": round(anchor_capacity, 3),
            "overturnDemand_kNm": round(overturn_demand, 3),
            "resistingMoment_kNm": round(resisting_moment, 3),
            "actualStabilityFactor": round(actual_stability, 3),
            "overhangLengthLimit_m": 5.0,
            "overhangConditionOk": overhang_ok,
            "ropeLayoutConditionOk": rope_layout_ok,
            "eachRopeIndependentlyCalculated": True,
            "ropeClampLimit": 4,
            "ropeClampConditionOk": clamp_ok,
            "secondaryBeamAreaDesign_kN_m2": round(secondary_area_design, 3),
            "secondaryBeamLineDesign_kN_m": round(secondary_line_design, 3),
            "secondaryBeamMoment_kNm": round(secondary_moment, 3),
            "secondaryBeamStress_N_mm2": round(secondary_stress, 2),
            "panelLineDesign_kN_m": round(panel_line_design, 3),
            "panelW_mm3": round(panel_w, 1),
            "panelMoment_kNm": round(panel_moment, 3),
            "panelStress_N_mm2": round(panel_stress, 2),
            "panelThicknessLimit_mm": 50.0,
            "panelThicknessConditionOk": panel_thickness_ok,
            "weldDemandPerConnection_kN": round(
                weld_demand_per_connection, 3
            ),
            "weldCapacityPerConnection_kN": round(
                weld_capacity_per_connection, 3
            ),
            "guardrailConfigurationOk": guardrail_ok,
            "guardrailFailedItems": guardrail_failed,
        },
        "assumptions": [
            "pmsc.ini [RaisePlat information]中的3.9m×3.5m、16a主梁、12.6次梁、6×19 d=18.5mm钢丝绳、Lraise=3.5m、Lanchor=1.5m及5kN/m²堆载仅作为计算样例，不是推荐值；工程中必须按专项设计和产品证明替换。",
            "每根主梁按相同荷载分担，主梁最大区间按简支梁包络，M=qL²/8，挠度v=5qkL⁴/(384EIx)；该模型偏于安全但不能替代连续梁或空间框架分析。",
            "主梁挠度限值采用L/250，属于JGJ 80-2016未明确给出的模块假定，须由项目专项方案确认。",
            "斜拉平台按两边各前后一道钢丝绳计算，每道均单独验算；前后道默认各承担该侧竖向荷载0.5，每根绳均单独满足[K]=8。",
            "钢丝绳卡按每个绳端不少于4个校核；卡环型号、绳卡与绳径匹配、锐角处软垫及紧固方法仍须按第6.4.7条现场验收。",
            "锚固/连接受拉需求取斜拉绳水平分量合力并乘1.5附加安全系数；该系数及群锚分配模型为模块假定。",
            "抗倾覆按绕建筑边沿的简化力矩平衡，后部支承力矩与竖向承载力由用户输入；JGJ 80-2016只提出稳定性要求，未给出专用安全系数。",
            "次梁按跨中最大正弯矩包络 M=q·L²/8，q由平台面设计荷载乘以输入次梁间距形成；该式偏于安全，不自动采用连续梁调幅或悬臂有利效应。",
            "铺板按1m宽、跨度为panelSpan的单跨简支板计算，W=1000·t²/6；默认50mm仅对应附录C.0.1最低厚度样例，实际强度须按木板或等效材料产品证明输入。",
            "焊缝采用仅抗剪的保守模型：每条焊缝需求=anchorDemand/anchorCount，承载力=he·lw·fw；若节点实际承受拉剪组合，必须按GB 50017补充组合验算。",
            "栏杆与吊环按用户申报的构造状态作符合性判断；6.4.6分别核对起重吊环和承载吊环，6.4.8核对平台外高内低、固定栏杆及挡板完全封闭。",
            "所有构件应设置在主体结构上并可靠连接；未经专项设计的临时设施不得设置悬挑式操作平台。",
        ],
    }


def _yes_no(value: bool) -> str:
    return "满足" if value else "不满足"
