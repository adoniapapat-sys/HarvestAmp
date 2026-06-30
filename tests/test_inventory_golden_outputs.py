# tests/test_inventory_golden_outputs.py
"""Golden output regression tests for weekly plans and inventory coverage."""
import os
import json
import yaml
import pytest
from harvestamp.workflows.supervisor import Supervisor
from harvestamp.core.contracts import contains_forbidden_wording

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))
GOLDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "golden", "inventory_weekly_plans"))

def load_farm_and_obs(farm_id: str) -> tuple:
    farm_file = "prairie_view_farms.yaml" if farm_id == "PVF_ROW_CROP_001" else "green_basket_organics.yaml"
    farm_profile = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", farm_file)))
    observations = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    return farm_profile, observations

def normalize_actionpack_for_golden(action_pack: dict) -> dict:
    status = action_pack.get("status")
    
    recs = action_pack.get("recommendations", [])
    rec_count = len(recs)
    rec_types = sorted(list(set(r.get("recommendation_type") for r in recs if r.get("recommendation_type"))))
    rec_titles = sorted(list(set(r.get("title") for r in recs if r.get("title"))))
    
    proposed_actions = action_pack.get("proposed_actions", [])
    proposed_types = sorted(list(set(a.get("action_type") for a in proposed_actions if a.get("action_type"))))
    
    proposed_statuses = sorted(list(set(
        a.get("status") or a.get("human_review_status", {}).get("status")
        for a in proposed_actions
        if a.get("status") or a.get("human_review_status", {}).get("status")
    )))
    
    missing_data = sorted(list(set(action_pack.get("missing_data", []))))
    warnings = sorted(list(set(action_pack.get("warnings", []))))
    
    evidence_summary = action_pack.get("evidence_summary", [])
    evidence_ids = sorted(list(set(e.get("evidence_id") for e in evidence_summary if e.get("evidence_id"))))
    evidence_trust_tiers = sorted(list(set(e.get("trust_tier") for e in evidence_summary if e.get("trust_tier"))))
    
    hr = action_pack.get("human_review_status", {})
    human_review = {
        "required": hr.get("required"),
        "status": hr.get("status"),
        "review_type": hr.get("review_type"),
        "approval_required_before": sorted(list(set(hr.get("approval_required_before", [])))),
        "recommended_reviewers": sorted(list(set(hr.get("recommended_reviewers", []))))
    }
    
    ap_str = json.dumps(action_pack).lower()
    
    has_fert = any(k in ap_str for k in ["fertilizer", "soil amendment", "urea", "uan 32", "granular fertilizer"]) or \
               any("fert" in e or "urea" in e or "uan" in e for e in evidence_ids)
               
    has_ppe = any(k in ap_str for k in ["safety/ppe", "safety gear", "ppe", "goggles", "gloves"]) or \
              any("ppe" in e for e in evidence_ids)
              
    has_cp = any(k in ap_str for k in ["herbicide", "fungicide", "adjuvant", "biological control", "biocontrol", "pesticide", "restricted-use", "applicator license", "label", "sds", "rei/phi", "organic documentation"]) or \
             any(any(x in e for x in ["herbicide", "fungicide", "adjuvant", "biocontrol", "pesticide"]) for e in evidence_ids)
             
    has_eq = any(k in ap_str for k in ["equipment maintenance", "spare parts", "tractor fuel filter", "planter disk opener", "hydraulic hose", "tiller drive belt", "greenhouse fan replacement motor", "walk-behind tiller", "fan belt", "replacement motor"]) or \
             any(any(x in e for x in ["part_tractor", "part_planter", "supply_hydraulic", "part_tiller", "part_greenhouse", "tractor_filter", "planter_disk", "hydraulic_hose"]) for e in evidence_ids)
             
    has_irr = any(k in ap_str for k in ["irrigation maintenance", "irrigation pump drive belt", "irrigation mainline valve", "drip tape", "drip irrigation emitters", "irrigation valve and fitting kit", "hose repair coupler", "drip irrigation system"]) or \
              any(any(x in e for x in ["irr_pump", "irr_main", "irr_drip", "irr_emitter", "irr_valve", "irr_hose", "pump_belt", "main_valve", "drip_tape", "emitters", "valve_kit", "hose_coupler"]) for e in evidence_ids)
              
    has_pkg = any(k in ap_str for k in ["csa box", "pint clamshell", "quart clamshell", "packaging", "receipt paper", "tent weight", "paper bags"]) or \
              any(any(x in e for x in ["clamshell", "boxes", "bags", "paper", "weights", "tent"]) for e in evidence_ids)
              
    has_grain = any(k in ap_str for k in ["grain bin", "stored grain", "bushels", "moisture", "test weight", "corn", "soybeans"]) or \
                any(any(x in e for x in ["bin_", "yld_", "tkt_", "load_ticket"]) for e in evidence_ids)
                
    inventory_coverage = {
        "fertilizer_or_soil_amendment": has_fert,
        "safety_ppe": has_ppe,
        "crop_protection_documentation": has_cp,
        "equipment_or_spare_parts": has_eq,
        "irrigation_supplies": has_irr,
        "packaging_or_market_supplies": has_pkg,
        "stored_grain_or_bin": has_grain
    }
    
    has_proposed_actions = len(proposed_actions) > 0
    
    restricted_terms = [
        "supplier pricing", "quote price", "operating margin", "gross margin", "customer financial", 
        "payment status", "buyer terms", "invoice", "official approval",
        "42,000.0 bu", "9,000.0 bu", "corn 56,000.0", "basis", "$184,800.00", "csa box reorder",
        "green bistro", "495.00", "partially_reconciled", "partially reconciled", "wholesale price", "2.40", "3.80"
    ]
    contains_rest = any(k in ap_str for k in restricted_terms)
    contains_forb = len(contains_forbidden_wording(ap_str)) > 0
    
    role_safety = {
        "has_proposed_actions": has_proposed_actions,
        "contains_restricted_terms": contains_rest,
        "contains_forbidden_wording": contains_forb
    }
    
    return {
        "status": status,
        "recommendation_count": rec_count,
        "recommendation_types": rec_types,
        "recommendation_titles_or_topics": rec_titles,
        "proposed_action_types": proposed_types,
        "proposed_action_statuses": proposed_statuses,
        "missing_data": missing_data,
        "warnings": warnings,
        "evidence_ids": evidence_ids,
        "evidence_trust_tiers": evidence_trust_tiers,
        "human_review": human_review,
        "inventory_coverage": inventory_coverage,
        "role_safety": role_safety
    }

