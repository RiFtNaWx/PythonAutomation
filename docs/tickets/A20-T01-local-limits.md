# A20-T01 -- local datasheet limits

**Epic:** A20
**Status:** implemented 2026-09-11

Local PDFs: `C:\Users\OoiJianHong\Downloads\Reference\Reference`
Index: `ate/config/datasheets.yaml` + `ate/core/lookup.py`
Limits: `ate/config/limits/<part>.yaml` from PDF extract + part yaml tables.
Web fetch only if PDF missing. Check: `python -m ate.core.check_lookup`
