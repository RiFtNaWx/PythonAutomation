---
keywords: dropdown, combobox, datalist, tags, setup-label-value, detect-family, run-conditions, duplicate-chips, enter-key, layout-test
main_idea: Setup path combos are migrated off datalist and open via .combo + #ate-combo-menu. Remaining REAL bugs are keyboard Enter racing on label Value, duplicate tag chips on Setup, detect-family reset, custom run-condition ids ignored in params(), and empty layout-test select.
---

# 2026-09-10 UI dropdown / combo / tag leftovers audit

PREFLIGHT: PARTIAL. Reuse: combo-tags-excel, setup-combo-level, extend-conditions-dropdowns. Spawn: skip.

Scope: `ate/ui/web/index.html`, `app.js` (fillCombo, fillSelect, initCombos, renderTagChips, renderConditions, owner/inv/layout/detect selects), `styles.css`, `ate/core/check_ui_contract.py`. Read-only audit.

## Not bugs (confirmed OK)

- No `<datalist>` or `list=` left in `ate/ui/web/` (`check_ui_contract.py` lines 62-63 guard this).
- Setup Component / Part / Package / Operator / Version / Kind / Value / board use `.combo` + body `#ate-combo-menu` (`app.js` 1070-1351, `styles.css` 427-526). Caret + mousedown opens menu.
- Native `<select>` with `appearance: none` still has CSS chevron (`styles.css` 393-401). `owner-select`, `inv-select`, `np-category`, `detect-family`, `detect-copy-from`, `layout-test`, run-condition `cond-*`, and `gain-profile-manual` should open on click.
- `inv-select` option `value` is the original `inventoryRows` index, not filtered position (`app.js` 273-284, 336-337) -- selection maps correctly.

## Ranked REAL bugs

### 1. Setup label Value -- Enter adds filter text, not highlighted row

| | |
|---|---|
| **Where** | `ate/ui/web/app.js:2187-2193` vs `1248-1295` |
| **Breaks** | In Add labels -> Value combo: type to filter, ArrowDown to highlight a row, press Enter. The first keydown handler clicks **Add label** with the raw filter string in the input. `onComboKey` runs second and only sets the input to the highlight. Operator gets the wrong label (partial text) or a duplicate/wrong token. Mouse pick works. |
| **Smallest fix** | Drop the extra `keydown` on `#setup-label-value`, or in that handler `if (comboOpenId === "setup-label-value" && comboHi >= 0) return;` before clicking Add, or call `stopImmediatePropagation` from `onComboKey` when it handles Enter. |

### 2. Duplicate tag chips on Setup (same token twice)

| | |
|---|---|
| **Where** | `ate/ui/web/index.html:109-140`, `ate/ui/web/app.js:1798-1804`, `2157-2168` |
| **Breaks** | `addSetupLabel` / `addCampaignTagFromText` push both `campaignLabels` and `campaignTags`. `paintTagsEditor` renders `campaignTags` in `#db-tag-chips` and `campaignLabels.map(labelToken)` in `#setup-label-chips`. Every label/tag appears twice on the same Setup panel (e.g. `board:G11-REV1` in both rows). Remove works from either row but looks like duplicate controls. |
| **Smallest fix** | Show labels only in `#setup-label-chips` and free-form tags only in `#db-tag-chips` (split by kind), or remove one chip row and keep a single editor. |

### 3. Wrap family select resets on every detect refresh

| | |
|---|---|
| **Where** | `ate/ui/web/app.js:1891-1896`, `1915-1920` |
| **Breaks** | Operator picks a different **Wrap family** then clicks Refresh scan, Apply campaign, or Wrap (all call `refreshDetectedPanel`). `fillDetectFamilySelect` always passes `activeFamily` as `selected`, wiping the choice. Scan list correctly uses `activeFamily` (`1922`); only wrap target (`2545`) reads the dropdown -- so the control looks interactive but the choice does not stick. |
| **Smallest fix** | In `fillDetectFamilySelect`, use `el.value || activeFamily` (if still in `fams`) instead of always `activeFamily`. |

### 4. Run conditions dropdowns beyond vcc/vccb never reach START params

| | |
|---|---|
| **Where** | `ate/ui/web/app.js:755-786`, `466-482`, `500-525` |
| **Breaks** | `renderConditions` builds `<select id="cond-${c.id}">` for any yaml `controls:` row with choices. `benchValues()` only reads `cond-vcc` and `cond-vccb` via `condNum`. Custom control ids (explicit `controls:` in part yaml) render and accept clicks but START/DEMO ignore them. |
| **Smallest fix** | Loop `paramCatalog.controls` in `benchValues()` or `params()` and copy each `cond-${id}` value into the params object under `c.id`. |

### 5. Waveform layout Test select empty when no mapped tests

| | |
|---|---|
| **Where** | `ate/ui/web/app.js:2755-2764`, `index.html:327-329` |
| **Breaks** | After Apply with no `sheet_map` / layout tests, `fillLayoutSelect` sets `innerHTML` to `""`. `#layout-test` is a dead empty dropdown; Reload does nothing useful. |
| **Smallest fix** | When `tests.length === 0`, inject one disabled `<option>-- no mapped tests --</option>` and skip RPC until a test exists (mirror `inv-select` placeholder pattern at `278`). |

### 6. Tag combo dropdown x does not prune label vocab (suggestions return)

| | |
|---|---|
| **Where** | `ate/ui/web/app.js:1223-1234` vs `1235-1244` |
| **Breaks** | `x` on `#db-tag-input` menu rows updates `comboStore` and campaign state but not `labelValueVocab` / `boardVocab`. `setup-label-value` path does prune vocab (`1235-1239`). After Reload tags, removed suggestions reappear from server vocab. |
| **Smallest fix** | Mirror the `setup-label-value` branch: drop the value from `labelValueVocab[kind]` / `boardVocab` before `saveCampaignLabels()`. |

## Lower / UX (not ranked as dead dropdowns)

- **detect-family vs scan**: Scan always uses `activeFamily` (`1922`); dropdown label is Wrap family only. Not a dead list; document in hint if operators expect scan to follow the box.
- **addSetupLabel duplicate**: silent no-op (`2163`) -- Enter/Add with existing token looks like Enter does nothing.
- **Tags tab vs Setup**: `#db-tag-input` and Tags page `#tag-free` both edit `campaignTags` -- intentional cross-page, not same-panel duplicate.
- **check_ui_contract.py**: Does not assert combo bind or select population; only tabs/fonts/datalist absence (`55-63`). UI combo regressions need a separate check or manual Ctrl+F5 pass.

## Checks (not run in this audit -- shell path quoting failed)

```
python -m ate.core.check_ui_contract
```

Expected: OK (no datalist leftovers in index.html).

Manual smoke (Ctrl+F5 `?v=20260910combo7`):

1. Setup -> Value combo: filter + ArrowDown + Enter -- label should match highlight.
2. Add label -> confirm single chip row (not two).
3. Detected tests -> change Wrap family -> Refresh scan -- selection should persist.
4. Logic/Level part with VCC corners -> change dropdown -> DEMO params in log should match.
5. Results -> layout Test with fresh campaign -- placeholder or disabled state, not blank select.
