"""RS29511 I2C-buffer DC. Not CMOS IDD. Not Soo wrap. Do not register.

PDF 7.5: ICC typ 2.0 max 4.5 mA at VCC=5.5 V, SDAIN/SCLIN=0, 10k on OUT.
SIM CMOS ICC is uA-class -- stamp the DMM, do not fake 2 mA.
READY is open-drain with 10k; idle high ~ VCC.
Cio SDA/SCL typ 6.5 max 10 pF; SIM DMM CAP is 5 pF.
"""
from __future__ import annotations

from typing import Any

from ate.core.runner import RunParams

_ICC_WIRE = (
    "RS29511 ICC: EN=VCC jumper; AWG CH1=SDAIN=0 V DC, CH2=SCLIN=0 V DC; "
    "10k pull-up SDAOUT/SCLOUT; DMM DCI on VCC. Continue."
)
_VOUT_WIRE = (
    "RS29511 READY: EN=VCC jumper; 10k pull-up READY to VCC; DMM VOLT on READY. "
    "Idle high. Continue."
)
_CAP_WIRE = (
    "RS29511 Cio: PSU OFF. DMM CAP SDAIN to GND (not EN, not 400 kHz C=I/Vf). Continue."
)


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def run_icc(instr, params: RunParams) -> dict[str, Any]:
    """PDF condition: SDAIN/SCLIN=0, 10k on OUT, VCC 2.3/3.3/5.0/5.5."""
    if getattr(instr, "psu", None) is None or getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: PSU, DMM")
    if getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: AWG")
    from ate.tests.logic.eugene_cap import _dmm_ua_after_settle, _ilim, _psu_ch1_only
    from dmm_setup import dmm_setup_current_continuous
    from generator_setup import set_output_load, setup_dc, stop_output
    from psu_setup import power_off

    if not _pause(params, _ICC_WIRE):
        return {"summary": "aborted", "data": {}}
    dmm_setup_current_continuous(instr.dmm)
    ilim = _ilim(params)
    vccs = [2.3, 3.3, 5.0, 5.5]
    rows: list[dict[str, Any]] = []
    last_ua: float | None = None
    hook = params.progress_hook
    try:
        set_output_load(instr.gen, 1, "INF")
        set_output_load(instr.gen, 2, "INF")
        setup_dc(instr.gen, 1, 0.0)
        setup_dc(instr.gen, 2, 0.0)
        for vcc in vccs:
            _psu_ch1_only(instr, vcc, ilim, ovp=5.6, ocp=0.2)
            ua = _dmm_ua_after_settle(
                instr.dmm,
                tag=f"RS29511 ICC VCC={vcc} SDAIN=0",
                last_ua=last_ua,
                hook=hook,
                hook_id="rs29511_icc",
            )
            last_ua = ua
            rows.append({"VCC": vcc, "SDAIN_V": 0.0, "ICC_uA": ua})
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
    if not rows:
        raise RuntimeError("RS29511 ICC: no points measured")
    at_55 = next((r for r in rows if abs(float(r["VCC"]) - 5.5) < 1e-9), rows[-1])
    icc = float(at_55["ICC_uA"])
    return {
        "summary": f"ICC={icc:.3f} uA @ 5.5 V SDAIN=0 (PDF typ 2.0 mA; SIM CMOS uA)",
        "data": {
            "hotswap_dc": True,
            "item": "ICC",
            "rows": rows,
            "ICC_uA": icc,
        },
        "measurements": [{"id": "ICC_uA", "value": icc, "unit": "uA"}],
    }


def run_vout(instr, params: RunParams) -> dict[str, Any]:
    """READY open-drain idle high (10k to VCC). Not CMOS push-pull VOH."""
    if getattr(instr, "psu", None) is None or getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: PSU, DMM")
    from dmm_setup import dmm_setup_voltage
    from psu_setup import power_off, power_on_protected

    if not _pause(params, _VOUT_WIRE):
        return {"summary": "aborted", "data": {}}
    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    vout = float("nan")
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        vout = float(dmm_setup_voltage(instr.dmm))
    finally:
        try:
            power_off(instr.psu)
        except Exception:
            pass
    return {
        "summary": f"READY={vout:.3f} V @ VCC={vcc} (10k pull-up idle high)",
        "data": {
            "hotswap_dc": True,
            "item": "READY",
            "VCC": vcc,
            "VOUT": vout,
        },
        "measurements": [{"id": "VOUT_V", "value": vout, "unit": "V"}],
    }


def run_cap(instr, params: RunParams) -> dict[str, Any]:
    """DMM CAP on SDAIN, PSU off. PDF Cio 6.5/10 pF; SIM 5 pF."""
    if getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: DMM")
    from dmm_setup import dmm_setup_cap
    from psu_setup import power_off

    if not _pause(params, _CAP_WIRE):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is not None:
        power_off(instr.psu)
    cap_f = float(dmm_setup_cap(instr.dmm))
    pf = cap_f * 1e12
    return {
        "summary": f"Cio={pf:.2f} pF (PDF typ 6.5 max 10; SIM 5)",
        "data": {
            "hotswap_dc": True,
            "item": "SDAIN",
            "CAP_pF": pf,
        },
        "measurements": [{"id": "CAP_pF", "value": pf, "unit": "pF"}],
    }