@pytest.fixture
def pvf_profile():
    return load_farm_and_obs("PVF_ROW_CROP_001")[0]

@pytest.fixture
def gbo_profile():
    return load_farm_and_obs("GBO_DIRECT_001")[0]

@pytest.mark.parametrize("farm_id, role, prompt, golden_filename", [
    ("PVF_ROW_CROP_001", "farm_owner", "What should I know about Prairie View Farms this week?", "pvf_farm_owner_weekly_plan.json"),
    ("PVF_ROW_CROP_001", "field_employee", "What should I know about Prairie View Farms this week?", "pvf_field_employee_weekly_plan.json"),
    ("GBO_DIRECT_001", "farm_owner", "What should I know about Green Basket Organics this week?", "gbo_farm_owner_weekly_plan.json"),
    ("GBO_DIRECT_001", "field_employee", "What should I know about Green Basket Organics this week?", "gbo_field_employee_weekly_plan.json"),
])
def test_inventory_weekly_plan_golden_outputs(farm_id, role, prompt, golden_filename):
    """Verify weekly plan ActionPack outputs match semantic golden JSON baselines."""
    supervisor = Supervisor()
    farm_profile, observations = load_farm_and_obs(farm_id)
    
    # Resolve user_id
    user_id = "user_001"
    for user in farm_profile.get("users", []):
        if user.get("role") == role:
            user_id = user.get("user_id")
            break
            
    ap = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id=user_id,
        user_role=role,
        prompt=prompt,
        observations=observations
    )
    
    normalized = normalize_actionpack_for_golden(ap)
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
                "UPDATE_GOLDENS=1 python -m pytest tests/test_inventory_golden_outputs.py -q"
            )
            
        with open(golden_path, "r") as f:
            golden_data = json.load(f)
            
        assert normalized == golden_data

def test_field_employee_golden_outputs_are_role_safe(pvf_profile, gbo_profile):
    """Verify that field employee golden outputs do not expose restricted information."""
    supervisor = Supervisor()
    obs = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    for farm, farm_id in [(pvf_profile, "PVF_ROW_CROP_001"), (gbo_profile, "GBO_DIRECT_001")]:
        user_id = next(u["user_id"] for u in farm.get("users", []) if u["role"] == "field_employee")
        ap = supervisor.run_workflow(
            farm_profile=farm,
            user_id=user_id,
            user_role="field_employee",
            prompt="Weekly plan",
            observations=obs
        )
        normalized = normalize_actionpack_for_golden(ap)
        
        assert normalized["role_safety"]["has_proposed_actions"] is False
        assert normalized["role_safety"]["contains_restricted_terms"] is False
        assert normalized["role_safety"]["contains_forbidden_wording"] is False

