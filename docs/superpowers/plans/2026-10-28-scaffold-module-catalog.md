# Scaffold Module Catalog Implementation Plan

## Commit 1: plan

Add this plan and the design spec. Commit only:

- `docs/superpowers/specs/2026-10-28-scaffold-module-catalog-design.md`
- `docs/superpowers/plans/2026-10-28-scaffold-module-catalog.md`

Commit message: `docs(calc): plan scaffold module catalog`

## Commit 2: backend catalog

1. Add `services/calc-api/calc_core/module_catalog.py`.
2. Define the exact region order, 13 categories, category `isNew` flags, all 70
   module titles and stable keys, and the 10 registry-backed mappings.
3. Build the response by enriching available entries from `registry`; leave
   planned keys out of the registry.
4. Change `/api/v1/catalog/modules` to return `regions`, ordered `categories` and
   a flat compatibility `modules` list.
5. Add contract tests for counts, ordering, unique keys, mappings, and unavailable
   keys.

## Commit 2: frontend catalog

6. Extend `apps/calc/src/api/calc.ts` with catalog/module types and the new
   response.
7. Update mocks and API tests to provide the complete wire shape.
8. Replace the hard-coded taxonomy in `ModuleTree.tsx` with backend categories and
   regions while preserving project, scheme, search and collapse behavior.
9. Update region order in `apps/calc/src/api/projects.ts`.
10. Add/update component and workspace tests for regions, all categories,
    planned/available behavior, search and existing interactions.

## Commit 2: QA

11. Add `docs/qa/2026-10-28-scaffold-module-catalog.md` with catalog counts,
    command results and browser evidence.
12. Commit only the implementation, tests and QA files with message
    `feat(calc): add complete scaffold module catalog`.

## Verification gates

Run from the repository root:

```powershell
cd services/calc-api
python -m pytest -q
cd ..\..
npm --prefix apps/calc test
npm --prefix apps/calc run check-types
npm --prefix apps/calc run build
node --check apps/calc/scripts/smoke.mjs
```

With the local dev stack running on `http://localhost:5179`, run ordinary and
dev-login smoke. Then use a real browser on an Shanghai project to verify:

- all 10 regions appear in the specified order;
- all 13 categories and representative planned entries appear;
- searching `防护棚` shows planned entries that cannot be clicked;
- the existing `扣件式脚手架` remains selectable and runs.

Delete the QA project and confirm the SQLite QA project residue is zero.

## Delivery

Push the branch without force and open a PR targeting
`feat/auth-project-workspace`. Do not include pre-existing dirty files,
`bun.lock`, screenshots or artifacts in the implementation commits.
