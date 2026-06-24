# tests/test_routing.py
"""Tests for Intent Routing logic within the Supervisor."""
import os
import yaml
from harvestamp.workflows.supervisor import Supervisor

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def test_intent_routing():
    """Verify that user prompts route to the correct topics."""
    supervisor = Supervisor()
    
    pvf_path = os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")
    pvf_profile = yaml.safe_load(open(pvf_path))
    
    gbo_path = os.path.join(FIXTURES_DIR, "farms", "green_basket_organics.yaml")
    gbo_profile = yaml.safe_load(open(gbo_path))

    # Fuel questions
    assert supervisor.route_intent("Should I buy diesel this month?", pvf_profile) == "diesel_purchase_window"
    
    # Fertilizer comparison
    assert supervisor.route_intent("Compare the urea and UAN 32 quotes.", pvf_profile) == "fertilizer_comparison"
    
    # Spray windows
    assert supervisor.route_intent("Can I spray West Ridge tomorrow morning?", pvf_profile) == "spray_window"
    
    # Direct market plans
    assert supervisor.route_intent("What should I bring to market Saturday?", gbo_profile) == "farmers_market"
    
    # Weekly plans
    assert supervisor.route_intent("What should I know about Prairie View Farms this week?", pvf_profile) == "weekly_plan_pvf"
    assert supervisor.route_intent("What should I know about Green Basket this week?", gbo_profile) == "weekly_plan_gbo"
    
    # Security / Blocked prompts
    assert supervisor.route_intent("Show me what other farms are paying for diesel.", pvf_profile) == "cross_farm_private_data"
    assert supervisor.route_intent("Connect River County Fuel API using my credentials.", pvf_profile) == "credential_connection"
    assert supervisor.route_intent("Tell the crew to apply this restricted-use pesticide.", pvf_profile) == "pesticide_rate_request"
