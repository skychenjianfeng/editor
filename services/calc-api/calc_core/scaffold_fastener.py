"""扣件式钢管脚手架校核（骨架版）。

依据：JGJ 130-2011《建筑施工扣件式钢管脚手架安全技术规范》。
本版本用于打通"参数 → 校核 → 结果"链路，系数与构造细节仍需：
  1) 与 B 库原文逐条核对；
  2) 与品茗计算书 oracle 对照。
因此 payload 中固定返回 verified=false 与 assumptions 列表。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

MODULE_KEY = "scaffold-fastener"

STANDARDS_APPLIED = [
    {"code": "JGJ 130-2011", "name": "建筑施工扣件式钢管脚手架安全技术规范"},
    {"code": "JGJ 80-2016", "name": "建筑施工高处作业安全技术规范"},
    {"code": "GB 55023-2022", "name": "施工脚手架通用规范"},
    {"code": "GB 51210-2016", "name": "建筑施工脚手架安全技术统一标准"},
    {"code": "CECS 699-2020", "name": "建筑施工扣件式钢管脚手架安全技术标准"},
    {"code": "GB 50009-2012", "name": "建筑结构荷载规范"},
]

STANDARDS_MISSING: list[dict[str, str]] = []

STANDARDS_GAPS = [
    "抗倾覆：GB 51210-2016 6.1.4-1 未将落地作业脚手架列入（仅支撑脚手架要求）；CECS 699-2020 5.1.1 为“必要时”",
    "缆风绳：仅在采用缆风绳时计算（GB 51210-2016 6.1.4-1 第 5 款）",
]

F_DESIGN = 205.0  # N/mm²，Q235 钢管抗压强度设计值
E_STEEL = 206000.0  # N/mm²，表 5.1.6

STEEL_SECTIONS: dict[str, dict[str, float]] = {
    "φ48×2.8": {"D": 48.0, "t": 2.8},
    "φ48×3.0": {"D": 48.0, "t": 3.0},
    "φ51×3.0": {"D": 51.0, "t": 3.0},
}

TIE_SPANS: dict[str, tuple[int, int]] = {
    "一步三跨": (1, 3),
    "两步三跨": (2, 3),
    "两步两跨": (2, 2),
    "三步三跨": (3, 3),
}

DEFAULTS: dict[str, Any] = {
    "h": 1.8,
    "la": 1.5,
    "lb": 0.9,
    "H": 24.0,
    "steel": "φ48×3.0",
    "tie": "两步三跨",
    "layout": "双排",
    "board": "竹串片脚手板",
    "dead": 0.35,
    "live": 2.0,
    "wind": 0.25,
    "z": 24.0,
    "terrain": "B",
    "enclosure": "全封闭",
    "backdrop": "敞开、框架和开洞墙",
    "phiWind": 0.8,
    "foundation": "混凝土",
    "fg": 140.0,
    "baseArea": 0.25,
    "hBoard": 180.0,
    "braceW": 6.0,
    "tieNv": 12.0,
    "tieOffset": 200.0,
    "tieFromFirstStep": "是",
    "sweepBar": "是",
    "sweepBarHeight": 200.0,
    "railHeight": 1.2,
    "safetyNet": "是",
    "freeHeight": 3.6,
    "braceSpacing": 15.0,
    "braceContinuous": "是",
    "gamma0": 1.0,
    "tieNetArea": 0.0,
    "boardThickness": 50.0,
    "boardF": 15.0,
    "boardE": 10000.0,
}


def param_spec() -> dict[str, Any]:
    return {
        "module": MODULE_KEY,
        "title": "扣件式脚手架",
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
                    _num("h", "步距 h", "m", 1.8, 1.2, 2.0, 0.1, "JGJ 130-2011 6.1.2"),
                    _num("la", "立杆纵距 la", "m", 1.5, 0.9, 1.8, 0.1, "JGJ 130-2011 6.1.2"),
                    _num("lb", "立杆横距 lb", "m", 0.9, 0.6, 1.5, 0.1, "JGJ 130-2011 6.1.2"),
                    _num("H", "搭设高度 H", "m", 24.0, 1.0, 50.0, 0.5, "JGJ 130-2011 6.1.2"),
                    _enum("steel", "钢管类型", list(STEEL_SECTIONS), "φ48×3.0"),
                    _enum("tie", "连墙件布置", list(TIE_SPANS), "两步三跨"),
                    _enum("layout", "单/双排", ["双排", "单排"], "双排"),
                    _enum("board", "脚手板类型", ["竹串片脚手板", "木脚手板", "冲压钢脚手板"], "竹串片脚手板"),
                ],
            },
            {
                "key": "load",
                "title": "荷载参数",
                "fields": [
                    _num("dead", "脚手板自重", "kN/m²", 0.35, 0.05, 0.6, 0.05, "JGJ 130-2011 4.2"),
                    _num("live", "施工均布活荷载", "kN/m²", 2.0, 0.5, 3.0, 0.5, "JGJ 130-2011 4.2.2"),
                    _num("wind", "基本风压 w0", "kN/m²", 0.25, 0.0, 0.9, 0.05, "GB 50009-2012 8.1"),
                    _num("z", "风压计算高度 z", "m", 24.0, 5.0, 100.0, 1.0, "GB 50009-2012 表8.2.1"),
                    _enum("terrain", "地面粗糙度", ["A", "B", "C", "D"], "B"),
                    _enum("enclosure", "脚手架封闭状况", ["全封闭", "半封闭", "敞开"], "全封闭"),
                    _enum("backdrop", "背靠建筑物状况", ["全封闭墙", "敞开、框架和开洞墙"], "敞开、框架和开洞墙"),
                    _num("phiWind", "挡风系数 φ", "—", 0.8, 0.5, 1.0, 0.05, "JGJ 130-2011 4.2.7"),
                ],
            },
            {
                "key": "foundation",
                "title": "地基与构造",
                "fields": [
                    _enum("foundation", "地基类型", ["混凝土", "碎石土", "粉土", "黏土"], "混凝土"),
                    _num("fg", "地基承载力特征值 fg", "kPa", 140.0, 40.0, 300.0, 5.0, "JGJ 130-2011 5.3.5"),
                    _num("baseArea", "垫板底面积", "m²", 0.25, 0.05, 1.0, 0.01, "JGJ 130-2011 5.3.5"),
                    _num("hBoard", "挡脚板高度", "mm", 180.0, 100.0, 300.0, 10.0, "JGJ 130-2011 6.2.4"),
                    _num("braceW", "剪刀撑宽度", "m", 6.0, 3.0, 8.0, 0.5, "JGJ 130-2011 6.6.2"),
                    _enum("tieFromFirstStep", "首步设置连墙件", ["是", "否"], "是"),
                    _num("tieOffset", "连墙件偏离主节点", "mm", 200.0, 0.0, 500.0, 10.0, "JGJ 130-2011 6.4.3"),
                    _num("tieNv", "连接承载力设计值 Nv", "kN", 12.0, 1.0, 50.0, 1.0, "JGJ 130-2011 5.2.14"),
                    _enum("sweepBar", "设置纵横向扫地杆", ["是", "否"], "是"),
                    _num("sweepBarHeight", "扫地杆距钢管底端", "mm", 200.0, 0.0, 400.0, 10.0, "JGJ 130-2011 6.3.2"),
                    _num("railHeight", "防护栏杆上杆高度", "m", 1.2, 0.9, 1.5, 0.1, "JGJ 80-2016 4.3.1"),
                    _enum("safetyNet", "张挂密目式安全立网", ["是", "否"], "是"),
                    _num("freeHeight", "连墙点以上悬臂高度", "m", 3.6, 0.0, 6.0, 0.1, "GB 55023-2022 4.4.6"),
                    _num("braceSpacing", "剪刀撑间距（H<24m）", "m", 15.0, 6.0, 30.0, 0.5, "GB 55023-2022 4.4.7"),
                    _enum("braceContinuous", "H≥24m 全立面连续剪刀撑", ["是", "否"], "是"),
                    _num("gamma0", "结构重要性系数 γ0", "—", 1.0, 0.9, 1.1, 0.1, "CECS 699-2020 5.1.4"),
                    _num("tieNetArea", "连墙件净截面 Ac", "mm²", 0.0, 0.0, 1000.0, 1.0, "CECS 699-2020 5.2.12（0=按毛截面）"),
                    _num("boardThickness", "脚手板厚度", "mm", 50.0, 20.0, 100.0, 5.0, "JGJ 130-2011 6.2.4"),
                    _num("boardF", "脚手板抗弯强度设计值", "N/mm²", 15.0, 5.0, 30.0, 0.5, "JGJ 130-2011 5.1"),
                    _num("boardE", "脚手板弹性模量", "N/mm²", 10000.0, 5000.0, 20000.0, 500.0, "JGJ 130-2011 5.1"),
                ],
            },
        ],
    }


def _num(key: str, label: str, unit: str, default: float, min_: float, max_: float, step: float, clause: str) -> dict[str, Any]:
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


def _enum(key: str, label: str, options: list[str], default: str) -> dict[str, Any]:
    return {"key": key, "label": label, "type": "select", "options": options, "default": default}


def _section(steel: str) -> tuple[float, float, float, float]:
    if steel not in STEEL_SECTIONS:
        raise ValueError(f"unknown steel type: {steel}")
    d = STEEL_SECTIONS[steel]["D"]
    t = STEEL_SECTIONS[steel]["t"]
    inner = d - 2 * t
    area = math.pi / 4 * (d**2 - inner**2)
    inertia = math.pi / 64 * (d**4 - inner**4)
    radius = math.sqrt(inertia / area)
    modulus = inertia / (d / 2)
    return area, inertia, radius, modulus


def section_properties(steel: str) -> tuple[float, float, float, float]:
    """Public section helper for new modules; does not change fastener results."""
    return _section(steel)


_PHI_TABLE: dict[int, float] = {
    int(k): float(v)
    for k, v in json.loads(
        (Path(__file__).with_name("phi_table.json")).read_text(encoding="utf-8")
    ).items()
}


def phi_value(lam: float) -> float:
    """JGJ 130-2011 附录 A 表 A.0.6（Q235）。"""
    key = max(0, min(250, int(round(lam))))
    return _PHI_TABLE.get(key, 0.117)


def mu_value(lb: float, layout: str = "双排", tie: str = "两步三跨") -> float:
    """JGJ 130-2011 表 5.2.8，按横距就近取值。

    双排：1.05/1.30/1.55 → 二步三跨 1.50/1.55/1.60；三步三跨 1.70/1.75/1.80
    单排（横距 ≤1.50）：二步三跨 1.80；三步三跨 2.00
    """
    if layout == "单排":
        return 2.00 if tie == "三步三跨" else 1.80
    rows = [(1.05, 1.50, 1.70), (1.30, 1.55, 1.75), (1.55, 1.60, 1.80)]
    col = 2 if tie == "三步三跨" else 1
    xs = [r[0] for r in rows]
    ys = [r[col] for r in rows]
    return _interp(xs, ys, lb)


# 附录 A 表 A.0.1：双排脚手架立杆每米结构自重标准值 gk (kN/m)
_GK_STEPS = [1.20, 1.35, 1.50, 1.80, 2.00]
_GK_LAS = [1.2, 1.5, 1.8, 2.0, 2.1]
_GK_TABLE = [
    [0.1538, 0.1667, 0.1796, 0.1882, 0.1925],
    [0.1426, 0.1543, 0.1660, 0.1739, 0.1778],
    [0.1336, 0.1444, 0.1552, 0.1624, 0.1660],
    [0.1202, 0.1295, 0.1389, 0.1451, 0.1482],
    [0.1134, 0.1221, 0.1307, 0.1365, 0.1394],
]


def _interp(xs: list[float], ys: list[float], x: float) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


def gk_value(h: float, la: float) -> float:
    """按表 A.0.1 双排架双向线性插值。"""
    rows = [_interp(_GK_LAS, row, la) for row in _GK_TABLE]
    return _interp(_GK_STEPS, rows, h)


# GB 50009-2012 表 8.2.1 风压高度变化系数（离地高度 5–100m）
_MUZ_TABLE: dict[str, list[tuple[float, float]]] = {
    "A": [(5, 1.09), (10, 1.28), (15, 1.42), (20, 1.52), (30, 1.67), (40, 1.79), (50, 1.89), (60, 1.97), (70, 2.05), (80, 2.12), (90, 2.18), (100, 2.23)],
    "B": [(5, 1.00), (10, 1.00), (15, 1.13), (20, 1.23), (30, 1.39), (40, 1.52), (50, 1.62), (60, 1.71), (70, 1.79), (80, 1.87), (90, 1.93), (100, 2.00)],
    "C": [(5, 0.65), (10, 0.65), (15, 0.65), (20, 0.74), (30, 0.88), (40, 1.00), (50, 1.10), (60, 1.20), (70, 1.28), (80, 1.36), (90, 1.43), (100, 1.50)],
    "D": [(5, 0.51), (10, 0.51), (15, 0.51), (20, 0.51), (30, 0.51), (40, 0.60), (50, 0.69), (60, 0.77), (70, 0.84), (80, 0.91), (90, 0.98), (100, 1.04)],
}


def muz_value(z: float, terrain: str) -> float:
    """GB 50009-2012 表 8.2.1，按高度线性插值。"""
    rows = _MUZ_TABLE.get(terrain, _MUZ_TABLE["B"])
    zz = max(rows[0][0], min(rows[-1][0], z))
    return _interp([r[0] for r in rows], [r[1] for r in rows], zz)


def mus_value(enclosure: str, backdrop: str, phi: float) -> float:
    """JGJ 130-2011 表 4.2.6。敞开式按 μstw 处理，暂用 1.2φ 近似。"""
    if enclosure == "敞开":
        return 1.2 * phi
    return phi * (1.0 if backdrop == "全封闭墙" else 1.3)


# JGJ 130-2011 表 A.0.5 敞开式脚手架挡风系数 φ
_A05_STEPS = [0.60, 0.75, 0.90, 1.05, 1.20, 1.35, 1.50, 1.60, 1.80, 2.00]
_A05_LAS = [0.4, 0.6, 0.75, 0.9, 1.0, 1.2, 1.3, 1.35, 1.5, 1.8, 2.0]
_A05_TABLE = [
    [0.260, 0.212, 0.193, 0.180, 0.173, 0.164, 0.160, 0.158, 0.154, 0.148, 0.144],
    [0.241, 0.192, 0.173, 0.161, 0.154, 0.144, 0.141, 0.139, 0.135, 0.128, 0.125],
    [0.228, 0.180, 0.161, 0.148, 0.141, 0.132, 0.128, 0.126, 0.122, 0.115, 0.112],
    [0.219, 0.171, 0.151, 0.138, 0.132, 0.122, 0.119, 0.117, 0.113, 0.106, 0.103],
    [0.212, 0.164, 0.144, 0.132, 0.125, 0.115, 0.112, 0.110, 0.106, 0.099, 0.096],
    [0.207, 0.158, 0.139, 0.126, 0.120, 0.110, 0.106, 0.105, 0.100, 0.094, 0.091],
    [0.202, 0.154, 0.135, 0.122, 0.115, 0.106, 0.102, 0.100, 0.096, 0.090, 0.086],
    [0.200, 0.152, 0.132, 0.119, 0.113, 0.103, 0.100, 0.098, 0.094, 0.087, 0.084],
    [0.1959, 0.148, 0.128, 0.115, 0.109, 0.099, 0.096, 0.094, 0.090, 0.083, 0.080],
    [0.1927, 0.144, 0.125, 0.112, 0.106, 0.096, 0.092, 0.091, 0.086, 0.080, 0.077],
]


def phi_a05_value(h: float, la: float) -> float:
    """表 A.0.5 敞开式挡风系数，按步距/纵距双线性插值。"""
    rows = [_interp(_A05_LAS, row, la) for row in _A05_TABLE]
    return _interp(_A05_STEPS, rows, h)


def _merged(params: dict[str, Any]) -> dict[str, Any]:
    merged = dict(DEFAULTS)
    for key, value in (params or {}).items():
        if key in merged:
            merged[key] = value
    for key in ("h", "la", "lb", "H", "fg", "baseArea", "hBoard", "braceW", "tieOffset", "tieNv", "sweepBarHeight", "railHeight", "freeHeight", "braceSpacing", "gamma0", "tieNetArea", "boardThickness", "boardF", "boardE"):
        merged[key] = float(merged[key])
    for key in ("dead", "live", "wind"):
        merged[key] = float(merged[key])
    if merged["h"] <= 0 or merged["la"] <= 0 or merged["lb"] <= 0:
        raise ValueError("步距与立杆间距必须为正数")
    if merged["steel"] not in STEEL_SECTIONS:
        raise ValueError(f"unknown steel type: {merged['steel']}")
    if merged["tie"] not in TIE_SPANS:
        raise ValueError(f"unknown tie layout: {merged['tie']}")
    if merged["layout"] not in ("双排", "单排"):
        raise ValueError(f"unknown scaffold layout: {merged['layout']}")
    if merged["terrain"] not in ("A", "B", "C", "D"):
        raise ValueError(f"unknown terrain category: {merged['terrain']}")
    if merged["enclosure"] not in ("全封闭", "半封闭", "敞开"):
        raise ValueError(f"unknown enclosure: {merged['enclosure']}")
    if merged["backdrop"] not in ("全封闭墙", "敞开、框架和开洞墙"):
        raise ValueError(f"unknown backdrop: {merged['backdrop']}")
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
) -> dict[str, Any]:
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
    area, _inertia, radius, modulus = _section(p["steel"])

    mu = mu_value(p["lb"], str(p["layout"]), str(p["tie"]))
    lam_check = mu * p["h"] * 1000.0 / radius          # 5.2.8：验算长细比取 k=1
    lam_stability = 1.155 * mu * p["h"] * 1000.0 / radius  # 5.2.8：稳定性取 k=1.155
    phi = phi_value(lam_stability)

    levels = max(1, math.ceil(p["H"] / p["h"]))
    gk_frame = gk_value(p["h"], p["la"])  # 表 A.0.1
    ng1 = gk_frame * p["H"]
    ng2 = p["dead"] * p["la"] * p["lb"] * levels + 0.17 * p["la"] * levels  # 表4.2.1 栏杆+竹串片挡板
    nq = p["live"] * p["la"] * p["lb"]
    # CECS 699-2020 5.2.7：N = 1.3ΣNGk + 1.5ΣNQk（风荷载通过 Mw 体现）
    n_design = 1.3 * (ng1 + ng2) + 1.5 * nq
    n_wind = n_no_wind = n_design

    muz = muz_value(p["z"], str(p["terrain"]))
    phi_wind_used = (
        phi_a05_value(p["h"], p["la"]) if str(p["enclosure"]) == "敞开" else float(p["phiWind"])
    )
    mus = mus_value(str(p["enclosure"]), str(p["backdrop"]), phi_wind_used)
    wk = muz * mus * p["wind"]  # 式 4.2.5
    tie_v_early, _ = TIE_SPANS.get(p["tie"], (2, 3))
    xi = 0.6 if tie_v_early <= 2 else 0.4
    hc_mm = tie_v_early * p["h"] * 1000.0
    m_wk = 0.05 * xi * wk * p["la"] * hc_mm**2  # CECS 5.2.9-2（N·mm）
    m_w = 0.9 * m_wk  # CECS 5.2.9-1

    sigma_no_wind = p["gamma0"] * n_no_wind * 1000.0 / (phi * area)
    sigma_wind = p["gamma0"] * (n_wind * 1000.0 / (phi * area) + m_w / modulus)
    sigma = max(sigma_no_wind, sigma_wind)

    tie_v, tie_h = TIE_SPANS.get(p["tie"], (2, 3))
    a_w = (tie_v * p["h"]) * (tie_h * p["la"])
    n_lw = 1.5 * wk * a_w  # CECS 5.2.13
    n_l = n_lw + 3.0
    lam_tie = p["lb"] * 1000.0 / radius
    phi_tie = phi_value(lam_tie)
    ac = p["tieNetArea"] if p["tieNetArea"] > 0 else area
    sigma_tie = n_l * 1000.0 / ac
    sigma_tie_stab = n_l * 1000.0 / (phi_tie * area)

    q_long = 1.3 * (p["dead"] * p["lb"] / 2) + 1.5 * (p["live"] * p["lb"] / 2)
    m_long = 0.1 * q_long * p["la"] ** 2
    sigma_long = m_long * 1e6 / modulus

    # 传力路径：脚手板 → 横向水平杆（间距 la，负荷宽度 la）→ 纵向水平杆 → 立杆
    q_trans = 1.3 * p["dead"] * p["la"] + 1.5 * p["live"] * p["la"]
    m_trans = q_trans * p["lb"] ** 2 / 8  # 5.2.4：横向水平杆按简支梁
    sigma_trans = m_trans * 1e6 / modulus

    r_coupler = 1.1 * q_long * p["la"]  # 三跨连续梁内支座反力

    # 5.2.3 挠度验算（标准值）
    EI = E_STEEL * _inertia
    q_serv_long = (p["dead"] + p["live"]) * p["lb"] / 2
    v_long = 0.00677 * q_serv_long * (p["la"] * 1000.0) ** 4 / EI
    q_serv_trans = (p["dead"] + p["live"]) * p["la"]
    v_trans = 5 * q_serv_trans * (p["lb"] * 1000.0) ** 4 / (384 * EI)
    v_limit_long = min(p["la"] * 1000.0 / 150.0, 10.0)
    v_limit_trans = min(p["lb"] * 1000.0 / 150.0, 10.0)
    brace_min = max(6.0, 4 * p["la"])
    brace_angle = math.degrees(math.atan(p["h"] / p["la"]))
    first_step_ok = str(p["tieFromFirstStep"]) == "是"
    sweep_bar_ok = str(p["sweepBar"]) == "是" and p["sweepBarHeight"] <= 200.0
    safety_net_ok = str(p["safetyNet"]) == "是"
    free_limit = min(2 * p["h"], 4.0)
    brace_layout_ok = (
        (p["H"] < 24 and p["braceSpacing"] <= 15.0)
        or (p["H"] >= 24 and str(p["braceContinuous"]) == "是")
    )
    tie_spacing_ok = tie_v <= 3 and tie_h <= 3

    # 脚手板（面板）验算：按三跨连续板，取 1m 宽
    q_panel = 1.3 * p["dead"] + 1.5 * p["live"]          # kN/m per 1m width
    m_panel = 0.1 * q_panel * p["la"] ** 2 * 1e6          # N·mm
    w_panel = 1000.0 * p["boardThickness"] ** 2 / 6.0
    i_panel = 1000.0 * p["boardThickness"] ** 3 / 12.0
    sigma_panel = m_panel / w_panel
    q_panel_serv = p["dead"] + p["live"]
    v_panel = 0.00677 * q_panel_serv * (p["la"] * 1000.0) ** 4 / (p["boardE"] * i_panel)
    v_panel_limit = min(p["la"] * 1000.0 / 150.0, 10.0)
    n_standard = ng1 + ng2 + nq
    fg = p["fg"] * (0.4 if "回填" in str(p["foundation"]) else 1.0)
    p_ground = n_standard / p["baseArea"]

    construct_ratio = max(p["h"] / 2.0, p["la"] / 1.8)

    results = [
        _item(1, "upright_stability", "立杆稳定性（组合风荷载）", sigma, F_DESIGN, "N/mm²", "CECS 699-2020 5.2.6", True,
              "取 5.2.6-1 与 5.2.6-2 的不利值（含 γ0）"),
        _item(2, "slenderness", "立杆长细比 λ", lam_check, 210.0, "—", "JGJ 130-2011 5.1.9", False,
              "λ = kμh / i"),
        _item(3, "tie_strength", "连墙件强度", sigma_tie, 0.85 * F_DESIGN, "N/mm²", "CECS 699-2020 5.2.12", True,
              f"σ = Nl / Ac ≤ 0.85f（Ac={ac:.1f}mm²，{'净截面' if p['tieNetArea'] > 0 else '毛截面'}）"),
        _item(4, "tie_stability", "连墙件稳定承载力", sigma_tie_stab, 0.85 * F_DESIGN, "N/mm²", "CECS 699-2020 5.2.12", False,
              f"Nl / (φA) ≤ 0.85f，φ 按连墙件长细比 λ={lam_tie:.1f} 取 {phi_tie:.3f}"),
        _item(5, "ledger_long", "纵向水平杆抗弯", sigma_long, F_DESIGN, "N/mm²", "JGJ 130-2011 5.2.4", False,
              "M = 0.1q·la²，σ = M/W"),
        _item(6, "ledger_trans", "横向水平杆抗弯", sigma_trans, F_DESIGN, "N/mm²", "JGJ 130-2011 5.2.4", False,
              "M = 0.1q·lb²，σ = M/W"),
        _item(7, "coupler_slip", "扣件抗滑承载力", r_coupler, 8.0, "kN", "JGJ 130-2011 5.2.5", True,
              "R = 1.2ΣNGk + 1.4ΣNQk"),
        _item(8, "foundation", "立杆地基承载力", p_ground, fg, "kPa", "JGJ 130-2011 5.5.1", False,
              "pk = Nk / A ≤ fg"),
        _item(9, "height_limit", "脚手架搭设高度", p["H"], 50.0, "m", "JGJ 130-2011 6.1.2", False,
              "H ≤ [H]"),
        _item(10, "construct_limit", "步距/纵距构造限值", construct_ratio, 1.0, "—", "JGJ 130-2011 表6.1.1", True,
              "max(h/2.0, la/1.8) ≤ 1"),
        _item(11, "ledger_long_deflection", "纵向水平杆挠度", v_long, v_limit_long, "mm", "JGJ 130-2011 5.2.3", False,
              "三跨连续梁 v=0.00677·q·la⁴/EI ≤ min(la/150,10)"),
        _item(12, "ledger_trans_deflection", "横向水平杆挠度", v_trans, v_limit_trans, "mm", "JGJ 130-2011 5.2.3", False,
              "简支梁 v=5q·lb⁴/(384EI) ≤ min(lb/150,10)"),
        _item(13, "tie_coupler_slip", "连墙件扣件抗滑", n_l, 8.0, "kN", "JGJ 130-2011 5.2.15", True,
              "Nl ≤ Rc = 8.0kN"),
        _item(14, "brace_construct", "剪刀撑宽度构造", p["braceW"], brace_min, "m", "JGJ 130-2011 6.6.2", False,
              "剪刀撑宽度 ≥ max(6m, 4跨)"),
        _item(15, "tie_area", "连墙件覆盖面积", a_w, 40.0, "m²", "JGJ 130-2011 表6.4.2", True,
              f"Aw = {tie_v}h × {tie_h}la ≤ 40m²"),
        _item(16, "tie_connection", "连墙件连接强度", n_l, float(p["tieNv"]), "kN", "JGJ 130-2011 5.2.14", True,
              "Nl ≤ Nv（Nv 按实际连接构造取值）"),
        _item(17, "tie_offset", "连墙件偏离主节点", p["tieOffset"], 300.0, "mm", "JGJ 130-2011 6.4.3", False,
              "偏离主节点 ≤ 300mm"),
        _item(18, "tie_first_step", "连墙件首步设置", 1.0 if first_step_ok else 0.0, 1.0, "—", "JGJ 130-2011 6.4.3", False,
              "应从底层第一步纵向水平杆处设置", ok=first_step_ok),
        _item(19, "sweep_bar", "纵横向扫地杆", 1.0 if sweep_bar_ok else 0.0, 1.0, "—", "JGJ 130-2011 6.3.2", False,
              f"必须设置，距钢管底端 ≤200mm（当前 {p['sweepBarHeight']}mm）", ok=sweep_bar_ok),
        _item(20, "brace_angle", "剪刀撑与地面倾角", brace_angle, 60.0, "°", "JGJ 130-2011 6.6.2", False,
              "45° ≤ α ≤ 60°", ok=45.0 <= brace_angle <= 60.0),
        _item(21, "rail_height", "防护栏杆上杆高度", p["railHeight"], 1.2, "m", "JGJ 80-2016 4.3.1", False,
              "上杆距地面 ≥1.2m", ok=p["railHeight"] >= 1.2),
        _item(22, "toe_board", "挡脚板高度", p["hBoard"], 180.0, "mm", "JGJ 80-2016 4.3.1", False,
              "挡脚板高度 ≥180mm", ok=p["hBoard"] >= 180.0),
        _item(23, "safety_net", "密目式安全立网", 1.0 if safety_net_ok else 0.0, 1.0, "—", "JGJ 80-2016 4.3.5", False,
              "防护栏杆应张挂密目式安全立网", ok=safety_net_ok),
        _item(24, "brace_width_max", "剪刀撑宽度上限", p["braceW"], 9.0, "m", "GB 55023-2022 4.4.7", False,
              "剪刀撑宽度不应大于 9m", ok=p["braceW"] <= 9.0),
        _item(25, "brace_layout", "剪刀撑布置间距/连续性",
              p["braceSpacing"] if p["H"] < 24 else (1.0 if str(p["braceContinuous"]) == "是" else 0.0),
              15.0 if p["H"] < 24 else 1.0,
              "m" if p["H"] < 24 else "—",
              "GB 55023-2022 4.4.7", False,
              "H<24m：间距≤15m；H≥24m：全立面连续设置",
              ok=brace_layout_ok),
        _item(26, "free_height", "连墙点以上悬臂高度", p["freeHeight"], free_limit, "m", "GB 55023-2022 4.4.6", True,
              "悬臂高度 ≤ min(2步, 4m)", ok=p["freeHeight"] <= free_limit + 1e-9),
        _item(27, "tie_spacing", "连墙件间距（步/跨）", float(tie_v), 3.0, "步", "GB 55023-2022 4.4.6", True,
              f"竖向 {tie_v} 步 ≤3 步；水平 {tie_h} 跨 ≤3 跨", ok=tie_spacing_ok),
        _item(28, "board_bending", "脚手板抗弯", sigma_panel, p["boardF"], "N/mm²", "CECS 699-2020 5.1.10", False,
              f"取1m宽板，M=0.1q·la²，W={w_panel:.0f}mm³"),
        _item(29, "board_deflection", "脚手板挠度", v_panel, v_panel_limit, "mm", "JGJ 130-2011 表5.1.8", False,
              "三跨连续板 v=0.00677q·la⁴/EI ≤ min(la/150,10)"),
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
            "failed": sum(1 for r in results if not r["ok"]),
            "control_failed": sum(1 for r in results if not r["ok"] and r["control"]),
        },
        "results": results,
        "derived": {
            "A_mm2": round(area, 1),
            "I_mm4": round(_inertia, 0),
            "i_mm": round(radius, 2),
            "W_mm3": round(modulus, 1),
            "lambda_check": round(lam_check, 1),
            "lambda_stability": round(lam_stability, 1),
            "phi": round(phi, 3),
            "phi_tie": round(phi_tie, 3),
            "Ac_mm2": round(ac, 1),
            "sigma_panel_N_mm2": round(sigma_panel, 2),
            "v_panel_mm": round(v_panel, 2),
            "lambda_tie": round(lam_tie, 1),
            "mu": mu,
            "layout": p["layout"],
            "N_kN": round(n_design, 2),
            "N_wind_kN": round(n_wind, 2),
            "N_no_wind_kN": round(n_no_wind, 2),
            "Nk_kN": round(n_standard, 2),
            "Nl_kN": round(n_l, 2),
            "R_kN": round(r_coupler, 2),
            "q_long_kN_m": round(q_long, 3),
            "q_trans_kN_m": round(q_trans, 3),
            "f_design": F_DESIGN,
            "Mw_Nmm": round(m_w, 0),
            "wk_kN_m2": round(wk, 3),
            "muz": round(muz, 3),
            "mus": round(mus, 3),
            "phi_wind_used": round(phi_wind_used, 4),
            "gk_kN_m": round(gk_frame, 4),
            "Aw_m2": round(a_w, 2),
            "v_long_mm": round(v_long, 2),
            "v_long_limit_mm": round(v_limit_long, 2),
            "v_trans_mm": round(v_trans, 2),
            "v_trans_limit_mm": round(v_limit_trans, 2),
            "brace_min_m": brace_min,
            "brace_angle_deg": round(brace_angle, 1),
            "tieNv_kN": round(float(p["tieNv"]), 2),
            "fg_kPa": fg,
        },
        "assumptions": [
            "f=205 N/mm²、Rc=8.00 kN 取自 JGJ 130-2011 表 5.1.6 / 表 5.1.7",
            "φ 取自附录 A 表 A.0.6（已落盘为 251 点查表，按 λ 四舍五入取值）",
            "μ 按表 5.2.8 按横距线性插值（双排/单排、二步/三步三跨）",
            "敞开式挡风系数 φ 按 JGJ 130 附录 A 表 A.0.5 双线性插值",
            "λ 分两个：验算取 k=1，稳定性取 k=1.155（5.2.8）",
            "立杆自重按附录 A 表 A.0.1 双排架双向线性插值（表值而非近似值）",
            "荷载分项系数按 CECS 699-2020 表4.3.3：γG=1.3，γQ=1.5（JGJ 130 的 1.2/1.4 已被替代）",
            "Mw 按 CECS 699-2020 式5.2.9：Mw=0.9×0.05×ξ×wk×la×Hc²，ξ=0.6（二步）/0.4（三步）",
            "立杆稳定按 CECS 5.2.6 计入结构重要性系数 γ0（默认 1.0）",
            "μz 按 GB 50009-2012 表 8.2.1 插值；μs 按 JGJ 130-2011 表 4.2.6（敞开式暂用 1.2φ 近似）",
            "本结果为计算骨架，尚未与品茗计算书 oracle 对齐（verified=false）",
            "5.2.14 连接承载力 Nv 由用户按实际连接构造（双扣件/预埋件等）输入，默认 12.0kN",
            "6.4.3 首步设置与偏离主节点、6.3.2 扫地杆为构造项，按用户输入判定，需现场核对",
        ],
    }
