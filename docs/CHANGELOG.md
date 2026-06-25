# HarvestAmp Changelog

This changelog records source-of-truth documentation, schema, fixture, and configuration changes for HarvestAmp.

HarvestAmp follows a documentation-first build approach. Major product and architecture decisions belong in `DECISION_LOG.md`; this changelog records what changed and when.

---

## Versioning Convention

- `v0.x` versions are planning and MVP-design artifacts.
- Live working files use stable names, such as `02_AGENT_ARCHITECTURE.md`.
- Versioned snapshots use suffixes, such as `02_AGENT_ARCHITECTURE_v0_4_HarvestAmp.md`.
- Implementation scaffolds live in `schemas/`, `fixtures/`, and `configs/`.

---

## [Unreleased]

### Added
- Implemented mock/manual irrigation scheduling and water-request workflows (IRR-001 through IRR-005) using local fixture data only.
- Added YAML fixtures and schema definitions for `irrigation_schedules` and `irrigation_requests` under `fixtures/data_observations.yaml`, `fixtures/scenarios.yaml`, and `schemas/data_observations.schema.yaml`.
- Implemented `get_irrigation_schedule` and `get_irrigation_request_context` under `ToolGateway` in `harvestamp/gateway/tools.py` with capability gates and farm isolation checks.
- Integrated credentials exposure detection and unauthorized role blocks directly in `Supervisor.run_workflow` in `harvestamp/workflows/supervisor.py`, logging security audits without executing specialists.
- Updated `WeatherAgent`, `RecordsAgent`, and `ComplianceAgent` in `harvestamp/agents/specialists.py` to support irrigation weather context, Thursday scheduling advisories, draft Tuesday request contexts, and water-rights expert review triggers.
- Updated `HumanReviewPolicy` and `RecommendationSynthesizer` to draft proposed action `submit_irrigation_request` (with `needs_user_approval` and `blocked_until_approved`) and propagate `needs_info` statuses.
- Added functional tests in `tests/test_irrigation.py` covering all scenario paths and gate policies.
- Implemented the first read-only connector: National Weather Service (NWS) forecast API adapter in `harvestamp/connectors/nws_weather.py` supporting coordinate rounding to 4 decimal places, live network querying (behind environment variables and User-Agent safety checks), and default offline mock mode.
- Integrated the NWS Weather Connector in `ToolGateway.get_weather` in shadow mode: logs connector results as shadow evidence to the Evidence Board, but returns mock weather observations for actual agent execution.
- Added NWS failure fallback mapping: if NWS is stale, unavailable, or errors, falls back to mock fixture weather (if available) with `fallback_used=True` and `fallback_reason` metadata, and lowers WeatherAgent finding confidence to `"low"`.
- Added unit tests in `tests/test_nws_weather_connector.py` covering successful weather responses, NWS failure status codes, Evidence Board recording, gateway fallback mediation, WeatherAgent confidence degradation, and simulated live mode paths.
- Added irrigation scheduling / water-request domain to planning docs (data-source entries, risk/human-review policy, agent contracts, sample scenarios, evaluation expectations, and next build tasks).
- Added optional irrigation fields to `03_FARM_PROFILES.md`.

### Planned
- Add first UI prototype for weekly plans, procurement recommendations, human-review gates, and disclosure previews.

---

## [0.4.2] - 2026-06-24

### Fixed
- Fixed stale PVF-004 test expectations in `tests/test_scenarios.py` to match normalized missing-data labels.
- Resolved `NameError: name 'topic' is not defined` crash in `scripts/run_scenario.py` by deriving the topic before context package creation.
- Adjusted aggregate human review policy for `SYS-005` stale clamshell inventory when no supplier messages or purchase orders are created to require no approval and flag status as `needs_info`.
- Filtered packaging inventory and packaging evidence from GBO-005 organic input verification results.
- Redacted sensitive fuel/grain evidence IDs for `field_employee` in Prairie View Farms weekly plans, replacing them with a redacted operational evidence label `"Authorized operational records"`.
- Escalated GBO-005 Organic Input Records finding review status to `needs_expert_review` when certifier/expert review is recommended.
- Softened PVF-002 diesel buy recommendation wording to suggest considering a split-buy strategy or preparing a fuel quote inquiry for approval.

