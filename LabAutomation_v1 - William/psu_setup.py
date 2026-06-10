"""PSU setup helpers.

Author: William
Version: 1.0

Provides common DP832 power-supply operations used by the test framework.

Available functions:
- power_on(psu, channel, voltage)
- power_off(psu)
- power_on_protected(psu, channel, voltage, current_limit, ovp=None, ocp=None)
- query_psu_mode(psu, channel)
- step_voltage(psu, channel, start_voltage, end_voltage, step_size, delay=0.1)
"""

import time

# def power_on(psu, voltage):
    # psu.write(":OUTP CH1,OFF")
    # psu.write(f":SOUR1:VOLT {voltage}")
    # time.sleep(0.5)
    # psu.write(":OUTP CH1,ON")


def power_on(psu, channel: int, voltage: float):
    """
    Power ON a DP832 channel safely.

    psu     : VISA handle to DP832
    channel : PSU channel number (1, 2, or 3)
    voltage : Output voltage in volts
    """

    psu.write(f":OUTP CH{channel},OFF")       # Ensure channel is OFF
    psu.write(f":SOUR{channel}:VOLT {voltage}")  # Set voltage
    time.sleep(0.5)                           # Allow voltage register to settle
    psu.write(f":OUTP CH{channel},ON")        # Enable 

def power_off(psu):
    psu.write(":OUTP CH1,OFF")
    psu.write(":OUTP CH2,OFF")
    psu.write(":OUTP CH3,OFF")

def power_on_protected(psu, channel, voltage, current_limit, ovp=None, ocp=None):
    """
    Safe power ON with OVP & OCP protection (flexible channel)

    psu           : VISA handle to DP832
    channel       : PSU channel number (1 / 2 / 3)
    voltage       : Output voltage (V)
    current_limit : Current limit (A)
    ovp           : Over-voltage protection (V), default = 110% of voltage
    ocp           : Over-current protection (A), default = current_limit
    """

    # 1️⃣ Ensure output OFF (safety)
    psu.write(f":OUTP CH{channel},OFF")

    # 2️⃣ Set voltage & current limit
    psu.write(f":SOUR{channel}:VOLT {voltage}")
    psu.write(f":SOUR{channel}:CURR {current_limit}")

    # 3️⃣ Set OVP (default = 10% above voltage)
    if ovp is None:
        ovp = voltage * 1.1

    psu.write(f":SOUR{channel}:VOLT:PROT {ovp}")
    psu.write(f":SOUR{channel}:VOLT:PROT:STAT ON")

    # 4️⃣ Set OCP (default = current limit)
    if ocp is None:
        ocp = current_limit

    psu.write(f":SOUR{channel}:CURR:PROT {ocp}")
    psu.write(f":SOUR{channel}:CURR:PROT:STAT ON")

    # 5️⃣ Small delay before ON
    time.sleep(0.5)

    # 6️⃣ Turn ON output
    psu.write(f":OUTP CH{channel},ON")

    # 7️⃣ Stabilization delay
    time.sleep(1)


def query_psu_mode(psu, channel):
    """
    Query the PSU mode for a specific channel: 'CV' (Constant Voltage) or 'CC' (Constant Current).

    psu     : VISA handle to DP832
    channel : PSU channel number (1, 2, or 3)

    Returns: 'CV' or 'CC'
    """
    mode = psu.query(f":OUTPut:MODE? CH{channel}").strip()
    return mode


def step_voltage(psu, channel, start_voltage, end_voltage, step_size, delay=0.1):
    """
    Step the PSU voltage from start_voltage to end_voltage in increments of step_size.

    psu           : VISA handle to DP832
    channel       : PSU channel number (1, 2, or 3)
    start_voltage : Starting voltage (V)
    end_voltage   : Ending voltage (V)
    step_size     : Voltage step size (V), positive for up, negative for down
    delay         : Delay between steps (seconds)
    """
    if step_size == 0:
        raise ValueError("step_size cannot be zero")

    print(f"Debug: stepping PSU CH{channel} from {start_voltage}V to {end_voltage}V in {step_size}V increments")

    current_voltage = start_voltage
    direction = 1 if step_size > 0 else -1
    end_voltage = max(start_voltage, end_voltage) if direction == 1 else min(start_voltage, end_voltage)

    while (direction == 1 and current_voltage <= end_voltage) or (direction == -1 and current_voltage >= end_voltage):
        print(f"Debug: setting PSU CH{channel} voltage to {current_voltage}V")
        psu.write(f":SOUR{channel}:VOLT {current_voltage}")
        time.sleep(delay)
        current_voltage += step_size

    # Ensure final voltage is set
    print(f"Debug: final PSU CH{channel} voltage set to {end_voltage}V")
    psu.write(f":SOUR{channel}:VOLT {end_voltage}")
    time.sleep(delay)

