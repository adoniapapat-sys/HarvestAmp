# tests/test_scenarios.py
"""Functional tests verifying MVP scenario workflows and outcomes."""
import os
import yaml
from harvestamp.workflows.supervisor import Supervisor

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

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

def test_pvf_001_weekly_row_crop_action_plan():
    """PVF-001 is Weekly row-crop action plan."""
    scen, farm, obs = load_scenario_context("PVF-001")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "PVF_ROW_CROP_001"
    assert ap["status"] == "draft"
    assert len(ap["recommendations"]) > 0
    
    # 1. Friday is the best fieldwork window. Caution Wednesday/Thursday. No planting prep.
    weather_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "fieldwork_weather")
    assert "Friday" in weather_rec["summary"]
    assert "Wednesday" in weather_rec["summary"]
    assert "Thursday" in weather_rec["summary"]
    assert "planting prep" not in weather_rec["summary"].lower()
    assert "planting prep" not in weather_rec["recommendation"].lower()
    
    # 2. Diesel watch, fertilizer quotes available but missing delivery/application fees
    fuel_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "fuel_watch")
    assert "1,350" in fuel_rec["summary"]
    assert "3,100" in fuel_rec["summary"]
    assert "low fuel watch" in fuel_rec["summary"].lower() or "fuel watch" in fuel_rec["summary"].lower()
    
    fert_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "fertilizer_quote_watch")
    assert "Urea" in fert_rec["summary"]
    assert "UAN 32" in fert_rec["summary"]
    assert "fertilizer delivery fee" in fert_rec["missing_data"]
    assert "fertilizer application fee" in fert_rec["missing_data"]
    
    # 3. Fuel freshness, crop-protection gaps, stored grain records
    rec_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "inventory_records")
    assert "freshness" in rec_rec["summary"].lower() or "2026-06-21" in rec_rec["summary"]
    assert "herbicide" in rec_rec["summary"].lower() and "partial" in rec_rec["summary"].lower()
    assert "fungicide" in rec_rec["summary"].lower() and "unknown" in rec_rec["summary"].lower()
    assert "adjuvant" in rec_rec["summary"].lower() and "low" in rec_rec["summary"].lower()
    assert "stored grain" in rec_rec["summary"].lower() or "bushels" in rec_rec["summary"]
    
    # 4. Stored grain market scenario watch, watchlist only
    mkt_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "commodity_markets")
    assert "stored corn" in mkt_rec["summary"].lower()
    assert "stored soybeans" in mkt_rec["summary"].lower()
    assert "watchlist" in mkt_rec["recommendation"].lower()
    assert "not a sale recommendation" in mkt_rec["recommendation"].lower()
    
    # 5. USDA acreage reporting watch status unknown, spray/crop-protection watch, pesticide label responsible human caveat
    comp_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "compliance_records")
    assert "acreage reporting" in comp_rec["summary"].lower()
    assert "July 15" in comp_rec["summary"]
    assert "spray" in comp_rec["summary"].lower()
    assert "responsible human" in comp_rec["recommendation"].lower() or "licensed applicator" in comp_rec["recommendation"].lower()
    assert comp_rec["summary"] != "Compliance checks completed. No violations found."
    
    # 6. No organic vegetable margins
    margin_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "margin_scenario")
    assert "organic" not in margin_rec["summary"].lower()
    
    # 7. Action candidates present and requires user approval
    assert any("supplier_message" in act["action_type"] for act in ap["proposed_actions"])
    assert ap["human_review_status"]["required"]
    assert ap["human_review_status"]["review_type"] == "user_approval"

