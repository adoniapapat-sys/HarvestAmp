# tests/test_context_minimization.py
"""Tests for task-scoped context minimization."""
import os
import yaml
from harvestamp.context.builder import ContextPackageBuilder

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def test_context_minimization_fuel_topic():
    """Verify that fuel topic context includes fuel data but excludes GBO/CSA data."""
    pvf_path = os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")
    farm_profile = yaml.safe_load(open(pvf_path))
    
    builder = ContextPackageBuilder()
    
    # Build context for fuel buy window
    ctx = builder.build_context_package(farm_profile, "farm_owner", "fuel_buy_window")
    
    # Must include fuel inventory and quotes
    assert any(inv["item_type"] == "diesel" for inv in ctx["relevant_inventory"])
    assert any(q["input_type"] == "diesel" for q in ctx["relevant_quotes"])
    
    # Must NOT include CSA member count or organic details
    assert "csa_members" not in ctx
    assert "organic_context" not in ctx
    assert "growing_areas" not in ctx

def test_context_minimization_role_redactions():
    """Verify that field employee has quotes and pricing redacted."""
    pvf_path = os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")
    farm_profile = yaml.safe_load(open(pvf_path))
    
    builder = ContextPackageBuilder()
    
    # Field Employee
    ctx = builder.build_context_package(farm_profile, "field_employee", "fuel_buy_window")
    
    assert ctx["relevant_quotes"] == []
    assert "supplier_pricing_redacted" in ctx["redactions_applied"]
    assert "supplier_quotes" in ctx["prohibited_disclosures"]
