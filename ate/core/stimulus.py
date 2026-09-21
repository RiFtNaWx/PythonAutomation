"""AWG / PSU shape each TestSpec actually programs.

UI badge + check_stimulus. Tests bake their own APPL; Advanced freq/amp
only some OpAmp bodies read.
"""
from __future__ import annotations

from typing import Any

# wave: SQU SIN DC PULS RAMP NOIS off (no AWG)
_BY_ID: dict[str, dict[str, str]] = {
    "cin": {
        "wave": "SQU",
        "detail": "PSU CH1=3.3 V (CH2/CH3 OFF); AWG CH1 high-Z square 1/5/10 MHz; DMM DCI",
        "sweep": "freq",
        "sweep_hint": "Freq start/stop/step MHz (default 1 / 10 / 4 -> 1, 5, 10 MHz)",
    },
    "cpd": {
        "wave": "SQU",
        "detail": "PSU CH1 1.8-5 V (CH2/CH3 OFF); AWG CH1 high-Z square 10 MHz; DMM DCI",
        "sweep": "vcc",
        "sweep_hint": "PSU VCC 1.8-5 V at 10 MHz",
    },
    "tp": {
        "wave": "SQU",
        "detail": "PSU VCC; AWG square ~400 kHz (legacy TP)",
    },
    "tidle": {"wave": "SQU", "detail": "PSU VCC; AWG square (TIDLE)"},
    "tdis": {
        "wave": "SQU",
        "detail": "3-state: AWG A DC + OE square, pull R on Y. RS29511: AWG EN, MSO READY",
    },
    "ten": {
        "wave": "SQU",
        "detail": "3-state: AWG A DC + OE square, pull R on Y. RS29511: AWG EN, MSO READY",
    },
    "supply_current": {
        "wave": "DC",
        "detail": "PSU CH1=VCC (CH2/CH3 OFF); AWG CH1 DC on Input A (RS1G07); DMM DCI",
    },
    "supply_current_sweep": {
        "wave": "DC",
        "detail": "PSU VCC sweep; AWG DC levels on inputs",
        "sweep": "vcc",
        "sweep_hint": "PSU VCC corners / start-stop-step",
    },
    "delta_supply_current": {
        "wave": "DC",
        "detail": "PSU + AWG DC on inputs",
        "sweep": "vcc",
        "sweep_hint": "VCC start/stop/step (default 0 to 5 by 0.5). AWG CH1 then CH2 alternate at each step",
    },
    "off_current": {"wave": "DC", "detail": "PSU + AWG DC"},
    "input_thresholds": {"wave": "DC", "detail": "AWG DC VIN sweep; DMM", "sweep": "vin"},
    "ioff_leakage": {"wave": "DC", "detail": "PSU + AWG DC leakage"},
    "ioz": {
        "wave": "DC",
        "detail": "PSU CH1=VCC CH2=Y force CH3=OE Hi-Z; DMM DCI on Y; AWG CH1=0 if present",
    },
    "input_leakage_sweep": {
        "wave": "DC",
        "detail": "PSU + AWG DC VIN sweep",
        "sweep": "vcc",
        "sweep_hint": "PSU VCC list from part yaml or start/stop/step",
    },
    "vih_vil": {
        "wave": "DC",
        "detail": "AWG DC VIN sweep; DMM on Y (default Ariff)",
        "sweep": "vcc",
        "sweep_hint": "VCC list from part yaml, or start/stop/step",
    },
    "voh_load": {"wave": "DC", "detail": "PSU VCC/Vref/V+ ; AWG DC high on inputs; DMM VOH"},
    "vol_load": {"wave": "DC", "detail": "PSU VCC/Vref/V+ ; AWG DC 0 on inputs; DMM VOL"},
    "slew": {"wave": "SQU", "detail": "AWG square 1 kHz 1 Vpp then 2 Vpp; PSU rails"},
    "settling": {"wave": "SQU", "detail": "AWG square 1 kHz 2 Vpp"},
    "ort": {"wave": "SQU", "detail": "AWG square 1 kHz 0.2 Vpp, +/- offset"},
    "gbw": {
        "wave": "SIN",
        "detail": "AWG sine ~50 mVpp, freq sweep (GBW)",
        "sweep": "freq",
        "sweep_hint": "GBW freq search (board locked). Range boxes are CIN/fmax.",
    },
    "sssr": {"wave": "SQU", "detail": "AWG square 500 kHz 0.1 Vpp"},
    "lssr": {"wave": "SQU", "detail": "AWG square 250 kHz 4 Vpp"},
    "npr": {"wave": "SIN", "detail": "AWG sine 1 kHz 6 Vpp"},
    "vih": {"wave": "DC", "detail": "RS0204 AWG DC VIN; PSU VCCA/VCCB"},
    "vil": {"wave": "DC", "detail": "RS0204 AWG DC VIN"},
    "voh": {"wave": "DC", "detail": "RS0204 AWG DC + DMM"},
    "vol": {"wave": "DC", "detail": "RS0204 AWG DC + DMM"},
    "icc": {
        "wave": "DC",
        "detail": "Path B ICC: DMM-on-VCC, IO=0 (CH2 Y-load OFF), 2^n corners; VI=VCC or GND",
        "sweep": "vcc",
    },
    "delta_icc": {
        "wave": "DC",
        "detail": "SeeLim dICC original; Continue wiring; one input at VCC-0.6 V",
        "sweep": "vcc",
    },
    "ii": {
        "wave": "DC",
        "detail": "SeeLim II original; DMM in series with the pin under test",
        "sweep": "vcc",
    },
    "ioff": {
        "wave": "DC",
        "detail": "Path B Ioff; VCC=0; 2^n I/O ports; n+1 DMM (VCC then inputs then Y)",
    },
    "input_threshold": {
        "wave": "DC",
        "detail": "SeeLim VIH/VIL trip (same physics as vih_vil -- do not enable both)",
        "sweep": "vin",
    },
    "il": {"wave": "DC", "detail": "RS0204 AWG DC leakage"},
    "tpd": {"wave": "SQU", "detail": "RS0204 AWG square ~400 kHz A->B"},
    "tp_rs0204": {"wave": "SQU", "detail": "RS0204 AWG square B->A"},
    "tsu": {"wave": "SQU", "detail": "RS0204 AWG square setup time"},
    "th": {"wave": "SQU", "detail": "RS0204 AWG square hold"},
    "fmax": {
        "wave": "SQU",
        "detail": "RS0204 AWG square 1-20 MHz",
        "sweep": "freq",
        "sweep_hint": "AWG square 1-20 MHz (body list unless range set)",
    },
    "tr": {"wave": "SQU", "detail": "RS0204 AWG square rise"},
    "tf": {"wave": "SQU", "detail": "RS0204 AWG square fall"},
    "tsk": {"wave": "SQU", "detail": "RS0204 AWG square both AWG channels"},
    "tw": {"wave": "PULS", "detail": "RS0204 AWG pulse 1 MHz 50% duty"},
    "iq": {"wave": "DC", "detail": "LDO PSU VIN; AWG DC if used", "sweep": "vin"},
    "iplus": {
        "wave": "off",
        "detail": "PSU CH1=V+; DMM DCI in series; no AWG",
        "sweep": "vcc",
        "sweep_hint": "V+ corners from part yaml (1.8/3.3/5.0) unless you change start/stop/step",
    },
    "leakage_off": {
        "wave": "off",
        "detail": "PSU CH1=V+ CH2/CH3 bias; DMM DCI; no AWG",
        "sweep": "vcc",
        "sweep_hint": "V+ sweep same as Iplus",
    },
    "leakage_on": {
        "wave": "off",
        "detail": "PSU CH1=V+ CH2/CH3 bias; DMM DCI; no AWG",
        "sweep": "vcc",
        "sweep_hint": "V+ sweep same as Iplus",
    },
    "input_leakage": {
        "wave": "off",
        "detail": "PSU CH1=V+; DMM DCI on IN; no AWG",
        "sweep": "vcc",
        "sweep_hint": "V+ sweep same as Iplus",
    },
    "ron": {
        "wave": "off",
        "detail": "PSU CH1=V+ CH3=VCOM CH2 CC into COM; DMM VDC COM-NO/NC; no AWG",
        "sweep": "vcom",
        "sweep_hint": "Each V+ corner; VCOM 0 / half / V+",
    },
    "ton_toff": {
        "wave": "SQU",
        "detail": "PSU CH1=V+; AWG square on IN; MSO CH1=IN CH2=COM/NO",
    },
    "clk_q": {
        "wave": "SQU",
        "detail": "PSU VCC; AWG CH1=CLK square CH2=D DC; MSO CH1=CLK CH2=Q",
    },
    "con_coff": {
        "wave": "off",
        "detail": "DMM CAP CIN/CON/COFF; PSU V+ for CON/COFF select; no AWG",
    },
    "tbbm": {
        "wave": "SQU",
        "detail": "PSU CH1=V+; AWG square on IN; MSO CH1=NO CH2=NC",
    },
    "iso": {
        "wave": "SIN",
        "detail": "PSU CH1=V+; IN1=GND; AWG 1 MHz 1 Vpp on NC; MSO CH1=NC CH2=COM (high-Z)",
    },
    "xtalk": {
        "wave": "SIN",
        "detail": "PSU CH1=V+; IN1=IN2=GND; AWG 1 MHz 1 Vpp on COM1; MSO CH1=COM1 CH2=COM2 (high-Z)",
    },
    "usb_ron": {
        "wave": "DC",
        "detail": "RS2227 USB DPDT; PSU V+; AWG OE=0 S=0/V+; CH2 10 mA D+; DMM V D+-HSDn",
    },
    "usb_ton_toff": {
        "wave": "SQU",
        "detail": "RS2227 OE=GND; AWG square on S; MSO CH1=S CH2=HSD1+",
    },
    "usb_iso": {
        "wave": "SIN",
        "detail": "RS2227 OE=V+; AWG 1 MHz 1 Vpp on D+; MSO CH1=D+ CH2=HSD1 (high-Z)",
    },
    "usb_xtalk": {
        "wave": "SIN",
        "detail": "RS2227 OE=GND S=GND; AWG 1 MHz 1 Vpp on D+; MSO CH1=HSD1 CH2=HSD2 (high-Z)",
    },
    "pulse_width": {
        "wave": "PULS",
        "detail": "PSU VCC; AWG pulse on B; MSO CH2=Q (RS1G123 RC)",
    },
    "serial_shift": {
        "wave": "SQU",
        "detail": "PSU VCC; AWG CH1=CLK square CH2=A DC; DMM on Q7; strap B high",
    },
    "psrr": {
        "wave": "DC",
        "detail": "BUFFER; dual-rail Vs 2.5 then 5.5; AWG DC 0 V; DMM VOUT",
    },
    "vth": {
        "wave": "DC",
        "detail": "PSU V+ and COM=V+/2; AWG DC sweep IN; DMM NO",
        "sweep": "vin",
        "sweep_hint": "AWG DC VIN sweep at each V+",
    },
    "cmrr": {
        "wave": "DC",
        "detail": "BUFFER; Vs=5.5 dual-rail; AWG DC Vcm; DMM VOUT",
    },
    "power_on_time": {
        "wave": "DC",
        "detail": "BUFFER; dual-rail; AWG DC 0 V; MSO CH1=VCC CH2=VOUT delay",
    },
    "vohl": {
        "wave": "DC",
        "detail": "BUFFER; Vs=5.5 dual-rail; AWG DC near +rail then -rail; DMM VOUT",
    },
    "vos_sweep": {"wave": "DC", "detail": "VOS DC sweep", "sweep": "vin"},
    "ac_vin_sweep": {"wave": "SIN", "detail": "AC Vin sweep", "sweep": "vin"},
    "i2c_ii": {
        "wave": "DC",
        "detail": "RS0302 EN=0 AWG DC; PSU CH1=5 V; DMM DCI on SCL1",
    },
    "i2c_ron": {
        "wave": "DC",
        "detail": "RS0302 VREF1/VREF2; AWG EN high; CH3 10 mA; DMM V SCL1-SCL2",
    },
    "i2c_cioff": {
        "wave": "off",
        "detail": "RS0302 EN=0; VREF off; DMM CAP SCL1-GND",
    },
}


def for_test(
    test_id: str, *, family: str = "", part: str = ""
) -> dict[str, Any]:
    tid = str(test_id or "").strip().lower()
    fam = str(family or "").strip().lower()
    pk = str(part or "").strip().lower()
    if fam in ("lim", "analog_switch"):
        fam = "switch"
    if tid == "cpd" and (fam == "level" or pk == "rs0204"):
        return {
            "wave": "off",
            "detail": "RS0204 Cio: DUT unpowered, DMM CAP (not dynamic Cpd)",
        }
    if tid == "vih_vil" and pk == "rs1gt34":
        return {
            "wave": "off",
            "detail": "PSU CH1=VCC, PSU CH2=Input A, MSO CH1=Y; no AWG, no freq",
            "sweep": "vcc",
            "sweep_hint": "Fixed 2.0 and 3.3, then 4.5-5.5 start/stop/step (0.01 OK). VIN trip step separate.",
        }
    row = _BY_ID.get(tid)
    if not row:
        return {"wave": "", "detail": ""}
    out = {"wave": row["wave"], "detail": row["detail"]}
    if row.get("sweep"):
        out["sweep"] = row["sweep"]
        out["sweep_hint"] = row.get("sweep_hint") or ""
    return out
