# HarvestAmp Continuation Handoff

**Document purpose:** This file is a compact handoff so the HarvestAmp project can be resumed later without relying on the full chat history.

**Current product name:** HarvestAmp  
**Product type:** Google AI / Google Cloud agriculture agent MVP  
**Current stage:** Planning, architecture, source-of-truth documentation, schemas, fixtures, and build-plan scaffold are drafted. No production code has been requested or generated yet beyond planning/scaffold artifacts.

---

## 1. One-paragraph project summary

HarvestAmp is a farm operations, procurement, and margin-support agent intended for a future Google AI / Google Cloud agent marketplace-style deployment. The MVP focuses on two farm profiles: a large conventional row-crop operation and a small certified organic direct-market farm. HarvestAmp should monitor and reason over weather, fieldwork windows, fuel, fertilizer, seed, inventory, supplier quotes, market/sales context, USDA/compliance deadlines, organic constraints, and farm records. Its value is not generic farm information lookup; its value is turning trusted data and farm-specific context into practical recommendations, action plans, alerts, quote comparisons, and human-reviewed next steps.

---

## 2. Current source-of-truth files

Use the live, non-versioned files as the current working set:

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
DECISION_LOG.md
CHANGELOG.md
configs/human_review_rules.yaml
schemas/*.schema.yaml
fixtures/*.yaml
```

Versioned files exist as checkpoints only. Do not treat older versioned files as the current source of truth unless explicitly rolling back.

---

## 3. Brand/name rule

The product and agent are named **HarvestAmp**.

Use:

```text
HarvestAmp        # user-facing product and agent name
harvestamp        # lowercase internal prefix
harvestamp-*      # connector/tool/service prefixes
```

Do not reintroduce any prior working name in user-facing copy, code names, prompts, UI labels, schemas, configs, marketplace copy, or tests.

---

## 4. MVP farm profiles

The MVP intentionally supports two synthetic demo farms first.

### 4.1 Prairie View Farms

Large conventional row-crop profile.

Focus areas:

- Corn/soybean/wheat-style row-crop operations
- Fuel planning and diesel buy-window recommendations
- Fertilizer quote comparison
- Seed/order awareness
- Fieldwork weather windows
- Spray-window guardrails
- Grain market context and margin scenarios
- USDA/crop-insurance-style deadline reminders
- Inventory and invoice updates
- Human review for financial, pesticide, compliance, and external supplier actions

### 4.2 Green Basket Organics

Small certified organic direct-market profile.

Focus areas:

- Organic vegetable/direct-market production
- CSA planning
- Farmers market pack lists
- Restaurant/wholesale availability drafts
- Packaging inventory and reorder planning
- Organic input verification
- Market-day weather
- High tunnel/watchlist planning
- Customer and sales privacy boundaries
- Human review for organic compliance, external customer messages, financial purchases, and record changes

---

## 5. Core architecture decisions

These decisions should be treated as binding unless deliberately revised in `DECISION_LOG.md`.

### 5.1 Google-first direction

HarvestAmp should be designed for Google AI / Google Cloud products, including an eventual path through Google ADK-style agents, Google Cloud services, and Antigravity-assisted development.

### 5.2 Multi-agent architecture

HarvestAmp is not one giant chatbot. It is a supervised multi-agent system with specialist agents and deterministic infrastructure.

Core agents/services:

```text
Credential Broker / Authorization Service   # deterministic service, not normal LLM agent
Tool Gateway                                # deterministic authorization and tool boundary
Context Package Builder                     # task-scoped context assembly
Supervisor / Orchestrator Agent
Intent Router
Farm Profile Agent
Weather + Fieldwork Agent
Input Procurement Agent
Records + Inventory Agent
Market + Sales Agent
Compliance Agent
Margin + Scenario Agent
Recommendation Synthesizer
Action Agent
Document / Media Intake Agent
Credential Setup Assistant
Optional Crop / Livestock Risk Agent
Future Advisor / Co-op Admin Agent
```

### 5.3 Credentials are never handled by normal LLM agents

Raw credentials, API keys, OAuth tokens, passwords, supplier portal logins, Google account tokens, and similar secrets must never appear in prompts, agent memory, logs, transcripts, vector stores, or model context.

Agents request capabilities. The Credential Broker and Tool Gateway decide whether those capabilities are authorized.

### 5.4 No ambient open-web monitoring for production decisions

HarvestAmp agents should not roam the open web for production decisions. Data should enter through trusted connectors, authorized integrations, public APIs, supplier uploads/emails, user-entered values, farm records, and scheduled/event-driven monitoring.

### 5.5 Task-scoped context

Agents receive only the minimum farm data required for the active task. HarvestAmp must not provide unrestricted farm records to an LLM when a small derived context package is enough.

### 5.6 No cross-farm or cross-tenant leakage

One farm's supplier quotes, acreage, field locations, inventory, margin calculations, break-even values, crop plans, yields, sales plans, customer lists, or documents must not be used to answer another farm's question unless an authorized multi-farm workflow explicitly allows it and data is appropriately de-identified or permissioned.

### 5.7 Human-in-the-loop by risk tier

HarvestAmp can analyze, summarize, compare, draft, and recommend. It must require human approval before committing, sending, purchasing, disclosing, filing, applying, deleting, granting access, changing official records, or making high-risk decisions sound final.

### 5.8 Scenario guidance, not deterministic price prediction

HarvestAmp should not promise perfect commodity, fuel, fertilizer, or input price prediction. It should provide scenarios, confidence, source freshness, watchlists, buy-now/wait/split logic, and human-reviewed recommendations.

---

## 6. Data-source strategy

### MVP data sources

Start with:

- Public weather and alerts
- Public USDA-style market/deadline/ag data
- Public fuel benchmarks and forecasts
- User-entered values
- Uploaded supplier quotes, invoices, seed orders, packaging orders, and farm records
- Mock fixtures for tests and demos

### Post-MVP data sources

Commercial data and forecasting services may be considered later, especially:

- DTN or Barchart/cmdtyView for row-crop markets, cash bids, basis, and related data
- Argus, Green Markets, CRU, S&P Fertecon, or Profercy for fertilizer market intelligence
- StoneX, Expana/Mintec, S&P Global, LSEG/Reuters for enterprise market intelligence
- Mercaris or Argus Organic/Non-GMO if organic commodity market workflows become important
- Co-op, ag retailer, seed dealer, fuel distributor, POS, CSA, Google Workspace, and farm-management integrations

### Decision priority

For farm-specific procurement advice, the farmer's actual authorized supplier quote should be treated as more actionable than a benchmark price.

---

## 7. Human review summary

Human review is required for:

- Financial commitments or large purchasing recommendations
- Supplier selection or outbound supplier messages
- Crop sales, livestock sales, storage, hedging, or market-plan changes
- Pesticide/herbicide/fungicide/insecticide/tank-mix/rate/label/drift/pre-harvest/re-entry guidance
- Fertilizer/manure/nutrient-management recommendations beyond arithmetic comparison
- Organic input or certification-sensitive determinations
- Livestock illness, medication, vaccination, withdrawal, ration, or animal-health decisions
- USDA, crop insurance, tax, legal, payroll, food-safety, or official compliance workflows
- Sharing farm data, field boundaries, supplier quotes, financials, customer lists, or reports externally
- Permission changes, credential changes, exports, deletion, and official record changes
- Low-confidence, stale-data, missing-data, or conflicting-source cases that could affect a high-impact decision

The Action Agent must check the `human_review` object before taking any external or high-impact action.

---

## 8. Current scaffold artifacts

### Schemas

The scaffold includes YAML schema-style files for shared structures:

```text
schemas/common_defs.schema.yaml
schemas/work_item.schema.yaml
schemas/farm_context_package.schema.yaml
schemas/agent_finding.schema.yaml
schemas/recommendation.schema.yaml
schemas/action_pack.schema.yaml
schemas/human_review.schema.yaml
schemas/evidence_item.schema.yaml
schemas/farm_profile.schema.yaml
schemas/quote.schema.yaml
schemas/inventory_item.schema.yaml
schemas/audit_event.schema.yaml
```

### Fixtures

The scaffold includes synthetic YAML fixtures:

```text
fixtures/prairie_view_farms.yaml
fixtures/green_basket_organics.yaml
fixtures/sample_work_items.yaml
fixtures/sample_context_packages.yaml
fixtures/sample_evidence.yaml
fixtures/sample_uploads_and_quotes.yaml
fixtures/sample_agent_findings.yaml
fixtures/sample_action_packs.yaml
fixtures/sample_audit_events.yaml
fixtures/sample_scenarios.yaml
```

### Configs

The scaffold includes:

```text
configs/human_review_rules.yaml
```

These files are planning/build scaffolds, not final production schemas.

---

## 9. Recommended next development sequence

When work resumes, the most practical next steps are:

1. Create or organize the repository structure.
2. Place the source-of-truth docs under a `docs/` directory.
3. Place schemas under `schemas/`.
4. Place fixtures under `fixtures/`.
5. Place rule configs under `configs/`.
6. Add a project `README.md` that points to the source-of-truth files.
7. Build a minimal skeleton that can load fixtures, validate schemas, and run sample scenarios.
8. Build the deterministic Credential Broker / Authorization Service stub.
9. Build the Tool Gateway stub.
10. Build the Context Package Builder.
11. Build the Supervisor / Orchestrator skeleton with mock specialist agents.
12. Build the first vertical slice: Weekly Farm Action Plan using mock data.
13. Add the Weather + Fieldwork Agent.
14. Add the Input Procurement Agent.
15. Add the Records + Inventory Agent.
16. Add the Recommendation Synthesizer.
17. Add the Action Agent with approval gates.
18. Run the evaluation tests from `08_EVALUATION_TESTS.md` against the sample scenarios.
19. Only after the mock workflows work, add real data connectors.

---

## 10. First vertical slice to build

The first runnable MVP slice should be:

```text
User asks: "What should I know about my farm this week?"

Supervisor routes to:
- Weather + Fieldwork Agent
- Input Procurement Agent
- Records + Inventory Agent
- Market + Sales Agent
- Compliance Agent

Agents return AgentFindings.
Recommendation Synthesizer produces ActionPack.
Risk/Human Review policy marks required approvals.
Action Agent refuses external action unless approval is recorded.
```

This should work for both Prairie View Farms and Green Basket Organics using fixtures before real integrations.

---

## 11. Antigravity starter prompt

Use this prompt to resume development in Antigravity or another coding agent:

```text
You are working on HarvestAmp, a Google AI / Google Cloud agriculture agent MVP.

Read these files first and treat them as the current source of truth:
- 01_PRODUCT_BRIEF.md
- 02_AGENT_ARCHITECTURE.md
- 03_FARM_PROFILES.md
- 04_DATA_SOURCES.md
- 05_AGENT_CONTRACTS.md
- 06_RISK_AND_HUMAN_REVIEW_POLICY.md
- 07_SAMPLE_SCENARIOS.md
- 08_EVALUATION_TESTS.md
- 09_MVP_SCOPE.md
- 10_BUILD_PLAN.md
- DECISION_LOG.md
- CHANGELOG.md
- configs/human_review_rules.yaml
- schemas/*.schema.yaml
- fixtures/*.yaml

The product/agent is named HarvestAmp. Do not use any prior working name.

Important constraints:
- Build against contracts, schemas, fixtures, and evaluation tests.
- Do not invent architecture that conflicts with the source-of-truth documents.
- Use a supervised multi-agent architecture.
- Keep credentials out of LLM prompts and agent memory.
- Use task-scoped context only.
- Enforce human review for financial, compliance, safety, privacy, external-disclosure, and official-record actions.
- Start with mock/manual/uploaded/public data before real vendor integrations.

Current task:
[INSERT SPECIFIC TASK HERE]

At the end, update CHANGELOG.md and, if a significant architectural or product decision is made, update DECISION_LOG.md.
Provide a short handoff summary with changed files, tests run, and unresolved questions.
```

---

## 12. Suggested next task prompt

A strong next prompt is:

```text
Create the initial HarvestAmp repository structure and a minimal local runner that loads the YAML fixtures, validates the main schemas at a basic level, and runs the first sample workflow: Weekly Farm Action Plan for Prairie View Farms and Green Basket Organics using mock AgentFindings. Do not integrate real APIs yet. Enforce the human_review gate in the Action Agent stub.
```

Another useful non-code task is:

```text
Create README.md and ANTIGRAVITY_TASKS.md from the existing source-of-truth documents so the build can proceed in small tasks.
```

---

## 13. Open questions to revisit

These are still open or likely to need decisions:

1. Is HarvestAmp the final brand after trademark/domain/marketplace checks?
2. Should the first pilot buyer be an individual farm, a crop consultant, a co-op, an ag retailer, or a farm-management company?
3. Which Google Cloud runtime and agent deployment pattern will be used first?
4. Which exact weather provider will be used in the first live integration?
5. Will the MVP include only mock/manual commodity prices or a licensed market-data source?
6. What dollar thresholds should trigger user approval for fuel, fertilizer, seed, packaging, and other purchases?
7. What roles should exist in the MVP beyond farm owner, farm manager, advisor, and worker?
8. Will Google Workspace integrations be included in MVP or deferred?
9. How should customer data retention and deletion be implemented?
10. What exact marketplace positioning should be used: farmer-facing, advisor-facing, co-op-facing, or enterprise ag operations?

---

## 14. How to continue in a later ChatGPT session

Upload or provide this file together with the latest source-of-truth files, then say:

```text
Continue the HarvestAmp project from CONTINUATION_HANDOFF.md. Use the live docs 01 through 10, DECISION_LOG.md, CHANGELOG.md, schemas, configs, and fixtures as source of truth. Help me with the next step.
```

If the later session has no access to the project files, paste this handoff first and then re-upload the zip/scaffold or the specific files needed for the next task.

---

## 15. Handoff note

Current project status: HarvestAmp has a complete planning and architecture scaffold. The next phase should be implementation setup, repository organization, schema/fixture validation, and a mock first vertical slice. Continue to keep conversations short, task-specific, and grounded in files rather than relying on long chat memory.
