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

        # Irrigation triggers
        if topic == "irrigation_advisory":
            if specialist_hr.get("review_type") == "expert_review" or "water_rights_or_allocation_sensitive" in hr["reason"]:
                hr.update({
                    "required": True,
                    "review_type": "expert_review",
                    "risk_tier": "tier_3",
                    "status": "needs_expert_review",
                    "reason": list(set(hr["reason"] + ["water_rights_or_allocation_sensitive"])),
                    "recommended_reviewer": ["farm_owner"],
                    "approval_required_before": []
                })
            else:
                hr.update({
                    "required": False,
                    "review_type": "none",
                    "risk_tier": "tier_0",
                    "status": "review_not_required",
                    "reason": [],
                    "recommended_reviewer": [],
                    "approval_required_before": []
                })
            return hr

        if topic == "irrigation_request_records":
            if confidence == "low" or len(missing_data) > 0:
                hr.update({
                    "required": False,
                    "review_type": "none",
                    "risk_tier": "tier_0",
                    "status": "needs_info",
                    "reason": ["low_confidence_due_to_missing_data"],
                    "recommended_reviewer": [],
                    "approval_required_before": []
                })
            else:
                hr.update({
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["irrigation_water_request"],
                    "recommended_reviewer": ["farm_owner", "farm_manager"],
                    "approval_required_before": ["submit_irrigation_request"]
                })
            return hr

        if topic == "irrigation_compliance":
            if specialist_hr.get("review_type") == "expert_review" or "water_rights_or_allocation_sensitive" in hr["reason"]:
                hr.update({
                    "required": True,
                    "review_type": "expert_review",
                    "risk_tier": "tier_3",
                    "status": "needs_expert_review",
                    "reason": list(set(hr["reason"] + ["water_rights_or_allocation_sensitive"])),
                    "recommended_reviewer": ["farm_owner"],
                    "approval_required_before": ["submit_irrigation_request"]
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

        if topic == "inventory_records":
            if user_role not in ["field_employee", "field_lead", "market_staff"]:
                sum_str = str(finding_data.get("summary", "")).lower()
                if "cooler" in sum_str and ("draft" in sum_str or "blocked" in sum_str):
                    hr.update({
                        "required": True,
                        "review_type": "user_approval",
                        "risk_tier": "tier_2",
                        "status": "needs_user_approval",
                        "reason": ["post_harvest_inventory_review", "draft_cooler_inventory_update"],
                        "recommended_reviewer": ["farm_owner", "farm_manager"],
                        "approval_required_before": ["commit_to_official_records"]
                    })
            return hr

        # Harvest-time domain review gates
        if topic == "yield_records":
            status = "needs_info" if finding_data.get("missing_data") else "review_not_required"
            hr.update({
                "required": status == "needs_info",
                "review_type": "user_approval" if status == "needs_info" else "none",
                "risk_tier": "tier_1" if status == "needs_info" else "tier_0",
                "status": status,
                "reason": list(set(hr["reason"] + ["yield_record_review"])),
                "recommended_reviewer": ["farm_owner", "farm_manager"] if status == "needs_info" else [],
                "approval_required_before": ["provide_field_c_adjusted_quantity", "provide_field_c_dockage_or_shrink"] if status == "needs_info" else []
            })
            return hr

        if topic == "harvest_records":
            hr.update({
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": list(set(hr["reason"] + ["official_record_update", "cooler_inventory_update"])),
                "recommended_reviewer": ["farm_owner", "farm_manager"],
                "approval_required_before": ["commit_to_official_records"]
            })
            return hr

        if topic == "grain_records":
            status = "needs_user_approval"
            reason_list = ["official_record_update", "grain_reconciliation_needed"]
            blockers = ["commit_to_official_records"]
            sum_str = str(finding_data.get("summary", "")).lower()
            if "bin reconciliation" in sum_str or "bin inventory" in sum_str or "out of sync" in sum_str or "out_of_sync" in sum_str or "variance" in sum_str or "mismatch" in sum_str:
                status = "needs_info"
                reason_list = ["grain_bin_reconciliation"]
                blockers = ["resolve_bin_variance", "commit_to_official_records"]
            
            if "out_of_sync" in sum_str or finding_data.get("missing_data") or "needs_info" in str(specialist_hr.get("status", "")):
                status = "needs_info"
            
            if user_role in ["field_employee"]:
                status = "review_not_required"
                reason_list = []
                blockers = []
            
            hr.update({
                "required": status in ["needs_user_approval", "needs_info"],
                "review_type": "user_approval" if status in ["needs_user_approval", "needs_info"] else "none",
                "risk_tier": "tier_2" if status == "needs_user_approval" else ("tier_1" if status == "needs_info" else "tier_0"),
                "status": status,
                "reason": list(set(hr["reason"] + reason_list)),
                "recommended_reviewer": ["farm_owner"],
                "approval_required_before": blockers
            })
            return hr

        sum_str = str(finding_data.get("summary", "")).lower()
        if topic == "direct_market_sales" or (topic == "farmers_market" and ("returned" in sum_str or "returns" in sum_str)):
            status = "needs_user_approval"
            reason_list = ["sales_reconciliation_needed"]
            blockers = ["reconcile_sales_records"]
            if "returned" in sum_str or "returns" in sum_str:
                blockers = ["reconcile_sales_records", "verify_returned_inventory_quality", "commit_to_official_records"]
                reason_list.append("post_harvest_inventory_review")
            elif "csa packout" in sum_str or "shortage" in sum_str or "pre-order" in sum_str:
                blockers = ["approve_harvest_plan", "commit_to_official_records"]
                reason_list.append("post_harvest_inventory_review")
            
            if user_role in ["field_employee"]:
                status = "review_not_required"
                reason_list = []
                blockers = []
            
            hr.update({
                "required": status == "needs_user_approval",
                "review_type": "user_approval" if status == "needs_user_approval" else "none",
                "risk_tier": "tier_2" if status == "needs_user_approval" else "tier_0",
                "status": status,
                "reason": list(set(hr["reason"] + reason_list)),
                "recommended_reviewer": ["farm_owner", "farm_manager"],
                "approval_required_before": blockers
            })
            return hr

        if topic == "commodity_markets":
            sum_str = str(finding_data.get("summary", "")).lower()
            if ("elevator" in sum_str or "settlement" in sum_str) and "watch" not in sum_str:
                status = "needs_user_approval"
                required = True
                rt = "user_approval"
                tier = "tier_2"
                blockers = ["commit_to_official_records"]
            else:
                status = "needs_info" if finding_data.get("missing_data") else "review_not_required"
                required = status == "needs_info"
                rt = "user_approval" if status == "needs_info" else "none"
                tier = "tier_1" if status == "needs_info" else "tier_0"
                blockers = ["provide_local_bid", "provide_local_basis", "no_sale_recommendation_without_current_farm_authorized_bid_basis"] if status == "needs_info" else []
            
            if user_role in ["field_employee"]:
                status = "review_not_required"
                required = False
                rt = "none"
                tier = "tier_0"
                blockers = []

            hr.update({
                "required": required,
                "review_type": rt,
                "risk_tier": tier,
                "status": status,
                "reason": list(set(hr["reason"] + ["elevator_settlement_review"])),
                "recommended_reviewer": ["farm_owner"],
                "approval_required_before": blockers
            })
            return hr

        # Compliance check escalation: if the compliance finding recommends certifier/expert review,
        # ensure its status is needs_expert_review or needs_user_approval.
        if topic in ["compliance_records", "organic_input_records"]:
            rec_lower = finding_data.get("recommendation", "").lower()
            sum_lower = finding_data.get("summary", "").lower()
            
            # Crop insurance caution specific check
            if "crop insurance and production-record compliance:" in sum_lower:
                hr.update({
                    "required": True,
                    "review_type": "expert_review",
                    "risk_tier": "tier_3",
                    "status": "needs_expert_review",
                    "reason": list(set(hr["reason"] + ["production_record_caution", "yield_record_review"])),
                    "recommended_reviewer": ["certified_crop_advisor", "farm_owner"],
                    "approval_required_before": ["report_to_crop_insurance", "report_to_fsa"]
                })
                return hr

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

        # General review status safety net
        if hr.get("status") in ["needs_user_approval", "needs_expert_review", "needs_info"]:
            hr["required"] = True
            if hr.get("review_type") in ["none", ""]:
                hr["review_type"] = "user_approval"
            if hr.get("risk_tier") in ["tier_0", ""]:
                hr["risk_tier"] = "tier_1" if hr.get("status") == "needs_info" else "tier_2"

        return hr

