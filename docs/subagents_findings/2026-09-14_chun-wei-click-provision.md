<!-- keywords: chun-wei, add-person, create-folders, forget, playwright, combo-snapback -->
<!-- main_idea: Click-typed Chun Wei, Create folders provisioned 29 SKUs; Forget dropped yaml. Combo used to snap unknown names back to Ariff -- fixed. -->

# Chun Wei click-through (2026-09-14)

## Human path (Playwright)

1. Type Operator folder `Chun Wei`
2. Click combo **Add Chun Wei**
3. Modal title **Add Chun Wei?** (after fix; before fix it said Add Ariff)
4. Click **Create folders**
5. Notice: `Added Chun Wei · 29 SKU folders + golden workbooks · log xlsx in _ate`
6. Header: `Power / RS3213 / SOT23-5 / Chun Wei / Version_1`
7. Disk: 29 `Chun Wei` trees + `RS3213_Lab_Report.xlsx`
8. More -> **Forget person** -> yaml row gone (`chunwei` removed). Folders stay by product law; test trees then deleted.

## Bugs found

| Issue | Fix |
|-------|-----|
| Typed new name then combo/Add person snapped to Ariff (`pickLiveOperator` first disk op) | Keep typed name if not in disk/yaml list |
| Combo **Add Chun Wei** did not open the modal (only Enter did) | `applyComboPick` opens add-person modal |
| Forget left Operator folder text as Chun Wei while top Operator = Eugene | Forget now writes fallback label into `#db-operator` |

## Cache

`app.js?v=20260914prov3` -- Ctrl+F5
