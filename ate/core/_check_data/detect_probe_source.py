"""Fixture for check_test_detect — not a live family module."""

def test_parameter():
    """Config helper: must not appear as a wrap row."""
    return [{"test_name": "dummy", "parameters": ["X"]}]


def test_detect_probe(instr, logger=None):
    """Clean golden: has instr, no stdin prompts."""
    psu = instr.psu
    return {"ok": True, "psu": bool(psu)}


def test_input_threshold(psu, dmm, logger=None, vcc_list=None):
    """Clean See Lin / Lim style: bare handles, not instr."""
    return {"VIH": 1.0, "psu": bool(psu), "dmm": bool(dmm)}


def _prompt(msg):
    return input(msg)


def test_ioz(instr, logger=None):
    """Dirty via helper: must be blocked even without a direct input() call."""
    _prompt("wire Y")
    return {}


def test_cpd(instr, logger=None):
    """Dirty golden: must be blocked."""
    input("Testing...")
    return {}


def test_detect_extra(instr, logger=None):
    return {"extra": 1}
