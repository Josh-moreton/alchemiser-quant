"""Business Unit: shared; Status: current.

Mathematical Utilities.
"""

def round_decimal(value, decimal_places):
    return round(value, decimal_places)

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def calculate_percentage(numerator, denominator):
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100

def calculate_ratio(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator