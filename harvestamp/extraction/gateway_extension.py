"""ToolGateway registration for local document extraction.

This is kept separate from harvestamp.gateway.tools so the shadow milestone can
be applied as a small, reversible extension. Once accepted, the method can be
moved into ToolGateway directly.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from harvestamp.auth.roles import check_cross_farm_block

from .document_extractor import DocumentExtractor, redact_for_role
from .schemas import DocumentExtractionResult


def extract_local_document(
    self: Any,
    capability_grant: Dict[str, Any],
    requesting_farm_id: str,
    target_farm_id: str,
    file_path: str,
    document_id: Optional[str] = None,
    user_role: str = "farm_owner",
    evidence_board: Optional[Any] = None,
) -> Dict[str, Any]:
    """Extract a local/fixture farm document through ToolGateway.

    The method follows the same ConnectorResult-like pattern as the existing
    shadow connectors. It never touches Drive, Gmail, portals, supplier systems,
    browsers, external messaging, or official record writes.
    """
    if not check_cross_farm_block(requesting_farm_id, target_farm_id):
        raise PermissionError("Cross-farm data access blocked.")
    if not self._verify_grant(capability_grant, "records_tool"):
        raise PermissionError("Unauthorized tool access capability.")

    extraction: DocumentExtractionResult = DocumentExtractor().extract_file(
        file_path=file_path,
        farm_id=target_farm_id,
        document_id=document_id,
        source_name="local_fixture_upload",
    )
    restricted_roles = {"field_employee", "seasonal_worker", "crew_member", "employee"}
    payload = redact_for_role(extraction, user_role) if user_role in restricted_roles else extraction.to_dict()
    evidence = extraction.evidence

    if evidence_board is not None:
        evidence_board.add_evidence(
            evidence_id=extraction.evidence_id,
            source_id=evidence.get("source_id", extraction.document_id),
            source_name=evidence.get("source_name", "local_fixture_upload"),
            trust_tier=evidence.get("trust_level", "T2 Farm-supplied document"),
            freshness_status=evidence.get("freshness_status", "document_date_or_upload_required"),
            privacy_class=extraction.data_sensitivity,
            data_payload=payload,
            description=f"Local document extraction draft for {extraction.document_type}",
            timestamp=None,
            farm_id=target_farm_id,
            authorization_status="authorized",
            connector_mode="local_fixture",
            fallback_used=False,
            fallback_reason=None,
        )

    return {
        "result_id": f"res_{extraction.evidence_id}",
        "source_id": extraction.document_id,
        "source_name": "Local Document Extraction",
        "retrieved_at": None,
        "freshness_status": "document_date_or_upload_required",
        "trust_tier": "T2 Farm-supplied document",
        "privacy_class": extraction.data_sensitivity,
        "payload": payload,
        "evidence_reference": extraction.evidence_id,
        "timestamp": None,
        "farm_id": target_farm_id,
        "authorization_status": "authorized",
        "fallback_used": False,
        "fallback_reason": None,
        "status": extraction.extraction_status,
        "connector_mode": "local_fixture",
    }


def register_tool_gateway_extension(ToolGateway: Any) -> None:
    """Attach the local-document capability to ToolGateway once."""
    if getattr(ToolGateway, "_local_document_extension_registered", False):
        return
    setattr(ToolGateway, "extract_local_document", extract_local_document)
    setattr(ToolGateway, "_local_document_extension_registered", True)
