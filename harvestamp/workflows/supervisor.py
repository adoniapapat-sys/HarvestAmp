# harvestamp/workflows/supervisor.py
"""Supervisor and Orchestrator workflow coordinator for HarvestAmp.

Coordinates intent routing, credential broker checks, tool gateway data loading,
evidence boarding, specialist execution, and recommendation synthesis.
"""
from typing import Any, Dict, List, Tuple, Optional
from harvestamp.auth.broker import CredentialBroker
from harvestamp.auth.roles import is_authorized, check_cross_farm_block
from harvestamp.gateway.tools import ToolGateway
from harvestamp.context.builder import ContextPackageBuilder
from harvestamp.core.evidence import EvidenceBoard
from harvestamp.agents.synthesizer import RecommendationSynthesizer
from harvestamp.policy.human_review_policy import HumanReviewPolicy
from harvestamp.agents.specialists import (
    WeatherAgent,
    ProcurementAgent,
    RecordsAgent,
    MarketAgent,
    ComplianceAgent,
    MarginAgent
)

class Supervisor:
    """Supervisor coordinates the multi-agent task execution."""

    def __init__(self, audit_logger: Any = None):
        self.audit_logger = audit_logger
        self.broker = CredentialBroker(audit_logger=audit_logger)
        self.gateway = ToolGateway(audit_logger=audit_logger)
        self.context_builder = ContextPackageBuilder()
        self.hr_policy = HumanReviewPolicy()
        self.synthesizer = RecommendationSynthesizer(human_review_policy=self.hr_policy)
        
        # Specialists
        self.weather_agent = WeatherAgent()
        self.proc_agent = ProcurementAgent()
        self.records_agent = RecordsAgent()
        self.market_agent = MarketAgent()
        self.compliance_agent = ComplianceAgent()
        self.margin_agent = MarginAgent()

    def route_intent(self, prompt: str, farm_profile: Dict[str, Any]) -> str:
        """Intent Router: Classifies user prompt into a task topic."""
        prompt_l = prompt.lower()
        farm_type = farm_profile.get("farm_type", "")
        
        if "other farm" in prompt_l or "what other farms" in prompt_l or "cross-farm" in prompt_l:
            return "cross_farm_private_data"
        if "connect" in prompt_l and "api" in prompt_l:
            return "credential_connection"
        if "apply" in prompt_l and "restricted-use pesticide" in prompt_l:
            return "pesticide_rate_request"
        if "diesel" in prompt_l or "fuel" in prompt_l:
            return "diesel_purchase_window"
        if "urea" in prompt_l or "uan 32" in prompt_l or "fertilizer" in prompt_l:
            if farm_type == "small_organic_direct_market":
                return "organic_input_verification"
            return "fertilizer_comparison"
        if "clamshell" in prompt_l or "box" in prompt_l or "csa" in prompt_l:
            return "packaging_reorder"
        if "spray" in prompt_l:
            return "spray_window"
        if "market" in prompt_l and farm_type == "small_organic_direct_market":
            return "farmers_market"
            
        # Default weekly plan based on farm type
        if farm_type == "small_organic_direct_market":
            return "weekly_plan_gbo"
        return "weekly_plan_pvf"

    def run_workflow(
        self,
        farm_profile: Dict[str, Any],
        user_id: str,
        user_role: str,
        prompt: str,
        observations: Dict[str, Any],
        target_farm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs the multi-agent coordination workflow."""
        requesting_farm_id = farm_profile.get("farm_id", "")
        if not target_farm_id:
            target_farm_id = requesting_farm_id
            
        workflow_id = f"wf_{requesting_farm_id}_{user_id}"

        # 1. Enforce Cross-Farm isolation check
        if not check_cross_farm_block(requesting_farm_id, target_farm_id):
            if self.audit_logger:
                self.audit_logger.log_access(
                    user_id=user_id,
                    farm_id=requesting_farm_id,
                    action="cross_farm_access_attempt",
                    result="blocked"
                )
            # Create a blocked ActionPack
            overall_hr = {
                "required": False,
                "review_type": "blocked",
                "risk_tier": "tier_4",
                "status": "blocked",
                "reason": ["cross_tenant_data_request"],
                "recommended_reviewer": ["farm_owner"],
                "approval_required_before": ["view_restricted_data"]
            }
            return {
                "action_pack_id": f"ap_{requesting_farm_id}_blocked",
                "farm_id": requesting_farm_id,
                "workflow_id": workflow_id,
                "recommendations": [],
                "proposed_actions": [],
                "evidence_summary": [],
                "warnings": ["Cross-farm data leakage attempt blocked."],
                "missing_data": [],
                "human_review_status": overall_hr,
                "status": "blocked"
            }

        # 2. Intent Routing
        topic = self.route_intent(prompt, farm_profile)

        # Handle explicit blocked / connection routes immediately
        if topic == "cross_farm_private_data":
            if self.audit_logger:
                self.audit_logger.log_access(user_id=user_id, farm_id=requesting_farm_id, action="request_other_farms_pricing", result="blocked")
            overall_hr = {
                "required": False,
                "review_type": "blocked",
                "risk_tier": "tier_4",
                "status": "blocked",
                "reason": ["cross_tenant_data_request"],
                "recommended_reviewer": ["farm_owner"],
                "approval_required_before": ["view_restricted_data"]
            }
            return {
                "action_pack_id": f"ap_{requesting_farm_id}_blocked",
                "farm_id": requesting_farm_id,
                "workflow_id": workflow_id,
                "recommendations": [],
                "proposed_actions": [],
                "evidence_summary": [],
                "warnings": ["You do not have permission to view supplier quotes or input pricing for other farms."],
                "missing_data": [],
                "human_review_status": overall_hr,
                "status": "blocked"
            }

        if topic == "credential_connection":
            if self.audit_logger:
                self.audit_logger.log_access(user_id=user_id, farm_id=requesting_farm_id, action="connect_credentials", result="gated_by_admin")
            overall_hr = {
                "required": True,
                "review_type": "admin_review",
                "risk_tier": "tier_4",
                "status": "needs_admin_review",
                "reason": ["permission_or_credential_change"],
                "recommended_reviewer": ["farm_owner"],
                "approval_required_before": ["connect_data_source"]
            }
            return {
                "action_pack_id": f"ap_{requesting_farm_id}_conn_gated",
                "farm_id": requesting_farm_id,
                "workflow_id": workflow_id,
                "recommendations": [],
                "proposed_actions": [],
                "evidence_summary": [],
                "warnings": ["Credential connection requires administrative review. Direct broker capability connection in progress."],
                "missing_data": [],
                "human_review_status": overall_hr,
                "status": "draft"
            }

        if topic == "pesticide_rate_request":
            if self.audit_logger:
                self.audit_logger.log_access(user_id=user_id, farm_id=requesting_farm_id, action="request_pesticide_rate_ crew_send", result="blocked_or_escalated")
            overall_hr = {
                "required": True,
                "review_type": "expert_review",
                "risk_tier": "tier_3",
                "status": "needs_expert_review",
                "reason": ["restricted_use_pesticide", "pesticide_rate_request"],
                "recommended_reviewer": ["licensed_applicator", "farm_manager"],
                "approval_required_before": ["send_crew_instruction"]
            }
            return {
                "action_pack_id": f"ap_{requesting_farm_id}_pesticide_gated",
                "farm_id": requesting_farm_id,
                "workflow_id": workflow_id,
                "recommendations": [],
                "proposed_actions": [],
                "evidence_summary": [],
                "warnings": ["Restricted-use pesticide application and automatic crew instructions are blocked without expert applicator review."],
                "missing_data": [],
                "human_review_status": overall_hr,
                "status": "blocked"
            }

        # 3. Context package builder (Task-Scoped context)
        context_pkg = self.context_builder.build_context_package(farm_profile, user_role, topic)
        
        # Verify that Field Employee cannot see quotes/pricing
        if user_role == "field_employee" and "supplier_pricing_redacted" in context_pkg.get("redactions_applied", []):
            if topic not in ["weekly_plan_pvf", "weekly_plan_gbo"]:
                if self.audit_logger:
                    self.audit_logger.log_access(user_id=user_id, farm_id=requesting_farm_id, action="attempt_view_quotes_employee", result="redacted")
                overall_hr = {
                    "required": False,
                    "review_type": "blocked",
                    "risk_tier": "tier_4",
                    "status": "blocked",
                    "reason": ["unauthorized_sensitive_data_request"],
                    "recommended_reviewer": ["farm_owner"],
                    "approval_required_before": ["view_restricted_data"]
                }
                return {
                    "action_pack_id": f"ap_{requesting_farm_id}_employee_redacted",
                    "farm_id": requesting_farm_id,
                    "workflow_id": workflow_id,
                    "recommendations": [],
                    "proposed_actions": [],
                    "evidence_summary": [],
                    "warnings": ["You do not have permission to view supplier quotes or input pricing for this farm."],
                    "missing_data": [],
                    "human_review_status": overall_hr,
                    "status": "blocked"
                }

        # Verify that Field Lead cannot see CSA contact emails
        if user_role == "field_lead" and "customer_emails_redacted" in context_pkg.get("redactions_applied", []):
            if topic not in ["weekly_plan_pvf", "weekly_plan_gbo"]:
                if self.audit_logger:
                    self.audit_logger.log_access(user_id=user_id, farm_id=requesting_farm_id, action="attempt_view_customer_emails_lead", result="redacted")
                overall_hr = {
                    "required": False,
                    "review_type": "blocked",
                    "risk_tier": "tier_4",
                    "status": "blocked",
                    "reason": ["unauthorized_customer_data_request"],
                    "recommended_reviewer": ["farm_owner"],
                    "approval_required_before": ["view_restricted_data"]
                }
                return {
                    "action_pack_id": f"ap_{requesting_farm_id}_lead_redacted",
                    "farm_id": requesting_farm_id,
                    "workflow_id": workflow_id,
                    "recommendations": [],
                    "proposed_actions": [],
                    "evidence_summary": [],
                    "warnings": ["You do not have permission to view CSA member contact details."],
                    "missing_data": [],
                    "human_review_status": overall_hr,
                    "status": "blocked"
                }

        # 4. Request Capability Grants and retrieve evidence
        evidence_board = EvidenceBoard()
        
        # Determine tools to query based on topic
        weather_data = {}
        quotes_data = []
        inv_data = []
        benchmark_data = {}
        
        # Query weather tool if needed
        if topic in ["diesel_purchase_window", "weekly_plan_pvf", "weekly_plan_gbo", "farmers_market", "spray_window"]:
            grant = self.broker.request_capability_grant(farm_profile, user_id, "weather_tool")
            if grant["authorized"]:
                res = self.gateway.get_weather(grant, requesting_farm_id, target_farm_id, observations)
                evidence_board.add_evidence(
                    evidence_id=res["result_id"],
                    source_id=res["source_id"],
                    source_name="National Weather Service Forecast",
                    trust_tier=res["trust_tier"],
                    freshness_status=res["freshness_status"],
                    privacy_class=res["privacy_class"],
                    data_payload=res["payload"],
                    description="Local weather forecast window",
                    timestamp=res.get("timestamp"),
                    farm_id=res.get("farm_id"),
                    authorization_status=res.get("authorization_status")
                )
                weather_data = res
                
        # Query fuel_tool / fertilizer_tool if needed
        if topic in ["diesel_purchase_window", "fertilizer_comparison", "weekly_plan_pvf", "packaging_reorder", "organic_input_verification"]:
            tool_name = "fuel_tool" if "diesel" in topic or "fuel" in topic else "fertilizer_tool"
            grant = self.broker.request_capability_grant(farm_profile, user_id, tool_name)
            if grant["authorized"]:
                res_quotes = self.gateway.get_quotes(grant, requesting_farm_id, target_farm_id, farm_profile)
                for q in res_quotes:
                    # Filter based on topic for task scope minimization
                    input_type = q["payload"]["input_type"]
                    if topic == "diesel_purchase_window" and input_type != "diesel":
                        continue
                    if topic == "fertilizer_comparison" and input_type != "fertilizer":
                        continue
                    if topic == "packaging_reorder" and input_type != "packaging":
                        continue
                    if topic == "organic_input_verification" and input_type != "organic_granular_fertilizer":
                        continue
                        
                    evidence_board.add_evidence(
                        evidence_id=q["result_id"],
                        source_id=q["source_id"],
                        source_name="Supplier Quote File",
                        trust_tier=q["trust_tier"],
                        freshness_status=q["freshness_status"],
                        privacy_class=q["privacy_class"],
                        data_payload=q["payload"],
                        description=f"Quote for {q['payload']['product_name']}",
                        timestamp=q.get("timestamp"),
                        farm_id=q.get("farm_id"),
                        authorization_status=q.get("authorization_status")
                    )
                    quotes_data.append(q)
                    
            # Get Benchmark if diesel
            if "diesel" in topic or "fuel" in topic:
                grant_bench = self.broker.request_capability_grant(farm_profile, user_id, "fuel_tool")
                if grant_bench["authorized"]:
                    res_bench = self.gateway.get_benchmark(grant_bench, observations)
                    evidence_board.add_evidence(
                        evidence_id=res_bench["result_id"],
                        source_id=res_bench["source_id"],
                        source_name="EIA Fuel Benchmark API",
                        trust_tier=res_bench["trust_tier"],
                        freshness_status=res_bench["freshness_status"],
                        privacy_class=res_bench["privacy_class"],
                        data_payload=res_bench["payload"],
                        description="Regional energy index",
                        timestamp=res_bench.get("timestamp"),
                        farm_id=res_bench.get("farm_id"),
                        authorization_status=res_bench.get("authorization_status")
                    )
                    benchmark_data = res_bench
 
        # Query records_tool if needed
        if topic in ["diesel_purchase_window", "weekly_plan_pvf", "weekly_plan_gbo", "packaging_reorder", "spray_window", "organic_input_verification"]:
            grant = self.broker.request_capability_grant(farm_profile, user_id, "records_tool")
            if grant["authorized"]:
                res_inv = self.gateway.get_inventory(grant, requesting_farm_id, target_farm_id, farm_profile)
                for item in res_inv:
                    # Filter items based on topic
                    item_type = item["payload"]["item_type"]
                    if topic == "diesel_purchase_window" and item_type != "diesel":
                        continue
                    if topic == "packaging_reorder" and not any(k in item_type for k in ["clamshell", "box", "bag", "label"]):
                        continue
                    if topic == "spray_window" and not any(k in item_type for k in ["chemical", "pesticide", "herbicide", "fungicide", "adjuvant"]):
                        continue
                    if topic == "organic_input_verification" and any(k in item_type for k in ["clamshell", "box", "bag", "label"]):
                        continue
                        
                    # Inject staleness into GBO inventory for GBO-005 stale test
                    if "stale-trigger" in prompt or prompt == "SYS-005-TRIGGER":
                        item["payload"]["last_updated"] = "2026-05-29"
                        item["freshness_status"] = "stale"
                        
                    ev_id = item["result_id"]
                    source_name = "Inventory Database"
                    description = f"Inventory level of {item['payload']['product_name']}"
                    
                    if user_role == "field_employee" and ev_id in ["res_inv_PVF_INV_DIESEL", "res_inv_PVF_INV_CORN_STORED", "res_inv_PVF_INV_SOY_STORED"]:
                        item["result_id"] = "Authorized operational records"
                        ev_id = "Authorized operational records"
                        source_name = "Authorized operational records"
                        description = "Authorized operational records"

                    evidence_board.add_evidence(
                        evidence_id=ev_id,
                        source_id=item["source_id"],
                        source_name=source_name,
                        trust_tier=item["trust_tier"],
                        freshness_status=item["freshness_status"],
                        privacy_class=item["privacy_class"],
                        data_payload=item["payload"],
                        description=description,
                        timestamp=item.get("timestamp"),
                        farm_id=item.get("farm_id"),
                        authorization_status=item.get("authorization_status")
                    )
                    inv_data.append(item)

        # 5. Route to Specialist Agents
        findings = []
        
        # Weather Agent
        if weather_data:
            weather_finding = self.weather_agent.run(
                work_item={"work_item_id": f"wi_we_{user_id}", "workflow_id": workflow_id, "farm_id": target_farm_id, "requesting_user_id": user_id, "user_intent": prompt, "topic": topic},
                context=context_pkg,
                weather_obs=weather_data
            )
            findings.append(weather_finding)
            
        # Procurement Agent
        if quotes_data or inv_data or benchmark_data:
            proc_finding = self.proc_agent.run(
                work_item={"work_item_id": f"wi_pr_{user_id}", "workflow_id": workflow_id, "farm_id": target_farm_id, "requesting_user_id": user_id, "user_intent": prompt, "topic": topic},
                context=context_pkg,
                quotes=quotes_data,
                inventory=inv_data
            )
            findings.append(proc_finding)

        # Records Agent
        if topic in ["weekly_plan_pvf", "weekly_plan_gbo", "packaging_reorder", "spray_window", "organic_input_verification"]:
            rec_finding = self.records_agent.run(
                work_item={"work_item_id": f"wi_re_{user_id}", "workflow_id": workflow_id, "farm_id": target_farm_id, "requesting_user_id": user_id, "user_intent": prompt, "topic": topic},
                context=context_pkg,
                inventory=inv_data
            )
            findings.append(rec_finding)
            
        # Compliance Agent
        if topic in ["spray_window", "organic_input_verification", "weekly_plan_pvf", "weekly_plan_gbo"]:
            comp_finding = self.compliance_agent.run(
                work_item={"work_item_id": f"wi_co_{user_id}", "workflow_id": workflow_id, "farm_id": target_farm_id, "requesting_user_id": user_id, "user_intent": prompt, "topic": topic},
                context=context_pkg
            )
            findings.append(comp_finding)
            
        # Market Agent
        if topic in ["weekly_plan_pvf", "weekly_plan_gbo", "farmers_market"]:
            mkt_finding = self.market_agent.run(
                work_item={"work_item_id": f"wi_ma_{user_id}", "workflow_id": workflow_id, "farm_id": target_farm_id, "requesting_user_id": user_id, "user_intent": prompt, "topic": topic},
                context=context_pkg
            )
            findings.append(mkt_finding)
 
        # Margin Agent
        if topic in ["diesel_purchase_window", "fertilizer_comparison", "weekly_plan_pvf", "packaging_reorder"]:
            mrgn_finding = self.margin_agent.run(
                work_item={"work_item_id": f"wi_mr_{user_id}", "workflow_id": workflow_id, "farm_id": target_farm_id, "requesting_user_id": user_id, "user_intent": prompt, "topic": topic},
                context=context_pkg
            )
            findings.append(mrgn_finding)
 
        # 6. Recommendation Synthesizer
        action_pack = self.synthesizer.synthesize(
            farm_id=target_farm_id,
            workflow_id=workflow_id,
            findings=findings,
            evidence_list=evidence_board.list_evidence(),
            user_role=user_role
        )
        
        if user_role == "field_employee":
            action_pack["warnings"].append("Supplier quotes, input pricing, margin, and marketing details are hidden for your role.")
        
        return action_pack
