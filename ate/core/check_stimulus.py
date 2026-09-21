"""Fail-closed: AWG APPL shapes + PSU ON match what Logic/OpAmp tests claim.

Run: python -m ate.core.check_stimulus
"""
from __future__ import annotations

import sys

from ate.core.stimulus import for_test
from ate.core.tags import list_boards
from ate.core.database import set_context
from ate.instruments.sim import SimResource, bus_snapshot, reset_bus
from dmm_setup import dmm_setup_current
from generator_setup import (
    setup_dc,
    setup_pulse,
    setup_sine,
    setup_square,
    stop_output,
)
from psu_setup import power_off, power_on_protected


def main() -> int:
    errors: list[str] = []

    want = {
        ("cin", "logic", ""): "SQU",
        ("slew", "opamp", ""): "SQU",
        ("gbw", "opamp", ""): "SIN",
        ("voh_load", "logic", ""): "DC",
        ("tw", "level", "rs0204"): "PULS",
        ("cpd", "level", "rs0204"): "off",
        ("cpd", "logic", "rs1g07"): "SQU",
        ("supply_current", "logic", "rs1g07"): "DC",
        ("ron", "switch", "rs2323"): "off",
        ("ton_toff", "switch", "rs2323"): "SQU",
        ("clk_q", "logic", "rs1g74"): "SQU",
        ("con_coff", "switch", "rs2323"): "off",
        ("tbbm", "switch", "rs2323"): "SQU",
        ("iso", "switch", "rs2323"): "SIN",
        ("xtalk", "switch", "rs2323"): "SIN",
        ("usb_iso", "switch", "rs2227"): "SIN",
        ("usb_xtalk", "switch", "rs2227"): "SIN",
        ("pulse_width", "logic", "rs1g123"): "PULS",
        ("serial_shift", "logic", "rs164"): "SQU",
        ("psrr", "opamp", "rs622"): "DC",
        ("cmrr", "opamp", "rs622"): "DC",
        ("power_on_time", "opamp", "rs622"): "DC",
        ("vohl", "opamp", "rs622"): "DC",
        ("ort", "opamp", "rs622"): "SQU",
        ("vth", "switch", "rs2323"): "DC",
        ("ioz", "logic", "rs1g126"): "DC",
        ("icc", "logic", "rs1g97"): "DC",
        ("delta_icc", "logic", "rs1g97"): "DC",
        ("ii", "logic", "rs1g97"): "DC",
        ("input_threshold", "logic", "rs1g97"): "DC",
        ("vih_vil", "logic", "rs1gt34"): "off",
        ("ten", "logic", "rs1g126"): "SQU",
        ("tdis", "logic", "rs1g126"): "SQU",
        ("ten", "logic", "rs29511"): "SQU",
        ("tdis", "logic", "rs29511"): "SQU",
        ("ioff", "logic", "rs1g126"): "DC",
        ("i2c_ii", "level", "rs0302"): "DC",
        ("i2c_ron", "level", "rs0302"): "DC",
        ("i2c_cioff", "level", "rs0302"): "off",
        ("usb_ron", "switch", "rs2227"): "DC",
        ("usb_ton_toff", "switch", "rs2227"): "SQU",
    }
    for (tid, fam, part), wave in want.items():
        got = for_test(tid, family=fam, part=part).get("wave")
        if got != wave:
            errors.append(f"{tid} {fam} {part}: wave {got!r} want {wave!r}")

    set_context(
        component="Logic",
        part="RS1G07",
        package="SC70-5",
        operator="Eugene",
        version="Version_1",
        model="RS1G07XC5",
        part_key="rs1g07",
        sample_size=1,
    )
    boards = list_boards(family="logic", package="SC70-5")
    if "LOGIC-SC70-REV1" not in boards:
        errors.append(f"logic SC70-5 boards missing LOGIC-SC70-REV1, got {boards}")

    reset_bus()
    awg = SimResource("AWG")
    psu = SimResource("PSU")

    def snap() -> tuple[str, float, bool, float, str]:
        b = bus_snapshot()
        return (
            str(b.get("func") or ""),
            float(b.get("freq") or 0.0),
            bool(b.get("psu_on")),
            float(b.get("psu_v") or 0.0),
            str(b.get("out") or "OFF"),
        )

    setup_square(awg, 1, 10e6, 3.3, 1.65)
    func, freq, _, _, out = snap()
    if func != "SQU" or abs(freq - 10e6) > 1 or out != "ON":
        errors.append(f"setup_square bus {snap()}")

    setup_sine(awg, 1, 1000, 0.05, 0)
    func, freq, _, _, out = snap()
    if func != "SIN" or abs(freq - 1000) > 1:
        errors.append(f"setup_sine bus {snap()}")

    setup_pulse(awg, 1, 1e6, 1.8, 0.9, duty=50)
    func, _, _, _, _ = snap()
    if func != "PULS":
        errors.append(f"setup_pulse bus {snap()}")

    setup_dc(awg, 1, 1.65)
    func, _, _, _, _ = snap()
    if func != "DC":
        errors.append(f"setup_dc bus {snap()}")

    from generator_setup import set_output_load

    set_output_load(awg, 1, "INF")
    if not any("LOAD INF" in str(w).upper() for w in awg.writes):
        errors.append("set_output_load must write :OUTP1:LOAD INF")

    power_on_protected(psu, 1, 3.3, 0.05)
    _, _, psu_on, psu_v, _ = snap()
    if not psu_on or abs(psu_v - 3.3) > 0.05:
        errors.append(f"PSU ON bus {snap()}")

    stop_output(awg)
    power_off(psu)
    _, _, psu_on, _, awg_out = snap()
    if psu_on or awg_out == "ON":
        errors.append(f"idle after stop/power_off {snap()}")

    dmm = SimResource("DMM")
    dmm_setup_current(dmm)
    if dmm.dmm_func != "CURR":
        errors.append(f"dmm_setup_current must switch to DCI, func={dmm.dmm_func!r}")
    if not any("CONF:CURR" in str(w).upper() for w in dmm.writes):
        errors.append("dmm_setup_current must write :CONF:CURR:DC so DMM6500 shows DCI")
    joined = " ".join(str(w).upper() for w in dmm.writes)
    if any(tok in joined for tok in ("NPLC", "AZER", "AVER", "TRAC")):
        errors.append("dmm_setup_current must not send NPLC/AZER/AVER/TRAC (DMM6500 -113)")
    dmm_ua = SimResource("DMM")
    dmm_setup_current(dmm_ua, range_a=0.0001)
    joined_ua = " ".join(str(w) for w in dmm_ua.writes)
    if "0.0001" in joined_ua or "1e-4" in joined_ua.lower():
        errors.append(
            "dmm_setup_current must not send RANG/CONF 0.0001 (DMM6500 -113 on 1.7.16a)"
        )
    if "SENS:CURR:DC:RANG" in joined.upper() or "SENS:CURR:DC:RANG" in joined_ua.upper():
        errors.append(
            "dmm_setup_current must not send :SENS:CURR:DC:RANG "
            "(DMM6500 -113; CONF:CURR:DC 0.01 is enough)"
        )

    voh_126 = for_test("voh", family="logic", part="rs1g126")
    if "RS0204" in str(voh_126.get("detail") or ""):
        errors.append("rs1g126 voh stimulus must not say RS0204")
    ioz_126 = for_test("ioz", family="logic", part="rs1g126")
    if ioz_126.get("wave") != "DC":
        errors.append(f"rs1g126 ioz wave {ioz_126.get('wave')!r} want DC")
    if "AWG" in str(ioz_126.get("detail") or "").upper():
        errors.append("rs1g126 ioz stimulus must not require AWG")
    if "PSU CH3" not in str(ioz_126.get("detail") or ""):
        errors.append("rs1g126 ioz stimulus must name PSU CH3 OE")
    cin_st = for_test("cin", family="logic")
    if cin_st.get("sweep") != "freq":
        errors.append("cin stimulus must declare sweep=freq")
    delta_st = for_test("delta_supply_current", family="logic")
    if delta_st.get("sweep") != "vcc":
        errors.append("delta_supply_current stimulus must declare sweep=vcc")
    iplus_st = for_test("iplus", family="switch")
    if iplus_st.get("sweep") != "vcc":
        errors.append("iplus stimulus must declare sweep=vcc")
    if errors:
        print("FAIL check_stimulus:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_stimulus SQU/SIN/PULS/DC + LOAD INF + PSU ON/OFF + logic SC70-5 board")
    return 0


if __name__ == "__main__":
    sys.exit(main())