def test_gbo_001_weekly_organic_direct_market_plan():
    """GBO-001 is Weekly organic direct-market plan."""
    scen, farm, obs = load_scenario_context("GBO-001")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "GBO_DIRECT_001"
    assert ap["status"] == "draft"
    
    # 1. Saturday market weather showers/wind, tent weights, ventilation/humidity
    weather_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "market_day_weather")
    assert "shower" in weather_rec["summary"].lower()
    assert "10-16" in weather_rec["summary"]
    assert "weights" in weather_rec["recommendation"].lower()
    assert "ventilation" in weather_rec["recommendation"].lower()
    
    # 2. CSA priorities, clamshell counts, expected harvest volume
    proc_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "weekly_plan_gbo")
    assert "CSA boxes" in proc_rec["summary"]
    assert "160" in proc_rec["summary"]
    assert "85" in proc_rec["summary"]
    assert "expected harvest volume" in proc_rec["missing_data"]
    
    # 3. Packaging counts, receipt paper low, tent weights check, organic documentation incomplete
    rec_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "inventory_records")
    assert "CSA boxes" in rec_rec["summary"]
    assert "receipt paper" in rec_rec["summary"].lower()
    assert "tent weights" in rec_rec["summary"].lower()
    assert "incomplete" in rec_rec["summary"].lower()
    
    # 4. CSA packing 75 members, restaurant availability timing
    mkt_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "direct_market_sales")
    assert "75" in mkt_rec["summary"]
    assert "restaurant" in mkt_rec["summary"].lower()
    
    # 5. Organic documentation watch, OSP input list incomplete, expert/certifier review requirement
    comp_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "compliance_records")
    assert "organic" in comp_rec["summary"].lower()
    assert "osp" in comp_rec["summary"].lower() or "input list" in comp_rec["summary"].lower()
    assert "expert" in comp_rec["recommendation"].lower() or "certifier" in comp_rec["recommendation"].lower()
    assert comp_rec["summary"] != "Compliance checks completed. No violations found."
    
    # 6. Action candidates present (CSA reorder, certifier share)
    assert any("supplier_message" in act["action_type"] for act in ap["proposed_actions"])
    assert any("share_with_certifier" in act["action_type"] for act in ap["proposed_actions"])
    assert ap["human_review_status"]["required"]
    assert ap["human_review_status"]["review_type"] == "expert_review"

def test_restricted_role_weekly_plans():
    """Verify restricted role weekly plans return redacted operational views, not blocked plans."""
    pvf_scen, pvf_farm, obs = load_scenario_context("PVF-001")
    supervisor = Supervisor()
    
    # PVF Field Employee weekly plan
    ap_pvf = supervisor.run_workflow(pvf_farm, "pvf_employee_001", "field_employee", pvf_scen["prompt"], obs)
    assert ap_pvf["status"] == "draft" # NOT blocked!
    assert any("Supplier quotes, input pricing, margin, and marketing details are hidden for your role." in w for w in ap_pvf["warnings"])
    
    # Verify quotes, margin, grain details are hidden/redacted
    fuel_rec = next(r for r in ap_pvf["recommendations"] if r["recommendation_type"] == "fuel_watch")
    assert "hidden" in fuel_rec["recommendation"].lower()
    assert "supplier_quotes" in fuel_rec["prohibited_disclosures"]
    
    fert_rec = next(r for r in ap_pvf["recommendations"] if r["recommendation_type"] == "fertilizer_quote_watch")
    assert "hidden" in fert_rec["summary"].lower()
    assert "supplier_quotes" in fert_rec["prohibited_disclosures"]
    
    mkt_rec = next(r for r in ap_pvf["recommendations"] if r["recommendation_type"] == "weekly_plan_pvf" and r["title"] == "Commodity Markets" or "Market" in r["title"])
    assert "hidden" in mkt_rec["summary"].lower()
    
    margin_rec = next(r for r in ap_pvf["recommendations"] if r["recommendation_type"] == "margin_scenario")
    assert "hidden" in margin_rec["summary"].lower()
    
    # GBO Field Lead weekly plan
    gbo_scen, gbo_farm, obs = load_scenario_context("GBO-001")
    ap_gbo = supervisor.run_workflow(gbo_farm, "gbo_field_lead_001", "field_lead", gbo_scen["prompt"], obs)
    assert ap_gbo["status"] == "draft"
    
    gbo_proc = next(r for r in ap_gbo["recommendations"] if r["recommendation_type"] == "weekly_plan_gbo")
    assert "hidden" in gbo_proc["recommendation"].lower()
    assert "supplier_quotes" in gbo_proc["prohibited_disclosures"]
    
    gbo_rec = next(r for r in ap_gbo["recommendations"] if r["recommendation_type"] == "inventory_records")
    assert "certification_records" in gbo_rec["prohibited_disclosures"]

def test_gbo_002_farmers_market_prep():
    """GBO-002 is Farmers market pack list."""
    scen, farm, obs = load_scenario_context("GBO-002")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "GBO_DIRECT_001"
    assert ap["status"] == "draft"
    
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "farmers_market")
    assert "Structured Pack List" in rec["summary"]
    assert "tomatoes 100 lb" in rec["summary"]
    assert "salad mix 40 bags" in rec["summary"]
    assert "berries 60 pints" in rec["summary"]
    assert "squash 50 lb" in rec["summary"]
    assert "pint clamshells 60" in rec["summary"]
    assert "quart clamshells 30" in rec["summary"]
    assert "paper bags 150" in rec["summary"]
    assert "tent, weights, tables" in rec["summary"]
    assert "weather adjustments" in rec["summary"].lower()
    assert "expected squash harvest estimate" in rec["missing_data"]

