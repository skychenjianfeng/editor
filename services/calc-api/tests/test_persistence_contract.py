import json
import os
import uuid
from datetime import datetime, timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calcapi.settings")

import django

django.setup()

from calc_runs.models import CalcRun, ScaffoldProject


def test_run_metadata_contract():
    run_id = uuid.uuid4()
    created_at = datetime(2026, 10, 26, 4, 0, tzinfo=timezone.utc)
    summary = {"total": 29, "failed": 2, "control_failed": 1}
    record = CalcRun(
        id=run_id,
        created_at=created_at,
        module="scaffold-fastener",
        title="扣件式脚手架",
        standard="JGJ 130-2011",
        verified=False,
        params={"h": 1.8},
        payload={"run_id": str(run_id), "summary": summary},
        summary=summary,
    )

    metadata = record.metadata()

    assert metadata == {
        "run_id": str(run_id),
        "created_at": "2026-10-26T04:00:00+00:00",
        "module": "scaffold-fastener",
        "title": "扣件式脚手架",
        "standard": "JGJ 130-2011",
        "verified": False,
        "summary": summary,
        "total": 29,
        "failed": 2,
        "control_failed": 1,
    }
    assert json.loads(json.dumps(record.payload))["run_id"] == str(run_id)
    assert str(record) == f"扣件式脚手架 ({run_id})"


def test_run_and_project_owner_fields_are_required_cascades():
    for model in (CalcRun, ScaffoldProject):
        owner = model._meta.get_field("owner")
        assert not owner.null
        assert owner.remote_field.on_delete.__name__ == "CASCADE"
        assert owner.db_index
