import pytest

from calc_core import drawing


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize("view", ["elevation", "plan", "side", "section"])
def test_tie_member_has_specialized_geometry(view):
    geometry = drawing.build_geometry_for_module(
        "scaffold-tie-member",
        "连墙件计算",
        {"H": 24.0, "h": 1.8, "la": 1.5, "lb": 0.9, "tieLength": 0.9},
        view,
    )
    assert geometry["view"] == view
    text = "\n".join(
        item["text"]
        for layer in geometry["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    )
    assert "连墙件计算" in text
    assert "参数化示意" in text
    assert "建筑墙面" in text
    if view == "elevation":
        assert "竖向间距" in text
    elif view == "plan":
        assert "水平间距" in text
    else:
        assert "计算长度" in text


def test_tie_member_png_and_dxf_export_are_valid():
    png = drawing.export_png(
        {"H": 24.0},
        "plan",
        module_key="scaffold-tie-member",
        module_title="连墙件计算",
    )
    dxf = drawing.export_dxf(
        {"H": 24.0},
        "elevation",
        module_key="scaffold-tie-member",
        module_title="连墙件计算",
    )
    assert png.startswith(PNG_SIGNATURE)
    assert b"SECTION" in dxf[:200]
