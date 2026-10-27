"""脚手架通用计算书的内力与变形图。"""

from __future__ import annotations

from typing import Any

from . import charts, drawing


MODULE_TITLES = {
    "scaffold-fastener-pinming": "扣件式脚手架（品茗双立杆）",
    "scaffold-tie-member": "连墙件计算",
    "full-hall-scaffold": "满堂脚手架",
    "door-scaffold": "门式钢管脚手架",
    "cantilever-scaffold": "型钢悬挑脚手架",
    "suspended-basket": "高处作业吊篮",
    "attached-lifting-scaffold": "附着式升降脚手架",
    "ground-operation-platform": "落地式操作平台",
    "cantilever-operation-platform": "悬挑式操作平台",
}


def build_scaffold_figures(
    module_key: str,
    payload: dict[str, Any],
) -> list[tuple[bytes, str]]:
    """返回指定脚手架模块的 PNG 与图题；其他模块返回空列表。"""
    module_title = MODULE_TITLES.get(module_key)
    if module_title is None:
        return []

    params = payload["params"]
    derived = payload["derived"]
    figures: list[tuple[bytes, str]] = []

    def add(png: bytes, detail: str) -> None:
        figures.append((png, f"{module_title}简化计算模型：{detail}"))

    if module_key == "scaffold-fastener-pinming":
        caption = f"{module_title}简化计算模型：纵向水平杆（三跨连续梁）"
        add(
            charts.beam_diagrams(
                derived["qLongDesign_kN_m"],
                params["la"],
                206000.0 * params["sectionInertia"],
                "continuous",
                caption,
                service_q=derived["qLongService_kN_m"],
            ),
            "纵向水平杆（三跨连续梁）",
        )
        caption = (
            f"{module_title}简化计算模型：横向水平杆"
            "（简支梁，P@L/3 + 自重；v 含单样本系数）"
        )
        add(
            charts.simple_beam_point_load_diagrams(
                derived["R_long_kN"],
                derived["qTransDesign_kN_m"],
                params["lb"],
                206000.0 * params["sectionInertia"],
                service_point_load=derived["R_longService_kN"],
                service_q=derived["qTransService_kN_m"],
                deflection_factor=params["pinmingTransverseDeflectionFactor"],
                title=caption,
            ),
            "横向水平杆（简支梁，P@L/3 + 自重；v 含单样本系数）",
        )
        for pole_label, axial_key, moment_key in (
            ("单立杆", "N_no_wind_single_kN", "Mw_single_kNm"),
            ("双立杆", "N_no_wind_double_kN", "Mw_double_kNm"),
        ):
            caption = (
                f"{module_title}简化计算模型：{pole_label}轴力与风弯矩"
            )
            add(
                charts.column_diagrams(
                    derived[axial_key],
                    derived[moment_key],
                    params["H"],
                    caption,
                ),
                f"{pole_label}轴力与风弯矩",
            )
    elif module_key == "scaffold-tie-member":
        add(
            drawing.export_png(
                params,
                "elevation",
                dark=False,
                module_key=module_key,
                module_title=module_title,
            ),
            "正立面连墙件布置",
        )
        add(
            drawing.export_png(
                params,
                "plan",
                dark=False,
                module_key=module_key,
                module_title=module_title,
            ),
            "平面连墙件布置",
        )
    elif module_key == "full-hall-scaffold":
        caption = f"{module_title}简化计算模型：水平杆（三跨连续梁）"
        add(
            charts.beam_diagrams(
                derived["q_ledger_design_kN_m"],
                params["la"],
                params["E"] * params["I_mm4"],
                "continuous",
                caption,
            ),
            "水平杆（三跨连续梁）",
        )
        caption = f"{module_title}简化计算模型：立杆轴力与风弯矩"
        add(
            charts.column_diagrams(
                derived["N_no_wind_kN"],
                derived["Mw_kNm"],
                params["H"],
                caption,
            ),
            "立杆轴力与风弯矩",
        )
    elif module_key == "door-scaffold":
        caption = f"{module_title}简化计算模型：门架横梁（简支梁）"
        add(
            charts.beam_diagrams(
                params["beamQd"],
                params["frameWidth"],
                params["beamE"] * params["beamI"],
                "simple",
                caption,
            ),
            "门架横梁（简支梁）",
        )
        caption = f"{module_title}简化计算模型：立杆轴力与风弯矩"
        add(
            charts.column_diagrams(
                derived["N_ledger_kN"],
                derived["Mwk_kNm"],
                params["H"],
                caption,
            ),
            "立杆轴力与风弯矩",
        )
    elif module_key == "cantilever-scaffold":
        caption = f"{module_title}简化计算模型：悬挑梁"
        add(
            charts.cantilever_beam_diagrams(
                params["q"],
                params["L"],
                params["E"] * params["I_mm4"],
                caption,
            ),
            "悬挑梁",
        )
    elif module_key == "suspended-basket":
        caption = f"{module_title}简化计算模型：平台梁（简支梁）"
        add(
            charts.beam_diagrams(
                derived["beamLineLoad_kN_m"],
                params["platformSpan"],
                params["beamE"] * params["beamI"],
                "simple",
                caption,
            ),
            "平台梁（简支梁）",
        )
    elif module_key == "attached-lifting-scaffold":
        caption = f"{module_title}简化计算模型：主框架立柱轴力与风弯矩"
        add(
            charts.column_diagrams(
                derived["mainFrameDemand_kN"],
                derived["windMoment_kNm"],
                derived["bodyHeight_m"],
                caption,
            ),
            "主框架立柱轴力与风弯矩",
        )
    elif module_key == "ground-operation-platform":
        caption = f"{module_title}简化计算模型：平台板1m带（简支板）"
        add(
            charts.beam_diagrams(
                derived["q_service_kN_m2"],
                params["panelSpan"],
                params["panelE"] * derived["panelI_mm4"],
                "simple",
                caption,
            ),
            "平台板1m带（简支板）",
        )
    elif module_key == "cantilever-operation-platform":
        caption = f"{module_title}简化计算模型：主梁（简支梁）"
        add(
            charts.beam_diagrams(
                derived["designLineLoad_kN_m"],
                derived["mainBeamCalcSpan_m"],
                params["steelE"] * params["mainBeamI"],
                "simple",
                caption,
            ),
            "主梁（简支梁）",
        )

    return figures
