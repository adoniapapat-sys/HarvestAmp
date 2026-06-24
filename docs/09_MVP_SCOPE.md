# 09_MVP_SCOPE.md

# MVP Scope: HarvestAmp

**Version:** 0.1  
**Date:** 2026-06-22  
**Status:** Draft MVP source-of-truth document  
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

**Intended use:** Practical implementation boundary for Antigravity tasks, Google ADK workflow planning, UI scoping, evaluation planning, and MVP delivery decisions.

---

## 0. Important Note

This document defines the **first MVP boundary** for HarvestAmp.

HarvestAmp is a multi-agent farming operations and input-margin advisor. The product vision is intentionally large. The MVP must be intentionally small.

The MVP should prove that HarvestAmp can:

1. Understand two very different farm types.
2. Route user requests to the right specialist agents.
3. Use farm-specific context instead of generic farming advice.
4. Combine weather, procurement, inventory, market, compliance, and records context into practical recommendations.
5. Enforce privacy, authorization, credential, and human-review guardrails.
6. Produce useful weekly plans, buy-window recommendations, quote comparisons, and direct-market planning support.
7. Avoid high-risk or overconfident advice.
8. Be evaluated against stable synthetic scenarios before real customer data or real integrations are used.

This document should be used to prevent scope creep.

If an idea is not listed in this document as **MVP In Scope**, it should be treated as **post-MVP** unless the product owner explicitly moves it into the MVP.

---

## 1. MVP Definition

The HarvestAmp MVP is a **working multi-agent decision-support prototype** for two synthetic farm profiles:

1. **Prairie View Farms**  
   A large conventional row-crop operation focused on corn, soybeans, winter wheat, fuel, fertilizer, seed, grain-market context, weather windows, fieldwork planning, and margin protection.

2. **Green Basket Organics**  
   A small certified organic direct-market vegetable farm focused on CSA, farmers markets, restaurant availability, packaging inventory, harvest planning, organic input review, market-day weather, and customer-facing drafts.

The MVP should be able to run a small set of representative workflows end to end using synthetic, mock, uploaded, or manually entered data.

The MVP is **not** a full production agriculture platform. It is not yet a complete marketplace-ready commercial product. It is the first proof that the architecture, agent contracts, data boundaries, human-review policy, and user experience can work together.

---

## 2. MVP Goal

The MVP goal is:

> Demonstrate that HarvestAmp can deliver farm-specific, source-aware, human-reviewed action recommendations for two representative farm types using a multi-agent architecture and controlled data inputs.

The MVP should answer the question:

> Is HarvestAmp useful enough, safe enough, and structured enough to justify deeper implementation, real integrations, and commercial pilot conversations?

---

## 3. MVP Non-Goals

The MVP should **not** try to prove everything.

HarvestAmp does **not** need to support the following in the first MVP:

1. Every crop.
2. Every livestock type.
3. Every country or region.
4. Every USDA, crop insurance, pesticide, organic, food safety, tax, or legal workflow.
5. Real supplier portal integrations.
6. Automatic purchases.
7. Commodity trading execution.
8. Full pesticide-label interpretation.
9. Definitive crop disease diagnosis.
10. Definitive organic certification rulings.
11. Veterinary medical recommendations.
12. Bank integrations.
13. Live marketplace deployment.
14. Paid commercial data feeds.
15. Full mobile offline capability.
16. Equipment telematics.
17. IoT fuel-tank sensors.
18. Drone imagery.
19. Yield-map ingestion.
20. Multi-tenant enterprise administration for co-ops or advisors.

These may become future features, but they should not block the MVP.

---

## 4. MVP Product Shape

The MVP should feel like a simple app experience powered by multiple agents.

The app experience should include:

1. A chat or prompt interface.
2. A basic farm dashboard.
3. A weekly action plan view.
4. A recommendation card format.
5. A human-review / approval state display.
6. A small upload/manual-entry flow for quotes, invoices, or farm records.
7. A simple task / alert output view.
8. A basic data-source and evidence display.

The MVP does not need to be visually polished, but it should clearly demonstrate the product logic.

---

## 5. MVP Farm Profiles

HarvestAmp MVP is scoped to the two synthetic profiles defined in `03_FARM_PROFILES.md`.

### 5.1 Prairie View Farms

**Farm type:** Large conventional row-crop farm  
**Primary operations:** Corn, soybeans, winter wheat  
**Sales model:** Commodity grain / elevator / storage context  
**Primary value:** Protect operating margin and manage fieldwork by combining weather, input costs, inventory, supplier quotes, grain-market context, crop risk, and deadlines.

MVP must support Prairie View workflows for:

1. Weekly row-crop action plan.
2. Fuel buy-window advisor.
3. Draft fuel supplier message.
4. Fertilizer quote comparison.
5. Spray-window guardrail response.
6. Stored grain sale scenario analysis.
7. Wheat harvest weather window.
8. Field employee privacy boundary.
9. Fuel invoice upload and inventory update.
10. Conflicting fuel data handling.

### 5.2 Green Basket Organics

**Farm type:** Small certified organic direct-market vegetable farm  
**Primary operations:** Diversified vegetables, CSA, farmers market, restaurant sales  
**Sales model:** Direct-to-consumer and local wholesale  
**Primary value:** Coordinate harvest, packaging, market-day planning, organic-input review, customer communication, and weekly task planning.

MVP must support Green Basket workflows for:

1. Weekly organic direct-market plan.
2. Farmers market pack list.
3. CSA box plan and newsletter draft.
4. Packaging reorder advisor.
5. Organic input verification.
6. Restaurant availability draft.
7. High tunnel heat and humidity watch.
8. Market crew task list.
9. Organic record upload.
10. Customer-data privacy boundary.

---

## 6. MVP User Roles

The MVP should demonstrate basic role-aware behavior, even if full enterprise identity management is mocked.

### 6.1 Required MVP roles

