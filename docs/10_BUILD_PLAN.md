# 10_BUILD_PLAN.md

# Build Plan: HarvestAmp

**Version:** 0.1  
**Date:** 2026-06-23  
**Status:** Draft implementation planning document  
**Product / agent name:** HarvestAmp  
**Related documents:**

- `01_PRODUCT_BRIEF.md`
- `02_AGENT_ARCHITECTURE.md`
- `03_FARM_PROFILES.md`
- `04_DATA_SOURCES.md`
- `05_AGENT_CONTRACTS.md`
- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`
- `07_SAMPLE_SCENARIOS.md`
- `08_EVALUATION_TESTS.md`
- `09_MVP_SCOPE.md`

**Intended use:** Practical execution plan for building the HarvestAmp MVP using Antigravity, Google ADK, Gemini / Vertex AI, Google Cloud services, controlled data connectors, evaluation tests, and staged human-review workflows.

---

## 0. Important Note

This document is the build roadmap for the HarvestAmp MVP.

HarvestAmp is intentionally ambitious. The MVP should be intentionally narrow. The goal is not to build a complete agriculture platform in the first pass. The goal is to prove that a multi-agent architecture can produce useful, safe, farm-specific recommendations for two representative farm profiles while enforcing authorization, privacy, evidence, and human-review guardrails.

This build plan should be used to keep Antigravity tasks focused. Each task should reference the relevant source-of-truth documents and produce artifacts that can be evaluated against `07_SAMPLE_SCENARIOS.md` and `08_EVALUATION_TESTS.md`.

This document should not be treated as code. It is an implementation roadmap, task sequencing guide, and acceptance-gate checklist.

---

## 1. Build Objective

The MVP build objective is:

> Build a working HarvestAmp prototype that can run the highest-value row-crop and organic direct-market workflows end to end using synthetic farm profiles, controlled data inputs, structured multi-agent outputs, human-review policy enforcement, and a simple app interface.

The MVP should demonstrate that HarvestAmp can:

1. Load two farm profiles.
2. Route requests through a Supervisor / Orchestrator.
3. Create task-scoped context packages.
4. Call specialist agents or deterministic services.
5. Produce structured `AgentFinding` outputs.
6. Gather evidence into an Evidence Board.
7. Apply risk and human-review rules.
8. Produce an `ActionPack` for the user.
9. Block unsafe or unauthorized action.
10. Save approved updates into memory / records.
11. Pass scenario and evaluation tests.

The first successful demo should answer:

> Can HarvestAmp create a useful weekly farm action plan and procurement recommendation for two very different farms without leaking data, inventing unsupported claims, or bypassing human review?

---

## 2. Build Principles

### 2.1 Source-of-truth first

The repository documents are the memory of the project. Antigravity conversations are not the source of truth.

Every build task should begin by reading the relevant documents:

```text
01_PRODUCT_BRIEF.md
02_AGENT_ARCHITECTURE.md
03_FARM_PROFILES.md
04_DATA_SOURCES.md
05_AGENT_CONTRACTS.md
06_RISK_AND_HUMAN_REVIEW_POLICY.md
07_SAMPLE_SCENARIOS.md
08_EVALUATION_TESTS.md
09_MVP_SCOPE.md
10_BUILD_PLAN.md
```

If a design decision changes, update the relevant source-of-truth document. Do not leave important decisions only in chat history.

### 2.2 Build a vertical slice before breadth

HarvestAmp should first prove a complete path through the system:

```text
User request
-> Intent Router
-> Supervisor
-> Context Package Builder
-> Specialist agents
-> Evidence Board
-> Recommendation Synthesizer
-> Human-review policy
-> Action Agent gate
-> UI output
-> Memory / record update
-> Evaluation test
```

Do not build all agent features before this vertical path works.

### 2.3 Deterministic services before free-form autonomy

Use deterministic services for:

- Authorization checks.
- Credential handling.
- Tool permissions.
- Unit conversions.
- Price normalization.
- Cost-per-acre math.
- Nutrient-cost math.
- Approval-state checks.
- Audit logging.
- Tenant isolation.
- Schema validation.

Use LLM agents for:

- Reasoning over context.
- Summarizing evidence.
- Generating farmer-friendly recommendations.
- Drafting messages.
- Explaining tradeoffs.
- Handling ambiguous user language.
- Producing structured findings from messy documents or notes.

### 2.4 Agents request capabilities, not credentials

No agent should receive raw credentials. Agents request capabilities through the Tool Gateway. The Credential Broker / Authorization Service decides whether the tool call is allowed.

### 2.5 Human approval before high-impact action

HarvestAmp may analyze, compare, summarize, draft, and recommend. It must not commit, send, purchase, disclose, file, delete, grant access, or execute high-impact external actions without the required approval state.

### 2.6 Evidence before recommendations

Every recommendation should trace back to evidence. Evidence may be synthetic in MVP, but it must still be labeled as synthetic, public, user-entered, uploaded, or derived.

### 2.7 Test every workflow with both success and failure cases

Each major workflow should have:

- A happy-path test.
- A missing-data test.
- A stale-data test.
- A privacy-boundary test.
- A human-review test.
- An unsafe-action test where applicable.

---

## 3. Recommended Technology Shape

This section defines the intended technology shape for the MVP. It does not require every production service to be fully deployed on day one.

### 3.1 Development environment

| Layer | Recommended tool | MVP use |
|---|---|---|
| Agent development | Antigravity | Build tasks, refactors, tests, UI iterations, walkthrough artifacts |
| Agent framework | Google ADK | Define agents, tools, deterministic workflows, graph routing, sequential / parallel / loop patterns |
| Model layer | Gemini / Vertex AI | Agent reasoning, synthesis, extraction, drafting |
| Local / dev runner | Local environment or ADK dev tooling | Fast workflow testing before cloud deployment |
| Test harness | Project tests plus scenario fixtures | Evaluate contracts, routing, schemas, math, privacy, and human review |
| Source control | Git | Version docs, configs, schemas, tests, prompts, and code |

### 3.2 Google Cloud MVP staging

| Stage | Google component | MVP role |
|---|---|---|
| Identity / permissions | IAM, app-level RBAC, later Agent Identity | Role-aware access and tool authorization |
| Secrets | Secret Manager or managed auth pattern | Keep credentials out of prompts and logs |
| Agent deployment | Agent Runtime or equivalent controlled runtime | Later MVP / pilot deployment once local workflows pass |
| Long-term personalization | Sessions / Memory Bank or app database | Persist farm context, preferences, and session state where appropriate |
| Database | Firestore, Cloud SQL, or equivalent | Store farms, users, fields, inventory, quotes, records, recommendations |
| Analytics / reporting | BigQuery optional | Later evaluation, usage, and aggregate analytics |
| Scheduled checks | Cloud Scheduler | Simulated or real monitoring jobs |
| Event bus | Pub/Sub | Trigger workflows from data changes or scheduled jobs |
| Document extraction | Document AI / Vision OCR optional | Extract invoices, quotes, labels, records, and notes |
| Sensitive-data controls | Sensitive Data Protection optional | Classify, redact, mask, and de-identify sensitive data |
| Marketplace prep | Cloud Marketplace AI agent listing process | Post-MVP commercialization planning |

### 3.3 Reference anchors

These official references should be used when implementation begins:

- Google ADK documentation: `https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk`
- ADK workflow documentation: `https://adk.dev/workflows/`
- Agent Runtime documentation: `https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime`
- Memory Bank documentation: `https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank`
- Cloud Scheduler documentation: `https://docs.cloud.google.com/scheduler/docs`
- Pub/Sub documentation: `https://docs.cloud.google.com/pubsub/docs`
- Cloud Marketplace AI agents: `https://docs.cloud.google.com/marketplace/docs/partners/ai-agents`
- Cloud Marketplace AI agent pricing models: `https://docs.cloud.google.com/marketplace/docs/partners/ai-agents/pricing-models`
- Secret Manager documentation: `https://docs.cloud.google.com/secret-manager/docs/overview`
- Sensitive Data Protection documentation: `https://docs.cloud.google.com/sensitive-data-protection/docs`

