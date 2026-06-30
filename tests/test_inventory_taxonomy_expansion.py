# tests/test_inventory_taxonomy_expansion.py
"""Integration and contract tests for the fertilizer and PPE inventory slice."""
import os
import yaml
import pytest
import json
from harvestamp.gateway.tools import ToolGateway
from harvestamp.agents import RecordsInventoryAgent, ProcurementAgent, ComplianceAgent
from harvestamp.core.contracts import normalize_agent_finding_contract, contains_forbidden_wording

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def load_farm_profile(filename):
    path = os.path.join(FIXTURES_DIR, "farms", filename)
    with open(path, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def pvf_profile():
    return load_farm_profile("prairie_view_farms.yaml")

@pytest.fixture
def gbo_profile():
    return load_farm_profile("green_basket_organics.yaml")

@pytest.fixture
def mock_grant():
    return {"authorized": True, "capability": "capability:records_tool"}

@pytest.fixture
def mock_procurement_grants():
    # Grant both fertilizer_tool and fuel_tool capabilities for procurement
    return {"authorized": True, "capability": "capability:fertilizer_tool"}

def test_tool_gateway_loads_new_inventory(pvf_profile, gbo_profile, mock_grant):
    """Verify that ToolGateway loads new fertilizer and PPE inventory items with correct prefixes."""
    gateway = ToolGateway()
    
    # 1. Test PVF
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    pvf_ids = [item["result_id"] for item in pvf_inv]
    
    assert "res_inv_PVF_INV_UREA" in pvf_ids
    assert "res_inv_PVF_INV_UAN32" in pvf_ids
    assert "res_inv_PVF_INV_PPE_RESPIRATORS" in pvf_ids
    assert "res_inv_PVF_INV_PPE_GLOVES" in pvf_ids
    
    # Check that Urea payload has correct fields
    urea_item = next(item for item in pvf_inv if item["result_id"] == "res_inv_PVF_INV_UREA")
    assert urea_item["payload"]["item_type"] == "fertilizer"
    assert urea_item["payload"]["quantity"] == 8.0
    assert urea_item["payload"]["reorder_threshold"] == 10.0
    
    # 2. Test GBO
    gbo_inv = gateway.get_inventory(mock_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    gbo_ids = [item["result_id"] for item in gbo_inv]
    
    assert "res_inv_GBO_INV_ORGANIC_FERT" in gbo_ids
    assert "res_inv_GBO_INV_COMPOST" in gbo_ids
    assert "res_inv_GBO_INV_PPE_GOGGLES" in gbo_ids
    assert "res_inv_GBO_INV_PPE_APRONS" in gbo_ids

def test_records_inventory_agent_surfaces_low_stock(pvf_profile, gbo_profile, mock_grant):
    """Verify RecordsInventoryAgent dynamically identifies low-stock items based on reorder_threshold."""
    gateway = ToolGateway()
    agent = RecordsInventoryAgent()
    
    # 1. PVF weekly plan
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    work_item = {
        "work_item_id": "wi_pvf_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    context = {
        "user_role": "farm_owner",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    finding = agent.run(work_item, context, pvf_inv)
    
    # Urea is 8.0 tons (threshold 10.0) -> low stock
    # UAN 32 is 15.0 tons (threshold 10.0) -> OK
    # Respirator Masks is 2.0 (threshold 3.0) -> low stock
    # Gloves is 50.0 (threshold 20.0) -> OK
    assert "Low fertilizer stock watch: Urea" in finding["summary"]
    assert "Low safety/PPE stock watch: Respirator Masks" in finding["summary"]
    assert "UAN 32" not in finding["summary"]
    assert "Safety Gloves" not in finding["summary"]
    assert "Plan to reorder safety/PPE gear" in finding["recommendation"]
    
    # 2. GBO weekly plan
    gbo_inv = gateway.get_inventory(mock_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    work_item = {
        "work_item_id": "wi_gbo_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "weekly_plan_gbo"
    }
    context = {
        "user_role": "farm_owner",
        "farm_type": "small_organic_direct_market",
        "topic": "weekly_plan_gbo"
    }
    finding_gbo = agent.run(work_item, context, gbo_inv)
    
    # GBO Organic Granular Fertilizer is 4.0 (threshold 5.0) -> low
    # GBO Compost is 12.0 (threshold 8.0) -> OK
    # GBO Goggles is 1.0 (threshold 3.0) -> low
    # GBO Aprons is 12.0 (threshold 6.0) -> OK
    assert "Low fertilizer/soil amendment stock watch: Organic Granular Fertilizer" in finding_gbo["summary"]
    assert "Low safety/PPE stock watch: Safety Goggles" in finding_gbo["summary"]
    assert "Compost Amendment" not in finding_gbo["summary"]
    assert "Wash-pack Aprons" not in finding_gbo["summary"]

def test_records_inventory_agent_missing_threshold_neutral(mock_grant):
    """Verify that when reorder_threshold is missing, the agent does not crash and handles it neutrally."""
    agent = RecordsInventoryAgent()
    mock_inv = [
        {
            "result_id": "res_inv_TEST_UREA",
            "payload": {
                "item_id": "TEST_UREA",
                "item_type": "fertilizer",
                "product_name": "Urea",
                "quantity": 10.0,
                "unit": "tons",
                "last_updated": "2026-06-21"
                # missing reorder_threshold
            }
        }
    ]
    work_item = {
        "work_item_id": "wi_pvf_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001"
    }
    context = {
        "user_role": "farm_owner",
        "farm_type": "row_crop",
        "topic": "weekly_plan_pvf"
    }
    
    # Should run successfully without crashing
    finding = agent.run(work_item, context, mock_inv)
    assert finding is not None
    # Since reorder_threshold is missing, it should not list it as low stock
    assert "Low fertilizer stock watch" not in finding["summary"]

def test_records_inventory_agent_unsafe_wording(pvf_profile, mock_grant):
    """Verify RecordsInventoryAgent does not emit purchase, execution, or order placement language."""
    gateway = ToolGateway()
    agent = RecordsInventoryAgent()
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    work_item = {
        "work_item_id": "wi_pvf_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001"
    }
    context = {
        "user_role": "farm_owner",
        "farm_type": "row_crop",
        "topic": "weekly_plan_pvf"
    }
    finding = agent.run(work_item, context, pvf_inv)
    
    # Serialize finding and check forbidden wording
    serialized = json.dumps(finding)
    forbidden = contains_forbidden_wording(serialized)
    assert forbidden == []
    
    # Check extra unsafe phrases
    unsafe_phrases = ["order placed", "purchase approved", "supplier selected", "message sent", "official record updated", "inventory updated"]
    for phrase in unsafe_phrases:
         assert phrase not in serialized.lower()

def test_procurement_agent_fertilizer_stock_context(pvf_profile, gbo_profile, mock_grant, mock_procurement_grants):
    """Verify ProcurementAgent incorporates fertilizer stock levels and suggests draft inquiries when low."""
    gateway = ToolGateway()
    agent = ProcurementAgent()
    
    # Mock some quotes
    quotes = [
        {
            "result_id": "res_quote_urea",
            "payload": {"product_name": "Urea", "price": 475.00, "unit": "USD_per_ton", "quote_id": "PVF_Q1"}
        },
        {
            "result_id": "res_quote_uan",
            "payload": {"product_name": "UAN 32", "price": 340.00, "unit": "USD_per_ton", "quote_id": "PVF_Q2"}
        }
    ]
    
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    work_item = {
        "work_item_id": "wi_pvf_proc",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001"
    }
    context = {
        "user_role": "farm_owner",
        "farm_type": "row_crop",
        "topic": "weekly_plan_pvf"
    }
    
    findings = agent.run(work_item, context, quotes, pvf_inv)
    assert isinstance(findings, list)
    
    fert_finding = next(f for f in findings if f["recommendation_type"] == "fertilizer_quote_watch")
    
    # Urea is low -> should trigger reorder draft note
    assert "Urea stock is 8.0 tons (below threshold 10.0 tons)" in fert_finding["summary"]
    assert "UAN 32 stock is 15.0 tons" in fert_finding["summary"]
    assert "Consider preparing a draft supplier quote request for owner/manager review due to low stocks" in fert_finding["recommendation"]
    
    # Verify no execution / send language
    serialized = json.dumps(fert_finding)
    assert "order placed" not in serialized.lower()
    assert "message sent" not in serialized.lower()

def test_procurement_agent_field_employee_redaction(pvf_profile, mock_grant):
    """Verify ProcurementAgent redacts price details and quotes for field_employee users."""
    gateway = ToolGateway()
    agent = ProcurementAgent()
    quotes = [
        {
            "result_id": "res_quote_urea",
            "payload": {"product_name": "Urea", "price": 475.00, "unit": "USD_per_ton", "quote_id": "PVF_Q1"}
        }
    ]
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    work_item = {
        "work_item_id": "wi_pvf_proc",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_employee_001"
    }
    context = {
        "user_role": "field_employee",
        "farm_type": "row_crop",
        "topic": "weekly_plan_pvf"
    }
    
    findings = agent.run(work_item, context, quotes, pvf_inv)
    serialized = json.dumps(findings).lower()
    
    # Prices and supplier details must be redacted
    assert "475" not in serialized
    assert "pricing details" in serialized or "details are hidden" in serialized
    assert "operating margin" not in serialized

def test_compliance_agent_surfaces_ppe_gaps_advisory_only(pvf_profile, gbo_profile, mock_grant):
    """Verify ComplianceAgent surfaces safety PPE gaps strictly as safety readiness warnings, without chemical advice."""
    gateway = ToolGateway()
    agent = ComplianceAgent()
    
    # 1. Test GBO (low goggles stock)
    gbo_inv = gateway.get_inventory(mock_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    work_item = {
        "work_item_id": "wi_gbo_comp",
        "workflow_id": "weekly_plan",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001"
    }
    context = {
        "user_role": "farm_owner",
        "farm_type": "organic_market_garden",
        "topic": "weekly_plan_gbo"
    }
    
    finding = agent.run(work_item, context, inventory=gbo_inv)
    
    # Goggles is low -> Goggles (1.0 units) should appear as safety readiness watch
    assert "Safety readiness watch: PPE inventory checks show low stock for: Safety Goggles" in finding["summary"]
    assert "Plan to reorder safety PPE to maintain safety readiness" in finding["recommendation"]
    
    # Assert no pesticide chemical advice is present
    serialized = json.dumps(finding).lower()
    assert "apply this pesticide" not in serialized
    assert "spray tomorrow" not in serialized
    assert "tank mix" not in serialized
