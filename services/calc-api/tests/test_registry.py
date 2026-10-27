import pytest

from calc_core import modules, registry


def test_scaffold_module_registered():
    defn = registry.get("scaffold-fastener")
    assert defn is not None
    assert defn.title == "扣件式脚手架"
    spec = defn.param_spec()
    assert spec["module"] == "scaffold-fastener"
    payload = defn.run({})
    assert payload["summary"]["total"] == 29
    geo = defn.geometry({}, "plan")
    assert geo["view"] == "plan"


def test_registry_list_contains_scaffold():
    items = registry.list_modules()
    keys = {m["key"] for m in items}
    assert "scaffold-fastener" in keys
    assert "scaffold-fastener-pinming" in keys
    assert keys == {
        "scaffold-fastener",
        "scaffold-fastener-pinming",
        "cantilever-scaffold",
        "full-hall-scaffold",
        "suspended-basket",
        "door-scaffold",
        "attached-lifting-scaffold",
        "ground-operation-platform",
        "cantilever-operation-platform",
        "scaffold-tie-member",
    }
    assert all("standard" in m and "verified" in m and "category" in m for m in items)
    assert {m["category"] for m in items} == {
        "落地与满堂",
        "悬挑与升降",
        "工具式与平台",
    }


def test_pinming_module_registered_with_generic_report_and_geometry():
    from calc_core import report

    defn = registry.require("scaffold-fastener-pinming")
    assert defn.title == "扣件式脚手架（品茗双立杆）"
    assert defn.standard == "JGJ 130-2011"
    assert defn.verified is False
    assert defn.category == "落地与满堂"
    assert defn.report is report.build_generic_docx
    assert defn.param_spec()["module"] == "scaffold-fastener-pinming"
    assert defn.run({})["summary"]["total"] == 16


def test_tie_member_registered():
    defn = registry.require("scaffold-tie-member")
    assert defn.title == "连墙件计算"
    assert defn.category == "落地与满堂"
    assert defn.standard == "JGJ 130-2011"
    assert defn.verified is False
    assert defn.param_spec()["module"] == "scaffold-tie-member"
    assert defn.run({})["summary"]["total"] >= 10


@pytest.mark.parametrize(
    "module_key",
    [
        "full-hall-scaffold",
        "door-scaffold",
        "cantilever-scaffold",
        "suspended-basket",
        "attached-lifting-scaffold",
        "ground-operation-platform",
        "cantilever-operation-platform",
        "scaffold-tie-member",
    ],
)
def test_registered_geometry_is_specialized(module_key):
    defn = registry.require(module_key)
    geometry = defn.geometry({}, "elevation")
    texts = [
        item["text"]
        for layer in geometry["layers"]
        for item in layer["items"]
        if item["type"] == "text"
    ]
    assert any(defn.title in text for text in texts)


def test_unknown_module_raises():
    with pytest.raises(KeyError):
        registry.require("not-a-module")


def test_custom_module_can_register():
    from calc_core.registry import ModuleDef

    registry.register(
        ModuleDef(
            key="demo-test",
            title="测试模块",
            standard="TEST",
            verified=True,
            param_spec=lambda: {"module": "demo-test", "groups": []},
            run=lambda params: {"ok": True},
            geometry=lambda params, view: {"view": view},
            report=lambda params, payload: b"",
        )
    )
    assert registry.get("demo-test").title == "测试模块"
