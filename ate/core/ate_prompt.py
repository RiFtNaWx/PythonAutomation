"""Filled Cursor prompt for the operator console (Path A/B/C).

One source for Tests page Copy and check_add_test. Live product is ate/ + 8766 + 5174.
"""
from __future__ import annotations

_SKILLS = (
    "Compulsory skills: .cursor/skills/ate-prompt, ate-add-test, ate-ocr, ponytail, i-have-adhd."
)
_LIVE = "Live product is ate/ + worker 8766 + UI 5174. Read AGENTS.md then docs/VIBE_CODE.md."
_DONT = (
    "Do not edit runner.py / database.py path shape. Do not call input() in TestSpec.run. "
    "Do not import Lim.* / Ariff.* / Soo.*. Do not scrape en.run-ic.com. Do not unpark A13."
)


def fill_prompt(
    *,
    path: str,
    operator: str,
    family: str,
    part: str,
    package: str,
    version: str,
    test_id: str = "",
) -> str:
    """Return a paste block with campaign slots filled. path is a|b|c."""
    job = str(path or "b").strip().lower()
    if job not in ("a", "b", "c"):
        job = "b"
    op = str(operator or "<Name>").strip() or "<Name>"
    fam = str(family or "logic").strip().lower() or "logic"
    if fam == "lim":
        fam = "switch"
    pk = str(part or "<rs1g07>").strip() or "<rs1g07>"
    pkg = str(package or "<SC70-5>").strip() or "<SC70-5>"
    ver = str(version or "Version_1").strip() or "Version_1"
    tid = str(test_id or "").strip() or "<id>"
    head = (
        f"{_LIVE}\n{_SKILLS}\n"
        f"Operator: {op} (not All). Family: {fam}. Part: {pk} {pkg}. {ver}.\n"
        f"{_DONT}\n"
    )
    if job == "a":
        body = (
            f"Job: Path A customize this Version. Enable existing TestSpec ids {tid} "
            "via Tests page Save this Version. Write _manifest/test_catalog.yaml. "
            "Catalog wins over parts yaml. Do not invent a TestSpec. Do not copy another person's catalog.\n"
            "Proof: Setup checkbox list shows the ids after Save."
        )
    elif job == "c":
        body = (
            f"Job: Path C remember def test_{tid} into family {fam} for this campaign. "
            "Tests page Remember + enable. Stores file:line in snippet_map.yaml and START triggers that function. "
            "Do not rewrite the golden. Do not write imported_<id>.py. Block if input() or Lim/Ariff/Soo.\n"
            "Proof: python -m ate.core.check_test_detect then DEMO that id."
        )
    else:
        body = (
            f"Job: Path B realize test {tid} in family {fam} for part {pk}. "
            f"Create ate/tests/<family>/{tid}.py (Tests page Write test, or Cursor). "
            "Import from that package __init__.py. register(TestSpec) with id, label, "
            "required_instruments, fixture_mode, lab_sheet, run, dual_channel=False. "
            "run() must use power_on_protected and params.pause_hook, never input(). "
            f"Return measurements [{{id, value, unit}}] matching ate/config/limits/{pk}.yaml specs[].id. "
            "Add id to parts yaml enabled_tests unless this Version catalog already lists it. "
            "Idle-restart worker. Do not edit runner.py.\n"
            "Proof: python -m ate.core.check_add_test then python -m ate.core.check_family_load then DEMO that id."
        )
    return head + body + "\nIs it like this? Affirm and build. Or name the slot that is wrong.\n"
