# DECISION_LOG.md
# Decision Log: HarvestAmp

Version: 0.1  
Date: 2026-06-23  
Status: Active source-of-truth support document  
Owner: Product owner / HarvestAmp project lead  
Related documents:

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

---

## 1. Purpose

This document records the major product, architecture, data, privacy, risk, MVP, and build decisions for HarvestAmp.

HarvestAmp will be developed across multiple Antigravity tasks and likely many separate conversations. This file exists to prevent context drift. Future agents, developers, and reviewers should treat this document as the durable record of what has already been decided, why it was decided, and what should not be re-litigated without an explicit new decision.

The decision log should be updated whenever the project makes a meaningful choice about:

- product positioning,
- MVP scope,
- farm types,
- agent architecture,
- data sources,
- privacy and authorization,
- human review,
- build order,
- Google technology usage,
- marketplace packaging,
- or post-MVP roadmap direction.

---

## 2. Decision Status Values

Use these status values consistently.

| Status | Meaning |
|---|---|
| `accepted` | Current active decision. Build work should follow it. |
| `superseded` | Replaced by a later decision. Keep for history, but do not follow. |
| `proposed` | Under consideration, not yet binding. |
| `deferred` | Important, but not needed for current MVP. |
| `rejected` | Considered and intentionally not adopted. |

---

## 3. Decision Record Template

Use this format for new decisions.

```md
## D-000: Decision title

Status: accepted | superseded | proposed | deferred | rejected  
Date: YYYY-MM-DD  
Owner: Product owner / architecture owner / security owner / other  
Related docs: `file.md`, `file.md`

### Context

What problem, ambiguity, or tradeoff led to the decision?

### Decision

What was decided?

### Rationale

Why this direction?

### Consequences

What this means for design, implementation, testing, or scope.

### Follow-up

Any future work, validations, or open questions.
```

---

## 4. Active Decision Index

| ID | Decision | Status |
|---|---|---|
| D-001 | Product name is HarvestAmp | accepted |
| D-002 | Use source-of-truth Markdown documents | accepted |
| D-003 | MVP focuses on two farm profiles | accepted |
| D-004 | Position HarvestAmp as an operations and input-margin agent | accepted |
| D-005 | Design for B2B/B2B2C marketplace buyers first | accepted |
| D-006 | Use a multi-agent hub-and-spoke architecture | accepted |
| D-007 | Use Google AI products as the target build direction | accepted |
| D-008 | Use Antigravity for focused build tasks, not project memory | accepted |
| D-009 | Build a supervisor skeleton early | accepted |
| D-010 | Data first, agent second | accepted |
| D-011 | Do not rely on ambient open-web monitoring | accepted |
| D-012 | Use task-scoped context for LLM agents | accepted |
| D-013 | Raw credentials must never enter LLM context | accepted |
| D-014 | Use Credential Broker / Authorization Service and Tool Gateway | accepted |
| D-015 | Treat farm data as private commercial data | accepted |
| D-016 | Enforce no cross-farm or cross-tenant leakage | accepted |
| D-017 | Use human-in-the-loop review for high-risk decisions | accepted |
| D-018 | Action Agent must not execute high-impact actions without approval | accepted |
| D-019 | Evidence is required for recommendations | accepted |
| D-020 | Use deterministic software for math, permissions, schedules, and rules | accepted |
| D-021 | Build with synthetic/mock data first | accepted |
| D-022 | MVP must include weekly action plans for both demo farms | accepted |
| D-023 | MVP must include procurement workflows | accepted |
| D-024 | MVP must include privacy and authorization simulations | accepted |
| D-025 | Forecasts are scenario inputs, not deterministic predictions | accepted |
| D-026 | Commercial market data is post-MVP or optional until value is proven | accepted |
| D-027 | Keep pesticide, organic, livestock-health, insurance, legal, and financial advice guarded | accepted |
| D-028 | Create evaluation tests before broad feature expansion | accepted |
| D-029 | Build one vertical slice before broad coverage | accepted |
| D-030 | Avoid over-agentizing the system | accepted |
| D-031 | Modular package layout and mock runner setup | accepted |
| D-032 | Recognize irrigation scheduling and water-request workflows as a HarvestAmp domain | accepted |
| D-033 | Establish MCP Connector Architecture | accepted |
| D-034 | Implement National Weather Service read-only connector in shadow mode | accepted |
| D-035 | Implement EIA Fuel Benchmark Connector in Shadow Mode | accepted |
| D-036 | Use USDA NASS Quick Stats as official regional benchmark context, not farm-specific yield truth | accepted |
| D-037 | Use USDA AMS MyMarketNews as official market report context, not farm-specific sales truth | accepted |
| D-038 | Use Crop Health Watchlist as read-only shadow/watchlist context, not treatment advice | accepted |
| D-039 | Make specialist agents explicit and align weekly plan outputs with the Grand Plan sections | accepted |
| D-040 | Expand Harvest, Yield, Post-Harvest Inventory, and Sales domain coverage | accepted |
| D-041 | Establish Acceptance and Weekly Plan Human Review Validation Gates | accepted |

---

# 5. Decision Records

---

## D-001: Product name is HarvestAmp

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `01_PRODUCT_BRIEF.md`, `02_AGENT_ARCHITECTURE.md`, `BRAND_RENAME_LOG.md`

### Context

The original working name was unavailable. A new product and agent name was needed before additional documents, schemas, prompts, connectors, and UI copy were created.

### Decision

The product and agent are named **HarvestAmp**.

Use:

- `HarvestAmp` for user-facing product and agent name.
- `harvestamp` for lowercase project/package prefixes.
- `HARVESTAMP` for environment-variable prefixes where needed.
- `harvestamp-*` for internal tool or connector names.

### Rationale

Naming should be settled before implementation to avoid inconsistent docs, prompts, packages, schemas, and marketplace copy.

### Consequences

All future documents, UI labels, prompts, schemas, connector names, build tasks, and marketplace copy should use HarvestAmp. Previous working names should not appear in user-facing output.

### Follow-up

Trademark, domain, marketplace, and social-handle availability still need to be verified before launch.

---

## D-002: Use source-of-truth Markdown documents

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: all current source-of-truth `.md` files

### Context

The project will likely be developed through many Antigravity tasks. Long AI conversations degrade and can lose prior assumptions.

### Decision

The project will maintain durable Markdown source-of-truth files. Antigravity tasks must read the relevant source-of-truth documents before making changes.

Current source-of-truth set:

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

### Rationale

Project state should live in files, not chat memory. This reduces drift, contradictory assumptions, and repeated decisions.

### Consequences

Every build task should begin by reading the relevant documents. Any material change should update the relevant source-of-truth file and this decision log if necessary.

### Follow-up

Create `CHANGELOG.md` to track file-level changes and versioned release notes.

---

