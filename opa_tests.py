# opa_tests.py
# Operational Amplifier (OPA) test procedures
# Tests for GBW (Gain-Bandwidth Product) and SR (Slew Rate)

def test_parameter():
    """Return the user-defined test configuration array.

    This function defines the available test names, parameter lists, and details.
    Parameters are only written to the datalog when their corresponding test is actually executed.
    """
    return [
        {
            "test_name": "OPA_RS622_Test",
            "parameters": ["IN+",
                           "GBW_MHz",
                           "SR_positive", 
                            "SR_negative",
                            "OverSHT",
                           "delay"
                           ],
            "details": "OPA Parameter tests"
        },
        # Add additional test configurations as needed
        # {
        #     "test_name": "Another_Test",
        #     "parameters": ["PARAM1", "PARAM2"],
        #     "details": "Description of another test"
        # }
    ]

TEST_CONFIGURATIONS = test_parameter()

import math

from dmm_setup import *
from generator_setup import *
from psu_setup import *
from scope_setup import *
from configurations import *
import time
from datalog import DataLogger
from utils import initial_time, final_time

def test_gbw(instr, vcc, gain, logger=None): # type: ignore
    """Measure Gain-Bandwidth Product (GBW).
    
    Measures the frequency at which gain drops to 0.707 (-3dB) of initial gain.
    Uses binary search to find the -3dB frequency point.
    
    Args:
        instr: Instruments object containing psu, gen, scope
        vcc: Supply voltage in Volts
        amp: Input amplitude in Volts (typically 50mV)
        gain: Closed-loop gain setting
        logger: Optional DataLogger for recording results
        
    Returns:
        Dictionary with 'IN+' and 'GBW_MHz' keys
    """
    psu = instr.psu
    gen = instr.gen
    scope = instr.scope
    
    try:
        # Setup phase
        # 1. Power supply configuration
        initial_time()

        power_on_protected(psu, 1, vcc / 2, current_limit)
        power_on_protected(psu, 2, vcc / 2, current_limit)
        time.sleep(1)
        
        # 2. Signal generator setup - initial sine wave at 1kHz
        setup_sine(gen, 1, 1000, 0.05, 0) 
        time.sleep(1)
      
        # 3. Oscilloscope setup for AC measurement
        # Use a low trigger level for the small OPA signal instead of half the supply.
        scope_setup(scope, 200e-6, 0)
        time.sleep(1)

        # Channel A: Scale/Offset setting
        
        # scope.write(f"CHAN1:SCALe {10e-3}")
        # scope.write(f"CHAN1:OFFS {10e-3}")

        # # Channel B: Scale/Offset setting
        # scope.write(f"CHAN2:SCALe {100e-3}")
        # scope.write(f"CHAN2:OFFS {-100e-3}")
        
      
        # Measurement phase
        # 4. Get initial amplitude at 1kHz baseline
        initial_amps = float(scope.query(":MEAS:ITEM? VAMP,CHAN2"))
        time.sleep(0.1)
        
        if not initial_amps:
            raise ValueError("GBW: no valid baseline VAMP samples (CHAN2). Check scope measurement setup / channel scaling / trigger.")
        
        # 5. Calculate target amplitude (0.707 of initial for -3dB point)
        target_amp = initial_amps * 0.707
        print(f"Target amplitude for -3dB point: {target_amp:.4f} V (initial was {initial_amps:.4f} V)")

        # input("Press Enter to start GBW measurement...")

        # 6. Binary search for -3dB frequency
        low = 10e3  # Frequency range: 100k Hz
        high = low
        
        while True:
            gen.write(f":SOUR1:FREQ {high}")
            time.sleep(0.5)
            current_amp = float(scope.query(":MEAS:ITEM? VAMP,CHAN2").strip())

            if current_amp <= target_amp:
                break

            low = high
            high *= 2

            if high > 50e6:
                raise ValueError("Could not bracket GBW before 50 MHz")
            
        while high - low > 100:
            mid = (low + high) / 2

            gen.write(f":SOUR1:FREQ {mid}")
            time.sleep(0.5)
            
            # Measure current amplitude at this frequency
            current_amp = float(scope.query(":MEAS:ITEM? VAMP,CHAN2"))
            if (not math.isfinite(current_amp)) or current_amp > 1e6:
                raise ValueError(f"Invalid VAMP reading from scope: {current_amp}. Check measurement setup and signal integrity at frequency {mid:.0f} Hz.")          
            time.sleep(0.1)
            
            # Adjust search range based on amplitude
            if current_amp > target_amp:
                # print("Amplitude too high -> increasing frequency")
                low = mid
            else:
                # print("Amplitude too low -> decreasing frequency")
                high = mid
            # print(f"mid={mid:.0f}, current_amp={current_amp:.4f}, target_amp={target_amp:.4f}, low={low:.0f}, high={high:.0f}")
            # input("Press Enter to continue GBW search...")
        
        duration_ms = final_time()
        gbw_freq = (low + high) / 2
        gbw_mhz = round(gbw_freq * gain / 1e6, 4)  # Convert to MHz
        print(f"Measured GBW: {gbw_mhz:.4f} MHz at VCC={vcc} V, Gain={gain}, IN+={vcc/2} V, Target Amplitude={target_amp:.4f} V")
        
        results = {
            # "IN+": vcc,
            "GBW_MHz": gbw_mhz
        }
        
        if logger:
            # logger.log_test("IN+", vcc, duration_ms=duration_gbw)
            logger.log_test("GBW_MHz", gbw_mhz, duration_ms=duration_ms)
        
        return results
        
    except Exception as e:
        print(f"Error measuring GBW: {e}")
        return None
    finally:
        try:
            stop_output(gen)
            power_off(psu)
            scope.write(":MEASure:CLEar ALL")
        except:
            pass

