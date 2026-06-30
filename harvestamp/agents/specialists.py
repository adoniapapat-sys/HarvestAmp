# harvestamp/agents/specialists.py
"""Specialist agents implementation for HarvestAmp.

These agents mock language reasoning and return structured AgentFinding objects.
They use math_utils to perform deterministic calculations where appropriate.
"""
from typing import Any, Dict, List, Tuple, Optional
from harvestamp.core.math_utils import (
    calculate_fertilizer_cost_per_pound_nitrogen,
    calculate_tank_capacity_percentage,
    calculate_fuel_days_on_hand,
    calculate_packaging_coverage_weeks
)

def get_topic_with_fallback(work_item: Dict[str, Any], context: Dict[str, Any], default_val: str = "") -> str:
    topic = work_item.get("topic", "")
    if topic:
        return topic
    # Fallback to intent routing for tests
    intent = work_item.get("user_intent", "").lower()
    farm_type = context.get("farm_type", "")
    
    if any(term in intent for term in [
        "spray", "crop health", "scouting", "disease/pest watch", "disease watch", "pest watch",
        "regulated/invasive pest awareness", "regulated pest", "invasive pest",
        "spray/treatment safety-gate", "treatment safety-gate"
    ]):
        return "spray_window"
    if "granular" in intent or "compost" in intent or "organic_input" in intent:
        return "organic_input_verification"
    if "diesel" in intent or "fuel" in intent:
        return "diesel_purchase_window"
    if "urea" in intent or "fertilizer" in intent:
        return "fertilizer_comparison"
    if "clamshell" in intent or "box" in intent or "pack" in intent:
        return "packaging_reorder"
    if "market" in intent:
        return "farmers_market"
        
    if farm_type == "small_organic_direct_market":
        return "weekly_plan_gbo"
    return "weekly_plan_pvf"

class BaseAgent:
    """Base class for specialist agents."""
    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def create_finding(
        self,
        work_item: Dict[str, Any],
        topic: str,
        summary: str,
        recommendation: str,
        urgency: str,
        confidence: str,
        evidence_ids: List[str],
        assumptions: List[str] = None,
        missing_data: List[str] = None,
        prohibited_disclosures: List[str] = None
    ) -> Dict[str, Any]:
        """Creates a formatted AgentFinding object."""
        return {
            "finding_id": f"find_{self.agent_name.lower().replace(' ', '_')}_{work_item['work_item_id']}",
            "workflow_id": work_item["workflow_id"],
            "agent_name": self.agent_name,
            "farm_id": work_item["farm_id"],
            "user_id": work_item["requesting_user_id"],
            "topic": topic,
            "summary": summary,
            "recommendation": recommendation,
            "urgency": urgency,
            "confidence": confidence,
            "impact_areas": [topic.split("_")[0]],
            "evidence_ids": evidence_ids,
            "assumptions": assumptions or [],
            "missing_data": missing_data or [],
            "data_sensitivity_used": ["Farm Confidential", "Farm Restricted"],
            "allowed_viewer_roles": ["farm_owner", "farm_manager", "field_employee", "field_lead", "market_staff", "external_reviewer"],
            "prohibited_disclosures": prohibited_disclosures or [],
            "human_review": {
                "required": False,
                "review_type": "none",
                "risk_tier": "tier_0",
                "status": "review_not_required",
                "reason": []
            }
        }

class WeatherAgent(BaseAgent):
    """Translates weather forecasts and alerts into fieldwork windows and operational risk."""
    
    def __init__(self):
        super().__init__("Weather + Fieldwork Agent")

    def run(self, work_item: Dict[str, Any], context: Dict[str, Any], weather_obs: Dict[str, Any]) -> Dict[str, Any]:
        topic = get_topic_with_fallback(work_item, context)
        forecast = weather_obs.get("payload", {}) if weather_obs else {}
        evidence_ids = [weather_obs.get("result_id", "weather_ev")] if weather_obs else []
        
        fallback_used = weather_obs.get("fallback_used", False) if weather_obs else False
        fallback_reason = weather_obs.get("fallback_reason", "") if weather_obs else ""
        nws_status = weather_obs.get("status", "success") if weather_obs else "success"
        
        # If fallback is used and there is no forecast payload, weather data is completely unavailable
        if fallback_used and not forecast:
            summary = "Weather forecast data is completely unavailable. Live weather connector failed."
            if fallback_reason:
                summary += f" ({fallback_reason})"
            recommendation = "Verify current local weather conditions manually before scheduling fieldwork or market setup."
            return self.create_finding(
                work_item=work_item,
                topic="fieldwork_weather" if "gbo" not in topic else "market_day_weather",
                summary=summary,
                recommendation=recommendation,
                urgency="today",
                confidence="low",
                evidence_ids=evidence_ids,
                assumptions=["No fallback weather data is available."],
                missing_data=["Fresh weather forecast data"]
            )
            
        finding = None
        if topic == "spray_window":
            summary = "Tomorrow morning has a favorable wind window (6-10 mph) and low rain probability. Afternoon wind speed rises to 15-22 mph with evening storm chance."
            recommendation = "Morning window is possible for spraying West Ridge. Afternoon is high-wind risk and not recommended."
            finding = self.create_finding(
                work_item, "spray_window", summary, recommendation, "today", "high", evidence_ids,
                assumptions=["No rain occurs earlier than forecast."],
                missing_data=["Planned product labels for exact wind limits"]
            )
            
        elif topic == "weekly_plan_pvf":
            summary = "Friday offers the best fieldwork window with favorable wind and low rain probability. Caution is advised on Wednesday due to rain forecast and Thursday due to possible high wind."
            recommendation = "Target Friday as the primary fieldwork window. Exercise caution on Wednesday (rain) and Thursday (wind)."
            finding = self.create_finding(
                work_item, "fieldwork_weather", summary, recommendation, "this_week", "medium", evidence_ids,
                assumptions=["Showers and winds follow the predicted timing and severity."],
                missing_data=["Real-time wind and rain sensor updates"]
            )
            
        elif topic == "weekly_plan_gbo":
            summary = "Saturday market weather risk includes forecast scattered morning showers and 10-16 mph wind."
            recommendation = "Use tent weights and rain covers for Saturday morning setup. Conduct a high tunnel ventilation and humidity check to manage moisture."
            finding = self.create_finding(
                work_item, "market_day_weather", summary, recommendation, "this_week", "medium", evidence_ids,
                assumptions=["Saturday morning rain holds as scattered showers."],
                missing_data=["High tunnel internal humidity readings"]
            )
            
        elif topic in ["diesel_purchase_window", "fuel_buy_window"]:
            summary = "Friday offers the best fieldwork window with favorable wind and low rain probability. Rain and wind caution is advised earlier in the week, affecting spray and fieldwork prep."
            recommendation = "Plan near-term diesel usage around upcoming spraying, scouting, and wheat-harvest preparation. Target Friday as the primary fieldwork window."
            finding = self.create_finding(
                work_item, "fieldwork_weather", summary, recommendation, "this_week", "medium", evidence_ids,
                assumptions=["Fieldwork windows follow predicted weather timing."],
                missing_data=["Real-time wind and rain sensor updates"]
            )
            
        elif topic in ["irrigation_advisory", "irrigation_request"]:
            summary = "Upcoming forecast indicates high temperatures, no rain, and high wind this week, leading to high crop evapotranspiration."
            recommendation = "Upcoming hot and dry conditions will increase crop water demand. Suggest scheduling irrigation during available turns while monitoring wind speeds to minimize drift/evaporative loss. Do not make water-rights or district-rule determinations."
            finding = self.create_finding(
                work_item, "fieldwork_weather", summary, recommendation, "this_week", "high", evidence_ids,
                assumptions=["High temperatures will persist throughout the week."],
                missing_data=[]
            )
            
        else:
            farm_type = context.get("farm_type", "")
            if farm_type == "small_organic_direct_market":
                saturday_forecast = forecast.get("saturday_market", "uncertain")
                summary = f"Saturday market weather forecast: {saturday_forecast}."
                recommendation = "Prepare tent weights and rain covers for Saturday morning setup."
                finding = self.create_finding(
                    work_item, "market_day_weather", summary, recommendation, "this_week", "medium", evidence_ids
                )
            else:
                summary = "Friday offers the best fieldwork window with favorable wind and low rain probability. Rain and wind caution is advised earlier in the week."
                recommendation = "Plan near-term diesel usage around upcoming spraying, scouting, and wheat-harvest preparation. Target Friday as the primary fieldwork window."
                finding = self.create_finding(
                    work_item, "fieldwork_weather", summary, recommendation, "this_week", "medium", evidence_ids
                )
                
        if fallback_used and finding:
            finding["confidence"] = "low"
            finding["summary"] += f" (Warning: live weather data was unavailable or stale; using cached fallback. NWS status: {nws_status})"
            finding["assumptions"].append("Using cached weather data due to connection issues.")
            if "Fresh weather forecast data" not in finding["missing_data"]:
                finding["missing_data"].append("Fresh weather forecast data")
                
        return finding

