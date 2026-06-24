# 01_PRODUCT_BRIEF.md

# Product Brief: HarvestAmp

**Version:** 0.4  
**Date:** 2026-06-23  
**Status:** Corrected source-of-truth draft for MVP implementation planning  
**Product / agent name:** HarvestAmp  
**Related documents:**

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
- `CHANGELOG.md`
- `configs/human_review_rules.yaml`
- `schemas/*.schema.yaml`
- `fixtures/*.yaml`

**Intended build environment:** Google AI stack, including Antigravity for focused development tasks, Google ADK-style orchestration for agent workflows, Gemini / Vertex AI for reasoning and synthesis, Google Cloud services for data and infrastructure, and Google Cloud Marketplace / AI Agent Marketplace as a possible later distribution channel.

---

## 0. Revision Notes

### 0.4 Corrected implementation-ready brief

This version:

- Uses **HarvestAmp** consistently as the current product and agent name.
- Removes legacy product-name references from positioning and marketplace copy.
- Aligns the product brief with `DECISION_LOG.md`, `09_MVP_SCOPE.md`, and `10_BUILD_PLAN.md`.
- Clarifies that `configs/human_review_rules.yaml` is a separate machine-readable policy scaffold, not content embedded in the architecture document.
- Reinforces the first implementation path: schemas, fixtures, deterministic security/policy services, mock agents, and the first Weekly Farm Action Plan vertical slice before real integrations.

### 0.3 HarvestAmp rename

Updated the working product name to **HarvestAmp** across live source-of-truth documents. Archived snapshots may retain earlier naming for history only.

---

## 1. Product Name

**Product and agent name:** HarvestAmp

Use:

```text
HarvestAmp        # user-facing product and agent name
harvestamp        # lowercase internal package / project prefix
harvestamp-*      # internal connector, service, or tool prefixes
```

Do not use previous working names in user-facing copy, prompts, code names, UI labels, schemas, configs, marketplace copy, or tests.

---

## 2. One-Line Description

**HarvestAmp is a farm-specific AI agent that helps farmers and agricultural advisors decide what to do, what to buy, when to buy, and what to watch by combining farm profile data, weather, input prices, inventory, crop and livestock risk signals, market context, sales channels, records, and compliance reminders.**

---

## 3. Product Summary

Farmers make daily decisions that are local, time-sensitive, and financially important. A farmer may need to decide whether to spray, plant, harvest, irrigate, buy fuel, book fertilizer, order seed, prepare for a farmers market, update organic records, or sell grain. These decisions are affected by weather, supplier quotes, fuel prices, fertilizer prices, seed availability, inventory, crop stage, market prices, regulatory deadlines, field records, sales-channel obligations, and the farmer's risk tolerance.

HarvestAmp is a **multi-agent farm operations and input-margin advisor**. It turns fragmented farm data into clear, farm-specific action recommendations, while preserving evidence, source freshness, privacy boundaries, and human-review requirements.

The MVP focuses on two synthetic farm types:

1. **Large conventional row-crop farm**  
   Example: corn, soybean, wheat, or similar broadacre operation selling through commodity channels.

2. **Small certified organic / direct-market farm**  
   Example: diversified vegetables, herbs, flowers, fruit, or mixed production selling through CSA, farmers markets, farm stand, restaurant, local wholesale, or similar channels.

HarvestAmp should not behave like a generic farming chatbot. It should act as an operational decision-support system that understands the farm profile, uses trusted data, routes work to specialist agents, and helps the user prioritize action.

---

## 4. Product Vision

The product vision is to become the farmer's daily operating intelligence layer.

Ideal user experience:

> Tell me what matters on my farm this week: what work to do or delay, what inputs to buy or watch, which weather windows matter, what risks are rising, which deadlines I should not miss, and how decisions affect margin.

Longer-term, HarvestAmp could support row-crop farms, specialty crop farms, livestock farms, greenhouse and nursery operations, organic farms, direct-market farms, co-ops, crop consultants, ag retailers, farm management organizations, and advisor networks.

For the MVP, HarvestAmp must prove that one architecture can adapt intelligently to two very different farm profiles:

- A large, input-intensive commodity crop operation.
- A small, certified organic, direct-market operation.

---

## 5. Why HarvestAmp Should Exist

Farmers already use weather apps, commodity apps, spreadsheets, extension articles, co-op quotes, seed dealer emails, USDA sites, equipment records, POS systems, and paper notes. The problem is not lack of information. The problem is that information is fragmented, time-sensitive, local, and hard to convert into practical action.