## D-003: MVP focuses on two farm profiles

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `03_FARM_PROFILES.md`, `09_MVP_SCOPE.md`, `07_SAMPLE_SCENARIOS.md`

### Context

Agriculture is too broad for a useful first MVP. A generic farmer agent would be shallow and hard to evaluate.

### Decision

The MVP will target two synthetic but realistic farm profiles:

1. **Prairie View Farms**: a large conventional row-crop operation.
2. **Green Basket Organics**: a small certified organic direct-market farm.

### Rationale

These profiles force HarvestAmp to handle very different operating models:

- large-scale commodity crop operations,
- input procurement,
- fuel and fertilizer decisions,
- grain-market context,
- organic input constraints,
- CSA/farmers market planning,
- packaging inventory,
- and direct-market sales workflows.

### Consequences

All MVP scenarios, fixtures, agent contracts, evaluations, and UI prototypes should prove value for these two profiles before adding more farm types.

### Follow-up

Post-MVP profiles may include livestock, dairy, greenhouse/nursery, specialty crop wholesale, and mixed farms.

---

## D-004: Position HarvestAmp as an operations and input-margin agent

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `01_PRODUCT_BRIEF.md`, `09_MVP_SCOPE.md`

### Context

A generic farming chatbot would not be sufficiently differentiated. Farmers already have separate weather, market, extension, supplier, and recordkeeping tools.

### Decision

HarvestAmp will be positioned as a farm-specific operations and input-margin agent.

Its core promise:

> HarvestAmp helps farmers and advisors understand what needs attention, what to buy, when to buy, what to watch, and what decisions require human review.

### Rationale

The most valuable product is not a dashboard of disconnected information. The value is converting weather, inventory, supplier quotes, crop risk, market data, deadlines, and farm context into action-oriented plans.

### Consequences

MVP workflows must emphasize decisions and action plans, not just data display.

### Follow-up

Marketplace copy should emphasize operations, procurement, margin awareness, evidence, and human review.

---

## D-005: Design for B2B/B2B2C marketplace buyers first

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `01_PRODUCT_BRIEF.md`, `09_MVP_SCOPE.md`, `10_BUILD_PLAN.md`

### Context

Google Cloud Marketplace and AI-agent marketplace channels are more enterprise-oriented than consumer app stores.

### Decision

HarvestAmp should be designed for buyers such as:

- ag retailers,
- farmer co-ops,
- crop consultants,
- farm management companies,
- large farm operators,
- food processors,
- lenders,
- insurers,
- and advisor organizations.

The farmer remains the end user, but the first commercial wedge may be an organization serving many farmers.

### Rationale

Enterprise buyers are more likely to use Google Cloud Marketplace procurement and may have stronger willingness to pay.

### Consequences

Architecture must support multi-tenant access, advisor roles, farm-level permissions, audit logs, and sensitive data boundaries.

### Follow-up

Marketplace packaging and pricing strategy should be refined later.

---

## D-006: Use a multi-agent hub-and-spoke architecture

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `05_AGENT_CONTRACTS.md`

### Context

HarvestAmp spans weather, procurement, records, markets, compliance, synthesis, actions, authorization, and farm profiles. One giant agent would be hard to test, govern, and improve.

### Decision

Use a hub-and-spoke architecture with a Supervisor / Orchestrator Agent coordinating narrow specialist agents and deterministic services.

### Rationale

Specialized agents are easier to test, route, constrain, and replace. The supervisor should coordinate work, not own all domain expertise.

### Consequences

Agent contracts must define inputs, outputs, allowed data classes, prohibited behavior, human-review triggers, and evidence requirements.

### Follow-up

Create schemas for shared objects such as `WorkItem`, `FarmContextPackage`, `AgentFinding`, `EvidenceItem`, `Recommendation`, and `ActionPack`.

---

## D-007: Use Google AI products as the target build direction

Status: accepted  
Date: 2026-06-23  
Owner: Product owner / architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `10_BUILD_PLAN.md`

### Context

The project is intended for Google AI products and eventual Google agent marketplace positioning.

### Decision

HarvestAmp should be designed around a Google-oriented stack, including:

- Antigravity for development tasks,
- Google Agent Development Kit or equivalent agent orchestration patterns,
- Gemini / Vertex AI model calls,
- Google Cloud services for data, scheduling, storage, identity, and deployment,
- Google Workspace integrations where appropriate,
- and marketplace packaging later.

### Rationale

The target deployment and marketplace direction should influence early architecture.

### Consequences

Design documents should map concepts to Google services without prematurely locking into every implementation detail.

### Follow-up

Before implementation, verify current Google product capabilities, APIs, pricing, marketplace rules, and deployment requirements.

---

## D-008: Use Antigravity for focused build tasks, not project memory

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `10_BUILD_PLAN.md`

### Context

AI development tools can degrade over long conversations and may lose track of earlier decisions.

### Decision

Use Antigravity in focused tasks. Each task should read source-of-truth docs, make a bounded change, update docs/tests, and produce a handoff summary.

Antigravity should not be treated as the durable memory of the project.

### Rationale

This keeps development modular, auditable, and resilient to context drift.

### Consequences

Build tasks should be small: one schema set, one service, one agent, one workflow, one UI area, or one evaluation suite at a time.

### Follow-up

Create a reusable Antigravity task prompt template and handoff summary template.

---

## D-009: Build a supervisor skeleton early

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `10_BUILD_PLAN.md`

### Context

If specialist agents are built independently without a routing framework, integration may become difficult.

### Decision

Build a simple supervisor skeleton early, using mock specialist agents at first.

### Rationale

This validates routing, shared schemas, context packages, evidence board behavior, human-review propagation, and final synthesis before each specialist is complete.

### Consequences

Early MVP should prove end-to-end workflow shape before domain depth.

### Follow-up

The first vertical slice should run both demo farms through the supervisor using mock or fixture-backed specialist outputs.

---

## D-010: Data first, agent second

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `04_DATA_SOURCES.md`

### Context

Farming recommendations depend heavily on accurate, local, authorized, and fresh data.

### Decision

HarvestAmp should collect, normalize, classify, and store trusted data first. Agents should then reason over controlled context packages.

### Rationale

Agents should not act as uncontrolled data collectors, memory stores, credential holders, or data-governance systems.

### Consequences

The architecture must include connectors, farm data layer, context builder, redaction, source trust, freshness checks, and auditability.

### Follow-up

Define fixtures and schemas before building production connectors.

---

## D-011: Do not rely on ambient open-web monitoring

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner  
Related docs: `04_DATA_SOURCES.md`, `02_AGENT_ARCHITECTURE.md`

### Context

The question was whether agents should ambiently monitor the web for weather, fuel, fertilizer, and market data.

### Decision

HarvestAmp agents should not roam the open web as their primary data strategy. Monitoring should use trusted connectors, public APIs, licensed feeds, user uploads, supplier integrations, email ingestion, manual entry, and farm records.

