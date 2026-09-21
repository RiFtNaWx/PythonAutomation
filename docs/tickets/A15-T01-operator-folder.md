# A15-T01 - Operator folder path + migrate

**Epic:** EPIC-A15
**Status:** implemented
**Model (implement):** composer-2.5

## Acceptance

WHEN a campaign is applied, THE SYSTEM SHALL use
`#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/`.

WHEN Operator is All, THE SYSTEM SHALL refuse writes (Create folders / DEMO / START / set_db_context).

WHEN `python -m ate.core.migrate_operator_folders --apply` runs, legacy
`Package/Version_*` folders SHALL move to `Package/{Pic}/Version_*` (inventory pic -> owners label; unknown -> `_unassigned`). Dry-run is default.

WHEN session JSON is written, identity SHALL include `operator`.
