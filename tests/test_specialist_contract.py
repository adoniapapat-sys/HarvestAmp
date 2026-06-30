# tests/test_specialist_contract.py
"""Contract tests for Specialist Agents."""
import json
import pytest
from harvestamp.agents import (
    WeatherFieldworkAgent,
    ProcurementAgent,
    RecordsInventoryAgent,
    MarketSalesAgent,
    ComplianceAgent,
    MarginScenarioAgent
)
from harvestamp.core.contracts import (
    normalize_agent_finding_contract,
    has_required_agent_finding_fields,
    contains_forbidden_wording,
    RESTRICTED_FIELD_EMPLOYEE_TERMS
)


def make_work_item(topic, farm_id="PVF_ROW_CROP_001", workflow_id="weekly_plan"):
    """Helper to construct a minimal work item dict."""
    return {
        "work_item_id": f"wi_{topic}_test",
        "workflow_id": workflow_id,
        "farm_id": farm_id,
        "requesting_user_id": "user_test",
        "topic": topic
    }


def make_context(user_role="farm_owner", farm_type="row_crop"):
    """Helper to construct a minimal context package."""
    return {
        "user_role": user_role,
        "farm_type": farm_type
    }


def normalize_findings(result):
    """Normalizes specialist run result into a list of finding dicts."""
    if result is None:
        return []
    if isinstance(result, dict):
        return [result]
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    pytest.fail(f"Unexpected specialist result type: {type(result)}")


def assert_contract_finding_shape(finding):
    """Asserts that a finding strictly conforms to the AgentFinding contract shape."""
    normalized = normalize_agent_finding_contract(finding)
    assert has_required_agent_finding_fields(normalized) is True
    assert isinstance(normalized["summary"], str)
    assert isinstance(normalized["evidence_ids"], list)
    assert isinstance(normalized["missing_data"], list)
    assert normalized["confidence"] is not None
    assert isinstance(normalized["human_review"], dict)
    assert isinstance(normalized["proposed_actions"], list)
    assert isinstance(normalized["blocked_actions"], list)
    return normalized


def assert_no_forbidden_text(obj):
    """Asserts that no forbidden executed action or advisor drift wording is present."""
    serialized = json.dumps(obj, sort_keys=True)
    assert contains_forbidden_wording(serialized) == []


def assert_field_employee_safe(obj):
    """Asserts that the serialized finding does not leak restricted terms or details."""
    serialized = json.dumps(obj, sort_keys=True).lower()
    for term in RESTRICTED_FIELD_EMPLOYEE_TERMS:
        assert term not in serialized
    
    # Assert additional role boundary checks
    restricted = ["supplier pricing", "quote price", "customer financial", "payment status", "buyer terms", "invoice", "official approval", "operating margin"]
    for term in restricted:
        assert term not in serialized
        
    assert contains_forbidden_wording(serialized) == []


# ----------------------------------------------------
# Test Cases
# ----------------------------------------------------

def test_weather_fieldwork_agent_returns_contract_shaped_weekly_finding():
    agent = WeatherFieldworkAgent()
    work_item = make_work_item("weekly_plan_pvf")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    weather_obs = {
        "result_id": "res_weather_mock_001",
        "source_id": "src_weather",
        "trust_tier": "public_context",
        "freshness_status": "fresh",
        "privacy_class": "Public Context",
        "payload": {
            "summary": "Rain and wind may constrain fieldwork."
        }
    }
    
    res = agent.run(work_item, context, weather_obs)
    findings = normalize_findings(res)
    
    assert len(findings) > 0
    for f in findings:
        assert_contract_finding_shape(f)
        assert isinstance(f["evidence_ids"], list)
        assert_no_forbidden_text(f)
        
        # Advisory checks
        recommendation = f["recommendation"].lower()
        for forbidden in ["apply this pesticide", "spray tomorrow", "tank mix", "schedule crew"]:
            assert forbidden not in recommendation


def test_weather_fieldwork_agent_keeps_spray_or_treatment_requests_safe():
    agent = WeatherFieldworkAgent()
    work_item = make_work_item("spray_window")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    weather_obs = {
        "result_id": "res_weather_mock_001",
        "source_id": "src_weather",
        "trust_tier": "public_context",
        "freshness_status": "fresh",
        "privacy_class": "Public Context",
        "payload": {
            "summary": "Wind speeds exceed spray thresholds."
        }
    }
    
    res = agent.run(work_item, context, weather_obs)
    findings = normalize_findings(res)
    
    for f in findings:
        assert_no_forbidden_text(f)
        recommendation = f["recommendation"].lower()
        for forbidden in ["apply this pesticide", "spray tomorrow", "tank mix", "treatment timing", "pesticide rate"]:
            assert forbidden not in recommendation


