---
keywords: level-stub, power-ldo-folders, rs0204, rs3213, seed-classified, track-tests, ate_suite
main_idea: Level/Stub retired. RS0204 lives under Level/ with logic tests. LDO campaigns under Power/ with IQ/VINMIN/LIR/LOR/IOUTMAX/IEN folders. New campaigns never grow OpAmp GBW/ORT.
---

# 2026-09-10 Level/LDO off Stub

PREFLIGHT: PARTIAL. Reuse: f22 migrate, type-rail-labels, qualification-scale-ingest. Spawn: skip.

## Disk

- Moved `#Test_Database/Logic/RS0204` -> `Level/RS0204` (ChangThong tests intact).
- Retired `Level/Stub` -> `Level/_retired_Stub` (OpAmp GBW/ORT placeholder).
- Created `Level/RS0204` UQFN + QFN, `Level/RS0302`, `Power/RS3213`, `Power/RS3235`.

## Code

- `ensure_product` folder = tracking class (Level/Power). `ate_suite` only loads tests (`suite_for_part`).
- `ensure_tree` no longer defaults to ORT/VOS/SlewRate/GBW.
- Sheet map + test folders from `enabled_tests`.
- Seed: `python -m ate.core.seed_classified_campaigns --apply`

RS0302 has no recipe yet (Setup only). RS0204 dual-rail suite stays logic.