HarvestAmp should help answer questions such as:

- What should I know about my farm this week?
- Should I plant, irrigate, fertilize, spray, harvest, deliver, or delay?
- Can I spray tomorrow morning?
- Should I buy diesel now, wait, or split the purchase?
- Which fertilizer quote is cheaper per usable nutrient?
- Am I short on seed, fertilizer, fuel, packaging, feed, parts, or market supplies?
- What should I scout this week?
- What weather risks affect my fields, high tunnels, animals, market day, CSA pickup, or delivery route?
- What does this input price change do to my break-even or market-week margin?
- What USDA, crop insurance, organic, food-safety, pesticide-label, or recordkeeping item needs attention?
- What should my crew do this week?
- What supplier message, customer note, task, reminder, or record update should be drafted for approval?

HarvestAmp should provide decision support, not just information display.

---

## 6. Target MVP Users

### 6.1 Primary MVP User 1: Large Row-Crop Operator

**Profile:**

- Operates hundreds to thousands of acres.
- Grows crops such as corn, soybeans, wheat, cotton, rice, sorghum, or similar broadacre crops.
- Buys significant quantities of fuel, fertilizer, seed, crop protection products, parts, and services.
- Sells through commodity channels such as elevators, processors, wholesalers, co-ops, or contracts.
- Cares about weather windows, fieldwork timing, basis, storage, input cost, break-even, crop progress, disease risk, and deadlines.

**Key pain points:**

- High input costs.
- Complex supplier quotes.
- Timing-sensitive fieldwork.
- Commodity price volatility.
- Need to protect margin per acre or per bushel.
- Many operational decisions during planting, spraying, side-dress, scouting, and harvest windows.

**Core value proposition:**

> Know what to do this week, when to work, what input prices matter, whether to buy fuel, fertilizer, or seed now or wait, and how decisions affect margin.

### 6.2 Primary MVP User 2: Small Organic / Direct-Market Farmer

**Profile:**

- Operates a smaller diversified farm.
- Grows vegetables, fruits, herbs, flowers, mushrooms, nursery plants, or mixed crops.
- May be certified organic, transitioning organic, or using organic/regenerative practices.
- Sells through farmers markets, CSA, farm stand, restaurant accounts, local wholesale, delivery, or online orders.
- Buys seed, transplants, compost, organic fertilizer, row cover, drip tape, soil media, packaging, clamshells, labels, market supplies, fuel, and small equipment.

**Key pain points:**

- Many crops and successions to manage.
- Labor and harvest planning complexity.
- Market-day weather risk.
- Packaging and supply shortages.
- Organic input documentation.
- Small margins and limited administrative time.
- Customer-facing channels require timely planning and communication.

**Core value proposition:**

> Plan harvests, market days, CSA boxes, input purchases, organic records, packaging inventory, weather risks, and weekly farm tasks from one assistant.

---

## 7. Buyers and Distribution Strategy

The strongest initial buyer may be a business or organization that serves many farms, even though the farmer remains the end user.

Potential buyers:

- Agricultural co-ops.
- Ag retailers.
- Crop consultants.
- Independent agronomists.
- Farm management companies.
- Large farm operators.
- Food hubs.
- Organic-service providers.
- Produce aggregators.
- Farm credit or agricultural finance organizations.
- Crop insurers or insurance agencies.
- Seed, fertilizer, fuel, or input suppliers seeking value-added digital services.

Potential distribution model:

- Google Cloud Marketplace / AI Agent Marketplace listing for enterprise buyers.
- Private offers for co-ops, consultants, ag retailers, and enterprise farm operators.
- Lightweight farmer-facing app experience layered on top of the agent service.

Marketplace readiness is **post-MVP**. The first MVP should prove product value and safety, not complete commercial packaging.

---

## 8. Product Positioning

### 8.1 What HarvestAmp Is

HarvestAmp is:

- A multi-agent farm operations advisor.
- A procurement and input-cost assistant.
- A weather-to-action decision-support tool.
- A margin and scenario-planning assistant.
- A records, task, inventory, and evidence assistant.
- A configurable farm-type-specific advisor.

### 8.2 What HarvestAmp Is Not

HarvestAmp is not:

