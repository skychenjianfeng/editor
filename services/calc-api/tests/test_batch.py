import csv
import io

import pytest

from calc_core import full_hall_scaffold as fhs
from calc_core import scaffold_fastener as sf
from calc_core import suspended_basket as sb
from calc_core.batch import MAX_CASES, batch_csv, run_batch


def test_batch_runs_and_summarises():
    cases = [
        {"h": 1.5, "la": 1.2, "lb": 0.9, "H": 18},
        {"h": 1.8, "la": 1.5, "lb": 0.9, "H": 24},
        {"h": 2.0, "la": 1.8, "lb": 1.2, "H": 40},
    ]
    result = run_batch(cases)
    assert result["count"] == 3
    assert len(result["rows"]) == 3
    assert result["rows"][0]["name"] == "C01"
    assert all("upright" in row for row in result["rows"])
    assert result["rows"][0]["params"] == cases[0]
    assert result["rows"][0]["module"] == "scaffold-fastener"
    assert result["failed"] >= 1


def test_primary_selects_first_failed_control_item():
    result = run_batch([{"h": 1.8, "la": 1.5}])
    row = result["rows"][0]
    primary = next(
        item
        for item in sf.run({"h": 1.8, "la": 1.5})["results"]
        if item["control"] and not item["ok"]
    )
    assert row["primary_key"] == primary["key"]
    assert row["primary_item"] == primary["item"]
    assert row["primary_value"] == primary["value"]
    assert row["primary_unit"] == primary["unit"]
    assert row["primary_ratio"] == primary["ratio"]
    assert row["primary_ok"] is False
    assert row["upright"] is not None
    assert row["upright_ratio"] is not None
    assert row["lambda"] is not None


def test_primary_falls_back_to_first_passing_control_item():
    result = run_batch([{}], runner=fhs.run)
    row = result["rows"][0]
    primary = next(item for item in fhs.run({})["results"] if item["control"])
    assert row["module"] == "full-hall-scaffold"
    assert row["params"] == {}
    assert row["primary_key"] == primary["key"]
    assert row["primary_value"] == primary["value"]
    assert row["primary_unit"] == primary["unit"]
    assert row["primary_ratio"] == primary["ratio"]
    assert row["primary_ok"] is True
    assert row["h"] is None
    assert row["la"] is None
    assert row["lb"] is None
    assert row["H"] is None


def test_primary_works_for_suspended_basket():
    params = {"counterWeight": 100.0}
    result = run_batch([params], runner=sb.run)
    row = result["rows"][0]
    primary = next(
        item
        for item in sb.run(params)["results"]
        if item["control"] and not item["ok"]
    )
    assert row["module"] == "suspended-basket"
    assert row["params"] == params
    assert row["primary_key"] == primary["key"]
    assert row["primary_item"] == primary["item"]
    assert row["primary_value"] == primary["value"]
    assert row["primary_unit"] == primary["unit"]
    assert row["primary_ratio"] == primary["ratio"]
    assert row["primary_ok"] is False
    assert row["failed"] == 2
    assert row["control_failed"] == 2
    assert row["ok"] is False


def test_batch_rejects_empty_and_oversized():
    with pytest.raises(ValueError):
        run_batch([])
    with pytest.raises(ValueError):
        run_batch([{}] * (MAX_CASES + 1))
    with pytest.raises(ValueError):
        run_batch(["oops"])


def test_batch_csv_has_bom_and_header():
    data = batch_csv(run_batch([{}], runner=sb.run))
    assert data.startswith("\ufeff".encode("utf-8"))
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline="")))
    assert rows[0] == [
        "工况",
        "模块",
        "主导控制项",
        "计算值",
        "单位",
        "利用率",
        "不满足项",
        "控制项不满足",
        "结论",
    ]
    assert rows[1][0] == "C01"
    assert rows[1][1] == "suspended-basket"
    assert rows[1][2] == sb.run({})["results"][0]["item"]
    assert rows[1][4] == "N/mm²"
    assert rows[1][5].endswith("%")
    assert rows[1][-1] == "通过"
