# tests/test_records_inventory_harvest.py
"""Tests for RecordsInventoryAgent behavior in harvest and yield domain."""
import pytest
from harvestamp.agents.records_inventory import RecordsInventoryAgent

def test_records_inventory_agent_harvest_log():
    agent = RecordsInventoryAgent()
    work_item = {
        "work_item_id": "wi_001",
        "workflow_id": "wf_001",
        "farm_id": "GBO_DIRECT_001",
        "requesting_user_id": "gbo_owner_001",
        "topic": "harvest_log_entry"
    }
    context = {"topic": "harvest_log_entry", "user_role": "farm_owner"}
    
    harvest_events = [
        {"result_id": "res_harv_GBO_HARV_001", "source_id": "DS-020", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {}}
    ]
    
    f = agent.run(work_item, context, [], harvest_events=harvest_events)
    assert f["topic"] == "harvest_records"
    assert "Draft cooler inventory updates" in f["summary"]
    assert "draft/blocked pending review" in f["summary"]
    assert "Reconcile harvest logs" in f["recommendation"]
    assert "res_harv_GBO_HARV_001" in f["evidence_ids"]

def test_records_inventory_agent_load_ticket():
    agent = RecordsInventoryAgent()
    
    # Farm owner view
    work_item = {
        "work_item_id": "wi_002",
        "workflow_id": "wf_002",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "load_ticket_intake"
    }
    context = {"topic": "load_ticket_intake", "user_role": "farm_owner"}
    tickets = [
        {"result_id": "res_tkt_PVF_TKT_001", "source_id": "DS-024", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {"destination": "Bin 1", "moisture_percent": 15.5}}
    ]
    
    f = agent.run(work_item, context, [], grain_load_tickets=tickets)
    assert "Bin 1" in f["summary"]
    assert "1,000" in f["summary"]
    assert "draft/blocked pending review" in f["summary"]
    
    # Field employee view (redacted destination)
    emp_context = {"topic": "load_ticket_intake", "user_role": "field_employee"}
    tickets_redacted = [
        {"result_id": "Authorized operational records", "source_id": "DS-024", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {"destination": "[REDACTED destination]"}}
    ]
    f_emp = agent.run(work_item, emp_context, [], grain_load_tickets=tickets_redacted)
    assert "Bin 1" not in f_emp["summary"]
    assert "Authorized operational records" in f_emp["evidence_ids"]
    assert "buyer_settlement_details" in f_emp["prohibited_disclosures"]

def test_records_inventory_agent_yield_summary():
    agent = RecordsInventoryAgent()
    work_item = {
        "work_item_id": "wi_003",
        "workflow_id": "wf_003",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "field_yield_summary"
    }
    context = {"topic": "field_yield_summary", "user_role": "farm_owner"}
    yields = [
        {"result_id": "res_yld_PVF_YLD_003", "source_id": "DS-026", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {"yield_record_id": "PVF_YLD_003"}}
    ]
    
    f = agent.run(work_item, context, [], yield_records=yields)
    assert "Field C adjusted quantity" in f["missing_data"]
    assert "Field C dockage/shrink" in f["missing_data"]
    assert f["human_review"]["status"] == "needs_info"

def test_records_inventory_agent_bin_reconciliation():
    agent = RecordsInventoryAgent()
    work_item = {
        "work_item_id": "wi_004",
        "workflow_id": "wf_004",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "bin_reconciliation"
    }
    context = {"topic": "bin_reconciliation", "user_role": "farm_owner"}
    bins = [
        {"result_id": "res_bin_PVF_BIN_003", "source_id": "DS-025", "trust_tier": "T3 User-entered", "freshness_status": "fresh", "privacy_class": "Farm Confidential", "payload": {}}
    ]
    
    f = agent.run(work_item, context, [], grain_bin_inventory=bins)
    assert "Bin 3" in f["summary"]
    assert "out_of_sync" in f["summary"]
    assert "status draft/blocked pending review" in f["summary"]
