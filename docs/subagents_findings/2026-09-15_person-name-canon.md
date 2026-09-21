---
keywords: seelim, seelim, lim, ariff, eugene, changtong, changthong, soo, chuntak, chun-tak, canonical, alias_of
main_idea: Display names are SeeLim, Ariff, Eugene, ChangTong, Soo, Chun Tak. Lim is an alias of seelim. Disk folders stay ChangThong / SeeLim. Soo is a different person.
---

PREFLIGHT: HIT
reuse: 2026-09-15_progress-stalker-pickup.md, 2026-09-14_chun-tak-rs1gt34-golden.md
spawn: skip

# 2026-09-15 person name canon

## Map (display, not a Users table)

| Typed / yaml / PIC | Board + picker | Disk folder |
|--------------------|----------------|-------------|
| lim, seelim, SeeLim | SeeLim | SeeLim (lim row is `alias_of: seelim`) |
| ariff | Ariff | Ariff |
| eugene | Eugene | Eugene |
| changthong / changtong | ChangTong | ChangThong (label unchanged) |
| soo | Soo | Soo (not merged with ChangTong) |
| chuntak / Chun Tak | Chun Tak | Chun Tak; tracking PIC on RS1GT34 |

## Shipped

- `canonical_person_label` in `database.py` (hard map first).
- Progress board groups by canon. Presence fold matches heartbeat ids.
- Picker hides `alias_of` (Lim). Saved `lim` remaps to `seelim`.
- RS2227 PIC `seelim`. RS1GT34 PIC `chuntak`. Chun Tak `parts: [rs1gt34]` only.

## Not

- Did not rename `ChangThong/` on disk.
- Did not merge Soo into ChangTong.
- Did not add a Users page.
