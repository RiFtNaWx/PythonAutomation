# A17-T01 - Tags + session datalog JSON API

**Epic:** EPIC-A17
**Status:** implemented
**Model (implement):** composer-2.5

## Goal

Campaign `_manifest/tags.yaml` + root `TAGS.txt`. Board vocab in `ate/config/boards.yaml`. Rolling `sessions/report.json` (STS shape) + `sessions/archive/{session_id}.json`. Worker RPCs. One runnable check. No UI.

## Acceptance

WHEN `save_tags` runs, THE SYSTEM SHALL write `_manifest/tags.yaml` and campaign-root `TAGS.txt` (one token per line).

WHEN `begin_session` / `record_step` / `end_session` run, THE SYSTEM SHALL update `sessions/report.json` and on end SHALL copy an archive snapshot under `sessions/archive/`.

WHEN `python -m ate.core.check_tags_datalog` runs, THE SYSTEM SHALL pass (temp campaign tags + report + archive).

## Out of ticket

- Tags UI page -> A17-T02
- Auto-paste / golden workbook -> A17-T03
