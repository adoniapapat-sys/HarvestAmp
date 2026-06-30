# tests/test_equipment_irrigation_inventory.py
"""Integration and contract tests for the equipment & irrigation inventory slice."""
import os
import yaml
import pytest
import subprocess
from harvestamp.gateway.tools import ToolGateway
from harvestamp.agents import RecordsInventoryAgent, ProcurementAgent
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

def test_fixture_validation_passes():
    """Verify that validate_fixtures.py passes cleanly."""
    res = subprocess.run(["python", "scripts/validate_fixtures.py"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "All fixtures validated successfully." in res.stdout

def test_gateway_loads_equipment_irrigation_inventory(pvf_profile, gbo_profile, mock_grant):
    """Verify that ToolGateway loads equipment and irrigation items with correct prefixes and custom properties."""
    gateway = ToolGateway()
    
    # 1. Test PVF
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    pvf_ids = [item["result_id"] for item in pvf_inv]
    
    assert "res_inv_PVF_INV_PART_TRACTOR_FILTER" in pvf_ids
    assert "res_inv_PVF_INV_PART_PLANTER_DISK" in pvf_ids
    assert "res_inv_PVF_INV_SUPPLY_HYDRAULIC_HOSE" in pvf_ids
    assert "res_inv_PVF_INV_IRR_PUMP_BELT" in pvf_ids
    assert "res_inv_PVF_INV_IRR_MAIN_VALVE" in pvf_ids
    
    tractor_filter = next(item for item in pvf_inv if item["result_id"] == "res_inv_PVF_INV_PART_TRACTOR_FILTER")
    assert tractor_filter["payload"]["item_type"] == "equipment_part"
    assert tractor_filter["payload"]["quantity"] == 1.0
    assert tractor_filter["payload"]["reorder_threshold"] == 2.0
    assert tractor_filter["payload"]["compatible_equipment"] == "Tractor"
    assert tractor_filter["payload"]["maintenance_criticality"] == "medium"
    
    pump_belt = next(item for item in pvf_inv if item["result_id"] == "res_inv_PVF_INV_IRR_PUMP_BELT")
    assert pump_belt["payload"]["item_type"] == "irrigation_supply"
    assert pump_belt["payload"]["quantity"] == 0.0
    assert pump_belt["payload"]["reorder_threshold"] == 1.0
    assert pump_belt["payload"]["compatible_equipment"] == "Irrigation pump"
    assert pump_belt["payload"]["maintenance_criticality"] == "high"
    
    # 2. Test GBO
    gbo_inv = gateway.get_inventory(mock_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    gbo_ids = [item["result_id"] for item in gbo_inv]
    assert "res_inv_GBO_INV_PART_TILLER_BELT" in gbo_ids
    assert "res_inv_GBO_INV_IRR_DRIP_TAPE" in gbo_ids

def test_records_inventory_agent_surfaces_equipment_irrigation(pvf_profile, mock_grant):
    """Verify RecordsInventoryAgent identifies low-stock equipment and irrigation parts with correct disclaimers."""
    gateway = ToolGateway()
    agent = RecordsInventoryAgent()
    
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
    
    # tractor fuel filter (1 <= 2), planter disk opener (4 <= 4), hydraulic hose (1 <= 2) are low stock
    assert "Equipment maintenance stock watch: low stock for: Tractor Fuel Filter (1.0 units), Planter Disk Opener (4.0 units), Hydraulic Hose (1.0 units)." in finding["summary"]
    # irrigation pump drive belt (0 <= 1), mainline valve (2 <= 2) are low stock
    assert "Irrigation maintenance readiness watch: low stock for: Irrigation Pump Drive Belt (0.0 units), Irrigation Mainline Valve (2.0 units)." in finding["summary"]
    
    assert "Prepare list of required spare parts for owner/manager review." in finding["recommendation"]
    assert "Review irrigation system readiness and prepare list of replacement parts for manager review." in finding["recommendation"]
    assert "This is inventory readiness context only and not a repair schedule, vendor contact, equipment modification, irrigation setting change, or maintenance-log update." in finding["summary"]

def test_records_inventory_agent_threshold_boundaries():
    """Verify that quantity <= reorder_threshold triggers stock warnings, and quantity > threshold does not."""
    agent = RecordsInventoryAgent()
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
    
    # 1. At threshold: qty 2.0, threshold 2.0 -> triggers
    inv_at = [{
        "result_id": "res_inv_item_1",
        "payload": {
            "item_id": "item_1",
            "item_type": "equipment_part",
            "product_name": "Tractor Filter",
            "quantity": 2.0,
            "reorder_threshold": 2.0,
            "unit": "units"
        }
    }]
    finding_at = agent.run(work_item, context, inv_at)
    assert "Tractor Filter (2.0 units)" in finding_at["summary"]
    
    # 2. Above threshold: qty 3.0, threshold 2.0 -> does not trigger
    inv_above = [{
        "result_id": "res_inv_item_1",
        "payload": {
            "item_id": "item_1",
            "item_type": "equipment_part",
            "product_name": "Tractor Filter",
            "quantity": 3.0,
            "reorder_threshold": 2.0,
            "unit": "units"
        }
    }]
    finding_above = agent.run(work_item, context, inv_above)
    assert "Equipment maintenance stock watch" not in finding_above["summary"]
    
    # 3. Missing threshold: reorder_threshold is None -> does not crash or trigger
    inv_missing = [{
        "result_id": "res_inv_item_1",
        "payload": {
            "item_id": "item_1",
            "item_type": "equipment_part",
            "product_name": "Tractor Filter",
            "quantity": 2.0,
            "unit": "units"
        }
    }]
    finding_missing = agent.run(work_item, context, inv_missing)
    assert "Equipment maintenance stock watch" not in finding_missing["summary"]

def test_procurement_agent_equipment_irrigation_neutral_context(pvf_profile, mock_grant):
    """Verify ProcurementAgent treats equipment/irrigation low stock as neutral context only."""
    gateway = ToolGateway()
    agent = ProcurementAgent()
    
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
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    context = {
        "user_role": "farm_owner",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    
    findings = agent.run(work_item, context, quotes, pvf_inv)
    fert_finding = next(f for f in findings if f["recommendation_type"] == "fertilizer_quote_watch")
    
    # Neutral context
    assert "Equipment and irrigation stock status (neutral context):" in fert_finding["summary"]
    assert "Tractor Fuel Filter" in fert_finding["summary"]
    assert "Planter Disk Opener" in fert_finding["summary"]
    assert "Irrigation Pump Drive Belt" in fert_finding["summary"]
    
    # Recommendation
    assert "Low-stock equipment or irrigation items can be compiled for owner/manager review." in fert_finding["recommendation"]
    
    # Must NOT recommend purchasing
    assert "order tractor" not in fert_finding["recommendation"].lower()
    assert "buy drive belt" not in fert_finding["recommendation"].lower()

def test_field_employee_redactions(pvf_profile, mock_grant):
    """Verify field employee outputs redact pricing and financial details."""
    gateway = ToolGateway()
    agent = ProcurementAgent()
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
        "requesting_user_id": "pvf_emp_001",
        "topic": "weekly_plan_pvf"
    }
    context = {
        "user_role": "field_employee",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    
    findings = agent.run(work_item, context, quotes, pvf_inv)
    for f in findings:
        assert "475" not in f["summary"]
        assert "340" not in f["summary"]
        assert "475" not in f["recommendation"]
        assert "340" not in f["recommendation"]

def test_no_executed_actions_wording(pvf_profile, mock_grant):
    """Verify no finding contains executed or external action wording."""
    gateway = ToolGateway()
    agent = RecordsInventoryAgent()
    
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
    
    forbidden = [
        "order placed", "supplier selected", "vendor contacted", "dealer contacted",
        "repair completed", "maintenance log updated", "inventory updated",
        "irrigation setting changed", "system modified"
    ]
    for word in forbidden:
        assert word not in finding["summary"].lower()
        assert word not in finding["recommendation"].lower()
