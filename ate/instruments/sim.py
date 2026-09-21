"""Fake PyVISA resources so DEMO / START can run with no USB.

SCPI coverage is the subset psu_setup / generator_setup / dmm_setup / scope_setup
actually send. Not a full instrument model.
"""
from __future__ import annotations

import re
from io import BytesIO
from typing import Any

SIM_MAP = {
    "MSO": "SIM::MSO5072",
    "PSU": "SIM::DP832",
    "AWG": "SIM::DG811",
    "DMM": "SIM::DMM6500",
}

_IDN = {
    "MSO": "RIGOL TECHNOLOGIES,MSO5072,SIM,0.0",
    "PSU": "RIGOL TECHNOLOGIES,DP832,SIM,0.0",
    "AWG": "RIGOL TECHNOLOGIES,DG811,SIM,0.0",
    "DMM": "KEITHLEY INSTRUMENTS,DMM6500,SIM,0.0",
}

def _awg_blank() -> dict[str, Any]:
    return {"func": "SQU", "freq": 1000.0, "vpp": 1.0, "offs": 0.0, "out": "OFF"}


# Shared AWG/PSU -> scope/DMM coupling (separate SimResource instances).
# Do not assume powered: psu_on/out start OFF; receivers follow drive.
# awg[1]/awg[2] are live; func/freq/vpp/out stay CH1 aliases for sim_bus UI.
_BUS: dict[str, Any] = {
    "awg": {1: _awg_blank(), 2: _awg_blank()},
    "func": "SQU",
    "freq": 1000.0,
    "vpp": 1.0,
    "out": "OFF",
    "psu_on": False,
    "psu_v": 0.0,
    "psu_v2": 0.0,
    "psu_v3": 0.0,
    "psu_ch2_on": False,
    "psu_ch3_on": False,
    "timebase": 1e-6,
    "vin_prev": None,
    "y_invert": False,
    "schmitt": False,
    "ldo_dut": False,
    "ldo_vout_set": 3.3,
}


def _publish_awg() -> None:
    awg = _BUS.get("awg") or {}
    c1 = awg.get(1) or _awg_blank()
    any_on = any(str((awg.get(i) or {}).get("out")) == "ON" for i in (1, 2))
    _BUS["func"] = c1.get("func") or "SQU"
    _BUS["freq"] = float(c1.get("freq") or 0.0)
    _BUS["vpp"] = float(c1.get("vpp") or 0.0)
    _BUS["out"] = "ON" if any_on else "OFF"


def reset_bus() -> None:
    _BUS["awg"] = {1: _awg_blank(), 2: _awg_blank()}
    _BUS.update(
        func="SQU",
        freq=1000.0,
        vpp=1.0,
        out="OFF",
        psu_on=False,
        psu_v=0.0,
        psu_v2=0.0,
        psu_v3=0.0,
        psu_ch2_on=False,
        psu_ch3_on=False,
        timebase=1e-6,
        vin_prev=None,
        y_invert=False,
        schmitt=False,
        logic_loaded=None,
        open_drain=False,
        ldo_dut=False,
        ldo_vout_set=3.3,
    )


def set_y_invert(on: bool) -> None:
    """DUT Y polarity. True = Schmitt inverter (RS1G14). Default buffer."""
    _BUS["y_invert"] = bool(on)


def set_schmitt(on: bool) -> None:
    """DUT input kind. True = VT+/VT- hysteresis (RS1G14 / RS1G97). Default CMOS."""
    _BUS["schmitt"] = bool(on)


def set_logic_loaded(mode: str | None) -> None:
    """Path B loaded VOH/VOL hook for SIM DMM. voh_sink | vol_source | None."""
    _BUS["logic_loaded"] = str(mode or "").strip() or None


def set_open_drain(on: bool) -> None:
    _BUS["open_drain"] = bool(on)


def set_ldo_dut(on: bool, vout_set: float = 3.3) -> None:
    """Path B LDO: DMM on VOUT. Do not infer from CH3 (that broke RS1G126 OE)."""
    _BUS["ldo_dut"] = bool(on)
    _BUS["ldo_vout_set"] = float(vout_set) if on else 3.3


def bus_snapshot() -> dict[str, Any]:
    return dict(_BUS)


def _visa_block(payload: bytes) -> bytes:
    n = str(len(payload))
    return f"#{len(n)}{n}".encode("ascii") + payload


def _sim_png() -> bytes:
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (16, 16), (24, 48, 72)).save(buf, format="PNG")
    return _visa_block(buf.getvalue())


def _norm(cmd: str) -> str:
    return str(cmd or "").strip().upper().replace(" ", "")


def _fnum(raw: str, default: float) -> float:
    text = str(raw or "").strip()
    if not text or text == "DEF":
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _parse_appl(n: str) -> None:
    m = re.search(r":SOUR(\d):APPL:(SIN|SQU|RAMP|PULS|NOIS|DC)(.*)", n)
    if not m:
        return
    ch = int(m.group(1))
    if ch not in (1, 2):
        ch = 1
    func = m.group(2)
    bits = [b for b in m.group(3).split(",") if b != ""]
    freq = _fnum(bits[0] if bits else "", 1000.0)
    vpp = _fnum(bits[1] if len(bits) > 1 else "", 1.0)
    offs = _fnum(bits[2] if len(bits) > 2 else "", 0.0)
    if func == "DC":
        vpp = _fnum(bits[2] if len(bits) > 2 else bits[-1] if bits else "", 0.0)
        freq = 0.0
        offs = vpp
    awg = _BUS.setdefault("awg", {1: _awg_blank(), 2: _awg_blank()})
    st = awg.setdefault(ch, _awg_blank())
    st["func"] = func
    st["freq"] = freq
    st["vpp"] = vpp
    st["offs"] = offs
    _publish_awg()


