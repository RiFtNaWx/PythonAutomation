"""OpAmp 0.1-10 Hz voltage noise (flicker), not spot density.

Lab Noise sheet is Noise_1_10Hz. Datasheet en (nV/rtHz at 1 kHz) needs an FFT /
analyzer -- this body does not invent that number.

Method: high closed-loop gain, AWG idle, AC-couple VOUT, 1 s/div (~10 s window),
measure Vpp, refer to input as Vn_pp / |gain|. Shield + linear PSU. Continue
gate; never input().
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from ate.core.paths import LAB_REPORT_PATH, PARTS_DIR
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.drivers.mso5072 import capture_jpeg
from ate.reporting.lab_report import (
    ensure_screenshot_dir,
    place_mapped_photos,
    save_named_screenshot,
)
from ate.reporting.photo_layout import photos_map

MYT = timezone(timedelta(hours=8))
FOLDER = "Noise_1_10Hz"
LAB_SHEET = "Noise"


def input_referred_uvpp(vout_pp_v: float, gain: float) -> float:
    """Output Vpp (volts) / |gain| -> input-referred uVpp."""
    g = abs(float(gain))
    if g < 1e-9:
        g = 1.0
    return (float(vout_pp_v) / g) * 1e6


def _part_noise_cfg(part_key: str) -> dict[str, Any]:
    pk = str(part_key or "rs622").strip().lower()
    path = PARTS_DIR / f"{pk}.yaml"
    if not path.is_file():
        return {}
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    block = data.get("noise") if isinstance(data, dict) else None
    return dict(block) if isinstance(block, dict) else {}


def _gain(params: RunParams, cfg: dict[str, Any]) -> float:
    g = float(params.gain or 0.0)
    if abs(g) >= 2.0:
        return g
    raw = cfg.get("gain")
    if raw not in (None, ""):
        return float(raw)
    return 1001.0


def _emit(params: RunParams, step_id: str, status: str, message: str) -> None:
    hook: Optional[Callable[..., None]] = getattr(params, "progress_hook", None)
    if hook:
        hook(step_id, status, message)


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _setup_scope(scope, *, timebase_s: float, vdiv: float, ch: int) -> None:
    """Slow window, AC couple. Do not AUToscale (hunts on noise)."""
    scope.write(":RUN")
    scope.write(f":TIMebase:MAIN:SCAle {float(timebase_s)}")
    scope.write(":TRIGger:MODE EDGE")
    scope.write(":TRIGger:SWEEp AUTO")
    scope.write(f":TRIGger:EDGE:SOURce CHAN{int(ch)}")
    scope.write(":TRIGger:EDGE:LEVel 0")
    scope.write(f":CHAN{int(ch)}:DISP ON")
    scope.write(f":CHAN{int(ch)}:COUPling AC")
    scope.write(f":CHAN{int(ch)}:SCALe {float(vdiv)}")
    scope.write(f":CHAN{int(ch)}:OFFSet 0")
    time.sleep(0.3)


def _read_vpp(scope, ch: int, wait_s: float) -> float:
    scope.write(":MEASure:CLEar ALL")
    scope.write(f":MEASure:ITEM VPP,CHAN{int(ch)}")
    try:
        scope.write(f":MEASure:STATistic:ITEM VPP,CHAN{int(ch)}")
        scope.write(":MEASure:STATistic:DISPlay ON")
    except Exception:
        pass
    time.sleep(max(1.0, float(wait_s)))
    try:
        raw = scope.query(
            f":MEASure:STATistic:ITEM? AVERages,VPP,CHAN{int(ch)}"
        ).strip()
        val = float(raw)
        if val == val and val > 0:
            return val
    except Exception:
        pass
    from scope_setup import measure_single

    return float(measure_single(scope, "VPP", int(ch)))


def _capture(scope, unit: int, channel: str) -> Path:
    out_dir = ensure_screenshot_dir(FOLDER, unit)
    ts = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")
    tmp = out_dir / f"_tmp_noise_U{unit}_{ts}.jpg"
    capture_jpeg(scope, tmp)
    path = save_named_screenshot(
        FOLDER, unit=unit, variant="FLICKER", source_bytes_path=tmp, channel=channel
    )
    try:
        if tmp.exists() and tmp != path:
            tmp.unlink()
    except Exception:
        pass
    return path


def _try_paste(shot: Path | None, unit: int, channel: str) -> str:
    if shot is None:
        return "no photo"
    try:
        photos_map(FOLDER)
    except KeyError:
        return "no paste.photos"
    try:
        place_mapped_photos(
            Path(LAB_REPORT_PATH),
            test_key=FOLDER,
            photo_path=shot,
            unit_index=unit,
            channel=channel,
        )
        return f"pasted {shot.name}"
    except Exception as exc:
        return f"Excel skipped: {exc}"


def _run(instr, params: RunParams) -> dict[str, Any]:
    from configurations import current_limit
    from generator_setup import stop_output
    from psu_setup import power_off, power_on_protected

    cfg = _part_noise_cfg(params.part)
    gain = _gain(params, cfg)
    timebase_s = float(cfg.get("timebase_s") or 1.0)
    vdiv = float(cfg.get("vdiv") or 0.05)
    out_ch = int(cfg.get("out_channel") or 2)
    wait_s = max(8.0, timebase_s * 10.0)
    unit = int(params.unit_index or 1)
    channel = (params.channel or "CHA").upper()
    psu, gen, scope = instr.psu, getattr(instr, "gen", None), getattr(instr, "scope", None)

    _emit(params, "capture", "running", f"Noise 0.1-10Hz DUT_{unit} {channel}")
    ok = _pause(
        params,
        "Noise 0.1-10 Hz | high-gain DUT (typ G=1001) | shield + unused inputs shorted | "
        "AWG off | AC-couple VOUT | wait one full 10 s sweep then Continue. "
        "This is Vpp/gain, not nV/rtHz.",
    )
    if not ok:
        return {"summary": "Noise aborted at Continue", "lab_sheet": LAB_SHEET}

    try:
        if psu is not None:
            power_on_protected(psu, 1, params.vcc / 2, current_limit)
            try:
                power_on_protected(psu, 2, params.vcc / 2, current_limit)
            except Exception:
                pass
        if gen is not None:
            try:
                stop_output(gen)
            except Exception:
                pass
        vout_pp = None
        shot = None
        if scope is not None:
            _setup_scope(scope, timebase_s=timebase_s, vdiv=vdiv, ch=out_ch)
            try:
                vout_pp = _read_vpp(scope, out_ch, wait_s)
            except Exception as exc:
                _emit(params, "capture", "running", f"Vpp read failed: {exc}")
            shot = _capture(scope, unit, channel)
        excel_msg = _try_paste(shot, unit, channel)
        meas: list[dict[str, Any]] = [{"id": "NOISE_GAIN", "value": gain, "unit": ""}]
        vn_in = None
        if vout_pp is not None and vout_pp == vout_pp and vout_pp > 0:
            vn_in = input_referred_uvpp(vout_pp, gain)
            meas.append({"id": "VN_OUT_PP_mV", "value": vout_pp * 1000.0, "unit": "mV"})
            meas.append({"id": "VN_IN_PP_uV", "value": vn_in, "unit": "uV"})
        bits = [excel_msg]
        if vn_in is not None:
            bits.insert(0, f"Vn_in={vn_in:.3g} uVpp (G={gain:g})")
        elif vout_pp is None:
            bits.insert(0, "no Vpp (photo only)")
        if shot:
            bits.append(shot.name)
        out: dict[str, Any] = {
            "summary": "Noise 0.1-10Hz: " + "; ".join(b for b in bits if b),
            "lab_sheet": LAB_SHEET,
            "measurements": meas,
            "gain": gain,
        }
        if shot:
            out["screenshots"] = [str(shot)]
        if vn_in is not None:
            out["VN_IN_PP_uV"] = vn_in
        return out
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


register(
    TestSpec(
        id="noise",
        label="Noise 0.1-10 Hz",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="ATE",
        lab_sheet=LAB_SHEET,
        run=_run,
        notes=(
            "0.1-10 Hz input-referred Vpp (Vout_pp / |gain|). "
            "RS622 datasheet en is 11 nV/rtHz at 1 kHz -- spectrum, not this capture. "
            "Set Conditions gain if the board is not G=1001."
        ),
        fixed_steps=[
            {"id": "capture", "label": "0.1-10 Hz Vpp capture", "phase": "measure"}
        ],
    )
)
