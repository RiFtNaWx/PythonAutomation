"""Self-check: measurement stamp honesty vs limits yaml.

Run: python -m ate.core.check_specs_datalog
"""
from __future__ import annotations

import sys


def main() -> int:
    errors: list[str] = []
    from ate.core.specs import (
        any_fail,
        enrich_measurement,
        judge_value,
        load_part_specs,
        measurements_from_result,
    )

    if judge_value(0.1, -1, 1) != "pass":
        errors.append("in-window pass")
    if judge_value(9, None, 1) != "fail":
        errors.append("over max fail")
    if judge_value(float("nan"), None, 3) != "fail":
        errors.append("NaN with a max must fail")
    nested = enrich_measurement(
        {"id": "Sub_results.ICC_OE_HIGH_A_HIGH.at_VCC", "value": 5.5},
        specs=load_part_specs("rs1g126"),
        test_id="icc",
    )
    if nested.get("result") == "fail" or nested.get("max") == 1.0:
        errors.append(f"ICC at_VCC must not inherit ICC_uA max, got {nested}")
    nested_blob = {
        "summary": "ICC",
        "data": {
            "Test": "ICC",
            "Sub_results": {
                "ICC_OE_HIGH_A_HIGH": {"worst_uA": 0.084, "at_VCC": 5.5},
            },
        },
        "measurements": [],
    }
    nested_meas = measurements_from_result(
        nested_blob, test_id="icc", part_key="rs1g126"
    )
    if any_fail(nested_meas):
        errors.append(f"empty-measurements ICC must not fail on at_VCC, got {nested_meas}")
    if any("at_VCC" in str(m.get("id")) for m in nested_meas):
        errors.append(f"prefer spec ids must drop nested at_VCC, got {nested_meas}")
    specs = load_part_specs("rs622")
    row = enrich_measurement({"id": "VOS_mV", "value": 0.7}, specs=specs, test_id="vos_sweep")
    if row.get("result") != "pass" or row.get("max") != 3.0:
        errors.append(f"VOS enrich {row}")
    row2 = enrich_measurement({"id": "VOS_mV", "value": 9}, specs=specs, test_id="vos_sweep")
    if row2.get("result") != "fail":
        errors.append(f"VOS over max {row2}")
    from ate.tests.opa.noise import input_referred_uvpp
    from ate.tests.opa.mapped_dc import CASES

    if abs(input_referred_uvpp(0.011011, 1001) - 11.0) > 0.05:
        errors.append("noise input-referred math")
    if any(c.test_id == "noise" for c in CASES):
        errors.append("noise must not stay a mapped_dc screenshot stub")
    en = next((s for s in specs if s.get("id") == "EN_1kHz_nVrtHz"), {})
    if en.get("typ") != 11:
        errors.append(f"EN_1kHz typ must be 11 from RS62X table, got {en}")
    vn = enrich_measurement({"id": "VN_IN_PP_uV", "value": 12}, specs=specs, test_id="noise")
    if vn.get("result") != "unspec":
        errors.append(f"VN_IN_PP_uV must stay unspec without min/max, got {vn}")
    from pathlib import Path
    import tempfile

    root = Path(__file__).resolve().parents[1]
    vos_src = (root / "tests" / "opa" / "vos.py").read_text(encoding="utf-8")
    if '"id": "VOS_mV"' not in vos_src:
        errors.append("vos_sweep must return VOS_mV measurement (not only fit.vos_mV)")
    if "CHAN2" not in vos_src:
        errors.append("vos_sweep Path B must read MSO CHAN2 VOUT")
    if "from opa_tests" in vos_src or "import opa_tests" in vos_src:
        errors.append("vos_sweep must not wrap opa_tests CHAN1=AWG")
    acg_src = (root / "tests" / "opa" / "ac_gain.py").read_text(encoding="utf-8")
    if '"id": "GAIN_VV"' not in acg_src:
        errors.append("ac_gain_check must stamp GAIN_VV")
    if "from opa_tests" in acg_src or "import opa_tests" in acg_src:
        errors.append("ac_gain_check must not wrap opa_tests CHAN1=AWG")
    gain_row = enrich_measurement({"id": "GAIN_VV", "value": 201}, specs=specs, test_id="ac_gain_check")
    if gain_row.get("result") != "unspec" or gain_row.get("typ") != 201:
        errors.append(f"GAIN_VV must stay unspec typ 201 (not AOL_dB min/max), got {gain_row}")
    settle_row = enrich_measurement({"id": "SETTLE_VPP_V", "value": 2.0}, specs=specs, test_id="settling")
    if settle_row.get("result") != "unspec":
        errors.append(f"SETTLE_VPP_V must stay unspec (not 0.1% SETTLE_us), got {settle_row}")
    settle_src = (root / "tests" / "opa" / "settling.py").read_text(encoding="utf-8")
    if "SETTLE_us" in settle_src:
        errors.append("settling must not stamp SETTLE_us")
    if '"id": "SETTLE_VPP_V"' not in settle_src:
        errors.append("settling leftover must stamp SETTLE_VPP_V")
    aol = next((s for s in specs if s.get("id") == "AOL_dB"), {})
    if aol.get("test") != "aol":
        errors.append("AOL_dB must stay bound to mapped aol, not ac_gain_check")
    voh_src = (root / "tests" / "logic" / "ariff_dc.py").read_text(encoding="utf-8")
    if "VOH_{" not in voh_src:
        errors.append("voh_load must emit VOH_* measurements")
    if "VIH_{" not in voh_src:
        errors.append("vih_vil must emit VIH_* measurements")
    if "ICC_uA" not in voh_src:
        errors.append("supply_current_sweep must return ICC_uA")
    iplus_src = (root / "tests" / "lim" / "rs2323.py").read_text(encoding="utf-8")
    if "IPLUS_uA" not in iplus_src:
        errors.append("iplus must return IPLUS_uA")
    if "IOZ_uA" not in iplus_src or "ION_uA" not in iplus_src:
        errors.append("leakage_off/on must stamp IOZ_uA / ION_uA")
    if '"id": "RON_ohm"' not in iplus_src:
        errors.append("ron must stamp RON_ohm")
    if '"id": "TON_ns"' not in iplus_src or '"id": "TOFF_ns"' not in iplus_src:
        errors.append("ton_toff must stamp TON_ns / TOFF_ns")
    if "CON_pF" not in iplus_src or "TBBM_ns" not in iplus_src:
        errors.append("con_coff/tbbm must stamp CON_pF / TBBM_ns")
    if "VTH_V" not in iplus_src:
        errors.append("vth must stamp VTH_V")
    iso_src = (root / "tests" / "lim" / "iso.py").read_text(encoding="utf-8")
    if '"id": "ISO_dB"' not in iso_src:
        errors.append("iso must stamp ISO_dB")
    if "simulated" not in iso_src:
        errors.append("iso must leftover-couple SIM CHAN2 (G11 is not COM residual)")
    if "chan2_off_vpp" not in iso_src:
        errors.append("iso must query CHAN2 on SIM then leftover-couple")
    xtalk_src = (root / "tests" / "lim" / "xtalk.py").read_text(encoding="utf-8")
    if '"id": "XTALK_dB"' not in xtalk_src:
        errors.append("xtalk must stamp XTALK_dB")
    if "simulated" not in xtalk_src:
        errors.append("xtalk must leftover-couple SIM CHAN2 (G11 is not COM2 residual)")
    if "chan2_off_vpp" not in xtalk_src:
        errors.append("xtalk must query CHAN2 on SIM then leftover-couple")
    usb_src = (root / "tests" / "lim" / "rs2227.py").read_text(encoding="utf-8")
    if "USB_ISO_dB" not in usb_src:
        errors.append("usb_iso must stamp USB_ISO_dB")
    if "USB_XTALK_dB" not in usb_src:
        errors.append("usb_xtalk must stamp USB_XTALK_dB")
    if "simulated" not in usb_src:
        errors.append("usb_iso must leftover-couple SIM CHAN2 (G11 is not HSD residual)")
    if "chan2_off_vpp" not in usb_src:
        errors.append("usb_iso must query CHAN2 on SIM then leftover-couple")
    psrr_src = (root / "tests" / "opa" / "psrr.py").read_text(encoding="utf-8")
    if '"id": "PSRR_dB"' not in psrr_src:
        errors.append("psrr Path B must stamp PSRR_dB")
    cmrr_src = (root / "tests" / "opa" / "cmrr.py").read_text(encoding="utf-8")
    if '"id": "CMRR_dB"' not in cmrr_src:
        errors.append("cmrr Path B must stamp CMRR_dB")
    pon_src = (root / "tests" / "opa" / "power_on.py").read_text(encoding="utf-8")
    if '"id": "POWERON_ns"' not in pon_src:
        errors.append("power_on_time Path B must stamp POWERON_ns")
    vohl_src = (root / "tests" / "opa" / "vohl.py").read_text(encoding="utf-8")
    if '"id": "VOH_V"' not in vohl_src or '"id": "VOL_V"' not in vohl_src:
        errors.append("vohl Path B must stamp VOH_V / VOL_V")
    buf_src = (root / "tests" / "opa" / "buffer_steps.py").read_text(encoding="utf-8")
    if '"id": "OVERSHOOT"' not in buf_src or '"id": "LSSR_VPP_V"' not in buf_src:
        errors.append("sssr/lssr must stamp OVERSHOOT / LSSR_VPP_V")
    ort_src = (root / "tests" / "opa" / "ort.py").read_text(encoding="utf-8")
    if '"id": "ORT_POS_us"' not in ort_src or '"id": "ORT_NEG_us"' not in ort_src:
        errors.append("ort Path B must stamp ORT_POS_us / ORT_NEG_us")
    pw_src = (root / "tests" / "logic" / "pulse_width.py").read_text(encoding="utf-8")
    if '"id": "PULSE_ns"' not in pw_src:
        errors.append("pulse_width must stamp PULSE_ns")
    sh_src = (root / "tests" / "logic" / "serial_shift.py").read_text(encoding="utf-8")
    if "Q7_HIGH_V" not in sh_src:
        errors.append("serial_shift must stamp Q7_HIGH_V")
    wraps_src = (root / "tests" / "logic" / "wraps.py").read_text(encoding="utf-8")
    if "cmos_prop" not in wraps_src or "rs29511_prop" not in wraps_src:
        errors.append("wraps tp/tidle must route Path B cmos_prop / rs29511_prop")
    if "from logic_tests" in wraps_src or "import logic_tests" in wraps_src:
        errors.append("wraps must not import repo-root logic goldens")
    if 'id="ten"' in wraps_src or 'id="tdis"' in wraps_src:
        errors.append("wraps.py must not register ten/tdis (oe_timing Path B owns them)")
    oe_src = (root / "tests" / "logic" / "oe_timing.py").read_text(encoding="utf-8")
    if "TEN_ns" not in oe_src or "TDIS_ns" not in oe_src:
        errors.append("oe_timing Path B must stamp TEN_ns / TDIS_ns")
    if "oe_active" not in oe_src:
        errors.append("oe_timing must read part yaml oe_active")
    if "READY" not in oe_src or "rs29511" not in oe_src:
        errors.append("oe_timing must Path B RS29511 EN->READY")
    prop_src = (root / "tests" / "logic" / "rs29511_prop.py").read_text(encoding="utf-8")
    if "TPD_PHL_ns" not in prop_src or "hotswap_prop" not in prop_src:
        errors.append("rs29511_prop Path B must stamp TPD_PHL_ns")
    cmos_src = (root / "tests" / "logic" / "cmos_prop.py").read_text(encoding="utf-8")
    if "TPD_PHL_ns" not in cmos_src or "cmos_prop" not in cmos_src:
        errors.append("cmos_prop Path B must stamp TPD_PHL_ns")
    dc_src = (root / "tests" / "logic" / "rs29511_dc.py").read_text(encoding="utf-8")
    if "ICC_uA" not in dc_src or "VOUT_V" not in dc_src or "CAP_pF" not in dc_src:
        errors.append("rs29511_dc Path B must stamp ICC_uA / VOUT_V / CAP_pF")
    rs295_specs = load_part_specs("rs29511")
    icc295 = next((s for s in rs295_specs if s.get("id") == "ICC_uA"), {})
    if float(icc295.get("max") or 0) != 4500:
        errors.append(f"rs29511 ICC_uA max must be 4500 uA (4.5 mA PDF), got {icc295}")
    cap295 = next((s for s in rs295_specs if s.get("id") == "CAP_pF"), {})
    if float(cap295.get("max") or 0) != 10:
        errors.append(f"rs29511 CAP_pF max must be 10 (CIO SDA/SCL), got {cap295}")
    rs0204_src = (root / "tests" / "logic" / "rs0204.py").read_text(encoding="utf-8")
    if "VOH_DROP_V" not in rs0204_src or "ICC_uA" not in rs0204_src:
        errors.append("rs0204 voh/icc must return VOH_DROP_V and ICC_uA")
    if "0.65" not in rs0204_src or "trip-point" not in rs0204_src:
        errors.append("rs0204 vih must apply 0.65*VCCA, not judge trip against VIH min")
    cap_src = (root / "tests" / "logic" / "eugene_cap.py").read_text(encoding="utf-8")
    if '"id": "CPD_pF"' not in cap_src or '"id": "CIN_pF"' not in cap_src:
        errors.append("cin/cpd must stamp CIN_pF/CPD_pF from I/(V*f)")
    g07 = load_part_specs("rs1g07")
    if not any(s.get("id") == "CPD_pF" and s.get("typ") == 6.0 for s in g07):
        errors.append("rs1g07 limits must include datasheet CPD_pF typ 6")
    from ate.core.specs import mock_demo_measurements

    vih_demo = mock_demo_measurements("vih", part_key="rs0204")
    vih_r = next((m for m in vih_demo if m.get("id") == "VIH_RATIO"), None)
    if not vih_r or vih_r.get("result") != "pass" or vih_r.get("min") != 0.65:
        errors.append(f"DEMO rs0204 vih VIH_RATIO must PASS min 0.65, got {vih_r}")
    icc_demo = mock_demo_measurements("supply_current_sweep", part_key="rs1g08")
    if not any(m.get("id") == "ICC_uA" for m in icc_demo):
        errors.append(f"DEMO supply_current_sweep must stamp ICC_uA, got {icc_demo}")
    voh_demo = mock_demo_measurements("voh_load", part_key="rs1g08")
    v45 = next((m for m in voh_demo if m.get("id") == "VOH_4p5V"), None)
    if not v45 or v45.get("result") != "pass" or v45.get("min") != 3.8:
        errors.append(f"DEMO voh_load VOH_4p5V must PASS min 3.8, got {v45}")
    v165 = next((m for m in voh_demo if m.get("id") == "VOH_1p65V"), None)
    if not v165 or v165.get("result") != "pass" or v165.get("min") != 1.2:
        errors.append(f"DEMO voh_load VOH_1p65V must PASS min 1.2, got {v165}")
    voh34 = mock_demo_measurements("voh_load", part_key="rs1gt34")
    if any(m.get("id") == "VOH_1p65V" for m in voh34):
        errors.append("rs1gt34 must not stamp G-family 1.65 V VOH")
    v20 = next((m for m in voh34 if m.get("id") == "VOH_2p0V"), None)
    if not v20 or v20.get("result") != "pass" or v20.get("min") != 1.6:
        errors.append(f"DEMO rs1gt34 VOH_2p0V must PASS min 1.6, got {v20}")
    voh14 = mock_demo_measurements("voh_load", part_key="rs1g14")
    v14 = next((m for m in voh14 if m.get("id") == "VOH_4p5V"), None)
    if not v14 or v14.get("result") != "pass" or v14.get("min") != 3.8:
        errors.append(f"DEMO rs1g14 VOH_4p5V must PASS min 3.8, got {v14}")
    voh08gt = mock_demo_measurements("voh_load", part_key="rs1gt08")
    if any(m.get("id") == "VOH_1p65V" for m in voh08gt):
        errors.append("rs1gt08 must not stamp G-family 1.65 V VOH")
    vol07 = mock_demo_measurements("vol_load", part_key="rs1g07")
    if any(str(m.get("id") or "").startswith("VOH_") for m in vol07):
        errors.append("rs1g07 vol_load must not stamp VOH_*")
    if not any(m.get("id") == "VOL_5p0V" for m in vol07):
        errors.append(f"DEMO rs1g07 vol_load missing VOL_5p0V, got {vol07}")
    gbw_demo = mock_demo_measurements("gbw", part_key="rs622")
    gbw = next((m for m in gbw_demo if m.get("id") == "GBW_MHz"), None)
    if not gbw or gbw.get("result") != "unspec":
        errors.append(f"DEMO gbw must stay unspec without min/max, got {gbw}")
    psrr_demo = mock_demo_measurements("psrr", part_key="rs622")
    psrr = next((m for m in psrr_demo if m.get("id") == "PSRR_dB"), None)
    if not psrr or psrr.get("result") != "pass" or psrr.get("min") != 78:
        errors.append(f"DEMO psrr must PASS PSRR_dB min 78 from RS62X 7.4, got {psrr}")
    cmrr_demo = mock_demo_measurements("cmrr", part_key="rs622")
    cmrr = next((m for m in cmrr_demo if m.get("id") == "CMRR_dB"), None)
    if not cmrr or cmrr.get("result") != "pass" or cmrr.get("min") != 74:
        errors.append(f"DEMO cmrr must PASS CMRR_dB min 74 from RS62X 7.4, got {cmrr}")
    vohl_demo = mock_demo_measurements("vohl", part_key="rs622")
    voh = next((m for m in vohl_demo if m.get("id") == "VOH_V"), None)
    if not voh or voh.get("result") != "unspec" or voh.get("min") is not None:
        errors.append(f"DEMO vohl VOH_V must stay unspec without min/max, got {voh}")
    ort_demo = mock_demo_measurements("ort", part_key="rs622")
    ort_pos = next((m for m in ort_demo if m.get("id") == "ORT_POS_us"), None)
    if not ort_pos or ort_pos.get("result") != "unspec" or ort_pos.get("min") is not None:
        errors.append(f"DEMO ort ORT_POS_us must stay unspec without min/max, got {ort_pos}")
    from ate.reporting.sts_datalog import export_sts

    tmp = Path(tempfile.mkdtemp(prefix="ate_sts_"))
    exported = export_sts(
        {
            "header": {"time": "t"},
            "identity": {"part": "RS622", "operator": "Eugene"},
            "steps": [
                {
                    "test_id": "gbw",
                    "dut": 1,
                    "success": True,
                    "measurements": [
                        {
                            "id": "GBW_MHz",
                            "unit": "MHz",
                            "typ": 7,
                            "value": 7,
                            "result": "unspec",
                        }
                    ],
                }
            ],
        },
        tmp,
    )
    pdf = Path(exported["pdf"]).read_bytes()
    if b"Parameter" not in pdf or b"GBW_MHz" not in pdf:
        errors.append("STS PDF must be a column table containing Parameter and GBW_MHz")
    extra = export_sts(
        {
            "header": {"time": "t"},
            "identity": {"part": "RS1G07", "operator": "Eugene"},
            "params": {"dut_indices": [8], "channels": ["CHA"]},
            "steps": [
                {
                    "test_id": "cin",
                    "dut": 8,
                    "channel": "CHA",
                    "success": True,
                    "measurements": [
                        {"id": "CIN_pF", "unit": "pF", "value": 4, "result": "pass"}
                    ],
                }
            ],
        },
        tmp,
    )
    pdf8 = Path(extra["pdf"]).read_bytes()
    if b"CIN_pF" not in pdf8 or b"8" not in pdf8:
        errors.append("STS PDF must keep DUT 8 / add-remove rows without a 4-DUT template")
    md8 = Path(extra["markdown"]).read_text(encoding="utf-8")
    if "Channel" not in md8 or "CHA" not in md8:
        errors.append("STS markdown must print Channel for each row")
    sw = load_part_specs("rs2323")
    if any(s.get("id") in ("SR_Vus", "GBW_MHz") for s in sw):
        errors.append("rs2323 must not carry RS222 opamp slew/GBW")
    ldo = load_part_specs("rs3213")
    if any(s.get("id") in ("SR_Vus", "GBW_MHz") for s in ldo):
        errors.append("rs3213 LDO must not carry RS358 opamp slew/GBW")
    from ate.core.lookup import INDEX_PATH

    if not INDEX_PATH.is_file():
        errors.append("build datasheets.yaml first (check_lookup)")
    if errors:
        print("FAIL check_specs_datalog:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_specs_datalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
