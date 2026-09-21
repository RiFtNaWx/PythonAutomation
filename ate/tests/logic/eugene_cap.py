"""Eugene RS1G07 IDD / CPD / CIN. PSU CH1 only, DMM DCI, AWG high-Z. No input().

RS0204 keeps pin-Cio Cpd; this body is for single-rail Logic (RS1G07).
Golden used stdin prompts; Continue is pause_hook.
"""
from __future__ import annotations

import time
from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_LOGIC = "LOGIC"
_NOTE = "Eugene RS1G07: PSU CH1=VCC (CH2/CH3 OFF), AWG CH1 high-Z, DMM DCI. Not RS0204 pin Cio."
_IDD_PARTS = frozenset(
    {
        "rs1g07",
        "rs74aup1g07",
        "rs1g14",
        "rs1g125",
        "rs164",
        "rs1g74",
        "rs1g123",
    }
)
_SETTLE_S = 5.0  # USB dwell after VCC/freq/AWG change. SIM skips sleep.


def _recipe_dwell_s(params: RunParams | None) -> float:
    """PRD-004: dwell_s wins, then settle_s, then module default."""
    if params is not None:
        d = getattr(params, "dwell_s", None)
        if d is not None:
            return float(d)
        s = getattr(params, "settle_s", None)
        if s is not None:
            return float(s)
    return _SETTLE_S


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _require(instr, *names: str) -> None:
    remap = {"MSO": "scope", "PSU": "psu", "AWG": "gen", "DMM": "dmm"}
    missing = [n for n in names if getattr(instr, remap[n], None) is None]
    if missing:
        raise RuntimeError(f"Missing instruments: {', '.join(missing)}")


def _ilim(params: RunParams) -> float:
    return float(getattr(params, "current_limit_a", None) or 0.10)


def _cap_pf(i_ua: float, vcc: float, freq: float) -> float | None:
    if not vcc or not freq:
        return None
    return (float(i_ua) * 1e-6) / (float(vcc) * float(freq)) * 1e12


def _psu_ch1_only(instr, vcc: float, ilim: float, *, ovp: float, ocp: float = 0.2) -> None:
    """Logic IDD/CIN/CPD: CH1=VCC, force CH2/CH3 OFF (leftover LDO/OpAmp rails)."""
    from psu_setup import _outp_is_on, power_on_protected

    psu = instr.psu
    for ch in (2, 3):
        if _outp_is_on(psu, ch) is not False:
            psu.write(f":OUTP CH{ch},OFF")
    power_on_protected(psu, 1, vcc, ilim, ovp=ovp, ocp=ocp)


def _dmm_ua_after_settle(
    dmm,
    *,
    tag: str,
    last_ua: float | None,
    hook=None,
    hook_id: str = "settle",
    dwell_s: float | None = None,
) -> float:
    """Dwell then one :READ?. Log delta so a stuck AWG/PSU is visible."""
    from dmm_setup import dmm_read
    wait = float(dwell_s if dwell_s is not None else _SETTLE_S)
    if hook:
        hook(hook_id, "running", f"{tag} settle {wait:.1f}s")
    print(f"{tag} settle {wait:.1f}s", flush=True)
    t0 = time.perf_counter()
    time.sleep(wait)
    waited = time.perf_counter() - t0
    if abs(waited - wait) > 0.5:
        print(f"{tag} settle wall {waited:.1f}s (want {wait:.1f}s)", flush=True)
    ua = float(dmm_read(dmm)) * 1e6
    if last_ua is None:
        print(f"{tag} {ua:.4f} uA", flush=True)
    else:
        delta = ua - last_ua
        print(f"{tag} {ua:.4f} uA (was {last_ua:.4f}, d={delta:+.4f})", flush=True)
        if abs(delta) < 0.001:
            print(f"WARN {tag} unchanged -- AWG/PSU may not have stepped", flush=True)
    if hook:
        hook(hook_id, "running", f"{tag} {ua:.4f} uA")
    return ua