# MSO5072 analog BW. Rise/fall on SIM is the instrument ceiling, not DUT tr.
_MSO_BW_HZ = 70e6
_MSO_TR_S = 0.35 / _MSO_BW_HZ


def _ch2_oe_dc(c1: dict[str, Any], c2: dict[str, Any]) -> bool:
    """AWG CH2 DC + CH1 toggling: USB MSO CHAN2 is DUT Y, not OE."""
    return (
        str(c2.get("out")) == "ON"
        and str(c2.get("func") or "") == "DC"
        and str(c1.get("out")) == "ON"
        and str(c1.get("func") or "") in ("SQU", "PULS", "RAMP", "SIN")
    )


def _g201_loop(c1: dict[str, Any], c2: dict[str, Any]) -> bool:
    """Research G201: dual matched rails, AWG CH1 on, CH2 off.

    ponytail: small-sine vs G11 GBW is vpp<=10 mVpp (G201 AC) vs ~50 mVpp (GBW).
    Upgrade: board-id SCPI if a third Av appears.
    """
    if str(c2.get("out")) == "ON" or str(c1.get("out")) != "ON":
        return False
    if not _BUS.get("psu_ch2_on"):
        return False
    v1 = float(_BUS.get("psu_v") or 0.0)
    v2 = float(_BUS.get("psu_v2") or 0.0)
    if not (v1 > 0.2 and abs(v1 - v2) < 0.15):
        return False
    func1 = str(c1.get("func") or "")
    if func1 == "DC":
        return True
    vpp1 = float(c1.get("vpp") or 0.0)
    return func1 == "SIN" and 0.0 < vpp1 <= 0.015


def _scope_item(item: str, ch: int) -> float:
    """MSO reading from last AWG APPL. AWG OFF -> no signal received (COUNT 0)."""
    item_u = str(item or "").upper()
    awg = _BUS.get("awg") or {}
    c1 = awg.get(1) or _awg_blank()
    c2 = awg.get(2) or _awg_blank()
    driven = str(c1.get("out")) == "ON" or str(c2.get("out")) == "ON"
    src = c1
    # CH2 DC is OE/control. USB CHAN2 is Y/B. Do not bind CHAN2 to OE DC VPP=0.
    if ch >= 2 and str(c2.get("out")) == "ON" and str(c2.get("func") or "") != "DC":
        src = c2
    vpp = float(src.get("vpp") or 0.0) if driven else 0.001
    freq = float(src.get("freq") or 1000.0)
    func = str(src.get("func") or "SQU")
    if "COUNT" in item_u:
        return 120.0 if driven else 0.0
    if "FREQ" in item_u:
        return freq if driven and freq else 0.0
    if "SLEW" in item_u:
        return (3.7e6 * max(vpp, 0.05)) if driven else 0.0
    if "DELAY" in item_u:
        # ponytail: two SIM windows, not a SPICE model. Upgrade: analog EN/READY.
        # ns-window (timebase < 10 us) -> CMOS / tDISABLE ~50 ns.
        # us-window (RS29511 tIDLE uses 50 us/div) -> 2*timebase (~100 us).
        if not driven:
            return 0.0
        tb = float(_BUS.get("timebase") or 1e-6)
        if tb >= 10e-6:
            return 2.0 * tb
        return 50e-9
    if "PWID" in item_u:
        if not driven:
            return 0.0
        if ch >= 2 and _ch2_oe_dc(c1, c2):
            freq1 = float(c1.get("freq") or 0.0)
            return (0.5 / freq1) if freq1 > 0 else 0.0
        # CHAN2 Q leftover-honest: follow driven src 0.5/f (not 500 ns dummy, not RC).
        freq_src = float(src.get("freq") or 0.0)
        return (0.5 / freq_src) if freq_src > 0 else 0.0
    if "RTIME" in item_u or "FTIME" in item_u:
        if not driven:
            return 0.0
        return _MSO_TR_S
    if "OVER" in item_u:
        # MSO OVERSHOOT. SIM 1-pole has no ring. Not the 0.12 unknown-item dummy.
        return 0.0
    offs = float(src.get("offs") or 0.0)
    dc_level = float(src.get("vpp") or 0.0) if func == "DC" else offs
    # G201 closed-loop: dual matched rails, AWG CH1, MSO CHAN2 = Av*VIN.
    # DC: Vos_dut=0. Small SIN (<=10 mVpp): Av=201 1-pole (f3dB=GBW/201).
    # G11 GBW uses ~50 mVpp -- do not steal that path. CHAN1 stays VIN.
    if ch >= 2 and _g201_loop(c1, c2):
        func1 = str(c1.get("func") or "")
        vin = (
            float(c1.get("vpp") or c1.get("offs") or 0.0)
            if func1 == "DC"
            else float(c1.get("offs") or 0.0)
        )
        av = 201.0
        if "VPP" in item_u or "VAMP" in item_u:
            if func1 == "DC":
                return 0.001
            freq1 = float(c1.get("freq") or 0.0)
            vpp1 = float(c1.get("vpp") or 0.0)
            f3db = 7.0e6 / av
            gain = av / (1.0 + (freq1 / f3db) ** 2) ** 0.5
            return vpp1 * gain
        return av * vin
    if "VAVG" in item_u or "VMEAN" in item_u:
        if not driven:
            # PSU CH2 VIN sweep: MSO CHAN1 on Y must match DMM (same DUT node).
            # Do not skip matched CH1/CH2 (VIN=VCC is a legal logic high).
            if _BUS.get("psu_on") and _BUS.get("psu_ch2_on"):
                return _dmm_volt()
            return 0.001
        if ch >= 2:
            return _dmm_volt()
        return dc_level
    if any(k in item_u for k in ("VPP", "VAMP", "VMAX", "VMIN")):
        if "VMIN" in item_u:
            if not driven:
                return 0.001
            return dc_level if func == "DC" else (offs - abs(vpp) / 2.0)
        if "VMAX" in item_u:
            if not driven:
                return 0.001
            return dc_level if func == "DC" else (offs + abs(vpp) / 2.0)
        if func == "DC":
            return 0.001
        if ch <= 1:
            return vpp if str(c1.get("out")) == "ON" else 0.001
        if _ch2_oe_dc(c1, c2):
            vcc = float(_BUS.get("psu_v") or 0.0)
            v2 = float(_BUS.get("psu_v2") or 0.0)
            oe = float(c2.get("vpp") or c2.get("offs") or 0.0)
            thresh = (vcc / 2.0) if vcc > 0.2 else 0.9
            if oe < thresh:
                return 0.001
            if v2 > vcc + 0.05 and v2 >= 1.2:
                return v2
            vpp1 = float(c1.get("vpp") or 0.0)
            return vpp1 if vpp1 > 0.05 else (vcc if vcc > 0.2 else 0.001)
        if str(c2.get("out")) == "ON":
            return float(c2.get("vpp") or 0.0)
        if not driven:
            return 0.001
        func1 = str(c1.get("func") or "SQU")
        freq1 = float(c1.get("freq") or 0.0)
        vpp1 = float(c1.get("vpp") or 0.0)
        if func1 in ("SQU", "PULS", "RAMP") or freq1 <= 0:
            return vpp1
        # G11 GBW is ~50 mVpp. BUFFER NPR is volts-class -- Av=1, clip to rails.
        # ponytail: vpp>0.2 is BUFFER. Upgrade: fixture-mode if a third Av appears.
        if vpp1 > 0.2:
            vs = abs(float(_BUS.get("psu_v") or 0.0)) + abs(
                float(_BUS.get("psu_v2") or 0.0)
            )
            return min(vpp1, vs) if vs > 0.2 else vpp1
        f3db = 7.0e6 / 11.0
        gain = 11.0 / (1.0 + (freq1 / f3db) ** 2) ** 0.5
        return vpp1 * gain
    # Rigol MSO invalid. USB does not stamp 0.12 for unknown ITEM.
    return 9.91e37


