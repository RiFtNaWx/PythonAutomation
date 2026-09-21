# generator_setup.py
# DG822 Pro (DG8Q) is 2-channel. Golden writes: APPL SQU/SIN/DC, OUTP1/OUTP2,
# OUTP1 LOAD INF. Do not send 4-ch OUTP, DCYC, or a standalone FREQ header -- those
# are DG4000 / 4-ch tokens -> SYST:ERR -116 Undefined Header.

import time

_AWG_CHS = (1, 2)


def _syst_err(gen) -> str:
    try:
        return str(gen.query("SYST:ERR?")).strip()
    except Exception:
        return ""


def setup_square(gen, ch, freq, vpp, offset, duty=50):
    """APPL SQU then ON. 4th number is start phase (degrees), default 0.

    DG822 Pro APPL:SQUare is freq, amp, offset, phase. That command forces 50%
    duty; do not send FUNC:SQU:DCYC (Error 116) and do not use FREQ (Error 116).
    `duty` is unused -- APPL overwrites duty to 50%.
    """
    gen.write(f":SOUR{ch}:APPL:SQU {freq},{vpp},{offset},0")
    gen.write(f":OUTP{ch} ON")
    err = _syst_err(gen)
    if err and not err.startswith("0"):
        print(f"AWG SYST:ERR after APPL:SQU {err}", flush=True)


def query_applied(gen, ch: int) -> str:
    """SOURn APPL? readback. Do not use FREQ? (Error 116 on DG822 Pro)."""
    try:
        return str(gen.query(f":SOUR{ch}:APPL?")).strip()
    except Exception:
        return ""


def applied_freq_hz(gen, ch: int, fallback: float) -> float:
    """APPL? is FUNC,freq,amp,offset,phase. Use freq (first number), not FREQ?."""
    raw = query_applied(gen, ch)
    if not raw:
        return float(fallback)
    text = raw.replace('"', "").replace("'", "")
    nums: list[float] = []
    for tok in text.split(","):
        try:
            nums.append(float(tok.strip()))
        except ValueError:
            continue
    if nums and nums[0] > 0:
        return nums[0]
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
    ch: Channel number (1-4)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    """
    gen.write(f":SOUR{ch}:APPL:SIN {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def setup_triangle(gen, ch, freq, vpp, offset, phase=0):
    """
    Setup triangle wave on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    """
    gen.write(f":SOUR{ch}:APPL:RAMP {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def setup_ramp(gen, ch, freq, vpp, offset, phase=0):
    """
    Setup ramp wave on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    """
    gen.write(f":SOUR{ch}:APPL:RAMP {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def setup_pulse(gen, ch, freq, vpp, offset, phase=0, duty=50):
    """
    Setup pulse wave on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    freq: Frequency in Hz
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0)
    duty: Duty cycle in percent (default 50)
    """
    gen.write(f":SOUR{ch}:APPL:PULS {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

def set_output_load(gen, ch, load="INF"):
    """
    Set AWG output load impedance for amplitude/offset calibration.

    INF = high-Z (open circuit). Use for direct drive into a high-impedance
    summing junction; default 50 OHM assumes terminated load (~2x open-circuit).
    Source: Rigol DG800 Programming Guide, :OUTPut[]:LOAD.
    """
    gen.write(f":OUTP{ch}:LOAD {load}")


def setup_dc(gen, ch, volts):
    """
    Setup DC output on the specified channel.

    Uses :SOUR<n>:APPL:DC <freq>,<ampl>,<offset> — frequency and amplitude
    are placeholders for the DC function; offset sets the output level.

    Source: Rigol DG800 Programming Guide, section [:SOURce[]]:APPLy:DC
    (DG822 Pro family). Example from manual: :SOUR1:APPL:DC 1,1,2  (2 Vdc).
    """
    gen.write(f":SOUR{ch}:APPL:DC DEF,DEF,{volts}")
    gen.write(f":OUTP{ch} ON")
    return True

def setup_noise(gen, ch, vpp, offset):
    """
    Setup noise on specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    """
    gen.write(f":SOUR{ch}:APPL:NOIS {0},{vpp},{offset},0")  # Freq and phase not applicable for noise
    gen.write(f":OUTP{ch} ON")

def apply_waveform(gen, ch, waveform, freq, vpp, offset, phase=0, duty=50):
    """
    General function to apply any waveform.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    waveform: 'SIN', 'SQU', 'RAMP', 'PULS', 'NOIS'
    freq: Frequency in Hz (ignored for NOIS)
    vpp: Peak-to-peak voltage
    offset: DC offset voltage
    phase: Phase in degrees (default 0, ignored for NOIS)
    duty: Duty cycle in percent (default 50, for SQU and PULS)
    """
    if waveform.upper() == 'NOIS':
        gen.write(f":SOUR{ch}:APPL:NOIS 0,{vpp},{offset},0")
    else:
        gen.write(f":SOUR{ch}:APPL:{waveform.upper()} {freq},{vpp},{offset},{phase}")
    gen.write(f":OUTP{ch} ON")

# Parameter control functions

def set_frequency(gen, ch, freq):
    """
    Set frequency for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    freq: Frequency in Hz
    """
    gen.write(f":SOUR{ch}:FREQ {freq}")

def set_amplitude(gen, ch, vpp):
    """
    Set amplitude (Vpp) for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    vpp: Peak-to-peak voltage
    """
    gen.write(f":SOUR{ch}:VOLT {vpp}")

def set_offset(gen, ch, offset):
    """
    Set DC offset for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    offset: DC offset voltage
    """
    gen.write(f":SOUR{ch}:VOLT:OFFS {offset}")

def set_phase(gen, ch, phase):
    """
    Set phase for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    phase: Phase in degrees
    """
    gen.write(f":SOUR{ch}:PHAS {phase}")

def set_duty_cycle(gen, ch, duty):
    """Unused on DG822 Pro. APPL default duty is 50%. Do not send a DCYC header."""
    return

# Output control functions

def enable_output(gen, ch):
    """
    Enable output for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    """
    gen.write(f":OUTP{ch} ON")

def disable_output(gen, ch):
    """
    Disable output for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    """
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
    ch: Channel number (1-4)
    
    Returns: 1 if ON, 0 if OFF
    """
    return int(gen.query(f":OUTP{ch}?").strip())

def query_frequency(gen, ch):
    """
    Query frequency for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    
    Returns: Frequency in Hz
    """
    return float(gen.query(f":SOUR{ch}:FREQ?").strip())

def query_amplitude(gen, ch):
    """
    Query amplitude for specified channel.
    
    gen: Generator instrument handle
    ch: Channel number (1-4)
    
    Returns: Amplitude in Vpp
    """
    return float(gen.query(f":SOUR{ch}:VOLT?").strip())

def reset_generator(gen):
    """
    Reset generator to default state.
    
    gen: Generator instrument handle
    """
    gen.write("*RST")
    time.sleep(0.5)