### Rationale

Open web browsing can be stale, unreliable, legally restricted, hard to audit, and unsafe for compliance-sensitive recommendations.

### Consequences

HarvestAmp should use controlled tools, not random browsing. Tools should enforce source trust, freshness, licensing, authorization, and audit logging.

### Follow-up

Post-MVP commercial data vendors can be wrapped behind HarvestAmp-controlled tools or MCP/ADK tool interfaces.

---

## D-012: Use task-scoped context for LLM agents

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner / security owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `05_AGENT_CONTRACTS.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

### Context

HarvestAmp may handle confidential farm data, supplier quotes, financial records, field locations, and customer information.

### Decision

Agents receive only the minimum context required for the active task. They do not receive full farm access by default.

### Rationale

Task-scoped context reduces privacy risk, cross-farm leakage, prompt bloat, and accidental disclosure.

### Consequences

The Context Package Builder must filter, redact, summarize, or derive data before passing it to LLM agents.

### Follow-up

Evaluation tests must verify that unrelated sensitive data does not appear in prompts or outputs.

---

## D-013: Raw credentials must never enter LLM context

Status: accepted  
Date: 2026-06-23  
Owner: Security owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `05_AGENT_CONTRACTS.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

### Context

HarvestAmp may connect to supplier portals, Google Workspace, APIs, data feeds, and farm-management systems.

### Decision

Raw credentials must never be exposed to LLM agents, prompts, memory, transcripts, vector stores, or logs.

This includes:

- passwords,
- API keys,
- OAuth tokens,
- refresh tokens,
- supplier portal credentials,
- private keys,
- bank credentials,
- and connection secrets.

### Rationale

Credentials are secrets. Agents should request capabilities, not secrets.

### Consequences

Credential handling must be deterministic infrastructure, not normal LLM behavior.

### Follow-up

Build or simulate a Credential Broker / Authorization Service before real integrations.

---

## D-014: Use Credential Broker / Authorization Service and Tool Gateway

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner / security owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `05_AGENT_CONTRACTS.md`

### Context

HarvestAmp needs a safe way for agents to access external tools and private farm data.

### Decision

Use a Credential Broker / Authorization Service and Tool Gateway.

Agents request capabilities. The Credential Broker and Tool Gateway decide whether the request is allowed and return only authorized, task-scoped data.

### Rationale

This separates reasoning from security enforcement.

### Consequences

The Tool Gateway must enforce:

- identity,
- role,
- farm permissions,
- credential state,
- tool allowlist,
- data class access,
- freshness requirements,
- and audit logging.

### Follow-up

Define `authorized_capabilities` and `credential_status` fields in context and work item schemas.

---

## D-015: Treat farm data as private commercial data

Status: accepted  
Date: 2026-06-23  
Owner: Product owner / security owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `04_DATA_SOURCES.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

### Context

Farm data can reveal commercial strategy, production capacity, supplier relationships, pricing leverage, margins, inventory, and financial position.

### Decision

HarvestAmp treats farm data as private commercial data.

### Rationale

Trust is central to adoption. Farmers and enterprise buyers will not use HarvestAmp if it leaks quotes, margins, fields, inventory, or customer information.

### Consequences

Data sensitivity classes must be used:

- Public,
- Farm Internal,
- Farm Confidential,
- Farm Restricted,
- Credentials and Secrets.

### Follow-up

Create tests for redaction, disclosure control, cross-farm isolation, and external-message preview.

---

## D-016: Enforce no cross-farm or cross-tenant leakage

Status: accepted  
Date: 2026-06-23  
Owner: Security owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `08_EVALUATION_TESTS.md`

### Context

HarvestAmp may eventually serve co-ops, advisors, and multi-farm organizations.

### Decision

HarvestAmp must never use one farm's private data to answer another farm's question unless the workflow is explicitly authorized and de-identified or the user has permission to both farms.

### Rationale

Cross-farm leakage is one of the highest trust and legal risks for the product.

### Consequences

All farm data must be partitioned by tenant, farm, and user role. Cross-farm analytics require explicit aggregation and de-identification rules.

### Follow-up

Add regression tests that intentionally attempt to reveal Prairie View data to Green Basket users and vice versa.

---

## D-017: Use human-in-the-loop review for high-risk decisions

Status: accepted  
Date: 2026-06-23  
Owner: Product owner / risk owner  
Related docs: `06_RISK_AND_HUMAN_REVIEW_POLICY.md`, `02_AGENT_ARCHITECTURE.md`, `05_AGENT_CONTRACTS.md`

### Context

HarvestAmp may discuss money, pesticide-related decisions, organic compliance, livestock health, market sales, supplier messages, crop insurance, USDA deadlines, legal/tax documents, and private data sharing.

### Decision

Use risk-based human-in-the-loop review.

HarvestAmp may analyze, summarize, compare, draft, and recommend. It must require human approval before it commits, sends, purchases, discloses, files, applies, deletes, grants access, or executes high-impact external actions.

### Rationale

The product should be useful without pretending to replace the farmer, agronomist, certifier, veterinarian, insurer, attorney, accountant, or government office.

### Consequences

Every `AgentFinding`, `Recommendation`, and `ActionPack` may include a `human_review` object.

### Follow-up

Implement a risk classifier and approval states before production action execution.

---

## D-018: Action Agent must not execute high-impact actions without approval

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner / risk owner  
Related docs: `06_RISK_AND_HUMAN_REVIEW_POLICY.md`, `05_AGENT_CONTRACTS.md`

### Context

HarvestAmp should eventually be able to draft messages, create tasks, update records, and prepare supplier communications. Some actions carry financial, privacy, or compliance risk.

### Decision

The Action Agent must check human-review status before executing any external or high-impact action.

### Rationale

Action gating prevents accidental purchases, disclosures, record changes, or commitments.

### Consequences

External sends, quote requests, purchase orders, official record updates, sensitive exports, permission changes, and document filings require approval.

### Follow-up

MVP can simulate execution by showing draft actions and requiring approval before marking them as executed.

---

## D-019: Evidence is required for recommendations

Status: accepted  
Date: 2026-06-23  
Owner: Product owner / architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `05_AGENT_CONTRACTS.md`, `08_EVALUATION_TESTS.md`

### Context

Agricultural recommendations are context-sensitive. Users need to understand why HarvestAmp suggests something.

### Decision

HarvestAmp recommendations must include evidence, assumptions, confidence, missing data, and human-review status when relevant.

### Rationale

Evidence builds trust and improves user decision-making.

### Consequences

The Evidence Board and `EvidenceItem` structure are core design components.

### Follow-up

Evaluation tests should fail recommendations that lack evidence for high-impact outputs.

---

## D-020: Use deterministic software for math, permissions, schedules, and rules

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `08_EVALUATION_TESTS.md`, `10_BUILD_PLAN.md`

### Context

Not every task should be handled by an LLM. Calculations and security controls need repeatability.

### Decision

Use deterministic software for:

- nutrient calculations,
- cost per acre,
- cost per pound of nutrient,
- fuel inventory math,
- role and permission checks,
- freshness checks,
- source hierarchy,
- scheduling,
- and policy enforcement.

Use LLMs for synthesis, explanation, messy document understanding, routing assistance, and farmer-facing language.

### Rationale

This improves reliability, testability, and safety.

### Consequences

Evaluation tests must include exact expected calculations.

### Follow-up

Create deterministic calculator modules and schema tests before relying on natural-language outputs.

---

## D-021: Build with synthetic/mock data first

Status: accepted  
Date: 2026-06-23  
Owner: Product owner / build owner  
Related docs: `07_SAMPLE_SCENARIOS.md`, `08_EVALUATION_TESTS.md`, `10_BUILD_PLAN.md`

### Context

Real agriculture integrations can be messy, licensed, local, and slow to obtain.

### Decision

Start with synthetic farm profiles, mock data, fixtures, manual entries, and uploaded quote examples.

### Rationale

This validates product logic before expensive integrations.

### Consequences

MVP demos should not depend on live supplier integrations or paid market feeds.

### Follow-up

Create `fixtures/` files for both MVP farm profiles.

---

## D-022: MVP must include weekly action plans for both demo farms

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `07_SAMPLE_SCENARIOS.md`, `09_MVP_SCOPE.md`, `10_BUILD_PLAN.md`

### Context

The flagship user experience is turning many data streams into a practical farm plan.

### Decision

The MVP must support weekly action-plan workflows for:

- Prairie View Farms,
- and Green Basket Organics.

### Rationale

This proves HarvestAmp can adapt to different farm types and sales models.

### Consequences

The first vertical slice should include weather, inventory, procurement, market/sales, compliance, synthesis, and human-review behavior.

### Follow-up

Use `07_SAMPLE_SCENARIOS.md` as the source of scenario prompts and expected outputs.

---

## D-023: MVP must include procurement workflows

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `01_PRODUCT_BRIEF.md`, `05_AGENT_CONTRACTS.md`, `09_MVP_SCOPE.md`

### Context

Fuel, fertilizer, seed, feed, packaging, and input purchases directly affect farm margin.

### Decision

HarvestAmp MVP must include procurement workflows, especially:

- fuel buy-window scenarios,
- fertilizer quote comparison,
- packaging reorder for direct-market farms,
- and inventory-aware recommendations.

### Rationale

Procurement and margin awareness are differentiators versus a generic farm chatbot.

### Consequences

The Procurement Agent, Records + Inventory Agent, Margin + Scenario Agent, and Recommendation Synthesizer are required MVP components.

### Follow-up

Do not promise exact price prediction. Use scenarios, confidence, and human approval.

---

## D-024: MVP must include privacy and authorization simulations

Status: accepted  
Date: 2026-06-23  
Owner: Security owner / product owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `08_EVALUATION_TESTS.md`, `09_MVP_SCOPE.md`

### Context

HarvestAmp handles sensitive data from the beginning, even if data is synthetic during MVP.

### Decision

The MVP must include simulated or basic versions of authorization, role checks, credential states, task-scoped context, Tool Gateway controls, and audit events.

### Rationale

Security and privacy are core product features, not post-launch additions.

### Consequences

Even early prototypes should demonstrate that unauthorized users cannot access other farms' data or execute high-risk actions.

### Follow-up

Build evaluation tests that try to violate privacy boundaries.

---

## D-025: Forecasts are scenario inputs, not deterministic predictions

Status: accepted  
Date: 2026-06-23  
Owner: Product owner / risk owner  
Related docs: `04_DATA_SOURCES.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

