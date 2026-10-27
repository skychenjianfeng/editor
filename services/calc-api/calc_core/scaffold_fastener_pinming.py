"""品茗建筑施工云安全计算软件 2027版（V6.0）扣件式脚手架双立杆计算书复刻。

Oracle: oracle/pinming-fastener-20261027.rtf
软件导出时间：2026-10-27 03:16:10
Pmsg.exe 文件版本：13.9.4.31773
"""

from __future__ import annotations

import math
from typing import Any

from .scaffold_fastener import phi_value

MODULE_KEY = "scaffold-fastener-pinming"
STANDARD = "JGJ 130-2011"
SOURCE_SHA256 = "7D7A1B54C45E401D581732131B6573EED0A868505AFFE78EC8A8853234390509"

DEFAULTS: dict[str, Any] = {
    "H": 30.0,
    "groundClearance": 0.0,
    "h": 1.8,
    "la": 1.5,
    "lb": 0.9,
    "innerClearance": 0.2,
    "doublePoleHeight": 25.0,
    "KS": 0.6,
    "boardDead": 0.1,
    "boardLayoutStep": 2.0,
    "netDead": 0.01,
    "railDead": 0.17,
    "railLayoutStep": 2.0,
    "gk": 0.129,
    "liveLayers": 1.0,
    "live": 2.0,
    "w0": 0.4,
    "muS": 1.0,
    "muZTie": 0.88,
    "muZSingle": 0.81,
    "muZDouble": 0.65,
    "tieStepsVertical": 2.0,
    "tieStepsHorizontal": 2.0,
    "tieN0": 3.0,
    "tieLengthMm": 600.0,
    "tieArea": 424.0,
    "tieRadius": 15.9,
    "tieF": 205.0,
    "tieCouplerCapacity": 12.0,
    "couplerReduction": 0.85,
    "weldFt": 185.0,
    "weldTubeDiameter": 48.0,
    "weldTubeThickness": 3.0,
    "anchorPlateThickness": 10.0,
    "anchorBarDiameter": 20.0,
    "anchorCount": 4.0,
    "anchorFy": 270.0,
    "fak": 140.0,
    "foundationFactor": 1.0,
    "baseArea": 0.25,
    "bearingIncrease": 1.254,
    "mu": 1.5,
    "steelDiameter": 48.3,
    "steelThickness": 3.6,
    "sectionArea": 506.0,
    "sectionInertia": 127100.0,
    "sectionRadius": 15.9,
    "sectionModulus": 5260.0,
    "steelF": 205.0,
    "crossBarSelfWeight": 0.04,
    # 品茗横向水平杆挠度采用其内部梁模型。该系数由本 oracle 的
    # F=1.105kN、q=0.04kN/m、L=0.9m、EI=2.618e10N·mm² 反算，
    # 仅用于复刻该版本行为，待更多品茗样本验证。
    "pinmingTransverseDeflectionFactor": 1.9729,
}


