# generator_setup.py
# DG822 Pro (DG8Q) is 2-channel. Golden writes: APPL SQU/SIN/DC, OUTP1/OUTP2,
# OUTP1 LOAD INF. Do not send 4-ch OUTP, DCYC, or a standalone FREQ header -- those
# are DG4000 / 4-ch tokens -> SYST:ERR -116 Undefined Header.

import re
import time

_AWG_CHS = (1, 2)

# Standalone FREQ / DCYC / OUTP3|4. APPL:SQU freq,amp,offset,phase is allowed.
_BANNED_FREQ = re.compile(r":SOUR(?:\d|\{[^}]+\})?:FREQ", re.I)


def _awg_ch(ch) -> int:
    n = int(ch)
    if n not in _AWG_CHS:
        raise ValueError(
            f"DG822 Pro CH{n} invalid -- only CH1/CH2 (OUTP3/4 is Error 116)"
        )
    return n


def is_banned_awg_scpi(cmd: str) -> bool:
    """True if this box would queue SYST:ERR -116 Undefined Header."""
    n = str(cmd or "").upper().replace(" ", "")
    if ":OUTP3" in n or ":OUTP4" in n:
        return True
    if "DCYC" in n:
        return True
    if _BANNED_FREQ.search(n):
        return True
    return False


def _syst_err(gen) -> str:
    try:
        return str(gen.query("SYST:ERR?")).strip()
    except Exception:
        return ""


def _parse_appl_raw(raw: str) -> tuple[str, float, float, float, float]:
    text = (raw or "").replace('"', "").replace("'", "")
    func = "SQU"
    nums: list[float] = []
    for tok in text.split(","):
        t = tok.strip()
        if not t:
            continue
        try:
            nums.append(float(t))
        except ValueError:
            func = t.upper()
    freq = nums[0] if nums else 1000.0
    vpp = nums[1] if len(nums) > 1 else 0.0
    offs = nums[2] if len(nums) > 2 else 0.0
    phase = nums[3] if len(nums) > 3 else 0.0
    return func, freq, vpp, offs, phase


def _appl_fields(gen, ch: int) -> tuple[str, float, float, float, float]:
    return _parse_appl_raw(query_applied(gen, ch))


def _reapply_appl(gen, ch, *, freq=None, vpp=None, offset=None, phase=None) -> None:
    """Change one APPL field. Never send a standalone FREQ / VOLT / PHAS header."""
    ch = _awg_ch(ch)
    was_on = True
    try:
        st = str(gen.query(f":OUTP{ch}?")).strip().upper()
        was_on = st in ("1", "ON")
    except Exception:
        pass
    func, f0, v0, o0, p0 = _appl_fields(gen, ch)
    freq = f0 if freq is None else float(freq)
    vpp = v0 if vpp is None else float(vpp)
    offset = o0 if offset is None else float(offset)
    phase = p0 if phase is None else float(phase)
    gen.write(f":OUTP{ch} OFF")
    fu = (func or "SQU").upper()
    if fu == "DC":
        gen.write(f":SOUR{ch}:APPL:DC DEF,DEF,{offset}")
    elif fu == "NOIS":
        gen.write(f":SOUR{ch}:APPL:NOIS 0,{vpp},{offset},0")
    else:
        gen.write(f":SOUR{ch}:APPL:{fu} {freq},{vpp},{offset},{phase}")
    if was_on:
        gen.write(f":OUTP{ch} ON")