### Context

Fuel, fertilizer, commodity, and weather forecasts can be wrong. The product should avoid overconfident predictions.

### Decision

HarvestAmp may use forecasts to support scenarios, watchlists, and confidence estimates. It must not present forecasts as certain.

### Rationale

This reduces financial, operational, and trust risk.

### Consequences

Recommendations should use language such as:

- consider,
- watch,
- scenario,
- confidence,
- based on current data,
- if conditions hold,
- and human approval required.

### Follow-up

Evaluation tests should fail deterministic-sounding market or fuel predictions.

---

## D-026: Commercial market data is post-MVP or optional until value is proven

Status: accepted  
Date: 2026-06-23  
Owner: Product owner  
Related docs: `04_DATA_SOURCES.md`, `09_MVP_SCOPE.md`

### Context

There are many agriculture market intelligence vendors, but licensing them early could add cost and complexity.

### Decision

The MVP should rely primarily on public official data, synthetic fixtures, manual entries, uploaded documents, and farmer-specific records. Commercial market data sources may be evaluated later.

Potential future sources include data vendors for grain markets, cash bids, fertilizer intelligence, fuel outlooks, organic/non-GMO markets, and ag news.

### Rationale

Validate the product value before purchasing or integrating paid feeds.

### Consequences

MVP must not depend on paid or unavailable feeds.

### Follow-up

Later evaluate vendors for row-crop market data, fertilizer intelligence, fuel trends, and organic/non-GMO commodity data.

---

## D-027: Keep pesticide, organic, livestock-health, insurance, legal, and financial advice guarded

Status: accepted  
Date: 2026-06-23  
Owner: Risk owner  
Related docs: `06_RISK_AND_HUMAN_REVIEW_POLICY.md`, `05_AGENT_CONTRACTS.md`, `08_EVALUATION_TESTS.md`

### Context

Some agricultural decisions can create safety, regulatory, certification, animal health, legal, financial, or insurance risk.

### Decision

HarvestAmp must guard high-risk domains with careful language, evidence, confidence, missing-data disclosure, and human/expert review.

### Rationale

HarvestAmp should assist, not replace, qualified professionals or responsible farm decision-makers.

### Consequences

The agent may provide scenarios, checklists, summaries, and draft questions. It must not provide definitive high-risk instructions without human review.

### Follow-up

Red-team tests must include requests for pesticide rates, organic certification decisions, livestock treatment, legal/tax filing, insurance eligibility, and commodity trading advice.

---

## D-028: Create evaluation tests before broad feature expansion

Status: accepted  
Date: 2026-06-23  
Owner: Build owner / evaluation owner  
Related docs: `08_EVALUATION_TESTS.md`, `10_BUILD_PLAN.md`

### Context

A multi-agent system can appear useful while violating privacy, routing, calculation, or human-review requirements.

### Decision

Build an evaluation harness early and require tests for each core workflow.

### Rationale

Evaluation prevents silent regressions and overconfident outputs.

### Consequences

No major new workflow should be considered MVP-ready without tests.

### Follow-up

