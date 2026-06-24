# tests/test_math_utils.py
"""Tests for deterministic math utility functions."""
import pytest
from harvestamp.core.math_utils import (
    calculate_diesel_cost_per_gallon,
    calculate_tank_capacity_percentage,
    calculate_fuel_days_on_hand,
    calculate_fertilizer_cost_per_pound_nitrogen,
    calculate_fertilizer_cost_per_acre,
    calculate_packaging_coverage_weeks
)

def test_diesel_cost_per_gallon():
    assert calculate_diesel_cost_per_gallon(7360, 2000) == 3.68
    with pytest.raises(ValueError):
        calculate_diesel_cost_per_gallon(500, 0)

def test_tank_capacity_percentage():
    assert calculate_tank_capacity_percentage(1350, 4000) == 33.75
    with pytest.raises(ValueError):
        calculate_tank_capacity_percentage(1000, 0)

def test_fuel_days_on_hand():
    assert calculate_fuel_days_on_hand(1000, 100) == 10.0
    assert calculate_fuel_days_on_hand(1000, 0) == float('inf')

def test_fertilizer_cost_per_pound_nitrogen():
    # Urea: $475/ton, 46% Nitrogen
    # pounds_n_per_ton = 2000 * 0.46 = 920 lbs
    # cost = 475 / 920 = 0.5163
    assert calculate_fertilizer_cost_per_pound_nitrogen(475.0, 46) == 0.5163

    # UAN 32: $340/ton, 32% Nitrogen
    # pounds_n_per_ton = 2000 * 0.32 = 640 lbs
    # cost = 340 / 640 = 0.5313
    assert calculate_fertilizer_cost_per_pound_nitrogen(340.0, 32) == 0.5312
    
    with pytest.raises(ValueError):
        calculate_fertilizer_cost_per_pound_nitrogen(400, 0)

def test_fertilizer_cost_per_acre():
    # Price: $400/ton, Rate: 100 lbs/acre
    # cost_per_lb = 400 / 2000 = 0.2
    # cost_per_acre = 0.2 * 100 = 20.0
    assert calculate_fertilizer_cost_per_acre(400.0, 100.0) == 20.0

def test_packaging_coverage_weeks():
    assert calculate_packaging_coverage_weeks(150, 75) == 2.0
    assert calculate_packaging_coverage_weeks(150, 0) == float('inf')
