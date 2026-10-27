"""Display catalog for the scaffold calculation workbench.

The catalog is intentionally separate from :mod:`calc_core.registry`: planned
items are discoverable in the UI but cannot be executed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

REGIONS = (
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
)

PLANNED_NOTE = "计算内核待接入"


@dataclass(frozen=True)
class CatalogModule:
    key: str
    title: str
    available: bool
    status: str


@dataclass(frozen=True)
class CatalogCategory:
    key: str
    title: str
    is_new: bool
    modules: tuple[CatalogModule, ...]


def _available(key: str, title: str) -> CatalogModule:
    return CatalogModule(
        key=key,
        title=title,
        available=True,
        status="available",
    )


def _planned(slug: str, title: str) -> CatalogModule:
    return CatalogModule(
        key=f"planned:{slug}",
        title=title,
        available=False,
        status="planned",
    )


CATEGORIES = (
    CatalogCategory(
        key="common-checks",
        title="常用验算",
        is_new=False,
        modules=(
            _planned("slab-scaffold", "脚手架在楼板上"),
            _planned("edge-guardrail", "临边防护栏杆"),
            _planned("structural-beam", "结构梁验算"),
            _available("scaffold-tie-member", "连墙件计算"),
        ),
    ),
    CatalogCategory(
        key="ground-scaffold",
        title="落地式脚手架",
        is_new=False,
        modules=(
            _available("scaffold-fastener", "扣件式脚手架"),
            _available("scaffold-fastener-pinming", "扣件式脚手架（品茗双立杆）"),
            _available("door-scaffold", "门式脚手架"),
            _planned("double-row-bamboo", "双排外竹脚手架"),
            _planned("bowl-buckle-scaffold", "碗扣式脚手架"),
            _planned("timber-scaffold", "木脚手架"),
            _planned("disk-buckle-scaffold", "盘扣式脚手架"),
            _planned("multi-row-scaffold", "多排脚手架"),
            _planned("inclined-cantilever-scaffold", "斜挑脚手架"),
        ),
    ),
    CatalogCategory(
        key="climbing-temporary-support",
        title="爬架临时支撑平台",
        is_new=True,
        modules=(
            _planned("climbing-support-fastener", "爬架临时支撑平台(扣件式)"),
            _planned("climbing-support-disk-buckle", "爬架临时支撑平台(盘扣式)"),
            _planned("climbing-support-steel-cantilever", "爬架临时支撑平台(型钢悬挑)"),
        ),
    ),
    CatalogCategory(
        key="suspended-basket",
        title="吊篮工程",
        is_new=False,
        modules=(
            _planned("basket-parapet-clamp", "吊篮（女儿墙卡钳）"),
            _available("suspended-basket", "标准吊篮"),
            _planned("basket-front-anchor", "吊篮（悬挂装置前锚固点）"),
            _planned("basket-front-beam-extension", "吊篮（悬挂装置前梁加长）"),
            _planned("basket-increased-height", "吊篮（悬挂装置增高）"),
            _planned("basket-rigid-fixing", "吊篮（悬挂装置刚性固定）"),
            _planned("basket-rear-anchor-fixing", "吊篮（悬挂装置后锚固式固定）"),
            _planned("basket-rear-wire-rope", "吊篮（悬挂装置后拉钢丝绳固定）"),
        ),
    ),
    CatalogCategory(
        key="mobile-operation-platform",
        title="移动操作平台",
        is_new=False,
        modules=(
            _planned("mobile-platform-fastener", "移动操作平台(扣件式)"),
            _planned("mobile-platform-disk-buckle", "移动操作平台(盘扣式)"),
            _planned("mobile-platform-door", "移动操作平台(门式)"),
        ),
    ),
    CatalogCategory(
        key="shaft-operation-platform",
        title="井道操作平台",
        is_new=False,
        modules=(
            _planned("shaft-platform-fastener", "井道操作平台(扣件式)"),
            _planned("shaft-platform-disk-buckle", "井道操作平台(盘扣式)"),
            _planned("triangular-elevator-shaft-steel", "三角式电梯井钢平台"),
        ),
    ),
    CatalogCategory(
        key="ramp",
        title="斜道",
        is_new=False,
        modules=(
            _planned("ramp-fastener", "斜道(扣件式)"),
            _planned("ramp-disk-buckle", "斜道(盘扣式)"),
        ),
    ),
    CatalogCategory(
        key="operation-and-unloading-platform",
        title="操作平台、卸料平台",
        is_new=False,
        modules=(
            _planned("disk-buckle-operation-platform", "盘扣式操作平台"),
            _planned("disk-buckle-unloading-platform", "盘扣式卸料平台"),
            _planned("steel-pipe-ground-unloading-platform", "钢管落地卸料平台"),
            _planned("steel-cantilever-unloading-platform", "型钢悬挑卸料平台"),
            _available("ground-operation-platform", "落地式操作平台（自研）"),
            _available("cantilever-operation-platform", "悬挑式操作平台（自研）"),
            _available("full-hall-scaffold", "满堂脚手架"),
            _planned("full-hall-support", "满堂支撑架"),
        ),
    ),
    CatalogCategory(
        key="construction-elevator-platform",
        title="施工升降机卸料平台",
        is_new=False,
        modules=(
            _planned("elevator-unloading-fastener", "施工升降机卸料平台(扣件式)"),
            _planned("elevator-unloading-disk-buckle", "施工升降机卸料平台(盘扣式)"),
            _planned("elevator-cantilever-fastener", "施工升降机悬挑平台(扣件式)"),
            _planned("elevator-cantilever-disk-buckle", "施工升降机悬挑平台(盘扣式)"),
            _planned(
                "elevator-turnbuckle-cantilever-fastener",
                "施工升降机花篮螺栓悬挑平台(扣件式)",
            ),
            _planned(
                "elevator-turnbuckle-cantilever-disk-buckle",
                "施工升降机花篮螺栓悬挑平台(盘扣式)",
            ),
        ),
    ),
    CatalogCategory(
        key="tool-scaffold",
        title="工具式脚手架",
        is_new=False,
        modules=(
            _available("attached-lifting-scaffold", "导轨式附着升降脚手架"),
            _planned("all-steel-attached-lifting", "全钢附着升降脚手架"),
        ),
    ),
    CatalogCategory(
        key="protective-shed",
        title="防护棚",
        is_new=True,
        modules=(
            _planned("protective-shed-fastener", "防护棚(扣件式)"),
            _planned("protective-shed-disk-buckle", "防护棚(盘扣式)"),
            _planned("cantilever-protective-shed", "悬挑防护棚"),
            _planned("steel-cantilever-protective-shed", "型钢悬挑防护棚"),
            _planned("transformer-protective-shed", "变压器防护棚"),
        ),
    ),
    CatalogCategory(
        key="steel-cantilever-scaffold",
        title="型钢悬挑脚手架",
        is_new=False,
        modules=(
            _available("cantilever-scaffold", "型钢悬挑脚手架（扣件式）"),
            _planned("cantilever-corner-integral", "型钢悬挑脚手架(阳角整体计算)"),
            _planned(
                "multi-row-cantilever-no-longitudinal-beam",
                "多排悬挑架(无纵向钢梁)",
            ),
            _planned(
                "multi-row-cantilever-with-longitudinal-beam",
                "多排悬挑架(有纵向钢梁)",
            ),
            _planned("cantilever-bowl-buckle", "型钢悬挑脚手架(碗扣式)"),
            _planned("cantilever-door", "型钢悬挑脚手架(门式)"),
            _planned("cantilever-disk-buckle", "型钢悬挑脚手架(盘扣式)"),
            _planned("cantilever-main-beam-check", "搁置主梁验算"),
            _planned("cantilever-external-triangular-bracket", "悬挑外挂三角架"),
        ),
    ),
    CatalogCategory(
        key="turnbuckle-cantilever-scaffold",
        title="花篮螺栓悬挑架",
        is_new=False,
        modules=(
            _planned("turnbuckle-fastener", "花篮螺栓悬挑架(扣件式)"),
            _planned("turnbuckle-bowl-buckle", "花篮螺栓悬挑架(碗扣式)"),
            _planned("turnbuckle-disk-buckle", "花篮螺栓悬挑架(盘扣式)"),
            _planned("turnbuckle-corner-integral", "花篮螺栓悬挑架(阳角整体计算)"),
            _planned("turnbuckle-door", "花篮螺栓悬挑架(门式)"),
            _planned(
                "turnbuckle-multi-row-no-longitudinal-beam",
                "花篮螺栓多排悬挑架(无纵向钢梁)",
            ),
            _planned(
                "turnbuckle-multi-row-with-longitudinal-beam",
                "花篮螺栓多排悬挑架(有纵向钢梁)",
            ),
            _planned("turnbuckle-main-beam-check", "搁置主梁验算(花篮螺栓式)"),
        ),
    ),
)


def _module_payload(
    module: CatalogModule,
    registered: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if module.available:
        metadata = registered.get(module.key)
        if metadata is None:
            raise RuntimeError(
                f"available catalog module {module.key!r} is missing from the registry"
            )
        standard = str(metadata.get("standard") or "")
        verified = bool(metadata.get("verified", False))
        note = ""
    else:
        standard = ""
        verified = False
        note = PLANNED_NOTE

    return {
        "key": module.key,
        "title": module.title,
        "standard": standard,
        "verified": verified,
        "available": module.available,
        "status": module.status,
        "note": note,
    }


def build_catalog_payload(
    registered_modules: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    registered = {str(item["key"]): item for item in registered_modules}
    categories = []
    flat_modules = []

    for category in CATEGORIES:
        modules = [
            _module_payload(module, registered)
            for module in category.modules
        ]
        categories.append(
            {
                "key": category.key,
                "title": category.title,
                "isNew": category.is_new,
                "modules": modules,
            }
        )
        flat_modules.extend(
            {
                **module,
                "category": category.title,
            }
            for module in modules
        )

    return {
        "regions": list(REGIONS),
        "categories": categories,
        "modules": flat_modules,
    }
