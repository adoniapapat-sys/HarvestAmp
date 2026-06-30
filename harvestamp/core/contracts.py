# harvestamp/core/contracts.py
"""Shared contract definitions and normalization helpers for HarvestAmp.

Defines the fields, scopes, and allowed action types/statuses for agents,
findings, and ActionPacks, facilitating verification and structural guarantees.
"""
from typing import Any, Dict, List, Optional

# 1. Agent Finding Fields
AGENT_FINDING_FIELDS = [
    "finding_id",
    "agent",
    "lane",
    "finding_type",
    "summary",
    "details",
    "evidence_ids",
    "source_scope",
    "farm_record_anchor",
    "public_context_only",
    "missing_data",
    "assumptions",
    "confidence",
    "human_review",
    "review_required",
    "recommended_reviewers",
    "role_visibility",
    "proposed_actions",
    "blocked_actions",
    "safety_flags"
]

# 2. Action Pack Fields
ACTION_PACK_FIELDS = [
    "action_pack_id",
    "farm_id",
    "workflow_id",
    "recommendations",
    "proposed_actions",
    "evidence_summary",
    "warnings",
    "missing_data",
    "human_review_status",
    "status"
]

# 3. Source Scope Values
SOURCE_SCOPE_VALUES = [
    "farm_record",
    "public_context",
    "document_extraction",
    "fixture",
    "mixed"
]

# 4. Draft-Only Action Types
DRAFT_ONLY_ACTION_TYPES = [
    "supplier_message",
    "customer_message",
    "certifier_message",
    "draft_official_record_update",
    "draft_inventory_reconciliation",
    "draft_bin_reconciliation",
    "draft_cooler_inventory_update",
    "draft_sales_record_reconciliation",
    "draft_grain_load_ticket_record",
    "draft_elevator_settlement_record",
    "draft_harvest_record_update"
]

# 5. MVP Action Statuses
MVP_ACTION_STATUSES = [
    "draft",
    "needs_info",
    "needs_user_approval",
    "needs_expert_review",
    "blocked_pending_user_approval",
    "approved_simulated",
    "rejected",
    "not_executed"
]

# 6. Executed Action Wording (Prohibited in active advice / outputs)
EXECUTED_ACTION_WORDING = [
    "email sent",
    "message sent",
    "supplier contacted",
    "customer contacted",
    "buyer contacted",
    "order placed",
    "purchase approved",
    "sale executed",
    "grain sold",
    "invoice sent",
    "official record updated",
    "inventory updated",
    "filed with regulator",
    "filed with fsa"
]

# 7. Advisor Drift Wording (Prohibited in active advice / outputs)
ADVISOR_DRIFT_WORDING = [
    "sell now",
    "hold grain",
    "lock in price",
    "hedge now",
    "apply this pesticide",
    "spray tomorrow",
    "tank mix"
]

# 8. Restricted Field Employee Terms (Prohibited in field_employee views)
RESTRICTED_FIELD_EMPLOYEE_TERMS = [
    "supplier pricing",
    "quote price",
    "operating margin",
    "gross margin",
    "customer financial",
    "payment status",
    "buyer terms",
    "invoice",
    "official approval"
]


def normalize_agent_finding_contract(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Shallowly copies the finding and populates missing contract fields with defaults.

    Does not invent domain facts; derives values from nested structures if present.
    """
    res = dict(finding)

    # Establish structural defaults
    defaults = {
        "finding_id": None,
        "agent": None,
        "lane": None,
        "finding_type": None,
        "summary": "",
        "details": {},
        "evidence_ids": [],
        "source_scope": "farm_record",
        "farm_record_anchor": None,
        "public_context_only": False,
        "missing_data": [],
        "assumptions": [],
        "confidence": "medium",
        "human_review": {},
        "review_required": False,
        "recommended_reviewers": [],
        "role_visibility": ["farm_owner", "farm_manager"],
        "proposed_actions": [],
        "blocked_actions": [],
        "safety_flags": []
    }

    # Extract review details from human_review dict if present and not overridden
    hr = res.get("human_review")
    if isinstance(hr, dict):
        if "required" in hr and "review_required" not in res:
            defaults["review_required"] = bool(hr["required"])
        if "recommended_reviewers" in hr and "recommended_reviewers" not in res:
            defaults["recommended_reviewers"] = list(hr["recommended_reviewers"])
        elif "reviewers" in hr and "recommended_reviewers" not in res:
            defaults["recommended_reviewers"] = list(hr["reviewers"])

    # Apply defaults
    for k, v in defaults.items():
        if k not in res:
            res[k] = v

    return res


def has_required_agent_finding_fields(finding: Dict[str, Any]) -> bool:
    """Returns True if all agent finding contract fields are present."""
    return all(field in finding for field in AGENT_FINDING_FIELDS)


def normalize_action_pack_contract(action_pack: Dict[str, Any]) -> Dict[str, Any]:
    """Shallowly copies the action pack and populates missing fields with defaults."""
    res = dict(action_pack)

    defaults = {
        "action_pack_id": None,
        "farm_id": None,
        "workflow_id": None,
        "recommendations": [],
        "proposed_actions": [],
        "evidence_summary": [],
        "warnings": [],
        "missing_data": [],
        "human_review_status": {},
        "status": "draft"
    }

    for k, v in defaults.items():
        if k not in res:
            res[k] = v

    return res


def has_required_action_pack_fields(action_pack: Dict[str, Any]) -> bool:
    """Returns True if all action pack contract fields are present."""
    return all(field in action_pack for field in ACTION_PACK_FIELDS)


def contains_forbidden_wording(text: str) -> List[str]:
    """Performs a case-insensitive check for executed action and advisor drift wording.

    Returns a list of matching phrases.
    """
    matches = []
    text_lower = text.lower()
    for phrase in EXECUTED_ACTION_WORDING + ADVISOR_DRIFT_WORDING:
        if phrase in text_lower:
            matches.append(phrase)
    return matches
