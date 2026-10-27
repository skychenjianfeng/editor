import pytest

from calc_core import full_hall_scaffold as fhs


def test_spec_shape():
    spec = fhs.param_spec()
    assert spec["module"] == "full-hall-scaffold"
    assert spec["title"] == "满堂脚手架"
    assert spec["standard"] == "JGJ 130-2011"
    assert spec["verified"] is False

    fields = {field["key"]: field for group in spec["groups"] for field in group["fields"]}
    assert {
        "h",
        "la",
        "lb",
        "H",
        "lengthX",
        "lengthY",
        "dead",
        "live",
        "gk",
        "A_mm2",
        "I_mm4",
        "W_mm3",
        "i_mm",
        "fg",
        "baseArea",
        "couplerRc",
        "verticalBraceSpacing",
        "verticalBraceCoverageComplete",
        "horizontalBraceSpacing",
        "horizontalBraceLayoutComplete",
        "braceWidth",
        "braceAngle",
        "tieHorizontalSpacing",
        "tieVerticalSpacing",
        "tieArrangementComplete",
        "ladderInstalled",
        "ladderStepSpacing",
        "boardSupportSpacing",
        "boardFullCoverageAndFixed",
    } <= fields.keys()
    assert fields["h"]["default"] == pytest.approx(1.5)
    assert fields["W_mm3"]["default"] == pytest.approx(5260.0)
    assert fields["couplerRc"]["default"] == pytest.approx(8.0)
    assert fields["couplerRc"]["unit"] == "kN"
    assert fields["verticalBraceCoverageComplete"]["type"] == "boolean"

    new_keys = {
        "couplerRc",
        "verticalBraceSpacing",
        "verticalBraceCoverageComplete",
        "horizontalBraceSpacing",
        "horizontalBraceLayoutComplete",
        "braceWidth",
        "braceAngle",
        "tieHorizontalSpacing",
        "tieVerticalSpacing",
        "tieArrangementComplete",
        "ladderInstalled",
        "ladderStepSpacing",
        "boardSupportSpacing",
        "boardFullCoverageAndFixed",
    }
    for key in new_keys:
        assert {"label", "type", "unit", "default", "min", "max", "clause"} <= fields[key].keys()
        assert fields[key]["clause"]


def test_default_run_has_nine_passing_checks():
    payload = fhs.run({})
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
    assert payload["module"] == "full-hall-scaffold"
    assert payload["standard"] == "JGJ 130-2011"
    assert payload["summary"] == {"total": 9, "failed": 0, "control_failed": 0}
    assert {result["key"] for result in payload["results"]} == {
        "ledger_bending",
        "ledger_deflection",
        "upright_stability",
        "upright_slenderness_construction",
        "foundation_bearing",
        "coupler_slip",
        "brace_configuration",
        "tie_requirement",
        "ladder_board_configuration",
    }
    assert all(result["ok"] for result in payload["results"])
    assert payload["standards"]["complete"] is False
    assert payload["standards"]["applied"][0]["clauses"]
    assert payload["standards"]["gaps"]


def test_reduced_horizontal_bar_section_fails_bending_and_deflection():
    payload = fhs.run({"W_mm3": 1000.0, "I_mm4": 10000.0})
    results = {result["key"]: result for result in payload["results"]}
    assert results["ledger_bending"]["ok"] is False
    assert results["ledger_deflection"]["ok"] is False
    assert payload["summary"]["failed"] >= 2


def test_excessive_height_and_small_foundation_fail_construction_and_bearing():
    payload = fhs.run({"H": 30.0, "fg": 20.0, "baseArea": 0.10})
    results = {result["key"]: result for result in payload["results"]}
    assert results["upright_slenderness_construction"]["ok"] is False
    assert results["foundation_bearing"]["ok"] is False
    assert payload["summary"]["failed"] >= 2


def test_coupler_slip_fails_above_user_capacity():
    payload = fhs.run({"couplerRc": 2.0})
    results = {result["key"]: result for result in payload["results"]}

    assert results["coupler_slip"]["value"] == pytest.approx(2.55, abs=0.01)
    assert results["coupler_slip"]["limit"] == pytest.approx(2.0)
    assert results["coupler_slip"]["ok"] is False
    assert payload["derived"]["R_coupler_kN"] == pytest.approx(2.55, abs=0.01)


def test_brace_configuration_fails_when_required_layout_is_missing():
    payload = fhs.run(
        {
            "verticalBraceSpacing": 7.0,
            "verticalBraceCoverageComplete": False,
            "horizontalBraceSpacing": 8.0,
            "horizontalBraceLayoutComplete": False,
            "braceWidth": 7.0,
            "braceAngle": 55.0,
        }
    )
    results = {result["key"]: result for result in payload["results"]}

    assert results["brace_configuration"]["ok"] is False
    assert "外周/内部覆盖或由底至顶连续" in results["brace_configuration"]["detail"]


def test_aspect_ratio_above_two_without_ties_fails():
    payload = fhs.run(
        {
            "H": 13.0,
            "lengthX": 6.0,
            "lengthY": 6.0,
            "tieArrangementComplete": False,
        }
    )
    results = {result["key"]: result for result in payload["results"]}

    assert payload["derived"]["aspect_ratio"] == pytest.approx(2.17)
    assert results["upright_slenderness_construction"]["ok"] is True
    assert results["tie_requirement"]["ok"] is False
    assert "高宽比 2.17>2" in results["tie_requirement"]["detail"]


def test_ladder_and_board_boundary_failure():
    payload = fhs.run(
        {
            "ladderInstalled": False,
            "ladderStepSpacing": 350.0,
            "boardSupportSpacing": 0.7,
            "boardFullCoverageAndFixed": False,
        }
    )
    results = {result["key"]: result for result in payload["results"]}

    assert results["ladder_board_configuration"]["ok"] is False
    assert "踏步 350.0mm≤300mm" in results["ladder_board_configuration"]["detail"]
    assert "支承水平杆 0.70m≤la/2=0.60m" in results["ladder_board_configuration"]["detail"]
