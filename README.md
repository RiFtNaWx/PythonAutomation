# PythonAutomation (ATE operator console)

Lab characterization on a Rigol bench (MSO, DP832, DG8xx, optional DMM) plus an **operator console** that already knows multiple people, product families, and campaign folders.

If you are about to vibe-code: **read [AGENTS.md](AGENTS.md) then [docs/VIBE_CODE.md](docs/VIBE_CODE.md).** AGENTS.md is which file. VIBE_CODE.md is how to edit, check, debug, and add a test (Path A customize / Path B realize / Path C wrap-then-fill).

## Who gets what

| Who | Start here | Do not |
|-----|------------|--------|
| **Run tests only** | Unzip `ATE_Console_Try_*.zip` (or GitHub Release on `eugene-console`), sync SharePoint `#Test_Database`, `START.bat` | Edit Python, keep a private database in the unzip |
| **Change the product** | `git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git`, [AGENTS.md](AGENTS.md), `run_ate_app.bat` | Ship operators a git clone; they get the zip |

Clone auto-update: opening the folder in Cursor/VS Code, or `run_ate_app.bat`, runs `python -m ate.core.sync_repo` at most once a day. That is `git fetch` + `git pull --ff-only`. Uncommitted files are never replaced. If you have local commits that diverged, it fetches only and leaves your work.

Results always go to the OneDrive-synced `#Test_Database` (path in `ate/config/cloud_db.txt`). There is no second upload API. OneDrive is the upload.

Rebuild the operator zip: `venv\Scripts\python.exe pack_ate_console.py` (Desktop + `dist/`). SharePoint https lives in `ate/config/sharepoint.url`.

## Two stacks (pick the live one)

| Stack | How you run it | When to use it |
|-------|----------------|----------------|
| **Console (live)** | `run_ate_app.bat` -- worker `http://127.0.0.1:8766`, UI `http://127.0.0.1:5174` | New tests, new people, new parts, Excel paste, DEMO, START |
| Legacy `main.py` | `venv\Scripts\python.exe main.py` | Old one-shot scripts. Not a plugin. The console will not see a `test_*` until it is wrapped into `ate/tests/<family>/` |

Team git / `push` / `env.local`: [WORKFLOW.md](WORKFLOW.md). Plug-in slots: [docs/ATE_PLUGIN.md](docs/ATE_PLUGIN.md). UI chrome: [ate/ui/web/UI_CONTRACT.md](ate/ui/web/UI_CONTRACT.md).

## Same product, different operators

The database is a folder tree, not a user login server:

```
#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/
```

Two people on RS1G08 is two operator folders under the same part/package. Workbooks and sessions stay separate. Top-right **All** can look; it cannot Create folders / DEMO / START.

### Add a user (person)

1. Add a row to `ate/config/owners.yaml` (`id`, `label`, defaults, `parts`). `label` becomes the folder name.
2. Ctrl+F5 Setup. Pick that person (not All).
3. Pick a tracking-sheet row (or type part + package) -> **Create folders + open**.

Do not add a Users path segment and do not add a SQL user table. Detail and a yaml snippet: [AGENTS.md](AGENTS.md).

### Add a version

Setup, person selected, type `Version_N` in the Version box, then Apply. That creates `Version_N` under *that* person only. It does not clone the xlsx and does not touch another operator's tree. There is no extra + Version button.

### Add a product we are actually testing

One SKU row in `ate/config/inventory.yaml` (tracking sheet). Then Create folders. Do not scrape en.run-ic.com (RS724-Q1 stays off until we test it).

## Quick start (console)

1. First-time machine: [WORKFLOW.md](WORKFLOW.md) (Python 3.11, clone, `python install.py`).
2. Bench: MSO5000-class, DP832, DG800 family; DMM if the test list needs it. Discover uses `*IDN?` -- no hardcoded USB addresses.
3. From the repo:

```bat
run_ate_app.bat
```

