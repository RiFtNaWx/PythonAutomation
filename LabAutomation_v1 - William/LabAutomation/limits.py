# limits.py
# Datasheet limits and pass/fail criteria for RS29511 Logic Device Test
# Contains only specification values (nominal, tolerance), no test logic

# Test specifications for datalog pass/fail
# Format: parameter: (nominal_value, tolerance_percent)
# These are datasheet specifications used to determine if a measurement passes or fails
TEST_SPECS = {
    'VCC': (5.5, 5.0),           # Supply voltage: 5.5V nominal, 5% tolerance
    'IN_T_O_HL': (1, 10.0),    # Input to Output propagation delay (High to Low): 3.2 ns, 10% tolerance
    'IN_T_O_LH': (2, 10.0),    # Input to Output propagation delay (Low to High): 3.5 ns, 10% tolerance
    'TDIS': (3, 10.0),         # Disable time: 6.8 ns, 10% tolerance
    'TEN': (4, 10.0),          # Enable time: 7.1 ns, 10% tolerance
    'TIDLE_HL': (5, 10.0),     # Idle propagation delay (High to Low): 3.0 ns, 10% tolerance
    'TIDLE_LH': (6, 10.0),     # Idle propagation delay (Low to High): 3.5 ns, 10% tolerance
    'O_T_IN_HL': (7, 10.0),    # Output to Input propagation delay (High to Low): 3.2 ns, 10% tolerance
    'O_T_IN_LH': (8, 10.0),    # Output to Input propagation delay (Low to High): 3.5 ns, 10% tolerance
}

# Category mapping for soft bin assignment.
# 1 = PASS, 2 = FAIL functional test, 3 = FAIL AC-related test
TEST_CATEGORIES = {
    'VCC': 'functional',
    'IN_T_O_HL': 'ac',
    'IN_T_O_LH': 'functional',
    'TDIS': 'ac',
    'TEN': 'functional',
    'TIDLE_HL': 'ac',
    'TIDLE_LH': 'ac',
    'O_T_IN_HL': 'ac',
    'O_T_IN_LH': 'ac',
    'TEST':'functional'
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
