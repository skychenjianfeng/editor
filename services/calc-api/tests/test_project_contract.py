import uuid
import os
from datetime import datetime, timezone

import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calcapi.settings")

import django

django.setup()

from calc_runs.models import ScaffoldProject, ScaffoldScheme
from calc_runs.serializers import (
    InputValidationError,
    validate_project_payload,
    validate_scheme_payload,
)


def test_project_and_scheme_metadata_contract():
    project_id = uuid.uuid4()
    scheme_id = uuid.uuid4()
    timestamp = datetime(2026, 10, 26, 5, 0, tzinfo=timezone.utc)
    project = ScaffoldProject(
        id=project_id,
        name="外架项目",
        region="上海",
        status="calculating",
        code="",
        client="建设单位",
        location="上海",
        designer="设计人",
        note="说明",
        created_at=timestamp,
        updated_at=timestamp,
    )
    scheme = ScaffoldScheme(
        id=scheme_id,
        project=project,
        name="北立面",
        module="scaffold-fastener",
        module_title="扣件式脚手架",
        params={"height": 24},
        created_at=timestamp,
        updated_at=timestamp,
    )

    scheme_metadata = scheme.metadata()
    project_metadata = project.metadata(schemes=[scheme_metadata])

    assert project_metadata["project_id"] == str(project_id)
    assert project_metadata["region"] == "上海"
    assert project_metadata["status"] == "calculating"
    assert project_metadata["status_label"] == "计算中"
    assert project_metadata["scheme_count"] == 1
    assert project_metadata["schemes"] == [scheme_metadata]
    assert scheme_metadata["scheme_id"] == str(scheme_id)
    assert scheme_metadata["project_id"] == str(project_id)
    assert scheme_metadata["last_run_id"] is None
    assert str(project) == f"外架项目 ({project_id})"
    assert str(scheme) == f"北立面 ({scheme_id})"


def test_scheme_accepts_last_run_id_and_project_cascade():
    run_id = uuid.uuid4()
    scheme = ScaffoldScheme(
        name="东立面",
        module="scaffold-fastener",
        module_title="扣件式脚手架",
        last_run_id=run_id,
    )

    assert scheme.last_run_id == run_id
    assert ScaffoldScheme._meta.get_field("project").remote_field.on_delete.__name__ == "CASCADE"
    assert ScaffoldScheme._meta.get_field("last_run").remote_field.on_delete.__name__ == "SET_NULL"
    assert not ScaffoldProject._meta.get_field("code").unique


def test_project_payload_validation_and_defaults():
    cleaned = validate_project_payload(
        {"name": "  项目一  ", "region": "  上海  ", "status": "calculating"}
    )

    assert cleaned == {
        "name": "项目一",
        "region": "上海",
        "status": "calculating",
        "code": "",
        "client": "",
        "location": "",
        "designer": "",
        "note": "",
    }
    default_status = validate_project_payload({"name": "项目二", "region": "全国"})
    assert default_status["status"] == "preparing"
    assert validate_project_payload({"code": "A-01"}, partial=True) == {"code": "A-01"}
    with pytest.raises(InputValidationError, match="region is required"):
        validate_project_payload({"name": "项目一"})
    with pytest.raises(InputValidationError, match="name is required"):
        validate_project_payload({"region": "全国", "note": "缺少名称"})
    with pytest.raises(InputValidationError, match="unknown field"):
        validate_project_payload({"name": "项目", "region": "全国", "unexpected": True})


def test_scheme_payload_validation():
    run_id = str(uuid.uuid4())
    cleaned = validate_scheme_payload(
        {
            "name": " 北侧方案 ",
            "module": "scaffold-fastener",
            "params": {"height": 20},
            "last_run_id": run_id,
        }
    )

    assert cleaned == {
        "name": "北侧方案",
        "module": "scaffold-fastener",
        "params": {"height": 20},
        "last_run_id": run_id,
    }
    assert validate_scheme_payload({"last_run_id": None}, partial=True) == {
        "last_run_id": None
    }
    with pytest.raises(InputValidationError, match="params must be a JSON object"):
        validate_scheme_payload({"name": "方案", "module": "scaffold-fastener", "params": []})
    with pytest.raises(InputValidationError, match="valid UUID"):
        validate_scheme_payload({"last_run_id": "not-a-uuid"}, partial=True)
