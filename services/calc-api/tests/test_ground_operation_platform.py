import pytest

from calc_core import ground_operation_platform as gop


def test_spec_shape_and_limits():
    spec = gop.param_spec()
    assert spec["module"] == "ground-operation-platform"
    assert spec["title"] == "落地式操作平台"
    assert spec["standard"] == "JGJ 80-2016"
    assert spec["verified"] is False

    fields = {
        field["key"]: field
        for group in spec["groups"]
        for field in group["fields"]
    }
    assert {
        "platformKind",
        "la",
        "lb",
        "h",
        "H",
        "length",
        "width",
        "constructionLoad",
        "materialLoad",
        "panelSpan",
        "panelThickness",
        "joistW",
        "uprightA",
        "uprightPhi",
        "fk",
        "kc",
        "baseArea",
        "couplerRc",
        "guardrailHeight",
        "toeBoardHeight",
        "tieSpacing",
        "ladderStepSpacing",
        "doubleHorizontalRails",
        "independentAndRigidConnection",
        "braceInstalled",
        "ladderInstalled",
    } <= fields.keys()
    assert fields["platformKind"]["options"] == ["施工平台", "接料平台"]
    assert fields["la"]["default"] == pytest.approx(0.9)
    assert fields["lb"]["default"] == pytest.approx(0.9)
    assert fields["h"]["default"] == pytest.approx(1.5)
    assert fields["H"]["default"] == pytest.approx(4.0)
    assert fields["constructionLoad"]["default"] == pytest.approx(4.0)
    assert fields["materialLoad"]["default"] == pytest.approx(5.0)
    assert fields["fk"]["default"] == pytest.approx(100.0)
    assert fields["kc"]["default"] == pytest.approx(0.40)
    assert fields["baseArea"]["default"] == pytest.approx(0.25)
    assert fields["couplerRc"]["default"] == pytest.approx(8.0)
    assert fields["doubleHorizontalRails"]["type"] == "boolean"
    assert "6.1.4" in fields["guardrailHeight"]["clause"]
    assert "6.3.1-5" in fields["tieSpacing"]["clause"]


def test_default_run_has_eight_items_and_keeps_geometry_failure():
    payload = gop.run({})
    assert set(payload) == {
        "run_id",
        "module",
        "params",
        "verified",
        "standard",
        "standards",
        "summary",
        "results",
        "derived",
        "assumptions",
    }
    assert payload["module"] == "ground-operation-platform"
    assert payload["standard"] == "JGJ 80-2016"
    assert payload["verified"] is False
    assert payload["standards"]["complete"] is False
    assert payload["standards"]["gaps"]

    results = {result["key"]: result for result in payload["results"]}
    assert set(results) == {
        "geometry_construction",
        "panel_bending",
        "panel_deflection",
        "joist_bending",
        "upright_stability",
        "foundation_bearing",
        "coupler_slip",
        "guardrail_tie_configuration",
    }
    assert payload["derived"]["platform_area_m2"] == pytest.approx(9.0)
    assert payload["derived"]["aspect_ratio"] == pytest.approx(4.0 / 3.0, rel=1e-3)
    assert payload["derived"]["live_load_kN_m2"] == pytest.approx(4.0)
    assert results["geometry_construction"]["ok"] is False
    assert all(
        results[key]["ok"]
        for key in (
            "panel_bending",
            "panel_deflection",
            "joist_bending",
            "upright_stability",
            "foundation_bearing",
            "coupler_slip",
            "guardrail_tie_configuration",
        )
    )
    assert payload["summary"]["failed"] == 1


