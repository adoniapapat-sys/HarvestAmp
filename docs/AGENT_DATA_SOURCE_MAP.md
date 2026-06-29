# HarvestAmp Agent Data Source Map

## Purpose

This document maps what information each HarvestAmp agent needs, where that information should come from, how it should be authorized, and how evidence should be preserved.

The core rule is:

```text
Agents know what information they need.
The Supervisor, Context Package Builder, Credential Broker, ToolGateway, and EvidenceBoard decide where to get it, whether the user is authorized, and how it is labeled.
```

Agents should not become independent source fetchers or direct connector callers. They should receive task-scoped, evidence-backed context from the Supervisor.

---

## Core Data Flow

```text
User request
  -> Intent Router / Supervisor
  -> Context Package Builder
  -> Credential Broker authorization
  -> ToolGateway capability request
  -> Connector / fixture / local document result
  -> EvidenceBoard source-labeled evidence
  -> Specialist agents
  -> AgentFindings
  -> Recommendation Synthesizer
  -> Human Review Policy
  -> Action Agent gate
  -> ActionPack + Audit Events
```

---

## Source Classification

HarvestAmp should label every source by its role in decision-making.

| Source class | Meaning | Decision role |
|---|---|---|
| Farm-specific records | Inventory, quotes, invoices, harvest logs, sales commitments, documents, records entered or uploaded by the farm | Decision anchor after source labeling and review |
| Local fixture data | Synthetic farm records used for MVP testing | Test decision anchor for synthetic scenarios |
| Local document extraction | Uploaded/local invoices, quotes, tickets, records, parsed into draft records | Draft anchor only until reviewed |
| Public official / extension context | NWS, EIA, NASS, AMS, Crop Health Watchlist, Extension/IPM-style watchlists | Context only; does not override farm truth |
| Future read-only ingestion | User-approved Google Drive or Gmail ingestion | Farm-specific source only after consent, scoping, redaction, and review |
| Future action-capable integrations | Supplier portals, email sending, record writeback, order systems | Deferred; must remain approval-gated |

---

## Common Fields for Data Requirements

Each agent data requirement should define:

```text
Data requirement
Current provider / capability
Current fixture or evidence examples
Future provider, if any
Decision role: farm anchor, public context, draft-only, or derived math
Role visibility
Human-review behavior
Missing-data behavior
Evidence requirements
```

---

# 1. Weather + Fieldwork Agent

## Agent data principle

The Weather + Fieldwork Agent needs weather and operation-window context. It should not fetch weather directly from connector classes. The Supervisor should request authorized weather capability and pass evidence-backed weather context to the agent.

| Data requirement | Current provider / capability | Current evidence examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| Forecast and fieldwork windows | `weather_tool` through ToolGateway | `res_weather_nws_<farm_id>` | NWS live shadow, farm weather station, weather sensor feed | Public official context plus farm operation context | Generally visible to operational roles | Mark stale or fallback; do not present as certain | Source, timestamp, freshness, connector mode, fallback flag |
| Rain, wind, heat, frost, humidity constraints | `weather_tool`, weather fixtures | NWS offline/mock weather evidence | NWS live, sensor data | Context only | Generally visible | Flag uncertainty and missing local measurements | Forecast source, timestamp, confidence |
| Market-day weather | `weather_tool` plus Market/Sales context | GBO Saturday market weather evidence | NWS live, local station | Context for market prep | Generally visible | Surface as watch, not commitment | Weather evidence plus market-day reference |
| High tunnel / greenhouse weather risk | Weather fixture plus farm profile | GBO high tunnel watch | Sensor feed, tunnel humidity/temperature records | Context for human action | Generally visible unless sensitive operational detail | Missing internal humidity readings should be explicit | Weather evidence, farm site reference |
| Irrigation-need signals | Weather fixture, irrigation scenario fixture | Existing irrigation mock workflows | Weather station, irrigation records, soil moisture sensors | Context only | Role-dependent if water rights are sensitive | Needs_info if allocation or moisture missing | Weather evidence plus water/soil evidence |
| Planned weather-dependent operations | Context Package Builder from farm plans/scenarios | Weekly plan operation context | Calendar/task systems later | Farm-specific operational context | Role-scoped | Do not schedule automatically | Operation evidence or scenario reference |

