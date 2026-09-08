"""Fail-closed UI contract for ate/ui/web (A17-T02).

Run: python -m ate.core.check_ui_contract
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "ui" / "web"
INDEX = WEB / "index.html"


def main() -> int:
    errors: list[str] = []
    if not INDEX.is_file():
        print("FAIL check_ui_contract: index.html missing")
        return 1
    html = INDEX.read_text(encoding="utf-8")

    tabs = re.findall(r'data-page="([a-z0-9\-]+)"', html)
    if not tabs:
        errors.append("no data-page tabs found")
    for name in tabs:
        if f'id="page-{name}"' not in html:
            errors.append(f"tab data-page={name!r} missing section#page-{name}")

    nav_count = len(re.findall(r'<nav\s+class="[^"]*\btabs\b', html))
    if nav_count != 1:
        errors.append(f"expected exactly 1 nav.tabs, found {nav_count}")

    # Google Fonts families: count family= tokens only
    families: list[str] = []
    for m in re.finditer(r"family=([A-Za-z0-9+]+)", html):
        fam = m.group(1).replace("+", " ")
        if fam and fam not in families:
            families.append(fam)
    if len(families) > 3:
        errors.append(f"too many webfont families ({len(families)}): {families}")

    if "UI_CONTRACT.md" not in (WEB / "UI_CONTRACT.md").name or not (WEB / "UI_CONTRACT.md").is_file():
        errors.append("ate/ui/web/UI_CONTRACT.md missing")
    agents = Path(__file__).resolve().parents[2] / "AGENTS.md"
    if not agents.is_file():
        errors.append("repo AGENTS.md missing")

    if "tags" not in tabs:
        errors.append("Tags tab (data-page=tags) missing")

    if errors:
        print("FAIL check_ui_contract:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK check_ui_contract tabs={tabs} fonts={families}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