| Role | Description | MVP capability |
|---|---|---|
| Farm owner | Primary decision-maker and account owner | Can view all farm data, approve high-impact actions, manage farm profile |
| Farm manager | Operational decision-maker | Can view most farm data, approve some tasks, prepare action plans |
| Field employee / crew member | Limited operational user | Can view assigned tasks and non-sensitive operational details only |
| Advisor / consultant | Optional reviewer | Can view only authorized farm information and provide review context |
| Account admin | Permission and data-sharing authority | Can approve credential, integration, export, and access decisions |

### 6.2 MVP role behavior

The MVP should demonstrate at least two role boundaries:

1. A field employee should not see supplier quotes, margin calculations, break-even information, or sensitive inventory unless authorized.
2. An outgoing message or report should not disclose sensitive farm data without explicit approval from an authorized user.

Full enterprise-grade role management may be post-MVP, but the MVP must prove that role awareness exists in the architecture and test cases.

---

## 7. MVP Agent System

The MVP should implement or simulate the following HarvestAmp agents and deterministic services.

### 7.1 Required MVP agents and services

| Component | MVP status | Purpose |
|---|---:|---|
| Credential Broker / Authorization Service | Required | Enforce user, farm, role, credential, and tool-access permissions |
| Tool Gateway | Required | Mediate all external or simulated tool calls |
| Context Package Builder | Required | Provide task-scoped context to agents |
| Supervisor / Orchestrator Agent | Required | Route requests and coordinate specialist agents |
| Intent Router | Required | Classify incoming user requests or scheduled triggers |
| Farm Profile Agent | Required | Collect and update basic farm profile information |
| Weather + Fieldwork Agent | Required | Translate weather and field context into operational risk and windows |
| Input Procurement Agent | Required | Analyze fuel, fertilizer, seed, packaging, and supplier quote workflows |
| Records + Inventory Agent | Required | Track inventory, extracted document data, notes, and task updates |
| Market + Sales Agent | Required but limited | Provide commodity/direct-market context and scenario framing |
| Compliance Agent | Required but limited | Apply guardrails for organic, USDA, pesticide, food safety, and documentation triggers |
| Margin + Scenario Agent | Required | Convert prices, inventory, and assumptions into scenarios and margin impact |
| Recommendation Synthesizer | Required | Produce farmer-facing recommendations and action packs |
| Action Agent | Required but gated | Draft tasks, reminders, messages, and updates only after approval where required |
| Document / Media Intake Agent | Required but limited | Extract structured fields from uploaded quotes, invoices, records, or notes |
| Credential Setup Assistant | Optional in MVP | Help explain permission setup; may be mocked |
| Crop / Livestock Risk Agent | Optional / limited | Crop risk watchlist only; no definitive diagnosis or treatment recommendation |

### 7.2 MVP orchestration patterns

The MVP should demonstrate these orchestration types:

1. **Single-agent workflow**  
   Example: summarize an uploaded fuel invoice.

2. **Sequential workflow**  
   Example: upload fertilizer quote -> extract fields -> normalize units -> compare options -> synthesize recommendation -> require approval.

3. **Parallel fan-out / gather workflow**  
   Example: weekly action plan runs weather, procurement, market, records, and compliance agents in parallel, then synthesizes output.

4. **Conditional routing**  
   Example: organic input question routes to procurement plus compliance plus human review.

5. **Loop / refinement workflow**  
   Example: user edits a draft supplier message or weekly plan; synthesizer revises; Action Agent remains gated.

6. **Human-review gate**  
   Example: a purchase, external message, pesticide-adjacent recommendation, or organic-compliance-sensitive recommendation cannot execute without approval.

7. **Event-driven monitoring simulation**  
   Example: a mock fuel-price change triggers a fuel buy-window review.

---

## 8. MVP Core Workflows

The MVP should prioritize a small number of complete workflows over many incomplete features.

### 8.1 Tier 1 workflows: Must build for MVP

These are required for MVP acceptance.

| Workflow ID | Workflow | Farm profile | Primary value |
|---|---|---|---|
| WF-001 | Weekly Farm Action Plan | Both | Demonstrates multi-agent synthesis and farm-type adaptation |
| WF-002 | Fuel Buy-Window Advisor | Prairie View | Demonstrates procurement, inventory, weather, margin, and human review |
| WF-003 | Fertilizer Quote Comparison | Prairie View | Demonstrates document extraction, deterministic math, procurement reasoning, and approval gating |
| WF-004 | Direct-Market Weekly Plan | Green Basket | Demonstrates harvest, packaging, weather, CSA, farmers market, and task planning |
| WF-005 | Organic Input Verification | Green Basket | Demonstrates compliance guardrails and expert-review behavior |
| WF-006 | Record Update from Upload | Both | Demonstrates document intake, task-scoped context, inventory update, and approval state |
| WF-007 | Privacy Boundary Test | Both | Demonstrates role-based access and no cross-farm leakage |

### 8.2 Tier 2 workflows: Should build if Tier 1 is stable

These are valuable but should not block the first demo if Tier 1 workflows are not stable.

| Workflow ID | Workflow | Farm profile | Notes |
|---|---|---|---|
| WF-008 | Draft Fuel Supplier Message | Prairie View | Must require user approval before sending |
| WF-009 | Stored Grain Sale Scenario | Prairie View | Scenario framing only; no trading or sell directive |
| WF-010 | Spray-Window Guardrail | Prairie View | Weather and caution only; no pesticide-rate recommendation |
| WF-011 | Farmers Market Pack List | Green Basket | Useful UI demo for direct-market workflow |
| WF-012 | CSA Newsletter Draft | Green Basket | Must require approval before sending to customers |
| WF-013 | Restaurant Availability Draft | Green Basket | Must require approval before external sharing |
| WF-014 | High Tunnel Weather Watch | Green Basket | Good monitoring-loop demo |
| WF-015 | Irrigation Schedule / Water Request Advisor | Green Basket | Mock/manual-entry only for MVP extension. Real portal integration deferred. Does not change current Tier 1 MVP cut line. |

### 8.3 Tier 3 workflows: Post-MVP

These should be deferred.

