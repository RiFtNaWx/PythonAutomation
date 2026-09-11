---
keywords: try-packet, zip, START.bat, pack_ate_console, downloadable, portable-bench
main_idea: Whole operator console packs to Desktop zip ATE_Console_Try_YYYY-MM-DD.zip. Unzip, START.bat, DEMO. Packet uses local #Test_Database; no kicad/git/venv.
---

# 2026-09-11 Downloadable ATE try packet

PREFLIGHT: PARTIAL. Reuse: ship-next-printable. Spawn: skip.

## How to hand it over

1. `python pack_ate_console.py` (from repo; uses venv python).
2. Zip lands on Desktop and `dist/`.
3. They unzip, double-click `START.bat`, wait 2-5 min first pip, then DEMO.

## What is in / out

In: `ate/`, launch bats, wrap-root py (`opa_tests.py`, `logic_tests.py`, setups), `requirements-console.txt`.
Out: venv, `.git`, `kicad-source-mirror`, `Github_Auto`, `env.local`.

Packet `bench.yaml` points `test_database_root` at folder-local `#Test_Database`. `paths.expand_user_path` allows `%USERPROFILE%` and relative roots.

## Proof

```
python pack_ate_console.py --check
python pack_ate_console.py
```
