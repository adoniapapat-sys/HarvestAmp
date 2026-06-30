# tests/test_weekly_plan_harvest_coverage.py
"""Tests verifying concise weekly plan harvest coverage and employee redactions."""
import os
import yaml
import pytest
from harvestamp.workflows.supervisor import Supervisor

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def load_context():
    obs = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    pvf_farm = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")))
    gbo_farm = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", "green_basket_organics.yaml")))
    return obs, pvf_farm, gbo_farm

def test_pvf_weekly_plan_owner_vs_employee():
    obs, pvf_farm, _ = load_context()
    supervisor = Supervisor()

    # Owner Weekly Plan
    ap_owner = supervisor.run_workflow(
        farm_profile=pvf_farm,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="Show weekly plan for Prairie View",
        observations=obs
    )
    assert ap_owner["status"] == "draft"
    
    # Assert proposed actions use correct source evidence IDs
    acts = ap_owner["proposed_actions"]
    
    fuel_act = next(a for a in acts if a["action_type"] == "supplier_message")
    assert fuel_act["payload"]["source_evidence_id"] == "res_quote_PVF_QUOTE_DIESEL_2026_06_21"
    
    bin_act = next(a for a in acts if a["action_type"] == "draft_bin_reconciliation")
    assert bin_act["payload"]["source_evidence_id"] == "res_bin_PVF_BIN_003"
    
    yield_act = next(a for a in acts if a["action_type"] == "draft_official_record_update")
    assert yield_act["payload"]["source_evidence_id"].startswith("res_yld_") or yield_act["payload"]["source_evidence_id"].startswith("res_tkt_")
    
    
    inv_act = next(a for a in acts if a["action_type"] == "draft_inventory_reconciliation")
    assert inv_act["payload"]["source_evidence_id"] == "res_bin_PVF_BIN_003"
    
    # Assert owner sees grain/harvest details
    records_rec = next(r for r in ap_owner["recommendations"] if r["recommendation_type"] == "inventory_records")
    assert "stored corn" in records_rec["summary"].lower() or "corn 42,000.0 bu" in records_rec["summary"].lower()
    
    market_rec = next(r for r in ap_owner["recommendations"] if r["recommendation_type"] == "commodity_markets")
    assert "basis" in market_rec["recommendation"].lower() or "price" in market_rec["summary"].lower()
    
    # Employee Weekly Plan
    ap_emp = supervisor.run_workflow(
        farm_profile=pvf_farm,
        user_id="pvf_employee_001",
        user_role="field_employee",
        prompt="Show weekly plan for Prairie View",
        observations=obs
    )
    assert ap_emp["status"] == "draft"

    # Redactions check: no exact pricing, margin, or quote values in employee view
    import json
    emp_str = json.dumps(ap_emp).lower()
    assert "42,000.0 bu" not in emp_str
    assert "9,000.0 bu" not in emp_str
    assert "corn 56,000.0" not in emp_str
    assert "basis" not in emp_str
    assert "$184,800.00" not in emp_str
    assert "csa box reorder" not in emp_str

    # Redacted evidence checklist
    ev_ids = [e["evidence_id"] for e in ap_emp["evidence_summary"]]
    assert "res_yld_PVF_YLD_001" not in ev_ids
    assert "res_bin_PVF_BIN_001" not in ev_ids
    assert "res_bin_PVF_BIN_002" not in ev_ids
    assert "Authorized operational records" in ev_ids

    # Assert draft actions are completely hidden for employee
    assert not ap_emp["proposed_actions"]
    for r in ap_emp["recommendations"]:
        assert not r.get("proposed_actions")

