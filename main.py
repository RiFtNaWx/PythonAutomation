"""Main test runner.

Author: William
Version: 1.0

Coordinates instrument setup, test execution, and result logging.

Imports available helper functions from:
- instruments
- logic_tests
- configurations
- datalog
- dmm_setup
- generator_setup
- psu_setup
- scope_setup
"""

from typing import Set

from instruments import Instruments
from logic_tests import test_supply_current, test_off_current, test_delta_supply_current
#from config import *
from configurations import *
from datalog import save_results
from dmm_setup import *
from generator_setup import *
from psu_setup import *
from scope_setup import *
import time
#from utils import *

def test_generator_procedures(instr):
    """
    Test the new generator procedures.
    """
    print("Testing Generator Procedures...")

    gen = instr.gen
    if not gen:
        print("No generator found!")
        return

    # Reset generator
    reset_generator(gen)
    print("Generator reset.")

    # Test different waveforms
    waveforms = [
        ('SIN', 1000, 2, 0, 0),  # Sine: 1kHz, 2Vpp, 0V offset, 0 phase
        ('SQU', 1000, 2, 0, 0, 50),  # Square: 1kHz, 2Vpp, 0V offset, 0 phase, 50% duty
        ('RAMP', 1000, 2, 0, 0),  # Ramp: 1kHz, 2Vpp, 0V offset, 0 phase
        ('PULS', 1000, 2, 0, 0, 25),  # Pulse: 1kHz, 2Vpp, 0V offset, 0 phase, 25% duty
        ('NOIS', 0, 1, 0),  # Noise: 1Vpp, 0V offset
    ]

    for i, params in enumerate(waveforms):
        ch = 1  # Use channel 1
        waveform = params[0]
        if waveform == 'NOIS':
            freq, vpp, offset = params[1], params[2], params[3]
            setup_noise(gen, ch, vpp, offset)
            print(f"Set channel {ch} to {waveform} with {vpp}Vpp, {offset}V offset")
        else:
            freq, vpp, offset, phase = params[1], params[2], params[3], params[4]
            duty = params[5] if len(params) > 5 else 50
            apply_waveform(gen, ch, waveform, freq, vpp, offset, phase, duty)
            print(f"Set channel {ch} to {waveform} with {freq}Hz, {vpp}Vpp, {offset}V offset, {phase}° phase, {duty}% duty")

        time.sleep(2)  # Wait to observe

        # Query some parameters
        print(f"  Queried frequency: {query_frequency(gen, ch)} Hz")
        print(f"  Queried amplitude: {query_amplitude(gen, ch)} Vpp")
        print(f"  Output state: {'ON' if query_output_state(gen, ch) else 'OFF'}")

    # Test parameter changes
    print("\nTesting parameter changes...")
    set_frequency(gen, 1, 2000)  # Change to 2kHz
    print(f"Changed frequency to {query_frequency(gen, 1)} Hz")

    set_amplitude(gen, 1, 3)  # Change to 3Vpp
    print(f"Changed amplitude to {query_amplitude(gen, 1)} Vpp")

    # Test per-channel output control
    print("\nTesting output control...")
    disable_output(gen, 1)
    print(f"Channel 1 output: {'ON' if query_output_state(gen, 1) else 'OFF'}")

    enable_output(gen, 1)
    print(f"Channel 1 output: {'ON' if query_output_state(gen, 1) else 'OFF'}")

    # Stop all outputs
    stop_output(gen)
    print("All outputs stopped.")

    print("Generator test completed.\n")

def verify_current_measurement_procedure(instr, samples=10, delay=0.1):
    """Verify DC current readings by clearing the DMM buffer and reading statistics."""
    if not instr.dmm:
        print("No DMM instrument available.")
        return None

    print("Verifying current measurement on DMM...")
    stats = verify_current_measurement(instr.dmm, samples=samples, delay=0.1)
    print(f"  Average current: {stats['average']:.6g} A")
    print(f"  Max current: {stats['max']:.6g} A")
    print(f"  Min current: {stats['min']:.6g} A")
    return stats


def main():
    print("Final Main:")
    print(f"Configured VCC values: {VCC_LIST}")

    instr = Instruments()
    try:
        instr.reset_all()

        # Test generator procedures first
       # test_generator_procedures(instr)

        # print("Running RS1G08 supply current sweep from 1.65V to 5.5V...")
        # supply_results = test_supply_current(instr)
        # save_results(supply_results, EXCEL_FILE, sheet_name='Supply_Current')
        # print(f"Saved supply current sweep results to {EXCEL_FILE} sheet 'Supply_Current'.")
        
        print("Running delta supply current measurement...")
        delta_results = test_delta_supply_current(instr, vcc=3.0)  
        save_results(delta_results, EXCEL_FILE, sheet_name='Delta_Supply_Current')
        print(f"Saved delta supply current results to {EXCEL_FILE} sheet 'Delta_Supply_Current'.")
        # off_results = test_off_current(instr, vcc=0.0)
        # save_results(off_results, EXCEL_FILE, sheet_name='Off_Current')
        # print(f"Saved off-current results to {EXCEL_FILE} sheet 'Off_Current'.")
        
    except Exception as e:
        print(f"Serious fail occurred: {e}")
        raise
    finally:
        print("Cleaning up: turning off outputs before closing instruments...")
        try:
            stop_output(instr.gen)
        except Exception as e:
            print(f"Warning: could not stop generator outputs: {e}")

        try:
            power_off(instr.psu)
        except Exception as e:
            print(f"Warning: could not turn off PSU outputs: {e}")

        try:
            disable_all_scope_channels(instr.scope)
        except Exception as e:
            print(f"Warning: could not disable scope channels: {e}")

        instr.close_all()

if __name__ == "__main__":
    main()


