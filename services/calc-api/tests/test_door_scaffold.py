import pytest

from calc_core import door_scaffold as ds


def test_spec_shape_and_parameters():
    spec = ds.param_spec()
    assert spec["module"] == "door-scaffold"
    assert spec["title"] == "门式钢管脚手架"
    assert spec["standard"] == "JGJ 128-2010"
    assert spec["verified"] is False

    fields = {
        field["key"]
        for group in spec["groups"]
        for field in group["fields"]
    }
    assert {
        "H",
        "g1",
        "g2",
        "sumNQk",
        "phi",
        "A1",
        "f",
        "frameWidth",
        "beamQd",
        "beamQk",
        "beamW",
        "beamI",
        "tieL1",
        "tieH1",
        "tieNv",
        "fak",
        "kc",
        "Ad",
        "crossBracingBothSides",
        "crossBracingLocked",
        "connectingRodsInstalled",
        "connectingRodClearance",
        "lockingArmOrPositivePin",
        "baseInstalled",
        "hangingBoardsContinuous",
        "boardsFallPrevention",
        "boardHoleDiameter",
        "braceAtCornersAndEnds",
        "braceMaxInterval",
        "braceContinuousFullHeight",
        "braceFullOuterFace",
        "braceAngle",
        "braceLapLength",
        "braceLapFasteners",
        "braceWidthSpans",
        "braceWidth",
        "horizontalTopAndTieLevels",
        "horizontalSpacingSteps",
        "horizontalContinuous",
        "horizontalCornerOpeningEachStep",
        "horizontalAttachedToPosts",
        "tieNearTransomOffset",
        "tieFixedToPost",
        "tieAtCornerAndOpenEnds",
        "tieCornerOpeningVerticalSpacing",
        "tieScaffoldEndLower",
        "tieSlope",
    } <= fields
    assert all(field["clause"].startswith("JGJ 128-2010") for group in spec["groups"] for field in group["fields"])
    assert all(
        {"key", "label", "unit", "default", "clause"} <= set(field)
        for group in spec["groups"]
        for field in group["fields"]
    )


def test_default_run_has_nine_passing_checks():
    payload = ds.run({})
    assert payload["module"] == "door-scaffold"
    assert payload["standard"] == "JGJ 128-2010"
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

    results = {result["key"]: result for result in payload["results"]}
    assert set(results) == {
        "ledger_stability",
        "beam_bending",
        "beam_deflection",
        "tie_capacity",
        "foundation_bearing",
        "assembly_construction",
        "brace_configuration",
        "horizontal_reinforcement",
        "tie_detail",
    }
    assert all(result["ok"] for result in results.values())

    assert results["ledger_stability"]["value"] == pytest.approx(14.64)
    assert results["ledger_stability"]["limit"] == pytest.approx(40.16)
    assert results["beam_bending"]["value"] == pytest.approx(164.09)
    assert results["beam_bending"]["limit"] == pytest.approx(205.0)
    assert results["beam_deflection"]["value"] == pytest.approx(4.13)
    assert results["beam_deflection"]["limit"] == pytest.approx(4.88)
    assert results["tie_capacity"]["value"] == pytest.approx(9.81)
    assert results["tie_capacity"]["limit"] == pytest.approx(30.0)
    assert results["foundation_bearing"]["value"] == pytest.approx(91.92)
    assert results["foundation_bearing"]["limit"] == pytest.approx(120.0)
    for key in {
        "assembly_construction",
        "brace_configuration",
        "horizontal_reinforcement",
        "tie_detail",
    }:
        assert results[key]["ratio"] == pytest.approx(1.0)
        assert results[key]["value"] == results[key]["limit"]
        assert all(check["ok"] for check in results[key]["checks"])


def test_overload_and_heavy_beam_fail_ledger_and_beam_checks():
    payload = ds.run({"sumNQk": 100.0, "beamQd": 20.0, "beamQk": 20.0})
    failed = {result["key"] for result in payload["results"] if not result["ok"]}
    assert {"ledger_stability", "beam_bending", "beam_deflection"} <= failed
    assert payload["summary"]["control_failed"] >= 2


def test_weak_tie_and_soft_foundation_fail():
    payload = ds.run({"tieNv": 5.0, "fak": 100.0, "kc": 0.8})
    results = {result["key"]: result for result in payload["results"]}
    assert results["tie_capacity"]["ok"] is False
    assert results["foundation_bearing"]["ok"] is False
    assert payload["summary"]["failed"] >= 2


def test_assembly_and_locking_arm_failure():
    payload = ds.run(
        {
            "crossBracingBothSides": False,
            "lockingArmOrPositivePin": False,
            "boardHoleDiameter": 26.0,
        }
    )
    results = {result["key"]: result for result in payload["results"]}
    assert results["assembly_construction"]["ok"] is False
    assert results["assembly_construction"]["ratio"] < 1.0
    assert {"门架两侧交叉支撑", "锁臂或插销式/弹销式连接"} <= {
        check["label"]
        for check in results["assembly_construction"]["checks"]
        if not check["ok"]
    }


def test_brace_configuration_failure():
    payload = ds.run({"braceAngle": 70.0, "braceMaxInterval": 20.0})
    results = {result["key"]: result for result in payload["results"]}
    assert results["brace_configuration"]["ok"] is False
    failed_labels = {
        check["label"]
        for check in results["brace_configuration"]["checks"]
        if not check["ok"]
    }
    assert any("夹角" in label for label in failed_labels)
    assert any("间隔" in label for label in failed_labels)


def test_horizontal_reinforcement_failure():
    payload = ds.run(
        {
            "horizontalSpacingSteps": 3.0,
            "horizontalContinuous": False,
        }
    )
    results = {result["key"]: result for result in payload["results"]}
    assert results["horizontal_reinforcement"]["ok"] is False
    assert results["horizontal_reinforcement"]["ratio"] < 1.0


def test_tie_detail_failure():
    payload = ds.run(
        {
            "tieNearTransomOffset": 250.0,
            "tieFixedToPost": False,
            "tieCornerOpeningVerticalSpacing": 4.5,
        }
    )
    results = {result["key"]: result for result in payload["results"]}
    assert results["tie_detail"]["ok"] is False
    assert results["tie_detail"]["ratio"] < 1.0