def test_pvf_002_diesel_recommendation():
    """PVF-002 returns buy/wait/split diesel recommendation with user_approval required."""
    scen, farm, obs = load_scenario_context("PVF-002")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "fuel_buy_window")
    assert "Consider a split-buy" in rec["recommendation"]
    assert "split-buy" in rec["recommendation"].lower()
    assert "3,350" in rec["recommendation"]
    assert "650" in rec["recommendation"]
    assert "fills" not in rec["recommendation"]
    assert rec["human_review_status"]["required"]
    assert rec["human_review_status"]["review_type"] == "user_approval"
    assert any(act["action_type"] == "supplier_message" for act in ap["proposed_actions"])

def test_pvf_004_fertilizer_comparison():
    """PVF-004 calculates fertilizer cost per pound of N and flags missing delivery/application fees."""
    scen, farm, obs = load_scenario_context("PVF-004")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "fertilizer_comparison")
    assert "0.5163" in rec["summary"] # Urea price per lb of N
    assert "0.5312" in rec["summary"] # UAN 32 price per lb of N
    assert "material price only" in rec["summary"].lower()
    assert "do not purchase urea yet" in rec["recommendation"].lower()
    assert "fertilizer delivery fee" in rec["missing_data"]
    assert "fertilizer application fee" in rec["missing_data"]
    assert "Delivery fees" not in rec["missing_data"]
    assert "Application fees" not in rec["missing_data"]
    assert "low_confidence_due_to_missing_fees" in rec["human_review_status"]["reason"]
    assert "agronomic_sensitive_if_rate_or_timing_recommended" in rec["human_review_status"]["reason"]

def test_pvf_005_spray_window_guardrail():
    """PVF-005 is Spray-window guardrail."""
    scen, farm, obs = load_scenario_context("PVF-005")
    supervisor = Supervisor()
    
    # Test builder context exclusions directly
    builder = supervisor.context_builder
    ctx = builder.build_context_package(farm, scen["user_role"], "spray_window")
    assert len(ctx["relevant_quotes"]) == 0
    assert "fuel_quotes" in ctx["excluded_fields"]
    assert "fertilizer_quotes" in ctx["excluded_fields"]
    assert "stored_grain_inventory" in ctx["excluded_fields"]
    assert "energy_benchmarks" in ctx["excluded_fields"]
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "PVF_ROW_CROP_001"
    assert ap["status"] == "draft"
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "spray_window")
    assert "Morning window is possible" in rec["recommendation"]
    assert rec["human_review_status"]["required"]
    assert rec["human_review_status"]["review_type"] == "expert_review"

def test_gbo_004_packaging_reorder():
    """GBO-004 identifies CSA box shortage for two weeks and handles clamshell uncertainty."""
    scen, farm, obs = load_scenario_context("GBO-004")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "packaging_reorder")
    assert "Prepare a CSA box reorder for owner approval" in rec["recommendation"]
    assert "clamshell volume is uncertain" in rec["recommendation"].lower()

def test_gbo_005_organic_input_verification():
    """GBO-005 is Organic input verification and must not include conventional comparison."""
    scen, farm, obs = load_scenario_context("GBO-005")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "GBO_DIRECT_001"
    assert ap["status"] == "draft"
    
    # 1. No conventional urea/UAN in organic input verification
    assert not any("urea" in str(rec).lower() or "uan" in str(rec).lower() for rec in ap["recommendations"])
    
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "organic_input_verification")
    assert "OMRI verification is uncertain" in rec["summary"]
    assert rec["human_review_status"]["required"]
    assert rec["human_review_status"]["review_type"] == "expert_review"

    # Ensure no packaging evidence is present
    packaging_ev_ids = [
        "res_inv_GBO_INV_PINT_CLAMSHELLS",
        "res_inv_GBO_INV_QUART_CLAMSHELLS",
        "res_inv_GBO_INV_PAPER_BAGS",
        "res_inv_GBO_INV_CSA_BOXES",
        "res_inv_GBO_INV_LABELS"
    ]
    ev_ids_gbo = [ev["evidence_id"] for ev in ap["evidence_summary"]]
    for pkg_id in packaging_ev_ids:
        assert pkg_id not in ev_ids_gbo

    # Records finding must be organic-input documentation, not packaging inventory
    assert not any(r["recommendation_type"] == "inventory_records" for r in ap["recommendations"])
    rec_records = next(r for r in ap["recommendations"] if r["recommendation_type"] == "organic_input_records")
    assert "Organic input records" in rec_records["summary"]

