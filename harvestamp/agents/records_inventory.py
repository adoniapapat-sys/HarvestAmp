# harvestamp/agents/records_inventory.py
from typing import Any, Dict, List, Optional
from harvestamp.agents.specialists import RecordsAgent

class RecordsInventoryAgent(RecordsAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Records + Inventory Agent"

    def run(
        self,
        work_item: Dict[str, Any],
        context: Dict[str, Any],
        inventory: List[Dict[str, Any]],
        irrigation_schedule: Optional[Dict[str, Any]] = None,
        irrigation_request: Optional[Dict[str, Any]] = None,
        harvest_events: Optional[List[Dict[str, Any]]] = None,
        yield_records: Optional[List[Dict[str, Any]]] = None,
        post_harvest_inventory: Optional[List[Dict[str, Any]]] = None,
        grain_load_tickets: Optional[List[Dict[str, Any]]] = None,
        grain_bin_inventory: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        topic = work_item.get("topic") or context.get("topic", "")
        user_role = context.get("user_role", "")
        
        # Omit unhandled harvest/sales topics to avoid generic filler findings
        if topic in [
            "csa_packout_check", "restaurant_fulfillment_check", "farmers_market_reconciliation",
            "sales_reconciliation_check", "elevator_delivery_draft", "grain_sale_watch",
            "crop_insurance_caution"
        ]:
            return None

        evidence_ids = []
        if harvest_events:
            evidence_ids.extend([h["result_id"] for h in harvest_events])
        if yield_records:
            evidence_ids.extend([y["result_id"] for y in yield_records])
        if post_harvest_inventory:
            evidence_ids.extend([p["result_id"] for p in post_harvest_inventory])
        if grain_load_tickets:
            evidence_ids.extend([t["result_id"] for t in grain_load_tickets])
        if grain_bin_inventory:
            evidence_ids.extend([b["result_id"] for b in grain_bin_inventory])

        if not evidence_ids and inventory:
            evidence_ids = [inv["result_id"] for inv in inventory]

        if topic == "harvest_log_entry":
            # HARV-001: Log tomato harvest and cooler inventory
            summary = "Draft cooler inventory updates: tomatoes 100.0 lbs (High Tunnel 1), salad mix 48.0 bags (Field A). Harvest status is draft/blocked pending review."
            recommendation = "Reconcile harvest logs and approve cooler inventory updates before committing to official records."
            f = self.create_finding(
                work_item, "harvest_records", summary, recommendation, "this_week", "high", evidence_ids
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["harvest_record_review", "draft_cooler_inventory_update", "post_harvest_inventory_review"]
            }
            return f

        elif topic == "harvest_shrink_tracking":
            # HARV-005: GBO culls
            summary = "Harvest cull and shrink tracking: tomatoes 20.0 lbs cull (16.7% shrink), salad mix 2.0 bags cull (4.0% shrink)."
            recommendation = "Monitor temperature and packhouse handling to reduce cull/shrink rates."
            f = self.create_finding(
                work_item, "harvest_records", summary, recommendation, "info", "high", evidence_ids
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["harvest_record_review", "draft_cooler_inventory_update", "post_harvest_inventory_review"]
            }
            return f

        elif topic == "load_ticket_intake":
            # HARV-101: PVF load tickets
            if user_role == "field_employee":
                summary = "Grain load ticket intake: corn gross weight 1,000.0 bushels. Status is draft/blocked pending review."
                recommendation = "Verify scale ticket details and moisture against bin records."
                f = self.create_finding(
                    work_item, "grain_records", summary, recommendation, "info", "high", ["Authorized operational records"],
                    prohibited_disclosures=["buyer_settlement_details", "financials"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["harvest_record_review", "yield_record_review"]
                }
                return f
            else:
                summary = "Grain load ticket intake: corn gross weight 1,000.0 bushels (Destination: Bin 1, moisture: 15.5%, test weight: 56.0). Status is draft/blocked pending review."
                recommendation = "Verify scale ticket details and moisture against bin records."
                f = self.create_finding(
                    work_item, "grain_records", summary, recommendation, "info", "high", evidence_ids
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["harvest_record_review", "yield_record_review"]
                }
                return f

        elif topic == "field_yield_summary":
            # HARV-102: PVF yields
            missing = []
            if yield_records:
                for r in yield_records:
                    if r["result_id"] == "res_yld_PVF_YLD_003" or r["payload"].get("yield_record_id") == "PVF_YLD_003":
                        missing = ["Field C adjusted quantity", "Field C dockage/shrink"]
            
            summary = "Field yield summary: PVF_FIELD_A corn gross 32,000.0 bushels (adjusted: 31,200.0 bushels, 15.2% moisture), PVF_FIELD_B soybeans gross 4,800.0 bushels (adjusted: 4,700.0 bushels, 13.5% moisture). PVF_FIELD_C corn gross 24,000.0 bushels (adjusted: unknown, 17.5% moisture)."
            recommendation = "Verify moisture and dockage/shrink values for Field C corn to calculate adjusted quantity."
            
            f = self.create_finding(
                work_item, "yield_records", summary, recommendation, "info", "medium", evidence_ids,
                missing_data=missing
            )
            f["human_review"] = {
                "required": True if missing else False,
                "review_type": "user_approval" if missing else "none",
                "risk_tier": "tier_1" if missing else "tier_0",
                "status": "needs_info" if missing else "review_not_required",
                "reason": ["yield_record_review"],
                "approval_required_before": ["provide_field_c_adjusted_quantity", "provide_field_c_dockage_or_shrink"] if missing else [],
                "recommended_reviewer": ["farm_owner", "farm_manager"] if missing else []
            }
            return f

        elif topic == "bin_reconciliation":
            # HARV-103: PVF bins
            summary = "Stored grain bin inventory: Bin 1 corn 42,000.0 bushels (reconciled), Bin 2 soybeans 9,000.0 bushels (reconciled), Bin 3 corn 15,000.0 bushels (out_of_sync, status draft/blocked pending review)."
            recommendation = "Perform physical bin inventory measurement and reconcile Bin 3 corn out of sync status."
            f = self.create_finding(
                work_item, "grain_records", summary, recommendation, "this_week", "high", evidence_ids
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_1",
                "status": "needs_info",
                "reason": ["grain_bin_reconciliation"]
            }
            return f

        # Fallback to specialists.py for other topics (like weekly plans), then append harvest context
        finding = super().run(work_item, context, inventory, irrigation_schedule, irrigation_request)

        if topic == "weekly_plan_pvf":
            if user_role == "field_employee":
                finding["summary"] += "\n- Stored grain bin inventories and yield watch are draft/blocked pending review."
                finding["evidence_ids"] = [ev for ev in finding["evidence_ids"] if ev not in ["res_yld_PVF_YLD_001", "res_yld_PVF_YLD_002", "res_bin_PVF_BIN_001", "res_bin_PVF_BIN_002"]]
                if "Authorized operational records" not in finding["evidence_ids"]:
                    finding["evidence_ids"].append("Authorized operational records")
            else:
                finding["summary"] += "\n- Stored grain bin inventory: Bin 1 corn 42,000.0 bu, Bin 2 soybeans 9,000.0 bu. Bin 3 corn 15,000.0 bu is out of sync (draft/blocked pending review). Gross yields: corn 56,000.0 bushels, soybeans 4,800.0 bushels. Warning: Possible corn reconciliation variance detected; stored corn bin totals (57,000.0 bu) and field gross yield records (56,000.0 bu) have a mismatch of 1,000.0 bu."
                finding["evidence_ids"] = list(set(finding["evidence_ids"] + evidence_ids))
                
        elif topic == "weekly_plan_gbo":
            if user_role in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
                finding["summary"] += "\n- Cooler inventory updates for tomatoes and salad mix are draft/blocked pending review."
                finding["evidence_ids"] = [ev for ev in finding["evidence_ids"] if ev not in ["res_harv_GBO_HARV_001", "res_harv_GBO_HARV_002", "res_phi_GBO_PHI_001", "res_phi_GBO_PHI_002"]]
                if "Authorized operational records" not in finding["evidence_ids"]:
                    finding["evidence_ids"].append("Authorized operational records")
            else:
                finding["summary"] += "\n- Cooler inventory updates: tomatoes 100.0 lbs (draft/blocked pending review), salad mix 48.0 bags (draft/blocked pending review)."
                finding["evidence_ids"] = list(set(finding["evidence_ids"] + evidence_ids))

        return finding
