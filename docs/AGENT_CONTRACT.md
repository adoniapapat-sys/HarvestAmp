# HarvestAmp Agent & Synthesizer Contract Specification

This document defines the interface and safety contract boundaries for all agent findings, recommendations, proposed actions, and ActionPacks generated within HarvestAmp.

---

## 1. Agent Finding Required Fields

Every normalized agent finding must contain the following fields:

| Field Name | Type | Description / Default Value |
|---|---|---|
| `agent` | `str` or `None` | Name/ID of the emitting agent |
| `lane` | `str` or `None` | The topic lane classification (e.g. `direct_market_sales`) |
| `finding_type` | `str` or `None` | Type category of the finding (e.g. `csa_packout_check`) |
| `summary` | `str` | Text summary of the finding |
| `details` | `dict` | Additional structured parameters (defaults to `{}`) |
| `evidence_ids` | `list[str]` | IDs of direct supporting evidence records (defaults to `[]`) |
| `source_scope` | `str` | Scope category of evidence (defaults to `"farm_record"`) |
| `farm_record_anchor` | `str` or `None` | Reference identifier for key decision records |
| `public_context_only` | `bool` | True if finding relies entirely on public context |
| `missing_data` | `list[str]` | Missing inputs required for complete execution |
| `assumptions` | `list[str]` | Assumptions made during calculation |
| `confidence` | `str` | Confidence level: `"high"`, `"medium"`, or `"low"` |
| `human_review` | `dict` | Nested human review policy details |
| `review_required` | `bool` | Conveniency flag indicating if review is required |
| `recommended_reviewers` | `list[str]` | Recommended reviewers (derived from `human_review` if present) |
| `role_visibility` | `list[str]` | Authorized viewer roles (defaults to all manager/owner roles) |
| `proposed_actions` | `list[dict]` | List of proposed draft actions |
| `blocked_actions` | `list[str]` | List of blocked actions / action blockers |
| `safety_flags` | `list[str]` | Safety warnings or restrictions |

---

## 2. ActionPack Required Fields

The synthesized ActionPack object returned by the workflow coordinator must contain:

- `action_pack_id`: Unique identifier for the action pack execution.
- `farm_id`: The ID of the target farm.
- `workflow_id`: Workflow runner context ID.
- `recommendations`: Aggregated recommendation findings list.
- `proposed_actions`: List of proposed draft actions (empty for restricted roles).
- `evidence_summary`: Summaries of all resolved evidence records.
- `warnings`: Action pack warnings (e.g., role warnings, missing data notifications).
- `missing_data`: List of missing data requirements aggregated from findings.
- `human_review_status`: Top-level human review status and blockers dictionary.
- `status`: Overall action pack execution status (e.g. `"draft"`, `"blocked"`).

---

## 3. Source Scopes

All resolved evidence must be tagged with a source scope indicating its provenance:
- `farm_record`: Farm-confidential data (harvest logs, scale tickets, bin records).
- `public_context`: Public benchmarks (USDA AMS news, EIA fuel, NWS weather).
- `document_extraction`: Extracted values from user-provided PDF/doc files.
- `fixture`: Pre-loaded test fixture files.
- `mixed`: Integrations containing multiple source scopes.

---

## 4. Evidence Preservation

- Every proposed draft action must point directly to its primary source evidence via `source_evidence_id`.
- Dynamic actions must not list unrelated evidence IDs; the `related_evidence` list must be trimmed to only contain records directly supporting that specific action.
- Public context (e.g. NWS weather) must never be used as primary source evidence for farm-specific record updates or financial actions.

---

## 5. Missing-Data Visibility

- Gaps in required datasets must be logged in the `missing_data` array.
- Findings must not contain contradictory missing-data records (e.g., listing a data item as missing when it is present in the context).
- If critical information is missing, the finding/action status must transition to `needs_info`, triggering a required review.

---

## 6. Draft-Only Action Rule

All proposed actions must be **draft-only**. The system does not write directly to external endpoints or execute real-world changes without explicit user approval.
Allowed action types are defined in `DRAFT_ONLY_ACTION_TYPES` (e.g. `draft_cooler_inventory_update`, `supplier_message`).

---

## 7. Human-Review Rule

All action updates, elevator settlements, bin updates, and compliance tasks must require human review before commit:
- Action payload statuses must reflect approval gates (`blocked_pending_user_approval`, `needs_info`).
- Review statuses must match: `needs_info` must result in `required: True` in the human review block.

---

## 8. Role-Visibility Rule

- Restricted roles (such as `field_employee`) must receive sanitized outputs.
- Proposed actions are hidden from the employee view.
- Recommendations are softened to instruct the employee to verify counts physically or contact management.
- Prices, margins, and private customer names are hidden or masked.

---

## 9. Public-Context-Only Rule

- Public connector data (EIA index, USDA regional reports) serves as advisory context only.
- Local, farm-specific records (quotes, orders) serve as the decision anchor.

---

## 10. Lane-Discipline Rule

- Specialists must only emit findings and recommendations belonging to their designated functional lanes.
- Inter-agent coordination is mediated by the Synthesizer and Supervisor to prevent cross-contamination of concerns.

---

## 11. MVP Action Boundary

No execution side-effects (e.g. sending emails, executing sales, updating databases) are permitted. All outputs are simulated and returned as drafts within the ActionPack container.
Phrases indicating real-world action execution ("email sent", "sale executed", "invoice sent") or direct financial advisory drift ("sell now", "hedge now") are strictly prohibited in the agent's textual output.

---

## 12. Why Phase 1 Defines the Contract but Does Not Enforce Runtime Validation Yet

To ensure system stability, Phase 1 establishes the shared contract surface, helper functions, and test coverage to validate findings and ActionPacks without changing the live runtime execution behavior of the agents or workflows. This provides a safe, incremental path to full enforcement in subsequent phases.
