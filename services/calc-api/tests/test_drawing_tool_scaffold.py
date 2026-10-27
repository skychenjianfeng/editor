from __future__ import annotations

import json

import pytest

from calc_core.drawing_tool_scaffold import (
    build_attached_lifting_geometry,
    build_suspended_basket_geometry,
)


BASKET_PARAMS = {
    "platformSpan": 6.0,
    "platformWeight": 450.0,
    "ratedLoad": 630.0,
    "outerLength": 1.5,
    "innerLength": 4.5,
    "frameWeight": 350.0,
    "counterWeight": 600.0,
    "wireRopeCount": 2,
}

LIFTING_PARAMS = {
    "H": 65.0,
    "storeyHeight": 3.6,
    "h": 1.8,
    "la": 1.5,
    "lb": 0.8,
    "n": 8,
    "k": 4,
    "overhang": 0.3,
    "cantileverHeight": 3.6,
}


def _items(geometry, layer_id):
    return next(layer["items"] for layer in geometry["layers"] if layer["id"] == layer_id)


def _texts(geometry):
    return [
        item["text"]
        for layer in geometry["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    ]


@pytest.mark.parametrize("view", ["elevation", "plan", "side", "section"])
@pytest.mark.parametrize(
    "builder,params",
    [
        (build_suspended_basket_geometry, BASKET_PARAMS),
        (build_attached_lifting_geometry, LIFTING_PARAMS),
    ],
)
def test_four_views_share_geometry_contract(builder, params, view):
    geometry = builder(params, view)
    assert geometry["view"] == view
    assert geometry["units"] == "mm"
    assert [layer["id"] for layer in geometry["layers"]] == ["upright", "level", "brace", "dim"]
    assert geometry["bounds"]["maxX"] > geometry["bounds"]["minX"]
    assert geometry["bounds"]["maxY"] > geometry["bounds"]["minY"]
    assert all(layer["items"] for layer in geometry["layers"])
    json.dumps(geometry)


def test_basket_elevation_has_two_or_more_ropes_and_separate_counterweight():
    geometry = build_suspended_basket_geometry(BASKET_PARAMS, "elevation")
    brace = _items(geometry, "brace")
    vertical_ropes = [
        item
        for item in brace
        if item["type"] == "line"
        and abs(item["x1"] - item["x2"]) < 0.01
        and abs(item["y2"] - item["y1"]) > 1000
    ]
    assert len(vertical_ropes) >= 2
    assert any(text.startswith("工作钢丝绳×") for text in _texts(geometry))
    assert any("配重 600kg" in text for text in _texts(geometry))

    counter_top = max(
        item["y1"]
        for item in _items(geometry, "upright")
        if item["type"] == "line" and 0 <= item["x1"] <= 1000 and item["y1"] > 3000
    )
    platform_bottom = min(
        item["y1"]
        for item in _items(geometry, "level")
        if item["type"] == "line" and item["y1"] == item["y2"] and item["y1"] < 500
    )
    assert counter_top > platform_bottom + 2000


def test_basket_plan_shows_platform_and_two_lifting_points():
    geometry = build_suspended_basket_geometry(BASKET_PARAMS, "plan")
    points = [item for item in _items(geometry, "upright") if item["type"] == "circle"]
    assert len(points) == 2
    assert all(item["role"] == "lifting-point" for item in points)
    texts = _texts(geometry)
    assert any("吊篮平台" in text for text in texts)
    assert any("6000" in text for text in texts)


def test_basket_side_and_section_show_width_and_suspension_relation():
    side = build_suspended_basket_geometry(BASKET_PARAMS, "side")
    section = build_suspended_basket_geometry(BASKET_PARAMS, "section")
    for geometry, view_text in ((side, "侧立面"), (section, "剖面")):
        texts = _texts(geometry)
        assert any(view_text in text for text in texts)
        assert any("宽度 800" in text for text in texts)
        assert any("悬挂臂" in text for text in texts)
        assert any("配重" in text for text in texts)
    assert len(_items(section, "level")) > len(_items(side, "level"))


def test_attached_elevation_has_k_machines_and_k_supports():
    geometry = build_attached_lifting_geometry(LIFTING_PARAMS, "elevation")
    upright = _items(geometry, "upright")
    brace = _items(geometry, "brace")
    machines = [item for item in upright if item["type"] == "circle" and item.get("role") == "machine"]
    supports = [item for item in brace if item["type"] == "circle" and item.get("role") == "wall-support"]
    assert len(machines) == LIFTING_PARAMS["k"]
    assert len(supports) == LIFTING_PARAMS["k"]
    texts = _texts(geometry)
    assert any("提升机位/防坠点×4" in text for text in texts)
    assert any("附墙支座×4" in text for text in texts)


def test_attached_plan_shows_frame_strip_machines_and_inside_outside():
    geometry = build_attached_lifting_geometry(LIFTING_PARAMS, "plan")
    machines = [
        item
        for item in _items(geometry, "upright")
        if item["type"] == "circle" and item.get("role") == "machine"
    ]
    supports = [
        item
        for item in _items(geometry, "upright")
        if item["type"] == "circle" and item.get("role") == "wall-support"
    ]
    assert len(machines) == LIFTING_PARAMS["k"]
    assert len(supports) == LIFTING_PARAMS["k"]
    texts = _texts(geometry)
    assert any("架体条带" in text for text in texts)
    assert any("建筑内侧" in text for text in texts)
    assert any("架体外侧" in text for text in texts)


def test_attached_side_and_section_distinguish_inside_and_outside():
    side = build_attached_lifting_geometry(LIFTING_PARAMS, "side")
    section = build_attached_lifting_geometry(LIFTING_PARAMS, "section")
    for geometry in (side, section):
        texts = _texts(geometry)
        assert any("建筑内侧" in text for text in texts)
        assert any("架体外侧" in text for text in texts)
        assert any("底部防护" in text for text in texts)
        assert any("顶部防护" in text for text in texts)
    assert len(_items(section, "level")) > len(_items(side, "level"))


def test_views_are_geometrically_distinct():
    basket_views = [build_suspended_basket_geometry(BASKET_PARAMS, view) for view in ("elevation", "plan", "side", "section")]
    lifting_views = [build_attached_lifting_geometry(LIFTING_PARAMS, view) for view in ("elevation", "plan", "side", "section")]
    assert len({json.dumps(geometry, sort_keys=True, ensure_ascii=False) for geometry in basket_views}) == 4
    assert len({json.dumps(geometry, sort_keys=True, ensure_ascii=False) for geometry in lifting_views}) == 4


@pytest.mark.parametrize("view", ["elevation", "plan", "side", "section"])
def test_each_view_has_module_name_disclaimer_and_dimensions(view):
    basket = build_suspended_basket_geometry(BASKET_PARAMS, view)
    lifting = build_attached_lifting_geometry(LIFTING_PARAMS, view)
    basket_text = " ".join(_texts(basket))
    lifting_text = " ".join(_texts(lifting))
    assert "高处作业吊篮" in basket_text
    assert "附着式升降脚手架" in lifting_text
    assert basket_text.count("参数化构造示意（非施工图）") >= 1
    assert lifting_text.count("参数化构造示意（非施工图）") >= 1

    if view == "plan":
        assert "6000" in basket_text and "4500" in lifting_text
    elif view in {"side", "section"}:
        assert "800" in basket_text and "800" in lifting_text
    else:
        assert "配重 600kg" in basket_text
        assert "14000" in lifting_text or "14400" in lifting_text or "65000" in lifting_text
