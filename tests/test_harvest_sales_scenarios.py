# tests/test_harvest_sales_scenarios.py
"""Functional tests verifying MVP harvest and sales scenarios (HARV-001 through HARV-106)."""
import os
import yaml
import pytest
from harvestamp.workflows.supervisor import Supervisor

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def load_scenario_context(scenario_id: str) -> tuple:
    scenarios = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "scenarios.yaml")))
    observations = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    scenario = next((s for s in scenarios if s["scenario_id"] == scenario_id), None)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found.")
    farm_file = "prairie_view_farms.yaml" if "PVF" in scenario["farm_profile"] else "green_basket_organics.yaml"
    farm_profile = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", farm_file)))
    return scenario, farm_profile, observations

def test_harv_001_tomato_harvest():
    scen, farm, obs = load_scenario_context("HARV-001")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "draft"
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "harvest_records")
    assert "Draft cooler inventory updates" in rec["summary"]
    
    # Assert proposed actions
    acts = ap["proposed_actions"]
    assert any(a["action_type"] == "draft_harvest_record_update" for a in acts)
    assert any(a["action_type"] == "draft_cooler_inventory_update" for a in acts)
    for a in acts:
        assert a["external_action"] is False
        assert a["status"] == "blocked_pending_user_approval"
    assert ap["human_review_status"]["status"] == "needs_user_approval"
    
    # Assert source_evidence_id and related_evidence matches record type
    act_harvest = next(a for a in acts if a["action_type"] == "draft_harvest_record_update")
    assert act_harvest["payload"]["source_evidence_id"].startswith("res_harv_")
    
    act_cooler = next(a for a in acts if a["action_type"] == "draft_cooler_inventory_update")
    assert act_cooler["payload"]["source_evidence_id"].startswith("res_phi_")
    assert any(e.startswith("res_harv_") for e in act_cooler["payload"]["related_evidence"])

def test_harv_002_csa_packout_shortage():
    scen, farm, obs = load_scenario_context("HARV-002")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "draft"
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "direct_market_sales")
    assert "Shortage is 27.0 bags" in rec["summary"]
    # No draft/blocked wording in the recommendation/summary because it is read-only operation advice
    assert "draft/blocked" not in rec["recommendation"].lower()
    assert "draft/blocked" not in rec["summary"].lower()

def test_harv_003_restaurant_fulfillment_shortage():
    scen, farm, obs = load_scenario_context("HARV-003")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "draft"
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "direct_market_sales")
    assert "shortage of 7.0 bags" in rec["summary"]
    assert "draft/blocked" not in rec["recommendation"].lower()

def test_harv_004_farmers_market_returns():
    scen, farm, obs = load_scenario_context("HARV-004")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "farmers_market")
    assert "squash 20.0 lbs returned" in rec["summary"]
    assert "draft/blocked pending review" in rec["summary"]
    
    # Assert proposed action
    acts = ap["proposed_actions"]
    assert any(a["action_type"] == "draft_returned_inventory_reconciliation" for a in acts)
    for a in acts:
        assert a["external_action"] is False
        assert a["status"] == "blocked_pending_user_approval"
    assert ap["human_review_status"]["status"] == "needs_user_approval"
    
    # Assert blockers
    assert "verify_returned_inventory_quality" in ap["human_review_status"]["approval_required_before"]
    assert "reconcile_sales_records" in ap["human_review_status"]["approval_required_before"]
    assert "commit_to_official_records" in ap["human_review_status"]["approval_required_before"]
    
    # Assert primary evidence ID is the sales record, and related contains com and phi
    act = next(a for a in acts if a["action_type"] == "draft_returned_inventory_reconciliation")
    assert act["payload"]["source_evidence_id"] == "res_sal_GBO_SAL_001"
    assert any(e.startswith("res_com_") for e in act["payload"]["related_evidence"])
    assert any(e.startswith("res_phi_") for e in act["payload"]["related_evidence"])

def test_harv_005_shrink_cull_tracking():
    scen, farm, obs = load_scenario_context("HARV-005")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "harvest_records")
    assert "tomatoes 20.0 lbs cull" in rec["summary"]
    assert "16.7% shrink" in rec["summary"]

def test_harv_006_sales_reconciliation():
    scen, farm, obs = load_scenario_context("HARV-006")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "direct_market_sales")
    assert "$495.00" in rec["summary"]
    assert "partially_reconciled" in rec["summary"]
    assert "draft/blocked pending review" in rec["summary"]
    
    # Assert proposed action
    acts = ap["proposed_actions"]
    assert any(a["action_type"] == "draft_sales_record_reconciliation" for a in acts)
    for a in acts:
        assert a["external_action"] is False
        assert a["status"] == "blocked_pending_user_approval"
    assert ap["human_review_status"]["status"] == "needs_user_approval"
    
    # Assert primary evidence ID is the sales record, and related contains com and phi
    act = next(a for a in acts if a["action_type"] == "draft_sales_record_reconciliation")
    assert act["payload"]["source_evidence_id"] == "res_sal_GBO_SAL_001"
    assert any(e.startswith("res_com_") for e in act["payload"]["related_evidence"])
    assert any(e.startswith("res_phi_") for e in act["payload"]["related_evidence"])

