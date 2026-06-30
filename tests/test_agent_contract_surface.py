# tests/test_agent_contract_surface.py
"""Tests for the HarvestAmp agent contract surface definitions and helpers."""
from harvestamp.core.contracts import (
    AGENT_FINDING_FIELDS,
    ACTION_PACK_FIELDS,
    SOURCE_SCOPE_VALUES,
    DRAFT_ONLY_ACTION_TYPES,
    MVP_ACTION_STATUSES,
    normalize_agent_finding_contract,
    has_required_agent_finding_fields,
    normalize_action_pack_contract,
    has_required_action_pack_fields,
    contains_forbidden_wording
)


def test_normalize_agent_finding_contract_adds_fields_without_inventing_facts():
    # 1. Input finding
    raw_finding = {
        "agent": "records_inventory",
        "lane": "records_inventory",
        "finding_type": "draft_bin_reconciliation",
        "summary": "Bin 3 needs reconciliation.",
        "evidence_ids": ["res_bin_PVF_BIN_003"],
    }
    
    normalized = normalize_agent_finding_contract(raw_finding)
    
    # Assert all AGENT_FINDING_FIELDS exist
    for field in AGENT_FINDING_FIELDS:
        assert field in normalized
        
    # Assert existing values are preserved
    assert normalized["agent"] == "records_inventory"
    assert normalized["lane"] == "records_inventory"
    assert normalized["finding_type"] == "draft_bin_reconciliation"
    assert normalized["summary"] == "Bin 3 needs reconciliation."
    assert normalized["evidence_ids"] == ["res_bin_PVF_BIN_003"]
    
    # Assert default values are applied correctly
    assert normalized["missing_data"] == []
    assert normalized["proposed_actions"] == []
    assert normalized["blocked_actions"] == []
    assert normalized["public_context_only"] is False
    assert normalized["source_scope"] == "farm_record"
    assert normalized["farm_record_anchor"] is None
    assert normalized["confidence"] == "medium"


def test_normalize_agent_finding_contract_derives_review_required_and_reviewers():
    # 2. Input finding with human_review nested dictionary
    raw_finding = {
        "agent": "records_inventory",
        "summary": "Review required.",
        "human_review": {
            "required": True,
            "recommended_reviewers": ["farm_owner", "farm_manager"]
        }
    }
    
    normalized = normalize_agent_finding_contract(raw_finding)
    
    assert normalized["review_required"] is True
    assert normalized["recommended_reviewers"] == ["farm_owner", "farm_manager"]
    
    # Check alternate "reviewers" fallback in human_review
    raw_finding_alt = {
        "agent": "records_inventory",
        "summary": "Review required.",
        "human_review": {
            "required": True,
            "reviewers": ["farm_manager"]
        }
    }
    
    normalized_alt = normalize_agent_finding_contract(raw_finding_alt)
    assert normalized_alt["review_required"] is True
    assert normalized_alt["recommended_reviewers"] == ["farm_manager"]


def test_has_required_agent_finding_fields_accepts_normalized_finding():
    # 3. Market sales stored grain watch finding
    raw_finding = {
        "agent": "market_sales",
        "lane": "commodity_markets",
        "finding_type": "stored_grain_watch",
        "summary": "Stored corn in Bin 1.",
        "evidence_ids": ["res_grain_PVF_BIN_001"],
        "missing_data": ["local_bid", "local_basis"],
        "blocked_actions": ["no_sale_recommendation_without_current_farm_authorized_bid_basis"]
    }
    
    normalized = normalize_agent_finding_contract(raw_finding)
    assert has_required_agent_finding_fields(normalized) is True


def test_normalize_action_pack_contract_adds_fields_without_inventing_facts():
    # 4. Input ActionPack dict
    raw_action_pack = {
        "farm_id": "PVF_ROW_CROP_001",
        "workflow_id": "weekly_plan",
        "recommendations": ["Review Bin 3 reconciliation."],
    }
    
    normalized = normalize_action_pack_contract(raw_action_pack)
    
    # Assert all ACTION_PACK_FIELDS exist
    for field in ACTION_PACK_FIELDS:
        assert field in normalized
        
    # Assert provided values are preserved
    assert normalized["farm_id"] == "PVF_ROW_CROP_001"
    assert normalized["workflow_id"] == "weekly_plan"
    assert normalized["recommendations"] == ["Review Bin 3 reconciliation."]
    
    # Assert default values are applied correctly
    assert normalized["proposed_actions"] == []
    assert normalized["evidence_summary"] == []
    assert normalized["missing_data"] == []
    assert normalized["human_review_status"] == {}
    assert normalized["status"] == "draft"


def test_has_required_action_pack_fields_accepts_normalized_action_pack():
    # 5. Full ActionPack validation
    raw_action_pack = {
        "action_pack_id": "ap_PVF_001",
        "farm_id": "PVF_ROW_CROP_001",
        "workflow_id": "weekly_plan",
        "recommendations": [],
        "proposed_actions": [],
        "evidence_summary": [],
        "warnings": [],
        "missing_data": [],
        "human_review_status": {},
        "status": "draft"
    }
    
    normalized = normalize_action_pack_contract(raw_action_pack)
    assert has_required_action_pack_fields(normalized) is True


def test_contains_forbidden_wording_catches_execution_and_advisor_drift():
    # 6. Prohibited text test
    text = "Order placed. You should sell now and lock in price."
    matches = contains_forbidden_wording(text)
    
    assert "order placed" in matches
    assert "sell now" in matches
    assert "lock in price" in matches


def test_draft_only_action_types_includes_current_harvest_and_record_actions():
    # 7. Action types list checks
    expected_actions = [
        "supplier_message",
        "customer_message",
        "certifier_message",
        "draft_official_record_update",
        "draft_bin_reconciliation",
        "draft_cooler_inventory_update",
        "draft_sales_record_reconciliation",
        "draft_grain_load_ticket_record",
        "draft_elevator_settlement_record",
        "draft_harvest_record_update"
    ]
    for action_type in expected_actions:
        assert action_type in DRAFT_ONLY_ACTION_TYPES


def test_source_scope_values_includes_expected():
    # 8. Source scopes checklist
    expected_scopes = [
        "farm_record",
        "public_context",
        "document_extraction",
        "fixture",
        "mixed"
    ]
    for scope in expected_scopes:
        assert scope in SOURCE_SCOPE_VALUES


def test_mvp_action_statuses_includes_expected():
    # 9. Action statuses checklist
    expected_statuses = [
        "draft",
        "needs_info",
        "needs_user_approval",
        "needs_expert_review",
        "blocked_pending_user_approval",
        "approved_simulated",
        "rejected",
        "not_executed"
    ]
    for status in expected_statuses:
        assert status in MVP_ACTION_STATUSES