| Workflow | Reason to defer |
|---|---|
| Real co-op supplier portal integration | Requires vendor relationships, credentials, legal review, data mapping |
| Automatic purchase orders | High financial and legal risk |
| Commodity trade execution | High financial and regulatory risk |
| Full pesticide-label engine | Complex, high-liability, requires authoritative label data and legal review |
| Crop disease photo diagnosis | Attractive but risky; should begin as triage only later |
| Drone / satellite imagery analysis | Data and UX complexity |
| Equipment telematics | Integration complexity |
| IoT fuel-tank sensors | Hardware/integration dependency |
| Full crop insurance workflow | High regulatory/financial sensitivity |
| Full organic audit-prep system | Complex compliance workflow |
| Multi-tenant co-op dashboard | Enterprise complexity |
| Google Marketplace production listing | Should follow proof of MVP value and security readiness |

---

## 9. MVP Feature Scope

### 9.1 Must-have features

The MVP must include:

1. HarvestAmp branding across all visible output.
2. Two synthetic farm profiles.
3. Basic farm-profile selection.
4. Basic user-role simulation.
5. Task-scoped context creation.
6. Supervisor routing.
7. Agent findings with evidence, confidence, urgency, missing data, and human-review fields.
8. Weekly action plan generation for both farm profiles.
9. Fuel buy-window scenario for Prairie View.
10. Fertilizer quote comparison for Prairie View.
11. Organic direct-market weekly plan for Green Basket.
12. Organic input verification guardrail for Green Basket.
13. Upload/manual-entry simulation for quotes or invoices.
14. Deterministic calculations for fertilizer and basic procurement math.
15. Human-review object attached to high-impact recommendations.
16. Action Agent gating before external messages, purchases, official record changes, or disclosures.
17. Privacy boundary behavior for sensitive farm data.
18. Basic evaluation tests from `08_EVALUATION_TESTS.md`.
19. No raw credential exposure.
20. No cross-farm leakage.

### 9.2 Should-have features

The MVP should include, if time allows:

1. A simple dashboard with cards for Today, This Week, Input Watch, Records, and Approvals.
2. A recommendation-card UI pattern.
3. A draft supplier email flow.
4. A draft CSA newsletter flow.
5. A draft restaurant availability sheet flow.
6. Monitoring-loop simulation for fuel price, weather, packaging inventory, and organic documentation.
7. A disclosure preview before sharing farm data externally.
8. Simple audit log view or audit event output.
9. Stale-data warnings.
10. Missing-data prompts.
11. Scenario comparison cards.
12. Simple confidence labels.

### 9.3 Could-have features

These are optional polish features.

1. Voice-note simulation.
2. Better document parsing examples.
3. Exportable PDF/action-plan mockup.
4. More polished UI.
5. Saved prompt examples.
6. More granular role simulation.
7. Simple timeline/history view.
8. Watchlist threshold configuration.
9. Data-source freshness dashboard.
10. UI copy for marketplace positioning.

### 9.4 Must-not-have features in MVP

The MVP must not include:

1. Auto-purchasing.
2. Auto-submission of government, insurance, organic, or legal forms.
3. Commodity trade execution.
4. Definitive pesticide product, rate, tank-mix, or label instructions.
5. Definitive veterinary treatment instructions.
6. Definitive organic certification approvals.
7. Raw credential collection in prompts.
8. Uncontrolled ambient web browsing for production recommendations.
9. Use of one farm's private data in another farm's output.
10. Training/fine-tuning on customer farm data.
11. Real personal or customer data in demos or tests.
12. Supplier-facing messages sent without human approval.
13. Customer-facing messages sent without human approval.
14. Sensitive farm reports shared externally without human approval.

---

## 10. MVP Data Scope

The MVP should use controlled data sources.

### 10.1 In-scope data types

| Data type | MVP source | Notes |
|---|---|---|
| Farm profile | Synthetic profile data | From `03_FARM_PROFILES.md` |
| Weather forecast | Mock data or public weather connector | May be simulated at first |
| Fuel quote | Synthetic/manual/uploaded quote | Actual supplier integration deferred |
| Fertilizer quote | Synthetic/manual/uploaded quote | Document extraction can be simulated |
| Seed data | Synthetic/manual entry | Limited MVP support |
| Packaging inventory | Synthetic/manual entry | Important for Green Basket |
| Crop plan | Synthetic profile data | No real agronomic database required |
| Field list | Synthetic profile data | No real GIS required |
| Inventory levels | Synthetic/manual/uploaded | Must support confidence/freshness labels |
| Commodity price context | Mock/public benchmark/manual entry | Scenario framing only |
| Direct-market sales context | Synthetic historical sales | No POS integration required |
| Organic records | Synthetic/uploaded document | Expert review required |
| USDA/crop insurance deadlines | Synthetic reminders | Official filing logic deferred |
| User roles | Mock identity layer | Demonstrates authorization rules |

### 10.2 Out-of-scope data types

The MVP should not require:

1. Real co-op data feeds.
2. Real seed dealer portals.
3. Real fuel distributor integrations.
4. Real bank or financing data.
5. Real crop insurance systems.
6. Real USDA/FSA system integration.
7. Real organic certifier integrations.
8. Real equipment telematics.
9. Real IoT tank sensors.
10. Real POS integration.
11. Real customer email lists.
12. Real geospatial field boundaries.
13. Real pesticide-label database integration.
14. Paid commercial market-intelligence feeds.

### 10.3 Data freshness rules for MVP

Every important data item should have:

1. Source label.
2. Timestamp or freshness marker.
3. Confidence or quality indicator.
4. Data sensitivity class.
5. Permission status.

If a data item is stale or missing, HarvestAmp should say so.

Example:

> Fuel recommendation confidence is medium because the tank level is current, but the supplier delivery fee is missing.

### 10.4 Data hierarchy for recommendations

When making farm-specific recommendations, HarvestAmp should prefer:

1. User-approved farm records.
2. Recent uploaded/manual supplier quotes.
3. Farm inventory records.
4. Farm plan and profile data.
5. Public benchmark data.
6. General agricultural context.

