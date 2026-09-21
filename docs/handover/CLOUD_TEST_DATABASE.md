# Cloud Database for Test (`#Test_Database`)

**Audience:** Kevin (POC), AE, anyone who will run the software on a laptop.  
**Date:** 2026-09-11  
**One sentence:** `#Test_Database` is a shared OneDrive folder. The program runs on each laptop. START writes into that folder. OneDrive uploads. Nothing runs in the cloud.

---

## 1. What Kevin is taking over

Not a website. Not SQL. Not a login server.

It is this folder, synced to every lab PC:

```
#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/
```

Example -- same part, two people, nobody overwrites the other:

```
#Test_Database/Logic/RS1G08/SC70-5/Ariff/Version_1
#Test_Database/Logic/RS1G08/SC70-5/ChangThong/Version_1
```

Inside each Version folder:

```
_manifest/          sheet_map.yaml (Excel cells), test_catalog.yaml, tags.yaml
workbook/           the live lab xlsx
sessions/           report.json (living latest) + session_*.json (full START) + datalog.md|.html|.pdf
{TestKey}/DUT_n/    screenshots, graphs, records/*.json
```

**Operator** = person folder (Eugene, Ariff, ...).  
**Family / Component** = product class (OpAmp, Logic, AnalogSwitch, Level, Power).  
**All** (top-right of the UI) = view only. It cannot Create folders / DEMO / START.

Do not add a `Tags` or `Users` folder under `#Test_Database`. Tags live in `_manifest/tags.yaml` + campaign `TAGS.txt`.

---

## 2. Two layers (this is the whole architecture)

```
  Laptop A (zip or git)          Laptop B                    SharePoint RD
  ---------------------          --------                    -------------
  Console UI :5174               same app                    #Test_Database
  Worker     :8766     ----write---->  local OneDrive copy  ----sync---->  cloud
  Python code (local)            Python code (local)
```

| Layer | Lives where | Who updates it | How it spreads |
|-------|-------------|----------------|----------------|
| **Software** (console, tests, yaml recipes) | Each laptop: zip `START.bat` **or** `git clone -b eugene-console` | Eugene / vibe-coders via git | Rebuild zip, or `git pull --ff-only` |
| **Results** (xlsx, JSON, photos, STS pdf) | `#Test_Database` | Every operator START / Fill Excel | OneDrive sync. No Graph. No A13 MCP |

Windows **cannot** treat an `https://...sharepoint.com/...` link as a folder. That is why two files exist:

| File | Contents | Used as |
|------|----------|---------|
| `ate/config/sharepoint.url` | one https line | Browser "Open central DB" fallback |
| `ate/config/cloud_db.txt` | one **local** path, e.g. `C:\Users\You\...\Documents\#Test_Database` | Real writes |

Resolve order for the write root:

1. Env `ATE_TEST_DATABASE_ROOT` if that folder exists
2. `ate/config/cloud_db.txt` if that folder exists (Choose folder wins)
3. Auto-discover OneDrive `#Test_Database` shortcuts (any Add-shortcut date / nested Core AE vs AE FAE)
4. `ate/config/bench.yaml` `test_database_root` if it exists
5. Remembered path even if missing -- console still opens; Setup **Choose folder**

Code: `ate/core/paths.py` `load_test_db_root()` / `sharepoint_url()`.  
Path shape (blast radius): `ate/core/database.py` -- **do not "simplify" this file**.

SharePoint library link (saved in repo):

https://jumptechwin.sharepoint.com/sites/RD/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FRD%2FShared%20Documents%2FGeneral%2FHandover%2FJianhong%2F%23Test%5FDatabase&p=true&ga=1

Chrome title: Research & Development / Documents / `#Test_Database`.  
Top folders already there: AnalogSwitch, Level, Logic, OpAmp, Power.

---

## 3. How a person uses it (Kevin can teach this)

### 3.1 App user (AE / Design -- no git)

