# tests/test_market_sales_agent_harvest.py
"""Tests for MarketSalesAgent behavior in harvest and sales domain."""
import pytest
from harvestamp.agents.market_sales import MarketSalesAgent

def test_market_sales_agent_csa_packout():
    agent = MarketSalesAgent()
    work_item = {
        "work_item_id": "wi_m1",
        "workflow_id": "wf_m1",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "csa_packout_check"
    }
    context = {"topic": "csa_packout_check", "user_role": "farm_owner"}
    
    commitments = [
        {"result_id": "res_com_GBO_COM_001", "source_id": "DS-022", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Restricted", "payload": {}}
    ]
    inv = [
        {"result_id": "res_phi_GBO_PHI_002", "source_id": "DS-021", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {}}
    ]
    
    f = agent.run(work_item, context, sales_commitments=commitments, post_harvest_inventory=inv)
    assert f["topic"] == "direct_market_sales"
    assert "CSA packout check" in f["summary"]
    assert "Shortage is 27.0 bags" in f["summary"]
    assert "Wednesday packout" in f["recommendation"]

def test_market_sales_agent_restaurant_fulfillment():
    agent = MarketSalesAgent()
    work_item = {
        "work_item_id": "wi_m2",
        "workflow_id": "wf_m2",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "restaurant_fulfillment_check"
    }
    context = {"topic": "restaurant_fulfillment_check", "user_role": "farm_owner"}
    
    commitments = [
        {"result_id": "res_com_GBO_COM_002", "source_id": "DS-022", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Restricted", "payload": {}}
    ]
    inv = [
        {"result_id": "res_phi_GBO_PHI_001", "source_id": "DS-021", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {}},
        {"result_id": "res_phi_GBO_PHI_002", "source_id": "DS-021", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {}}
    ]
    
    f = agent.run(work_item, context, sales_commitments=commitments, post_harvest_inventory=inv)
    assert "Restaurant order fulfillment check" in f["summary"]
    assert "shortage of 7.0 bags" in f["summary"]

def test_market_sales_agent_farmers_market_returns():
    agent = MarketSalesAgent()
    work_item = {
        "work_item_id": "wi_m3",
        "workflow_id": "wf_m3",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "farmers_market_reconciliation"
    }
    context = {"topic": "farmers_market_reconciliation", "user_role": "farm_owner"}
    
    f = agent.run(work_item, context)
    assert f["topic"] == "farmers_market"
    assert "returned inventory" in f["summary"].lower()
    assert "squash 20.0 lbs returned" in f["summary"]
    assert "reconciliation" in f["recommendation"].lower() or "sales record" in f["recommendation"].lower()

def test_market_sales_agent_sales_reconciliation():
    agent = MarketSalesAgent()
    work_item = {
        "work_item_id": "wi_m4",
        "workflow_id": "wf_m4",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "sales_reconciliation_check"
    }
    context = {"topic": "sales_reconciliation_check", "user_role": "farm_owner"}
    
    f = agent.run(work_item, context)
    assert "$495.00" in f["summary"]
    assert "partially_reconciled" in f["summary"]
    assert "draft/blocked pending review" in f["summary"]
    
    # Employee view (redacted)
    emp_context = {"topic": "sales_reconciliation_check", "user_role": "field_employee"}
    f_emp = agent.run(work_item, emp_context)
    assert "$495.00" not in f_emp["summary"]
    assert "hidden" in f_emp["summary"]
    assert "Authorized operational records" in f_emp["evidence_ids"]

def test_market_sales_agent_grain_watch():
    agent = MarketSalesAgent()
    work_item = {
        "work_item_id": "wi_m5",
        "workflow_id": "wf_m5",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "grain_sale_watch"
    }
    context = {"topic": "grain_sale_watch", "user_role": "farm_owner"}
    
    f = agent.run(work_item, context)
    assert "grain sale watch" in f["summary"].lower()
    assert "42,000.0" in f["summary"]
    assert "blocked due to missing local bid/basis data" in f["recommendation"]
    assert "local bid and basis data" in f["missing_data"]

def test_market_sales_agent_elevator_delivery():
    agent = MarketSalesAgent()
    work_item = {
        "work_item_id": "wi_m6",
        "workflow_id": "wf_m6",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "elevator_delivery_draft"
    }
    context = {"topic": "elevator_delivery_draft", "user_role": "farm_owner"}
    
    f = agent.run(work_item, context)
    assert "elevator delivery and settlement" in f["summary"].lower()
    assert "4,700.0" in f["summary"]
    assert "draft/blocked pending review" in f["summary"]
