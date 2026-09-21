# ATE operator console -- 3 OneNote pages

GitHub login, Git install, `git config`, `env.local`, and `.\push` / green circle are **already** in the Github_Auto OneNote. This notebook is only PythonAutomation ATE.

Live product: `ate/` + worker **8766** + UI **http://127.0.0.1:5174**. Do not start new tests in root `main.py`.

How to paste: each `=== PAGE n ===` is one OneNote page. Put the PNG on the **left**, steps on the **right** (same as the Github_Auto collage).

---

=== PAGE 1 ===

# Get the ATE console on this PC

Two tracks. Pick one. Do not mix (do not keep a private unzip copy if you also git clone).

| Who | You get | Database |
|-----|---------|----------|
| **Run tests only** | Zip `ATE_Console_Try_*.zip`, double-click `START.bat` | Same OneDrive shortcut of `#Test_Database` |
| **Change the product** (vibe-code) | `git clone -b eugene-console` this repo, double-click `START.bat` | Same folder. Never a second database |

## Step 1 -- You already have GitHub + Git + Python

Use the Github_Auto OneNote for: GitHub account, Company Portal Python (tick **Add Python to PATH**), Git for Windows (PATH = "Git from the command line and also from 3rd-party software"), `git --version`, `git config --global user.name` / `user.email`.

**IMAGE A (capture):** GitHub profile username visible (Eugene must see this on the PR). Same shot as Github_Auto Step 1.

If Eugene has not added your GitHub user to `RiFtNaWx/PythonAutomation`, clone will fail. Send him your username.

## Step 2 -- Add OneDrive shortcut (not Sync)

Everyone writes into the OneDrive shortcut of `#Test_Database`. Windows cannot use the https URL as a folder.

