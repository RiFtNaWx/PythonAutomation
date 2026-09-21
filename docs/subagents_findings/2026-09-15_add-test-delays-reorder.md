keywords: prd-004, settle_s, timeout_s, dwell_s, overlay_for, test_params, html5-reorder, enabled_tests, path-a, path-b, check_add_test, not-a14
main_idea: PRD-004 recipe adds per-test settle/timeout/dwell via Parameters+Write and RunParams.overlay_for; Tests page Path A uses HTML5 drag reorder into test_catalog.yaml enabled_tests order (not xyflow); check_add_test validates parts yaml ids, repo snippet_map pointers, and no input() in registered runs.

## Part 1 -- recipe timing

- `ate/core/database.py` `_TEST_PARAM_FLOATS` includes `settle_s`, `timeout_s`, `dwell_s`.
- `ate/core/runner.py` `RunParams` fields + `overlay_for` copies them per test_id.
- `ate/ui/web/app.js` `testParamEditorHtml` + `collectOneTestParams` round-trip via `data-param`.
- `ate/tests/logic/eugene_cap.py` `_recipe_dwell_s` + `_dmm_ua_after_settle(dwell_s=...)`.
- `ate/tests/logic/ariff_dc.py` `_recipe_settle_s` for VOH/VOL; `_settle_ua(..., params=...)`.

## Part 2 -- Add/save + reorder (not A14)

- `#panel-campaign-tests` hint: Add / save tests; drag `::` handle on `#campaign-tests`.
- `campaignTestOrderIds()` + `initCampaignTestReorder()`; Save uses DOM order for checked ids.
- `list_campaign_tests` sorts `available` by catalog `enabled_tests` order when present.
- `index.html` cache bump `?v=20260915recipe2`; `styles.css` drag-handle chrome.

## Part 3 -- checks

- `check_walk_order`: timing clean + overlay_for round-trip.
- `check_ui_contract`: paramNumInput timing keys + reorder helpers (explicit not A14).
- `check_add_test` `_check_path_b_integrity`: parts enabled_tests vs all families registry; repo `snippet_map` file:line; registered run() no `input()`; scaffold honesty marker kept.

## Skipped

- A14 xyflow / Monaco / no-code wizard (explicitly not built).

## Verify

```
subst Z: "c:\Users\OoiJianHong\Eugene's Repo\PythonAutomation"
Z:\venv\Scripts\python.exe -m ate.core.check_walk_order
Z:\venv\Scripts\python.exe -m ate.core.check_ui_contract
Z:\venv\Scripts\python.exe -m ate.core.check_add_test
Z:\venv\Scripts\python.exe -m ate.core.check_test_detect
```

Operator: **Ctrl+F5** after UI pull; idle-restart worker when `ate/tests/**` or `runner.py` changed.
