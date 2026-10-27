import hashlib
import json
from pathlib import Path

import pytest

from calc_core import scaffold_fastener_pinming as sfp


ORACLE_PATH = (
    Path(__file__).resolve().parents[3]
    / "oracle"
    / "pinming-fastener-20261027.json"
)
ORACLE_RTF_PATH = ORACLE_PATH.with_suffix(".rtf")


def _oracle():
    return json.loads(ORACLE_PATH.read_text(encoding="utf-8"))


def test_spec_and_source_identity():
    spec = sfp.param_spec()
    assert spec["module"] == "scaffold-fastener-pinming"
    assert spec["title"] == "扣件式脚手架（品茗双立杆）"
    assert spec["verified"] is False
    assert sfp.SOURCE_SHA256 == _oracle()["source"]["sha256"]


def test_source_sha256_matches_rtf_bytes():
    assert (
        hashlib.sha256(ORACLE_RTF_PATH.read_bytes()).hexdigest().upper()
        == sfp.SOURCE_SHA256
    )


def test_default_run_reproduces_pinming_oracle():
    payload = sfp.run({})
    oracle = _oracle()

    assert payload["summary"] == {
        "total": 16,
        "failed": 0,
        "control_failed": 0,
    }
    assert payload["standards"]["oracle"] == {
        "verified": True,
        "source": "pinming-fastener-20261027.rtf",
        "sha256": sfp.SOURCE_SHA256,
        "exported_at": "2026-10-27T03:16:10+08:00",
    }

    results = {item["key"]: item for item in payload["results"]}
    for key, (value, limit) in oracle["checks"].items():
        assert results[key]["value"] == pytest.approx(value, rel=0.01), key
        assert results[key]["limit"] == pytest.approx(limit, rel=0.01), key
        assert results[key]["ok"] is True
        assert results[key]["source"] == "pinming-fastener-20261027.rtf"

    intermediates = oracle["intermediates"]
    for key in (
        "qLongDesign_kN_m",
        "qLongService_kN_m",
        "M_long_kNm",
        "R_long_kN",
        "M_trans_kNm",
        "R_trans_kN",
        "NQ1_kN",
        "lambda_check",
        "lambda_stability",
        "tie_wind_kN",
        "tie_axial_kN",
        "anchor_area_required_mm2",
        "foundation_pressure_kPa",
    ):
        assert payload["derived"][key] == pytest.approx(
            intermediates[key], rel=0.01
        ), key


def test_derived_has_snake_case_aliases_while_retaining_camel_case():
    derived = sfp.run({})["derived"]
    aliases = {
        "anchor_area_required_mm2": "anchorAreaRequired_mm2",
        "anchor_area_provided_mm2": "anchorAreaProvided_mm2",
        "foundation_pressure_kPa": "foundationPressure_kPa",
        "foundation_capacity_kPa": "foundationCapacity_kPa",
    }
    for snake_key, camel_key in aliases.items():
        assert derived[snake_key] == derived[camel_key]


def test_transverse_deflection_factor_is_an_isolated_single_sample_risk():
    base = sfp.run({})
    changed = sfp.run({"pinmingTransverseDeflectionFactor": 2.5})
    base_results = {item["key"]: item["value"] for item in base["results"]}
    changed_results = {item["key"]: item["value"] for item in changed["results"]}

    assert base["params"]["pinmingTransverseDeflectionFactor"] == pytest.approx(1.9729)
    assert changed_results["trans_deflection"] != base_results["trans_deflection"]
    assert {
        key: value for key, value in changed_results.items() if key != "trans_deflection"
    } == {
        key: value for key, value in base_results.items() if key != "trans_deflection"
    }
    assert any(
        "单样本" in text and "非规范值" in text
        for text in base["standards"]["gaps"]
    )
    assert any(
        "单样本" in text and "不得外推" in text
        for text in base["assumptions"]
    )
    assert base["verified"] is False
    assert base["standards"]["oracle"]["verified"] is True


def test_thicker_or_longer_member_changes_geometry_and_loads():
    base = sfp.run({})
    changed = sfp.run({"H": 40.0, "doublePoleHeight": 35.0, "wind": 0})
    assert changed["params"]["H"] == 40.0
    assert changed["derived"]["N_no_wind_double_kN"] != base["derived"]["N_no_wind_double_kN"]


def test_bad_double_pole_height_is_rejected():
    with pytest.raises(ValueError, match="双立杆计算高度"):
        sfp.run({"H": 20.0, "doublePoleHeight": 25.0})
