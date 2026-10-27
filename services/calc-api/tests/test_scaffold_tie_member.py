import pytest

from calc_core import scaffold_tie_member as tie


def _result(payload, key):
    return next(row for row in payload["results"] if row["key"] == key)


def test_param_spec_contract():
    spec = tie.param_spec()
    assert spec["module"] == "scaffold-tie-member"
    assert spec["title"] == "连墙件计算"
    assert spec["verified"] is False
    fields = {
        field["key"]
        for group in spec["groups"]
        for field in group["fields"]
    }
    assert {
        "layout",
        "scaffoldType",
        "H",
        "h",
        "la",
        "tieVerticalSpacing",
        "tieHorizontalSpacing",
        "tieLength",
        "connectionType",
        "tieNv",
        "tieNetArea",
        "wind",
        "terrain",
    } <= fields


def test_default_payload_uses_jgj_wind_factor_and_axial_force_sum():
    payload = tie.run({})
    d = payload["derived"]
    assert payload["module"] == "scaffold-tie-member"
    assert payload["verified"] is False
    assert d["N0_kN"] == pytest.approx(3.0)
    assert d["Nlw_kN"] == pytest.approx(
        1.4 * d["wk_kN_m2"] * d["Aw_m2"], abs=0.05
    )
    assert d["Nl_kN"] == pytest.approx(
        d["Nlw_kN"] + d["N0_kN"], abs=0.05
    )
    assert payload["summary"]["total"] == len(payload["results"])


def test_spacing_and_height_drive_result_keys():
    payload = tie.run({})
    keys = {row["key"] for row in payload["results"]}
    assert {
        "tie_strength",
        "tie_stability",
        "tie_connection",
        "tie_coupler_slip",
        "tie_vertical_spacing",
        "tie_horizontal_spacing",
        "tie_area",
        "tie_offset",
        "tie_first_step",
        "single_row_height",
        "soft_tie_height",
    } == keys


def test_wind_pressure_increases_axial_force():
    low = tie.run({"wind": 0.2})
    high = tie.run({"wind": 0.4})
    assert high["derived"]["Nl_kN"] > low["derived"]["Nl_kN"]


def test_net_area_and_tie_length_increase_stresses():
    wide = tie.run({"tieNetArea": 600.0, "tieLength": 0.8})
    narrow = tie.run({"tieNetArea": 300.0, "tieLength": 1.6})
    assert (
        _result(narrow, "tie_strength")["value"]
        > _result(wide, "tie_strength")["value"]
    )
    assert (
        _result(narrow, "tie_stability")["value"]
        > _result(wide, "tie_stability")["value"]
    )


def test_non_coupler_connection_omits_coupler_slip():
    payload = tie.run({"connectionType": "螺栓连接"})
    keys = {row["key"] for row in payload["results"]}
    assert "tie_coupler_slip" not in keys


@pytest.mark.parametrize(
    ("overrides", "key"),
    [
        ({"tieVerticalSpacing": 5.5}, "tie_vertical_spacing"),
        ({"tieHorizontalSpacing": 5.5}, "tie_horizontal_spacing"),
        ({"tieOffset": 350.0}, "tie_offset"),
        ({"tieFromFirstStep": "否"}, "tie_first_step"),
        (
            {"H": 30.0, "layout": "单排", "scaffoldType": "单排"},
            "single_row_height",
        ),
        (
            {"H": 30.0, "connectionType": "软拉硬撑"},
            "soft_tie_height",
        ),
    ],
)
def test_construction_rules_fail(overrides, key):
    assert _result(tie.run(overrides), key)["ok"] is False


def test_cantilever_high_area_limit_is_27_square_metres():
    payload = tie.run(
        {
            "H": 55.0,
            "scaffoldType": "双排悬挑",
            "tieVerticalSpacing": 6.5,
            "tieHorizontalSpacing": 4.5,
        }
    )
    result = _result(payload, "tie_area")
    assert result["limit"] == pytest.approx(27.0)
    assert result["ok"] is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"steel": "unknown"},
        {"layout": "三排"},
        {"scaffoldType": "落地"},
        {"connectionType": "未知连接"},
        {"H": 0.0},
        {"tieNv": 0.0},
        {"wind": -0.1},
    ],
)
def test_invalid_parameters_raise_value_error(overrides):
    with pytest.raises(ValueError):
        tie.run(overrides)
