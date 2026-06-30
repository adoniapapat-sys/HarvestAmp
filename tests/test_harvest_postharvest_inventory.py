# tests/test_harvest_postharvest_inventory.py
"""Tests for harvest, post-harvest, and packaging supply inventory slice."""
import os
import json
import yaml
import pytest
from harvestamp.gateway.tools import ToolGateway
from harvestamp.agents import RecordsInventoryAgent, ProcurementAgent, ComplianceAgent, MarketSalesAgent
from harvestamp.core.contracts import normalize_agent_finding_contract, contains_forbidden_wording

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def load_farm_profile(filename: str) -> dict:
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
def mock_procurement_grant():
    return {"authorized": True, "capability": "capability:fertilizer_tool"}

def test_fixture_validation(pvf_profile, gbo_profile):
    """Verify that added items have correct item_types and properties."""
    # PVF Check
    pvf_bags = next(i for i in pvf_profile["inventory"] if i["item_id"] == "PVF_INV_GRAIN_SAMPLE_BAGS")
    assert pvf_bags["item_type"] == "grain_storage_supply"
    assert pvf_bags["compatible_workflow"] == "grain_storage"
    
    pvf_env = next(i for i in pvf_profile["inventory"] if i["item_id"] == "PVF_INV_LOAD_TICKET_ENVELOPES")
    assert pvf_env["item_type"] == "harvest_supply"
    assert pvf_env["compatible_workflow"] == "harvest_records"
    
    # GBO Check
    gbo_totes = next(i for i in gbo_profile["inventory"] if i["item_id"] == "GBO_INV_HARVEST_TOTES")
    assert gbo_totes["item_type"] == "harvest_supply"
    assert gbo_totes["compatible_workflow"] == "harvest"
    
    gbo_strips = next(i for i in gbo_profile["inventory"] if i["item_id"] == "GBO_INV_SANITIZER_TEST_STRIPS")
    assert gbo_strips["item_type"] == "wash_pack_supply"
    assert gbo_strips["food_safety_relevant"] is True
    assert gbo_strips["compatible_workflow"] == "wash_pack"

