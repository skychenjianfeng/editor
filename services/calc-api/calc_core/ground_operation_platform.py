"""落地式操作平台验算。

依据 JGJ 80-2016《建筑施工高处作业安全技术规范》第 4.3、6.1、6.3 节及附录 B。
第 6.3.3 条要求按相关脚手架规范继续计算构件；本模块采用附录 B 的受弯、轴心
受压表达，并对地基承载力与水平杆扣件抗滑作明确简化验算。未覆盖项目在
standards.gaps 与 assumptions 中列明。
"""

from __future__ import annotations

from typing import Any

MODULE_KEY = "ground-operation-platform"
STANDARD = "JGJ 80-2016"

DEFAULTS: dict[str, Any] = {
    # pmsc.ini [GroundPlat information] 的示例尺寸/荷载，不作为推荐值。
    "platformKind": "施工平台",
    "la": 0.9,
    "lb": 0.9,
    "h": 1.5,
    "H": 4.0,
    "length": 3.0,
    "width": 3.0,
    "dead": 0.35,
    "constructionLoad": 4.0,
    "materialLoad": 5.0,
    "gammaG": 1.2,
    "gammaQ": 1.4,
    "panelSpan": 0.3,
    "panelThickness": 18.0,
    "panelE": 6000.0,
    "panelF": 15.0,
    "panelDeflectionRatio": 150.0,
    "panelDeflectionCap": 10.0,
    "joistW": 5260.0,
    "joistF": 205.0,
    "uprightA": 506.0,
    "uprightPhi": 0.40,
    "uprightF": 205.0,
    "gk": 0.13,
    "fk": 100.0,
    "kc": 0.40,
    "baseArea": 0.25,
    "couplerRc": 8.0,
    "guardrailHeight": 1.2,
    "toeBoardHeight": 180.0,
    "tieSpacing": 4.0,
    "ladderStepSpacing": 300.0,
    "doubleHorizontalRails": True,
    "independentAndRigidConnection": True,
    "braceInstalled": True,
    "ladderInstalled": True,
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
        "title": "落地式操作平台",
        "standard": STANDARD,
        "verified": False,
        "groups": [
            {
                "key": "geometry",
                "title": "平台尺寸与类型",
                "fields": [
                    {
                        "key": "platformKind",
                        "label": "平台类型",
                        "type": "select",
                        "options": ["施工平台", "接料平台"],
                        "default": "施工平台",
                        "clause": "JGJ 80-2016 6.3.1-2（第9页）",
                    },
                    num("la", "立杆纵距 la", "m", 0.9, 0.6, 1.8, 0.05, "JGJ 80-2016 6.3.2～6.3.3（第9页）"),
                    num("lb", "立杆横距 lb", "m", 0.9, 0.6, 1.8, 0.05, "JGJ 80-2016 6.3.2～6.3.3（第9页）"),
                    num("h", "步距 h", "m", 1.5, 0.9, 2.0, 0.1, "JGJ 80-2016 6.3.2～6.3.4（第9页）"),
                    num("H", "平台搭设高度 H", "m", 4.0, 2.0, 15.0, 0.5, "JGJ 80-2016 6.3.1-1（第9页）"),
                    num("length", "平台长度", "m", 3.0, 0.9, 20.0, 0.1, "JGJ 80-2016 6.3.1-1（第9页）"),
                    num("width", "平台宽度", "m", 3.0, 0.9, 20.0, 0.1, "JGJ 80-2016 6.3.1-1（第9页）"),
                ],
            },
            {
                "key": "load",
                "title": "荷载参数",
                "fields": [
                    num("dead", "平台板及构配件自重标准值", "kN/m²", 0.35, 0.05, 1.0, 0.05, "JGJ 80-2016 6.1.1、6.3.3（第9页）"),
                    num(
                        "constructionLoad",
                        "施工荷载标准值（pmsc 示例默认 4.0）",
                        "kN/m²",
                        4.0,
                        0.0,
                        20.0,
                        0.1,
                        "JGJ 80-2016 6.3.1-2（第9页）",
                    ),
                    num(
                        "materialLoad",
                        "材料堆载标准值（pmsc 示例默认 5.0）",
                        "kN/m²",
                        5.0,
                        0.0,
                        30.0,
                        0.1,
                        "JGJ 80-2016 6.1.5、6.3.1-2（第9页）",
                    ),
                    num("gammaG", "恒荷载分项系数 γG", "—", 1.2, 1.0, 1.5, 0.05, "JGJ 80-2016 附录B B.0.1"),
                    num("gammaQ", "活荷载分项系数 γQ", "—", 1.4, 1.0, 1.5, 0.05, "JGJ 80-2016 附录B B.0.1"),
                ],
            },
            {
                "key": "panel",
                "title": "平台板参数",
                "fields": [
                    num("panelSpan", "平台板计算跨度", "m", 0.3, 0.1, 0.9, 0.05, "JGJ 80-2016 6.1.3（第9页）（补充计算）"),
                    num("panelThickness", "平台板厚度", "mm", 18.0, 5.0, 80.0, 1.0, "JGJ 80-2016 6.1.3（第9页）"),
                    num("panelE", "平台板弹性模量 E", "N/mm²", 6000.0, 1000.0, 210000.0, 500.0, "补充计算参数"),
                    num("panelF", "平台板抗弯强度设计值 f", "N/mm²", 15.0, 1.0, 300.0, 1.0, "补充计算参数"),
                    num("panelDeflectionRatio", "平台板挠度限值分母", "—", 150.0, 100.0, 400.0, 10.0, "补充计算参数"),
                    num("panelDeflectionCap", "平台板挠度绝对限值", "mm", 10.0, 1.0, 30.0, 1.0, "补充计算参数"),
                ],
            },
            {
                "key": "joist",
                "title": "搁栅或水平杆参数",
                "fields": [
                    num("joistW", "搁栅截面模量 W", "mm³", 5260.0, 100.0, 100000.0, 10.0, "JGJ 80-2016 6.3.3、附录B（第9、16页）"),
                    num("joistF", "搁栅抗弯强度设计值 f", "N/mm²", 205.0, 10.0, 400.0, 5.0, "JGJ 80-2016 附录B B.0.1（第16页）"),
                ],
            },
            {
                "key": "upright",
                "title": "立杆稳定参数",
                "fields": [
                    num("uprightA", "立杆毛截面面积 A", "mm²", 506.0, 50.0, 5000.0, 1.0, "JGJ 80-2016 附录B B.0.3-2（第17页）"),
                    num("uprightPhi", "轴心受压稳定系数 φ", "—", 0.40, 0.05, 1.0, 0.01, "JGJ 80-2016 6.3.3、附录B B.0.3-2（第9、17页）"),
                    num("uprightF", "立杆抗压强度设计值 f", "N/mm²", 205.0, 20.0, 400.0, 5.0, "JGJ 80-2016 6.3.3、附录B B.0.3-2（第9、17页）"),
                    num("gk", "立杆每米结构自重标准值 gk", "kN/m", 0.13, 0.01, 1.0, 0.01, "JGJ 80-2016 6.3.3（第9页）（补充计算）"),
                ],
            },
            {
                "key": "foundation_and_connection",
                "title": "地基与水平杆连接",
                "fields": [
                    num(
                        "fk",
                        "地基承载力特征值 fak（参数键 fk）",
                        "kPa",
                        100.0,
                        10.0,
                        500.0,
                        5.0,
                        "JGJ 80-2016 6.3.3（按相关脚手架规范继续验算）",
                    ),
                    num(
                        "kc",
                        "地基承载力调整系数 kc",
                        "—",
                        0.40,
                        0.10,
                        1.0,
                        0.05,
                        "JGJ 80-2016 6.3.3（按相关脚手架规范及地基资料取值）",
                    ),
                    num(
                        "baseArea",
                        "单根立杆基础底面积",
                        "m²",
                        0.25,
                        0.05,
                        2.0,
                        0.01,
                        "JGJ 80-2016 6.3.3（按相关脚手架规范继续验算）",
                    ),
                    num(
                        "couplerRc",
                        "水平杆连接扣件抗滑承载力设计值 Rc",
                        "kN",
                        8.0,
                        1.0,
                        40.0,
                        0.5,
                        "JGJ 80-2016 6.3.3（按相关脚手架规范继续验算）",
                    ),
                ],
            },
            {
                "key": "guardrail_and_stability",
                "title": "防护栏杆与架体构造",
                "fields": [
                    num(
                        "guardrailHeight",
                        "防护栏杆上横杆高度",
                        "m",
                        1.2,
                        1.2,
                        2.0,
                        0.05,
                        "JGJ 80-2016 4.3.1-1、6.1.4",
                    ),
                    num(
                        "toeBoardHeight",
                        "挡脚板高度",
                        "mm",
                        180.0,
                        180.0,
                        300.0,
                        10.0,
                        "JGJ 80-2016 4.3.1、6.1.4",
                    ),
                    num(
                        "tieSpacing",
                        "连墙件最大竖向/水平间隔",
                        "m",
                        4.0,
                        0.5,
                        4.0,
                        0.1,
                        "JGJ 80-2016 6.3.1-5",
                    ),
                    num(
                        "ladderStepSpacing",
                        "扶梯踏步间距",
                        "mm",
                        300.0,
                        100.0,
                        400.0,
                        10.0,
                        "JGJ 80-2016 6.1.4",
                    ),
                    boolean(
                        "doubleHorizontalRails",
                        "防护栏杆设置上下两道横杆且立杆固定",
                        True,
                        "JGJ 80-2016 4.3.1、4.3.2、6.1.4",
                    ),
                    boolean(
                        "independentAndRigidConnection",
                        "平台独立设置且与建筑结构刚性连接，不与脚手架连接",
                        True,
                        "JGJ 80-2016 6.3.1-3",
                    ),
                    boolean(
                        "braceInstalled",
                        "外立面设置剪刀撑或斜撑并设置水平剪刀撑",
                        True,
                        "JGJ 80-2016 6.3.1-4、6.3.1-5",
                    ),
                    boolean(
                        "ladderInstalled",
                        "单独设置的操作平台配置上下扶梯",
                        True,
                        "JGJ 80-2016 6.1.4",
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

    platform_kind = str(merged["platformKind"])
    if platform_kind not in {"施工平台", "接料平台"}:
        raise ValueError("platformKind 必须为“施工平台”或“接料平台”")

    bool_keys = {
        "doubleHorizontalRails",
        "independentAndRigidConnection",
        "braceInstalled",
        "ladderInstalled",
    }
    numeric_keys = [
        key for key in DEFAULTS if key not in {"platformKind", *bool_keys}
    ]
    p: dict[str, Any] = {key: float(merged[key]) for key in numeric_keys}
    p["platformKind"] = platform_kind
    for key in bool_keys:
        p[key] = bool(merged[key])

    positive_keys = (
        "la",
        "lb",
        "h",
        "H",
        "length",
        "width",
        "panelSpan",
        "panelThickness",
        "panelE",
        "panelF",
        "panelDeflectionRatio",
        "panelDeflectionCap",
        "joistW",
        "joistF",
        "uprightA",
        "uprightPhi",
        "uprightF",
        "gk",
        "fk",
        "kc",
        "baseArea",
        "couplerRc",
        "guardrailHeight",
        "toeBoardHeight",
        "tieSpacing",
        "ladderStepSpacing",
    )
    for key in positive_keys:
        if p[key] <= 0:
            raise ValueError(f"{key} 必须大于 0")

    for key in ("dead", "constructionLoad", "materialLoad", "gammaG", "gammaQ"):
        if p[key] < 0:
            raise ValueError(f"{key} 不得小于 0")
    if p["gammaG"] <= 0 or p["gammaQ"] <= 0:
        raise ValueError("gammaG、gammaQ 必须大于 0")
    if not 0 < p["uprightPhi"] <= 1:
        raise ValueError("uprightPhi 应在 (0, 1] 范围内")
    if not 0 < p["kc"] <= 1:
        raise ValueError("kc 应在 (0, 1] 范围内")
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
) -> dict[str, Any]:
    return {
        "no": no,
        "key": key,
        "item": item,
        "value": round(value, 3),
        "limit": round(limit, 3),
        "unit": unit,
        "ratio": round(value / limit if limit else 0.0, 3),
        "ok": (value <= limit + 1e-9) if ok is None else ok,
        "clause": clause,
        "control": control,
        "detail": detail,
    }


def run(params: dict[str, Any]) -> dict[str, Any]:
    p = _merged(params)

    area = p["length"] * p["width"]
    aspect_ratio = p["H"] / min(p["length"], p["width"])
    load_limit = 2.0 if p["platformKind"] == "施工平台" else 3.0
    live = (
        p["constructionLoad"]
        if p["platformKind"] == "施工平台"
        else max(p["constructionLoad"], p["materialLoad"])
    )

    utilization = max(
        area / 10.0,
        p["H"] / 15.0,
        aspect_ratio / 2.5,
        live / load_limit,
    )
    construction_ok = utilization <= 1.0 + 1e-9
    construction_detail = (
        f"{p['platformKind']}：A={area:.2f}m²≤10；H={p['H']:.2f}m≤15；"
        f"H/min(B,L)={aspect_ratio:.2f}≤2.5；"
        f"qk={live:.2f}kN/m²≤{load_limit:.1f}kN/m²"
    )

    q_design_area = p["gammaG"] * p["dead"] + p["gammaQ"] * live
    q_service_area = p["dead"] + live

    panel_span_mm = p["panelSpan"] * 1000.0
    panel_w = 1000.0 * p["panelThickness"] ** 2 / 6.0
    panel_i = 1000.0 * p["panelThickness"] ** 3 / 12.0
    panel_moment = q_design_area * p["panelSpan"] ** 2 / 8.0
    panel_stress = panel_moment * 1e6 / panel_w
    panel_deflection = (
        5.0
        * q_service_area
        * panel_span_mm**4
        / (384.0 * p["panelE"] * panel_i)
    )
    panel_deflection_limit = min(
        panel_span_mm / p["panelDeflectionRatio"],
        p["panelDeflectionCap"],
    )

    joist_line_design = q_design_area * p["panelSpan"]
    joist_moment = joist_line_design * p["la"] ** 2 / 8.0
    joist_stress = joist_moment * 1e6 / p["joistW"]

    upright_axial = (
        q_design_area * p["la"] * p["lb"]
        + p["gammaG"] * p["gk"] * p["H"]
    )
    upright_stress = upright_axial * 1000.0 / (p["uprightPhi"] * p["uprightA"])

    upright_service_axial = q_service_area * p["la"] * p["lb"] + p["gk"] * p["H"]
    foundation_pressure = upright_service_axial / p["baseArea"]
    foundation_limit = p["kc"] * p["fk"]

    # 水平杆端部连接按扣件抗滑验算；1.1 为模块明确采用的影响系数。
    coupler_demand = 1.1 * joist_line_design * p["la"]
    coupler_ok = coupler_demand <= p["couplerRc"] + 1e-9

    guardrail_checks = [
        ("栏杆高度≥1.2m", p["guardrailHeight"] >= 1.2 - 1e-9),
        ("挡脚板≥180mm", p["toeBoardHeight"] >= 180.0 - 1e-9),
        ("上下两道横杆", p["doubleHorizontalRails"]),
        ("独立设置且刚性连墙", p["independentAndRigidConnection"]),
        ("剪刀撑/斜撑", p["braceInstalled"]),
        ("连墙间隔≤4m", p["tieSpacing"] <= 4.0 + 1e-9),
        ("扶梯已设置", p["ladderInstalled"]),
        ("踏步间距≤400mm", p["ladderStepSpacing"] <= 400.0 + 1e-9),
    ]
    guardrail_ok = all(ok for _, ok in guardrail_checks)
    guardrail_failed = [label for label, ok in guardrail_checks if not ok]

    results = [
        _item(
            1,
            "geometry_construction",
            "面积、高度、高宽比及平台荷载构造控制",
            utilization,
            1.0,
            "—",
            "JGJ 80-2016 6.1.2、6.3.1（正文第9页）",
            True,
            construction_detail,
            ok=construction_ok,
        ),
        _item(
            2,
            "panel_bending",
            "平台板抗弯",
            panel_stress,
            p["panelF"],
            "N/mm²",
            "JGJ 80-2016 6.1.3（正文第9页）；平台板公式为补充计算",
            True,
            "取 1m 宽带按简支板验算：M=(γG·gk+γQ·qk)L²/8，σ=M/W≤f",
        ),
        _item(
            3,
            "panel_deflection",
            "平台板挠度",
            panel_deflection,
            panel_deflection_limit,
            "mm",
            "JGJ 80-2016 6.1.3（正文第9页）；公式及限值为补充计算",
            False,
            "v=5(qk+gk)L⁴/(384EI)≤min(L/150,10mm)",
        ),
        _item(
            4,
            "joist_bending",
            "水平杆或搁栅抗弯",
            joist_stress,
            p["joistF"],
            "N/mm²",
            "JGJ 80-2016 6.3.3、附录B B.0.1-1～B.0.2（第9、16页）",
            True,
            "按简支搁栅：M=(γG·gk+γQ·qk)·b·la²/8，σ=M/W≤f",
        ),
        _item(
            5,
            "upright_stability",
            "立杆稳定",
            upright_stress,
            p["uprightF"],
            "N/mm²",
            "JGJ 80-2016 6.3.3、附录B B.0.3-2（第9、17页）",
            True,
            "本模块选择校核立杆稳定：N/(φA)≤f；地基承载力另列 gap",
        ),
        _item(
            6,
            "foundation_bearing",
            "立杆基础地基承载力",
            foundation_pressure,
            foundation_limit,
            "kPa",
            "JGJ 80-2016 6.3.3（第9页，按相关脚手架规范继续验算）",
            True,
            (
                "Nk=(恒载+活载)·la·lb+gk·H，"
                "Nk/baseArea≤kc·fk；Nk为标准值，fk为地基承载力特征值"
            ),
        ),
        _item(
            7,
            "coupler_slip",
            "水平杆连接扣件抗滑",
            coupler_demand,
            p["couplerRc"],
            "kN",
            "JGJ 80-2016 6.3.3（第9页，按相关脚手架规范继续验算）",
            True,
            "明确采用 R=1.1·q·la≤Rc；q取水平杆从平台板带传来的设计线荷载",
            ok=coupler_ok,
        ),
        _item(
            8,
            "guardrail_tie_configuration",
            "防护栏杆、连墙件及稳定构造",
            1.0 if guardrail_ok else 0.0,
            1.0,
            "—",
            "JGJ 80-2016 4.3.1、6.1.4、6.3.1-3～6.3.1-5（正文第4、9页）",
            True,
            (
                "逐项核对栏杆高度、挡脚板、双横杆、刚性连墙/独立设置、"
                "剪刀撑/斜撑、连墙间隔和扶梯；"
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
                        "4.3.1",
                        "4.3.2",
                        "6.1.1",
                        "6.1.2",
                        "6.1.3",
                        "6.1.4",
                        "6.1.5",
                        "6.3.1",
                        "6.3.2",
                        "6.3.3",
                        "6.3.4",
                        "附录B B.0.1-1",
                        "附录B B.0.1-2",
                        "附录B B.0.2",
                        "附录B B.0.3-2",
                    ],
                }
            ],
            "missing": [],
            "complete": False,
            "gaps": [
                "JGJ 80-2016 第6.3.3条要求落地式平台按相关脚手架规范计算构件；本模块仅有 JGJ 80-2016 依据，借用附录B的受弯、立杆稳定表达作补充验算，未替代扣件式/门式脚手架规范的原生公式。",
                "JGJ 80-2016 未给出落地式操作平台面板抗弯及挠度的专用公式；第2项取1m宽带简支板通用公式，第3项取5qL⁴/(384EI)，挠度限值按min(L/150,10mm)假定。",
                "第4项将平台板传来的面荷载乘以板跨形成搁栅线荷载，按单跨简支梁M=qL²/8验算；未考虑连续梁有利效应、悬臂、节点偏心及集中荷载。",
                "第6项按 Nk/baseArea≤kc·fk 验算立杆地基承载力；kc和fk须由所采用脚手架规范、地基资料及现场条件确定，本模块不推导其取值。",
                "第7项采用明确假设 R=1.1·q·la≤Rc；Rc须按实际扣件型式、产品证明及相关脚手架规范取值，未验算多扣件共同工作、扭转和重复荷载。",
                "第8项是6.1.4及6.3.1的声明式符合项，仅检查用户输入；连墙件强度与稳定、连接强度、扣件抗滑及架体整体分析仍需按相关脚手架规范另行计算。",
                "平台板、搁栅及立杆的 E、f、W、I、A、φ、gk 均由用户按实际材料、截面和相关脚手架规范输入；默认值仅用于示例，不是材料或选型推荐。",
                "未计算风荷载、施工偏心荷载、坠落冲击以及多层同时作业；这些作用应按项目专项施工方案补充。",
                "pmsc.ini [GroundPlat information] 示例为 la=lb=0.9m、h=1.5m、H=4m、材料堆载5kN/m²、施工荷载4kN/m²；这些示例值不满足本规范限载，不能视为推荐值。",
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
            "platform_area_m2": round(area, 3),
            "aspect_ratio": round(aspect_ratio, 3),
            "live_load_kN_m2": round(live, 3),
            "live_load_limit_kN_m2": round(load_limit, 3),
            "q_design_kN_m2": round(q_design_area, 3),
            "q_service_kN_m2": round(q_service_area, 3),
            "panelW_mm3": round(panel_w, 1),
            "panelI_mm4": round(panel_i, 1),
            "panelM_kNm": round(panel_moment, 4),
            "panelStress_N_mm2": round(panel_stress, 3),
            "panelDeflection_mm": round(panel_deflection, 3),
            "panelDeflectionLimit_mm": round(panel_deflection_limit, 3),
            "joistLineDesign_kN_m": round(joist_line_design, 3),
            "joistM_kNm": round(joist_moment, 4),
            "joistStress_N_mm2": round(joist_stress, 3),
            "uprightN_kN": round(upright_axial, 3),
            "uprightStress_N_mm2": round(upright_stress, 3),
            "uprightServiceN_kN": round(upright_service_axial, 3),
            "foundationPressure_kPa": round(foundation_pressure, 3),
            "foundationLimit_kPa": round(foundation_limit, 3),
            "couplerDemand_kN": round(coupler_demand, 3),
            "couplerCapacity_kN": round(p["couplerRc"], 3),
            "guardrailConfigurationOk": guardrail_ok,
            "guardrailFailedItems": guardrail_failed,
        },
        "assumptions": [
            "施工平台取 constructionLoad 作为控制活荷载；接料平台取 constructionLoad 与 materialLoad 的较大值，且分别以2.0、3.0kN/m²作为规范限值。",
            "平台板按单位宽度、单跨简支板计算；搁栅按板跨范围受荷、跨度la的单跨简支梁计算。",
            "立杆按la×lb负荷面积承担平台设计荷载，并计入γG·gk·H的架体自重；φ不自动按长细比生成，必须按所采用脚手架规范输入。",
            "地基承载力按标准组合 Nk=(dead+live)·la·lb+gk·H 计算，再以 Nk/baseArea≤kc·fk 验算；baseArea为单根立杆实际传力底面积，不自动考虑相邻立杆应力重叠。",
            "扣件抗滑取水平杆设计线荷载 q= (γG·dead+γQ·live)·panelSpan，并按 N=1.1·q·la 计；1.1为明确输入模型中的荷载影响放大系数，不是JGJ 80-2016规定值。",
            "防护栏杆及连墙构造项仅对用户申报的几何与构造条件作符合性判断，不替代第4.3.4条栏杆1kN外力验算及连墙件承载力计算。",
            "荷载基本组合仅采用γG·Gk+γQ·Qk，未组合风荷载；分项系数可由用户覆盖，但应自行按现行荷载规范确认。",
            "本模块只校核平台板、搁栅、立杆稳定、地基承载力、水平杆扣件抗滑及声明式构造条件；连墙件强度与稳定、连接强度和架体整体分析仍需专项复核。",
            "计算结构标记verified=false，尚未与品茗原计算书样本或完整专项方案逐项对照。",
        ],
    }
