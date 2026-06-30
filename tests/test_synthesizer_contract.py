# tests/test_synthesizer_contract.py
"""Contract tests for the RecommendationSynthesizer."""
import json
import pytest
from harvestamp.agents.synthesizer import RecommendationSynthesizer
from harvestamp.core.contracts import (
    MVP_ACTION_STATUSES,
    RESTRICTED_FIELD_EMPLOYEE_TERMS,
    contains_forbidden_wording,
    has_required_action_pack_fields,
    normalize_action_pack_contract,
)


def make_finding(
    finding_id,
    agent="records_inventory",
    lane="records_inventory",
    topic="bin_reconciliation",
    finding_type="draft_bin_reconciliation",
    summary="Summary text",
    recommendation="Rec text",
    evidence_ids=None,
    missing_data=None,
    confidence="medium",
    human_review=None,
    source_scope="farm_record",
    public_context_only=False
):
    """Helper to construct a minimal AgentFinding dict."""
    return {
        "finding_id": finding_id,
        "agent": agent,
        "lane": lane,
        "topic": topic,
        "finding_type": finding_type,
        "summary": summary,
        "recommendation": recommendation,
        "evidence_ids": evidence_ids or [],
        "missing_data": missing_data or [],
        "confidence": confidence,
        "human_review": human_review or {},
        "source_scope": source_scope,
        "public_context_only": public_context_only
    }


def make_evidence(evidence_id, source_name="fixture", trust_tier="farm_record"):
    """Helper to construct a minimal Evidence dict."""
    return {
        "evidence_id": evidence_id,
        "source_id": f"src_{evidence_id}",
        "source_name": source_name,
        "trust_tier": trust_tier,
        "freshness_status": "fresh",
        "privacy_class": "Farm Confidential"
    }


def test_synthesizer_output_normalizes_to_action_pack_contract():
    finding = make_finding(
        finding_id="finding_records_001",
        agent="records_inventory",
        lane="records_inventory",
        topic="bin_reconciliation",
        finding_type="draft_bin_reconciliation",
        summary="Bin 3 needs reconciliation.",
        recommendation="Review Bin 3 reconciliation before any official record update.",
        evidence_ids=["res_bin_PVF_BIN_003"],
        missing_data=[],
        confidence="medium",
        human_review={
            "required": True,
            "review_type": "user_approval",
            "status": "needs_user_approval",
            "recommended_reviewers": ["farm_owner"]
        }
    )
    
    evidence_list = [make_evidence("res_bin_PVF_BIN_003")]
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=evidence_list,
        user_role="farm_owner"
    )
    
    normalized = normalize_action_pack_contract(action_pack)
    
    assert has_required_action_pack_fields(normalized) is True
    assert normalized["farm_id"] == "PVF_ROW_CROP_001"
    assert normalized["workflow_id"] == "weekly_plan"
    assert isinstance(normalized["recommendations"], list)
    assert isinstance(normalized["proposed_actions"], list)
    assert isinstance(normalized["evidence_summary"], list)
    assert isinstance(normalized["warnings"], list)
    assert isinstance(normalized["missing_data"], list)
    assert isinstance(normalized["human_review_status"], dict)
    assert normalized["status"] is not None


def test_synthesizer_preserves_missing_data_top_level():
    finding = make_finding(
        finding_id="f1",
        topic="stored_grain_watch",
        summary="Stored grain watch requires local bid and basis.",
        recommendation="Keep this as watch-only until local bid and basis are available.",
        missing_data=["local_bid", "local_basis"],
        evidence_ids=["res_grain_PVF_BIN_001"]
    )
    
    evidence_list = [make_evidence("res_grain_PVF_BIN_001")]
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=evidence_list,
        user_role="farm_owner"
    )
    
    assert "local_bid" in action_pack["missing_data"]
    assert "local_basis" in action_pack["missing_data"]


def test_synthesizer_preserves_evidence_summary_and_deduplicates():
    f1 = make_finding("f1", topic="stored_grain_watch", evidence_ids=["res_grain_PVF_BIN_001"])
    f2 = make_finding("f2", topic="bin_reconciliation", evidence_ids=["res_grain_PVF_BIN_001"])
    
    # Duplicate entries in the evidence list
    evidence_list = [
        make_evidence("res_grain_PVF_BIN_001"),
        make_evidence("res_grain_PVF_BIN_001"),
        make_evidence("res_extra")
    ]
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[f1, f2],
        evidence_list=evidence_list,
        user_role="farm_owner"
    )
    
    ev_ids = [e["evidence_id"] for e in action_pack["evidence_summary"]]
    assert len(ev_ids) == len(set(ev_ids))  # deduplicated
    assert "res_grain_PVF_BIN_001" in ev_ids
    assert "res_extra" in ev_ids


