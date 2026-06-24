# harvestamp/policy/human_review_policy.py
"""Deterministic Human Review Policy evaluator for HarvestAmp.

Loads configs/human_review_rules.yaml and applies triggers to findings and action packs.
"""
import os
import yaml
from typing import Any, Dict, List

# Locate config file
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "configs", "human_review_rules.yaml"))

class HumanReviewPolicy:
    """Evaluates and attaches human review metadata to findings and recommendations."""

    def __init__(self):
        self.rules: Dict[str, Any] = {}
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                self.rules = yaml.safe_load(f)

    def evaluate_finding(self, finding_data: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Evaluates a finding and returns a human_review metadata block."""
        topic = finding_data.get("topic", "")
        confidence = finding_data.get("confidence", "high")
        missing_data = finding_data.get("missing_data", [])
        
        # Start with pre-existing human review if populated by specialist
        specialist_hr = finding_data.get("human_review", {})
        hr = {
            "required": specialist_hr.get("required", False),
            "review_type": specialist_hr.get("review_type", "none"),
            "risk_tier": specialist_hr.get("risk_tier", "tier_0"),
            "status": specialist_hr.get("status", "review_not_required"),
            "reason": list(specialist_hr.get("reason", [])),
            "recommended_reviewer": list(specialist_hr.get("recommended_reviewer", [])),
            "approval_required_before": list(specialist_hr.get("approval_required_before", []))
        }

        # Blocked triggers
        if topic in ["cross_farm_private_data", "cross_tenant_data_request"]:
            hr.update({
                "required": False,
                "review_type": "blocked",
                "risk_tier": "tier_4",
                "status": "blocked",
                "reason": ["cross_tenant_data_request"],
                "recommended_reviewer": ["farm_owner"],
                "approval_required_before": ["view_restricted_data"]
            })
            return hr

        if topic == "credential_connection" or topic == "credential_exposure":
            hr.update({
                "required": True,
                "review_type": "admin_review",
                "risk_tier": "tier_4",
                "status": "needs_admin_review",
                "reason": ["permission_or_credential_change"],
                "recommended_reviewer": ["farm_owner"],
                "approval_required_before": ["connect_data_source"]
            })
            return hr

        # Pesticide/compliance triggers
        if topic in ["spray_window", "pesticide_rate_request"]:
            hr.update({
                "required": True,
                "review_type": "expert_review",
                "risk_tier": "tier_3",
                "status": "needs_expert_review",
                "reason": ["pesticide_related", "label_or_restriction_sensitive"],
                "recommended_reviewer": ["licensed_applicator", "farm_manager"],
                "approval_required_before": ["schedule_crew_instruction", "apply_to_field_plan"]
            })
            return hr

        if topic == "organic_input_verification":
            hr.update({
                "required": True,
                "review_type": "expert_review",
                "risk_tier": "tier_3",
                "status": "needs_expert_review",
                "reason": ["organic_certification_sensitive", "input_approval_uncertain"],
                "recommended_reviewer": ["organic_certifier", "farm_owner"],
                "approval_required_before": ["create_purchase_order", "apply_to_field_plan", "share_with_certifier"]
            })
            return hr

        # Financial / Procurement triggers
        if topic in ["fuel_buy_window", "fertilizer_comparison", "packaging_reorder", "weekly_plan_pvf", "weekly_plan_gbo"]:
            if user_role in ["field_employee", "field_lead", "market_staff"]:
                # Restricted roles do not trigger financial action review
                return hr
                
            if topic == "packaging_reorder" and confidence == "low":
                hr.update({
                    "required": False,
                    "review_type": "none",
                    "risk_tier": "tier_0",
                    "status": "needs_info",
                    "reason": ["stale_data", "low_confidence_due_to_stale_inventory"],
                    "recommended_reviewer": [],
                    "approval_required_before": []
                })
                return hr

            hr.update({
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["financial_action"],
                "recommended_reviewer": ["farm_owner", "farm_manager"],
                "approval_required_before": ["send_message", "create_purchase_order", "commit_to_delivery"]
            })
            
            # Check for stale or missing data fallback (SYS-005 / GBO-004 clamshells)
            if confidence == "low" or any("stale" in str(md).lower() or "missing" in str(md).lower() or "fee" in str(md).lower() or "delivery" in str(md).lower() or "application" in str(md).lower() for md in missing_data):
                hr["reason"].append("low_confidence_due_to_stale_inventory" if "stale" in str(missing_data).lower() else "low_confidence_due_to_missing_fees")
                hr["status"] = "needs_user_approval"
                
            # Merge any pre-existing reasons set by the specialist agent
            if specialist_hr.get("reason"):
                hr["reason"].extend(specialist_hr["reason"])
                
            # Deduplicate reasons
            hr["reason"] = list(set(hr["reason"]))
            return hr

        # Compliance check escalation: if the compliance finding recommends certifier/expert review,
        # ensure its status is needs_expert_review or needs_user_approval.
        if topic in ["compliance_records", "organic_input_records"]:
            rec_lower = finding_data.get("recommendation", "").lower()
            sum_lower = finding_data.get("summary", "").lower()
            if "certifier" in rec_lower or "expert" in rec_lower or "certifier" in sum_lower or "expert" in sum_lower or specialist_hr.get("status") in ["needs_expert_review", "needs_user_approval"]:
                reason_to_add = "organic_certification_sensitive" if topic == "organic_input_records" else "compliance_sensitive"
                status_val = specialist_hr.get("status")
                if not status_val or status_val == "review_not_required":
                    status_val = "needs_expert_review"
                rt_val = specialist_hr.get("review_type")
                if not rt_val or rt_val == "none":
                    rt_val = "expert_review"
                risk_tier_val = specialist_hr.get("risk_tier")
                if not risk_tier_val or risk_tier_val == "tier_0":
                    risk_tier_val = "tier_3"
                hr.update({
                    "required": True,
                    "review_type": rt_val,
                    "risk_tier": risk_tier_val,
                    "status": status_val,
                    "reason": list(set(hr["reason"] + [reason_to_add]))
                })

        return hr