---

## 4. Build Phases

HarvestAmp should be built in phases. Each phase has a clear exit gate.

### Phase 0: Repository and document baseline

**Goal:** Create a stable project baseline before code generation.

**Inputs:**

- Source-of-truth documents `01` through `10`.
- Synthetic farm profiles.
- Sample scenarios.
- Evaluation plan.

**Tasks:**

1. Create repository structure.
2. Add source-of-truth docs.
3. Add a decision log.
4. Add a changelog.
5. Add a glossary.
6. Add a folder for schemas.
7. Add a folder for scenario fixtures.
8. Add a folder for prompts / agent instructions.
9. Add a folder for evaluation tests.
10. Add a folder for UI mockups or screenshots.

**Suggested structure:**

```text
harvestamp/
  docs/
    01_PRODUCT_BRIEF.md
    02_AGENT_ARCHITECTURE.md
    03_FARM_PROFILES.md
    04_DATA_SOURCES.md
    05_AGENT_CONTRACTS.md
    06_RISK_AND_HUMAN_REVIEW_POLICY.md
    07_SAMPLE_SCENARIOS.md
    08_EVALUATION_TESTS.md
    09_MVP_SCOPE.md
    10_BUILD_PLAN.md
    DECISION_LOG.md
    CHANGELOG.md
  schemas/
    work_item.schema.yaml
    farm_context_package.schema.yaml
    agent_finding.schema.yaml
    human_review.schema.yaml
    action_pack.schema.yaml
    evidence_item.schema.yaml
  fixtures/
    farms/
    weather/
    procurement/
    markets/
    organic/
    documents/
    scenarios/
  agents/
    supervisor/
    intent_router/
    weather_fieldwork/
    procurement/
    records_inventory/
    market_sales/
    compliance/
    margin_scenario/
    recommendation_synthesizer/
    action_agent/
    document_intake/
  tools/
    weather_tool/
    supplier_quotes_tool/
    fuel_tool/
    fertilizer_tool/
    marketdata_tool/
    records_tool/
    auth_tool/
  app/
    ui/
    api/
  tests/
    unit/
    integration/
    evaluation/
    privacy/
    red_team/
```

**Exit gate:**

- All current documents are present.
- Product name is HarvestAmp everywhere.
- No old working name appears in current docs, prompts, or UI labels.
- Repo has a clear folder structure.

---

### Phase 1: Schemas, fixtures, and deterministic core

**Goal:** Build the non-LLM foundation before agent behavior.

**Primary deliverables:**

1. Shared schemas.
2. Synthetic fixture data.
3. Role and permission model.
4. Human-review state model.
5. Deterministic math utilities.
6. Source and evidence model.

**Schemas to create first:**

- `WorkItem`
- `FarmContextPackage`
- `AgentFinding`
- `EvidenceItem`
- `HumanReview`
- `ActionPack`
- `FarmProfile`
- `UserRole`
- `InventoryItem`
- `SupplierQuote`
- `Recommendation`
- `AuditEvent`

**Synthetic fixture data:**

Create fixture files for:

- Prairie View Farms profile.
- Green Basket Organics profile.
- Prairie View weather window.
- Green Basket market-day weather.
- Prairie View fuel quotes.
- Prairie View fertilizer quotes.
- Prairie View inventory.
- Green Basket packaging inventory.
- Green Basket organic input document.
- Sample supplier message draft.
- Sample CSA newsletter draft.
- Sample invoice upload.
- Sample privacy-boundary user roles.

**Deterministic utilities:**

Build deterministic functions for:

- Currency normalization.
- Unit conversion.
- Gallons, tons, pounds, acres, beds, units, packages.
- Fertilizer nutrient conversion.
- Cost per acre.
- Cost per pound of nutrient.
- Tank capacity percentage.
- Days of inventory on hand.
- Data freshness classification.
- Approval-state transition checks.
- Data-sensitivity labeling.

