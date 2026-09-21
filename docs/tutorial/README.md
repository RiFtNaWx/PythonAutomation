# ATE tutorial (OneNote paste pack + HTML)

GitHub account, Git, Python PATH, `env.local`, and the green **push** button already live in the Github_Auto OneNote. **Do not copy that notebook here.**

This folder is the ATE operator console (`ate/` + worker **8766** + UI **5174**).

Write a golden `def test_*` (same delay style, then import + gated push): **[goldens/TUTORIAL.md](../../goldens/TUTORIAL.md)**.

## Full HTML tutorial (open in browser)

**[ATE_TUTORIAL.html](ATE_TUTORIAL.html)** -- every tab, workflow, and screenshot in one page. Sticky table of contents. Pictures in [images/](images/).

Open the HTML in Chrome. If a picture is missing, press Ctrl+F5.

## How a normal person runs a test

1. Double-click `START.bat` at the repo root (or the unzip). Wait for **Starting...** to clear.
2. Pick **your name** (not All, not Kevin). Left: family (Logic / OpAmp / ...). Click **Apply campaign**.
3. DUT **1**, channel **A**, tick **one** test on Setup.
4. No instruments: **DEMO (SIM)**. Instruments plugged in: **Discover** -> **Open Session** -> **START**, then **Continue** at each pause.
5. **Results** shows pass/fail. Files land in that Version `sessions` folder (`datalog.pdf`, `report.json`).

## OneNote paste pack

| OneNote page | File section | Who |
|--------------|--------------|-----|
| 1. Get the console | [ATE_ONENOTE.md](ATE_ONENOTE.md) Page 1 | Zip operators + git vibe-coders |
| 2. Run a campaign | Page 2 | Everyone who clicks START / DEMO |
| 3. Improve / vibe-code | Page 3 | Cursor / VS Code people |
| 4. Add / customize a test | Page 4 | Path A customize, Path B realize, Path C wrap |

Screenshots in [images/](images/) -- all filled 2026-09-14:

| File | What you see |
|------|----------------|
| `09-sharepoint-testdb.png` | SharePoint Add shortcut |
| `04-test-database-folder.png` | OneDrive shortcut in Explorer |
| `06-cloud-db-txt.png` | `cloud_db.txt` |
| `05-boot-splash.png` | Starting... |
| `15-first-run.png` | Who are you |
| `01-setup-campaign-session.png` | Setup + START / DEMO |
| `03-tests-customize.png` | Tests tab |
| `10-run-timeline.png` | Run tab after CIN DEMO |
| `02-results-sts.png` | Results STS table |
| `08-continue-gate.png` | Continue / Abort |
| `12-usb-live.png` | USB: do not DEMO |
| `12-discover-empty.png` | No USB instruments |
| `13-sessions-folder.png` | `sessions` with `datalog.pdf` |
| `07-psu-wiring.png` | PSU channel map |

Paste: each `=== PAGE n ===` heading = one OneNote page. Insert the PNG next to the step that names it (left picture, right bullets -- same layout as the Github_Auto tutorial).
