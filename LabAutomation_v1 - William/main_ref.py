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
from logic_tests import test_tp, dummy_test_1, dummy_test_2, dummy_test_3
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

        # Then run the original logic tests
        gen = instr.gen
        dmm = instr.dmm

        #gen.write(f":OUTP{ch} ON")

        """part1 - DC setup"""
        #gen.write(":SOUR1:FUNC ARB")
        #gen.write(":SOUR1:APPL:DC 100,5,3,90")
        #time.sleep(10)
  
        """part2 - basic AC setup"""
        #gen.write(":SOUR2:APPL:SQU 1000,3,0.75,0")

        power_on_protected(instr.psu, 2, 3.3, 0.5)
        enable_scope_channel(instr.scope, 2)
        enable_output(gen, 2)
        psu_mode = query_psu_mode(instr.psu, 2)
        print(f"PSU mode on channel 2: {psu_mode}")
        
        #setup_dc(gen, 1, 4)
        step_voltage(instr.psu, 2, 0, 3.33, 0.05, delay=2)

        
        for vcc in VCC_LIST:
            print(f"Running dummy tests at VCC={vcc}V")
            
            # Dummy Test 1
            result1 = dummy_test_1(instr, vcc)
            save_results([result1], EXCEL_FILE, sheet_name='Dummy_Test_1')
            print(f"  Saved Dummy Test 1 result to sheet 'Dummy_Test_1'")
            
            # Dummy Test 2
            result2 = dummy_test_2(instr, vcc)
            save_results([result2], EXCEL_FILE, sheet_name='Dummy_Test_2')
            print(f"  Saved Dummy Test 2 result to sheet 'Dummy_Test_2'")
            
            # Dummy Test 3
            result3 = dummy_test_3(instr, vcc)
            save_results([result3], EXCEL_FILE, sheet_name='Dummy_Test_3')
            print(f"  Saved Dummy Test 3 result to sheet 'Dummy_Test_3'")
        
        print(f"All dummy test results saved to {EXCEL_FILE} with different tabs.")

    except Exception as e:
        print(f"严重错误发生: {e}")
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