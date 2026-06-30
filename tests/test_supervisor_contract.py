# tests/test_supervisor_contract.py
"""Contract tests for Supervisor routing and role boundaries."""
import os
import yaml
import json
import pytest
from harvestamp.workflows.supervisor import Supervisor
from harvestamp.core.contracts import (
    normalize_action_pack_contract,
    has_required_action_pack_fields,
    contains_forbidden_wording,
    RESTRICTED_FIELD_EMPLOYEE_TERMS
)

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))


def load_farm_profile(farm_id):
    """Loads the farm profile YAML fixture based on farm ID."""
    filename = "prairie_view_farms.yaml" if "PVF" in farm else "green_basket_organics.yaml"
    path = os.path.join(FIXTURES_DIR, "farms", filename)
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_observations():
    """Loads the data observations YAML fixture."""
    path = os.path.join(FIXTURES_DIR, "data_observations.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


# Set up basic parameters for test loading
farm = "PVF_ROW_CROP_001"
gbo_farm_id = "GBO_DIRECT_001"


def test_supervisor_weekly_plan_owner_actionpack_has_contract_shape():
    farm_profile = load_farm_profile(farm)
    obs = load_observations()
    
    supervisor = Supervisor()
    output = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    
    assert output["status"] != "blocked"
    normalized = normalize_action_pack_contract(output)
    assert has_required_action_pack_fields(normalized) is True
    
    assert isinstance(normalized["recommendations"], list)
    assert len(normalized["recommendations"]) > 0
    assert isinstance(normalized["evidence_summary"], list)
    assert len(normalized["evidence_summary"]) > 0
    assert isinstance(normalized["proposed_actions"], list)
    assert isinstance(normalized["warnings"], list)
    assert isinstance(normalized["missing_data"], list)
    assert isinstance(normalized["human_review_status"], dict)
    
    serialized = json.dumps(output, sort_keys=True)
    assert contains_forbidden_wording(serialized) == []


def test_supervisor_weekly_plan_owner_routes_to_expected_lanes():
    farm_profile = load_farm_profile(farm)
    obs = load_observations()
    
    supervisor = Supervisor()
    output = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    
    recs = output["recommendations"]
    titles = [r["title"].lower() for r in recs]
    summaries = " ".join([r["summary"].lower() for r in recs])
    
    # Verify expected lanes semantically
    # 1. Weather / Fieldwork
    assert any("weather" in t or "fieldwork" in t or "irrigation" in t or "weather" in summaries for t in titles)
    # 2. Procurement / Fuel / Input
    assert any("fuel" in t or "input" in t or "procurement" in t or "diesel" in summaries or "urea" in summaries for t in titles)
    # 3. Records / Inventory / Bin / Yield
    assert any("records" in t or "inventory" in t or "bin" in t or "yield" in t or "bin" in summaries or "yield" in summaries for t in titles)
    # 4. Market / Sales / Stored grain watch
    assert any("market" in t or "sales" in t or "grain" in t or "watch" in summaries or "grain watch" in summaries for t in titles)
    # 5. Compliance / Production-record caution
    assert any("compliance" in t or "compliance" in summaries or "caution" in summaries for t in titles)


def test_supervisor_field_employee_has_no_proposed_actions_or_restricted_terms_pvf():
    farm_profile = load_farm_profile(farm)
    obs = load_observations()
    
    supervisor = Supervisor()
    output = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id="pvf_employee_001",
        user_role="field_employee",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    
    assert output["proposed_actions"] == []
    for r in output["recommendations"]:
        assert r["proposed_actions"] == []
        
    serialized = json.dumps(output, sort_keys=True).lower()
    for term in RESTRICTED_FIELD_EMPLOYEE_TERMS:
        assert term not in serialized
        
    # Exclude raw restricted evidence IDs such as res_inv_PVF_INV_DIESEL (should be masked to Authorized operational records)
    assert "res_inv_pvf_inv_diesel" not in serialized
    assert "authorized operational records" in serialized
    
    assert contains_forbidden_wording(serialized) == []


def test_supervisor_field_employee_has_no_proposed_actions_or_restricted_terms_gbo():
    farm_profile = load_farm_profile(gbo_farm_id)
    obs = load_observations()
    
    supervisor = Supervisor()
    output = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id="gbo_employee_001",
        user_role="field_employee",
        prompt="What should I know about Green Basket Organics this week?",
        observations=obs
    )
    
    assert output["proposed_actions"] == []
    for r in output["recommendations"]:
        assert r["proposed_actions"] == []
        
    serialized = json.dumps(output, sort_keys=True).lower()
    for term in RESTRICTED_FIELD_EMPLOYEE_TERMS:
        assert term not in serialized
        
    assert contains_forbidden_wording(serialized) == []