def _psu_ch2_logic_y(vcc: float, vin: float, invert: bool) -> float:
    """Y from PSU CH2 VIN. VCC/2 fails GT VIH max (1.5 at 3.3 V, 2.0 at 5.5 V)."""
    thresh = min(0.4 * vcc, 1.4) if vcc else 0.0
    high, low = (vcc if vcc else 0.001), 0.001
    if invert:
        return low if vin >= thresh else high
    return high if vin >= thresh else low


def _icc_a(vcc: float) -> float:
    """CMOS static ICC. Typ ~0.1 uA class; stay under 1 uA datasheet max."""
    return 5e-8 + 1.0e-7 * max(float(vcc) or 0.0, 0.0)


def _dmm_current() -> float:
    """No PSU ON -> floor. ICC(VCC)+II(VIN); switching I = C(VCC)*V*f."""
    if not _BUS.get("psu_on"):
        return 1e-12
    if _BUS.get("ldo_dut"):
        # IQ: CH1=VOUT bias, CH2=VIN, CH3 off. Voltage tests: CH1=VIN, CH3=EN.
        # Leftover Iq vs VIN, not CMOS ICC from VOUT-bias, not PDF Iq.
        if _BUS.get("psu_ch3_on"):
            vin = float(_BUS.get("psu_v") or 0.0)
        elif _BUS.get("psu_ch2_on"):
            vin = float(_BUS.get("psu_v2") or 0.0)
        else:
            vin = float(_BUS.get("psu_v") or 0.0)
        return _icc_a(vin)
    vcc = float(_BUS.get("psu_v") or 0.0)
    if _BUS.get("psu_ch3_on") and _BUS.get("psu_ch2_on"):
        y = abs(float(_BUS.get("psu_v2") or 0.0))
        return 4e-8 + 8e-9 * y
    i = _icc_a(vcc)
    awg = _BUS.get("awg") or {}
    for ch, st in awg.items():
        if str((st or {}).get("out")) != "ON":
            continue
        func = str(st.get("func") or "")
        freq = float(st.get("freq") or 0.0)
        vpp = float(st.get("vpp") or 0.0)
        if func == "DC":
            k = 6e-9 if int(ch) == 1 else 11e-9
            i += k * abs(vpp)
            if vcc > 0.5 and abs(abs(vpp) - vcc / 2.0) < 0.25:
                i += 1.5e-7
        elif func in ("SQU", "PULS") and freq >= 1e5:
            v = vcc if vcc > 0.2 else (vpp if vpp > 0 else 3.3)
            if v >= 4.5:
                cap = 6e-12
            elif v >= 3.0:
                cap = 4e-12
            else:
                cap = 3e-12
            i += cap * v * freq
    return i


