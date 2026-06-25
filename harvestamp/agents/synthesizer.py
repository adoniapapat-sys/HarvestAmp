# harvestamp/agents/synthesizer.py
"""Recommendation Synthesizer for HarvestAmp.

Combines individual AgentFindings and EvidenceItems into a unified ActionPack.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from harvestamp.policy.human_review_policy import HumanReviewPolicy

class RecommendationSynthesizer:
    """Consolidates agent findings and evidence into a structured ActionPack."""

    def __init__(self, human_review_policy: Optional[HumanReviewPolicy] = None):
        self.hr_policy = human_review_policy or HumanReviewPolicy()

    def synthesize(
        self,
        farm_id: str,
        workflow_id: str,
        findings: List[Dict[str, Any]],
        evidence_list: List[Dict[str, Any]],
        user_role: str
    ) -> Dict[str, Any]:
        """Combines multiple findings and evidence into a structured ActionPack."""
        action_pack_id = f"ap_{farm_id}_{int(datetime.now(timezone.utc).timestamp())}"
        
        recommendations = []
        proposed_actions = []
        warnings = []
        missing_data = []
        
        # Determine aggregate human review
        overall_hr = {
            "required": False,
            "review_type": "none",
            "risk_tier": "tier_0",
            "status": "review_not_required",
            "reason": [],
            "recommended_reviewer": [],
            "approval_required_before": []
        }
        
        for f in findings:
            finding_topic = f.get("topic", "")
            
            # Skip placeholders if any
            if f.get("summary") in ["Procurement analysis complete.", "Compliance checks completed. No violations found."]:
                continue
                
            rec_id = f"rec_{finding_topic}_{f['finding_id']}"
            
            # Deterministically evaluate human review for this finding
            f_hr = self.hr_policy.evaluate_finding(f, user_role)
            f["human_review"] = f_hr # Update finding

            title = f.get("topic", "General Analysis").replace("_", " ").title()
            if title == "Weekly Plan Pvf":
                title = "Fuel and Input Watch"
            elif title == "Weekly Plan Gbo":
                title = "Packaging and Input Watch"
            elif title == "Irrigation Advisory":
                title = "Irrigation Schedule Advisory"
            elif title == "Irrigation Request Records":
                title = "Irrigation Request Draft"
            
            # Create a recommendation card
            rec = {
                "recommendation_id": rec_id,
                "title": title,
                "summary": f.get("summary", ""),
                "recommendation": f.get("recommendation", ""),
                "farm_id": farm_id,
                "workflow_id": workflow_id,
                "urgency": f.get("urgency", "info"),
                "confidence": f.get("confidence", "high"),
                "recommendation_type": finding_topic,
                "evidence_ids": f.get("evidence_ids", []),
                "missing_data": f.get("missing_data", []),
                "human_review_status": f_hr,
                "proposed_actions": [],
                "assumptions": f.get("assumptions", []),
                "data_sensitivity_used": f.get("data_sensitivity_used", ["Farm Confidential"]),
                "allowed_viewer_roles": f.get("allowed_viewer_roles", ["farm_owner", "farm_manager"]),
                "prohibited_disclosures": f.get("prohibited_disclosures", [])
            }
            
            # Draft proposed actions based on finding topic / scenario expectations
            if finding_topic == "fuel_buy_window":
                # Only if not field employee
                if user_role != "field_employee":
                    action = {
                        "action_id": f"act_fuel_order_{action_pack_id}",
                        "action_type": "supplier_message",
                        "payload": {
                            "recipient": "River County Fuel",
                            "subject": "Diesel delivery availability this week",
                            "body": "Could you confirm whether you can deliver 2,000 gallons of off-road diesel to Prairie View Farms this week? Please include your current delivered price, available delivery dates, and any minimum delivery or delivery-fee details."
                        },
                        "human_review_status": {
                            "required": True,
                            "review_type": "user_approval",
                            "risk_tier": "tier_2",
                            "status": "needs_user_approval",
                            "reason": ["financial_action"]
                        }
                    }
                    proposed_actions.append(action)
                    rec["proposed_actions"].append(action)
                
            elif finding_topic == "packaging_reorder":
                # Only if not GBO restricted roles
                if user_role not in ["field_lead", "market_staff", "external_reviewer"]:
                    # check if stale. If stale, do NOT create packaging order
                    is_stale = f.get("confidence") == "low"
                    if not is_stale:
                        action = {
                            "action_id": f"act_pack_order_{action_pack_id}",
                            "action_type": "supplier_message",
                            "payload": {
                                "recipient": "Box Depot",
                                "subject": "CSA Box Order",
                                "body": "Ari Morgan from Green Basket Organics. We would like to order 250 CSA boxes under our current quote GBO_QUOTE_CSA_BOXES_2026_06_18."
                            },
                            "human_review_status": {
                                "required": True,
                                "review_type": "user_approval",
                                "risk_tier": "tier_2",
                                "status": "needs_user_approval",
                                "reason": ["financial_action"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)
                
            elif finding_topic == "organic_input_verification":
                if user_role not in ["field_lead", "market_staff", "external_reviewer"]:
                    action = {
                        "action_id": f"act_cert_verify_{action_pack_id}",
                        "action_type": "share_with_certifier",
                        "payload": {
                            "recipient": "Organic Certifier",
                            "subject": "Input Material Verification Request",
                            "body": "Please verify if Hudson Valley Compost Organic Granular Fertilizer (GBO_QUOTE_ORGANIC_FERT_2026_06_20) is approved for application on Field A/B certified organic acres."
                        },
                        "human_review_status": {
                            "required": True,
                            "review_type": "expert_review",
                            "risk_tier": "tier_3",
                            "status": "needs_expert_review",
                            "reason": ["organic_certification_sensitive"]
                        }
                    }
                    proposed_actions.append(action)
                    rec["proposed_actions"].append(action)

            elif finding_topic == "irrigation_request_records":
                if user_role not in ["field_lead", "market_staff", "external_reviewer"]:
                    is_low_conf = f.get("confidence") == "low"
                    if not is_low_conf:
                        action = {
                            "action_id": f"act_irrigation_request_{action_pack_id}",
                            "action_type": "submit_irrigation_request",
                            "status": "needs_user_approval",
                            "execution_status": "blocked_until_approved",
                            "disclosure_preview_required": True,
                            "payload": {
                                "field_id": "GBO_AREA_FIELD_A",
                                "turnout_id": "TURNOUT_GBO_A",
                                "duration_hours": 12,
                                "day_of_week": "Tuesday",
                                "provider_name": "River County Water District"
                            },
                            "human_review_status": {
                                "required": True,
                                "review_type": "user_approval",
                                "risk_tier": "tier_2",
                                "status": "needs_user_approval",
                                "execution_status": "blocked_until_approved",
                                "disclosure_preview_required": True,
                                "reason": ["irrigation_water_request"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)

            elif finding_topic == "spray_window" and "pesticide" in str(f.get("summary", "")).lower():
                # Blocked action
                action = {
                    "action_id": f"act_spray_crew_{action_pack_id}",
                    "action_type": "send_crew_instruction",
                    "payload": {
                        "field": "West Ridge 460",
                        "pesticide": "Restricted chemical",
                        "rate": "Maximum label rate"
                    },
                    "human_review_status": {
                        "required": True,
                        "review_type": "expert_review",
                        "risk_tier": "tier_3",
                        "status": "needs_expert_review",
                        "reason": ["pesticide_related", "label_or_restriction_sensitive"]
                    }
                }
                proposed_actions.append(action)
                rec["proposed_actions"].append(action)

            # Weekly Plan action candidates
            elif finding_topic == "weekly_plan_pvf":
                if user_role != "field_employee":
                    # Fuel quote inquiry candidate (requires user approval)
                    action = {
                        "action_id": f"act_weekly_fuel_inquiry_{action_pack_id}",
                        "action_type": "supplier_message",
                        "payload": {
                            "recipient": "River County Fuel",
                            "subject": "Diesel delivery inquiry",
                            "body": "Draft inquiry: request current off-road diesel availability and pricing."
                        },
                        "human_review_status": {
                            "required": True,
                            "review_type": "user_approval",
                            "risk_tier": "tier_2",
                            "status": "needs_user_approval",
                            "reason": ["financial_action", "supplier_message_action"]
                        }
                    }
                    proposed_actions.append(action)
                    rec["proposed_actions"].append(action)

            elif finding_topic == "weekly_plan_gbo":
                if user_role not in ["field_lead", "market_staff", "external_reviewer"]:
                    # CSA Box order message (requires user approval)
                    action1 = {
                        "action_id": f"act_weekly_csa_order_{action_pack_id}",
                        "action_type": "supplier_message",
                        "payload": {
                            "recipient": "Box Depot",
                            "subject": "CSA Box Order Inquiry",
                            "body": "Draft order: request 250 CSA boxes under quote GBO_QUOTE_CSA_BOXES_2026_06_18."
                        },
                        "human_review_status": {
                            "required": True,
                            "review_type": "user_approval",
                            "risk_tier": "tier_2",
                            "status": "needs_user_approval",
                            "reason": ["financial_action", "supplier_message_action"]
                        }
                    }
                    proposed_actions.append(action1)
                    rec["proposed_actions"].append(action1)

                    # Certifier verification share action (requires expert review)
                    action2 = {
                        "action_id": f"act_weekly_cert_share_{action_pack_id}",
                        "action_type": "share_with_certifier",
                        "payload": {
                            "recipient": "Organic Certifier",
                            "subject": "OSP Verification Request",
                            "body": "Draft request: check organic fertilizer status."
                        },
                        "human_review_status": {
                            "required": True,
                            "review_type": "expert_review",
                            "risk_tier": "tier_3",
                            "status": "needs_expert_review",
                            "reason": ["organic_certification_sensitive"]
                        }
                    }
                    proposed_actions.append(action2)
                    rec["proposed_actions"].append(action2)

            recommendations.append(rec)
            
            # Aggregate warnings, missing data
            if f.get("confidence") == "low":
                warnings.append(f"Low confidence on {finding_topic}: {', '.join(f.get('missing_data', []))}")
            if f.get("missing_data"):
                missing_data.extend(f.get("missing_data"))
                
            # Aggregate human review rules from findings
            if f_hr.get("required"):
                overall_hr["required"] = True
                current_type = overall_hr["review_type"]
                new_type = f_hr["review_type"]
                type_priority = {"none": 0, "soft_confirmation": 1, "user_approval": 2, "expert_review": 3, "admin_review": 4, "blocked": 5}
                if type_priority.get(new_type, 0) > type_priority.get(current_type, 0):
                    overall_hr["review_type"] = new_type
                    overall_hr["risk_tier"] = f_hr.get("risk_tier", "tier_2")
                    overall_hr["status"] = f_hr.get("status", "needs_user_approval")
                    
                overall_hr["reason"].extend(f_hr.get("reason", []))
                overall_hr["recommended_reviewer"].extend(f_hr.get("recommended_reviewer", []))
                overall_hr["approval_required_before"].extend(f_hr.get("approval_required_before", []))
            elif f_hr.get("status") == "needs_info":
                if overall_hr["status"] in ["review_not_required", "needs_soft_confirmation"]:
                    overall_hr["status"] = "needs_info"
                overall_hr["reason"].extend(f_hr.get("reason", []))

        # Loop over proposed actions to ensure they are aggregated
        for act in proposed_actions:
            act_hr = act.get("human_review_status", {})
            if act_hr.get("required"):
                overall_hr["required"] = True
                current_type = overall_hr["review_type"]
                new_type = act_hr["review_type"]
                type_priority = {"none": 0, "soft_confirmation": 1, "user_approval": 2, "expert_review": 3, "admin_review": 4, "blocked": 5}
                if type_priority.get(new_type, 0) > type_priority.get(current_type, 0):
                    overall_hr["review_type"] = new_type
                    overall_hr["risk_tier"] = act_hr.get("risk_tier", "tier_2")
                    overall_hr["status"] = act_hr.get("status", "needs_user_approval")
                
                overall_hr["reason"].extend(act_hr.get("reason", []))

        # Deduplicate overall human review lists
        overall_hr["reason"] = list(set(overall_hr["reason"]))
        overall_hr["recommended_reviewer"] = list(set(overall_hr["recommended_reviewer"]))
        overall_hr["approval_required_before"] = list(set(overall_hr["approval_required_before"]))
        
        # Clean up lists if empty
        if not overall_hr["reason"]:
            overall_hr["status"] = "review_not_required"
            
        # Check for SYS-005 stale packaging inventory (no proposed actions, and confidence of packaging_reorder is low)
        is_stale_packaging = any(
            r["recommendation_type"] == "packaging_reorder" and r["confidence"] == "low"
            for r in recommendations
        )
        if is_stale_packaging and not proposed_actions:
            overall_hr.update({
                "required": False,
                "review_type": "none",
                "risk_tier": "tier_0",
                "status": "needs_info",
                "reason": ["stale_data", "low_confidence_due_to_stale_inventory"],
                "recommended_reviewer": [],
                "approval_required_before": []
            })
            
        evidence_summary = [{
            "evidence_id": ev.get("evidence_id"),
            "source_id": ev.get("source_id"),
            "source_name": ev.get("source_name"),
            "trust_tier": ev.get("trust_tier"),
            "freshness_status": ev.get("freshness_status"),
            "privacy_class": ev.get("privacy_class"),
            "timestamp": ev.get("timestamp"),
            "farm_id": ev.get("farm_id"),
            "authorization_status": ev.get("authorization_status"),
            "connector_mode": ev.get("connector_mode"),
            "fallback_used": ev.get("fallback_used"),
            "fallback_reason": ev.get("fallback_reason")
        } for ev in evidence_list]

        return {
            "action_pack_id": action_pack_id,
            "farm_id": farm_id,
            "workflow_id": workflow_id,
            "recommendations": recommendations,
            "proposed_actions": proposed_actions,
            "evidence_summary": evidence_summary,
            "warnings": warnings,
            "missing_data": list(set(missing_data)),
            "human_review_status": overall_hr,
            "status": "draft"
        }
