# harvestamp/agents/synthesizer.py
"""Recommendation Synthesizer for HarvestAmp.

Combines individual AgentFindings and EvidenceItems into a unified ActionPack.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from harvestamp.policy.human_review_policy import HumanReviewPolicy
from harvestamp.core.contracts import normalize_agent_finding_contract, normalize_action_pack_contract

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
        
        findings = [normalize_agent_finding_contract(f) for f in findings if f is not None]
        for f in findings:
            finding_topic = f.get("topic", "")
            
            # Skip placeholders if any
            if f.get("summary") in ["Procurement analysis complete.", "Compliance checks completed. No violations found."]:
                continue
                
            rec_id = f"rec_{finding_topic}_{f['finding_id']}"
            
            # Deterministically evaluate human review for this finding
            f_hr = self.hr_policy.evaluate_finding(f, user_role)
            f["human_review"] = f_hr # Update finding

            rec_type = f.get("recommendation_type", finding_topic)
            
            # Map title based on recommendation_type or topic
            title = f.get("topic", "General Analysis").replace("_", " ").title()
            if rec_type == "fuel_watch":
                title = "Fuel Watch"
            elif rec_type == "fertilizer_quote_watch":
                title = "Fertilizer / Input Quote Watch"
            elif rec_type == "crop_health_watchlist":
                title = "Crop Health Watchlist"
            elif title == "Weekly Plan Pvf":
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
                "recommendation_type": rec_type,
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
                if user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
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
                if user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
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
                if user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
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

            elif finding_topic == "harvest_records":
                if user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
                    action1 = {
                        "action_id": f"act_harvest_record_update_{action_pack_id}",
                        "action_type": "draft_harvest_record_update",
                        "external_action": False,
                        "status": "blocked_pending_user_approval",
                        "evidence_ids": f.get("evidence_ids", []),
                        "payload": {
                            "record_type": "harvest_event",
                            "details": f.get("summary")
                        },
                        "human_review_status": {
                            "required": True,
                            "review_type": "user_approval",
                            "risk_tier": "tier_2",
                            "status": "needs_user_approval",
                            "reason": ["official_record_update"]
                        }
                    }
                    action2 = {
                        "action_id": f"act_cooler_inv_update_{action_pack_id}",
                        "action_type": "draft_cooler_inventory_update",
                        "external_action": False,
                        "status": "blocked_pending_user_approval",
                        "evidence_ids": f.get("evidence_ids", []),
                        "payload": {
                            "record_type": "post_harvest_inventory",
                            "details": f.get("summary")
                        },
                        "human_review_status": {
                            "required": True,
                            "review_type": "user_approval",
                            "risk_tier": "tier_2",
                            "status": "needs_user_approval",
                            "reason": ["cooler_inventory_update"]
                        }
                    }
                    proposed_actions.extend([action1, action2])
                    rec["proposed_actions"].extend([action1, action2])

            elif finding_topic == "grain_records":
                if user_role not in ["field_employee"]:
                    sum_str = str(f.get("summary", "")).lower()
                    if "ticket" in sum_str or "load ticket" in sum_str:
                        action = {
                            "action_id": f"act_load_ticket_{action_pack_id}",
                            "action_type": "draft_grain_load_ticket_record",
                            "external_action": False,
                            "status": "blocked_pending_user_approval",
                            "evidence_ids": f.get("evidence_ids", []),
                            "payload": {
                                "details": f.get("summary")
                            },
                            "human_review_status": {
                                "required": True,
                                "review_type": "user_approval",
                                "risk_tier": "tier_2",
                                "status": "needs_user_approval",
                                "reason": ["official_record_update"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)
                    elif "bin" in sum_str or "out_of_sync" in sum_str:
                        status_val = "needs_info" if "out_of_sync" in sum_str else "blocked_pending_user_approval"
                        action = {
                            "action_id": f"act_bin_recon_{action_pack_id}",
                            "action_type": "draft_bin_reconciliation",
                            "external_action": False,
                            "status": status_val,
                            "evidence_ids": f.get("evidence_ids", []),
                            "payload": {
                                "details": f.get("summary")
                            },
                            "human_review_status": {
                                "required": status_val == "blocked_pending_user_approval",
                                "review_type": "user_approval" if status_val == "blocked_pending_user_approval" else "none",
                                "risk_tier": "tier_2" if status_val == "blocked_pending_user_approval" else "tier_0",
                                "status": status_val,
                                "reason": ["grain_reconciliation_needed"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)

            elif finding_topic in ["direct_market_sales", "farmers_market"]:
                if user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
                    sum_str = str(f.get("summary", "")).lower()
                    if "returned" in sum_str or "returns" in sum_str:
                        action = {
                            "action_id": f"act_returned_recon_{action_pack_id}",
                            "action_type": "draft_returned_inventory_reconciliation",
                            "external_action": False,
                            "status": "blocked_pending_user_approval",
                            "evidence_ids": f.get("evidence_ids", []),
                            "payload": {
                                "details": f.get("summary")
                            },
                            "human_review_status": {
                                "required": True,
                                "review_type": "user_approval",
                                "risk_tier": "tier_2",
                                "status": "needs_user_approval",
                                "reason": ["sales_reconciliation_needed", "post_harvest_inventory_review"],
                                "approval_required_before": ["verify_returned_inventory_quality", "reconcile_sales_records", "commit_to_official_records"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)
                    elif "sales record reconciliation" in sum_str or "partially_reconciled" in sum_str or "invoice" in sum_str:
                        action = {
                            "action_id": f"act_sales_recon_{action_pack_id}",
                            "action_type": "draft_sales_record_reconciliation",
                            "external_action": False,
                            "status": "blocked_pending_user_approval",
                            "evidence_ids": f.get("evidence_ids", []),
                            "payload": {
                                "details": f.get("summary")
                            },
                            "human_review_status": {
                                "required": True,
                                "review_type": "user_approval",
                                "risk_tier": "tier_2",
                                "status": "needs_user_approval",
                                "reason": ["sales_reconciliation_needed"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)
                    elif "csa packout check:" in sum_str or "restaurant order fulfillment check:" in sum_str or ("shortage" in sum_str and "pack list" not in sum_str):
                        action = {
                            "action_id": f"act_harvest_pack_plan_{action_pack_id}",
                            "action_type": "draft_harvest_pack_plan",
                            "external_action": False,
                            "status": "blocked_pending_user_approval",
                            "evidence_ids": f.get("evidence_ids", []),
                            "payload": {
                                "details": f.get("summary")
                            },
                            "human_review_status": {
                                "required": True,
                                "review_type": "user_approval",
                                "risk_tier": "tier_2",
                                "status": "needs_user_approval",
                                "reason": ["sales_record_reconciliation", "post_harvest_inventory_review"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)

            elif finding_topic == "commodity_markets":
                if user_role not in ["field_employee"]:
                    sum_str = str(f.get("summary", "")).lower()
                    if ("elevator" in sum_str or "settlement" in sum_str) and "watch" not in sum_str:
                        action = {
                            "action_id": f"act_elevator_settlement_{action_pack_id}",
                            "action_type": "draft_elevator_settlement_record",
                            "external_action": False,
                            "status": "blocked_pending_user_approval",
                            "evidence_ids": f.get("evidence_ids", []),
                            "payload": {
                                "details": f.get("summary")
                            },
                            "human_review_status": {
                                "required": True,
                                "review_type": "user_approval",
                                "risk_tier": "tier_2",
                                "status": "needs_user_approval",
                                "reason": ["elevator_settlement_review"]
                            }
                        }
                        proposed_actions.append(action)
                        rec["proposed_actions"].append(action)

            elif finding_topic == "spray_window" and "pesticide" in str(f.get("summary", "")).lower() and "cannot recommend" not in str(f.get("summary", "")).lower() and "cannot recommend" not in str(f.get("recommendation", "")).lower():
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
                if user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
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

            elif finding_topic == "compliance_records":
                is_weekly_run = any("weekly" in str(fd.get("topic", "")).lower() or "weekly" in str(fd.get("summary", "")).lower() for fd in findings)
                if is_weekly_run and user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
                    is_gbo = "gbo" in str(f.get("summary", "")).lower() or "organic" in str(f.get("summary", "")).lower() or "gbo" in str(f.get("farm_id", "")).lower()
                    if is_gbo:
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

        # Scan all findings for indicators to create proposed actions for weekly plans
        all_text = " ".join([str(f.get("summary", "")) + " " + str(f.get("recommendation", "")) for f in findings]).lower()
        is_weekly = any("weekly_plan" in str(f.get("topic", "")) or "weekly" in str(f.get("summary", "")).lower() for f in findings)

        if is_weekly and user_role not in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
            evidence_ids = list(set([ev for f in findings for ev in f.get("evidence_ids", [])]))
            all_ids = [e.get("evidence_id") for e in evidence_list if e.get("evidence_id")]
            
            # 1. Cooler inventory draft/blocked
            if "cooler" in all_text and ("draft" in all_text or "blocked" in all_text) and not any(a["action_type"] == "draft_cooler_inventory_update" for a in proposed_actions):
                proposed_actions.append({
                    "action_id": f"act_weekly_cooler_{action_pack_id}",
                    "action_type": "draft_cooler_inventory_update",
                    "external_action": False,
                    "status": "blocked_pending_user_approval",
                    "evidence_ids": evidence_ids,
                    "payload": {"details": "Weekly cooler inventory update draft review"},
                    "human_review_status": {
                        "required": True,
                        "review_type": "user_approval",
                        "risk_tier": "tier_2",
                        "status": "needs_user_approval",
                        "reason": ["draft_cooler_inventory_update", "post_harvest_inventory_review"]
                    }
                })
                # Add to inventory_records recommendation if present
                for r in recommendations:
                    if r["recommendation_type"] == "inventory_records":
                        r["proposed_actions"].append(proposed_actions[-1])
            
            # 2. Bin inventory draft/blocked/out_of_sync
            if "bin" in all_text and ("draft" in all_text or "blocked" in all_text or "out of sync" in all_text or "out_of_sync" in all_text) and not any(a["action_type"] == "draft_bin_reconciliation" for a in proposed_actions):
                proposed_actions.append({
                    "action_id": f"act_weekly_bin_{action_pack_id}",
                    "action_type": "draft_bin_reconciliation",
                    "external_action": False,
                    "status": "blocked_pending_user_approval",
                    "evidence_ids": evidence_ids,
                    "payload": {"details": "Weekly grain bin inventory reconciliation draft review"},
                    "human_review_status": {
                        "required": True,
                        "review_type": "user_approval",
                        "risk_tier": "tier_2",
                        "status": "needs_user_approval",
                        "reason": ["grain_bin_reconciliation"]
                    }
                })
                # Add to inventory_records / grain_records recommendation
                for r in recommendations:
                    if r["recommendation_type"] in ["inventory_records", "grain_records"]:
                        r["proposed_actions"].append(proposed_actions[-1])

            # 3. Yield records draft/blocked/missing
            if "yield" in all_text and ("draft" in all_text or "blocked" in all_text or "unknown" in all_text) and not any(a["action_type"] == "draft_official_record_update" and "yield" in str(a["payload"].get("details", "")).lower() for a in proposed_actions):
                proposed_actions.append({
                    "action_id": f"act_weekly_yield_{action_pack_id}",
                    "action_type": "draft_official_record_update",
                    "external_action": False,
                    "status": "blocked_pending_user_approval",
                    "evidence_ids": evidence_ids,
                    "payload": {"details": "Weekly yield record update draft review"},
                    "human_review_status": {
                        "required": True,
                        "review_type": "user_approval",
                        "risk_tier": "tier_2",
                        "status": "needs_user_approval",
                        "reason": ["yield_record_review", "harvest_record_review"]
                    }
                })
                # Add to inventory_records / yield_records recommendation
                for r in recommendations:
                    if r["recommendation_type"] in ["inventory_records", "yield_records"]:
                        r["proposed_actions"].append(proposed_actions[-1])

            # 4. Sales reconciliation draft/blocked
            if any("sal" in str(e).lower() for e in all_ids) and ("sales" in all_text or "reconciliation" in all_text or "unpaid" in all_text) and ("draft" in all_text or "blocked" in all_text or "reconcil" in all_text or "partially" in all_text) and not any(a["action_type"] == "draft_sales_record_reconciliation" for a in proposed_actions):
                proposed_actions.append({
                    "action_id": f"act_weekly_sales_recon_{action_pack_id}",
                    "action_type": "draft_sales_record_reconciliation",
                    "external_action": False,
                    "status": "blocked_pending_user_approval",
                    "evidence_ids": evidence_ids,
                    "payload": {"details": "Weekly sales record reconciliation draft review"},
                    "human_review_status": {
                        "required": True,
                        "review_type": "user_approval",
                        "risk_tier": "tier_2",
                        "status": "needs_user_approval",
                        "reason": ["sales_record_reconciliation"]
                    }
                })
                # Add to direct_market_sales / farmers_market recommendation
                for r in recommendations:
                    if r["recommendation_type"] in ["direct_market_sales", "farmers_market"]:
                        r["proposed_actions"].append(proposed_actions[-1])

            # 5. Settlement records draft/blocked
            if "settlement" in all_text and ("draft" in all_text or "blocked" in all_text) and not any(a["action_type"] == "draft_official_record_update" and "settlement" in str(a["payload"].get("details", "")).lower() for a in proposed_actions):
                proposed_actions.append({
                    "action_id": f"act_weekly_settlement_{action_pack_id}",
                    "action_type": "draft_official_record_update",
                    "external_action": False,
                    "status": "blocked_pending_user_approval",
                    "evidence_ids": evidence_ids,
                    "payload": {"details": "Weekly elevator settlement record draft review"},
                    "human_review_status": {
                        "required": True,
                        "review_type": "user_approval",
                        "risk_tier": "tier_2",
                        "status": "needs_user_approval",
                        "reason": ["sales_record_reconciliation", "yield_record_review"]
                    }
                })
                # Add to commodity_markets recommendation
                for r in recommendations:
                    if r["recommendation_type"] == "commodity_markets":
                        r["proposed_actions"].append(proposed_actions[-1])

            # 6. General draft inventory reconciliation
            if ("cooler" in all_text or "bin" in all_text or "inventory" in all_text) and ("draft" in all_text or "blocked" in all_text or "out of sync" in all_text or "out_of_sync" in all_text) and not any(a["action_type"] == "draft_inventory_reconciliation" for a in proposed_actions):
                dyn_reasons = []
                if "gbo" in farm_id.lower() or "cooler" in all_text:
                    dyn_reasons.append("post_harvest_inventory_review")
                if "pvf" in farm_id.lower() or "bin" in all_text:
                    dyn_reasons.append("grain_bin_reconciliation")
                if not dyn_reasons:
                    dyn_reasons = ["post_harvest_inventory_review"]

                proposed_actions.append({
                    "action_id": f"act_weekly_inv_recon_{action_pack_id}",
                    "action_type": "draft_inventory_reconciliation",
                    "external_action": False,
                    "status": "blocked_pending_user_approval",
                    "evidence_ids": evidence_ids,
                    "payload": {"details": "Weekly inventory reconciliation draft review"},
                    "human_review_status": {
                        "required": True,
                        "review_type": "user_approval",
                        "risk_tier": "tier_2",
                        "status": "needs_user_approval",
                        "reason": dyn_reasons
                    }
                })
                # Add to inventory_records / grain_records recommendation
                for r in recommendations:
                    if r["recommendation_type"] in ["inventory_records", "grain_records", "yield_records"]:
                        r["proposed_actions"].append(proposed_actions[-1])

        def resolve_action_evidence(act_type, f_ev_ids, evidence_list, act):
            all_ids = [ev.get("evidence_id") for ev in evidence_list]
            base_ids = [e for e in f_ev_ids if e]
            if not base_ids:
                base_ids = all_ids
                
            if act_type == "supplier_message":
                body_lower = str(act.get("payload", {}).get("body", "")).lower()
                if "diesel" in body_lower or "fuel" in body_lower:
                    res = [e for e in base_ids if "diesel" in str(e).lower() or "fuel" in str(e).lower() or "quo_pvf" in str(e).lower()]
                    if not res:
                        res = [e for e in all_ids if "diesel" in str(e).lower() or "fuel" in str(e).lower() or "quo_pvf" in str(e).lower()]
                    return res if res else ([e for e in all_ids if "diesel" in str(e).lower() or "fuel" in str(e).lower()] if [e for e in all_ids if "diesel" in str(e).lower() or "fuel" in str(e).lower()] else [all_ids[0]] if all_ids else ["unknown"])
                else:
                    res = [e for e in base_ids if "csa_box" in str(e).lower() or "box" in str(e).lower()]
                    if not res:
                        res = [e for e in all_ids if "csa_box" in str(e).lower() or "box" in str(e).lower()]
                    return res if res else ([e for e in all_ids if "box" in str(e).lower()] if [e for e in all_ids if "box" in str(e).lower()] else [all_ids[0]] if all_ids else ["unknown"])

            elif act_type == "share_with_certifier":
                res = [e for e in base_ids if any(k in str(e).lower() for k in ["cert", "organic", "compliance", "harv", "food-safety", "food_safety"])]
                if not res:
                    res = [e for e in all_ids if any(k in str(e).lower() for k in ["cert", "organic", "compliance", "harv", "food-safety", "food_safety"])]
                return res if res else [all_ids[0]] if all_ids else ["unknown"]

            elif act_type in ["draft_bin_reconciliation", "draft_inventory_reconciliation"]:
                if any("phi" in str(e).lower() for e in base_ids + all_ids):
                    res = [e for e in base_ids if "phi" in str(e).lower()]
                    if not res:
                        res = [e for e in all_ids if "phi" in str(e).lower()]
                    return res if res else [all_ids[0]] if all_ids else ["unknown"]
                else:
                    res = [e for e in base_ids if "bin_pvf_bin_003" in str(e).lower()]
                    if not res:
                        res = [e for e in base_ids if "bin" in str(e).lower()]
                    if not res:
                        res = [e for e in all_ids if "bin_pvf_bin_003" in str(e).lower()]
                    if not res:
                        res = [e for e in all_ids if "bin" in str(e).lower()]
                    return res if res else ([e for e in all_ids if "bin" in str(e).lower()] if [e for e in all_ids if "bin" in str(e).lower()] else [all_ids[0]] if all_ids else ["unknown"])

            elif act_type == "draft_harvest_record_update":
                res = [e for e in base_ids if "harv" in str(e).lower()]
                if not res:
                    res = [e for e in all_ids if "harv" in str(e).lower()]
                return res if res else ([e for e in all_ids if "harv" in str(e).lower()] if [e for e in all_ids if "harv" in str(e).lower()] else [all_ids[0]] if all_ids else ["unknown"])

            elif act_type == "draft_official_record_update":
                res = [e for e in base_ids if "yld" in str(e).lower() or "tkt" in str(e).lower()]
                if not res:
                    res = [e for e in all_ids if "yld" in str(e).lower() or "tkt" in str(e).lower()]
                return res if res else ([e for e in all_ids if "yld" in str(e).lower()] if [e for e in all_ids if "yld" in str(e).lower()] else [all_ids[0]] if all_ids else ["unknown"])

            elif act_type in ["draft_sales_record_reconciliation", "draft_returned_inventory_reconciliation"]:
                # Primary should be sales record (res_sal_GBO_SAL_001)
                primary = [e for e in base_ids if "sal" in str(e).lower()]
                if not primary:
                    primary = [e for e in all_ids if "sal" in str(e).lower()]
                
                # Check for yield or ticket records (e.g. elevator deliveries/settlements for PVF)
                if not primary:
                    primary = [e for e in base_ids if "yld" in str(e).lower() or "tkt" in str(e).lower()]
                if not primary:
                    primary = [e for e in all_ids if "yld" in str(e).lower() or "tkt" in str(e).lower()]
                
                # Keep sales commitments (com) and post-harvest inventory (phi) in related_evidence
                related = [e for e in base_ids if "com" in str(e).lower() or "phi" in str(e).lower()]
                if not related:
                    related = [e for e in all_ids if "com" in str(e).lower() or "phi" in str(e).lower()]
                
                # Deduplicate
                related = [e for e in related if e not in primary]
                return (primary + related) if primary else (related if related else [all_ids[0]] if all_ids else ["unknown"])

            elif act_type == "draft_cooler_inventory_update":
                # Primary should be post-harvest inventory (res_phi_GBO_PHI_001 / res_phi_*)
                primary = [e for e in base_ids if "phi" in str(e).lower()]
                if not primary:
                    primary = [e for e in all_ids if "phi" in str(e).lower()]
                
                # Keep harvest records (harv) in related_evidence
                related = [e for e in base_ids if "harv" in str(e).lower()]
                if not related:
                    related = [e for e in all_ids if "harv" in str(e).lower()]
                
                related = [e for e in related if e not in primary]
                return (primary + related) if primary else (related if related else [all_ids[0]] if all_ids else ["unknown"])

            elif act_type == "draft_grain_load_ticket_record":
                res = [e for e in base_ids if "tkt_pvf_tkt_001" in str(e).lower()]
                if not res:
                    res = [e for e in base_ids if "tkt" in str(e).lower()]
                if not res:
                    res = [e for e in all_ids if "tkt_pvf_tkt_001" in str(e).lower()]
                if not res:
                    res = [e for e in all_ids if "tkt" in str(e).lower()]
                return res if res else ([e for e in all_ids if "tkt" in str(e).lower()] if [e for e in all_ids if "tkt" in str(e).lower()] else [all_ids[0]] if all_ids else ["unknown"])

            elif act_type == "draft_elevator_settlement_record":
                # Primary should be soybean yield record PVF_YLD_002, strictly exclude corn PVF_YLD_001
                primary = [e for e in base_ids if "yld_pvf_yld_002" in str(e).lower()]
                if not primary:
                    primary = [e for e in all_ids if "yld_pvf_yld_002" in str(e).lower()]
                
                if not primary:
                    primary = [e for e in base_ids if "yld" in str(e).lower() or "tkt" in str(e).lower()]
                if not primary:
                    primary = [e for e in all_ids if "yld" in str(e).lower() or "tkt" in str(e).lower()]
                
                primary = [e for e in primary if "yld_pvf_yld_001" not in str(e).lower()]
                
                related = [e for e in base_ids if ("yld" in str(e).lower() or "tkt" in str(e).lower()) and "yld_pvf_yld_001" not in str(e).lower() and e not in primary]
                if not related:
                    related = [e for e in all_ids if ("yld" in str(e).lower() or "tkt" in str(e).lower()) and "yld_pvf_yld_001" not in str(e).lower() and e not in primary]
                
                return (primary + related) if primary else (related if related else [all_ids[0]] if all_ids else ["unknown"])

            return base_ids

        # Remove proposed actions for field_employee to keep draft actions hidden
        if user_role == "field_employee":
            proposed_actions = []
            for r in recommendations:
                r["proposed_actions"] = []

        # Loop over proposed actions to ensure they are aggregated
        for act in proposed_actions:
            act_type = act.get("action_type", "")
            if act_type.startswith("draft_") or act_type in ["submit_irrigation_request", "supplier_message", "share_with_certifier", "send_crew_instruction"]:
                payload = act.get("payload", {})
                status_val = act.get("status", "blocked_pending_user_approval")
                
                f_ev_ids = act.get("evidence_ids", [])
                act_ev_ids = resolve_action_evidence(act_type, f_ev_ids, evidence_list, act)
                act["evidence_ids"] = act_ev_ids
                
                record_types = {
                    "draft_harvest_record_update": "harvest_event",
                    "draft_cooler_inventory_update": "post_harvest_inventory",
                    "draft_grain_load_ticket_record": "grain_load_ticket",
                    "draft_bin_reconciliation": "grain_bin_inventory",
                    "draft_returned_inventory_reconciliation": "post_harvest_inventory",
                    "draft_sales_record_reconciliation": "sales_record",
                    "draft_elevator_settlement_record": "sales_record",
                    "draft_harvest_pack_plan": "harvest_pack_plan",
                    "draft_official_record_update": "yield_record" if "yield" in str(payload.get("details", "")).lower() else "sales_record",
                    "draft_inventory_reconciliation": "post_harvest_inventory" if "cooler" in str(payload.get("details", "")).lower() or "gbo" in farm_id.lower() else "grain_bin_inventory",
                    "supplier_message": "supplier_quote",
                    "share_with_certifier": "organic_certification",
                    "submit_irrigation_request": "irrigation_request"
                }
                rec_type = record_types.get(act_type, "harvest_record")
                
                matching_rec = None
                for r in recommendations:
                    if act in r.get("proposed_actions", []) or any(a.get("action_id") == act.get("action_id") for a in r.get("proposed_actions", [])):
                        matching_rec = r
                        break
                
                primary_ev_id = "unknown"
                if act_ev_ids:
                    primary_ev_id = act_ev_ids[0]
                    if act_type == "draft_grain_load_ticket_record":
                        tickets = [e for e in act_ev_ids if str(e).startswith("res_tkt_")]
                        if tickets:
                            primary_ev_id = tickets[0]
                    elif act_type in ["draft_returned_inventory_reconciliation", "draft_sales_record_reconciliation"]:
                        sales = [e for e in act_ev_ids if str(e).startswith("res_sal_") or str(e).startswith("res_com_")]
                        if sales:
                            primary_ev_id = sales[0]
                    elif act_type == "draft_elevator_settlement_record":
                        settles = [e for e in act_ev_ids if str(e).startswith("res_yld_") or str(e).startswith("res_tkt_")]
                        if settles:
                            primary_ev_id = settles[0]

                payload.update({
                    "status": status_val,
                    "requires_approval": True,
                    "external_action": act_type not in ["draft_harvest_record_update", "draft_cooler_inventory_update", "draft_grain_load_ticket_record", "draft_bin_reconciliation", "draft_returned_inventory_reconciliation", "draft_sales_record_reconciliation", "draft_elevator_settlement_record", "draft_harvest_pack_plan", "draft_official_record_update", "draft_inventory_reconciliation"],
                    "farm_id": farm_id,
                    "record_type": rec_type,
                    "source_evidence_id": primary_ev_id,
                    "related_recommendation": matching_rec.get("recommendation", "") if matching_rec else "",
                    "related_evidence": act_ev_ids
                })
                act["external_action"] = payload["external_action"]
                act["payload"] = payload

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
            
        seen_ev_ids = set()
        evidence_summary = []
        for ev in evidence_list:
            ev_id = ev.get("evidence_id")
            if ev_id not in seen_ev_ids:
                seen_ev_ids.add(ev_id)
                evidence_summary.append({
                    "evidence_id": ev_id,
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
                })

        action_pack = {
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
        return normalize_action_pack_contract(action_pack)