def _ldo_vout() -> float:
    """DMM node = VOUT. VIN=CH1, EN=CH3, CH2=load. Leftover Vdo, not datasheet."""
    vin = float(_BUS.get("psu_v") or 0.0)
    en_on = bool(_BUS.get("psu_ch3_on"))
    en = float(_BUS.get("psu_v3") or 0.0)
    vset = float(_BUS.get("ldo_vout_set") or 3.3)
    if (not en_on) or en < 1.0 or vin <= 0.05:
        return 0.001
    # ponytail: leftover-honest dropout, not PDF Vdo@Iout. Upgrade: part yaml.
    vdo = 0.05
    if vin > vset + vdo:
        vout = vset
    else:
        vout = max(0.001, vin - vdo)
    if _BUS.get("psu_ch2_on"):
        load_v = abs(float(_BUS.get("psu_v2") or 0.0))
        vout = max(0.001, vout - 0.004 * load_v)
    return vout


def _dmm_volt() -> float:
    if not _BUS.get("psu_on"):
        return 0.001
    if _BUS.get("ldo_dut"):
        return _ldo_vout()
    vcc = float(_BUS.get("psu_v") or 0.0)
    v2 = float(_BUS.get("psu_v2") or 0.0)
    ch2 = bool(_BUS.get("psu_ch2_on"))
    dual = ch2 and vcc > 0 and abs(vcc - v2) < 0.05
    mode = _BUS.get("logic_loaded")
    if mode == "voh_sink" and vcc > 0.5:
        return max(vcc * 0.99, 0.001)
    if mode == "vol_source" and vcc > 0.5:
        if _BUS.get("open_drain"):
            return 0.001
        return max(vcc * 0.05, 0.001)
    # Translator VCCB is a logic rail above VCCA. Ariff VOH CH2 is an 80-320 mV
    # load Vref -- treating that as VCCB made SIM VOH equal Vref (SPEC FAIL).
    xlat = ch2 and vcc > 0 and v2 > vcc + 0.05 and v2 >= 1.2
    awg = _BUS.get("awg") or {}
    c1 = awg.get(1) or _awg_blank()
    c2 = awg.get(2) or _awg_blank()
    # RS164: CH1=CLK square, CH2=A DC. Q7 follows A after clocks. Not CH1 VCC.
    clk_data = (
        str(c1.get("out")) == "ON"
        and str(c1.get("func") or "") in ("SQU", "PULS")
        and str(c2.get("out")) == "ON"
        and str(c2.get("func") or "") == "DC"
    )
    if clk_data:
        vin = float(c2.get("vpp") or c2.get("offs") or 0.0)
        thresh = (vcc / 2.0) if vcc else 0.0
        if xlat:
            return v2 if vin >= thresh else 0.001
        return vcc if vin >= thresh else 0.001
    awg_dc = (
        str(_BUS.get("out") or "OFF") == "ON"
        and str(_BUS.get("func") or "") == "DC"
    )
    if awg_dc:
        vin = float(_BUS.get("vpp") or 0.0)
        if dual:
            # OpAmp buffer: Vout follows Vin. Tiny Vs and Vcm leaks ~ datasheet typ dB.
            vs = vcc + v2
            return vin + vin / (10.0 ** (92.0 / 20.0)) + vs / (10.0 ** (93.0 / 20.0))
        # CMOS VT below datasheet VIH max (RS1GT34 class), not 0.5*VCC.
        thresh = (0.32 * vcc + 0.05) if vcc else 0.0
        invert = bool(_BUS.get("y_invert"))
        if xlat and not invert:
            # Level shifter B-side. Trip below 0.35*VCCA so RS0204 VIL at 0.35*VCCA reads low.
            trip = 0.4 * vcc if vcc else thresh
            return v2 if vin >= trip else 0.001
        # CMOS Y. Invert only for Schmitt inverter DUT (RS1G14 Path B).
        # Do not invert AND/buffer/OE/RS164/xlat -- that is a global _dmm_volt invert.
        high, low = vcc, 0.001
        if invert:
            return low if vin >= thresh else high
        return high if vin >= thresh else low
    if ch2 and not dual and not xlat:
        # SeeLim / GT VIH: PSU CH2 is VIN, DMM reads Y. Same node as MSO VAVG.
        vin = v2
        prev = _BUS.get("vin_prev")
        prev_f = float(prev) if prev is not None else vin
        rising = vin >= prev_f - 1e-12
        _BUS["vin_prev"] = vin
        invert = bool(_BUS.get("y_invert"))
        if _BUS.get("schmitt"):
            # ponytail: RS1G97 9.2 VIH/VIL/DVT windows. Upgrade: yaml VT+/VT-.
            trip = (0.56 * vcc) if rising else (0.15 * vcc + 0.10)
            high, low = (vcc if vcc else 0.001), 0.001
            if invert:
                return low if vin >= trip else high
            return high if vin >= trip else low
        return _psu_ch2_logic_y(vcc, vin, invert)
    return vcc


