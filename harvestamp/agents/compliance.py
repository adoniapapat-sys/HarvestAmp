# harvestamp/agents/compliance.py
from typing import Any, Dict, List, Optional
from harvestamp.agents.specialists import ComplianceAgent

class ComplianceAgent(ComplianceAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Compliance Agent"

    def run(
        self,
        work_item: Dict[str, Any],
        context: Dict[str, Any],
        crop_health_watchlist: Optional[Dict[str, Any]] = None,
        harvest_events: Optional[List[Dict[str, Any]]] = None,
        yield_records: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        topic = work_item.get("topic") or context.get("topic", "")
        user_role = context.get("user_role", "")
        
        # Omit unhandled harvest topics to avoid generic filler findings
        if topic in [
            "csa_packout_check", "restaurant_fulfillment_check", "farmers_market_reconciliation",
            "sales_reconciliation_check", "elevator_delivery_draft", "grain_sale_watch",
            "harvest_shrink_tracking", "load_ticket_intake", "bin_reconciliation",
            "field_yield_summary"
        ]:
            return None

        evidence_ids = []
        if harvest_events:
            evidence_ids.extend([h["result_id"] for h in harvest_events])
        if yield_records:
            evidence_ids.extend([y["result_id"] for y in yield_records])

        if topic == "harvest_log_entry":
            # HARV-001/005 GBO compliance
            summary = "Organic compliance: organic harvest records are required for tomatoes and salad mix. Squash harvest log is in draft status, with food safety record flag set to false."
            recommendation = "Ensure complete organic lot logs and food safety sign-offs for squash before packing. Direct compliance updates remain blocked pending review."
            f = self.create_finding(
                work_item, "compliance_records", summary, recommendation, "high", "high", evidence_ids
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["food_safety_record_review"]
            }
            return f

        elif topic == "crop_insurance_caution":
            # HARV-106 PVF compliance caution
            summary = "Crop insurance and production-record compliance: field-level yields must match scale ticket weights. Yield record PVF_YLD_003 is draft with missing adjusted quantity."
            recommendation = "Review and verify all yield records against scale tickets before reporting to crop insurance or FSA. Official records are blocked pending approval."
            f = self.create_finding(
                work_item, "compliance_records", summary, recommendation, "high", "medium", evidence_ids
            )
            f["human_review"] = {
                "required": True,
                "review_type": "expert_review",
                "risk_tier": "tier_3",
                "status": "needs_expert_review",
                "reason": ["production_record_caution", "yield_record_review"],
                "recommended_reviewer": ["certified_crop_advisor", "farm_owner"],
                "approval_required_before": ["report_to_crop_insurance", "report_to_fsa"]
            }
            return f

        # Fallback to specialists.py for other topics (like weekly plans), then append harvest context
        finding = super().run(work_item, context, crop_health_watchlist)

        # Handle list or dict returns from super().run
        if isinstance(finding, list):
            for f in finding:
                self._append_weekly_compliance(f, topic, user_role, evidence_ids)
            return finding
        else:
            self._append_weekly_compliance(finding, topic, user_role, evidence_ids)
            return finding

    def _append_weekly_compliance(self, f: Dict[str, Any], topic: str, user_role: str, evidence_ids: List[str]):
        if f.get("topic") in ["compliance_general", "compliance_records"]:
            f["topic"] = "compliance_records"
            f["recommendation_type"] = "compliance_records"

        if topic == "weekly_plan_pvf":
            if user_role == "field_employee":
                f["summary"] += "\n- Field safety checks: verify food-safety logs and PPE before harvest operations."
                f["recommendation"] += "\n- Verify safety equipment availability."
            else:
                f["summary"] += "\n- Crop-insurance / production-record caution: Field yield records have official reporting obligations. Verify all yield records against load tickets."
                f["recommendation"] += "\n- Compare yield records with scale tickets before USDA/FSA reporting."
                f["evidence_ids"] = list(set(f["evidence_ids"] + evidence_ids))
        elif topic == "weekly_plan_gbo":
            if user_role in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
                f["summary"] += "\n- Organic compliance watch: sanitize wash-pack lines and verify lot labels."
                f["recommendation"] += "\n- Complete wash-pack line logs."
            else:
                f["summary"] += "\n- Organic compliance: organic harvest record and food-safety flags are active. Squash harvest log is currently draft (food safety record flag false)."
                f["recommendation"] += "\n- Reconcile squash lot numbers and verify food safety checks."
                f["evidence_ids"] = list(set(f["evidence_ids"] + evidence_ids))