- A generic farming chatbot.
- A replacement for an agronomist, veterinarian, crop insurance agent, accountant, attorney, organic certifier, food-safety expert, or licensed pesticide advisor.
- A fully autonomous chemical recommendation system.
- A guaranteed fuel, fertilizer, seed, crop, livestock, or commodity price forecasting system.
- A brokerage, hedging, or trading platform.
- A substitute for pesticide labels, regulatory requirements, or local expert review.
- A system that should freely browse the open web for production decisions.
- A system that should receive raw credentials inside LLM prompts or memory.

---

## 9. MVP Scope

### 9.1 MVP Farm Types

The MVP supports two synthetic profiles:

1. `PVF_ROW_CROP_001` - Prairie View Farms, a large conventional row-crop farm.
2. `GBO_DIRECT_001` - Green Basket Organics, a small certified organic direct-market farm.

### 9.2 MVP Core Workflows

#### Workflow 1: Weekly Farm Action Plan

User asks:

> What should I know about my farm this week?

The system produces:

- Top operational priorities.
- Weather windows and risks.
- Input purchase watchlist.
- Inventory concerns.
- Crop, fieldwork, market, or direct-market risks.
- Sales-channel tasks.
- Compliance or recordkeeping reminders.
- Missing data.
- Human-review flags.
- Approval-required draft actions.

This is the flagship MVP workflow because it validates the whole multi-agent system.

#### Workflow 2: Fuel Buy / Wait / Split Advisor

User asks:

> Should I buy diesel this month?

The system considers:

- Current supplier quote.
- Public benchmark trend, if available.
- Farm fuel inventory.
- Tank capacity.
- Expected fieldwork or delivery demand.
- Seasonality.
- Cash-flow preference if authorized.
- User risk tolerance.

The system recommends:

- Buy now.
- Wait and monitor.
- Split purchase.
- Ask for missing quote, tank, delivery, or inventory data.

The system must communicate uncertainty clearly and require approval before any supplier contact or purchase commitment.

#### Workflow 3: Fertilizer / Input Quote Comparison

User uploads or enters a quote and asks:

> Which fertilizer quote is better?

The system compares:

- Product type.
- Unit price.
- Delivery cost.
- Application cost.
- Nutrient content.
- Cost per acre when enough data exists.
- Cost per pound of actual nutrient.
- Timing and weather constraints.
- Existing inventory.
- Organic eligibility if relevant.

The system should highlight missing information and recommend human review where appropriate. It must separate arithmetic comparison from agronomic recommendation.

#### Workflow 4: Weather-to-Action Advisor

Example prompts:

> Can I spray tomorrow?  
> Can I plant this week?  
> Will the farmers market weather hurt sales?  
> Do I need to protect crops from frost?

The system considers:

- Forecast conditions.
- Wind, rain, temperature, frost, heat, humidity, storms, soil wetness, and drying windows.
- Farm type.
- Crop stage or planned task if known.
- Pesticide-label and compliance guardrails when relevant.

The system provides:

- Recommended work-window framing.
- Risk explanation.
- Confidence level.
- Missing data.
- Human/expert review flag when needed.

#### Workflow 5: Inventory and Supply Watch

User asks:

> Am I short on anything for the next two weeks?

The system checks:

- Fuel.
- Seed.
- Fertilizer.
- Crop protection or organic inputs.
- Packaging.
- Market supplies.
- Parts and maintenance supplies.
- Upcoming farm activities.

For row-crop farms, focus on fuel, fertilizer, seed, crop protection, parts, and seasonal fieldwork.

For small organic/direct-market farms, focus on seed, transplants, compost, organic fertilizer, packaging, labels, bags, clamshells, ice, crates, market supplies, and harvest planning.

#### Workflow 6: Direct-Market Weekly Plan

For small organic/direct-market farms, user asks:

> Help me plan this week's market or CSA.

The system considers:

- Crop availability.
- Harvest windows.
- Weather forecast.
- Packaging inventory.
- Customer orders or commitments.
- CSA commitments.
- Market-day weather.
- Organic and food-safety record reminders.
- Labor constraints if entered.

The system produces:

- Harvest list.
- Packing list.
- Market supplies checklist.
- CSA box suggestions.
- Weather risk notes.
- Low-inventory warnings.
- Customer or buyer communication drafts requiring approval.

#### Workflow 7: Recordkeeping and Task Logging

Example prompts:

> Log that I filled the diesel tank.  
> Log that I applied compost to Field 3.  
> Create a task to order clamshells.  
> Turn this note into a scouting report.

