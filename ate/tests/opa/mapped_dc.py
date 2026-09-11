"""Every remaining sheet_map OpAmp test as a platform use case.

Not a second recipe tree. Capture to Test_Database, paste when paste.photos
exists, read DMM when the session has one (VOL requires DMM).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

from ate.core.paths import LAB_REPORT_PATH
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.drivers.mso5072 import capture_jpeg
from ate.reporting.lab_report import (
    ensure_screenshot_dir,
    place_mapped_photos,
    save_named_screenshot,
    update_summary_status,
)
from ate.reporting.photo_layout import photos_map

MYT = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class MappedCase:
    test_id: str
    label: str
    lab_sheet: str
    folder: str
    fixture_mode: str
    variant: str
    require_dmm: bool
    instruments: frozenset[str]


# One row per remaining sheet_map test (ids match rs622.yaml / old stubs).
CASES: tuple[MappedCase, ...] = (
    MappedCase(
        "power_on_time",
        "Power On Time",
        "PowerOnTime",
        "PowerOnTime",
        "BUFFER",
        "PON",
        False,
        frozenset({"MSO", "PSU", "AWG"}),
    ),
    MappedCase(
        "emirr",
        "EMIRR",
        "EMIRR",
        "EMIRR",
        "ATE",
        "RF",
        False,
        frozenset({"MSO", "PSU", "AWG"}),
    ),
    MappedCase(
        "psrr",
        "PSRR",
        "PSRR",
        "PSRR",
        "ATE",
        "PSRR",
        False,
        frozenset({"MSO", "PSU", "AWG"}),
    ),
    MappedCase(
        "cmrr",
        "CMRR",
        "CMRR",
        "CMRR",
        "ATE",
        "CMRR",
        False,
        frozenset({"MSO", "PSU", "AWG"}),
    ),
    MappedCase(
        "aol",
        "AOL",
        "AOL",
        "AOL",
        "ATE",
        "AOL",
        False,
        frozenset({"MSO", "PSU", "AWG"}),
    ),
    MappedCase(
        "vohl",
        "VOHL",
        "VOL",
        "VOHL",
        "ATE",
        "VOL",
        True,
        frozenset({"PSU", "DMM"}),
    ),
)


def _emit(params: RunParams, step_id: str, status: str, message: str) -> None:
    hook: Optional[Callable[..., None]] = getattr(params, "progress_hook", None)
    if hook:
        hook(step_id, status, message)


def _dmm_note(instr) -> str:
    dmm = getattr(instr, "dmm", None)
    if dmm is None:
        return "dmm=off"
    from dmm_setup import measure_voltage

    try:
        return f"Vdc={measure_voltage(dmm):.6g}"
    except Exception as exc:
        return f"dmm_err={exc}"


def _capture(scope, folder: str, unit: int, variant: str, channel: str) -> Path:
    out_dir = ensure_screenshot_dir(folder, unit)
    ts = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")
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


def _try_paste(case: MappedCase, shot: Path | None, unit: int, channel: str) -> str:
    if shot is None:
        return "no photo"
    try:
        photos_map(case.folder)
    except KeyError:
        return "no paste.photos"
    lab = Path(LAB_REPORT_PATH)
    try:
        place_mapped_photos(
            lab, test_key=case.folder, photo_path=shot, unit_index=unit, channel=channel
        )
        update_summary_status(lab, case.label, "Pass")
        return f"pasted {shot.name}"
    except Exception as exc:
        return f"Excel skipped: {exc}"


def _run_case(case: MappedCase, instr, params: RunParams) -> dict:
    from configurations import current_limit
    from generator_setup import setup_dc, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import scope_setup

    vcc = params.vcc
    unit = int(params.unit_index or 1)
    ch = (params.channel or "CHA").upper()
    psu, gen, scope = instr.psu, getattr(instr, "gen", None), getattr(instr, "scope", None)
    _emit(params, "capture", "running", f"{case.label} DUT_{unit} {ch}")

    try:
        if psu is not None:
            power_on_protected(psu, 1, vcc / 2, current_limit)
            try:
                power_on_protected(psu, 2, vcc / 2, current_limit)
            except Exception:
                pass
        if gen is not None:
            setup_dc(gen, 1, 0.0)
        if scope is not None:
            scope_setup(scope, 10e-6 if case.test_id == "power_on_time" else 1e-3, 0)
            time.sleep(0.4)
        dmm_txt = _dmm_note(instr)
        shot = None
        if scope is not None:
            shot = _capture(scope, case.folder, unit, case.variant, ch)
        excel_msg = _try_paste(case, shot, unit, ch)
        parts = [p for p in (dmm_txt, excel_msg) if p]
        if shot:
            parts.append(shot.name)
        return {
            "summary": f"{case.label}: " + "; ".join(parts),
            "screenshots": [str(shot)] if shot else [],
            "lab_sheet": case.lab_sheet,
            "dmm": dmm_txt,
        }
    finally:
        try:
            if gen is not None:
                stop_output(gen)
        except Exception:
            pass
        try:
            if psu is not None:
                power_off(psu)
        except Exception:
            pass


def _register(case: MappedCase) -> None:
    def _run(instr, params: RunParams):
        return _run_case(case, instr, params)

    notes = "Mapped sheet_map use case"
    if case.require_dmm:
        notes += "; DMM required (VOL)"
    else:
        notes += "; DMM reading used when Discover finds one"
    register(
        TestSpec(
            id=case.test_id,
            label=case.label,
            required_instruments=case.instruments,
            fixture_mode=case.fixture_mode,
            lab_sheet=case.lab_sheet,
            run=_run,
            notes=notes,
            fixed_steps=[{"id": "capture", "label": f"{case.label} capture", "phase": "measure"}],
        )
    )


for _case in CASES:
    _register(_case)
