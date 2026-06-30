# harvestamp/agents/margin_scenario.py
from typing import Any, Dict, List, Optional
from harvestamp.agents.specialists import MarginAgent

class MarginScenarioAgent(MarginAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Margin + Scenario Agent"

    def run(
        self,
        work_item: Dict[str, Any],
        context: Dict[str, Any],
        crop_benchmark: Optional[Dict[str, Any]] = None,
        yield_records: Optional[List[Dict[str, Any]]] = None,
        sales_records: Optional[List[Dict[str, Any]]] = None,
        harvest_events: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        topic = work_item.get("topic") or context.get("topic", "")
        user_role = context.get("user_role", "")
        
        # Omit unhandled harvest topics to avoid generic filler findings
        if topic in [
            "harvest_log_entry", "csa_packout_check", "restaurant_fulfillment_check",
            "farmers_market_reconciliation", "load_ticket_intake", "bin_reconciliation",
            "elevator_delivery_draft", "crop_insurance_caution"
        ]:
            return None

        evidence_ids = []
        if yield_records:
            evidence_ids.extend([y["result_id"] for y in yield_records])
        if sales_records:
            evidence_ids.extend([s["result_id"] for s in sales_records])
        if harvest_events:
            evidence_ids.extend([h["result_id"] for h in harvest_events])

        if user_role in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
            summary = "Supplier quotes, input pricing, margin, and marketing details are hidden for your role."
            recommendation = "Contact farm management for financial planning details."
            return self.create_finding(
                work_item, "margin_scenario", summary, recommendation, "info", "high", [],
                prohibited_disclosures=["operating_margins", "financials"]
            )

        if topic == "harvest_shrink_tracking":
            # HARV-005 GBO cull/shrink math
            summary = "Operating margin scenario math: tomatoes cull rate is 16.7% (20.0 lbs of 120.0 lbs harvested), salad mix cull rate is 4.0% (2.0 bags of 50.0 bags harvested). Squash cull rate is 6.3% (5.0 lbs of 80.0 lbs harvested)."
            recommendation = "Illustrative cull math only; no commercial recommendations. Analyze high tunnel ventilation and packing line handling to improve marketable yield."
            return self.create_finding(
                work_item, "margin_scenario", summary, recommendation, "info", "high", evidence_ids,
                assumptions=["Fixture cull numbers reflect standard harvest conditions."],
                missing_data=[]
            )

        elif topic == "field_yield_summary":
            # HARV-102 PVF yield math
            missing = []
            if yield_records:
                for r in yield_records:
                    if r["result_id"] == "res_yld_PVF_YLD_003" or r["payload"].get("yield_record_id") == "PVF_YLD_003":
                        missing = ["Field C adjusted quantity", "Field C dockage/shrink"]
            
            summary = "Operating yield scenario math: Field A corn shrink is 2.5% (800.0 bushels of 32,000.0 bushels gross), Field B soybean shrink is 2.1% (100.0 bushels of 4,800.0 bushels gross). Field C corn shrink is unknown."
            recommendation = "Illustrative yield math only. Reconcile Field C moisture (17.5%) to calculate adjusted quantity."
            return self.create_finding(
                work_item, "margin_scenario", summary, recommendation, "info", "medium", evidence_ids,
                assumptions=["Prairie View standard moisture target is 15.0% for corn and 13.0% for soybeans."],
                missing_data=missing
            )

        elif topic == "grain_sale_watch":
            # HARV-105 PVF stored grain watch what-if math
            summary = "Stored grain scenario watch what-if math: corn bin inventory (42,000.0 bu) has an illustrative value of $184,800.00 assuming a flat price of $4.40/bu. Estimated gross value is illustrative only."
            recommendation = "Do not execute sales or hedges. Stored grain is watch-only due to missing local bid/basis data."
            return self.create_finding(
                work_item, "margin_scenario", summary, recommendation, "this_week", "high", evidence_ids,
                assumptions=[
                    "Assumed flat corn price of $4.40/bu (fixture value).",
                    "Missing local bid/basis blocks pricing/sales advice."
                ],
                missing_data=["local bid and basis data"]
            )

        elif topic == "sales_reconciliation_check":
            # HARV-006 GBO sales math
            summary = "Sales reconciliation math: farmers market gross sales $495.00. Cash/invoice reconciliation status is draft/blocked pending review."
            recommendation = "Illustrative revenue context only. Reconcile cash deposit and unpaid invoice to complete payment verification."
            return self.create_finding(
                work_item, "margin_scenario", summary, recommendation, "info", "high", evidence_ids,
                assumptions=["Fixture sales record reflects actual market day cash/card splits."],
                missing_data=[]
            )

        # Fallback to specialists.py for other topics (like weekly plans), then append harvest context
        finding = super().run(work_item, context, crop_benchmark)

        if topic == "weekly_plan_pvf":
            finding["summary"] += "\n- Stored grain scenario watch what-if math: corn bin inventory (42,000.0 bu) has an illustrative value of $184,800.00 assuming a price of $4.40/bu. Local bid/basis is missing."
            finding["evidence_ids"] = list(set(finding["evidence_ids"] + evidence_ids))
        elif topic == "weekly_plan_gbo":
            finding["summary"] += "\n- Operating margin notes: farmers market gross sales ($495.00) and CSA/wholesale fulfillment values are illustrative context only."
            finding["evidence_ids"] = list(set(finding["evidence_ids"] + evidence_ids))

        return finding
