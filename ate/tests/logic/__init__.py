"""Logic family -- import registers TestSpec. Add a file here, then enabled_tests in part yaml."""
from ate.tests.logic import ariff_dc  # noqa: F401
from ate.tests.logic import clk_q  # noqa: F401
from ate.tests.logic import eugene_cap  # noqa: F401
from ate.tests.logic import imported_input_off_leakage  # noqa: F401
from ate.tests.logic import pulse_width  # noqa: F401
from ate.tests.logic import rs0204  # noqa: F401
from ate.tests.logic import rs0302  # noqa: F401
from ate.tests.logic import serial_shift  # noqa: F401
from ate.tests.logic import seelim_dc  # noqa: F401
from ate.tests.logic import wraps  # noqa: F401
from ate.tests.logic import oe_timing  # noqa: F401
from ate.tests.logic import rs29511_prop  # noqa: F401
from ate.tests.logic import rs29511_dc  # noqa: F401
from ate.tests.logic import cmos_prop  # noqa: F401
from ate.tests.logic import product_model  # noqa: F401
from ate.tests.logic import logic_dc  # noqa: F401  # Path B last
from ate.tests.logic import dc  # noqa: F401

__all__ = [
    "wraps",
    "oe_timing",
    "rs29511_prop",
    "rs29511_dc",
    "cmos_prop",
    "ariff_dc",
    "rs0204",
    "rs0302",
    "imported_input_off_leakage",
    "eugene_cap",
    "clk_q",
    "pulse_width",
    "serial_shift",
    "seelim_dc",
    "product_model",
    "logic_dc",
    "dc",
]