1. Unzip `ATE_Console_Try_YYYY-MM-DD.zip` (from Desktop/`dist/` or GitHub Release).
2. OneDrive: **Add shortcut to My files** on `#Test_Database` (or on `General` if you already have another RD shortcut like RS-Train -- remove that first, then add one parent shortcut). Do **not** click Sync. Do **not** drag-copy.
3. `START.bat` / `python -m ate.core.sync_cloud_db` writes that OneDrive path into `ate/config/cloud_db.txt`. OneDrive keeps the folder updated. Software updates are git/zip, not this folder. If START cannot see the folder, the console still opens -- Setup **Choose folder**.
4. Double-click `START.bat`.
5. Setup: pick **person** (not All) -> Component / Part / Package / Version -> **Apply campaign**.
6. Discover -> Open Session -> tick tests -> START (or DEMO dry-run).
7. Results land in `.../{TheirName}/Version_N/sessions/` and `workbook/`. OneDrive uploads.

App zip sets `ATE_APP_ONLY=1`. It **refuses** to mkdir a private `#Test_Database` inside the unzip. If the synced folder is missing, `START.bat` still launches. Setup **Choose folder** writes `cloud_db.txt`. `require_cloud_db` prints WARN and exits 0.

### 3.2 Vibe-coder / engineer (git)

```
git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git
```

Read [AGENTS.md](../../AGENTS.md) before editing. Same `cloud_db.txt`. Daily update: `python -m ate.core.sync_repo` (Cursor folder-open and `run_ate_app.bat`). Clean tree = `git pull --ff-only`. Dirty tree = fetch only. **Never** `git reset --hard`.

Do not ship operators a git clone. They get the zip.

### 3.3 First-day PC checklist (under 10 minutes)

1. Open SharePoint `#Test_Database` (Handover / Jianhong). Click **Add shortcut to OneDrive**. Replace if asked.
2. Right-click the folder -> **Always keep on this device**. `START.bat` writes `cloud_db.txt`.
3. Double-click `START.bat` (git clone or zip). Or `run_ate_app.bat` if venv already exists.
4. Setup **Open central DB** -- should open the folder, not a random unzip copy.
5. Pick Eugene (or yourself) -> Apply campaign -> Open DB folder -- confirm you are inside `{Operator}/Version_N`.

---

## 4. What auto-scales when people create more tests

This is the "ability to scale automatically" row on the handover sheet.

| Action in Setup | What appears on disk | Syncs to everyone? |
|-----------------|----------------------|--------------------|
| **Create folders + open** | `{Component}/{Part}/{Package}/{Operator}/Version_1/` + `_manifest` stubs + workbook copy if tracking xlsx exists | Yes, after OneDrive |
| Type a new **Operator** name + **Save person** or Apply | `ate/config/owners.yaml` row (software) **and** that person's Version folder when you Create/Apply | Folder yes. `owners.yaml` is **in the git/zip**, not in `#Test_Database`. Rebuild zip or pull git so other PCs see the new person in the dropdown |
| Type a new **Version_N** + Apply | New Version under **that person only**. Copies `_manifest` stubs if missing. Does **not** clone the xlsx | Yes |
| START / DEMO | `sessions/report.json` merge, `session_*.json`, photos, STS datalog, Excel fill on session end | Yes |
| Wrap / Copy tests | Python under `ate/tests/` + part yaml `enabled_tests` | **Software** -- git/zip, not the cloud folder |
| Import xlsx | Campaign `workbook/` + `sheet_map.yaml` outline | Yes |
| Import family | `ate/tests/<family>/` + `extra_families.yaml` | Software -- git/zip |

**Scale rule:** data (runs, Excel, photos) scale by creating folders in `#Test_Database`. Code (new TestSpec, new family) scales by git, then a new zip.

**Same project, different people** is already the database shape. Do not invent a Users table.

---

## 5. What a START actually writes (living data)

After Open Session + START (or DEMO):

1. **Living latest** `sessions/report.json` -- merge by test_id + DUT (+ channel). A subset START **keeps** tests not run this time. Do not wipe this file across operators.
2. **History** `{TestKey}/DUT_n/records/{test_id}_{timestamp}.json`.
3. **Full START snapshot** `sessions/session_*.json`.
4. **STS** `sessions/datalog.md` + `.html` + column-table `.pdf` (Parameter / Unit / Min / Max / Typ / Value / Result).
5. **Photos** into xlsx cells listed in `sheet_map` `paste.photos` (if mapped).
6. **Numbers** into xlsx cells listed in `paste.values` (session end, or Results **Fill Excel numbers**). Locked xlsx -> `{stem}_filled.xlsx`, session does not crash.

