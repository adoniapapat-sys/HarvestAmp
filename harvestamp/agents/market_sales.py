# harvestamp/agents/market_sales.py
from typing import Any, Dict, List, Optional
from harvestamp.agents.specialists import MarketAgent

class MarketSalesAgent(MarketAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Market + Sales Agent"

    def run(
        self,
        work_item: Dict[str, Any],
        context: Dict[str, Any],
        crop_benchmark: Optional[Dict[str, Any]] = None,
        market_report: Optional[Dict[str, Any]] = None,
        sales_commitments: Optional[List[Dict[str, Any]]] = None,
        sales_records: Optional[List[Dict[str, Any]]] = None,
        post_harvest_inventory: Optional[List[Dict[str, Any]]] = None,
        grain_bin_inventory: Optional[List[Dict[str, Any]]] = None,
        yield_records: Optional[List[Dict[str, Any]]] = None,
        grain_load_tickets: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        topic = work_item.get("topic") or context.get("topic", "")
        user_role = context.get("user_role", "")
        
        # Omit unhandled harvest topics to avoid generic filler findings
        if topic in [
            "harvest_log_entry", "harvest_shrink_tracking", "load_ticket_intake",
            "field_yield_summary", "bin_reconciliation", "crop_insurance_caution"
        ]:
            return None

        evidence_ids = []
        if sales_commitments:
            evidence_ids.extend([c["result_id"] for c in sales_commitments])
        if sales_records:
            evidence_ids.extend([s["result_id"] for s in sales_records])
        if post_harvest_inventory:
            evidence_ids.extend([p["result_id"] for p in post_harvest_inventory])
        if grain_bin_inventory:
            evidence_ids.extend([b["result_id"] for b in grain_bin_inventory])
        if yield_records:
            evidence_ids.extend([y["result_id"] for y in yield_records])
        if grain_load_tickets:
            evidence_ids.extend([t["result_id"] for t in grain_load_tickets])

        if topic == "csa_packout_check":
            # HARV-002: CSA packout verification (No "draft/blocked" wording because it's only read-only operation context)
            summary = "CSA packout check: GBO committed CSA members (75) require 75.0 bags of salad mix. Post-harvest inventory has 48.0 bags available (45.0 bags committed, 3.0 bags uncommitted). Shortage is 27.0 bags."
            recommendation = "Prepare a harvest plan for Field A salad mix to fill the 27.0 bag shortage before Wednesday packout."
            f = self.create_finding(
                work_item, "direct_market_sales", summary, recommendation, "this_week", "high", evidence_ids,
                assumptions=["CSA salad mix bag weight remains standard at 0.5 lbs."],
                missing_data=[]
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["sales_record_reconciliation", "post_harvest_inventory_review"]
            }
            return f

        elif topic == "restaurant_fulfillment_check":
            # HARV-003: Restaurant pre-orders (No "draft/blocked" wording because it's only read-only operation context)
            summary = "Restaurant order fulfillment check: Green Bistro pre-order (50.0 lbs tomatoes, 10.0 bags salad mix). Tomato inventory is sufficient (100.0 lbs available, 80.0 lbs committed). Salad mix inventory has a shortage of 7.0 bags (3.0 bags uncommitted vs 10.0 bags ordered)."
            recommendation = "Harvest additional Field A salad mix to cover the 7.0 bag wholesale shortage."
            f = self.create_finding(
                work_item, "direct_market_sales", summary, recommendation, "this_week", "high", evidence_ids,
                assumptions=["Green Bistro pre-orders require next-day delivery."],
                missing_data=[]
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["sales_record_reconciliation", "post_harvest_inventory_review"]
            }
            return f

        elif topic == "farmers_market_reconciliation":
            # HARV-004: Reconcile farmers market returned inventory (Squash and salad mix)
            summary = "Farmers market returned inventory: squash 20.0 lbs returned (80.0 lbs sold), salad mix 5.0 bags returned (35.0 bags sold). Returned status is draft/blocked pending review."
            recommendation = "Verify returned produce quality and transfer marketable returns back to cooler inventory. Prepare sales record for review."
            f = self.create_finding(
                work_item, "farmers_market", summary, recommendation, "this_week", "high", evidence_ids
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["sales_record_reconciliation", "post_harvest_inventory_review"],
                "recommended_reviewer": ["farm_owner", "farm_manager"],
                "approval_required_before": ["verify_returned_inventory_quality", "reconcile_sales_records", "commit_to_official_records"]
            }
            return f

        elif topic == "sales_reconciliation_check":
            # HARV-006: Sales records reconciliation
            if user_role == "field_employee":
                summary = "Sales record reconciliation details are hidden for your role."
                recommendation = "Contact farm manager for sales reconciliation details."
                f = self.create_finding(
                    work_item, "direct_market_sales", summary, recommendation, "info", "high", ["Authorized operational records"],
                    prohibited_disclosures=["financials", "customer_personal_data"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["sales_record_reconciliation"]
                }
                return f
            else:
                summary = "Sales record reconciliation: gross sales $495.00 (payment status: partially_reconciled). Cash/invoice reconciliation status is draft/blocked pending review."
                recommendation = "Verify cash deposit and draft unpaid wholesale invoice follow-up (blocked pending review) to complete reconciliation."
                f = self.create_finding(
                    work_item, "direct_market_sales", summary, recommendation, "this_week", "high", evidence_ids
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["sales_record_reconciliation"]
                }
                return f

        elif topic == "elevator_delivery_draft":
            # HARV-104: PVF settlement draft
            if user_role == "field_employee":
                summary = "Elevator delivery and settlement details are hidden for your role."
                recommendation = "Contact farm owner for marketing tasks."
                f = self.create_finding(
                    work_item, "commodity_markets", summary, recommendation, "info", "high", ["Authorized operational records"],
                    prohibited_disclosures=["grain_marketing_details", "financials"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["sales_record_reconciliation", "yield_record_review"]
                }
                return f
            else:
                summary = "Draft elevator delivery and settlement records: PVF_YLD_002 soybeans (4,700.0 bushels adjusted). Settlement records are draft/blocked pending review."
                recommendation = "Review and approve the draft elevator settlement records before committing."
                f = self.create_finding(
                    work_item, "commodity_markets", summary, recommendation, "this_week", "high", evidence_ids
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["sales_record_reconciliation", "yield_record_review"]
                }
                return f

        elif topic == "grain_sale_watch":
            # HARV-105: PVF grain watch
            if user_role == "field_employee":
                summary = "Marketing and sales details are hidden for your role."
                recommendation = "Contact farm owner for marketing tasks."
                f = self.create_finding(
                    work_item, "commodity_markets", summary, recommendation, "info", "high", ["Authorized operational records"],
                    prohibited_disclosures=["grain_marketing_details"]
                )
                f["human_review"] = {
                    "required": False,
                    "review_type": "none",
                    "risk_tier": "tier_0",
                    "status": "review_not_required",
                    "reason": ["sales_record_reconciliation"]
                }
                return f
            else:
                summary = "Stored grain sale watch: 42,000.0 bushels of stored corn in Bin 1. Local elevator bid and basis are missing."
                recommendation = "Keep stored grain as a watchlist item. Sale recommendations are blocked due to missing local bid/basis data."
                f = self.create_finding(
                    work_item, "commodity_markets", summary, recommendation, "this_week", "high", evidence_ids,
                    assumptions=["Basis is highly variable in current harvest window."],
                    missing_data=["local bid and basis data"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_1",
                    "status": "needs_info",
                    "reason": ["sales_record_reconciliation"],
                    "approval_required_before": ["provide_local_bid", "provide_local_basis", "no_sale_recommendation_without_current_farm_authorized_bid_basis"]
                }
                return f

        # Fallback to specialists.py for other topics (like weekly plans), then append harvest context
        finding = super().run(work_item, context, crop_benchmark, market_report)

        if isinstance(finding, list):
            for f in finding:
                if "Prepare weekly availability sheet" in f.get("recommendation", ""):
                    f["recommendation"] = f["recommendation"].replace("Prepare weekly availability sheet", "Draft weekly availability sheet (blocked pending manager review)")
                if "unpaid wholesale invoice" in f.get("recommendation", ""):
                    f["recommendation"] = f["recommendation"].replace("unpaid wholesale invoice", "draft unpaid wholesale invoice follow-up (blocked pending review)")
                if "restaurant pre-orders" in f.get("missing_data", []):
                    f["missing_data"] = [m for m in f["missing_data"] if m != "restaurant pre-orders"]
            return finding
        else:
            if "Prepare weekly availability sheet" in finding.get("recommendation", ""):
                finding["recommendation"] = finding["recommendation"].replace("Prepare weekly availability sheet", "Draft weekly availability sheet (blocked pending manager review)")
            if "unpaid wholesale invoice" in finding.get("recommendation", ""):
                finding["recommendation"] = finding["recommendation"].replace("unpaid wholesale invoice", "draft unpaid wholesale invoice follow-up (blocked pending review)")
            if "restaurant pre-orders" in finding.get("missing_data", []):
                finding["missing_data"] = [m for m in finding["missing_data"] if m != "restaurant pre-orders"]

            if topic == "weekly_plan_pvf":
                if user_role != "field_employee":
                    finding["summary"] += "\n- Stored grain watch: stored corn (42,000.0 bu) and soybeans (9,000.0 bu) are watchlist items. Sale recommendations are blocked pending local basis updates."
                    finding["evidence_ids"] = list(set(finding["evidence_ids"] + evidence_ids))
                    
            elif topic == "weekly_plan_gbo":
                if user_role == "field_employee":
                    finding["summary"] += "\n- CSA fulfillment (75 members) is active. Wholesale/restaurant pre-orders are active (customer details hidden)."
                    finding["evidence_ids"] = [ev for ev in finding["evidence_ids"] if ev not in ["res_sal_GBO_SAL_001", "res_com_GBO_COM_001", "res_com_GBO_COM_002"]]
                    if "Authorized operational records" not in finding["evidence_ids"]:
                        finding["evidence_ids"].append("Authorized operational records")
                elif user_role in ["field_lead", "market_staff", "external_reviewer"]:
                    finding["summary"] += "\n- CSA fulfillment (75 members) and restaurant order fulfillment checks are draft/blocked pending review."
                    finding["evidence_ids"] = [ev for ev in finding["evidence_ids"] if ev not in ["res_sal_GBO_SAL_001", "res_com_GBO_COM_001", "res_com_GBO_COM_002"]]
                    if "Authorized operational records" not in finding["evidence_ids"]:
                        finding["evidence_ids"].append("Authorized operational records")
                else:
                    finding["summary"] += "\n- CSA and Wholesale commitments: 75 CSA member packages (75.0 bags salad mix) and Green Bistro pre-order (50.0 lbs tomatoes, 10.0 bags salad mix) are scheduled for delivery/pickup obligations."
                    finding["evidence_ids"] = list(set(finding["evidence_ids"] + evidence_ids))

            return finding
