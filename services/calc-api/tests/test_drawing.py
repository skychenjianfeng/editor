import pytest

from calc_core import drawing


PARAMS = {"h": 1.8, "la": 1.5, "lb": 0.9, "H": 24}


def test_elevation_geometry_layers():
    g = drawing.build_geometry(PARAMS, "elevation")
    ids = [layer["id"] for layer in g["layers"]]
    assert ids == ["upright", "level", "brace", "dim"]
    counts = {layer["id"]: len(layer["items"]) for layer in g["layers"]}
    assert counts["upright"] == 7
    assert counts["level"] >= 14
    assert counts["brace"] > 0


def test_elevation_height_uses_actual_H_not_rounded_levels():
    g = drawing.build_geometry(PARAMS, "elevation")
    dim_texts = [i["text"] for layer in g["layers"] if layer["id"] == "dim" for i in layer["items"] if i["type"] == "text"]
    assert "24000" in dim_texts
    assert "25200" not in dim_texts


def test_plan_geometry_has_posts():
    g = drawing.build_geometry(PARAMS, "plan")
    upright = next(layer for layer in g["layers"] if layer["id"] == "upright")
    assert upright["items"]
    assert all(item["type"] == "circle" for item in upright["items"])


def test_side_elevation_profile():
    g = drawing.build_geometry(PARAMS, "side")
    assert g["view"] == "side"
    upright = next(layer for layer in g["layers"] if layer["id"] == "upright")
    assert len(upright["items"]) == 2
    xs = {item["x1"] for item in upright["items"]}
    assert xs == {0, 900}


def test_section_has_boards_and_title():
    g = drawing.build_geometry(PARAMS, "section")
    assert g["view"] == "section"
    level = next(layer for layer in g["layers"] if layer["id"] == "level")
    dim = next(layer for layer in g["layers"] if layer["id"] == "dim")
    texts = [i["text"] for i in dim["items"] if i["type"] == "text"]
    # 剖面比侧立面多出脚手板线
    side_level = next(
        layer for layer in drawing.build_geometry(PARAMS, "side")["layers"] if layer["id"] == "level"
    )
    assert len(level["items"]) > len(side_level["items"])
    assert any("剖面" in t for t in texts)


@pytest.mark.parametrize("view", ["elevation", "plan", "side", "section"])
def test_pinming_module_uses_shared_fastener_geometry(view):
    params = {"h": 1.8, "la": 1.5, "lb": 0.9, "H": 30.0}
    assert drawing.build_geometry_for_module(
        "scaffold-fastener-pinming",
        "扣件式脚手架（品茗双立杆）",
        params,
        view,
    ) == drawing.build_geometry(params, view)


def test_dxf_export_is_text_dxf():
    data = drawing.export_dxf(PARAMS, "elevation")
    assert b"SECTION" in data[:200]
    assert b"EOF" in data[-200:]
    assert b"LINE" in data
    assert len(data) > 10_000


def test_png_export_is_png():
    data = drawing.export_png(PARAMS, "elevation")
    assert data.startswith(b"\x89PNG")
    assert len(data) > 20_000


def test_non_scaffold_geometry_is_module_labelled_schematic():
    g = drawing.build_geometry_for_module(
        "attached-lifting-scaffold",
        "附着式升降脚手架",
        {"la": 6.0, "lb": 1.2, "H": 20.0},
        "elevation",
    )
    texts = [
        item["text"]
        for layer in g["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    ]
    assert any("附着式升降脚手架" in text for text in texts)
    assert any("非施工图" in text for text in texts)
    assert not any("K1" == text for text in texts)


def test_non_scaffold_dxf_and_png_exports_use_schematic():
    dxf = drawing.export_dxf(
        {"la": 6.0, "lb": 1.2, "H": 20.0},
        "plan",
        module_key="attached-lifting-scaffold",
        module_title="附着式升降脚手架",
    )
    png = drawing.export_png(
        {"la": 6.0, "lb": 1.2, "H": 20.0},
        "elevation",
        module_key="attached-lifting-scaffold",
        module_title="附着式升降脚手架",
    )
    assert b"SECTION" in dxf[:200]
    assert b"EOF" in dxf[-200:]
    assert png.startswith(b"\x89PNG")
    assert len(png) > 20_000


@pytest.mark.parametrize(
    ("module_key", "module_title", "params"),
    [
        ("full-hall-scaffold", "满堂脚手架", {"H": 12.0, "la": 1.2, "lb": 1.2, "h": 1.5}),
        ("door-scaffold", "门式钢管脚手架", {"H": 20.0, "frameWidth": 1.219, "frameBay": 1.8, "stepHeight": 1.93}),
        ("cantilever-scaffold", "型钢悬挑脚手架", {"L": 1.5, "armLength": 1.2, "H": 24.0, "la": 1.5, "lb": 0.9, "h": 1.8}),
        ("suspended-basket", "高处作业吊篮", {"platformSpan": 6.0, "platformWeight": 450.0}),
        ("attached-lifting-scaffold", "附着式升降脚手架", {"H": 65.0, "h": 1.8, "la": 1.5, "lb": 0.8, "n": 8, "k": 4}),
        ("ground-operation-platform", "落地式操作平台", {"H": 4.0, "length": 3.0, "width": 3.0, "la": 0.9, "lb": 0.9}),
        ("cantilever-operation-platform", "悬挑式操作平台", {"platformLength": 3.9, "overhangLength": 3.5, "anchorLength": 1.5}),
    ],
)
def test_every_scaffold_module_dispatches_to_specialized_geometry(
    module_key,
    module_title,
    params,
):
    g = drawing.build_geometry_for_module(module_key, module_title, params, "elevation")
    assert g["view"] in {"elevation", "side", "section"}
    assert {layer["id"] for layer in g["layers"]} == {
        "upright",
        "level",
        "brace",
        "dim",
    }
    texts = [
        item["text"]
        for layer in g["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    ]
    assert any(module_title in text for text in texts)
    assert any("非施工图" in text for text in texts)


@pytest.mark.parametrize("view", ["elevation", "plan"])
def test_geometry_bounds_positive(view):
    g = drawing.build_geometry(PARAMS, view)
    assert g["bounds"]["maxX"] > g["bounds"]["minX"]
    assert g["bounds"]["maxY"] > g["bounds"]["minY"]
