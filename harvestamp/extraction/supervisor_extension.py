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


def _looks_like_explicit_document_review_prompt(prompt_l: str) -> bool:
    return any(
        phrase in prompt_l for phrase in [
            "review my local extracted documents",
            "review the supplier quote",
            "review the supplier invoice",
            "review the fuel receipt",
            "review the packaging receipt",
            "review the harvest load ticket",
            "review the inventory count sheet",
            "missing from the extracted document",
        ]
    )


def _document_type_from_review_prompt(prompt_l: str) -> Optional[str]:
    if "supplier quote" in prompt_l:
        return "supplier_quote"
    if "supplier invoice" in prompt_l:
        return "supplier_invoice"
    if "fuel receipt" in prompt_l:
        return "fuel_receipt"
    if "packaging receipt" in prompt_l:
        return "packaging_receipt"
    if "harvest load ticket" in prompt_l:
        return "harvest_load_ticket"
    if "inventory count sheet" in prompt_l:
        return "inventory_count_sheet"
    return None


def register_local_document_workflow(Supervisor: Any) -> None:
    """Register route/run hooks for DOC-* and explicit document scenarios."""
    if getattr(Supervisor, "_local_document_workflow_registered", False):
        return

    original_route_intent = Supervisor.route_intent
    original_run_workflow = Supervisor.run_workflow

    def route_intent(self: Any, prompt: str, farm_profile: Dict[str, Any]) -> str:
        prompt_l = prompt.lower()
        if _looks_like_explicit_document_review_prompt(prompt_l):
            return "document_review"
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
        if topic == "document_review":
            return _run_document_review_workflow(
                self=self,
                farm_profile=farm_profile,
                user_id=user_id,
                user_role=user_role,
                prompt=prompt,
                target_farm_id=target_farm_id,
            )
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


def _run_document_review_workflow(
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

    capability_grant = self.broker.request_capability_grant(farm_profile, user_id, "records_tool")
    if not capability_grant.get("authorized"):
        return _blocked_action_pack(
            requesting_farm_id,
            workflow_id,
            ["User lacks permission to view operational records for local document extraction."],
        )

    doc_type = _document_type_from_review_prompt(prompt.lower())

    extracted_docs = self.gateway.get_extracted_documents(
        capability_grant=capability_grant,
        requesting_farm_id=requesting_farm_id,
        target_farm_id=target_farm_id,
        user_role=user_role,
        document_type=doc_type,
    )

    evidence_board = EvidenceBoard()
    restricted_roles = {"field_employee", "seasonal_worker", "crew_member", "employee"}
    is_restricted = user_role in restricted_roles

    for doc in extracted_docs:
        ev_id = "Authorized operational records" if is_restricted else doc["evidence_id"]
        evidence_board.add_evidence(
            evidence_id=ev_id,
            source_id=doc["document_id"],
            source_name=doc.get("source_name", "Local Document Extraction"),
            trust_tier=doc["trust_tier"],
            freshness_status=doc.get("freshness_status", "fresh"),
            privacy_class=doc["privacy_class"],
            data_payload=doc["extracted_fields"],
            description=f"Local document extraction for {doc['document_type']}",
            timestamp=None,
            farm_id=target_farm_id,
            authorization_status="authorized",
        )

    context_pkg = self.context_builder.build_context_package(farm_profile, user_role, "document_review")
    work_item_proc = {
        "work_item_id": f"wi_pr_{user_id}",
        "workflow_id": workflow_id,
        "farm_id": target_farm_id,
        "requesting_user_id": user_id,
        "user_intent": prompt,
        "topic": "document_review"
    }
    work_item_rec = {
        "work_item_id": f"wi_re_{user_id}",
        "workflow_id": workflow_id,
        "farm_id": target_farm_id,
        "requesting_user_id": user_id,
        "user_intent": prompt,
        "topic": "document_review"
    }

    findings = []
    
    proc_finding = self.proc_agent.surface_extracted_documents(
        work_item=work_item_proc,
        context=context_pkg,
        extracted_documents=extracted_docs,
    )
    if proc_finding:
        findings.append(proc_finding)
        
    rec_finding = self.records_agent.surface_extracted_documents(
        work_item=work_item_rec,
        context=context_pkg,
        extracted_documents=extracted_docs,
    )
    if rec_finding:
        findings.append(rec_finding)

    action_pack = self.synthesizer.synthesize(
        farm_id=target_farm_id,
        workflow_id=workflow_id,
        findings=findings,
        evidence_list=evidence_board.list_evidence(),
        user_role=user_role
    )

    if is_restricted:
        warn = "Supplier quotes, input pricing, margin, and marketing details are hidden for your role."
        if warn not in action_pack.get("warnings", []):
            action_pack.setdefault("warnings", []).append(warn)

    return action_pack
