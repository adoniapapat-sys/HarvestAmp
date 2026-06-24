# scripts/validate_fixtures.py
"""Validates YAML fixtures against HarvestAmp schemas."""
import os
import sys
import yaml

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from harvestamp.core.schemas import validate_by_name

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def main():
    success = True
    
    # 1. Validate Prairie View Farms profile
    pvf_path = os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")
    if os.path.exists(pvf_path):
        with open(pvf_path, "r") as f:
            data = yaml.safe_load(f)
        valid, errs = validate_by_name(data, "farm_profile")
        if not valid:
            print(f"FAIL: prairie_view_farms.yaml failed validation:")
            for err in errs:
                print(f"  - {err}")
            success = False
        else:
            print("PASS: prairie_view_farms.yaml validated successfully against farm_profile.")
    else:
        print(f"ERROR: prairie_view_farms.yaml not found at {pvf_path}")
        success = False

    # 2. Validate Green Basket Organics profile
    gbo_path = os.path.join(FIXTURES_DIR, "farms", "green_basket_organics.yaml")
    if os.path.exists(gbo_path):
        with open(gbo_path, "r") as f:
            data = yaml.safe_load(f)
        valid, errs = validate_by_name(data, "farm_profile")
        if not valid:
            print(f"FAIL: green_basket_organics.yaml failed validation:")
            for err in errs:
                print(f"  - {err}")
            success = False
        else:
            print("PASS: green_basket_organics.yaml validated successfully against farm_profile.")
    else:
        print(f"ERROR: green_basket_organics.yaml not found at {gbo_path}")
        success = False

    # 3. Validate Source Metadata list
    sm_path = os.path.join(FIXTURES_DIR, "source_metadata.yaml")
    if os.path.exists(sm_path):
        with open(sm_path, "r") as f:
            items = yaml.safe_load(f)
        for i, item in enumerate(items):
            valid, errs = validate_by_name(item, "source_metadata")
            if not valid:
                print(f"FAIL: source_metadata.yaml item [{i}] failed validation:")
                for err in errs:
                    print(f"  - {err}")
                success = False
        if success:
            print("PASS: source_metadata.yaml all items validated successfully against source_metadata.")
    else:
        print(f"ERROR: source_metadata.yaml not found at {sm_path}")
        success = False

    # 4. Validate Scenarios list
    scen_path = os.path.join(FIXTURES_DIR, "scenarios.yaml")
    if os.path.exists(scen_path):
        with open(scen_path, "r") as f:
            items = yaml.safe_load(f)
        for i, item in enumerate(items):
            valid, errs = validate_by_name(item, "scenario")
            if not valid:
                print(f"FAIL: scenarios.yaml item [{i}] failed validation:")
                for err in errs:
                    print(f"  - {err}")
                success = False
        if success:
            print("PASS: scenarios.yaml all items validated successfully against scenario.")
    else:
        print(f"ERROR: scenarios.yaml not found at {scen_path}")
        success = False

    # 5. Validate Data Observations
    obs_path = os.path.join(FIXTURES_DIR, "data_observations.yaml")
    if os.path.exists(obs_path):
        with open(obs_path, "r") as f:
            data = yaml.safe_load(f)
        valid, errs = validate_by_name(data, "data_observations")
        if not valid:
            print(f"FAIL: data_observations.yaml failed validation:")
            for err in errs:
                print(f"  - {err}")
            success = False
        else:
            print("PASS: data_observations.yaml validated successfully against data_observations.")
    else:
        print(f"ERROR: data_observations.yaml not found at {obs_path}")
        success = False

    if not success:
        print("\nFixture validation failed.")
        sys.exit(1)
    else:
        print("\nAll fixtures validated successfully.")

if __name__ == "__main__":
    main()
