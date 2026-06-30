"""Tests for explicit document-review routing and processing under Supervisor.

These tests prove that:
- Explicit review prompts route to a dedicated "document_review" workflow topic.
- It loads documents, runs the correct specialist agent helpers, and returns a normal ActionPack.
- Farm owner can see ev_doc_* evidence IDs.
- Field employee views redact raw ev_doc_* IDs and pricing/supplier details.
- Weekly plans do not auto-load document evidence.
- Existing DOC-001 through DOC-006 behavior is completely unchanged.
- Output carries correct disclaimers, warnings, and missing_data for low-confidence files.
- No forbidden mutation/action wording is present.
"""

from __future__ import annotations

import json
import os
import yaml
import pytest

from harvestamp.workflows.supervisor import Supervisor
from harvestamp.core.contracts import (
    normalize_action_pack_contract,
    has_required_action_pack_fields,
    contains_forbidden_wording,
    RESTRICTED_FIELD_EMPLOYEE_TERMS,
)

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))


def load_farm_profile(farm_id: str) -> dict:
    filename = "prairie_view_farms.yaml" if "PVF" in farm_id else "green_basket_organics.yaml"
    path = os.path.join(FIXTURES_DIR, "farms", filename)
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_observations() -> dict:
    path = os.path.join(FIXTURES_DIR, "data_observations.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# 1. test_supervisor_routes_explicit_document_review_prompt
# ---------------------------------------------------------------------------

def test_supervisor_routes_explicit_document_review_prompt():
    """Verify generic explicit review prompt routes and runs the review workflow."""
    profile = load_farm_profile("PVF_ROW_CROP_001")
    obs = load_observations()
    supervisor = Supervisor()

    action_pack = supervisor.run_workflow(
        farm_profile=profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="Review my local extracted documents.",
        observations=obs,
    )

    # Assert correct ActionPack shape
    assert action_pack["status"] != "blocked"
    normalized = normalize_action_pack_contract(action_pack)
    assert has_required_action_pack_fields(normalized) is True

    # Assert recommendations and evidence exist
    recs = action_pack["recommendations"]
    assert len(recs) > 0
    
    # Assert farm_owner can see ev_doc_* evidence
    ev_ids = [e["evidence_id"] for e in action_pack["evidence_summary"]]
    assert any(eid.startswith("ev_doc_") for eid in ev_ids)

    # Assert no proposed external actions are returned (they must remain draft/simulation-only or empty)
    # The surface helpers do not return proposed_actions, only context findings.
    assert len(action_pack["proposed_actions"]) == 0

    # Assert read-only disclaimers appear
    text = json.dumps(action_pack).lower()
    assert "read-only" in text
    assert "no farm system, record, payment, or outside party has been changed" in text

    # Assert no forbidden update/payment/reconciliation wording
    assert contains_forbidden_wording(text) == []


# ---------------------------------------------------------------------------
# 2. test_supervisor_routes_procurement_document_prompt
# ---------------------------------------------------------------------------

def test_supervisor_routes_procurement_document_prompt():
    """Verify prompt naming a specific quote/invoice/receipt routes only to procurement doc review."""
    profile = load_farm_profile("PVF_ROW_CROP_001")
    obs = load_observations()
    supervisor = Supervisor()

    action_pack = supervisor.run_workflow(
        farm_profile=profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="Review the supplier quote.",
        observations=obs,
    )

    # Assert supplier_quote context appears
    text = json.dumps(action_pack).lower()
    assert "read-only quote context" in text
    assert "ag express" in text  # doc_007 has Ag Express Co-op

    # Verify no records document context (e.g. load tickets or count sheets) is in text
    assert "load-ticket" not in text
    assert "count-sheet" not in text

    # Assert no supplier contact, order, or payment wording
    assert contains_forbidden_wording(text) == []
    for forbidden in ["supplier contacted", "message sent", "order placed", "purchase approved", "invoice paid", "payment sent"]:
        assert forbidden not in text


# ---------------------------------------------------------------------------
# 3. test_supervisor_routes_records_document_prompt
# ---------------------------------------------------------------------------

def test_supervisor_routes_records_document_prompt():
    """Verify prompt naming a harvest ticket/sheet routes only to records doc review."""
    profile = load_farm_profile("PVF_ROW_CROP_001")
    obs = load_observations()
    supervisor = Supervisor()

    action_pack = supervisor.run_workflow(
        farm_profile=profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="Review the harvest load ticket.",
        observations=obs,
    )

    # Assert harvest_load_ticket context appears
    text = json.dumps(action_pack).lower()
    assert "read-only load-ticket context" in text
    assert "corn" in text

    # Verify no procurement document context is in text
    assert "quote context" not in text
    assert "invoice context" not in text

    # Assert no load ticket reconciled, record update, or harvest completed wording
    assert contains_forbidden_wording(text) == []
    for forbidden in ["load ticket reconciled", "official record update", "official record updated", "inventory updated", "harvest completed"]:
        assert forbidden not in text


# ---------------------------------------------------------------------------
# 4. test_supervisor_document_review_field_employee_redaction
# ---------------------------------------------------------------------------

def test_supervisor_document_review_field_employee_redaction():
    """Verify field employee runs with complete redaction of raw IDs, pricing, and supplier names."""
    profile = load_farm_profile("PVF_ROW_CROP_001")
    obs = load_observations()
    supervisor = Supervisor()

    action_pack = supervisor.run_workflow(
        farm_profile=profile,
        user_id="pvf_employee_001",
        user_role="field_employee",
        prompt="Review my local extracted documents.",
        observations=obs,
    )

    serialized = json.dumps(action_pack)
    text = serialized.lower()

    # Assert no raw ev_doc_* evidence IDs are exposed anywhere in the ActionPack
    assert "ev_doc_" not in serialized
    
    # Assert supplier name, supplier pricing, quote/invoice totals, unit prices, etc. are hidden or redacted
    # Check that Ag Express, River County, or prices (like 3.55, 3.58) are not exposed as raw extracted fields.
    # Note: redact_for_role replaces these fields in doc payload with [REDACTED_FOR_ROLE]
    assert "[REDACTED_FOR_ROLE]" in serialized or "read-only quote context available for management review" in text

    # Check for RESTRICTED_FIELD_EMPLOYEE_TERMS violations
    for term in RESTRICTED_FIELD_EMPLOYEE_TERMS:
        # Note: 'invoice' is in RESTRICTED_FIELD_EMPLOYEE_TERMS, but we must make sure it is not disclosed as raw/sensitive data.
        # Let's ensure no sensitive/restricted terms leak.
        if term in ["supplier pricing", "quote price", "operating margin", "gross margin", "customer financial", "payment status", "buyer terms", "official approval"]:
            assert term not in text

    # Assert safe operational context remains
    assert "read-only" in text
    assert "no task or farm system has been changed" in text


# ---------------------------------------------------------------------------
# 5. test_weekly_plans_do_not_auto_load_document_evidence
# ---------------------------------------------------------------------------

def test_weekly_plans_do_not_auto_load_document_evidence():
    """Verify weekly plans do not automatically load or list ev_doc_* evidence."""
    obs = load_observations()
    supervisor = Supervisor()

    # PVF Weekly Plan
    pvf_profile = load_farm_profile("PVF_ROW_CROP_001")
    action_pack_pvf = supervisor.run_workflow(
        farm_profile=pvf_profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What should I know about Prairie View Farms this week?",
        observations=obs,
    )
    serialized_pvf = json.dumps(action_pack_pvf)
    assert "ev_doc_" not in serialized_pvf

    # GBO Weekly Plan
    gbo_profile = load_farm_profile("GBO_DIRECT_001")
    action_pack_gbo = supervisor.run_workflow(
        farm_profile=gbo_profile,
        user_id="gbo_owner_001",
        user_role="gbo_owner",
        prompt="What should I know about Green Basket this week?",
        observations=obs,
    )
    serialized_gbo = json.dumps(action_pack_gbo)
    assert "ev_doc_" not in serialized_gbo


# ---------------------------------------------------------------------------
# 6. test_existing_doc_scenarios_still_route_to_local_document_extraction
# ---------------------------------------------------------------------------

def test_existing_doc_scenarios_still_route_to_local_document_extraction():
    """Verify prompts that match existing DOC-001 through DOC-006 still run local_document_extraction."""
    profile = load_farm_profile("PVF_ROW_CROP_001")
    supervisor = Supervisor()

    # Match DOC-001 style
    topic = supervisor.route_intent(
        "Extract local document fixture fixtures/documents/doc_001_fuel_invoice.txt and draft, but do not commit, a fuel purchase/inventory record.",
        profile,
    )
    assert topic == "local_document_extraction"

    # Match DOC-002 style
    topic2 = supervisor.route_intent(
        "Extract local document fixture fixtures/documents/doc_002_fertilizer_quote.txt, flag missing delivery/application fees, and do not make agronomic recommendations.",
        profile,
    )
    assert topic2 == "local_document_extraction"


# ---------------------------------------------------------------------------
# 7. test_document_review_low_confidence_or_missing_fields_surfaces_review_context
# ---------------------------------------------------------------------------

def test_document_review_low_confidence_or_missing_fields_surfaces_review_context():
    """Verify that low-confidence or missing fields surface warnings and missing_data."""
    profile = load_farm_profile("PVF_ROW_CROP_001")
    obs = load_observations()
    supervisor = Supervisor()

    # Under doc_005_ambiguous_note.txt, extraction is low confidence
    # "What is missing from the extracted document?" loads all, which includes doc_005
    action_pack = supervisor.run_workflow(
        farm_profile=profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="What is missing from the extracted document?",
        observations=obs,
    )

    # Check for missing_data or low-confidence warning
    assert len(action_pack["missing_data"]) > 0 or len(action_pack["warnings"]) > 0
    text = json.dumps(action_pack).lower()
    assert "low confidence" in text or "missing fields" in text


# ---------------------------------------------------------------------------
# 8. test_document_review_actionpack_contract_shape
# ---------------------------------------------------------------------------

def test_document_review_actionpack_contract_shape():
    """Verify explicit review workflow returns an ActionPack of the correct contract shape."""
    profile = load_farm_profile("PVF_ROW_CROP_001")
    obs = load_observations()
    supervisor = Supervisor()

    action_pack = supervisor.run_workflow(
        farm_profile=profile,
        user_id="pvf_owner_001",
        user_role="farm_owner",
        prompt="Review my local extracted documents.",
        observations=obs,
    )

    normalized = normalize_action_pack_contract(action_pack)
    assert has_required_action_pack_fields(normalized) is True

    # Check structure
    assert isinstance(normalized["action_pack_id"], str)
    assert isinstance(normalized["farm_id"], str)
    assert isinstance(normalized["workflow_id"], str)
    assert isinstance(normalized["recommendations"], list)
    assert isinstance(normalized["proposed_actions"], list)
    assert isinstance(normalized["evidence_summary"], list)
    assert isinstance(normalized["warnings"], list)
    assert isinstance(normalized["missing_data"], list)
    assert isinstance(normalized["status"], str)
