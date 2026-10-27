"""门式钢管脚手架验算：立杆稳定、横梁抗弯与挠度、连墙件、地基承载力。

依据：JGJ 128-2010《建筑施工门式钢管脚手架安全技术规范》。
"""

from __future__ import annotations

from typing import Any

MODULE_KEY = "door-scaffold"
STANDARD = "JGJ 128-2010"

DEFAULTS: dict[str, Any] = {
    "H": 20.0,
    "g1": 0.13,
    "g2": 0.07,
    "sumNQk": 6.58,
    "phi": 0.316,
    "A1": 310.0,
    "f": 205.0,
    "frameWidth": 1.219,
    "frameBay": 1.8,
    "stepHeight": 1.93,
    "muZ": 1.0,
    "muS": 0.8,
    "w0": 0.35,
    "beamQd": 2.5,
    "beamQk": 1.8,
    "beamW": 2830.0,
    "beamI": 60800.0,
    "beamE": 206000.0,
    "beamDeflectionRatio": 250.0,
    "tieL1": 4.5,
    "tieH1": 3.86,
    "tieNv": 30.0,
    "tieAc": 310.0,
    "tieA": 310.0,
    "tiePhi": 0.90,
    "fak": 150.0,
    "kc": 0.8,
    "Ad": 0.12,
    "crossBracingBothSides": True,
    "crossBracingLocked": True,
    "connectingRodsInstalled": True,
    "connectingRodClearance": 1.5,
    "lockingArmOrPositivePin": True,
    "baseInstalled": True,
    "hangingBoardsContinuous": True,
    "boardsFallPrevention": True,
    "boardHoleDiameter": 0.0,
    "braceAtCornersAndEnds": True,
    "braceMaxInterval": 15.0,
    "braceContinuousFullHeight": True,
    "braceFullOuterFace": True,
    "braceAngle": 50.0,
    "braceLapLength": 1200.0,
    "braceLapFasteners": 3.0,
    "braceWidthSpans": 5.0,
    "braceWidth": 8.0,
    "horizontalTopAndTieLevels": True,
    "horizontalSpacingSteps": 2.0,
    "horizontalContinuous": True,
    "horizontalCornerOpeningEachStep": True,
    "horizontalAttachedToPosts": True,
    "tieNearTransomOffset": 100.0,
    "tieFixedToPost": True,
    "tieAtCornerAndOpenEnds": True,
    "tieCornerOpeningVerticalSpacing": 3.5,
    "tieScaffoldEndLower": True,
    "tieSlope": 0.2,
}


