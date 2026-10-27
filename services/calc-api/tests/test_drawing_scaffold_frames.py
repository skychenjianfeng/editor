import pytest

from calc_core import drawing
from calc_core.drawing_scaffold_frames import (
    build_cantilever_scaffold_geometry,
    build_door_scaffold_geometry,
    build_full_hall_geometry,
)


VIEWS = ("elevation", "plan", "side", "section")
LAYER_IDS = ["upright", "level", "brace", "dim"]

FULL_HALL_PARAMS = {
    "H": 12.0,
    "la": 1.2,
    "lb": 1.2,
    "h": 1.5,
    "lengthX": 6.0,
    "lengthY": 6.0,
}
DOOR_PARAMS = {
    "H": 20.0,
    "frameWidth": 1.219,
    "frameBay": 1.8,
    "stepHeight": 1.93,
}
CANTILEVER_PARAMS = {
    "L": 1.5,
    "armLength": 1.2,
    "H": 24.0,
    "la": 1.5,
    "lb": 0.9,
    "h": 1.8,
}


def _layer(geometry, layer_id):
    return next(layer for layer in geometry["layers"] if layer["id"] == layer_id)


def _texts(geometry):
    return [
        item["text"]
        for layer in geometry["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    ]


def _assert_contract(geometry, view):
    assert geometry["view"] == view
    assert geometry["units"] == "mm"
    assert geometry["bounds"]["maxX"] > geometry["bounds"]["minX"]
    assert geometry["bounds"]["maxY"] > geometry["bounds"]["minY"]
    assert [layer["id"] for layer in geometry["layers"]] == LAYER_IDS
    assert [layer["color"] for layer in geometry["layers"]] == [
        drawing.COLORS[layer_id] for layer_id in LAYER_IDS
    ]


@pytest.mark.parametrize("view", VIEWS)
def test_full_hall_geometry_contract(view):
    _assert_contract(build_full_hall_geometry(FULL_HALL_PARAMS, view), view)


@pytest.mark.parametrize("view", VIEWS)
def test_door_scaffold_geometry_contract(view):
    _assert_contract(build_door_scaffold_geometry(DOOR_PARAMS, view), view)


@pytest.mark.parametrize("view", VIEWS)
def test_cantilever_scaffold_geometry_contract(view):
    _assert_contract(build_cantilever_scaffold_geometry(CANTILEVER_PARAMS, view), view)


def test_full_hall_plan_draws_upright_matrix_and_braces():
    geometry = build_full_hall_geometry(FULL_HALL_PARAMS, "plan")
    upright = _layer(geometry, "upright")["items"]
    level = _layer(geometry, "level")["items"]
    brace = _layer(geometry, "brace")["items"]

    assert len(upright) == 36
    assert all(item["type"] == "circle" for item in upright)
    assert len(level) == 12
    assert brace
    assert any("lengthX = 6000 mm" in text for text in _texts(geometry))
    assert any("满堂脚手架" in text and "参数化构造示意（非施工图）" in text for text in _texts(geometry))


def test_full_hall_large_plan_is_grid_limited():
    geometry = build_full_hall_geometry(
        {
            "H": 36.0,
            "la": 0.1,
            "lb": 0.1,
            "h": 0.3,
            "lengthX": 100.0,
            "lengthY": 100.0,
        },
        "plan",
    )
    upright = _layer(geometry, "upright")["items"]
    level = _layer(geometry, "level")["items"]

    assert len(upright) == 30 * 30
    assert len(level) == 30 + 30
    assert len(level) < 30 * 30


def test_full_hall_section_adds_internal_upright_and_boards():
    side = build_full_hall_geometry(FULL_HALL_PARAMS, "side")
    section = build_full_hall_geometry(FULL_HALL_PARAMS, "section")

    side_vertical = [
        item for item in _layer(side, "upright")["items"] if item["x1"] == item["x2"]
    ]
    section_vertical = [
        item for item in _layer(section, "upright")["items"] if item["x1"] == item["x2"]
    ]
    assert any(item["x1"] == 3000 for item in section_vertical)
    assert len(_layer(section, "level")["items"]) > len(_layer(side, "level")["items"])
    assert any("剖面 A-A" in text for text in _texts(section))


def test_door_elevation_and_plan_show_required_frames():
    elevation = build_door_scaffold_geometry(DOOR_PARAMS, "elevation")
    plan = build_door_scaffold_geometry(DOOR_PARAMS, "plan")

    assert any("门架梯形 / 门洞" in text for text in _texts(elevation))
    assert any("水平加固杆" in text for text in _texts(elevation))
    assert any("门式钢管脚手架" in text and "参数化构造示意（非施工图）" in text for text in _texts(elevation))
    plan_uprights = _layer(plan, "upright")["items"]
    assert len(plan_uprights) == 6
    assert any("平面门架排布" in text for text in _texts(plan))


def test_door_side_has_two_width_uprights_and_section_differs():
    side = build_door_scaffold_geometry(DOOR_PARAMS, "side")
    section = build_door_scaffold_geometry(DOOR_PARAMS, "section")

    vertical = [
        item for item in _layer(side, "upright")["items"] if item["x1"] == item["x2"]
    ]
    assert len(vertical) == 2
    assert {item["x1"] for item in vertical} == {0, 1219}
    assert any(item["type"] == "circle" for item in _layer(section, "level")["items"])
    assert any("剖面 A-A" in text for text in _texts(section))


def test_cantilever_elevation_has_floor_anchor_beam_and_dimensions():
    geometry = build_cantilever_scaffold_geometry(CANTILEVER_PARAMS, "elevation")
    texts = _texts(geometry)
    upright = _layer(geometry, "upright")["items"]
    brace = _layer(geometry, "brace")["items"]

    assert any("楼面/墙边" in text for text in texts)
    assert any("室内锚固段" in text for text in texts)
    assert any("悬挑工字钢" in text for text in texts)
    assert any("armLength = 1200 mm" in text for text in texts)
    assert any("L = 1500 mm" in text for text in texts)
    assert any("型钢悬挑脚手架" in text and "参数化构造示意（非施工图）" in text for text in texts)
    assert any(item["x2"] <= 1200 for item in brace)
    assert any(item["x1"] <= 1200 for item in upright)


def test_cantilever_default_height_and_plan_strip():
    geometry = build_cantilever_scaffold_geometry(
        {"L": 1.5, "armLength": 1.2, "la": 1.5, "lb": 0.9},
        "plan",
    )
    texts = _texts(geometry)
    assert any("H = 24000 mm" in text for text in texts)
    assert any("armLength + L = 1200 + 1500 mm" in text for text in texts)
    assert _layer(geometry, "upright")["items"]
    assert len(_layer(geometry, "level")["items"]) >= 6
