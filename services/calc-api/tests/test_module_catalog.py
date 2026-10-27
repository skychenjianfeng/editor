import json
import os

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calcapi.settings")

import django

django.setup()

from calc_core import registry  # noqa: E402
from calc_runs.models import CalcRun  # noqa: E402

EXPECTED_REGIONS = [
    "全国",
    "上海",
    "浙江",
    "广东",
    "江苏",
    "山东",
    "重庆",
    "北京",
    "湖北",
    "福建",
]

EXPECTED_CATEGORIES = [
    (
        "常用验算",
        False,
        ["脚手架在楼板上", "临边防护栏杆", "结构梁验算", "连墙件计算"],
    ),
    (
        "落地式脚手架",
        False,
        [
            "扣件式脚手架",
            "扣件式脚手架（品茗双立杆）",
            "门式脚手架",
            "双排外竹脚手架",
            "碗扣式脚手架",
            "木脚手架",
            "盘扣式脚手架",
            "多排脚手架",
            "斜挑脚手架",
        ],
    ),
    (
        "爬架临时支撑平台",
        True,
        [
            "爬架临时支撑平台(扣件式)",
            "爬架临时支撑平台(盘扣式)",
            "爬架临时支撑平台(型钢悬挑)",
        ],
    ),
    (
        "吊篮工程",
        False,
        [
            "吊篮（女儿墙卡钳）",
            "标准吊篮",
            "吊篮（悬挂装置前锚固点）",
            "吊篮（悬挂装置前梁加长）",
            "吊篮（悬挂装置增高）",
            "吊篮（悬挂装置刚性固定）",
            "吊篮（悬挂装置后锚固式固定）",
            "吊篮（悬挂装置后拉钢丝绳固定）",
        ],
    ),
    (
        "移动操作平台",
        False,
        ["移动操作平台(扣件式)", "移动操作平台(盘扣式)", "移动操作平台(门式)"],
    ),
    (
        "井道操作平台",
        False,
        ["井道操作平台(扣件式)", "井道操作平台(盘扣式)", "三角式电梯井钢平台"],
    ),
    ("斜道", False, ["斜道(扣件式)", "斜道(盘扣式)"]),
    (
        "操作平台、卸料平台",
        False,
        [
            "盘扣式操作平台",
            "盘扣式卸料平台",
            "钢管落地卸料平台",
            "型钢悬挑卸料平台",
            "落地式操作平台（自研）",
            "悬挑式操作平台（自研）",
            "满堂脚手架",
            "满堂支撑架",
        ],
    ),
    (
        "施工升降机卸料平台",
        False,
        [
            "施工升降机卸料平台(扣件式)",
            "施工升降机卸料平台(盘扣式)",
            "施工升降机悬挑平台(扣件式)",
            "施工升降机悬挑平台(盘扣式)",
            "施工升降机花篮螺栓悬挑平台(扣件式)",
            "施工升降机花篮螺栓悬挑平台(盘扣式)",
        ],
    ),
    (
        "工具式脚手架",
        False,
        ["导轨式附着升降脚手架", "全钢附着升降脚手架"],
    ),
    (
        "防护棚",
        True,
        [
            "防护棚(扣件式)",
            "防护棚(盘扣式)",
            "悬挑防护棚",
            "型钢悬挑防护棚",
            "变压器防护棚",
        ],
    ),
    (
        "型钢悬挑脚手架",
        False,
        [
            "型钢悬挑脚手架（扣件式）",
            "型钢悬挑脚手架(阳角整体计算)",
            "多排悬挑架(无纵向钢梁)",
            "多排悬挑架(有纵向钢梁)",
            "型钢悬挑脚手架(碗扣式)",
            "型钢悬挑脚手架(门式)",
            "型钢悬挑脚手架(盘扣式)",
            "搁置主梁验算",
            "悬挑外挂三角架",
        ],
    ),
    (
        "花篮螺栓悬挑架",
        False,
        [
            "花篮螺栓悬挑架(扣件式)",
            "花篮螺栓悬挑架(碗扣式)",
            "花篮螺栓悬挑架(盘扣式)",
            "花篮螺栓悬挑架(阳角整体计算)",
            "花篮螺栓悬挑架(门式)",
            "花篮螺栓多排悬挑架(无纵向钢梁)",
            "花篮螺栓多排悬挑架(有纵向钢梁)",
            "搁置主梁验算(花篮螺栓式)",
        ],
    ),
]

EXPECTED_AVAILABLE = {
    "连墙件计算": "scaffold-tie-member",
    "扣件式脚手架": "scaffold-fastener",
    "扣件式脚手架（品茗双立杆）": "scaffold-fastener-pinming",
    "门式脚手架": "door-scaffold",
    "标准吊篮": "suspended-basket",
    "落地式操作平台（自研）": "ground-operation-platform",
    "悬挑式操作平台（自研）": "cantilever-operation-platform",
    "满堂脚手架": "full-hall-scaffold",
    "导轨式附着升降脚手架": "attached-lifting-scaffold",
    "型钢悬挑脚手架（扣件式）": "cantilever-scaffold",
}


@pytest.fixture
def catalog_client():
    user = get_user_model().objects.create_user(
        "catalog@example.com",
        "catalog@example.com",
        "Strong-pass-2026",
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_catalog_contract_contains_all_screenshot_entries(catalog_client):
    response = catalog_client.get("/api/v1/catalog/modules")

    assert response.status_code == 200
    payload = response.json()
    assert payload["regions"] == EXPECTED_REGIONS

    actual_categories = [
        (
            category["title"],
            category["isNew"],
            [module["title"] for module in category["modules"]],
        )
        for category in payload["categories"]
    ]
    assert actual_categories == EXPECTED_CATEGORIES
    assert all(category["key"] for category in payload["categories"])

    modules = [
        module
        for category in payload["categories"]
        for module in category["modules"]
    ]
    assert len(modules) == 70
    assert len(payload["modules"]) == 70
    assert len({module["key"] for module in modules}) == 70
    assert len({module["title"] for module in modules}) == 70

    available = [module for module in modules if module["available"]]
    planned = [module for module in modules if not module["available"]]
    assert len(available) == 10
    assert len(planned) == 60
    assert all(module["status"] == "available" for module in available)
    assert all(module["status"] == "planned" for module in planned)
    assert {module["title"]: module["key"] for module in available} == EXPECTED_AVAILABLE

    registered = {item["key"]: item for item in registry.list_modules()}
    for module in available:
        definition = registered[module["key"]]
        assert module["standard"] == definition["standard"]
        assert module["verified"] is definition["verified"]
        assert module["note"] == ""
    for module in planned:
        assert module["key"].startswith("planned:")
        assert module["standard"] == ""
        assert module["verified"] is False
        assert module["note"] == "计算内核待接入"


@pytest.mark.django_db
def test_planned_catalog_keys_are_not_registered_or_runnable(catalog_client):
    payload = catalog_client.get("/api/v1/catalog/modules").json()
    planned_keys = [
        module["key"]
        for module in payload["modules"]
        if module["status"] == "planned"
    ]
    existing_runs = CalcRun.objects.count()

    assert len(planned_keys) == 60
    for key in planned_keys:
        assert registry.get(key) is None
        with pytest.raises(KeyError):
            registry.require(key)
        assert catalog_client.get(f"/api/v1/catalog/param-spec/{key}").status_code == 404
        response = catalog_client.post(
            "/api/v1/runs",
            data=json.dumps({"module": key, "params": {}}),
            content_type="application/json",
        )
        assert response.status_code == 404

    assert CalcRun.objects.count() == existing_runs