def _meas_reply(n: str) -> str | None:
    if "STATISTIC:ITEM?" in n:
        rest = n.split("ITEM?", 1)[-1]
        parts = rest.split(",")
        stat = parts[0] if parts else "CURRENT"
        item = parts[1] if len(parts) > 1 else "VPP"
        src = parts[2] if len(parts) > 2 else "CHAN1"
        if "COUNT" in stat:
            ch = 2 if "2" in src else 1
            return f"{_scope_item('COUNT', ch):.6g}"
        ch = 2 if "2" in src else 1
        return f"{_scope_item(item, ch):.6g}"
    if "MEAS:ITEM?" in n or "MEASURE:ITEM?" in n:
        rest = n.split("ITEM?", 1)[-1]
        parts = rest.split(",")
        item = parts[0] if parts else "VPP"
        src = parts[1] if len(parts) > 1 else "CHAN1"
        ch = 2 if "2" in src else 1
        return f"{_scope_item(item, ch):.6g}"
    return None


class SimResource:
    """Message-based stand-in: write / query / read_raw / clear / close."""

    def __init__(self, kind: str) -> None:
        self.kind = str(kind or "").upper()
        self.simulated = True
        self.timeout = 3000
        self.writes: list[str] = []
        self.outp = {1: "OFF", 2: "OFF", 3: "OFF", 4: "OFF"}
        self.prot = {
            1: {"VOLT": "OFF", "CURR": "OFF"},
            2: {"VOLT": "OFF", "CURR": "OFF"},
            3: {"VOLT": "OFF", "CURR": "OFF"},
        }
        self.scale = {"1": "0.2", "2": "0.2"}
        self.offs = {"1": "0.208", "2": "-0.208"}
        self.dmm_func = "VOLT"
        self.volt = {1: 0.0, 2: 0.0, 3: 0.0}
        self._pending_raw: bytes | None = None

    def _sync_psu_bus(self) -> None:
        if self.kind != "PSU":
            return
        on = any(self.outp.get(c) == "ON" for c in (1, 2, 3))
        _BUS["psu_on"] = on
        _BUS["psu_v"] = float(self.volt.get(1) or 0.0) if self.outp.get(1) == "ON" else 0.0
        _BUS["psu_ch2_on"] = self.outp.get(2) == "ON"
        _BUS["psu_v2"] = float(self.volt.get(2) or 0.0) if self.outp.get(2) == "ON" else 0.0
        _BUS["psu_ch3_on"] = self.outp.get(3) == "ON"
        _BUS["psu_v3"] = float(self.volt.get(3) or 0.0) if self.outp.get(3) == "ON" else 0.0

    def write(self, cmd: str) -> int:
        text = str(cmd)
        self.writes.append(text)
        n = _norm(text)
        if n == "*RST" or n.startswith("*RST"):
            if self.kind == "DMM":
                self.dmm_func = "VOLT"
        if n.startswith(":OUTPCH") and n.endswith(",ON"):
            ch = int(n[7])
            self.outp[ch] = "ON"
            self._sync_psu_bus()
        elif n.startswith(":OUTPCH") and n.endswith(",OFF"):
            ch = int(n[7])
            self.outp[ch] = "OFF"
            self._sync_psu_bus()
        elif n.startswith(":OUTP") and n.endswith("ON"):
            rest = n[5:]
            if rest[:1].isdigit():
                chn = int(rest[0])
                self.outp[chn] = "ON"
                if self.kind == "AWG":
                    bus = _BUS.setdefault("awg", {1: _awg_blank(), 2: _awg_blank()})
                    if chn in bus:
                        bus[chn]["out"] = "ON"
                    _publish_awg()
                self._sync_psu_bus()
        elif n.startswith(":OUTP") and n.endswith("OFF"):
            rest = n[5:]
            if rest[:1].isdigit():
                chn = int(rest[0])
                self.outp[chn] = "OFF"
                if self.kind == "AWG":
                    bus = _BUS.setdefault("awg", {1: _awg_blank(), 2: _awg_blank()})
                    if chn in bus:
                        bus[chn]["out"] = "OFF"
                    _publish_awg()
                self._sync_psu_bus()
        m_v = re.search(r":SOUR(\d):VOLT(-?[0-9.]+(?:E[+-]?\d+)?)$", n)
        if m_v:
            self.volt[int(m_v.group(1))] = _fnum(m_v.group(2), 0.0)
            self._sync_psu_bus()
        if ":APPL:" in n:
            _parse_appl(n)
        m_off = re.search(
            r":SOUR(\d):VOLT:OFFS(-?[0-9.]+(?:E[+-]?\d+)?)$", n
        )
        if m_off and self.kind == "AWG":
            chn = int(m_off.group(1))
            bus = _BUS.setdefault("awg", {1: _awg_blank(), 2: _awg_blank()})
            st = bus.setdefault(chn, _awg_blank())
            st["offs"] = _fnum(m_off.group(2), 0.0)
            if str(st.get("func") or "") == "DC":
                st["vpp"] = st["offs"]
            _publish_awg()
        m_tb = re.search(
            r"TIMEBASE:MAIN:SCAL(?:E)?(-?[0-9.]+(?:E[+-]?\d+)?)", n
        )
        if m_tb:
            _BUS["timebase"] = _fnum(m_tb.group(1), 1e-6)
        m_sc = re.search(r":?CHAN(\d):SCALE(-?[0-9.]+(?:E[+-]?\d+)?)$", n)
        if m_sc:
            self.scale[m_sc.group(1)] = m_sc.group(2)
        m_of = re.search(r":?CHAN(\d):OFFS(?:ET)?(-?[0-9.]+(?:E[+-]?\d+)?)$", n)
        if m_of:
            self.offs[m_of.group(1)] = m_of.group(2)
        for ch in (1, 2, 3):
            if f":SOUR{ch}:VOLT:PROT:STATON" in n:
                self.prot[ch]["VOLT"] = "ON"
            if f":SOUR{ch}:CURR:PROT:STATON" in n:
                self.prot[ch]["CURR"] = "ON"
        if "CONF:CURR" in n or ("SENS:FUNC" in n and "CURR" in n):
            self.dmm_func = "CURR"
        elif "CONF:CAP" in n or ("SENS:FUNC" in n and "CAP" in n):
            self.dmm_func = "CAP"
        elif "CONF:VOLT" in n or "SENS:FUNC" in n:
            self.dmm_func = "VOLT"
        if ":DISP:DATA?" in n:
            self._pending_raw = _sim_png()
        return len(text)

    def query(self, cmd: str) -> str:
        text = str(cmd)
        n = _norm(text)
        if n.startswith("SYST:ERR") or n.startswith(":SYST:ERR"):
            return '0,"No error"\n'
        if n.startswith(":OUTP?CH"):
            ch = int(n[8])
            return self.outp.get(ch, "OFF") + "\n"
        if n.startswith(":OUTP") and n.endswith("?"):
            rest = n[5:-1]
            if rest.isdigit():
                return self.outp.get(int(rest), "OFF") + "\n"
        for ch in (1, 2, 3):
            if f":SOUR{ch}:VOLT:PROT:STAT?" in n:
                return self.prot[ch]["VOLT"] + "\n"
            if f":SOUR{ch}:CURR:PROT:STAT?" in n:
                return self.prot[ch]["CURR"] + "\n"
        for ch in ("1", "2"):
            if f":CHAN{ch}:SCALE?" in n or f"CHAN{ch}:SCALE?" in n:
                return self.scale[ch] + "\n"
            if f":CHAN{ch}:OFFS?" in n or f"CHAN{ch}:OFFS?" in n:
                return self.offs[ch] + "\n"
        if self.kind == "PSU" and "MEAS:VOLT" in n:
            return f"{float(_BUS.get('psu_v') or 0.0):.6g}\n"
        if "APPL?" in n and self.kind == "AWG":
            m = re.search(r":SOUR(\d):APPL\?", n)
            ch = int(m.group(1)) if m else 1
            st = (_BUS.get("awg") or {}).get(ch) or _awg_blank()
            func = str(st.get("func") or "SQU")
            freq = float(st.get("freq") or 0.0)
            vpp = float(st.get("vpp") or 0.0)
            return f"{func},{freq:.6g},{vpp:.6g},0,0\n"
        if n.startswith(":READ?") or n == "READ?":
            if self.dmm_func == "CURR":
                return f"{_dmm_current():.6g}\n"
            if self.dmm_func == "CAP":
                return "5e-12\n"
            return f"{_dmm_volt():.6g}\n"
        meas = _meas_reply(n)
        if meas is not None:
            return meas + "\n"
        return "0\n"

    def read_raw(self) -> bytes:
        if self._pending_raw is not None:
            data = self._pending_raw
            self._pending_raw = None
            return data
        raise TimeoutError("SIM read_raw empty")

    def clear(self) -> None:
        self._pending_raw = None

    def close(self) -> None:
        return None

    def query_ascii_values(self, cmd: str, **_kw: Any) -> list[float]:
        try:
            return [float(self.query(cmd))]
        except Exception:
            return [0.0]


