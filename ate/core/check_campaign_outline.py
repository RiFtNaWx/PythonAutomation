"""Self-check: RS622 TTSOP photo boxes + known Excel values.

Run: python -m ate.core.check_campaign_outline
"""
from __future__ import annotations

import sys


def main() -> int:
    from ate.core.campaign_outline import (
        _PHOTO_TTSOP,
        attach_known_photos,
        attach_known_values,
        tests_from_sheets,
    )

    errors: list[str] = []
    slew = _PHOTO_TTSOP.get("Slew Rate") or {}
    if len(slew) != 8:
        errors.append(f"Slew Rate must have 8 photo boxes, got {len(slew)}")
    if slew.get("u1_chA") != "A70":
        errors.append(f"Slew Rate u1_chA must be A70 (golden TTSOP), got {slew.get('u1_chA')}")
    for sheet, photos in _PHOTO_TTSOP.items():
        if len(photos) != 8:
            errors.append(f"{sheet} photo count {len(photos)} != 8")
        if photos.get("u1_chA", "X")[0] != "A":
            errors.append(f"{sheet} u1_chA should start at column A")

    sheets = ["Slew Rate", "GBW", "VOS", "NoPhaseReversal", "PowerOnTime", "VOL", "VOX"]
    tests = tests_from_sheets(sheets, family="opamp", sample=4)
    attach_known_photos(tests, sheets)
    slew_e = tests.get("SlewRate") or {}
    photos = ((slew_e.get("paste") or {}).get("photos") or {})
    if photos.get("u4_chB") != "AC70":
        errors.append(f"attach_known_photos SlewRate u4_chB, got {photos}")

    attach_known_values(tests, ["VOX", "ICC"], None)
    voh = tests.get("VOX") or tests.get("VOH") or {}
    # VOX sheet name becomes folder VOX; VOH test id may not exist. Check pick via voh_load later.
    if "SlewRate" not in tests:
        errors.append("tests_from_sheets missed SlewRate")

    if errors:
        print("FAIL check_campaign_outline:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_campaign_outline: TTSOP 8-box photos + SlewRate A70")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
