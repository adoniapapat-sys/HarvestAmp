"""Supervisor workflow registration for local document extraction.

The extension wraps the existing Supervisor methods instead of bypassing the
Credential Broker, ToolGateway, EvidenceBoard, or human-review policy.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from harvestamp.auth.roles import check_cross_farm_block
from harvestamp.core.evidence import EvidenceBoard

DOC_FIXTURE_MAP = {
    "DOC-001": "fixtures/documents/doc_001_fuel_invoice.txt",
    "DOC-002": "fixtures/documents/doc_002_fertilizer_quote.txt",
    "DOC-003": "fixtures/documents/doc_003_seed_quote.txt",
    "DOC-004": "fixtures/documents/doc_004_packaging_invoice.txt",
    "DOC-005": "fixtures/documents/doc_005_ambiguous_note.txt",
    "DOC-006": "fixtures/documents/doc_006_sensitive_payment.txt",
}


def register_local_document_workflow(Supervisor: Any) -> None:
    """Register route/run hooks for DOC-* local document scenarios."""
    if getattr(Supervisor, "_local_document_workflow_registered", False):
        return

    original_route_intent = Supervisor.route_intent
    original_run_workflow = Supervisor.run_workflow

    def route_intent(self: Any, prompt: str, farm_profile: Dict[str, Any]) -> str:
        prompt_l = prompt.lower()
        if _looks_like_local_document_prompt(prompt_l):
            return "local_document_extraction"
        return original_route_intent(self, prompt, farm_profile)

    def run_workflow(
        self: Any,
        farm_profile: Dict[str, Any],
        user_id: str,
        user_role: str,
        prompt: str,
        observations: Dict[str, Any],
        target_farm_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        topic = route_intent(self, prompt, farm_profile)
        if topic == "local_document_extraction":
            return _run_local_document_extraction(
                self=self,
                farm_profile=farm_profile,
                user_id=user_id,
                user_role=user_role,
                prompt=prompt,
                target_farm_id=target_farm_id,
            )
        return original_run_workflow(
            self,
            farm_profile=farm_profile,
            user_id=user_id,
            user_role=user_role,
            prompt=prompt,
            observations=observations,
            target_farm_id=target_farm_id,
        )

    Supervisor.route_intent = route_intent
    Supervisor.run_workflow = run_workflow
    Supervisor._local_document_workflow_registered = True


def _run_local_document_extraction(
    self: Any,
    farm_profile: Dict[str, Any],
    user_id: str,
    user_role: str,
    prompt: str,
    target_farm_id: Optional[str] = None,
) -> Dict[str, Any]:
    requesting_farm_id = farm_profile.get("farm_id", "")
    target_farm_id = target_farm_id or requesting_farm_id
    workflow_id = f"wf_{requesting_farm_id}_{user_id}"

    if not check_cross_farm_block(requesting_farm_id, target_farm_id):
        return _blocked_action_pack(requesting_farm_id, workflow_id, ["Cross-farm data leakage attempt blocked."])

    file_path = _extract_document_path(prompt)
    if not file_path:
        return _needs_info_action_pack(
            farm_id=requesting_farm_id,
            workflow_id=workflow_id,
            warnings=["No local document fixture path was found in the prompt."],
            missing_data=["local_document_fixture"],
        )

    capability_grant = self.broker.request_capability_grant(farm_profile, user_id, "records_tool")
    if not capability_grant.get("authorized"):
        return _blocked_action_pack(
            requesting_farm_id,
            workflow_id,
            ["User lacks permission to view operational records for local document extraction."],
        )

    evidence_board = EvidenceBoard()
    try:
        tool_result = self.gateway.extract_local_document(
            capability_grant=capability_grant,
            requesting_farm_id=requesting_farm_id,
            target_farm_id=target_farm_id,
            file_path=file_path,
            document_id=_document_id_from_prompt(prompt),
            user_role=user_role,
            evidence_board=evidence_board,
        )
    except Exception as exc:
        return _needs_info_action_pack(
            farm_id=target_farm_id,
            workflow_id=workflow_id,
            warnings=[f"Local document extraction failed: {exc}"],
            missing_data=["readable_local_document"],
        )

    payload = tool_result["payload"]
    human_review = _human_review_for_runner(payload.get("human_review", {}))
    evidence_ids = [payload.get("evidence_id")] if payload.get("evidence_id") else []
    missing_fields = payload.get("missing_fields", [])

    recommendation = {
        "title": f"Review extracted {payload.get('document_type', 'document')} fields",
        "urgency": "normal",
        "confidence": payload.get("extraction_confidence", "low"),
        "summary": _summary_from_payload(payload),
        "recommendation": _recommendation_from_payload(payload),
        "evidence_ids": evidence_ids,
        "human_review_status": human_review,
    }

    proposed_actions = []
    for index, proposed in enumerate(payload.get("proposed_actions", []), start=1):
        proposed_actions.append(
            {
                "action_id": f"act_doc_{payload.get('document_id', 'local')}_{index}",
                "action_type": proposed.get("action_type", "draft_official_record_update"),
                "payload": {
                    "status": proposed.get("status", "blocked_pending_user_approval"),
                    "requires_approval": True,
                    "document_type": payload.get("document_type"),
                    "proposed_record": payload.get("proposed_record"),
                    "source_evidence_id": payload.get("evidence_id"),
                    "external_action": False,
                },
            }
        )

    warnings = list(payload.get("notes", []))
    if user_role == "field_employee":
        warnings.append("Supplier quote and pricing details are hidden for your role.")

    return {
        "action_pack_id": f"ap_{target_farm_id}_local_document",
        "farm_id": target_farm_id,
        "workflow_id": workflow_id,
        "recommendations": [recommendation],
        "proposed_actions": proposed_actions,
        "evidence_summary": evidence_board.list_evidence(),
        "warnings": warnings,
        "missing_data": missing_fields,
        "human_review_status": human_review,
        "status": "draft",
    }


def _looks_like_local_document_prompt(prompt_l: str) -> bool:
    return bool(
        "fixtures/documents/" in prompt_l
        or re.search(r"\bdoc-00[1-6]\b", prompt_l)
        or ("document" in prompt_l and ("extract" in prompt_l or "invoice" in prompt_l or "quote" in prompt_l))
    )


def _extract_document_path(prompt: str) -> Optional[str]:
    match = re.search(r"fixtures/documents/[A-Za-z0-9_.\-/]+", prompt)
    if match:
        return match.group(0).rstrip(".,;:)")
    doc_id = _document_id_from_prompt(prompt)
    if doc_id and doc_id in DOC_FIXTURE_MAP:
        return DOC_FIXTURE_MAP[doc_id]
    return None


def _document_id_from_prompt(prompt: str) -> Optional[str]:
    match = re.search(r"\bDOC-00[1-6]\b", prompt.upper())
    return match.group(0) if match else None


def _summary_from_payload(payload: Dict[str, Any]) -> str:
    fields = payload.get("extracted_fields", {})
    supplier = fields.get("supplier_name") or "unknown supplier"
    doc_type = payload.get("document_type", "document")
    confidence = payload.get("extraction_confidence", "low")
    missing = payload.get("missing_fields", [])
    missing_text = ", ".join(missing) if missing else "no required fields missing"
    return f"Extracted a {doc_type} from {supplier} with {confidence} confidence; {missing_text}."


def _recommendation_from_payload(payload: Dict[str, Any]) -> str:
    if payload.get("extraction_confidence") == "low" or payload.get("document_type") == "unknown":
        return "Ask the user to clarify the missing or ambiguous fields. Do not update official records."
    if payload.get("missing_fields"):
        return "Review the extracted draft and resolve missing fields before approving any official record update."
    return "Review the extracted draft before approving any official record update. No external action has been taken."


def _human_review_for_runner(review: Dict[str, Any]) -> Dict[str, Any]:
    status = review.get("status", "needs_user_approval")
    return {
        "required": bool(review.get("required", True)),
        "review_type": review.get("review_type", "user_approval"),
        "risk_tier": "tier_3" if status in {"needs_info", "needs_user_approval"} else "tier_2",
        "status": status,
        "reason": review.get("reason", ["farm_restricted_document"]),
        "recommended_reviewer": ["farm_owner", "farm_manager"],
        "approval_required_before": review.get(
            "approval_required_before",
            ["official_record_update", "external_message", "supplier_selection"],
        ),
    }


def _blocked_action_pack(farm_id: str, workflow_id: str, warnings: list[str]) -> Dict[str, Any]:
    hr = {
        "required": False,
        "review_type": "blocked",
        "risk_tier": "tier_4",
        "status": "blocked",
        "reason": ["authorization_or_cross_farm_block"],
        "recommended_reviewer": ["farm_owner"],
        "approval_required_before": ["view_restricted_data"],
    }
    return {
        "action_pack_id": f"ap_{farm_id}_local_document_blocked",
        "farm_id": farm_id,
        "workflow_id": workflow_id,
        "recommendations": [],
        "proposed_actions": [],
        "evidence_summary": [],
        "warnings": warnings,
        "missing_data": [],
        "human_review_status": hr,
        "status": "blocked",
    }


def _needs_info_action_pack(farm_id: str, workflow_id: str, warnings: list[str], missing_data: list[str]) -> Dict[str, Any]:
    hr = {
        "required": True,
        "review_type": "user_approval",
        "risk_tier": "tier_3",
        "status": "needs_info",
        "reason": ["missing_or_ambiguous_fields"],
        "recommended_reviewer": ["farm_owner", "farm_manager"],
        "approval_required_before": ["official_record_update"],
    }
    return {
        "action_pack_id": f"ap_{farm_id}_local_document_needs_info",
        "farm_id": farm_id,
        "workflow_id": workflow_id,
        "recommendations": [],
        "proposed_actions": [],
        "evidence_summary": [],
        "warnings": warnings,
        "missing_data": missing_data,
        "human_review_status": hr,
        "status": "draft",
    }
