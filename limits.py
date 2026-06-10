# limits.py
# Datasheet limits and pass/fail criteria for RS29511 Logic Device Test
# Contains only specification values (nominal, tolerance), no test logic

# Test specifications for datalog pass/fail
# Format: parameter: (nominal_value, tolerance_percent)
# These are placeholder values for OPA performance testing.
# Adjust the nominal and tolerance values to match the actual amplifier specification.
TEST_SPECS = {
    'IN+': ('typ', 2.5, 5.0),           # Supply voltage: 2.5V typical, 5% tolerance
    'GBW_MHz': ('typ', 9, 20),          # Gain-Bandwidth Product: 9 MHz typical, 20% tolerance
    'SR_positive': ('typ', 3.7, 20),     # Positive slew rate: 3.7 V/µs typical, 20% tolerance
    'SR_negative': ('typ', -4.7, 20),     # Negative slew rate: 4.7 V/µs typical, 20% tolerance
    'OverSHT': ('typ', 30, 20)           # Overshoot: 10% typical, 20% tolerance
}

# Category mapping for soft bin assignment.
# 1 = PASS, 2 = FAIL functional test, 3 = FAIL AC-related test
TEST_CATEGORIES = {
    'IN+': 'functional',
    'GBW_MHz': 'ac',
    'SR_positive': 'ac',
    'SR_negative': 'ac',
    'OverSHT': 'ac'
}

def get_test_category(parameter):
    """
    Return the category for a given test parameter.
    """
    return TEST_CATEGORIES.get(parameter, 'functional')