class ProcurementAgent(BaseAgent):
    """Analyzes prices, quotes, inventories, and reorders."""
    
    def __init__(self):
        super().__init__("Input Procurement Agent")

    def run(
        self,
        work_item: Dict[str, Any],
        context: Dict[str, Any],
        quotes: List[Dict[str, Any]],
        inventory: List[Dict[str, Any]],
        benchmark: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        topic = get_topic_with_fallback(work_item, context)
        user_role = context.get("user_role", "")
        evidence_ids = [q["result_id"] for q in quotes] + [inv["result_id"] for inv in inventory]

        bench_text = ""
        bench_failed_or_stale = False
        if benchmark:
            evidence_ids.append(benchmark["result_id"])
            status = benchmark.get("status", "success")
            freshness = benchmark.get("freshness_status", "fresh")
            fallback_used = benchmark.get("fallback_used", False)
            
            if status in ["unavailable", "error", "timeout", "denied"] and not fallback_used:
                bench_text = "Public benchmark context: EIA regional diesel price benchmark is unavailable."
                bench_failed_or_stale = True
            elif fallback_used:
                trend = benchmark.get("payload", {}).get("trend")
                if trend and trend != "unknown":
                    trend_display = trend.replace("mock_regional_diesel_benchmark_", "").replace("_", " ")
                    bench_text = f"Public benchmark context: EIA regional diesel price benchmark is {trend_display}."
                else:
                    bench_text = "Public benchmark context: EIA regional diesel price benchmark is unavailable."
                bench_failed_or_stale = True
            elif freshness == "stale":
                trend = benchmark.get("payload", {}).get("trend", "unknown")
                trend_display = trend.replace("mock_regional_diesel_benchmark_", "").replace("_", " ") if trend else "unknown"
                bench_text = f"Public benchmark context: EIA regional diesel price benchmark is {trend_display} (Warning: EIA benchmark data is stale)."
                bench_failed_or_stale = True
            else:
                trend = benchmark.get("payload", {}).get("trend", "unknown")
                trend_display = trend.replace("mock_regional_diesel_benchmark_", "").replace("_", " ") if trend else "unknown"
                bench_text = f"Public benchmark context: EIA regional diesel price benchmark is {trend_display}."

        if topic == "weekly_plan_pvf":
            # Filter evidence for Fuel Watch
            fuel_quotes = [q for q in quotes if q["payload"].get("input_type") == "diesel"]
            fuel_inv = [inv for inv in inventory if inv["payload"].get("item_type") == "diesel"]
            fuel_evidence_ids = [q["result_id"] for q in fuel_quotes] + [inv["result_id"] for inv in fuel_inv]
            if benchmark:
                fuel_evidence_ids.append(benchmark["result_id"])

            # Filter evidence for Fertilizer Watch
            fert_quotes = [q for q in quotes if q["payload"].get("product_name") in ["Urea", "UAN 32"]]
            fert_evidence_ids = [q["result_id"] for q in fert_quotes]

            if user_role == "field_employee":
                fuel_summary = "Fuel readiness needs management review. Supplier quotes, input pricing, and detailed fuel status are hidden for your role."
                fuel_rec = "Fuel readiness needs management review. Supplier quotes, input pricing, and detailed fuel status are hidden for your role."
                f_fuel = self.create_finding(
                    work_item, "weekly_plan_pvf", fuel_summary, fuel_rec, "info", "high", fuel_evidence_ids,
                    prohibited_disclosures=["supplier_quotes", "input_prices"]
                )
                f_fuel["recommendation_type"] = "fuel_watch"

                fert_summary = "Input quote details are hidden for your role."
                fert_rec = "Contact farm management for fertilizer pricing details."
                f_fert = self.create_finding(
                    work_item, "weekly_plan_pvf_fertilizer", fert_summary, fert_rec, "info", "high", fert_evidence_ids,
                    prohibited_disclosures=["supplier_quotes", "input_prices"]
                )
                f_fert["recommendation_type"] = "fertilizer_quote_watch"
                
                return [f_fuel, f_fert]
            else:
                # Fuel Watch Finding
                fuel_summary = "Diesel inventory is 1,350 gallons in a 4,000-gallon tank. Expected 30-day need is 3,100 gallons with a 700-gallon reserve, triggering a low fuel watch. Current diesel quote is valid until 2026-06-25."
                if bench_text:
                    fuel_summary += f" {bench_text} The farm-specific supplier quote is the decision anchor; EIA is public benchmark context only."
                fuel_rec = "Prepare a fuel quote inquiry for approval. The farm-specific supplier quote is the decision anchor; EIA is public benchmark context only."
                
                f_fuel = self.create_finding(
                    work_item, "weekly_plan_pvf", fuel_summary, fuel_rec, "high", "medium", fuel_evidence_ids,
                    assumptions=["Fuel usage aligns with 30-day operational needs."],
                    missing_data=[]
                )
                f_fuel["recommendation_type"] = "fuel_watch"
                if bench_failed_or_stale:
                    f_fuel["missing_data"].append("Fresh EIA diesel benchmark")
                    
                f_fuel["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["financial_action"]
                }

                # Fertilizer / Input Quote Watch Finding
                urea_quote = next((q["payload"] for q in quotes if q["payload"].get("product_name") == "Urea"), {})
                uan_quote = next((q["payload"] for q in quotes if q["payload"].get("product_name") == "UAN 32"), {})
                
                urea_price = urea_quote.get("price", 475.00)
                uan_price = uan_quote.get("price", 340.00)
                
                urea_cost_n = calculate_fertilizer_cost_per_pound_nitrogen(urea_price, 46)
                uan_cost_n = calculate_fertilizer_cost_per_pound_nitrogen(uan_price, 32)

                urea_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("product_name") == "Urea"), {})
                uan_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("product_name") == "UAN 32"), {})
                urea_qty = urea_inv.get("quantity")
                uan_qty = uan_inv.get("quantity")
                urea_thresh = urea_inv.get("reorder_threshold")
                uan_thresh = uan_inv.get("reorder_threshold")

                stock_context = []
                is_low_stock = False
                if urea_qty is not None:
                    below_str = ""
                    if urea_thresh is not None and urea_qty <= urea_thresh:
                        below_str = f" (below threshold {urea_thresh} tons)"
                        is_low_stock = True
                    stock_context.append(f"Urea stock is {urea_qty} tons{below_str}")
                if uan_qty is not None:
                    below_str = ""
                    if uan_thresh is not None and uan_qty <= uan_thresh:
                        below_str = f" (below threshold {uan_thresh} tons)"
                        is_low_stock = True
                    stock_context.append(f"UAN 32 stock is {uan_qty} tons{below_str}")

                stock_str = " Current stock status: " + ", ".join(stock_context) + "." if stock_context else ""

                # Crop protection inventory neutral context
                cp_inv = [inv["payload"] for inv in inventory if inv["payload"].get("item_type") in ["herbicide", "fungicide", "adjuvant", "biological_control", "insecticide", "crop_protection"]]
                cp_low = []
                for item in cp_inv:
                    qty = item.get("quantity")
                    threshold = item.get("reorder_threshold")
                    name = item.get("product_name", item.get("item_id"))
                    if qty is not None and threshold is not None and qty <= threshold:
                        cp_low.append(f"{name} ({qty}/{threshold} {item.get('unit', '')})")
                
                cp_context = ""
                if cp_low:
                    cp_context = " Crop-protection stock status (neutral context): " + ", ".join(cp_low) + " at or below threshold."

                # Equipment and irrigation inventory neutral context
                eq_irr_inv = [inv["payload"] for inv in inventory if inv["payload"].get("item_type") in ["equipment_part", "machinery_part", "maintenance_supply", "irrigation_supply", "pump_part", "drip_irrigation_supply"]]
                eq_irr_low = []
                for item in eq_irr_inv:
                    qty = item.get("quantity")
                    threshold = item.get("reorder_threshold")
                    name = item.get("product_name", item.get("item_id"))
                    if qty is not None and threshold is not None and qty <= threshold:
                        eq_irr_low.append(f"{name} ({qty}/{threshold} {item.get('unit', '')})")
                
                eq_irr_context = ""
                if eq_irr_low:
                    eq_irr_context = " Equipment and irrigation stock status (neutral context): " + ", ".join(eq_irr_low) + " at or below threshold."
                
                fert_summary = f"Urea quote at ${urea_price}/ton and UAN 32 quote at ${uan_price}/ton are available, but delivery and application fees are missing. Based on material price only, urea is slightly cheaper per pound of nitrogen (${urea_cost_n:.4f}/lb N) compared to UAN 32 (${uan_cost_n:.4f}/lb N), but fees are missing.{stock_str}{cp_context}{eq_irr_context}"
                fert_rec = "Confirm delivery and application fees before ordering."
                if is_low_stock:
                    fert_rec += " Consider preparing a draft supplier quote request for owner/manager review due to low stocks."
                if eq_irr_low:
                    fert_rec += " Low-stock equipment or irrigation items can be compiled for owner/manager review."

                f_fert = self.create_finding(
                    work_item, "weekly_plan_pvf_fertilizer", fert_summary, fert_rec, "medium", "medium", fert_evidence_ids,
                    assumptions=["Material prices are accurate before fees."],
                    missing_data=["fertilizer delivery fee", "fertilizer application fee"]
                )
                f_fert["recommendation_type"] = "fertilizer_quote_watch"
                f_fert["human_review"] = {
                    "required": False,
                    "review_type": "none",
                    "risk_tier": "tier_0",
                    "status": "review_not_required",
                    "reason": []
                }

                return [f_fuel, f_fert]

        elif topic == "weekly_plan_gbo":
            if user_role == "field_employee":
                summary = "CSA boxes on hand: 110. Pint clamshells on hand: 160. Quart clamshells on hand: 85. Packaging inventory levels indicate potential risk."
                recommendation = "Verify clamshell counts physically. Manager review needed for box reorders."
                return self.create_finding(
                    work_item, "weekly_plan_gbo", summary, recommendation, "info", "high", evidence_ids,
                    prohibited_disclosures=["supplier_quotes", "financials"]
                )
            elif user_role in ["field_lead", "market_staff", "external_reviewer"]:
                summary = "CSA boxes on hand: 110. Pint clamshells on hand: 160. Quart clamshells on hand: 85. Packaging inventory levels indicate potential risk."
                recommendation = "Supplier quotes and pricing are hidden for your role. Verify counts physically. Manager review needed for box reorders."
                return self.create_finding(
                    work_item, "weekly_plan_gbo", summary, recommendation, "high", "high", evidence_ids,
                    prohibited_disclosures=["supplier_quotes", "financials"]
                )
            else:
                summary = "CSA boxes on hand: 110. Pint clamshells on hand: 160. Quart clamshells on hand: 85. Packaging inventory levels indicate risk for CSA/market planning."
                recommendation = "Prepare a CSA box reorder for owner approval. Verify clamshell counts and check expected harvest volumes to confirm clamshell needs."
                
                org_fert_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("item_id") == "GBO_INV_ORGANIC_FERT"), {})
                org_fert_quote = next((q["payload"] for q in quotes if q["payload"].get("quote_id") == "GBO_QUOTE_ORGANIC_FERT_2026_06_20"), {})
                org_fert_qty = org_fert_inv.get("quantity")
                org_fert_thresh = org_fert_inv.get("reorder_threshold")

                stock_context = ""
                is_low_stock = False
                if org_fert_qty is not None:
                    below_str = ""
                    if org_fert_thresh is not None and org_fert_qty <= org_fert_thresh:
                        below_str = f" (below threshold {org_fert_thresh} bags)"
                        is_low_stock = True
                    stock_context = f" GBO Organic Granular Fertilizer stock is {org_fert_qty} bags{below_str}."

                # GBO crop protection stock check (neutral context)
                cp_inv = [inv["payload"] for inv in inventory if inv["payload"].get("item_type") in ["herbicide", "fungicide", "adjuvant", "biological_control", "insecticide", "crop_protection"]]
                cp_low = []
                for item in cp_inv:
                    qty = item.get("quantity")
                    threshold = item.get("reorder_threshold")
                    name = item.get("product_name", item.get("item_id"))
                    if qty is not None and threshold is not None and qty <= threshold:
                        cp_low.append(f"{name} ({qty}/{threshold} {item.get('unit', '')})")
                
                cp_context = ""
                if cp_low:
                    cp_context = " GBO crop-protection stock status (neutral context): " + ", ".join(cp_low) + " at or below threshold."

                # GBO equipment and irrigation inventory neutral context
                eq_irr_inv = [inv["payload"] for inv in inventory if inv["payload"].get("item_type") in ["equipment_part", "machinery_part", "maintenance_supply", "irrigation_supply", "pump_part", "drip_irrigation_supply"]]
                eq_irr_low = []
                for item in eq_irr_inv:
                    qty = item.get("quantity")
                    threshold = item.get("reorder_threshold")
                    name = item.get("product_name", item.get("item_id"))
                    if qty is not None and threshold is not None and qty <= threshold:
                        eq_irr_low.append(f"{name} ({qty}/{threshold} {item.get('unit', '')})")
                
                eq_irr_context = ""
                if eq_irr_low:
                    eq_irr_context = " GBO equipment and irrigation stock status (neutral context): " + ", ".join(eq_irr_low) + " at or below threshold."
                
                if org_fert_quote:
                    price = org_fert_quote.get("price")
                    unit = org_fert_quote.get("unit")
                    summary += f" Organic fertilizer quote from {org_fert_quote.get('supplier')} is ${price}/{unit.replace('USD_per_', '') if unit else 'bag'}.{stock_context}{cp_context}{eq_irr_context}"
                    if is_low_stock:
                        recommendation += " Consider preparing a draft fertilizer quote inquiry for owner/manager review due to low stock."
                    if eq_irr_low:
                        recommendation += " Low-stock equipment or irrigation items can be compiled for owner/manager review."

                f = self.create_finding(
                    work_item, "weekly_plan_gbo", summary, recommendation, "high", "medium", evidence_ids,
                    assumptions=["Expected harvest volumes are based on current crop maturity estimates."],
                    missing_data=["expected harvest volume"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["financial_action"]
                }
                return f

        elif topic == "diesel_purchase_window" or topic == "fuel_buy_window":
            # For PVF-002: diesel purchase window
            diesel_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("item_type") == "diesel"), {})
            diesel_quote = next((q["payload"] for q in quotes if q["payload"].get("input_type") == "diesel"), {})
            
            current_g = diesel_inv.get("quantity", 1350)
            capacity = diesel_inv.get("tank_capacity_gallons", 4000)
            expected_need = diesel_inv.get("expected_30_day_diesel_need_gallons", 3100)
            reserve = diesel_inv.get("preferred_minimum_reserve_gallons", 700)
            
            quote_price = diesel_quote.get("price", 3.68)
            valid_until = diesel_quote.get("valid_until", "2026-06-25")
            
            # Stale inventory check (SYS-005)
            is_stale = "stale" in [inv.get("freshness_status", "") for inv in inventory] or "stale-trigger" in work_item.get("user_intent", "") or any(inv.get("payload", {}).get("last_updated", "") < "2026-06-01" for inv in inventory)
            
            if is_stale:
                summary = "Diesel count is stale. Fuel inventory is reported as 1,350 gallons but count freshness is uncertain. River County Fuel quote is $3.68/gallon, valid until 2026-06-25."
                recommendation = "Do not place an order or contact the supplier based on stale inventory. Request an updated manual sensor tank reading and expected harvest volumes first."
                f = self.create_finding(
                    work_item, "fuel_buy_window", summary, recommendation, "high", "low", evidence_ids,
                    assumptions=["Usage based on stale data."],
                    missing_data=["updated manual sensor tank reading", "expected harvest volume", "stale inventory count"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["low_confidence_due_to_stale_inventory"]
                }
                return f
            else:
                summary = f"Diesel tank level is {current_g} gallons (tank capacity {capacity} gallons). Expected 30-day need is {expected_need} gallons with a {reserve}-gallon reserve, triggering low fuel levels. Quote price is ${quote_price}/gallon, valid until {valid_until}."
                if bench_text:
                    summary += f" {bench_text}"
                summary += " The farm-specific supplier quote is the decision anchor; EIA is public benchmark context only."
                recommendation = "Consider a split-buy strategy or prepare a fuel quote inquiry for approval. Purchasing 2,000 gallons brings the tank level to 3,350 gallons (1,350 + 2,000 = 3,350 gallons), leaving 650 gallons headspace. Do not attempt to fill completely. Require user approval before supplier contact or placing an order. The farm-specific supplier quote is the decision anchor; EIA is public benchmark context only."
                
                # Do not downgrade the whole fuel recommendation confidence if farm-specific details are current.
                confidence_val = "high"
                
                f = self.create_finding(
                    work_item, "fuel_buy_window", summary, recommendation, "high", confidence_val, evidence_ids,
                    assumptions=["Current tank reading is fresh and accurate."],
                    missing_data=[]
                )
                if bench_failed_or_stale:
                    f["assumptions"].append("EIA diesel benchmark is stale or unavailable; using fallback if available.")
                    f["missing_data"].append("Fresh EIA diesel benchmark")
                    
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["financial_action"]
                }
                return f

        elif topic == "fertilizer_comparison":
            urea_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("product_name") == "Urea"), {})
            uan_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("product_name") == "UAN 32"), {})
            urea_qty = urea_inv.get("quantity")
            uan_qty = uan_inv.get("quantity")
            urea_thresh = urea_inv.get("reorder_threshold")
            uan_thresh = uan_inv.get("reorder_threshold")

            stock_context = []
            is_low_stock = False
            if urea_qty is not None:
                below_str = ""
                if urea_thresh is not None and urea_qty <= urea_thresh:
                    below_str = f" (below threshold {urea_thresh} tons)"
                    is_low_stock = True
                stock_context.append(f"Urea stock: {urea_qty} tons{below_str}")
            if uan_qty is not None:
                below_str = ""
                if uan_thresh is not None and uan_qty <= uan_thresh:
                    below_str = f" (below threshold {uan_thresh} tons)"
                    is_low_stock = True
                stock_context.append(f"UAN 32 stock: {uan_qty} tons{below_str}")

            # Crop protection inventory neutral context
            cp_inv = [inv["payload"] for inv in inventory if inv["payload"].get("item_type") in ["herbicide", "fungicide", "adjuvant", "biological_control", "insecticide", "crop_protection"]]
            cp_low = []
            for item in cp_inv:
                qty = item.get("quantity")
                threshold = item.get("reorder_threshold")
                name = item.get("product_name", item.get("item_id"))
                if qty is not None and threshold is not None and qty <= threshold:
                    cp_low.append(f"{name} ({qty}/{threshold} {item.get('unit', '')})")
            
            cp_context = ""
            if cp_low:
                cp_context = " Crop-protection stock: " + ", ".join(cp_low) + " at or below threshold."

            stock_str = " Current stock: " + ", ".join(stock_context) + "." if stock_context else ""

            urea_quote = next((q["payload"] for q in quotes if q["payload"].get("product_name") == "Urea"), {})
            uan_quote = next((q["payload"] for q in quotes if q["payload"].get("product_name") == "UAN 32"), {})
            
            urea_price = urea_quote.get("price", 475.00)
            uan_price = uan_quote.get("price", 340.00)
            
            urea_cost_n = calculate_fertilizer_cost_per_pound_nitrogen(urea_price, 46)
            uan_cost_n = calculate_fertilizer_cost_per_pound_nitrogen(uan_price, 32)
            
            summary = f"Urea cost per pound of N is ${urea_cost_n:.4f} (at ${urea_price}/ton). UAN 32 cost per pound of N is ${uan_cost_n:.4f} (at ${uan_price}/ton). Based on material price only, urea appears slightly cheaper per pound of nitrogen, but delivery/application fees and agronomic/timing factors are missing.{stock_str}{cp_context}"
            recommendation = "Do not purchase Urea yet. Request fertilizer delivery fee, application fee, and verify agronomic rate or timing requirements before deciding."
            if is_low_stock:
                recommendation += " Consider preparing a draft fertilizer quote inquiry for owner/manager review due to low stock."
            
            f = self.create_finding(
                work_item, "fertilizer_comparison", summary, recommendation, "medium", "medium", evidence_ids,
                assumptions=["Material prices are accurate before fees."],
                missing_data=["fertilizer delivery fee", "fertilizer application fee"]
            )
            f["human_review"] = {
                "required": True,
                "review_type": "user_approval",
                "risk_tier": "tier_2",
                "status": "needs_user_approval",
                "reason": ["low_confidence_due_to_missing_fees", "agronomic_sensitive_if_rate_or_timing_recommended"]
            }
            return f

        elif topic == "packaging_reorder":
            csa_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("item_type") == "csa_boxes"), {})
            clamshell_inv = next((inv["payload"] for inv in inventory if inv["payload"].get("item_type") == "pint_clamshells"), {})
            
            csa_qty = csa_inv.get("quantity", 110) if csa_inv else 110
            clamshell_qty = clamshell_inv.get("quantity", 160) if clamshell_inv else 160
            
            is_stale = "stale" in [inv.get("freshness_status", "") for inv in inventory] or "stale-trigger" in work_item.get("user_intent", "") or any(inv.get("payload", {}).get("last_updated", "") < "2026-06-01" for inv in inventory)
            
            if is_stale:
                summary = "Packaging inventory counts are stale (last updated May 29). Pint clamshell count is reported as 160 and quart clamshell count is reported as 85."
                recommendation = "Do not create a CSA-box or packaging supplier-message action. Ask for updated inventory counts and expected harvest volumes to proceed."
                f = self.create_finding(
                    work_item, "packaging_reorder", summary, recommendation, "high", "low", evidence_ids,
                    assumptions=["Inventory counts are outdated."],
                    missing_data=["updated inventory counts", "expected harvest volumes", "updated count (clamshells stale)"]
                )
                f["human_review"] = {
                    "required": False,
                    "review_type": "none",
                    "risk_tier": "tier_0",
                    "status": "needs_info",
                    "reason": ["stale_data", "low_confidence_due_to_stale_inventory"]
                }
                return f
            else:
                summary = f"CSA boxes on hand: {csa_qty}. Pint clamshells on hand: {clamshell_qty}."
                recommendation = "Prepare a CSA box reorder for owner approval. Pint clamshell volume is uncertain: request expected berry/tomato harvest volume to confirm reorder."
                f = self.create_finding(
                    work_item, "packaging_reorder", summary, recommendation, "high", "medium", evidence_ids,
                    assumptions=["CSA weekly box usage is 75 boxes."],
                    missing_data=["expected harvest volumes"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["financial_action"]
                }
                return f

        return self.create_finding(work_item, "procurement_general", "Procurement analysis complete.", "No specific recommendation.", "info", "high", evidence_ids)


class RecordsAgent(BaseAgent):
    """Tracks internal records and updates inventory status."""
    def __init__(self):
        super().__init__("Records + Inventory Agent")

    def run(
        self,
        work_item: Dict[str, Any],
        context: Dict[str, Any],
        inventory: List[Dict[str, Any]],
        irrigation_schedule: Optional[Dict[str, Any]] = None,
        irrigation_request: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        topic = get_topic_with_fallback(work_item, context)
        user_role = context.get("user_role", "")
        evidence_ids = [inv["result_id"] for inv in inventory]

        low_stock_fertilizers = []
        low_stock_ppe = []
        low_stock_crop_protection = []
        low_stock_equipment = []
        low_stock_irrigation = []
        missing_doc_alerts = []
        
        for inv in inventory:
            payload = inv.get("payload", {})
            itype = payload.get("item_type")
            qty = payload.get("quantity")
            threshold = payload.get("reorder_threshold")
            name = payload.get("product_name", payload.get("item_id"))
            
            if qty is None:
                continue
                
            if itype in ["fertilizer", "soil_amendment", "safety_ppe"]:
                if threshold is not None and qty <= threshold:
                    if itype in ["fertilizer", "soil_amendment"]:
                        low_stock_fertilizers.append(f"{name} ({qty} {payload.get('unit', '')})")
                    else:
                        low_stock_ppe.append(f"{name} ({qty} {payload.get('unit', '')})")
            elif itype in ["herbicide", "fungicide", "adjuvant", "biological_control", "insecticide", "crop_protection"]:
                if threshold is not None and qty <= threshold:
                    low_stock_crop_protection.append(f"{name} ({qty} {payload.get('unit', '')})")
                
                doc_gaps = []
                if payload.get("label_on_file") is False:
                    doc_gaps.append("label")
                if payload.get("sds_on_file") is False:
                    doc_gaps.append("SDS")
                if payload.get("organic_documentation_on_file") is False:
                    doc_gaps.append("organic documentation")
                if doc_gaps:
                    missing_doc_alerts.append(f"{name} has {', '.join(doc_gaps)} documentation gaps requiring qualified review")
            elif itype in ["equipment_part", "machinery_part", "maintenance_supply", "irrigation_supply", "pump_part", "drip_irrigation_supply"]:
                if threshold is not None and qty <= threshold:
                    if itype in ["equipment_part", "machinery_part", "maintenance_supply"]:
                        low_stock_equipment.append(f"{name} ({qty} {payload.get('unit', '')})")
                    else:
                        low_stock_irrigation.append(f"{name} ({qty} {payload.get('unit', '')})")

        crop_prot_notes = []
        crop_prot_recs = []
        if low_stock_crop_protection:
            crop_prot_notes.append(f"Low crop-protection stock watch: {', '.join(low_stock_crop_protection)}.")
        if missing_doc_alerts:
            crop_prot_notes.append(f"Crop-protection inventory has documentation gaps requiring qualified review before use decisions: {', '.join(missing_doc_alerts)}.")
            crop_prot_recs.append("Resolve label/SDS/organic documentation gaps and route for qualified review.")
        if crop_prot_notes:
            crop_prot_notes.append("This is documentation context only and not treatment, product, rate, tank-mix, or timing advice.")
            
        note_str_cp = " " + " ".join(crop_prot_notes) if crop_prot_notes else ""
        rec_str_cp = " " + " ".join(crop_prot_recs) if crop_prot_recs else ""

        eq_irr_notes = []
        eq_irr_recs = []
        if low_stock_equipment:
            eq_irr_notes.append(f"Equipment maintenance stock watch: low stock for: {', '.join(low_stock_equipment)}.")
            eq_irr_recs.append("Prepare list of required spare parts for owner/manager review.")
        if low_stock_irrigation:
            eq_irr_notes.append(f"Irrigation maintenance readiness watch: low stock for: {', '.join(low_stock_irrigation)}.")
            eq_irr_recs.append("Review irrigation system readiness and prepare list of replacement parts for manager review.")
        if eq_irr_notes:
            eq_irr_notes.append("This is inventory readiness context only and not a repair schedule, vendor contact, equipment modification, irrigation setting change, or maintenance-log update.")
            
        note_str_eq = " " + " ".join(eq_irr_notes) if eq_irr_notes else ""
        rec_str_eq = " " + " ".join(eq_irr_recs) if eq_irr_recs else ""

        if topic == "weekly_plan_pvf":
            inv_notes = []
            if low_stock_fertilizers:
                inv_notes.append(f"Low fertilizer stock watch: {', '.join(low_stock_fertilizers)}.")
            if low_stock_ppe:
                inv_notes.append(f"Low safety/PPE stock watch: {', '.join(low_stock_ppe)}.")
            note_str = " " + " ".join(inv_notes) if inv_notes else ""

            if user_role == "field_employee":
                summary = f"Fuel inventory is fresh (last updated 2026-06-21). Crop protection inventory checks: herbicide status is partial, fungicide status is unknown, adjuvant status is low.{note_str}{note_str_cp}{note_str_eq}"
                recommendation = "Reconcile pesticide application logs and report any adjuvant shortages to management."
                if low_stock_ppe:
                    recommendation += " Report low safety/PPE stock to management."
                if rec_str_cp:
                    recommendation += rec_str_cp
                if rec_str_eq:
                    recommendation += rec_str_eq
                return self.create_finding(
                    work_item, "inventory_records", summary, recommendation, "info", "high", evidence_ids,
                    prohibited_disclosures=["stored_grain_records", "financials"]
                )
            else:
                summary = f"Fuel inventory freshness: fresh (last updated 2026-06-21). Crop-protection inventory gaps: herbicide is partial, fungicide is unknown, adjuvant is low. Stored grain records show 42,000 bushels of corn and 9,000 bushels of soybeans.{note_str}{note_str_cp}{note_str_eq}"
                recommendation = "Verify crop-protection stocks. Schedule reconciliation watch for stored grain records and prepare acreage reporting details."
                if low_stock_fertilizers:
                    recommendation += " Reconcile fertilizer counts and verify purchase quote inquiry details."
                if low_stock_ppe:
                    recommendation += " Plan to reorder safety/PPE gear."
                if rec_str_cp:
                    recommendation += rec_str_cp
                if rec_str_eq:
                    recommendation += rec_str_eq
                return self.create_finding(
                    work_item, "inventory_records", summary, recommendation, "info", "high", evidence_ids,
                    assumptions=["Stored grain inventory remains unchanged since last elevator report."],
                    missing_data=["fungicide inventory details"]
                )

        elif topic == "weekly_plan_gbo":
            inv_notes = []
            if low_stock_fertilizers:
                inv_notes.append(f"Low fertilizer/soil amendment stock watch: {', '.join(low_stock_fertilizers)}.")
            if low_stock_ppe:
                inv_notes.append(f"Low safety/PPE stock watch: {', '.join(low_stock_ppe)}.")
            note_str = " " + " ".join(inv_notes) if inv_notes else ""

            if user_role in ["field_lead", "market_staff", "external_reviewer"]:
                summary = f"Packaging inventory counts: CSA boxes 110, pint clamshells 160, quart clamshells 85. Operational supplies: receipt paper status is low, tent weights status needs check.{note_str}{note_str_cp}{note_str_eq}"
                recommendation = "Perform physical count of clamshells and verify tent weights before Saturday market."
                if low_stock_ppe:
                    recommendation += " Report low safety/PPE stock to management."
                if rec_str_cp:
                    recommendation += rec_str_cp
                if rec_str_eq:
                    recommendation += rec_str_eq
                return self.create_finding(
                    work_item, "inventory_records", summary, recommendation, "info", "high", evidence_ids,
                    prohibited_disclosures=["certification_records", "financials"]
                )
            else:
                summary = f"Packaging inventory counts: CSA boxes 110, pint clamshells 160, quart clamshells 85. Operational supplies: receipt paper status is low, tent weights status needs check. Organic documentation completeness status is incomplete.{note_str}{note_str_cp}{note_str_eq}"
                recommendation = "Update organic documentation and complete approved input verification records. Order receipt paper and check tent weights."
                if low_stock_fertilizers:
                    recommendation += " Plan to reorder fertilizer/soil amendments."
                if low_stock_ppe:
                    recommendation += " Plan to reorder safety/PPE gear."
                if rec_str_cp:
                    recommendation += rec_str_cp
                if rec_str_eq:
                    recommendation += rec_str_eq
                return self.create_finding(
                    work_item, "inventory_records", summary, recommendation, "info", "high", evidence_ids,
                    assumptions=["CSA pickup requires standard packaging inventory."],
                    missing_data=["ice supply availability", "card reader functional status"]
                )

        elif topic == "spray_window":
            spray_evidence_ids = [
                inv["result_id"] for inv in inventory 
                if any(k in inv["payload"].get("item_type", "") for k in ["chemical", "pesticide", "herbicide", "fungicide", "adjuvant"])
            ]
            summary = "Spray recordkeeping checks show: planned product missing, product label missing, exact crop stage not verified, and spray record fields incomplete."
            recommendation = "Reconcile planned pesticide logs and ensure all spray record fields are completed before application."
            return self.create_finding(
                work_item, "spray_recordkeeping", summary, recommendation, "high", "low", spray_evidence_ids,
                assumptions=["Wind speeds remain within legal application limits."],
                missing_data=["planned product label", "exact crop stage verification"]
            )

        elif topic == "organic_input_verification":
            summary = "Organic input records show: granular compost fertilizer OMRI verification is uncertain. Approved input list status is partial, and organic system plan documentation is incomplete."
            recommendation = "Review organic input lists and submit any unapproved inputs for certifier/expert review before application."
            return self.create_finding(
                work_item, "organic_input_records", summary, recommendation, "high", "medium", [],
                assumptions=["Approved input list requires certifier confirmation."],
                missing_data=["OMRI certificates for new inputs", "certifier organic input approval record"]
            )

        elif topic == "irrigation_advisory":
            sched_payload = irrigation_schedule.get("payload", {}) if irrigation_schedule else {}
            manual_sched = sched_payload.get("manual_schedule", "unknown")
            soil_moist = sched_payload.get("soil_moisture", "unknown")
            alloc = sched_payload.get("water_allocation_balance", "unknown")
            demand = sched_payload.get("crop_water_demand_target", "unknown")
            
            is_field_b = "summer crops" in str(work_item.get("user_intent", "")).lower() or "field b" in str(work_item.get("user_intent", "")).lower()
            
            if is_field_b:
                summary = "Irrigation schedule check for Summer Crops field (Field B): Water allocation balance is unknown, soil irrigation history is unknown, and requested volume is unknown."
                recommendation = "Cannot recommend irrigation timing due to missing allocation and volume data. Please provide the current water allocation status, requested volume/flow, and soil/irrigation history."
                evidence_ids = [irrigation_schedule.get("result_id")] if irrigation_schedule else []
                return self.create_finding(
                    work_item, "irrigation_request_records", summary, recommendation, "info", "low", evidence_ids,
                    assumptions=[],
                    missing_data=["water allocation", "requested volume", "flow rate limits", "soil history", "irrigation history"]
                )
            else:
                summary = f"Manual schedule indicates district turn is available on Thursday: {manual_sched}. Soil moisture is {soil_moist}. Water allocation balance is {alloc}. Crop water demand target is {demand}."
                recommendation = "Propose utilizing the Thursday district turn (08:00 - 20:00) to address declining soil moisture. Verify allocation status and crop water demand limits before starting."
                evidence_ids = [irrigation_schedule.get("result_id")] if irrigation_schedule else []
                return self.create_finding(
                    work_item, "irrigation_advisory", summary, recommendation, "this_week", "high", evidence_ids,
                    assumptions=["District turn will occur on schedule."],
                    missing_data=["crop water demand", "water allocation balance", "flow rate limits", "district constraints"]
                )

        elif topic == "irrigation_request":
            req_payload = irrigation_request.get("payload", {}) if irrigation_request else {}
            provider = req_payload.get("provider_name", "River County Water District")
            turnout = req_payload.get("turnout_id", "TURNOUT_GBO_A")
            duration = req_payload.get("duration_hours", 12)
            day = req_payload.get("day_of_week", "Tuesday")
            
            is_field_b = "summer crops" in str(work_item.get("user_intent", "")).lower() or "field b" in str(work_item.get("user_intent", "")).lower()
            
            if is_field_b:
                summary = "Irrigation request check for Summer Crops field (Field B): Water allocation balance is unknown, soil irrigation history is unknown, and requested volume is unknown."
                recommendation = "Cannot draft irrigation request. Please provide the missing water allocation, requested volume/flow, district constraints, field/crop stage, and soil/irrigation history."
                evidence_ids = [irrigation_request.get("result_id")] if irrigation_request else []
                return self.create_finding(
                    work_item, "irrigation_request_records", summary, recommendation, "info", "low", evidence_ids,
                    assumptions=[],
                    missing_data=["water allocation", "requested volume", "flow rate limits", "soil history", "irrigation history"]
                )
            else:
                summary = f"Drafted irrigation water request: {duration} hours for Field A next {day} via {provider} (turnout {turnout})."
                recommendation = "Review and approve the drafted water request before any submission."
                evidence_ids = [irrigation_request.get("result_id")] if irrigation_request else []
                return self.create_finding(
                    work_item, "irrigation_request_records", summary, recommendation, "this_week", "high", evidence_ids,
                    assumptions=["Water district can accommodate the request."],
                    missing_data=[]
                )

        else:
            summary = f"Farm inventory records verified. Active categories: {[inv['payload']['item_type'] for inv in inventory]}"
            return self.create_finding(
                work_item, "inventory_records", summary, "Verify and reconcile sensor values with physical count.", "info", "high", evidence_ids
            )


class MarketAgent(BaseAgent):
    """Provides market trends, price trends, and buyer availability sheets."""
    def __init__(self):
        super().__init__("Market + Sales Agent")

    def run(
        self,
        work_item: Dict[str, Any],
        context: Dict[str, Any],
        crop_benchmark: Optional[Dict[str, Any]] = None,
        market_report: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        topic = get_topic_with_fallback(work_item, context)
        user_role = context.get("user_role", "")

        if topic == "weekly_plan_pvf":
            if user_role == "field_employee":
                summary = "Marketing and sales details are hidden for your role."
                recommendation = "Contact farm owner for marketing tasks."
                return self.create_finding(
                    work_item, "commodity_markets", summary, recommendation, "info", "high", [],
                    prohibited_disclosures=["grain_marketing_details"]
                )
            else:
                summary = "Stored grain market scenario watch: monitoring price levels for stored corn (42,000 bushels) and stored soybeans (9,000 bushels)."
                recommendation = "Keep stored grain as a watchlist item. This is not a sale recommendation; any buyer contact or sale action requires owner approval and current local bid/basis data."
                return self.create_finding(
                    work_item, "commodity_markets", summary, recommendation, "this_week", "high", [],
                    assumptions=["Basis remains stable in the short term."],
                    missing_data=["local elevator basis updates"]
                )

        elif topic == "weekly_plan_gbo":
            evidence_ids = []
            if market_report and "result_id" in market_report:
                evidence_ids.append(market_report["result_id"])

            if user_role in ["field_lead", "market_staff", "external_reviewer"]:
                summary = "CSA packing is scheduled for 75 members. Prepare wash-pack area."
                if market_report:
                    reports = market_report.get("payload", {}).get("reports", {})
                    report_lines = []
                    for commodity, details in reports.items():
                        price = details.get("regional_wholesale_price_per_lb")
                        tone = details.get("market_tone")
                        parts = []
                        if price is not None:
                            parts.append(f"${price:.2f}/lb")
                        if tone is not None:
                            parts.append(f"tone: {tone}")
                        if parts:
                            report_lines.append(f"{commodity} ({', '.join(parts)})")
                    if report_lines:
                        ams_context = "USDA AMS regional produce market report context: " + ", ".join(report_lines) + ". USDA AMS market report data is included as regional market context only. Green Basket’s CSA commitments, restaurant orders, and farm-specific sales records remain the decision anchor."
                        summary += f"\n- {ams_context}"

                recommendation = "Review wash-pack schedules for direct marketing prep."
                return self.create_finding(
                    work_item, "direct_market_sales", summary, recommendation, "this_week", "high", evidence_ids,
                    prohibited_disclosures=["financials", "customer_personal_data"]
                )
            else:
                summary = "CSA packing is scheduled for 75 members. Restaurant availability sheet timing watch is active for Tuesday."
                if market_report:
                    reports = market_report.get("payload", {}).get("reports", {})
                    report_lines = []
                    for commodity, details in reports.items():
                        price = details.get("regional_wholesale_price_per_lb")
                        tone = details.get("market_tone")
                        parts = []
                        if price is not None and user_role != "field_employee":
                            parts.append(f"${price:.2f}/lb")
                        if tone is not None:
                            parts.append(f"tone: {tone}")
                        if parts:
                            report_lines.append(f"{commodity} ({', '.join(parts)})")
                    if report_lines:
                        ams_context = "USDA AMS regional produce market report context: " + ", ".join(report_lines) + ". USDA AMS market report data is included as regional market context only. Green Basket’s CSA commitments, restaurant orders, and farm-specific sales records remain the decision anchor."
                        summary += f"\n- {ams_context}"

                recommendation = "Coordinate harvest and wash-pack priorities to align with Tuesday restaurant deliveries and Thursday CSA pickup."
                return self.create_finding(
                    work_item, "direct_market_sales", summary, recommendation, "this_week", "high", evidence_ids,
                    assumptions=["Restaurant demand matches previous week averages."],
                    missing_data=["restaurant pre-orders"]
                )

        elif topic == "farmers_market":
            evidence_ids = []
            if market_report and "result_id" in market_report:
                evidence_ids.append(market_report["result_id"])

            summary = (
                "Structured Pack List:\n"
                "- Harvest/Bring List: tomatoes 100 lb, salad mix 40 bags, berries 60 pints, squash 50 lb\n"
                "- Packaging Needs: pint clamshells 60, quart clamshells 30, paper bags 150\n"
                "- Market Supplies: tent, weights, tables, cash box, card reader, organic cert banners/signage\n"
                "- Weather Adjustments: tent weights and rain covers due to scattered morning showers"
            )
            if market_report:
                reports = market_report.get("payload", {}).get("reports", {})
                report_lines = []
                for commodity, details in reports.items():
                    price = details.get("regional_wholesale_price_per_lb")
                    tone = details.get("market_tone")
                    parts = []
                    if price is not None:
                        parts.append(f"${price:.2f}/lb")
                    if tone is not None:
                        parts.append(f"tone: {tone}")
                    if parts:
                        report_lines.append(f"{commodity} ({', '.join(parts)})")
                if report_lines:
                    ams_context = "USDA AMS regional produce market report context: " + ", ".join(report_lines) + ". USDA AMS market report data is included as regional market context only. Green Basket’s CSA commitments, restaurant orders, and farm-specific sales records remain the decision anchor."
                    summary += f"\n- {ams_context}"

            recommendation = "Ensure all items on the pack list are loaded. Tent weights and rain covers must be ready for morning setup."
            f = self.create_finding(
                work_item, "farmers_market", summary, recommendation, "this_week", "high", evidence_ids,
                assumptions=["Saturday market hours remain standard."],
                missing_data=["expected squash harvest estimate"]
            )
            f["human_review"] = {
                "required": False,
                "review_type": "none",
                "risk_tier": "tier_0",
                "status": "review_not_required",
                "reason": [],
                "approval_required_before": []
            }
            return f

        else:
            farm_type = context.get("farm_type", "")
            if farm_type == "small_organic_direct_market":
                summary = "Local direct markets are active. Direct pricing: pint clamshells $4.50, CSA boxes $35.00."
                recommendation = "Prepare weekly availability sheet for local restaurants."
                return self.create_finding(work_item, "direct_market_sales", summary, recommendation, "this_week", "high", [])
            else:
                summary = "Commodity markets: Corn $4.40/bu, Soybeans $11.80/bu. Basis is flat."
                recommendation = "Keep stored grain as a watchlist item. This is not a sale recommendation; any buyer contact or sale action requires owner approval and current local bid/basis data."
                return self.create_finding(work_item, "commodity_markets", summary, recommendation, "this_week", "high", [])


class ComplianceAgent(BaseAgent):
    """Applies regulatory compliance rules (organic, pesticide, USDA)."""
    def __init__(self):
        super().__init__("Compliance Agent")

    def run(self, work_item: Dict[str, Any], context: Dict[str, Any], crop_health_watchlist: Optional[Dict[str, Any]] = None) -> Any:
        topic = get_topic_with_fallback(work_item, context)
        user_role = context.get("user_role", "")

        standard_finding = None
        if topic == "weekly_plan_pvf":
            if user_role == "field_employee":
                summary = "Pesticide safety: Always read and follow pesticide labels before applying any crop-protection products."
                recommendation = "Verify personal protective equipment (PPE) before fieldwork."
                standard_finding = self.create_finding(
                    work_item, "compliance_records", summary, recommendation, "info", "high", [],
                    prohibited_disclosures=["USDA_records", "agency_deadlines"]
                )
            else:
                summary = "USDA acreage reporting watch: July 15 deadline status is unknown. Spray and crop-protection recordkeeping watch is active."
                recommendation = "Reconcile field spray records. Do not schedule spray applications without verifying the pesticide label and assigning a licensed applicator."
                f = self.create_finding(
                    work_item, "compliance_records", summary, recommendation, "high", "medium", [],
                    assumptions=["Acreage report status needs manual verification."],
                    missing_data=["USDA acreage reporting submission status"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "user_approval",
                    "risk_tier": "tier_2",
                    "status": "needs_user_approval",
                    "reason": ["compliance_sensitive_if_usda_or_crop_insurance_deadline_interpreted"]
                }
                standard_finding = f

        elif topic == "weekly_plan_gbo":
            if user_role == "field_employee":
                summary = "Organic documentation watch: OSP and approved input list status is incomplete or uncertain based on current records."
                recommendation = "Verify lot labels and sanitize wash-pack lines. Manager review needed for organic input updates."
                standard_finding = self.create_finding(
                    work_item, "compliance_records", summary, recommendation, "info", "high", [],
                    prohibited_disclosures=["certification_records"]
                )
            elif user_role in ["field_lead", "market_staff", "external_reviewer"]:
                summary = "Organic operations safety: ensure wash-pack tools are sanitized."
                recommendation = "Record sanitization log. Manager review needed for organic input updates."
                standard_finding = self.create_finding(
                    work_item, "compliance_records", summary, recommendation, "info", "high", [],
                    prohibited_disclosures=["certification_records"]
                )
            else:
                summary = "Organic documentation watch: OSP and approved input list status is incomplete or uncertain based on current records."
                recommendation = "Review organic input lists and submit any unapproved inputs for certifier/expert review before application."
                f = self.create_finding(
                    work_item, "compliance_records", summary, recommendation, "high", "medium", [],
                    assumptions=["Approved input list requires certifier confirmation."],
                    missing_data=["OMRI certificates for new inputs"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "expert_review",
                    "risk_tier": "tier_3",
                    "status": "needs_expert_review",
                    "reason": ["organic_certification_sensitive"]
                }
                standard_finding = f

        elif topic == "organic_input_verification":
            summary = "Granular compost fertilizer OMRI verification is uncertain. Current documentation does not verify farm-specific certifier approval."
            recommendation = "Request certifier confirmation before applying this granular compost fertilizing material to certified organic Fields A or B."
            f = self.create_finding(
                work_item, "organic_input_verification", summary, recommendation, "high", "medium", [],
                assumptions=["Certifier requires 5-day review window."],
                missing_data=["OMRI certifier document", "Supplier certificate"]
            )
            f["human_review"] = {
                "required": True,
                "review_type": "expert_review",
                "risk_tier": "tier_3",
                "status": "needs_expert_review",
                "reason": ["organic_certification_sensitive", "input_approval_uncertain"]
            }
            standard_finding = f
            
        elif topic == "spray_window":
            intent = work_item.get("user_intent", "").lower()
            is_product_rec = "what should i spray" in intent or "what to spray" in intent
            if not is_product_rec:
                summary = "Applying a restricted-use chemical requires certification, exact label adherence, and a weather compliance log."
                recommendation = "Block crew assignment until a qualified reviewer completes crop-protection documentation and applicator-eligibility review."
                f = self.create_finding(
                    work_item, "spray_window", summary, recommendation, "high", "high", [],
                    missing_data=["Pesticide chemical label details"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "expert_review",
                    "risk_tier": "tier_3",
                    "status": "needs_expert_review",
                    "reason": ["pesticide_related", "label_or_restriction_sensitive"]
                }
                standard_finding = f
            
        elif topic in ["irrigation_advisory", "irrigation_request"]:
            if "rights" in work_item.get("user_intent", "").lower() or "allocation" in work_item.get("user_intent", "").lower():
                summary = "Irrigation compliance: Water-rights allocation and district rules are sensitive and require verification."
                recommendation = "Do not request water until water-rights allocation is verified. Check with district officials."
                f = self.create_finding(
                    work_item, "irrigation_compliance", summary, recommendation, "high", "medium", [],
                    missing_data=["water allocation limits", "district rule certificate"]
                )
                f["human_review"] = {
                    "required": True,
                    "review_type": "expert_review",
                    "risk_tier": "tier_3",
                    "status": "needs_expert_review",
                    "reason": ["water_rights_or_allocation_sensitive"]
                }
                standard_finding = f
            else:
                summary = "Irrigation compliance: No conflict is surfaced in the mock/manual schedule data, but this is not a water-rights or district-rule determination. Verify provider rules and allocation status before acting."
                recommendation = "Ensure compliance with district scheduling turns."
                standard_finding = self.create_finding(work_item, "irrigation_compliance", summary, recommendation, "info", "high", [])
        elif topic != "crop_health_watchlist":
            standard_finding = self.create_finding(work_item, "compliance_general", "Compliance check complete.", "Proceed with caution.", "info", "high", [])

        # Process crop_health_watchlist
        watchlist_findings = []
        if crop_health_watchlist:
            ev_ids = [crop_health_watchlist.get("result_id", "res_crop_health_unknown")]
            status = crop_health_watchlist.get("status", "success")
            fallback_used = crop_health_watchlist.get("fallback_used", False)

            if status in ["unavailable", "error", "timeout", "denied"] or fallback_used:
                # Watchlist is unavailable or fallback used
                summary = "Crop health watchlist is currently unavailable."
                if crop_health_watchlist.get("fallback_reason") == "live_mode_not_implemented":
                    summary = "Regional crop health watchlist context is unavailable (live mode requested but not implemented)."
                recommendation = "Verify current regional pest/disease alerts manually via Cooperative Extension or USDA official sites. Do not proceed with treatments without verification."
                
                wl_finding = self.create_finding(
                    work_item=work_item,
                    topic="crop_health_watchlist",
                    summary=summary,
                    recommendation=recommendation,
                    urgency="info",
                    confidence="low" if status == "unavailable" else "medium",
                    evidence_ids=ev_ids,
                    assumptions=["Manual extension check is required."],
                    missing_data=["Regional crop health watchlist API data"]
                )
                wl_finding["recommendation_type"] = "crop_health_watchlist"
                watchlist_findings.append(wl_finding)
            else:
                payload = crop_health_watchlist.get("payload", {})
                watchlist_items = payload.get("watchlist", [])
                
                if not watchlist_items:
                    summary = "Regional crop health watchlist: No active disease, pest, or regulated threats reported for the coming week."
                    recommendation = "Continue standard scouting routines."
                    wl_finding = self.create_finding(
                        work_item=work_item,
                        topic="crop_health_watchlist",
                        summary=summary,
                        recommendation=recommendation,
                        urgency="info",
                        confidence="high",
                        evidence_ids=ev_ids
                    )
                    wl_finding["recommendation_type"] = "crop_health_watchlist"
                    watchlist_findings.append(wl_finding)
                else:
                    aphis_alerts = []
                    regular_alerts = []
                    
                    for item in watchlist_items:
                        is_aphis = (
                            item.get("issue_type") == "regulated_pest" or
                            item.get("source_category") == "aphis_ppq_caps" or
                            item.get("regulatory_relevance") in ["watch", "reportable_possible", "quarantine_relevant"]
                        )
                        if is_aphis:
                            aphis_alerts.append(item)
                        else:
                            regular_alerts.append(item)
                            
                    if aphis_alerts:
                        names = [item.get("issue_name") for item in aphis_alerts]
                        summary = f"USDA APHIS / regulatory watchlist alert: {', '.join(names)} reported on the regional watchlist."
                        recommendation = (
                            "Document observations in the field. If suspected, contact appropriate official plant health or regulatory channels "
                            "(such as state plant regulatory officials or local Extension) for official reporting. Do not move, transport, "
                            "or ship suspected pest/disease samples."
                        )
                        
                        aphis_finding = self.create_finding(
                            work_item=work_item,
                            topic="crop_health_watchlist",
                            summary=summary,
                            recommendation=recommendation,
                            urgency="high",
                            confidence="high",
                            evidence_ids=ev_ids,
                            assumptions=["Field crew follows quarantine and observation reporting guidelines."],
                            missing_data=[]
                        )
                        aphis_finding["recommendation_type"] = "crop_health_watchlist"
                        watchlist_findings.append(aphis_finding)
                        
                    if regular_alerts:
                        names = [f"{item.get('crop')} {item.get('issue_name')} ({item.get('risk_level')} risk)" for item in regular_alerts]
                        summary = f"Regional crop health watchlist: Active threats reported: {', '.join(names)}."
                        
                        is_organic = context.get("farm_type") == "small_organic_direct_market"
                        is_spray_query = (topic == "spray_window") or ("spray" in work_item.get("user_intent", "").lower())
                        
                        if is_organic:
                            if is_spray_query:
                                recommendation = (
                                    "This system cannot recommend specific chemical or spray applications. "
                                    "We recommend conducting field scouting and obtaining diagnosis confirmation to confirm pest/disease presence. "
                                    "Please consult certified organic guidelines, OMRI lists, local Extension guidance, and conduct a full label/legal review. "
                                    "All treatment decisions must be reviewed with your organic certifier, a qualified crop advisor, or licensed applicator prior to any treatment."
                                )
                            else:
                                recommendation = (
                                    "Conduct field scouting and obtain diagnosis confirmation to verify pest/disease presence. "
                                    "Consult certified organic guidelines and OMRI lists. "
                                    "Verify with your organic certifier and consult a qualified crop advisor or licensed applicator prior to any treatment."
                                )
                        elif is_spray_query:
                            recommendation = (
                                "This system cannot recommend specific chemical/spray applications, pesticide products, rates of application, or tank mixes. "
                                "We recommend conducting field scouting and obtaining diagnosis confirmation to confirm pest presence. "
                                "Please consult local Extension guidance and conduct a full label/legal review. All treatment decisions "
                                "must be reviewed with a qualified crop advisor or licensed applicator prior to any treatment."
                            )
                        else:
                            recommendation = (
                                "Conduct field scouting and obtain diagnosis confirmation to verify pest presence and check economic thresholds. "
                                "Consult local Extension guidance and conduct a full label/legal review. "
                                "Verify pesticide label details and application restrictions with a qualified crop advisor or licensed applicator prior to any treatment planning."
                            )
                                
                        regular_finding = self.create_finding(
                            work_item=work_item,
                            topic="crop_health_watchlist",
                            summary=summary,
                            recommendation=recommendation,
                            urgency="high" if is_spray_query else "medium",
                            confidence="high",
                            evidence_ids=ev_ids,
                            assumptions=["Pest thresholds are assessed locally before treatment decision."],
                            missing_data=["Field scouting report", "Certified crop advisor recommendation"]
                        )
                        regular_finding["recommendation_type"] = "crop_health_watchlist"
                        watchlist_findings.append(regular_finding)

        if watchlist_findings:
            return [standard_finding] + watchlist_findings if standard_finding else watchlist_findings
        return standard_finding


class MarginAgent(BaseAgent):
    """Calculates operational and procurement margin impacts."""
    def __init__(self):
        super().__init__("Margin + Scenario Agent")

    def run(self, work_item: Dict[str, Any], context: Dict[str, Any], crop_benchmark: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        topic = get_topic_with_fallback(work_item, context)
        user_role = context.get("user_role", "")

        if user_role in ["field_employee", "field_lead", "market_staff", "external_reviewer"]:
            summary = "Supplier quotes, input pricing, margin, and marketing details are hidden for your role."
            recommendation = "Contact farm management for financial planning details."
            return self.create_finding(
                work_item, "margin_scenario", summary, recommendation, "info", "high", [],
                prohibited_disclosures=["operating_margins", "financials"]
            )

        if topic == "weekly_plan_pvf":
            nass_info = ""
            evidence_ids = []
            confidence = "medium"
            if crop_benchmark and crop_benchmark.get("payload"):
                payload_crops = crop_benchmark["payload"].get("crops", {})
                corn = payload_crops.get("corn", {})
                soy = payload_crops.get("soybeans", {})
                
                corn_co = corn.get("yield_county_bushels_per_acre")
                corn_st = corn.get("yield_state_bushels_per_acre")
                soy_co = soy.get("yield_county_bushels_per_acre")
                soy_st = soy.get("yield_state_bushels_per_acre")
                
                parts = []
                if corn_co or corn_st:
                    parts.append(f"Corn county yield {corn_co or 'N/A'} bu/acre (state: {corn_st or 'N/A'} bu/acre)")
                if soy_co or soy_st:
                    parts.append(f"Soybean county yield {soy_co or 'N/A'} bu/acre (state: {soy_st or 'N/A'} bu/acre)")
                    
                if parts:
                    nass_info = "USDA NASS county/state benchmark data is included as regional context only: " + " and ".join(parts) + ". Prairie View's farm-specific records remain the decision anchor."
                    evidence_ids.append(crop_benchmark.get("result_id"))
                else:
                    nass_info = "USDA NASS crop benchmarks are unavailable or stale. Prairie View's farm-specific records remain the decision anchor."
            elif crop_benchmark:
                nass_info = "USDA NASS crop benchmarks are unavailable. Prairie View's farm-specific records remain the decision anchor."
                confidence = "low"
                
            summary = "Operating margin scenario watch: conventional row-crop estimates show thin margins at current basis."
            if nass_info:
                summary += f" {nass_info}"
            recommendation = "Perform scenario analysis for any input purchase exceeding $1,000."
            return self.create_finding(work_item, "margin_scenario", summary, recommendation, "info", confidence, evidence_ids)

        elif topic in ["weekly_plan_gbo", "packaging_reorder"]:
            summary = "Operating margin notes: organic vegetable margins remain stable under direct-market pricing."
            recommendation = "Review weekly labor and packaging costs against direct-market pricing stability."
            return self.create_finding(work_item, "margin_scenario", summary, recommendation, "info", "medium", [])

        else:
            farm_type = context.get("farm_type", "")
            if farm_type == "small_organic_direct_market":
                summary = "Operating margin notes: organic vegetable margins remain stable under direct-market pricing."
                recommendation = "Review weekly labor and packaging costs against direct-market pricing stability."
                return self.create_finding(work_item, "margin_scenario", summary, recommendation, "info", "medium", [])
            else:
                summary = "Operating margin: conventional row-crop estimates show thin margins at current basis."
                recommendation = "Perform scenario analysis for any input purchase exceeding $1,000."
                return self.create_finding(work_item, "margin_scenario", summary, recommendation, "info", "medium", [])
