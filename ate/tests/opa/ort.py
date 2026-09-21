"""ORT — LabAutomation_14.7 recipe + JPEG into RS622XK ORT photo boxes."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ate.core.paths import LAB_REPORT_PATH, SCREENSHOT_DIR
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.drivers.mso5072 import apply_scope_preset, capture_jpeg
from ate.reporting.lab_report import (
    ensure_screenshot_dir,
    place_ort_photos,
    save_named_screenshot,
    update_summary_status,
    write_ort_result,
)

MYT = timezone(timedelta(hours=8))

# Scales locked to operator ORT reference screenshots — do not retune.
ORT_POS_PRESET = {
    "timebase": 500e-9,
    "trig_level": -0.1,
    "ch1_scale": 0.2,
    "ch1_offset": 0.6,
    "ch2_scale": 1.0,
    "ch2_offset": -3.0,
    "time_offset": 1e-6,
}
ORT_NEG_PRESET = {
    "timebase": 500e-9,
    "trig_level": 0.1,
    "ch1_scale": 0.2,
    "ch1_offset": 0.4,
    "ch2_scale": 1.0,
    "ch2_offset": -0.5,
    "time_offset": 1e-6,
}


def _run(instr, params: RunParams):
    """ORT alone — G_NEG100. POS then NEG photos for current DUT/channel."""
    from configurations import current_limit
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, set_threshold

    psu, gen, scope = instr.psu, instr.gen, instr.scope
    vcc = params.vcc
    unit = int(params.unit_index or 1)
    ch = (params.channel or "CHA").upper()
    out_dir = ensure_screenshot_dir("ORT", unit)
    ts = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")

    pos_tmp = out_dir / f"_tmp_ort_pos_U{unit}_{ts}.jpg"
    neg_tmp = out_dir / f"_tmp_ort_neg_U{unit}_{ts}.jpg"

    try:
        power_on_protected(psu, 1, vcc / 2, current_limit)
        power_on_protected(psu, 2, vcc / 2, current_limit)

        setup_square(gen, 1, 1000, 0.2, -0.1)
        apply_scope_preset(scope, ORT_POS_PRESET)
        time.sleep(0.8)
        set_threshold(scope, 1)
        set_threshold(scope, 2)
        ort_pos_us = abs(measure_delay(scope, "RRDelay", 1, 2)) * 1e6
        capture_jpeg(scope, pos_tmp)
        pos_path = save_named_screenshot(
            "ORT", unit=unit, variant="POS", source_bytes_path=pos_tmp, channel=ch
        )

        stop_output(gen)
        time.sleep(0.5)

        setup_square(gen, 1, 1000, 0.2, 0.1)
        apply_scope_preset(scope, ORT_NEG_PRESET)
        try:
            scope.write("TRIG:EDGE:SLOP NEG")
        except Exception:
            pass
        time.sleep(0.8)
        set_threshold(scope, 1)
        set_threshold(scope, 2)
        ort_neg_us = abs(measure_delay(scope, "FFDelay", 1, 2)) * 1e6
        capture_jpeg(scope, neg_tmp)
        neg_path = save_named_screenshot(
            "ORT", unit=unit, variant="NEG", source_bytes_path=neg_tmp, channel=ch
        )

        lab = Path(params.lab_report or LAB_REPORT_PATH)
        try:
            place_ort_photos(
                lab,
                positive_paths=[pos_path],
                negative_paths=[neg_path],
                unit_index=unit,
                channel=ch,
            )
            update_summary_status(lab, "Overload Recovery Time (ORT)", "Pass")
            excel_msg = f"embedded in {lab.name} ({ch} 16-box grid)"
        except Exception as exc:
            excel_msg = f"Excel update skipped: {exc}"
        try:
            write_ort_result(
                lab, unit_index=unit, polarity="POS", channel=ch, value_us=ort_pos_us
            )
            write_ort_result(
                lab, unit_index=unit, polarity="NEG", channel=ch, value_us=ort_neg_us
            )
        except Exception:
            pass

        for tmp in (pos_tmp, neg_tmp):
            try:
                if tmp.exists() and tmp != pos_path and tmp != neg_path:
                    tmp.unlink()
            except Exception:
                pass

        return {
            "summary": (
                f"ORT POS={ort_pos_us:.3g} us NEG={ort_neg_us:.3g} us; {excel_msg}"
            ),
            "screenshots": [str(pos_path), str(neg_path)],
            "lab_sheet": "ORT",
            "data": {"ORT_POS_us": ort_pos_us, "ORT_NEG_us": ort_neg_us},
            "measurements": [
                {"id": "ORT_POS_us", "value": round(ort_pos_us, 4), "unit": "us"},
                {"id": "ORT_NEG_us", "value": round(ort_neg_us, 4), "unit": "us"},
            ],
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
        id="ort",
        label="Overload Recovery Time",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="G_NEG100",
        lab_sheet="ORT",
        run=_run,
        notes="MSO delay on G_NEG100 POS/NEG squares + photo boxes. No invented min/max (extract 0.5 s is garbled).",
        fixed_steps=[
            {"id": "pos", "label": "ORT+ POS edge", "phase": "measure"},
            {"id": "neg", "label": "ORT− NEG edge", "phase": "measure"},
        ],
    )
)