## Current gaps

```text
- Field-level soil workability data is not yet modeled deeply.
- High-tunnel internal humidity readings are currently missing data, not a real source.
- Farm weather station or sensor data is not implemented.
- Weather is sometimes too broadly available; routing should stay task-scoped.
```

---

# 2. Procurement Agent

## Agent data principle

The Procurement Agent needs quotes, invoices, reorder triggers, supplier terms, and cost context. It should consume farm-specific quote/inventory evidence and public benchmarks only as supporting context. It must not contact suppliers or commit purchases.

| Data requirement | Current provider / capability | Current evidence examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| Fuel quotes | `fuel_tool`, quote fixtures | `res_quote_PVF_QUOTE_DIESEL_2026_06_21` | Local document extraction, Drive/Gmail ingestion | Farm-specific decision anchor | Hidden from field employees | Missing quote terms -> needs_info | Supplier, quote date, valid-until, unit price, evidence ID |
| Fertilizer quotes | `fertilizer_tool`, quote fixtures | `res_quote_PVF_QUOTE_UREA_2026_06_20`, `res_quote_PVF_QUOTE_UAN32_2026_06_20` | Local document extraction, Drive/Gmail ingestion | Farm-specific decision anchor | Hidden from field employees | Missing delivery/application fees -> needs_info | Product, unit, price, fees, valid-until, evidence ID |
| Seed quotes | Document extraction and future quote fixtures | DOC seed quote evidence | Drive/Gmail ingestion, local uploads | Farm-specific decision anchor | Restricted by role | Missing seed terms, treatment, population/acre target -> needs_info | Crop, variety, lot, treatment, price, source document |
| Packaging quotes and reorders | Packaging fixtures, document extraction | GBO CSA box quote/order draft evidence | Drive/Gmail ingestion, local uploads | Farm-specific decision anchor | Owner/manager visible; limited field view | Missing quantities/lead time -> needs_info | Supplier, units, unit price, lead time, evidence ID |
| Quote-to-invoice mismatch | Local document extraction | DOC invoice/quote evidence | Drive/Gmail ingestion | Farm-specific review signal | Restricted by role | Flag mismatch; do not approve purchase | Quote evidence, invoice evidence, variance |
| Inventory reorder triggers | `records_tool`, Inventory Database | Inventory IDs for diesel, packaging, stored grain, crop-protection gaps | Expanded inventory records | Derived from farm inventory | Role-scoped | Stale count -> needs_info | Inventory ID, last verified, threshold |
| Public cost benchmarks | EIA/NASS public context | `res_benchmark_eia_<farm_id>`, `res_benchmark_nass_<farm_id>` | Live public connectors | Public context only | Owner/manager mainly; field employees usually do not need pricing | If unavailable, omit or label fallback | Public source, freshness, connector mode |
| Organic or restricted input status | Compliance Agent, records_tool, fixtures | Organic input documentation flags | Document ingestion, certifier docs later | Compliance context | Role-restricted if sensitive | Unverified status -> block/review | Compliance evidence, documentation source |

## Current gaps

```text
- Procurement coverage is still too focused on fuel, fertilizer, and packaging.
- Seed, soil amendments, equipment parts, irrigation parts, PPE, and harvest supplies need fuller fixture coverage.
- Supplier lead time, contract status, volume commitment, and price history are not yet fully modeled.
```

---

# 3. Records + Inventory Agent

## Agent data principle

The Records + Inventory Agent owns the farm inventory and record truth layer. It should receive inventory records, document-extracted draft records, harvest/yield records, storage records, compliance documents, and freshness metadata. It should not commit official updates without approval.

