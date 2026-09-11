"""Fixture for check_test_detect — not a live family module."""

def test_detect_probe(instr, logger=None):
    """Clean golden: has instr, no stdin prompts."""
    psu = instr.psu
    return {"ok": True, "psu": bool(psu)}


def test_cpd(instr, logger=None):
    """Dirty golden: must be blocked."""
    input("Testing...")
    return {}
