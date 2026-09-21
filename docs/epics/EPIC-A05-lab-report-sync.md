# EPIC-A05 - OpAmp lab-report / sheet_map / TestSpec sync

**PRD:** [PRD-001-ate-multi-product-platform](../prd/PRD-001-ate-multi-product-platform.md)
**Repo:** PythonAutomation
**Status:** closed-accepted
**Sliced:** 2026-09-03 (epic-agent Mode A; F8 / F9)
**Closed:** 2026-09-03 (R-0003 adversary verify; F10)
**Tier:** boundary (report honesty) + visible surface (console lists missing sheets; runnable check)
**Depends on:** EPIC-A01 (closed); A02-A04 closed, not reopened
**Blocks:** none hard; later paste/automation for missing sheets depends on honest map
**Appetite:** 1 wave
**GitHub Issues:** do not open unless founder opts in

---

## Buyer-visible outcome

Operator / engineer can trust that every workbook **test** sheet (not Summary/Checklist) either has a matching registered OpAmp `TestSpec.lab_sheet` or is explicitly listed as missing; `sheet_map` `excel_sheet` names match the live xlsx; console does not pretend a sheet is covered when it is not.

---

## Acceptance (from PRD)

> WHEN the OpAmp lab-report sync check runs against the active campaign workbook + `sheet_map` + registered OpAmp `TestSpec.lab_sheet` values, THE SYSTEM SHALL FAIL if (1) a workbook test sheet (excluding Summary and Checklist) has no matching `TestSpec.lab_sheet`, OR (2) a registered `lab_sheet` is missing from the workbook, OR (3) a `sheet_map` `excel_sheet` value disagrees with the live xlsx sheet name it claims to map. WHEN a workbook test sheet such as Noise has no matching spec, THE SYSTEM SHALL list it in the console (a registered stub that raises RuntimeError is OK; inventing a measurement suite is not).

**Optional stretch (out of this slice):** Slew Rate / GBW paste via existing `lab_report` helpers. Skipped: SlewRate `sheet_map` has no photo anchors; GBW would need a new `place_*` path (not a few lines on `embed_photo` / `place_ort_photos` / `place_settling_photos`).

---

## Design constraints

- Source of truth for sheet names = live xlsx (`RS622XK_Lab_Report_TTSOP.xlsx` via campaign / `bench.yaml`). Fix `sheet_map` and/or `lab_sheet` strings to match; do not invent alternate names.
- Add Noise (and any other xlsx-only sheet) as stub or explicit listed gap - do **not** implement Noise/PSRR/CMRR/AOL measurement bodies.
- Known `sheet_map` drifts vs live names (must fail check until fixed): `Slew` vs `Slew Rate`, `PhaseReversal` vs `NoPhaseReversal`, `PowerOn` vs `PowerOnTime`, `VOHL` vs `VOL`. Map entries whose `excel_sheet` is not on the live workbook (e.g. Iq / Ib / Isc / IOS / Inoise / SlewTemp) must be removed, commented out of sync scope with honesty, or otherwise made so the check cannot green-pass while claiming a missing sheet.
- Runnable check: prefer extend `ate/core/check_family_load.py` **or** tiny sibling `ate/core/check_lab_report_sync.py`; must be greppable and CI/local runnable. Prefer sibling if cheaper than bloating family-load probes.
- Do not reopen A01-A04. Do not slice Level. Logic sheet_map / #Test_Database out unless proven to block OpAmp honesty.
- Part yaml id drift (BUFFER stub ids vs yaml; G1001 `vos_lab`) is note-only unless it blocks the sync check.

---

## Ticket index

| ID | File | Status | One-line acceptance |
|----|------|--------|---------------------|
| A05-T01 | [A05-T01-lab-report-sync.md](../tickets/A05-T01-lab-report-sync.md) | closed-accepted | sheet_map excel_sheet match live xlsx; Noise stub; sync check fails on missing/orphan/drift; console lists gaps |

**Ponytail:** one ticket. Map fix + Noise stub + runnable check share one honesty invariant and the same evidence (live sheets vs registry vs yaml). Splitting would race the check against a half-fixed map. No second ticket for paste stretch.

---

## File contention

| Area | Tickets | Note |
|------|---------|------|
| External campaign `_manifest/sheet_map.yaml` (path in `ate/config/bench.yaml`) | T01 | Fix `excel_sheet` drift; handle map-only orphans not on live xlsx |
| `ate/tests/opa/stubs.py` | T01 | Add Noise stub (`lab_sheet="Noise"`); keep RuntimeError pattern |
| `ate/core/check_lab_report_sync.py` (preferred) or extend `check_family_load.py` | T01 | Fail on (1)(2)(3); list missing sheets to console |
| `ate/config/bench.yaml` | T01 read | Resolves workbook + sheet_map paths |
| `ate/reporting/lab_report.py` | **out** | Paste stretch skipped this wave |
| `ate/tests/opa/slew.py`, `gbw.py` | **out** | No paste wiring this wave |

Later epics must not invent full Noise/PSRR suites just to make the check green - stub/list is enough.

---

## Out of epic

- Full Noise / PSRR / CMRR / AOL / EMIRR measurement automation
- Slew Rate / GBW workbook paste (stretch; needs anchors / new place_*)
- Full Level suite; no-code wizard
- Logic lab-report / sheet_map sync as a second product claim
- Reopening A01-A04
- GitHub Issues unless founder opts in

---

## Completeness (Mode B - after T01 closes)

**COMPLETE / closed-accepted (2026-09-03 R-0003).** Evidence (venv python; working_directory `EUGENE~1\PYTHON~1`):

1. Pass: `python -m ate.core.check_lab_report_sync` -> `OK lab-report sync...` exit 0
2. Prior green: `python -m ate.core.check_family_load` -> `OK opamp=17 logic=7 restored=17...` exit 0
3. Fail-path: temporarily set `SlewRate.excel_sheet` to `Slew` -> FAIL lists `SlewRate -> 'Slew'`; restored to `Slew Rate` -> pass again. Map left honest (BOM from temp edit stripped).
4. Static: Noise stub `lab_sheet="Noise"`; no Noise/PSRR measurement body; no `place_slew`/`place_gbw`; map excel_sheet matches live xlsx; Iq/Ib orphans gone.
5. RPC idle: `list_tests` includes `id=noise` / `lab_sheet=Noise`.

Finding: `docs/subagents_findings/2026-09-03_a05-t01-r0003-verify-pass.md`.
