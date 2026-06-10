import math

from pyvisa import logger
from LabAutomation.main import test_generator_procedures
from dmm_setup import *
from generator_setup import *
from psu_setup import *
from scope_setup import *
from configurations import *
import time
from datalog import save_results,DataLogger
from utils import initial_time, final_time
from instruments import *
from logic_tests import *
from opa_tests import *
from utils import *

instr = Instruments()
logger = DataLogger("test_results.xlsx")
results = []  # Global list to store test results

safeMode = False  # Set to True to enable failsafe mode, False for normal operation

def test():
    print("This is a test function. Replace with actual test code.")
    # results.append(test_powerONtime(instr, vcc, logger))

def main():
    # Initialize instruments
    instr = Instruments()

    print("Test Mode")
    
    # Run tests
    test_generator_procedures(instr)

    try:
        instr.reset_all()

        #test line
        test()

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        print("Recommended to clean up: turning off outputs before closing instruments...")
        if safeMode == True:
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
        else:
            print("Failsafe mode disabled: skipping cleanup to preserve instrument state for debugging.")
            pass

if __name__ == "__main__":
    main()