4. UI: pick a **person** (not All), Apply campaign. USB: Discover then Open Session, tick tests, START. No USB: **DEMO (SIM)** -- fake PyVISA, same START path, STS PDF in `sessions/`. Lab walk: [docs/DEMO.md](docs/DEMO.md). OneNote pack: [docs/tutorial/ATE_ONENOTE.md](docs/tutorial/ATE_ONENOTE.md).
5. After worker-loaded code changes: `restart_ate_worker.bat` (not mid-run). After UI-only: Ctrl+F5.

Ports: **8766** worker, **5174** UI. Never 8765 / 3000 / 3001 / 5000.

## Where to change code (short)

Full table: [AGENTS.md](AGENTS.md). Cheat sheet:

| Need | Place |
|------|--------|
| New person | `ate/config/owners.yaml` |
| Tracking SKU | `ate/config/inventory.yaml` |
| Part recipe / enabled tests | `ate/config/parts/<key>.yaml` |
| New measurement | `ate/tests/<family>/` + `register(TestSpec)` + `__init__.py` import + `measurements` ([VIBE_CODE.md](docs/VIBE_CODE.md) Path B) |
| New family | Setup Import family or `extra_families.yaml` |
| Photo cells | campaign `_manifest/sheet_map.yaml` |
| Console UI | `ate/ui/web/` + UI_CONTRACT |
| Campaign path logic | `ate/core/database.py` (high blast radius -- do not "simplify") |

**Do not** add tests by editing `main.py` or `runner.py`. **Do not** call `input()` inside a TestSpec. **Do not** `import Lim.*`.

## Checks

```
python -m ate.core.check_new_product
python -m ate.core.check_operator_tree
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
python -m ate.core.check_add_test
python -m ate.core.check_demo_families
```

Run the check that matches the layer you changed. More commands in AGENTS.md.

## Docs map

| Doc | Use it for |
|-----|------------|
| [docs/handover/2026-09-11_jianhong_checklist.md](docs/handover/2026-09-11_jianhong_checklist.md) | Jian Hong leaving: cloud DB, software/Excel, VoS, agent prompts |
| [STATUS.md](STATUS.md) | Boss / stakeholder: Done, Ongoing, Not complete |
| [docs/tutorial/ATE_TUTORIAL.html](docs/tutorial/ATE_TUTORIAL.html) | Full browser tutorial: every tab, spec, workflow, screenshots |
| [docs/tutorial/ATE_ONENOTE.md](docs/tutorial/ATE_ONENOTE.md) | 4 OneNote pages: get the console, run START/DEMO, vibe-code, add/customize a test |
| [docs/VIBE_CODE.md](docs/VIBE_CODE.md) | Edit / check / debug / add a test (Path A/B/C) |
| [docs/DEMO.md](docs/DEMO.md) | USB START + SIM backup + extra family acts + add-test rehearsal |
| [docs/tickets/INDEX.md](docs/tickets/INDEX.md) | All tickets: closed / leftover / parked |
| [docs/SHIP_NEXT.md](docs/SHIP_NEXT.md) | Printable next waves: leftovers, V07, how to ship |
| [AGENTS.md](AGENTS.md) | Vibe-code / agent: where to edit, add user/version, do-not list |
| [docs/ATE_PLUGIN.md](docs/ATE_PLUGIN.md) | Family ingest, TestSpec slots, Logic/Switch/RS0204 notes |
| [ate/ui/web/UI_CONTRACT.md](ate/ui/web/UI_CONTRACT.md) | Tabs, fonts, `check_ui_contract` |
| [WORKFLOW.md](WORKFLOW.md) | Clone, `push`, env.local |
| [TEST_DESIGN.md](TEST_DESIGN.md) | Legacy `main.py` test anatomy (golden source, not the console) |
| [PYVISA_OPA_DEEP_DIVE.md](PYVISA_OPA_DEEP_DIVE.md) | SCPI / Voffset / sweep pitfalls |
| `readme.txt` | Oldest file map |

## Legacy `main.py` (do not start here)

Instruments still auto-discover via PyVISA. Root layout (`opa_tests.py`, `logic_tests.py`, `limits.py`, ...) is owned per [WORKFLOW.md](WORKFLOW.md). Wrap goldens into `ate/tests/` instead of growing `main.py`.

Questions on campaign folders or the console: use AGENTS.md, then Eugene.
