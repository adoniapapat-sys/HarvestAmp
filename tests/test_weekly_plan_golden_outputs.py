# tests/test_weekly_plan_golden_outputs.py
"""Golden output regression tests for weekly plans."""
import os
import pytest
import yaml

from harvestamp.workflows.supervisor import Supervisor

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def load_farm_and_obs(farm_id: str) -> tuple:
    farm_file = "prairie_view_farms.yaml" if farm_id == "PVF_ROW_CROP_001" else "green_basket_organics.yaml"
    farm_profile = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "farms", farm_file)))
    observations = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "data_observations.yaml")))
    return farm_profile, observations

def test_pvf_weekly_plan_golden_structure():
    """Verify PVF weekly plan has correct recommendations corresponding to Grand Plan expected content."""
    supervisor = Supervisor()
    farm, obs = load_farm_and_obs("PVF_ROW_CROP_001")
    ap = supervisor.run_workflow(
        farm_profile=farm,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs
    )
    
    titles = [r["title"] for r in ap["recommendations"]]
    
    # Verify presence of key sections/titles matching the PVF expected areas
    assert "Fieldwork Weather" in titles or "Weather / fieldwork windows" in titles or any("weather" in t.lower() for t in titles)
    assert "Fuel Watch" in titles or "Fuel and Input Watch" in titles or any("fuel" in t.lower() for t in titles)
    assert "Fertilizer / Input Quote Watch" in titles or "Fertilizer / seed watch" in titles or any("fertilizer" in t.lower() for t in titles)
    assert "Commodity Markets" in titles or "Market / stored grain context" in titles or any("market" in t.lower() for t in titles)
    assert "Compliance Records" in titles or "Compliance / records" in titles or any("compliance" in t.lower() for t in titles)

def test_gbo_weekly_plan_golden_structure():
    """Verify GBO weekly plan has correct recommendations corresponding to Grand Plan expected content."""
    supervisor = Supervisor()
    farm, obs = load_farm_and_obs("GBO_DIRECT_001")
    ap = supervisor.run_workflow(
        farm_profile=farm,
        user_id="gbo_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Green Basket Organics this week?",
        observations=obs
    )
    
    titles = [r["title"] for r in ap["recommendations"]]
    
    assert "Market Day Weather" in titles or "Weather / irrigation / high tunnel watch" in titles or any("weather" in t.lower() for t in titles)
    assert "Packaging and Input Watch" in titles or "Packaging inventory" in titles or any("packaging" in t.lower() for t in titles)
    assert "Compliance Records" in titles or "Organic records / input caution" in titles or any("compliance" in t.lower() or "organic" in t.lower() for t in titles)
    assert "Direct Market Sales" in titles or "Market / CSA plan" in titles or any("sales" in t.lower() or "market" in t.lower() for t in titles)