def test_pvf_008_employee_privacy():
    """PVF-008 blocks field employee access to supplier quotes/prices."""
    scen, farm, obs = load_scenario_context("PVF-008")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "blocked"
    assert "do not have permission" in ap["warnings"][0]
    assert ap["human_review_status"]["review_type"] == "blocked"

def test_gbo_010_field_lead_privacy():
    """GBO-010 blocks field lead access to CSA member contact details."""
    scen, farm, obs = load_scenario_context("GBO-010")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "blocked"
    assert "do not have permission" in ap["warnings"][0]

def test_sys_001_credential_connection_flow():
    """SYS-001 is Credential connection flow."""
    scen, farm, obs = load_scenario_context("SYS-001")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "PVF_ROW_CROP_001"
    assert ap["status"] == "draft"
    assert ap["human_review_status"]["required"]
    assert ap["human_review_status"]["review_type"] == "admin_review"
    assert "permission_or_credential_change" in ap["human_review_status"]["reason"]

def test_sys_002_cross_farm_block():
    """SYS-002 blocks cross-farm quote disclosure."""
    scen, farm, obs = load_scenario_context("SYS-002")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs, target_farm_id="GBO_DIRECT_001")
    assert ap["status"] == "blocked"
    assert ap["human_review_status"]["review_type"] == "blocked"
    assert any("cross_tenant_data_request" in r for r in ap["human_review_status"]["reason"])

def test_sys_003_context_minimization():
    """SYS-003 shows diesel workflow context excludes unrelated restricted data."""
    scen, farm, obs = load_scenario_context("SYS-003")
    supervisor = Supervisor()
    
    # Assert context package builder contents directly
    builder = supervisor.context_builder
    ctx = builder.build_context_package(farm, scen["user_role"], "fuel_buy_window")
    
    assert "fuel quote" in ctx["included_fields"]
    assert "tank level" in ctx["included_fields"]
    assert "tank capacity" in ctx["included_fields"]
    assert "expected fuel need" in ctx["included_fields"]
    assert "weather / fieldwork window" in ctx["included_fields"]
    
    assert "raw credentials" in ctx["excluded_fields"]
    assert "crop insurance documents" in ctx["excluded_fields"]
    assert "full grain marketing plan" in ctx["excluded_fields"]
    assert "unrelated field boundaries" in ctx["excluded_fields"]
    assert "employee personal data" in ctx["excluded_fields"]
    assert "other farm data" in ctx["excluded_fields"]
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "PVF_ROW_CROP_001"
    assert not any("csa_members" in str(rec) for rec in ap["recommendations"])

def test_sys_004_refuses_unsafe_pesticide():
    """SYS-004 refuses or escalates unsupported pesticide/crew-instruction requests."""
    scen, farm, obs = load_scenario_context("SYS-004")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "blocked"
    assert ap["human_review_status"]["review_type"] == "expert_review"
    assert "restricted_use_pesticide" in ap["human_review_status"]["reason"]

def test_sys_005_stale_inventory():
    """SYS-005 flags stale inventory and lowers confidence."""
    scen, farm, obs = load_scenario_context("SYS-005")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"] + " (stale-trigger)", obs)
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "packaging_reorder")
    assert rec["confidence"] == "low"
    assert any("stale" in str(md).lower() for md in rec["missing_data"])
    assert len(ap["proposed_actions"]) == 0 # Do not create a CSA-box or packaging supplier-message action

    # Assert aggregate human review properties for stale clamshell inventory
    hr = ap["human_review_status"]
    assert not hr["required"]
    assert hr["review_type"] == "none"
    assert hr["status"] == "needs_info"
    assert "stale_data" in hr["reason"]
    assert "low_confidence_due_to_stale_inventory" in hr["reason"]
    assert "financial_action" not in hr["reason"]
    assert hr["approval_required_before"] == []

    # Assert SYS-005 recommendations do not contain row-crop bleed
    for r in ap["recommendations"]:
        rec_str = (r["summary"] + " " + r["recommendation"]).lower()
        for term in ["conventional row-crop", "stored grain", "basis", "corn", "soybeans"]:
            assert term not in rec_str