def test_farm_owner_golden_outputs_preserve_inventory_coverage(pvf_profile, gbo_profile):
    """Verify that farm owner outputs preserve correct structured inventory coverage and evidence IDs."""
    supervisor = Supervisor()
    obs = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    # 1. PVF Owner
    user_id_pvf = next(u["user_id"] for u in pvf_profile.get("users", []) if u["role"] == "farm_owner")
    ap_pvf = supervisor.run_workflow(pvf_profile, user_id_pvf, "farm_owner", "Weekly plan", obs)
    norm_pvf = normalize_actionpack_for_golden(ap_pvf)
    
    assert norm_pvf["inventory_coverage"]["fertilizer_or_soil_amendment"] is True
    assert norm_pvf["inventory_coverage"]["safety_ppe"] is True
    assert norm_pvf["inventory_coverage"]["crop_protection_documentation"] is True
    assert norm_pvf["inventory_coverage"]["equipment_or_spare_parts"] is True
    assert norm_pvf["inventory_coverage"]["irrigation_supplies"] is True
    assert norm_pvf["inventory_coverage"]["stored_grain_or_bin"] is True
    
    # At least one res_inv_* evidence ID is present
    assert any(e.startswith("res_inv_") for e in norm_pvf["evidence_ids"])
    
    # 2. GBO Owner
    user_id_gbo = next(u["user_id"] for u in gbo_profile.get("users", []) if u["role"] == "farm_owner")
    ap_gbo = supervisor.run_workflow(gbo_profile, user_id_gbo, "farm_owner", "Weekly plan", obs)
    norm_gbo = normalize_actionpack_for_golden(ap_gbo)
    
    assert norm_gbo["inventory_coverage"]["fertilizer_or_soil_amendment"] is True
    assert norm_gbo["inventory_coverage"]["safety_ppe"] is True
    assert norm_gbo["inventory_coverage"]["crop_protection_documentation"] is True
    assert norm_gbo["inventory_coverage"]["equipment_or_spare_parts"] is True
    assert norm_gbo["inventory_coverage"]["irrigation_supplies"] is True
    assert norm_gbo["inventory_coverage"]["packaging_or_market_supplies"] is True
    
    assert any(e.startswith("res_inv_") for e in norm_gbo["evidence_ids"])

def test_golden_outputs_preserve_draft_only_action_semantics(pvf_profile, gbo_profile):
    """Verify that all outputs remain draft-only and contain only allowed local statuses."""
    supervisor = Supervisor()
    obs = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    for farm in [pvf_profile, gbo_profile]:
        for role in ["farm_owner", "field_employee"]:
            user_id = next(u["user_id"] for u in farm.get("users", []) if u["role"] == role)
            ap = supervisor.run_workflow(farm, user_id, role, "Weekly plan", obs)
            
            # Action statuses must be known safe ones
            for a in ap.get("proposed_actions", []):
                status = a.get("status") or a.get("human_review_status", {}).get("status")
                if status:
                    assert status in [
                        "draft", "needs_info", "needs_user_approval", "needs_expert_review",
                        "blocked_pending_user_approval", "review_not_required", "approved"
                    ]
                
            # No output contains executed-action wording
            ap_str = json.dumps(ap).lower()
            assert not contains_forbidden_wording(ap_str)

def test_public_context_not_action_anchor_in_golden_outputs(pvf_profile, gbo_profile):
    """Verify that public-context evidence is not used as the primary anchor for proposed actions."""
    supervisor = Supervisor()
    obs = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    for farm in [pvf_profile, gbo_profile]:
        for role in ["farm_owner"]:
            user_id = next(u["user_id"] for u in farm.get("users", []) if u["role"] == role)
            ap = supervisor.run_workflow(farm, user_id, role, "Weekly plan", obs)
            
            # If public-context evidence (like weather or benchmark) is present, proposed actions must not be solely anchored on them.
            for action in ap.get("proposed_actions", []):
                ref_ev = action.get("payload", {}).get("source_evidence_id", "")
                if ref_ev:
                    # Verify primary source evidence is not a public context source
                    assert not ref_ev.startswith("res_wtr_")
                    assert not ref_ev.startswith("res_bnc_")
