# tests/test_scenario_golden_outputs.py
"""Golden output regression tests for focused workflow scenarios."""
import os
import json
import yaml
import pytest
from harvestamp.workflows.supervisor import Supervisor
from harvestamp.core.contracts import contains_forbidden_wording
from tests.test_inventory_golden_outputs import normalize_actionpack_for_golden

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))
GOLDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "golden", "scenarios"))

def load_scenario_context(scenario_id: str) -> tuple:
    """Helper to load fixtures and scenarios."""
    scenarios = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "scenarios.yaml")))
    observations = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    scenario = next((s for s in scenarios if s["scenario_id"] == scenario_id), None)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found.")
        
    farm_file = "prairie_view_farms.yaml" if "PVF" in scenario["farm_profile"] or "multi_tenant" in scenario["farm_profile"] else "green_basket_organics.yaml"
    farm_profile = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", farm_file)))
    
    return scenario, farm_profile, observations

def normalize_actionpack_for_scenario_golden(action_pack: dict) -> dict:
    normalized = normalize_actionpack_for_golden(action_pack)
    
    ap_str = json.dumps(action_pack).lower()
    
    has_procurement = any(r.get("recommendation_type") == "fertilizer_quote_watch" or "procurement" in str(r).lower() for r in action_pack.get("recommendations", [])) or \
                      "procurement" in ap_str or "quote" in ap_str or "price" in ap_str
                      
    has_compliance = any(r.get("recommendation_type") == "compliance_records" or "compliance" in str(r).lower() for r in action_pack.get("recommendations", [])) or \
                     "compliance" in ap_str
                     
    has_records_inventory = any(r.get("recommendation_type") in ["inventory_records", "organic_input_records"] or "records" in str(r).lower() or "inventory" in str(r).lower() for r in action_pack.get("recommendations", [])) or \
                            "records" in ap_str or "inventory" in ap_str
                            
    has_crop_protection = "spray" in ap_str or "pesticide" in ap_str or "herbicide" in ap_str or "fungicide" in ap_str or "adjuvant" in ap_str
    
    has_organic = "organic" in ap_str or "omri" in ap_str or "certifier" in ap_str or "osp" in ap_str
    
    has_packaging = "packaging" in ap_str or "clamshell" in ap_str or "csa box" in ap_str or "tent weight" in ap_str
    
    has_fuel = "fuel" in ap_str or "diesel" in ap_str or "tank" in ap_str
    
    has_missing = len(action_pack.get("missing_data", [])) > 0
    
    has_public = any(e.get("connector_mode") == "public" or "public" in str(e).lower() for e in action_pack.get("evidence_summary", [])) or \
                 "public" in ap_str
                 
    normalized["scenario_flags"] = {
        "has_procurement_context": has_procurement,
        "has_compliance_context": has_compliance,
        "has_records_inventory_context": has_records_inventory,
        "has_crop_protection_guardrail": has_crop_protection,
        "has_organic_documentation_context": has_organic,
        "has_packaging_or_market_supply_context": has_packaging,
        "has_fuel_or_diesel_context": has_fuel,
        "has_missing_data": has_missing,
        "has_public_context": has_public
    }
    
    return normalized

@pytest.mark.parametrize("scenario_id, golden_filename", [
    ("PVF-002", "pvf_002_diesel_purchase_window.json"),
    ("GBO-004", "gbo_004_packaging_reorder.json"),
    ("PVF-005", "pvf_005_spray_window_guardrail.json"),
    ("GBO-005", "gbo_005_organic_input_verification.json"),
])
def test_scenario_golden_outputs(scenario_id, golden_filename):
    """Verify scenario ActionPack outputs match semantic golden JSON baselines."""
    supervisor = Supervisor()
    scen, farm, obs = load_scenario_context(scenario_id)
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    normalized = normalize_actionpack_for_scenario_golden(ap)
    
    golden_path = os.path.join(GOLDEN_DIR, golden_filename)
    update_goldens = os.environ.get("UPDATE_GOLDENS") == "1"
    
    if update_goldens:
        os.makedirs(GOLDEN_DIR, exist_ok=True)
        with open(golden_path, "w") as f:
            json.dump(normalized, f, indent=2, sort_keys=True)
    else:
        if not os.path.exists(golden_path):
            pytest.fail(
                f"Golden file missing: {golden_path}. "
                "Run with UPDATE_GOLDENS=1 environment variable to create it: "
                "UPDATE_GOLDENS=1 python -m pytest tests/test_scenario_golden_outputs.py -q"
            )
            
        with open(golden_path, "r") as f:
            golden_data = json.load(f)
            
        assert normalized == golden_data

