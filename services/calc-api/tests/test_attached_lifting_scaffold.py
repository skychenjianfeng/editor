import pytest

from calc_core import attached_lifting_scaffold as als


def test_spec_shape_and_pmsc_inputs():
    spec = als.param_spec()
    assert spec["module"] == "attached-lifting-scaffold"
    assert spec["title"] == "附着式升降脚手架"
    assert spec["standard"] == "JGJ 202-2010"
    assert spec["verified"] is False

    fields = {
        field["key"]: field
        for group in spec["groups"]
        for field in group["fields"]
    }
    assert {
        "H",
        "storeyHeight",
        "h",
        "la",
        "lb",
        "n",
        "k",
        "overhang",
        "cantileverHeight",
        "attachBoltCount",
        "antiFallCapacity",
        "antiFallSteelRodDiameter",
        "antiFallDustProtection",
        "antiFallSensitivity",
        "syncLoadStopPct",
        "liftingDeviceCapacity",
        "suspensionBeamLoad",
        "suspensionBeamLength",
        "suspensionBeamSectionModulus",
        "suspensionBeamSteelStrength",
        "guideRailUtilization",
        "facadeBraceFullHeight",
        "facadeBraceNodeFastened",
        "facadeBraceAngle",
        "overhangSymmetricTie",
        "overhangTieAngle",
    } <= fields.keys()
    assert fields["H"]["default"] == pytest.approx(65.0)
    assert fields["storeyHeight"]["default"] == pytest.approx(3.6)
    assert fields["h"]["default"] == pytest.approx(1.8)
    assert fields["la"]["default"] == pytest.approx(1.5)
    assert fields["lb"]["default"] == pytest.approx(0.8)
    assert fields["n"]["default"] == pytest.approx(8.0)
    assert fields["k"]["default"] == pytest.approx(4.0)
    assert all(
        field["clause"].startswith("JGJ 202-2010")
        for group in spec["groups"]
        for field in group["fields"]
    )


def test_default_run_has_nine_checks_and_declares_gaps():
    payload = als.run({})
    assert payload["module"] == "attached-lifting-scaffold"
    assert payload["standard"] == "JGJ 202-2010"
    assert payload["verified"] is False
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
    assert payload["summary"] == {"total": 9, "failed": 0, "control_failed": 0}
    assert payload["standards"]["complete"] is False
    assert payload["standards"]["gaps"]
    assert payload["assumptions"]

    results = {result["key"]: result for result in payload["results"]}
    assert set(results) == {
        "wind_horizontal_brace",
        "main_frame_strength",
        "wall_bolt_capacity",
        "anti_fall_device",
        "sync_and_geometry",
        "lifting_device_capacity",
        "suspension_beam_strength",
        "guide_rail_capacity",
        "brace_full_height",
    }
    assert all(result["ok"] for result in results.values())
    assert results["sync_and_geometry"]["ratio"] == pytest.approx(1.0)
    assert payload["derived"]["bodyHeight_m"] == pytest.approx(14.4)
    assert payload["derived"]["wk_kN_m2"] == pytest.approx(0.372)
    assert payload["derived"]["liftingDeviceDemand_kN"] == pytest.approx(
        26.175,
        abs=0.01,
    )
    assert payload["derived"]["suspensionBeamBendingMoment_kNm"] == pytest.approx(
        39.0
    )
    assert payload["derived"]["suspensionBeamMomentCapacity_kNm"] == pytest.approx(
        45.1
    )


def test_strong_wind_with_weak_brace_fails_horizontal_check():
    payload = als.run(
        {
            "w0": 3.0,
            "bracePhi": 0.10,
            "braceArea": 100.0,
        }
    )
    results = {result["key"]: result for result in payload["results"]}
    assert results["wind_horizontal_brace"]["ok"] is False
    assert payload["summary"]["control_failed"] >= 1


def test_weak_wall_bolt_and_concrete_bearing_fail_attachment_check():
    payload = als.run(
        {
            "attachBoltCount": 1.0,
            "attachBoltD": 8.0,
            "attachBoltDe": 6.0,
            "attachBoltFtb": 50.0,
            "attachBoltFvb": 50.0,
            "concreteWidth": 50.0,
            "concreteFc": 5.0,
        }
    )
    results = {result["key"]: result for result in payload["results"]}
    assert results["wall_bolt_capacity"]["ok"] is False
    assert payload["summary"]["failed"] >= 1


def test_lifting_device_rated_capacity_is_insufficient():
    payload = als.run({"liftingDeviceCapacity": 20.0})
    results = {result["key"]: result for result in payload["results"]}
    assert results["lifting_device_capacity"]["value"] == pytest.approx(26.18)
    assert results["lifting_device_capacity"]["ok"] is False
    assert payload["summary"]["control_failed"] >= 1


def test_suspension_beam_bending_strength_fails():
    payload = als.run({"suspensionBeamLoad": 40.0})
    results = {result["key"]: result for result in payload["results"]}
    assert results["suspension_beam_strength"]["value"] == pytest.approx(104.0)
    assert results["suspension_beam_strength"]["limit"] == pytest.approx(45.1)
    assert results["suspension_beam_strength"]["ok"] is False


def test_guide_rail_external_utilization_must_not_exceed_one():
    payload = als.run({"guideRailUtilization": 1.01})
    results = {result["key"]: result for result in payload["results"]}
    assert results["guide_rail_capacity"]["value"] == pytest.approx(1.01)
    assert results["guide_rail_capacity"]["ok"] is False
    assert "外部专项验算回填项" in results["guide_rail_capacity"]["detail"]


def test_facade_brace_construction_fails_when_not_full_height():
    payload = als.run(
        {
            "facadeBraceFullHeight": 0.0,
            "facadeBraceNodeFastened": 0.0,
        }
    )
    results = {result["key"]: result for result in payload["results"]}
    assert results["brace_full_height"]["ok"] is False
    assert results["brace_full_height"]["value"] == pytest.approx(0.0)
    assert "全高连续=0" in results["brace_full_height"]["detail"]


def test_anti_fall_accessories_and_steel_rod_are_checked():
    payload = als.run(
        {
            "antiFallSteelRodDiameter": 20.0,
            "antiFallDustProtection": 0.0,
            "antiFallSensitivity": 0.0,
        }
    )
    results = {result["key"]: result for result in payload["results"]}
    assert results["anti_fall_device"]["ok"] is False
    assert "直径≥25mm" in results["anti_fall_device"]["detail"]
