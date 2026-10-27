"""批量工况：参数矩阵 → 逐工况校核 → 汇总。"""

from __future__ import annotations

import csv
import io
from typing import Any

from . import scaffold_fastener as sf

MAX_CASES = 200


def _primary_result(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    """按失败控制项、通过控制项、普通项的优先级选择主导项。"""
    for result in results:
        if result.get("control") is True and result.get("ok") is False:
            return result
    for result in results:
        if result.get("control") is True:
            return result
    return results[0] if results else None


def run_batch(cases: list[dict[str, Any]], runner=sf.run) -> dict[str, Any]:
    if not cases:
        raise ValueError("批量工况不能为空")
    if len(cases) > MAX_CASES:
        raise ValueError(f"单批最多 {MAX_CASES} 个工况，当前 {len(cases)}")
    if not all(isinstance(case, dict) for case in cases):
        raise ValueError("每个工况必须是参数对象")

    rows = []
    for index, params in enumerate(cases, start=1):
        payload = runner(params)
        results = payload["results"]
        primary = _primary_result(results)
        upright = next((r for r in results if r["key"] == "upright_stability"), None)
        slenderness = next((r for r in results if r["key"] == "slenderness"), None)
        rows.append(
            {
                "index": index,
                "name": f"C{index:02d}",
                "params": params,
                "module": payload["module"],
                "primary_item": primary["item"] if primary else None,
                "primary_key": primary["key"] if primary else None,
                "primary_value": primary["value"] if primary else None,
                "primary_unit": primary["unit"] if primary else None,
                "primary_ratio": primary["ratio"] if primary else None,
                "primary_ok": primary["ok"] if primary else None,
                "failed": payload["summary"]["failed"],
                "control_failed": payload["summary"]["control_failed"],
                "ok": payload["summary"]["failed"] == 0,
                "h": params.get("h"),
                "la": params.get("la"),
                "lb": params.get("lb"),
                "H": params.get("H"),
                "upright": upright["value"] if upright else None,
                "upright_ratio": upright["ratio"] if upright else None,
                "lambda": slenderness["value"] if slenderness else None,
            }
        )

    return {
        "count": len(rows),
        "failed": sum(1 for r in rows if not r["ok"]),
        "control_failed": sum(1 for r in rows if r["control_failed"] > 0),
        "rows": rows,
    }


def batch_csv(result: dict[str, Any]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(
        [
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
    )
    for row in result["rows"]:
        writer.writerow(
            [
                row["name"],
                row["module"],
                row["primary_item"],
                row["primary_value"],
                row["primary_unit"],
                f"{row['primary_ratio'] * 100:.1f}%" if row["primary_ratio"] is not None else "",
                row["failed"],
                row["control_failed"],
                "通过" if row["ok"] else "不满足",
            ]
        )
    return ("\ufeff" + buf.getvalue()).encode("utf-8")
