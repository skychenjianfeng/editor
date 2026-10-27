"""落地式与悬挑式操作平台参数化构造示意。

本模块只生成几何数据，不参与承载力计算。坐标单位统一为 mm；输入尺寸
如按既有计算模块以 m 传入，会自动换算为 mm。
"""

from __future__ import annotations

import math
from typing import Any

from calc_core.drawing import _line, _payload, _text

GROUND_MODULE_KEY = "ground-operation-platform"
GROUND_MODULE_NAME = "落地式操作平台"
CANTILEVER_MODULE_KEY = "cantilever-operation-platform"
CANTILEVER_MODULE_NAME = "悬挑式操作平台"
SCHEMATIC_NOTE = "参数化构造示意（非施工图）"
VALID_VIEWS = {"elevation", "plan", "side", "section"}


def _mm(value: Any, default: float) -> float:
    """把 m 或 mm 输入统一为 mm。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number <= 0:
        return default
    return number * 1000.0 if number < 100.0 else number


def _spacing_mm(value: Any, default: float) -> float:
    return _mm(value, default)


def _positions(total: float, spacing: float) -> list[float]:
    spacing = max(spacing, 1.0)
    result = [0.0]
    cursor = spacing
    while cursor < total - 0.01:
        result.append(cursor)
        cursor += spacing
    if abs(result[-1] - total) > 0.01:
        result.append(total)
    return result


def _title_texts(title: str, width: float, base_y: float) -> list[dict[str, Any]]:
    return [
        _text(f"{title} · {SCHEMATIC_NOTE}", width / 2, base_y + 180, 190),
        _text(
            GROUND_MODULE_KEY if title.startswith(GROUND_MODULE_NAME) else CANTILEVER_MODULE_KEY,
            width / 2,
            base_y + 390,
            130,
        ),
        _text(SCHEMATIC_NOTE, width / 2, base_y + 570, 145),
    ]


def _ground_values(params: dict[str, Any]) -> dict[str, Any]:
    kind = str(params.get("platformKind") or "施工平台")
    return {
        "platformKind": kind,
        "length": _mm(params.get("length"), 3000.0),
        "width": _mm(params.get("width"), 3000.0),
        "H": _mm(params.get("H"), 4000.0),
        "la": _spacing_mm(params.get("la"), 900.0),
        "lb": _spacing_mm(params.get("lb"), 900.0),
        "h": _spacing_mm(params.get("h"), 1500.0),
    }


def _ground_module_texts(kind: str, view_title: str, width: float, base_y: float) -> list[dict[str, Any]]:
    return _title_texts(f"{GROUND_MODULE_NAME} · {kind} · {view_title}", width, base_y)


def _ground_plan(values: dict[str, Any]) -> dict[str, Any]:
    length = values["length"]
    width = values["width"]
    xs = _positions(length, values["la"])
    ys = _positions(width, values["lb"])
    kind = values["platformKind"]

    outline = [
        _line(0, 0, length, 0),
        _line(length, 0, length, width),
        _line(length, width, 0, width),
        _line(0, width, 0, 0),
    ]
    grid = [_line(x, 0, x, width) for x in xs] + [_line(0, y, length, y) for y in ys]

    opening_width = min(1200.0, length * 0.28)
    opening_left = length / 2 - opening_width / 2
    opening_right = length / 2 + opening_width / 2
    guardrail_y = max(0.0, width - 75.0)
    guardrails = [
        _line(0, guardrail_y, opening_left, guardrail_y),
        _line(opening_right, guardrail_y, length, guardrail_y),
        _line(0, 75, 0, guardrail_y),
        _line(length, 75, length, guardrail_y),
        _line(0, 0, 0, 75),
        _line(length, 0, length, 75),
    ]

    uprights = [
        {"type": "circle", "x": round(x, 2), "y": round(y, 2), "r": 42.0}
        for y in ys
        for x in xs
    ]

    braces: list[dict[str, Any]] = []
    for row, (y1, y2) in enumerate(zip(ys, ys[1:])):
        for col, (x1, x2) in enumerate(zip(xs, xs[1:])):
            if (row + col) % 2 == 0:
                braces.append(_line(x1, y1, x2, y2))
            else:
                braces.append(_line(x2, y1, x1, y2))

    dim = [
        _line(0, -600, length, -600),
        _line(0, -700, 0, -500),
        _line(length, -700, length, -500),
        _text(f"长 {length:.0f} mm", length / 2, -950, 180),
        _line(-800, 0, -800, width),
        _line(-900, 0, -700, 0),
        _line(-900, width, -700, width),
        _text(f"宽 {width:.0f} mm", -1080, width / 2, 180, rotation=90),
        _text("立杆网格（圆点为立杆）", length / 2, width + 170, 150),
        _text("防护栏杆（上人/卸料开口）", length / 2, guardrail_y - 165, 150),
        _text("连墙/刚性连接（示意）", length * 0.22, 260, 140),
        _text(f"la={values['la']:.0f} mm · lb={values['lb']:.0f} mm", length / 2, -160, 145),
    ]
    dim += _ground_module_texts(kind, "平面", length, width + 330)

    return _payload(
        "plan",
        length,
        width + 1000,
        {
            "upright": uprights,
            "level": outline + grid + guardrails,
            "brace": braces,
            "dim": dim,
        },
    )


def _ground_elevation(values: dict[str, Any]) -> dict[str, Any]:
    length = values["length"]
    height = values["H"]
    xs = _positions(length, values["la"])
    step = values["h"]
    kind = values["platformKind"]
    rail_height = 1050.0

    uprights = [_line(x, 0, x, height) for x in xs]
    for x in (0.0, length):
        uprights.append(_line(x, height + 120, x, height + rail_height))

    levels: list[dict[str, Any]] = []
    y = step
    while y < height - 1.0:
        levels.append(_line(0, y, length, y))
        y += step
    levels.extend(
        [
            _line(0, height - 110, length, height - 110),
            _line(0, height, length, height),
            _line(0, height + 120, length, height + 120),
            _line(0, height + 500, length, height + 500),
            _line(0, height + 1000, length, height + 1000),
            _line(0, height + 580, -300, height + 580),
            _line(length, height + 580, length + 300, height + 580),
        ]
    )

    braces: list[dict[str, Any]] = []
    level_y = [0.0]
    y = step
    while y < height - 1.0:
        level_y.append(y)
        y += step
    level_y.append(height)
    for index, (x1, x2) in enumerate(zip(xs, xs[1:])):
        for row, (y1, y2) in enumerate(zip(level_y, level_y[1:])):
            if index in {0, len(xs) - 2}:
                if (index + row) % 2 == 0:
                    braces.append(_line(x1, y1, x2, y2))
                else:
                    braces.append(_line(x2, y1, x1, y2))

    dim = [
        _line(0, -600, length, -600),
        _line(0, -700, 0, -500),
        _line(length, -700, length, -500),
        _text(f"长 {length:.0f} mm", length / 2, -950, 180),
        _line(-850, 0, -850, height),
        _line(-950, 0, -750, 0),
        _line(-950, height, -750, height),
        _text(f"H={height:.0f} mm", -1120, height / 2, 180, rotation=90),
        _text(f"步距 h={step:.0f} mm · 纵距 la={values['la']:.0f} mm", length / 2, height + 1250, 155),
        _text("平台板", length * 0.70, height + 220, 150),
        _text("防护栏杆", length * 0.72, height + 820, 150),
        _text("连墙/刚性连接", -160, height + 660, 135),
    ]
    dim += _ground_module_texts(kind, "立面", length, height + 1390)

    return _payload(
        "elevation",
        length,
        height + 2000,
        {
            "upright": uprights,
            "level": levels,
            "brace": braces,
            "dim": dim,
        },
    )


def _ground_profile(values: dict[str, Any], view: str) -> dict[str, Any]:
    width = values["width"]
    height = values["H"]
    ys = _positions(width, values["lb"])
    step = values["h"]
    kind = values["platformKind"]
    is_section = view == "section"
    title = "剖面 A-A（横向）" if is_section else "侧立面（横距方向）"

    uprights = [_line(y, 0, y, height) for y in ys]
    uprights.extend(
        [
            _line(0, height + 120, 0, height + 1050),
            _line(width, height + 120, width, height + 1050),
        ]
    )

    levels: list[dict[str, Any]] = []
    y = step
    while y < height - 1.0:
        levels.append(_line(0, y, width, y))
        y += step
    levels.extend(
        [
            _line(0, height - 110, width, height - 110),
            _line(0, height, width, height),
            _line(0, height + 120, width, height + 120),
            _line(0, height + 500, width, height + 500),
            _line(0, height + 1000, width, height + 1000),
            _line(width, height + 570, width + 320, height + 570),
        ]
    )

    braces: list[dict[str, Any]] = []
    level_y = [0.0]
    y = step
    while y < height - 1.0:
        level_y.append(y)
        y += step
    level_y.append(height)
    for row, (y1, y2) in enumerate(zip(level_y, level_y[1:])):
        if row % 2 == 0:
            braces.append(_line(0, y1, width, y2))
        else:
            braces.append(_line(width, y1, 0, y2))

    if is_section:
        levels.extend(_line(0, height - 70 + index * 14, 420, height - 70 + index * 14) for index in range(6))
        uprights.append({"type": "circle", "x": round(width / 2, 2), "y": round(height + 60, 2), "r": 55.0})

    dim = [
        _line(0, -600, width, -600),
        _line(0, -700, 0, -500),
        _line(width, -700, width, -500),
        _text(f"宽 {width:.0f} mm", width / 2, -950, 180),
        _line(-850, 0, -850, height),
        _line(-950, 0, -750, 0),
        _line(-950, height, -750, height),
        _text(f"H={height:.0f} mm", -1120, height / 2, 180, rotation=90),
        _text(f"横距 lb={values['lb']:.0f} mm · 步距 h={step:.0f} mm", width / 2, -160, 145),
        _text("平台板", width * 0.66, height + 220, 150),
        _text("防护栏杆", width * 0.66, height + 820, 150),
        _text("连墙/刚性连接", width + 380, height + 620, 135),
    ]
    if is_section:
        dim.append(_text("平台板剖面/主梁断点", width * 0.55, height - 220, 140))
    dim += _ground_module_texts(kind, title, width, height + 1390)

    return _payload(
        view,
        width,
        height + 2000,
        {
            "upright": uprights,
            "level": levels,
            "brace": braces,
            "dim": dim,
        },
    )


def build_ground_operation_platform_geometry(params: dict[str, Any], view: str = "elevation") -> dict[str, Any]:
    """生成落地式操作平台四视图 Geometry payload。"""
    values = _ground_values(params or {})
    selected = view if view in VALID_VIEWS else "elevation"
    if selected == "plan":
        return _ground_plan(values)
    if selected in {"side", "section"}:
        return _ground_profile(values, selected)
    return _ground_elevation(values)


def _cantilever_values(params: dict[str, Any]) -> dict[str, Any]:
    try:
        side_count = int(round(float(params.get("sideCount", 2))))
    except (TypeError, ValueError):
        side_count = 2
    side_count = min(4, max(1, side_count))
    return {
        "platformLength": _mm(params.get("platformLength"), 3900.0),
        "overhangLength": _mm(params.get("overhangLength"), 3500.0),
        "anchorLength": _mm(params.get("anchorLength"), 1500.0),
        "frontRopeDistance": _mm(params.get("frontRopeDistance"), 3500.0),
        "rearRopeDistance": _mm(params.get("rearRopeDistance"), 2000.0),
        "frontRopeAngle": float(params.get("frontRopeAngle", 55.0) or 55.0),
        "rearRopeAngle": float(params.get("rearRopeAngle", 55.0) or 55.0),
        "sideCount": side_count,
    }


def _cantilever_module_texts(title: str, width: float, base_y: float) -> list[dict[str, Any]]:
    return _title_texts(f"{CANTILEVER_MODULE_NAME} · {title}", width, base_y)


def _cantilever_plan(values: dict[str, Any]) -> dict[str, Any]:
    length = values["platformLength"]
    anchor = values["anchorLength"]
    overhang = values["overhangLength"]
    wall_y = anchor
    outer_y = anchor + overhang
    main_x = [length * 0.18, length * 0.82]

    wall = [_line(0, wall_y, length, wall_y)]
    platform_outline = [
        _line(0, wall_y, length, wall_y),
        _line(length, wall_y, length, outer_y),
        _line(length, outer_y, 0, outer_y),
        _line(0, outer_y, 0, wall_y),
    ]
    indoor_anchor_area = [
        _line(0, 0, length, 0),
        _line(0, 0, 0, wall_y),
        _line(length, 0, length, wall_y),
    ]
    main_beams = [_line(x, 0, x, outer_y) for x in main_x]
    secondary_y = [wall_y, wall_y + overhang / 3, wall_y + 2 * overhang / 3, outer_y]
    secondary_beams = [_line(main_x[0], y, main_x[1], y) for y in secondary_y]
    guardrail = [
        _line(0, outer_y - 80, length, outer_y - 80),
        _line(0, outer_y - 450, length, outer_y - 450),
    ]

    anchors = [
        {"type": "circle", "x": round(x, 2), "y": round(y, 2), "r": 52.0}
        for x in main_x
        for y in (anchor * 0.18, anchor * 0.68)
    ]
    rope_marks = [
        {"type": "circle", "x": round(x, 2), "y": round(wall_y + min(values["frontRopeDistance"], overhang * 0.92), 2), "r": 38.0}
        for x in main_x
    ]
    rope_marks += [
        {"type": "circle", "x": round(x, 2), "y": round(wall_y + min(values["rearRopeDistance"], overhang * 0.82), 2), "r": 38.0}
        for x in main_x
    ]

    braces = [
        _line(main_x[0], wall_y, main_x[1], outer_y),
        _line(main_x[1], wall_y, main_x[0], outer_y),
        _line(main_x[0], 0, main_x[1], wall_y * 0.7),
        _line(main_x[1], 0, main_x[0], wall_y * 0.7),
    ]

    dim = [
        _line(0, -600, length, -600),
        _line(0, -700, 0, -500),
        _line(length, -700, length, -500),
        _text(f"平台沿边长 {length:.0f} mm", length / 2, -950, 180),
        _line(-750, 0, -750, outer_y),
        _text(f"锚固段 {anchor:.0f} mm", -1050, wall_y / 2, 165, rotation=90),
        _text(f"悬挑段 {overhang:.0f} mm", -1050, wall_y + overhang / 2, 165, rotation=90),
        _text("建筑墙边", length * 0.72, wall_y + 150, 150),
        _text("双主梁（2根）", length * 0.50, wall_y + overhang * 0.48, 155),
        _text("次梁", length * 0.30, wall_y + overhang / 3 + 120, 145),
        _text("室内锚固段", length * 0.50, anchor * 0.48, 155),
        _text("锚点（室内连接件）", length * 0.50, anchor * 0.82, 150),
        _text("前/后道钢丝绳吊点", length * 0.50, outer_y * 0.87, 145),
        _text("沿平台外缘设防护栏杆", length * 0.50, outer_y + 160, 145),
        _text(f"斜拉绳侧数 {values['sideCount']}", length * 0.18, anchor * 0.18 - 160, 140),
    ]
    dim += _cantilever_module_texts("平面", length, outer_y + 330)

    return _payload(
        "plan",
        length,
        outer_y + 1000,
        {
            "upright": anchors + rope_marks,
            "level": outline_items(wall + platform_outline + indoor_anchor_area + main_beams + secondary_beams + guardrail),
            "brace": braces,
            "dim": dim,
        },
    )


def outline_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """保留 line/circle 项并去除完全重复的线段。"""
    result: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for item in items:
        key = tuple(sorted(item.items()))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _cantilever_profile(values: dict[str, Any], view: str) -> dict[str, Any]:
    anchor = values["anchorLength"]
    overhang = values["overhangLength"]
    wall_x = anchor
    outer_x = anchor + overhang
    is_section = view == "section"
    title = "剖面 A-A（悬挑方向）" if is_section else "立面（悬挑方向）"

    inner_deck_y = 900.0
    slope = max(80.0, min(260.0, overhang * 0.045))
    outer_deck_y = inner_deck_y + slope
    beam_start_y = 520.0
    beam_wall_y = 600.0
    beam_outer_y = outer_deck_y - 85.0

    def deck_y_at(x: float) -> float:
        ratio = (x - wall_x) / max(overhang, 1.0)
        return inner_deck_y + slope * min(1.0, max(0.0, ratio))

    front_distance = min(max(values["frontRopeDistance"], 100.0), overhang * 0.95)
    rear_distance = min(max(values["rearRopeDistance"], 100.0), overhang * 0.85)
    if abs(front_distance - rear_distance) < 80.0:
        front_distance = min(overhang * 0.95, rear_distance + max(180.0, overhang * 0.15))

    rope_ends: list[tuple[float, float, str]] = []
    for distance, angle, label in (
        (rear_distance, values["rearRopeAngle"], "后道钢丝绳"),
        (front_distance, values["frontRopeAngle"], "前道钢丝绳"),
    ):
        attach_x = wall_x + distance
        attach_y = deck_y_at(attach_x) + 55.0
        top_y = attach_y + distance * math.tan(math.radians(min(85.0, max(20.0, angle))))
        rope_ends.append((attach_x, attach_y, label, top_y))

    topmost = max(item[3] for item in rope_ends)
    total_height = max(topmost, outer_deck_y + 1100.0) + 550.0

    uprights = [
        _line(wall_x, 0, wall_x, total_height - 250),
        _line(outer_x, outer_deck_y, outer_x, outer_deck_y + 1000),
        _line(outer_x, outer_deck_y + 980, outer_x + 40, outer_deck_y + 980),
        {"type": "circle", "x": round(anchor * 0.18, 2), "y": round(beam_start_y, 2), "r": 52.0},
        {"type": "circle", "x": round(anchor * 0.68, 2), "y": round(beam_start_y, 2), "r": 52.0},
    ]
    for index in range(8):
        y = 180.0 + index * 170.0
        if y < total_height - 350:
            uprights.append(_line(wall_x - 90, y, wall_x + 90, y + 100))

    levels = [
        _line(0, beam_start_y, wall_x, beam_wall_y),
        _line(0, beam_start_y - 75, wall_x, beam_wall_y - 75),
        _line(wall_x, beam_wall_y, outer_x, beam_outer_y),
        _line(wall_x, beam_wall_y - 85, outer_x, beam_outer_y - 85),
        _line(wall_x, inner_deck_y, outer_x, outer_deck_y),
        _line(wall_x, inner_deck_y - 95, outer_x, outer_deck_y - 95),
        _line(wall_x, inner_deck_y + 500, outer_x, outer_deck_y + 500),
        _line(wall_x, inner_deck_y + 980, outer_x, outer_deck_y + 980),
    ]

    braces: list[dict[str, Any]] = []
    braces.append(_line(0, beam_start_y - 10, wall_x, beam_start_y + 220))
    braces.append(_line(0, beam_start_y + 180, wall_x, beam_start_y - 35))
    for attach_x, attach_y, _label, top_y in rope_ends:
        braces.append(_line(wall_x, top_y, attach_x, attach_y))
        braces.append(_line(wall_x, top_y - 35, attach_x, attach_y - 55))

    if is_section:
        for index in range(9):
            x = wall_x + 160 + index * max(80.0, overhang * 0.09)
            if x >= outer_x:
                break
            y = deck_y_at(x)
            levels.append(_line(x - 28, y + 18, x + 28, y - 72))
        uprights.append(
            {"type": "circle", "x": round(wall_x + overhang * 0.52, 2), "y": round(deck_y_at(wall_x + overhang * 0.52) - 45, 2), "r": 62.0}
        )

    dim = [
        _line(0, -600, wall_x, -600),
        _line(0, -700, 0, -500),
        _line(wall_x, -700, wall_x, -500),
        _text(f"室内锚固段 {anchor:.0f} mm", wall_x / 2, -950, 175),
        _line(wall_x, -1350, outer_x, -1350),
        _line(wall_x, -1450, wall_x, -1250),
        _line(outer_x, -1450, outer_x, -1250),
        _text(f"悬挑段 {overhang:.0f} mm", (wall_x + outer_x) / 2, -1700, 175),
        _line(-750, 0, -750, outer_deck_y),
        _text(f"平台高度 {outer_deck_y:.0f} mm", -1080, outer_deck_y / 2, 155, rotation=90),
        _text("建筑墙体边线", wall_x, total_height - 420, 155),
        _text("室内锚固段", anchor * 0.48, beam_start_y - 190, 150),
        _text("悬挑主梁", wall_x + overhang * 0.55, (beam_wall_y + beam_outer_y) / 2 - 170, 155),
        _text("平台板（外高内低）", wall_x + overhang * 0.55, outer_deck_y + 210, 155),
        _text("外缘防护栏杆", outer_x + 260, outer_deck_y + 760, 140),
        _text(f"斜拉绳侧数 {values['sideCount']} · 每侧前/后各1道（示意）", wall_x + overhang * 0.48, total_height - 680, 145),
        _text(f"平台沿边长度 {values['platformLength']:.0f} mm", wall_x + overhang * 0.50, -2250, 145),
    ]
    for attach_x, _attach_y, label, top_y in rope_ends:
        angle = values["frontRopeAngle"] if label.startswith("前") else values["rearRopeAngle"]
        dim.append(_text(f"{label} α={angle:g}°", (wall_x + attach_x) / 2, top_y + 90, 155))
    if is_section:
        dim.append(_text("主梁剖面 / 平台板断面", wall_x + overhang * 0.55, outer_deck_y - 260, 145))

    dim += _cantilever_module_texts(title, outer_x, total_height + 80)
    return _payload(
        view,
        outer_x,
        total_height + 900,
        {
            "upright": uprights,
            "level": levels,
            "brace": braces,
            "dim": dim,
        },
    )


def _cantilever_side(values: dict[str, Any]) -> dict[str, Any]:
    length = values["platformLength"]
    side_count = values["sideCount"]
    deck_y = 1050.0
    wall_y = 430.0
    rail_y = deck_y + 1000.0
    main_x = [length * 0.18, length * 0.82]

    uprights = [
        _line(x, wall_y, x, deck_y) for x in main_x
    ] + [
        {"type": "circle", "x": round(x, 2), "y": round(wall_y, 2), "r": 52.0}
        for x in main_x
    ]
    uprights.extend(_line(x, deck_y, x, rail_y) for x in (0.0, length))

    levels = [
        _line(0, wall_y, length, wall_y),
        _line(0, wall_y - 90, length, wall_y - 90),
        _line(0, deck_y, length, deck_y),
        _line(0, deck_y - 110, length, deck_y - 110),
        _line(0, deck_y + 500, length, deck_y + 500),
        _line(0, rail_y, length, rail_y),
    ]
    levels.extend(_line(main_x[0], deck_y - 75 + index * 12, main_x[1], deck_y - 75 + index * 12) for index in range(5))
    levels.extend(_line(0, wall_y - 240, length, wall_y - 240) for _ in range(1))

    braces: list[dict[str, Any]] = []
    for index in range(side_count):
        offset = index * 45.0
        braces.extend(
            [
                _line(0, wall_y + 60 + offset, length * 0.40, deck_y + 90 + offset),
                _line(length, wall_y + 60 + offset, length * 0.60, deck_y + 90 + offset),
            ]
        )
    braces.extend(
        [
            _line(main_x[0], wall_y, main_x[1], deck_y),
            _line(main_x[1], wall_y, main_x[0], deck_y),
        ]
    )

    dim = [
        _line(0, -550, length, -550),
        _line(0, -650, 0, -450),
        _line(length, -650, length, -450),
        _text(f"平台沿边长 {length:.0f} mm", length / 2, -900, 180),
        _line(-750, wall_y - 240, -750, rail_y),
        _text(f"平台侧高 {rail_y - wall_y:.0f} mm", -1080, (rail_y + wall_y) / 2, 155, rotation=90),
        _text("建筑墙面（沿边方向）", length / 2, wall_y - 330, 150),
        _text("室内锚固段（沿边投影）", length / 2, wall_y + 150, 145),
        _text("双主梁端部（示意）", length / 2, deck_y - 190, 150),
        _text("前/后道钢丝绳（沿边方向投影）", length / 2, deck_y + 650, 145),
        _text(f"斜拉绳侧数 {side_count}", length / 2, deck_y + 860, 145),
    ]
    dim += _cantilever_module_texts("侧立面（长度方向）", length, rail_y + 160)

    return _payload(
        "side",
        length,
        rail_y + 800,
        {
            "upright": uprights,
            "level": levels,
            "brace": braces,
            "dim": dim,
        },
    )


def build_cantilever_operation_platform_geometry(
    params: dict[str, Any],
    view: str = "elevation",
) -> dict[str, Any]:
    """生成悬挑式操作平台四视图 Geometry payload。"""
    values = _cantilever_values(params or {})
    selected = view if view in VALID_VIEWS else "elevation"
    if selected == "plan":
        return _cantilever_plan(values)
    if selected == "side":
        return _cantilever_side(values)
    return _cantilever_profile(values, selected)
