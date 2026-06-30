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
    
    recs = action_pack.get("recommendations", [])
    
    def find_rec_by_title(title_query):
        for r in recs:
            if title_query.lower() in r["title"].lower():
                return r
        return None

    def print_section(section_name, content_summary, content_rec=None, hr_status=None):
        print(f"=== {section_name.upper()} ===")
        if content_summary:
            print(f"  Summary:        {content_summary}")
        if content_rec:
            print(f"  Recommendation: {content_rec}")
        if hr_status:
            print(f"  Review Status:  {hr_status.get('status')} (Risk Tier: {hr_status.get('risk_tier')})")
        print()

    if args.farm == "PVF_ROW_CROP_001":
        # PVF Expected Sections
        # 1. Executive summary
        if args.role == "field_employee":
            print_section("Executive summary", "Weekly field employee plan. Focus on fieldwork safety and task execution.")
            print_section("Today", "Review fieldwork safety boundaries and prepare PPE.")
            print_section("This week", "Target Friday as the primary fieldwork window.")
        else:
            print_section("Executive summary", "Prairie View Farms Weekly Action Plan. Weather is favorable for Friday fieldwork. Low fuel watch is active. Fertilizer quotes are ready but missing fees.")
            print_section("Today", "Review urea vs UAN 32 quotes. Reconcile field spray records.")
            print_section("This week", "Perform fieldwork on Friday. Verify crop-protection stocks. Schedule stored grain reconciliation watch.")

        # 2. Weather / fieldwork windows
        r = find_rec_by_title("Fieldwork Weather") or find_rec_by_title("Weather")
        if r:
            print_section("Weather / fieldwork windows", r["summary"], r["recommendation"], r["human_review_status"])
        else:
            print_section("Weather / fieldwork windows", "N/A or Hidden")

        # 3. Fuel and input watch
        r = find_rec_by_title("Fuel Watch")
        if r:
            print_section("Fuel and input watch", r["summary"], r["recommendation"], r["human_review_status"])
        else:
            print_section("Fuel and input watch", "N/A or Hidden")

        # 4. Fertilizer / seed watch
        r = find_rec_by_title("Fertilizer")
        if r:
            print_section("Fertilizer / seed watch", r["summary"], r["recommendation"], r["human_review_status"])
        else:
            print_section("Fertilizer / seed watch", "N/A or Hidden")

        # 5. Market / stored grain context
        r = find_rec_by_title("Commodity Markets") or find_rec_by_title("Markets")
        if r:
            print_section("Market / stored grain context", r["summary"], r["recommendation"], r["human_review_status"])
        else:
            print_section("Market / stored grain context", "N/A or Hidden")

        # 6. Compliance / records
        r_inv = find_rec_by_title("Inventory Records")
        r_comp = find_rec_by_title("Compliance Records")
        comp_summary = ""
        comp_rec = ""
        hr_stat = None
        if r_inv:
            comp_summary += r_inv["summary"] + " "
            comp_rec += r_inv["recommendation"] + " "
            hr_stat = r_inv["human_review_status"]
        if r_comp:
            comp_summary += r_comp["summary"]
            comp_rec += r_comp["recommendation"]
            hr_stat = r_comp["human_review_status"]
        if comp_summary:
            print_section("Compliance / records", comp_summary.strip(), comp_rec.strip(), hr_stat)
        else:
            print_section("Compliance / records", "N/A or Hidden")

    else:
        # GBO Expected Sections
        # 1. Executive summary
        if args.role == "field_employee":
            print_section("Executive summary", "Green Basket Organics Weekly Direct-Market Plan. High tunnel check is recommended for Saturday weather. Late blight watchlist is active.")
            print_section("Today", "Prepare Saturday market setup materials including tent weights.")
            print_section("This week", "Coordinate Tuesday restaurant delivery harvest and Thursday CSA packaging.")
        else:
            print_section("Executive summary", "Green Basket Organics Weekly Direct-Market Plan. High tunnel check is recommended for Saturday weather. CSA box reorder is drafted. Late blight watchlist is active.")
            print_section("Today", "Prepare Saturday market setup materials including tent weights. Submit OSP verification request.")
            print_section("This week", "Coordinate Tuesday restaurant delivery harvest and Thursday CSA packaging. Update organic documentation.")

        # 2. Market / CSA plan
        r = find_rec_by_title("Direct Market Sales") or find_rec_by_title("Sales")
        if r:
            print_section("Market / CSA plan", r["summary"], r["recommendation"], r["human_review_status"])
        else:
            print_section("Market / CSA plan", "N/A or Hidden")

        # 3. Harvest and wash-pack priorities
        r_inv = find_rec_by_title("Inventory Records")
        if r_inv:
            print_section("Harvest and wash-pack priorities", r_inv["summary"], "Coordinate harvest and wash-pack priorities to align with Tuesday restaurant deliveries and Thursday CSA pickup.", r_inv["human_review_status"])
        else:
            print_section("Harvest and wash-pack priorities", "N/A or Hidden")

        # 4. Packaging inventory
        r_pack = find_rec_by_title("Packaging") or find_rec_by_title("Packaging and Input Watch")
        if r_pack:
            print_section("Packaging inventory", r_pack["summary"], r_pack["recommendation"], r_pack["human_review_status"])
        else:
            print_section("Packaging inventory", "N/A or Hidden")

        # 5. Weather / irrigation / high tunnel watch
        r_wtr = find_rec_by_title("Market Day Weather") or find_rec_by_title("Weather")
        if r_wtr:
            print_section("Weather / irrigation / high tunnel watch", r_wtr["summary"], r_wtr["recommendation"], r_wtr["human_review_status"])
        else:
            print_section("Weather / irrigation / high tunnel watch", "N/A or Hidden")

        # 6. Organic records / input caution
        r_comp = find_rec_by_title("Compliance Records")
        if r_comp:
            print_section("Organic records / input caution", r_comp["summary"], r_comp["recommendation"], r_comp["human_review_status"])
        else:
            print_section("Organic records / input caution", "N/A or Hidden")

    # 7. Missing data
    print_section("Missing data", ", ".join(action_pack["missing_data"]) if action_pack["missing_data"] else "None")

    # 8. Needs approval / gates
    hr = action_pack["human_review_status"]
    print_section("Needs approval", f"Review Required: {hr['required']}\n  Review Type:     {hr['review_type']}\n  Reasons:         {hr['reason']}", hr_status=hr)

    # 9. Evidence summary
    print("=== EVIDENCE SUMMARY ===")
    if not action_pack.get("evidence_summary"):
        print("  None.")
    for ev in action_pack.get("evidence_summary", []):
        source_name = ev.get("source_name") or ev.get("source_id") or "Unknown"
        freshness = ev.get("freshness_status") or "unknown"
        ev_id = ev.get("evidence_id") or "N/A"
        mode_str = f" | Mode: {ev.get('connector_mode')}" if ev.get('connector_mode') else ""
        print(f"  - Source: {source_name} | Freshness: {freshness} | Evidence ID: {ev_id}{mode_str}")
    print()

    # 10. Draft actions
    print("=== DRAFT ACTIONS ===")
    if not action_pack["proposed_actions"]:
        print("  None.")
    for action in action_pack["proposed_actions"]:
        print(f"  - Type: {action['action_type']} | ID: {action['action_id']}")
        print(f"    Draft Payload: {action['payload']}")
    print()

    print("--- LOGGED AUDIT EVENTS ---")
    for evt in logger.list_events():
        print(f"[{evt['timestamp']}] Action: {evt['action']} | Result: {evt['result']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