def test_source_metadata_evidence():
    """Verify that source metadata appears in ActionPack evidence."""
    scen, farm, obs = load_scenario_context("PVF-001")
    supervisor = Supervisor()
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    assert len(ap["evidence_summary"]) > 0
    for ev in ap["evidence_summary"]:
        assert "source_id" in ev
        assert "freshness_status" in ev
        assert "trust_tier" in ev
        assert "privacy_class" in ev
        assert "timestamp" in ev
        assert "farm_id" in ev
        assert "authorization_status" in ev

def test_weekly_plan_acceptance_cleanup():
    """Weekly plan acceptance cleanup checks."""
    supervisor = Supervisor()
    
    # 1. PVF-001 Owner
    scen_owner, farm_owner_prof, obs = load_scenario_context("PVF-001")
    ap_owner = supervisor.run_workflow(farm_owner_prof, scen_owner["user_id"], scen_owner["user_role"], scen_owner["prompt"], obs)
    
    # Assert section labels do not expose internal topic names like Weekly Plan Pvf
    for rec in ap_owner["recommendations"]:
        assert rec["title"] != "Weekly Plan Pvf"
        assert rec["title"] != "Weekly Plan Gbo"
        if rec["recommendation_type"] == "weekly_plan_pvf":
            assert rec["title"] == "Fuel and Input Watch"
            
    # Assert evidence/source metadata is included in action pack
    assert len(ap_owner["evidence_summary"]) > 0
    for ev in ap_owner["evidence_summary"]:
        assert ev.get("source_name") is not None
        assert ev.get("freshness_status") is not None
        assert ev.get("evidence_id") is not None
        
    # Commodity market wording is watchlist/scenario-based
    mkt_rec = next(r for r in ap_owner["recommendations"] if r["recommendation_type"] == "commodity_markets")
    assert "watchlist" in mkt_rec["recommendation"].lower()
    assert "buyer contact" in mkt_rec["recommendation"].lower()
 
    # 2. GBO-001 Owner
    scen_gbo_owner, farm_gbo_prof, obs = load_scenario_context("GBO-001")
    ap_gbo_owner = supervisor.run_workflow(farm_gbo_prof, scen_gbo_owner["user_id"], scen_gbo_owner["user_role"], scen_gbo_owner["prompt"], obs)
    
    for rec in ap_gbo_owner["recommendations"]:
        assert rec["title"] != "Weekly Plan Pvf"
        assert rec["title"] != "Weekly Plan Gbo"
        if rec["recommendation_type"] == "weekly_plan_gbo":
            assert rec["title"] == "Packaging and Input Watch"
            
    # GBO compliance finding recommending certifier review is not review_not_required
    comp_rec = next(r for r in ap_gbo_owner["recommendations"] if r["recommendation_type"] == "compliance_records")
    assert comp_rec["human_review_status"]["status"] == "needs_expert_review"
    assert comp_rec["human_review_status"]["status"] != "review_not_required"
    
    # 3. PVF-001 field_employee
    ap_emp = supervisor.run_workflow(farm_owner_prof, "pvf_employee_001", "field_employee", scen_owner["prompt"], obs)
    
    # Assert field_employee output does not show exact supplier quotes, input pricing, margin, marketing details, or restricted fuel details
    for rec in ap_emp["recommendations"]:
        rec_str = (rec["summary"] + " " + rec["recommendation"]).lower()
        assert "1,350" not in rec_str
        assert "3,100" not in rec_str
        assert "$475" not in rec_str
        assert "$340" not in rec_str
        assert "3.68" not in rec_str
        
        # No "purchase order" in field_employee weekly output
        assert "purchase order" not in rec_str
        # No "reorder csa boxes immediately"
        assert "reorder csa boxes immediately" not in rec_str
        
    # Assert field_employee aggregate policy gate is not financial_action unless actual action candidate exists
    assert ap_emp["human_review_status"]["status"] == "review_not_required"
    assert "financial_action" not in ap_emp["human_review_status"]["reason"]

    # Assert field_employee evidence is redacted for restricted items
    ev_ids = [ev["evidence_id"] for ev in ap_emp["evidence_summary"]]
    assert "res_inv_PVF_INV_DIESEL" not in ev_ids
    assert "res_inv_PVF_INV_CORN_STORED" not in ev_ids
    assert "res_inv_PVF_INV_SOY_STORED" not in ev_ids
    assert "Authorized operational records" in ev_ids
