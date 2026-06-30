# tests/test_action_gating_contract.py
"""Contract tests for human review policy and action gating."""
import json
import pytest
from harvestamp.agents.action_agent import ActionAgent
from harvestamp.policy.action_gate import ActionGate
from harvestamp.policy.human_review_policy import HumanReviewPolicy
from harvestamp.core.contracts import (
    DRAFT_ONLY_ACTION_TYPES,
    MVP_ACTION_STATUSES,
    contains_forbidden_wording
)


def make_human_review(
    required=True,
    review_type="user_approval",
    status="needs_user_approval",
    approval_required_before=None,
    recommended_reviewer=None,
):
    """Returns a human_review dict compatible with ActionGate/ActionAgent."""
    return {
        "required": required,
        "review_type": review_type,
        "status": status,
        "reason": ["reconcile_sales_records"] if required else [],
        "recommended_reviewer": recommended_reviewer or ["farm_owner"],
        "approval_required_before": approval_required_before or ["commit_to_official_records"]
    }


def make_action(
    action_type="draft_official_record_update",
    status="needs_user_approval",
    external_action=False,
    evidence_ids=None,
    requires_approval=True,
    human_review_status=None,
):
    """Returns a proposed action dictionary matching the current action shape."""
    evs = evidence_ids or ["res_yld_PVF_YLD_001"]
    hr_status = human_review_status or make_human_review(required=requires_approval, status=status)
    return {
        "action_id": f"act_{action_type}_test",
        "action_type": action_type,
        "external_action": external_action,
        "status": status,
        "evidence_ids": evs,
        "payload": {
            "status": status,
            "requires_approval": requires_approval,
            "external_action": external_action,
            "farm_id": "PVF_ROW_CROP_001",
            "record_type": "yield_record",
            "source_evidence_id": evs[0] if evs else "unknown",
            "related_evidence": evs
        },
        "human_review_status": hr_status
    }


def test_action_gate_blocks_unapproved_draft_action():
    action = make_action(
        action_type="draft_official_record_update",
        status="needs_user_approval",
        requires_approval=True,
        evidence_ids=["res_yld_PVF_YLD_001"]
    )
    
    gate = ActionGate()
    is_allowed, gate_msg = gate.verify_action_execution(
        action_payload=action,
        human_review_status=action["human_review_status"],
        user_has_permission=True
    )
    
    assert is_allowed is False
    assert "human review required" in gate_msg
    assert contains_forbidden_wording(gate_msg) == []
    
    agent = ActionAgent(action_gate=gate)
    with pytest.raises(PermissionError) as excinfo:
        agent.execute_action(action, action["human_review_status"], user_has_permission=True)
        
    assert "human review required" in str(excinfo.value)
    assert contains_forbidden_wording(str(excinfo.value)) == []


def test_action_gate_allows_approved_simulated_action_only_with_permission():
    action = make_action(
        action_type="draft_official_record_update",
        status="approved",
        requires_approval=True,
        evidence_ids=["res_yld_PVF_YLD_001"]
    )
    
    gate = ActionGate()
    is_allowed, gate_msg = gate.verify_action_execution(
        action_payload=action,
        human_review_status=action["human_review_status"],
        user_has_permission=True
    )
    assert is_allowed is True
    
    agent = ActionAgent(action_gate=gate)
    success, exec_msg = agent.execute_action(
        action_payload=action,
        human_review_status=action["human_review_status"],
        user_has_permission=True
    )
    assert success is True
    assert "executed successfully" in exec_msg
    assert contains_forbidden_wording(exec_msg) == []


def test_action_gate_blocks_unauthorized_role_even_if_status_approved():
    action = make_action(
        action_type="draft_official_record_update",
        status="approved",
        requires_approval=True,
        evidence_ids=["res_yld_PVF_YLD_001"]
    )
    
    agent = ActionAgent()
    with pytest.raises(PermissionError) as excinfo:
        agent.execute_action(
            action_payload=action,
            human_review_status=action["human_review_status"],
            user_has_permission=False
        )
        
    assert "user lacks required authorization" in str(excinfo.value)
    assert contains_forbidden_wording(str(excinfo.value)) == []


def test_draft_only_action_types_are_never_executed_without_approval():
    gate = ActionGate()
    for action_type in DRAFT_ONLY_ACTION_TYPES:
        action = make_action(
            action_type=action_type,
            status="needs_user_approval",
            requires_approval=True
        )
        
        is_allowed, gate_msg = gate.verify_action_execution(
            action_payload=action,
            human_review_status=action["human_review_status"],
            user_has_permission=True
        )
        assert is_allowed is False
        assert contains_forbidden_wording(gate_msg) == []