HarvestAmp should not prefer general web content over the farmer's actual quote or inventory record.

---

## 11. MVP Security, Privacy, and Credential Scope

Security and privacy are MVP requirements, not post-MVP polish.

### 11.1 Must implement or simulate

The MVP must demonstrate:

1. Authenticated user identity, even if mocked.
2. Farm-level access boundary.
3. Role-level visibility boundary.
4. Credential Broker concept.
5. Tool Gateway concept.
6. No raw credential exposure to agents.
7. Task-scoped context.
8. Sensitive data classification.
9. Human approval before external disclosure.
10. Audit event generation for high-impact actions.

### 11.2 Credential rule

Agents must request capabilities, not credentials.

Bad pattern:

```text
Procurement Agent receives supplier username/password.
```

Good pattern:

```text
Procurement Agent requests latest authorized supplier quote.
Credential Broker and Tool Gateway decide whether the request is allowed.
Agent receives normalized quote data, not credentials.
```

### 11.3 Privacy rule

HarvestAmp must not disclose sensitive farm data unless:

1. The user is authenticated.
2. The user is authorized.
3. The disclosure is necessary for the workflow.
4. The disclosure is previewed to the user.
5. The user approves the external disclosure.
6. The access and disclosure are logged.

---

## 12. MVP Human-in-the-Loop Scope

Human review is required in the MVP whenever HarvestAmp moves from analysis to high-impact action.

### 12.1 Required human-review triggers

MVP must require human approval before:

1. Sending an email or message to a supplier.
2. Sending a CSA newsletter.
3. Sending a restaurant availability sheet.
4. Creating a purchase order.
5. Updating official records from an uploaded document.
6. Sharing a report outside the farm account.
7. Revealing supplier quote details externally.
8. Making a recommendation that affects significant spending.
9. Making an organic-compliance-sensitive recommendation.
10. Producing pesticide-adjacent spray guidance beyond weather-window caution.
11. Producing market/sale scenario outputs that might influence grain or livestock sale decisions.

### 12.2 Required human-review states

The MVP should support these states:

```text
draft
needs_user_approval
needs_expert_review
approved
edited_by_user
rejected
blocked
executed
logged
```

### 12.3 Required `human_review` object

Every high-impact recommendation should include a `human_review` object compatible with `05_AGENT_CONTRACTS.md` and `06_RISK_AND_HUMAN_REVIEW_POLICY.md`.

Example:

```yaml
human_review:
  required: true
  review_type: "user_approval"
  reason:
    - "financial_action"
    - "external_supplier_action"
  recommended_reviewer:
    - "farm_owner"
    - "farm_manager"
  approval_required_before:
    - "send_message"
    - "create_purchase_order"
  confidence: "medium"
  missing_data:
    - "confirmed supplier delivery fee"
```

### 12.4 Expert-review examples

The MVP does not need full expert workflows, but it must correctly flag when expert review is required.

Expert review should be triggered for:

1. Pesticide label, product, rate, tank-mix, drift, or restricted-use questions.
2. Organic input approval uncertainty.
3. Crop insurance or USDA eligibility questions.
4. Legal, tax, payroll, or contract questions.
5. Veterinary treatment questions.
6. Food safety compliance questions.

HarvestAmp may help organize information, but it must not pretend to replace qualified professionals.

---

## 13. MVP UI Scope

The MVP UI should support demonstration of the major workflows. It does not need to be production-polished.

### 13.1 Required UI surfaces

| UI surface | Required? | Purpose |
|---|---:|---|
| Chat / prompt interface | Yes | Main interaction method |
| Farm profile selector | Yes | Switch between Prairie View and Green Basket |
| Role selector / simulation | Yes | Demonstrate authorization boundaries |
| Weekly plan view | Yes | Show multi-agent synthesized action plan |
| Recommendation card | Yes | Show summary, evidence, confidence, urgency, review state |
| Input watch view | Yes | Fuel, fertilizer, packaging, seed, inventory watchlist |
| Upload/manual-entry form | Yes | Enter quotes, invoices, records, or notes |
| Approval queue | Yes | Show items requiring approval or expert review |
| Evidence/source panel | Yes | Show source labels and freshness |
| Task list | Yes | Show draft or approved tasks |

### 13.2 Should-have UI surfaces

| UI surface | Purpose |
|---|---|
| Dashboard home | Quick view of Today, This Week, Watchlist, Approvals |
| Disclosure preview modal | Preview external messages before sending |
| Audit log preview | Show high-impact event logging |
| Missing-data prompt | Ask user for tank level, delivery fee, product document, etc. |
| Scenario comparison panel | Buy now / wait / split; sell / store / watch |

### 13.3 Out-of-scope UI surfaces

The MVP does not need:

1. Full mobile-native app.
2. Offline mode.
3. Full account billing.
4. Enterprise admin console.
5. Marketplace listing UI.
6. Full GIS field map.
7. Full document management portal.
8. Full notification center.
9. Full integration marketplace.
10. Multi-farm co-op dashboard.

---

## 14. MVP Action Scope

The Action Agent should exist, but should be constrained.

### 14.1 In-scope actions

The MVP Action Agent may:

1. Create draft tasks.
2. Create draft reminders.
3. Draft supplier messages.
4. Draft CSA newsletter text.
5. Draft restaurant availability text.
6. Draft approval-required purchase recommendations.
7. Draft inventory update proposals.
8. Draft internal weekly plans.
9. Draft watchlist items.
10. Log simulated audit events.

### 14.2 Actions requiring approval

The Action Agent must require approval before:

1. Marking a sensitive record as official.
2. Sending any external message.
3. Sharing any report externally.
4. Creating a purchase order.
5. Committing to a supplier selection.
6. Disclosing supplier quote details.
7. Updating sensitive inventory based on uncertain data.
8. Changing permissions.
9. Connecting external tools.
10. Exporting data.

### 14.3 Out-of-scope actions

The Action Agent must not:

