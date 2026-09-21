# EPIC-A07 - Photo-grid SoT + Results waveform preview

**PRD:** [PRD-001-ate-multi-product-platform](../prd/PRD-001-ate-multi-product-platform.md)
**Repo:** PythonAutomation
**Status:** implemented
**Sliced:** 2026-09-03 (F14)
**Tier:** visible surface + paste SoT
**Depends on:** EPIC-A06 closed; A05 sheet_map honesty
**Blocks:** none hard
**Appetite:** 1 wave
**GitHub Issues:** do not open unless founder opts in

---

## Buyer-visible outcome

Operator opens Results, picks a characterization test, sees the same DUT x channel photo grid the lab workbook uses, reconstructed from Test_Database graphs (preferred) or screenshots. Click a cell to compare latest vs previous waveform. Edit the Excel anchor and Save -- that writes `_manifest/sheet_map.yaml` `paste.photos`, which is the only place Python paste reads.

---

## Acceptance (from PRD)

> WHEN an engineer changes a photo box, THE SYSTEM SHALL have one SoT: campaign `_manifest/sheet_map.yaml` `tests.<key>.paste.photos` (Python paste helpers SHALL read that map, not a second hardcoded A91 dict). WHEN the operator opens Results and selects a test that has `paste.photos`, THE SYSTEM SHALL reconstruct that DUT x channel grid from Test_Database `graphs/` (preferred) or `screenshots/` and SHALL let them compare the latest capture to the previous one. WHEN they save a new Excel cell from that page, THE SYSTEM SHALL write that cell back into `sheet_map.yaml` so the next `embed_photo` uses it.

**Ticket-level sharpening:**

- `ate/reporting/photo_layout.py` is the lookup module. `lab_report.place_*` must not keep `_SSSR_PHOTO_ANCHORS` / `_LSSR_PHOTO_ANCHORS` / `_SETTLING_UNIT_COLS`.
- `python -m ate.reporting.check_photo_layout` SHALL fail if those hardcoded maps return, and SHALL prove parser + YAML patch + live map lookup.
- Family load + lab-report sync stay green.
- Ports stay 8766 / 5174. Worker GET `/shot` only serves files under the campaign root in `screenshots` or `graphs`.

---

## Design constraints

- Reconstruct with existing PNG/JPG. No CSV chart library this wave.
- Overlay may be CSS mix-blend. No OpenCV.
- Surgical YAML patch for Save (keep comments). Do not dump a rewritten unordered map if a line patch works.
- Do not reopen A01-A06. Do not slice PowerOn / Noise / PSRR / RS1G / Lim / Level. Do not replace DataLogger.

---

## Ticket index

| ID | File | Status | One-line acceptance |
|----|------|--------|---------------------|
| A07-T01 | [A07-T01-photo-layout-preview.md](../tickets/A07-T01-photo-layout-preview.md) | implemented (R-0003 pending) | sheet_map SoT + Results grid compare/save + check_photo_layout |

**Ponytail:** one ticket. Lookup + UI + save share the same YAML keys.

---

## Out of epic

- CSV-to-canvas traces; drag-drop Excel clone
- GBW paste caller (anchors already in yaml)
- PowerOn / Noise / PSRR bodies; RS1G / Lim / Level
- DataLogger replacement; second Excel system