def test_gbo_weekly_plan_owner_vs_employee():
    obs, _, gbo_farm = load_context()
    supervisor = Supervisor()

    # Owner view
    ap_owner = supervisor.run_workflow(
        farm_profile=gbo_farm,
        user_id="gbo_owner_001",
        user_role="farm_owner",
        prompt="Show GBO weekly plan",
        observations=obs
    )
    
    # Assert proposed actions use correct source evidence IDs
    acts = ap_owner["proposed_actions"]
    
    csa_act = next(a for a in acts if a["action_type"] == "supplier_message")
    assert csa_act["payload"]["source_evidence_id"] == "res_inv_GBO_INV_CSA_BOXES"
    
    cert_act = next(a for a in acts if a["action_type"] == "share_with_certifier")
    assert cert_act["payload"]["source_evidence_id"].startswith("res_harv_")
    
    cooler_act = next(a for a in acts if a["action_type"] == "draft_cooler_inventory_update")
    assert cooler_act["payload"]["source_evidence_id"].startswith("res_phi_")
    
    inv_act = next(a for a in acts if a["action_type"] == "draft_inventory_reconciliation")
    assert inv_act["payload"]["source_evidence_id"].startswith("res_phi_")
    
    # Assert owner section review status
    rec_phi = next(r for r in ap_owner["recommendations"] if r["recommendation_type"] == "inventory_records")
    assert "tomatoes 100.0 lbs" in rec_phi["summary"] or "tomatoes" in rec_phi["summary"]
    assert rec_phi["human_review_status"]["status"] == "needs_user_approval"

    # Lead view (redacted/operational-only)
    ap_lead = supervisor.run_workflow(
        farm_profile=gbo_farm,
        user_id="gbo_field_lead_001",
        user_role="field_lead",
        prompt="Show GBO weekly plan",
        observations=obs
    )
    rec_lead = next(r for r in ap_lead["recommendations"] if r["recommendation_type"] == "inventory_records")
    assert "cooler inventory updates" in rec_lead["summary"].lower()
    assert "draft/blocked pending review" in rec_lead["summary"].lower()

def test_no_weekly_plan_crowding():
    obs, pvf_farm, gbo_farm = load_context()
    supervisor = Supervisor()

    ap_pvf = supervisor.run_workflow(pvf_farm, "pvf_owner_001", "farm_owner", "Show PVF plan", obs)
    for rec in ap_pvf["recommendations"]:
        # Verify summaries are concise
        assert len(rec["summary"].split("\n")) <= 5, f"Summary in {rec['title']} is too long: {rec['summary']}"

    ap_gbo = supervisor.run_workflow(gbo_farm, "gbo_owner_001", "farm_owner", "Show GBO plan", obs)
    for rec in ap_gbo["recommendations"]:
        assert len(rec["summary"].split("\n")) <= 5, f"Summary in {rec['title']} is too long: {rec['summary']}"

def test_gbo_weekly_plan_employee_redactions():
    obs, _, gbo_farm = load_context()
    supervisor = Supervisor()

    ap_emp = supervisor.run_workflow(
        farm_profile=gbo_farm,
        user_id="gbo_employee_001",
        user_role="field_employee",
        prompt="Show weekly plan for GBO",
        observations=obs
    )
    assert ap_emp["status"] == "draft"

    # Redactions check: no customer names, sales totals, payment status, pricing, margin, unpaid invoice details in employee view
    import json
    emp_str = json.dumps(ap_emp).lower()

    # Redact customer names
    assert "green bistro" not in emp_str

    # Redact sales totals / cash deposit values
    assert "495.00" not in emp_str

    # Redact payment status
    assert "partially_reconciled" not in emp_str
    assert "partially reconciled" not in emp_str

    # Redact margins or pricing
    assert "operating margin" not in emp_str
    assert "16.7%" not in emp_str
    assert "wholesale price" not in emp_str
    assert "2.40" not in emp_str
    assert "3.80" not in emp_str

    # Redact unpaid invoice details
    assert "unpaid" not in emp_str
    assert "invoice" not in emp_str

    # Redacted evidence checklist
    ev_ids = [e["evidence_id"] for e in ap_emp["evidence_summary"]]
    assert "res_sal_GBO_SAL_001" not in ev_ids
    assert "res_com_GBO_COM_001" not in ev_ids
    assert "res_com_GBO_COM_002" not in ev_ids
    assert "Authorized operational records" in ev_ids

    # Assert draft actions are completely hidden for employee
    assert not ap_emp["proposed_actions"]
    for r in ap_emp["recommendations"]:
        assert not r.get("proposed_actions")