def test_missing_evidence_blocks_or_requires_info_for_record_action():
    action = make_action(
        action_type="draft_official_record_update",
        status="needs_info",
        evidence_ids=[],
        requires_approval=True
    )
    
    gate = ActionGate()
    is_allowed, gate_msg = gate.verify_action_execution(
        action_payload=action,
        human_review_status=action["human_review_status"],
        user_has_permission=True
    )
    
    assert is_allowed is False
    assert "human review required" in gate_msg
    assert contains_forbidden_wording(gate_msg) == []


def test_human_review_policy_missing_data_demotes_to_needs_info():
    policy = HumanReviewPolicy()
    
    # Using topic "commodity_markets" and matching summary details for grain sale watch
    finding = {
        "finding_id": "finding_missing_bid_basis",
        "topic": "commodity_markets",
        "summary": "Stored grain watch: Bin 1 corn.",
        "confidence": "medium",
        "missing_data": ["local_bid", "local_basis"],
        "evidence_ids": ["res_grain_PVF_BIN_001"]
    }
    
    hr = policy.evaluate_finding(finding, user_role="farm_owner")
    
    assert hr["required"] is True
    assert hr["status"] == "needs_info"
    
    blockers = hr.get("approval_required_before", [])
    assert "provide_local_bid" in blockers
    assert "provide_local_basis" in blockers
    
    assert contains_forbidden_wording(json.dumps(hr)) == []


def test_human_review_policy_low_confidence_requires_review_or_needs_info():
    policy = HumanReviewPolicy()
    
    # Using topic "packaging_reorder" for low confidence stale inventory trigger
    finding = {
        "finding_id": "f_low_conf",
        "topic": "packaging_reorder",
        "confidence": "low",
        "missing_data": ["invoice_total", "supplier_terms"],
        "evidence_ids": ["res_doc_DOC_005"]
    }
    
    hr = policy.evaluate_finding(finding, user_role="farm_owner")
    
    assert hr["status"] == "needs_info"
    assert contains_forbidden_wording(json.dumps(hr)) == []


def test_human_review_policy_sensitive_topics_require_expert_or_user_review():
    policy = HumanReviewPolicy()
    
    # 1. FSA Production record / crop insurance warning topic in compliance_records
    finding_fsa = {
        "finding_id": "f_fsa",
        "topic": "compliance_records",
        "summary": "crop insurance and production-record compliance: warning",
        "confidence": "high",
        "evidence_ids": ["res_yld_PVF_YLD_001"]
    }
    hr_fsa = policy.evaluate_finding(finding_fsa, user_role="farm_owner")
    assert hr_fsa["required"] is True
    assert hr_fsa["status"] == "needs_expert_review"
    assert contains_forbidden_wording(json.dumps(hr_fsa)) == []
    
    # 2. Pesticide / spray treatment topic
    finding_spray = {
        "finding_id": "f_spray",
        "topic": "spray_window",
        "confidence": "high",
        "evidence_ids": ["res_health_watchlist"]
    }
    hr_spray = policy.evaluate_finding(finding_spray, user_role="farm_owner")
    assert hr_spray["required"] is True
    assert hr_spray["status"] == "needs_expert_review"
    assert contains_forbidden_wording(json.dumps(hr_spray)) == []


def test_action_statuses_are_local_or_review_states():
    actions = [
        make_action(action_type="draft_bin_reconciliation", status="draft"),
        make_action(action_type="draft_cooler_inventory_update", status="needs_info"),
        make_action(action_type="draft_sales_record_reconciliation", status="needs_user_approval"),
        make_action(action_type="draft_elevator_settlement_record", status="blocked_pending_user_approval"),
        make_action(action_type="supplier_message", status="approved")
    ]
    
    allowed_repo_statuses = MVP_ACTION_STATUSES + [
        "approved",
        "approved_with_edits",
        "review_not_required",
        "blocked",
        "blocked_pending_user_approval",
        "needs_soft_confirmation",
        "needs_admin_review"
    ]
    
    for act in actions:
        status = act["status"]
        assert status in allowed_repo_statuses
        
        for forbidden_term in ["sent", "filed", "ordered", "sold", "contacted", "updated", "executed"]:
            assert forbidden_term not in status.lower()
