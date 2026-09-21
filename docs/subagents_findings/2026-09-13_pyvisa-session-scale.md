---
keywords: pyvisa, visa-backend, discover-cache, open-session, asrl, list_tree-cache, sim
main_idea: Live Open Session scanned USB twice (empty {} mapping triggered a third). One shared PyVISA RM with NI/@ivi/@py fallback, 15s Discover cache, skip ASRL/RAW, list_tree 8s cache. SIM still has no RM.
---

# 2026-09-13 PyVISA session + scale

## Cause

`find_instruments()` built its own `ResourceManager()`, then `Instruments()` built another. `open_session` always re-scanned, and `Instruments(self._mapping or None)` treated `{}` as missing so it scanned again. COM `ASRL` ports were skipped, but USB `::RAW` still got `*IDN?`. `list_tree()` walked the whole `#Test_Database` on every Apply/load.

## Shipped

- `visa_resource_manager()` tries default, `@ivi`, then `@py`. Clear error if none. Backend name on `session_status.visa_backend`.
- Discover `force=True`. Open Session reuses a 15s cache and passes mapping through (empty dict is not a rescan).
- Skip ASRL and USB RAW. IDN probe timeout 2000ms. Close handles in `finally`.
- `list_tree` caches the default root 8s; `ensure_tree` / `ensure_version` / `ensure_product` call `invalidate_tree_cache()`.
- `python -m ate.core.check_visa` (fake ASRL skip + live `list_resources`).

## Does not prove

- A specific MSO/PSU is plugged in. This PC's NI-VISA listed only `ASRL3`/`ASRL4` (skipped). Discover `{}` is correct until USB instruments enumerate.
- Slew VISA poison retry (`check_slew_capture_run`).
- Full Logic START through Continue gates.

## Extra

`applyTestDefaults` had an extra `}` (cache `visa1` would not boot). `check_ui_contract` now runs `node --check` on `app.js`.