| Data requirement | Current provider / capability | Current evidence examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| Fuel inventory | `records_tool`, Inventory Database | `res_inv_PVF_INV_DIESEL` | Tank monitor, accounting/inventory system later | Farm-specific anchor | Details restricted for field employees | Stale count -> needs_info | Inventory ID, quantity, capacity, last verified |
| Stored grain inventory | `records_tool`, Inventory Database | `res_inv_PVF_INV_CORN_STORED`, `res_inv_PVF_INV_SOY_STORED` | Scale tickets, bin sensors, settlement records | Farm-specific anchor | Financial details restricted | Missing reconciliation/basis -> watch only | Crop, quantity, bin, last reconciled |
| Packaging inventory | `records_tool`, Inventory Database | GBO clamshells, CSA boxes, labels evidence | POS/warehouse later, manual counts | Farm-specific anchor | Operational count visible; pricing restricted | Low or stale count -> draft review | Item ID, quantity, threshold, last verified |
| Crop-protection inventory | `records_tool`, fixtures | Herbicide partial, fungicide unknown, adjuvant low | Document/receipt ingestion, inventory system | Farm-specific and compliance-sensitive | Restricted details by role | Unknown details -> needs_info | Item, quantity/status, label/document evidence |
| Seed lots and planting stock | Future inventory fixture expansion | Not yet fully modeled | Seed invoices, seed tags, local upload/Drive | Farm-specific anchor and compliance-sensitive | Restricted if pricing/treatment sensitive | Missing lot/germination/docs -> needs_info | Lot number, variety, germination, docs |
| Fertilizer and amendments inventory | Current fertilizer quote context; not full inventory | Partial via quotes | Inventory fixtures, invoices, delivery tickets | Farm-specific anchor | Pricing restricted | Missing fees/docs/quantity -> needs_info | Item, analysis, quantity, source docs |
| Equipment, machinery, and spare parts | Future inventory expansion | Not yet fully modeled | Maintenance logs, parts invoices | Operational anchor | Generally operational; valuation restricted | Missing service status -> watch | Equipment ID, service status, parts stock |
| Irrigation supplies | Irrigation mock workflows; future inventory | IRR scenario context | Inventory fixtures, irrigation records | Operational context | Role-scoped | Missing allocation/parts -> needs_info | Parts/equipment/water evidence |
| Harvest/post-harvest inventory | Future harvest domain expansion | Current GBO weekly plan only references expected harvest volume as missing | Harvest logs, cooler inventory, packout records | Farm-specific anchor | Operational counts visible; customer/financial restricted | Missing harvest volume -> needs_info | Harvest event ID, lot, quantity, storage |
| Document-extracted draft records | Local document extraction | `ev_doc_*` evidence IDs | Drive/Gmail/local uploads | Draft anchor only until reviewed | Farm Restricted | Low confidence -> needs_info, no commit | Source document, extracted fields, confidence |
| Safety and PPE inventory | Future inventory expansion | Field employee PPE watch in weekly plan | Inventory fixture, safety logs | Operational/safety anchor | Generally visible | Missing inspection -> watch/needs_info | PPE item, inspection date, requirement |

## Current gaps

```text
- Full inventory taxonomy is not implemented.
- Harvest/post-harvest, equipment parts, irrigation parts, PPE, seed lots, and amendments need richer fixtures.
- Inventory source-of-truth boundaries with Procurement should be formalized.
- Official record update approval state needs a review queue later.
```

---

# 4. Market + Sales Agent

## Agent data principle

The Market + Sales Agent needs farm commitments, available inventory, orders, pack lists, delivery status, sales records, and public market context. Farm commitments and sales records are anchors. AMS and other public market data are context only.

