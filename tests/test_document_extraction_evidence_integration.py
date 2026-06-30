"""Tests for document extraction read-only evidence integration.

These tests verify that extracted-document evidence can be loaded via
ToolGateway, surfaced through RecordsAgent and ProcurementAgent as
read-only context, and that role redaction, wording safety, and
evidence-ID conventions are preserved.

None of these tests update inventory, official records, or golden
outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from harvestamp.extraction import DocumentExtractor, redact_for_role
from harvestamp.gateway.tools import ToolGateway
from harvestamp.agents.specialists import ProcurementAgent, RecordsAgent

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "fixtures" / "documents"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _records_grant() -> Dict[str, Any]:
    return {"authorized": True, "capability": "capability:records_tool"}


def _make_work_item(farm_id: str = "PVF_ROW_CROP_001") -> Dict[str, Any]:
    return {
        "work_item_id": "wi_test_doc_evidence",
        "workflow_id": "wf_test_doc_evidence",
        "farm_id": farm_id,
        "requesting_user_id": "test_user",
        "user_intent": "review extracted documents",
        "topic": "extracted_document_review",
    }


def _make_context(
    user_role: str = "farm_owner",
    farm_type: str = "large_row_crop",
) -> Dict[str, Any]:
    return {"user_role": user_role, "farm_type": farm_type}


FORBIDDEN_PHRASES = [
    "order placed",
    "supplier contacted",
    "message sent",
    "invoice paid",
    "payment sent",
    "inventory updated",
    "official record updated",
    "load ticket reconciled",
    "harvest completed",
    "records updated",
    "payment executed",
]


# ---------------------------------------------------------------------------
# 1. test_toolgateway_loads_extracted_documents_as_readonly_evidence
# ---------------------------------------------------------------------------

class TestToolGatewayLoadsExtractedDocuments:
    """get_extracted_documents returns documents from fixtures/documents/
    with ev_doc_* evidence IDs and preserved metadata."""

    def test_returns_documents(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        assert len(docs) > 0

    def test_evidence_ids_start_with_ev_doc(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        for doc in docs:
            assert doc["evidence_id"].startswith("ev_doc_"), (
                f"Evidence ID {doc['evidence_id']} does not start with ev_doc_"
            )

    def test_no_evidence_ids_start_with_res_inv(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        for doc in docs:
            assert not doc["evidence_id"].startswith("res_inv_"), (
                f"Evidence ID {doc['evidence_id']} must not start with res_inv_"
            )

    def test_extraction_metadata_preserved(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        for doc in docs:
            assert "extraction_status" in doc
            assert "extraction_confidence" in doc
            assert "missing_fields" in doc
            assert "human_review" in doc
            assert "source_file_reference" in doc
            assert "document_type" in doc
            assert "farm_id" in doc
            assert "extracted_fields" in doc
            assert "evidence_id" in doc

    def test_source_file_references_preserved(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        for doc in docs:
            ref = doc["source_file_reference"]
            assert ref, f"source_file_reference is empty for {doc['document_id']}"
            assert "fixtures/documents/" in ref or "doc_" in ref

    def test_trust_tier_and_privacy(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        for doc in docs:
            assert doc["trust_tier"] == "T2 Farm-supplied document"
            assert doc["privacy_class"] == "Farm Restricted"
            assert doc["status"] == "draft"
            assert doc["verification"] == "unverified"
            assert doc["origin"] == "local_user_provided"
            assert doc["official_update_allowed"] is False
            assert doc["external_actions_allowed"] is False


# ---------------------------------------------------------------------------
# 2. test_toolgateway_filters_extracted_documents
# ---------------------------------------------------------------------------

class TestToolGatewayFilters:
    """get_extracted_documents supports filtering by document_type and farm_id."""

    def test_filter_by_document_type(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
            document_type="fuel_invoice",
        )
        assert len(docs) > 0
        for doc in docs:
            assert doc["document_type"] == "fuel_invoice"

    def test_filter_by_harvest_load_ticket(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
            document_type="harvest_load_ticket",
        )
        assert len(docs) > 0
        for doc in docs:
            assert doc["document_type"] == "harvest_load_ticket"

    def test_filter_by_farm_id(self):
        gw = ToolGateway()
        # doc_011 has farm_id PVF_ROW_CROP_001 in its text
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
            farm_id_filter="PVF_ROW_CROP_001",
        )
        for doc in docs:
            fixture_farm = doc["extracted_fields"].get("farm_id") or doc["farm_id"]
            assert fixture_farm == "PVF_ROW_CROP_001"


# ---------------------------------------------------------------------------
# 3. test_document_evidence_is_read_only
# ---------------------------------------------------------------------------

class TestDocumentEvidenceIsReadOnly:
    """Serialized extracted documents contain no wording or flags implying
    mutations have occurred."""

    def test_no_mutation_wording_in_serialized_output(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        serialized = json.dumps(docs).lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in serialized, (
                f"Forbidden phrase '{phrase}' found in serialized document evidence"
            )

    def test_all_documents_are_draft_unverified(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        for doc in docs:
            assert doc["official_update_allowed"] is False
            assert doc["external_actions_allowed"] is False
            assert doc["decision_anchor_status"] == "draft_pending_review"


# ---------------------------------------------------------------------------
# 4. test_records_agent_surfaces_harvest_documents_as_context_only_when_explicitly_passed
# ---------------------------------------------------------------------------

class TestRecordsAgentSurfacesHarvestDocuments:
    """RecordsAgent.surface_extracted_documents surfaces harvest_load_ticket
    and inventory_count_sheet as read-only context with no mutation language."""

    def _get_harvest_docs(self) -> List[Dict[str, Any]]:
        gw = ToolGateway()
        all_docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        return [d for d in all_docs if d["document_type"] in ("harvest_load_ticket", "inventory_count_sheet")]

    def test_read_only_context_appears(self):
        agent = RecordsAgent()
        docs = self._get_harvest_docs()
        assert len(docs) > 0, "Need harvest/inventory fixture docs"
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        summary_lower = finding["summary"].lower()
        assert "read-only" in summary_lower

    def test_evidence_ids_for_owner(self):
        agent = RecordsAgent()
        docs = self._get_harvest_docs()
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        for eid in finding["evidence_ids"]:
            assert eid.startswith("ev_doc_") or eid == "Authorized operational records"

    def test_no_mutation_language(self):
        agent = RecordsAgent()
        docs = self._get_harvest_docs()
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        serialized = json.dumps(finding).lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in serialized, (
                f"Forbidden phrase '{phrase}' found in RecordsAgent finding"
            )

    def test_owner_read_only_disclaimer(self):
        agent = RecordsAgent()
        docs = self._get_harvest_docs()
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        assert "no farm system, record, payment, or outside party has been changed" in finding["summary"].lower()


# ---------------------------------------------------------------------------
# 5. test_procurement_agent_surfaces_procurement_documents_as_context_only_when_explicitly_passed
# ---------------------------------------------------------------------------

class TestProcurementAgentSurfacesProcurementDocuments:
    """ProcurementAgent.surface_extracted_documents surfaces supplier_quote,
    supplier_invoice, fuel_receipt, and packaging_receipt as read-only context."""

    def _get_procurement_docs(self) -> List[Dict[str, Any]]:
        gw = ToolGateway()
        all_docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        return [d for d in all_docs if d["document_type"] in (
            "supplier_quote", "supplier_invoice", "fuel_receipt", "packaging_receipt"
        )]

    def test_read_only_context_appears(self):
        agent = ProcurementAgent()
        docs = self._get_procurement_docs()
        assert len(docs) > 0, "Need procurement fixture docs"
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        summary_lower = finding["summary"].lower()
        assert "read-only" in summary_lower

    def test_evidence_ids_for_owner(self):
        agent = ProcurementAgent()
        docs = self._get_procurement_docs()
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        for eid in finding["evidence_ids"]:
            assert eid.startswith("ev_doc_")

    def test_no_mutation_language(self):
        agent = ProcurementAgent()
        docs = self._get_procurement_docs()
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        serialized = json.dumps(finding).lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in serialized, (
                f"Forbidden phrase '{phrase}' found in ProcurementAgent finding"
            )

    def test_owner_read_only_disclaimer(self):
        agent = ProcurementAgent()
        docs = self._get_procurement_docs()
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), docs
        )
        assert finding is not None
        assert "no farm system, record, payment, or outside party has been changed" in finding["summary"].lower()


# ---------------------------------------------------------------------------
# 6. test_low_confidence_or_missing_fields_require_review_context
# ---------------------------------------------------------------------------

class TestLowConfidenceOrMissingFields:
    """Incomplete extractions produce warnings and review-required context
    without automatic action."""

    def test_ambiguous_doc_produces_warnings(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
            document_type="unknown",
        )
        assert len(docs) > 0, "doc_005 should classify as unknown"
        for doc in docs:
            assert doc["extraction_confidence"] == "low"
            assert len(doc["missing_fields"]) > 0
            assert doc["human_review"]["required"] is True

    def test_partial_doc_surfaces_review_context_in_records_agent(self):
        # Use the ambiguous note plus a harvest doc with missing fields
        extractor = DocumentExtractor()
        incomplete = extractor.extract_text(
            text="Harvest Load Ticket\nFarm ID: PVF_ROW_CROP_001\nDate: 2026-06-25\nProduct: Corn",
            farm_id="PVF_ROW_CROP_001",
            document_id="DOC_INCOMPLETE_TICKET",
        )
        doc_dict = {
            "evidence_id": incomplete.evidence_id,
            "document_id": incomplete.document_id,
            "document_type": incomplete.document_type,
            "farm_id": incomplete.farm_id,
            "source_file_reference": "inline",
            "extraction_status": incomplete.extraction_status,
            "extraction_confidence": incomplete.extraction_confidence,
            "missing_fields": list(incomplete.missing_fields),
            "human_review": incomplete.human_review.to_dict(),
            "extracted_fields": incomplete.extracted_fields,
        }

        agent = RecordsAgent()
        finding = agent.surface_extracted_documents(
            _make_work_item(), _make_context("farm_owner"), [doc_dict]
        )
        assert finding is not None
        # Should have missing_data or warnings
        assert len(finding.get("missing_data", [])) > 0 or "review" in finding["summary"].lower()

    def test_no_automatic_action_on_low_confidence(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
            document_type="unknown",
        )
        for doc in docs:
            assert doc["official_update_allowed"] is False
            assert doc["external_actions_allowed"] is False


# ---------------------------------------------------------------------------
# 7. test_field_employee_document_context_redaction
# ---------------------------------------------------------------------------

class TestFieldEmployeeDocumentContextRedaction:
    """Field employee views do not expose supplier pricing, quote totals,
    invoice totals, unit prices, payment details, customer financials,
    buyer terms, or raw ev_doc_* evidence IDs."""

    def test_gateway_redacts_supplier_pricing_for_field_employee(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
            user_role="field_employee",
        )
        for doc in docs:
            fields = doc["extracted_fields"]
            # Supplier pricing fields should be redacted
            for key in ("supplier_name", "unit_price", "total_price"):
                if key in fields and fields[key] not in (None, "", "missing"):
                    assert fields[key] == "[REDACTED_FOR_ROLE]", (
                        f"Field {key}={fields[key]} not redacted for field_employee in {doc['document_id']}"
                    )

    def test_procurement_agent_redacts_for_field_employee(self):
        gw = ToolGateway()
        all_docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        procurement_docs = [d for d in all_docs if d["document_type"] in (
            "supplier_quote", "supplier_invoice", "fuel_receipt", "packaging_receipt"
        )]
        agent = ProcurementAgent()
        finding = agent.surface_extracted_documents(
            _make_work_item(),
            _make_context("field_employee"),
            procurement_docs,
        )
        assert finding is not None
        serialized = json.dumps(finding).lower()
        # Raw ev_doc_* IDs should not be exposed
        assert "ev_doc_" not in serialized
        # Should use authorized operational records
        assert "authorized operational records" in serialized

    def test_records_agent_redacts_for_field_employee(self):
        gw = ToolGateway()
        all_docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        records_docs = [d for d in all_docs if d["document_type"] in (
            "harvest_load_ticket", "inventory_count_sheet"
        )]
        agent = RecordsAgent()
        finding = agent.surface_extracted_documents(
            _make_work_item(),
            _make_context("field_employee"),
            records_docs,
        )
        assert finding is not None
        serialized = json.dumps(finding).lower()
        # Raw ev_doc_* IDs should not be exposed
        assert "ev_doc_" not in serialized
        assert "authorized operational records" in serialized

    def test_field_employee_safe_disclaimer(self):
        gw = ToolGateway()
        all_docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        records_docs = [d for d in all_docs if d["document_type"] in (
            "harvest_load_ticket", "inventory_count_sheet"
        )]
        agent = RecordsAgent()
        finding = agent.surface_extracted_documents(
            _make_work_item(),
            _make_context("field_employee"),
            records_docs,
        )
        assert finding is not None
        assert "no task or farm system has been changed" in finding["summary"].lower()


# ---------------------------------------------------------------------------
# 8. test_no_external_or_update_wording_in_document_evidence_outputs
# ---------------------------------------------------------------------------

class TestNoExternalOrUpdateWording:
    """Neither ToolGateway outputs nor direct agent outputs contain any
    forbidden execution or mutation wording."""

    def test_toolgateway_outputs_clean(self):
        gw = ToolGateway()
        docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        serialized = json.dumps(docs).lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in serialized, (
                f"Forbidden phrase '{phrase}' found in ToolGateway output"
            )

    def test_records_agent_outputs_clean(self):
        gw = ToolGateway()
        all_docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        records_docs = [d for d in all_docs if d["document_type"] in (
            "harvest_load_ticket", "inventory_count_sheet"
        )]
        agent = RecordsAgent()
        for role in ("farm_owner", "farm_manager", "field_employee"):
            finding = agent.surface_extracted_documents(
                _make_work_item(), _make_context(role), records_docs
            )
            if finding:
                serialized = json.dumps(finding).lower()
                for phrase in FORBIDDEN_PHRASES:
                    assert phrase not in serialized, (
                        f"Forbidden phrase '{phrase}' found in RecordsAgent output for role={role}"
                    )

    def test_procurement_agent_outputs_clean(self):
        gw = ToolGateway()
        all_docs = gw.get_extracted_documents(
            capability_grant=_records_grant(),
            requesting_farm_id="PVF_ROW_CROP_001",
            target_farm_id="PVF_ROW_CROP_001",
        )
        procurement_docs = [d for d in all_docs if d["document_type"] in (
            "supplier_quote", "supplier_invoice", "fuel_receipt", "packaging_receipt"
        )]
        agent = ProcurementAgent()
        for role in ("farm_owner", "farm_manager", "field_employee"):
            finding = agent.surface_extracted_documents(
                _make_work_item(), _make_context(role), procurement_docs
            )
            if finding:
                serialized = json.dumps(finding).lower()
                for phrase in FORBIDDEN_PHRASES:
                    assert phrase not in serialized, (
                        f"Forbidden phrase '{phrase}' found in ProcurementAgent output for role={role}"
                    )