Turn sample scenarios into automated or semi-automated test cases.

---

## D-029: Build one vertical slice before broad coverage

Status: accepted  
Date: 2026-06-23  
Owner: Product owner / build owner  
Related docs: `09_MVP_SCOPE.md`, `10_BUILD_PLAN.md`

### Context

HarvestAmp could expand into too many farm types and workflows too quickly.

### Decision

Build a working vertical slice before adding breadth.

The first vertical slice should prove:

- farm profile selection,
- supervisor routing,
- weather analysis,
- procurement analysis,
- inventory context,
- market/sales context,
- compliance flags,
- synthesis,
- human-review gating,
- and user-facing action plan output.

### Rationale

A narrow but complete workflow is more valuable than many disconnected partial features.

### Consequences

Do not start with livestock, equipment telematics, full GIS, real supplier integrations, or production marketplace packaging.

### Follow-up

Use Prairie View weekly plan and Green Basket weekly plan as the first two vertical-slice demos.

---

## D-030: Avoid over-agentizing the system

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `10_BUILD_PLAN.md`

### Context

It is tempting to turn every function into an LLM agent.

### Decision

Use agents where language, judgment, synthesis, messy document interpretation, or routing adds value. Use deterministic software for repeatable operations.

### Rationale

This improves reliability, cost control, security, and testability.

### Consequences

The system should include deterministic services, schemas, calculators, rules, permissions, and tool wrappers alongside LLM agents.

### Follow-up

During implementation, challenge every proposed new agent with: could this be a deterministic function, service, or rule instead?

---

## D-031: Modular package layout and mock runner setup

Status: accepted  
Date: 2026-06-23  
Owner: Architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `10_BUILD_PLAN.md`

### Context

HarvestAmp is starting implementation. We need to organize the codebase. A clean, modular structure makes it easy to isolate and test deterministic services vs specialist agents.

### Decision

Implement the following design choices for the first MVP prototype:
- **Modular Package Layout**: Structure the codebase under `harvestamp/` into specialized sub-packages: `core`, `auth`, `gateway`, `context`, `policy`, `agents`, `workflows`, `tools`, `audit`.
- **Simplified YAML Schema Format**: Use a custom YAML schema format for the MVP scaffold, verified programmatically via custom python validators.
- **Integrated Intent Router**: Fold the Intent Router directly into the `Supervisor` workflow class to streamline coordination for the initial scaffold.
- **Evidence Board**: Add an Evidence Board/evidence collector module to track source metadata, confidence levels, and trust tiers.
- **Synthetic/Mock Data & No Real Integrations**: Rely purely on local synthetic YAML fixtures and mock data connectors. No live external API integrations or real supplier communications are established in this task.
- **Final Fixture Layout**: Standardize synthetic data fixtures into:
  - `fixtures/farms/prairie_view_farms.yaml`
  - `fixtures/farms/green_basket_organics.yaml`
  - `fixtures/source_metadata.yaml`
  - `fixtures/data_observations.yaml`
  - `fixtures/scenarios.yaml`
- **Local Mock Scenario Runner**: Implement `scripts/run_scenario.py` to evaluate the system against the initial scenario set.

### Rationale

This structure ensures clear separation of concerns, simplifies testing, prevents raw credential leakage to LLM prompts, strictly enforces human-review gates, and models data isolation and freshness without requiring external network dependencies.

### Consequences

- All files will be placed under the specified modular package directories.
- Stubs and mock agents will return structured YAML-validated objects conforming to the defined schemas.
- Verification tests will run the full set of MVP scenarios using local mock/synthetic data only.

### Follow-up

Review the modular layout and integration boundaries after the first demo.

---

## D-032: Recognize irrigation scheduling and water-request workflows as a HarvestAmp domain

Status: accepted  
Date: 2026-06-24  
Owner: Product owner / architecture owner / risk owner  
Related docs: `03_FARM_PROFILES.md`, `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`, `07_SAMPLE_SCENARIOS.md`, `08_EVALUATION_TESTS.md`, `09_MVP_SCOPE.md`, `10_BUILD_PLAN.md`, `configs/human_review_rules.yaml`

### Context

Many irrigated farming regions require farmers to log into irrigation district, canal company, water association, or water-management websites to request irrigation times, flow rates, or water volumes for fields.

### Decision

HarvestAmp will recognize irrigation scheduling and water-request workflows as a supported domain, using mock/manual/uploaded data first. Real credentialed irrigation portal integration is deferred until Credential Broker, Tool Gateway, human-review gates, audit logging, and provider permissions are ready.

### Rationale

Irrigation scheduling is operationally important, but it carries credential, external-action, resource-allocation, and district-rule risk.

### Consequences

Irrigation workflows require task-scoped context, no raw credentials in chat, user approval before external submission, and expert/responsible-human review where allocation or district-rule uncertainty exists.

### Follow-up

Implement a mock/manual irrigation workflow after this documentation/config patch is accepted.

---

## D-033: Establish MCP Connector Architecture

Status: accepted  
Date: 2026-06-24  
Owner: Architecture owner  
Related docs: `02_AGENT_ARCHITECTURE.md`, `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`

### Context

HarvestAmp needs to connect to outside services. MCP-compatible connectors are the preferred architecture, but agents must not call MCP servers directly. All connectors must stay behind Credential Broker, Tool Gateway, source metadata, task-scoped context, and audit logging.

### Decision

Establish the Model Context Protocol (MCP) connector architecture for HarvestAmp where the Tool Gateway mediates all connector access, preventing specialist agents from invoking external APIs or connectors directly.

### Rationale

This prevents credential leakage to LLM prompts, enforces consistent metadata tracking, and ensures audit logging for all external integrations.

### Consequences

- Specialist agents request abstract capabilities instead of direct connector targets.
- Tool Gateway normalizes output to `ConnectorResult` including `SourceMetadata`.

---

## D-034: Implement National Weather Service read-only connector in shadow mode

Status: accepted  
Date: 2026-06-24  
Owner: Architecture owner / security owner  
Related docs: `04_DATA_SOURCES.md`, `08_EVALUATION_TESTS.md`, `10_BUILD_PLAN.md`

### Context

We need to implement the first read-only connector for NWS weather forecasts without requiring internet for test suites by default, preserving the mock observations fallback, and keeping farm locations confidential.

### Decision

Implement the NWS Weather Connector in shadow mode. The connector rounds coordinates to 4 decimal places for privacy, supports both offline mock mode and live mode (env-flagged with User-Agent check), and logs the NWS results as shadow evidence to the Evidence Board while falling back to mock observations for agent reasoning.

### Rationale

Enables live network testing without breaking offline test determinism or altering agent prompts/logic, ensuring safe, privacy-preserving validation.

### Consequences

