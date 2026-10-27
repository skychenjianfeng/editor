"""脚手架框架体系的参数化几何示意。

本模块只负责满堂脚手架、门式钢管脚手架和型钢悬挑脚手架的二维示意
几何，不参与承载力验算，也不生成施工图。输入长度沿用平台模块参数
的米制单位，输出坐标统一换算为毫米。
"""

from __future__ import annotations

import math
from typing import Any, Iterable

from .drawing import _line, _payload, _text

_VIEWS = {"elevation", "plan", "side", "section"}
_MAX_GRID = 30
_SCHEMATIC_NOTE = "参数化构造示意（非施工图）"


def _safe_value(params: dict[str, Any], key: str, default: float) -> float:
    try:
        value = float((params or {}).get(key, default))
    except (TypeError, ValueError):
        value = default
    if not math.isfinite(value) or value <= 0:
        value = default
    return value


def _mm(params: dict[str, Any], key: str, default: float) -> float:
    """模块参数单位为 m，几何坐标统一为 mm。"""
    return _safe_value(params, key, default) * 1000.0


def _view_name(view: str) -> str:
    return view if view in _VIEWS else "elevation"


def _positions(span: float, spacing: float, max_count: int = _MAX_GRID) -> list[float]:
    """按实际跨度与间距布点，过多时均匀抽稀并保留两端。"""
    span = max(span, 1.0)
    spacing = max(spacing, 1.0)
    raw_count = max(2, math.ceil(span / spacing - 1e-9) + 1)
    if raw_count <= max_count:
        return [min(index * spacing, span) for index in range(raw_count)]
    return [span * index / (max_count - 1) for index in range(max_count)]


def _levels(top: float, step: float, base: float = 0.0, max_count: int = _MAX_GRID) -> list[float]:
    """按实际总高和步距分层，过多时均匀抽稀并保留顶部。"""
    height = max(top - base, 1.0)
    step = max(step, 1.0)
    raw_count = max(2, math.ceil(height / step - 1e-9) + 1)
    if raw_count <= max_count:
        return [base] + [base + min(index * step, height) for index in range(1, raw_count)]
    return [base + height * index / (max_count - 1) for index in range(max_count)]


def _caption(title: str, view_label: str, width: float, height: float) -> dict[str, Any]:
    return _text(
        f"{title} · {view_label} · {_SCHEMATIC_NOTE}",
        width / 2,
        height + 450,
        180,
    )


def _dedupe(values: Iterable[float]) -> list[float]:
    result: list[float] = []
    for value in sorted(values):
        if not result or abs(value - result[-1]) > 1e-6:
            result.append(value)
    return result


def _plan_dimensions(
    width: float,
    depth: float,
    *,
    width_label: str,
    depth_label: str,
    detail: str,
) -> list[dict[str, Any]]:
    return [
        _line(0, -600, width, -600),
        _line(0, -700, 0, -500),
        _line(width, -700, width, -500),
        _text(width_label, width / 2, -950, 190),
        _line(-800, 0, -800, depth),
        _line(-900, 0, -700, 0),
        _line(-900, depth, -700, depth),
        _text(depth_label, -1150, depth / 2, 180, rotation=90),
        _text(detail, width / 2, depth + 160, 160),
    ]


