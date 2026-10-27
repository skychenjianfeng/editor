import pytest

from calc_core import suspended_basket as sb


def _results(payload):
    return {result["key"]: result for result in payload["results"]}


def test_spec_shape_and_parameters():
    spec = sb.param_spec()
    assert spec["module"] == "suspended-basket"
    assert spec["title"] == "高处作业吊篮"
    assert spec["standard"] == "GB/T 19155-2017"
    assert spec["verified"] is False

    fields = {
        field["key"]: field
        for group in spec["groups"]
        for field in group["fields"]
    }
    assert {
        "ratedLoad",
        "platformWeight",
        "platformSpan",
        "beamCount",
        "beamW",
        "beamI",
        "hoistLimitLoad",
        "outerLength",
        "innerLength",
        "counterWeight",
        "wireBreakForce",
        "wireRopeCount",
        "wireMinSafety",
        "jgjDeadLoad",
        "jgjConstructionLoad",
        "jgjWindLoad",
        "supportPointDesignReaction",
        "supportPointMinCapacity",
        "backupDeviceInstalled",
        "backupDeviceMechanicalAutomatic",
        "backupDeviceTestableReset",
        "backupDeviceCalibrationValid",
    } <= fields.keys()
    assert fields["ratedLoad"]["default"] == pytest.approx(630.0)
    assert fields["stabilityFactor"]["default"] == pytest.approx(3.0)
    assert fields["wireMinSafety"]["default"] == pytest.approx(12.0)
    assert fields["jgjWindLoad"]["unit"] == "kN"
    assert fields["supportPointDesignReaction"]["unit"] == "kN"
    assert fields["backupDeviceMechanicalAutomatic"]["type"] == "boolean"
    assert "GB/T 19155-2017 8.8.1" in fields["backupDeviceInstalled"]["clause"]
    assert "GB/T 19155-2017 6.5.5.3" in fields["counterWeight"]["clause"]
    assert "JGJ 202-2010 5.2.1" in fields["wireMinSafety"]["clause"]
    assert "JGJ 202-2010 5.2.2" in fields["jgjWindLoad"]["clause"]
    assert "5.2.5" in fields["supportPointDesignReaction"]["clause"]


def test_default_run_has_eight_passing_checks():
    payload = sb.run({})
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
    assert payload["module"] == "suspended-basket"
    assert payload["standard"] == "GB/T 19155-2017"
    assert payload["verified"] is False
    assert payload["summary"] == {"total": 8, "failed": 0, "control_failed": 0}
    assert {
        item["code"] for item in payload["standards"]["applied"]
    } == {"GB/T 19155-2017", "JGJ 202-2010"}

    results = _results(payload)
    assert set(results) == {
        "platform_bending",
        "platform_deflection",
        "suspension_stability",
        "counterweight_requirement",
        "wire_rope_safety",
        "jgj_wire_rope_wind",
        "support_point_capacity",
        "safety_device_configuration",
    }
    assert all(result["ok"] for result in results.values())
    assert results["platform_bending"]["value"] == pytest.approx(57.02)
    assert results["platform_bending"]["limit"] == pytest.approx(176.69)
    assert results["platform_deflection"]["value"] == pytest.approx(6.03)
    assert results["platform_deflection"]["limit"] == pytest.approx(30.00)
    assert results["suspension_stability"]["value"] == pytest.approx(3.52)
    assert results["counterweight_requirement"]["value"] == pytest.approx(600.00)
    assert results["counterweight_requirement"]["limit"] == pytest.approx(490.00)
    assert results["wire_rope_safety"]["value"] == pytest.approx(14.83)
    assert results["wire_rope_safety"]["limit"] == pytest.approx(12.00)
    assert results["jgj_wire_rope_wind"]["value"] == pytest.approx(49.38)
    assert results["jgj_wire_rope_wind"]["limit"] == pytest.approx(80.00)
    assert results["support_point_capacity"]["value"] == pytest.approx(20.00)
    assert results["support_point_capacity"]["limit"] == pytest.approx(30.00)
    assert results["safety_device_configuration"]["value"] == pytest.approx(4.0)
    assert results["safety_device_configuration"]["limit"] == pytest.approx(4.0)
    assert "GB/T 19155-2017 8.8.1" in results["safety_device_configuration"]["clause"]
    assert not any("钢吊杆" in gap for gap in payload["standards"]["gaps"])
    assert payload["derived"]["jgjQ1_kN"] == pytest.approx(5.395)
    assert payload["derived"]["jgjQ2_kN"] == pytest.approx(1.0)


def test_low_counterweight_fails_overturning_and_counterweight_checks():
    payload = sb.run({"counterWeight": 100.0})
    results = _results(payload)
    assert results["suspension_stability"]["ok"] is False
    assert results["counterweight_requirement"]["ok"] is False
    assert payload["summary"]["failed"] == 2
    assert payload["summary"]["control_failed"] == 2
    assert payload["derived"]["actualStabilityFactor"] == pytest.approx(1.143)
    assert payload["derived"]["requiredCounterWeight_kg"] == pytest.approx(490.0)


def test_low_wire_break_force_fails_wire_safety_check():
    payload = sb.run({"wireBreakForce": 20.0})
    results = _results(payload)
    assert results["wire_rope_safety"]["ok"] is False
    assert results["wire_rope_safety"]["value"] == pytest.approx(3.71)
    assert results["wire_rope_safety"]["limit"] == pytest.approx(12.0)
    assert payload["summary"]["failed"] == 2
    assert payload["summary"]["control_failed"] == 2


def test_jgj_wind_combination_fails_when_qd_exceeds_break_force():
    payload = sb.run({"jgjWindLoad": 20.0})
    results = _results(payload)
    assert results["jgj_wire_rope_wind"]["ok"] is False
    assert results["jgj_wire_rope_wind"]["value"] == pytest.approx(102.26)
    assert results["jgj_wire_rope_wind"]["limit"] == pytest.approx(80.0)
    assert payload["summary"]["failed"] == 1


def test_support_point_capacity_fails_when_demand_exceeds_capacity():
    payload = sb.run({"supportPointMinCapacity": 10.0})
    results = _results(payload)
    assert results["support_point_capacity"]["ok"] is False
    assert results["support_point_capacity"]["value"] == pytest.approx(20.0)
    assert results["support_point_capacity"]["limit"] == pytest.approx(10.0)
    assert payload["summary"]["failed"] == 1


def test_backup_device_not_testable_fails_safety_configuration():
    payload = sb.run({"backupDeviceTestableReset": False})
    results = _results(payload)
    check = results["safety_device_configuration"]
    assert check["ok"] is False
    assert any(
        item["label"] == "防坠落装置可测试并可复位" and not item["ok"]
        for item in check["checks"]
    )
    assert payload["summary"]["failed"] == 1


def test_incomplete_anti_fall_configuration_fails_safety_device_check():
    payload = sb.run({"backupDeviceCalibrationValid": False})
    results = _results(payload)
    check = results["safety_device_configuration"]
    assert check["ok"] is False
    assert any(
        item["label"] == "防坠装置标定在有效期内" and not item["ok"]
        for item in check["checks"]
    )
    assert payload["summary"]["failed"] == 1