def test_tool_gateway_loads_supplies(pvf_profile, gbo_profile, mock_grant):
    """Verify that new harvest and packaging supplies load through ToolGateway with res_inv_* prefixes."""
    gateway = ToolGateway()
    
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    pvf_ids = [item["result_id"] for item in pvf_inv]
    assert "res_inv_PVF_INV_GRAIN_SAMPLE_BAGS" in pvf_ids
    assert "res_inv_PVF_INV_LOAD_TICKET_ENVELOPES" in pvf_ids
    assert "res_inv_PVF_INV_BIN_LABELS" in pvf_ids
    assert "res_inv_PVF_INV_BIN_CLEANOUT_SUPPLIES" in pvf_ids
    
    gbo_inv = gateway.get_inventory(mock_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    gbo_ids = [item["result_id"] for item in gbo_inv]
    assert "res_inv_GBO_INV_HARVEST_TOTES" in gbo_ids
    assert "res_inv_GBO_INV_SANITIZER_TEST_STRIPS" in gbo_ids
    assert "res_inv_GBO_INV_PRODUCE_BAGS" in gbo_ids
    assert "res_inv_GBO_INV_CSA_LINERS" in gbo_ids
    assert "res_inv_GBO_INV_COOLER_LABELS" in gbo_ids

def test_records_agent_pvf_readiness(pvf_profile):
    """Verify RecordsAgent surfaces PVF harvest/grain-storage readiness context."""
    agent = RecordsInventoryAgent()
    gateway = ToolGateway()
    grant = {"authorized": True, "capability": "capability:records_tool"}
    inv = gateway.get_inventory(grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    
    # Run weekly plan for PVF Owner
    wi = {
        "work_item_id": "wi_pvf_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    ctx = {
        "user_role": "farm_owner",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    f = agent.run(wi, ctx, inv)
    
    assert f is not None
    assert "Harvest supply readiness watch: low stock for: Load Ticket Envelopes" in f["summary"]
    assert "Grain storage/bin readiness watch: low stock" in f["summary"]
    assert "Grain Sample Bags" in f["summary"]
    assert "Grain Bin Labels" in f["summary"]
    assert "Bin Cleanout Supplies" in f["summary"]
    assert "Verify bin cleanout and grain sampling preparation checklist" in f["recommendation"]
    
    # Assert safety disclaimer is present
    assert "This is inventory readiness context only and not a completed harvest" in f["summary"]

def test_records_agent_gbo_readiness(gbo_profile):
    """Verify RecordsAgent surfaces GBO harvest/wash-pack/packaging/market readiness context."""
    agent = RecordsInventoryAgent()
    gateway = ToolGateway()
    grant = {"authorized": True, "capability": "capability:records_tool"}
    inv = gateway.get_inventory(grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    
    # Run weekly plan for GBO Owner
    wi = {
        "work_item_id": "wi_gbo_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "weekly_plan_gbo"
    }
    ctx = {
        "user_role": "farm_owner",
        "farm_type": "small_organic_direct_market",
        "topic": "weekly_plan_gbo"
    }
    f = agent.run(wi, ctx, inv)
    
    assert f is not None
    assert "Harvest supply readiness watch: low stock for: Harvest Totes" in f["summary"]
    assert "Post-harvest/wash-pack supply readiness watch: low stock" in f["summary"]
    assert "Sanitizer Test Strips" in f["summary"]
    assert "Cooler Labels" in f["summary"]
    assert "Packaging/market supply watch: low stock" in f["summary"]
    assert "Pint Clamshells" in f["summary"]
    assert "Quart Clamshells" in f["summary"]
    assert "CSA Boxes" in f["summary"]
    assert "Produce Bags" in f["summary"]
    assert "CSA Box Liners" in f["summary"]
    assert "Sanitizer Test Strips sanitizer monitoring details" in f["missing_data"]

def test_quantity_threshold_triggers():
    """Verify quantity <= reorder_threshold behavior, and no threshold doesn't crash."""
    agent = RecordsInventoryAgent()
    wi = {
        "work_item_id": "wi_gbo_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "weekly_plan_gbo"
    }
    ctx = {
        "user_role": "farm_owner",
        "farm_type": "small_organic_direct_market",
        "topic": "weekly_plan_gbo"
    }
    
    # 1. quantity <= reorder_threshold triggers
    inv_low = [{
        "result_id": "res_inv_totes",
        "payload": {
            "item_id": "res_inv_totes",
            "item_type": "harvest_supply",
            "product_name": "Harvest Totes",
            "quantity": 10.0,
            "reorder_threshold": 12.0,
            "unit": "units",
            "last_updated": "2026-06-21"
        }
    }]
    f_low = agent.run(wi, ctx, inv_low)
    assert "Harvest Totes" in f_low["summary"]
    
    # 2. quantity > reorder_threshold does not trigger
    inv_high = [{
        "result_id": "res_inv_totes",
        "payload": {
            "item_id": "res_inv_totes",
            "item_type": "harvest_supply",
            "product_name": "Harvest Totes",
            "quantity": 15.0,
            "reorder_threshold": 12.0,
            "unit": "units",
            "last_updated": "2026-06-21"
        }
    }]
    f_high = agent.run(wi, ctx, inv_high)
    assert "Harvest supply readiness watch" not in f_high["summary"]
    
    # 3. Missing reorder_threshold does not crash
    inv_missing_thresh = [{
        "result_id": "res_inv_totes",
        "payload": {
            "item_id": "res_inv_totes",
            "item_type": "harvest_supply",
            "product_name": "Harvest Totes",
            "quantity": 15.0,
            "unit": "units",
            "last_updated": "2026-06-21"
        }
    }]
    f_missing = agent.run(wi, ctx, inv_missing_thresh)
    assert "Harvest supply readiness watch" not in f_missing["summary"]

def test_procurement_agent_neutral_context(pvf_profile, gbo_profile, mock_procurement_grant):
    """Verify ProcurementAgent includes low-stock supplies as neutral context only."""
    agent = ProcurementAgent()
    gateway = ToolGateway()
    grant = {"authorized": True, "capability": "capability:records_tool"}
    
    pvf_inv = gateway.get_inventory(grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    gbo_inv = gateway.get_inventory(grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    
    pvf_quotes = gateway.get_quotes(mock_procurement_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    gbo_quotes = gateway.get_quotes(mock_procurement_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    
    # PVF check
    wi_pvf = {
        "work_item_id": "wi_pvf_proc",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    ctx_pvf = {
        "user_role": "farm_owner",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    findings_pvf = agent.run(wi_pvf, ctx_pvf, pvf_quotes, pvf_inv)
    
    f_fert_pvf = next(f for f in findings_pvf if f["recommendation_type"] == "fertilizer_quote_watch")
    assert "Harvest and grain storage stock status (neutral context):" in f_fert_pvf["summary"]
    assert "Load Ticket Envelopes" in f_fert_pvf["summary"]
    assert "Low-stock harvest, wash-pack, packaging, or market supply items can be compiled for owner/manager review." in f_fert_pvf["recommendation"]
    
    # GBO check
    wi_gbo = {
        "work_item_id": "wi_gbo_proc",
        "workflow_id": "weekly_plan",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "weekly_plan_gbo"
    }
    ctx_gbo = {
        "user_role": "farm_owner",
        "farm_type": "small_organic_direct_market",
        "topic": "weekly_plan_gbo"
    }
    finding_gbo = agent.run(wi_gbo, ctx_gbo, gbo_quotes, gbo_inv)
    
    assert "GBO harvest, wash-pack, and packaging stock status (neutral context):" in finding_gbo["summary"]
    assert "Pint Clamshells" in finding_gbo["summary"]
    assert "Low-stock harvest, wash-pack, packaging, or market supply items can be compiled for owner/manager review." in finding_gbo["recommendation"]

def test_market_sales_agent_non_executing():
    """Verify MarketSalesAgent remains non-executing and doesn't crash on standard queries."""
    agent = MarketSalesAgent()
    # Check that csa_packout_check operates as normal
    wi = {
        "work_item_id": "wi_gbo_mkt",
        "workflow_id": "csa_packout",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "csa_packout_check"
    }
    ctx = {
        "user_role": "farm_owner",
        "farm_type": "small_organic_direct_market",
        "topic": "csa_packout_check"
    }
    
    post_harvest_inventory = [{
        "result_id": "res_inv_gbo_inv_salad_mix",
        "source_id": "DS-003",
        "payload": {
            "item_id": "salad_mix",
            "quantity": 48.0,
            "unit": "bags"
        }
    }]
    sales_commitments = [{"result_id": "res_com_1", "payload": {"csa_members": 75}}]
    
    f = agent.run(
        wi, ctx, 
        sales_commitments=sales_commitments, 
        post_harvest_inventory=post_harvest_inventory
    )
    assert f is not None
    assert "Shortage is 27.0 bags" in f["summary"]
    assert "Prepare a harvest plan" in f["recommendation"]

def test_employee_redactions(pvf_profile):
    """Verify that employee views redact pricing, margins, stored grain volume details."""
    agent = RecordsInventoryAgent()
    gateway = ToolGateway()
    grant = {"authorized": True, "capability": "capability:records_tool"}
    inv = gateway.get_inventory(grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    
    wi = {
        "work_item_id": "wi_pvf_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_employee_001",
        "topic": "weekly_plan_pvf"
    }
    ctx = {
        "user_role": "field_employee",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    f = agent.run(wi, ctx, inv)
    
    # Employee summary check
    assert "42,000 bushels" not in f["summary"]
    assert "9,000 bushels" not in f["summary"]
    assert "stored_grain_records" in f.get("prohibited_disclosures", [])

def test_no_unsafe_or_executed_action_wording(pvf_profile):
    """Verify no findings contain executed actions or advisor drift phrases."""
    agent = RecordsInventoryAgent()
    gateway = ToolGateway()
    grant = {"authorized": True, "capability": "capability:records_tool"}
    inv = gateway.get_inventory(grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    
    wi = {
        "work_item_id": "wi_pvf_rec",
        "workflow_id": "weekly_plan",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    ctx = {
        "user_role": "farm_owner",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    f = agent.run(wi, ctx, inv)
    
    ap_str = json.dumps(f).lower()
    
    disclaimer = "This system cannot recommend specific chemical/spray applications, pesticide products, rates of application, or tank mixes.".lower()
    cleaned_ap_str = ap_str.replace(disclaimer, "")
    
    assert not contains_forbidden_wording(cleaned_ap_str)