def test_sr(instr, vcc, logger=None):
    """Measure Slew Rate (SR) - positive and negative.
    
    Measures the maximum rate of change of output voltage in response to
    a square wave input. Tests both positive and negative slew rates.
    
    Args:
        instr: Instruments object containing psu, gen, scope
        vcc: Supply voltage in Volts
        amp: Input amplitude in Volts (typically 1V)
        logger: Optional DataLogger for recording results
        
    Returns:
        Dictionary with 'IN+', 'SR_positive', and 'SR_negative' keys
    """
    psu = instr.psu
    gen = instr.gen
    scope = instr.scope
       
    try:
        initial_time()
        # Setup phase
        # 1. Power supply configuration
        power_on_protected(psu, 1, vcc / 2, current_limit)
        time.sleep(1)
        power_on_protected(psu, 2, vcc / 2, current_limit)
        time.sleep(1)
        
        # 2. Signal generator setup - square wave for slew rate measurement
        setup_square(gen, 1, 1000, 2, 0)  # Convert to V
        time.sleep(1)
        
        # 3. Oscilloscope setup for transient measurement
        # Use wider timebase (100 µs) to capture full rising/falling edges for SR measurement
        scope_setup(scope, 200e-9, 0)
        time.sleep(1)

        # Channel A: Scale/Offset setting
        
        scope.write(f"CHAN1:SCALe {500e-3}")
        scope.write(f"CHAN1:OFFS {-20e-3}")

        # Channel B: Scale/Offset setting
        scope.write(f"CHAN2:SCALe {500e-3}")
        scope.write(f"CHAN2:OFFS {-500e-3}")

        scope.write(f"TIMebase:OFFSet {400e-9}")
        
        # input("Press Enter to continue...")

        # Measurement phase
        # 4. Collect slew rate measurements (multiple samples for averaging)

        # Query positive and negative slew rates from oscilloscope
        scope.write(f"TRIG:EDGE:SLOP POS")
        pslew = float(scope.query(":MEAS:ITEM? PSLewrate,CHAN2")) * 1e-6  # Convert to V/µs
        my_capture = screenshot()
        
        # input("Press Enter to continue...")
        scope.write(":SYSTem:KEY:PRESs MOFF") 
        scope.write(f"TRIG:EDGE:SLOP NEG")
        time.sleep(1)
        nslew = float(scope.query(":MEAS:ITEM? NSLewrate,CHAN2")) * 1e-6
        my_capture = screenshot()
        time.sleep(1)

        # input("Press Enter to continue...")

        print(f"PSlew={pslew:.4f} V/µs, NSlew={nslew:.4f} V/µs")

        time.sleep(0.01)
        
        duration_ms = final_time()
        
        if not math.isfinite(pslew) or pslew > 1e6:
            raise ValueError(f"Invalid PSlew reading: {pslew}. Check scope measurement setup and signal integrity.")

        if not math.isfinite(nslew) or nslew > 1e6:
            raise ValueError(f"Invalid NSlew reading: {nslew}. Check scope measurement setup and signal integrity.")
        
        # Calculate averages
        
        results = {
            # "IN+": vcc,
            "SR_positive": pslew,
            "SR_negative": nslew
        }
        
        if logger:
            print(f"Test results: IN+={vcc} V, SR+={pslew:.4f} V/µs, SR-={nslew:.4f} V/µs")
            # logger.log_test("IN+", vcc, duration_ms=duration_sr)
            logger.log_test("SR_positive", pslew, duration_ms=duration_ms)
            logger.log_test("SR_negative", nslew, duration_ms=duration_ms)
        
        return results
        
    except Exception as e:
        print(f"Error measuring SR: {e}")
        return None
    finally:
        try:
            stop_output(gen)
            power_off(psu)
            scope.write(":MEASure:CLEar ALL")
        except:
                pass