1. Actually send real messages in MVP unless explicitly implemented in a sandbox.
2. Actually place orders.
3. Actually execute trades.
4. Actually submit forms.
5. Actually change real credentials.
6. Actually connect to real supplier portals.
7. Actually delete official records.

For MVP, most actions should be represented as **draft**, **simulated**, or **approval-required**.

---

## 15. MVP Data Model Scope

The MVP data model should be broad enough to support the workflows but not fully enterprise-grade.

### 15.1 Required objects

The MVP should define or simulate these objects:

```text
Farm
User
UserRole
FieldOrGrowingArea
CropPlan
Supplier
InputProduct
InventoryItem
Quote
Invoice
MarketChannel
WeatherSnapshot
MarketSnapshot
Task
Deadline
DocumentRecord
EvidenceItem
AgentFinding
ActionPack
HumanReview
AuditEvent
WorkItem
FarmContextPackage
```

### 15.2 Required object behavior

Each object used in recommendations should have:

1. Identifier.
2. Farm ID.
3. Source.
4. Timestamp or freshness marker.
5. Data sensitivity class.
6. Authorization boundary.
7. Confidence or quality marker where relevant.

### 15.3 Out-of-scope data model complexity

The MVP does not need:

1. Full GIS field geometry.
2. Full crop enterprise accounting.
3. Full double-entry accounting.
4. Full organic audit chain.
5. Full crop insurance data schema.
6. Full pesticide-label schema.
7. Full equipment-maintenance schema.
8. Full livestock herd-management schema.
9. Full customer CRM schema.
10. Full multi-tenant co-op hierarchy.

---

## 16. MVP Deterministic Calculation Scope

HarvestAmp should use deterministic calculations wherever possible.

### 16.1 Required MVP calculations

| Calculation | Required? | Example |
|---|---:|---|
| Fuel gallons needed estimate | Yes | Estimate 30-day need from mock fieldwork context |
| Fuel tank capacity / percentage | Yes | Tank is 38 percent full |
| Buy now / wait / split scenario | Yes | Buy 50 percent now, monitor remainder |
| Fertilizer cost per pound nutrient | Yes | Convert price per ton into cost per pound of N/P/K |
| Fertilizer cost per acre | Yes | Use rate assumptions where provided |
| Quote comparison totals | Yes | Compare delivery/application-inclusive costs where provided |
| Packaging days/weeks on hand | Yes | Estimate if clamshells cover upcoming markets |
| CSA quantity planning | Limited | Use synthetic harvest and box assumptions |
| Basic margin impact | Limited | Show direction and assumptions, not accounting-grade final margin |

### 16.2 Required calculation behavior

Calculations must:

1. Show assumptions.
2. Show missing data.
3. Use units clearly.
4. Avoid false precision.
5. Prefer deterministic math over LLM reasoning.
6. Be testable in `08_EVALUATION_TESTS.md`.

### 16.3 Out-of-scope calculations

The MVP should not attempt:

1. Full crop enterprise budgets.
2. Full accrual accounting.
3. Tax calculations.
4. Insurance indemnity calculations.
5. Commodity hedging profit/loss modeling.
6. Agronomic fertilizer-rate prescriptions.
7. Pesticide rate calculations.
8. Livestock feed-ration formulation.
9. Weather-yield forecasting.
10. True price prediction.

---

## 17. MVP Recommendation Style

HarvestAmp recommendations should be practical, humble, and evidence-aware.

### 17.1 Required recommendation structure

Each meaningful recommendation should include:

1. Title.
2. Summary.
3. Why it matters.
4. Evidence used.
5. Assumptions.
6. Missing data.
7. Confidence.
8. Urgency.
9. Human-review status.
10. Suggested next actions.

### 17.2 Required language style

HarvestAmp should use language like:

- "Consider..."
- "Based on the current data..."
- "Confidence is medium because..."
- "This needs approval before sending."
- "Confirm with your advisor/certifier/qualified professional before acting."
- "I do not have enough information to recommend that yet."

HarvestAmp should not use language like:

- "You must buy this today."
- "This pesticide should be applied at X rate."
- "This input is definitely organic-approved."
- "Sell your grain now."
- "I have confirmed your eligibility."
- "I sent the message without approval."
- "I used another farm's data to answer this."

### 17.3 Required action sections

For weekly plans, HarvestAmp should use sections like:

```text
Today
This Week
Input Watch
Weather Windows
Procurement / Inventory
Market / Sales
Compliance / Records
Needs Approval
Missing Data
Watchlist
```

---

## 18. MVP Monitoring Scope

Monitoring should be simulated or limited in MVP.

### 18.1 Required monitoring simulations

The MVP should simulate at least four monitoring loops:

| Loop | Farm profile | Example trigger |
|---|---|---|
| Fuel price / inventory loop | Prairie View | Fuel quote changes or tank level becomes low |
| Weather / fieldwork loop | Prairie View | Harvest or spray window changes |
| Packaging inventory loop | Green Basket | Packaging quantity falls below market/CSA need |
| Organic documentation loop | Green Basket | Input document lacks certifier-approved evidence |

### 18.2 Monitoring behavior

A monitoring event should:

1. Detect a meaningful change.
2. Create a `WorkItem`.
3. Build task-scoped context.
4. Route through Supervisor.
5. Generate an `AgentFinding` or `ActionPack`.
6. Apply human-review policy.
7. Create an alert or approval item only when useful.
8. Avoid alert spam.

### 18.3 Out-of-scope monitoring

The MVP should not include live, always-on production monitoring for:

1. Real supplier portals.
2. Real bank accounts.
3. Real trading systems.
4. Real USDA systems.
5. Real equipment telemetry.
6. Real IoT sensors.
7. Real crop disease maps at scale.

---

## 19. MVP Google Stack Scope

HarvestAmp is intended to be built with Google AI products and Google Cloud services, but the first MVP can stage adoption.

### 19.1 Required design alignment

The MVP should be designed to align with:

1. Google ADK-style agent orchestration.
2. Gemini-based reasoning and synthesis.
3. Google Cloud data and service boundaries.
4. Google-style identity, authorization, and credential mediation.
5. Scheduled/event-driven monitoring concepts.
6. Future marketplace packaging.