def loopback_check(
    psu: SimResource | None = None,
    awg: SimResource | None = None,
    scope: SimResource | None = None,
    dmm: SimResource | None = None,
) -> dict[str, Any]:
    """Drive PSU/AWG, assert DMM/MSO received it. Does not assume powered."""
    from psu_setup import power_off, power_on_protected

    reset_bus()
    psu = psu or SimResource("PSU")
    awg = awg or SimResource("AWG")
    scope = scope or SimResource("MSO")
    dmm = dmm or SimResource("DMM")
    checks: list[dict[str, Any]] = []

    def add(cid: str, ok: bool, detail: str) -> None:
        checks.append({"id": cid, "ok": bool(ok), "detail": detail})

    awg.write(":OUTP1 OFF")
    power_off(psu)
    dmm.write(":SENS:FUNC 'CURR:DC'")
    i_off = float(dmm.query(":READ?"))
    add("psu_off_current", i_off < 1e-7, f"I={i_off}")

    power_on_protected(psu, 1, 3.3, 0.1)
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    v_on = float(dmm.query(":READ?"))
    add("psu_on_volt_received", abs(v_on - 3.3) < 0.25, f"V={v_on}")
    dmm.write(":SENS:FUNC 'CURR:DC'")
    i_on = float(dmm.query(":READ?"))
    add("psu_on_icc", 1e-8 < i_on < 2e-6, f"I={i_on}")

    awg.write(":SOUR1:APPL:SQU 1000,1,0,0")
    awg.write(":OUTP1 ON")
    vpp = float(scope.query(":MEASure:STATistic:ITEM? CURRent,VPP,CHAN1"))
    cnt = float(scope.query(":MEASure:STATistic:ITEM? COUNt,PSLewrate,CHAN2"))
    add("awg_vpp_received", abs(vpp - 1.0) < 0.05, f"Vpp={vpp}")
    add("awg_count_received", cnt >= 80, f"COUNT={cnt}")

    awg.write(":OUTP1 OFF")
    vpp_off = float(scope.query(":MEASure:STATistic:ITEM? CURRent,VPP,CHAN1"))
    cnt_off = float(scope.query(":MEASure:STATistic:ITEM? COUNt,PSLewrate,CHAN2"))
    add("awg_off_vpp", vpp_off < 0.02, f"Vpp={vpp_off}")
    add("awg_off_count", cnt_off < 10, f"COUNT={cnt_off}")

    power_off(psu)
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    v_off = float(dmm.query(":READ?"))
    add("psu_off_volt", v_off < 0.05, f"V={v_off}")

    reset_bus()
    power_on_protected(psu, 1, 2.5, 0.1)
    power_on_protected(psu, 2, 2.5, 0.1)
    awg.write(":SOUR1:APPL:SIN 500,0.004,0,0")
    awg.write(":OUTP1 ON")
    vpp1_g201 = float(scope.query(":MEAS:ITEM? VPP,CHAN1"))
    vpp2_g201 = float(scope.query(":MEAS:ITEM? VPP,CHAN2"))
    add("g201_chan1_vin", abs(vpp1_g201 - 0.004) < 0.0005, f"Vpp1={vpp1_g201}")
    av201 = (vpp2_g201 / 0.004) if vpp1_g201 else 0.0
    add("g201_chan2_av201", 180.0 < av201 < 220.0, f"Av={av201}")
    awg.write(":SOUR1:APPL:SIN 1000,0.05,0,0")
    vpp2_g11 = float(scope.query(":MEAS:ITEM? VPP,CHAN2"))
    av11 = (vpp2_g11 / 0.05) if vpp2_g11 else 0.0
    add("g11_gbw_av11", 9.0 < av11 < 12.0, f"Av={av11}")

    reset_bus()
    power_on_protected(psu, 1, 3.3, 0.1)
    power_on_protected(psu, 2, 0.0, 0.05)
    power_on_protected(psu, 3, 0.0, 0.05)
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    y_lo = float(dmm.query(":READ?"))
    add("seelim_ch3_0v_y_low", y_lo < 0.2, f"Y={y_lo}")
    psu.write(":SOUR2:VOLT 3.3")
    y_hi = float(dmm.query(":READ?"))
    add("seelim_ch2_sweep_y_high", y_hi > 2.5, f"Y={y_hi}")

    reset_bus()
    power_on_protected(psu, 1, 3.3, 0.1)
    power_on_protected(psu, 2, 1.20, 0.05)
    y_gt_lo = float(scope.query(":MEAS:ITEM? VAVG,CHAN1"))
    add("gt_mso_vin_1p20_y_low", y_gt_lo < 0.5, f"Y={y_gt_lo}")
    psu.write(":SOUR2:VOLT 1.45")
    y_gt_hi = float(scope.query(":MEAS:ITEM? VAVG,CHAN1"))
    add("gt_mso_vin_1p45_y_high", y_gt_hi > 2.5, f"Y={y_gt_hi}")

    dmm.write(":SENS:FUNC 'VOLT:DC'")
    for vin, tag in ((1.20, "1p20"), (1.45, "1p45"), (3.3, "3p3")):
        reset_bus()
        power_on_protected(psu, 1, 3.3, 0.1)
        power_on_protected(psu, 2, vin, 0.05)
        vd = float(dmm.query(":READ?"))
        vs = float(scope.query(":MEAS:ITEM? VAVG,CHAN1"))
        add(f"dmm_mso_y_agree_{tag}", abs(vd - vs) < 0.05, f"DMM={vd} MSO={vs} VIN={vin}")

    reset_bus()
    set_schmitt(True)
    power_on_protected(psu, 1, 3.3, 0.1)
    power_on_protected(psu, 2, 1.45, 0.05)
    vd_s = float(dmm.query(":READ?"))
    vs_s = float(scope.query(":MEAS:ITEM? VAVG,CHAN1"))
    add(
        "dmm_mso_y_agree_schmitt_1p45",
        abs(vd_s - vs_s) < 0.05 and vd_s < 0.5,
        f"DMM={vd_s} MSO={vs_s}",
    )
    set_schmitt(False)

    reset_bus()
    power_on_protected(psu, 1, 3.3, 0.1)
    awg.write(":SOUR1:APPL:DC DEF,DEF,0.5")
    awg.write(":OUTP1 ON")
    vd_a = float(dmm.query(":READ?"))
    vs2 = float(scope.query(":MEAS:ITEM? VAVG,CHAN2"))
    add(
        "dmm_mso_chan2_y_agree_vin_1p20",
        abs(vd_a - vs2) < 0.05 and vd_a < 0.5,
        f"DMM={vd_a} MSO2={vs2}",
    )

    reset_bus()
    power_on_protected(psu, 1, 3.3, 0.1)
    power_on_protected(psu, 2, 0.0, 0.05)
    power_on_protected(psu, 3, 3.3, 0.05)
    y_oe = float(dmm.query(":READ?"))
    add("seelim_oe_high_a0_y_low", y_oe < 0.2, f"Y={y_oe}")

    reset_bus()
    power_on_protected(psu, 1, 5.0, 0.1)
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    set_y_invert(True)
    awg.write(":SOUR1:APPL:DC DEF,DEF,5")
    awg.write(":OUTP1 ON")
    y_a_hi = float(dmm.query(":READ?"))
    add("inverter_a_high_y_not_vcc", y_a_hi < 0.5, f"Y={y_a_hi}")
    awg.write(":SOUR1:APPL:DC DEF,DEF,0")
    y_a_lo = float(dmm.query(":READ?"))
    add("inverter_a_low_y_vcc", abs(y_a_lo - 5.0) < 0.25, f"Y={y_a_lo}")
    set_y_invert(False)
    awg.write(":SOUR1:APPL:DC DEF,DEF,5")
    y_buf = float(dmm.query(":READ?"))
    add("buffer_a_high_y_vcc_after_invert", abs(y_buf - 5.0) < 0.25, f"Y={y_buf}")

    reset_bus()
    power_on_protected(psu, 1, 5.0, 0.1)
    awg.write(":SOUR1:APPL:SQU 1000,5,2.5,0")
    awg.write(":OUTP1 ON")
    awg.write(":SOUR2:APPL:DC DEF,DEF,5")
    awg.write(":OUTP2 ON")
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    q_hi = float(dmm.query(":READ?"))
    awg.write(":SOUR2:APPL:DC DEF,DEF,0")
    q_lo = float(dmm.query(":READ?"))
    add("serial_q7_follows_a_high", abs(q_hi - 5.0) < 0.25, f"Qhi={q_hi}")
    add("serial_q7_follows_a_low", q_lo < 0.2, f"Qlo={q_lo}")
    awg.write(":OUTP2 OFF")
    pwid2 = float(scope.query(":MEASure:STATistic:ITEM? CURRent,PWIDth,CHAN2"))
    add("chan2_pwid_follows_ch1", abs(pwid2 - 5e-4) < 5e-5, f"PWID2={pwid2}")

    reset_bus()
    power_on_protected(psu, 1, 2.75, 0.1)
    power_on_protected(psu, 2, 2.75, 0.1)
    awg.write(":SOUR1:APPL:SIN 1000,6,0,0")
    awg.write(":OUTP1 ON")
    v_npr = float(scope.query(":MEAS:ITEM? VPP,CHAN2"))
    add("npr_chan2_not_g11", 0.4 < v_npr < 12.0, f"Vpp2={v_npr}")
    ov = float(scope.query(":MEAS:ITEM? OVERSHOOT,CHAN2"))
    add("overshoot_not_dummy", abs(ov - 0.12) > 1e-6, f"OV={ov}")
    per = float(scope.query(":MEAS:ITEM? PERIod,CHAN1"))
    add(
        "unknown_item_not_dummy",
        abs(per) > 1e10 and abs(per - 0.12) > 1e-6,
        f"PER={per}",
    )

    reset_bus()
    set_ldo_dut(True, 3.3)
    power_on_protected(psu, 1, 5.0, 0.4)
    power_on_protected(psu, 3, 5.0, 0.05)
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    v_lir_hi = float(dmm.query(":READ?"))
    add(
        "ldo_vout_not_vin",
        abs(v_lir_hi - 3.3) < 0.15 and abs(v_lir_hi - 5.0) > 0.5,
        f"V={v_lir_hi}",
    )
    psu.write(":SOUR1:VOLT 3.4")
    v_lir_lo = float(dmm.query(":READ?"))
    lir_mv = abs(v_lir_hi - v_lir_lo) * 1000.0
    add("ldo_lir_not_vin_alias", abs(lir_mv - 1600.0) > 1.0, f"LIR={lir_mv}")
    power_on_protected(psu, 2, 0.5, 0.05)
    v_load = float(dmm.query(":READ?"))
    add("ldo_load_not_schmitt", v_load > 2.5, f"V={v_load}")
    reset_bus()
    set_ldo_dut(True, 3.3)
    power_off(psu)
    power_on_protected(psu, 1, 3.3, 0.1)
    power_on_protected(psu, 2, 2.0, 0.1)
    dmm.write(":CONF:CURR:DC 0.01")
    dmm.write(":SENS:FUNC 'CURR:DC'")
    i_iq_lo = float(dmm.query(":READ?"))
    psu.write(":SOUR2:VOLT 5.0")
    i_iq_hi = float(dmm.query(":READ?"))
    add(
        "ldo_iq_follows_vin",
        i_iq_hi > i_iq_lo * 1.5 and abs(i_iq_lo - (5e-8 + 1.0e-7 * 3.3)) > 1e-9,
        f"Ilo={i_iq_lo} Ihi={i_iq_hi}",
    )
    set_ldo_dut(False)
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


def simulated_handles() -> dict[str, SimResource]:
    reset_bus()
    return {k: SimResource(k) for k in ("MSO", "PSU", "AWG", "DMM")}