The system:

- Extracts structured data.
- Creates draft records.
- Updates inventory or official records only after required approval.
- Creates tasks or reminders when authorized.
- Flags missing required information.
- Routes compliance-sensitive records to review.

---

## 10. MVP Feature Set

### 10.1 Must-Have MVP Features

- Farm profile onboarding or synthetic fixture loading.
- Farm-type routing for two MVP profiles.
- Mock identity and role simulation.
- Supplier and input profile.
- Inventory tracking for key inputs.
- Manual data entry for fuel, fertilizer, seed, packaging, and other input prices.
- Upload/manual-entry simulation for quotes and invoices.
- Weather-to-action recommendations using mock or approved public data.
- Weekly Farm Action Plan.
- Fuel buy/wait/split recommendation.
- Fertilizer/input quote comparison.
- Direct-market planning mode.
- Human-review flagging.
- Evidence, source, timestamp, assumptions, confidence, and missing-data display.
- User approval before actions are taken.
- Memory or record update only after authorization and required approval.
- No raw credentials in prompts, logs, memory, fixtures, or model context.
- No cross-farm leakage.

### 10.2 Should-Have MVP Features

- Basic task list and reminders.
- Basic margin calculator.
- Saved supplier list.
- Saved price history.
- Exportable weekly report mockup.
- Voice-note input simulation for field records.
- Alerts for price changes, deadlines, weather risks, and low inventory.
- Disclosure preview before external messages.
- Audit-event preview for high-impact actions.

### 10.3 Later Features

- Gmail/Drive ingestion for supplier quotes and documents.
- Calendar integration.
- Co-op and supplier integrations.
- Tank sensor integration.
- Equipment telematics.
- Farm management software integrations.
- Crop disease photo triage.
- Advanced crop-stage modeling.
- Advanced commodity/basis strategy.
- Livestock mode.
- Greenhouse/nursery mode.
- Specialty crop wholesale mode.
- White-labeled co-op or advisor portal.
- Marketplace private-offer packaging.
- Multi-farm advisor dashboard.

---

## 11. Out of Scope for MVP

The MVP will not attempt to provide:

- Support for every crop type.
- Support for every country or regulatory environment.
- Fully autonomous purchasing.
- Guaranteed price forecasting.
- Pesticide application rates as final recommendations.
- Veterinary diagnosis or treatment.
- Legal, financial, insurance, tax, or accounting advice.
- Direct commodity trading execution.
- Input brokerage.
- Drone imagery analysis.
- Deep agronomic prescriptions without expert review.
- Full farm ERP replacement.
- Real supplier portal integrations.
- Real bank integrations.
- Real government or insurance filing.
- Uncontrolled open-web monitoring for production decisions.

---

## 12. Core Agent System Concept

HarvestAmp should use multiple specialist agents coordinated by a supervisor/orchestrator, with deterministic services enforcing security, authorization, data minimization, policy, and tool access.

### 12.1 Supervisor / Orchestrator Agent

Responsibilities:

- Classify user intent.
- Read task-scoped farm context and memory.
- Decide which specialist agents to invoke.
- Choose sequential, parallel, conditional, or loop workflow.
- Gather agent findings.
- Send findings to recommendation synthesis.
- Apply human-review policy.
- Return final ActionPack to the user.
- Update memory after user decisions where authorized.

### 12.2 Specialist Agents

Initial MVP agents:

1. **Farm Profile Agent** - collects and maintains farm type, crops, fields, suppliers, inputs, sales channels, inventory, organic status, and preferences.
2. **Weather + Fieldwork Agent** - converts weather conditions into work-window and risk recommendations.
3. **Input Procurement Agent** - handles fuel, fertilizer, seed, packaging, organic inputs, parts, quotes, buy/wait/split recommendations, and price monitoring.
4. **Records + Inventory Agent** - tracks field notes, inventory, purchases, invoices, tasks, tank levels, seed orders, packaging, and input usage.
5. **Market + Sales Agent** - supports commodity context for row-crop farms and direct-market planning for small farms.
6. **Compliance Agent** - flags USDA, organic, pesticide-label, food-safety, crop-insurance, veterinary, legal, tax, and recordkeeping risks.
7. **Margin + Scenario Agent** - converts costs and prices into practical scenarios such as cost per acre, cost per bushel, cost per market week, and buy-now/wait/split options.
8. **Recommendation Synthesizer** - converts specialist findings into farmer-friendly recommendations, action lists, alerts, and reports.
9. **Action Agent** - creates draft tasks, reminders, supplier-message drafts, reports, and inventory updates after approval.
10. **Document / Media Intake Agent** - extracts structured fields from uploaded documents or notes and creates draft records.