---

## [0.4.1] - 2026-06-23

### Changed
- Decoupled internal topic names from user-facing section titles: mapped "Weekly Plan Pvf" to "Prairie View Input Watch" and "Weekly Plan Gbo" to "Green Basket Packaging Watch".
- Restored "Evidence Used" section to the weekly-plan runner CLI output.
- Softened directive procurement wording (e.g. "Prepare a CSA box reorder for owner approval" and "Prepare a fuel quote inquiry for approval").
- Adjusted Green Basket compliance finding review status to respect expert/certifier review requirements (`needs_expert_review`) instead of defaulting to `review_not_required`.
- Hardened Prairie View `field_employee` view to redact exact gallons, expected 30-day need, and purchase order recommendations, replacing them with a redacted operational message.
- Bypassed financial and user approval policies for restricted roles on weekly plans when no actionable proposed actions are drafted.
- Keep commodity market recommendations scenario/watchlist-based ("watchlist item; not a sale recommendation").

### Security and Privacy
- Restricted roles (like `field_employee`) receive fully redacted recommendations and do not trigger financial action review gates on weekly plans, preventing unauthorized access to pricing, margins, or quotes.

## [0.4.0] - 2026-06-23

### Added
- Implemented `test_restricted_role_weekly_plans` to verify restricted-role weekly plans return redacted operational views instead of fully blocked outputs.
- Enhanced `test_source_metadata_evidence` to verify source metadata fields are preserved in ActionPack evidence summaries.

### Changed
- Hardened the Weekly Farm Plan Runner to switch specialist agents on `work_item["topic"]` rather than intent keywords.
- Updated `WeatherAgent` to return Prairie View fieldwork weather and GBO Saturday market weather with forecast uncertainty and proper advice (covers tent weights, ventilating high tunnels).
- Updated `ProcurementAgent` to use fixture-specific fuel levels and quotes, flag low fuel watches, caution on missing fertilizer fees, apply buy/wait/split framing with correct tank math (bringing tank to 3,350 gallons with 650 gallons headspace, avoiding saying it fills the 4,000-gallon tank), and ask for updated inventory counts and expected harvest volumes when clamshell data is stale.
- Updated `RecordsAgent` to verify fuel inventory freshness, crop-protection gaps, stored grain records, and organic documentation completeness.
- Updated `MarketAgent` to track stored grain watches without executing sales, direct-market CSA packing and restaurant availability, and structured farmers market pack lists with weather adjustments.
- Updated `ComplianceAgent` to track USDA deadlines, organic status uncertainty, OSP input approvals, and spray label responsible human caveats.
- Updated `MarginAgent` to hide financial margin scenarios for restricted roles.
- Enhanced `ContextPackageBuilder` to enforce task-scoped context minimization (SYS-003 and PVF-005 spray-window exclusions).
- Hardened `RecommendationSynthesizer` to draft action candidates for weekly plans (fuel quote inquiry for PVF, CSA box order and certifier verification request for GBO) and ensure aggregate ActionPack review reflects required approval.

### Security and Privacy
- Restricted roles (e.g. `field_employee`, `field_lead`, `market_staff`) now receive redacted operational views for weekly plans instead of fully blocked plans, with sensitive quotes, certification details, financials, and margins filtered out and warnings applied.

---

## [0.3.0] - 2026-06-23

### Added

- Created repository folder structure.
- Created `README.md` and `ANTIGRAVITY_TASKS.md`.
- Implemented YAML schemas in `schemas/` for all HarvestAmp entities:
  - `common_defs`, `work_item`, `farm_context_package`, `agent_finding`, `evidence_item`, `human_review`, `action_pack`, `audit_event`, `source_metadata`, `connector_result`, `recommendation`, `farm_profile`, `quote`, `inventory_item`, and `scenario`.
- Created configs in `configs/human_review_rules.yaml`.
- Created YAML fixtures under `fixtures/` in their final layout:
  - `fixtures/farms/prairie_view_farms.yaml`
  - `fixtures/farms/green_basket_organics.yaml`
  - `fixtures/source_metadata.yaml`
  - `fixtures/data_observations.yaml`
  - `fixtures/scenarios.yaml`
