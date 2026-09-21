<!-- keywords: add-person, provision-operator, all-skus, golden-workbook, playwright, 5174, btn-provision-person -->
<!-- main_idea: Add person Create folders (checkbox default ON) and More "All SKUs + golden" call the same provision_operator RPC as the JianHong CLI so every new operator gets inventory trees + empty pretty workbooks. -->

# Add-person button = JianHong provision (2026-09-14)

## UI

- Setup `#btn-add-operator` -> `#add-operator-all-skus` checked by default.
- Create folders -> RPC `provision_operator` (all `inventory.yaml` SKUs + empty golden xlsx + `_ate` log).
- Uncheck -> ticks only (`only_parts`), still golden xlsx for those SKUs.
- More `#btn-provision-person` re-runs all-SKU for the current Operator folder.
- Did not click Create on live Eugene (would rewrite Eugene `parts:` to all 29).

## Proof

- `python -m ate.core.check_ui_contract` OK
- `python -m ate.core.check_provision_operator` OK (29 + only_parts slice=1)
- Worker RPC dry_run JianHong count=29
- Playwright 5174: Add person modal checkbox ON, Cancel; More shows All SKUs + golden; Tests/Run/Results; Logic heading; JianHong in Operator list
- Console: favicon 404 only

## Repeat

Type name in Operator folder -> Add person -> Create folders (~10-20s). Ctrl+F5 after UI pull (`?v=20260914prov1`).
