"""DMM setup helpers.

Author: William
Version: 1.0

Provides measurement support for the digital multimeter.

Available functions:
- measure_voltage(dmm)
- measure_current(dmm)
- measure_capacitance(dmm)
- query_float(dmm, cmd)
- dmm_read_avg(dmm, n=5)
- clear_dmm_buffer(dmm)
- verify_current_measurement(dmm, samples=10, delay=0.1)
- dmm_setup_voltage(dmm)
- dmm_setup_current(dmm)
- dmm_setup_cap(dmm)
"""

def measure_voltage(dmm):
    dmm.write("*RST")
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    dmm.write(":SENS:VOLT:DC:RANG:AUTO ON")

    value = dmm.query(":READ?")
    return float(value)
	
def measure_current(dmm):
    dmm.write("*RST")
    dmm.write(":SENS:FUNC 'CURR:DC'")
    dmm.write(":SENS:CURR:DC:RANG:AUTO ON")

    value = dmm.query(":READ?")
    return float(value)
	
def measure_capacitance(dmm):
    dmm.write("*RST")
    dmm.write(":SENS:FUNC 'CAP'")
    dmm.write(":SENS:CAP:RANG:AUTO ON")

    value = dmm.query(":READ?")
    return float(value)
    
import time
import statistics

def query_float(dmm, cmd):
    response = dmm.query(cmd).strip()
    try:
        return float(response)
    except ValueError:
        raise ValueError(f"DMM returned non-numeric response for {cmd}: {response!r}")


def dmm_read_avg(dmm, n=5):
    values = [query_float(dmm, ":READ?") for _ in range(n)]
    return sum(values)/len(values)


def clear_dmm_buffer(dmm):
    """Clear the DMM active buffer if supported by the instrument."""
    dmm.write(":TRAC:CLE 'defbuffer1'")
    # for cmd in ["*CLS", ":TRAC:CLEAR", ":TRAC:CLE", ":SYST:BUF:CLEAR", ":SYST:BUF:DEL", ":SYST:MEM:CLEAR", ":SYST:MEM:DEL"]:
        # try:
            # dmm.write(cmd)
        # except Exception:
            # pass


def verify_current_measurement(dmm, samples=10, delay=0.1):
    """Configure the DMM for DC current measurement and return average/max/min.

    Args:
        dmm: PyVISA DMM resource handle
        samples: Number of readings to collect
        delay: Delay in seconds between readings

    Returns:
        dict: {'average': float, 'max': float, 'min': float, 'samples': list}
    """
    dmm.write("*CLS")
    dmm.write(":SENS:FUNC 'CURR:DC'")
    dmm.write(":SENS:CURR:DC:RANG:AUTO ON")

    #time.sleep(10)

    #dmm.write(":SENS:CURR:INP AUTO")
    dmm.write(":SENS:CURR:NPLC 1")
    dmm.write(":SENS:CURR:AZER ON")
    dmm.write(":SENS:CURR:AVER:TCON REP")
    dmm.write(":SENS:CURR:AVER:COUN 10")
    dmm.write(":SENS:CURR:AVER ON")
    clear_dmm_buffer(dmm)

    values = []
    for _ in range(samples):
        time.sleep(delay)
        values.append(query_float(dmm, ":READ?"))
    #dmm.write(":SENS:VOLT:AZER OFF")
    
    return {
        'average': statistics.mean(values),
        'max': max(values),
        'min': min(values),
        'samples': values,
    }


def dmm_setup_voltage(dmm):
    """Setup DMM for DC voltage measurement and return measurement.
    
    Args:
        dmm: PyVISA DMM resource handle
        
    Returns:
        float: Measured voltage in volts
    """
    dmm.write("*RST")
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    dmm.write(":SENS:VOLT:DC:RANG:AUTO ON")
    value = dmm.query(":READ?")
    return float(value)

def dmm_setup_current(dmm):
    """Setup DMM for DC current measurement and return measurement.
    
    Args:
        dmm: PyVISA DMM resource handle
        
    Returns:
        float: Measured current in amps
    """
    dmm.write("*RST")
    dmm.write(":SENS:FUNC 'CURR:DC'")
    dmm.write(":SENS:CURR:DC:RANG:AUTO ON")
    value = dmm.query(":READ?")
    return float(value)

def dmm_setup_cap(dmm):
    """Setup DMM for capacitance measurement and return measurement.
    
    Args:
        dmm: PyVISA DMM resource handle
        
    Returns:
        float: Measured capacitance in farads
    """
    dmm.write("*RST")
    dmm.write(":SENS:FUNC 'CAP'")
    dmm.write(":SENS:CAP:RANG:AUTO ON")
    value = dmm.query(":READ?")
    return float(value)

def dmm_read(dmm):
    """Read current DMM measurement without reconfiguration.
    
    Args:
        dmm: PyVISA DMM resource handle
        
    Returns:
        float: Current measurement value
    """
    value = dmm.query(":READ?")
    return float(value)