**Exit gate:**

- Schemas validate sample outputs.
- Fixture data loads without errors.
- Deterministic math passes tests.
- Human-review object validates against schema.
- Data sensitivity classes are represented in fixtures.

---

### Phase 2: Authorization, credentials, context, and tool gateway skeleton

**Goal:** Build the safety boundary before connecting agents to data.

**Primary components:**

1. Credential Broker / Authorization Service.
2. Tool Gateway.
3. Context Package Builder.
4. Audit Logger.
5. Policy Engine skeleton.

**MVP behavior:**

The system may use mock credentials and mock users, but the architecture must behave as if sensitive data and credentials exist.

**Required rules:**

1. Agents never receive raw credentials.
2. Agents request tool capabilities.
3. Tool Gateway checks authorization before returning data.
4. Context Package Builder includes only task-scoped data.
5. Role-based access limits are enforced.
6. All sensitive data access creates an audit event.
7. Cross-farm access is denied unless explicitly authorized.
8. External disclosure actions require approval.

**Minimum roles to simulate:**

- Farm owner.
- Farm manager.
- Field employee.
- Advisor / consultant.
- Account admin.

**Exit gate:**

- Field employee cannot access supplier quotes or margins.
- Advisor cannot access farms not assigned to them.
- No agent context contains raw credentials.
- Cross-farm data request is blocked.
- Tool call without authorization is denied.
- Audit log records sensitive access.

---

### Phase 3: Supervisor skeleton and mock specialist agents

**Goal:** Prove routing and orchestration before individual agents are complete.

**Primary components:**

1. Intent Router.
2. Supervisor / Orchestrator.
3. Mock Weather Agent.
4. Mock Procurement Agent.
5. Mock Records Agent.
6. Mock Market Agent.
7. Mock Compliance Agent.
8. Mock Margin Agent.
9. Mock Recommendation Synthesizer.
10. Mock Action Agent gate.

**MVP routes to support first:**

| User request | Required route |
|---|---|
| "What should I know this week?" | Weather, procurement, records, market, compliance, margin, synthesizer |
| "Should I buy diesel this month?" | Procurement, weather, records, market, margin, synthesizer |
| "Compare these fertilizer quotes." | Document intake, procurement, records, compliance, margin, synthesizer |
| "Can I spray tomorrow?" | Weather, crop-risk optional, compliance, records, synthesizer |
| "What should I bring to market Saturday?" | Weather, records, procurement, market/sales, synthesizer |
| "Can I use this organic input?" | Document intake, compliance, records, synthesizer, expert review gate |

**Orchestration patterns:**

Use simple patterns at first:

- Sequential: document upload -> extraction -> normalization -> analysis -> synthesis.
- Parallel: weekly plan -> weather, procurement, market, compliance, records -> evidence board -> synthesis.
- Loop: draft recommendation -> risk check -> revise if overconfident or missing review flag.

**Exit gate:**

- Supervisor routes all Tier 1 MVP scenarios correctly.
- Mock agents return valid `AgentFinding` objects.
- Synthesizer creates a valid `ActionPack`.
- Risk policy attaches `human_review` when required.
- Action Agent refuses to execute gated actions without approval.

---

### Phase 4: Build the first real vertical workflow

**Goal:** Build the flagship weekly planning workflow end to end.

**Workflow:**

```text
User: What should I know this week?
```

**Farm profiles:**

- Prairie View Farms.
- Green Basket Organics.

**Required behavior for Prairie View Farms:**

HarvestAmp should consider:

- Weather and fieldwork window.
- Fuel inventory and price watch.
- Fertilizer or seed watchlist.
- Crop / scouting watchlist, if present in fixture data.
- Grain market context.
- Compliance / deadlines watchlist.
- Records or inventory gaps.
- Human-review flags for high-impact actions.

**Required behavior for Green Basket Organics:**

HarvestAmp should consider:

- Market-day weather.
- CSA and farmers market planning.
- Packaging inventory.
- Organic input / documentation watchlist.
- Harvest tasks.
- Customer-facing draft guardrails.
- Human-review flags for external messages.

**Expected output:**

A weekly `ActionPack` with sections:

- Summary.
- Today.
- This week.
- Watchlist.
- Procurement / inventory.
- Market / sales.
- Compliance / records.
- Human review required.
- Missing data.
- Evidence.
- Proposed actions.

**Exit gate:**

- Weekly plan works for both farms.
- Output is farm-specific, not generic.
- Evidence is labeled.
- Human-review flags are present where needed.
- Field employee role sees a restricted version.
- Tests pass for the weekly plan scenarios.

---

### Phase 5: Procurement workflows

**Goal:** Build the highest-value procurement workflows.

**Workflow 1:** Fuel buy-window advisor.  
**Workflow 2:** Fertilizer quote comparison.  
**Workflow 3:** Packaging reorder advisor for direct-market farm.

### 5.1 Fuel buy-window advisor

**Inputs:**

- Fuel quote.
- Historical fuel quote.
- Tank level.
- Tank capacity.
- Upcoming weather / fieldwork window.
- Expected fuel demand.
- Delivery lead time.
- Risk tolerance.

**Output:**

- Buy now / wait / split recommendation.
- Confidence.
- Missing data.
- Scenario assumptions.
- Human-review requirement before supplier message or purchase.

**Must not:**

- Predict exact future fuel price with certainty.
- Commit to fuel purchase.
- Send supplier message without approval.
- Reveal competing supplier quote unless approved.

### 5.2 Fertilizer quote comparison

**Inputs:**

- Uploaded quote or manual quote.
- Product type.
- Unit price.
- Delivery / application fees where available.
- Nutrient content.
- Acres.
- Crop plan.
- Soil-test target if available.
- Organic status if relevant.

**Output:**

- Normalized quote table.
- Cost per unit.
- Cost per pound of nutrient.
- Estimated cost per acre.
- Missing data.
- Human-review flags.

**Must not:**

