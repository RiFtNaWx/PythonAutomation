"""Photo-grid SoT check (A07-T01).

Run: python -m ate.reporting.check_photo_layout
"""
from __future__ import annotations

import sys
from pathlib import Path

from ate.reporting import lab_report, photo_layout


_BANNED = (
    "_SSSR_PHOTO_ANCHORS",
    "_LSSR_PHOTO_ANCHORS",
    "_SETTLING_UNIT_COLS",
    "_SETTLING_BODY_ROW",
)


def _sample_yaml() -> str:
    return (
        "tests:\n"
        "  Foo:\n"
        "    paste:\n"
        "      photos:\n"
        "        u1_chA: A1  # keep comment\n"
        "        u1_chB: E1\n"
        "  Bar:\n"
        "    paste:\n"
        "      photos:\n"
        "        u1_chA: B1\n"
    )


def check_photo_layout() -> list[str]:
    errors: list[str] = []
    src = Path(lab_report.__file__).read_text(encoding="utf-8")
    for name in _BANNED:
        if name in src:
            errors.append(f"lab_report.py still hardcodes {name}")

    parsed = photo_layout.parse_photo_key("u2_chB")
    if not parsed or parsed["key"] != "u2_chB" or parsed["unit"] != 2:
        errors.append("parse_photo_key u2_chB failed")
    ort = photo_layout.parse_photo_key("pos_u1_chA")
    if not ort or ort["key"] != "pos_u1_chA" or ort["polarity"] != "POS":
        errors.append("parse_photo_key pos_u1_chA failed")

    patched = photo_layout.patch_photos_yaml(
        _sample_yaml(), "Foo", {"u1_chA": "z9"}
    )
    if "u1_chA: Z9" not in patched:
        errors.append("YAML patch did not update Foo u1_chA")
    if "# keep comment" not in patched:
        errors.append("YAML patch dropped comment")
    if "u1_chA: B1" not in patched:
        errors.append("YAML patch mutated Bar")

    try:
        photo_layout.patch_photos_yaml(_sample_yaml(), "Foo", {"u1_chA": "not_a_cell"})
        errors.append("invalid cell was accepted")
    except ValueError:
        pass

    try:
        photo_layout.resolve_shot_file("../secret.png")
        errors.append("path traversal accepted")
    except (PermissionError, FileNotFoundError):
        pass

    try:
        tests = photo_layout.list_photo_tests()
    except Exception as exc:
        errors.append(f"list_photo_tests: {exc}")
        return errors
    if tests:
        key = tests[0]["test_key"]
        try:
            grid = photo_layout.photos_map(key)
        except Exception as exc:
            errors.append(f"photos_map({key}): {exc}")
            return errors
        if not grid:
            errors.append(f"{key} paste.photos empty after parse")
        else:
            first = next(iter(grid))
            parsed_first = photo_layout.parse_photo_key(first)
            if parsed_first:
                got = photo_layout.photo_anchor(
                    key,
                    parsed_first["unit"],
                    parsed_first["channel"],
                    parsed_first["polarity"],
                )
                if got != grid[first]:
                    errors.append(f"photo_anchor drift {key} {first}: {got} vs {grid[first]}")
    return errors


def main() -> int:
    errors = check_photo_layout()
    if errors:
        print("FAIL photo-layout:")
        for line in errors:
            print(f"  - {line}")
        return 1
    print("OK photo-layout: sheet_map SoT, no hardcoded paste maps, YAML patch keeps comments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
