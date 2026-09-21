---
keywords: photo-boxes, merged-cell, discover, sample-size, trial-band, a70, campaign-outline, golden-layout
main_idea: Photo paste cells are the top-left of live 4-col x 10-row merges, not hardcoded A70/A45. Row follows intro wrap; DUT count and trial bands grow the grid. Do not re-run golden insert on the filled RS622 TTSOP book.
---

# 2026-09-11 Adaptive photo boxes

PREFLIGHT: PARTIAL. Reuse: sharepoint-rs622-photos, campaign-outline, a07-photo-layout. Spawn: skip.

Filled Eugene TTSOP xlsx is not an 8-box A70 grid. Slew is four stacked 4x10 bands (POS 1VPP / 2VPP / NEG 1VPP / 2VPP) starting A42 after conclusion. VOS is one DUT CHA/CHB pair at A39. YAML that copied A70 + DUT2-4 was inventing cells.

`discover_photo_anchors` reads those merges. `apply_photo_bands` places the same size only when no boxes exist (`write=True`). `campaign_outline.attach_known_photos` writes discovered keys into `paste.photos`. `_PHOTO_TTSOP` is gone.

Check: `python -m ate.reporting.check_photo_layout` and `python -m ate.core.check_campaign_outline`.
