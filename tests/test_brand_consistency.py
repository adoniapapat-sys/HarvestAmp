# tests/test_brand_consistency.py
"""Tests for brand consistency across the repository.

Ensures no legacy product names are used in active code, schemas, or configs.
"""
import os

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_no_legacy_brand_names():
    """Verify that legacy name 'FarmHand' does not exist in code, schemas, or configs."""
    legacy_name = "FarmHand"
    
    # Files to search
    search_dirs = ["harvestamp", "schemas", "configs", "scripts"]
    
    found_occurrences = []
    
    for sdir in search_dirs:
        full_dir = os.path.join(PROJECT_DIR, sdir)
        if not os.path.exists(full_dir):
            continue
            
        for root, dirs, files in os.walk(full_dir):
            for file in files:
                if file.endswith((".py", ".yaml", ".yml", ".json")):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # Case insensitive check
                        if legacy_name.lower() in content.lower():
                            found_occurrences.append(file_path)
                            
    assert not found_occurrences, f"Found legacy brand name '{legacy_name}' in: {found_occurrences}"

def test_brand_name_harvestamp_present():
    """Verify that 'HarvestAmp' is referenced in README.md."""
    readme_path = os.path.join(PROJECT_DIR, "README.md")
    assert os.path.exists(readme_path)
    with open(readme_path, "r") as f:
        readme_content = f.read()
    assert "HarvestAmp" in readme_content
