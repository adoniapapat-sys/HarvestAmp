# tests/test_schemas.py
"""Tests for schema validation of HarvestAmp entities."""
import os
import yaml
import pytest
from harvestamp.core.schemas import validate_by_name, SCHEMAS_DIR

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def test_schemas_exist():
    """Verify that all expected schema files are present."""
    expected = [
        "common_defs", "work_item", "farm_context_package", "agent_finding",
        "evidence_item", "human_review", "action_pack", "audit_event",
        "source_metadata", "connector_result", "recommendation",
        "farm_profile", "quote", "inventory_item", "scenario"
    ]
    for name in expected:
        path = os.path.join(SCHEMAS_DIR, f"{name}.schema.yaml")
        assert os.path.exists(path), f"Schema {name} is missing at {path}"

def test_farms_profile_validation():
    """Verify PVF and GBO fixtures pass the farm_profile schema validation."""
    for filename in ["prairie_view_farms.yaml", "green_basket_organics.yaml"]:
        path = os.path.join(FIXTURES_DIR, "farms", filename)
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        valid, errs = validate_by_name(data, "farm_profile")
        assert valid, f"{filename} failed validation: {errs}"

def test_source_metadata_validation():
    """Verify source_metadata.yaml items pass validation."""
    path = os.path.join(FIXTURES_DIR, "source_metadata.yaml")
    with open(path, "r") as f:
        items = yaml.safe_load(f)
    for i, item in enumerate(items):
        valid, errs = validate_by_name(item, "source_metadata")
        assert valid, f"Source metadata item [{i}] failed: {errs}"

def test_scenarios_validation():
    """Verify scenarios.yaml items pass validation."""
    path = os.path.join(FIXTURES_DIR, "scenarios.yaml")
    with open(path, "r") as f:
        items = yaml.safe_load(f)
    for i, item in enumerate(items):
        valid, errs = validate_by_name(item, "scenario")
        assert valid, f"Scenario item [{i}] failed: {errs}"

def test_invalid_type_validation():
    """Verify that wrong data types trigger validation errors."""
    bad_profile = {
        "farm_id": "PVF_ROW_CROP_001",
        "farm_name": 12345,  # Should be string
        "farm_type": "conventional",
        "location": "Illinois",
        "scale": "1800 acres",
        "users": []
    }
    valid, errs = validate_by_name(bad_profile, "farm_profile")
    assert not valid
    assert any("Expected string" in err for err in errs)