def setup_square(gen, ch, freq, vpp, offset, duty=50):
    """APPL SQU then ON. 4th number is start phase (degrees), default 0.

    DG822 Pro APPL:SQUare is freq, amp, offset, phase. That command forces 50%
    duty; do not send FUNC:SQU:DCYC (Error 116) and do not use FREQ (Error 116).
    `duty` is unused -- APPL overwrites duty to 50%.
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:APPL:SQU {freq},{vpp},{offset},0")
    gen.write(f":OUTP{ch} ON")
    err = _syst_err(gen)
    if err and not err.startswith("0"):
        print(f"AWG SYST:ERR after APPL:SQU {err}", flush=True)


def query_applied(gen, ch: int) -> str:
    """SOURn APPL? readback. Do not use FREQ? (Error 116 on DG822 Pro)."""
    ch = _awg_ch(ch)
    try:
        return str(gen.query(f":SOUR{ch}:APPL?")).strip()
    except Exception:
        return ""


def applied_freq_hz(gen, ch: int, fallback: float) -> float:
    """APPL? is FUNC,freq,amp,offset,phase. Use freq (first number), not FREQ?."""
    raw = query_applied(gen, ch)
    if not raw:
        return float(fallback)
    func, freq, _vpp, _offs, _phase = _parse_appl_raw(raw)
    del func
    if freq > 0:
        return freq
    return float(fallback)


def stop_output(gen):
    """DG822 Pro has CH1/CH2 only. Extra OUTP channels -> Error 116."""
    for ch in _AWG_CHS:
        gen.write(f":OUTP{ch} OFF")

# New procedures for different waveforms

def setup_sine(gen, ch, freq, vpp, offset, phase=0):
    """
    Setup sine wave on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:APPL:SIN {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def setup_triangle(gen, ch, freq, vpp, offset, phase=0):
    """
    Setup triangle wave on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:APPL:RAMP {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def setup_ramp(gen, ch, freq, vpp, offset, phase=0):
    """
    Setup ramp wave on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:APPL:RAMP {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def setup_pulse(gen, ch, freq, vpp, offset, phase=0, duty=50):
    """
    Setup pulse wave on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    duty: Duty cycle in percent (default 50)
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:APPL:PULS {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def set_output_load(gen, ch, load="INF"):
    """
    Set AWG output load impedance for amplitude/offset calibration.

    INF = high-Z (open circuit). Use for direct drive into a high-impedance
    summing junction; default 50 OHM assumes terminated load (~2x open-circuit).
    Source: Rigol DG800 Programming Guide, :OUTPut[]:LOAD.
    """
    ch = _awg_ch(ch)
    gen.write(f":OUTP{ch}:LOAD {load}")


def setup_dc(gen, ch, volts):
    """
    Setup DC output on the specified channel.

    Uses :SOUR<n>:APPL:DC <freq>,<ampl>,<offset> - frequency and amplitude
    are placeholders for the DC function; offset sets the output level.

    Source: Rigol DG800 Programming Guide, section [:SOURce[]]:APPLy:DC
    (DG822 Pro family). Example from manual: :SOUR1:APPL:DC 1,1,2  (2 Vdc).
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:APPL:DC DEF,DEF,{volts}")
    gen.write(f":OUTP{ch} ON")
    return True

def setup_noise(gen, ch, vpp, offset):
    """
    Setup noise on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:APPL:NOIS {0},{vpp},{offset},0")
    gen.write(f":OUTP{ch} ON")

def apply_waveform(gen, ch, waveform, freq, vpp, offset, phase=0, duty=50):
    """
    General function to apply any waveform.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    waveform: 'SIN', 'SQU', 'RAMP', 'PULS', 'NOIS'
    freq: Frequency in Hz (ignored for NOIS)
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0, ignored for NOIS)
    duty: Duty cycle in percent (default 50, for SQU and PULS)
    """
    ch = _awg_ch(ch)
    if waveform.upper() == 'NOIS':
        gen.write(f":SOUR{ch}:APPL:NOIS 0,{vpp},{offset},0")
    else:
        gen.write(f":SOUR{ch}:APPL:{waveform.upper()} {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

# Parameter control functions

def set_frequency(gen, ch, freq):
    """Change Hz via APPL (this box has no standalone FREQ header)."""
    _reapply_appl(gen, ch, freq=float(freq))

def set_amplitude(gen, ch, vpp):
    """Change Vpp via APPL (do not send standalone VOLT header)."""
    _reapply_appl(gen, ch, vpp=float(vpp))

def set_offset(gen, ch, offset):
    """
    Set DC offset for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    offset: DC offset voltage
    """
    ch = _awg_ch(ch)
    gen.write(f":SOUR{ch}:VOLT:OFFS {offset}")

def set_phase(gen, ch, phase):
    """Change phase via APPL (do not send standalone PHAS header)."""
    _reapply_appl(gen, ch, phase=float(phase))

def set_duty_cycle(gen, ch, duty):
    """Unused on DG822 Pro. APPL default duty is 50%. Do not send a DCYC header."""
    return

# Output control functions

def enable_output(gen, ch):
    """
    Enable output for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    """
    ch = _awg_ch(ch)
    gen.write(f":OUTP{ch} ON")

def disable_output(gen, ch):
    """
    Disable output for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    """
    ch = _awg_ch(ch)
    gen.write(f":OUTP{ch} OFF")


def _visa_clear(inst) -> None:
    try:
        inst.clear()
    except Exception:
        pass
    try:
        inst.write("*CLS")
    except Exception:
        pass


def park_generator_idle(
    gen,
    ch: int = 1,
    freq_hz: float = 1000.0,
    vpp: float = 0.05,
) -> None:
    """CH1/CH2 OFF only. FUNC/FREQ/APPL are 116 or they flash AC on DG822 Pro."""
    ch = _awg_ch(ch)
    for attempt in range(2):
        _visa_clear(gen)
        try:
            stop_output(gen)
        except Exception:
            pass
        try:
            state = gen.query(f":OUTP{ch}?").strip()
            if state in ("0", "OFF"):
                return
        except Exception:
            pass
        time.sleep(0.25)

# Query functions

def query_output_state(gen, ch):
    """
    Query output state for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-2)
    
    Returns: 1 if ON, 0 if OFF
    """
    ch = _awg_ch(ch)
    return int(gen.query(f":OUTP{ch}?").strip())

def query_frequency(gen, ch):
    """Hz from APPL? (FREQ? is Error 116 on DG822 Pro)."""
    ch = _awg_ch(ch)
    return applied_freq_hz(gen, ch, 0.0)

def query_amplitude(gen, ch):
    """Vpp from APPL? (VOLT? is not this box's header)."""
    _func, _freq, vpp, _offs, _phase = _appl_fields(gen, ch)
    return vpp

def reset_generator(gen):
    """
    Reset generator to default state.
    
    gen: Generator instrument handle
    """
    gen.write("*RST")
    time.sleep(0.5)