- NWSWeatherConnector returns normalized `ConnectorResult`.
- If NWS connector fails (unavailable/stale/error/timeout/denied), the system falls back to mock fixture weather (if available) but sets `fallback_used = True` and lowers the WeatherAgent's confidence to `"low"`.

## D-035: Implement EIA Fuel Benchmark Connector in Shadow Mode

Status: accepted  
Date: 2026-06-24  
Owner: Architecture owner / security owner  
Related docs: `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`, `08_EVALUATION_TESTS.md`, `10_BUILD_PLAN.md`

### Context

We need to implement a read-only fuel benchmark connector to support the Prairie View fuel buy-window workflow (`PVF-002`). EIA benchmark data must be treated as public benchmark context, not as the farmer's actual delivered supplier quote.

### Decision

Implement the EIA Fuel Benchmark Connector in shadow mode. The connector selects region-specific series IDs based on farm profile locations without exposing coordinates/locations, supporting both offline mock mode and live mode (env-flagged with `HARVESTAMP_EIA_SHADOW_LIVE` and `HARVESTAMP_EIA_API_KEY`).

The following mode and fallback rules apply:
- **Offline Mock Mode (Live Disabled)**: When `HARVESTAMP_EIA_SHADOW_LIVE` is not set to `1`, the connector runs in `offline_mock` mode. It returns simulated EIA benchmark data directly with `fallback_used = False`.
- **Fixture Fallback Mode (Live/Connector Failure)**: When live mode is enabled but the EIA API request fails (e.g., due to timeout, invalid API key, or unavailable service), the system falls back to the local benchmark fixture, recording the event with `fallback_used = True` and a populated `fallback_reason`. In both cases, shadow EIA results are logged as evidence on the `EvidenceBoard` with their actual status.

### Rationale

Treating EIA data as public benchmark context rather than the delivered quote prevents overriding farm-specific commercial agreements (supplier quotes). Fallback mechanics ensure the system remains robust during API failures, keeping the farmer's quote as the decision anchor. Mode-based labeling clarifies whether a result represents an offline simulation or a live integration fallback.

### Consequences

- `EIAFuelBenchmarkConnector` returns normalized `ConnectorResult` including `SourceMetadata`.
- `ToolGateway` mediates all EIA connector access.
- ProcurementAgent uses benchmark context in `PVF-002` without replacing the supplier quote as the decision anchor.
- If EIA fails, overall recommendation confidence is not downgraded from "high" to "medium" if farm-specific details are current.

## D-036: Use USDA NASS Quick Stats as official regional benchmark context, not farm-specific yield truth

Status: accepted  
Date: 2026-06-25  
Owner: Architecture owner / security owner  
Related docs: `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`, `08_EVALUATION_TESTS.md`, `10_BUILD_PLAN.md`

### Context

We need to implement a read-only crop benchmark connector to support the Prairie View weekly planning workflow. Crop statistics must be treated as public regional benchmark context, and must not replace farm-specific records or make deterministic farm-level yield claims.

### Decision

Implement the USDA NASS Quick Stats Connector in shadow mode. The connector supports both offline mock mode and live mode (env-flagged with `HARVESTAMP_NASS_SHADOW_LIVE` and `HARVESTAMP_NASS_API_KEY`).

The following mode and fallback rules apply:
- **Offline Mock Mode (Live Disabled)**: When `HARVESTAMP_NASS_SHADOW_LIVE` is not set to `1`, the connector runs in `offline_mock` mode. It returns simulated NASS crop benchmark data directly with `fallback_used = False`.
- **Fixture Fallback Mode (Live/Connector Failure)**: When live mode is enabled but the NASS API request fails (e.g., due to timeout, invalid API key, or unavailable service), the system falls back to the local `nass_crop_benchmarks` fixture, recording the event with `fallback_used = True` and a populated `fallback_reason`. In both cases, shadow NASS results are logged as evidence on the `EvidenceBoard` with their actual status.

### Rationale

Treating NASS data as public benchmark context rather than farm truth prevents overconfident crop yield predictions or overriding farm-specific plans. Fallback mechanics ensure the system remains robust during USDA API failures. Mode-based labeling clarifies whether a result represents an offline simulation or a live integration fallback.

### Consequences

- `NASSQuickStatsConnector` returns normalized `ConnectorResult` including `SourceMetadata` without exposing query credentials.
- `ToolGateway` mediates all NASS connector access.
- `MarginAgent` and `MarketAgent` present NASS as public regional benchmark context only and include a clear warning that NASS does not override farm-specific records.
- If NASS fails or is stale, the crop benchmark context confidence is marked lower (`"low"`).

## D-037: Use USDA AMS MyMarketNews as official market report context, not farm-specific sales truth

Status: accepted  
Date: 2026-06-25  
Owner: Architecture owner / security owner  
Related docs: `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`, `08_EVALUATION_TESTS.md`, `10_BUILD_PLAN.md`

### Context

We need to implement a read-only produce market report connector to support direct-market planning for Green Basket Organics. Produce price statistics must be treated as public regional benchmark context, and must not replace farm-specific records (CSA commitments, restaurant orders, actual sales records) or make deterministic pricing recommendations.

### Decision

Implement the USDA AMS MyMarketNews Connector in shadow mode. The connector supports both offline mock mode and live mode (env-flagged with `HARVESTAMP_AMS_SHADOW_LIVE` and `HARVESTAMP_AMS_API_KEY`).

The following rules apply:
- **Keep AMS as Read-only Context**: Use report findings for regional market context only. Green Basket's CSA commitments, restaurant orders, and farm-specific sales records remain the decision anchor.
- **Tolerate Missing/Different Fields**: Connector output must tolerate missing or differently named report fields instead of hardcoding tomato/salad mix reports rigidly.
- **Config-driven Mappings**: AMS report mappings are fixture/config driven using `slug_id`, `slug_name`, `report_title`, `commodity_map`, `market_type`, and `region`.
- **Connector Mode & Source Labels**:
  - `USDA AMS MyMarketNews API (live)`
  - `USDA AMS MyMarketNews Connector (offline mock)`
  - `Local AMS Market Fixture Fallback`
- **Do Not Recommend Final Price Changes**: Do not recommend final price changes solely from AMS context, and do not create customer/buyer-facing messages from AMS data without user approval.
- **Security Check**: API key values and full request URLs containing credentials must never appear in connector results, evidence, ActionPacks, logs, warnings, exceptions, or rendered outputs.

### Rationale

Treating AMS data as public benchmark context rather than farm truth prevents overconfident pricing predictions or overriding farm-specific sales realities. Fallback mechanics ensure the system remains robust during USDA API failures. Mode-based labeling clarifies whether a result represents an offline simulation or a live integration fallback.

### Consequences

- `AMSMarketNewsConnector` returns normalized `ConnectorResult` including `SourceMetadata` without exposing query credentials.
- `ToolGateway` mediates all AMS connector access.
- `MarketAgent` presents AMS as public regional benchmark context only and includes a clear warning that AMS does not override farm-specific records.
- If AMS fails or is stale, the market report context confidence is marked lower.