### 12.3 Deterministic Services

The following are not normal LLM agents:

- Credential Broker / Authorization Service.
- Tool Gateway.
- Context Package Builder.
- Audit Logger.
- Unit and nutrient calculators.
- Human-review policy checker.
- Role and permission checks.
- Source freshness checks.

---

## 13. Data Sources and Intake Strategy

HarvestAmp agents should not randomly browse the open web as their primary information source. The system should use approved data connectors, farm records, uploads, manual entries, and user-authorized integrations.

### 13.1 MVP Data Intake Sources

- Synthetic farm profiles and fixtures.
- User-entered farm profile.
- User-entered supplier quotes.
- Uploaded quote PDFs, invoices, documents, or extracted text.
- Manual inventory entries.
- Mock or approved weather data connector.
- Public benchmark data where available.
- Saved farm memory and previous user decisions.

### 13.2 Later Data Intake Sources

- Supplier email ingestion.
- Google Drive import.
- Google Calendar reminders.
- Co-op integrations.
- Fuel distributor integrations.
- Ag retailer integrations.
- Seed dealer portals.
- Farm management software.
- Equipment data.
- Tank sensors.
- Weather stations.
- Premium market data providers.

### 13.3 Data Quality Principle

For purchasing decisions, prioritize data in this order:

1. Current supplier quote for the specific farmer.
2. Recent invoice or transaction history.
3. Supplier integration data.
4. Regional benchmark data.
5. Public market trend data.
6. User assumptions.

The product should label source, timestamp, freshness, assumptions, confidence, and authorization status.

---

## 14. Farm Profile Fields

Minimum farm profile fields for MVP:

- Farm name.
- Location / county / state.
- Farm type.
- Primary crops.
- Organic/conventional/transitional/mixed status.
- Approximate acres or production scale.
- Sales channels.
- Key suppliers.
- Stored inputs.
- Fuel tank capacity and current level, if known.
- Fertilizer inventory or booked amounts.
- Seed inventory or orders.
- Packaging inventory for direct-market farms.
- Preferred risk posture: conservative, balanced, aggressive.
- Preferred recommendation style.
- User role: farmer, advisor, co-op employee, farm manager, market staff, field employee, or admin.

---

## 15. MVP User Journeys

### 15.1 Row-Crop Weekly Briefing

**User:** "What should I know this week?"

**System should:**

1. Read farm profile.
2. Check weather and fieldwork windows.
3. Check fuel level and price history.
4. Check fertilizer/seed/input status.
5. Check commodity/sales context.
6. Check deadlines and compliance reminders.
7. Produce a weekly action plan.
8. Highlight missing data.
9. Ask for approval before creating tasks, reminders, supplier messages, or external actions.

**Output structure:**

- Top priorities.
- Weather windows.
- Input watch.
- Market watch.
- Inventory risks.
- Compliance/deadline reminders.
- Recommended tasks.
- Missing information.
- Human-review flags.

### 15.2 Row-Crop Fuel Purchase Question

**User:** "Should I buy diesel this month?"

**System should:**

1. Read tank level and capacity.
2. Read current supplier quote.
3. Compare to price history and benchmarks.
4. Estimate near-term demand based on farm activities.
5. Consider cash-flow or risk posture if authorized.
6. Recommend buy, wait, split, or request more info.
7. Explain assumptions and uncertainty.
8. Offer a draft reminder or supplier message that requires approval.

### 15.3 Fertilizer Quote Comparison

**User:** uploads two quotes and asks which is better.

**System should:**

1. Extract product names, units, prices, delivery, terms, and quantities.
2. Normalize prices.
3. Convert to cost per usable nutrient.
4. Compare cost per acre where possible.
5. Check timing/weather constraints.
6. Check organic status if relevant.
7. Identify missing information.
8. Recommend next action only within evidence and review limits.

### 15.4 Small Organic Market Week Plan

**User:** "Help me plan this Saturday's market."

**System should:**

1. Read farm profile and sales channels.
2. Check market-day weather.
3. Review expected harvest availability.
4. Check packaging and supplies inventory.
5. Check organic recordkeeping needs.
6. Suggest harvest, packing, and market tasks.
7. Flag weather or inventory issues.
8. Draft customer update or availability list only when requested and requiring approval.

