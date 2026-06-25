# tests/test_crop_health_watchlist_connector.py
"""Unit and integration tests for CropHealthWatchlistConnector and shadow-mode capabilities."""
import os
import re
import pytest
import yaml
from unittest.mock import MagicMock

from harvestamp.connectors.crop_health_watchlist import CropHealthWatchlistConnector
from harvestamp.workflows.supervisor import Supervisor
from harvestamp.gateway.tools import ToolGateway
from harvestamp.auth.broker import CredentialBroker
from harvestamp.agents.specialists import ComplianceAgent
from harvestamp.agents.synthesizer import RecommendationSynthesizer
from harvestamp.extraction import DocumentExtractor

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

# 1. test_connector_offline_pvf
def test_connector_offline_pvf():
    """Verify CropHealthWatchlistConnector offline mock results for PVF."""
    connector = CropHealthWatchlistConnector()
    res = connector.fetch_watchlist(farm_id="PVF_ROW_CROP_001")
    assert res["status"] == "success"
    assert res["connector_mode"] == "offline_mock"
    assert res["fallback_used"] is False
    assert len(res["payload"]["watchlist"]) == 3
    
    # Confirm Tar Spot, Japanese Beetle, and Stink Bug are present
    issues = [item["issue_name"] for item in res["payload"]["watchlist"]]
    assert "Tar Spot" in issues
    assert "Japanese Beetle" in issues
    assert "Brown Marmorated Stink Bug" in issues

# 2. test_connector_offline_gbo
def test_connector_offline_gbo():
    """Verify CropHealthWatchlistConnector offline mock results for GBO."""
    connector = CropHealthWatchlistConnector()
    res = connector.fetch_watchlist(farm_id="GBO_DIRECT_001")
    assert res["status"] == "success"
    assert res["connector_mode"] == "offline_mock"
    assert len(res["payload"]["watchlist"]) == 1
    assert res["payload"]["watchlist"][0]["issue_name"] == "Late Blight"

# 3. test_connector_live_stub
def test_connector_live_stub(monkeypatch):
    """Verify live mode stub behaviour returns fallback_used=True when shadow live env var is set."""
    monkeypatch.setenv("HARVESTAMP_CROP_HEALTH_SHADOW_LIVE", "1")
    connector = CropHealthWatchlistConnector()
    res = connector.fetch_watchlist(farm_id="PVF_ROW_CROP_001")
    assert res["fallback_used"] is True
    assert res["fallback_reason"] == "live_mode_not_implemented"
    assert res["connector_mode"] == "live"
    assert res["status"] == "unavailable"

# 4. test_connector_empty_or_unknown
def test_connector_empty_or_unknown():
    """Verify unknown farm IDs return empty watchlist."""
    connector = CropHealthWatchlistConnector()
    res = connector.fetch_watchlist(farm_id="UNKNOWN_FARM")
    assert res["status"] == "success"
    assert res["payload"]["watchlist"] == []

# 5. test_tool_gateway_mediation
def test_tool_gateway_mediation():
    """Verify ToolGateway mediates access and logs to EvidenceBoard."""
    gateway = ToolGateway()
    broker = CredentialBroker()
    
    # Setup mock evidence board
    evidence_board = MagicMock()
    
    scen, farm, obs = load_scenario_context("IPM-001")
    grant = broker.request_capability_grant(farm, scen["user_id"], "crop_health_watchlist")
    
    res = gateway.get_crop_health_watchlist(
        capability_grant=grant,
        requesting_farm_id="PVF_ROW_CROP_001",
        target_farm_id="PVF_ROW_CROP_001",
        observations=obs,
        evidence_board=evidence_board
    )
    
    assert res["status"] == "success"
    assert "watchlist" in res["payload"]
    assert evidence_board.add_evidence.called

# 6. test_tool_gateway_unauthorized
def test_tool_gateway_unauthorized():
    """Verify ToolGateway raises PermissionError when capability grant is unauthorized."""
    gateway = ToolGateway()
    grant = {"authorized": False, "reason": "No access"}
    
    with pytest.raises(PermissionError) as exc:
        gateway.get_crop_health_watchlist(
            capability_grant=grant,
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
            observations={}
        )
    assert "Unauthorized tool access capability" in str(exc.value)

