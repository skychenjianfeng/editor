"""内置模块注册。新增模块时在此登记即可。"""

from __future__ import annotations

from . import (
    attached_lifting_scaffold,
    cantilever_scaffold,
    cantilever_operation_platform,
    door_scaffold,
    drawing,
    full_hall_scaffold,
    ground_operation_platform,
    registry,
    report,
    scaffold_fastener,
    scaffold_fastener_pinming,
    scaffold_tie_member,
    suspended_basket,
)


def _geometry(module_key: str, module_title: str):
    def build(params, view):
        return drawing.build_geometry_for_module(
            module_key,
            module_title,
            params,
            view,
        )

    return build


SCAFFOLD_FASTENER = registry.register(
    registry.ModuleDef(
        key=scaffold_fastener.MODULE_KEY,
        title="扣件式脚手架",
        standard="JGJ 130-2011",
        verified=False,
        param_spec=scaffold_fastener.param_spec,
        run=scaffold_fastener.run,
        geometry=drawing.build_geometry,
        report=report.build_docx,
        category="落地与满堂",
    )
)

SCAFFOLD_FASTENER_PINMING = registry.register(
    registry.ModuleDef(
        key=scaffold_fastener_pinming.MODULE_KEY,
        title="扣件式脚手架（品茗双立杆）",
        standard="JGJ 130-2011",
        verified=False,
        param_spec=scaffold_fastener_pinming.param_spec,
        run=scaffold_fastener_pinming.run,
        geometry=_geometry(
            "scaffold-fastener-pinming",
            "扣件式脚手架（品茗双立杆）",
        ),
        report=report.build_generic_docx,
        category="落地与满堂",
    )
)

SCAFFOLD_TIE_MEMBER = registry.register(
    registry.ModuleDef(
        key=scaffold_tie_member.MODULE_KEY,
        title="连墙件计算",
        standard="JGJ 130-2011",
        verified=False,
        param_spec=scaffold_tie_member.param_spec,
        run=scaffold_tie_member.run,
        geometry=_geometry("scaffold-tie-member", "连墙件计算"),
        report=report.build_generic_docx,
        category="落地与满堂",
    )
)

CANTILEVER = registry.register(
    registry.ModuleDef(
        key=cantilever_scaffold.MODULE_KEY,
        title="型钢悬挑脚手架",
        standard="JGJ 130-2011",
        verified=False,
        param_spec=cantilever_scaffold.param_spec,
        run=cantilever_scaffold.run,
        geometry=_geometry("cantilever-scaffold", "型钢悬挑脚手架"),
        report=report.build_generic_docx,
        category="悬挑与升降",
    )
)

FULL_HALL_SCAFFOLD = registry.register(
    registry.ModuleDef(
        key=full_hall_scaffold.MODULE_KEY,
        title="满堂脚手架",
        standard="JGJ 130-2011",
        verified=False,
        param_spec=full_hall_scaffold.param_spec,
        run=full_hall_scaffold.run,
        geometry=_geometry("full-hall-scaffold", "满堂脚手架"),
        report=report.build_generic_docx,
        category="落地与满堂",
    )
)

SUSPENDED_BASKET = registry.register(
    registry.ModuleDef(
        key=suspended_basket.MODULE_KEY,
        title="高处作业吊篮",
        standard="GB/T 19155-2017",
        verified=False,
        param_spec=suspended_basket.param_spec,
        run=suspended_basket.run,
        geometry=_geometry("suspended-basket", "高处作业吊篮"),
        report=report.build_generic_docx,
        category="工具式与平台",
    )
)

DOOR_SCAFFOLD = registry.register(
    registry.ModuleDef(
        key=door_scaffold.MODULE_KEY,
        title="门式钢管脚手架",
        standard="JGJ 128-2010",
        verified=False,
        param_spec=door_scaffold.param_spec,
        run=door_scaffold.run,
        geometry=_geometry("door-scaffold", "门式钢管脚手架"),
        report=report.build_generic_docx,
        category="落地与满堂",
    )
)

ATTACHED_LIFTING_SCAFFOLD = registry.register(
    registry.ModuleDef(
        key=attached_lifting_scaffold.MODULE_KEY,
        title="附着式升降脚手架",
        standard="JGJ 202-2010",
        verified=False,
        param_spec=attached_lifting_scaffold.param_spec,
        run=attached_lifting_scaffold.run,
        geometry=_geometry("attached-lifting-scaffold", "附着式升降脚手架"),
        report=report.build_generic_docx,
        category="悬挑与升降",
    )
)

GROUND_OPERATION_PLATFORM = registry.register(
    registry.ModuleDef(
        key=ground_operation_platform.MODULE_KEY,
        title="落地式操作平台",
        standard="JGJ 80-2016",
        verified=False,
        param_spec=ground_operation_platform.param_spec,
        run=ground_operation_platform.run,
        geometry=_geometry("ground-operation-platform", "落地式操作平台"),
        report=report.build_generic_docx,
        category="工具式与平台",
    )
)

CANTILEVER_OPERATION_PLATFORM = registry.register(
    registry.ModuleDef(
        key=cantilever_operation_platform.MODULE_KEY,
        title="悬挑式操作平台",
        standard="JGJ 80-2016",
        verified=False,
        param_spec=cantilever_operation_platform.param_spec,
        run=cantilever_operation_platform.run,
        geometry=_geometry("cantilever-operation-platform", "悬挑式操作平台"),
        report=report.build_generic_docx,
        category="工具式与平台",
    )
)