Run ledger (Results tab) lists session JSON from this same tree. Chip `x` deletes one session JSON. It does **not** delete the Version folder.

---

## 6. Done vs not done (cloud row)

### Done

- Folder contract + operator person path.
- Setup Open central DB (folder if present, else https; never mkdir a private DB) + **Choose folder** picker.
- App zip refuses private unzip DB. Missing folder does **not** block START.
- Living JSON merge (A18), tags, run ledger.
- OneDrive is the only upload.
- `check_cloud_db` + `require_cloud_db` (WARN, exit 0).
- Pack zip: `PACK.bat` + `.github/workflows/pack-console.yml`.

### Not done / do not promise

| Item | Status | Who continues |
|------|--------|----------------|
| Auto-create `owners.yaml` on every laptop without a zip rebuild | Not automatic. Person yaml is software | Eugene: rebuild zip after Save person, or tell people to git pull |
| Graph API / OneDrive MCP merge-center (A13) | **Parked** | Do not unpark |
| Conflict UI when two people edit the same xlsx at once | OneDrive last-writer-wins. Mitigation = **one person per operator folder** | Kevin: teach "do not share one Version folder" |
| Website catalog scrape into `#Test_Database` | Forbidden | Never |
| SQL / Users / Tags path axis | Forbidden | Never |
| Cloud running the Python worker | No. Worker is always local (VISA USB to the bench) | Kevin: "cloud holds files, bench holds instruments" |

### Fundamental structure still to tighten (Kevin + Eugene, later)

1. Document the SharePoint permission group (RD) so new AE get sync, not a forwarded zip of data.
2. After each `owners.yaml` / `inventory.yaml` change, pack a new zip the same day.
3. Optional: a one-page "if OneDrive says conflict, keep the operator folder owner" note. No new software.

---

## 7. How to continue development (Kevin + agents)

Read order:

1. This file.
2. [AGENTS.md](../../AGENTS.md) -- where to change, blast radius.
3. [docs/ATE_PLUGIN.md](../ATE_PLUGIN.md) -- campaign slots.
4. [docs/PROMPT_GUIDE.md](../PROMPT_GUIDE.md) -- paste-one-block prompts.
5. [AGENT_PROMPTS.md](AGENT_PROMPTS.md) -- copy-paste for Cursor.

**Customization that is allowed without Python:**

- Add a person: Setup Operator folder -> Save person.
- Add a Version: type Version_N -> Apply.
- Add a SKU we are testing: one `inventory.yaml` row + Create folders. Do not scrape RUN-IC homepage.
- Tags: Tags tab.
- Photo / number cells: campaign `_manifest/sheet_map.yaml` (or Results Waveform layout for photos).

**Customization that needs an agent + worker restart:**

- New `TestSpec` in `ate/tests/<family>/`.
- New family: Setup Import family or `extra_families.yaml`. Never ingest into `opamp`/`logic`/`level`.
- Limits: `ate/config/limits/<part>.yaml`.

**Never:**

- Edit `ate/core/database.py` path shape "to make it simpler".
- Point the zip at a private `#Test_Database` inside the unzip.
- Unpark A13.
- Call `input()` in a test (blocks the worker).

Proof:

```
python -m ate.core.check_cloud_db
python -m ate.core.check_operator_tree
python -m ate.core.check_new_product
python pack_ate_console.py --check
```

---

## 8. What to say (Kevin, under 1 minute)

Say it like this. Stop. Don't add extra terms.

"It's just a shared folder on OneDrive. Name is `#Test_Database`.

The program is on your laptop. The scope stays on the desk.

You press START, files go under your name. OneDrive uploads them.

Two people, two folders. Don't share one Version.

New person: Apply, folder appears. New test code still needs a software update.

Work Report is a different Excel. Don't drop it in this folder."
