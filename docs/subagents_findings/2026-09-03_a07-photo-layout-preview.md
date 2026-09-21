---
keywords: a07-t01, photo-layout, sheet_map, paste.photos, waveform-layout, results-preview, overlay
main_idea: A07 makes campaign sheet_map.yaml paste.photos the only photo-box SoT; Results reconstructs that DUT grid from Test_Database graphs/screenshots and compares latest vs previous. lab_report no longer hardcodes A91 maps.
---

# 2026-09-03 A07 photo-layout preview (implemented; R-0003 not self-closed)

## What shipped

- `ate/reporting/photo_layout.py` -- lookup, preview, surgical YAML save, `/shot` path guard
- `lab_report.place_*` reads `photo_anchor()` only (banned `_SSSR_PHOTO_ANCHORS` / `_LSSR_*` / `_SETTLING_UNIT_COLS`)
- Worker `layout_preview` / `save_photo_layout`; GET `/shot` campaign-root `screenshots`/`graphs` only (traversal = 403)
- Results -> Waveform layout on :5174

## Checks (this turn)

```
python -m ate.reporting.check_photo_layout   # OK
python -m ate.core.check_family_load         # OK opamp=17 logic=7
python -m ate.core.check_lab_report_sync     # OK
worker ping version 0.2.5
GET /shot?rel=../secret.png -> 403
```

## Browser (SettlingTime)

U1 CHA reconstructed from 4 files; click opened Compare latest vs previous (`BAND_0p01` vs `BAND_0p1` JPEGs via `:8766/shot`). Overlay checkbox present. Save not exercised on live yaml (patch unit-tested).

## Out / later

PowerOn / Noise / PSRR still stubs. CSV canvas traces not built. GBW paste caller still later (anchors already in yaml). Independent R-0003 still required.