| Data requirement | Current provider / capability | Current evidence examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| CSA commitments | Farm sales fixtures / weekly plan context | GBO 75 CSA members | CSA management system later | Farm-specific anchor | Owner/manager; operational subset for crew | Missing member/order changes -> needs_info | CSA commitment ID, date, share count |
| Restaurant orders | Farm sales fixtures / weekly plan context | Restaurant timing watch | Order system, local uploads, Drive/Gmail | Farm-specific anchor | Customer/financial details restricted | Missing pre-orders -> needs_info | Order ID, items, quantities, delivery date |
| Farmers market plan | Farm sales fixtures / weekly plan context | Saturday market prep | POS/market records later | Farm-specific anchor | Role-scoped | Missing pack quantities -> needs_info | Market plan ID, date, items |
| Harvest availability | Records + Inventory handoff | Currently expected harvest volume missing | Harvest logs, cooler inventory, packout | Farm-specific anchor | Operational counts visible; financial restricted | Missing harvest volume -> needs_info | Harvest event, lot, inventory evidence |
| Packaging constraints | Records + Inventory handoff | GBO CSA boxes/clamshell inventory | Inventory system later | Farm-specific anchor | Operational count visible | Low/stale count -> draft procurement watch | Inventory IDs and thresholds |
| Public direct-market context | AMS connector | `res_benchmark_ams` | AMS live read-only, other public sources later | Public context only | Generally owner/manager | If unavailable, omit or label fallback | Report ID, date, source, connector mode |
| Stored grain market watch | Market/Sales plus Inventory and Scenario | Stored corn/soybean watchlist | Local bids/basis later | Watch context only | Restricted to owner/manager | Missing bid/basis -> no sale math/recommendation | Stored quantity, bid/basis evidence if present |
| Sales records and payment status | Future sales domain expansion | Not yet fully modeled | POS, accounting, invoices later | Farm-specific anchor | Financial/customer restricted | Missing reconciliation -> needs_info | Sale ID, payment status, channel, date |
| Returned/unsold inventory | Future harvest/sales expansion | Not yet modeled | Market reconciliation logs | Farm-specific anchor | Operational counts visible | Missing returns -> needs_info | Market record, inventory update evidence |

## Current gaps

```text
- Harvest results, packout, returned inventory, sales reconciliation, invoices, and payment status are not yet modeled.
- CSA/restaurant/farmers market commitments are present only in a thin weekly-plan form.
- Stored grain sale watch lacks current local bid/basis data and should remain watch-only.
```

---

# 5. Compliance Agent

## Agent data principle

The Compliance Agent needs records, documents, deadlines, safety flags, and compliance-sensitive context. It flags risk and missing records. It does not provide legal advice, pesticide product/rate/tank-mix advice, organic approval decisions, or official filings.

| Data requirement | Current provider / capability | Current evidence examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| Organic certification records | `records_tool`, organic fixtures | GBO OSP / approved input list incomplete | Drive/local uploads, certifier docs later | Farm-specific compliance anchor | Owner/manager, restricted by role | Missing docs -> expert review / needs_info | Document ID, status, date, source |
| Seed source documentation | Records/Inventory, future seed inventory | Not fully modeled | Seed invoices/tags/document ingestion | Farm-specific compliance anchor | Restricted if pricing/treatment sensitive | Missing docs -> needs_info | Seed lot, organic search docs, evidence ID |
| Spray/crop-protection records | `records_tool`, compliance fixtures | PVF spray recordkeeping watch | Application logs, local uploads | Compliance anchor | Restricted by role | Missing EPA reg/applicator/weather fields -> incomplete | Application log ID, source fields |
| REI/PHI intervals as recorded facts | Future compliance fixture expansion | Not fully modeled | Application records, crop records | Compliance context | Restricted if sensitive | Conflict -> human review/block | Application record and harvest record evidence |
| RUP/applicator license tracking | Future compliance fixture expansion | Not fully modeled | License records | Compliance anchor | Restricted | Expiration -> watch/expert review | License ID, expiration date |
| USDA/FSA/crop insurance deadline watch | Records/tool fixtures | PVF acreage reporting watch | User-entered program records | Compliance-sensitive watch | Owner/manager | Unknown status -> needs_info | Deadline source/reference, farm status |
| Crop-health watchlist | `crop_health_watchlist` through ToolGateway | `res_crop_health_<farm_id>` | Public extension/IPM/APHiS-style context | Public context only | Generally visible, no pricing | Unavailable -> fallback labeled | Source, issue, risk, report date, mode |
| Food safety / wash-pack records | Future harvest/sales expansion | Not yet modeled | Wash-pack logs, local uploads | Farm-specific compliance anchor | Role-scoped | Missing logs -> needs_info | Log ID, date, lot, source |
| Document integrity and audit readiness | Local document extraction, records_tool | DOC evidence IDs | Drive/Gmail/local uploads | Draft/compliance anchor | Farm Restricted | Low confidence -> needs_info | Source doc, extraction confidence, redactions |

## Current gaps

```text
- Food safety, PHI/REI, applicator license, seed-source documentation, and full organic audit readiness need deeper fixtures.
- Compliance needs formal handoffs from Inventory, Procurement, Market/Sales, and Action Agent.
```

