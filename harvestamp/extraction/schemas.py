"""Data structures for local document extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class HumanReview:
    required: bool
    review_type: str
    status: str
    reason: List[str] = field(default_factory=list)
    approval_required_before: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentExtractionResult:
    document_id: str
    farm_id: str
    document_type: str
    source_name: str
    source_file_reference: str
    extraction_status: str
    extraction_confidence: str
    data_sensitivity: str
    extracted_fields: Dict[str, Any]
    missing_fields: List[str]
    redactions_applied: List[str]
    evidence_id: str
    human_review: HumanReview
    evidence: Dict[str, Any]
    proposed_record: Optional[Dict[str, Any]] = None
    proposed_actions: List[Dict[str, Any]] = field(default_factory=list)
    official_update_allowed: bool = False
    external_actions_allowed: bool = False
    decision_anchor_status: str = "draft_pending_review"
    notes: List[str] = field(default_factory=list)
    redacted_text_excerpt: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["human_review"] = self.human_review.to_dict()
        return data