- Recommend agronomic application rates unless explicitly scoped and reviewed.
- Make environmental compliance determinations.
- Certify organic acceptability.

### 5.3 Packaging reorder advisor

**Inputs:**

- Current packaging inventory.
- CSA count.
- Farmers market plan.
- Restaurant orders.
- Past usage.
- Delivery lead time.

**Output:**

- Items likely short.
- Suggested reorder timing.
- Draft purchase list.
- Human approval required before order or vendor message.

**Exit gate:**

- Three procurement workflows pass scenario tests.
- Human-review policy is correctly applied.
- Deterministic math passes tests.
- Sensitive supplier data is not leaked.

---

### Phase 6: Document and media intake MVP

**Goal:** Support uploads without overbuilding document intelligence.

**In scope:**

- Fuel invoice extraction.
- Fertilizer quote extraction.
- Packaging invoice extraction.
- Organic input document summary.
- Field note / voice note text ingestion if available as text.

**Out of scope for MVP:**

- Full OCR reliability guarantee.
- All invoice formats.
- Automatic document filing to government or certifier.
- Complex contract interpretation.
- Pesticide-label interpretation beyond high-level warning and review trigger.

**Required extraction fields:**

For supplier quotes:

```text
supplier_name
input_category
product_name
unit
quantity
unit_price
delivery_fee
application_fee
quote_date
expiration_date
payment_terms
source_document_id
confidence
missing_fields
```

For invoices:

```text
supplier_name
invoice_date
items
quantities
unit_prices
total
farm_or_field_reference
inventory_update_candidate
source_document_id
confidence
missing_fields
```

**Exit gate:**

- Upload flow extracts useful fields from MVP sample documents.
- Low-confidence extractions require user confirmation.
- Sensitive document data is labeled.
- Inventory update requires approval before official record changes.

---

### Phase 7: Human-review and Action Agent implementation

**Goal:** Make approvals visible and enforceable.

**Approval states:**

```text
draft
needs_user_approval
needs_expert_review
needs_admin_review
approved
edited_by_user
rejected
blocked
executed
logged
```

**Action Agent can prepare:**

- Draft supplier message.
- Draft restaurant availability message.
- Draft CSA newsletter.
- Draft task list.
- Draft purchase list.
- Draft calendar reminder.
- Draft inventory update.
- Draft advisor report.

**Action Agent cannot execute without approval:**

- Send external message.
- Contact supplier.
- Create purchase order.
- Update official farm record.
- Share report externally.
- Export sensitive data.
- Change permissions.
- Delete records.

**Exit gate:**

- Gated actions cannot execute while in `draft` or `needs_*_review` status.
- Approval changes are logged.
- Rejected actions do not execute.
- User edits are preserved.
- External disclosure preview shows sensitive fields before send.

---

### Phase 8: UI prototype

**Goal:** Create a simple app experience that demonstrates the agent workflows.

**Required surfaces:**

1. Farm selector.
2. Role selector or login simulation.
3. Chat / prompt input.
4. Weekly action plan view.
5. Recommendation cards.
6. Evidence panel.
7. Human-review status panel.
8. Upload / manual-entry form.
9. Draft action preview.
10. Task / alert list.

**Recommendation card fields:**

```text
title
summary
farm
workflow
urgency
confidence
recommendation_type
evidence_count
missing_data
human_review_status
proposed_actions
approve / edit / reject controls
```

**UI principles:**

- Show source and confidence.
- Show missing data.
- Show what requires approval.
- Show what will be shared externally before sending.
- Make role restrictions visible.
- Avoid presenting high-risk content as final instruction.

**Exit gate:**

- User can run the primary scenarios from UI.
- User can see why a recommendation was made.
- User can approve, edit, or reject a draft action.
- Restricted role cannot see sensitive fields.
- Demo flow is understandable without reading the code.

---

### Phase 9: Monitoring-loop simulation

**Goal:** Simulate the future background-monitoring architecture without full production integrations.

**MVP monitoring loops:**

1. Fuel price watch.
2. Weather window watch.
3. Packaging inventory watch.
4. Compliance / deadline watch.
5. Stale data watch.

**Implementation approach:**

Use scheduled or manually triggered mock jobs that load fixture updates and publish a workflow trigger.

Example:

```text
mock_scheduler_trigger
-> load new fuel quote fixture
-> detect threshold change
-> create WorkItem
-> Supervisor routes to Procurement Agent
-> Recommendation Synthesizer creates alert
-> Action Agent gates external action
```

**Exit gate:**

- At least two monitoring loops can trigger an alert.
- Alerts are deduplicated or marked as repeated.
- Low-importance changes do not spam the user.
- Human-review policy still applies to triggered recommendations.

---

### Phase 10: Evaluation, red-team, and readiness gate

**Goal:** Validate that HarvestAmp is useful, safe, and stable enough for a private demo or pilot planning.

**Evaluation sources:**

- `07_SAMPLE_SCENARIOS.md`.
- `08_EVALUATION_TESTS.md`.
- Synthetic farm fixtures.
- Unit tests.
- Integration tests.
- UI walkthroughs.
- Red-team prompts.

**Required evaluation suites:**

1. Brand consistency.
2. Schema validation.
3. Supervisor routing.
4. Agent output contracts.
5. Human-review triggers.
6. Action Agent gating.
7. Authorization and privacy.
8. Cross-farm leakage prevention.
9. Deterministic math.
10. Evidence and freshness.
11. Role-based UI behavior.
12. Disclosure previews.
13. Unsupported high-risk request handling.
14. Regression tests.

**Critical fail conditions:**

HarvestAmp must not be considered demo-ready if it:

1. Leaks one farm's private data to another farm.
2. Exposes raw credentials to an LLM context.
3. Sends external messages without approval.
4. Creates purchase orders without approval.
5. Gives definitive pesticide-rate, veterinary, legal, tax, crop-insurance, or regulated financial advice.
6. Treats stale, synthetic, or missing data as current and certain.
7. Bypasses human review for high-impact actions.
8. Produces recommendations without evidence or assumptions.
9. Uses the prior working product name in user-facing output.
10. Fails deterministic math for cost, inventory, or unit conversion.

