"""扣件式脚手架参数化出图：几何模型 + DXF/PNG 导出。

坐标单位统一为 mm，原点位于架体左下角（平面图为中心对称）。
几何模型与渲染解耦：同一份 layers 既供前端 SVG，也供 DXF/PNG。
"""

from __future__ import annotations

import io
import math
from typing import Any

import ezdxf

COLORS = {
    "upright": "#e5484d",
    "level": "#e5484d",
    "brace": "#3e63dd",
    "dim": "#30a46c",
}

LAYER_NAMES = {
    "upright": "立杆",
    "level": "水平杆",
    "brace": "剪刀撑",
    "dim": "尺寸标注",
}

LAYER_ACI = {"upright": 1, "level": 1, "brace": 5, "dim": 3}


def _line(x1: float, y1: float, x2: float, y2: float) -> dict[str, Any]:
    return {"type": "line", "x1": round(x1, 2), "y1": round(y1, 2), "x2": round(x2, 2), "y2": round(y2, 2)}


def _text(text: str, x: float, y: float, size: float = 180.0, rotation: float = 0.0) -> dict[str, Any]:
    return {"type": "text", "text": text, "x": round(x, 2), "y": round(y, 2), "size": size, "rotation": rotation}


def build_geometry(params: dict[str, Any], view: str = "elevation", bays: int = 6, plan_rows: int = 4) -> dict[str, Any]:
    h = float(params.get("h", 1.8)) * 1000
    la = float(params.get("la", 1.5)) * 1000
    lb = float(params.get("lb", 0.9)) * 1000
    height = float(params.get("H", 24)) * 1000

    if view == "plan":
        return _plan(la, lb, bays, plan_rows)
    if view == "side":
        return _profile(lb, h, height, title=f"侧立面 · 横距 {lb / 1000:.2f}m")
    if view == "section":
        return _profile(lb, h, height, title="剖面 A-A", boards=True)
    return _elevation(h, la, height, bays)


