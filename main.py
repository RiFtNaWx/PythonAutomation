# main.py

from datetime import datetime
from instruments import Instruments
from logic_tests import *
from opa_tests import *
#from config import *
from configurations import *
from datalog import save_results, DataLogger
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

def main():
    print("Final Main:")
    print(f"Configured VCC values: {VCC_LIST}")

    instr = Instruments()
    logger = DataLogger(test_name="OPA_GBW_SR_Test", user_id="user")
    results = []

    # Pre-flight: confirm USB-VISA resources (not ASRL/COM hub fallback)
    print("\n=== VISA resource pre-flight ===")
    for name, session in (("scope", instr.scope), ("psu", instr.psu), ("gen", instr.gen)):
        res = getattr(session, "resource_name", None) or "(unknown)"
        print(f"  {name}: {res}")
        if str(res).upper().startswith("ASRL"):
            print(
                f"WARNING: {name} enumerated as serial, not USB-VISA — check hub "
                f"connection"
            )

    try:
        instr.reset_all()

        # Test generator procedures first
        # test_generator_procedures(instr)

        # Run OPA tests
        print("\n=== Running OPA GBW and SR Tests ===")
        for vcc in VCC_LIST:
            print(f"\nRunning OPA tests at VCC={vcc}V")
            # results.append(test_opa_gbw(instr, vcc, logger))
            # results.append(test_opa_sr(instr, vcc, logger))
            run_tag = datetime.now().strftime("%Y-%m-%d %H%M%S")
            results.append(
                test_vos_sweep(
                    instr,
                    vcc=vcc,
                    gain=201,
                    sheet_name=f"vos sweep {run_tag}",
                )
            )
            # results.append(test_settlingTime(instr, vcc, logger))
            # results.append(test_SSR(instr, vcc, logger))
            # results.append(test_LSR(instr, vcc, logger))
            # results.append(test_ORT(instr, vcc, logger))
            # results.append(test_powerONtime(instr, vcc, logger))

        for r in results:
            if r and "fit" in r:
                f = r["fit"]
                print(
                    f"\n=== VOS SWEEP RESULT ===\n"
                    f"slope={f['slope']:.4f} V/V  "
                    f"intercept={f['intercept']*1000:.4f} mV  "
                    f"R2={f['r_squared']:.6f}  "
                    f"VOS={f['vos_mV']:.4f} mV\n"
                )

    except Exception as e:
        print(f"Error occurred during testing: {e}")
        raise
    finally:
        print("Cleaning up: turning off outputs before closing instruments...")
        try:
            logger.save_to_csv()
        except Exception as e:
            print(f"Warning: could not save datalog: {e}")
        
        try:
            stop_output(instr.gen)
        except Exception as e:
            print(f"Warning: could not stop generator outputs: {e}")

        try:
            power_off(instr.psu)
        except Exception as e:
            print(f"Warning: could not turn off PSU outputs: {e}")

        try:
            instr.close_all()
        except Exception as e:
            print(f"Warning: could not close instruments: {e}")

if __name__ == "__main__":
    main()