---

---

# 6. Superseded Decisions

## S-001: FarmHand working name

Status: superseded  
Date superseded: 2026-06-23  
Superseded by: D-001  
Related docs: `BRAND_RENAME_LOG.md`

### Former decision

The project used FarmHand as the working product and agent name.

### Superseding decision

The product and agent are now named HarvestAmp.

### Consequence

Do not use the previous working name in current docs, code, prompts, UI labels, marketplace copy, or user-facing outputs.

---

# 7. Deferred Decisions

These topics matter but are intentionally deferred beyond the current MVP unless needed for a demo or pilot.

| ID | Deferred decision | Reason deferred |
|---|---|---|
| F-001 | Final marketplace pricing model | Need product validation and buyer discovery first. |
| F-002 | Paid commercial data vendors | Need MVP proof before licensing cost. |
| F-003 | Real supplier integrations | Start with manual entries, uploads, and synthetic fixtures. |
| F-004 | Production Google Cloud deployment architecture | Design alignment exists, but MVP can begin locally or in a simplified environment. |
| F-005 | Mobile native app | MVP can start with web/mobile-responsive UI. |
| F-006 | Livestock support | Post-MVP farm type. |
| F-007 | Greenhouse/nursery support | Post-MVP farm type. |
| F-008 | Automated government filing | Too high-risk for MVP. |
| F-009 | Automated commodity trades or hedging | Too high-risk and likely outside intended scope. |
| F-010 | Automated purchasing or purchase-order execution | MVP should draft and require approval, not execute automatically. |
| F-011 | Production-grade crop image diagnosis | Can be future triage feature, not core MVP. |
| F-012 | Real credentialed Google Workspace ingestion | Can be simulated or implemented later after auth skeleton. |

---

# 8. Rejected Decisions

## R-001: Build a generic farming chatbot

Status: rejected  
Date: 2026-06-23

### Reason

A generic chatbot would be too broad, too shallow, and insufficiently differentiated.

### Replacement

HarvestAmp will be a farm-specific operations and input-margin agent.

---

## R-002: Let agents freely browse the open web for production decisions

Status: rejected  
Date: 2026-06-23

### Reason

Open-web browsing is unreliable, hard to audit, potentially stale, and risky for prices, compliance, and farm-specific recommendations.

### Replacement

Use trusted connectors, authorized integrations, public APIs, licensed feeds, uploads, manual entries, and stored farm records.

---

## R-003: Put raw credentials inside an LLM agent

Status: rejected  
Date: 2026-06-23

### Reason

Raw credentials must never enter LLM context.

### Replacement

Use Credential Broker / Authorization Service and Tool Gateway.

---

## R-004: Build every farm type in the MVP

Status: rejected  
Date: 2026-06-23

### Reason

Agriculture is too broad. Supporting everything early would reduce quality and focus.

### Replacement

Start with Prairie View Farms and Green Basket Organics.

---

## R-005: Make definitive price predictions

Status: rejected  
Date: 2026-06-23

### Reason

Fuel, fertilizer, and commodity prices are uncertain. Overconfident price prediction could create financial risk.

### Replacement

Use forecasts and benchmarks for scenarios, watchlists, confidence levels, and human-reviewed recommendations.

---

# 9. Open Decisions

These decisions still need to be made or validated.

| ID | Open decision | Notes |
|---|---|---|
| O-001 | Confirm HarvestAmp brand availability | Trademark, domain, marketplace, and social availability should be checked. |
| O-002 | Choose exact first UI format | Chat-first, dashboard-first, or combined MVP. |
| O-003 | Choose first implementation datastore | Firestore, Cloud SQL, local JSON fixtures, or hybrid. |
| O-004 | Choose schema format | JSON Schema, YAML schema, Pydantic-style models, protocol buffers, or another approach. |
| O-005 | Decide how much Google Cloud to use in local MVP | The design aligns with Google, but first prototype may be simplified. |
| O-006 | Decide whether to build a standalone MCP layer now | MCP may be useful later; initial ADK/tool wrappers may be simpler. |
| O-007 | Choose first public weather integration | Likely NWS/NOAA for U.S. MVP, but implementation details need confirmation. |
| O-008 | Choose whether to include live public APIs in first demo | Mock data may be enough for first vertical slice. |
| O-009 | Define exact marketplace buyer persona for first pilot | Co-op, crop consultant, ag retailer, or large farm operator. |
| O-010 | Define pricing hypothesis for pilot | Subscription, usage-based, combined, or private offer. |
| O-011 | Define retention policy | How long prompts, logs, extracted documents, and audit events should persist. |
| O-012 | Define data export and deletion policy | Especially important for enterprise buyers. |
| O-013 | Define legal disclaimers and terms | Needed before pilot or marketplace packaging. |
| O-014 | Decide whether small organic MVP includes customer data | CSA/customer data increases privacy burden. |
| O-015 | Decide whether row-crop MVP includes crop insurance documents | Useful but high-risk and document-heavy. |

---

# 10. Maintenance Rules

## 10.1 When to add a decision

Add a decision when the project chooses a path that affects:

- product scope,
- architecture,
- user roles,
- data sources,
- privacy/security,
- human review,
- agent boundaries,
- build sequence,
- marketplace strategy,
- or post-MVP roadmap.

## 10.2 When to supersede a decision

Do not delete old decisions. Mark them as `superseded` and add a new decision with a higher ID.

## 10.3 When to reject a proposed path

If a path is discussed and intentionally not chosen, add it to the rejected section. This prevents future tasks from rediscovering and re-proposing the same risky direction.

## 10.4 When to update related documents

A decision is not complete until affected source-of-truth documents are updated.

For example:

- New human-review decision -> update `06_RISK_AND_HUMAN_REVIEW_POLICY.md` and `05_AGENT_CONTRACTS.md`.
- New data-source decision -> update `04_DATA_SOURCES.md`.
- New MVP scope decision -> update `09_MVP_SCOPE.md`.
- New build-order decision -> update `10_BUILD_PLAN.md`.

## 10.5 Antigravity usage rule

Every Antigravity task should include this instruction:

```text
Before making changes, read DECISION_LOG.md and the relevant HarvestAmp source-of-truth documents. Do not contradict accepted decisions. If a change requires revisiting an accepted decision, propose a new decision record instead of silently changing the architecture.
```

---

# 11. Current Build Direction Summary

HarvestAmp is a Google-oriented, multi-agent farm operations and input-margin MVP. The first build should focus on two synthetic farm profiles: Prairie View Farms and Green Basket Organics.

