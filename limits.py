# limits.py
# Datasheet limits and pass/fail criteria for RS29511 Logic Device Test
# Contains only specification values (nominal, tolerance), no test logic

# Test specifications for datalog pass/fail
# Format: parameter: (nominal_value, tolerance_percent)
# These are placeholder values for OPA performance testing.
# Adjust the nominal and tolerance values to match the actual amplifier specification.
TEST_SPECS = {
    'IN+': (5.0, 5.0),           # VCC check placeholder — nominal 5 V, ±5%
    'AC_GAIN': (201.0, 10.0),
    'VOS_mV': (1.5, 100.0),      # 0–3 mV window via ±100% of 1.5 mV nominal
    'FIT_R2': (1.0, 5.0),        # 0.95–1.05
    'JUNCTION_VPP_mV': (0.5, 100.0),  # 0–1 mV
}

# Category mapping for soft bin assignment.
# 1 = PASS, 2 = FAIL functional test, 3 = FAIL AC-related test
TEST_CATEGORIES = {
    'VCC': 'functional',
    'IN+': 'functional',
    'GBW_MHz': 'ac',
    'SR_positive': 'ac',
    'SR_negative': 'ac',
    'AC_GAIN': 'ac',
    'VOS_mV': 'ac',
    'FIT_R2': 'ac',
    'JUNCTION_VPP_mV': 'ac',
}

# Helper function to calculate pass/fail limits
def get_limits(parameter):
    """
    Calculate min/max limits for a given parameter based on datasheet specifications.
    
    Args:
        parameter (str): Parameter name from TEST_SPECS
        
    Returns:
        tuple: (min_value, max_value) calculated from nominal and tolerance
        
    Raises:
        ValueError: If parameter not found in TEST_SPECS
    """
    if parameter not in TEST_SPECS:
        raise ValueError(f"Parameter '{parameter}' not found in TEST_SPECS")
    
    nominal, tolerance_percent = TEST_SPECS[parameter]
    tolerance = nominal * tolerance_percent / 100.0
    min_val = nominal - tolerance
    max_val = nominal + tolerance
    
    return min_val, max_val


def get_test_category(parameter):
    """
    Return the category for a given test parameter.
    """
    return TEST_CATEGORIES.get(parameter, 'functional')