**Exit gate:**

- All Tier 1 MVP scenarios pass.
- Critical fail tests pass.
- Demo workflow runs end to end.
- Known limitations are documented.
- Next-phase backlog is written.

---

## 5. Recommended Antigravity Task Sequence

Use many small Antigravity tasks rather than one long conversation.

Each task should have:

- A narrow goal.
- Source documents to read first.
- Files it may edit.
- Files it must not edit.
- Acceptance tests.
- Required artifacts.
- A handoff summary.

### Task 1: Initialize repository and docs

**Goal:** Create the project repository structure and place source-of-truth docs.

**Read first:**

- `01_PRODUCT_BRIEF.md`
- `09_MVP_SCOPE.md`
- `10_BUILD_PLAN.md`

**Deliverables:**

- Folder structure.
- Docs copied into `docs/`.
- `DECISION_LOG.md`.
- `CHANGELOG.md`.
- Basic README.

**Acceptance:**

- Project name is HarvestAmp.
- No old working name remains.
- Source docs are easy to find.

### Task 2: Create schemas and fixtures

**Goal:** Define the shared objects and synthetic data.

**Read first:**

- `03_FARM_PROFILES.md`
- `05_AGENT_CONTRACTS.md`
- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`
- `07_SAMPLE_SCENARIOS.md`

**Deliverables:**

- Schema files.
- Synthetic farm fixtures.
- Sample quotes, invoices, weather, inventory, and market context.
- Schema validation tests.

**Acceptance:**

- All fixtures validate.
- Human-review object validates.
- AgentFinding and ActionPack examples validate.

### Task 3: Build authorization and context skeleton

**Goal:** Implement the Credential Broker / Authorization Service skeleton, Tool Gateway, and Context Package Builder.

**Read first:**

- `02_AGENT_ARCHITECTURE.md`
- `05_AGENT_CONTRACTS.md`
- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

**Deliverables:**

- Mock user roles.
- Permission checks.
- Tool-call authorization checks.
- Task-scoped context builder.
- Audit event output.

**Acceptance:**

- Field employee cannot access restricted financial or supplier data.
- Cross-farm access is denied.
- Agents do not receive credentials.
- Audit events are produced.

### Task 4: Build supervisor skeleton and mock agents

**Goal:** Build routing and orchestration before real specialist agent behavior.

**Read first:**

- `02_AGENT_ARCHITECTURE.md`
- `05_AGENT_CONTRACTS.md`
- `07_SAMPLE_SCENARIOS.md`

**Deliverables:**

- Intent Router.
- Supervisor routing logic.
- Mock specialist agents.
- Evidence Board.
- Mock Recommendation Synthesizer.

**Acceptance:**

- Tier 1 scenarios route correctly.
- All mock agents return valid AgentFinding structures.
- Weekly plan workflow creates a valid ActionPack.

### Task 5: Build Weather + Fieldwork Agent

**Goal:** Implement weather-to-action reasoning over fixture weather data.

**Read first:**

- `04_DATA_SOURCES.md`
- `05_AGENT_CONTRACTS.md`
- `07_SAMPLE_SCENARIOS.md`

**Deliverables:**

- Weather agent instructions.
- Weather fixture parser.
- Weather findings.
- Spray-window guardrail behavior.
- Market-day weather findings.

**Acceptance:**

- Agent considers wind, rain, heat, frost, fieldwork relevance, and forecast confidence.
- Agent does not make pesticide product/rate recommendations.
- Agent triggers human review where required.

### Task 6: Build Procurement Agent and deterministic math

**Goal:** Implement fuel, fertilizer, and packaging procurement workflows.

**Read first:**

- `04_DATA_SOURCES.md`
- `05_AGENT_CONTRACTS.md`
- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`
- `07_SAMPLE_SCENARIOS.md`

**Deliverables:**

- Fuel buy-window workflow.
- Fertilizer quote normalization.
- Packaging reorder workflow.
- Math tests.
- Human-review triggers.

**Acceptance:**

- Cost-per-acre and cost-per-nutrient math passes.
- Fuel recommendation uses inventory and fieldwork context.
- Purchase recommendations require approval.

### Task 7: Build Records + Inventory Agent

**Goal:** Implement inventory and record update logic.

**Read first:**

- `03_FARM_PROFILES.md`
- `05_AGENT_CONTRACTS.md`
- `07_SAMPLE_SCENARIOS.md`

**Deliverables:**

- Inventory summaries.
- Candidate updates from invoice / upload.
- Approval gate for official record changes.
- Role-aware record visibility.

**Acceptance:**

- Inventory updates are draft until approved.
- Sensitive inventory is hidden from restricted roles.
- Audit events are generated.

### Task 8: Build Compliance Agent

**Goal:** Implement limited MVP compliance guardrails.

**Read first:**

- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`
- `04_DATA_SOURCES.md`
- `07_SAMPLE_SCENARIOS.md`

**Deliverables:**

- Organic input review trigger.
- Pesticide/spray guardrail trigger.
- USDA / deadline reminder placeholder.
- External disclosure review trigger.

**Acceptance:**

- Agent does not make final organic certification rulings.
- Agent does not provide definitive pesticide application instruction.
- Expert review is triggered for organic and pesticide-sensitive scenarios.

### Task 9: Build Market + Sales Agent

**Goal:** Implement limited commodity and direct-market context.

**Read first:**

- `03_FARM_PROFILES.md`
- `04_DATA_SOURCES.md`
- `07_SAMPLE_SCENARIOS.md`

**Deliverables:**

- Stored grain sale scenario framing.
- Direct-market pack list and availability context.
- CSA box / restaurant draft context.
- Human-review trigger for external messages or financial decisions.

**Acceptance:**

- Agent frames scenarios without telling user to trade or sell definitively.
- External customer or restaurant messages require approval.
- Evidence and assumptions are included.

### Task 10: Build Recommendation Synthesizer

**Goal:** Convert findings into useful farmer-facing action packs.

**Read first:**

- `05_AGENT_CONTRACTS.md`
- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`
- `07_SAMPLE_SCENARIOS.md`
- `08_EVALUATION_TESTS.md`