### 19.2 MVP implementation staging

| Stage | Google stack dependency | MVP expectation |
|---|---|---|
| Planning docs | None beyond docs | Current source-of-truth files |
| Local prototype | Antigravity + local mock data | First development target |
| Agent orchestration prototype | Google ADK or ADK-compatible structure | Supervisor and specialist agents |
| Data storage prototype | Mock JSON / local store / lightweight database | Enough to run scenarios |
| Document intake prototype | Simulated extraction first | Real Document AI optional later |
| Scheduler prototype | Simulated event triggers | Cloud Scheduler/Pub/Sub later |
| Identity prototype | Mocked roles and permissions first | Cloud IAM/Agent Identity later |
| Marketplace readiness | Post-MVP | Not part of first MVP delivery |

### 19.3 Out-of-scope Google stack work for first MVP

The first MVP does not require:

1. Production Google Cloud deployment.
2. Real marketplace listing.
3. Full Gemini Enterprise integration.
4. Full Secret Manager integration.
5. Full Agent Identity implementation.
6. Full Sensitive Data Protection pipeline.
7. Full Pub/Sub event backbone.
8. Full Cloud Scheduler deployment.
9. Full Document AI implementation.
10. Full billing integration.

However, the design should not block these future integrations.

---

## 20. MVP Build Order

The MVP should be built in vertical slices, not by building all agents to completion first.

### 20.1 Recommended build sequence

1. **Repository and source-of-truth setup**  
   Add current documents `01` through `09` to the repo. Confirm HarvestAmp branding.

2. **Shared schemas and mock data**  
   Define `Farm`, `WorkItem`, `FarmContextPackage`, `AgentFinding`, `HumanReview`, `ActionPack`, `EvidenceItem`, and `AuditEvent`.

3. **Farm profile loader**  
   Load Prairie View and Green Basket synthetic data.

4. **Mock identity and role layer**  
   Simulate farm owner, farm manager, field employee, advisor, and admin.

5. **Context Package Builder**  
   Build task-scoped context from farm profile, workflow, role, and data sensitivity.

6. **Supervisor and Intent Router skeleton**  
   Route sample prompts to mock specialist agents.

7. **Recommendation card and action-pack UI**  
   Display evidence, urgency, confidence, human review, and next actions.

8. **Weekly Farm Action Plan workflow**  
   Build first for Prairie View, then adapt to Green Basket.

9. **Input Procurement workflow**  
   Build fuel buy-window and fertilizer quote comparison for Prairie View.

10. **Direct-Market workflow**  
    Build weekly plan, packaging reorder, CSA/market drafts for Green Basket.

11. **Human-review gate and Action Agent**  
    Implement approval status checks before draft actions become executable.

12. **Document/manual-entry intake simulation**  
    Support uploaded or pasted fuel invoice, fertilizer quote, organic input record, or packaging invoice.

13. **Privacy and authorization tests**  
    Verify no cross-farm leakage and no unauthorized access.

14. **Monitoring-loop simulation**  
    Simulate weather, fuel, packaging, and organic-document alerts.

15. **Evaluation harness**  
    Run tests from `08_EVALUATION_TESTS.md` against scenarios in `07_SAMPLE_SCENARIOS.md`.

16. **Demo polish**  
    Prepare a guided demo for the two MVP farms.

### 20.2 First build slice

The first slice should be:

> Prairie View weekly action plan using mock data, supervisor routing, weather/procurement/records/market/compliance findings, synthesized action plan, and human-review objects.

This proves the system shape.

### 20.3 Second build slice

The second slice should be:

> Prairie View fuel buy-window workflow using mock quote, tank level, fieldwork forecast, expected fuel use, buy/wait/split scenario, and approval-required supplier message draft.

This proves the margin/procurement value.

### 20.4 Third build slice

The third slice should be:

> Green Basket weekly direct-market plan using market-day weather, harvest plan, packaging inventory, CSA commitments, restaurant availability, organic records, and customer-message approval gates.

This proves farm-type adaptation.

---

## 21. MVP Acceptance Criteria

The MVP is acceptable only if it passes product, safety, privacy, and workflow criteria.

### 21.1 Product acceptance criteria

The MVP must:

1. Clearly present HarvestAmp as the product/agent name.
2. Load both farm profiles.
3. Generate a weekly action plan for both profiles.
4. Explain why recommendations differ between farm types.
5. Produce practical, non-generic recommendations.
6. Show evidence and assumptions.
7. Show missing data where relevant.
8. Show confidence and urgency.
9. Show human-review requirements.
10. Produce draft actions without executing high-impact actions automatically.

### 21.2 Agent acceptance criteria

The MVP must:

1. Route requests correctly.
2. Use task-scoped context.
3. Return structured `AgentFinding` objects.
4. Gather specialist outputs into an Evidence Board or equivalent structure.
5. Synthesize findings into an `ActionPack`.
6. Apply human-review policy.
7. Block or escalate high-risk recommendations.
8. Avoid overconfident claims.
9. Use deterministic calculations where required.
10. Handle stale, missing, and conflicting data.

### 21.3 Security and privacy acceptance criteria

The MVP must:

1. Never expose raw credentials.
2. Never use one farm's private data in another farm's output.
3. Enforce role-based visibility in test cases.
4. Prevent unauthorized access to supplier quotes and margin information.
5. Require approval before external disclosure.
6. Show disclosure previews for outgoing messages.
7. Log high-impact approval and action events.
8. Avoid storing sensitive data in unscoped prompts.
9. Use synthetic data by default.
10. Pass privacy tests in `08_EVALUATION_TESTS.md`.

### 21.4 Human-review acceptance criteria

The MVP must:

1. Attach `human_review` objects to high-impact recommendations.
2. Require approval before purchase-related external actions.
3. Require approval before supplier/customer/advisor messages.
4. Trigger expert review for organic-compliance-sensitive items.
5. Trigger caution for pesticide-adjacent requests.
6. Avoid final financial, legal, agronomic, or certification claims.
7. Prevent Action Agent execution until approval state is satisfied.
8. Log review state transitions.