def test_procurement_agent_returns_contract_shaped_findings():
    agent = ProcurementAgent()
    work_item = make_work_item("diesel_purchase_window")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    quotes = [{
        "result_id": "res_quote_PVF_QUOTE_DIESEL_2026_06_21",
        "source_id": "src_diesel",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential",
        "payload": {
            "input_type": "diesel",
            "product_name": "Off-road diesel",
            "price_per_gallon": 3.10
        }
    }]
    
    inventory = [{
        "result_id": "res_inv_PVF_INV_DIESEL",
        "source_id": "src_inv",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential",
        "payload": {
            "product_name": "Diesel",
            "quantity": 1000
        }
    }]
    
    benchmark = {
        "result_id": "res_benchmark_eia_PVF_ROW_CROP_001",
        "source_id": "src_eia",
        "trust_tier": "public_context",
        "freshness_status": "fresh",
        "privacy_class": "Public Context",
        "payload": {
            "weekly_average_price": 3.15
        }
    }
    
    res = agent.run(work_item, context, quotes, inventory, benchmark)
    findings = normalize_findings(res)
    
    assert len(findings) > 0
    for f in findings:
        assert_contract_finding_shape(f)
        assert len(f["evidence_ids"]) > 0
        assert_no_forbidden_text(f)
        
        summary = f["summary"].lower()
        recommendation = f["recommendation"].lower()
        for word in ["order placed", "supplier selected", "purchase approved", "message sent"]:
            assert word not in summary
            assert word not in recommendation


def test_procurement_agent_field_employee_hides_pricing_and_financials():
    agent = ProcurementAgent()
    work_item = make_work_item("weekly_plan_pvf")
    context = make_context(user_role="field_employee", farm_type="row_crop")
    
    quotes = [{
        "result_id": "res_quote_PVF_QUOTE_DIESEL_2026_06_21",
        "source_id": "src_diesel",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential",
        "payload": {
            "input_type": "diesel",
            "price_per_gallon": 3.10
        }
    }]
    
    res = agent.run(work_item, context, quotes, [])
    findings = normalize_findings(res)
    
    for f in findings:
        assert_field_employee_safe(f)


def test_records_inventory_agent_returns_contract_shaped_bin_or_yield_finding():
    agent = RecordsInventoryAgent()
    work_item = make_work_item("bin_reconciliation")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    grain_bin_inventory = [{
        "result_id": "res_bin_PVF_BIN_003",
        "source_id": "src_bin",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential",
        "payload": {
            "bin_id": "Bin 3",
            "crop": "corn",
            "quantity": 15000
        }
    }]
    
    res = agent.run(work_item, context, [], grain_bin_inventory=grain_bin_inventory)
    findings = normalize_findings(res)
    
    assert len(findings) > 0
    for f in findings:
        assert_contract_finding_shape(f)
        assert "res_bin_PVF_BIN_003" in f["evidence_ids"]
        assert_no_forbidden_text(f)
        
        serialized = json.dumps(f).lower()
        for forbidden in ["inventory updated", "official record updated", "grain sold", "filed with regulator"]:
            assert forbidden not in serialized


def test_records_inventory_agent_lane_boundary_returns_none_for_market_topic():
    agent = RecordsInventoryAgent()
    work_item = make_work_item("grain_sale_watch")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    res = agent.run(work_item, context, [])
    assert res is None


def test_market_sales_agent_returns_contract_shaped_stored_grain_watch():
    agent = MarketSalesAgent()
    work_item = make_work_item("grain_sale_watch")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    grain_bin_inventory = [{
        "result_id": "res_bin_PVF_BIN_001",
        "source_id": "src_bin",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential",
        "payload": {
            "bin_id": "Bin 1",
            "crop": "corn",
            "quantity": 42000
        }
    }]
    
    res = agent.run(work_item, context, grain_bin_inventory=grain_bin_inventory)
    findings = normalize_findings(res)
    
    assert len(findings) > 0
    for f in findings:
        assert_contract_finding_shape(f)
        assert "local bid and basis data" in f["missing_data"] or "local_bid" in f["missing_data"] or "local bid/basis data" in f["missing_data"] or any("bid" in m for m in f["missing_data"])
        assert_no_forbidden_text(f)
        
        serialized = json.dumps(f).lower()
        forbidden = ["sell now", "hold grain", "hedge now", "lock in price", "buyer contacted", "sale executed", "invoice sent"]
        for word in forbidden:
            assert word not in serialized


def test_market_sales_agent_public_context_is_advisory_only():
    agent = MarketSalesAgent()
    work_item = make_work_item("weekly_plan_gbo", farm_id="GBO_DIRECT_001")
    context = make_context(user_role="farm_owner", farm_type="small_organic_direct_market")
    
    market_report = {
        "result_id": "res_benchmark_ams",
        "source_id": "src_ams",
        "trust_tier": "public_context",
        "freshness_status": "fresh",
        "privacy_class": "Public Context",
        "payload": {
            "reports": {
                "tomatoes": {"regional_wholesale_price_per_lb": 2.40, "market_tone": "steady"}
            }
        }
    }
    
    res = agent.run(work_item, context, market_report=market_report)
    findings = normalize_findings(res)
    
    for f in findings:
        assert "USDA AMS" in f["summary"]
        assert "advisory" in f["summary"].lower() or "context only" in f["summary"].lower() or "context" in f["summary"].lower()
        assert "anchor" in f["summary"].lower() or "commitments" in f["summary"].lower() or "sales records" in f["summary"].lower()


