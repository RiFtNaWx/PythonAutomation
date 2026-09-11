"""Self-check: PSU protect defaults are DUT-capped; unprotected power_on banned.

Run: python -m ate.drivers.check_psu_protect
"""
from __future__ import annotations

import inspect
import sys

from psu_setup import (
    OCP_ABS_MAX_A,
    OCP_MARGIN_A,
    OVP_ABS_MAX_V,
    OVP_MARGIN_V,
    power_on,
    power_on_protected,
    resolve_protect,
)


def main() -> int:
    ovp, ocp = resolve_protect(5.0, 0.1)
    if abs(ovp - (5.0 + OVP_MARGIN_V)) > 1e-9:
        raise AssertionError(f"default OVP want 5.3 got {ovp}")
    if abs(ocp - (0.1 + OCP_MARGIN_A)) > 1e-9:
        raise AssertionError(f"default OCP want 0.2 got {ocp}")

    # Stricter (lower) allowed
    ovp2, ocp2 = resolve_protect(5.0, 0.1, ovp=5.1, ocp=0.05)
    if ovp2 != 5.1 or ocp2 != 0.05:
        raise AssertionError(f"stricter trips broken: {ovp2},{ocp2}")

    # Ariff-style 5.6 still DUT-capped
    ovp3, _ = resolve_protect(0.0, 0.1, ovp=5.6)
    if ovp3 != 5.6:
        raise AssertionError(f"DUT-capped 5.6 expected, got {ovp3}")

    try:
        resolve_protect(5.0, 0.1, ovp=30.0)
        raise AssertionError("instrument-max OVP must raise")
    except ValueError:
        pass
    try:
        resolve_protect(5.0, 0.1, ocp=3.0)
        raise AssertionError("instrument-max OCP must raise")
    except ValueError:
        pass

    try:
        power_on(None, 1, 5.0)
        raise AssertionError("power_on must raise")
    except RuntimeError as exc:
        if "power_on_protected" not in str(exc):
            raise AssertionError(f"unexpected: {exc}") from exc

    src = inspect.getsource(power_on_protected)
    if "PROT:STAT ON" not in src:
        raise AssertionError("power_on_protected must enable PROT:STAT")
    if "refuse ON" not in src and "_prot_stat_on" not in src:
        raise AssertionError("power_on_protected must readback protect STAT")

    print(
        f"OK psu-protect: OVP+{OVP_MARGIN_V}V OCP+{OCP_MARGIN_A}A "
        f"ceil={OVP_ABS_MAX_V}V/{OCP_ABS_MAX_A}A; unprotected banned"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
