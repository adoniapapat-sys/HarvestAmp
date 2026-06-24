# tests/test_human_review.py
"""Tests for human review policy triggers."""
from harvestamp.policy.human_review_policy import HumanReviewPolicy

def test_human_review_triggers():
    """Verify that different topics trigger the correct human review levels and tiers."""
    policy = HumanReviewPolicy()

    # Informational finding
    info_finding = {"topic": "weather_summary", "confidence": "high", "missing_data": []}
    hr_info = policy.evaluate_finding(info_finding, "farm_owner")
    assert not hr_info["required"]
    assert hr_info["review_type"] == "none"
    assert hr_info["risk_tier"] == "tier_0"

    # Fuel Procurement purchase finding (Tier 2 User Approval)
    fuel_finding = {"topic": "fuel_buy_window", "confidence": "medium", "missing_data": []}
    hr_fuel = policy.evaluate_finding(fuel_finding, "farm_owner")
    assert hr_fuel["required"]
    assert hr_fuel["review_type"] == "user_approval"
    assert hr_fuel["risk_tier"] == "tier_2"
    assert "financial_action" in hr_fuel["reason"]

    # Spray window guidance (Tier 3 Expert Review)
    spray_finding = {"topic": "spray_window", "confidence": "high", "missing_data": []}
    hr_spray = policy.evaluate_finding(spray_finding, "farm_manager")
    assert hr_spray["required"]
    assert hr_spray["review_type"] == "expert_review"
    assert hr_spray["risk_tier"] == "tier_3"
    assert "pesticide_related" in hr_spray["reason"]

    # Organic input verification (Tier 3 Expert Review)
    organic_finding = {"topic": "organic_input_verification", "confidence": "medium", "missing_data": []}
    hr_organic = policy.evaluate_finding(organic_finding, "farm_owner")
    assert hr_organic["required"]
    assert hr_organic["review_type"] == "expert_review"
    assert hr_organic["risk_tier"] == "tier_3"
    assert "organic_certification_sensitive" in hr_organic["reason"]

    # Cross-tenant data request (Tier 4 Blocked)
    cross_finding = {"topic": "cross_farm_private_data", "confidence": "high", "missing_data": []}
    hr_cross = policy.evaluate_finding(cross_finding, "farm_owner")
    assert not hr_cross["required"] # Blocked actions are prevented, not approved
    assert hr_cross["review_type"] == "blocked"
    assert hr_cross["status"] == "blocked"
    assert "cross_tenant_data_request" in hr_cross["reason"]
