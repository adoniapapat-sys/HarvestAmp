# tests/test_source_metadata.py
"""Tests for source metadata presence in findings and ActionPacks."""
import os
import yaml
from harvestamp.workflows.supervisor import Supervisor

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def test_source_metadata_present_in_action_pack():
    """Verify that ActionPack contains full source metadata for all evidence."""
    scenarios = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "scenarios.yaml")))
    observations = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    
    # Load PVF-002 scenario
    scen = next(s for s in scenarios if s["scenario_id"] == "PVF-002")
    farm_profile = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")))
    
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id=scen["user_id"],
        user_role=scen["user_role"],
        prompt=scen["prompt"],
        observations=observations
    )
    
    # ActionPack must have evidence summary
    assert len(ap["evidence_summary"]) > 0
    
    for ev in ap["evidence_summary"]:
        # Every evidence item must contain: source_id, source_name, trust_tier, freshness_status, privacy_class
        assert "source_id" in ev and ev["source_id"] is not None
        assert "source_name" in ev and ev["source_name"] is not None
        assert "trust_tier" in ev and ev["trust_tier"] is not None
        assert "freshness_status" in ev and ev["freshness_status"] is not None
        assert "privacy_class" in ev and ev["privacy_class"] is not None

    # Recommendations must contain evidence references
    for rec in ap["recommendations"]:
        if rec["recommendation_type"] in ["fuel_buy_window", "fertilizer_comparison", "packaging_reorder", "fieldwork_weather", "market_day_weather"]:
            assert len(rec["evidence_ids"]) > 0
