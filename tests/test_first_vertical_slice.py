# tests/test_first_vertical_slice.py
"""Regression tests for the first vertical-slice mock agent workflow."""
import os
import json
import pytest
import yaml

from harvestamp.workflows.supervisor import Supervisor
from harvestamp.agents import (
    WeatherFieldworkAgent,
    ProcurementAgent,
    RecordsInventoryAgent,
    MarketSalesAgent,
    ComplianceAgent,
    MarginScenarioAgent
)

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def load_farm_and_obs(farm_id: str) -> tuple:
    farm_file = "prairie_view_farms.yaml" if farm_id == "PVF_ROW_CROP_001" else "green_basket_organics.yaml"
    farm_profile = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", farm_file)))
    observations = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    return farm_profile, observations

def test_workflow_routing_and_findings():
    """Verify that weekly plan routes through the explicit mock specialist agents and returns valid findings."""
    supervisor = Supervisor()
    farm, obs = load_farm_and_obs("PVF_ROW_CROP_001")
    
    # Verify the instantiated agent classes are correct
    assert isinstance(supervisor.weather_agent, WeatherFieldworkAgent)
    assert isinstance(supervisor.proc_agent, ProcurementAgent)
    assert isinstance(supervisor.records_agent, RecordsInventoryAgent)
    assert isinstance(supervisor.market_agent, MarketSalesAgent)
    assert isinstance(supervisor.compliance_agent, ComplianceAgent)
    assert isinstance(supervisor.margin_agent, MarginScenarioAgent)

    ap = supervisor.run_workflow(
        farm_profile=farm,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )

    # 1. ActionPack contains recommendations, proposed actions, evidence summary, assumptions, missing data, confidence, human review
    assert "recommendations" in ap
    assert "proposed_actions" in ap
    assert "evidence_summary" in ap
    assert "missing_data" in ap
    assert "human_review_status" in ap
    
    # 2. Assert mock agents return AgentFinding-shaped objects (checked via recommendation structure)
    for rec in ap["recommendations"]:
        assert "recommendation_id" in rec
        assert "title" in rec
        assert "summary" in rec
        assert "recommendation" in rec
        assert "confidence" in rec
        assert "urgency" in rec
        assert "human_review_status" in rec

def test_pvf_row_crop_specificity():
    """Verify that PVF weekly plan contains row-crop specific topics and no GBO direct-market details."""
    supervisor = Supervisor()
    farm, obs = load_farm_and_obs("PVF_ROW_CROP_001")
    ap = supervisor.run_workflow(
        farm_profile=farm,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    ap_str = json.dumps(ap).lower()
    
    # PVF Specifics
    assert "corn" in ap_str or "soybean" in ap_str
    assert "diesel" in ap_str
    assert "urea" in ap_str or "uan 32" in ap_str
    
    # No GBO Specifics
    assert "csa box" not in ap_str
    assert "clamshell" not in ap_str

def test_gbo_organic_specificity():
    """Verify that GBO weekly plan contains organic and direct-market specific topics."""
    supervisor = Supervisor()
    farm, obs = load_farm_and_obs("GBO_DIRECT_001")
    ap = supervisor.run_workflow(
        farm_profile=farm,
        user_id="gbo_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Green Basket Organics this week?",
        observations=obs
    )
    ap_str = json.dumps(ap).lower()
    
    # GBO Specifics
    assert "csa" in ap_str
    assert "clamshell" in ap_str
    assert "organic" in ap_str
    
    # No PVF Specifics
    assert "urea" not in ap_str
    assert "uan 32" not in ap_str

def test_field_employee_role_restriction():
    """Verify that field employee output is restricted and supplier pricing / financials are hidden."""
    supervisor = Supervisor()
    farm, obs = load_farm_and_obs("PVF_ROW_CROP_001")
    ap = supervisor.run_workflow(
        farm_profile=farm,
        user_id="pvf_employee_001",
        user_role="field_employee",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    ap_str = json.dumps(ap).lower()
    
    # Hidden pricing warning
    assert "supplier quotes, input pricing, margin, and marketing details are hidden for your role" in ap_str
    # Verify no quote prices (e.g. $475 or $340) are in the recommendations
    for rec in ap["recommendations"]:
        rec_text = (rec["summary"] + " " + rec["recommendation"]).lower()
        assert "$475" not in rec_text
        assert "$340" not in rec_text

def test_action_gating_and_privacy():
    """Verify that external actions require approval, no credentials appear, and no cross-farm data leaks."""
    supervisor = Supervisor()
    farm, obs = load_farm_and_obs("PVF_ROW_CROP_001")
    ap = supervisor.run_workflow(
        farm_profile=farm,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    
    # Proposed actions should require approval
    for act in ap["proposed_actions"]:
        assert act["human_review_status"]["required"] is True
        assert act["human_review_status"]["status"] in ["needs_user_approval", "needs_expert_review"]
        
    ap_str = json.dumps(ap).lower()
    # No raw passwords/credentials
    assert "password" not in ap_str
    assert "secret_key" not in ap_str
    assert "waterpass" not in ap_str
    
    # No cross-farm leaks
    assert "green basket" not in ap_str
    assert "gbo" not in ap_str