### 15.5 Small Organic Input Compliance Question

**User:** "Can I buy this fertilizer for my organic vegetable fields?"

**System should:**

1. Extract product name and quote/document details.
2. Check whether farm is certified organic, transitioning, or organic-practice-oriented.
3. Check farm-specific approved input records if available.
4. Flag certifier confirmation when evidence is incomplete.
5. Identify missing approval documentation.
6. Recommend safe next steps without making final certification claims.

---

## 16. Human Review and Safety Guardrails

HarvestAmp includes human-review flags for high-risk categories.

Human review is required or strongly recommended for:

- Pesticide application rates, product selection, tank mixes, label interpretation, drift, PHI, REI, and restricted-use decisions.
- Organic certification eligibility or input approval.
- Food safety compliance.
- Crop insurance decisions.
- USDA program eligibility or filings.
- Veterinary diagnosis or animal treatment.
- Major financial commitments.
- Commodity trading, hedging, or binding sale decisions.
- Legal, tax, payroll, accounting, lease, or contract advice.
- External disclosure of restricted farm data.
- Permission changes, credential changes, exports, deletion, and official record changes.

HarvestAmp can provide:

- Summaries.
- Checklists.
- Scenario comparisons.
- Questions to ask an expert.
- Drafts for user review.
- Source-labeled evidence references.

HarvestAmp must not pretend to replace licensed or local expertise.

The machine-readable scaffold for these rules lives in:

```text
configs/human_review_rules.yaml
```

---

## 17. Recommendation Style

All meaningful recommendations should include:

- Recommendation.
- Reasoning summary.
- Evidence/source summary.
- Assumptions.
- Confidence level.
- Missing data.
- Human-review flag, if needed.
- Suggested next action only when indicated.

Preferred tone:

- Practical.
- Plain-English.
- Local and farm-specific.
- Humble about uncertainty.
- Action-oriented.
- Not overly technical unless requested.

Example:

```text
Recommendation: Consider a split diesel purchase.

Why: Your tank is about 34% full, the current quote is recent and expires this week, and upcoming fieldwork may increase diesel demand. Buying the full expected 30-day need now may reduce shortage risk but reduces price flexibility.

Suggested action: Buy enough to cover the next fieldwork window and reserve, then set a watch alert for the remaining expected need.

Confidence: Medium.

Missing data: Confirmed delivered price and delivery fee.

Human review: User approval required before contacting the supplier or creating a purchase order.
```

---

## 18. Differentiation

HarvestAmp differentiates by combining farm context, operations, procurement, inventory, sales channel, and margin impact.

Many tools show weather, prices, or records. HarvestAmp should answer:

> Given my farm, inventory, suppliers, weather, crops, sales channel, records, and risk tolerance, what should I do next?

Key differentiators:

- Farm-type-specific workflows.
- Procurement and margin focus.
- Buy/wait/split recommendations.
- Supplier quote comparison.
- Inventory-aware decision support.
- Direct-market and organic support, not only commodity row-crop support.
- Human-review guardrails.
- Multi-agent architecture designed for enterprise deployment.
- Source, timestamp, evidence, and confidence display.

---

## 19. Success Metrics

### 19.1 Product Usage Metrics

- Weekly active farms.
- Weekly active advisors/users.
- Number of weekly plans generated.
- Number of input quotes analyzed.
- Number of inventory updates logged.
- Number of weather-to-action questions answered.
- Number of approved tasks or reminders created.
- Number of supplier/customer message drafts generated.

### 19.2 Business Value Metrics

- Estimated savings from quote comparison.
- Avoided stockouts.
- Timely purchase decisions.
- Reduced missed deadlines.
- Reduced time spent gathering data.
- Improved record completeness.
- Increased advisor capacity if sold to consultants, co-ops, or ag retailers.

### 19.3 Quality Metrics

- Recommendation acceptance rate.
- User edits to recommendations.
- Human-review flag accuracy.
- Source/evidence completeness.
- Missing-data detection accuracy.
- False-alert rate.
- User trust rating.
- Cross-farm leakage test pass rate.
- Action-gate enforcement test pass rate.

---

## 20. Monetization Hypothesis

The most likely monetization path is B2B or B2B2F rather than a low-cost individual farmer chatbot.

Possible pricing models:

