"""连墙件计算四视图参数化示意图。"""

from __future__ import annotations

import math
from typing import Any

from .drawing import _line, _payload, _text


_VIEWS = {"elevation", "plan", "side", "section"}
_CAPTION = "连墙件计算 · 参数化示意（非施工图）"


def _value(params: dict[str, Any], key: str, default: float) -> float:
    try:
        value = float((params or {}).get(key, default))
    except (TypeError, ValueError):
        value = default
    if not math.isfinite(value) or value <= 0:
        return default
    return value


def _height_positions(height: float, spacing: float) -> list[float]:
    positions = [
        spacing * index
        for index in range(1, math.ceil(height / spacing) + 1)
    ]
    if positions and positions[-1] > height:
        positions.pop()
    return positions or [height]


def build_tie_member_geometry(
    params: dict[str, Any],
    view: str = "elevation",
) -> dict[str, Any]:
    view = view if view in _VIEWS else "elevation"
    height = _value(params, "H", 24.0) * 1000.0
    step = _value(params, "h", 1.8) * 1000.0
    long_spacing = _value(params, "la", 1.5) * 1000.0
    transverse_spacing = _value(params, "lb", 0.9) * 1000.0
    tie_length = _value(params, "tieLength", 0.9) * 1000.0
    tie_vertical = _value(params, "tieVerticalSpacing", 3.6) * 1000.0
    tie_horizontal = _value(params, "tieHorizontalSpacing", 4.5) * 1000.0

    if view == "plan":
        return _plan(
            tie_length=tie_length,
            transverse_spacing=transverse_spacing,
            tie_horizontal=tie_horizontal,
        )
    if view in {"side", "section"}:
        return _profile(
            height=height,
            tie_length=tie_length,
            transverse_spacing=transverse_spacing,
            tie_vertical=tie_vertical,
            view=view,
        )
    return _elevation(
        height=height,
        step=step,
        long_spacing=long_spacing,
        tie_vertical=tie_vertical,
    )


def _elevation(
    *,
    height: float,
    step: float,
    long_spacing: float,
    tie_vertical: float,
) -> dict[str, Any]:
    width = long_spacing * 3.0
    posts = [index * long_spacing for index in range(4)]
    inner_offsets = [post + 110.0 for post in posts]
    upright = [_line(x, 0, x, height) for x in posts]
    upright.extend(_line(x, 0, x, height) for x in inner_offsets)

    level_y = [
        min(step * index, height)
        for index in range(1, math.ceil(height / step))
    ]
    level = [_line(0, y, width + 110.0, y) for y in level_y]
    tie_y = _height_positions(height, tie_vertical)
    level.extend(_line(-260.0, y, width + 110.0, y) for y in tie_y)

    wall = [_line(-260.0, 0, -260.0, height)]
    wall.extend(
        _line(-260.0, height * index / 16.0, 0, height * index / 16.0)
        for index in range(17)
    )
    tie_points = [
        {"type": "circle", "x": 0.0, "y": round(y, 2), "r": 48.0}
        for y in tie_y
    ]

    dim = [
        _line(0, -650, width, -650),
        _line(0, -760, 0, -540),
        _line(width, -760, width, -540),
        _text(f"3 × la = {width:.0f} mm", width / 2, -980, 180),
        _line(-750, 0, -750, height),
        _line(-860, 0, -640, 0),
        _line(-860, height, -640, height),
        _text(f"H = {height:.0f} mm", -1100, height / 2, 180, rotation=90),
        _text("建筑墙面", 260.0, height + 180, 155),
        _text(
            f"竖向间距 = {tie_vertical / 1000.0:.2f} m"
            " · 连墙杆 / 内外立杆（投影）",
            width / 2,
            height + 500,
            155,
        ),
        _text(_CAPTION, width / 2, height + 820, 180),
    ]
    return _payload(
        "elevation",
        width,
        height,
        {
            "upright": upright,
            "level": level + tie_points,
            "brace": wall,
            "dim": dim,
        },
    )


