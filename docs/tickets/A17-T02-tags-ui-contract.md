# A17-T02 - Tags page + AGENTS / UI contract

**Epic:** EPIC-A17
**Status:** implemented
**Model (implement):** composer-2.5
**Depends on:** A17-T01 RPCs

## Goal

4th tab Tags; chips beside Model on Setup; Import/filter by tag. Root `AGENTS.md` + `ate/ui/web/UI_CONTRACT.md` + `check_ui_contract`.

## Acceptance

WHEN Setup shows Model, THE SYSTEM SHALL show tag chips beside `#db-model`.

WHEN Tags page saves, THE SYSTEM SHALL call `save_tags` and refresh chips.

WHEN `python -m ate.core.check_ui_contract` runs, THE SYSTEM SHALL fail if a `data-page` lacks `#page-*` or a second `.tabs` nav appears.

## Out of ticket

- Backend tags/datalog -> A17-T01
- Golden paste -> A17-T03