def test_market_sales_agent_field_employee_hides_customer_and_payment_details():
    agent = MarketSalesAgent()
    work_item = make_work_item("sales_reconciliation_check", farm_id="GBO_DIRECT_001")
    context = make_context(user_role="field_employee", farm_type="small_organic_direct_market")
    
    sales_records = [{
        "result_id": "res_sal_GBO_SAL_001",
        "source_id": "src_sal",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential",
        "payload": {
            "customer_name": "Green Bistro",
            "payment_status": "partially_reconciled",
            "gross_amount": 495.00
        }
    }]
    
    res = agent.run(work_item, context, sales_records=sales_records)
    findings = normalize_findings(res)
    
    for f in findings:
        assert_field_employee_safe(f)


def test_compliance_agent_returns_contract_shaped_review_finding():
    agent = ComplianceAgent()
    work_item = make_work_item("crop_insurance_caution")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    res = agent.run(work_item, context)
    findings = normalize_findings(res)
    
    assert len(findings) > 0
    for f in findings:
        assert_contract_finding_shape(f)
        assert f["human_review"]["required"] is True
        assert_no_forbidden_text(f)
        
        serialized = json.dumps(f).lower()
        forbidden = ["filed with fsa", "filed with regulator", "organic input approved", "official record updated"]
        for word in forbidden:
            assert word not in serialized


def test_compliance_agent_pesticide_sensitive_topic_is_safe():
    agent = ComplianceAgent()
    work_item = make_work_item("spray_window")
    context = make_context(user_role="farm_owner", farm_type="row_crop")
    
    res = agent.run(work_item, context)
    findings = normalize_findings(res)
    
    for f in findings:
        assert_no_forbidden_text(f)
        recommendation = f["recommendation"].lower()
        for word in ["pesticide product", "tank-mix advice", "treatment timing"]:
            assert word not in recommendation


def test_margin_scenario_agent_returns_math_only_contract_finding():
    agent = MarginScenarioAgent()
    work_item = make_work_item("harvest_shrink_tracking", farm_id="GBO_DIRECT_001")
    context = make_context(user_role="farm_owner", farm_type="small_organic_direct_market")
    
    harvest_events = [{
        "result_id": "res_harv_GBO_HARV_001",
        "source_id": "src_harv",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential",
        "payload": {
            "lot_number": "GBO_TOM_001",
            "quantity_harvested": 120,
            "marketable_quantity": 100,
            "cull_quantity": 20
        }
    }]
    
    res = agent.run(work_item, context, harvest_events=harvest_events)
    findings = normalize_findings(res)
    
    assert len(findings) > 0
    for f in findings:
        assert_contract_finding_shape(f)
        assert "res_harv_GBO_HARV_001" in f["evidence_ids"]
        assert_no_forbidden_text(f)
        
        serialized = json.dumps(f).lower()
        forbidden = ["buying", "selling", "hedging", "lock in price"]
        for word in forbidden:
            assert word not in serialized


def test_margin_scenario_agent_field_employee_hides_cost_or_margin_details():
    agent = MarginScenarioAgent()
    work_item = make_work_item("weekly_plan_pvf")
    context = make_context(user_role="field_employee", farm_type="row_crop")
    
    res = agent.run(work_item, context)
    findings = normalize_findings(res)
    
    for f in findings:
        assert_field_employee_safe(f)


def test_representative_specialist_outputs_all_normalize_to_contract_shape():
    mock_weather_obs = {
        "result_id": "res_weather_mock_001",
        "source_id": "src_weather",
        "trust_tier": "public_context",
        "freshness_status": "fresh",
        "privacy_class": "Public Context",
        "payload": {
            "summary": "Rain and wind may constrain fieldwork."
        }
    }
    
    agents = [
        # agent, work_item, context, args
        (WeatherFieldworkAgent(), make_work_item("weekly_plan_pvf"), make_context(), [mock_weather_obs]),
        (ProcurementAgent(), make_work_item("diesel_purchase_window"), make_context(), [[], []]),
        (RecordsInventoryAgent(), make_work_item("bin_reconciliation"), make_context(), [[]]),
        (MarketSalesAgent(), make_work_item("grain_sale_watch"), make_context(), []),
        (ComplianceAgent(), make_work_item("crop_insurance_caution"), make_context(), []),
        (MarginScenarioAgent(), make_work_item("harvest_shrink_tracking", farm_id="GBO_DIRECT_001"), make_context(farm_type="small_organic_direct_market"), [])
    ]
    
    for agent, work_item, context, args in agents:
        res = agent.run(work_item, context, *args)
        findings = normalize_findings(res)
        
        for f in findings:
            normalized = assert_contract_finding_shape(f)
            assert isinstance(normalized["evidence_ids"], list)
            assert isinstance(normalized["missing_data"], list)
            assert isinstance(normalized["proposed_actions"], list)
            assert len(normalized["proposed_actions"]) == 0
            assert isinstance(normalized["blocked_actions"], list)
            assert_no_forbidden_text(normalized)