**Deliverables:**

- Weekly action plan synthesis.
- Recommendation cards.
- Missing-data summary.
- Human-review summary.
- Evidence summary.

**Acceptance:**

- Output is specific to farm type.
- Output is concise enough for user interface.
- High-risk recommendations are not overconfident.
- Sensitive fields are not shown to unauthorized roles.

### Task 11: Build Action Agent and approval gates

**Goal:** Create draft actions and enforce approval before execution.

**Read first:**

- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`
- `05_AGENT_CONTRACTS.md`
- `08_EVALUATION_TESTS.md`

**Deliverables:**

- Draft task creation.
- Draft supplier message.
- Draft restaurant availability message.
- Draft CSA newsletter.
- Approval state transitions.
- External disclosure preview.

**Acceptance:**

- Action cannot execute without required approval.
- Rejected action does not execute.
- Edited action preserves audit trail.
- Sensitive disclosure preview appears before send.

### Task 12: Build basic UI prototype

**Goal:** Build the user-facing demo surface.

**Read first:**

- `09_MVP_SCOPE.md`
- `07_SAMPLE_SCENARIOS.md`
- `08_EVALUATION_TESTS.md`

**Deliverables:**

- Farm selector.
- Role selector or mock login.
- Chat input.
- Weekly plan view.
- Recommendation cards.
- Evidence panel.
- Approval controls.
- Upload/manual entry form.

**Acceptance:**

- User can run primary scenarios from UI.
- User can inspect evidence.
- User can approve, edit, or reject actions.
- Role restrictions are visible.

### Task 13: Build monitoring-loop simulation

**Goal:** Simulate background watching for MVP.

**Read first:**

- `02_AGENT_ARCHITECTURE.md`
- `04_DATA_SOURCES.md`
- `09_MVP_SCOPE.md`

**Deliverables:**

- Mock fuel price watch.
- Mock weather watch.
- Mock packaging inventory watch.
- Triggered alerts.
- Deduplication or alert-state handling.

**Acceptance:**

- Monitoring event can trigger a supervisor workflow.
- Alert includes evidence and review state.
- Low-importance changes do not spam.

### Task 14: Build evaluation harness and red-team tests

**Goal:** Make the MVP measurable.

**Read first:**

- `08_EVALUATION_TESTS.md`
- `07_SAMPLE_SCENARIOS.md`
- `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

**Deliverables:**

- Automated evaluation runner.
- Scenario test cases.
- Critical fail tests.
- Red-team prompt set.
- Regression suite.
- Demo readiness report.

**Acceptance:**

- Tier 1 scenarios pass.
- Critical fail tests pass.
- Known limitations report is generated.

### Task 15: Demo packaging and pilot backlog

**Goal:** Prepare the MVP for demo and next-phase planning.

**Read first:**

- `09_MVP_SCOPE.md`
- `10_BUILD_PLAN.md`
- `08_EVALUATION_TESTS.md`

**Deliverables:**

- Demo script.
- Walkthrough screenshots or recordings.
- Known limitations.
- Pilot backlog.
- Data-source backlog.
- Marketplace-readiness checklist.

**Acceptance:**

- Demo can be run consistently.
- Pilot questions are documented.
- Post-MVP roadmap is prioritized.

---

## 6. Recommended First Vertical Slice

The first vertical slice should be:

> Weekly Farm Action Plan for both MVP farm profiles.

This is the best first slice because it exercises almost every major part of the system without requiring real integrations or complex document parsing.

### 6.1 Prairie View Farms weekly plan

**User prompt:**

```text
What should I know about Prairie View Farms this week?
```

**Expected route:**

```text
Intent Router
-> Supervisor
-> Context Package Builder
-> Weather + Fieldwork Agent
-> Input Procurement Agent
-> Records + Inventory Agent
-> Market + Sales Agent
-> Compliance Agent
-> Margin + Scenario Agent
-> Recommendation Synthesizer
-> Risk Classifier
-> Action Agent gate
```

**Expected output:**

- Fieldwork weather window.
- Fuel watch item.
- Fertilizer or seed watch item.
- Market context.
- Compliance reminder or no known deadline.
- Missing data.
- Human-review required for purchase or supplier message.
- Draft tasks.

### 6.2 Green Basket Organics weekly plan

**User prompt:**

```text
What should Green Basket Organics prepare for this week?
```

**Expected route:**

```text
Intent Router
-> Supervisor
-> Context Package Builder
-> Weather + Fieldwork Agent
-> Input Procurement Agent
-> Records + Inventory Agent
-> Market + Sales Agent
-> Compliance Agent
-> Recommendation Synthesizer
-> Action Agent gate
```

**Expected output:**

- Market-day weather note.
- Harvest / pack priorities.
- Packaging inventory watch.
- CSA / restaurant draft note.
- Organic record or input reminder.
- Human-review required before external customer or restaurant messages.
- Draft tasks.

### 6.3 Why this comes first

This workflow proves:

1. Multi-agent routing.
2. Farm-type adaptation.
3. Context minimization.
4. Procurement logic.
5. Market/sales differences.
6. Compliance guardrails.
7. Human-review policy.
8. Role-aware output.
9. Evidence labeling.
10. UI action plan display.

---

## 7. MVP Dependency Order

The build should follow this dependency order:

```text
Docs
-> schemas
-> fixtures
-> auth/context/tool gateway
-> supervisor skeleton
-> mock agents
-> first vertical workflow
-> real specialist agents
-> synthesizer
-> action gates
-> UI
-> monitoring simulation
-> evaluation harness
-> demo packaging
```

Do not reverse this order by building the UI or real data integrations too early.

---

## 8. What Not to Build Yet

The MVP should not spend time on:

