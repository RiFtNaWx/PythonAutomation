# ATE operator console -- status 2026-09-11

Paste this to stakeholders. Engineer detail: `AGENTS.md`, `docs/prd/PRD-001-ate-multi-product-platform.md`.
**Printable next/upcoming ship plan:** [docs/SHIP_NEXT.md](docs/SHIP_NEXT.md).

## What is live today (Done)

1. One console (ports **8766** / **5174**) for OpAmp, Logic, Analog switch, Level stub. Left rail switches real tests, not only a folder name.
2. People: each person is a folder `.../{Name}/Version_N`. Eugene and Ariff do not overwrite each other. Add a person from Setup (no Python).
3. Campaigns: Create folders, +Version, Detect/Wrap golden tests (blocks `input()`), copy tests same family only.
4. Safety: PSU OVP/OCP always DUT-capped. START blocked until Open Session. Header **All** blocks writes.
5. Tags + who-ran-what: chips, TAGS.txt, Results Run ledger. Delete one session JSON without deleting the Version folder.
6. Photos: after a run, screenshots can paste into Excel cells listed in `sheet_map` (photo boxes only).
7. Central data: `#Test_Database` (sync that folder with OneDrive/SharePoint if the lab wants cloud). No second Excel cloud writer.
8. Living latest results JSON per person+Version (`sessions/report.json`): re-run a subset of tests and old tests stay with their timestamps; new tests update. Full STARTs stay as `sessions/session_*.json`. Per-test history under `{test_key}/DUT_n/records/`.
9. STS datalog after each merge: `sessions/datalog.md` + `.html` + column-table `.pdf`. Limits from local Reference PDFs (`ate/core/lookup.py` + `ate/config/datasheets.yaml`) then `ate/config/limits/<key>.yaml`. Website only if that SKU has no local PDF.
10. Excel numbers: `sheet_map` `paste.values` DUT columns (RS622 TTSOP GBW `R20:U20`; SOP8 GBW `C21`; Logic VOX `G16` for VOH 4.5V; LIM Iplus `B2`). Fill on session end or Results **Fill Excel numbers**. Merged cells skip; filled tracking xlsx does not get golden merge-center. Setup combos do not auto-Apply; click **Apply campaign**. Header Lim opens SeeLim's live RS2323 folder when that is the inventory PIC.
11. STS `datalog.pdf` is a column table (Parameter / Unit / Min / Max / Typ / Value / Result). Local PDF text is glyph-joined so `VOH` stays readable. Missing analog-switch / LDO PDFs fetch into local Reference only (not `#Test_Database`). RS2323 rON min/max table is still an image.

## Ongoing (next waves -- do these in order)

1. **A20 leftover:** RS2323 rON min/max is still a PDF image; banner typ 0.6 + IPLUS max 1. 1G CMOS VOH/VOL stamp from part yaml. STS PDF is a column table.
2. **R-0003:** Independent verify still pending on A07-A12.
3. Stub RUN-IC classes stay parked.

## Not complete (do not tell the lab these work yet)

Must (buyer-visible leftovers):

1. Logic fill maps the overlapping 4.5V VOX cells plus ICC D10, not every yaml VCC corner. RS0204 Icc/VOH stay unmapped (condition grids). ORT is photos; it does not invent recovery-time numbers.
2. Analog switch / LDO PDFs are website-fetched into local Reference when missing; RS2323 electrical table body is still an image. 1G CMOS push-pull parts have VOH/VOL tables like RS1G08. Open-drain 1G07 stays ICC/VCC.
3. Full measurement suites for stub RUN-IC classes: Comparator, Interface, Vref, Data conversion, Clock (`live: false`). Level/Power/LDO are partial stubs.
4. OpAmp **PSRR / CMRR / AOL / EMIRR / PowerOn** are still mapped captures. **Noise** is 0.1-10 Hz input-referred Vpp, not nV/rtHz.

Parked (explicitly out of scope for now):

5. OneDrive / Excel MCP merge-center (A13), xyflow canvas (A14), no-code test wizard, ML trainer, NTFS Keywords.
6. Dual-stack delete of legacy `main.py` / root `*_tests.py`.
7. Scraping en.run-ic.com into `#Test_Database`.

## How the team continues without breaking others

Read [AGENTS.md](AGENTS.md).

- Do not edit `runner.py` to add a test.
- Do not edit `database.py` path shape.
- Do not start work in `main.py`.
- Do not wipe `sessions/report.json` across operators or invent a Tags/Users folder axis.

## Quick proof commands

```
python -m ate.core.check_tags_datalog
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
```