# 7. test_decoupling
def test_decoupling():
    """Verify no direct imports of CropHealthWatchlistConnector in agents or workflows."""
    agents_dir = os.path.abspath(os.path.join(FIXTURES_DIR, "..", "harvestamp", "agents"))
    workflows_dir = os.path.abspath(os.path.join(FIXTURES_DIR, "..", "harvestamp", "workflows"))
    
    pattern = "CropHealthWatchlistConnector"
    
    # Check agents
    for root, _, files in os.walk(agents_dir):
        for file in files:
            if file.endswith(".py"):
                content = open(os.path.join(root, file)).read()
                assert pattern not in content, f"Direct reference to {pattern} found in agent file {file}"
                
    # Check workflows
    for root, _, files in os.walk(workflows_dir):
        for file in files:
            if file.endswith(".py"):
                content = open(os.path.join(root, file)).read()
                assert pattern not in content, f"Direct reference to {pattern} found in workflow file {file}"

# 8. test_routing_crop_health
def test_routing_crop_health():
    """Verify intent routing keywords route to the crop_health_watchlist topic."""
    supervisor = Supervisor()
    farm = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")))
    
    prompts = [
        "scouting corn fields for tar spot",
        "crop health status for Midwest",
        "check the disease/pest watch list",
        "regulated/invasive pest awareness info",
        "spray/treatment safety-gate requests",
    ]
    
    for prompt in prompts:
        assert supervisor.route_intent(prompt, farm) == "crop_health_watchlist"

# 9. test_safety_aphis_alerts
def test_safety_aphis_alerts():
    """Verify APHIS alerts suggest documenting and regulatory channels only, no diagnose or transport."""
    scen, farm, obs = load_scenario_context("IPM-001")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    # Find compliance recommendation for crop_health_watchlist
    recs = [r for r in ap["recommendations"] if r["recommendation_type"] == "crop_health_watchlist"]
    assert len(recs) > 0
    
    aphis_rec = next(r for r in recs if "APHIS" in r["summary"])
    assert "document observations" in aphis_rec["recommendation"].lower()
    assert "official plant health" in aphis_rec["recommendation"].lower()
    
    # Assert prohibited patterns:
    rec_text = aphis_rec["recommendation"].lower()
    
    # Check that we do not instruct movement/shipment
    assert "diagnose" not in rec_text
    assert "ship sample" not in rec_text
    assert "send sample" not in rec_text
    assert "move sample" not in rec_text
    # We are allowed to say "do not move, transport, or ship suspected samples"
    assert "do not move, transport, or ship" in rec_text

# 10. test_safety_spray_refusal
def test_safety_spray_refusal():
    """Verify spray request refuses recommendations, does not draft act_spray_crew action."""
    scen, farm, obs = load_scenario_context("IPM-003") # "what should I spray?"
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    recs = [r for r in ap["recommendations"] if r["recommendation_type"] == "crop_health_watchlist"]
    assert len(recs) > 0
    
    # Find the regular watchlist recommendation
    spray_rec = next(r for r in recs if "Active threats" in r["summary"])
    rec_text = spray_rec["recommendation"].lower()
    
    # Check that it refuses naming specific products/rates
    assert "cannot recommend" in rec_text
    assert "scouting" in rec_text
    assert "crop advisor" in rec_text
    assert "extension" in rec_text
    
    # Prohibited patterns check (active recommendation patterns)
    prohibited_patterns = [
        r"apply\s+(?:pesticide|fungicide|insecticide|chemical|herbicide|product)",
        r"use\s+(?:pesticide|fungicide|insecticide|chemical|herbicide|product)",
        r"spray\s+(?:pesticide|fungicide|insecticide|chemical|herbicide|product)",
        r"recommend\s+(?:pesticide|fungicide|insecticide|chemical|herbicide|product)",
        r"at\s+a\s+rate\s+of",
        r"tank-mix\s+with",
        r"mix\s+with"
    ]
    for pattern in prohibited_patterns:
        assert not re.search(pattern, rec_text), f"Prohibited recommendation pattern matched: {pattern}"

    # Verify that the words pesticide/fungicide/insecticide CAN be used in refusal context
    # (Checking that the test doesn't merely assert absence of these words)
    assert any(w in rec_text for w in ["chemical", "pesticide", "product"])
    
    # Check that act_spray_crew is NOT drafted in proposed actions
    actions = ap["proposed_actions"]
    assert not any(act["action_id"].startswith("act_spray_crew") for act in actions)