def build_full_hall_geometry(params: dict[str, Any], view: str = "elevation") -> dict[str, Any]:
    """生成满堂脚手架四类二维示意几何。"""
    view = _view_name(view)
    height = _mm(params, "H", 12.0)
    long_spacing = _mm(params, "la", 1.2)
    transverse_spacing = _mm(params, "lb", 1.2)
    step = _mm(params, "h", 1.5)
    length_x = _mm(params, "lengthX", 6.0)
    length_y = _mm(params, "lengthY", 6.0)
    title = "满堂脚手架"

    if view == "plan":
        xs = _positions(length_x, long_spacing)
        ys = _positions(length_y, transverse_spacing)
        upright = [
            {"type": "circle", "x": round(x, 2), "y": round(y, 2), "r": 40.0}
            for x in xs
            for y in ys
        ]
        level = [_line(0, y, length_x, y) for y in ys] + [
            _line(x, 0, x, length_y) for x in xs
        ]
        brace: list[dict[str, Any]] = []
        for index in range(0, len(xs) - 1, 2):
            brace.append(_line(xs[index], 0, xs[index + 1], ys[min(1, len(ys) - 1)]))
        if len(ys) > 1:
            for index in range(0, len(ys) - 1, 2):
                brace.append(_line(0, ys[index], xs[min(1, len(xs) - 1)], ys[index + 1]))
        dim = _plan_dimensions(
            length_x,
            length_y,
            width_label=f"lengthX = {length_x:.0f} mm",
            depth_label=f"lengthY = {length_y:.0f} mm",
            detail=f"平面立杆矩阵 {len(xs)}×{len(ys)} · 纵距 {long_spacing:.0f} mm",
        )
        dim.append(_caption(title, "平面", length_x, length_y))
        return _payload(
            "plan",
            length_x,
            length_y,
            {"upright": upright, "level": level, "brace": brace, "dim": dim},
        )

    if view == "side":
        return _full_hall_profile(
            width=length_y,
            height=height,
            step=step,
            spacing=transverse_spacing,
            title=title,
            view_label="侧立面",
            section=False,
        )

    if view == "section":
        return _full_hall_profile(
            width=length_y,
            height=height,
            step=step,
            spacing=transverse_spacing,
            title=title,
            view_label="剖面 A-A",
            section=True,
        )

    return _full_hall_profile(
        width=length_x,
        height=height,
        step=step,
        spacing=long_spacing,
        title=title,
        view_label="立面",
        section=False,
    )


def _full_hall_profile(
    *,
    width: float,
    height: float,
    step: float,
    spacing: float,
    title: str,
    view_label: str,
    section: bool,
) -> dict[str, Any]:
    if section:
        xs = [0.0, width / 2, width]
    else:
        xs = _positions(width, spacing)
    levels = _levels(height, step)

    upright = [_line(x, 0, x, height) for x in xs]
    level = [_line(0, y, width, y) for y in levels]
    if section:
        level.extend(_line(0, y - 55, width, y - 55) for y in levels[1:])

    brace: list[dict[str, Any]] = []
    for index in range(0, len(xs) - 1, 2):
        brace.append(_line(xs[index], 0, xs[index + 1], levels[-1]))
        brace.append(_line(xs[index + 1], 0, xs[index], levels[-1]))

    dim = [
        _line(0, -600, width, -600),
        _line(0, -700, 0, -500),
        _line(width, -700, width, -500),
        _text(f"{width:.0f} mm", width / 2, -950, 190),
        _line(-800, 0, -800, height),
        _line(-900, 0, -700, 0),
        _line(-900, height, -700, height),
        _text(f"H = {height:.0f} mm", -1150, height / 2, 180, rotation=90),
        _text(f"步距 h = {step:.0f} mm", width / 2, height + 160, 160),
        _caption(title, view_label, width, height),
    ]
    if section:
        dim.append(_text("内部立杆 / 脚手板截面", width / 2, height - 360, 150))

    rendered_view = "section" if section else ("side" if view_label == "侧立面" else "elevation")
    return _payload(
        rendered_view,
        width,
        height,
        {"upright": upright, "level": level, "brace": brace, "dim": dim},
    )