def _awg_square(instr, vcc: float, freq: float) -> float:
    """OFF then APPL:SQU then ON. Do not send a standalone FREQ header (Error 116).

    Returns the APPL? frequency so CIN/CPD C=I/(V f) uses the live speed, not the want.
    """
    from generator_setup import applied_freq_hz, set_output_load, setup_square

    gen = instr.gen
    gen.write(":OUTP1 OFF")
    time.sleep(0.2)
    set_output_load(gen, 1, "INF")
    setup_square(gen, 1, freq, vcc, vcc / 2.0)
    got = applied_freq_hz(gen, 1, freq)
    print(f"AWG APPL:SQU want {freq:g} Hz got {got:g} Hz {vcc} Vpp (no FREQ header)", flush=True)
    return got


def run_cpd(instr, params: RunParams) -> dict[str, Any]:
    """VCC corners 1.8/2.5/3.3/5.0 V, 10 MHz square, DMM current in uA."""
    part = str(getattr(params, "part", "") or "").strip().lower()
    if part == "rs0204":
        from ate.tests.logic.rs0204 import _run_cpd

        return _run_cpd(instr, params)
    _require(instr, "PSU", "AWG", "DMM")
    from dmm_setup import dmm_setup_current

    if not _pause(
        params,
        "CPD: PSU CH1=VCC (CH2/CH3 OFF), AWG CH1 high-Z square 10 MHz, DMM DCI. Continue.",
    ):
        return {"summary": "aborted", "data": {}}
    dmm_setup_current(instr.dmm)
    ilim = _ilim(params)
    vccs = [1.8, 2.5, 3.3, 5.0]
    rows: list[dict[str, Any]] = []
    hook = params.progress_hook
    last_ua: float | None = None
    try:
        for vcc in vccs:
            _psu_ch1_only(instr, vcc, ilim, ovp=min(vcc + 0.2, 6.0), ocp=0.2)
            freq = _awg_square(instr, vcc, 10e6)
            ua = _dmm_ua_after_settle(
                instr.dmm,
                tag=f"CPD VCC={vcc} V",
                last_ua=last_ua,
                hook=hook,
                hook_id="cpd_dmm",
                dwell_s=_recipe_dwell_s(params),
            )
            last_ua = ua
            pf = _cap_pf(ua, vcc, freq)
            rows.append({"VCC": vcc, "I_uA": ua, "freq_hz": freq, "CPD_pF": pf})
    finally:
        try:
            from generator_setup import stop_output

            stop_output(instr.gen)
        except Exception:
            pass
    last = rows[-1] if rows else {}
    pf = last.get("CPD_pF")
    return {
        "summary": f"CPD n={len(rows)} last={pf} pF @ {last.get('VCC')} V",
        "data": {"rows": rows},
        "measurements": [
            {"id": "CPD_pF", "value": pf, "unit": "pF"}
        ]
        if last and pf is not None
        else [],
    }