---

# 6. Margin + Scenario Agent

## Agent data principle

The Margin + Scenario Agent should mostly consume other agents' findings and evidence-backed inputs. It is a calculator with context, not an advisor. It should not fetch broad data directly unless the Supervisor provides a scoped scenario package.

| Data requirement | Current provider / capability | Current evidence examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| Fuel cost inputs | Procurement findings, fuel quote evidence | Diesel quote + EIA benchmark | Document extraction, Drive/Gmail | Farm cost anchor plus public context | Restricted from field employees | Missing quote -> scenario unavailable or range only | Quote evidence, assumptions |
| Fertilizer/input cost inputs | Procurement findings, fertilizer quote evidence | Urea/UAN quotes | Quote/invoice ingestion | Farm cost anchor | Restricted from field employees | Missing delivery/application fees -> no false precision | Quote evidence, missing-fee list |
| Seed/packaging costs | Procurement and document extraction | Packaging invoice/quote evidence | Ingestion later | Farm cost anchor | Restricted from field employees | Missing unit cost -> needs_info | Source docs, units, assumptions |
| Yield/harvest quantities | Records + Inventory findings | Stored grain quantities currently; harvest not deep yet | Harvest/yield records | Farm anchor | Restricted by role if financial | Missing yield -> cannot calculate break-even | Yield/harvest evidence, assumptions |
| Sales/revenue assumptions | Market + Sales findings | GBO AMS context and commitments; limited sales fixtures | Sales records/POS later | Farm sales anchor; public context only as benchmark | Financial/customer restricted | Missing actual price/order -> show assumptions or refuse precision | Sales evidence, channel, quantity, price assumptions |
| Stored grain scenario inputs | Inventory + Market/Sales + public context | Stored corn/soybean quantities; local bid missing | Local bid/basis records later | Watch/math only | Owner/manager | Missing basis/bid -> no sell/hold recommendation | Quantity, bid/basis, storage assumptions |
| Budget vs actual context | Future records/accounting fixtures | Not yet modeled | Accounting integration later, manual fixtures | Farm financial anchor | Owner/manager only | Missing actuals -> needs_info | Budget/actual evidence |

## Current gaps

```text
- Margin + Scenario Agent has a defined boundary but limited implementation depth.
- It needs harvest/yield/sales data before useful enterprise math is possible.
- It must avoid making recommendations and must always show assumptions.
```

---

# 7. Recommendation Synthesizer

## Component data principle

The Synthesizer consumes AgentFindings and EvidenceBoard items. It should not call connectors or fetch new farm data. Its job is to organize findings into a clear, role-safe ActionPack.

| Data requirement | Current provider | Current examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| AgentFindings | Specialist agents | Weekly plan sections | Expanded agent findings | Derived from agents | Role-filtered | If findings conflict, surface or prioritize by policy | Agent name, evidence IDs, confidence |
| Evidence summary | EvidenceBoard | Weekly plan evidence summary | Same | Traceability | Role-filtered | Missing evidence -> warning/test failure | Evidence ID, source, freshness |
| Human review state | Human Review Policy | needs_user_approval, needs_expert_review, review_not_required | Review Queue later | Safety metadata | Visible as status | Missing review metadata -> block or default conservative | Review type, risk tier, blockers |
| Proposed actions | Specialist agents / synthesizer assembly | Draft fuel inquiry, CSA order, certifier share | Review Queue later | Draft only | Role-filtered | Missing payload fields -> needs_info | Action ID, source evidence, payload summary |
| Role constraints | Credential Broker / roles | Field employee restricted weekly plan | Same | Authorization | Role-specific | If uncertain, hide restricted data | Role, denied capabilities, redactions |

## Current gaps

```text
- Synthesizer needs stronger de-duplication and output-crowding controls as domains expand.
- It needs a documented rule for context vs recommendation vs action in every section.
```

---

# 8. Action Agent

## Component data principle

The Action Agent receives proposed actions and review metadata. It gates, blocks, validates, or marks actions as simulated-approved/rejected. It should not decide what the farmer should do and should not execute external actions in the MVP.