def build_door_scaffold_geometry(params: dict[str, Any], view: str = "elevation") -> dict[str, Any]:
    """生成门式钢管脚手架四类二维示意几何。"""
    view = _view_name(view)
    height = _mm(params, "H", 20.0)
    frame_width = _mm(params, "frameWidth", 1.219)
    frame_bay = _mm(params, "frameBay", 1.8)
    step_height = _mm(params, "stepHeight", 1.93)
    title = "门式钢管脚手架"

    if view == "plan":
        return _door_plan(
            height=height,
            frame_width=frame_width,
            frame_bay=frame_bay,
            step_height=step_height,
            title=title,
        )
    if view == "side":
        return _door_profile(
            height=height,
            frame_width=frame_width,
            frame_bay=frame_bay,
            step_height=step_height,
            title=title,
            section=False,
        )
    if view == "section":
        return _door_profile(
            height=height,
            frame_width=frame_width,
            frame_bay=frame_bay,
            step_height=step_height,
            title=title,
            section=True,
        )
    return _door_elevation(
        height=height,
        frame_width=frame_width,
        frame_bay=frame_bay,
        step_height=step_height,
        title=title,
    )


def _door_frame(
    x0: float,
    y0: float,
    y1: float,
    width: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tier_height = max(y1 - y0, 1.0)
    shoulder = y1 - 0.18 * tier_height
    inset = 0.14 * width
    door_inset = 0.21 * width
    door_head = y1 - 0.26 * tier_height

    upright = [
        _line(x0, y0, x0, shoulder),
        _line(x0 + width, y0, x0 + width, shoulder),
        _line(x0, shoulder, x0 + inset, y1),
        _line(x0 + width, shoulder, x0 + width - inset, y1),
        _line(x0 + door_inset, y0, x0 + door_inset, door_head),
        _line(x0 + width - door_inset, y0, x0 + width - door_inset, door_head),
    ]
    level = [
        _line(x0 + inset, y1, x0 + width - inset, y1),
        _line(x0 + door_inset, door_head, x0 + width - door_inset, door_head),
    ]
    return upright, level


def _door_elevation(
    *,
    height: float,
    frame_width: float,
    frame_bay: float,
    step_height: float,
    title: str,
) -> dict[str, Any]:
    levels = _levels(height, step_height)
    upright: list[dict[str, Any]] = []
    level: list[dict[str, Any]] = []
    brace: list[dict[str, Any]] = []

    for index, (y0, y1) in enumerate(zip(levels, levels[1:])):
        frame_upright, frame_level = _door_frame(0.0, y0, y1, frame_width)
        upright.extend(frame_upright)
        level.extend(frame_level)
        if index % 2 == 0:
            brace.append(_line(0, y0, frame_width * 0.86, y1))
        else:
            brace.append(_line(frame_width * 0.86, y0, 0, y1))

    level.extend(_line(0, y, frame_width, y) for y in levels[1:])
    dim = [
        _line(0, -600, frame_width, -600),
        _line(0, -700, 0, -500),
        _line(frame_width, -700, frame_width, -500),
        _text(f"门架宽度 b = {frame_width:.0f} mm", frame_width / 2, -950, 180),
        _line(-800, 0, -800, height),
        _text(f"H = {height:.0f} mm", -1120, height / 2, 180, rotation=90),
        _text(
            f"门架梯形 / 门洞（示意）· 水平加固杆 @ {step_height:.0f} mm"
            f" · 门架跨距 l = {frame_bay:.0f} mm",
            frame_width / 2,
            height + 160,
            155,
        ),
        _caption(title, "立面", frame_width, height),
    ]
    return _payload(
        "elevation",
        frame_width,
        height,
        {"upright": upright, "level": level, "brace": brace, "dim": dim},
    )


def _door_profile(
    *,
    height: float,
    frame_width: float,
    frame_bay: float,
    step_height: float,
    title: str,
    section: bool,
) -> dict[str, Any]:
    levels = _levels(height, step_height)
    upright = [
        _line(0, 0, 0, height),
        _line(frame_width, 0, frame_width, height),
    ]
    level = [_line(0, y, frame_width, y) for y in levels]
    brace: list[dict[str, Any]] = []
    for index, (y0, y1) in enumerate(zip(levels, levels[1:])):
        if index % 2 == 0:
            brace.append(_line(0, y0, frame_width, y1))
        else:
            brace.append(_line(frame_width, y0, 0, y1))

    if section:
        level.extend(
            {"type": "circle", "x": round(frame_width / 2, 2), "y": round(y, 2), "r": 32.0}
            for y in levels[1:]
        )
        level.extend(_line(0, y - 55, frame_width, y - 55) for y in levels[1:])

    label = "剖面 A-A" if section else "侧立面"
    detail = "剖面显示水平杆截面" if section else "门架宽度方向两立杆"
    dim = [
        _line(0, -600, frame_width, -600),
        _line(0, -700, 0, -500),
        _line(frame_width, -700, frame_width, -500),
        _text(f"门架宽度 b = {frame_width:.0f} mm", frame_width / 2, -950, 180),
        _line(-800, 0, -800, height),
        _text(f"H = {height:.0f} mm", -1120, height / 2, 180, rotation=90),
        _text(
            f"{detail} · 门架跨距 l = {frame_bay:.0f} mm",
            frame_width / 2,
            height + 160,
            150,
        ),
        _caption(title, label, frame_width, height),
    ]
    return _payload(
        "section" if section else "side",
        frame_width,
        height,
        {"upright": upright, "level": level, "brace": brace, "dim": dim},
    )


def _door_plan(
    *,
    height: float,
    frame_width: float,
    frame_bay: float,
    step_height: float,
    title: str,
) -> dict[str, Any]:
    frame_count = 3
    width = (frame_count - 1) * frame_bay
    depth = frame_width
    xs = [index * frame_bay for index in range(frame_count)]

    upright = [
        {"type": "circle", "x": round(x, 2), "y": round(y, 2), "r": 42.0}
        for x in xs
        for y in (0.0, depth)
    ]
    level = [_line(x, 0, x, depth) for x in xs] + [
        _line(0, 0, width, 0),
        _line(0, depth, width, depth),
    ]
    brace = [
        _line(xs[index], 0, xs[index + 1], depth)
        for index in range(len(xs) - 1)
        if index % 2 == 0
    ]
    dim = _plan_dimensions(
        width,
        depth,
        width_label=f"门架跨距 l = {frame_bay:.0f} mm × {frame_count - 1}",
        depth_label=f"门架宽度 b = {frame_width:.0f} mm",
        detail=f"平面门架排布 {frame_count} 榀（示意）· 水平加固杆 @ {step_height:.0f} mm",
    )
    dim.extend(_text(f"M{index + 1}", x, -360, 145) for index, x in enumerate(xs))
    dim.append(_caption(title, "平面", width, depth))
    return _payload(
        "plan",
        width,
        depth,
        {"upright": upright, "level": level, "brace": brace, "dim": dim},
    )


def build_cantilever_scaffold_geometry(
    params: dict[str, Any],
    view: str = "elevation",
) -> dict[str, Any]:
    """生成型钢悬挑脚手架四类二维示意几何。"""
    view = _view_name(view)
    cantilever = _mm(params, "L", 1.5)
    anchor = _mm(params, "armLength", 1.2)
    height = _mm(params, "H", 24.0)
    long_spacing = _mm(params, "la", 1.5)
    transverse_spacing = _mm(params, "lb", 0.9)
    step = _mm(params, "h", 1.8)
    title = "型钢悬挑脚手架"

    if view == "plan":
        return _cantilever_plan(
            cantilever=cantilever,
            anchor=anchor,
            height=height,
            long_spacing=long_spacing,
            transverse_spacing=transverse_spacing,
            step=step,
            title=title,
        )
    if view in {"side", "section"}:
        return _cantilever_profile(
            cantilever=cantilever,
            anchor=anchor,
            height=height,
            transverse_spacing=transverse_spacing,
            step=step,
            title=title,
            section=view == "section",
        )
    return _cantilever_elevation(
        cantilever=cantilever,
        anchor=anchor,
        height=height,
        long_spacing=long_spacing,
        step=step,
        title=title,
    )


def _cantilever_elevation(
    *,
    cantilever: float,
    anchor: float,
    height: float,
    long_spacing: float,
    step: float,
    title: str,
) -> dict[str, Any]:
    total_width = anchor + cantilever
    beam_y = 250.0
    deck_bottom = -180.0
    post_offsets = _positions(cantilever, long_spacing, max_count=_MAX_GRID - 1)
    xs = _dedupe([anchor] + [anchor + offset for offset in post_offsets])
    levels = _levels(height, step, base=beam_y + 80)

    upright = [_line(x, beam_y + 80, x, height) for x in xs]
    level = [
        _line(0, beam_y - 80, total_width, beam_y - 80),
        _line(0, beam_y + 80, total_width, beam_y + 80),
        _line(0, beam_y, total_width, beam_y),
        _line(0, beam_y - 80, 0, beam_y + 80),
        _line(total_width, beam_y - 80, total_width, beam_y + 80),
        _line(0, deck_bottom, anchor + 320, deck_bottom),
        _line(0, 0, anchor + 320, 0),
        _line(anchor, deck_bottom, anchor, min(height, 1200.0)),
    ]
    level.extend(_line(xs[0], y, xs[-1], y) for y in levels[1:])

    brace: list[dict[str, Any]] = []
    for index in range(0, len(xs) - 1, 2):
        brace.append(_line(xs[index], beam_y + 80, xs[index + 1], levels[min(1, len(levels) - 1)]))
        brace.append(_line(xs[index + 1], beam_y + 80, xs[index], levels[min(1, len(levels) - 1)]))

    for x in _dedupe([anchor * 0.28, anchor * 0.68]):
        brace.extend(
            [
                _line(x, deck_bottom, x, beam_y + 170),
                _line(x - 90, beam_y + 170, x + 90, beam_y + 170),
            ]
        )
    brace.append(_line(anchor + cantilever * 0.78, height * 0.48, anchor * 0.32, beam_y + 120))

    dim = [
        _line(0, -650, anchor, -650),
        _line(0, -750, 0, -550),
        _line(anchor, -750, anchor, -550),
        _text(f"armLength = {anchor:.0f} mm", anchor / 2, -980, 180),
        _line(anchor, -650, total_width, -650),
        _line(total_width, -750, total_width, -550),
        _text(f"L = {cantilever:.0f} mm", anchor + cantilever / 2, -980, 190),
        _line(-800, beam_y, -800, height),
        _line(-900, beam_y, -700, beam_y),
        _line(-900, height, -700, height),
        _text(f"H = {height:.0f} mm", -1150, (height + beam_y) / 2, 180, rotation=90),
        _text("室内锚固段", anchor / 2, beam_y + 360, 155),
        _text("楼面/墙边", anchor + 160, 160, 145),
        _text("悬挑工字钢", anchor + cantilever / 2, beam_y - 260, 155),
        _text("斜拉/锚固示意", anchor + cantilever * 0.38, height * 0.55, 145),
        _caption(title, "立面", total_width, height),
    ]
    return _payload(
        "elevation",
        total_width,
        height,
        {"upright": upright, "level": level, "brace": brace, "dim": dim},
    )


def _cantilever_plan(
    *,
    cantilever: float,
    anchor: float,
    height: float,
    long_spacing: float,
    transverse_spacing: float,
    step: float,
    title: str,
) -> dict[str, Any]:
    total_width = anchor + cantilever
    depth = transverse_spacing
    beam_rows = [0.0, depth / 2, depth]
    scaffold_offsets = _positions(cantilever, long_spacing)
    scaffold_xs = [anchor + offset for offset in scaffold_offsets]
    anchor_xs = [anchor * 0.28, anchor * 0.68]

    upright = [
        {"type": "circle", "x": round(x, 2), "y": round(y, 2), "r": 40.0}
        for x in scaffold_xs
        for y in (0.0, depth)
    ]
    upright.extend(
        {"type": "circle", "x": round(x, 2), "y": round(y, 2), "r": 28.0}
        for x in anchor_xs
        for y in beam_rows[1:2]
    )
    level = [_line(0, y, total_width, y) for y in beam_rows]
    level.extend(
        [
            _line(anchor, -250, anchor, depth + 250),
            _line(anchor, 0, total_width, 0),
            _line(anchor, depth, total_width, depth),
        ]
    )
    brace = [
        _line(scaffold_xs[index], 0, scaffold_xs[index + 1], depth)
        for index in range(0, len(scaffold_xs) - 1, 2)
    ]
    dim = _plan_dimensions(
        total_width,
        depth,
        width_label=f"armLength + L = {anchor:.0f} + {cantilever:.0f} mm",
        depth_label=f"lb = {depth:.0f} mm",
        detail=(
            f"悬挑梁与架体条带 · {len(scaffold_xs)} 个横向节点"
            f" · H = {height:.0f} mm · h = {step:.0f} mm"
        ),
    )
    dim.extend(
        [
            _line(0, -350, anchor, -350),
            _text(f"armLength = {anchor:.0f} mm", anchor / 2, -430, 150),
            _line(anchor, -520, total_width, -520),
            _text(f"L = {cantilever:.0f} mm", anchor + cantilever / 2, -520, 155),
            _text("室内锚固", anchor / 2, depth + 320, 145),
            _caption(title, "平面", total_width, depth),
        ]
    )
    return _payload(
        "plan",
        total_width,
        depth,
        {"upright": upright, "level": level, "brace": brace, "dim": dim},
    )


def _cantilever_profile(
    *,
    cantilever: float,
    anchor: float,
    height: float,
    transverse_spacing: float,
    step: float,
    title: str,
    section: bool,
) -> dict[str, Any]:
    width = max(transverse_spacing, 600.0)
    beam_y = 250.0
    post_xs = [0.0, width / 2, width] if section else [0.0, width]
    levels = _levels(height, step, base=beam_y + 80)

    upright = [_line(x, beam_y + 80, x, height) for x in post_xs]
    level = [
        _line(-180, beam_y - 80, width + 180, beam_y - 80),
        _line(-180, beam_y + 80, width + 180, beam_y + 80),
        _line(-180, -180, width + 180, -180),
        _line(-180, 0, width + 180, 0),
    ]
    level.extend(_line(0, y, width, y) for y in levels[1:])
    if section:
        level.extend(_line(0, y - 55, width, y - 55) for y in levels[1:])

    brace = [_line(0, beam_y + 80, width, height * 0.45)]
    if section:
        brace.append(_line(width, beam_y + 80, width / 2, height * 0.60))

    label = "剖面 A-A" if section else "侧立面"
    dim = [
        _line(0, -600, width, -600),
        _text(f"lb = {width:.0f} mm", width / 2, -950, 185),
        _line(-800, beam_y, -800, height),
        _text(f"H = {height:.0f} mm", -1120, (height + beam_y) / 2, 180, rotation=90),
        _text("工字钢及楼面", width / 2, height + 160, 155),
        _text(
            f"L = {cantilever:.0f} mm · armLength = {anchor:.0f} mm"
            " · 内部立杆 / 脚手板截面"
            if section
            else f"L = {cantilever:.0f} mm · armLength = {anchor:.0f} mm",
            width / 2,
            height + 160,
            140,
        ),
        _caption(title, label, width, height),
    ]

    return _payload(
        "section" if section else "side",
        width,
        height,
        {"upright": upright, "level": level, "brace": brace, "dim": dim},
    )
