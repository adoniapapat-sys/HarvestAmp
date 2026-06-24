# tests/test_freshness.py
"""Tests for data freshness and staleness handling policies."""
import os
import yaml
from harvestamp.agents.specialists import ProcurementAgent

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def test_stale_inventory_lowers_confidence():
    """Verify that stale inventory level triggers low confidence and warnings."""
    agent = ProcurementAgent()
    
    work_item = {
        "work_item_id": "wi_test_freshness",
        "workflow_id": "wf_test_freshness",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "user_intent": "Do I have enough clamshells?"
    }
    
    context = {"farm_type": "small_organic_direct_market"}
    
    # Fresh inventory data
    inventory_fresh = [
        {
            "result_id": "res_csa_boxes",
            "payload": {"item_id": "csa_boxes", "item_type": "csa_boxes", "quantity": 110, "last_updated": "2026-06-21", "product_name": "CSA Boxes"}
        },
        {
            "result_id": "res_clamshells",
            "payload": {"item_id": "clamshells", "item_type": "pint_clamshells", "quantity": 160, "last_updated": "2026-06-21", "product_name": "Pint Clamshells"}
        }
    ]
    
    finding_fresh = agent.run(work_item, context, [], inventory_fresh)
    assert finding_fresh["confidence"] == "medium" # Medium due to clamshell usage uncertainty, but not low
    
    # Stale inventory data (last updated May 29, planning week is late June)
    inventory_stale = [
        {
            "result_id": "res_csa_boxes",
            "payload": {"item_id": "csa_boxes", "item_type": "csa_boxes", "quantity": 110, "last_updated": "2026-06-21", "product_name": "CSA Boxes"}
        },
        {
            "result_id": "res_clamshells_stale",
            "payload": {"item_id": "clamshells", "item_type": "pint_clamshells", "quantity": 160, "last_updated": "2026-05-29", "product_name": "Pint Clamshells"}
        }
    ]
    
    finding_stale = agent.run(work_item, context, [], inventory_stale)
    assert finding_stale["confidence"] == "low"
    assert any("stale" in str(md).lower() for md in finding_stale["missing_data"])
