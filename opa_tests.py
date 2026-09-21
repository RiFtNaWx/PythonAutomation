#Testing VSC and GitHub integration with this line of code. Please ignore.

# opa_tests.py
# Operational Amplifier (OPA) test procedures
# Tests for GBW (Gain-Bandwidth Product) and SR (Slew Rate)

def test_parameter():
    """Return the user-defined test configuration array.

    This function defines the available test names, parameter lists, and details.
    Parameters are only written to the datalog when their corresponding test is actually executed.
    """
    
    return [
        {
            "test_name": "OPA_RS622_Test",
            "parameters": ["IN+"],
            "details": "OPA Parameter tests"
        },
        # Add additional test configurations as needed
        # {
        #     "test_name": "Another_Test",
        #     "parameters": ["PARAM1", "PARAM2"],
        #     "details": "Description of another test"
        # }
    ]

TEST_CONFIGURATIONS = test_parameter()


from dmm_setup import *
from generator_setup import *
from psu_setup import *
from scope_setup import *
from configurations import *
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from openpyxl import Workbook, load_workbook
from datalog import DataLogger
from utils import initial_time, final_time

DEFAULT_VOS_EXCEL_PATH = r"C:\Users\OoiJianHong\Downloads\VOS Research.xlsx"
MYT = timezone(timedelta(hours=8))

# =========================
# Debug configuration
# =========================
# Option A: hardcode
DEBUG_MODE = True # Set to True to enable debug prints, False to disable

# Option B: override by environment variable:
#   Windows PowerShell:  $env:OPA_DEBUG="1"
#   cmd.exe:             set OPA_DEBUG=1
#   bash:                export OPA_DEBUG=1
DEBUG_MODE = os.getenv("OPA_DEBUG", "0").strip().lower() in ("1", "true", "yes", "y", "on")

def dbg(msg: str, *, enabled: bool = None): # type: ignore
    """Lightweight debug print with consistent prefix + timestamp."""
    use = DEBUG_MODE if enabled is None else enabled
    if use:
        ts = time.strftime("%H:%M:%S")
        print(f"[OPA-DEBUG {ts}] {msg}")

def safe_write(instr, cmd: str, label: str = "WRITE"):
    """Write SCPI and print it if debug is enabled."""
    dbg(f"{label}: {cmd}")
    return instr.write(cmd)

def safe_query(instr, cmd: str, label: str = "QUERY"):
    """Query SCPI and print cmd + raw response if debug is enabled."""
    dbg(f"{label}: {cmd}")
    resp = instr.query(cmd)
    dbg(f"{label}-RESP: {resp!r}")
    return resp

def safe_float(x, *, context: str = ""):
    """Convert to float with debug info on failure."""
    try:
        return float(x)
    except Exception as e:
        dbg(f"FLOAT-CONVERT FAIL {context}: value={x!r}, err={e}")
        raise


def _build_vin_sweep_mV(vin_range_mV=(-5, 5), step_mV=0.1):
    """Build Vin sweep in mV using integer 0.1 mV steps to avoid float drift."""
    lo_step = int(round(vin_range_mV[0] / step_mV))
    hi_step = int(round(vin_range_mV[1] / step_mV))
    return [i * step_mV for i in range(lo_step, hi_step + 1)]


def _scope_setup_dc_static(scope, chan_scale, time_scale, trig_level=0.0):
    """Configure scope vertical scale and timebase once — no :AUToscale."""
    scope.write(f":CHAN1:SCAL {chan_scale}")
    scope.write(f":CHAN1:OFFS 0")
    scope.write(f":TIM:SCAL {time_scale}")
    scope.write(":TRIGger:SWEep AUTO")
    scope.write(":TRIGger:MODE EDGE")
    scope.write(":TRIGger:EDGE:SLOPe POSitive")
    scope.write(":TRIGger:EDGE:SOURce CHAN1")
    scope.write(f":TRIGger:EDGE:LEVel {trig_level}")
    scope.write(":SYSTem:KEY:PRESs MOFF")
    time.sleep(0.5)


def _linear_fit(xs, ys):
    """Least-squares fit y = m*x + b; returns (slope, intercept, r_squared)."""
    n = len(xs)
    if n < 2:
        raise ValueError("Need at least 2 points for linear fit")
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        raise ValueError("Cannot fit line: zero variance in Vin")
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot else float("nan")
    return slope, intercept, r_squared


def _query_scope_meas(scope, item, ch, timeout_ms=5000):
    """Read a single :MEAS:ITEM? value from the scope (bounded VISA timeout)."""
    last_exc: Exception | None = None
    old_to = getattr(scope, "timeout", 5000)
    for attempt in range(2):
        try:
            scope.timeout = int(timeout_ms)
            scope.write(f":MEAS:ITEM {item},CHAN{ch}")
            return float(scope.query(f":MEAS:ITEM? {item},CHAN{ch}"))
        except Exception as exc:
            last_exc = exc
            if attempt == 0:
                try:
                    park_scope_idle(scope, clear=True)
                except Exception:
                    recover_scope_session(scope, run=True)
                time.sleep(0.25)
        finally:
            try:
                scope.timeout = old_to
            except Exception:
                pass
    raise last_exc  # type: ignore[misc]


def _get_or_create_sheet(wb, sheet_name):
    if sheet_name in wb.sheetnames:
        return wb[sheet_name]
    return wb.create_sheet(sheet_name)