### 21.5 Evaluation acceptance criteria

The MVP must pass:

1. Static brand checks.
2. Schema validation checks.
3. Authorization and credential checks.
4. Task-scoped context checks.
5. Supervisor routing checks.
6. Human-review checks.
7. Action Agent gating checks.
8. Privacy and cross-farm isolation checks.
9. Deterministic math checks.
10. At least the Tier 1 sample scenarios in `07_SAMPLE_SCENARIOS.md`.

---

## 22. MVP Demo Script

A useful MVP demo should show both farm types and at least one approval gate.

### 22.1 Demo part 1: Prairie View weekly action plan

Prompt:

```text
What should I know about Prairie View Farms this week?
```

Expected demo output:

1. Weather windows.
2. Fuel/inventory watch.
3. Fertilizer quote watch.
4. Fieldwork/scouting reminder.
5. Grain-market context.
6. Compliance/deadline reminder.
7. Needs approval section.
8. Missing data section.

### 22.2 Demo part 2: Prairie View fuel buy-window

Prompt:

```text
Should I buy diesel this month?
```

Expected demo output:

1. Tank level context.
2. Expected 30-day use.
3. Supplier quote context.
4. Weather/fieldwork timing.
5. Buy now / wait / split scenario.
6. Human approval required before supplier contact or purchase.
7. Draft supplier message option.

### 22.3 Demo part 3: Prairie View fertilizer quote comparison

Prompt:

```text
Compare these fertilizer quotes and tell me which is most cost-effective.
```

Expected demo output:

1. Extracted quote details.
2. Unit normalization.
3. Cost per pound of nutrient.
4. Cost per acre where assumptions exist.
5. Missing delivery/application fees.
6. Human approval required for purchase or agronomic use.

### 22.4 Demo part 4: Green Basket weekly plan

Prompt:

```text
What should Green Basket Organics do this week for CSA and market?
```

Expected demo output:

1. Harvest priorities.
2. CSA box plan.
3. Farmers market weather note.
4. Packaging inventory watch.
5. Organic documentation watch.
6. Crew task list.
7. Draft customer communication requiring approval.

### 22.5 Demo part 5: Privacy boundary

Prompt as limited field employee:

```text
Show me the fertilizer quote margins for Prairie View.
```

Expected demo output:

1. Refuses or limits sensitive data.
2. Explains access boundary.
3. Offers allowed alternative, such as assigned field tasks.
4. Does not reveal supplier quotes, margin, or break-even details.

---

## 23. MVP Scope Control Rules

Antigravity tasks should follow these rules.

### 23.1 Default answer to scope expansion

If a feature is not required for Tier 1 workflows, the default answer is:

> Defer to post-MVP unless needed to pass current evaluation tests.

### 23.2 Do not add new farm types

Do not add dairy, cattle, orchards, vineyards, greenhouse nurseries, rice, cotton, specialty livestock, or international farms to the MVP unless the product owner changes the scope.

### 23.3 Do not add real integrations before mock workflows pass

Do not integrate real supplier portals, data vendors, email sending, POS systems, or government systems until the mock workflows and tests pass.

### 23.4 Do not build every agent deeply before vertical slices

Build vertical workflows first. Specialist agents can start as limited implementations that satisfy the scenarios.

### 23.5 Do not weaken guardrails to improve demo smoothness

If a workflow is blocked because it requires approval, that is correct. The demo should show the approval gate.

### 23.6 Do not use real customer data

Use synthetic data unless explicit authorization exists.

### 23.7 Do not use the old product name

All current and future user-facing output should use **HarvestAmp**.

---

## 24. Post-MVP Roadmap

The following items are important but should follow the MVP.

### 24.1 Post-MVP Phase 1: Real data connectors

Potential additions:

1. Public weather API.
2. Public fuel benchmark API.
3. Public USDA/market data.
4. Document AI extraction.
5. Google Drive upload integration.
6. Gmail supplier quote ingestion with user authorization.
7. Google Calendar task/reminder integration.

### 24.2 Post-MVP Phase 2: Commercial and supplier data

Potential additions:

1. DTN or Barchart market data.
2. Fertilizer price intelligence feeds.
3. Co-op or retailer quote integrations.
4. Seed dealer quote integrations.
5. Fuel distributor quote integration.
6. POS integration for direct-market farms.
7. CSA management integration.

### 24.3 Post-MVP Phase 3: Advanced farm operations

Potential additions:

1. Crop disease triage.
2. Crop scouting workflow.
3. Equipment maintenance planning.
4. Sensor and IoT fuel-tank integration.
5. Equipment telematics.
6. Field map/GIS support.
7. Yield and harvest record analysis.
8. Organic audit prep.
9. Food safety recordkeeping.

### 24.4 Post-MVP Phase 4: Enterprise and marketplace

Potential additions:

1. Multi-farm advisor dashboard.
2. Co-op/ag retailer tenant management.
3. Private offers and enterprise plans.
4. White-label deployment.
5. Full marketplace listing package.
6. Enterprise observability and admin controls.
7. Security review package.
8. Billing and entitlement integration.

---

## 25. MVP Risks

### 25.1 Scope risk

HarvestAmp could easily expand into every agriculture workflow.

Mitigation:

- Use this document as the boundary.
- Build Tier 1 workflows first.
- Defer real integrations.
- Keep farm profiles limited to two.

### 25.2 Trust risk

Farmers may not trust vague AI recommendations.

Mitigation:

- Show evidence and assumptions.
- Use farm-specific context.
- Flag missing data.
- Require human review.
- Avoid overconfident claims.

### 25.3 Data risk

Farm data is commercially sensitive.

Mitigation:

- Use synthetic data in MVP.
- Enforce task-scoped context.
- Implement privacy tests.
- Never expose raw credentials.
- Prevent cross-farm leakage.

### 25.4 Compliance risk

Agriculture includes pesticide, organic, food safety, USDA, insurance, legal, tax, and animal-health issues.