- Created modular Python package `harvestamp/` containing sub-packages:
  - `core` (Evidence Board, math utilities, schema validation)
  - `auth` (roles permission model, Credential Broker)
  - `gateway` (Tool Gateway)
  - `context` (Context Package Builder)
  - `policy` (deterministic human review policy and action gating rules)
  - `agents` (mock specialist agents)
  - `workflows` (Supervisor workflow and Intent Router)
  - `audit` (audit logging)
- Created execution runner scripts in `scripts/`:
  - `validate_fixtures.py` (fixture validation)
  - `run_scenario.py` (local mock scenario runner for 15 scenarios)
  - `run_weekly_plan.py` (weekly plan runner)
- Created pytest test suite in `tests/` covering:
  - schema validation, authorization, data freshness, human review rules, math utilities, context minimization, supervisor routing, action gating, brand consistency, and source metadata.

---

## [0.2.0] - 2026-06-23

### Added

- Added `CHANGELOG.md`.
- Added schema scaffold directory: `schemas/`.
- Added fixture scaffold directory: `fixtures/`.
- Added config scaffold directory: `configs/`.
- Added `configs/human_review_rules.yaml`.
- Added MVP schema drafts:
  - `schemas/common_defs.schema.yaml`
  - `schemas/work_item.schema.yaml`
  - `schemas/farm_context_package.schema.yaml`
  - `schemas/agent_finding.schema.yaml`
  - `schemas/recommendation.schema.yaml`
  - `schemas/action_pack.schema.yaml`
  - `schemas/human_review.schema.yaml`
  - `schemas/evidence_item.schema.yaml`
  - `schemas/farm_profile.schema.yaml`
  - `schemas/quote.schema.yaml`
  - `schemas/inventory_item.schema.yaml`
  - `schemas/audit_event.schema.yaml`
- Added MVP fixtures:
  - `fixtures/prairie_view_farms.yaml`
  - `fixtures/green_basket_organics.yaml`
  - `fixtures/sample_work_items.yaml`
  - `fixtures/sample_context_packages.yaml`
  - `fixtures/sample_evidence.yaml`
  - `fixtures/sample_uploads_and_quotes.yaml`
  - `fixtures/sample_agent_findings.yaml`
  - `fixtures/sample_action_packs.yaml`
  - `fixtures/sample_audit_events.yaml`
  - `fixtures/sample_scenarios.yaml`

### Notes

- Schema files are planning scaffolds, not final production contracts.
- Fixture files are synthetic and must not include real customer farm data unless explicitly authorized.
- The initial fixture IDs align with `03_FARM_PROFILES.md` where practical: `PVF_ROW_CROP_001`, `GBO_DIRECT_001`, `pvf_owner_001`, and `gbo_owner_001`.

---

## [0.1.0] - 2026-06-23

### Added

- Created the initial HarvestAmp source-of-truth document set:
  - `01_PRODUCT_BRIEF.md`
  - `02_AGENT_ARCHITECTURE.md`
  - `03_FARM_PROFILES.md`
  - `04_DATA_SOURCES.md`
  - `05_AGENT_CONTRACTS.md`
  - `06_RISK_AND_HUMAN_REVIEW_POLICY.md`
  - `07_SAMPLE_SCENARIOS.md`
  - `08_EVALUATION_TESTS.md`
  - `09_MVP_SCOPE.md`
  - `10_BUILD_PLAN.md`
  - `DECISION_LOG.md`
- Established the two-farm MVP scope:
  - Prairie View Farms: large conventional row-crop operation.
  - Green Basket Organics: small certified organic direct-market operation.
- Established HarvestAmp as the working product and agent name.
- Established the multi-agent architecture with a Supervisor / Orchestrator Agent and specialist agents.
- Established deterministic infrastructure for authorization, credentials, tool access, context packaging, audit logging, and policy enforcement.
- Established human-in-the-loop gates for financial, compliance, safety, privacy, external disclosure, and irreversible actions.

### Security and Privacy

- Agents receive task-scoped context, not unrestricted farm data.
- Raw credentials must never be exposed to LLM prompts, logs, memory, vector stores, or transcripts.
- Cross-farm and cross-tenant leakage is a critical-fail rule.

---

## Change Entry Template

```md
## [x.y.z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Removed
- ...

### Security and Privacy
- ...

### Notes
- ...
```