def test_supervisor_blocks_cross_farm_access():
    farm_profile = load_farm_profile(farm)
    obs = load_observations()
    
    supervisor = Supervisor()
    output = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="Show me Green Basket Organics records.",
        observations=obs,
        target_farm_id=gbo_farm_id
    )
    
    assert output["status"] == "blocked"
    assert output["proposed_actions"] == []
    assert len(output["recommendations"]) == 0
    
    serialized = json.dumps(output, sort_keys=True)
    assert gbo_farm_id not in serialized
    assert contains_forbidden_wording(serialized) == []


def test_supervisor_and_agents_do_not_import_connector_classes_directly():
    base_dirs = ["harvestamp/agents", "harvestamp/workflows"]
    connectors = [
        "NWSWeatherConnector",
        "EIAFuelBenchmarkConnector",
        "NASSQuickStatsConnector",
        "AMSMarketNewsConnector",
        "CropHealthWatchlistConnector"
    ]
    
    for base_dir in base_dirs:
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r") as f:
                        content = f.read()
                        
                        # Remove comments to avoid false positives
                        clean_lines = []
                        for line in content.splitlines():
                            if not line.strip().startswith("#"):
                                clean_lines.append(line)
                        clean_content = "\n".join(clean_lines)
                        
                        for connector in connectors:
                            assert connector not in clean_content, f"Direct connector usage found in {path}: {connector}"


def test_toolgateway_is_mediation_layer_for_connectors():
    supervisor_path = "harvestamp/workflows/supervisor.py"
    connectors = [
        "NWSWeatherConnector",
        "EIAFuelBenchmarkConnector",
        "NASSQuickStatsConnector",
        "AMSMarketNewsConnector",
        "CropHealthWatchlistConnector"
    ]
    
    # Assert ToolGateway is referenced
    with open(supervisor_path, "r") as f:
        supervisor_content = f.read()
        assert "ToolGateway" in supervisor_content
        
        # Verify no direct connector class names in supervisor.py
        for connector in connectors:
            assert connector not in supervisor_content
            
    # Verify no direct connector class names in specialist files
    for root, _, files in os.walk("harvestamp/agents"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    content = f.read()
                    for connector in connectors:
                        assert connector not in content, f"Connector {connector} referenced in agent file {path}"


def test_public_context_not_sole_source_for_proposed_actions():
    farm_profile = load_farm_profile(farm)
    obs = load_observations()
    
    supervisor = Supervisor()
    output = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    
    public_evidence_ids = {
        "res_weather_nws_PVF_ROW_CROP_001",
        "res_benchmark_eia_PVF_ROW_CROP_001",
        "res_benchmark_nass_PVF_ROW_CROP_001",
        "res_crop_health_PVF_ROW_CROP_001"
    }
    
    proposed = output["proposed_actions"]
    for act in proposed:
        assert act["evidence_ids"] != []
        
        # Check that it's not solely anchored on public context
        assert not all(e in public_evidence_ids for e in act["evidence_ids"])
        
        payload = act.get("payload", {})
        source_ev = payload.get("source_evidence_id")
        assert source_ev not in public_evidence_ids
        
        related = payload.get("related_evidence", [])
        if any(r in public_evidence_ids for r in related):
            # If public context is in related evidence, it should not be the sole evidence
            non_public = [r for r in related if r not in public_evidence_ids]
            assert len(non_public) >= 1


def test_narrow_document_or_specific_topic_does_not_overroute_unrelated_lanes():
    farm_profile = load_farm_profile(farm)
    obs = load_observations()
    
    supervisor = Supervisor()
    output = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="Review this fertilizer quote.",
        observations=obs
    )
    
    # Assert it is focused on procurement / fertilizer
    recs = output["recommendations"]
    titles = [r["title"].lower() for r in recs]
    
    # Weather and crop health recommendations should not be present
    assert not any("weather" in t or "crop health" in t for t in titles)
    
    # Proposed actions should only relate to procurement/fuel/fertilizer/quotes
    for act in output["proposed_actions"]:
        assert act["action_type"] in ["supplier_message", "draft_inventory_reconciliation"]
