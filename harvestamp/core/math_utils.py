# harvestamp/core/math_utils.py
"""Deterministic math utilities for HarvestAmp.

All mathematical logic is defined here to ensure accuracy and repeatability,
avoiding free-form arithmetic calculations by LLM agents.
"""

def calculate_diesel_cost_per_gallon(total_cost: float, total_gallons: float) -> float:
    """Calculates cost per gallon of diesel."""
    if total_gallons <= 0:
        raise ValueError("Total gallons must be greater than zero.")
    return round(total_cost / total_gallons, 4)

def calculate_tank_capacity_percentage(current_gallons: float, total_capacity: float) -> float:
    """Calculates diesel tank fullness percentage."""
    if total_capacity <= 0:
        raise ValueError("Total capacity must be greater than zero.")
    return round((current_gallons / total_capacity) * 100, 2)

def calculate_fuel_days_on_hand(current_gallons: float, daily_avg_usage: float) -> float:
    """Calculates fuel days on hand based on average usage."""
    if daily_avg_usage < 0:
        raise ValueError("Daily average usage cannot be negative.")
    if daily_avg_usage == 0:
        return float('inf')
    return round(current_gallons / daily_avg_usage, 2)

def calculate_fertilizer_cost_per_pound_nitrogen(price_per_ton: float, nitrogen_percent: float) -> float:
    """Calculates material-only cost per pound of Nitrogen.
    
    Urea: nitrogen_percent = 46 (for 46%)
    UAN 32: nitrogen_percent = 32 (for 32%)
    """
    if price_per_ton < 0 or nitrogen_percent <= 0:
        raise ValueError("Price per ton must be non-negative and Nitrogen percentage must be greater than zero.")
    pounds_n_per_ton = 2000 * (nitrogen_percent / 100.0)
    return round(price_per_ton / pounds_n_per_ton, 4)

def calculate_fertilizer_cost_per_acre(price_per_ton: float, application_rate_lbs_per_acre: float) -> float:
    """Calculates material cost per acre for fertilizer application."""
    if price_per_ton < 0 or application_rate_lbs_per_acre < 0:
        raise ValueError("Parameters must be non-negative.")
    cost_per_lb = price_per_ton / 2000.0
    return round(cost_per_lb * application_rate_lbs_per_acre, 2)

def calculate_packaging_coverage_weeks(quantity_on_hand: float, expected_weekly_usage: float) -> float:
    """Calculates packaging coverage in weeks."""
    if expected_weekly_usage < 0:
        raise ValueError("Expected weekly usage cannot be negative.")
    if expected_weekly_usage == 0:
        return float('inf')
    return round(quantity_on_hand / expected_weekly_usage, 2)