def param_spec() -> dict[str, Any]:
    def boolean(key, label, default, clause):
        return {
            "key": key,
            "label": label,
            "type": "boolean",
            "unit": "—",
            "default": default,
            "clause": clause,
        }

    def num(key, label, unit, default, lo, hi, step, clause):
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
        "title": "门式钢管脚手架",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "load",
                "title": "荷载与架体参数",
                "fields": [
                    num("H", "脚手架搭设高度 H", "m", 20.0, 1.0, 55.0, 0.5, "JGJ 128-2010 5.1.3"),
                    num("g1", "每米高构配件自重产生的轴向力标准值 N_G1k", "kN/m", 0.13, 0.01, 2.0, 0.01, "JGJ 128-2010 4.2.1、5.2.1"),
                    num("g2", "每米高附件自重产生的轴向力标准值 N_G2k", "kN/m", 0.07, 0.0, 2.0, 0.01, "JGJ 128-2010 4.2.1、5.2.1"),
                    num("sumNQk", "一榀门架各层施工荷载标准值总和 ΣN_Qk", "kN", 6.58, 0.0, 100.0, 0.1, "JGJ 128-2010 4.2.2、5.2.1"),
                    num("muZ", "风压高度变化系数 μ_z", "—", 1.0, 0.5, 3.0, 0.01, "JGJ 128-2010 4.2.6"),
                    num("muS", "风荷载体型系数 μ_s", "—", 0.8, 0.1, 2.0, 0.01, "JGJ 128-2010 4.2.6"),
                    num("w0", "基本风压 w0", "kN/m²", 0.35, 0.0, 1.5, 0.01, "JGJ 128-2010 4.2.6"),
                ],
            },
            {
                "key": "frame",
                "title": "门架立杆参数",
                "fields": [
                    num("phi", "门架立杆稳定系数 φ", "—", 0.316, 0.05, 1.0, 0.001, "JGJ 128-2010 5.2.1、附录B 表B.0.5"),
                    num("A1", "单根立杆毛截面面积 A1", "mm²", 310.0, 50.0, 2000.0, 1.0, "JGJ 128-2010 5.2.1、附录B 表B.0.4"),
                    num("f", "钢管抗压、抗弯强度设计值 f", "N/mm²", 205.0, 100.0, 400.0, 5.0, "JGJ 128-2010 表5.1.8"),
                    num("frameWidth", "门架宽度 b", "m", 1.219, 0.8, 1.3, 0.001, "JGJ 128-2010 3.0.3、表B.0.1-1"),
                    num("frameBay", "门架跨距 l", "m", 1.8, 0.5, 2.0, 0.05, "JGJ 128-2010 2.1.20、6.5.2"),
                    num("stepHeight", "门架步距 h", "m", 1.93, 0.8, 3.0, 0.01, "JGJ 128-2010 2.1.19、6.5.2"),
                ],
            },
            {
                "key": "beam",
                "title": "门架横梁参数",
                "fields": [
                    num("beamQd", "横梁均布设计荷载 q_d", "kN/m", 2.5, 0.1, 30.0, 0.1, "JGJ 128-2010 5.1.2（补充验算）"),
                    num("beamQk", "横梁均布标准荷载 q_k", "kN/m", 1.8, 0.1, 30.0, 0.1, "JGJ 128-2010 5.1.2（补充验算）"),
                    num("beamW", "横梁截面模量 W", "mm³", 2830.0, 100.0, 100000.0, 10.0, "JGJ 128-2010 表B.0.4"),
                    num("beamI", "横梁截面惯性矩 I", "mm⁴", 60800.0, 1000.0, 10000000.0, 100.0, "JGJ 128-2010 表B.0.4"),
                    num("beamE", "横梁弹性模量 E", "N/mm²", 206000.0, 200000.0, 210000.0, 1000.0, "JGJ 128-2010 表5.1.8"),
                    num("beamDeflectionRatio", "横梁挠度限值分母", "—", 250.0, 100.0, 500.0, 10.0, "JGJ 128-2010 5.1.2（限值待复核）"),
                ],
            },
            {
                "key": "tie",
                "title": "连墙件参数",
                "fields": [
                    num("tieL1", "连墙件水平间距 L1", "m", 4.5, 0.5, 10.0, 0.1, "JGJ 128-2010 5.3.2、6.5.2"),
                    num("tieH1", "连墙件竖向间距 H1", "m", 3.86, 0.5, 10.0, 0.01, "JGJ 128-2010 5.3.2、6.5.2"),
                    num("tieNv", "连接抗拉（压）承载力设计值 N_v", "kN", 30.0, 1.0, 200.0, 1.0, "JGJ 128-2010 5.3.3"),
                    num("tieAc", "连墙件净截面面积 A_c", "mm²", 310.0, 10.0, 2000.0, 1.0, "JGJ 128-2010 5.3.1"),
                    num("tieA", "连墙件毛截面面积 A", "mm²", 310.0, 10.0, 2000.0, 1.0, "JGJ 128-2010 5.3.1"),
                    num("tiePhi", "连墙件稳定系数 φ", "—", 0.90, 0.05, 1.0, 0.01, "JGJ 128-2010 5.3.1、附录B 表B.0.6"),
                ],
            },
            {
                "key": "foundation",
                "title": "地基承载力参数",
                "fields": [
                    num("fak", "地基承载力特征值 f_ak", "kPa", 150.0, 20.0, 1000.0, 5.0, "JGJ 128-2010 5.6.3"),
                    num("kc", "地基承载力修正系数 k_c", "—", 0.8, 0.4, 1.0, 0.05, "JGJ 128-2010 表5.6.4"),
                    num("Ad", "一榀门架底座或垫板底面面积 A_d", "m²", 0.12, 0.01, 2.0, 0.01, "JGJ 128-2010 5.6.1"),
                ],
            },
            {
                "key": "assembly",
                "title": "门架与配件装配构造",
                "fields": [
                    boolean("crossBracingBothSides", "门架两侧设置交叉支撑", True, "JGJ 128-2010 6.2.2"),
                    boolean("crossBracingLocked", "交叉支撑与锁销锁牢", True, "JGJ 128-2010 6.2.2"),
                    boolean("connectingRodsInstalled", "上下榀门架设置连接棒", True, "JGJ 128-2010 6.2.3"),
                    num("connectingRodClearance", "连接棒与门架立杆配合间隙", "mm", 1.5, 0.0, 20.0, 0.1, "JGJ 128-2010 6.2.3"),
                    boolean("lockingArmOrPositivePin", "设置锁臂，或采用插销式/弹销式连接棒", True, "JGJ 128-2010 6.2.4"),
                    boolean("baseInstalled", "底部门架立杆设置底座", True, "JGJ 128-2010 6.2.6"),
                    boolean("hangingBoardsContinuous", "作业层挂扣式脚手板连续满铺", True, "JGJ 128-2010 6.2.5"),
                    boolean("boardsFallPrevention", "脚手板有防松动或脱落措施", True, "JGJ 128-2010 6.2.5"),
                    num("boardHoleDiameter", "脚手板孔洞内切圆直径", "mm", 0.0, 0.0, 100.0, 1.0, "JGJ 128-2010 6.2.5"),
                ],
            },
            {
                "key": "brace",
                "title": "剪刀撑构造",
                "fields": [
                    boolean("braceAtCornersAndEnds", "H≤24m 时转角处、两端设置剪刀撑", True, "JGJ 128-2010 6.3.1"),
                    num("braceMaxInterval", "H≤24m 时外侧立面剪刀撑最大间隔", "m", 15.0, 0.0, 50.0, 0.5, "JGJ 128-2010 6.3.1"),
                    boolean("braceContinuousFullHeight", "剪刀撑由底至顶连续设置", True, "JGJ 128-2010 6.3.1"),
                    boolean("braceFullOuterFace", "H>24m 时全外侧立面连续设置剪刀撑", True, "JGJ 128-2010 6.3.1"),
                    num("braceAngle", "剪刀撑斜杆与地面夹角", "°", 50.0, 30.0, 90.0, 1.0, "JGJ 128-2010 6.3.2-1"),
                    num("braceLapLength", "剪刀撑斜杆搭接长度", "mm", 1200.0, 0.0, 3000.0, 50.0, "JGJ 128-2010 6.3.2-3"),
                    num("braceLapFasteners", "搭接处旋转扣件数量", "个", 3.0, 0.0, 10.0, 1.0, "JGJ 128-2010 6.3.2-3"),
                    num("braceWidthSpans", "每道剪刀撑宽度（跨距数）", "跨", 5.0, 1.0, 12.0, 1.0, "JGJ 128-2010 6.3.2-4"),
                    num("braceWidth", "每道剪刀撑实际宽度", "m", 8.0, 1.0, 20.0, 0.5, "JGJ 128-2010 6.3.2-4"),
                ],
            },
            {
                "key": "horizontal",
                "title": "水平加固杆构造",
                "fields": [
                    boolean("horizontalTopAndTieLevels", "顶层和连墙件设置层设置水平加固杆", True, "JGJ 128-2010 6.3.3-1"),
                    num("horizontalSpacingSteps", "水平加固杆实际最大竖向步数间距", "步", 2.0, 0.0, 12.0, 1.0, "JGJ 128-2010 6.3.3-3"),
                    boolean("horizontalContinuous", "水平加固杆在设置层面连续", True, "JGJ 128-2010 6.3.3-6"),
                    boolean("horizontalCornerOpeningEachStep", "转角及开口端两跨内每步设置水平加固杆", True, "JGJ 128-2010 6.3.3-4"),
                    boolean("horizontalAttachedToPosts", "水平加固杆与门架立杆扣紧", True, "JGJ 128-2010 6.3.3"),
                ],
            },
            {
                "key": "tie_detail",
                "title": "连墙件细部构造",
                "fields": [
                    num("tieNearTransomOffset", "连墙件距门架横杆最大距离", "mm", 100.0, 0.0, 1000.0, 10.0, "JGJ 128-2010 6.5.4"),
                    boolean("tieFixedToPost", "连墙件固定在门架立杆上", True, "JGJ 128-2010 6.5.4"),
                    boolean("tieAtCornerAndOpenEnds", "转角处或开口型端部增设连墙件", True, "JGJ 128-2010 6.5.3"),
                    num("tieCornerOpeningVerticalSpacing", "角部/开口端连墙件实际最大竖向间距", "m", 3.5, 0.0, 10.0, 0.1, "JGJ 128-2010 6.5.3"),
                    boolean("tieScaffoldEndLower", "非水平连墙件脚手架连接端低于结构连接端", True, "JGJ 128-2010 6.5.5"),
                    num("tieSlope", "非水平连墙件坡度（高差/水平距离）", "—", 0.2, 0.0, 2.0, 0.01, "JGJ 128-2010 6.5.5"),
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


def _item(no, key, item, value, limit, unit, clause, control, detail, ok=None):
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


def _conformity_item(no, key, item, checks, clause, control, detail):
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

    wk = p["muZ"] * p["muS"] * p["w0"]
    qwk = wk * p["frameBay"]
    Mwk = qwk * p["tieH1"] ** 2 / 10.0
    permanent_load = (p["g1"] + p["g2"]) * p["H"]
    N_no_wind = 1.2 * permanent_load + 1.4 * p["sumNQk"]
    N_wind = 1.2 * permanent_load + 0.9 * 1.4 * (
        p["sumNQk"] + 2.0 * Mwk / p["frameWidth"]
    )
    N_ledger = max(N_no_wind, N_wind)
    N_ledger_capacity = p["phi"] * 2.0 * p["A1"] * p["f"] / 1000.0

    beam_moment = p["beamQd"] * p["frameWidth"] ** 2 / 8.0
    beam_stress = beam_moment * 1e6 / p["beamW"]
    beam_length_mm = p["frameWidth"] * 1000.0
    beam_deflection = (
        5.0
        * p["beamQk"]
        * beam_length_mm**4
        / (384.0 * p["beamE"] * p["beamI"])
    )
    beam_deflection_limit = beam_length_mm / p["beamDeflectionRatio"]

    Nw = 1.4 * wk * p["tieL1"] * p["tieH1"]
    Nl = Nw + 3.0
    tie_strength_capacity = 0.85 * p["f"] * p["tieAc"] / 1000.0
    tie_stability_capacity = 0.85 * p["tiePhi"] * p["f"] * p["tieA"] / 1000.0
    tie_capacity = min(p["tieNv"], tie_strength_capacity, tie_stability_capacity)
    tie_cover_area = p["tieL1"] * p["tieH1"]
    tie_cover_limit = 40.0 if p["H"] <= 40.0 else 27.0
    vertical_factor = 3.0 if p["H"] <= 40.0 else 2.0
    horizontal_max = 3.0 * p["frameBay"]
    vertical_max = vertical_factor * p["stepHeight"]
    tie_spacing_ok = (
        p["tieL1"] <= horizontal_max + 1e-9
        and p["tieH1"] <= vertical_max + 1e-9
        and tie_cover_area <= tie_cover_limit + 1e-9
    )

    Nk_no_wind = permanent_load + p["sumNQk"]
    Nk_wind = permanent_load + 0.9 * (
        p["sumNQk"] + 2.0 * Mwk / p["frameWidth"]
    )
    Nk = max(Nk_no_wind, Nk_wind)
    foundation_pressure = Nk / p["Ad"]
    foundation_capacity = p["kc"] * p["fak"]

    assembly_checks = [
        ("门架两侧交叉支撑", p["crossBracingBothSides"]),
        ("交叉支撑与锁销锁牢", p["crossBracingLocked"]),
        ("上下榀门架连接棒", p["connectingRodsInstalled"]),
        (
            f"连接棒配合间隙 {p['connectingRodClearance']:.2f}mm≤2mm",
            p["connectingRodClearance"] <= 2.0 + 1e-9,
        ),
        ("锁臂或插销式/弹销式连接", p["lockingArmOrPositivePin"]),
        ("底部门架立杆底座", p["baseInstalled"]),
        ("挂扣式脚手板连续满铺", p["hangingBoardsContinuous"]),
        ("脚手板防松动或脱落措施", p["boardsFallPrevention"]),
        (
            f"脚手板孔洞内切圆 {p['boardHoleDiameter']:.2f}mm≤25mm",
            p["boardHoleDiameter"] <= 25.0 + 1e-9,
        ),
    ]

    brace_checks = [
        (
            f"剪刀撑夹角 {p['braceAngle']:.1f}°在45°～60°",
            45.0 - 1e-9 <= p["braceAngle"] <= 60.0 + 1e-9,
        ),
        (
            f"剪刀撑搭接 {p['braceLapLength']:.0f}mm≥1000mm",
            p["braceLapLength"] >= 1000.0 - 1e-9,
        ),
        (
            f"搭接旋转扣件 {p['braceLapFasteners']:.0f}个≥3个",
            p["braceLapFasteners"] >= 3.0 - 1e-9,
        ),
        (
            f"剪刀撑宽度 {p['braceWidthSpans']:.0f}跨在4～6跨",
            4.0 - 1e-9 <= p["braceWidthSpans"] <= 6.0 + 1e-9,
        ),
        (
            f"剪刀撑宽度 {p['braceWidth']:.1f}m在6～10m",
            6.0 - 1e-9 <= p["braceWidth"] <= 10.0 + 1e-9,
        ),
        ("剪刀撑由底至顶连续", p["braceContinuousFullHeight"]),
    ]
    if p["H"] <= 24.0:
        brace_checks.extend(
            [
                ("转角处、两端设置剪刀撑", p["braceAtCornersAndEnds"]),
                (
                    f"外侧立面剪刀撑间隔 {p['braceMaxInterval']:.1f}m≤15m",
                    p["braceMaxInterval"] <= 15.0 + 1e-9,
                ),
            ]
        )
    else:
        brace_checks.append(("全外侧立面连续剪刀撑", p["braceFullOuterFace"]))

    horizontal_spacing_limit = 1.0 if p["H"] > 40.0 else 2.0
    horizontal_checks = [
        ("顶层和连墙件设置层设置水平加固杆", p["horizontalTopAndTieLevels"]),
        (
            f"水平加固杆步数间距 {p['horizontalSpacingSteps']:.0f}步≤{horizontal_spacing_limit:.0f}步",
            p["horizontalSpacingSteps"] <= horizontal_spacing_limit + 1e-9,
        ),
        ("水平加固杆连续设置", p["horizontalContinuous"]),
        ("转角及开口端两跨内每步设置", p["horizontalCornerOpeningEachStep"]),
        ("水平加固杆与门架立杆扣紧", p["horizontalAttachedToPosts"]),
    ]

    tie_detail_checks = [
        (
            f"连墙件距横杆 {p['tieNearTransomOffset']:.0f}mm≤200mm",
            p["tieNearTransomOffset"] <= 200.0 + 1e-9,
        ),
        ("连墙件固定在门架立杆", p["tieFixedToPost"]),
        ("转角处或开口端增设连墙件", p["tieAtCornerAndOpenEnds"]),
        (
            f"角部/开口端竖向间距 {p['tieCornerOpeningVerticalSpacing']:.1f}m≤4.0m",
            p["tieCornerOpeningVerticalSpacing"] <= 4.0 + 1e-9,
        ),
        (
            "非水平连墙件脚手架端低于结构端",
            p["tieSlope"] <= 1e-12 or p["tieScaffoldEndLower"],
        ),
        (
            f"连墙件坡度 {p['tieSlope']:.2f}<1:3",
            p["tieSlope"] < 1.0 / 3.0 - 1e-12,
        ),
    ]

    results = [
        _item(
            1,
            "ledger_stability",
            "门架立杆稳定",
            N_ledger,
            N_ledger_capacity,
            "kN",
            "JGJ 128-2010 5.2.1-1～5.2.1-6",
            True,
            "N=max[1.2(N_G1k+N_G2k)H+1.4ΣN_Qk, "
            "1.2(N_G1k+N_G2k)H+0.9×1.4(ΣN_Qk+2M_wk/b)]"
            "≤N^d=φ·2A1·f；M_wk=w_k·l·H1²/10",
        ),
        _item(
            2,
            "beam_bending",
            "门架横梁抗弯",
            beam_stress,
            p["f"],
            "N/mm²",
            "JGJ 128-2010 5.1.2、5.1.8（横梁专用公式未列）",
            True,
            "简支横梁 M=q_d·b²/8，σ=M/W≤f",
        ),
        _item(
            3,
            "beam_deflection",
            "门架横梁挠度",
            beam_deflection,
            beam_deflection_limit,
            "mm",
            "JGJ 128-2010 5.1.2（挠度公式及限值为补充验算）",
            False,
            "v=5q_k·b⁴/(384EI)≤b/250",
        ),
        _item(
            4,
            "tie_capacity",
            "连墙件承载力及构造",
            Nl,
            tie_capacity,
            "kN",
            "JGJ 128-2010 4.2.6、5.3.1～5.3.3、6.5.2",
            True,
            "N_l=1.4μ_zμ_sw0·L1H1+3000≤min(N_v,0.85fA_c,0.85φfA)；"
            "并校核L1≤3l、H1≤3h及覆盖面积",
            ok=Nl <= tie_capacity + 1e-9 and tie_spacing_ok,
        ),
        _item(
            5,
            "foundation_bearing",
            "地基承载力",
            foundation_pressure,
            foundation_capacity,
            "kPa",
            "JGJ 128-2010 5.6.1～5.6.4",
            True,
            "P=N_k/A_d≤f_a=k_c·f_ak；"
            "N_k取不组合风和组合风轴向力标准值的较大值",
        ),
        _conformity_item(
            6,
            "assembly_construction",
            "门架与配件装配构造",
            assembly_checks,
            "JGJ 128-2010 6.2.2～6.2.6",
            True,
            "逐项核对交叉支撑、连接棒与锁臂、底座及挂扣式脚手板构造；"
            "结果为通过项数/检查项数，不对构造条文件值作公式化计算",
        ),
        _conformity_item(
            7,
            "brace_configuration",
            "剪刀撑布置与搭接构造",
            brace_checks,
            "JGJ 128-2010 6.3.1、6.3.2",
            True,
            "按H≤24m或H>24m分别核对剪刀撑布置，并校核夹角、搭接、"
            "扣件数量及每道宽度；结果为通过项数/检查项数",
        ),
        _conformity_item(
            8,
            "horizontal_reinforcement",
            "水平加固杆构造",
            horizontal_checks,
            "JGJ 128-2010 6.3.3",
            True,
            f"按H≤40m至少每2步、H>40m每步校核，并核对顶层、连墙层、"
            f"连续设置及与立杆扣紧；结果为通过项数/检查项数",
        ),
        _conformity_item(
            9,
            "tie_detail",
            "连墙件细部构造",
            tie_detail_checks,
            "JGJ 128-2010 6.5.3～6.5.5",
            True,
            "独立于连墙件承载力，核对靠横杆距离、固定于立杆、"
            "角部/开口端间距及向下坡度；结果为通过项数/检查项数",
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
                    "name": "建筑施工门式钢管脚手架安全技术规范",
                },
            ],
            "missing": [],
            "complete": False,
            "gaps": [
                "JGJ 128-2010 第5章未单列门架横梁自身抗弯和挠度计算公式；本模块按简支梁通用公式补充验算，横梁截面和荷载需按实际构造复核。",
                "横梁挠度限值取 b/250，该限值不是 JGJ 128-2010 直接规定，使用前应结合门架产品要求或专项方案确认。",
                "门架立杆稳定承载力按 JGJ 128-2010 式(5.2.1-6)计算；本模块默认参数对应 MF1219 φ42 门架、H≤40m，其他型号应重新取 φ、A1 并复核适用范围。",
                "连墙件连接强度 N_v 由用户按实际扣件、螺栓、预埋件或焊接连接另行确定；本模块只作 5.3.3 对比验算。",
                "地基承载力只按 5.6.1～5.6.4 验算平均压力，未开展地基变形、软弱下卧层及立杆下垫板局部承压验算。",
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
            "wk_kPa": round(wk, 3),
            "qwk_kN_m": round(qwk, 3),
            "Mwk_kNm": round(Mwk, 3),
            "N_no_wind_kN": round(N_no_wind, 3),
            "N_wind_kN": round(N_wind, 3),
            "N_ledger_kN": round(N_ledger, 3),
            "N_ledger_capacity_kN": round(N_ledger_capacity, 3),
            "beamMoment_kNm": round(beam_moment, 3),
            "beamStress_N_mm2": round(beam_stress, 3),
            "beamDeflection_mm": round(beam_deflection, 3),
            "beamDeflectionLimit_mm": round(beam_deflection_limit, 3),
            "Nw_kN": round(Nw, 3),
            "Nl_kN": round(Nl, 3),
            "tieCapacity_kN": round(tie_capacity, 3),
            "tieCoverArea_m2": round(tie_cover_area, 3),
            "tieCoverLimit_m2": round(tie_cover_limit, 3),
            "tieHorizontalMax_m": round(horizontal_max, 3),
            "tieVerticalMax_m": round(vertical_max, 3),
            "tieSpacingOk": tie_spacing_ok,
            "Nk_no_wind_kN": round(Nk_no_wind, 3),
            "Nk_wind_kN": round(Nk_wind, 3),
            "Nk_kN": round(Nk, 3),
            "foundationPressure_kPa": round(foundation_pressure, 3),
            "foundationCapacity_kPa": round(foundation_capacity, 3),
            "braceHeightBranch": "H≤24m" if p["H"] <= 24.0 else "H>24m",
            "horizontalSpacingStepLimit": horizontal_spacing_limit,
            "tieSlopeLimit": round(1.0 / 3.0, 4),
        },
        "assumptions": [
            "默认工况为落地式、密目式安全网全封闭 MF1219 φ42 门架，搭设高度 20m，Q235 钢管。",
            "一榀门架的稳定承载力按两根立杆毛截面面积 A=2A1 计算，默认 φ=0.316 对应 JGJ 128-2010 表 B.0.5-1 的 H≤40m 工况。",
            "门架横梁按跨度等于门架宽度 b 的简支梁计算，设计荷载与标准荷载分别取 beamQd、beamQk；二者均由用户按实际搁置和传力路径确定。",
            "连墙件按轴心拉压构件验算，N_l 包含 3.0kN 附加作用；构造要求按落地式全封闭、H≤40m 的 JGJ 128-2010 表 6.5.2 校核。",
            "地基承载力中 A_d 取一榀门架下底座或垫板的等效总面积；N_k 按 JGJ 128-2010 式(5.6.2-1)、式(5.6.2-2)取较大值。",
        ],
    }
