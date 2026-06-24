# scripts/run_scenario.py
"""Scenario runner script for HarvestAmp MVP.

Loads and runs a specific scenario by its ID, printing findings and action packs.
"""
import os
import sys
import argparse
from typing import Any
import yaml

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from harvestamp.workflows.supervisor import Supervisor
from harvestamp.audit.logger import AuditLogger
from harvestamp.agents.action_agent import ActionAgent

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def load_yaml(path: str) -> Any:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def find_scenario(scenarios: list, scenario_id: str) -> dict:
    for s in scenarios:
        if s.get("scenario_id") == scenario_id:
            return s
    return None

def main():
    parser = argparse.ArgumentParser(description="Run HarvestAmp MVP scenario runner.")
    parser.add_argument("scenario_id", help="Scenario ID to run (e.g. PVF-001, GBO-004, SYS-002)")
    parser.add_argument("--action-id", help="Optional Action ID from the ActionPack to execute", default=None)
    parser.add_argument("--approve", action="store_true", help="Simulate approving the action pack before executing action")
    args = parser.parse_args()

    scenarios_path = os.path.join(FIXTURES_DIR, "scenarios.yaml")
    observations_path = os.path.join(FIXTURES_DIR, "data_observations.yaml")
    
    if not os.path.exists(scenarios_path) or not os.path.exists(observations_path):
        print("Error: Scenarios or data observations fixtures missing.")
        sys.exit(1)

    scenarios = load_yaml(scenarios_path)
    observations = load_yaml(observations_path)
    
    scenario = find_scenario(scenarios, args.scenario_id)
    if not scenario:
        print(f"Error: Scenario '{args.scenario_id}' not found.")
        print("Available scenarios:")
        for s in scenarios:
            print(f"  - {s['scenario_id']}: {s['name']}")
        sys.exit(1)

    print("=" * 80)
    print(f"RUNNING SCENARIO: {scenario['scenario_id']} - {scenario['name']}")
    print(f"Farm Profile:    {scenario['farm_profile']}")
    print(f"User / Role:     {scenario.get('user_id', 'unknown')} ({scenario['user_role']})")
    print(f"Prompt:          \"{scenario['prompt']}\"")
    print("=" * 80)

    # Load appropriate farm profile
    farm_file = "prairie_view_farms.yaml" if "PVF" in scenario["farm_profile"] or "multi_tenant" in scenario["farm_profile"] else "green_basket_organics.yaml"
    farm_profile = load_yaml(os.path.join(FIXTURES_DIR, "farms", farm_file))

    # Initialize components
    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)
    
    # Check if this is a cross-farm target check (for SYS-002)
    target_farm_id = None
    if scenario["scenario_id"] == "SYS-002":
        # Target a different farm to test leakage block
        target_farm_id = "GBO_DIRECT_001"
        
    prompt_str = scenario["prompt"]
    # Handle stale count trigger simulation
    if scenario["scenario_id"] == "SYS-005":
        prompt_str = scenario["prompt"] + " (stale-trigger)"

    # Run supervisor coordination workflow
    action_pack = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id=scenario.get("user_id", "user_001"),
        user_role=scenario["user_role"],
        prompt=prompt_str,
        observations=observations,
        target_farm_id=target_farm_id
    )

    # Print results
    print("\n[ACTION PACK RESULTS]")
    print(f"Action Pack ID: {action_pack['action_pack_id']}")
    print(f"Overall Status: {action_pack['status']}")

    if scenario["scenario_id"] == "SYS-003":
        topic = scenario.get("topic") or scenario.get("workflow") or scenario.get("expected_topic")
        if not topic:
            topic = supervisor.route_intent(prompt_str, farm_profile)
        ctx_pkg = supervisor.context_builder.build_context_package(farm_profile, scenario["user_role"], topic)
        print("\n--- TASK-SCOPED CONTEXT MINIMIZATION (SYS-003) ---")
        print(f"Included Context Fields: {ctx_pkg['included_fields']}")
        print(f"Excluded Context Fields: {ctx_pkg['excluded_fields']}")
    
    print("\n--- RECOMMENDATIONS ---")
    if not action_pack["recommendations"]:
        print("None or Blocked.")
    for rec in action_pack["recommendations"]:
        print(f"* Title: {rec['title']} (Urgency: {rec['urgency']}, Confidence: {rec['confidence']})")
        print(f"  Summary:        {rec['summary']}")
        print(f"  Recommendation: {rec['recommendation']}")
        print(f"  Human Review:   {rec['human_review_status']['status']} (Reason: {rec['human_review_status']['reason']})")
        print()

    print("--- PROPOSED ACTIONS ---")
    if not action_pack["proposed_actions"]:
        print("None.")
    for action in action_pack["proposed_actions"]:
        print(f"* ID:   {action['action_id']}")
        print(f"  Type: {action['action_type']}")
        print(f"  Payload: {action['payload']}")
        print()

    print("--- EVIDENCE USED ---")
    if not action_pack["evidence_summary"]:
        print("None.")
    for ev in action_pack["evidence_summary"]:
        print(f"- {ev['evidence_id']} from {ev['source_name']} (Trust: {ev['trust_tier']}, Freshness: {ev['freshness_status']})")

    print("\n--- WARNINGS & MISSING DATA ---")
    for w in action_pack["warnings"]:
        print(f"WARNING: {w}")
    if action_pack["missing_data"]:
        print(f"Missing Data Identified: {action_pack['missing_data']}")

    print("\n--- HUMAN REVIEW STATUS ---")
    hr = action_pack["human_review_status"]
    print(f"Review Required:        {hr['required']}")
    print(f"Review Type:           {hr['review_type']}")
    print(f"Risk Tier:             {hr['risk_tier']}")
    print(f"Status:                {hr['status']}")
    print(f"Reasons:               {hr['reason']}")
    print(f"Recommended Reviewer:  {hr['recommended_reviewer']}")
    print(f"Approval Blockers:     {hr['approval_required_before']}")

    # Check if action execution is requested
    if args.action_id:
        print("\n" + "=" * 40)
        print(f"EXECUTING ACTION: {args.action_id}")
        print("=" * 40)
        
        # Find action
        target_action = None
        for act in action_pack["proposed_actions"]:
            if act["action_id"] == args.action_id:
                target_action = act
                break
                
        if not target_action:
            print(f"Error: Proposed action '{args.action_id}' not found in ActionPack.")
            sys.exit(1)
            
        action_agent = ActionAgent(audit_logger=logger)
        
        # If user passed --approve, simulate state update to 'approved'
        hr_status = hr.copy()
        if args.approve:
            hr_status["status"] = "approved"
            print("User simulation: Gating review APPROVED.")
        else:
            print(f"Executing without approval (Current review status: '{hr_status['status']}')")
            
        try:
            success, msg = action_agent.execute_action(
                target_action,
                hr_status,
                user_has_permission=True
            )
            print(f"SUCCESS: {msg}")
        except PermissionError as e:
            print(f"BLOCKED BY ACTION GATE: {e}")

    # Print Audit logs
    print("\n--- SECURITY AUDIT LOGS ---")
    for evt in logger.list_events():
        print(f"[{evt['timestamp']}] User {evt['user_id']} | Action: {evt['action']} | Result: {evt['result']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