| Data requirement | Current provider | Current examples | Future provider | Decision role | Role visibility | Missing-data behavior | Evidence required |
|---|---|---|---|---|---|---|---|
| Proposed action payloads | Synthesizer / ActionPack | Draft supplier messages, draft official record updates | Review Queue later | Draft action | Role-filtered | Missing required fields -> needs_info | Action ID, payload, source evidence |
| Human review status | Human Review Policy | needs_user_approval, needs_expert_review | Review Queue later | Approval gate | Role-specific | Missing status -> block conservatively | Review type, blockers, risk tier |
| Reviewer authorization | Credential Broker / roles | Field employee denied fuel/fertilizer capability | Review Queue later | Authorization | Role-specific | Unauthorized -> denied | User role, allowed actions |
| Sensitive data labels | EvidenceBoard, extraction redaction | Farm Restricted docs, redacted sensitive content | Ingestion/redaction later | Safety gate | Restricted | Sensitive raw values -> redact/block | Sensitivity label, redaction record |
| Audit events | Audit Logger | Capability request logs | Review decision logs later | Traceability | Internal/admin | Missing audit -> test failure for high-risk action | Audit event ID, action ID, user ID |
| Approval state | Current ActionPack only; Review Queue future | blocked_pending_user_approval | Review Queue local simulation | Local simulated state | Role-restricted | No approval -> not_executed | Approval/rejection record |

## Current gaps

```text
- There is not yet a full Review Queue + Approval Simulation component.
- Action Agent gating exists conceptually and in tests, but action lifecycle states should be expanded later.
- Approved actions should remain local/simulated until real integrations are intentionally added.
```

---

# Cross-Agent Source Rules

## 1. Agents do not import connector classes directly

Bad pattern:

```text
WeatherFieldworkAgent imports NWSWeatherConnector
ComplianceAgent imports CropHealthWatchlistConnector
MarketSalesAgent imports AMSMarketNewsConnector
```

Preferred pattern:

```text
Supervisor requests capability through ToolGateway
ToolGateway returns evidence-backed normalized result
Agent receives scoped context and evidence IDs
```

## 2. Farm-specific data is the anchor

Decision anchors include:

```text
farm inventory
supplier quotes
uploaded invoices
harvest logs
sales commitments
restaurant orders
CSA commitments
scale/load tickets
user-approved records
```

Public sources include:

```text
NWS
EIA
NASS
AMS
Crop Health Watchlist / Extension / IPM-style context
```

Public sources are context only.

## 3. Missing data must be explicit

If a data source is missing or stale, agents should produce:

```text
needs_info
low confidence
fallback_used
watch_only
no false-precision number
```

## 4. Role visibility follows source sensitivity

Field employees may see operational readiness and safety context, but should not see:

```text
supplier pricing
margin
customer financial details
restricted documents
buyer terms
settlement details
sensitive compliance details
```

## 5. Future ingestion does not change the agent boundary

Even after Google Drive or Gmail ingestion is added later, agents should still receive normalized, evidence-backed context. They should not browse folders or emails directly.

---

# Priority Source Gaps to Address Next

## High priority

```text
harvest logs
field/block yield records
grain load or scale tickets
bin inventory reconciliation
cooler inventory
packout and cull/shrink records
restaurant/CSA/farmers market fulfillment
sales records and payment/reconciliation status
full inventory taxonomy: seed lots, amendments, equipment parts, irrigation supplies, harvest supplies, PPE
```

## Medium priority

```text
supplier lead times
quote history and price spike baselines
standard price lists
local bid/basis records
budget vs actual fixtures
organic seed search documentation
PHI/REI and application completeness fixtures
```

## Deferred

```text
Google Drive ingestion
Gmail ingestion
supplier portals
POS/accounting integrations
barcode scanning
external email sending
real order execution
real official record writeback
```

---

# Acceptance Criteria for This Map

This document is useful if it helps answer:

```text
What data does each agent need?
Who is allowed to retrieve it?
What current fixture or tool provides it?
What future source might provide it?
Is it farm truth or public context?
What evidence ID must be attached?
What happens when it is missing?
Which roles may see it?
What action, if any, can be drafted from it?
```