- Monthly subscription per organization.
- Monthly subscription per advisor seat.
- Usage-based pricing per active farm profile.
- Usage-based pricing per field, acre block, document, quote, or alert run.
- Combined subscription plus usage.
- Private enterprise offers for co-ops, crop consultants, ag retailers, and large farm operators.

Suggested MVP commercial hypothesis:

> Ag advisors, co-ops, and large farm operators will pay for a farm-specific operations and procurement agent if it saves time, improves input purchasing decisions, reduces missed risks, and creates better weekly planning for multiple farms.

---

## 21. Technical Strategy at Product-Brief Level

HarvestAmp should be designed for Google's AI and cloud ecosystem.

High-level components:

- Antigravity for focused development tasks and project workflow.
- Google ADK-style agent definitions and orchestration.
- Gemini / Vertex AI for language understanding, extraction, reasoning, summarization, and synthesis.
- Google Cloud data services for farm profiles, quotes, records, inventory, events, and analytics.
- Scheduled jobs and event triggers for monitoring weather, prices, inventory, and deadlines.
- Google Marketplace-compatible packaging for later enterprise distribution.

The project should avoid relying on long chat memory as the source of truth. Project files should define the product, architecture, agent contracts, data models, risk rules, evaluation scenarios, and build plan.

---

## 22. Recommended MVP Build Order

1. Create and stabilize source-of-truth documents.
2. Create schemas and fixtures.
3. Create `configs/human_review_rules.yaml` as a separate policy scaffold.
4. Build fixture/schema validation.
5. Build mock Credential Broker / Authorization Service.
6. Build Tool Gateway stub.
7. Build Context Package Builder.
8. Build Supervisor skeleton with mock specialist agents.
9. Build Recommendation Synthesizer.
10. Build Action Agent with approval gates.
11. Build first Weekly Farm Action Plan workflow for Prairie View Farms.
12. Adapt Weekly Farm Action Plan to Green Basket Organics.
13. Add fuel buy/wait/split workflow.
14. Add fertilizer quote comparison workflow.
15. Add direct-market planning workflow.
16. Add document/manual-entry intake simulation.
17. Add evaluation tests and red-team cases.
18. Add UI shell.
19. Add monitoring simulations.
20. Add real data connectors only after mock workflows pass.

---

## 23. Key Assumptions

- Initial product is U.S.-focused unless changed later.
- MVP focuses on two farm types: large row-crop and small organic/direct-market.
- MVP uses manual entry, uploaded documents, mock fixtures, and controlled public data before deep supplier integrations.
- HarvestAmp supports decision-making but does not replace licensed experts or responsible farm managers.
- Strongest initial buyer may be an agricultural organization rather than an individual farmer.
- Input procurement and margin protection are major differentiators.
- Product should be designed for future Google Cloud Marketplace / AI Agent Marketplace distribution.
- Security, privacy, task-scoped context, and human-review gates are MVP requirements, not later polish.

---

## 24. Open Questions for Product Owner

### Business and Market

1. Is the initial geographic market the United States?
2. Is the preferred first buyer an individual farmer, a co-op, a crop consultant, an ag retailer, or a large farm operator?
3. Should the MVP be positioned as a farmer tool, advisor tool, or co-op/grower portal?
4. Should the product prioritize row-crop farms or small organic farms first in the demo?
5. Should the agent be white-labelable for co-ops or consultants?

### Farm Scope

6. Which row crops should the first demo support beyond the existing corn/soybean/wheat synthetic profile?
7. Which small-farm crops should the first demo emphasize: vegetables, fruit, flowers, herbs, greenhouse, or mixed?
8. Should livestock remain completely out of scope for MVP?
9. Should direct-market mode focus first on farmers markets, CSA, farm stand, restaurant, or local wholesale?

### Data and Integrations

10. Which weather source should be used first once mock data is replaced?
11. Should supplier quotes be entered manually first, uploaded as documents, or read from email?
12. Which co-ops, seed dealers, fuel suppliers, or ag retailers should be targeted for pilots?
13. Should the agent store financial data such as break-even, cash-flow constraints, and purchase history?
14. Should file uploads be included in first MVP or simulated at first?

### Product Behavior

15. How proactive should alerts be?
16. Should the agent create tasks automatically or only after explicit user approval?
17. What level of uncertainty is acceptable for buy/wait/split recommendations?
18. Should recommendations use conservative, balanced, or aggressive defaults?
19. Should users customize thresholds for alerts?

