# psu_setup.py
# DP832 power sequencing (live PSU API -- not procedures.py)
#
# HARD RULE: DUT bring-up always programs OVP/OCP. Defaults are DUT-capped
# (Vset+0.3 V, Iset+0.1 A), never instrument max (DP832 30 V / 3 A).

import time

# Absolute ceilings -- below DP832 hardware max; DUT must not request higher.
OVP_ABS_MAX_V = 6.0
OCP_ABS_MAX_A = 0.5
OVP_MARGIN_V = 0.3
OCP_MARGIN_A = 0.1


def _outp_is_on(psu, channel: int):
    """True/False from :OUTP? ; None if the query failed."""
    try:
        raw = str(psu.query(f":OUTP? CH{channel}")).strip().upper()
    except Exception:
        return None
    if raw in ("1", "ON"):
        return True
    if raw in ("0", "OFF"):
        return False
    return None


def _prot_stat_on(psu, channel: int, kind: str) -> bool:
    """kind is VOLT or CURR. True if PROT:STAT is ON."""
    try:
        raw = str(psu.query(f":SOUR{channel}:{kind}:PROT:STAT?")).strip().upper()
    except Exception:
        return False
    return raw in ("1", "ON")


def resolve_protect(voltage: float, current_limit: float, ovp=None, ocp=None) -> tuple[float, float]:
    """DUT-capped OVP/OCP. Defaults V+0.3 / I+0.1. Never DP832 instrument max."""
    v = float(voltage)
    i = float(current_limit)
    ovp_v = (v + OVP_MARGIN_V) if ovp is None else float(ovp)
    ocp_a = (i + OCP_MARGIN_A) if ocp is None else float(ocp)
    if ovp_v > OVP_ABS_MAX_V:
        raise ValueError(f"OVP {ovp_v} V exceeds DUT ceiling {OVP_ABS_MAX_V} V")
    if ocp_a > OCP_ABS_MAX_A:
        raise ValueError(f"OCP {ocp_a} A exceeds DUT ceiling {OCP_ABS_MAX_A} A")
    return ovp_v, ocp_a


def power_on(psu, channel: int, voltage: float):
    """Banned for DUT work -- use power_on_protected so OVP/OCP are always set."""
    raise RuntimeError(
        "Unprotected power_on is banned. Use power_on_protected (OVP/OCP always ON)."
    )


def power_off(psu):
    """All DP832 channels OFF; retry once if readback still ON."""
    for _ in range(2):
        for ch in (1, 2, 3):
            psu.write(f":OUTP CH{ch},OFF")
        leftover = False
        for ch in (1, 2, 3):
            st = _outp_is_on(psu, ch)
            if st is None:
                return
            if st:
                leftover = True
        if not leftover:
            return
        time.sleep(0.15)


def power_on_protected(psu, channel, voltage, current_limit, ovp=None, ocp=None):
    """Set V/I/OVP/OCP then ON. Never pulse OFF -- runner SAFE IDLE is the only off-ramp.

    Raise PROT to the DUT ceiling first, then V/I, then tighten. A live channel
    that writes VOLT before raising OVP (VIN 2.0 -> 5.0) trips DP832 OV -- the
    front panel looks like 'overvoltage' and 'reduce the limit' mid-test.
    Steady-state trip stays Vset+0.3 / Iset+0.1, not 6 V / 0.5 A.
    """
    ovp_v, ocp_a = resolve_protect(voltage, current_limit, ovp=ovp, ocp=ocp)

    psu.write(f":SOUR{channel}:VOLT:PROT {OVP_ABS_MAX_V}")
    psu.write(f":SOUR{channel}:CURR:PROT {OCP_ABS_MAX_A}")
    # Keep STAT armed. Rewriting STAT ON every sweep step flashes the OV/OC lamps.
    if not _prot_stat_on(psu, channel, "VOLT"):
        psu.write(f":SOUR{channel}:VOLT:PROT:STAT ON")
    if not _prot_stat_on(psu, channel, "CURR"):
        psu.write(f":SOUR{channel}:CURR:PROT:STAT ON")
    time.sleep(0.4)  # protect arm delay -- DP832 needs this before VOLT

    psu.write(f":SOUR{channel}:VOLT {voltage}")
    psu.write(f":SOUR{channel}:CURR {current_limit}")
    time.sleep(0.4)

    psu.write(f":SOUR{channel}:VOLT:PROT {ovp_v}")
    psu.write(f":SOUR{channel}:CURR:PROT {ocp_a}")
    time.sleep(0.4)
    if not _prot_stat_on(psu, channel, "VOLT"):
        raise RuntimeError(f"PSU CH{channel} OVP STAT failed to enable -- refuse ON")
    if not _prot_stat_on(psu, channel, "CURR"):
        raise RuntimeError(f"PSU CH{channel} OCP STAT failed to enable -- refuse ON")

    psu.write(f":OUTP CH{channel},ON")
    time.sleep(0.5)
    if _outp_is_on(psu, channel) is False:
        psu.write(f":OUTP CH{channel},ON")
        time.sleep(0.3)
