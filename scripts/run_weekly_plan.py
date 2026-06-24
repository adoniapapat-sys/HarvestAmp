# scripts/run_weekly_plan.py
"""Weekly Farm Plan runner for HarvestAmp MVP.

Runs the weekly planning workflow for a specified farm and user role.
"""
import os
import sys
import argparse
import yaml

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from harvestamp.workflows.supervisor import Supervisor
from harvestamp.audit.logger import AuditLogger

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def main():
    parser = argparse.ArgumentParser(description="Run HarvestAmp Weekly Farm Plan.")
    parser.add_argument("--farm", choices=["PVF_ROW_CROP_001", "GBO_DIRECT_001"], default="PVF_ROW_CROP_001", help="Farm profile ID")
    parser.add_argument("--role", choices=["farm_owner", "farm_manager", "field_employee", "field_lead"], default="farm_owner", help="User role to simulate")
    args = parser.parse_args()

    farm_file = "prairie_view_farms.yaml" if args.farm == "PVF_ROW_CROP_001" else "green_basket_organics.yaml"
    farm_path = os.path.join(FIXTURES_DIR, "farms", farm_file)
    observations_path = os.path.join(FIXTURES_DIR, "data_observations.yaml")

    if not os.path.exists(farm_path) or not os.path.exists(observations_path):
        print("Error: Missing fixture files.")
        sys.exit(1)

    farm_profile = yaml.safe_load(open(farm_path))
    observations = yaml.safe_load(open(observations_path))

    # Match user_id based on role
    user_id = "user_001"
    for user in farm_profile.get("users", []):
        if user.get("role") == args.role:
            user_id = user.get("user_id")
            break

    prompt = f"What should I know about {farm_profile['farm_name']} this week?"

    print("=" * 80)
    print(f"WEEKLY FARM PLAN RUNNER - HARVESTAMP")
    print(f"Farm:            {farm_profile['farm_name']} ({args.farm})")
    print(f"Simulating Role: {args.role} (User ID: {user_id})")
    print(f"Prompt:          \"{prompt}\"")
    print("=" * 80)

    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)

    action_pack = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id=user_id,
        user_role=args.role,
        prompt=prompt,
        observations=observations
    )

    print(f"\n[WEEKLY PLAN ACTION PACK - {action_pack['status'].upper()}]")
    print(f"Action Pack ID: {action_pack['action_pack_id']}")
    
    print("\n--- RECOMMENDATIONS ---")
    if not action_pack["recommendations"]:
        print("None or Blocked due to role restrictions.")
    for rec in action_pack["recommendations"]:
        print(f"* SECTION: {rec['title']}")
        print(f"  Summary:        {rec['summary']}")
        print(f"  Recommendation: {rec['recommendation']}")
        print(f"  Review Status:  {rec['human_review_status']['status']} (Risk Tier: {rec['human_review_status']['risk_tier']})")
        print()

    print("--- DRAFT ACTIONS REQUIRING APPROVAL ---")
    if not action_pack["proposed_actions"]:
        print("None.")
    for action in action_pack["proposed_actions"]:
        print(f"- Type: {action['action_type']} | ID: {action['action_id']}")
        print(f"  Draft Payload: {action['payload']}")
        
    print("\n--- WARNINGS & MISSING DATA ---")
    for w in action_pack["warnings"]:
        print(f"WARNING: {w}")
    if action_pack["missing_data"]:
        print(f"Missing fields: {action_pack['missing_data']}")

    print("\n--- EVIDENCE USED ---")
    if not action_pack.get("evidence_summary"):
        print("None.")
    for ev in action_pack.get("evidence_summary", []):
        source_name = ev.get("source_name") or ev.get("source_id") or "Unknown"
        freshness = ev.get("freshness_status") or "unknown"
        ev_id = ev.get("evidence_id") or "N/A"
        print(f"- Source: {source_name} | Freshness: {freshness} | Evidence ID: {ev_id}")

    print("\n--- AGGREGATE POLICY GATES ---")
    hr = action_pack["human_review_status"]
    print(f"Review Required:        {hr['required']}")
    print(f"Review Type:           {hr['review_type']}")
    print(f"Status:                {hr['status']}")
    print(f"Reasons triggered:     {hr['reason']}")

    print("\n--- LOGGED AUDIT EVENTS ---")
    for evt in logger.list_events():
        print(f"[{evt['timestamp']}] Action: {evt['action']} | Result: {evt['result']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