def test_harv_101_load_ticket_intake():
    scen, farm, obs = load_scenario_context("HARV-101")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "grain_records")
    assert "gross weight 1,000.0 bushels" in rec["summary"]
    assert "draft/blocked pending review" in rec["summary"]
    
    # Assert proposed action
    acts = ap["proposed_actions"]
    assert any(a["action_type"] == "draft_grain_load_ticket_record" for a in acts)
    for a in acts:
        assert a["external_action"] is False
        assert a["status"] == "blocked_pending_user_approval"
    assert ap["human_review_status"]["status"] == "needs_user_approval"
    
    # Assert primary evidence ID is the specific load ticket
    act = next(a for a in acts if a["action_type"] == "draft_grain_load_ticket_record")
    assert act["payload"]["source_evidence_id"] == "res_tkt_PVF_TKT_001"

def test_harv_102_yield_summary():
    scen, farm, obs = load_scenario_context("HARV-102")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "yield_records")
    assert "Field C adjusted quantity" in rec["missing_data"]
    assert rec["human_review_status"]["status"] == "needs_info"
    
    # Assert blockers and reviewers
    hr = rec["human_review_status"]
    assert "provide_field_c_adjusted_quantity" in hr["approval_required_before"]
    assert "provide_field_c_dockage_or_shrink" in hr["approval_required_before"]
    assert "farm_owner" in hr["recommended_reviewer"]
    assert "farm_manager" in hr["recommended_reviewer"]

def test_harv_103_bin_reconciliation():
    scen, farm, obs = load_scenario_context("HARV-103")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "grain_records")
    assert "Bin 3 corn 15,000.0 bushels" in rec["summary"]
    assert "out_of_sync" in rec["summary"]
    assert "draft/blocked pending review" in rec["summary"]
    
    # Assert proposed action
    acts = ap["proposed_actions"]
    assert any(a["action_type"] == "draft_bin_reconciliation" for a in acts)
    for a in acts:
        assert a["external_action"] is False
        assert a["status"] == "needs_info"
    assert ap["human_review_status"]["status"] == "needs_info"
    
    # Assert primary evidence ID is the out-of-sync bin record
    act = next(a for a in acts if a["action_type"] == "draft_bin_reconciliation")
    assert act["payload"]["source_evidence_id"] == "res_bin_PVF_BIN_003"

def test_harv_104_elevator_delivery_settlement():
    scen, farm, obs = load_scenario_context("HARV-104")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "commodity_markets")
    assert "PVF_YLD_002 soybeans" in rec["summary"]
    assert "draft/blocked pending review" in rec["summary"]
    
    # Assert proposed action
    acts = ap["proposed_actions"]
    assert any(a["action_type"] == "draft_elevator_settlement_record" for a in acts)
    for a in acts:
        assert a["external_action"] is False
        assert a["status"] == "blocked_pending_user_approval"
    assert ap["human_review_status"]["status"] == "needs_user_approval"
    
    # Assert primary evidence ID is the soybean yield record PVF_YLD_002 (and not PVF_YLD_001)
    act = next(a for a in acts if a["action_type"] == "draft_elevator_settlement_record")
    assert act["payload"]["source_evidence_id"] == "res_yld_PVF_YLD_002"

def test_harv_105_stored_grain_watch():
    scen, farm, obs = load_scenario_context("HARV-105")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "commodity_markets")
    assert "stored corn" in rec["summary"].lower()
    assert "local elevator bid and basis are missing" in rec["summary"].lower()
    assert "blocked due to missing local bid/basis data" in rec["recommendation"]
    assert "local bid and basis data" in rec["missing_data"]
    
    # Assert blockers
    hr = ap["human_review_status"]
    assert hr["status"] == "needs_info"
    assert "provide_local_bid" in hr["approval_required_before"]
    assert "provide_local_basis" in hr["approval_required_before"]
    assert "no_sale_recommendation_without_current_farm_authorized_bid_basis" in hr["approval_required_before"]

def test_harv_106_crop_insurance_caution():
    scen, farm, obs = load_scenario_context("HARV-106")
    ap = Supervisor().run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "compliance_records")
    assert "crop insurance" in rec["summary"].lower()
    assert "blocked pending approval" in rec["recommendation"]
    
    # Check recommended reviewer and blockers
    hr = ap["human_review_status"]
    assert hr["status"] == "needs_expert_review"
    assert "certified_crop_advisor" in hr["recommended_reviewer"]
    assert "farm_owner" in hr["recommended_reviewer"]
    assert "report_to_crop_insurance" in hr["approval_required_before"]
    assert "report_to_fsa" in hr["approval_required_before"]