def test_synthesizer_low_confidence_generates_warning():
    finding = make_finding(
        finding_id="f1",
        topic="document_extraction",
        confidence="low",
        missing_data=["invoice_total", "supplier_terms"],
        evidence_ids=["res_doc_DOC_005"]
    )
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=[make_evidence("res_doc_DOC_005")],
        user_role="farm_owner"
    )
    
    assert len(action_pack["warnings"]) > 0
    warning_text = action_pack["warnings"][0].lower()
    assert "low confidence" in warning_text
    assert "document_extraction" in warning_text or "invoice_total" in warning_text or "supplier_terms" in warning_text


def test_synthesizer_does_not_emit_forbidden_execution_or_advisor_wording():
    # Make a finding that triggers weekly plan proposed actions
    finding = make_finding(
        finding_id="f1",
        topic="weekly_plan_pvf",
        summary="Weekly bin reconciliation is draft/blocked.",
        recommendation="Verify stored grain bin inventory.",
        evidence_ids=["res_bin_PVF_BIN_003"]
    )
    
    evidence_list = [make_evidence("res_bin_PVF_BIN_003")]
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=evidence_list,
        user_role="farm_owner"
    )
    
    serialized = json.dumps(action_pack, sort_keys=True)
    assert contains_forbidden_wording(serialized) == []
    
    # Assert proposed action statuses are valid simulated/local statuses
    for act in action_pack["proposed_actions"]:
        if "status" in act:
            assert act["status"] in MVP_ACTION_STATUSES or act["status"] in ["blocked_pending_user_approval", "needs_info"]

    # Explicit negative assertions
    forbidden = ["order placed", "sale executed", "invoice sent", "official record updated", "inventory updated"]
    for word in forbidden:
        assert word not in serialized.lower()


def test_synthesizer_keeps_public_context_from_becoming_action_anchor():
    # A farm-record finding
    finding_sales = make_finding(
        finding_id="finding_sales_001",
        topic="sales_commitment",
        evidence_ids=["res_sal_GBO_SAL_001"],
        summary="Review GBO sales commitments.",
        recommendation="reconcile sales commitments"
    )
    
    # A public-context finding
    finding_ams = make_finding(
        finding_id="finding_public_ams_001",
        topic="ams_market_context",
        evidence_ids=["public_ams_context"],
        summary="AMS public market context is advisory only.",
        recommendation="Use public market context as background only.",
        source_scope="public_context",
        public_context_only=True
    )
    
    evidence_list = [
        make_evidence("res_sal_GBO_SAL_001"),
        make_evidence("public_ams_context", source_name="ams", trust_tier="public_context")
    ]
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="GBO_DIRECT_001",
        workflow_id="weekly_plan",
        findings=[finding_sales, finding_ams],
        evidence_list=evidence_list,
        user_role="farm_owner"
    )
    
    ev_ids = [e["evidence_id"] for e in action_pack["evidence_summary"]]
    assert "public_ams_context" in ev_ids
    
    # Ensure no proposed action uses public_ams_context as the sole anchor or primary evidence
    for act in action_pack["proposed_actions"]:
        assert act["evidence_ids"] != ["public_ams_context"]
        payload = act.get("payload", {})
        assert payload.get("source_evidence_id") != "public_ams_context"
        related = payload.get("related_evidence", [])
        if "public_ams_context" in related:
            assert len(related) > 1


def test_synthesizer_field_employee_output_has_no_proposed_actions_or_restricted_terms():
    finding = make_finding(
        finding_id="f1",
        topic="weekly_plan_gbo",
        summary="Weekly cooler inventory is draft/blocked.",
        recommendation="Review cooler inventory levels.",
        evidence_ids=["res_phi_GBO_PHI_001"]
    )
    
    evidence_list = [make_evidence("res_phi_GBO_PHI_001")]
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="GBO_DIRECT_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=evidence_list,
        user_role="field_employee"
    )
    
    assert action_pack["proposed_actions"] == []
    for r in action_pack["recommendations"]:
        assert r["proposed_actions"] == []
        
    serialized = json.dumps(action_pack, sort_keys=True).lower()
    for term in RESTRICTED_FIELD_EMPLOYEE_TERMS:
        assert term not in serialized


def test_synthesizer_does_not_invent_price_yield_or_quantity_values():
    finding = make_finding(
        finding_id="f1",
        topic="stored_grain_watch",
        summary="Stored grain watch requires local bid and basis.",
        recommendation="Keep this watch-only until local bid and basis are available.",
        evidence_ids=["res_grain_PVF_BIN_001"],
        missing_data=["local_bid", "local_basis"],
        confidence="medium"
    )
    
    action_pack = RecommendationSynthesizer().synthesize(
        farm_id="PVF_ROW_CROP_001",
        workflow_id="weekly_plan",
        findings=[finding],
        evidence_list=[make_evidence("res_grain_PVF_BIN_001")],
        user_role="farm_owner"
    )
    
    serialized = json.dumps(action_pack, sort_keys=True)
    
    assert "$" not in serialized
    assert "$/bu" not in serialized
    assert "per bushel" not in serialized.lower()
    assert "56,000" not in serialized
    assert "56000" not in serialized
    assert "1,000" not in serialized
    assert "1000" not in serialized
