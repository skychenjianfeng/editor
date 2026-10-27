import pytest

from calc_core import cantilever_scaffold as cs


def test_spec_shape():
    spec = cs.param_spec()
    assert spec["module"] == "cantilever-scaffold"
    assert spec["standard"] == "JGJ 130-2011"
    assert spec["verified"] is False

    fields = {f["key"]: f for g in spec["groups"] for f in g["fields"]}
    assert {
        "q", "L", "W_mm3", "phiB", "I_mm4", "E", "f", "anchorN", "anchorAs",
        "anchorFy", "webArea", "tauAllow", "armLength", "K",
    } <= fields.keys()
    assert fields["W_mm3"]["default"] == pytest.approx(141000)
    assert fields["phiB"]["default"] == pytest.approx(0.9)
    assert "待复核" in fields["phiB"]["clause"]
    assert fields["I_mm4"]["default"] == pytest.approx(11300000)


def test_default_run_has_six_passing_checks():
    payload = cs.run({})
    assert payload["module"] == "cantilever-scaffold"
    assert payload["standard"] == "JGJ 130-2011"
    assert set(payload) == {
        "run_id", "module", "params", "verified", "standard", "standards",
        "summary", "results", "derived", "assumptions",
    }
    assert payload["summary"]["total"] == 6
    assert payload["summary"]["failed"] == 0

    keys = {r["key"] for r in payload["results"]}
    assert keys == {
        "cantilever_bending", "cantilever_global_stability",
        "cantilever_deflection", "anchor_tension", "cantilever_shear",
        "anchor_overturning",
    }
    assert all(r["ok"] for r in payload["results"])


def test_low_phi_b_fails_global_stability():
    payload = cs.run({"phiB": 0.1})
    stability = next(
        r for r in payload["results"] if r["key"] == "cantilever_global_stability"
    )
    assert stability["ok"] is False
    assert stability["clause"].startswith("JGJ 130-2011 5.6.4")


def test_multiple_anchor_points_apply_085_reduction():
    payload = cs.run({"anchorN": 2})
    anchor = next(r for r in payload["results"] if r["key"] == "anchor_tension")
    unreduced = 2 * 314.0 * 210.0 / 1000.0
    assert payload["derived"]["anchor_reduction_factor"] == pytest.approx(0.85)
    assert anchor["limit"] == pytest.approx(unreduced * 0.85, abs=0.01)
    assert "0.85" in anchor["detail"]
    assert "5.6.7" in anchor["detail"]


def test_single_anchor_point_has_no_reduction():
    payload = cs.run({"anchorN": 1})
    anchor = next(r for r in payload["results"] if r["key"] == "anchor_tension")
    single_capacity = 1 * 314.0 * 210.0 / 1000.0
    assert payload["derived"]["anchor_reduction_factor"] == pytest.approx(1.0)
    assert anchor["limit"] == pytest.approx(single_capacity, abs=0.01)
    assert "不折减" in anchor["detail"]


def test_increased_length_fails_bending():
    payload = cs.run({"L": 5.0})
    bending = next(r for r in payload["results"] if r["key"] == "cantilever_bending")
    assert bending["ok"] is False


def test_reduced_section_modulus_fails_bending():
    payload = cs.run({"W_mm3": 1000.0})
    bending = next(r for r in payload["results"] if r["key"] == "cantilever_bending")
    assert bending["ok"] is False
