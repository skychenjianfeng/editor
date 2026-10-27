"""附着式升降脚手架验算。

依据：JGJ 202-2010《建筑施工工具式脚手架安全技术规范》。

本模块按第 4 章的分项系数、构件计算公式和构造要求，对风荷载、
竖向主框架、附墙穿墙螺栓、防坠装置、升降动力设备、悬吊梁、
导轨专项验算回填值、外立面剪刀撑构造及升降同步/架体构造进行简化验算。
未覆盖的完整空间分析、变形、连接细部、悬吊梁支座和节点验算在
standards.gaps 中列明。
"""

from __future__ import annotations

import math
from typing import Any

MODULE_KEY = "attached-lifting-scaffold"
STANDARD = "JGJ 202-2010"

# 几何和荷载基准取自品茗 pmsc.ini 的 [AttachedLifting information] 示例。
# 这些值是输入基线，不是规范推荐值，也不表示示例工程必然合格。
DEFAULTS: dict[str, Any] = {
    "H": 65.0,
    "storeyHeight": 3.6,
    "h": 1.8,
    "la": 1.5,
    "lb": 0.8,
    "n": 8.0,
    "k": 4.0,
    "overhang": 0.3,
    "cantileverHeight": 3.6,
    "polesPerPoint": 4.0,
    "w0": 0.3,
    "muZ": 1.24,
    "muS": 1.0,
    "betaZ": 1.0,
    "braceAngle": 50.0,
    "bracePhi": 0.75,
    "braceArea": 506.0,
    "f": 205.0,
    "poleWeight": 0.129,
    "boardWeight": 0.35,
    "railWeight": 0.17,
    "netWeight": 0.01,
    "boardLayers": 2.0,
    "liveLayers": 2.0,
    "liveLoad": 3.0,
    "liftLiveLoad": 0.5,
    "mainFramePhi": 0.75,
    "mainFramePoles": 4.0,
    "mainFrameArea": 506.0,
    "impactFactor": 2.0,
    "attachBoltCount": 2.0,
    "attachBoltD": 30.0,
    "attachBoltDe": 26.72,
    "attachBoltFtb": 400.0,
    "attachBoltFvb": 320.0,
    "concreteWidth": 300.0,
    "concreteFc": 13.026,
    "betaB": 0.39,
    "betaL": 1.73,
    "antiFallCapacity": 100.0,
    "antiFallBrakeDistance": 60.0,
    "antiFallPerPoint": 1.0,
    "antiFallMechanical": 1.0,
    "antiFallIndependent": 1.0,
    "syncControlType": 1.0,
    "syncLoadWarnPct": 15.0,
    "syncLoadStopPct": 30.0,
    "syncHeightStopMm": 30.0,
    "liftingDeviceCapacity": 40.0,
    "suspensionBeamLength": 1.0,
    "suspensionBeamSectionModulus": 220000.0,
    "suspensionBeamSteelStrength": 205.0,
    "suspensionBeamLoad": 15.0,
    "guideRailUtilization": 0.75,
    "facadeBraceFullHeight": 1.0,
    "facadeBraceIntegrated": 1.0,
    "facadeBraceNodeFastened": 1.0,
    "facadeBraceAngle": 50.0,
    "overhangSymmetricTie": 1.0,
    "overhangTieAngle": 50.0,
    "antiFallSteelRodApplicable": 1.0,
    "antiFallSteelRodDiameter": 30.0,
    "antiFallDustProtection": 1.0,
    "antiFallSensitivity": 1.0,
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

    return {
        "module": MODULE_KEY,
        "title": "附着式升降脚手架",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "geometry",
                "title": "工程与架体几何",
                "fields": [
                    num("H", "结构高度 H", "m", 65.0, 10.0, 300.0, 0.5, "JGJ 202-2010 4.1.2"),
                    num("storeyHeight", "层高", "m", 3.6, 2.0, 6.0, 0.1, "JGJ 202-2010 4.4.2"),
                    num("h", "步距 h", "m", 1.8, 0.9, 3.0, 0.1, "JGJ 202-2010 4.2.2、4.4.2"),
                    num("la", "架体支承跨度/机位间距 la", "m", 1.5, 0.6, 7.0, 0.1, "JGJ 202-2010 2.1.12、4.4.2"),
                    num("lb", "架体宽度 lb", "m", 0.8, 0.6, 1.2, 0.05, "JGJ 202-2010 2.1.11、4.4.2"),
                    num("n", "架体步数 n", "步", 8.0, 1.0, 30.0, 1.0, "JGJ 202-2010 2.1.10、4.4.2"),
                    num("k", "提升机位/附墙支承点数 k", "个", 4.0, 1.0, 12.0, 1.0, "JGJ 202-2010 4.3.5、4.4.5"),
                    num("overhang", "水平悬挑长度", "m", 0.3, 0.0, 2.0, 0.05, "JGJ 202-2010 2.1.14、4.4.2"),
                    num("cantileverHeight", "最高支承点以上悬臂高度", "m", 3.6, 0.0, 6.0, 0.1, "JGJ 202-2010 2.1.13、4.4.8"),
                    num("polesPerPoint", "每个机位竖向杆件数", "根", 4.0, 1.0, 8.0, 1.0, "JGJ 202-2010 4.2.2（杆数按实际构造输入）"),
                ],
            },
            {
                "key": "wind",
                "title": "风荷载与水平支撑",
                "fields": [
                    num("w0", "基本风压 w0", "kN/m²", 0.3, 0.0, 1.5, 0.05, "JGJ 202-2010 4.1.2"),
                    num("muZ", "风压高度变化系数 μz", "—", 1.24, 0.5, 3.0, 0.01, "JGJ 202-2010 4.1.2"),
                    num("muS", "脚手架风荷载体型系数 μs", "—", 1.0, 0.0, 2.0, 0.05, "JGJ 202-2010 4.1.2、表4.1.2-4"),
                    num("betaZ", "风振系数 βz", "—", 1.0, 0.5, 2.0, 0.05, "JGJ 202-2010 4.1.2"),
                    num("braceAngle", "水平剪刀撑与水平面夹角", "°", 50.0, 45.0, 60.0, 1.0, "JGJ 202-2010 4.4.12"),
                    num("bracePhi", "水平斜杆稳定系数 φ", "—", 0.75, 0.05, 1.0, 0.01, "JGJ 202-2010 4.3.2、附录A"),
                    num("braceArea", "水平斜杆截面积 A", "mm²", 506.0, 10.0, 5000.0, 1.0, "JGJ 202-2010 4.2.9"),
                    num("f", "钢材强度设计值 f", "N/mm²", 205.0, 100.0, 400.0, 5.0, "JGJ 202-2010 4.2.1、4.3.2"),
                ],
            },
            {
                "key": "vertical_load",
                "title": "竖向荷载与主框架",
                "fields": [
                    num("poleWeight", "立杆每米自重标准值", "kN/m", 0.129, 0.01, 0.5, 0.001, "JGJ 202-2010 4.1.2"),
                    num("boardWeight", "脚手板自重标准值", "kN/m²", 0.35, 0.0, 0.6, 0.01, "JGJ 202-2010 表4.1.2-1"),
                    num("railWeight", "栏杆及挡脚板线荷载", "kN/m", 0.17, 0.0, 0.3, 0.01, "JGJ 202-2010 表4.1.2-2"),
                    num("netWeight", "密目安全立网自重", "kN/m²", 0.01, 0.0, 0.05, 0.001, "JGJ 202-2010 4.1.2"),
                    num("boardLayers", "脚手板铺设层数", "层", 2.0, 1.0, 8.0, 1.0, "JGJ 202-2010 4.1.2（层数按实际构造输入）"),
                    num("liveLayers", "同时作业层数", "层", 2.0, 1.0, 4.0, 1.0, "JGJ 202-2010 表4.1.2-3"),
                    num("liveLoad", "使用工况施工活荷载", "kN/m²", 3.0, 0.5, 3.0, 0.5, "JGJ 202-2010 表4.1.2-3"),
                    num("liftLiveLoad", "升降工况施工活荷载", "kN/m²", 0.5, 0.0, 0.5, 0.1, "JGJ 202-2010 表4.1.2-3"),
                    num("mainFramePhi", "主框架压杆稳定系数 φ", "—", 0.75, 0.05, 1.0, 0.01, "JGJ 202-2010 4.3.2、附录A"),
                    num("mainFramePoles", "主框架同时受力杆数", "根", 4.0, 1.0, 8.0, 1.0, "JGJ 202-2010 4.2.2（杆数按实际构造输入）"),
                    num("mainFrameArea", "单根主框架杆截面积 A", "mm²", 506.0, 10.0, 5000.0, 1.0, "JGJ 202-2010 4.2.9"),
                ],
            },
            {
                "key": "attachment",
                "title": "附墙支座与穿墙螺栓",
                "fields": [
                    num("impactFactor", "附墙支座冲击系数", "—", 2.0, 1.0, 2.0, 0.1, "JGJ 202-2010 4.1.8、4.3.5"),
                    num("attachBoltCount", "单支座穿墙螺栓数", "个", 2.0, 1.0, 8.0, 1.0, "JGJ 202-2010 4.3.6；品茗示例输入"),
                    num("attachBoltD", "螺栓螺杆直径 D螺", "mm", 30.0, 8.0, 50.0, 0.5, "JGJ 202-2010 4.3.6-2"),
                    num("attachBoltDe", "螺纹处有效截面直径 d0", "mm", 26.72, 6.0, 45.0, 0.01, "JGJ 202-2010 4.3.6-3"),
                    num("attachBoltFtb", "螺栓抗拉强度设计值 f_t^b", "N/mm²", 400.0, 50.0, 500.0, 5.0, "JGJ 202-2010 4.2.7、4.3.6"),
                    num("attachBoltFvb", "螺栓抗剪强度设计值 f_v^b", "N/mm²", 320.0, 50.0, 500.0, 5.0, "JGJ 202-2010 4.2.7、4.3.6"),
                    num("concreteWidth", "混凝土墙厚 b", "mm", 300.0, 80.0, 1000.0, 10.0, "JGJ 202-2010 4.3.7"),
                    num("concreteFc", "混凝土轴心抗压强度设计值 fc", "N/mm²", 13.026, 3.0, 50.0, 0.001, "JGJ 202-2010 4.3.7"),
                    num("betaB", "螺栓孔混凝土受荷系数 βb", "—", 0.39, 0.1, 1.0, 0.01, "JGJ 202-2010 4.3.7"),
                    num("betaL", "局部承压提高系数 βl", "—", 1.73, 1.0, 3.0, 0.01, "JGJ 202-2010 4.3.7"),
                ],
            },
            {
                "key": "safety",
                "title": "防坠、同步与构造",
                "fields": [
                    num("antiFallCapacity", "单个防坠装置承载力设计值", "kN", 100.0, 1.0, 500.0, 1.0, "JGJ 202-2010 4.3.9、4.5.3"),
                    num("antiFallBrakeDistance", "防坠装置制动距离", "mm", 60.0, 0.0, 300.0, 1.0, "JGJ 202-2010 表4.5.3"),
                    num("antiFallPerPoint", "每个升降点防坠装置数", "个", 1.0, 0.0, 3.0, 1.0, "JGJ 202-2010 4.5.3"),
                    num("antiFallMechanical", "机械全自动防坠（1是/0否）", "—", 1.0, 0.0, 1.0, 1.0, "JGJ 202-2010 4.5.3"),
                    num("antiFallIndependent", "防坠与提升独立固定（1是/0否）", "—", 1.0, 0.0, 1.0, 1.0, "JGJ 202-2010 4.3.9、4.5.3"),
                    num("syncControlType", "同步控制类型（1限制荷载或高差）", "—", 1.0, 0.0, 1.0, 1.0, "JGJ 202-2010 4.5.1、4.5.4"),
                    num("syncLoadWarnPct", "荷载同步报警阈值", "%", 15.0, 0.0, 50.0, 1.0, "JGJ 202-2010 4.5.4"),
                    num("syncLoadStopPct", "荷载同步停机阈值", "%", 30.0, 0.0, 60.0, 1.0, "JGJ 202-2010 4.5.4"),
                    num("syncHeightStopMm", "水平高差停机阈值", "mm", 30.0, 0.0, 100.0, 1.0, "JGJ 202-2010 4.5.4"),
                    num("antiFallSteelRodApplicable", "采用钢吊杆式防坠装置（1是/0否）", "—", 1.0, 0.0, 1.0, 1.0, "JGJ 202-2010 4.5.3-6"),
                    num("antiFallSteelRodDiameter", "钢吊杆直径", "mm", 30.0, 0.0, 100.0, 1.0, "JGJ 202-2010 4.5.3-6"),
                    num("antiFallDustProtection", "已设防尘防污染措施（1是/0否）", "—", 1.0, 0.0, 1.0, 1.0, "JGJ 202-2010 4.5.3-4"),
                    num("antiFallSensitivity", "防坠装置灵敏可靠、运转自如（1是/0否）", "—", 1.0, 0.0, 1.0, 1.0, "JGJ 202-2010 4.5.3-4"),
                ],
            },
            {
                "key": "lifting_equipment",
                "title": "升降动力设备与悬吊梁",
                "fields": [
                    num(
                        "liftingDeviceCapacity",
                        "升降动力设备额定值 Nc",
                        "kN",
                        40.0,
                        1.0,
                        500.0,
                        1.0,
                        "JGJ 202-2010 4.3.12-2",
                    ),
                    num(
                        "suspensionBeamLoad",
                        "悬臂梁端部实际验算荷载（冲击及不均匀系数前）",
                        "kN",
                        15.0,
                        0.1,
                        1000.0,
                        0.1,
                        "JGJ 202-2010 4.3.11-1",
                    ),
                    num(
                        "suspensionBeamLength",
                        "悬臂梁计算长度 L",
                        "m",
                        1.0,
                        0.1,
                        5.0,
                        0.05,
                        "JGJ 202-2010 4.3.11-1、4.3.11-2",
                    ),
                    num(
                        "suspensionBeamSectionModulus",
                        "悬臂梁截面模量 W",
                        "mm³",
                        220000.0,
                        1000.0,
                        10000000.0,
                        1000.0,
                        "JGJ 202-2010 4.3.11-2",
                    ),
                    num(
                        "suspensionBeamSteelStrength",
                        "悬臂梁钢材抗弯强度设计值 f",
                        "N/mm²",
                        205.0,
                        100.0,
                        400.0,
                        5.0,
                        "JGJ 202-2010 4.2.1、4.3.11-2",
                    ),
                ],
            },
            {
                "key": "guide_and_brace",
                "title": "导轨专项验算回填与外立面剪刀撑",
                "fields": [
                    num(
                        "guideRailUtilization",
                        "导轨专项验算外部回填利用率",
                        "—",
                        0.75,
                        0.0,
                        5.0,
                        0.01,
                        "JGJ 202-2010 4.3.8（抗弯、抗压、抗剪、焊缝、稳定、锚栓和变形外部专项验算）",
                    ),
                    num(
                        "facadeBraceFullHeight",
                        "外立面全高连续剪刀撑（1是/0否）",
                        "—",
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        "JGJ 202-2010 4.4.12",
                    ),
                    num(
                        "facadeBraceIntegrated",
                        "剪刀撑将主框架、水平桁架和架体连成一体（1是/0否）",
                        "—",
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        "JGJ 202-2010 4.4.12",
                    ),
                    num(
                        "facadeBraceNodeFastened",
                        "剪刀撑与覆盖范围内每个主节点扣紧（1是/0否）",
                        "—",
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        "JGJ 202-2010 4.4.12",
                    ),
                    num(
                        "facadeBraceAngle",
                        "外立面剪刀撑斜杆水平夹角",
                        "°",
                        50.0,
                        45.0,
                        60.0,
                        1.0,
                        "JGJ 202-2010 4.4.12",
                    ),
                    num(
                        "overhangSymmetricTie",
                        "悬挑端成对对称斜拉杆（1是/0否）",
                        "—",
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        "JGJ 202-2010 4.4.12",
                    ),
                    num(
                        "overhangTieAngle",
                        "悬挑端斜拉杆水平夹角",
                        "°",
                        50.0,
                        45.0,
                        90.0,
                        1.0,
                        "JGJ 202-2010 4.4.12",
                    ),
                ],
            },
        ],
    }