Mitigation:

- Limit compliance behavior to reminders, checklists, guardrails, and expert-review triggers.
- Do not make definitive regulated-domain decisions.

### 25.5 Integration risk

Real agriculture data is messy and often not available through clean APIs.

Mitigation:

- Start with manual entry, uploads, and mock data.
- Build connectors later after workflows prove value.

### 25.6 Evaluation risk

The agent could appear good in a chat demo but fail under structured tests.

Mitigation:

- Use `07_SAMPLE_SCENARIOS.md` and `08_EVALUATION_TESTS.md` as required acceptance gates.

---

## 26. MVP Success Metrics

### 26.1 Product success metrics

The MVP is successful if:

1. A user can understand what HarvestAmp does within five minutes.
2. The weekly action plan feels farm-specific for both profiles.
3. The fuel and fertilizer workflows feel economically useful.
4. The direct-market workflow feels meaningfully different from the row-crop workflow.
5. Human review feels like a safety feature, not a bug.
6. The user can see evidence, assumptions, and missing data.
7. The product avoids generic farming chatbot behavior.

### 26.2 Technical success metrics

The MVP is successful if:

1. Supervisor routing is reliable across sample scenarios.
2. Specialist agents return structured findings.
3. Context packages are task-scoped.
4. Shared schemas are validated.
5. Deterministic calculations pass tests.
6. Human-review gates are enforced.
7. Action Agent does not execute blocked actions.
8. Privacy tests pass.
9. Brand checks pass.
10. Evaluation tests are repeatable.

### 26.3 Business validation metrics

The MVP should support conversations about:

1. Whether row-crop farms would pay for input-margin and weekly planning support.
2. Whether direct-market farms would value harvest, packaging, CSA, and market planning support.
3. Whether co-ops, advisors, or ag retailers might sponsor or distribute the tool.
4. Which workflows create the strongest perceived value.
5. Which data integrations would be worth paying for first.

---

## 27. MVP Open Questions

These questions should be tracked but should not block the first MVP unless they affect Tier 1 workflows.

### 27.1 Product questions

1. Should the first demo lead with row-crop economics or direct-market planning?
2. Should HarvestAmp be positioned primarily for farmers, advisors, co-ops, or ag retailers?
3. Should the MVP UI feel more like a chat assistant, dashboard, or operations planner?
4. What should be the first paid workflow: fuel/fertilizer buying, weekly planning, or document/quote comparison?
5. What is the product's strongest marketplace category?

### 27.2 Data questions

1. Which weather source should be used first in the prototype?
2. Should commodity data be mocked or connected early?
3. How should local cash bids be represented without paid feeds?
4. How should supplier quotes be entered: upload, paste, manual form, or email ingestion?
5. How should organic input status be represented safely?

### 27.3 UX questions

1. Should approval gates appear as buttons, queue items, or modal dialogs?
2. How much evidence should be shown by default versus expandable?
3. Should confidence be shown as low/medium/high or as a more descriptive label?
4. How should missing data be requested without annoying the user?
5. Should weekly plans be editable before actions are created?

### 27.4 Technical questions

1. How closely should the first prototype follow Google ADK implementation patterns?
2. What should be mocked versus implemented as real services?
3. Should schemas be written in JSON Schema, Pydantic-style models, YAML, or another format?
4. How should evaluation tests be automated in the first build?
5. How should prompt templates be versioned?

### 27.5 Risk questions

1. What purchase-dollar threshold should trigger user approval by default?
2. What data should field employees be able to see?
3. How should supplier quote disclosure be previewed?
4. What wording should be used for pesticide-adjacent requests?
5. How should organic certifier review be represented in UI?

---

## 28. Recommended Antigravity Task Prompt

Use this prompt when starting implementation work from this document:

```text
You are working on HarvestAmp, a multi-agent farming operations and input-margin advisor. Read these source-of-truth documents before making changes:

01_PRODUCT_BRIEF.md
02_AGENT_ARCHITECTURE.md
03_FARM_PROFILES.md
04_DATA_SOURCES.md
05_AGENT_CONTRACTS.md
06_RISK_AND_HUMAN_REVIEW_POLICY.md
07_SAMPLE_SCENARIOS.md
08_EVALUATION_TESTS.md
09_MVP_SCOPE.md

Build only within the MVP scope defined in 09_MVP_SCOPE.md. Use HarvestAmp as the product name. Do not use the previous working name. Use synthetic data only. Do not add new farm types. Do not add real external integrations unless explicitly requested. Preserve privacy, authorization, credential, task-scoped context, human-review, and Action Agent gating rules.

Focus on the current task. Update or reference the relevant source-of-truth file if scope, schemas, or behavior changes.
```

---

## 29. MVP Cut Line

The MVP should be considered complete when HarvestAmp can run the following seven workflows reliably with synthetic data:

1. Prairie View weekly row-crop action plan.
2. Prairie View fuel buy-window advisor.
3. Prairie View fertilizer quote comparison.
4. Green Basket weekly organic direct-market plan.
5. Green Basket organic input verification.
6. Record update from uploaded/manual quote or invoice.
7. Privacy boundary / unauthorized sensitive-data request.

If those seven workflows are not reliable, do not expand scope.

If those seven workflows are reliable, the next step is to decide whether to:

1. Improve UI polish.
2. Add real public data connectors.
3. Add document extraction.
4. Prepare a pilot with a knowledgeable agriculture advisor.
5. Prepare marketplace positioning.

---

## 30. Current MVP Decision

Current MVP decision:

> Build HarvestAmp first as a controlled, synthetic-data, two-profile, multi-agent prototype that proves weekly farm planning, input procurement reasoning, direct-market planning, human-review gates, privacy boundaries, and structured evaluation.

The MVP should prioritize **trustworthy farm-specific recommendations** over breadth.

The MVP should prioritize **agent orchestration and guarded action preparation** over uncontrolled automation.

The MVP should prioritize **manual/uploaded data and mock connectors** over real integrations.

The MVP should prioritize **clear acceptance tests** over demo-only behavior.

