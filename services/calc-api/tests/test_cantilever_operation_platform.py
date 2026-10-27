import pytest

from calc_core import cantilever_operation_platform as cop


def _results(payload):
    return {result["key"]: result for result in payload["results"]}


def test_spec_shape_and_contract():
    spec = cop.param_spec()
    assert spec["module"] == "cantilever-operation-platform"
    assert spec["title"] == "悬挑式操作平台"
    assert spec["standard"] == "JGJ 80-2016"
    assert spec["verified"] is False

    fields = {
        field["key"]: field
        for group in spec["groups"]
        for field in group["fields"]
    }
    assert {
        "platformLength",
        "overhangLength",
        "anchorLength",
        "mainBeamW",
        "mainBeamI",
        "mainBeamSelfWeight",
        "liveLoad",
        "frontRopesPerSide",
        "rearRopesPerSide",
        "frontRopeAngle",
        "rearRopeAngle",
        "wireBreakForce",
        "wireClampCount",
        "anchorCount",
        "anchorTensionCapacity",
        "supportMomentCapacity",
        "rearSupportVerticalCapacity",
        "stabilityFactor",
        "secondaryBeamSpan",
        "secondaryBeamSpacing",
        "secondaryBeamW",
        "secondaryBeamF",
        "panelSpan",
        "panelThickness",
        "panelF",
        "weldThroat",
        "weldEffectiveLength",
        "weldStrength",
        "outerSideHigher",
        "guardrailFixed",
        "guardrailFullyEnclosed",
        "liftingRingInstalled",
        "loadBearingRingInstalled",
    } <= fields.keys()
    assert fields["platformLength"]["default"] == pytest.approx(3.9)
    assert fields["overhangLength"]["default"] == pytest.approx(3.5)
    assert fields["anchorLength"]["default"] == pytest.approx(1.5)
    assert fields["liveLoad"]["default"] == pytest.approx(5.0)
    assert fields["wireClampCount"]["default"] == pytest.approx(4.0)
    assert "6.4.2" in fields["overhangLength"]["clause"]
    assert "6.4.3" in fields["frontRopesPerSide"]["clause"]
    assert "6.4.7" in fields["wireClampCount"]["clause"]
    assert "C.0.2" in fields["secondaryBeamSpan"]["clause"]
    assert "C.0.1" in fields["panelThickness"]["clause"]
    assert "6.4.5" in fields["weldThroat"]["clause"]
    assert fields["outerSideHigher"]["type"] == "boolean"


def test_default_run_has_nine_passing_checks():
    payload = cop.run({})
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
    assert payload["module"] == "cantilever-operation-platform"
    assert payload["standard"] == "JGJ 80-2016"
    assert payload["verified"] is False
    assert payload["summary"] == {
        "total": 9,
        "failed": 0,
        "control_failed": 0,
    }

    results = _results(payload)
    assert set(results) == {
        "main_beam_bending",
        "main_beam_deflection",
        "wire_rope_capacity",
        "anchor_connection_capacity",
        "overturning_support",
        "secondary_beam_bending",
        "platform_panel_bending",
        "weld_connection",
        "guardrail_configuration",
    }
    assert all(result["ok"] for result in results.values())
    assert payload["derived"]["overhangConditionOk"] is True
    assert payload["derived"]["ropeLayoutConditionOk"] is True
    assert payload["derived"]["ropeClampConditionOk"] is True
    assert payload["derived"]["eachRopeIndependentlyCalculated"] is True
    assert payload["derived"]["frontRopeSafety"] >= 8.0
    assert payload["derived"]["rearRopeSafety"] >= 8.0
    assert payload["derived"]["panelThicknessConditionOk"] is True
    assert payload["derived"]["guardrailConfigurationOk"] is True


def test_overlong_cantilever_fails_length_construction_boundary():
    payload = cop.run({"overhangLength": 5.1})
    bending = _results(payload)["main_beam_bending"]
    assert bending["ok"] is False
    assert payload["derived"]["overhangConditionOk"] is False
    assert payload["summary"]["control_failed"] >= 1


