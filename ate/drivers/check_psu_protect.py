"""Self-check: PSU protect defaults are DUT-capped; unprotected power_on banned.

Run: python -m ate.drivers.check_psu_protect
"""
from __future__ import annotations

import inspect
import re
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
    if "protect arm delay" not in src:
        raise AssertionError("power_on_protected must delay after OVP ceiling before VOLT")
    if "if not _prot_stat_on" not in src:
        raise AssertionError("must not rewrite PROT:STAT ON every sweep step")
    if "refuse ON" not in src and "_prot_stat_on" not in src:
        raise AssertionError("power_on_protected must readback protect STAT")
    volt_at = src.find(":SOUR{channel}:VOLT {voltage}")
    ceil_at = src.find(":SOUR{channel}:VOLT:PROT {OVP_ABS_MAX_V}")
    if volt_at < 0 or ceil_at < 0 or ceil_at > volt_at:
        raise AssertionError("must raise OVP ceiling before VOLT (live sweep trip)")

    class _TripPsu:
        """Fails the check if VOLT is written above armed OVP while OUTP is ON."""

        def __init__(self) -> None:
            self.writes: list[str] = []
            self.outp = {1: "OFF", 2: "OFF", 3: "OFF"}
            self.volt = {1: 0.0, 2: 0.0, 3: 0.0}
            self.ovp = {1: 0.0, 2: 0.0, 3: 0.0}
            self.ovp_on = {1: False, 2: False, 3: False}
            self.ocp_on = {1: False, 2: False, 3: False}
            self.tripped: list[str] = []

        def write(self, cmd: str) -> None:
            self.writes.append(str(cmd))
            t = str(cmd).upper().replace(" ", "")
            for ch in (1, 2, 3):
                if f":OUTPCH{ch},ON" in t:
                    self.outp[ch] = "ON"
                elif f":OUTPCH{ch},OFF" in t:
                    self.outp[ch] = "OFF"
                if f":SOUR{ch}:VOLT:PROT:STATON" in t:
                    self.ovp_on[ch] = True
                if f":SOUR{ch}:CURR:PROT:STATON" in t:
                    self.ocp_on[ch] = True
            m_ovp = re.search(r":SOUR(\d):VOLT:PROT([0-9.]+)$", t)
            if m_ovp:
                ch = int(m_ovp.group(1))
                self.ovp[ch] = float(m_ovp.group(2))
                if self.outp[ch] == "ON" and self.ovp_on[ch] and self.volt[ch] > self.ovp[ch] + 1e-9:
                    self.tripped.append(f"OVP tighten CH{ch} V={self.volt[ch]} OVP={self.ovp[ch]}")
                    self.outp[ch] = "OFF"
                return
            m_v = re.search(r":SOUR(\d):VOLT(-?[0-9.]+)$", t)
            if m_v:
                ch = int(m_v.group(1))
                v = float(m_v.group(2))
                if self.outp[ch] == "ON" and self.ovp_on[ch] and v > self.ovp[ch] + 1e-9:
                    self.tripped.append(f"OVP trip CH{ch} V={v} OVP={self.ovp[ch]}")
                    self.outp[ch] = "OFF"
                    return
                self.volt[ch] = v

        def query(self, cmd: str) -> str:
            t = str(cmd).upper().replace(" ", "")
            for ch in (1, 2, 3):
                if f":OUTP?CH{ch}" in t:
                    return self.outp[ch]
                if f":SOUR{ch}:VOLT:PROT:STAT?" in t:
                    return "ON" if self.ovp_on[ch] else "OFF"
                if f":SOUR{ch}:CURR:PROT:STAT?" in t:
                    return "ON" if self.ocp_on[ch] else "OFF"
            return "OFF"

    live = _TripPsu()
    power_on_protected(live, 1, 2.0, 0.1)
    power_on_protected(live, 1, 5.0, 0.1)
    power_on_protected(live, 1, 2.0, 0.1)
    if live.tripped:
        raise AssertionError(f"live V step must not trip OVP: {live.tripped}")
    if live.outp[1] != "ON":
        raise AssertionError("CH1 must stay ON after 2.0->5.0->2.0")
    if abs(live.ovp[1] - 2.3) > 1e-9:
        raise AssertionError(f"final OVP must tighten to 2.3, got {live.ovp[1]}")

    from pathlib import Path

    ldo = Path(__file__).resolve().parents[1] / "tests" / "power" / "ldo.py"
    ldo_src = ldo.read_text(encoding="utf-8")
    if "ovp=6.0" in ldo_src or "ovp=5.6" in ldo_src or "_enable_dc" in ldo_src:
        raise AssertionError("LDO must use default Vset+0.3 OVP; no 6 V trip or AWG 5.5 V EN")

    print(
        f"OK psu-protect: OVP+{OVP_MARGIN_V}V OCP+{OCP_MARGIN_A}A "
        f"ceil={OVP_ABS_MAX_V}V/{OCP_ABS_MAX_A}A; unprotected banned"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
