"""工具式脚手架的参数化构造示意几何。

本模块只生成 Geometry payload，坐标单位统一为 mm。吊篮和附着式升降
脚手架均按参数形成构造示意，不替代专项施工图、节点详图或结构计算。
"""

from __future__ import annotations

import math
from typing import Any

from .drawing import _line, _payload, _text

VIEWS = ("elevation", "plan", "side", "section")
VIEW_LABELS = {
    "elevation": "立面",
    "plan": "平面",
    "side": "侧立面",
    "section": "剖面",
}
NON_CONSTRUCTION_NOTE = "参数化构造示意（非施工图）"


def _number(params: dict[str, Any], key: str, default: float) -> float:
    try:
        value = float(params.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default


def _mm(params: dict[str, Any], key: str, default_mm: float, *, allow_zero: bool = False) -> float:
    """接受输入表单常用的 m，也兼容已经换算为 mm 的正数。"""
    value = _number(params, key, default_mm / 1000.0)
    if value < 0 or (value == 0 and not allow_zero):
        return default_mm
    return value * 1000.0 if 0 < value < 100 else value


def _count(params: dict[str, Any], key: str, default: int, *, at_least: int = 1) -> int:
    value = int(round(_number(params, key, float(default))))
    return max(at_least, value)


def _view(view: str) -> str:
    normalized = str(view).lower()
    return normalized if normalized in VIEWS else "elevation"


def _circle(x: float, y: float, radius: float, role: str) -> dict[str, Any]:
    return {
        "type": "circle",
        "x": round(x, 2),
        "y": round(y, 2),
        "r": radius,
        "role": role,
    }


def _title(module_title: str, view: str) -> str:
    return f"{module_title} · {VIEW_LABELS[view]}{NON_CONSTRUCTION_NOTE}"


def _dimension_line(
    items: list[dict[str, Any]],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    label: str,
    tx: float,
    ty: float,
    *,
    rotation: float = 0.0,
) -> None:
    items.extend(
        [
            _line(x1, y1, x2, y2),
            _text(label, tx, ty, 160, rotation=rotation),
        ]
    )


def build_suspended_basket_geometry(params: dict[str, Any], view: str = "elevation") -> dict[str, Any]:
    """生成高处作业吊篮的四视图构造几何。"""
    p = params or {}
    view = _view(view)
    span = _mm(p, "platformSpan", 6000.0)
    outer = _mm(p, "outerLength", 1500.0)
    inner = _mm(p, "innerLength", 4500.0)
    platform_width = _mm(p, "platformWidth", 800.0)
    wire_count = _count(p, "wireRopeCount", 2, at_least=2)
    counter_weight = _number(p, "counterWeight", 600.0)

    if view == "plan":
        return _suspended_plan(span, platform_width, wire_count, counter_weight)
    if view in {"side", "section"}:
        return _suspended_profile(view, outer, inner, platform_width, wire_count, counter_weight)
    return _suspended_elevation(outer, inner, span, platform_width, wire_count, counter_weight)


def _suspended_elevation(
    outer: float,
    inner: float,
    span: float,
    platform_width: float,
    wire_count: int,
    counter_weight: float,
) -> dict[str, Any]:
    title = _title("高处作业吊篮", "elevation")
    basket_height = max(900.0, min(1300.0, platform_width * 1.35))
    guard_height = 1100.0
    roof_y = basket_height + guard_height + 900.0
    beam_y = roof_y + 220.0
    support_x = inner
    draw_width = max(span, inner + outer)
    support_x = draw_width - outer
    counter_width = max(300.0, min(900.0, support_x * 0.22))

    rope_xs = [
        span * (0.18 + 0.64 * i / max(1, wire_count - 1))
        for i in range(wire_count)
    ]

    upright = [
        _line(0, 0, 0, roof_y),
        _line(span, 0, span, roof_y),
        _line(0, basket_height, 0, basket_height + guard_height),
        _line(span / 2, basket_height, span / 2, basket_height + guard_height),
        _line(span, basket_height, span, basket_height + guard_height),
        _line(support_x, roof_y, support_x, beam_y),
    ]
    # 配重块画在屋面后支架端，与下方吊篮平台保持独立。
    counter_left = 80.0
    counter_right = counter_left + counter_width
    counter_bottom = beam_y
    counter_top = beam_y + max(360.0, min(520.0, counter_width * 0.65))
    upright.extend(
        [
            _line(counter_left, counter_bottom, counter_right, counter_bottom),
            _line(counter_right, counter_bottom, counter_right, counter_top),
            _line(counter_right, counter_top, counter_left, counter_top),
            _line(counter_left, counter_top, counter_left, counter_bottom),
            _line(counter_left + counter_width / 3, counter_bottom, counter_left + counter_width / 3, counter_top),
            _line(counter_left + 2 * counter_width / 3, counter_bottom, counter_left + 2 * counter_width / 3, counter_top),
        ]
    )

    level = [
        _line(0, roof_y, max(span, support_x + outer), roof_y),
        _line(0, beam_y, support_x, beam_y),
        _line(support_x, beam_y, support_x + outer, beam_y),
        _line(0, 0, span, 0),
        _line(0, basket_height, span, basket_height),
        _line(0, basket_height + guard_height, span, basket_height + guard_height),
    ]

    brace = [_line(x, beam_y, x, basket_height + guard_height) for x in rope_xs]
    brace.extend(
        [
            _line(counter_right, beam_y, support_x * 0.55, beam_y),
            _line(support_x, beam_y, support_x + outer * 0.55, roof_y),
        ]
    )

    dim = [
        _text(title, draw_width / 2, beam_y + 760, 190),
        _text("高处作业吊篮", draw_width / 2, beam_y + 520, 165),
        _text(f"配重 {counter_weight:.0f}kg", (counter_left + counter_right) / 2, counter_top + 240, 155),
        _text("屋面/墙边", support_x, roof_y + 170, 155),
        _text(f"工作钢丝绳×{wire_count}", span / 2, basket_height + guard_height + 350, 155),
        _text("吊篮平台", span / 2, basket_height / 2, 155),
        _text("护栏", span * 0.76, basket_height + guard_height + 150, 145),
        _text(f"前支架臂 Lo={outer:.0f}", support_x + outer / 2, beam_y + 180, 145),
        _text(f"后支架臂 Li={inner:.0f}", support_x / 2, beam_y + 180, 145),
    ]
    _dimension_line(dim, 0, -420, span, -420, f"平台跨度 {span:.0f}", span / 2, -760)
    _dimension_line(dim, -620, 0, -620, roof_y, f"悬挂高度 {roof_y:.0f}", -980, roof_y / 2, rotation=90)

    layers = {"upright": upright, "level": level, "brace": brace, "dim": dim}
    return _payload("elevation", draw_width, beam_y + 420, layers)


def _suspended_plan(
    span: float,
    platform_width: float,
    wire_count: int,
    counter_weight: float,
) -> dict[str, Any]:
    title = _title("高处作业吊篮", "plan")
    wall_y = -500.0
    hoist_xs = [span * (0.2 + 0.6 * i / max(1, wire_count - 1)) for i in range(wire_count)]

    upright = [
        _circle(x, platform_width * 0.48, 85.0, "lifting-point")
        for x in hoist_xs
    ]
    upright.extend(
        [
            _line(0, 0, 0, platform_width),
            _line(span, 0, span, platform_width),
        ]
    )
    level = [
        _line(0, 0, span, 0),
        _line(span, 0, span, platform_width),
        _line(span, platform_width, 0, platform_width),
        _line(0, platform_width, 0, 0),
        _line(0, wall_y, span, wall_y),
    ]
    brace = []
    for x in hoist_xs:
        brace.append(_line(x, platform_width + 220, x, platform_width * 0.48))
        brace.append(_line(x, wall_y, x, platform_width + 220))

    dim = [
        _text(title, span / 2, platform_width + 620, 180),
        _text("高处作业吊篮", span / 2, platform_width + 400, 150),
        _text("吊篮平台", span / 2, platform_width / 2, 160),
        _text(f"配重 {counter_weight:.0f}kg（屋面）", span / 2, wall_y - 230, 150),
        _text(f"吊点×{wire_count}", span / 2, platform_width + 260, 145),
        _text("墙边", span * 0.82, wall_y + 100, 140),
    ]
    _dimension_line(dim, 0, -880, span, -880, f"平台长度 {span:.0f}", span / 2, -1080)
    _dimension_line(dim, span + 420, 0, span + 420, platform_width, f"宽度 {platform_width:.0f}", span + 760, platform_width / 2, rotation=90)

    layers = {"upright": upright, "level": level, "brace": brace, "dim": dim}
    return _payload("plan", span, platform_width + 500, layers)


def _suspended_profile(
    view: str,
    outer: float,
    inner: float,
    platform_width: float,
    wire_count: int,
    counter_weight: float,
) -> dict[str, Any]:
    title = _title("高处作业吊篮", view)
    support_x = inner
    width = inner + outer
    basket_height = max(850.0, min(1300.0, platform_width * 1.35))
    guard_height = 1100.0
    roof_y = basket_height + guard_height + 850.0
    beam_y = roof_y + 220.0
    platform_x1 = max(support_x, support_x + outer - platform_width)
    platform_x2 = support_x + outer
    counter_width = max(300.0, min(900.0, inner * 0.22))
    rope_xs = [
        platform_x1 + platform_width * (0.28 + 0.44 * i / max(1, wire_count - 1))
        for i in range(wire_count)
    ]

    upright = [
        _line(0, 0, 0, roof_y),
        _line(support_x, 0, support_x, roof_y),
        _line(support_x, roof_y, support_x, beam_y),
        _line(platform_x1, 0, platform_x1, basket_height),
        _line(platform_x2, 0, platform_x2, basket_height),
        _line(platform_x1, basket_height, platform_x1, basket_height + guard_height),
        _line(platform_x2, basket_height, platform_x2, basket_height + guard_height),
    ]
    counter_top = beam_y + max(360.0, min(520.0, counter_width * 0.65))
    upright.extend(
        [
            _line(60, beam_y, 60 + counter_width, beam_y),
            _line(60 + counter_width, beam_y, 60 + counter_width, counter_top),
            _line(60 + counter_width, counter_top, 60, counter_top),
            _line(60, counter_top, 60, beam_y),
        ]
    )

    level = [
        _line(0, roof_y, support_x, roof_y),
        _line(0, beam_y, support_x, beam_y),
        _line(support_x, beam_y, support_x + outer, beam_y),
        _line(platform_x1, 0, platform_x2, 0),
        _line(platform_x1, basket_height, platform_x2, basket_height),
        _line(platform_x1, basket_height + guard_height, platform_x2, basket_height + guard_height),
    ]
    brace = [_line(x, beam_y, x, basket_height + guard_height) for x in rope_xs]
    brace.append(_line(0, beam_y, support_x * 0.55, roof_y))

    if view == "section":
        level.extend(
            [
                _line(platform_x1, basket_height - 90, platform_x2, basket_height - 90),
                _line(platform_x1 + 80, 80, platform_x1 + 80, basket_height - 90),
                _line(platform_x2 - 80, 80, platform_x2 - 80, basket_height - 90),
            ]
        )

    dim = [
        _text(title, width / 2, beam_y + 760, 185),
        _text("高处作业吊篮", width / 2, beam_y + 520, 150),
        _text("建筑墙体", support_x / 2, roof_y - 380, 155),
        _text("屋面/墙边", support_x, roof_y + 160, 150),
        _text("配重", 60 + counter_width / 2, counter_top + 230, 150),
        _text(f"{counter_weight:.0f}kg", 60 + counter_width / 2, counter_top + 70, 135),
        _text("悬挂臂", (support_x + platform_x2) / 2, beam_y + 160, 145),
        _text(f"工作钢丝绳×{wire_count}", (platform_x1 + platform_x2) / 2, basket_height + guard_height + 330, 145),
        _text("吊篮平台宽度", (platform_x1 + platform_x2) / 2, -320, 145),
    ]
    _dimension_line(dim, platform_x1, -420, platform_x2, -420, f"宽度 {platform_width:.0f}", (platform_x1 + platform_x2) / 2, -760)
    _dimension_line(dim, support_x, -420, support_x + outer, -420, f"Lo={outer:.0f}", support_x + outer / 2, -1080)
    _dimension_line(dim, 0, beam_y + 100, support_x, beam_y + 100, f"Li={inner:.0f}", support_x / 2, beam_y + 390)

    layers = {"upright": upright, "level": level, "brace": brace, "dim": dim}
    return _payload(view, width, beam_y + 420, layers)


def build_attached_lifting_geometry(params: dict[str, Any], view: str = "elevation") -> dict[str, Any]:
    """生成附着式升降脚手架的四视图构造几何。"""
    p = params or {}
    view = _view(view)
    building_height = _mm(p, "H", 65000.0)
    storey_height = _mm(p, "storeyHeight", 3600.0)
    step_height = _mm(p, "h", 1800.0)
    span = _mm(p, "la", 1500.0)
    width_depth = _mm(p, "lb", 800.0)
    steps = _count(p, "n", 8)
    points = _count(p, "k", 4)
    overhang = _mm(p, "overhang", 300.0, allow_zero=True)
    cantilever_height = _mm(p, "cantileverHeight", 3600.0, allow_zero=True)
    body_height = steps * step_height
    frame_width = max(span, (points - 1) * span)
    building_width = frame_width + 2 * overhang
    total_height = max(building_height, body_height + cantilever_height + storey_height)

    if view == "plan":
        return _attached_plan(frame_width, width_depth, span, points, overhang)
    if view in {"side", "section"}:
        return _attached_profile(
            view,
            body_height,
            cantilever_height,
            step_height,
            width_depth,
            overhang,
            total_height,
        )
    return _attached_elevation(
        total_height,
        body_height,
        cantilever_height,
        storey_height,
        step_height,
        span,
        width_depth,
        frame_width,
        building_width,
        points,
        steps,
        overhang,
    )


def _machine_positions(x0: float, width: float, points: int) -> list[float]:
    if points == 1:
        return [x0 + width / 2]
    return [x0 + width * i / (points - 1) for i in range(points)]


def _attached_elevation(
    total_height: float,
    body_height: float,
    cantilever_height: float,
    storey_height: float,
    step_height: float,
    span: float,
    width_depth: float,
    frame_width: float,
    building_width: float,
    points: int,
    steps: int,
    overhang: float,
) -> dict[str, Any]:
    title = _title("附着式升降脚手架", "elevation")
    x0 = overhang
    x1 = x0 + frame_width
    machine_xs = _machine_positions(x0, frame_width, points)
    support_y = max(step_height, body_height - step_height * 1.5)
    top_guard_y = body_height + min(650.0, max(300.0, step_height * 0.35))

    upright = [
        _line(0, 0, 0, total_height),
        _line(building_width, 0, building_width, total_height),
        _line(x0, 0, x0, body_height),
        _line(x1, 0, x1, body_height),
    ]
    upright.extend(_line(x, 0, x, body_height) for x in machine_xs[1:-1])
    upright.extend(_circle(x, body_height - step_height * 0.35, 70.0, "machine") for x in machine_xs)
    upright.extend(
        [
            _line(x0, body_height, x0, body_height + cantilever_height),
            _line(x1, body_height, x1, body_height + cantilever_height),
        ]
    )

    level: list[dict[str, Any]] = []
    floors = int(math.floor(total_height / storey_height)) + 1
    level.extend(_line(0, min(i * storey_height, total_height), building_width, min(i * storey_height, total_height)) for i in range(floors))
    level.append(_line(0, total_height, building_width, total_height))
    level.extend(_line(x0, i * step_height, x1, i * step_height) for i in range(steps + 1))
    level.extend(
        [
            _line(x0 - 120, 120, x1 + 120, 120),
            _line(x0 - 120, top_guard_y, x1 + 120, top_guard_y),
            _line(x0 - 120, body_height + cantilever_height, x1 + 120, body_height + cantilever_height),
        ]
    )

    brace: list[dict[str, Any]] = []
    for bay in range(max(0, points - 1)):
        left = machine_xs[bay]
        right = machine_xs[bay + 1]
        for step in range(steps):
            y1 = step * step_height
            y2 = (step + 1) * step_height
            if (bay + step) % 2:
                brace.append(_line(left, y1, right, y2))
            else:
                brace.append(_line(right, y1, left, y2))
    brace.extend(_circle(x, support_y, 65.0, "wall-support") for x in machine_xs)
    brace.extend(
        [
            _line(x - 150, support_y - 70, x + 150, support_y - 70) for x in machine_xs
        ]
    )

    dim = [
        _text(title, building_width / 2, total_height + 760, 190),
        _text("附着式升降脚手架", building_width / 2, total_height + 500, 150),
        _text(f"提升机位/防坠点×{points}", building_width / 2, body_height + 260, 150),
        _text(f"附墙支座×{points}", building_width / 2, support_y + 260, 145),
        _text("顶部防护", x1 + 380, top_guard_y + 160, 140),
        _text("底部防护", x0 - 320, 240, 140),
        _text(f"架体高 {body_height:.0f}", x0 - 420, body_height / 2, 145, rotation=90),
        _text(f"悬臂 {cantilever_height:.0f}", x1 + 360, body_height + cantilever_height / 2, 135, rotation=90),
        _text(f"机位间距 la={span:.0f}", (x0 + x1) / 2, -180, 145),
        _text(f"架体宽 lb={width_depth:.0f}", building_width / 2, 80, 135),
    ]
    _dimension_line(dim, -650, 0, -650, total_height, f"建筑 H={total_height:.0f}", -980, total_height / 2, rotation=90)

    layers = {"upright": upright, "level": level, "brace": brace, "dim": dim}
    return _payload("elevation", building_width, total_height + 300, layers)


def _attached_plan(
    frame_width: float,
    width_depth: float,
    span: float,
    points: int,
    overhang: float,
) -> dict[str, Any]:
    title = _title("附着式升降脚手架", "plan")
    machine_xs = _machine_positions(0, frame_width, points)
    wall_y = -max(220.0, overhang)

    upright = [_circle(x, width_depth * 0.35, 72.0, "machine") for x in machine_xs]
    upright.extend(_circle(x, wall_y, 55.0, "wall-support") for x in machine_xs)
    upright.extend(
        [
            _line(0, 0, 0, width_depth),
            _line(frame_width, 0, frame_width, width_depth),
        ]
    )
    level = [
        _line(0, 0, frame_width, 0),
        _line(frame_width, 0, frame_width, width_depth),
        _line(frame_width, width_depth, 0, width_depth),
        _line(0, width_depth, 0, 0),
        _line(0, wall_y, frame_width, wall_y),
    ]
    brace: list[dict[str, Any]] = []
    for left, right in zip(machine_xs, machine_xs[1:]):
        brace.extend(
            [
                _line(left, 0, right, width_depth),
                _line(right, 0, left, width_depth),
                _line(left, 0, left, wall_y),
                _line(right, 0, right, wall_y),
            ]
        )

    dim = [
        _text(title, frame_width / 2, width_depth + 640, 185),
        _text("附着式升降脚手架", frame_width / 2, width_depth + 400, 150),
        _text(f"架体条带 · 机位×{points} · 支座×{points}", frame_width / 2, width_depth / 2, 145),
        _text("建筑内侧", frame_width / 2, wall_y + 130, 135),
        _text("架体外侧", frame_width / 2, width_depth - 130, 135),
        _text(f"机位间距 la={span:.0f}", frame_width / 2, -700, 145),
    ]
    _dimension_line(dim, 0, -900, frame_width, -900, f"架体长度 {frame_width:.0f}", frame_width / 2, -1080)
    _dimension_line(dim, frame_width + 380, 0, frame_width + 380, width_depth, f"架体宽度 {width_depth:.0f}", frame_width + 720, width_depth / 2, rotation=90)

    layers = {"upright": upright, "level": level, "brace": brace, "dim": dim}
    return _payload("plan", frame_width, width_depth + 500, layers)


def _attached_profile(
    view: str,
    body_height: float,
    cantilever_height: float,
    step_height: float,
    width_depth: float,
    overhang: float,
    total_height: float,
) -> dict[str, Any]:
    title = _title("附着式升降脚手架", view)
    wall_x = 0.0
    inner_x = overhang
    outer_x = overhang + width_depth
    frame_top = body_height + cantilever_height
    support_ys = [
        max(step_height, body_height - step_height * 1.5),
        max(step_height, body_height - step_height * 3.5),
    ]
    if body_height <= step_height * 2:
        support_ys = [body_height]

    upright = [
        _line(wall_x, 0, wall_x, total_height),
        _line(inner_x, 0, inner_x, body_height),
        _line(outer_x, 0, outer_x, frame_top),
    ]
    upright.extend(_line(inner_x, y, outer_x, y) for y in support_ys)
    upright.extend(
        [
            _line(wall_x, min(support_ys), inner_x, min(support_ys)),
            _line(wall_x, max(support_ys), inner_x, max(support_ys)),
        ]
    )

    level: list[dict[str, Any]] = []
    levels = max(1, int(round(body_height / step_height)))
    level.extend(_line(inner_x, i * step_height, outer_x, i * step_height) for i in range(levels + 1))
    level.extend(
        [
            _line(wall_x, 120, inner_x, 120),
            _line(wall_x, frame_top, outer_x, frame_top),
        ]
    )
    if view == "section":
        level.extend(_line(inner_x + 70, i * step_height - 70, outer_x - 70, i * step_height - 70) for i in range(1, levels + 1))

    brace = []
    for i in range(levels):
        y1 = i * step_height
        y2 = min((i + 1) * step_height, body_height)
        if i % 2:
            brace.append(_line(inner_x, y1, outer_x, y2))
        else:
            brace.append(_line(outer_x, y1, inner_x, y2))
    brace.extend(_circle(inner_x, y, 55.0, "wall-support") for y in support_ys)

    dim = [
        _text(title, (wall_x + outer_x) / 2, frame_top + 760, 180),
        _text("附着式升降脚手架", (wall_x + outer_x) / 2, frame_top + 500, 145),
        _text("建筑内侧", wall_x + 200, min(total_height * 0.55, frame_top + 600), 140, rotation=90),
        _text("架体外侧", outer_x + 260, max(800, frame_top * 0.65), 140, rotation=90),
        _text("附墙支座", inner_x / 2, max(support_ys) + 220, 135),
        _text("底部防护", inner_x + 120, 260, 135),
        _text("顶部防护", outer_x - 120, frame_top + 180, 135),
    ]
    _dimension_line(dim, -520, 0, -520, total_height, f"建筑 H={total_height:.0f}", -850, total_height / 2, rotation=90)
    _dimension_line(dim, inner_x, -420, outer_x, -420, f"架体宽 lb={width_depth:.0f}", (inner_x + outer_x) / 2, -760)
    _dimension_line(dim, 0, -420, inner_x, -420, f"离墙悬挑 {overhang:.0f}", inner_x / 2, -1080)
    _dimension_line(dim, outer_x + 300, body_height, outer_x + 300, frame_top, f"悬臂 {cantilever_height:.0f}", outer_x + 640, (body_height + frame_top) / 2, rotation=90)

    layers = {"upright": upright, "level": level, "brace": brace, "dim": dim}
    return _payload(view, outer_x, frame_top + 420, layers)
