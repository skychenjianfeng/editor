import math

import pytest

from calc_core import scaffold_fastener as sf


def test_param_spec_shape():
    spec = sf.param_spec()
    assert spec["module"] == "scaffold-fastener"
    assert spec["verified"] is False
    assert len(spec["groups"]) == 3
    fields = [f for g in spec["groups"] for f in g["fields"]]
    assert len(fields) == 36
    assert {f["key"] for f in fields} >= {"h", "la", "lb", "H", "wind", "z", "terrain", "phiWind"}


def test_default_run_has_ten_checks_with_one_failure():
    payload = sf.run({})
    assert payload["summary"]["total"] == 29
    assert payload["summary"]["failed"] == 2
    assert payload["verified"] is False
    first = payload["results"][0]
    assert first["clause"] == "CECS 699-2020 5.2.6"
    assert first["ok"] is False


def test_standards_coverage_declared():
    payload = sf.run({})
    applied = {s["code"] for s in payload["standards"]["applied"]}
    missing = {s["code"] for s in payload["standards"]["missing"]}
    assert "JGJ 130-2011" in applied
    assert "JGJ 80-2016" in applied
    assert {"GB 55023-2022", "GB 51210-2016", "CECS 699-2020"} <= applied
    assert missing == set()
    assert len(payload["standards"]["gaps"]) >= 2
    assert payload["standards"]["complete"] is True


def test_deflection_checks_present_and_pass():
    payload = sf.run({})
    results = {r["key"]: r for r in payload["results"]}
    assert results["ledger_long_deflection"]["ok"] is True
    assert results["ledger_trans_deflection"]["ok"] is True
    assert results["ledger_long_deflection"]["limit"] == pytest.approx(10.0)
    assert results["tie_coupler_slip"]["ok"] is False
    assert results["tie_coupler_slip"]["control"] is True
    assert results["brace_construct"]["ok"] is True
    assert results["tie_area"]["ok"] is True
    assert results["tie_connection"]["ok"] is True
    assert results["tie_offset"]["ok"] is True
    assert results["tie_first_step"]["ok"] is True
    assert results["sweep_bar"]["ok"] is True
    assert results["brace_angle"]["ok"] is True
    assert results["rail_height"]["ok"] is True
    assert results["toe_board"]["ok"] is True
    assert results["safety_net"]["ok"] is True
    assert results["brace_width_max"]["ok"] is True
    assert results["brace_layout"]["ok"] is True
    assert results["free_height"]["ok"] is True
    assert results["tie_spacing"]["ok"] is True
    assert results["board_bending"]["ok"] is True
    assert results["board_deflection"]["ok"] is True


def test_phi_table_matches_appendix_a():
    assert sf.phi_value(142) == pytest.approx(0.34, abs=1e-3)
    assert sf.phi_value(196) == pytest.approx(0.188, abs=1e-3)
    assert sf.phi_value(0) == pytest.approx(1.0, abs=1e-3)
    assert sf.phi_value(999) == pytest.approx(sf.phi_value(250), abs=1e-6)


def test_muz_interpolates_gb50009():
    assert sf.muz_value(5, "C") == pytest.approx(0.65, abs=1e-6)
    assert sf.muz_value(24, "B") == pytest.approx(1.294, abs=1e-3)
    assert sf.muz_value(200, "B") == pytest.approx(2.00, abs=1e-6)


def test_mus_matches_table_4_2_6():
    assert sf.mus_value("全封闭", "敞开、框架和开洞墙", 0.8) == pytest.approx(1.04)
    assert sf.mus_value("全封闭", "全封闭墙", 0.8) == pytest.approx(0.8)
    assert sf.mus_value("敞开", "全封闭墙", 0.8) == pytest.approx(0.96)


def test_mu_table_covers_layout_and_tie():
    assert sf.mu_value(1.05, "双排", "两步三跨") == pytest.approx(1.50)
    assert sf.mu_value(1.30, "双排", "两步三跨") == pytest.approx(1.55)
    assert sf.mu_value(1.55, "双排", "三步三跨") == pytest.approx(1.80)
    assert sf.mu_value(0.9, "单排", "两步三跨") == pytest.approx(1.80)
    assert sf.mu_value(0.9, "单排", "三步三跨") == pytest.approx(2.00)
    assert sf.mu_value(1.175, "双排", "两步三跨") == pytest.approx(1.525, abs=1e-3)


def test_open_scaffold_phi_uses_appendix_a05():
    assert sf.phi_a05_value(1.8, 1.5) == pytest.approx(0.090, abs=1e-3)
    assert sf.phi_a05_value(1.8, 2.0) == pytest.approx(0.080, abs=1e-3)
    payload = sf.run({"enclosure": "敞开"})
    assert payload["derived"]["phi_wind_used"] < 0.2


def test_tie_net_area_increases_stress():
    gross = sf.run({})["results"][2]["value"]
    net = sf.run({"tieNetArea": 300})["results"][2]["value"]
    assert net > gross
    assert net / gross == pytest.approx(424.1 / 300, rel=1e-2)


def test_slenderness_uses_k1_and_stability_uses_k1155():
    derived = sf.run({})["derived"]
    assert derived["lambda_check"] / derived["lambda_stability"] == pytest.approx(1 / 1.155, abs=1e-3)


def test_gk_matches_appendix_a_at_table_point():
    assert sf.gk_value(1.8, 1.5) == pytest.approx(0.1295, abs=1e-6)
    assert sf.gk_value(2.0, 1.2) == pytest.approx(0.1134, abs=1e-6)


def test_larger_step_increases_upright_stress():
    base = sf.run({"h": 1.8})["results"][0]["value"]
    taller = sf.run({"h": 2.0})["results"][0]["value"]
    assert taller > base


def test_backfill_foundation_applies_04_factor():
    normal = sf.run({"foundation": "黏土", "fg": 140})["results"][7]
    backfill = sf.run({"foundation": "回填土", "fg": 140})["results"][7]
    assert normal["limit"] == pytest.approx(140.0)
    assert backfill["limit"] == pytest.approx(56.0)


def test_foundation_uses_standard_axial_force():
    payload = sf.run({"baseArea": 0.25})
    ground = payload["results"][7]
    expected = payload["derived"]["Nk_kN"] / 0.25
    assert ground["value"] == pytest.approx(expected, rel=1e-3)


def test_wind_moment_uses_equation_5_2_9():
    payload = sf.run({})
    d = payload["derived"]
    wk = sf.muz_value(24, "B") * sf.mus_value("全封闭", "敞开、框架和开洞墙", 0.8) * 0.25
    hc = 2 * 1.8 * 1000.0
    expected = 0.9 * 0.05 * 0.6 * wk * 1.5 * hc**2
    assert d["Mw_Nmm"] == pytest.approx(expected, abs=1.0)


def test_unknown_steel_rejected():
    with pytest.raises(ValueError):
        sf.run({"steel": "φ60×3.0"})


@pytest.mark.parametrize(
    "params",
    [
        {"tie": "五步十跨"},
        {"layout": "三排"},
        {"terrain": "E"},
        {"enclosure": "半敞开"},
    ],
)
def test_unknown_enums_rejected(params):
    with pytest.raises(ValueError):
        sf.run(params)
