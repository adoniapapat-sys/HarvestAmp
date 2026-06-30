# tests/test_contract_normalization_integration.py
"""Contract normalization integration tests."""
import json
import pytest
from harvestamp.agents.synthesizer import RecommendationSynthesizer
from harvestamp.core.contracts import (
    ACTION_PACK_FIELDS,
    AGENT_FINDING_FIELDS,
    contains_forbidden_wording,
    has_required_action_pack_fields,
    has_required_agent_finding_fields,
    normalize_action_pack_contract,
    normalize_agent_finding_contract,
)


def make_evidence(evidence_id: str) -> dict:
    """Helper to return a minimal evidence metadata dict."""
    return {
        "evidence_id": evidence_id,
        "source_id": "src_test",
        "source_name": "Test Source",
        "trust_tier": "farm_record",
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential"
    }


def test_agent_finding_contract_includes_finding_id():
    assert "finding_id" in AGENT_FINDING_FIELDS


def test_normalize_agent_finding_contract_supplies_finding_id_key_without_inventing_id():
    finding = {
        "agent": "records_inventory",
        "lane": "records_inventory",
        "topic": "bin_reconciliation",
        "finding_type": "draft_bin_reconciliation",
        "summary": "Bin 3 needs reconciliation.",
        "evidence_ids": ["res_bin_PVF_BIN_003"],
    }
    
    normalized = normalize_agent_finding_contract(finding)
    
    assert "finding_id" in normalized
    assert normalized["finding_id"] is None
    assert normalized["summary"] == "Bin 3 needs reconciliation."
    assert has_required_agent_finding_fields(normalized) is True


def test_actionpack_normalization_preserves_existing_values():
    action_pack = {
        "farm_id": "PVF_ROW_CROP_001",
        "workflow_id": "weekly_plan",
        "recommendations": ["Review Bin 3 reconciliation."],
    }
    
    normalized = normalize_action_pack_contract(action_pack)
    
    for field in ACTION_PACK_FIELDS:
        assert field in normalized
        
    assert has_required_action_pack_fields(normalized) is True
    assert normalized["farm_id"] == "PVF_ROW_CROP_001"
    assert normalized["workflow_id"] == "weekly_plan"
    assert normalized["recommendations"] == ["Review Bin 3 reconciliation."]
    assert normalized["status"] == "draft"
    assert normalized["proposed_actions"] == []
    assert normalized["evidence_summary"] == []
    assert normalized["missing_data"] == []
    assert normalized["human_review_status"] == {}


def test_synthesizer_accepts_findings_missing_optional_contract_fields_after_boundary_normalization():
    # Finding is missing optional fields like proposed_actions, assumptions, etc.
    finding = {
        "finding_id": "finding_records_minimal_001",
        "agent": "records_inventory",
        "lane": "records_inventory",
        "topic": "bin_reconciliation",
        "finding_type": "draft_bin_reconciliation",
        "summary": "Bin 3 needs reconciliation.",
        "recommendation": "Review Bin 3 reconciliation before any official record update.",
        "evidence_ids": ["res_bin_PVF_BIN_003"],
    }
    
    synthesizer = RecommendationSynthesizer()
    action_pack = synthesizer.synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=[make_evidence("res_bin_PVF_BIN_003")],
        user_role="farm_owner",
    )
    
    assert has_required_action_pack_fields(action_pack) is True
    assert isinstance(action_pack["missing_data"], list)
    assert isinstance(action_pack["warnings"], list)
    assert isinstance(action_pack["human_review_status"], dict)


def test_synthesizer_preserves_valid_finding_values_after_normalization():
    finding = {
        "finding_id": "finding_records_001",
        "agent": "records_inventory",
        "lane": "records_inventory",
        "topic": "bin_reconciliation",
        "finding_type": "draft_bin_reconciliation",
        "summary": "Bin 3 needs reconciliation.",
        "recommendation": "Review Bin 3 reconciliation before any official record update.",
        "evidence_ids": ["res_bin_PVF_BIN_003"],
        "missing_data": ["variance_reason"],
        "confidence": "medium",
        "human_review": {
            "required": True,
            "review_type": "user_approval",
            "status": "needs_user_approval",
            "recommended_reviewers": ["farm_owner"]
        }
    }
    
    synthesizer = RecommendationSynthesizer()
    action_pack = synthesizer.synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=[make_evidence("res_bin_PVF_BIN_003")],
        user_role="farm_owner",
    )
    
    assert action_pack["farm_id"] == "PVF_ROW_CROP_001"
    assert action_pack["workflow_id"] == "weekly_plan"
    assert "variance_reason" in action_pack["missing_data"]
    assert any(e["evidence_id"] == "res_bin_PVF_BIN_003" for e in action_pack["evidence_summary"])
    assert any("bin 3" in r["summary"].lower() for r in action_pack["recommendations"])
    assert has_required_action_pack_fields(action_pack) is True


def test_synthesizer_return_is_actionpack_normalized():
    finding = {
        "finding_id": "finding_records_001",
        "agent": "records_inventory",
        "lane": "records_inventory",
        "topic": "bin_reconciliation",
        "finding_type": "draft_bin_reconciliation",
        "summary": "Bin 3 needs reconciliation.",
        "recommendation": "Review Bin 3 reconciliation.",
        "evidence_ids": ["res_bin_PVF_BIN_003"],
    }
    
    synthesizer = RecommendationSynthesizer()
    action_pack = synthesizer.synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=[make_evidence("res_bin_PVF_BIN_003")],
        user_role="farm_owner",
    )
    
    # Assert every ActionPack contract field exists directly in returned dictionary
    for field in ACTION_PACK_FIELDS:
        assert field in action_pack
    assert has_required_action_pack_fields(action_pack) is True


def test_normalization_integration_does_not_create_executed_or_advisor_wording():
    finding = {
        "finding_id": "finding_records_001",
        "agent": "records_inventory",
        "lane": "records_inventory",
        "topic": "bin_reconciliation",
        "finding_type": "draft_bin_reconciliation",
        "summary": "Bin 3 needs reconciliation.",
        "recommendation": "Review Bin 3 reconciliation.",
        "evidence_ids": ["res_bin_PVF_BIN_003"],
    }
    
    synthesizer = RecommendationSynthesizer()
    action_pack = synthesizer.synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=[make_evidence("res_bin_PVF_BIN_003")],
        user_role="farm_owner",
    )
    
    serialized = json.dumps(action_pack, sort_keys=True)
    assert contains_forbidden_wording(serialized) == []
    
    forbidden = [
        "email sent", "message sent", "order placed", "sale executed",
        "invoice sent", "official record updated", "inventory updated"
    ]
    for phrase in forbidden:
        assert phrase not in serialized.lower()
