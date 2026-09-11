"""BUFFER step-response wraps — LA-1 test_SSR / test_LSR / test_NPR."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

from ate.core.paths import LAB_REPORT_PATH
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.drivers.mso5072 import capture_jpeg
from ate.reporting.lab_report import (
    ensure_screenshot_dir,
    place_lssr_photos,
    place_sssr_photos,
    save_named_screenshot,
    update_summary_status,
)

MYT = timezone(timedelta(hours=8))


def _emit(params: RunParams, step_id: str, status: str, message: str) -> None:
    hook: Optional[Callable[..., None]] = getattr(params, "progress_hook", None)
    if hook:
        hook(step_id, status, message)


def _capture(
    scope,
    *,
    folder: str,
    unit: int,
    variant: str,
    channel: str,
    out_dir: Path,
    ts: str,
) -> Path:
    tmp = out_dir / f"_tmp_{folder}_{variant}_U{unit}_{ts}.jpg"
    capture_jpeg(scope, tmp)
    path = save_named_screenshot(
        folder, unit=unit, variant=variant, source_bytes_path=tmp, channel=channel
    )
    try:
        if tmp.exists() and tmp != path:
            tmp.unlink()
    except Exception:
        pass
    return path


def _run_sssr(instr, params: RunParams):
    """Small Signal Step Response — LA-1 test_SSR; overshoot on CH2."""
    from configurations import current_limit
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import scope_setup

    psu, gen, scope = instr.psu, instr.gen, instr.scope
    vcc = params.vcc
    unit = int(params.unit_index or 1)
    ch = (params.channel or "CHA").upper()
    folder = "SmallSignalStep"
    out_dir = ensure_screenshot_dir(folder, unit)
    ts = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")

    try:
        power_on_protected(psu, 1, vcc / 2, current_limit)
        power_on_protected(psu, 2, vcc / 2, current_limit)
        setup_square(gen, 1, 500_000, 0.1, 0)
        scope_setup(scope, 200e-9, 0.025)
        time.sleep(1)
        scope.write("CHAN1:SCALe 0.05")
        scope.write("CHAN1:OFFS 0.05")
        scope.write("CHAN2:SCALe 0.05")
        scope.write("CHAN2:OFFS 0")
        scope.write("TIMebase:OFFSet 600e-9")
        scope.write(":MEASure:ITEM OVERshoot,CHAN2")
        time.sleep(1)
        overshoot = float(scope.query(":MEASure:ITEM? OVERshoot,CHAN2").strip())
        print(f"SSSR overshoot CH2: {overshoot}", flush=True)
        _emit(params, "capture", "running", "Capturing SSSR scope photo")
        shot = _capture(
            scope,
            folder=folder,
            unit=unit,
            variant="STEP",
            channel=ch,
            out_dir=out_dir,
            ts=ts,
        )
        lab = Path(params.lab_report or LAB_REPORT_PATH)
        try:
            place_sssr_photos(lab, photo_path=shot, unit_index=unit, channel=ch)
            update_summary_status(lab, "Small Signal Step Response", "Pass")
            excel_msg = f"embedded {shot.name} in {lab.name}"
        except Exception as exc:
            excel_msg = f"Excel update skipped: {exc}"
        return {
            "summary": f"SSSR photo -> Test_Database; {excel_msg}",
            "screenshots": [str(shot)],
            "lab_sheet": "SSSR",
            "OverSHT": overshoot,
        }
    finally:
        try:
            stop_output(gen)
            power_off(psu)
            scope.write(":MEASure:CLEar ALL")
        except Exception:
            pass


def _run_lssr(instr, params: RunParams):
    """Large Signal Step Response — LA-1 test_LSR."""
    from configurations import current_limit
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import scope_setup

    psu, gen, scope = instr.psu, instr.gen, instr.scope
    vcc = params.vcc
    unit = int(params.unit_index or 1)
    ch = (params.channel or "CHA").upper()
    folder = "LargeSignalStep"
    out_dir = ensure_screenshot_dir(folder, unit)
    ts = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")

    try:
        power_on_protected(psu, 1, vcc / 2, current_limit)
        power_on_protected(psu, 2, vcc / 2, current_limit)
        setup_square(gen, 1, 250_000, 4, 0)
        scope_setup(scope, 500e-9, 1)
        time.sleep(1)
        scope.write("CHAN1:SCALe 1")
        scope.write("CHAN1:OFFS 1")
        scope.write("CHAN2:SCALe 1")
        scope.write("CHAN2:OFFS 0")
        scope.write("TIMebase:OFFSet 1e-6")
        time.sleep(1)
        _emit(params, "capture", "running", "Capturing LSSR scope photo")
        shot = _capture(
            scope,
            folder=folder,
            unit=unit,
            variant="STEP",
            channel=ch,
            out_dir=out_dir,
            ts=ts,
        )
        lab = Path(params.lab_report or LAB_REPORT_PATH)
        try:
            place_lssr_photos(lab, photo_path=shot, unit_index=unit, channel=ch)
            update_summary_status(lab, "Large Signal Step Response", "Pass")
            excel_msg = f"embedded {shot.name} in {lab.name}"
        except Exception as exc:
            excel_msg = f"Excel update skipped: {exc}"
        return {
            "summary": f"LSSR photo -> Test_Database; {excel_msg}",
            "screenshots": [str(shot)],
            "lab_sheet": "LSSR",
        }
    finally:
        try:
            stop_output(gen)
            power_off(psu)
            scope.write(":MEASure:CLEar ALL")
        except Exception:
            pass


def _run_npr(instr, params: RunParams):
    """No Phase Reversal — LA-1 test_NPR; screenshots only (no paste anchors)."""
    from configurations import current_limit
    from generator_setup import setup_sine, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import scope_setup

    psu, gen, scope = instr.psu, instr.gen, instr.scope
    vcc = params.vcc
    unit = int(params.unit_index or 1)
    ch = (params.channel or "CHA").upper()
    folder = "PhaseReversal"
    out_dir = ensure_screenshot_dir(folder, unit)
    ts = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")

    try:
        power_on_protected(psu, 1, (vcc / 2) + 0.25, current_limit)
        power_on_protected(psu, 2, (vcc / 2) + 0.25, current_limit)
        setup_sine(gen, 1, 1000, 6, 0)
        scope_setup(scope, 125e-6, 1)
        time.sleep(1)
        scope.write("CHAN1:SCALe 1")
        scope.write("CHAN1:OFFS 0")
        scope.write("CHAN2:SCALe 1")
        scope.write("CHAN2:OFFS -1")
        scope.write("TIMebase:OFFSet 0")
        time.sleep(1)
        _emit(params, "capture", "running", "Capturing NPR scope photo")
        shot = _capture(
            scope,
            folder=folder,
            unit=unit,
            variant="NPR",
            channel=ch,
            out_dir=out_dir,
            ts=ts,
        )
        return {
            "summary": f"NPR photo -> Test_Database ({shot.name})",
            "screenshots": [str(shot)],
            "lab_sheet": "NoPhaseReversal",
        }
    finally:
        try:
            stop_output(gen)
            power_off(psu)
            scope.write(":MEASure:CLEar ALL")
        except Exception:
            pass


register(
    TestSpec(
        id="sssr",
        label="Small Signal Step Response",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="BUFFER",
        lab_sheet="SSSR",
        run=_run_sssr,
        notes="LA-1 test_SSR: 0.1Vpp 500kHz; overshoot on CH2",
        fixed_steps=[{"id": "capture", "label": "SSSR capture", "phase": "measure"}],
    )
)
register(
    TestSpec(
        id="lssr",
        label="Large Signal Step Response",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="BUFFER",
        lab_sheet="LSSR",
        run=_run_lssr,
        notes="LA-1 test_LSR: 4Vpp 250kHz",
        fixed_steps=[{"id": "capture", "label": "LSSR capture", "phase": "measure"}],
    )
)
register(
    TestSpec(
        id="no_phase_reversal",
        label="Phase Reversal Protection",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="BUFFER",
        lab_sheet="NoPhaseReversal",
        run=_run_npr,
        notes="LA-1 test_NPR; screenshots only (no workbook paste anchors)",
        fixed_steps=[{"id": "capture", "label": "NPR capture", "phase": "measure"}],
    )
)