def test_diesel_purchase_window_golden_safety():
    """Verify PVF-002 diesel purchase evaluation is safe and context-only."""
    supervisor = Supervisor()
    scen, farm, obs = load_scenario_context("PVF-002")
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    norm = normalize_actionpack_for_scenario_golden(ap)
    
    assert norm["scenario_flags"]["has_fuel_or_diesel_context"] is True
    assert norm["scenario_flags"]["has_procurement_context"] is True
    
    ap_str = json.dumps(ap).lower()
    for word in ["order placed", "supplier selected", "message sent", "purchase approved", "inventory updated"]:
        assert word not in ap_str
        
    for a in ap.get("proposed_actions", []):
        status = a.get("status") or a.get("human_review_status", {}).get("status")
        if status:
            assert status in [
                "draft", "needs_info", "needs_user_approval", "needs_expert_review",
                "blocked_pending_user_approval", "review_not_required", "approved"
            ]

def test_packaging_reorder_golden_safety():
    """Verify GBO-004 packaging reorder evaluation is safe and draft-only."""
    supervisor = Supervisor()
    scen, farm, obs = load_scenario_context("GBO-004")
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    norm = normalize_actionpack_for_scenario_golden(ap)
    
    assert norm["scenario_flags"]["has_packaging_or_market_supply_context"] is True
    
    ap_str = json.dumps(ap).lower()
    for word in ["supplier contact", "message sent", "order placed", "purchase approved", "invoice sent", "inventory updated"]:
        assert word not in ap_str
        
    for a in ap.get("proposed_actions", []):
        status = a.get("status") or a.get("human_review_status", {}).get("status")
        if status:
            assert status in [
                "draft", "needs_info", "needs_user_approval", "needs_expert_review",
                "blocked_pending_user_approval", "review_not_required", "approved"
            ]

def test_spray_window_golden_guardrail():
    """Verify PVF-005 spray window check strictly enforces pesticide label and application rate guardrails."""
    supervisor = Supervisor()
    scen, farm, obs = load_scenario_context("PVF-005")
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    norm = normalize_actionpack_for_scenario_golden(ap)
    
    assert norm["scenario_flags"]["has_crop_protection_guardrail"] is True
    
    ap_str = json.dumps(ap).lower()
    # Check that no chemical spray rate/tank-mix recommendations are present
    assert "apply this pesticide" not in ap_str
    assert "safe to apply" not in ap_str
    
    for a in ap.get("proposed_actions", []):
        status = a.get("status") or a.get("human_review_status", {}).get("status")
        if status:
            assert status in [
                "draft", "needs_info", "needs_user_approval", "needs_expert_review",
                "blocked_pending_user_approval", "review_not_required", "approved"
            ]

def test_organic_input_verification_golden_guardrail():
    """Verify GBO-005 organic input check enforces OSP compliance and review guardrails."""
    supervisor = Supervisor()
    scen, farm, obs = load_scenario_context("GBO-005")
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    norm = normalize_actionpack_for_scenario_golden(ap)
    
    assert norm["scenario_flags"]["has_organic_documentation_context"] is True
    assert norm["scenario_flags"]["has_compliance_context"] is True
    
    ap_str = json.dumps(ap).lower()
    assert "organic approved" not in ap_str
    assert "certification approved" not in ap_str
    assert "legally compliant" not in ap_str
    assert "safe to use" not in ap_str

def test_scenario_public_context_not_action_anchor():
    """Verify that no proposed action is solely anchored on public context."""
    supervisor = Supervisor()
    obs = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    for scenario_id in ["PVF-002", "GBO-004", "PVF-005", "GBO-005"]:
        scen, farm, _ = load_scenario_context(scenario_id)
        ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
        
        for action in ap.get("proposed_actions", []):
            ref_ev = action.get("payload", {}).get("source_evidence_id", "")
            if ref_ev:
                assert not ref_ev.startswith("res_wtr_")
                assert not ref_ev.startswith("res_bnc_")

def test_scenario_outputs_no_executed_action_wording():
    """Verify that no scenario output contains executed action or advisor drift wording."""
    supervisor = Supervisor()
    obs = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    disclaimer = "This system cannot recommend specific chemical/spray applications, pesticide products, rates of application, or tank mixes.".lower()
    
    for scenario_id in ["PVF-002", "GBO-004", "PVF-005", "GBO-005"]:
        scen, farm, _ = load_scenario_context(scenario_id)
        ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
        ap_str = json.dumps(ap).lower()
        
        # Strip the allowed disclaimer to avoid matching "tank mix"
        cleaned_ap_str = ap_str.replace(disclaimer, "").replace(disclaimer.strip(), "")
        
        assert not contains_forbidden_wording(cleaned_ap_str)
