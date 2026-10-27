import json
import os

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calcapi.settings")

import django

django.setup()

from calc_runs.models import CalcRun, ScaffoldProject


@pytest.fixture
def users():
    User = get_user_model()
    return (
        User.objects.create_user("one@example.com", "one@example.com", "Strong-pass-2026"),
        User.objects.create_user("two@example.com", "two@example.com", "Strong-pass-2026"),
    )


@pytest.mark.django_db
def test_project_crud_is_owner_scoped(users):
    first, second = users
    client = Client()
    client.force_login(first)

    created = client.post(
        "/api/v1/projects",
        data=json.dumps(
            {
                "name": "上海项目",
                "region": "上海",
                "status": "calculating",
                "code": "SH-01",
            }
        ),
        content_type="application/json",
    )
    assert created.status_code == 201
    project_id = created.json()["project_id"]
    assert created.json()["region"] == "上海"
    assert created.json()["status"] == "calculating"
    assert created.json()["scheme_count"] == 0

    client.force_login(second)
    assert client.get("/api/v1/projects").json()["projects"] == []
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404
    assert (
        client.patch(
            f"/api/v1/projects/{project_id}",
            data=json.dumps({"name": "越权"}),
            content_type="application/json",
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/projects/{project_id}",
            data=json.dumps({"status": "unknown"}),
            content_type="application/json",
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/projects/{project_id}").status_code == 404


@pytest.mark.django_db
def test_anonymous_data_calculation_and_export_endpoints_return_401():
    client = Client()
    json_body = json.dumps({"params": {}})
    requests = [
        ("get", "/api/v1/projects"),
        ("get", "/api/v1/runs"),
        ("get", "/api/v1/catalog/modules"),
        ("post", "/api/v1/runs"),
        ("post", "/api/v1/geometry"),
        ("post", "/api/v1/report.docx"),
        ("post", "/api/v1/export.dxf"),
        ("post", "/api/v1/export.png"),
        ("post", "/api/v1/batches"),
        ("post", "/api/v1/export.results.csv"),
    ]
    for method, path in requests:
        if method == "get":
            response = client.get(path)
        else:
            response = client.post(path, data=json_body, content_type="application/json")
        assert response.status_code == 401, path


@pytest.mark.django_db
def test_project_progress_is_derived(users):
    user, _ = users
    project = ScaffoldProject.objects.create(
        owner=user,
        name="进度项目",
        region="江苏",
        status="calculating",
    )
    run = CalcRun.objects.create(
        owner=user,
        module="scaffold-fastener",
        title="扣件式脚手架",
        standard="JGJ 130-2011",
        verified=False,
        params={},
        payload={},
        summary={"total": 10, "failed": 2, "control_failed": 1},
    )
    project.schemes.create(
        name="方案一",
        module="scaffold-fastener",
        module_title="扣件式脚手架",
        params={},
        last_run=run,
    )

    client = Client()
    client.force_login(user)
    payload = client.get(f"/api/v1/projects/{project.id}").json()
    assert payload["scheme_count"] == 1
    assert payload["failed_control_count"] == 1
    assert payload["last_calculated_at"] == run.created_at.isoformat()
    assert payload["status_label"] == "计算中"
    assert payload["region"] == "江苏"


@pytest.mark.django_db
def test_region_and_status_validation_and_default(users):
    client = Client()
    client.force_login(users[0])
    invalid_region = client.post(
        "/api/v1/projects",
        data=json.dumps({"name": "项目", "region": "火星"}),
        content_type="application/json",
    )
    invalid_status = client.post(
        "/api/v1/projects",
        data=json.dumps({"name": "项目", "region": "全国", "status": "unknown"}),
        content_type="application/json",
    )
    missing_region = client.post(
        "/api/v1/projects",
        data=json.dumps({"name": "项目"}),
        content_type="application/json",
    )
    default_status = client.post(
        "/api/v1/projects",
        data=json.dumps({"name": "默认状态项目", "region": "全国"}),
        content_type="application/json",
    )

    assert invalid_region.status_code == 400
    assert "region" in invalid_region.json()["errors"]
    assert invalid_status.status_code == 400
    assert "status" in invalid_status.json()["errors"]
    assert missing_region.status_code == 400
    assert "region" in missing_region.json()["errors"]
    assert default_status.status_code == 201
    assert default_status.json()["status"] == "preparing"
    assert default_status.json()["status_label"] == "筹备中"


@pytest.mark.django_db
def test_project_status_filter_is_owner_scoped(users):
    first, second = users
    ScaffoldProject.objects.create(
        owner=first,
        name="筹备项目",
        region="全国",
        status="preparing",
    )
    ScaffoldProject.objects.create(
        owner=first,
        name="计算项目",
        region="上海",
        status="calculating",
    )
    ScaffoldProject.objects.create(
        owner=second,
        name="他人计算项目",
        region="江苏",
        status="calculating",
    )

    client = Client()
    client.force_login(first)
    payload = client.get("/api/v1/projects?status=calculating").json()

    assert [project["name"] for project in payload["projects"]] == ["计算项目"]


@pytest.mark.django_db
def test_scheme_and_run_operations_are_owner_scoped(users):
    first, second = users
    first_project = ScaffoldProject.objects.create(
        owner=first,
        name="第一用户项目",
        region="全国",
    )
    first_scheme = first_project.schemes.create(
        name="第一用户方案",
        module="scaffold-fastener",
        module_title="扣件式脚手架",
        params={},
    )
    first_run = CalcRun.objects.create(
        owner=first,
        module="scaffold-fastener",
        title="扣件式脚手架",
        standard="JGJ 130-2011",
        verified=False,
        params={},
        payload={"run_id": "first-user"},
        summary={},
    )
    second_project = ScaffoldProject.objects.create(
        owner=second,
        name="第二用户项目",
        region="全国",
    )

    client = Client()
    client.force_login(second)
    assert client.get("/api/v1/runs").json()["runs"] == []
    assert client.get(f"/api/v1/runs/{first_run.id}").status_code == 404
    assert client.get(f"/api/v1/projects/{first_project.id}/schemes").status_code == 404
    assert client.get(f"/api/v1/schemes/{first_scheme.id}").status_code == 404
    assert client.delete(f"/api/v1/schemes/{first_scheme.id}").status_code == 404
    assert (
        client.patch(
            f"/api/v1/schemes/{first_scheme.id}",
            data=json.dumps({"name": ""}),
            content_type="application/json",
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/projects/{first_project.id}/schemes",
            data=json.dumps({}),
            content_type="application/json",
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/projects/{first_project.id}/schemes",
            data=json.dumps({"name": "越权方案", "module": "scaffold-fastener"}),
            content_type="application/json",
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/projects/{second_project.id}/schemes",
            data=json.dumps(
                {
                    "name": "错误关联",
                    "module": "scaffold-fastener",
                    "last_run_id": str(first_run.id),
                }
            ),
            content_type="application/json",
        ).status_code
        == 404
    )

    client.force_login(first)
    created_run = client.post(
        "/api/v1/runs",
        data=json.dumps({"params": {}}),
        content_type="application/json",
    )
    assert created_run.status_code == 200
    assert CalcRun.objects.get(id=created_run.json()["run_id"]).owner == first