def _merged(params: dict[str, Any]) -> dict[str, float]:
    merged = dict(DEFAULTS)
    for key, value in (params or {}).items():
        if key in merged:
            merged[key] = value
    p = {key: float(value) for key, value in merged.items()}

    positive = (
        "H",
        "storeyHeight",
        "h",
        "la",
        "lb",
        "n",
        "k",
        "polesPerPoint",
        "bracePhi",
        "braceArea",
        "f",
        "boardLayers",
        "liveLayers",
        "mainFramePhi",
        "mainFramePoles",
        "mainFrameArea",
        "attachBoltCount",
        "attachBoltD",
        "attachBoltDe",
        "attachBoltFtb",
        "attachBoltFvb",
        "concreteWidth",
        "concreteFc",
        "betaB",
        "betaL",
        "antiFallCapacity",
        "liftingDeviceCapacity",
        "suspensionBeamLength",
        "suspensionBeamSectionModulus",
        "suspensionBeamSteelStrength",
        "suspensionBeamLoad",
    )
    for key in positive:
        if p[key] <= 0:
            raise ValueError(f"{key} 必须大于 0")
    if not 0.0 < p["braceAngle"] < 90.0:
        raise ValueError("braceAngle 应在 0°～90° 范围内")
    if p["attachBoltDe"] > p["attachBoltD"] + 1e-9:
        raise ValueError("attachBoltDe 不得大于 attachBoltD")
    if p["impactFactor"] < 1.0:
        raise ValueError("impactFactor 不得小于 1.0")
    if p["guideRailUtilization"] < 0.0:
        raise ValueError("guideRailUtilization 不得小于 0")
    if not 0.0 < p["facadeBraceAngle"] < 90.0:
        raise ValueError("facadeBraceAngle 应在 0°～90° 范围内")
    if not 0.0 < p["overhangTieAngle"] < 90.0:
        raise ValueError("overhangTieAngle 应在 0°～90° 范围内")
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

    body_height = p["n"] * p["h"]
    tributary_area = p["la"] * p["lb"]
    wk = p["betaZ"] * p["muZ"] * p["muS"] * p["w0"]

    # 4.1.2、4.1.5：风荷载标准值及水平风荷载设计值。
    wind_point_force = 1.4 * wk * p["la"] * p["h"]
    brace_axial = wind_point_force / math.cos(math.radians(p["braceAngle"]))
    brace_stress = brace_axial * 1000.0 / (p["bracePhi"] * p["braceArea"])

    # 4.1.2、4.1.5：单个机位范围内永久荷载、施工活荷载及风弯矩。
    tube_dead = p["poleWeight"] * body_height * p["polesPerPoint"]
    board_dead = p["boardWeight"] * tributary_area * p["boardLayers"]
    rail_dead = p["railWeight"] * p["la"] * 2.0 * p["boardLayers"]
    net_dead = p["netWeight"] * p["la"] * body_height
    dead_load = tube_dead + board_dead + rail_dead + net_dead
    use_live = p["liveLoad"] * tributary_area * p["liveLayers"]
    lift_live = p["liftLiveLoad"] * tributary_area * p["liveLayers"]
    use_design_load = 1.2 * dead_load + 1.4 * use_live
    lift_design_load = 1.2 * dead_load + 1.4 * lift_live

    wind_line_design = 1.4 * wk * p["la"]
    wind_moment = wind_line_design * p["h"] ** 2 / 10.0
    wind_chord_force = wind_moment / p["lb"]
    main_frame_demand = use_design_load + wind_chord_force
    main_frame_capacity = (
        p["mainFramePhi"]
        * p["mainFramePoles"]
        * p["mainFrameArea"]
        * p["f"]
        / 1000.0
    )

    # 4.1.8、4.3.5～4.3.7：支座冲击系数、螺栓拉剪相关和孔壁局部承压。
    support_vertical = p["impactFactor"] * use_design_load
    support_horizontal = p["impactFactor"] * 1.4 * wk * p["la"] * body_height
    bolt_shear = support_vertical / p["attachBoltCount"]
    bolt_tension = support_horizontal / p["attachBoltCount"]
    bolt_shear_capacity = (
        math.pi * p["attachBoltD"] ** 2 / 4.0 * p["attachBoltFvb"] / 1000.0
    )
    bolt_tension_capacity = (
        math.pi * p["attachBoltDe"] ** 2 / 4.0 * p["attachBoltFtb"] / 1000.0
    )
    bolt_interaction = math.sqrt(
        (bolt_shear / bolt_shear_capacity) ** 2
        + (bolt_tension / bolt_tension_capacity) ** 2
    )
    concrete_bearing_demand = bolt_shear
    concrete_bearing_capacity = (
        1.35
        * p["betaB"]
        * p["betaL"]
        * p["concreteFc"]
        * p["concreteWidth"]
        * p["attachBoltD"]
        / 1000.0
    )
    concrete_ratio = concrete_bearing_demand / concrete_bearing_capacity
    attachment_ok = bolt_interaction <= 1.0 + 1e-9 and concrete_ratio <= 1.0 + 1e-9

    # 4.3.9、4.5.3：使用/升降不利工况乘冲击系数，并校核制动距离和独立设置。
    anti_fall_demand = p["impactFactor"] * max(use_design_load, lift_design_load)
    anti_fall_brake_limit = 80.0 if p["k"] >= 3.0 else 150.0
    steel_rod_ok = (
        p["antiFallSteelRodApplicable"] < 0.5
        or p["antiFallSteelRodDiameter"] >= 25.0 - 1e-9
    )
    anti_fall_ok = (
        anti_fall_demand <= p["antiFallCapacity"] + 1e-9
        and p["antiFallBrakeDistance"] <= anti_fall_brake_limit + 1e-9
        and p["antiFallPerPoint"] >= 1.0
        and p["antiFallMechanical"] >= 1.0
        and p["antiFallIndependent"] >= 1.0
        and steel_rod_ok
        and p["antiFallDustProtection"] >= 1.0
        and p["antiFallSensitivity"] >= 1.0
    )
    anti_fall_ratio = max(
        anti_fall_demand / p["antiFallCapacity"],
        p["antiFallBrakeDistance"] / anti_fall_brake_limit,
    )

    # 4.3.12：升降动力设备按升降工况单机位总荷载设计值的 2 倍选型。
    lifting_device_demand = 2.0 * lift_design_load
    lifting_device_ok = (
        lifting_device_demand <= p["liftingDeviceCapacity"] + 1e-9
    )

    # 4.3.11：升降/防坠工况乘冲击系数 2，使用工况再乘荷载不均匀系数 1.3。
    # 悬臂梁端部荷载取实际专项验算值；本模块只给出 M=N·L 的弯曲强度包络。
    suspension_beam_lift_load = 2.0 * p["suspensionBeamLoad"]
    suspension_beam_use_load = 2.0 * 1.3 * p["suspensionBeamLoad"]
    suspension_beam_end_load = max(
        suspension_beam_lift_load,
        suspension_beam_use_load,
    )
    suspension_beam_moment = (
        suspension_beam_end_load * p["suspensionBeamLength"]
    )
    suspension_beam_moment_capacity = (
        p["suspensionBeamSectionModulus"]
        * p["suspensionBeamSteelStrength"]
        / 1_000_000.0
    )
    suspension_beam_ok = (
        suspension_beam_moment <= suspension_beam_moment_capacity + 1e-9
    )

    # 4.3.8：导轨完整截面验算由外部专项计算书完成，本模块仅做利用率回填对比。
    guide_rail_ok = p["guideRailUtilization"] <= 1.0 + 1e-9

    # 4.4.12：外立面剪刀撑及悬挑端斜拉的构造符合项。
    facade_brace_angle_ok = 45.0 - 1e-9 <= p["facadeBraceAngle"] <= 60.0 + 1e-9
    overhang_tie_ok = (
        p["overhang"] <= 1e-9
        or (
            p["overhangSymmetricTie"] >= 1.0
            and p["overhangTieAngle"] >= 45.0 - 1e-9
        )
    )
    brace_construction_ok = (
        p["facadeBraceFullHeight"] >= 1.0
        and p["facadeBraceIntegrated"] >= 1.0
        and p["facadeBraceNodeFastened"] >= 1.0
        and facade_brace_angle_ok
        and overhang_tie_ok
    )

    # 4.4.2、4.4.8、4.5.1、4.5.4：构造限值和同步控制阈值。
    height_limit = 5.0 * p["storeyHeight"]
    span_limit = 7.0
    product_limit = 110.0
    overhang_limit = min(2.0, p["la"] / 2.0)
    cantilever_limit = min(0.4 * body_height, 6.0)
    geometry_checks = {
        "height": body_height <= height_limit + 1e-9,
        "width": p["lb"] <= 1.2 + 1e-9,
        "span": p["la"] <= span_limit + 1e-9,
        "height_span_product": body_height * p["la"] <= product_limit + 1e-9,
        "overhang": p["overhang"] <= overhang_limit + 1e-9,
        "cantilever": p["cantileverHeight"] <= cantilever_limit + 1e-9,
    }
    sync_checks = {
        "control_type": p["syncControlType"] >= 1.0,
        "load_warning": p["syncLoadWarnPct"] <= 15.0 + 1e-9,
        "load_stop": p["syncLoadStopPct"] <= 30.0 + 1e-9,
        "height_stop": p["syncHeightStopMm"] <= 30.0 + 1e-9,
    }
    sync_geometry_checks = {**geometry_checks, **sync_checks}
    sync_geometry_ratio = max(
        body_height / height_limit,
        p["lb"] / 1.2,
        p["la"] / span_limit,
        body_height * p["la"] / product_limit,
        p["overhang"] / overhang_limit if overhang_limit else 999.0,
        p["cantileverHeight"] / cantilever_limit if cantilever_limit else 999.0,
        p["syncLoadWarnPct"] / 15.0 if p["syncLoadWarnPct"] > 0 else 0.0,
        p["syncLoadStopPct"] / 30.0 if p["syncLoadStopPct"] > 0 else 0.0,
        p["syncHeightStopMm"] / 30.0 if p["syncHeightStopMm"] > 0 else 0.0,
    )
    sync_geometry_ok = all(sync_geometry_checks.values())

    results = [
        _item(
            1,
            "wind_horizontal_brace",
            "架体风荷载/水平斜杆",
            brace_stress,
            p["f"],
            "N/mm²",
            "JGJ 202-2010 4.1.2、4.1.5、4.3.2、4.4.12",
            True,
            "w_k=βzμzμsw0；F_w=1.4w_k·la·h；N_br=F_w/cosθ；N_br/(φA)≤f",
        ),
        _item(
            2,
            "main_frame_strength",
            "竖向主框架受压承载力",
            main_frame_demand,
            main_frame_capacity,
            "kN",
            "JGJ 202-2010 4.1.5～4.1.7、4.2.2、4.3.2、4.3.4",
            True,
            "N=1.2G_k+1.4Q_k+M_w/lb≤φ·n_p·A·f；"
            "G_k按单机位条带自重、Q_k按同时作业层活荷载",
        ),
        _item(
            3,
            "wall_bolt_capacity",
            "附墙支座/穿墙螺栓承载力",
            bolt_interaction,
            1.0,
            "—",
            "JGJ 202-2010 4.1.8、4.3.5～4.3.7",
            True,
            "支座设计荷载×2；螺栓拉剪相关 "
            "√[(Nv/Nvb)²+(Nt/Ntb)²]≤1，并校核孔壁混凝土局部承压",
            ok=attachment_ok,
            ratio=max(bolt_interaction, concrete_ratio),
        ),
        _item(
            4,
            "anti_fall_device",
            "防坠装置",
            anti_fall_demand,
            p["antiFallCapacity"],
            "kN",
            "JGJ 202-2010 4.3.9、4.5.3",
            True,
            "使用/升降不利工况×冲击系数≤装置承载力；另校核制动距离、"
            "每点装置数、机械全自动、与提升装置独立固定、防尘防污、"
            "灵敏可靠；钢吊杆式另校核直径≥25mm",
            ok=anti_fall_ok,
            ratio=anti_fall_ratio,
        ),
        _item(
            5,
            "sync_and_geometry",
            "升降同步与架体构造",
            sync_geometry_ratio,
            1.0,
            "—",
            "JGJ 202-2010 4.4.2、4.4.8、4.5.1、4.5.4",
            True,
            f"架体高 {body_height:.2f}≤{height_limit:.2f}m；宽 {p['lb']:.2f}≤1.2m；"
            f"跨度 {p['la']:.2f}≤7m；高×跨 {body_height * p['la']:.2f}≤110m²；"
            f"悬挑 {p['overhang']:.2f}≤{overhang_limit:.2f}m；"
            f"悬臂高 {p['cantileverHeight']:.2f}≤{cantilever_limit:.2f}m；"
            f"同步报警 {p['syncLoadWarnPct']:.0f}%≤15%、停机 "
            f"{p['syncLoadStopPct']:.0f}%≤30%、高差 "
            f"{p['syncHeightStopMm']:.0f}mm≤30mm",
            ok=sync_geometry_ok,
            ratio=sync_geometry_ratio,
        ),
        _item(
            6,
            "lifting_device_capacity",
            "升降动力设备额定承载力",
            lifting_device_demand,
            p["liftingDeviceCapacity"],
            "kN",
            "JGJ 202-2010 4.3.12",
            True,
            "Ns=2×升降工况单机位总荷载设计值≤Nc；"
            "Nc取设备额定值，动力设备型号及产品资料须另行核验",
            ok=lifting_device_ok,
        ),
        _item(
            7,
            "suspension_beam_strength",
            "升降/防坠悬臂梁抗弯",
            suspension_beam_moment,
            suspension_beam_moment_capacity,
            "kN·m",
            "JGJ 202-2010 4.3.11、4.2.3",
            True,
            "端部荷载按实际专项验算值输入；M_lift=2.0·N·L，"
            "M_use=2.0×1.3·N·L，取最不利；M≤W·f。"
            "仅校核简化弯曲强度，变形、抗剪、稳定、焊缝及附墙支座分别另验",
            ok=suspension_beam_ok,
        ),
        _item(
            8,
            "guide_rail_capacity",
            "导轨专项验算利用率",
            p["guideRailUtilization"],
            1.0,
            "—",
            "JGJ 202-2010 4.3.8",
            True,
            "外部专项验算回填项：导轨抗弯、抗压、抗剪、焊缝、平面内外稳定、"
            "锚固螺栓及变形验算利用率必须≤1；本模块不生成截面公式",
            ok=guide_rail_ok,
        ),
        _item(
            9,
            "brace_full_height",
            "外立面全高剪刀撑构造",
            1.0 if brace_construction_ok else 0.0,
            1.0,
            "—",
            "JGJ 202-2010 4.4.12",
            True,
            f"全高连续={p['facadeBraceFullHeight']:.0f}；"
            f"三部分连成一体={p['facadeBraceIntegrated']:.0f}；"
            f"主节点扣紧={p['facadeBraceNodeFastened']:.0f}；"
            f"外立面斜杆夹角={p['facadeBraceAngle']:.0f}°（应45°～60°）；"
            f"悬挑端对称斜拉={p['overhangSymmetricTie']:.0f}；"
            f"斜拉夹角={p['overhangTieAngle']:.0f}°"
            + ("（应≥45°）" if p["overhang"] > 1e-9 else "（无悬挑时本项不适用）"),
            ok=brace_construction_ok,
            ratio=0.0 if brace_construction_ok else 1.0,
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
                    "name": "建筑施工工具式脚手架安全技术规范",
                    "clauses": [
                        "2.1.10",
                        "2.1.11",
                        "2.1.12",
                        "2.1.13",
                        "2.1.14",
                        "4.1.2",
                        "4.1.5",
                        "4.1.6",
                        "4.1.7",
                        "4.1.8",
                        "4.2.1",
                        "4.2.2",
                        "4.2.7",
                        "4.2.9",
                        "4.3.1",
                        "4.3.2",
                        "4.3.4",
                        "4.3.5",
                        "4.3.6",
                        "4.3.7",
                        "4.3.8",
                        "4.3.9",
                        "4.3.11",
                        "4.3.12",
                        "4.4.2",
                        "4.4.5",
                        "4.4.8",
                        "4.4.12",
                        "4.5.1",
                        "4.5.3",
                        "4.5.4",
                    ],
                }
            ],
            "missing": [],
            "complete": False,
            "gaps": [
                "第 3.0.1～3.0.5 条的 Q235 钢管规格、材质证明、焊接材料、"
                "螺栓和锚栓合格证明未自动核验；本模块仅按输入截面和强度设计值计算，"
                "进场构配件仍须查证产品合格证、检验报告并检查锈蚀等外观缺陷。",
                "未建立竖向主框架、水平支承桁架和架体构架的完整空间杆系模型；"
                "本模块用单个机位条带和简化风弯矩验算主框架，不能代替专项施工方案中的整体内力分析。",
                "风荷载按一个水平杆节点条带传给水平剪刀撑，斜杆轴力按单斜杆平衡水平力；"
                "未计入节点刚度、杆件偏心、风振动力效应和前后片桁架荷载分配。",
                "竖向主框架只校核轴压稳定与风弯矩叠加，未分别验算受拉杆强度、"
                "节点板、焊缝、连接螺栓、局部稳定及变形，上述项目见 4.2.2、4.2.3、4.3.4。",
                "附墙支座未验算支座钢构件自身的抗弯、抗压、抗剪、焊缝和平面内外稳定；"
                "穿墙螺栓按各栓平均受力并假定竖载全为剪力、风载全为拉力，实际锚固构造需另行复核。",
                "未验算附墙支座处建筑结构构件的整体承载力，墙体厚度和混凝土强度仅用于"
                "4.3.7 螺栓孔局部承压；连接处混凝土不得低于 C10 的 4.4.5 要求仍需现场核查。",
                "防坠装置承载力由产品资料或型式检验报告输入；本模块仅比较荷载与产品能力，"
                "钢吊杆式装置仅按 4.5.3-6 校核直径不小于 25mm，未计算吊杆强度；"
                "本模块不替代 4.5.3 的制动性能试验、防尘防污和灵敏性现场检查。",
                "4.3.12 仅校核升降动力设备额定值与 Ns=2×升降工况单机位总荷载设计值的关系；"
                "电动机、液压系统、链条、钢丝绳、吊具及索具的选型和产品能力仍须按产品资料核验。",
                "4.3.11 悬臂梁仅按 M=N·L 校核简化弯曲强度，未自动计算抗剪、挠度、"
                "平面内外稳定、焊缝、局部承压，也未分别计算悬挂动力设备和防坠装置的附墙支座。",
                "4.2.3 要求的受弯变形、水平位移等正常使用极限状态未建立通用截面自动公式；"
                "悬臂梁和架体变形须由外部专项计算回填复核。",
                "4.3.8 导轨的完整抗弯、抗压、抗剪、焊缝、稳定、锚栓和变形验算不在本模块内生成；"
                "guideRailUtilization 必须由可复核的外部专项计算书回填，本模块只判断其是否≤1。",
                "4.4.12 外立面全高剪刀撑、主节点扣紧和悬挑端对称斜拉按输入构造符合标志校核；"
                "标志不能替代现场实测、扣件扭矩检查、节点隐蔽验收和照片记录。",
                "第 5 章为高处作业吊篮，不适用于附着式升降脚手架；"
                "本模块未套用第 5 章限值，相关吊篮内容由 suspended-basket 模块处理。",
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
            "bodyHeight_m": round(body_height, 3),
            "tributaryArea_m2": round(tributary_area, 3),
            "wk_kN_m2": round(wk, 4),
            "windPointForce_kN": round(wind_point_force, 3),
            "braceAxial_kN": round(brace_axial, 3),
            "braceStress_N_mm2": round(brace_stress, 3),
            "deadLoad_kN": round(dead_load, 3),
            "useLiveLoad_kN": round(use_live, 3),
            "liftLiveLoad_kN": round(lift_live, 3),
            "useDesignLoad_kN": round(use_design_load, 3),
            "liftDesignLoad_kN": round(lift_design_load, 3),
            "windMoment_kNm": round(wind_moment, 3),
            "windChordForce_kN": round(wind_chord_force, 3),
            "mainFrameDemand_kN": round(main_frame_demand, 3),
            "mainFrameCapacity_kN": round(main_frame_capacity, 3),
            "supportVertical_kN": round(support_vertical, 3),
            "supportHorizontal_kN": round(support_horizontal, 3),
            "boltShear_kN": round(bolt_shear, 3),
            "boltTension_kN": round(bolt_tension, 3),
            "boltShearCapacity_kN": round(bolt_shear_capacity, 3),
            "boltTensionCapacity_kN": round(bolt_tension_capacity, 3),
            "boltInteraction": round(bolt_interaction, 4),
            "concreteBearingDemand_kN": round(concrete_bearing_demand, 3),
            "concreteBearingCapacity_kN": round(concrete_bearing_capacity, 3),
            "concreteBearingRatio": round(concrete_ratio, 4),
            "antiFallDemand_kN": round(anti_fall_demand, 3),
            "antiFallBrakeLimit_mm": anti_fall_brake_limit,
            "liftingDeviceDemand_kN": round(lifting_device_demand, 3),
            "suspensionBeamLiftEndLoad_kN": round(suspension_beam_lift_load, 3),
            "suspensionBeamUseEndLoad_kN": round(suspension_beam_use_load, 3),
            "suspensionBeamBendingMoment_kNm": round(suspension_beam_moment, 3),
            "suspensionBeamMomentCapacity_kNm": round(
                suspension_beam_moment_capacity,
                3,
            ),
            "guideRailUtilization": round(p["guideRailUtilization"], 3),
            "facadeBraceConstructionOk": brace_construction_ok,
            "heightLimit_m": round(height_limit, 3),
            "overhangLimit_m": round(overhang_limit, 3),
            "cantileverLimit_m": round(cantilever_limit, 3),
            "syncGeometryRatio": round(sync_geometry_ratio, 4),
        },
        "assumptions": [
            "默认几何参数取自品茗 pmsc.ini 的 [AttachedLifting information] 示例："
            "H=65m、层高 3.6m、h=1.8m、la=1.5m、lb=0.8m、n=8、k=4；"
            "这些值仅用于回放示例输入，不是规范推荐值或合格结论。",
            "n 解释为架体步数，架体高度按 n·h 计算；k 解释为提升机位/附墙支承点数。"
            "该解释来自参数组合关系，仍需与品茗计算书逐项对照确认。",
            "钢结构按 JGJ 202-2010 第 3 章假定采用合格的 Q235 构配件和 φ48.3×3.6mm 钢管；"
            "截面面积、稳定系数和强度设计值均由输入提供，程序不替代材料进场验收。",
            "一个机位的竖向荷载条带宽度取 la、架体宽度取 lb；"
            "脚手板按 boardLayers 层铺设，施工活荷载按 liveLayers 层同时作用。",
            "竖向主框架风弯矩按一个步距内的风线荷载以 qh²/10 估算，"
            "该弯矩由主框架两侧杆件以 lb 为力臂承担；仅作为简化杆件校核。",
            "水平风荷载由一个矩形步距条带传给 45°～60° 水平剪刀撑，"
            "假定单根斜杆平衡该条带水平力，不考虑多杆空间分配。",
            "附墙支座按 4.1.8 的冲击系数放大使用工况设计荷载；"
            "同一支座各穿墙螺栓平均分担竖向剪力和水平拉力。",
            "防坠装置按使用工况和升降工况设计荷载的较大值乘冲击系数；"
            "制动距离限值按 k≥3 的整体式脚手架取 80mm，否则取 150mm；"
            "钢吊杆式装置仅按“是否适用+直径≥25mm”校核，吊杆承载力仍须专项计算。",
            "升降动力设备 Ns 按升降工况单机位总荷载设计值的 2 倍计算，"
            "并与输入设备额定值 Nc 比较；额定值应取产品铭牌或型式检验资料。",
            "suspensionBeamLoad 是悬臂梁端部实际专项验算荷载，定义为尚未乘 4.3.11 "
            "冲击系数和不均匀系数的设计荷载；升降/防坠包络取 2.0N，"
            "使用工况取 2.0×1.3N，再以 M=N·L 取不利弯矩。",
            "suspensionBeamSectionModulus 和 suspensionBeamSteelStrength 由用户按实际钢梁"
            "截面及材质输入；本模块不根据型钢型号自动查截面，也不按截面塑性发展系数修正。",
            "guideRailUtilization 是导轨外部专项验算结果回填项，不是本模块由截面尺寸推导；"
            "回填值应能对应抗弯、抗压、抗剪、焊缝、稳定、锚栓和变形中的控制项。",
            "外立面剪刀撑参数表示现场构造核查和方案图示确认结果；"
            "45°～60°、主节点扣紧和悬挑端对称斜拉仍需现场验收。",
            "同步控制按荷载报警阈值不高于 15%、停机阈值不高于 30%、"
            "水平高差停机阈值不高于 30mm 进行保守校核。",
            "计算结果标记 verified=false，正式应用前应与项目专项施工方案、"
            "产品型式检验报告和品茗计算书样本对照复核。",
        ],
    }
