# tests/test_harvest_domain.py
"""Tests for schema and domain-level validation of the harvest domain."""
import pytest
from harvestamp.core.schemas import validate_by_name

def test_harvest_event_validation():
    # Valid
    valid_event = {
        "harvest_event_id": "GBO_HARV_001",
        "farm_id": "GBO_DIRECT_001",
        "crop": "tomatoes",
        "field_or_block": "HT1",
        "harvest_date": "2026-06-23",
        "quantity_harvested": 100.0,
        "unit": "lbs",
        "marketable_quantity": 80.0,
        "cull_quantity": 20.0,
        "destination": "Cooler",
        "storage_location": "Cooler",
        "lot_or_batch": "LOT-01",
        "evidence_id": "res_01",
        "organic_record_required": True,
        "food_safety_record_required": True,
        "status": "completed"
    }
    v, e = validate_by_name(valid_event, "harvest_event")
    assert v, f"Valid event failed: {e}"

    # Invalid: negative quantities
    bad_event1 = valid_event.copy()
    bad_event1["quantity_harvested"] = -5.0
    v, e = validate_by_name(bad_event1, "harvest_event")
    assert not v, "Negative quantity should fail"

    # Invalid: marketable + cull > harvested
    bad_event2 = valid_event.copy()
    bad_event2["marketable_quantity"] = 90.0
    bad_event2["cull_quantity"] = 20.0  # Sum is 110 > 100
    v, e = validate_by_name(bad_event2, "harvest_event")
    assert not v, "Marketable + cull > harvested should fail"
    assert any("cannot exceed quantity harvested" in err for err in e)

    # Invalid: missing farm_id
    bad_event3 = valid_event.copy()
    del bad_event3["farm_id"]
    v, e = validate_by_name(bad_event3, "harvest_event")
    assert not v, "Missing farm_id should fail"

    # Invalid: missing evidence_id
    bad_event4 = valid_event.copy()
    del bad_event4["evidence_id"]
    v, e = validate_by_name(bad_event4, "harvest_event")
    assert not v, "Missing evidence_id should fail"

    # Invalid: invalid status enum
    bad_event5 = valid_event.copy()
    bad_event5["status"] = "unknown_status"
    v, e = validate_by_name(bad_event5, "harvest_event")
    assert not v, "Invalid status should fail"

def test_yield_record_validation():
    valid_yield = {
        "yield_record_id": "PVF_YLD_001",
        "farm_id": "PVF_ROW_CROP_001",
        "crop": "corn",
        "field_id": "PVF_FIELD_A",
        "harvested_area_acres": 160.0,
        "gross_quantity": 30000.0,
        "unit": "bushels",
        "adjusted_quantity": 29000.0,
        "moisture_percent": 15.0,
        "test_weight": 56.0,
        "dockage_or_shrink": 1000.0,
        "storage_or_delivery": "Bin 1",
        "evidence_id": "res_02",
        "missing_fields": [],
        "status": "verified"
    }
    v, e = validate_by_name(valid_yield, "yield_record")
    assert v, f"Valid yield failed: {e}"

    # Invalid: adjusted > gross
    bad_yield = valid_yield.copy()
    bad_yield["adjusted_quantity"] = 35000.0
    v, e = validate_by_name(bad_yield, "yield_record")
    assert not v, "Adjusted > gross should fail"
    assert any("cannot exceed gross quantity" in err for err in e)

def test_post_harvest_inventory_validation():
    valid_inv = {
        "inventory_id": "GBO_PHI_001",
        "farm_id": "GBO_DIRECT_001",
        "crop_or_item": "tomatoes",
        "quantity_available": 100.0,
        "unit": "lbs",
        "storage_location": "Cooler",
        "lot_or_batch": "LOT-01",
        "committed_quantity": 40.0,
        "uncommitted_quantity": 60.0,
        "quality_grade": "A",
        "shelf_life_watch": False,
        "evidence_id": "res_03",
        "status": "available"
    }
    v, e = validate_by_name(valid_inv, "post_harvest_inventory")
    assert v, f"Valid post harvest inv failed: {e}"

    # Invalid: committed + uncommitted > available
    bad_inv = valid_inv.copy()
    bad_inv["committed_quantity"] = 50.0
    bad_inv["uncommitted_quantity"] = 60.0  # Sum is 110 > 100
    v, e = validate_by_name(bad_inv, "post_harvest_inventory")
    assert not v, "Committed + uncommitted > available should fail"
    assert any("cannot exceed quantity available" in err for err in e)