def run_idd(instr, params: RunParams) -> dict[str, Any]:
    """RS1G07 IDD: PSU CH1 VCC corners, AWG CH1 DC 0/5.5 on Input A, DMM DCI.

    OVP is 5.6 V, never 5.5. Vset=OVP (or 10% of 5.0 = 5.5) trips DP832 at the 5.5 V corner.
    """
    _require(instr, "PSU", "AWG", "DMM")
    from dmm_setup import dmm_setup_current_continuous
    from generator_setup import set_output_load, setup_dc, stop_output

    if not _pause(
        params,
        "IDD: PSU CH1=VCC (CH2/CH3 OFF), AWG CH1 DC on Input A, DMM DCI. Continue.",
    ):
        return {"summary": "aborted", "data": {}}
    dmm_setup_current_continuous(instr.dmm)
    ilim = _ilim(params)
    vccs = [1.65, 3.3, 5.0, 5.5]
    inputs = [0.0, 5.5]
    rows: list[dict[str, Any]] = []
    hook = params.progress_hook
    last_ua: float | None = None
    try:
        set_output_load(instr.gen, 1, "INF")
        for vcc in vccs:
            _psu_ch1_only(instr, vcc, ilim, ovp=5.6, ocp=0.2)
            for a_v in inputs:
                if not setup_dc(instr.gen, 1, a_v):
                    continue
                ua = _dmm_ua_after_settle(
                    instr.dmm,
                    tag=f"IDD VCC={vcc} Vin={a_v}",
                    last_ua=last_ua,
                    hook=hook,
                    hook_id="idd_dmm",
                    dwell_s=_recipe_dwell_s(params),
                )
                last_ua = ua
                rows.append({"VCC": vcc, "INPUT_A_V": a_v, "IDD_uA": ua})
        if not rows:
            raise RuntimeError("IDD: no points measured")
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
    last = rows[-1]
    mx = max(abs(float(r["IDD_uA"])) for r in rows)
    return {
        "summary": f"IDD n={len(rows)} last={last['IDD_uA']:.3f} uA @ {last['VCC']} V",
        "data": {"rows": rows},
        "measurements": [{"id": "ICC_uA", "value": mx, "unit": "uA"}],
    }


def run_cin(instr, params: RunParams) -> dict[str, Any]:
    """CIN at 3.3 V across 1/5/10 MHz, DMM current in uA."""
    _require(instr, "PSU", "AWG", "DMM")
    from dmm_setup import dmm_setup_current

    if not _pause(
        params,
        "CIN: PSU CH1=3.3 V (CH2/CH3 OFF), AWG CH1 high-Z square 1/5/10 MHz, DMM DCI. Continue.",
    ):
        return {"summary": "aborted", "data": {}}
    dmm_setup_current(instr.dmm)
    ilim = _ilim(params)
    vcc = 3.3
    freqs = list(params.resolved_freq_hz() or []) or [1e6, 5e6, 10e6]
    rows: list[dict[str, Any]] = []
    hook = params.progress_hook
    last_ua: float | None = None
    try:
        _psu_ch1_only(instr, vcc, ilim, ovp=min(vcc + 0.2, 6.0), ocp=0.2)
        for freq in freqs:
            mhz = int(freq / 1e6)
            got = _awg_square(instr, vcc, freq)
            ua = _dmm_ua_after_settle(
                instr.dmm,
                tag=f"CIN {mhz} MHz",
                last_ua=last_ua,
                hook=hook,
                hook_id="cin_dmm",
                dwell_s=_recipe_dwell_s(params),
            )
            last_ua = ua
            pf = _cap_pf(ua, vcc, got)
            rows.append({"VCC": vcc, "I_uA": ua, "freq_hz": got, "CIN_pF": pf})
    finally:
        try:
            from generator_setup import stop_output

            stop_output(instr.gen)
        except Exception:
            pass
    last = rows[-1] if rows else {}
    pf = last.get("CIN_pF")
    return {
        "summary": f"CIN n={len(rows)} last={pf} pF @ {last.get('freq_hz', 0) / 1e6:.0f} MHz",
        "data": {"rows": rows},
        "measurements": [
            {"id": "CIN_pF", "value": pf, "unit": "pF"}
        ]
        if last and pf is not None
        else [],
    }


register(
    TestSpec(
        id="cin",
        label="CIN (Eugene)",
        required_instruments=frozenset({"PSU", "AWG", "DMM"}),
        fixture_mode=_LOGIC,
        lab_sheet="CIN",
        run=run_cin,
        dual_channel=False,
        notes=_NOTE,
    )
)
register(
    TestSpec(
        id="cpd",
        label="CPD (Eugene)",
        required_instruments=frozenset({"PSU", "AWG", "DMM"}),
        fixture_mode=_LOGIC,
        lab_sheet="CPD",
        run=run_cpd,
        dual_channel=False,
        notes=_NOTE,
    )
)
