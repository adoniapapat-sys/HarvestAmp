"""Tests for the local HarvestAmp document extraction shadow milestone."""

from __future__ import annotations

import json
from pathlib import Path

from harvestamp.extraction import (
    DocumentExtractor,
    can_reference_as_reviewed_decision_anchor,
    is_source_labeled,
    redact_for_role,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "fixtures" / "documents"


def extract(name: str, farm_id: str = "PVF_ROW_CROP_001"):
    return DocumentExtractor().extract_file(DOCS / name, farm_id=farm_id).to_dict()


def test_doc_001_fuel_invoice_extraction():
    res = extract("doc_001_fuel_invoice.txt")
    fields = res["extracted_fields"]
    assert res["document_type"] == "fuel_invoice"
    assert res["extraction_confidence"] == "high"
    assert fields["supplier_name"] == "River County Fuel Cooperative"
    assert fields["invoice_or_quote_date"] == "2026-06-20"
    assert fields["quantity"] == 2500.0
    assert fields["unit"] == "gallons"
    assert fields["unit_price"] == 3.62
    assert fields["total_price"] == 9285.0
    assert fields["delivery_fee"] == 235.0
    assert is_source_labeled(res)
    assert res["human_review"]["status"] == "needs_user_approval"
    assert res["official_update_allowed"] is False
    assert res["external_actions_allowed"] is False
    assert res["proposed_actions"][0]["status"] == "blocked_pending_user_approval"


def test_doc_002_fertilizer_quote_flags_missing_fees_without_agronomic_recommendation():
    res = extract("doc_002_fertilizer_quote.txt")
    fields = res["extracted_fields"]
    assert res["document_type"] == "fertilizer_quote"
    assert fields["supplier_name"] == "Prairie Ag Retail"
    assert fields["product_name"] == "Urea 46-0-0"
    assert fields["invoice_or_quote_date"] == "2026-06-21"
    assert fields["unit_price"] == 455.0
    assert fields["valid_until"] == "2026-07-05"
    assert "delivery_fee" in res["missing_fields"]
    assert "application_fee" in res["missing_fields"]
    assert res["human_review"]["status"] == "needs_info"
    assert not res["proposed_actions"]
    assert any("No agronomic rate" in note for note in res["notes"])


def test_doc_003_seed_quote_extraction_and_missing_population_target():
    res = extract("doc_003_seed_quote.txt")
    fields = res["extracted_fields"]
    assert res["document_type"] == "seed_quote"
    assert fields["supplier_name"] == "North Ridge Seed"
    assert fields["crop"] == "Corn"
    assert fields["variety_hybrid"] == "NR 112-day VT2P synthetic"
    assert fields["quantity"] == 180.0
    assert fields["unit"] == "bags"
    assert fields["unit_price"] == 289.0
    assert fields["treatment_trait"] == "standard fungicide treatment; trait package VT2P"
    assert "population_or_acre_target" in res["missing_fields"]
    assert can_reference_as_reviewed_decision_anchor(res) is False
    assert any("No supplier selection" in note for note in res["notes"])


def test_doc_004_packaging_invoice_extraction_for_green_basket():
    res = extract("doc_004_packaging_invoice.txt", farm_id="GBO_DIRECT_001")
    fields = res["extracted_fields"]
    assert res["farm_id"] == "GBO_DIRECT_001"
    assert res["document_type"] == "packaging_invoice"
    assert fields["supplier_name"] == "Market Pack Supply"
    assert fields["invoice_or_quote_date"] == "2026-06-19"
    assert fields["quantity"] == 80.0
    assert fields["unit"] == "cases"
    assert fields["unit_price"] == 18.5
    assert fields["delivery_fee"] == 42.0
    assert fields["total_price"] == 1847.0
    assert res["proposed_record"]["record_type"] == "draft_packaging_inventory_record"
    assert res["official_update_allowed"] is False


def test_doc_005_low_confidence_ambiguous_document_needs_info():
    res = extract("doc_005_ambiguous_note.txt")
    assert res["document_type"] == "unknown"
    assert res["extraction_confidence"] == "low"
    assert res["extraction_status"] == "partial"
    assert res["human_review"]["status"] == "needs_info"
    assert res["proposed_record"] is None
    assert res["proposed_actions"] == []
    assert res["official_update_allowed"] is False
    assert "unit_price" in res["missing_fields"]


def test_doc_006_sensitive_content_is_redacted_and_not_repeated():
    res = extract("doc_006_sensitive_payment.txt")
    serialized = json.dumps(res, sort_keys=True)
    assert "password" in res["redactions_applied"]
    assert "bank_account" in res["redactions_applied"]
    assert "routing_number" in res["redactions_applied"]
    assert "superSecret123" not in serialized
    assert "123456789012" not in serialized
    assert "091000019" not in serialized
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_ACCOUNT]" in serialized
    assert "[REDACTED_ROUTING]" in serialized


def test_extracted_quote_data_is_farm_restricted():
    res = extract("doc_001_fuel_invoice.txt")
    assert res["data_sensitivity"] == "Farm Restricted"
    assert res["evidence"]["data_sensitivity"] == "Farm Restricted"


def test_field_employee_cannot_view_restricted_quote_values():
    res = extract("doc_001_fuel_invoice.txt")
    employee_view = redact_for_role(res, "field_employee")
    fields = employee_view["extracted_fields"]
    assert fields["supplier_name"] == "[REDACTED_FOR_ROLE]"
    assert fields["unit_price"] == "[REDACTED_FOR_ROLE]"
    assert fields["total_price"] == "[REDACTED_FOR_ROLE]"
    assert employee_view["proposed_record"] == "[REDACTED_FOR_ROLE]"
    assert "role_based_quote_redaction" in employee_view["redactions_applied"]


def test_no_hallucinated_fields_for_missing_values():
    res = extract("doc_002_fertilizer_quote.txt")
    fields = res["extracted_fields"]
    assert fields["delivery_fee"] == "missing"
    assert fields["application_fee"] == "missing"
    assert "delivery_fee" in res["missing_fields"]
    assert "application_fee" in res["missing_fields"]


def test_reviewed_decision_anchor_requires_source_label_and_approval():
    res = extract("doc_001_fuel_invoice.txt")
    assert is_source_labeled(res) is True
    assert can_reference_as_reviewed_decision_anchor(res) is False
    res["decision_anchor_status"] = "reviewed_approved"
    res["human_review"]["status"] = "approved"
    assert can_reference_as_reviewed_decision_anchor(res) is True
