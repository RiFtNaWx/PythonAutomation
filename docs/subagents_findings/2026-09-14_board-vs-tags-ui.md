---
keywords: board, campaign-board, one-board, central-_ate, tags-chips, TAGS.txt, family-scoped
main_idea: Board is a single fixture pick per campaign, vocab same product class only, saved to #Test_Database/_ate. Free tags stay bubbles (+N more) for File Explorer. Kind+Value board pile removed.
---

# 2026-09-14 Board vs free tags UI

PREFLIGHT: PARTIAL
reuse: combo-tags-excel, type-rail-labels, a17-tags, codeless-owner-tags
spawn: skip

## Change

- Setup `#campaign-board` = one PCB per campaign
- Save collapses multiple boards to last one; remembers into `#Test_Database/_ate/boards.yaml` by family
- `list_boards` = config + central + same-class scan only (no OpAmp G11 on Power/Logic)
- Free tags: `#db-tag-input` + chips `+N more` -> TAGS.txt
- Clear tags keeps board
- Removed Kind+Value board pile from Setup

## Checks

`python -m ate.core.check_ui_contract`
`python -m ate.core.check_tags_datalog`

## Operator

Ctrl+F5 console. Pick Board under Setup More. Type other tags with Space.