### Compliance and Risk

20. How strict should the human-review gate be?
21. Should pesticide-related questions be included in MVP only as weather/caution guardrails or deferred entirely?
22. Should organic certification workflows be included in MVP or treated as advisory only?
23. Should high-risk recommendation caveats be shown inline or in expandable review cards?

---

## 25. Initial MVP Definition

The first MVP should prove one core claim:

> HarvestAmp can generate useful weekly action plans for two very different farm types by combining weather, inventory, input prices, supplier quotes, market/sales context, records, and compliance reminders while preserving evidence, privacy, and human-review gates.

### MVP Demo Scenario A: Prairie View Farms

The system should support:

- Corn/soybean/wheat operation.
- Field locations and acreage summaries.
- Diesel tank level and capacity.
- Fertilizer quotes.
- Seed order status.
- Commodity sales channel.
- Weather forecast.
- Inventory records.
- Upcoming fieldwork.

Expected output:

- Weekly action plan.
- Fuel buy/wait/split recommendation.
- Fertilizer quote analysis.
- Weather work-window recommendation.
- Market/input margin watch.
- Compliance reminders.
- Human-review and approval-required actions.

### MVP Demo Scenario B: Green Basket Organics

The system should support:

- Diversified vegetable operation.
- Certified organic status.
- Farmers market and CSA sales channels.
- Seed/transplant needs.
- Compost or organic fertilizer quote.
- Packaging inventory.
- Market-day weather.
- Harvest planning.
- Basic recordkeeping.

Expected output:

- Weekly farm plan.
- Market-day planning checklist.
- Packaging shortage alert.
- Organic input caution flag.
- Harvest and packing task list.
- Customer or CSA communication draft requiring approval.

---

## 26. Non-Negotiable Product Principles

1. **Farm-specific beats generic.** HarvestAmp must use farm profile and memory whenever possible.
2. **Decision support beats information display.** The product should help users decide what to do, not merely show data.
3. **Input costs matter.** Fuel, fertilizer, seed, feed, packaging, parts, and inputs should connect to margin.
4. **Inventory changes recommendations.** Price is not meaningful without need, capacity, storage, timing, and lead time.
5. **Sales channel changes everything.** Commodity, CSA, farmers market, wholesale, restaurant, and farm stand workflows differ.
6. **Human review is required for high-risk decisions.** HarvestAmp should be useful without replacing experts.
7. **Source and timestamp matter.** Recommendations should explain where information came from and how current it is.
8. **Start narrow, then expand.** MVP should be strong for two farm types before expanding.
9. **Credentials never enter LLM context.** Agents request capabilities; infrastructure handles secrets.
10. **No cross-farm leakage.** Private data from one farm must not answer another farm's question.

---

## 27. Draft Product Tagline Options

- "Know what to do, what to buy, and what to watch on your farm."
- "A weekly operations and input-margin agent for farms."
- "Turn weather, prices, inventory, and farm records into action."
- "The farm-specific agent for operations, procurement, and margin decisions."
- "From field conditions to fuel prices, know your next best action."

---

## 28. Draft Marketplace Description

HarvestAmp helps farms, co-ops, crop consultants, and agricultural organizations turn fragmented farm data into practical action plans. The agent combines farm profile data, weather, field status, supplier quotes, input inventory, fuel and fertilizer costs, seed orders, commodity or direct-market sales context, compliance reminders, source freshness, and user preferences to recommend what needs attention now.

For large row-crop operations, HarvestAmp helps evaluate fieldwork windows, fuel buying, fertilizer quotes, seed readiness, input costs, commodity market context, and weekly priorities.

For small organic and direct-market farms, HarvestAmp helps plan harvests, market days, CSA boxes, packaging supplies, organic input cautions, weather risks, and weekly farm tasks.

The system is designed as a multi-agent workflow with specialist agents for weather, procurement, records, markets, compliance, margin scenarios, and recommendation synthesis. Human-review guardrails are included for high-risk decisions such as pesticide use, organic certification, veterinary issues, crop insurance, legal, financial, and compliance-sensitive matters.

---

## 29. Current Product Decision

Proceed with an MVP centered on:

> **Weekly Farm Action Plan + Input Procurement Advisor for two farm profiles: Prairie View Farms and Green Basket Organics.**

This MVP should show that HarvestAmp can adapt to different farming businesses while sharing a common architecture, memory layer, evidence model, privacy boundary, and recommendation format.
