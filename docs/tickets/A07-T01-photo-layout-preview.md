# A07-T01 - Photo-grid SoT + Results waveform preview

**Epic:** EPIC-A07
**PRD:** PRD-001
**Status:** closed-accepted
**Step:** current: 6 / 6
**Depends on:** EPIC-A06 closed; A05 sheet_map honesty
**Model (implement):** composer-2.5-fast (parent executing F14)
**Model (verify/close):** Grok 4.5 high (`cursor-grok-4.5-high`)
**Adversary rule:** R-0003 - implementer is never the verifier

---

## Problem

Workbook photo boxes are duplicated: live `_manifest/sheet_map.yaml` `paste.photos` plus hardcoded dicts in `ate/reporting/lab_report.py` (`_SSSR_PHOTO_ANCHORS`, `_LSSR_PHOTO_ANCHORS`, `_SETTLING_UNIT_COLS`). Results is a last-run table only -- operators cannot see the DUT grid, compare waveforms, or adjust Excel cells on the laptop.

---

## Acceptance

WHEN paste helpers place SSSR / LSSR / Settling / ORT photos, THE SYSTEM SHALL resolve Excel anchors from campaign `sheet_map.yaml` `tests.<key>.paste.photos` via `ate/reporting/photo_layout.py` and SHALL NOT keep a second hardcoded A91/A84/col-map in `lab_report.py`.

WHEN Results is opened on the operator console, THE SYSTEM SHALL list tests that have `paste.photos`, reconstruct the DUT x channel (and POS/NEG when present) grid from Test_Database `graphs/` or `screenshots/`, and SHALL show latest vs previous for a clicked cell (side-by-side; overlay difference allowed).

WHEN the operator saves a new cell like `A92` from that grid, THE SYSTEM SHALL patch that key in `sheet_map.yaml` (preserve surrounding comments when using a line patch) so the next `embed_photo` uses it.

WHEN `python -m ate.reporting.check_photo_layout` runs, THE SYSTEM SHALL fail if `_SSSR_PHOTO_ANCHORS` (or sibling hardcoded maps) reappear in `lab_report.py`, and SHALL pass parser + YAML patch self-checks.

WHEN `python -m ate.core.check_family_load` and `python -m ate.core.check_lab_report_sync` run after the change, THE SYSTEM SHALL stay green.

WHEN worker GET `/shot` is used, THE SYSTEM SHALL refuse paths outside the campaign root or outside `screenshots`/`graphs`.

---

## Why it is not a one-liner

Trap: UI preview that still pastes from hardcoded dicts (two SoTs). Trap: serving arbitrary files from GET `/shot`. Trap: yaml.safe_dump wiping sheet_map comments. Trap: CSV chart library. Trap: reopening A06 BUFFER recipes.

---

## Files likely touched

- `ate/reporting/photo_layout.py` (new)
- `ate/reporting/check_photo_layout.py` (new)
- `ate/reporting/lab_report.py` - delete hardcoded photo dicts; call photo_layout
- `ate/worker/server.py` - `layout_preview`, `save_photo_layout`, GET `/shot`
- `ate/ui/web/index.html`, `app.js`, `styles.css`
- `docs/ATE_PLUGIN.md` - one slot: where to change image layout

---

## Step

```
Step: current: 1 / 6
```

1. [x] `photo_layout.py` parse / lookup / preview / surgical YAML save
2. [x] `lab_report.place_*` reads photo_layout only
3. [x] Worker RPC + GET `/shot` (campaign-root only)
4. [x] Results grid + compare + save
5. [x] `check_photo_layout` + family_load + lab_report_sync green
6. [x] Idle worker restart done; Ctrl+F5 note; R-0003 2026-09-13 PASS

---

## Out

PowerOn / Noise / PSRR; RS1G / Lim / Level; DataLogger replace; CSV canvas; A01-A06 reopen; GBW paste caller.