def _write_vos_sweep_excel(
    rows,
    excel_path,
    *,
    sheet_name="vos sweep",
    analysis_sheet_name="vos analysis",
    data_start_row=20,
    test_name="VOS DC Sweep",
    vcc=5.0,
    gain=201.0,
    vin_range_mV=(-5, 5),
    step_mV=0.1,
    fit=None,
):
    """Write sweep data and analysis to Excel; preserve rows above data_start_row."""
    path = Path(excel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header_row = data_start_row
    first_data_row = data_start_row + 1
    timestamp_myt = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S MYT (UTC+8)")

    try:
        if path.exists():
            wb = load_workbook(path)
        else:
            wb = Workbook()
            wb.active.title = sheet_name

        ws = _get_or_create_sheet(wb, sheet_name)
        ws.cell(header_row, 1, "Vin_mV")
        ws.cell(header_row, 2, "Vmax_V")
        ws.cell(header_row, 3, "Vavg_V")
        ws.cell(header_row, 4, "Vpp_V")
        for i, row in enumerate(rows):
            r = first_data_row + i
            ws.cell(r, 1, row["Vin_mV"])
            ws.cell(r, 2, row["Vmax_V"])
            ws.cell(r, 3, row["Vavg_V"])
            ws.cell(r, 4, row["Vpp_V"])

        ws_analysis = _get_or_create_sheet(wb, analysis_sheet_name)
        meta = [
            ("Test", test_name),
            ("Date/Time", timestamp_myt),
            ("Sheet (data)", sheet_name),
            ("VCC (V)", vcc),
            ("Assumed gain", gain),
            ("Vin range (mV)", f"{vin_range_mV[0]} to {vin_range_mV[1]}"),
            ("Vin step (mV)", step_mV),
            ("Data header row", header_row),
            ("Sweep points", len(rows)),
        ]
        for i, (label, value) in enumerate(meta, start=1):
            ws_analysis.cell(i, 1, label)
            ws_analysis.cell(i, 2, value)

        if fit:
            base = len(meta) + 2
            ws_analysis.cell(base, 1, "Linear fit: Vavg_V = slope * Vin_V + intercept")
            ws_analysis.cell(base + 1, 1, "Measured slope (V/V)")
            ws_analysis.cell(base + 1, 2, fit["slope"])
            ws_analysis.cell(base + 2, 1, "Intercept (V)")
            ws_analysis.cell(base + 2, 2, fit["intercept"])
            ws_analysis.cell(base + 3, 1, "R-squared")
            ws_analysis.cell(base + 3, 2, fit["r_squared"])
            ws_analysis.cell(base + 4, 1, "VOS estimate (mV)")
            ws_analysis.cell(base + 4, 2, fit["vos_mV"])
            ws_analysis.cell(base + 5, 1, "VOS formula")
            ws_analysis.cell(base + 5, 2, "-intercept / slope * 1000")

        wb.save(path)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write to '{excel_path}' — close the file in Excel (or any "
            f"other program holding it open) and retry."
        ) from exc


def test_vos_sweep(
    instr,
    vcc=5.0,
    vin_range_mV=(-5, 5),
    step_mV=0.1,
    settle_s=0.3,
    excel_path=DEFAULT_VOS_EXCEL_PATH,
    sheet_name="vos sweep",
    analysis_sheet_name="vos analysis",
    data_start_row=20,
    gain=201.0,
    test_name="VOS DC Sweep",
):
    """Sweep DG822 G1 DC output while recording MSO5072 CHAN1 Vmax/Vavg/Vpp.

    PSU: CH1 and CH2 both commanded to +VCC/2 (2.5 V at vcc=5). The negative
    rail (VSS) is a wiring convention — CH2 + tied to GND, CH2 − is VSS.
    OVP = Vset + 0.3 V, OCP = Iset + 0.1 A on top of current_limit.

    Not wired into main.py — call standalone after bench sign-off.
    """
    psu = instr.psu
    gen = instr.gen
    scope = instr.scope

    vin_mV = _build_vin_sweep_mV(vin_range_mV, step_mV)
    vin_v_preview = [m / 1000.0 for m in vin_mV]
    print(f"Vin sweep (V), first 5: {vin_v_preview[:5]}")
    print(f"Vin sweep (V), last 5:  {vin_v_preview[-5:]}")
    print(f"Total sweep points: {len(vin_mV)}")

    vcc_half = vcc / 2
    # OVP/OCP: margin above setpoint. Both rails commanded positive magnitude.
    ovp_margin_v = 0.3
    ocp_margin_a = 0.1
    ocp_trip = current_limit + ocp_margin_a
    ovp_trip = vcc_half + ovp_margin_v

    max_vout_v = abs(vin_range_mV[1]) * gain * 1e-3
    chan_scale = max(0.02, max_vout_v / 3)
    time_scale = 10e-3

    rows = []
    try:
        power_on_protected(
            psu, 1, vcc_half, current_limit,
            ovp=ovp_trip, ocp=ocp_trip,
        )
        power_on_protected(
            psu, 2, vcc_half, current_limit,
            ovp=ovp_trip, ocp=ocp_trip,
        )
        time.sleep(1)

        set_output_load(gen, 1, "INF")
        _scope_setup_dc_static(scope, chan_scale, time_scale, trig_level=0.0)

        for idx, vin_mv in enumerate(vin_mV):
            vin_v = vin_mv / 1000.0
            if idx == 0:
                # setup_dc changes AWG mode; needs extra settle + throwaway read
                setup_dc(gen, 1, vin_v)
                enable_output(gen, 1)
                time.sleep(settle_s + 0.75)
                _query_scope_meas(scope, "VMAX", 1)
                _query_scope_meas(scope, "VAVG", 1)
                _query_scope_meas(scope, "VPP", 1)
            else:
                set_offset(gen, 1, vin_v)
                enable_output(gen, 1)
                time.sleep(settle_s)

            vmax = _query_scope_meas(scope, "VMAX", 1)
            vavg = _query_scope_meas(scope, "VAVG", 1)
            vpp = _query_scope_meas(scope, "VPP", 1)
            rows.append({
                "Vin_mV": vin_mv,
                "Vmax_V": vmax,
                "Vavg_V": vavg,
                "Vpp_V": vpp,
            })
            dbg(f"VOS step {idx + 1}/{len(vin_mV)} Vin={vin_mv} mV "
                f"Vmax={vmax:.6f} Vavg={vavg:.6f} Vpp={vpp:.6f}")

        vin_v = [row["Vin_mV"] / 1000.0 for row in rows]
        vavg_v = [row["Vavg_V"] for row in rows]
        slope, intercept, r_squared = _linear_fit(vin_v, vavg_v)
        vos_mV = (-intercept / slope * 1000.0) if slope else float("nan")
        fit = {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "vos_mV": vos_mV,
        }
        print(
            f"Linear fit: slope={slope:.4f} V/V, intercept={intercept:.6f} V, "
            f"R2={r_squared:.6f}, VOS~{vos_mV:.4f} mV"
        )

        _write_vos_sweep_excel(
            rows,
            excel_path,
            sheet_name=sheet_name,
            analysis_sheet_name=analysis_sheet_name,
            data_start_row=data_start_row,
            test_name=test_name,
            vcc=vcc,
            gain=gain,
            vin_range_mV=vin_range_mV,
            step_mV=step_mV,
            fit=fit,
        )
        print(
            f"VOS sweep complete -- {len(rows)} rows written to '{sheet_name}' "
            f"in {excel_path}"
        )
        return {"rows": rows, "fit": fit}

    finally:
        try:
            stop_output(gen)
        except Exception:
            pass
        try:
            power_off(psu)
        except Exception:
            pass


def _scope_setup_ac_gain(scope, ch1_scale, ch2_scale, time_scale, trig_level=0.0):
    """Fixed CH1/CH2 scales + timebase for AC gain — no :AUToscale."""
    scope.write(":CHAN1:DISP ON")
    scope.write(":CHAN1:COUP DC")
    scope.write(f":CHAN1:SCAL {ch1_scale}")
    scope.write(":CHAN1:OFFS 0")
    scope.write(":CHAN2:DISP ON")
    scope.write(":CHAN2:COUP DC")
    scope.write(f":CHAN2:SCAL {ch2_scale}")
    scope.write(":CHAN2:OFFS 0")
    scope.write(f":TIM:SCAL {time_scale}")
    scope.write(":TRIGger:SWEep AUTO")
    scope.write(":TRIGger:MODE EDGE")
    scope.write(":TRIGger:EDGE:SLOPe POSitive")
    # Trigger on CH1 (larger OutB) — CH2 node is mV-class and may not trigger cleanly
    scope.write(":TRIGger:EDGE:SOURce CHAN1")
    scope.write(f":TRIGger:EDGE:LEVel {trig_level}")
    scope.write(":SYSTem:KEY:PRESs MOFF")
    time.sleep(0.5)


def _is_valid_scope_meas(value):
    """Reject Rigol invalid/overflow tokens (~9.9e37) and NaN."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    return abs(v) < 1e20 and v == v


def _avg_scope_meas(scope, item, ch, n_avg):
    """Average n_avg valid :MEAS:ITEM? readings; return NaN if all invalid."""
    vals = []
    for _ in range(n_avg):
        v = _query_scope_meas(scope, item, ch)
        if _is_valid_scope_meas(v):
            vals.append(v)
        else:
            dbg(f"Invalid scope meas {item} CHAN{ch}: {v!r}")
    if not vals:
        return float("nan")
    return sum(vals) / len(vals)


def _write_ac_gain_excel(
    excel_path,
    *,
    freq_hz,
    amp_vpp_commanded,
    vpp_ch1,
    vpp_ch2,
    gain_vs_commanded,
    loop_ok,
    junction_limit_vpp,
    vcc,
    sheet_name="ac gain check",
):
    """Append one AC gain result row; do not touch vos sweep / analysis sheets."""
    path = Path(excel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp_myt = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S MYT (UTC+8)")
    headers = [
        "timestamp_MYT",
        "vcc_V",
        "freq_hz",
        "amp_vpp_commanded",
        "vpp_ch1_measured",
        "vpp_ch2_junction",
        "gain_vs_commanded",
        "loop_health_ok",
        "junction_limit_vpp",
    ]
    row = [
        timestamp_myt,
        vcc,
        freq_hz,
        amp_vpp_commanded,
        vpp_ch1,
        vpp_ch2,
        gain_vs_commanded,
        loop_ok,
        junction_limit_vpp,
    ]

    try:
        if path.exists():
            wb = load_workbook(path)
        else:
            wb = Workbook()
            wb.active.title = sheet_name

        ws = _get_or_create_sheet(wb, sheet_name)
        if ws.max_row < 1 or ws.cell(1, 1).value is None:
            for col, h in enumerate(headers, start=1):
                ws.cell(1, col, h)
            next_row = 2
        else:
            next_row = ws.max_row + 1
        for col, val in enumerate(row, start=1):
            ws.cell(next_row, col, val)
        wb.save(path)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write to '{excel_path}' — close the file in Excel (or any "
            f"other program holding it open) and retry."
        ) from exc


def test_ac_gain_check(
    instr,
    vcc=5.0,
    freq_hz=500.0,
    amp_vpp=0.004,
    settle_s=1.0,
    n_avg=5,
    excel_path=DEFAULT_VOS_EXCEL_PATH,
    sheet_name="ac gain check",
    gain_nominal=201.0,
    junction_vpp_limit=0.001,
):
    """AC sine closed-loop gain + virtual-ground health check.

    Wiring: CH1=OutB, CH2=R2/R4 summing junction (virtual ground).

    Trustworthy gain: gain_vs_commanded = Vpp_CH1 / amp_vpp_commanded.
    Do NOT use CH1/CH2 as gain — junction should be near zero (~Vout/A_OL).

    CH2 is a health check only: warn if Vpp_CH2 > junction_vpp_limit (1 mV).
    High junction Vpp usually means OutB pickup, wrong side of R4, or loop not nulling.
    """
    psu = instr.psu
    gen = instr.gen
    scope = instr.scope

    vcc_half = vcc / 2
    ovp_margin_v = 0.3
    ocp_margin_a = 0.1
    ocp_trip = current_limit + ocp_margin_a
    ovp_trip = vcc_half + ovp_margin_v

    time_scale = (1.0 / freq_hz) * 4.0 / 10.0
    ch1_scale = max(0.02, (amp_vpp * gain_nominal) / 3.0)
    ch2_scale = max(0.005, amp_vpp)

    try:
        power_on_protected(
            psu, 1, vcc_half, current_limit,
            ovp=ovp_trip, ocp=ocp_trip,
        )
        power_on_protected(
            psu, 2, vcc_half, current_limit,
            ovp=ovp_trip, ocp=ocp_trip,
        )
        time.sleep(1)

        set_output_load(gen, 1, "INF")
        print(
            "NOTE: OUTP:LOAD=INF. Primary gain = CH1/amp_cmd. "
            "CH2 is virtual-ground health only (not a gain denominator)."
        )

        _scope_setup_ac_gain(scope, ch1_scale, ch2_scale, time_scale, trig_level=0.0)
        setup_sine(gen, 1, freq_hz, amp_vpp, 0)
        time.sleep(settle_s)

        vpp_ch1 = _avg_scope_meas(scope, "VPP", 1, n_avg)
        vpp_ch2 = _avg_scope_meas(scope, "VPP", 2, n_avg)

        gain_vs_commanded = (vpp_ch1 / amp_vpp) if (
            _is_valid_scope_meas(vpp_ch1) and amp_vpp
        ) else float("nan")

        ch2_ok = _is_valid_scope_meas(vpp_ch2)
        loop_ok = bool(ch2_ok and vpp_ch2 <= junction_vpp_limit)
        if not ch2_ok:
            print(
                "WARNING: CH2 Vpp invalid (overflow / channel off). "
                "Cannot judge loop health."
            )
        elif not loop_ok:
            print(
                f"WARNING: junction Vpp={vpp_ch2 * 1000:.3f} mV exceeds "
                f"{junction_vpp_limit * 1000:.3f} mV limit — likely OutB "
                f"pickup, wrong side of R4, or loop not nulling. "
                f"Do NOT use CH1/CH2 as gain."
            )
        else:
            print(
                f"Loop health OK: junction Vpp={vpp_ch2 * 1000:.3f} mV "
                f"<= {junction_vpp_limit * 1000:.3f} mV"
            )

        print(
            f"\\n=== AC GAIN CHECK ===\\n"
            f"freq={freq_hz} Hz  amp_cmd={amp_vpp * 1000:.3f} mVpp\\n"
            f"Vpp_CH1(OutB)={vpp_ch1:.6f} V\\n"
            f"Vpp_CH2(junction/VG)={vpp_ch2:.6f} V  "
            f"health={'OK' if loop_ok else 'FAIL/CHECK'}\\n"
            f"gain_vs_commanded (CH1/amp_cmd)={gain_vs_commanded:.4f} V/V\\n"
            f"(nominal gain~={gain_nominal:.1f})\\n"
        )

        _write_ac_gain_excel(
            excel_path,
            sheet_name=sheet_name,
            freq_hz=freq_hz,
            amp_vpp_commanded=amp_vpp,
            vpp_ch1=vpp_ch1,
            vpp_ch2=vpp_ch2,
            gain_vs_commanded=gain_vs_commanded,
            loop_ok=loop_ok,
            junction_limit_vpp=junction_vpp_limit,
            vcc=vcc,
        )
        print(f"AC gain row written to '{sheet_name}' in {excel_path}")
        return {
            "freq_hz": freq_hz,
            "amp_vpp_commanded": amp_vpp,
            "vpp_ch1": vpp_ch1,
            "vpp_ch2": vpp_ch2,
            "gain_vs_commanded": gain_vs_commanded,
            "loop_ok": loop_ok,
            "junction_vpp_limit": junction_vpp_limit,
            "gain_measured": float("nan"),
        }

    finally:
        try:
            stop_output(gen)
        except Exception:
            pass
        try:
            power_off(psu)
        except Exception:
            pass


AC_VIN_SUMMARY_SHEET = "ac vin summary"
AC_VIN_DATA_START_ROW = 20


def _ac_vin_repeat_sheet_name(repeat: int) -> str:
    ts = datetime.now(MYT).strftime("%Y-%m-%d %H%M%S")
    return f"ac vin R{repeat:02d} {ts}"


def _write_ac_vin_repeat_sheet(
    rows,
    excel_path,
    *,
    sheet_name,
    data_start_row=AC_VIN_DATA_START_ROW,
):
    """Write one AC Vin sweep repeat to its own data sheet."""
    path = Path(excel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header_row = data_start_row
    first_data_row = data_start_row + 1

    try:
        if path.exists():
            wb = load_workbook(path)
        else:
            wb = Workbook()
            wb.active.title = sheet_name

        ws = _get_or_create_sheet(wb, sheet_name)
        ws.cell(header_row, 1, "Vin_mV")
        ws.cell(header_row, 2, "Vavg_ch1")
        ws.cell(header_row, 3, "Vpp_ch1")
        ws.cell(header_row, 4, "Vpp_ch2")
        for i, row in enumerate(rows):
            r = first_data_row + i
            ws.cell(r, 1, row["Vin_mV"])
            ws.cell(r, 2, row["Vavg_ch1"])
            ws.cell(r, 3, row["Vpp_ch1"])
            ws.cell(r, 4, row["Vpp_ch2"])
        wb.save(path)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write to '{excel_path}' — close the file in Excel (or any "
            f"other program holding it open) and retry."
        ) from exc


def _embed_screenshot_in_sheet(ws, image_path, *, anchor_cell: str, max_width=480):
    """Embed a JPEG/PNG into an openpyxl worksheet (scaled to max_width)."""
    from openpyxl.drawing.image import Image as XLImage

    img_path = Path(image_path)
    if not img_path.is_file():
        return
    xl_img = XLImage(str(img_path))
    if xl_img.width and xl_img.width > max_width:
        scale = max_width / float(xl_img.width)
        xl_img.width = int(xl_img.width * scale)
        xl_img.height = int(xl_img.height * scale)
    ws.add_image(xl_img, anchor_cell)


def _append_ac_vin_summary_row(
    excel_path,
    *,
    summary_row: dict,
    summary_sheet_name=AC_VIN_SUMMARY_SHEET,
):
    """Append one repeat summary row to the fixed AC Vin summary sheet."""
    path = Path(excel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "timestamp_MYT",
        "repeat",
        "vcc",
        "freq_hz",
        "amp_vpp",
        "fit_slope",
        "fit_intercept",
        "fit_R2",
        "vos_mV",
        "gain_vs_commanded_mean",
        "junction_Vpp_max_mV",
        "loop_ok",
        "data_sheet",
        "screenshot_path",
        "screenshot",
    ]
    row = [summary_row.get(h, "") for h in headers]

    try:
        if path.exists():
            wb = load_workbook(path)
        else:
            wb = Workbook()
            wb.active.title = summary_sheet_name

        ws = _get_or_create_sheet(wb, summary_sheet_name)
        if ws.max_row < 1 or ws.cell(1, 1).value is None:
            for col, h in enumerate(headers, start=1):
                ws.cell(1, col, h)
            next_row = 2
        else:
            next_row = ws.max_row + 1
        for col, val in enumerate(row, start=1):
            # Column 15 ("screenshot") holds the embedded image, not a text value
            if headers[col - 1] == "screenshot":
                continue
            ws.cell(next_row, col, val)

        shot = summary_row.get("screenshot_path") or ""
        if shot:
            try:
                _embed_screenshot_in_sheet(ws, shot, anchor_cell=f"O{next_row}")
                ws.row_dimensions[next_row].height = 120
                ws.column_dimensions["O"].width = 40
            except Exception as exc:
                print(f"WARNING: could not embed screenshot in Excel: {exc}")

        wb.save(path)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write to '{excel_path}' — close the file in Excel (or any "
            f"other program holding it open) and retry."
        ) from exc


def _maybe_capture_scope_png(scope, filepath):
    """Call capture_scope_png if available; return path string or None."""
    try:
        from scope_setup import capture_scope_png
        return capture_scope_png(scope, filepath)
    except ImportError:
        return None


def test_ac_vin_sweep(
    instr,
    vcc=5.0,
    vin_range_mV=(-5, 5),
    step_mV=0.1,
    freq_hz=500.0,
    amp_vpp=0.004,
    settle_s=1.0,
    n_repeats=3,
    excel_path=DEFAULT_VOS_EXCEL_PATH,
    gain=201.0,
    junction_vpp_limit=0.001,
    data_start_row=AC_VIN_DATA_START_ROW,
    logger=None,
):
    """AC Vin sweep: sine stimulus at each DC offset, multi-repeat with Excel + optional datalog.

    At each Vin: DG822 CH1 sine (freq_hz, amp_vpp) with DC offset = Vin.
    CH1 = OutB (Vavg + Vpp); CH2 = virtual-ground junction (Vpp health only).
    Linear fit Vavg_CH1 vs Vin_V yields VOS; mean(Vpp_CH1/amp_vpp) estimates closed-loop gain.
    """
    psu = instr.psu
    gen = instr.gen
    scope = instr.scope

    vin_mV = _build_vin_sweep_mV(vin_range_mV, step_mV)
    print(f"AC Vin sweep: {len(vin_mV)} points, {n_repeats} repeat(s)")
    print(f"  Vin range: {vin_range_mV[0]} to {vin_range_mV[1]} mV, step {step_mV} mV")
    print(f"  AC: {freq_hz} Hz, {amp_vpp * 1000:.3f} mVpp")

    vcc_half = vcc / 2
    ovp_margin_v = 0.3
    ocp_margin_a = 0.1
    ocp_trip = current_limit + ocp_margin_a
    ovp_trip = vcc_half + ovp_margin_v

    time_scale = (1.0 / freq_hz) * 4.0 / 10.0
    max_dc_out = abs(vin_range_mV[1]) * gain * 1e-3
    max_ac_out = amp_vpp * gain
    ch1_scale = max(0.02, (max_dc_out + max_ac_out) / 3.0)
    ch2_scale = max(0.005, amp_vpp)

    screenshot_dir = Path("oscilloscope_screenshots")
    repeats_out = []

    try:
        power_on_protected(
            psu, 1, vcc_half, current_limit,
            ovp=ovp_trip, ocp=ocp_trip,
        )
        power_on_protected(
            psu, 2, vcc_half, current_limit,
            ovp=ovp_trip, ocp=ocp_trip,
        )
        time.sleep(1)

        set_output_load(gen, 1, "INF")
        _scope_setup_ac_gain(scope, ch1_scale, ch2_scale, time_scale, trig_level=0.0)

        for rep in range(1, n_repeats + 1):
            sheet_name = _ac_vin_repeat_sheet_name(rep)
            rows = []
            gain_ratios = []
            junction_vpp_vals = []

            print(f"\n--- AC Vin sweep repeat {rep}/{n_repeats} -- sheet '{sheet_name}' ---")

            for idx, vin_mv in enumerate(vin_mV):
                vin_v = vin_mv / 1000.0
                if idx == 0:
                    setup_sine(gen, 1, freq_hz, amp_vpp, vin_v)
                    time.sleep(settle_s + 0.75)
                    _query_scope_meas(scope, "VAVG", 1)
                    _query_scope_meas(scope, "VPP", 1)
                    _query_scope_meas(scope, "VPP", 2)
                else:
                    set_offset(gen, 1, vin_v)
                    time.sleep(settle_s)

                vavg = _query_scope_meas(scope, "VAVG", 1)
                vpp_ch1 = _query_scope_meas(scope, "VPP", 1)
                vpp_ch2 = _query_scope_meas(scope, "VPP", 2)

                rows.append({
                    "Vin_mV": vin_mv,
                    "Vavg_ch1": vavg,
                    "Vpp_ch1": vpp_ch1,
                    "Vpp_ch2": vpp_ch2,
                })

                if _is_valid_scope_meas(vpp_ch1) and amp_vpp:
                    gain_ratios.append(vpp_ch1 / amp_vpp)
                if _is_valid_scope_meas(vpp_ch2):
                    junction_vpp_vals.append(vpp_ch2)

                dbg(
                    f"AC Vin R{rep} step {idx + 1}/{len(vin_mV)} "
                    f"Vin={vin_mv} mV Vavg={vavg:.6f} Vpp1={vpp_ch1:.6f} Vpp2={vpp_ch2:.6f}"
                )

            vin_v_fit = [row["Vin_mV"] / 1000.0 for row in rows]
            vavg_fit = [row["Vavg_ch1"] for row in rows]
            slope, intercept, r_squared = _linear_fit(vin_v_fit, vavg_fit)
            vos_mV = (-intercept / slope * 1000.0) if slope else float("nan")
            fit = {
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "vos_mV": vos_mV,
            }

            gain_vs_commanded_mean = (
                sum(gain_ratios) / len(gain_ratios) if gain_ratios else float("nan")
            )
            junction_vpp_max = max(junction_vpp_vals) if junction_vpp_vals else float("nan")
            loop_ok = bool(
                junction_vpp_vals
                and junction_vpp_max <= junction_vpp_limit
            )

            print(
                f"  fit: slope={slope:.4f} V/V, intercept={intercept:.6f} V, "
                f"R2={r_squared:.6f}, VOS~{vos_mV:.4f} mV"
            )
            print(
                f"  gain_vs_commanded_mean={gain_vs_commanded_mean:.4f}, "
                f"junction_Vpp_max={junction_vpp_max * 1000:.3f} mV, "
                f"loop_ok={loop_ok}"
            )

            _write_ac_vin_repeat_sheet(
                rows,
                excel_path,
                sheet_name=sheet_name,
                data_start_row=data_start_row,
            )

            ts_screenshot = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")
            screenshot_path = screenshot_dir / f"ac_vin_R{rep:02d}_{ts_screenshot}.jpg"
            captured = _maybe_capture_scope_png(scope, screenshot_path)

            timestamp_myt = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S MYT (UTC+8)")
            _append_ac_vin_summary_row(
                excel_path,
                summary_row={
                    "timestamp_MYT": timestamp_myt,
                    "repeat": rep,
                    "vcc": vcc,
                    "freq_hz": freq_hz,
                    "amp_vpp": amp_vpp,
                    "fit_slope": slope,
                    "fit_intercept": intercept,
                    "fit_R2": r_squared,
                    "vos_mV": vos_mV,
                    "gain_vs_commanded_mean": gain_vs_commanded_mean,
                    "junction_Vpp_max_mV": junction_vpp_max * 1000.0,
                    "loop_ok": loop_ok,
                    "data_sheet": sheet_name,
                    "screenshot_path": captured or "",
                },
            )

            if logger:
                logger.log_test("IN+", vcc)
                logger.log_test("AC_GAIN", slope)
                logger.log_test("VOS_mV", vos_mV)
                logger.log_test("FIT_R2", r_squared)
                logger.log_test("JUNCTION_VPP_mV", junction_vpp_max * 1000.0)

            repeats_out.append({
                "fit": fit,
                "rows": rows,
                "gain_vs_commanded_mean": gain_vs_commanded_mean,
                "junction_vpp_max": junction_vpp_max,
                "loop_ok": loop_ok,
                "sheet_name": sheet_name,
                "screenshot_path": captured,
            })

            print(f"  Repeat {rep} written to '{sheet_name}' in {excel_path}")

        summary = {
            "n_repeats": n_repeats,
            "excel_path": excel_path,
            "summary_sheet": AC_VIN_SUMMARY_SHEET,
            "vin_range_mV": vin_range_mV,
            "step_mV": step_mV,
            "freq_hz": freq_hz,
            "amp_vpp": amp_vpp,
            "vcc": vcc,
        }
        return {"repeats": repeats_out, "summary": summary}

    finally:
        try:
            stop_output(gen)
        except Exception:
            pass
        try:
            power_off(psu)
        except Exception:
            pass


def _gbw_init_statistics(scope) -> None:
    """Once per GBW run — Freq1 / Vpp1 / Vpp2 statistic table."""
    try:
        scope.clear()
        scope.write("*CLS")
    except Exception as exc:
        print(f"GBW scope clear skipped: {exc}", flush=True)
    try:
        scope.write(":MEASure:CLEar ALL")
        time.sleep(0.15)
    except Exception as exc:
        print(f"GBW MEASure:CLEar skipped: {exc}", flush=True)
    try:
        scope.write(":MEASure:ITEM FREQuency,CHAN1")
        scope.write(":MEASure:ITEM VPP,CHAN1")
        scope.write(":MEASure:ITEM VPP,CHAN2")
        for cmd in (
            ":MEASure:STATistic:ITEM FREQuency,CHAN1",
            ":MEASure:STATistic:ITEM VPP,CHAN1",
            ":MEASure:STATistic:ITEM VPP,CHAN2",
            ":MEASure:STATistic:DISPlay ON",
            ":MEASure:STATistic:RESet",
        ):
            try:
                scope.write(cmd)
            except Exception as exc:
                print(f"GBW statistics cmd skipped ({cmd}): {exc}", flush=True)
        time.sleep(0.35)
    except Exception as exc:
        print(f"GBW statistics setup skipped: {exc}", flush=True)


def _gbw_wait_measure_menu_off(scope) -> None:
    """Dismiss Rigol measure softkey menu only — statistics stay on."""
    try:
        scope.write(":SYSTem:KEY:PRESs MOFF")
    except Exception:
        pass
    time.sleep(0.35)
    try:
        scope.write(":MEASure:STATistic:DISPlay ON")
    except Exception:
        pass
    time.sleep(0.15)


def _gbw_shot_timed(scope, shot_cb, variant: str, *, timeout_s: float = 12.0) -> str | None:
    """Screenshot with hard timeout — never block GBW sweep on :DISP:DATA?."""
    if not shot_cb:
        return None
    out: list[str] = []
    err: list[BaseException] = []

    def _run() -> None:
        try:
            _gbw_prepare_screenshot(scope)
            try:
                path = shot_cb(scope, variant)
            except TypeError:
                path = shot_cb(scope)
            if path:
                out.append(str(path))
        except BaseException as exc:
            err.append(exc)

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    th.join(timeout=timeout_s)
    if th.is_alive():
        print(
            f"GBW screenshot ({variant}) TIMEOUT after {timeout_s}s — skip, continue sweep",
            flush=True,
        )
        try:
            park_scope_idle(scope, clear=True)
        except Exception:
            pass
        return None
    if err:
        print(f"GBW screenshot ({variant}) skipped: {err[0]}", flush=True)
        try:
            park_scope_idle(scope, clear=True)
        except Exception:
            pass
        return None
    return out[0] if out else None


def _gbw_prepare_screenshot(scope) -> None:
    """Stats already running — close measure menu, brief settle, capture."""
    _gbw_wait_measure_menu_off(scope)


def _gbw_vdiv(vpp: float, *, divisions: float = 4.0) -> float:
    """Pick nearest Rigol V/div so ~`divisions` of the waveform fit on screen."""
    need = max(float(vpp) / divisions, 0.005)
    scales = (
        0.001, 0.002, 0.005, 0.01, 0.02, 0.05,
        0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0,
    )
    for s in scales:
        if s >= need:
            return s
    return scales[-1]


def _gbw_read_vpp(scope, ch: int, *, settle_s: float = 0.35) -> float:
    """VPP via :MEAS:ITEM? (same path as AC gain — avoids statistic VI errors)."""
    time.sleep(settle_s)
    v = _avg_scope_meas(scope, "VPP", int(ch), 2)
    if not _is_valid_scope_meas(v) or v <= 0:
        raise ValueError(f"GBW: no valid VPP on CHAN{ch} (got {v})")
    return v


def _gbw_set_sine(gen, freq_hz: float, vpp_v: float) -> None:
    """APPL:SIN + OUTP ON every step (DG800 needs full rewrite, not bare :FREQ)."""
    setup_sine(gen, 1, float(freq_hz), float(vpp_v), 0, 0)
    enable_output(gen, 1)
    time.sleep(0.35)


def _gbw_scope_for_freq(
    scope,
    freq_hz: float,
    *,
    vin_vpp: float = 0.05,
    vout_vpp: float = 0.55,
) -> None:
    """Timebase + vertical: CH1 upper half, CH2 lower half (no overlap / clip)."""
    f = max(float(freq_hz), 100.0)
    period = 1.0 / f
    tscale = min(max(period / 4.0, 200e-9), 500e-6)
    # Extra headroom so offset stacking never clips peaks
    ch1 = _gbw_vdiv(vin_vpp, divisions=2.5)
    ch2 = _gbw_vdiv(vout_vpp, divisions=2.5)
    # Screen is ~±4 div: park CH1 ~+2 div, CH2 ~−2 div
    off1 = 2.0 * ch1
    off2 = -2.0 * ch2
    scope.write(":RUN")
    scope.write(f":TIMebase:MAIN:SCAle {tscale}")
    scope.write(":TRIGger:MODE EDGE")
    scope.write(":TRIGger:EDGE:SLOPe POSitive")
    scope.write(":TRIGger:EDGE:SOURce CHAN2")
    scope.write(":TRIGger:EDGE:LEVel 0")
    scope.write(f":CHAN1:SCALe {ch1}")
    scope.write(f":CHAN2:SCALe {ch2}")
    scope.write(f":CHAN1:OFFSet {off1}")
    scope.write(f":CHAN2:OFFSet {off2}")
    scope.write(":CHAN1:COUPling AC")
    scope.write(":CHAN2:COUPling AC")
    scope.write(":CHAN1:DISP ON")
    scope.write(":CHAN2:DISP ON")
    time.sleep(0.25)


def _gbw_fit_vertical(scope, *, vin_vpp: float, vout_vpp: float) -> None:
    """Re-apply V/div from measured amplitudes; stack CH1 up / CH2 down."""
    ch1 = _gbw_vdiv(vin_vpp, divisions=2.5)
    ch2 = _gbw_vdiv(vout_vpp, divisions=2.5)
    scope.write(f":CHAN1:SCALe {ch1}")
    scope.write(f":CHAN2:SCALe {ch2}")
    scope.write(f":CHAN1:OFFSet {2.0 * ch1}")
    scope.write(f":CHAN2:OFFSet {-2.0 * ch2}")
    time.sleep(0.35)


def _gbw_find_f3db(
    gen,
    scope,
    *,
    vpp_in: float,
    target_vout: float,
    vout_1k: float,
    progress_cb=None,
    debug: bool = False,
) -> tuple[float, list[dict]]:
    """Lab sweep: coarse +100 kHz, fine +10 k / +1 k / +100 / +10 Hz."""

    sweep_log: list[dict] = []
    coarse_step_hz = 100_000.0
    baseline_hz = 1000.0

    def prog(step: str, msg: str) -> None:
        line = f"GBW {step}: {msg}"
        dbg(line, enabled=debug)
        print(line, flush=True)
        if progress_cb:
            progress_cb(step, msg)

    def vout_at(freq: float) -> float:
        _gbw_set_sine(gen, freq, vpp_in)
        expect = max(target_vout, vout_1k * 0.5)
        _gbw_scope_for_freq(scope, freq, vin_vpp=vpp_in, vout_vpp=expect)
        v = _gbw_read_vpp(scope, 2)
        _gbw_fit_vertical(scope, vin_vpp=vpp_in, vout_vpp=max(v, target_vout * 0.8))
        return _gbw_read_vpp(scope, 2, settle_s=0.35)

    def log_pt(phase: str, freq_hz: float, vout_v: float) -> None:
        sweep_log.append(
            {
                "phase": phase,
                "freq_hz": round(freq_hz, 2),
                "freq_kHz": round(freq_hz / 1000.0, 4),
                "vout_mV": round(vout_v * 1000, 3),
                "target_mV": round(target_vout * 1000, 3),
            }
        )

    last_good = baseline_hz
    f_hi = coarse_step_hz
    f_lo = baseline_hz
    f = coarse_step_hz
    while f <= 1_000_000.0:
        v = vout_at(f)
        log_pt("coarse", f, v)
        prog(
            "coarse",
            f"f={f/1000:.0f} kHz VOUT={v*1000:.2f} mV "
            f"target={target_vout*1000:.2f} mV",
        )
        if v <= target_vout:
            f_hi = f
            f_lo = last_good
            break
        last_good = f
        f += coarse_step_hz
    else:
        raise ValueError(
            "GBW: VOUT never reached -3 dB below 1 MHz "
            f"(last coarse {last_good/1000:.0f} kHz)"
        )

    best = f_hi
    fine_steps = (
        (10_000, "fine_10k"),
        (1_000, "fine_1k"),
        (100, "fine_100"),
        (10, "fine_10"),
    )
    for i, (step_hz, tag) in enumerate(fine_steps):
        if i == 0:
            start = int(f_lo) + step_hz
        else:
            start = int(max(f_lo, best - 10 * step_hz))
        for ff in range(start, int(best) + 1, step_hz):
            v = vout_at(float(ff))
            log_pt(tag, float(ff), v)
            prog(tag, f"f={ff/1000:.4f} kHz VOUT={v*1000:.2f} mV")
            if v <= target_vout:
                best = float(ff)
                break

    prog("done", f"f-3dB ~= {best/1000:.4f} kHz")
    return float(best), sweep_log


def measure_gbw(
    instr,
    vcc,
    amp,
    gain,
    logger=None,
    debug: bool = None,
    current_limit_a=None,
    progress_cb=None,
    pause_cb=None,
    shot_cb=None,
):  # type: ignore
    """Measure GBW — lab procedure matching hand calc.

    1. AWG 50 mVpp sine @ 1 kHz (LOAD=INF), scope CH1=IN+ CH2=VOUT (fit on screen)
    2. Stats on (Freq1, Vpp1, Vpp2); record Av; target = VOUT * 0.707
    3. Screenshot @ 1 kHz — statistics stay on; measure menu OFF (MOFF)
    4. Coarse +100 kHz; fine +10 k / +1 k / +100 / +10 Hz to first VOUT <= target
    5. Screenshot @ f-3dB; GBW(MHz) = Av * f_3dB / 1e6
    """
    power_supply = instr.psu
    signal_generator = instr.gen
    oscilloscope = instr.scope
    if oscilloscope is not None:
        try:
            oscilloscope.timeout = 15000
        except Exception:
            pass
        recover_scope_session(oscilloscope)

    dbg(f"GBW START vcc={vcc}, amp={amp}, gain={gain}", enabled=debug)
    screenshots: list[str] = []

    def _shot(variant: str) -> None:
        path = _gbw_shot_timed(oscilloscope, shot_cb, variant, timeout_s=12.0)
        if path:
            screenshots.append(path)

    try:
        from configurations import current_limit as _default_ilim

        ilim = float(current_limit_a if current_limit_a is not None else _default_ilim)
        vcc_half = vcc / 2
        ovp_trip = vcc_half + 0.3
        ocp_trip = ilim + 0.1

        power_on_protected(power_supply, 1, vcc_half, ilim, ovp=ovp_trip, ocp=ocp_trip)
        power_on_protected(power_supply, 2, vcc_half, ilim, ovp=ovp_trip, ocp=ocp_trip)
        time.sleep(1)

        if progress_cb:
            progress_cb("awg_1k", "PSU on — AWG 50 mVpp @ 1 kHz")

        set_output_load(signal_generator, 1, "INF")
        vpp_in = float(amp)
        expect_vout = vpp_in * float(gain)
        _gbw_set_sine(signal_generator, 1000.0, vpp_in)
        _gbw_scope_for_freq(
            oscilloscope, 1000.0, vin_vpp=vpp_in, vout_vpp=expect_vout
        )
        if progress_cb:
            progress_cb("baseline", "Statistics on — reading Vpp @ 1 kHz")
        _gbw_init_statistics(oscilloscope)
        time.sleep(0.5)

        try:
            outp = signal_generator.query(":OUTP1?").strip()
            print(
                f"GBW AWG check: OUTP1={outp} (expect 1/ON) @ 1 kHz {vpp_in*1000:.1f} mVpp",
                flush=True,
            )
        except Exception as exc:
            print(f"GBW AWG query failed: {exc}", flush=True)

        # First read, then refit vertical so CH2 is fully on-screen, then re-read
        vpp_in_meas = _gbw_read_vpp(oscilloscope, 1)
        vout_1k = _gbw_read_vpp(oscilloscope, 2)
        _gbw_fit_vertical(oscilloscope, vin_vpp=vpp_in_meas, vout_vpp=vout_1k)
        vpp_in_meas = _gbw_read_vpp(oscilloscope, 1)
        vout_1k = _gbw_read_vpp(oscilloscope, 2)

        if vpp_in_meas < 1e-4:
            raise ValueError(
                f"GBW: IN+ Vpp too small ({vpp_in_meas*1000:.3f} mV) — "
                "AWG off, wrong probe, or LOAD not INF"
            )
        target_vout = vout_1k * 0.707
        av = (vout_1k / vpp_in_meas) if vpp_in_meas else float(gain)
        print(
            f"GBW baseline @1kHz: Vpp_IN={vpp_in_meas*1000:.3f} mV "
            f"VOUT={vout_1k*1000:.3f} mV Av={av:.3f} "
            f"target(-3dB)={target_vout*1000:.3f} mV",
            flush=True,
        )
        if progress_cb:
            progress_cb(
                "baseline",
                f"IN={vpp_in_meas*1000:.2f} mV VOUT={vout_1k*1000:.2f} mV Av={av:.3f}",
            )

        if pause_cb:
            print(f"GBW checkpoint (auto-continue): 1 kHz baseline", flush=True)
            pause_cb(
                "GBW @ 1 kHz — confirm both sines fully on screen (Freq1/Vpp1/Vpp2), then Continue"
            )

        if progress_cb:
            progress_cb("shot_1k", "Screenshot @ 1 kHz (12s max, then sweep)")
        _shot("1kHz_baseline")

        if progress_cb:
            progress_cb("coarse", "Sweep starting — coarse +100 kHz")
        initial_time()
        f_3db, sweep_log = _gbw_find_f3db(
            signal_generator,
            oscilloscope,
            vpp_in=vpp_in,
            target_vout=target_vout,
            vout_1k=vout_1k,
            progress_cb=progress_cb,
            debug=debug,
        )
        duration_gbw = final_time()

        # Park at f-3dB, fit, screenshot for the lab record
        _gbw_set_sine(signal_generator, f_3db, vpp_in)
        _gbw_scope_for_freq(
            oscilloscope, f_3db, vin_vpp=vpp_in_meas, vout_vpp=target_vout
        )
        vout_f3 = _gbw_read_vpp(oscilloscope, 2)
        _gbw_fit_vertical(oscilloscope, vin_vpp=vpp_in_meas, vout_vpp=vout_f3)
        if progress_cb:
            progress_cb(
                "shot_f3db",
                f"Screenshot @ f-3dB={f_3db/1000:.2f} kHz VOUT={vout_f3*1000:.1f} mV",
            )
        if pause_cb:
            print(
                f"GBW checkpoint (auto-continue): f-3dB ~ {f_3db/1000:.2f} kHz",
                flush=True,
            )
            pause_cb(
                f"GBW f-3dB ~ {f_3db/1000:.2f} kHz -- check Vpp2~{target_vout*1000:.0f} mV, then Continue"
            )
        _shot(f"f3db_{f_3db/1000:.0f}kHz")

        gbw_mhz = round(av * f_3db * 1e-6, 4)
        results = {
            "IN+": vcc,
            "Vpp_IN_mV": round(vpp_in_meas * 1000, 4),
            "VOUT_1k_mV": round(vout_1k * 1000, 4),
            "VOUT_707_mV": round(target_vout * 1000, 4),
            "VOUT_f3db_mV": round(vout_f3 * 1000, 4),
            "Av": round(av, 4),
            "F_3dB_kHz": round(f_3db / 1000.0, 4),
            "F_3dB_Hz": round(f_3db, 2),
            "GBW_MHz": gbw_mhz,
            "gain": float(gain),
            "baseline_freq_Hz": 1000.0,
            "target_ratio": 0.707,
            "calculation": f"GBW_MHz = Av({av:.4f}) × f_3dB_MHz({f_3db/1e6:.6f})",
            "sweep_log": sweep_log,
        }
        if screenshots:
            results["screenshot"] = screenshots[-1]
            results["screenshots"] = screenshots
        print(f"GBW RESULT: {results}", flush=True)
        if progress_cb:
            progress_cb(
                "gbw_calc",
                f"Av={av:.3f} x {f_3db/1e6:.4f} MHz = {gbw_mhz:.4f} MHz",
            )

        if logger:
            logger.log_test("VOUT_1k_mV", results["VOUT_1k_mV"], duration_ms=duration_gbw)
            logger.log_test("F_3dB_kHz", results["F_3dB_kHz"], duration_ms=duration_gbw)
            logger.log_test("GBW_MHz", gbw_mhz, duration_ms=duration_gbw)

        return results

    except Exception as e:
        print(f"Error measuring GBW: {e}", flush=True)
        raise
    finally:
        try:
            from generator_setup import park_generator_idle
            from psu_setup import power_off
            from scope_setup import park_scope_idle

            park_generator_idle(signal_generator)
            power_off(power_supply)
            if oscilloscope is not None:
                park_scope_idle(oscilloscope, clear=True)
        except Exception as cleanup_exc:
            print(f"GBW cleanup: {cleanup_exc}", flush=True)
            try:
                disable_output(signal_generator, 1)
            except Exception:
                pass
            if oscilloscope is not None:
                try:
                    from scope_setup import park_scope_idle

                    park_scope_idle(oscilloscope, clear=True)
                except Exception:
                    pass


def measure_sr(instr, vcc, amp, logger=None):
    """Measure Slew Rate (SR) - positive and negative.
    
    Measures the maximum rate of change of output voltage in response to
    a square wave input. Tests both positive and negative slew rates.
    
    Args:
        instr: Instruments object containing psu, gen, scope
        vcc: Supply voltage in Volts
        amp: Input amplitude in Volts (typically 1V)
        logger: Optional DataLogger for recording results
        
    Returns:
        Dictionary with 'IN+', 'SR_positive', and 'SR_negative' keys
    """
    power_supply = instr.psu
    signal_generator = instr.gen
    oscilloscope = instr.scope
    
    start_time = time.time() * 1000  # in milliseconds
    
    try:
        # Setup phase
        # 1. Power supply configuration
        power_on_protected(power_supply, 1, vcc / 2, current_limit)
        time.sleep(1)
        power_on_protected(power_supply, 2, vcc / 2, current_limit)
        time.sleep(1)
        
        # 2. Signal generator setup - square wave for slew rate measurement
        setup_square(signal_generator, 1, 1000, amp, 0)  # Convert to V
        time.sleep(1)
        enable_output(signal_generator, 1)
        time.sleep(1)
        
        # 3. Oscilloscope setup for transient measurement
        # Use wider timebase (100 µs) to capture full rising/falling edges for SR measurement
        scope_setup(oscilloscope, 500e-9, 0)
        time.sleep(1)
        
        input("Press Enter to continue...")

        # Measurement phase
        # 4. Collect slew rate measurements (multiple samples for averaging)
        initial_time()
        pslewrates = []
        nslewrates = []
        
        for measurement_idx in range(20):
            try:
                # Query positive and negative slew rates from oscilloscope
                pslew = float(oscilloscope.query(":MEAS:ITEM? PSLewrate,CHAN2")) * 1e-6  # Convert to V/µs
                nslew = float(oscilloscope.query(":MEAS:ITEM? NSLewrate,CHAN2")) * 1e-6

                print(f"Sample {measurement_idx+1}: PSlew={pslew:.4f} V/us, NSlew={nslew:.4f} V/us")

                pslewrates.append(pslew)
                nslewrates.append(nslew)
            except Exception as e:
                pass
            time.sleep(0.01)
        
        duration_sr = final_time()
        
        if not pslewrates or not nslewrates:
            raise ValueError("Could not obtain valid slew rate measurements")
        
        # Calculate averages
        sr_positive = round(sum(pslewrates) / len(pslewrates), 4)
        sr_negative = round(sum(nslewrates) / len(nslewrates), 4)
        
        results = {
            "IN+": vcc,
            "SR_positive": sr_positive,
            "SR_negative": sr_negative
        }
        
        if logger:
            logger.log_test("IN+", vcc, duration_ms=duration_sr)
            logger.log_test("SR_positive", sr_positive, duration_ms=duration_sr)
            logger.log_test("SR_negative", sr_negative, duration_ms=duration_sr)
        
        return results
        
    except Exception as e:
        print(f"Error measuring SR: {e}")
        return None
    finally:
        try:
            disable_output(signal_generator, 1)
        except:
            pass


def test_opa_gbw(instr, vcc, logger=None):
    """Test OPA GBW at specified VCC.

    1 kHz baseline Av, then stepped freq sweep to VOUT x 0.707.
    """
    amp = 0.05  # 50 mVpp input
    gain = 11   # nominal closed-loop (GBW uses measured Av)
    return measure_gbw(instr, vcc, amp, gain, logger)


def test_opa_sr(instr, vcc, logger=None):
    """Test OPA Slew Rate at specified VCC.
    
    Wrapper function for measuring slew rate that follows the standard test pattern.
    Measures both positive and negative slew rates.
    
    Args:
        instr: Instruments object
        vcc: Supply voltage in Volts
        logger: Optional DataLogger for recording results
        
    Returns:
        Dictionary with test results
    """
    amp = 1.0  # 1V input amplitude for SR measurement
    return measure_sr(instr, vcc, amp, logger)


def test_opa_bandwidth(instr, vcc, logger=None):
    """Test OPA bandwidth - combined GBW and SR measurement.
    
    Comprehensive bandwidth test combining GBW measurement and slew rate.
    Tests device performance at specified VCC level.
    
    Args:
        instr: Instruments object
        vcc: Supply voltage in Volts
        logger: Optional DataLogger for recording results
        
    Returns:
        Dictionary with combined GBW and SR results
    """
    gbw_result = test_opa_gbw(instr, vcc, logger)
    sr_result = test_opa_sr(instr, vcc, logger)
    
    # Combine results
    combined = {
        "IN+": vcc,
    }
    if gbw_result:
        combined.update(gbw_result)
    if sr_result:
        combined.update(sr_result)
    
    return combined

def test_settlingTime(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control

    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()


    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 1 kHz frequency: tests high-speed response

    setup_square(gen, 1, 1000, 2, 0)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 200e-9, 0.5)

    # set_threshold(scope, 1)
    # set_threshold(scope, 2)

    # ========== MEASUREMENT PHASE ==========
    r_IN = measure_single(scope, "VPP", 1)  # Input amplitude
    r_settlingTime = measure_single(scope, "VPP", 2)  # Rising edge delay
    print(f"Measured IN+: {r_IN:.4f} V")

    duration_hl = final_time()
    end_time = time.time() * 1000  # in milliseconds
    overall_duration_ms = end_time - start_time
    
    print(f"Test duration: {overall_duration_ms:.2f} ms")

    my_capture = screenshot()

    input("Press Enter to continue...")

    results = {
        "IN+": r_IN,
        # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    }

    if logger:
        # Log VCC with overall duration
        logger.log_test("IN+", r_IN, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)

    stop_output(gen)

    power_off(psu)

    return results
    
def test_SSR(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control

    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()


    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_square(gen, 1, 500000, 0.1, 0)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 200e-9, 0.025)

    # set_threshold(scope, 1)
    # set_threshold(scope, 2)

    # ========== MEASUREMENT PHASE ==========
    t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    duration_hl = final_time()
    end_time = time.time() * 1000  # in milliseconds
    overall_duration_ms = end_time - start_time

    print(f"Test duration: {overall_duration_ms:.2f} ms")

    time.sleep(10)  # Wait for any transient effects to settle

    # my_capture = screenshot()
    input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")

    stop_output(gen)

    power_off(psu)

    results = {
        # "VCC": vcc,
        # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
        # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    }

    # if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)
        # logger.log_test("IN_T_O_LH", t_rise * 1e9, duration_ms=duration_lh)
        # logger.log_test("O_T_IN_HL", t_fall_rev * 1e9, duration_ms=duration_hl_rev)
        # logger.log_test("O_T_IN_LH", t_rise_rev * 1e9, duration_ms=duration_lh_rev)

    return results
    
def test_LSR(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control
    
    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()


    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_square(gen, 1, 250000, 4, 0)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 200e-9, 1)

    # set_threshold(scope, 1)
    # set_threshold(scope, 2)

    # ========== MEASUREMENT PHASE ==========
    # t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    duration_hl = final_time()
    end_time = time.time() * 1000  # in milliseconds
    overall_duration_ms = end_time - start_time
    
    print(f"Test duration: {overall_duration_ms:.2f} ms")

    time.sleep(10)  # Wait for any transient effects to settle

    # my_capture = screenshot()
    input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")

    results = {
        # "VCC": vcc,
        # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
        # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    }

    # if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)
        # logger.log_test("IN_T_O_LH", t_rise * 1e9, duration_ms=duration_lh)
        # logger.log_test("O_T_IN_HL", t_fall_rev * 1e9, duration_ms=duration_hl_rev)
        # logger.log_test("O_T_IN_LH", t_rise_rev * 1e9, duration_ms=duration_lh_rev)

    stop_output(gen)

    power_off(psu)

    return results

def test_ORT(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control
    
    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()

    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_square(gen, 1, 1000, 0.2, 0.1)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 1e-6, 0.1)

    # ========== MEASUREMENT PHASE ==========
    # t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    duration_hl = final_time()
    end_time = time.time() * 1000  # in milliseconds
    overall_duration_ms = end_time - start_time

    print(f"Test duration: {overall_duration_ms:.2f} ms")

    # my_capture = screenshot()
    input("Press Enter to continue...")

    initial_time()

    stop_output(gen)
    time.sleep(1) 

    setup_square(gen, 1, 1000, 0.2, -0.1)

    scope_setup(scope, 1e-6, -0.1)

    time.sleep(10)  # Wait for any transient effects to settle

    my_capture = screenshot()
    input("Press Enter to continue...")

    results = {
        # "VCC": vcc,
        # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
        # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    }

    # if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)
        # logger.log_test("IN_T_O_LH", t_rise * 1e9, duration_ms=duration_lh)
        # logger.log_test("O_T_IN_HL", t_fall_rev * 1e9, duration_ms=duration_hl_rev)
        # logger.log_test("O_T_IN_LH", t_rise_rev * 1e9, duration_ms=duration_lh_rev)

    stop_output(gen)

    power_off(psu)

    return results

#STILL IN DEVELOPMENT - NOT CALLED IN MAIN YET
def test_powerONtime(instr, vcc, logger=None): 
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control
    
    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()


    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_square(gen, 1, 1000, 0.2, 0.1)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 1e-6, vcc/2)

    # ========== MEASUREMENT PHASE ==========
    # t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    # my_capture = screenshot()
    input("Press Enter to continue...")

    setup_square(gen, 1, 1000, 0.2, 0.1)

    duration_hl = final_time()
    end_time = time.time() * 1000  # in milliseconds
    overall_duration_ms = end_time - start_time

    print(f"Test duration: {overall_duration_ms:.2f} ms")

    time.sleep(10)  # Wait for any transient effects to settle

    # my_capture = screenshot()
    input("Press Enter to continue...")

    results = {
        # "VCC": vcc,
        # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
        # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    }

    # if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)
        # logger.log_test("IN_T_O_LH", t_rise * 1e9, duration_ms=duration_lh)
        # logger.log_test("O_T_IN_HL", t_fall_rev * 1e9, duration_ms=duration_hl_rev)
        # logger.log_test("O_T_IN_LH", t_rise_rev * 1e9, duration_ms=duration_lh_rev)

    stop_output(gen)

    power_off(psu)

    return results