@pytest.mark.parametrize(
    ("platform_kind", "construction_load", "material_load", "should_pass"),
    [
        ("施工平台", 2.0, 0.0, True),
        ("施工平台", 2.01, 0.0, False),
        ("接料平台", 0.0, 3.0, True),
        ("接料平台", 0.0, 3.01, False),
    ],
)
def test_platform_load_boundaries(
    platform_kind,
    construction_load,
    material_load,
    should_pass,
):
    payload = gop.run(
        {
            "platformKind": platform_kind,
            "constructionLoad": construction_load,
            "materialLoad": material_load,
        }
    )
    result = next(
        item for item in payload["results"] if item["key"] == "geometry_construction"
    )
    assert result["ok"] is should_pass


@pytest.mark.parametrize(
    "params",
    [
        {"length": 3.2, "width": 3.2},  # 面积超过 10m²
        {"H": 15.1, "length": 10.0, "width": 10.0},  # 高度超过 15m
        {"H": 7.51, "length": 3.0, "width": 3.0},  # 高宽比超过 2.5
    ],
)
def test_geometry_boundaries_fail(params):
    payload = gop.run({"constructionLoad": 2.0, "materialLoad": 0.0, **params})
    result = next(
        item for item in payload["results"] if item["key"] == "geometry_construction"
    )
    assert result["ok"] is False
    assert payload["summary"]["control_failed"] >= 1


def test_member_failures_are_reported():
    payload = gop.run(
        {
            "constructionLoad": 2.0,
            "materialLoad": 0.0,
            "panelThickness": 1.0,
            "joistW": 100.0,
            "uprightPhi": 0.01,
        }
    )
    failed = {result["key"] for result in payload["results"] if not result["ok"]}
    assert {
        "panel_bending",
        "panel_deflection",
        "joist_bending",
        "upright_stability",
    } <= failed


@pytest.mark.parametrize(
    ("base_area", "should_pass"),
    [
        (((0.35 + 2.0) * 0.9**2 + 0.13 * 4.0) / 40.0, True),  # 恰在 kc·fk 边界
        (0.0605, False),  # 面积减小，压力超过上限
        (0.0610, True),  # 面积增大，压力低于上限
    ],
)
def test_foundation_bearing_boundaries(base_area, should_pass):
    payload = gop.run(
        {
            "constructionLoad": 2.0,
            "materialLoad": 0.0,
            "fk": 100.0,
            "kc": 0.4,
            "baseArea": base_area,
        }
    )
    result = next(
        item for item in payload["results"] if item["key"] == "foundation_bearing"
    )
    assert result["ok"] is should_pass


@pytest.mark.parametrize(
    ("coupler_rc", "should_pass"),
    [
        (1.1 * (1.2 * 0.35 + 1.4 * 2.0) * 0.3 * 0.9, True),  # 恰在 Rc 边界
        (0.956, False),
        (1.0, True),
    ],
)
def test_coupler_slip_boundaries(coupler_rc, should_pass):
    payload = gop.run(
        {
            "constructionLoad": 2.0,
            "materialLoad": 0.0,
            "couplerRc": coupler_rc,
        }
    )
    result = next(
        item for item in payload["results"] if item["key"] == "coupler_slip"
    )
    assert result["ok"] is should_pass


@pytest.mark.parametrize(
    ("overrides", "should_pass"),
    [
        (
            {
                "guardrailHeight": 1.2,
                "toeBoardHeight": 180.0,
                "tieSpacing": 4.0,
                "ladderStepSpacing": 400.0,
            },
            True,
        ),
        ({"guardrailHeight": 1.19}, False),
        ({"toeBoardHeight": 179.0}, False),
        ({"tieSpacing": 4.01}, False),
        ({"independentAndRigidConnection": False}, False),
        ({"braceInstalled": False}, False),
    ],
)
def test_guardrail_tie_configuration_boundaries(overrides, should_pass):
    payload = gop.run(
        {
            "constructionLoad": 2.0,
            "materialLoad": 0.0,
            **overrides,
        }
    )
    result = next(
        item
        for item in payload["results"]
        if item["key"] == "guardrail_tie_configuration"
    )
    assert result["ok"] is should_pass