1. Real paid data feeds.
2. Real supplier portal integrations.
3. Automatic purchases.
4. Commodity trade execution.
5. Pesticide-label interpretation engine.
6. Definitive crop disease diagnosis.
7. Veterinary decision support.
8. Full government form filing.
9. Bank integrations.
10. Drone imagery.
11. Equipment telematics.
12. Full mobile offline mode.
13. White-label co-op portal.
14. Multi-region farm coverage.
15. Full marketplace submission package.
16. Custom model fine-tuning.
17. Production billing.
18. Real customer data ingestion.

These features can be documented in the backlog, but they should not block the MVP.

---

## 9. Data Integration Ladder

HarvestAmp should add data integrations in levels.

### Level 0: Synthetic data

Use fixture data only.

**Use for:**

- Agent routing.
- Schema validation.
- UI testing.
- Human-review policy.
- Evaluation tests.

### Level 1: Manual entry and uploads

Allow the user to enter or upload:

- Fuel quote.
- Fertilizer quote.
- Seed quote.
- Packaging inventory.
- Invoice.
- Farm note.
- Organic input document.

**Use for:**

- Realistic procurement workflows without supplier integrations.

### Level 2: Public official APIs

Add public official sources such as weather, public market data, fuel benchmarks, and agricultural reports where licensing permits.

**Use for:**

- Weather context.
- Benchmark context.
- Market context.
- Deadline / compliance context.

### Level 3: Licensed commercial data

Add commercial data only after MVP workflows prove value.

Potential categories:

- Cash grain bids.
- Basis.
- Fertilizer market intelligence.
- Fuel and energy forecasts.
- Organic / non-GMO market data.
- Producer-facing market news.

### Level 4: Supplier and farm-system integrations

Add integrations only after security, permissioning, and human-review workflows are stable.

Potential integrations:

- Co-op supplier quotes.
- Fuel distributor quote feed.
- Seed dealer data.
- Farm management software.
- POS / CSA systems.
- Tank monitors.
- Equipment telemetry.

---

## 10. Build Gates

HarvestAmp should use formal gates.

### Gate A: Architecture gate

Pass criteria:

- Docs `01` through `10` exist.
- Product name is HarvestAmp.
- MVP scope is clear.
- Human-review policy exists.
- Agent contracts exist.

### Gate B: Schema and fixture gate

Pass criteria:

- Core schemas validate.
- Fixtures for both farms validate.
- Human-review object validates.
- AgentFinding examples validate.

### Gate C: Safety boundary gate

Pass criteria:

- Credential Broker / Authorization Service skeleton exists.
- Tool Gateway exists.
- Context Package Builder enforces task-scoped context.
- Cross-farm leakage tests pass.
- Role-based restriction tests pass.

### Gate D: Routing gate

Pass criteria:

- Intent Router works for MVP prompts.
- Supervisor routes scenarios to correct agents.
- Mock agents return structured findings.

### Gate E: First vertical slice gate

Pass criteria:

- Weekly plan works for Prairie View Farms.
- Weekly plan works for Green Basket Organics.
- Output includes evidence, missing data, confidence, and review flags.

### Gate F: Procurement gate

Pass criteria:

- Fuel buy-window workflow works.
- Fertilizer quote comparison works.
- Packaging reorder workflow works.
- Financial actions require approval.

### Gate G: UI gate

Pass criteria:

- User can run primary workflows from UI.
- User can inspect evidence.
- User can approve, edit, reject draft actions.
- Restricted roles cannot see restricted data.

### Gate H: Evaluation gate

Pass criteria:

- Tier 1 scenarios pass.
- Critical fail tests pass.
- Red-team tests pass.
- Demo readiness report exists.

### Gate I: Demo gate

Pass criteria:

- Demo script works.
- Known limitations are documented.
- Pilot backlog is prepared.
- No critical safety, privacy, or human-review gaps remain.

---

## 11. MVP Demo Script

The first demo should be short and focused.

### Demo 1: Row-crop weekly plan

1. Select Prairie View Farms.
2. User role: Farm owner.
3. Ask: "What should I know this week?"
4. Show weekly plan.
5. Open fuel recommendation.
6. Show evidence and missing data.
7. Show human-review status.
8. Draft supplier message.
9. Show approval gate before send.

### Demo 2: Fertilizer quote comparison

1. Upload sample fertilizer quotes.
2. HarvestAmp extracts quote details.
3. HarvestAmp normalizes cost.
4. HarvestAmp compares cost per nutrient and cost per acre.
5. Show missing delivery/application fee if absent.
6. Show human-review trigger before purchase.

### Demo 3: Spray-window guardrail

1. Ask: "Can I spray tomorrow?"
2. HarvestAmp checks weather window.
3. HarvestAmp refuses to recommend product/rate.
4. HarvestAmp requires label/advisor review.

### Demo 4: Organic direct-market weekly plan

1. Select Green Basket Organics.
2. Ask: "What should we prepare for market and CSA this week?"
3. Show market-day weather.
4. Show harvest / packaging priorities.
5. Draft CSA newsletter or restaurant availability.
6. Show external disclosure approval before send.

### Demo 5: Privacy boundary

1. Switch role to field employee.
2. Ask for supplier quote or margin details.
3. HarvestAmp blocks sensitive details.
4. Show allowed operational task view only.

---

## 12. Antigravity Prompt Template

Use this prompt style for each task.

