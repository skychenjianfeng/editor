# 2026-10-28 Scaffold Module Catalog QA

## Scope

Verified the complete scaffold catalog in the Xuangou Tianshu calculation
workbench without changing calculation formulas, run behavior, project CRUD,
navigation or authentication.

## Catalog contract

- Regions: 10
- Categories: 13
- Total modules: 70
- Available modules: 10
- Planned modules: 60
- Planned note: `计算内核待接入`
- Planned key prefix: `planned:`

Region order:

`全国、上海、浙江、广东、江苏、山东、重庆、北京、湖北、福建`

The backend contract test checks every screenshot category and module title,
unique keys, the exact 10 registry mappings, and that planned keys are absent
from the registry. It also verifies that each planned key returns 404 for
`/param-spec` and `/runs` and creates no calculation run.

## Automated verification

Backend:

```text
cd services/calc-api
python -m pytest -q
298 passed, 7 warnings in 38.49s
```

The seven warnings are existing `pyparsing` deprecation warnings from `ezdxf`.

Frontend:

```text
npm --prefix apps/calc test
20 test files passed, 55 tests passed in 8.88s

npm --prefix apps/calc run check-types
passed

npm --prefix apps/calc run build
passed; Vite reported the existing >500 kB chunk-size warning

node --check apps/calc/scripts/smoke.mjs
passed
```

Biome checked all changed frontend files. Ruff checked the changed backend files.
No formatting or lint errors remained. Two pre-existing informational React
dependency diagnostics remain in the workspace page effect; neither fails the
check.

## Smoke

Ordinary smoke against `http://localhost:5179`:

```text
smoke ok: login=200 root=present workspace-fallback=200
redirect=/login?next=/workspace anonymous-me=401
```

Dev-login smoke:

```text
smoke ok: dev-login=prefilled routes=4 active=desktop+computed-colors
desktop-nav=232px mobile-expanded=aria desktop-directory=true
mobile-close=button+escape+navigation viewport=1440+1024+390 overflow=none
console-errors=0 qa-project=ui-crud+1024-actions-visible+calc
+1024-ui-deleted cleanup=finally
```

## Real browser evidence

Google Chrome 1440×900, local dev stack:

- Logged in with the local prefilled development account.
- Opened an Shanghai project calculation route.
- Observed all ten regions in exact order; only `上海` carried
  `aria-current="true"`.
- Observed all 13 catalog categories exactly once.
- Searched `防护棚`; `防护棚(扣件式)` appeared with `待接入`, `disabled`, and
  `aria-disabled="true"`.
- Clicked the disabled planned button through the DOM; no planned
  parameter-spec or run request was issued.
- Switched to `扣件式脚手架（品茗双立杆）`; POST `/api/v1/runs` returned 200 for
  `scaffold-fastener-pinming`.
- Switched back to `扣件式脚手架`; POST `/api/v1/runs` returned 200 for
  `scaffold-fastener`, and the item remained `aria-current="page"`.
- Browser console errors: 0. Page errors: 0.

The real-browser QA project was deleted in a `finally` cleanup. A subsequent
SQLite query for project names beginning with `QA ` returned:

```text
{'qa_project_count': 0, 'names': []}
```
