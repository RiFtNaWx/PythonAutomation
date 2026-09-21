# ATE operator console -- status 2026-09-15

Paste this to stakeholders. Engineer detail: `AGENTS.md`, [PRD-001](docs/prd/PRD-001-ate-multi-product-platform.md), [PRD-002](docs/prd/PRD-002-operator-profile-workflow.md), [PRD-003](docs/prd/PRD-003-snippet-pointer-trigger.md). Leaving pack: [docs/handover/2026-09-11_jianhong_checklist.md](docs/handover/2026-09-11_jianhong_checklist.md).
**Printable next/upcoming ship plan:** [docs/SHIP_NEXT.md](docs/SHIP_NEXT.md). **Ticket ledger:** [docs/tickets/INDEX.md](docs/tickets/INDEX.md). **How to vibe-code / add a test:** [docs/VIBE_CODE.md](docs/VIBE_CODE.md).

## What is live today (Done)

1. One console (ports **8766** / **5174**) for OpAmp, Logic, Analog switch, Level stub. Left rail switches real tests, not only a folder name.
2. People: each person is a folder `.../{Name}/Version_N`. Eugene and Ariff do not overwrite each other. Add a person from Setup (no Python).
3. Campaigns: Create folders, type Version_N then Apply, Detect/Wrap golden tests (blocks `input()`), copy tests same family only.
4. Safety: PSU OVP/OCP always DUT-capped. START blocked until Open Session. Header **All** blocks writes.
5. Tags + who-ran-what: chips, TAGS.txt, Results Run ledger. Delete one session JSON without deleting the Version folder.
6. Photos: after a run, screenshots can paste into Excel cells listed in `sheet_map` (photo boxes only).
7. Central data: `#Test_Database` (Add shortcut to OneDrive, not Sync). No second Excel cloud writer.
8. Living latest results JSON per person+Version (`sessions/report.json`): re-run a subset of tests and old tests stay with their timestamps; new tests update. Full STARTs stay as `sessions/session_*.json`. Per-test history under `{test_key}/DUT_n/records/`.
9. STS datalog after each merge: `sessions/datalog.md` + `.html` + column-table `.pdf`. Limits from local Reference PDFs (`ate/core/lookup.py` + `ate/config/datasheets.yaml`) then `ate/config/limits/<key>.yaml`. Website only if that SKU has no local PDF.
10. Excel numbers: `sheet_map` `paste.values` DUT columns (RS622 TTSOP GBW `R20:U20`; SOP8 GBW `C21`; Logic VOX 4.5V DUT row probed on the sheet -- RS1G08 `G16`, RS1G32 `G21`; LIM Iplus `B2`). Every campaign map uses the same RS622 outline keys from `ate/core/campaign_outline.py` (no FILL_ME). Fill on session end or Results **Fill Excel numbers**. Merged cells skip; filled tracking xlsx does not get golden merge-center. Setup combos do not auto-Apply; click **Apply campaign**. Header Lim opens SeeLim's live RS2323 folder when that is the inventory PIC.
11. STS `datalog.pdf` is a column table (Parameter / Unit / Min / Max / Typ / Value / Result). Local PDF text is glyph-joined so `VOH` stays readable. Missing analog-switch / LDO PDFs fetch into local Reference only (not `#Test_Database`). RS2323 rON min/max table is still an image. DEMO on RS1G08 / RS622 / RS2323 / RS0204 stamps spec min/max/result into `report.json` + STS pdf (GBW stays unspec: typ only).

## Ongoing (next waves -- do these in order)

1. **A27 (READY, this pointer ask):** remember `file:line` in `snippet_map.yaml`; Remember/START triggers the original function; UI does not write Python. A16 wrap-copy stays leftover until T02. Do not reopen A16 tickets.
2. **A23:** typed `FORGET {label}` before yaml Forget. Folders stay. After A22 (implemented). Different files than A27; do not fly A25/A26 with A27.
3. **A22 (done):** Setup product-code chips + `assign_owner_products` -> `owners.yaml` `parts:` + this operator Version_1. Unassign drops yaml only. Ctrl+F5.
4. **A20 leftover:** RS2323 rON min/max is still a PDF image; banner typ 0.6 + IPLUS max 1. 1G CMOS VOH/VOL stamp from part yaml. STS PDF is a column table. Do not invent a rON table.
5. **A19 leftover:** Logic fill maps unique VOX Vcc rows only. Yaml 2.0 / 3.3 / 5.0 / 5.5 corners have no VOX row. RS0204 Icc/VOH stay unmapped until a live xlsx is probed. Do not guess cells.

Ticket scale: A27-T01/T02/T03 READY 2026-09-15 (PRD-003). A22-T01/T02 implemented 2026-09-14. A23 next on the profile board. A24-A26 still blocked / no tickets. A01-A21 stay closed/implemented.

## Not complete (do not tell the lab these work yet)

Must (buyer-visible leftovers):

1. Logic fill maps every unique VOX Vcc row (1.65 / 2.3 / 3.0 / 4.5 DUT G/H/I) plus ICC D10. Yaml 2.0 / 3.3 / 5.0 / 5.5 corners have no VOX row. RS0204 Icc/VOH stay unmapped (condition grids). ORT is photos; it does not invent recovery-time numbers.
2. Analog switch / LDO PDFs are website-fetched into local Reference when missing; RS2323 electrical table body is still an image. 1G CMOS push-pull parts have VOH/VOL tables like RS1G08. Open-drain 1G07 stays ICC/VCC.
3. Full measurement suites for stub RUN-IC classes: Comparator, Interface, Vref, Data conversion, Clock (`live: false`). Level/Power/LDO are partial stubs.
4. OpAmp **PSRR / CMRR / AOL / EMIRR / PowerOn** are still mapped captures. **Noise** is 0.1-10 Hz input-referred Vpp, not nV/rtHz.

Parked (explicitly out of scope for now):

5. OneDrive / Excel MCP merge-center (A13), Monaco full editor, ML trainer, NTFS Keywords, folder-delete on Forget, Users login. A14 Recipe canvas is unparked (closed opcodes; PRD-005).
6. Dual-stack delete of legacy `main.py` / root `*_tests.py`.
7. Scraping en.run-ic.com into `#Test_Database`.

## How the team continues without breaking others

Read [AGENTS.md](AGENTS.md).

- Do not edit `runner.py` to add a test.
- Do not edit `database.py` path shape.
- Do not start work in `main.py`.
- Do not wipe `sessions/report.json` across operators or invent a Tags/Users folder axis.
- Add-test Path A (this Version catalog) is not Path B (new TestSpec). Wrap scaffold is not filled. See [docs/VIBE_CODE.md](docs/VIBE_CODE.md).

## Quick proof commands

```
python -m ate.core.check_tags_datalog
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
python -m ate.core.check_add_test
python -m ate.core.check_demo_families
```