def test_insufficient_rope_clamps_fail_wire_rope_boundary():
    payload = cop.run({"wireClampCount": 3.0})
    wire = _results(payload)["wire_rope_capacity"]
    assert wire["ok"] is False
    assert payload["derived"]["ropeClampConditionOk"] is False
    assert "不得少于4个" in cop.param_spec()["groups"][2]["fields"][-1]["label"]


def test_missing_rear_rope_fails_two_ropes_per_side_boundary():
    payload = cop.run({"rearRopesPerSide": 0.0})
    wire = _results(payload)["wire_rope_capacity"]
    assert wire["ok"] is False
    assert payload["derived"]["ropeLayoutConditionOk"] is False
    assert "前后两道" in wire["detail"]


def test_low_breaking_force_fails_wire_rope_capacity():
    payload = cop.run({"wireBreakForce": 80.0})
    wire = _results(payload)["wire_rope_capacity"]
    assert wire["ok"] is False
    assert wire["value"] < wire["limit"]


def test_low_support_moment_fails_overturning_boundary():
    payload = cop.run(
        {
            "supportMomentCapacity": 0.0,
            "rearSupportVerticalCapacity": 10.0,
        }
    )
    support = _results(payload)["overturning_support"]
    assert support["ok"] is False
    assert support["value"] < support["limit"]


@pytest.mark.parametrize(
    ("secondary_w", "should_pass"),
    [
        (
            (1.2 * 0.55 + 1.4 * 5.0) * 0.4 * 3.0**2 / 8.0 * 1e6 / 215.0,
            True,
        ),
        (
            (1.2 * 0.55 + 1.4 * 5.0) * 0.4 * 3.0**2 / 8.0 * 1e6 / 215.0 * 0.999,
            False,
        ),
        (
            (1.2 * 0.55 + 1.4 * 5.0) * 0.4 * 3.0**2 / 8.0 * 1e6 / 215.0 * 1.001,
            True,
        ),
    ],
)
def test_secondary_beam_bending_boundaries(secondary_w, should_pass):
    payload = cop.run({"secondaryBeamW": secondary_w})
    result = _results(payload)["secondary_beam_bending"]
    assert result["ok"] is should_pass


@pytest.mark.parametrize(
    ("panel_f", "should_pass"),
    [
        ((1.2 * 0.55 + 1.4 * 5.0) * 1.0 * 1.0**2 / 8.0 * 1e6 / (1000 * 50**2 / 6), True),
        ((1.2 * 0.55 + 1.4 * 5.0) * 1.0 * 1.0**2 / 8.0 * 1e6 / (1000 * 50**2 / 6) * 0.99, False),
        (2.3, True),
    ],
)
def test_platform_panel_bending_boundaries(panel_f, should_pass):
    payload = cop.run({"panelSpan": 1.0, "panelF": panel_f})
    result = _results(payload)["platform_panel_bending"]
    assert result["ok"] is should_pass


def test_platform_panel_thickness_below_50mm_fails():
    payload = cop.run({"panelThickness": 49.9})
    result = _results(payload)["platform_panel_bending"]
    assert result["ok"] is False
    assert payload["derived"]["panelThicknessConditionOk"] is False


@pytest.mark.parametrize(
    ("weld_strength", "should_pass"),
    [
        (30.0, False),
        (40.0, True),
        (160.0, True),
    ],
)
def test_weld_connection_boundaries(weld_strength, should_pass):
    payload = cop.run({"weldStrength": weld_strength})
    result = _results(payload)["weld_connection"]
    assert result["ok"] is should_pass
    assert result["unit"] == "kN"


@pytest.mark.parametrize(
    ("overrides", "should_pass"),
    [
        (
            {
                "outerSideHigher": True,
                "guardrailFixed": True,
                "guardrailFullyEnclosed": True,
                "liftingRingInstalled": True,
                "loadBearingRingInstalled": True,
            },
            True,
        ),
        ({"outerSideHigher": False}, False),
        ({"guardrailFixed": False}, False),
        ({"guardrailFullyEnclosed": False}, False),
        ({"liftingRingInstalled": False}, False),
        ({"loadBearingRingInstalled": False}, False),
    ],
)
def test_guardrail_configuration_boundaries(overrides, should_pass):
    payload = cop.run(overrides)
    result = _results(payload)["guardrail_configuration"]
    assert result["ok"] is should_pass