def test_settlingTime(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control

    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()

    try:
        # 1. Enable power supply with current protection
        power_on_protected(psu, 1, vcc/2, current_limit)
        power_on_protected(psu, 2, vcc/2, current_limit)
        
        # 2. Configure signal generator for square wave input
        # - 1 kHz frequency: tests high-speed response

        setup_square(gen, 1, 1000, 2, 0)

        # 3. Configure oscilloscope for timing measurement
        # - 200 ns timebase: captures fast transitions and settling behavior
        scope_setup(scope, 200e-9, 0.5)

        # Channel A: Scale/Offset setting
        scope.write(f"CHAN1:SCALe {500e-3}")
        scope.write(f"CHAN1:OFFS {0}")

        scope.write(f"CHAN2:SCALe {500e-3}")
        scope.write(f"CHAN2:OFFS {-500e-3}")

        scope.write(f"TIMebase:OFFSet {400e-9}")

        # set_threshold(scope, 1)
        # set_threshold(scope, 2)

        # ========== MEASUREMENT PHASE ==========
        # r_IN = measure_single(scope, "VPP", 1)  # Input amplitude
        r_settlingTime = measure_single(scope, "VPP", 2)  # Rising edge delay
        # print(f"Measured IN+: {r_IN:.4f} V")
        print(f"Measured Settling Time: {r_settlingTime:.4f} s")

        duration_ms = final_time()
        
        print(f"Test duration: {duration_ms:.2f} ms")

        input("Press Enter to continue...")

        # my_capture = screenshot()

        # input("Press Enter to continue...")

        # results = {
            # "IN+": r_IN,
            # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
        # }

        # if logger:
            # Log VCC with overall duration
            # logger.log_test("IN+", r_IN, duration_ms=overall_duration_ms)
            # # Log each parameter with its individual measurement duration
            # logger.log_test("SettlingTime", r_settlingTime, duration_ms=duration_ms)

        # return results

    except Exception as e:
        print(f"Error measuring SettlingTime: {e}")
        return None
    finally:
        try:
            stop_output(gen)
            power_off(psu)
            scope.write(":MEASure:CLEar ALL")
        except:
                pass
    
def test_SSR(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control

    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()


    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_square(gen, 1, 500000, 0.1, 0)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 200e-9, 0.025)

    time.sleep(1)  # Wait for settings to take effect

    # Channel A: Scale/Offset setting
    scope.write(f"CHAN1:SCALe {50e-3}")
    scope.write(f"CHAN1:OFFS {50e-3}")

    # Channel B: Scale/Offset setting
    scope.write(f"CHAN2:SCALe {50e-3}")
    scope.write(f"CHAN2:OFFS {0}")

    scope.write(f"TIMebase:OFFSet {600e-9}")

    # set_threshold(scope, 1)
    # set_threshold(scope, 2)

    # ========== MEASUREMENT PHASE ==========
    scope.write(":MEASure:ITEM OVERshoot,CHAN2")  # 

    duration_ms = final_time()

    print(f"Test duration: {duration_ms:.2f} ms")

    time.sleep(1)  # Wait for any transient effects to settle

    # my_capture = screenshot()
    overshoot = scope.write(":MEASure:ITEM? OVERshoot,CHAN2")  # Rising edge delay
    # input("Press Enter to continue...")

    stop_output(gen)
    power_off(psu)
    scope.write(":MEASure:CLEar ALL")

    results = {
        # "VCC": vcc,
        "OverSHT": overshoot,      # Overshoot percentage
    }

    if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        logger.log_test("OverSHT", overshoot, duration_ms=duration_ms)

    return results
    
def test_LSR(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control
    
    start_time = time.time() * 1000  # in milliseconds

    # ========== SETUP PHASE ==========

    initial_time()

    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_square(gen, 1, 250000, 4, 0)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 500e-9, 1)
    time.sleep(1)  # Wait for settings to take effect

    # Channel A: Scale/Offset setting
    scope.write(f"CHAN1:SCALe {1}")
    scope.write(f"CHAN1:OFFS {1}")

    # Channel B: Scale/Offset setting
    scope.write(f"CHAN2:SCALe {1}")
    scope.write(f"CHAN2:OFFS {0}")

    scope.write(f"TIMebase:OFFSet {1e-6}")

    # set_threshold(scope, 1)
    # set_threshold(scope, 2)

    # ========== MEASUREMENT PHASE ==========
    # t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    duration_ms = final_time()
    end_time = time.time() * 1000  # in milliseconds
    overall_duration_ms = end_time - start_time
    
    print(f"Test duration: {duration_ms:.2f} ms")

    time.sleep(1)  # Wait for any transient effects to settle

    # input("Press Enter to continue...")
    my_capture = screenshot()
    # input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")
    # my_capture = screenshot()
    # input("Press Enter to continue...")
    # my_capture = screenshot()

    # results = {
        # "VCC": vcc,
        # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
        # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    # }

    # if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)
        # logger.log_test("IN_T_O_LH", t_rise * 1e9, duration_ms=duration_lh)
        # logger.log_test("O_T_IN_HL", t_fall_rev * 1e9, duration_ms=duration_hl_rev)
        # logger.log_test("O_T_IN_LH", t_rise_rev * 1e9, duration_ms=duration_lh_rev)

    stop_output(gen)
    power_off(psu)
    scope.write(":MEASure:CLEar ALL")

    # return results

def test_ORT(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control
    
    # ========== SETUP PHASE ==========

    initial_time()

    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc/2, current_limit)
    power_on_protected(psu, 2, vcc/2, current_limit)
    
    # 2. Configure signal generator for square wave input

    setup_square(gen, 1, 1000, 0.2, -0.1)

    # 3. Configure oscilloscope for timing measurement
    # - 500 ns timebase: captures fast transitions and settling behavior
    scope_setup(scope, 500e-9, -0.1)
    time.sleep(1)  # Wait for settings to take effect

    # Channel A: Oscilloscope Scale/Offset setting
    scope.write(f"CHAN1:SCALe {200e-3}")
    scope.write(f"CHAN1:OFFS {600e-3}")

    # Channel B: Oscilloscope Scale/Offset setting
    scope.write(f"CHAN2:SCALe {1}")
    scope.write(f"CHAN2:OFFS {-3}")

    scope.write(f"TIMebase:OFFSet {1e-6}")

    ## measure delay (NOT WORKING)

    # scope.write(":CHAN1:DISP ON")
    # scope.write(":CHAN2:DISP ON")

    
    # scope.write(":TRIG:MODE EDGE")
    # scope.write(":TRIG:EDGE:SOUR CHAN1")
    # scope.write(":TRIG:EDGE:SLOP POS")   # Rising edge trigger
    # scope.write(":TRIG:SWEEP NORM

    # scope.write(":MEAS:SETUP:TYPE DELAY")
    # scope.write(":MEAS:SETUP:SOUR1 CHAN1")
    # scope.write(":MEAS:SETUP:SOUR2 CHAN2")
    # scope.write(":MEAS:SETUP:EDGE1 RISE")
    # scope.write(":MEAS:SETUP:EDGE2 FALL")

    # scope.write(":MEAS:ITEM DELAY")
    # scope.write(":MEAS:DISPLAY ON")

    # time.sleep(5)

    # delay = scope.query(":MEAS:ITEM? DELAY")

    # print(delay)

    # scope.write(":MEAS:DISPLAY ON")

    # scope.write(":MEAS:SETUP:UPPER 100")
    # scope.write(":MEAS:SETUP:MID 98")
    # scope.write(":MEAS:SETUP:LOWER 50")

    # ========== MEASUREMENT PHASE ==========
    # t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    input("Press Enter to continue...")
    my_capture = screenshot()
    time.sleep(1)  # Wait for any transient effects to settle

    stop_output(gen)
    time.sleep(1) 

#############################################################
    # Testing NEGATIVE OVERLOAD RECOVERY

    setup_square(gen, 1, 1000, 0.2, 0.1)

    scope_setup(scope, 500e-9, 0.1)

    time.sleep(1)  # Wait for settings to take effect

    scope.write(f"TRIG:EDGE:SLOP NEG")

    scope.write(f"CHAN1:SCALe {200e-3}")
    scope.write(f"CHAN1:OFFS {400e-3}")

    scope.write(f"CHAN2:SCALe {1}")
    scope.write(f"CHAN2:OFFS {-500e-3}")

    scope.write(f"TIMebase:OFFSet {1e-6}")
    time.sleep(1)  # Wait for settings to take effect

    input("Press Enter to continue...")
    my_capture = screenshot()
    duration_ms = final_time()
    print(f"Test duration: {duration_ms:.2f} ms")

    # results = {
    #     "IN+": vcc,
    #     # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
    #     # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    # }

    # if logger:
    #     # Log VCC with overall duration
    #     logger.log_test("IN+", vcc, duration_ms=overall_duration_ms)
    #     # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)
        # logger.log_test("IN_T_O_LH", t_rise * 1e9, duration_ms=duration_lh)
        # logger.log_test("O_T_IN_HL", t_fall_rev * 1e9, duration_ms=duration_hl_rev)
        # logger.log_test("O_T_IN_LH", t_rise_rev * 1e9, duration_ms=duration_lh_rev)

    stop_output(gen)
    power_off(psu)
    scope.write(":MEASure:CLEar ALL")

    # return results

def test_NPR(instr, vcc, logger=None):
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control
    
    # ========== SETUP PHASE ==========

    initial_time()

    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, (vcc/2)+0.25, current_limit)
    power_on_protected(psu, 2, (vcc/2)+0.25, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_sine(gen, 1, 1000, 6, 0)

    # 3. Configure oscilloscope for timing measurement
    scope_setup(scope, 125e-6, 1)
    time.sleep(1)  # Wait for settings to take effect

    # Channel A: Scale/Offset setting
    scope.write(f"CHAN1:SCALe {1}")
    scope.write(f"CHAN1:OFFS {0}")

    # Channel B: Scale/Offset setting
    scope.write(f"CHAN2:SCALe {1}")
    scope.write(f"CHAN2:OFFS {-1}")

    scope.write(f"TIMebase:OFFSet {0}")

    # ========== MEASUREMENT PHASE ==========
    # t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    duration_ms = final_time()
    
    print(f"Test duration: {duration_ms:.2f} ms")

    time.sleep(1)  # Wait for any transient effects to settle

    # input("Press Enter to continue...")
    my_capture = screenshot()
    time.sleep(1)  # Wait for any transient effects to settle  

    # results = {
        # "VCC": vcc,
        # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
    # }

    # if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)

    stop_output(gen)
    power_off(psu)
    scope.write(":MEASure:CLEar ALL")

    # return results

def test_powerONtime(instr, vcc, logger=None): 
    scope = instr.scope  # Oscilloscope object for measuring timing delays
    gen = instr.gen      # Signal generator object for creating input stimulus
    psu = instr.psu      # Power supply object for device power control
    
    # ========== SETUP PHASE ==========

    initial_time()


    # 1. Enable power supply with current protection
    power_on_protected(psu, 1, vcc, current_limit)
    
    # 2. Configure signal generator for square wave input
    # - 500 kHz frequency: tests high-speed response

    setup_dc(gen, 1, 0.2)

    # 3. Configure oscilloscope for timing measurement
    # - 200 ns timebase: captures fast transitions and settling behavior

    scope_setup(scope, 10e-6, vcc/2)
    scope.write(f"CHAN1:SCALe {2}")
    scope.write(f"CHAN2:SCALe {100e-3}")

    input("Press Enter to continue...")

    scope_single_capture(scope, 1, 2.5)

    input("Press Enter to continue...")

    setup_dc(gen, 2, 0.5)
    time.sleep(1)
    input("Press Enter to continue...")


    # ========== MEASUREMENT PHASE ==========
    # t_rise = measure_delay(scope, "RRDelay", 2, 1)  # Rising edge delay

    my_capture = screenshot()

    duration_ms = final_time()

    print(f"Test duration: {duration_ms:.2f} ms")

    # results = {
        # "VCC": vcc,
        # "IN_T_O_HL": t_fall * 1e9,      # High-to-low propagation delay (ns)
        # "IN_T_O_LH": t_rise * 1e9,      # Low-to-high propagation delay (ns)
    # }

    # if logger:
        # Log VCC with overall duration
        # logger.log_test("VCC", vcc, duration_ms=overall_duration_ms)
        # # Log each parameter with its individual measurement duration
        # logger.log_test("IN_T_O_HL", t_fall * 1e9, duration_ms=duration_hl)
        # logger.log_test("IN_T_O_LH", t_rise * 1e9, duration_ms=duration_lh)
        # logger.log_test("O_T_IN_HL", t_fall_rev * 1e9, duration_ms=duration_hl_rev)
        # logger.log_test("O_T_IN_LH", t_rise_rev * 1e9, duration_ms=duration_lh_rev)

    setup_dc(gen, 2, 0)

    stop_output(gen)

    print("Reset MOSFET by grounding gate")
    input("Press Enter to continue...")

    power_off(psu)

    # return results