def _dimension_mm(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number <= 0:
        return default
    return number * 1000.0 if number < 100.0 else number


def build_schematic_geometry(
    params: dict[str, Any],
    view: str = "elevation",
    *,
    module_key: str,
    module_title: str,
) -> dict[str, Any]:
    """非脚手架模块的诚实参数化示意图，不冒充专项施工图。"""
    width = _dimension_mm(
        params.get("L")
        or params.get("lengthX")
        or params.get("platformLength")
        or params.get("length")
        or params.get("la"),
        6000.0,
    )
    depth = _dimension_mm(
        params.get("B")
        or params.get("width")
        or params.get("lb"),
        1800.0,
    )
    height = _dimension_mm(
        params.get("H")
        or params.get("High")
        or params.get("platformSpan"),
        3000.0,
    )
    caption = f"{module_title} · 参数化示意（非施工图）"

    if view == "plan":
        frame = [
            _line(0, 0, width, 0),
            _line(width, 0, width, depth),
            _line(width, depth, 0, depth),
            _line(0, depth, 0, 0),
        ]
        members = [
            _line(width / 3, 0, width / 3, depth),
            _line(2 * width / 3, 0, 2 * width / 3, depth),
            _line(0, depth / 2, width, depth / 2),
        ]
        supports = [
            {"type": "circle", "x": x, "y": y, "r": 45.0}
            for x, y in ((0, 0), (width, 0), (0, depth), (width, depth))
        ]
        dim = [
            _line(0, -600, width, -600),
            _line(0, -700, 0, -500),
            _line(width, -700, width, -500),
            _text(f"{width:.0f}", width / 2, -1000, 200),
            _line(-800, 0, -800, depth),
            _text(f"{depth:.0f}", -1100, depth / 2, 190, rotation=90),
            _text(caption, width / 2, depth + 500, 180),
            _text(module_key, width / 2, depth + 850, 130),
        ]
        return _payload("plan", width, depth, {"upright": supports, "level": frame + members, "brace": [], "dim": dim})

    frame = [
        _line(0, 0, width, 0),
        _line(0, 0, 0, height),
        _line(width, 0, width, height),
        _line(0, height, width, height),
    ]
    members = [
        _line(width / 3, 0, width / 3, height),
        _line(2 * width / 3, 0, 2 * width / 3, height),
        _line(0, height / 2, width, height / 2),
    ]
    brace = [_line(0, 0, width / 3, height), _line(width, 0, 2 * width / 3, height)]
    dim = [
        _line(0, -600, width, -600),
        _line(0, -700, 0, -500),
        _line(width, -700, width, -500),
        _text(f"{width:.0f}", width / 2, -1000, 200),
        _line(-800, 0, -800, height),
        _text(f"{height:.0f}", -1100, height / 2, 190, rotation=90),
        _text(caption, width / 2, height + 500, 180),
        _text(module_key, width / 2, height + 850, 130),
    ]
    return _payload(view if view in {"side", "section"} else "elevation", width, height, {"upright": frame, "level": members, "brace": brace, "dim": dim})


def build_geometry_for_module(
    module_key: str,
    module_title: str,
    params: dict[str, Any],
    view: str = "elevation",
) -> dict[str, Any]:
    if module_key in {"scaffold-fastener", "scaffold-fastener-pinming"}:
        return build_geometry(params, view)
    if module_key == "scaffold-tie-member":
        from .drawing_tie_member import build_tie_member_geometry

        return build_tie_member_geometry(params, view)
    if module_key == "full-hall-scaffold":
        from .drawing_scaffold_frames import build_full_hall_geometry

        return build_full_hall_geometry(params, view)
    if module_key == "door-scaffold":
        from .drawing_scaffold_frames import build_door_scaffold_geometry

        return build_door_scaffold_geometry(params, view)
    if module_key == "cantilever-scaffold":
        from .drawing_scaffold_frames import build_cantilever_scaffold_geometry

        return build_cantilever_scaffold_geometry(params, view)
    if module_key == "suspended-basket":
        from .drawing_tool_scaffold import build_suspended_basket_geometry

        return build_suspended_basket_geometry(params, view)
    if module_key == "attached-lifting-scaffold":
        from .drawing_tool_scaffold import build_attached_lifting_geometry

        return build_attached_lifting_geometry(params, view)
    if module_key == "ground-operation-platform":
        from .drawing_operation_platforms import (
            build_ground_operation_platform_geometry,
        )

        return build_ground_operation_platform_geometry(params, view)
    if module_key == "cantilever-operation-platform":
        from .drawing_operation_platforms import (
            build_cantilever_operation_platform_geometry,
        )

        return build_cantilever_operation_platform_geometry(params, view)
    return build_schematic_geometry(
        params,
        view,
        module_key=module_key,
        module_title=module_title,
    )


def _elevation(h: float, la: float, height: float, bays: int) -> dict[str, Any]:
    levels = max(1, math.ceil(height / h))
    width = bays * la
    total_h = height  # 顶层可能是不足一步的实际高度，不用 levels*h

    upright = [_line(i * la, 0, i * la, total_h) for i in range(bays + 1)]
    level_y = [j * h for j in range(levels) if j * h < total_h] + [total_h]
    level = [_line(0, y, width, y) for y in level_y]

    brace: list[dict[str, Any]] = []
    for j in range(levels):
        for b in (0, max(0, bays // 2)):
            y1, y2 = j * h, min((j + 1) * h, total_h)
            if (j + b) % 2 == 0:
                brace.append(_line(b * la, y1, (b + 1) * la, y2))
                brace.append(_line((b + 1) * la, y1, b * la, y2))
            else:
                brace.append(_line(b * la, y1, (b + 1) * la, y2))
                brace.append(_line((b + 1) * la, y1, b * la, y2))

    dim: list[dict[str, Any]] = []
    dim.append(_line(0, -600, width, -600))
    dim.append(_line(0, -700, 0, -500))
    dim.append(_line(width, -700, width, -500))
    dim.append(_text(f"{width:.0f}", width / 2, -1000, 200))
    dim.append(_line(-800, 0, -800, total_h))
    dim.append(_line(-900, 0, -700, 0))
    dim.append(_line(-900, total_h, -700, total_h))
    dim.append(_text(f"{total_h:.0f}", -1200, total_h / 2, 200, rotation=90))
    dim.append(_text("±0.000", -300, -120, 160))
    for i in range(bays + 1):
        dim.append(_line(i * la, -560, i * la, -640))
        dim.append(_text(f"K{i + 1}", i * la, -420, 150))
    dim.append(
        _text(f"步距 {h / 1000:.2f}m · 纵距 {la / 1000:.2f}m · 共 {levels} 步", width / 2, total_h + 400, 170)
    )

    return _payload("elevation", width, total_h, {"upright": upright, "level": level, "brace": brace, "dim": dim})


def _plan(la: float, lb: float, nx: int, ny: int) -> dict[str, Any]:
    width = (nx - 1) * la
    depth = (ny - 1) * lb

    upright = [
        {"type": "circle", "x": round(i * la, 2), "y": round(j * lb, 2), "r": 40.0}
        for i in range(nx)
        for j in range(ny)
    ]
    level = [_line(0, j * lb, width, j * lb) for j in range(ny)] + [
        _line(i * la, 0, i * la, depth) for i in range(nx)
    ]
    brace = []
    for b in range(0, nx - 1, 2):
        brace.append(_line(b * la, 0, (b + 1) * la, lb))
        brace.append(_line((b + 1) * la, 0, b * la, lb))

    dim = [
        _line(0, -600, width, -600),
        _line(0, -700, 0, -500),
        _line(width, -700, width, -500),
        _text(f"{width:.0f}", width / 2, -1000, 200),
        _line(-800, 0, -800, depth),
        _line(-900, 0, -700, 0),
        _line(-900, depth, -700, depth),
        _text(f"{depth:.0f}", -1200, depth / 2, 200, rotation=90),
        _text(f"纵距 {la / 1000:.2f}m · 横距 {lb / 1000:.2f}m", width / 2, depth + 400, 170),
    ]

    return _payload("plan", width, depth, {"upright": upright, "level": level, "brace": brace, "dim": dim})


def _profile(lb: float, h: float, height: float, title: str, boards: bool = False) -> dict[str, Any]:
    """侧立面/剖面：显示脚手架进深方向（横距 lb）。"""
    levels = max(1, math.ceil(height / h))
    total_h = height
    level_y = [j * h for j in range(levels) if j * h < total_h] + [total_h]

    upright = [_line(x, 0, x, total_h) for x in (0.0, lb)]
    level = [_line(0, y, lb, y) for y in level_y]
    if boards:
        level += [_line(0, y - 60, lb, y - 60) for y in level_y[1:]]

    brace = []
    for j in range(levels):
        y1, y2 = j * h, min((j + 1) * h, total_h)
        if j % 2 == 0:
            brace.append(_line(0, y1, lb, y2))
        else:
            brace.append(_line(lb, y1, 0, y2))

    dim = [
        _line(0, -600, lb, -600),
        _line(0, -700, 0, -500),
        _line(lb, -700, lb, -500),
        _text(f"{lb:.0f}", lb / 2, -1000, 190),
        _line(-800, 0, -800, total_h),
        _text(f"{total_h:.0f}", -1100, total_h / 2, 190, rotation=90),
        _text("±0.000", -260, -120, 150),
        _text(title, lb / 2, total_h + 400, 170),
    ]

    return _payload("section" if boards else "side", lb, total_h, {"upright": upright, "level": level, "brace": brace, "dim": dim})


def _payload(view: str, width: float, height: float, layers: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "view": view,
        "units": "mm",
        "bounds": {"minX": -1400.0, "minY": -1200.0, "maxX": round(width + 400, 2), "maxY": round(height + 600, 2)},
        "layers": [
            {
                "id": key,
                "name": LAYER_NAMES[key],
                "color": COLORS[key],
                "items": items,
            }
            for key, items in layers.items()
        ],
    }


def export_dxf(
    params: dict[str, Any],
    view: str = "elevation",
    *,
    module_key: str = "scaffold-fastener",
    module_title: str = "扣件式脚手架",
) -> bytes:
    geometry = build_geometry_for_module(module_key, module_title, params, view)
    doc = ezdxf.new("R2010")
    for key, name in LAYER_NAMES.items():
        if name not in doc.layers:
            doc.layers.add(name, color=LAYER_ACI[key])
    msp = doc.modelspace()

    for layer in geometry["layers"]:
        name = layer["name"]
        for item in layer["items"]:
            if item["type"] == "line":
                msp.add_line((item["x1"], item["y1"]), (item["x2"], item["y2"]), dxfattribs={"layer": name})
            elif item["type"] == "circle":
                msp.add_circle((item["x"], item["y"]), item["r"], dxfattribs={"layer": name})
            elif item["type"] == "text":
                text = msp.add_text(
                    item["text"],
                    height=item.get("size", 180),
                    dxfattribs={"layer": name, "rotation": item.get("rotation", 0)},
                )
                text.set_placement((item["x"], item["y"]))

    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


def export_png(
    params: dict[str, Any],
    view: str = "elevation",
    dpi: int = 144,
    dark: bool = True,
    *,
    module_key: str = "scaffold-fastener",
    module_title: str = "扣件式脚手架",
) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    geometry = build_geometry_for_module(module_key, module_title, params, view)
    bounds = geometry["bounds"]
    width_in = 9.6
    height_in = max(4.2, width_in * (bounds["maxY"] - bounds["minY"]) / max(1e-6, bounds["maxX"] - bounds["minX"]))
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    bg = "#0b0e13" if dark else "#ffffff"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    for layer in geometry["layers"]:
        color = layer["color"]
        for item in layer["items"]:
            if item["type"] == "line":
                ax.plot([item["x1"], item["x2"]], [item["y1"], item["y2"]], color=color, linewidth=1.1)
            elif item["type"] == "circle":
                ax.add_patch(plt.Circle((item["x"], item["y"]), item["r"], color=color))
            elif item["type"] == "text":
                ax.text(
                    item["x"],
                    item["y"],
                    item["text"],
                    color=color,
                    fontsize=max(6, item.get("size", 180) / 28),
                    rotation=item.get("rotation", 0),
                    ha="center",
                    va="center",
                )

    ax.set_xlim(bounds["minX"], bounds["maxX"])
    ax.set_ylim(bounds["minY"], bounds["maxY"])
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0.2)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()