```text
You are working on HarvestAmp, a multi-agent farming operations and input-margin advisor.

Before making changes, read:
- docs/01_PRODUCT_BRIEF.md
- docs/02_AGENT_ARCHITECTURE.md
- docs/03_FARM_PROFILES.md
- docs/04_DATA_SOURCES.md
- docs/05_AGENT_CONTRACTS.md
- docs/06_RISK_AND_HUMAN_REVIEW_POLICY.md
- docs/07_SAMPLE_SCENARIOS.md
- docs/08_EVALUATION_TESTS.md
- docs/09_MVP_SCOPE.md
- docs/10_BUILD_PLAN.md

Task goal:
[insert narrow task]

Allowed files to edit:
[insert files/folders]

Do not edit:
[insert protected files]

Acceptance criteria:
[insert tests or expected behavior]

Important constraints:
- Use the product name HarvestAmp only.
- Do not use any previous working product name.
- Agents must not receive raw credentials.
- Agents must use task-scoped context.
- External actions require approval when human_review requires it.
- Farm data must not leak across farms, users, or tenants.
- High-risk agricultural, financial, legal, insurance, pesticide, organic, or veterinary outputs require review or refusal.
- Use synthetic data only unless explicitly authorized.

Deliverables:
- Implement the task.
- Add or update tests.
- Provide a concise handoff summary.
- Note any assumptions or open questions in docs/DECISION_LOG.md.
```

---

## 13. Handoff Summary Template

Each Antigravity task should end with a handoff summary.

```text
Task completed:

Files changed:

What was built:

How to run or verify:

Tests added or updated:

Scenarios covered:

Known limitations:

Open questions:

Next recommended task:
```

This prevents future tasks from depending on chat memory.

---

## 14. Decision Log Requirements

Create and maintain `DECISION_LOG.md`.

Log decisions such as:

- Why HarvestAmp uses task-scoped context.
- Why supplier quotes override generic benchmarks for farm-specific procurement decisions.
- Which data sources are MVP versus post-MVP.
- Which human-review triggers are enforced in MVP.
- Which Google services are mocked versus real.
- Which workflows are deferred.
- Which role permissions exist in MVP.
- Which schema changes affect agent contracts.

Suggested format:

```md
## Decision YYYY-MM-DD: [Title]

**Decision:**

**Reason:**

**Alternatives considered:**

**Impact:**

**Related docs:**
```

---

## 15. Backlog Structure

Maintain a backlog grouped by category.

### MVP must-have

Items required for first demo.

### MVP should-have

Items useful but not demo-blocking.

### Post-MVP pilot

Items likely needed for a real pilot.

### Marketplace readiness

Items needed for Google Cloud Marketplace listing and commercial packaging.

### Enterprise readiness

Items needed for co-ops, advisors, ag retailers, and large farm organizations.

### Research / uncertain

Items requiring validation, vendor discussions, licensing, or domain expert review.

---

## 16. Marketplace Readiness Later

The MVP is not the marketplace submission. Marketplace readiness should be a later workstream.

Marketplace readiness will likely require:

1. Clear product listing copy.
2. Pricing model decision.
3. Deployment model decision.
4. Security and privacy documentation.
5. Data governance documentation.
6. Vendor setup.
7. Support model.
8. Terms of service.
9. Acceptable use policy.
10. Product screenshots or demo materials.
11. Integration documentation.
12. Evaluation / safety documentation.
13. Customer onboarding workflow.
14. Billing and usage reporting if usage-based pricing is used.

Do not let marketplace packaging block the MVP build. Build the product evidence first.

---

## 17. Pilot Readiness Later

Before any real pilot with a farmer, co-op, or advisor, HarvestAmp should have:

1. Clear consent language.
2. Data-use policy.
3. Data deletion and export policy.
4. User roles and permissions.
5. Credential revocation.
6. Audit logs.
7. Human-review gates.
8. Known limitations.
9. Support contact.
10. Domain expert review of sensitive workflows.
11. No use of real farm data in tests or demos without explicit authorization.

---

## 18. Domain Expert Review Plan

HarvestAmp should eventually involve human domain experts.

Recommended reviewers:

| Domain | Reviewer type |
|---|---|
| Row-crop operations | Farmer, crop consultant, agronomist |
| Fertilizer economics | Agronomist, ag retailer, farm economist |
| Fuel procurement | Farm manager, fuel distributor, co-op purchasing lead |
| Grain marketing | Grain marketer, farm economist, elevator professional |
| Organic compliance | Organic certifier or certification specialist |
| Direct-market farming | CSA/farmers market operator |
| Food safety | Produce safety specialist |
| Pesticide guardrails | Licensed applicator, extension specialist, crop advisor |
| Privacy/security | Cloud security reviewer, privacy counsel |

Domain review should focus on whether HarvestAmp is useful, appropriately cautious, and transparent about evidence and limitations.

---

## 19. MVP Acceptance Criteria

HarvestAmp MVP is acceptable when:

1. Two farm profiles are implemented.
2. Tier 1 scenarios pass.
3. Weekly action plans work for both farms.
4. Fuel buy-window workflow works.
5. Fertilizer quote comparison works.
6. Packaging reorder workflow works.
7. Organic input review workflow triggers expert review.
8. Spray-window workflow avoids unsafe pesticide guidance.
9. Action Agent blocks unapproved external action.
10. Role-based privacy boundary works.
11. Cross-farm leakage tests pass.
12. Deterministic math tests pass.
13. Recommendations include evidence, assumptions, confidence, and missing data.
14. UI demonstrates the primary workflows.
15. Known limitations are documented.
16. No prior working product name appears in user-facing output.

---

## 20. Final Cut Line for MVP

The MVP should stop at:

> A controlled, evaluated, synthetic-data HarvestAmp prototype that demonstrates farm-specific weekly planning, procurement recommendations, document/manual input handling, human-review gates, privacy controls, and simple UI workflows for Prairie View Farms and Green Basket Organics.

Anything beyond that belongs in post-MVP unless it is required to make the above demo credible.

---

## 21. Next Documents or Artifacts

After this build plan, the likely next artifacts are:

1. `DECISION_LOG.md`
2. `CHANGELOG.md`
3. `11_REPOSITORY_STRUCTURE.md` or implementation README
4. `schemas/*.schema.yaml`
5. `fixtures/*.json` or fixture YAML files
6. `configs/human_review_rules.yaml`
7. `prompts/agent_instructions/*.md`
8. `demo/DEMO_SCRIPT.md`
9. `marketplace/MARKETPLACE_READINESS.md`

The next practical step is to initialize the repository structure and convert the shared structures from the planning docs into schemas and fixture files.
