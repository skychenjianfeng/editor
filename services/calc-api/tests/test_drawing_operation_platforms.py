from __future__ import annotations

import math

import pytest

from calc_core.drawing_operation_platforms import (
    CANTILEVER_MODULE_KEY,
    CANTILEVER_MODULE_NAME,
    GROUND_MODULE_KEY,
    GROUND_MODULE_NAME,
    SCHEMATIC_NOTE,
    build_cantilever_operation_platform_geometry,
    build_ground_operation_platform_geometry,
)

GROUND_PARAMS = {
    "length": 3.0,
    "width": 3.0,
    "H": 4.0,
    "la": 0.9,
    "lb": 0.9,
    "h": 1.5,
    "platformKind": "接料平台",
}

CANTILEVER_PARAMS = {
    "platformLength": 3.9,
    "overhangLength": 3.5,
    "anchorLength": 1.5,
    "frontRopeDistance": 3.5,
    "rearRopeDistance": 2.0,
    "frontRopeAngle": 55.0,
    "rearRopeAngle": 50.0,
    "sideCount": 2,
}


def _items(geometry: dict, layer_id: str) -> list[dict]:
    return next(layer for layer in geometry["layers"] if layer["id"] == layer_id)["items"]


def _texts(geometry: dict) -> list[str]:
    return [
        item["text"]
        for layer in geometry["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    ]


def _all_items(geometry: dict) -> list[dict]:
    return [item for layer in geometry["layers"] for item in layer["items"]]


def _assert_payload_contract(geometry: dict, view: str) -> None:
    assert geometry["view"] == view
    assert geometry["units"] == "mm"
    assert set(geometry["bounds"]) == {"minX", "minY", "maxX", "maxY"}
    assert [layer["id"] for layer in geometry["layers"]] == ["upright", "level", "brace", "dim"]
    assert all(isinstance(layer["items"], list) for layer in geometry["layers"])
    assert all(item["type"] in {"line", "circle", "text"} for item in _all_items(geometry))


@pytest.mark.parametrize("view", ["elevation", "plan", "side", "section"])
def test_ground_operation_platform_four_view_contract(view: str) -> None:
    geometry = build_ground_operation_platform_geometry(GROUND_PARAMS, view)
    _assert_payload_contract(geometry, view)
    text = "\n".join(_texts(geometry))
    assert GROUND_MODULE_NAME in text
    assert GROUND_MODULE_KEY in text
    assert SCHEMATIC_NOTE in text
    assert GROUND_PARAMS["platformKind"] in text


def test_ground_plan_contains_support_grid_and_outer_profile() -> None:
    geometry = build_ground_operation_platform_geometry(GROUND_PARAMS, "plan")
    uprights = _items(geometry, "upright")
    assert len(uprights) == 25
    assert all(item["type"] == "circle" for item in uprights)
    xs = {item["x"] for item in uprights}
    ys = {item["y"] for item in uprights}
    assert xs == {0.0, 900.0, 1800.0, 2700.0, 3000.0}
    assert ys == {0.0, 900.0, 1800.0, 2700.0, 3000.0}
    assert len(_items(geometry, "level")) >= 10


def test_ground_plan_shows_guardrail_and_opening() -> None:
    geometry = build_ground_operation_platform_geometry(GROUND_PARAMS, "plan")
    text = "\n".join(_texts(geometry))
    assert "防护栏杆" in text
    assert "开口" in text
    guardrail_lines = [
        item
        for item in _items(geometry, "level")
        if item["type"] == "line" and item["y1"] == item["y2"] == 2925.0
    ]
    assert len(guardrail_lines) >= 2


def test_ground_elevation_shows_supports_levels_braces_and_rigid_connection() -> None:
    geometry = build_ground_operation_platform_geometry(GROUND_PARAMS, "elevation")
    assert len(_items(geometry, "upright")) >= 5
    assert len(_items(geometry, "level")) >= 6
    assert len(_items(geometry, "brace")) >= 3
    text = "\n".join(_texts(geometry))
    assert "连墙/刚性连接" in text
    assert "平台板" in text
    assert "防护栏杆" in text
    assert "4000" in text
    assert "1500" in text


def test_ground_side_and_section_are_distinct() -> None:
    side = build_ground_operation_platform_geometry(GROUND_PARAMS, "side")
    section = build_ground_operation_platform_geometry(GROUND_PARAMS, "section")
    assert "侧立面" in "\n".join(_texts(side))
    assert "剖面 A-A" in "\n".join(_texts(section))
    assert _all_items(side) != _all_items(section)


@pytest.mark.parametrize("view", ["elevation", "plan", "side", "section"])
def test_cantilever_operation_platform_four_view_contract(view: str) -> None:
    geometry = build_cantilever_operation_platform_geometry(CANTILEVER_PARAMS, view)
    _assert_payload_contract(geometry, view)
    text = "\n".join(_texts(geometry))
    assert CANTILEVER_MODULE_NAME in text
    assert CANTILEVER_MODULE_KEY in text
    assert SCHEMATIC_NOTE in text
    assert "2" in text


def test_cantilever_elevation_shows_indoor_anchor_wall_ropes_and_sloped_deck() -> None:
    geometry = build_cantilever_operation_platform_geometry(CANTILEVER_PARAMS, "elevation")
    text = "\n".join(_texts(geometry))
    assert "建筑墙体边线" in text
    assert "室内锚固段" in text
    assert "悬挑主梁" in text
    assert "前道钢丝绳" in text
    assert "后道钢丝绳" in text
    assert "平台板（外高内低）" in text

    wall_x = CANTILEVER_PARAMS["anchorLength"] * 1000
    rope_lines = [
        item
        for item in _items(geometry, "brace")
        if item["type"] == "line" and math.isclose(item["x1"], wall_x, abs_tol=0.01)
    ]
    assert len(rope_lines) >= 4
    assert any(item["y1"] > 2000 for item in rope_lines)


def test_cantilever_plan_shows_double_main_beams_secondary_beams_and_anchors() -> None:
    geometry = build_cantilever_operation_platform_geometry(CANTILEVER_PARAMS, "plan")
    text = "\n".join(_texts(geometry))
    assert "双主梁（2根）" in text
    assert "次梁" in text
    assert "锚点" in text
    assert "前/后道钢丝绳吊点" in text
    assert len([item for item in _items(geometry, "upright") if item["type"] == "circle"]) >= 8

    main_x = {
        CANTILEVER_PARAMS["platformLength"] * 1000 * 0.18,
        CANTILEVER_PARAMS["platformLength"] * 1000 * 0.82,
    }
    long_beams = [
        item
        for item in _items(geometry, "level")
        if item["type"] == "line" and item["x1"] == item["x2"] and item["x1"] in main_x
    ]
    assert len(long_beams) == 2


def test_cantilever_dimension_text_uses_mm_and_parameter_values() -> None:
    elevation = build_cantilever_operation_platform_geometry(CANTILEVER_PARAMS, "elevation")
    text = "\n".join(_texts(elevation))
    assert "室内锚固段 1500 mm" in text
    assert "悬挑段 3500 mm" in text
    assert "前道钢丝绳 α=55°" in text
    assert "后道钢丝绳 α=50°" in text
    assert "平台沿边长度 3900 mm" in text
    assert SCHEMATIC_NOTE in text


def test_cantilever_rope_positions_follow_parameters() -> None:
    params = dict(CANTILEVER_PARAMS)
    first = build_cantilever_operation_platform_geometry(params, "elevation")
    params.update({"frontRopeDistance": 3.0, "rearRopeDistance": 1.4, "sideCount": 3})
    second = build_cantilever_operation_platform_geometry(params, "elevation")
    first_braces = _items(first, "brace")
    second_braces = _items(second, "brace")
    assert first_braces != second_braces
    assert "斜拉绳侧数 3" in "\n".join(_texts(second))