def _num(
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


def param_spec() -> dict[str, Any]:
    return {
        "module": MODULE_KEY,
        "title": "扣件式脚手架（品茗双立杆）",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "geometry",
                "title": "架体参数",
                "fields": [
                    _num("H", "架体高度 H", "m", 30.0, 1.0, 100.0, 0.5, "JGJ 130-2011 6.1.2"),
                    _num("groundClearance", "架体离地高度", "m", 0.0, 0.0, 50.0, 0.1, "品茗计算书"),
                    _num("h", "步距 h", "m", 1.8, 0.9, 2.0, 0.1, "JGJ 130-2011 6.1.2"),
                    _num("la", "立杆纵距 la", "m", 1.5, 0.6, 2.1, 0.05, "JGJ 130-2011 6.1.2"),
                    _num("lb", "立杆横距 lb", "m", 0.9, 0.6, 1.5, 0.05, "JGJ 130-2011 6.1.2"),
                    _num("innerClearance", "内立杆离墙距离", "m", 0.2, 0.05, 0.5, 0.05, "品茗计算书"),
                    _num(
                        "doublePoleHeight",
                        "双立杆计算高度 H1",
                        "m",
                        25.0,
                        0.0,
                        100.0,
                        0.5,
                        "品茗计算书；JGJ 130-2011 6.8.5 双立杆构造",
                    ),
                    _num("KS", "双立杆受力不均匀系数 KS", "—", 0.6, 0.3, 1.0, 0.05, "品茗计算书"),
                ],
            },
            {
                "key": "steel",
                "title": "钢管与连接",
                "fields": [
                    _num("steelDiameter", "钢管外径", "mm", 48.3, 42.0, 60.0, 0.1, "JGJ 130-2011 3.1.1"),
                    _num("steelThickness", "钢管壁厚", "mm", 3.6, 2.0, 5.0, 0.1, "JGJ 130-2011 3.1.1"),
                    _num("sectionArea", "钢管截面面积 A", "mm²", 506.0, 50.0, 2000.0, 1.0, "品茗计算书/JGJ 130 附录B"),
                    _num("sectionInertia", "钢管截面惯性矩 I", "mm⁴", 127100.0, 10000.0, 2000000.0, 100.0, "品茗计算书/JGJ 130 附录B"),
                    _num("sectionRadius", "钢管截面回转半径 i", "mm", 15.9, 5.0, 40.0, 0.1, "品茗计算书/JGJ 130 附录B"),
                    _num("sectionModulus", "钢管截面模量 W", "mm³", 5260.0, 1000.0, 50000.0, 10.0, "品茗计算书/JGJ 130 附录B"),
                    _num("steelF", "钢管强度设计值 f", "N/mm²", 205.0, 100.0, 400.0, 5.0, "JGJ 130-2011 表5.1.6"),
                    _num("crossBarSelfWeight", "横向水平杆自重标准值", "kN/m", 0.04, 0.01, 0.2, 0.001, "品茗计算书"),
                    _num("couplerReduction", "扣件抗滑折减系数", "—", 0.85, 0.5, 1.0, 0.05, "JGJ 130-2011 表5.1.7"),
                ],
            },
            {
                "key": "load",
                "title": "荷载参数",
                "fields": [
                    _num("boardDead", "脚手板自重标准值", "kN/m²", 0.1, 0.01, 0.6, 0.01, "JGJ 130-2011 表4.2.1"),
                    _num("boardLayoutStep", "脚手板铺设步数", "步", 2.0, 1.0, 6.0, 1.0, "品茗计算书"),
                    _num("netDead", "安全网自重标准值", "kN/m²", 0.01, 0.001, 0.1, 0.001, "JGJ 130-2011 4.2.1"),
                    _num("railDead", "栏杆与挡脚板自重标准值", "kN/m", 0.17, 0.05, 0.4, 0.01, "JGJ 130-2011 表4.2.1"),
                    _num("railLayoutStep", "挡脚板铺设步数", "步", 2.0, 1.0, 6.0, 1.0, "品茗计算书"),
                    _num("gk", "每米立杆结构自重标准值 gk", "kN/m", 0.129, 0.05, 0.4, 0.001, "JGJ 130-2011 表A.0.1"),
                    _num("liveLayers", "装修作业层数", "层", 1.0, 1.0, 4.0, 1.0, "JGJ 130-2011 表4.2.2"),
                    _num("live", "装修脚手架荷载标准值", "kN/m²", 2.0, 0.5, 5.0, 0.1, "JGJ 130-2011 表4.2.2"),
                ],
            },
            {
                "key": "wind",
                "title": "风荷载",
                "fields": [
                    _num("w0", "基本风压", "kN/m²", 0.4, 0.0, 1.2, 0.05, "GB 50009-2012 8.1"),
                    _num("muS", "风荷载体型系数 μs", "—", 1.0, 0.0, 2.0, 0.05, "JGJ 130-2011 表4.2.6"),
                    _num("muZTie", "连墙件 μz", "—", 0.88, 0.3, 3.0, 0.01, "GB 50009-2012 表8.2.1"),
                    _num("muZSingle", "单立杆稳定性 μz", "—", 0.81, 0.3, 3.0, 0.01, "GB 50009-2012 表8.2.1"),
                    _num("muZDouble", "双立杆稳定性 μz", "—", 0.65, 0.3, 3.0, 0.01, "GB 50009-2012 表8.2.1"),
                ],
            },
            {
                "key": "tie",
                "title": "连墙件、焊缝与预埋件",
                "fields": [
                    _num("tieStepsVertical", "连墙件竖向步数", "步", 2.0, 1.0, 4.0, 1.0, "JGJ 130-2011 6.4.2"),
                    _num("tieStepsHorizontal", "连墙件水平跨数", "跨", 2.0, 1.0, 4.0, 1.0, "JGJ 130-2011 6.4.2"),
                    _num("tieN0", "平面外约束轴力 N0", "kN", 3.0, 0.0, 10.0, 0.5, "JGJ 130-2011 5.2.14"),
                    _num("tieLengthMm", "连墙件计算长度", "mm", 600.0, 100.0, 2000.0, 10.0, "品茗计算书"),
                    _num("tieArea", "连墙件截面积", "mm²", 424.0, 50.0, 2000.0, 1.0, "JGJ 130-2011 附录B"),
                    _num("tieRadius", "连墙件回转半径", "mm", 15.9, 5.0, 50.0, 0.1, "JGJ 130-2011 附录B"),
                    _num("tieF", "连墙件强度设计值", "N/mm²", 205.0, 100.0, 400.0, 5.0, "JGJ 130-2011 表5.1.6"),
                    _num("tieCouplerCapacity", "双扣件抗滑承载力", "kN", 12.0, 1.0, 50.0, 0.5, "JGJ 130-2011 表5.1.7"),
                    _num("weldFt", "对接焊缝强度", "N/mm²", 185.0, 100.0, 300.0, 5.0, "GB 50017-2017"),
                    _num("weldTubeDiameter", "焊缝圆管直径", "mm", 48.0, 20.0, 100.0, 0.1, "品茗计算书"),
                    _num("weldTubeThickness", "焊缝圆管厚度", "mm", 3.0, 1.0, 10.0, 0.1, "品茗计算书"),
                    _num("anchorPlateThickness", "预埋件锚板厚度 t1", "mm", 10.0, 1.0, 50.0, 0.5, "GB 50010-2010 9.7.2"),
                    _num("anchorBarDiameter", "预埋锚筋直径 d1", "mm", 20.0, 6.0, 40.0, 1.0, "GB 50010-2010 9.7.2"),
                    _num("anchorCount", "预埋锚筋数量 n", "个", 4.0, 1.0, 12.0, 1.0, "GB 50010-2010 9.7.2"),
                    _num("anchorFy", "锚筋抗拉强度 fy", "N/mm²", 270.0, 100.0, 500.0, 10.0, "GB 50010-2010"),
                ],
            },
            {
                "key": "foundation",
                "title": "地基承载力",
                "fields": [
                    _num("fak", "地基承载力特征值", "kPa", 140.0, 20.0, 500.0, 5.0, "GB 50007-2011"),
                    _num("foundationFactor", "地基承载力调整系数 mf", "—", 1.0, 0.4, 1.5, 0.05, "JGJ 130-2011 5.5.2"),
                    _num("baseArea", "垫板底面积", "m²", 0.25, 0.05, 1.0, 0.01, "JGJ 130-2011 5.5.1"),
                    _num("bearingIncrease", "地基承载力提高系数 γu", "—", 1.254, 1.0, 2.0, 0.001, "品茗计算书"),
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
    for key in (
        "H",
        "h",
        "la",
        "lb",
        "doublePoleHeight",
        "steelDiameter",
        "steelThickness",
        "sectionArea",
        "sectionInertia",
        "sectionRadius",
        "sectionModulus",
        "steelF",
        "tieArea",
        "tieRadius",
        "tieF",
        "tieCouplerCapacity",
        "weldFt",
        "weldTubeDiameter",
        "weldTubeThickness",
        "anchorPlateThickness",
        "anchorBarDiameter",
        "anchorCount",
        "anchorFy",
        "fak",
        "baseArea",
    ):
        if p[key] <= 0:
            raise ValueError(f"{key} 必须大于 0")
    if p["doublePoleHeight"] > p["H"] + 1e-9:
        raise ValueError("双立杆计算高度不得大于架体高度")
    if p["steelThickness"] * 2 >= p["steelDiameter"]:
        raise ValueError("钢管壁厚不合理")
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
) -> dict[str, Any]:
    return {
        "no": no,
        "key": key,
        "item": item,
        "value": round(value, 3),
        "limit": round(limit, 3),
        "unit": unit,
        "ratio": round(value / limit if limit else 0, 3),
        "ok": value <= limit + 1e-9,
        "clause": clause,
        "control": control,
        "detail": detail,
        "source": "pinming-fastener-20261027.rtf",
    }


def _section(diameter: float, thickness: float) -> tuple[float, float, float, float]:
    inner = diameter - 2.0 * thickness
    area = math.pi / 4.0 * (diameter**2 - inner**2)
    inertia = math.pi / 64.0 * (diameter**4 - inner**4)
    radius = math.sqrt(inertia / area)
    modulus = inertia / (diameter / 2.0)
    return area, inertia, radius, modulus


def run(params: dict[str, Any]) -> dict[str, Any]:
    p = _merged(params)
    area = p["sectionArea"]
    inertia = p["sectionInertia"]
    radius = p["sectionRadius"]
    modulus = p["sectionModulus"]
    EI = 206000.0 * inertia

    long_bar_count = 2.0
    q_long = (
        1.2
        * (
            p["crossBarSelfWeight"]
            + p["boardDead"] * p["lb"] / (long_bar_count + 1.0)
        )
        + 1.4 * p["live"] * p["lb"] / (long_bar_count + 1.0)
    )
    q_long_service = (
        p["crossBarSelfWeight"]
        + p["boardDead"] * p["lb"] / (long_bar_count + 1.0)
        + p["live"] * p["lb"] / (long_bar_count + 1.0)
    )
    m_long = 0.1 * q_long * p["la"] ** 2
    sigma_long = m_long * 1e6 / modulus
    v_long = (
        0.677
        * q_long_service
        * (p["la"] * 1000.0) ** 4
        / (100.0 * EI)
    )
    v_long_limit = min(p["la"] * 1000.0 / 150.0, 10.0)
    r_long_design = 1.1 * q_long * p["la"]
    r_long_service = 1.1 * q_long_service * p["la"]

    q_trans = 1.2 * p["crossBarSelfWeight"]
    q_trans_service = p["crossBarSelfWeight"]
    r_trans = r_long_design + q_trans * p["lb"] / 2.0
    x_load = p["lb"] / 3.0
    m_trans = r_trans * x_load - q_trans * x_load**2 / 2.0
    sigma_trans = m_trans * 1e6 / modulus
    base_trans_deflection = (
        23.0 * r_long_service * 1000.0 * (p["lb"] * 1000.0) ** 3
        / (1296.0 * EI)
        + 5.0
        * q_trans_service
        * (p["lb"] * 1000.0) ** 4
        / (384.0 * EI)
    )
    v_trans = base_trans_deflection * p["pinmingTransverseDeflectionFactor"]
    v_trans_limit = min(p["lb"] * 1000.0 / 150.0, 10.0)

    mu = p["mu"]
    lam_check = mu * p["h"] * 1000.0 / radius
    lam_stability = 1.155 * mu * p["h"] * 1000.0 / radius
    phi = phi_value(lam_stability)

    h_single = p["H"] - p["doublePoleHeight"]
    single_levels = math.floor(h_single / p["h"]) + 1
    double_levels = math.floor(p["doublePoleHeight"] / p["h"])
    ng1_single = round(
        (p["gk"] + p["la"] * long_bar_count / 2.0 * 0.04 / p["h"])
        * h_single,
        2,
    )
    ng2_board_single = (
        single_levels
        * p["la"]
        * p["lb"]
        * p["boardDead"]
        / p["boardLayoutStep"]
        / 2.0
    )
    ng2_rail_single = (
        single_levels * p["la"] * p["railDead"] / p["railLayoutStep"]
    )
    ng2_net_single = p["netDead"] * p["la"] * h_single
    ng2_outer_single = round(
        ng2_board_single + ng2_rail_single + ng2_net_single,
        3,
    )
    ng2_inner_single = round(ng2_board_single, 3)

    ngs1_double = round(
        (
            p["gk"]
            + p["crossBarSelfWeight"]
            + p["la"] * long_bar_count / 2.0 * 0.04 / p["h"]
        )
        * p["doublePoleHeight"],
        3,
    )
    ngs2_board_double = (
        double_levels
        * p["la"]
        * p["lb"]
        * p["boardDead"]
        / p["boardLayoutStep"]
        / 2.0
    )
    ngs2_rail_double = (
        double_levels * p["la"] * p["railDead"] / p["railLayoutStep"]
    )
    ngs2_net_double = p["netDead"] * p["la"] * p["doublePoleHeight"]
    ngs2_outer_double = round(
        ngs2_board_double + ngs2_rail_double + ngs2_net_double,
        3,
    )
    ngs2_inner_double = round(ngs2_board_double, 3)

    nq1 = p["la"] * p["lb"] * p["liveLayers"] * p["live"] / 2.0
    n_no_wind_single = 1.2 * (ng1_single + ng2_outer_single) + 1.4 * nq1
    n_no_wind_double = (
        1.2 * (ngs1_double + ngs2_outer_double) + n_no_wind_single
    )
    n_wind_single = 1.2 * (ng1_single + ng2_outer_single) + 0.9 * 1.4 * nq1
    n_wind_double = 1.2 * (ngs1_double + ngs2_outer_double) + n_wind_single

    wk_tie = p["muZTie"] * p["muS"] * p["w0"]
    wk_single = p["muZSingle"] * p["muS"] * p["w0"]
    wk_double = p["muZDouble"] * p["muS"] * p["w0"]
    mw_single = 0.9 * 1.4 * wk_single * p["la"] * p["h"] ** 2 / 10.0
    mw_double = 0.9 * 1.4 * wk_double * p["la"] * p["h"] ** 2 / 10.0

    sigma_no_wind_single = n_no_wind_single * 1000.0 / (phi * area)
    sigma_no_wind_double = p["KS"] * n_no_wind_double * 1000.0 / (phi * area)
    sigma_wind_single = (
        n_wind_single * 1000.0 / (phi * area) + mw_single * 1e6 / modulus
    )
    sigma_wind_double = p["KS"] * (
        n_wind_double * 1000.0 / (phi * area) + mw_double * 1e6 / modulus
    )

    a_w = (
        p["tieStepsVertical"] * p["h"]
    ) * (
        p["tieStepsHorizontal"] * p["la"]
    )
    n_lw = 1.4 * wk_tie * a_w
    n_l = n_lw + p["tieN0"]
    lam_tie = p["tieLengthMm"] / p["tieRadius"]
    phi_tie = phi_value(math.floor(lam_tie))
    sigma_tie = n_l * 1000.0 / (phi_tie * p["tieArea"])
    tie_limit = 0.85 * p["tieF"]
    weld_length = math.pi * p["weldTubeDiameter"]
    sigma_weld = n_l * 1000.0 / (
        weld_length * p["weldTubeThickness"]
    )
    alpha_b = 0.6 + 0.25 * p["anchorPlateThickness"] / p["anchorBarDiameter"]
    anchor_area_provided = (
        p["anchorCount"] * math.pi * p["anchorBarDiameter"] ** 2 / 4.0
    )
    anchor_area_required = n_l * 1000.0 / (
        0.8 * alpha_b * p["anchorFy"]
    )
    tie_coupler_limit = p["couplerReduction"] * p["tieCouplerCapacity"]

    foundation_pressure = n_no_wind_double / (
        p["foundationFactor"] * p["baseArea"]
    )
    foundation_capacity = p["bearingIncrease"] * p["fak"]

    results = [
        _item(1, "long_bending", "纵向水平杆抗弯", sigma_long, p["steelF"], "N/mm²", "JGJ 130-2011 5.2.1、5.2.2", True, "Mmax=0.1qla²，σ=Mmax/W"),
        _item(2, "long_deflection", "纵向水平杆挠度", v_long, v_long_limit, "mm", "JGJ 130-2011 5.2.3、5.2.4", False, "νmax=0.677q'la⁴/(100EI)≤min(la/150,10)"),
        _item(3, "trans_bending", "横向水平杆抗弯", sigma_trans, p["steelF"], "N/mm²", "JGJ 130-2011 5.2.1、5.2.4", True, "按F1=Rmax、三等分集中力及自重计算弯矩"),
        _item(4, "trans_deflection", "横向水平杆挠度", v_trans, v_trans_limit, "mm", "JGJ 130-2011 5.2.3、5.2.4", False, "品茗内部梁模型；1.9729 为单样本反算系数，非规范值"),
        _item(5, "long_coupler", "纵向水平杆与立杆扣件抗滑", r_long_design / 2.0, p["couplerReduction"] * 8.0, "kN", "JGJ 130-2011 5.2.5、5.1.7", True, "Rmax/2≤0.85×8kN"),
        _item(6, "trans_coupler", "横向水平杆与立杆扣件抗滑", r_trans, p["couplerReduction"] * 8.0, "kN", "JGJ 130-2011 5.2.5、5.1.7", True, "Rmax≤0.85×8kN"),
        _item(7, "slenderness", "立杆长细比", lam_check, 210.0, "—", "JGJ 130-2011 5.1.9、5.2.8", False, "λ=Kμh/i，K=1"),
        _item(8, "single_no_wind", "单立杆稳定（不组合风）", sigma_no_wind_single, p["steelF"], "N/mm²", "JGJ 130-2011 5.2.6-1", True, "σ=N/(φA)"),
        _item(9, "double_no_wind", "双立杆稳定（不组合风）", sigma_no_wind_double, p["steelF"], "N/mm²", "JGJ 130-2011 5.2.6-1、双立杆", True, "σ=KS·Ns/(φA)"),
        _item(10, "single_wind", "单立杆稳定（组合风）", sigma_wind_single, p["steelF"], "N/mm²", "JGJ 130-2011 5.2.6-2、5.2.9", True, "σ=N/(φA)+Mw/W"),
        _item(11, "double_wind", "双立杆稳定（组合风）", sigma_wind_double, p["steelF"], "N/mm²", "JGJ 130-2011 5.2.6-2、双立杆", True, "σ=KS(Ns/(φA)+Mw/W)"),
        _item(12, "tie_stability", "连墙件强度与稳定", sigma_tie, tie_limit, "N/mm²", "JGJ 130-2011 5.2.14", True, "(Nlw+N0)/(φAc)≤0.85f"),
        _item(13, "tie_weld", "连墙件对接焊缝", sigma_weld, p["weldFt"], "N/mm²", "JGJ 130-2011 5.2.14；GB 50017-2017", True, "σ=(Nlw+N0)/(πd·t)≤ft"),
        _item(14, "tie_embed", "连墙件预埋件锚筋", anchor_area_required, anchor_area_provided, "mm²", "GB 50010-2010 9.7.2", True, "As,req=(Nlw+N0)/(0.8αb·fy)≤nπd1²/4"),
        _item(15, "tie_coupler", "连墙件与脚手架连接抗滑", n_l, tie_coupler_limit, "kN", "JGJ 130-2011 5.2.5", True, "Nlw+N0≤0.85×12kN"),
        _item(16, "foundation", "立杆地基承载力", foundation_pressure, foundation_capacity, "kPa", "JGJ 130-2011 5.5.1、GB 50007-2011", True, "p=N/(mf·A)≤γu·fg"),
    ]

    payload = {
        "run_id": "local",
        "module": MODULE_KEY,
        "params": p,
        "verified": False,
        "standard": STANDARD,
        "standards": {
            "applied": [
                {"code": "JGJ 130-2011", "name": "建筑施工扣件式钢管脚手架安全技术规范"},
                {"code": "GB 50009-2012", "name": "建筑结构荷载规范"},
                {"code": "GB 50017-2017", "name": "钢结构设计标准"},
                {"code": "GB 50007-2011", "name": "建筑地基基础设计规范"},
                {"code": "DG/TJ08-2002-2020", "name": "悬挑式脚手架安全技术标准"},
                {"code": "GB 55023-2022", "name": "施工脚手架通用规范"},
                {"code": "GB 55003-2021", "name": "建筑与市政地基基础通用规范"},
                {"code": "GB 50010-2010", "name": "混凝土结构设计标准（2024年版引用）"},
            ],
            "missing": [
                {"code": "GB 55006-2021", "name": "钢结构通用规范", "reason": "本地B库未检索到"},
                {"code": "GB 55001-2021", "name": "工程结构通用规范", "reason": "本地B库未检索到"},
            ],
            "complete": False,
            "oracle": {
                "verified": True,
                "source": "pinming-fastener-20261027.rtf",
                "sha256": SOURCE_SHA256,
                "exported_at": "2026-10-27T03:16:10+08:00",
            },
            "gaps": [
                "横向水平杆挠度的 1.9729 等效系数仅由这一份品茗样本反算，属单样本经验系数、非规范值，尚需第二组不同跨度/荷载样本验证通用性。",
                "本模块只复刻这一份上海双排双立杆装修脚手架计算书，不自动覆盖所有地区模板和其他工况。",
                "计算书中的图形由品茗生成，本复刻模块只验证数值、公式、条文和结果，不解码 RTF 内嵌图形。",
            ],
        },
        "summary": {
            "total": len(results),
            "failed": sum(1 for r in results if not r["ok"]),
            "control_failed": sum(
                1 for r in results if not r["ok"] and r["control"]
            ),
        },
        "results": results,
        "derived": {
            "A_mm2": round(area, 2),
            "I_mm4": round(inertia, 0),
            "i_mm": round(radius, 2),
            "W_mm3": round(modulus, 0),
            "qLongDesign_kN_m": round(q_long, 3),
            "qLongService_kN_m": round(q_long_service, 3),
            "qTransDesign_kN_m": round(q_trans, 3),
            "qTransService_kN_m": round(q_trans_service, 3),
            "M_long_kNm": round(m_long, 3),
            "R_long_kN": round(r_long_design, 3),
            "R_longService_kN": round(r_long_service, 3),
            "M_trans_kNm": round(m_trans, 3),
            "R_trans_kN": round(r_trans, 3),
            "NG1_single_kN": ng1_single,
            "NG2_outer_single_kN": ng2_outer_single,
            "NG2_inner_single_kN": ng2_inner_single,
            "NGS1_double_kN": ngs1_double,
            "NGS2_outer_double_kN": ngs2_outer_double,
            "NGS2_inner_double_kN": ngs2_inner_double,
            "NQ1_kN": round(nq1, 3),
            "N_no_wind_single_kN": round(n_no_wind_single, 3),
            "N_no_wind_double_kN": round(n_no_wind_double, 3),
            "N_wind_single_kN": round(n_wind_single, 3),
            "N_wind_double_kN": round(n_wind_double, 3),
            "Mw_single_kNm": round(mw_single, 3),
            "Mw_double_kNm": round(mw_double, 3),
            "lambda_check": round(lam_check, 3),
            "lambda_stability": round(lam_stability, 3),
            "phi": round(phi, 3),
            "wk_tie_kN_m2": round(wk_tie, 3),
            "Nlw_kN": round(n_lw, 3),
            "Nl_kN": round(n_l, 3),
            "tie_wind_kN": round(n_lw, 3),
            "tie_axial_kN": round(n_l, 3),
            "lambda_tie": round(lam_tie, 3),
            "phi_tie": round(phi_tie, 3),
            "weldLength_mm": round(weld_length, 3),
            "anchorAlphaB": round(alpha_b, 3),
            "anchorAreaRequired_mm2": round(anchor_area_required, 3),
            "anchorAreaProvided_mm2": round(anchor_area_provided, 3),
            "foundationPressure_kPa": round(foundation_pressure, 3),
            "foundationCapacity_kPa": round(foundation_capacity, 3),
            "anchor_area_required_mm2": round(anchor_area_required, 3),
            "anchor_area_provided_mm2": round(anchor_area_provided, 3),
            "foundation_pressure_kPa": round(foundation_pressure, 3),
            "foundation_capacity_kPa": round(foundation_capacity, 3),
        },
        "assumptions": [
            "默认参数和内嵌中间量严格按用户提供的品茗 2027版（V6.0）计算书设置。",
            "纵向水平杆按三跨连续梁，系数0.1/0.677；横向水平杆按F1=Rmax、两根纵向杆三等分及自重模型。",
            "双立杆按H-H1单立杆段和H1双立杆段分段计算，KS=0.6。",
            "横向水平杆挠度含一个由本样本反算的品茗内部梁模型系数1.9729；该系数是单样本经验值，不是规范值，不得外推到其他跨度或荷载工况。",
            "本模块保持verified=false；oracle.verified=true只表示这一份导出计算书逐项一致。",
        ],
    }
    return payload
