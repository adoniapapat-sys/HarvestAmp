# tests/test_crop_protection_inventory.py
"""Integration and contract tests for the crop-protection inventory slice."""
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

def test_gateway_loads_crop_protection_inventory(pvf_profile, gbo_profile, mock_grant):
    """Verify that ToolGateway loads crop-protection inventory items with correct prefixes."""
    gateway = ToolGateway()
    
    # 1. Test PVF
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    pvf_ids = [item["result_id"] for item in pvf_inv]
    
    assert "res_inv_PVF_INV_HERBICIDE_NONSELECTIVE" in pvf_ids
    assert "res_inv_PVF_INV_FUNGICIDE_GENERAL" in pvf_ids
    assert "res_inv_PVF_INV_ADJUVANT_GENERAL" in pvf_ids
    
    # Check that Fungicide payload has correct fields
    fungicide_item = next(item for item in pvf_inv if item["result_id"] == "res_inv_PVF_INV_FUNGICIDE_GENERAL")
    assert fungicide_item["payload"]["item_type"] == "fungicide"
    assert fungicide_item["payload"]["quantity"] == 4.0
    assert fungicide_item["payload"]["reorder_threshold"] == 5.0
    assert fungicide_item["payload"]["label_on_file"] is False
    assert fungicide_item["payload"]["restricted_use_flag"] is True
    
    # 2. Test GBO
    gbo_inv = gateway.get_inventory(mock_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    gbo_ids = [item["result_id"] for item in gbo_inv]
    assert "res_inv_GBO_INV_BIOCONTROL_GENERAL" in gbo_ids

def test_records_inventory_agent_surfaces_crop_protection(pvf_profile, gbo_profile, mock_grant):
    """Verify RecordsInventoryAgent dynamically identifies low-stock and documentation gaps for crop protection."""
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
    
    # Nonselective Herbicide is 15.0 (reorder 20.0) -> low stock
    # Fungicide Inventory Item is 4.0 (reorder 5.0) -> low stock
    # Adjuvant Inventory Item is 8.0 (reorder 10.0) -> low stock
    assert "Low crop-protection stock watch: Nonselective Herbicide Inventory Item" in finding["summary"]
    assert "Fungicide Inventory Item" in finding["summary"]
    assert "Adjuvant Inventory Item" in finding["summary"]
    
    # Fungicide has label documentation gaps requiring qualified review
    assert "Fungicide Inventory Item has label documentation gaps requiring qualified review" in finding["summary"]
    assert "Resolve label/SDS/organic documentation gaps and route for qualified review" in finding["recommendation"]
    assert "This is documentation context only and not treatment, product, rate, tank-mix, or timing advice." in finding["summary"]
    
    # Check that evidence IDs are preserved
    assert "res_inv_PVF_INV_HERBICIDE_NONSELECTIVE" in finding["evidence_ids"]
    assert "res_inv_PVF_INV_FUNGICIDE_GENERAL" in finding["evidence_ids"]

def test_procurement_agent_crop_protection_neutral_context(pvf_profile, mock_grant):
    """Verify ProcurementAgent includes crop-protection stock as neutral context without buy recommendations."""
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
    
    # Neutral stock context should appear
    assert "Crop-protection stock status (neutral context): Nonselective Herbicide Inventory Item" in fert_finding["summary"]
    
    # But it must NOT recommend crop-protection purchases or quote inquiries based solely on this
    assert "reorder crop-protection" not in fert_finding["recommendation"].lower()
    assert "herbicide" not in fert_finding["recommendation"].lower()

def test_compliance_agent_routes_to_expert_review(pvf_profile, gbo_profile, mock_grant):
    """Verify ComplianceAgent routes missing docs and restricted use/applicator flags to expert review."""
    gateway = ToolGateway()
    agent = ComplianceAgent()
    
    # 1. GBO Biological Control lacks organic documentation
    gbo_inv = gateway.get_inventory(mock_grant, "GBO_DIRECT_001", "GBO_DIRECT_001", gbo_profile)
    work_item = {
        "work_item_id": "wi_gbo_comp",
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
    
    finding = agent.run(work_item, context, inventory=gbo_inv)
    
    # GBO Biological Control Inventory Item lacks organic documentation
    assert "Biological Control Inventory Item has organic documentation documentation gaps requiring qualified review" in finding["summary"]
    assert "needs_expert_review" == finding["human_review"]["status"]
    assert "expert_review" == finding["human_review"]["review_type"]
    assert "tier_3" == finding["human_review"]["risk_tier"]
    assert "crop_protection_documentation_gap" in finding["human_review"]["reason"]
    assert "resolve_GBO_INV_BIOCONTROL_GENERAL_documentation" in finding["human_review"]["approval_required_before"]

    # 2. PVF restricted use and applicator license required
    pvf_inv = gateway.get_inventory(mock_grant, "PVF_ROW_CROP_001", "PVF_ROW_CROP_001", pvf_profile)
    work_item["farm_id"] = "PVF_ROW_CROP_001"
    work_item["topic"] = "weekly_plan_pvf"
    context["farm_type"] = "large_conventional_row_crop"
    context["topic"] = "weekly_plan_pvf"
    finding_pvf = agent.run(work_item, context, inventory=pvf_inv)
    assert "Fungicide Inventory Item is flagged as restricted-use and requires qualified review" in finding_pvf["summary"]
    assert "Nonselective Herbicide Inventory Item is flagged as requiring a licensed applicator and requires qualified review" in finding_pvf["summary"]
    assert "needs_user_approval" == finding_pvf["human_review"]["status"]
    assert "user_approval" == finding_pvf["human_review"]["review_type"]
    assert "restricted_use_review" in finding_pvf["human_review"]["reason"]
    assert "applicator_license_review" in finding_pvf["human_review"]["reason"]

def test_field_employee_redactions(pvf_profile, mock_grant):
    """Verify field employee views do not expose supplier prices, terms, or financial details."""
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
        "requesting_user_id": "pvf_employee_001",
        "topic": "weekly_plan_pvf"
    }
    context = {
        "user_role": "field_employee",
        "farm_type": "large_conventional_row_crop",
        "topic": "weekly_plan_pvf"
    }
    findings = agent.run(work_item, context, quotes, pvf_inv)
    serialized = json.dumps(findings).lower()
    
    restricted = ["475", "supplier pricing", "quote price", "operating margin", "invoice", "buyer terms"]
    for word in restricted:
        assert word not in serialized

def test_safety_advisory_wording_compliance(pvf_profile, mock_grant):
    """Verify that agent outputs do not contain pesticide recommendations, spray instructions, or tank-mix advice."""
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
    serialized = json.dumps(finding).lower()
    serialized_clean = serialized.replace(
        "this is documentation context only and not treatment, product, rate, tank-mix, or timing advice.", ""
    ).replace(
        "resolve label/sds/organic documentation gaps and route for qualified review.", ""
    ).replace(
        "restricted-use or applicator-license flags require qualified review.", ""
    )
    
    # Avoid prescribing applications
    assert "apply" not in serialized_clean
    assert "spray" not in serialized_clean
    assert "treatment" not in serialized_clean
    
    # Avoid recommending specific products or tank mixes
    assert "tank mix" not in serialized_clean
    assert "application rate" not in serialized_clean
    assert "recommended product" not in serialized_clean
    assert "safe to apply" not in serialized_clean
    assert "organic approved" not in serialized_clean
    
    # Avoid execution language
    assert "order placed" not in serialized
    assert "purchase approved" not in serialized
    assert "supplier selected" not in serialized
    assert "message sent" not in serialized
    assert "official record updated" not in serialized
    assert "inventory updated" not in serialized