Lab folder (everyone): [SharePoint Handover / Jianhong / #Test_Database](https://jumptechwin.sharepoint.com/sites/RD/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FRD%2FShared%20Documents%2FGeneral%2FHandover%2FJianhong%2F%23Test%5FDatabase&p=true&ga=1)

1. Open that URL. Click **Add shortcut to OneDrive** (not Sync, not drag-copy).
2. If asked *Replace folder with your shortcut?* click **Replace**.
3. Wait for Explorer under `OneDrive - JumpWin Tech\Research & Development - #Test_Database`. Right-click -> **Always keep on this device**.
4. `START.bat` or `python -m ate.core.sync_cloud_db` writes `ate/config/cloud_db.txt` (one local path, not https).

**IMAGE A (capture):** SharePoint page with **Add shortcut to OneDrive** -- `docs/tutorial/images/09-sharepoint-testdb.png`
**IMAGE B (capture):** Explorer OneDrive shortcut with OpAmp / Logic / Level -- `docs/tutorial/images/04-test-database-folder.png`
**IMAGE C (capture):** Notepad of `cloud_db.txt` OneDrive path -- `docs/tutorial/images/06-cloud-db-txt.png`

## Step 3A -- Zip operators (no git)

1. Unzip `ATE_Console_Try_*.zip` (Desktop or `dist/`).
2. Confirm `cloud_db.txt` (Step 2).
3. Double-click `START.bat`. First run 2-5 min (`venv` + pip).
4. Browser opens `http://127.0.0.1:5174`. If the page looks old: **Ctrl+F5**.

**IMAGE D (capture):** Explorer of the unzip with `START.bat` highlighted.
**IMAGE E (capture):** First splash "Operator console / Starting..." then the Setup page.

Do not edit Python in the zip. Do not copy `#Test_Database` into the zip.

## Step 3B -- Vibe-coders (git clone)

Default GitHub `main` is the **old** lab tree. Day-to-day console is branch **`eugene-console`**.

Open VS Code / Cursor terminal in a parent folder (not inside someone else's clone) and run:

```
git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git
cd PythonAutomation
python --version
python install.py
```

`install.py` creates `venv\`, installs packages, and may start the Github_Auto green push button (that button is git, not ATE). First time takes a few minutes. You want:

```
INSTALLATION COMPLETED SUCCESSFULLY
```

Then:

```
run_ate_app.bat
```

That starts worker **8766** + UI **5174** (hidden windows). Browser: `http://127.0.0.1:5174`.

**IMAGE F (capture):** VS Code Welcome / Clone Repository, URL `https://github.com/RiFtNaWx/PythonAutomation.git`, then the branch picker showing `eugene-console` (or the clone command in the terminal).
**IMAGE G (capture):** Terminal `python install.py` ending in INSTALLATION COMPLETED.
**IMAGE H (capture):** Cursor/VS Code folder opened on `PythonAutomation` with `ate\` visible in the explorer (not only `main.py`).

`env.local` stays in `Github_Auto/` for **push**. It is not how ATE talks to instruments. Never paste API keys or `ghp_` tokens into OneNote, chat, or a tutorial. If a key leaked, ask Eugene for a new `env.local` and rotate the GitHub token.

Daily git on a clone PC: opening the folder or `run_ate_app.bat` runs `python -m ate.core.sync_repo` (fetch + `git pull --ff-only` if the tree is clean). Dirty tree = fetch only. Never `git reset --hard`.

## Step 4 -- Ports (do not invent others)

| Port | What |
|------|------|
| **8766** | ATE worker |
| **5174** | Operator UI |
| 8765 | clipdrop -- leave it |
| 3000 / 3001 / 5000 | Founder reserved -- leave them |

## Page 1 check

- Browser shows **Operator console**, family rail on the left (OpAmp / Logic / Analog SW / Level / Power).
- Top-right **Operator** dropdown has names (Eugene, Ariff, ...). **All** and **Kevin** cannot START.
- Setup hint mentions Discover / Open Session / DEMO.

**IMAGE 01 (in repo):** `docs/tutorial/images/01-setup-campaign-session.png` -- Setup: campaign boxes, Discover / Open Session / Open SIM, START + DEMO (SIM), DUT 1 ticked.

---

=== PAGE 2 ===

# Run a campaign (use the software)

Mental model (do not invent a fourth axis):

| Word | What it is | What it is not |
|------|------------|----------------|
| Family | Left rail: OpAmp / Logic / Analog SW / Level / Power | A person |
| Operator | Person folder (`Eugene`, `Ariff`, ...) | A login server |
| Campaign | One Version tree: workbook + sessions | A website SKU dump |

Same part, two people:

```
#Test_Database/Logic/RS1G08/SC70-5/Ariff/Version_1
#Test_Database/Logic/RS1G08/SC70-5/ChangThong/Version_1
```

Do not overwrite someone else's Version folder. Do not add a `Users` or `Tags` folder under `#Test_Database`.

## Step 1 -- Pick you, then Apply

1. Top-right Operator = **you** (not All, not Kevin).
2. Left rail = the product class (example: **Logic**).
3. Component / Part / Package / Operator folder / Version (example: Logic / **RS1G07** / **SC70-5** / Eugene / Version_1).
4. Click **Apply campaign**. That loads or creates `#Test_Database/{Component}/{Part}/{Package}/{You}/Version_N`.

**IMAGE 01 again:** same Setup shot. Circle: Operator dropdown, family rail, five campaign boxes, **Apply campaign**.

Breadcrumb under the title must match the tree (example: `Logic / RS1G07 / SC70-5 / Eugene / Version_1`).

First-run popup may ask "Who are you?" -- pick your name. Kevin is observer only.

## Step 2 -- DUT, channel, one test

- DUT checkboxes: leave **1** ticked for a first run (4 DUTs = 4 board-change Continues).
- Channel **A** on. Tick **B** only if the test is dual-channel and you will move the probe.
- Test program: tick **one** test on Setup. Do not tick boxes on the **Tests** page to run (those boxes are the Version catalog).
- USB: do not Select-all.

**IMAGE I (capture):** Close-up of DUT 1 + CHA + one test row ticked, START and DEMO (SIM) visible. START is disabled until a session is open.

## Step 3 -- No USB: DEMO (SIM)

Use this when the bench is unplugged, or as a rehearsal.

1. Click **DEMO (SIM)**.
2. The console **checks USB first**. If nothing answers `*IDN?`, it opens fake PyVISA (`SIM::MSO5072` / DP832 / DG811 / DMM), proves a loopback (PSU/AWG drive, DMM/scope receive), then runs the same START path.
3. Continue is automatic. Sleeps are skipped. Values may be typ / 0 / placeholder. The run must still finish.
4. If USB **did** answer `*IDN?`, DEMO **refuses** and tells you to Open Session + START. That is correct.

**IMAGE J (capture):** After DEMO, Run tab timeline with completed steps, then Results.

## Step 4 -- USB live: Discover then Open Session then START

Do this when MSO5072, DP832, DG8xx, and DMM are powered and USB-connected. Close Ultra Sigma / other VISA apps first.

Morning check in a terminal (git clone):

```
python -m ate.core.check_visa
```

You want `KEEP USB0::...` and `preflight mode=usb`. Only `SKIP ASRL` means COM ports only -- not ready.

On the console:

1. **Discover**. Instrument tiles (MSO PSU AWG DMM) turn green. If a popup says **No USB instruments**, stop: cables, power, Ultra Sigma, Discover again.
2. **Open Session** (not DEMO). Hint must show a VISA backend, **not** `SIM session`. PSU output is still OFF until START.
3. Tick one test. Photogenic: Logic `supply_current`, or OpAmp **slew**. Eugene `cin` / `cpd` need DMM current.
4. **START**. Click **Continue** at each gate (board / DUT). Sleeps are real. PSU will power the socket. Do not walk away on Select-all.
5. Results: Status / Total / Pass / Fail.

**IMAGE K (capture):** Session hint `Session open (IVIVisaLibrary:default): MSO, PSU, AWG, DMM` and green tiles.
**IMAGE L (capture):** Continue / operator gate dock (title + Continue button).
**IMAGE M (capture):** Empty Discover alert: "No USB instruments. Close Ultra Sigma..."

Never assume the PSU is ON just because USB enumerated. Open Session is identity (`*IDN?`). START is when output turns on.

## Step 5 -- Reports (the artifact)

**IMAGE 02 (in repo):** `docs/tutorial/images/02-results-sts.png` -- Last results table + **Export STS datalog** / **Fill Excel numbers** / **Fetch limits**.

| File (under this Version `sessions/`) | What to say |
|---------------------------------------|-------------|
| `datalog.pdf` (also `.md` / `.html`) | STS sheet: Parameter / Min / Max / Typ / Value / Result |
| `report.json` | Living latest. Merge. Does not wipe tests you did not run this START |
| `{test}/DUT_1/records/*.json` | Per-test history |
| `run_log.txt` | Step dump |

- **Export STS datalog** writes those STS files.
- **Fill Excel numbers** on USB writes the **live** lab xlsx (and can paste photos). Say that out loud before you click.
- DEMO / Open SIM fills `workbook/*_demo.xlsx` and does **not** overwrite the live xlsx or paste photos.

**IMAGE N (capture):** Explorer of `...\Eugene\Version_1\sessions\` with `datalog.pdf` and `report.json`.
**IMAGE O (capture):** First page of `datalog.pdf` STS table.

**Open DB folder** / **Open sessions** / **Open central DB** on Setup jump to those paths.

## Step 6 -- Tests page (catalog, not START)

Setup **Add / edit tests** opens the Tests tab. Tick tests to **show** them on Setup for **this Version only**. Save this Version. Wrap golden `test_*` here (same family). Copy from another person is parked.

**IMAGE 03 (in repo):** `docs/tutorial/images/03-tests-customize.png`.

## Step 7 -- After worker-loaded code

Someone changed `ate/core/runner.py`, `ate/tests/**`, or the worker: idle `restart_ate_worker.bat` (not mid-run). UI-only (`app.js`): **Ctrl+F5**. `owners.yaml` / part yaml: Ctrl+F5 is usually enough.

## Team rules (console)

| Rule | Why |
|------|-----|
| You, not All | All / Kevin cannot Create folders / DEMO / START |
| Apply before START | Campaign path must exist |
| One test + DUT 1 on first USB | Continue gates and PSU-on-socket |
| DEMO vs Open Session | DEMO = fake SCPI. USB *IDN = live START |
| Do not fill someone else's xlsx as PASS | DEMO uses `*_demo.xlsx` |
| Do not delete Version folders | Chip x on the run ledger deletes one JSON only |

## Troubleshooting (console)

| Problem | Fix |
|---------|-----|
| Worker offline | `run_ate_app.bat` or `restart_ate_worker.bat`. Port 8766 |
| UI looks old | Ctrl+F5. Cache is `app.js?v=...` |
| Discover `{}` | Close Ultra Sigma, USB+power, Discover again. Or DEMO if no bench |
| START disabled | Open Session or Open SIM first |
| DEMO says use Open Session | USB answered *IDN. That is the live path |
| Building plan stuck | Do not re-import `get_context` in `run_sequence`. Restart idle worker |
| Excel did not change on DEMO | Look for `*_demo.xlsx`, not the live lab book |
| Wrong part (RS622 on RS1G07) | Apply campaign again. Part comes from the campaign, not a leftover box |
| `venv not found` | `python install.py` from the repo root |

## Quick card -- every lab day

1. Operator = you. Family rail. Apply campaign.
2. No USB: DEMO (SIM). USB: Discover -> Open Session -> one test -> START -> Continue.
3. Results: STS PDF. USB Fill Excel only if you mean to write the live book.
4. End of day: Github_Auto **push** (other OneNote). Console files in `ate/` go through that PR.

---

=== PAGE 3 ===

# Improve the ATE console (vibe-code)

Read **AGENTS.md** (where to edit) then **docs/VIBE_CODE.md** (how to edit, check, debug, add a test). That pair is the law. Shortest wrong fix still breaks everyone.

Open Cursor on the **clone** (`eugene-console`), not on the operator zip.

## Step 1 -- Same 5 steps every time

1. Stop at the first AGENTS.md "Where to change" row.
2. Edit only those files.
3. Run the matching check.
4. Worker-loaded: idle `restart_ate_worker.bat`. UI: **Ctrl+F5**.
5. Click DEMO or START once. A green check is not a demo.

Blast radius (edit only with a reason): `ate/core/database.py`, `runner.py`, `registry.py`, `ate/worker/server.py`, `ate/ui/web/*`.

**IMAGE P (capture):** Cursor split: AGENTS.md table left, `docs/VIBE_CODE.md` Path B right.

## Step 2 -- What you may touch (stop at the first row)

| I want to... | Touch | Do not touch |
|--------------|-------|--------------|
| Add a **person** | Setup Save person, or `owners.yaml` | `database.py` path; Users table |
| Add a **Version** | Type Version_N, Apply | Cloning another person's xlsx |
| Enable tests on **this Version** | Tests page Save (Path A) | Shared parts yaml unless every operator |
| New **measurement** | Path B TestSpec + `__init__.py` + measurements | `main.py`, `runner.py`, `input()` |
| Wrap golden `test_*` | Path C Remember + enable (pointer) | Rewriting the golden or `imported_*.py` |
| Datasheet min/max | `ate/config/limits/<key>.yaml` | Catalog scrape |
| Excel cell | campaign `sheet_map.yaml` | Hardcoded A91 |
| UI | `ate/ui/web/` + bump `?v=` | Second nav / new CSS framework |

## Step 3 -- Add a person (console)

1. Operator folder box: type `Jane`. **Save person** or Apply.
2. Pick Jane (not All). Create folders / Apply.
3. Forget person drops yaml only. Folders stay.

**IMAGE Q (capture):** Save person + new name in Operator dropdown.

## Step 4 -- Paste this into Cursor

Full blocks: `docs/PROMPT_GUIDE.md`. Prefix every chat with the VIBE_CODE debug block. Add-test Path A/B/C are separate pastes -- do not mix.

**IMAGE S (capture):** Cursor chat with the Path B prompt and VIBE_CODE.md open.

## Step 5 -- Prove then debug

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_demo_families
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
```

Fail: `sessions/run_log.txt`, `report.json`, worker window, F12. Table: VIBE_CODE.md section 5.

## Step 6 -- Share (Github_Auto OneNote)

Author trees: [goldens/TUTORIAL.md](../../goldens/TUTORIAL.md). Import: `UPDATE_GOLDENS.bat`. Then `.\push` or green button. Safety gateway AST-checks first; mixed `goldens/` + `runner.py` in the same dirty tree is blocked. Title `feat:` / `fix:` / `config:`. Never commit `env.local` or `cloud_db.txt`.

## Page 3 do-not list

- Tags or Users folder axis
- Hardcoded photo cells
- A13 / A14
- `input()` in `TestSpec.run`
- Treating Path A Save as a new TestSpec, or Path C as a rewrite of the golden

---

=== PAGE 4 ===

# Add or customize a test (three paths)

Do not mix. Full page: repo `docs/VIBE_CODE.md`.

| Path | You do | Done when |
|------|--------|-----------|
| **A Customize** | Tests page tick existing ids, **Save this Version** | Setup shows that id on **this** operator Version |
| **B Realize** | New Python TestSpec + yaml + limits | DEMO writes `measurements` `{id,value,unit}` |
| **C Remember + trigger** | Tests **Remember + enable** -- pointer only, does not rewrite the golden | START runs the original `def test_*` |

## Path A -- this Version only

**IMAGE 03 (in repo):** `docs/tutorial/images/03-tests-customize.png`.

1. Apply campaign.
2. Setup **Add / edit tests**.
3. Tick ids that already exist in this category.
4. **Save this Version** -> `_manifest/test_catalog.yaml`.
5. That list **wins** over `ate/config/parts/<key>.yaml`. A short catalog hides `cin` even if part yaml lists it.

Save does not create a TestSpec. Copy between people is parked.

## Path B -- realize (Python)

Worked example: `cin` / `cpd`.

**IMAGE R (capture):** `eugene_cap.py` `register(TestSpec(id="cin"` + `rs1g07.yaml` `enabled_tests` + limits `CIN_pF`.

1. File `ate/tests/logic/eugene_cap.py` (or `ate/tests/<family>/<id>.py`).
2. Import in `ate/tests/<family>/__init__.py`.
3. `register(TestSpec)` with `run()` using `power_on_protected` + `pause_hook`. Never `input()`.
4. Return `measurements: [{id, value, unit}]`.
5. Add id to part yaml `enabled_tests` (shared recipe).
6. Limits `specs[].id` must match measurement id.
7. Idle `restart_ate_worker.bat`. Ctrl+F5.
8. DEMO that id. Open `sessions/report.json`.

Do not edit `runner.py`. Check: `python -m ate.core.check_add_test`.

## Path C -- remember, do not rewrite

Author recipe: [goldens/TUTORIAL.md](../../goldens/TUTORIAL.md).

1. Tests page **Refresh scan**.
2. **Remember + enable on this Version**. Stores `file:line` in `snippet_map.yaml`. Does **not** write `imported_<id>.py`.
3. Change params/limits in the original golden. Keep `time.sleep`.
4. Leftover A16: `ate/tests/logic/imported_input_off_leakage.py` may still say fill body. Do not copy that.

`input()` / `Lim.*` rows stay blocked on START. Run those via that tree's `python main.py`, or Path B with `pause_hook`.

## Page 4 check

- You can name which path you just used.
- Path A did not add a `.py` file.
- Path B DEMO shows a measurement id in STS PDF.
- Path C Remember is a pointer, not a new `imported_*.py`.


---

# IMAGE SHOT LIST (capture remaining)

Already in `docs/tutorial/images/`:

| File | Use on |
|------|--------|
| `01-setup-campaign-session.png` | Page 1 check + Page 2 Step 1 |
| `02-results-sts.png` | Page 2 Step 5 |
| `03-tests-customize.png` | Page 2 Step 6 |

Still capture (Win+Shift+S, paste into OneNote next to the step):

| ID | Exact frame | Must show |
|----|-------------|-----------|
| A | github.com signup / your profile | Username Eugene will see on the PR |
| B | Explorer `#Test_Database` | OpAmp / Logic folders or empty root |
| C | `ate/config/cloud_db.txt` | One local path, not https |
| D | Unzip + `START.bat` | Zip operators only |
| E | Boot splash then Setup | "Operator console" |
| F | `git clone -b eugene-console` | Branch name visible |
| G | `python install.py` success | INSTALLATION COMPLETED |
| H | Cursor explorer `ate\` | Not only `main.py` |
| I | DUT 1 + one test + START/DEMO | START disabled until session |
| J | Run timeline after DEMO | Completed steps |
| K | Open Session live hint | VISA backend, tiles green, not SIM |
| L | Continue gate | Continue button |
| M | Discover empty alert | "No USB instruments" |
| N | `sessions\` folder | `datalog.pdf`, `report.json` |
| O | `datalog.pdf` first page | Min Max Typ Value Result |
| P | AGENTS.md + eugene_cap.py | Where-to-change + TestSpec |
| Q | Save person | New name in Operator dropdown |
| R | parts yaml `enabled_tests` | cin / cpd listed |
| T | Path A vs Path B vs Path C | Tests page Save vs eugene_cap.py vs imported_input_off_leakage.py |

OneNote layout: screenshot left (~40% width), bullets right. Number the picture with the Step heading so search works.
