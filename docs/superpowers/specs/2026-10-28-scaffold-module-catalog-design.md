# 2026-10-28 Scaffold Module Catalog Design

## Goal

Expose the complete scaffold directory shown in the three Pinming screenshots in
the Xuangou Tianshu calculation workbench without pretending that unimplemented
calculations exist. The catalog contains 70 entries: 10 entries backed by the
existing registry and 60 explicitly planned entries.

## Sources of truth

- `services/calc-api/calc_core/module_catalog.py` owns region order, category
  order, category `isNew`, module titles, stable keys, availability and status.
- `services/calc-api/calc_core/registry.py` remains the executable-module
  registry and contains exactly the existing 10 modules.
- Available catalog entries map to an existing registry key. Planned entries use
  the unique key `planned:<slug>` and are never registered.

## Region order

`全国、上海、浙江、广东、江苏、山东、重庆、北京、湖北、福建`

The project region is fixed when a project is created. The calculation page only
shows the ordered regions as non-interactive context and highlights the current
project region.

## Category order

1. 常用验算
2. 落地式脚手架
3. 爬架临时支撑平台 (`isNew=true`)
4. 吊篮工程
5. 移动操作平台
6. 井道操作平台
7. 斜道
8. 操作平台、卸料平台
9. 施工升降机卸料平台
10. 工具式脚手架
11. 防护棚 (`isNew=true`)
12. 型钢悬挑脚手架
13. 花篮螺栓悬挑架

## HTTP contract

`GET /api/v1/catalog/modules` returns:

```json
{
  "regions": ["全国", "上海", "..."],
  "categories": [
    {
      "key": "common-checks",
      "title": "常用验算",
      "isNew": false,
      "modules": [
        {
          "key": "scaffold-tie-member",
          "title": "连墙件计算",
          "standard": "JGJ 130-2011",
          "verified": false,
          "available": true,
          "status": "available",
          "note": ""
        }
      ]
    }
  ],
  "modules": []
}
```

`modules` is a flat concatenation of every category module in catalog order for
compatibility with clients that still consume the older endpoint shape.

Available entries obtain `standard` and `verified` from the registry. Planned
entries have an empty standard, `verified=false`, `available=false`,
`status="planned"`, and the fixed note `计算内核待接入`.

The registry remains unchanged. `/param-spec/<key>` and `/runs` therefore return
404 for every `planned:*` key.

## Workbench behavior

- Render all 10 regions from the backend response. They are not buttons or
  selectors; their accessible group label is
  `项目地区（创建项目时确定）`, and the project region is highlighted.
- Render categories in backend order, including the `新增` badge for categories
  with `isNew=true`.
- Available modules are selectable. Available modules with `verified=false` show
  `骨架版`.
- Planned modules show `待接入`, expose `disabled` and `aria-disabled=true`, and
  never call `onSelect`.
- Search matches module title, standard and category title. A non-matching query
  shows an explicit empty result.
- Preserve project/scheme links, module-category collapse, search, workbench
  return link, and new-scheme actions.
- The default selected module remains `scaffold-fastener`. Only available keys
  can enter the geometry, parameter-spec, run, batch, report or export flows.

## Non-goals

- No calculation formula, backend run behavior, project CRUD, navigation,
  authentication or region enumeration changes.
- No implementation of the 60 planned calculations.
- No calculation-page region switching.

## Verification

- Backend contract tests cover region/category/catalog order, 70 unique entries,
  the 10 available registry mappings, and planned keys being non-runnable.
- Registry tests continue to assert exactly the existing 10 modules.
- Frontend tests cover all regions and categories, planned disabling,
  available selection, catalog search, collapse and existing project/scheme
  behavior.
- Run backend tests, frontend tests, typecheck, build, smoke scripts and a real
  browser flow against an Shanghai project. Confirm the QA SQLite project is
  removed afterward.