The system should use a supervisor and narrow specialist agents, but not overuse LLMs where deterministic services are better. It should begin with schemas, fixtures, mock data, authorization/context skeletons, and a supervisor skeleton. It should then build one vertical slice: a weekly action plan that combines weather, procurement, inventory, market/sales context, compliance flags, synthesis, evidence, and human-review gating.

The MVP should not attempt full real-world integrations, automated purchases, crop diagnosis, legal/insurance decisions, government filing, or automated trading. It should prove that HarvestAmp can make farm-specific recommendations safely, with evidence, role-aware data access, task-scoped context, and human approval for high-impact actions.


## D-LOCAL-DOC-001: Local uploaded document extraction remains draft until review

Status: proposed for acceptance
Date: 2026-06-25
Owner: Product / architecture owner
Related docs: `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

### Context

Farm-specific invoices and supplier quotes are more actionable than public benchmarks, but they can contain commercially sensitive pricing, payment details, and ambiguous fields.

### Decision

HarvestAmp will initially parse local files and synthetic fixtures only. Extracted fields are source-labeled and Farm Restricted, but they remain draft pending review. Official record updates, supplier selection, external messages, and purchases require explicit approval.

### Consequences

The first document extraction milestone improves farm-specific usefulness without introducing Drive, Gmail, supplier portals, OAuth, payment handling, or automatic record mutation.


## D-038: Use Crop Health Watchlist as read-only shadow/watchlist context, not treatment advice

Status: accepted
Date: 2026-06-25
Owner: Agronomic Product Compliance Lead
Related docs: `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

### Context

To provide regional agronomic utility, HarvestAmp should incorporate public disease, pest, abiotic, and regulatory watchlists (such as Extension bulletins, IPM centers, and USDA APHIS PPQ/CAPS alerts). However, providing specific chemical treatment, active ingredient, pesticide product, application rate, or tank-mix recommendations introduces significant legal and environmental compliance risks.

### Decision

HarvestAmp will implement a read-only `CropHealthWatchlistConnector` in shadow/watchlist mode under the `crop_health_watchlist` capability. 
1. Watchlist data serves strictly as public regional context and cannot override farm-specific scouting, crop, or organic certification records.
2. Direct spray queries (e.g. "what should I spray?") will be redirected to scouting, official label review, and a certified crop advisor, actively refusing specific pesticide recommendations.
3. For APHIS/regulatory-style alerts, the system will not diagnose the pest or suggest sample movement/shipment, advising only field documentation and contacting appropriate official plant health/regulatory channels.

### Consequences

HarvestAmp provides regional crop health awareness to farmers safely, without prescribing chemical treatments or violating regulatory quarantine reporting guidelines.


## D-039: Make specialist agents explicit and align weekly plan outputs with the Grand Plan sections

Status: accepted
Date: 2026-06-25
Owner: Architecture Lead
Related docs: `02_AGENT_ARCHITECTURE.md`, `10_BUILD_PLAN.md`

### Context

To satisfy the first vertical slice alignment of the Grand Plan, specialist agents must be explicitly exposed in separate agent modules. Additionally, the weekly action plan output printed by the CLI simulator should map directly to the 12 required sections for Prairie View Farms and Green Basket Organics.

### Decision

1. Expose explicit mock specialist agents: `WeatherFieldworkAgent`, `ProcurementAgent`, `RecordsInventoryAgent`, `MarketSalesAgent`, `ComplianceAgent`, and `MarginScenarioAgent` in dedicated modules under `harvestamp/agents/`.
2. Update the supervisor weekly-plan topic routing to invoke these agents and return AgentFinding-shaped objects.
3. Update `scripts/run_weekly_plan.py` to organize and print findings exactly according to the 12 Grand Plan sections.

### Consequences

The weekly action plan outputs are fully structured and consistent with the Grand Plan expectations, and agent boundaries are cleanly defined and exposed.


## D-040: Expand Harvest, Yield, Post-Harvest Inventory, and Sales domain coverage

Status: accepted
Date: 2026-06-29
Owner: Domain Lead
Related docs: `02_AGENT_ARCHITECTURE.md`, `04_DATA_SOURCES.md`

### Context

To fill the missing harvest-time workflow for Prairie View Farms (PVF) and Green Basket Organics (GBO), we must support harvest events, yield records, post-harvest inventories, sales commitments, sales records, grain load tickets, and grain bin inventories.

### Decision

1. **Schemas & Constraints**: Added seven new schemas with required minimum: 0 bounds, enum-constrained statuses, and custom domain validation relations.
2. **Gateway Loaders**: Added data loading routines to `ToolGateway` that filter by target farm and apply custom role-based redactions for field employees.
3. **Agent Overrides**: Implemented specific business logic overrides in the named agent modules (`RecordsInventoryAgent`, `MarketSalesAgent`, `ComplianceAgent`, and `MarginScenarioAgent`).
4. **Safety & Policy Guidelines**: Stored grain remains scenario-only (no sales or hedge advice), and official records or inventory updates are marked "draft/blocked pending review".

### Consequences

The system supports the full harvest-time workflow safely and securely across both farm profiles, with role-based safety gates active.


## D-041: Establish Acceptance and Weekly Plan Human Review Validation Gates

Status: accepted
Date: 2026-06-29
Owner: Security & Risk Lead
Related docs: `06_RISK_AND_HUMAN_REVIEW_POLICY.md`, `02_AGENT_ARCHITECTURE.md`

### Context

To satisfy harvest-time acceptance validation, the supervisor and agents must automatically draft proposed actions, aggregate specific human review reasons, avoid missing-data contradictions, flag grain mismatches, de-duplicate weekly plan sections, and verify employee redactions for both Prairie View Farms and Green Basket Organics.

### Decision

1. **Automatic Proposed Actions**: Integrated weekly plan scanners to automatically draft proposed actions (`draft_inventory_reconciliation`, `draft_official_record_update`, `draft_bin_reconciliation`, `draft_cooler_inventory_update`, `draft_sales_record_reconciliation`) when weekly summaries mention draft/blocked status.
2. **Domain-Specific Reasons**: Standardized human review reasons list: `draft_cooler_inventory_update`, `harvest_record_review`, `post_harvest_inventory_review`, `grain_bin_reconciliation`, `yield_record_review`, `production_record_caution`, `sales_record_reconciliation`, `food_safety_record_review`.
3. **Corn Variance Warning**: Configured `RecordsInventoryAgent` to compare PVF gross yield records (56,000 bu) and bin inventories (57,000 bu) and print a mismatch warning.
4. **GBO Weekly De-duplication**: Focused Market / CSA plan findings on obligations/commitments, while routing cooler stock/shortfalls to Wash-Pack priorities.
5. **Employee Redactions**: Hidden customer names, pricing, sales totals, payment status, margins, and unpaid invoices in GBO weekly plans for `field_employee`. Added unit tests verifying these constraints.

### Consequences

Scenarios and weekly plans are robustly validated, secure, and fully consistent with role access privileges.




