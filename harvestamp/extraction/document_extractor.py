"""Local, fixture-driven document extraction for HarvestAmp.

This parser is intentionally conservative: it reads only caller-supplied local
files, never uses Drive/Gmail/portals/browsers, redacts sensitive payment or
credential-like values, labels outputs as Farm Restricted, and keeps all
proposed record mutations draft-only until review.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .schemas import DocumentExtractionResult, HumanReview

MISSING = "missing"
FARM_RESTRICTED = "Farm Restricted"
SOURCE_NAME = "local_fixture_upload"
RESTRICTED_ROLE_REDACTIONS = {"field_employee", "seasonal_worker", "crew_member", "employee"}

SENSITIVE_PATTERNS: List[Tuple[str, re.Pattern[str], str]] = [
    ("password", re.compile(r"(?i)\b(password|passcode|pwd)\s*[:=]\s*([^\s,;]+)"), r"\1: [REDACTED_SECRET]"),
    ("api_key_or_token", re.compile(r"(?i)\b(api[_ -]?key|token|secret)\s*[:=]\s*([A-Za-z0-9_\-]{8,})"), r"\1: [REDACTED_SECRET]"),
    ("bank_account", re.compile(r"(?i)\b(account|acct|bank account)\s*(number|no\.)?\s*[:#]?\s*([0-9][0-9\- ]{5,}[0-9])"), r"\1 \2: [REDACTED_ACCOUNT]"),
    ("routing_number", re.compile(r"(?i)\b(routing|aba)\s*(number|no\.)?\s*[:#]?\s*([0-9]{9})"), r"\1 \2: [REDACTED_ROUTING]"),
    ("payment_card", re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_CARD]"),
]

REQUIRED_FIELDS: Dict[str, List[str]] = {
    "fuel_invoice": ["supplier_name", "invoice_or_quote_date", "product_name", "quantity", "unit", "unit_price", "total_price"],
    "fertilizer_quote": ["supplier_name", "invoice_or_quote_date", "product_name", "unit_price", "valid_until", "delivery_fee", "application_fee"],
    "seed_quote": ["supplier_name", "invoice_or_quote_date", "crop", "variety_hybrid", "quantity", "unit", "unit_price", "treatment_trait", "population_or_acre_target"],
    "packaging_invoice": ["supplier_name", "invoice_or_quote_date", "product_name", "quantity", "unit", "unit_price", "total_price"],
    "general_input_invoice": ["supplier_name", "invoice_or_quote_date", "product_name", "quantity", "unit", "unit_price", "total_price"],
    "supplier_quote": ["supplier_name", "invoice_or_quote_date", "product_name", "unit_price", "valid_until"],
    "supplier_invoice": ["supplier_name", "invoice_or_quote_date", "product_name", "quantity", "unit", "unit_price", "total_price"],
    "fuel_receipt": ["supplier_name", "invoice_or_quote_date", "product_name", "quantity", "unit", "unit_price", "total_price"],
    "packaging_receipt": ["supplier_name", "invoice_or_quote_date", "product_name", "quantity", "unit", "unit_price", "total_price"],
    "harvest_load_ticket": ["farm_id", "invoice_or_quote_date", "product_name", "quantity", "unit"],
    "inventory_count_sheet": ["farm_id", "invoice_or_quote_date", "product_name", "quantity", "unit"],
    "unknown": ["supplier_name", "invoice_or_quote_date", "product_name", "quantity", "unit_price", "total_price"],
}


class DocumentExtractor:
    """Conservative parser for synthetic/local farm documents."""

    def extract_file(
        self,
        file_path: str | Path,
        farm_id: str,
        document_id: Optional[str] = None,
        source_name: str = SOURCE_NAME,
    ) -> DocumentExtractionResult:
        path = Path(file_path)
        text = _read_local_text(path)
        return self.extract_text(
            text=text,
            farm_id=farm_id,
            document_id=document_id or _document_id_from_path(path),
            source_file_reference=str(path),
            source_name=source_name,
        )

    def extract_text(
        self,
        text: str,
        farm_id: str,
        document_id: str,
        source_file_reference: str = "inline_text",
        source_name: str = SOURCE_NAME,
    ) -> DocumentExtractionResult:
        redacted_text, redactions = redact_sensitive_text(text)
        doc_type = classify_document_type(redacted_text)
        fields = extract_fields(redacted_text, doc_type)
        missing_fields = compute_missing_fields(doc_type, fields)
        confidence = confidence_for(doc_type, missing_fields)
        status = status_for(doc_type, confidence, missing_fields)
        human_review = human_review_for(doc_type, confidence, missing_fields)
        evidence_id = build_evidence_id(document_id, source_file_reference, fields)
        evidence = build_evidence(evidence_id, document_id, doc_type, source_name, source_file_reference, redactions)
        proposed_record = build_proposed_record(doc_type, farm_id, document_id, fields, evidence_id)
        proposed_actions = build_proposed_actions(doc_type, confidence, missing_fields, proposed_record)
        notes = build_notes(doc_type, missing_fields, redactions)
        return DocumentExtractionResult(
            document_id=document_id,
            farm_id=farm_id,
            document_type=doc_type,
            source_name=source_name,
            source_file_reference=source_file_reference,
            extraction_status=status,
            extraction_confidence=confidence,
            data_sensitivity=FARM_RESTRICTED,
            extracted_fields=fields,
            missing_fields=missing_fields,
            redactions_applied=redactions,
            evidence_id=evidence_id,
            human_review=human_review,
            evidence=evidence,
            proposed_record=proposed_record,
            proposed_actions=proposed_actions,
            official_update_allowed=False,
            external_actions_allowed=False,
            decision_anchor_status="draft_pending_review",
            notes=notes,
            redacted_text_excerpt=_excerpt(redacted_text),
        )


def _read_local_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Local document not found: {path}")
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("PDF extraction requires optional pypdf; use text fixtures for default tests.") from exc
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def _document_id_from_path(path: Path) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_").upper()
    return f"DOC_{safe}" if safe else "DOC_LOCAL_UPLOAD"


def redact_sensitive_text(text: str) -> Tuple[str, List[str]]:
    redacted = text
    applied: List[str] = []
    for label, pattern, replacement in SENSITIVE_PATTERNS:
        redacted_next, count = pattern.subn(replacement, redacted)
        if count:
            applied.append(label)
            redacted = redacted_next
    return redacted, sorted(set(applied))


def classify_document_type(text: str) -> str:
    lower = text.lower()
    if _contains_any_phrase(lower, ["fuel receipt", "diesel receipt"]):
        return "fuel_receipt"
    if _contains_any_phrase(lower, ["packaging receipt", "clamshell receipt"]):
        return "packaging_receipt"
    if _contains_any_phrase(lower, ["load ticket", "scale ticket", "harvest ticket", "harvest load ticket"]):
        return "harvest_load_ticket"
    if _contains_any_phrase(lower, ["inventory count", "count sheet", "physical count sheet", "inventory count sheet"]):
        return "inventory_count_sheet"
    
    # Explicit exact phrase matches for supplier quote / invoice
    if _contains_any_phrase(lower, ["supplier quote", "vendor quote", "price quote"]):
        return "supplier_quote"
    if _contains_any_phrase(lower, ["supplier invoice", "vendor invoice"]):
        return "supplier_invoice"

    # Specific quotes and invoices
    if _contains_any_phrase(lower, ["46-0-0"]) or _contains_any_word(lower, ["fertilizer", "urea", "uan", "anhydrous", "potash"]):
        return "fertilizer_quote" if _contains_any_word(lower, ["quote"]) else "general_input_invoice"
    if _contains_any_phrase(lower, ["seed quote", "seed corn", "trait package", "seed treatment"]) or _contains_any_word(lower, ["hybrid"]):
        return "seed_quote"
    if _contains_any_phrase(lower, ["csa box", "produce bags"]) or _contains_any_word(lower, ["clamshell", "packaging", "labels"]):
        return "packaging_invoice"
        
    # General fuel invoices
    if _contains_any_phrase(lower, ["dyed diesel", "fuel invoice"]) or _contains_any_word(lower, ["diesel", "gallons"]):
        return "fuel_invoice"

    # General supplier quotes and invoices (keyword based fallback)
    if "quote" in lower and ("supplier" in lower or "vendor" in lower):
        return "supplier_quote"
    if "invoice" in lower and ("supplier" in lower or "vendor" in lower):
        return "supplier_invoice"
        
    if _contains_any_word(lower, ["invoice", "quote", "receipt"]):
        return "general_input_invoice"
    return "unknown"


def _contains_any_word(text: str, words: Iterable[str]) -> bool:
    return any(re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text) for word in words)


def _contains_any_phrase(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def extract_fields(text: str, document_type: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
        "supplier_name": _find_labeled_text(text, ["Supplier", "Vendor", "From", "Dealer"]),
        "farm_id": _find_labeled_text(text, ["Farm ID", "Farm", "Location"]),
        "invoice_or_quote_date": _find_date(text),
        "product_name": _find_product_name(text),
        "quantity": None,
        "unit": None,
        "unit_price": _find_money(text, ["Unit Price", "Unit Cost", "Price", "Rate"]),
        "total_price": _find_money(text, ["Total Price", "Total", "Invoice Total", "Quote Total", "Amount Due"]),
        "delivery_fee": _find_money_or_missing(text, ["Delivery Fee", "Delivery", "Freight", "Shipping"]),
        "application_fee": _find_money_or_missing(text, ["Application Fee", "Application", "Application Charge"]),
        "valid_until": _find_labeled_text(text, ["Valid Until", "Expires", "Expiration Date"]),
        "crop": _find_labeled_text(text, ["Crop"]),
        "variety_hybrid": _find_labeled_text(text, ["Hybrid", "Variety"]),
        "treatment_trait": _find_labeled_text(text, ["Treatment", "Trait", "Trait Package"]),
        "discount_terms": _find_labeled_text(text, ["Discount Terms", "Discount", "Terms"]),
        "population_or_acre_target": _find_labeled_text(text, ["Population Target", "Acre Target", "Target Acres", "Seeding Rate"]),
    }
    quantity, unit = _find_quantity_and_unit(text, document_type)
    fields["quantity"] = quantity
    fields["unit"] = unit
    line_items = _extract_line_items(text)
    if line_items:
        fields["line_items"] = line_items
        fields["product_name"] = fields["product_name"] or line_items[0].get("description")
        fields["quantity"] = fields["quantity"] if fields["quantity"] is not None else line_items[0].get("quantity")
        fields["unit"] = fields["unit"] or line_items[0].get("unit")
        fields["unit_price"] = fields["unit_price"] if fields["unit_price"] is not None else line_items[0].get("unit_price")
    return fields


def _find_labeled_text(text: str, labels: Iterable[str]) -> Optional[str]:
    for label in labels:
        match = re.search(rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*(.+?)\s*$", text)
        if match:
            return _clean_value(match.group(1))
    return None


def _find_date(text: str) -> Optional[str]:
    labeled = _find_labeled_text(text, ["Invoice Date", "Quote Date", "Date"])
    search_space = labeled or text
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b", search_space)
    return match.group(0) if match else labeled


def _find_product_name(text: str) -> Optional[str]:
    value = _find_labeled_text(text, ["Product", "Item", "Description"])
    if value:
        return value
    lower = text.lower()
    for keyword, product in [("dyed diesel", "Dyed diesel"), ("diesel", "Diesel"), ("urea", "Urea"), ("uan", "UAN"), ("clamshell", "Clamshell packaging"), ("csa box", "CSA boxes"), ("seed corn", "Seed corn")]:
        if keyword in lower:
            return product
    return None


def _find_money(text: str, labels: Iterable[str]) -> Optional[float]:
    for label in labels:
        match = re.search(rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*\$?([0-9,]+(?:\.[0-9]+)?)", text)
        if match:
            return _to_float(match.group(1))
    return None


def _find_money_or_missing(text: str, labels: Iterable[str]) -> Any:
    value = _find_money(text, labels)
    if value is not None:
        return value
    for label in labels:
        if re.search(rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*(not included|n/a|na|tbd|missing|unknown)", text):
            return MISSING
    return MISSING


def _find_quantity_and_unit(text: str, document_type: str) -> Tuple[Optional[float], Optional[str]]:
    # Extract unit if on a separate line
    unit_match = re.search(r"(?im)^\s*Unit\s*[:\-]\s*([A-Za-z][A-Za-z /_-]*)", text)
    unit = _clean_unit(unit_match.group(1)) if unit_match else None

    patterns = [
        r"(?im)^\s*Quantity\s*[:\-]\s*([0-9,]+(?:\.[0-9]+)?)[ \t]*([A-Za-z][A-Za-z /_-]*)?",
        r"(?im)^\s*Gallons\s*[:\-]\s*([0-9,]+(?:\.[0-9]+)?)",
        r"(?im)^\s*Bags\s*[:\-]\s*([0-9,]+(?:\.[0-9]+)?)",
        r"(?im)^\s*Cases\s*[:\-]\s*([0-9,]+(?:\.[0-9]+)?)",
        r"(?im)^\s*Units\s*[:\-]\s*([0-9,]+(?:\.[0-9]+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            qty = _to_float(match.group(1))
            if len(match.groups()) >= 2 and match.group(2):
                unit = _clean_unit(match.group(2))
            elif not unit:
                if "gallons" in pattern.lower():
                    unit = "gallons"
                elif "bags" in pattern.lower():
                    unit = "bags"
                elif "cases" in pattern.lower():
                    unit = "cases"
                else:
                    unit = _default_unit_for(document_type)
            return qty, unit
    generic = re.search(r"(?i)\b([0-9,]+(?:\.[0-9]+)?)\s*(gallons|gal|tons|ton|bags|bag|cases|case|boxes|box|units|each)\b", text)
    if generic:
        return _to_float(generic.group(1)), _clean_unit(generic.group(2))
    return None, unit


def _extract_line_items(text: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    pattern = re.compile(r"(?im)^\s*[-*]?\s*([0-9,]+(?:\.[0-9]+)?)\s+(cases|case|boxes|box|bags|bag|units|each|gallons|tons|ton|rolls|roll)\s+(.+?)\s+@\s+\$?([0-9,]+(?:\.[0-9]+)?)(?:/\w+)?(?:\s*=\s*\$?([0-9,]+(?:\.[0-9]+)?))?\s*$")
    for match in pattern.finditer(text):
        items.append({
            "quantity": _to_float(match.group(1)),
            "unit": _clean_unit(match.group(2)),
            "description": _clean_value(match.group(3)),
            "unit_price": _to_float(match.group(4)),
            "line_total": _to_float(match.group(5)) if match.group(5) else None,
        })
    return items


def compute_missing_fields(document_type: str, fields: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for key in REQUIRED_FIELDS.get(document_type, REQUIRED_FIELDS["unknown"]):
        value = fields.get(key)
        if value is None or value == "" or value == MISSING:
            missing.append(key)
    return missing


def confidence_for(document_type: str, missing_fields: List[str]) -> str:
    if document_type == "unknown":
        return "low"
    required_count = len(REQUIRED_FIELDS.get(document_type, [])) or 1
    completeness = (required_count - len(missing_fields)) / required_count
    if completeness >= 0.85:
        return "high"
    if completeness >= 0.55:
        return "medium"
    return "low"


def status_for(document_type: str, confidence: str, missing_fields: List[str]) -> str:
    if document_type == "unknown" or confidence == "low" or missing_fields:
        return "partial"
    return "success"


def human_review_for(document_type: str, confidence: str, missing_fields: List[str]) -> HumanReview:
    if document_type == "unknown" or confidence == "low":
        return HumanReview(True, "user_approval", "needs_info", ["low_confidence_extraction", "missing_or_ambiguous_fields"], ["official_record_update", "external_message", "supplier_selection"])
    reasons = ["official_record_update", "farm_restricted_document"]
    if missing_fields:
        reasons.append("missing_fields")
    return HumanReview(True, "user_approval", "needs_user_approval" if not missing_fields else "needs_info", reasons, ["official_record_update", "external_message", "supplier_selection"])


def build_evidence_id(document_id: str, source_file_reference: str, fields: Dict[str, Any]) -> str:
    digest_src = json.dumps({"document_id": document_id, "source_file_reference": source_file_reference, "fields": fields}, sort_keys=True, default=str)
    return f"ev_doc_{hashlib.sha256(digest_src.encode('utf-8')).hexdigest()[:12]}"


def build_evidence(evidence_id: str, document_id: str, document_type: str, source_name: str, source_file_reference: str, redactions: List[str]) -> Dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_id": document_id,
        "source_name": source_name,
        "source_type": "uploaded_document",
        "document_type": document_type,
        "source_file_reference": source_file_reference,
        "trust_level": "T2 Farm-supplied document",
        "freshness_status": "document_date_or_upload_required",
        "data_sensitivity": FARM_RESTRICTED,
        "redactions_applied": redactions,
        "connector_mode": "local_fixture",
        "fallback_used": False,
    }


def build_proposed_record(document_type: str, farm_id: str, document_id: str, fields: Dict[str, Any], evidence_id: str) -> Optional[Dict[str, Any]]:
    if document_type == "unknown":
        return None
    record_type = {
        "fuel_invoice": "draft_fuel_purchase_record",
        "fertilizer_quote": "draft_fertilizer_quote_record",
        "seed_quote": "draft_seed_quote_record",
        "packaging_invoice": "draft_packaging_inventory_record",
        "general_input_invoice": "draft_input_invoice_record",
        "supplier_quote": "draft_supplier_quote_record",
        "supplier_invoice": "draft_supplier_invoice_record",
        "fuel_receipt": "draft_fuel_receipt_record",
        "packaging_receipt": "draft_packaging_receipt_record",
        "harvest_load_ticket": "draft_harvest_load_ticket",
        "inventory_count_sheet": "draft_inventory_count_sheet",
    }.get(document_type, "draft_document_record")
    return {"record_type": record_type, "farm_id": farm_id, "document_id": document_id, "status": "draft_pending_review", "source_evidence_id": evidence_id, "fields": {k: v for k, v in fields.items() if v not in (None, "")}}


def build_proposed_actions(document_type: str, confidence: str, missing_fields: List[str], proposed_record: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if document_type == "unknown" or confidence == "low" or proposed_record is None or missing_fields:
        return []
    return [{"action_type": "draft_official_record_update", "status": "blocked_pending_user_approval", "requires_approval": True, "target_record_type": proposed_record["record_type"], "external_action": False}]


def build_notes(document_type: str, missing_fields: List[str], redactions: List[str]) -> List[str]:
    notes: List[str] = []
    if document_type == "fertilizer_quote":
        notes.append("No agronomic rate, timing, product selection, or tank-mix recommendation was made.")
    if document_type == "seed_quote":
        notes.append("No supplier selection or planting-rate decision was made.")
    if document_type == "inventory_count_sheet":
        notes.append("This inventory count sheet does not update inventory records automatically.")
    if document_type in ["fuel_receipt", "packaging_receipt", "supplier_invoice", "supplier_quote"]:
        notes.append("This invoice or receipt is not marked paid and no payment was executed.")
    if document_type == "harvest_load_ticket":
        notes.append("This harvest/load ticket is not marked reconciled.")
    if missing_fields:
        notes.append("Missing or ambiguous fields must be resolved before the record can be approved.")
    if redactions:
        notes.append("Sensitive payment or credential-like content was redacted before evidence summary generation.")
    notes.append("No external message, order, supplier selection, or official record update was executed.")
    return notes


def is_source_labeled(result: DocumentExtractionResult | Dict[str, Any]) -> bool:
    data = result.to_dict() if isinstance(result, DocumentExtractionResult) else result
    ev = data.get("evidence") or {}
    return bool(data.get("evidence_id") and ev.get("source_id") and ev.get("source_name") and ev.get("source_type") and ev.get("source_file_reference"))


def can_reference_as_reviewed_decision_anchor(result: DocumentExtractionResult | Dict[str, Any]) -> bool:
    data = result.to_dict() if isinstance(result, DocumentExtractionResult) else result
    return bool(is_source_labeled(data) and data.get("decision_anchor_status") == "reviewed_approved" and data.get("human_review", {}).get("status") == "approved")


def redact_for_role(result: DocumentExtractionResult | Dict[str, Any], user_role: str) -> Dict[str, Any]:
    data = result.to_dict() if isinstance(result, DocumentExtractionResult) else json.loads(json.dumps(result))
    if user_role not in RESTRICTED_ROLE_REDACTIONS:
        return data
    fields = data.get("extracted_fields", {})
    for key in {"supplier_name", "unit_price", "total_price", "delivery_fee", "application_fee", "discount_terms", "line_items"}:
        if key in fields and fields[key] not in (None, "", MISSING):
            fields[key] = "[REDACTED_FOR_ROLE]"
    if data.get("proposed_record"):
        data["proposed_record"] = "[REDACTED_FOR_ROLE]"
    data.setdefault("redactions_applied", [])
    if "role_based_quote_redaction" not in data["redactions_applied"]:
        data["redactions_applied"].append("role_based_quote_redaction")
    data["role_view"] = user_role
    data["notes"] = list(data.get("notes", [])) + ["Supplier quote and pricing details are hidden from this role."]
    return data


def _to_float(value: str) -> float:
    return float(value.replace(",", ""))


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip(".;"))


def _clean_unit(unit: str) -> str:
    unit = unit.strip().lower().replace("/", " ")
    synonyms = {"gal": "gallons", "gallon": "gallons", "ton": "tons", "bag": "bags", "case": "cases", "box": "boxes", "each": "units", "roll": "rolls"}
    return synonyms.get(unit, unit)


def _default_unit_for(document_type: str) -> Optional[str]:
    return {
        "fuel_invoice": "gallons",
        "fertilizer_quote": "tons",
        "seed_quote": "bags",
        "packaging_invoice": "cases",
        "supplier_quote": "units",
        "supplier_invoice": "units",
        "fuel_receipt": "gallons",
        "packaging_receipt": "cases",
        "harvest_load_ticket": "bushels",
        "inventory_count_sheet": "units"
    }.get(document_type)


def _excerpt(text: str, limit: int = 800) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]