# 11. test_organic_rules
def test_organic_rules():
    """Verify organic GBO alert includes organic certifications and OMRI guidance."""
    scen, farm, obs = load_scenario_context("IPM-005")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    recs = [r for r in ap["recommendations"] if r["recommendation_type"] == "crop_health_watchlist"]
    assert len(recs) > 0
    
    gbo_rec = recs[0]
    assert "organic" in gbo_rec["recommendation"].lower()
    assert "omri" in gbo_rec["recommendation"].lower()
    assert "certifier" in gbo_rec["recommendation"].lower()

# 12. test_unavailable_fallback
def test_unavailable_fallback():
    """Verify fallback behavior in IPM-004 when status is unavailable."""
    scen, farm, obs = load_scenario_context("IPM-004")
    supervisor = Supervisor()
    
    # IPM-004 sets crop_health_mock_status to unavailable
    obs["crop_health_mock_status"] = "unavailable"
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    recs = [r for r in ap["recommendations"] if r["recommendation_type"] == "crop_health_watchlist"]
    assert len(recs) > 0
    
    fallback_rec = recs[0]
    assert fallback_rec["confidence"] == "low"
    assert "unavailable" in fallback_rec["summary"].lower()
    assert "manually" in fallback_rec["recommendation"].lower()

# 13. test_regression_exclusions
def test_regression_exclusions():
    """Verify crop health watchlist is NOT requested or injected in PVF-002 or DOC-001 workflows."""
    supervisor = Supervisor()
    
    # PVF-002
    scen_pvf2, farm_pvf2, obs_pvf2 = load_scenario_context("PVF-002")
    ap_pvf2 = supervisor.run_workflow(
        farm_profile=farm_pvf2,
        user_id=scen_pvf2["user_id"],
        user_role=scen_pvf2["user_role"],
        prompt=scen_pvf2["prompt"],
        observations=obs_pvf2
    )
    
    # Check that crop health evidence is not in evidence summary
    for ev in ap_pvf2["evidence_summary"]:
        assert ev["source_id"] not in ["DS-016", "DS-017", "DS-018"]
        assert "crop_health" not in ev["evidence_id"]
        
    # Check that recommendations do not contain crop health
    for rec in ap_pvf2["recommendations"]:
        assert rec["recommendation_type"] != "crop_health_watchlist"
        assert "tar spot" not in rec["summary"].lower()
        
    # DOC-001 document extraction
    doc_res = DocumentExtractor().extract_file(
        os.path.join(FIXTURES_DIR, "documents", "doc_001_fuel_invoice.txt"),
        farm_id="PVF_ROW_CROP_001"
    ).to_dict()
    
    # Check that there is absolutely no crop health watchlist in extracted fields or notes
    assert "crop_health_watchlist" not in doc_res
    assert "watchlist" not in doc_res
    notes_str = " ".join(doc_res.get("notes", [])).lower()
    assert "tar spot" not in notes_str
    assert "beetle" not in notes_str
    assert "stink bug" not in notes_str


# 14. test_ipm_leakage_regression
def test_ipm_leakage_regression():
    """Verify that IPM outputs (IPM-001 through IPM-005) do not contain any forbidden spray planning/execution strings."""
    supervisor = Supervisor()
    
    forbidden_strings = [
        "Spray Window",
        "Spray Recordkeeping",
        "spraying West Ridge",
        "application rates",
        "weather compliance log",
        "Block crew assignment",
        "apply_to_field_plan",
        "schedule_crew_instruction"
    ]
    
    ipm_scenarios = ["IPM-001", "IPM-002", "IPM-003", "IPM-004", "IPM-005"]
    
    for scenario_id in ipm_scenarios:
        scen, farm, obs = load_scenario_context(scenario_id)
        
        # Simulate unavailable mock status for IPM-004
        if scenario_id == "IPM-004":
            obs = dict(obs)
            obs["crop_health_mock_status"] = "unavailable"
            
        ap = supervisor.run_workflow(
            farm_profile=farm,
            user_id=scen["user_id"],
            user_role=scen["user_role"],
            prompt=scen["prompt"],
            observations=obs
        )
        
        # Serialize ActionPack to string
        import json
        ap_str = json.dumps(ap)
        
        # Check all forbidden strings case-insensitively for maximum safety
        for forbidden in forbidden_strings:
            assert forbidden.lower() not in ap_str.lower(), f"Scenario {scenario_id} output contains forbidden string: '{forbidden}'"