def _plan(
    *,
    tie_length: float,
    transverse_spacing: float,
    tie_horizontal: float,
) -> dict[str, Any]:
    width = tie_horizontal * 2.0
    inner_y = tie_length
    outer_y = tie_length + transverse_spacing
    depth = outer_y
    xs = [0.0, tie_horizontal, width]

    upright = [
        {"type": "circle", "x": round(x, 2), "y": round(y, 2), "r": 45.0}
        for x in xs
        for y in (inner_y, outer_y)
    ]
    level = [
        _line(0, inner_y, width, inner_y),
        _line(0, outer_y, width, outer_y),
    ]
    level.extend(_line(x, 0, x, outer_y) for x in xs)
    wall = [
        _line(0, 0, width, 0),
        _line(0, -140, width, -140),
    ]
    wall.extend(_line(x, -140, x + 180, 0) for x in (width / 3, 2 * width / 3))

    dim = [
        _line(0, -560, width, -560),
        _line(0, -680, 0, -440),
        _line(width, -680, width, -440),
        _text(
            f"水平间距 = {tie_horizontal / 1000.0:.2f} m",
            width / 2,
            -900,
            175,
        ),
        _line(width + 430, 0, width + 430, outer_y),
        _line(width + 320, 0, width + 540, 0),
        _line(width + 320, outer_y, width + 540, outer_y),
        _text(
            f"lb = {transverse_spacing:.0f} mm",
            width + 760,
            depth / 2,
            165,
            rotation=90,
        ),
        _line(0, -350, tie_length, -350),
        _text(
            f"计算长度 = {tie_length / 1000.0:.2f} m",
            tie_length / 2,
            -420,
            150,
        ),
        _text(
            "建筑墙面 / 连墙杆 / 内排立杆 / 外排立杆",
            width / 2,
            outer_y + 320,
            150,
        ),
        _text(_CAPTION, width / 2, outer_y + 640, 180),
    ]
    return _payload(
        "plan",
        width,
        outer_y,
        {"upright": upright, "level": level, "brace": wall, "dim": dim},
    )


def _profile(
    *,
    height: float,
    tie_length: float,
    transverse_spacing: float,
    tie_vertical: float,
    view: str,
) -> dict[str, Any]:
    inner_x = tie_length
    outer_x = tie_length + transverse_spacing
    width = outer_x
    upright = [
        _line(inner_x, 0, inner_x, height),
        _line(outer_x, 0, outer_x, height),
    ]
    tie_y = _height_positions(height, tie_vertical)
    level = [_line(0, y, outer_x, y) for y in tie_y]
    wall = [_line(0, 0, 0, height)]
    if view == "section":
        wall.extend(
            [
                _line(-180, 0, -180, height),
                _line(-180, 0, 0, 0),
                _line(-180, height, 0, height),
            ]
        )
    wall.extend(
        _line(-180, y, 0, y + 90)
        for y in (height * index / 14.0 for index in range(14))
    )

    dim = [
        _line(0, -560, outer_x, -560),
        _line(0, -680, 0, -440),
        _line(outer_x, -680, outer_x, -440),
        _line(0, -790, tie_length, -790),
        _text(
            f"计算长度 = {tie_length / 1000.0:.2f} m",
            tie_length / 2,
            -960,
            160,
        ),
        _text(
            f"lb = {transverse_spacing:.0f} mm",
            tie_length + transverse_spacing / 2,
            -960,
            150,
        ),
        _line(-650, 0, -650, height),
        _line(-760, 0, -540, 0),
        _line(-760, height, -540, height),
        _text(f"H = {height:.0f} mm", -1000, height / 2, 175, rotation=90),
        _text("建筑墙面", -90.0, height + 180, 150),
        _text(
            f"竖向间距 = {tie_vertical / 1000.0:.2f} m"
            " · 连墙杆 / 内外立杆",
            width / 2,
            height + 500,
            150,
        ),
        _text(_CAPTION, width / 2, height + 820, 180),
    ]
    return _payload(
        view,
        width,
        height,
        {"upright": upright, "level": level, "brace": wall, "dim": dim},
    )
