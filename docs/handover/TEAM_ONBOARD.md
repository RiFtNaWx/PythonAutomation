# New team onboard -- build, use, test, keep shipping

**Date:** 2026-09-21  
**Audience:** the team taking over after JH.  
**Live product:** `ate/` + worker **8766** + UI **5174**. There is no second stack.

Print this. Then [AGENTS.md](../../AGENTS.md). Logic DC bench leftovers stay in [HANDOVER.md](../../HANDOVER.md).

---

## 0. Two products (do not mix)

| Who | What they get | Database |
|-----|---------------|----------|
| Operator / AE | Zip from `PACK.bat` or GitHub Actions `ATE_Console_Try_YYYY-MM-DD.zip` | Same OneDrive `#Test_Database` |
| Engineer | `git clone -b eugene-console` then `START.bat` | Same folder. Never a private unzip copy |

Results are files. OneDrive uploads them. No Graph. No A13. No SQL.

---

## 1. Use (operator, under 10 minutes)

1. Unzip so `START.bat` is at the top.
2. OneDrive: **Add shortcut to My files** on SharePoint `#Test_Database` (link in `ate/config/sharepoint.url`). Do not click Sync. Do not drag-copy.
3. Double-click `START.bat`. First run 2 to 5 minutes. Browser: `http://127.0.0.1:5174`. Stale UI: Ctrl+F5.
4. If the folder is not on this PC yet, **the console still opens**. Setup -> **Choose folder** -> pick the OneDrive `#Test_Database` (or a local save folder if you are not synced). That writes `ate/config/cloud_db.txt`.
5. Pick a person (not All) -> Apply campaign -> Discover -> Open Session -> START (or DEMO with no USB).

Shortcut path is allowed to differ per PC. Same SharePoint folder:

```
...\OneDrive - JumpWin Tech\Research & Development - #Test_Database
...\OneDrive - JumpWin Tech\Research & Development-AE FAE - Core AE\#Test_Database
...\OneDrive - JumpWin Tech\Research & Development-AE FAE - AE FAE\Core AE\#Test_Database
```

START auto-finds those. If it cannot, Choose folder. Software never stays disabled.

Tree:

```
#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/
```

---

## 2. Build a downloadable zip (engineer, ~2 minutes)

Local:

```
PACK.bat
```

or `venv\Scripts\python.exe pack_ate_console.py`. Zip lands on Desktop and `dist/`.

Pipeline (already in repo): `.github/workflows/pack-console.yml`

- Push to `eugene-console` (ate/ or START/pack files) -> Actions artifact `ATE_Console_Try`
- Tag `console-YYYY-MM-DD` or `v*` -> GitHub Release with the zip
- Manual: Actions -> pack-console -> Run workflow

Check without writing a zip: `python pack_ate_console.py --check`

Do not ship a git clone to operators. Do not put `cloud_db.txt` in the zip.

---

## 3. Test before you say it works

Run the layer you touched. A green check that never could fail is not a check.

Must for this handover slice:

```
python -m ate.core.check_cloud_db
python -m ate.core.check_launch
python -m ate.core.check_ui_contract
python pack_ate_console.py --check
```

After a Path B test: `python -m ate.core.check_add_test` then DEMO that id.  
After Logic DC yaml: `python -m ate.core.check_logic_dc`.  
Full list: [AGENTS.md](../../AGENTS.md) Checks.

Idle-restart worker after `ate/tests/**`, `ate/worker/**`, `runner.py`: `restart_ate_worker.bat` (not mid-run). UI-only: Ctrl+F5.

Proof is DEMO/START of the id, not only a green check.

---

## 4. Continue development (stop at the first AGENTS.md row)

| I want to... | Touch | Do not |
|--------------|-------|--------|
| Add a person | Setup Add person | Users table, `database.py` path shape |
| Add a SKU we test | one `inventory.yaml` row | scrape en.run-ic.com |
| New test | Path B `register(TestSpec)` in `ate/tests/<family>/` | `runner.py`, `input()`, `Lim.*` |
| This Version only | Tests page Save catalog | shared parts yaml unless every operator |
| Limits | `ate/config/limits/<key>.yaml` + ingest | guess Excel A91 |
| Cloud folder on a PC | `cloud_db.txt` via START or Choose folder | A13 Graph, private unzip DB |
| Operator UI | `ate/ui/web/*` + `UI_CONTRACT.md` | second nav, fourth webfont |
| Pack zip | `PACK.bat` / workflow | rewrite packer into a second installer |

Prompt shape: `.cursor/skills/ate-prompt/`. How: [docs/VIBE_CODE.md](../VIBE_CODE.md).

Blast radius: `database.py` (folder contract), `runner.py` (every START), `registry.py`, `worker/server.py`, `ate/ui/web/*`.

Never `git reset --hard`. Dirty tree = fetch only (`python -m ate.core.sync_repo`).

---

## 5. Cloud DB contract (do not invent a fourth writer)

Resolve order for the write root:

1. Env `ATE_TEST_DATABASE_ROOT` if that folder exists
2. `ate/config/cloud_db.txt` if that folder exists (explicit Choose folder wins)
3. Auto-discover OneDrive shortcuts (any Add-shortcut date)
4. `bench.yaml` `test_database_root` if it exists
5. Remembered path even if missing -- console still opens

https lives in `ate/config/sharepoint.url` (browser only). Windows cannot use https as a folder.

Parked: A13 OneDrive MCP / Graph.

---

## 6. First week for the new team

1. Clone `eugene-console`. Double-click `START.bat`. Ctrl+F5. DEMO one Logic part.
2. Run the four commands in section 3. They must pass on a clean tree.
3. `PACK.bat`. Unzip on a second folder. Confirm START opens even with a wrong `cloud_db.txt`, then Choose folder.
4. Read [CLOUD_TEST_DATABASE.md](CLOUD_TEST_DATABASE.md) and [SOFTWARE_CONSOLE.md](SOFTWARE_CONSOLE.md).
5. Logic DC leftovers (GT34 VOL board change, CONFIRMED families LIVE): [HANDOVER.md](../../HANDOVER.md).

No Verify PASS is claimed from this page.
