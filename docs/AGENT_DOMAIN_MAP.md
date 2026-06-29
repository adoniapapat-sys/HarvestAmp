# HarvestAmp Agent Domain Map

## Purpose

HarvestAmp is a supervised multi-agent farm operations assistant. The Supervisor coordinates specialist agents, but each agent must stay inside a clearly defined lane.

This document defines the domain responsibilities for:

1. Weather + Fieldwork Agent
2. Procurement Agent
3. Records + Inventory Agent
4. Market + Sales Agent
5. Compliance Agent
6. Margin + Scenario Agent
7. Recommendation Synthesizer
8. Action Agent

Core rule:

```text
Agents produce evidence-backed findings.
The Synthesizer turns findings into a coherent ActionPack.
The Action Agent gates proposed actions.
Humans approve or reject action.
```

No agent should silently execute external actions, update official records, create financial commitments, send messages, or invent missing facts.

---

## Shared Agent Output Contract

Each specialist agent should return structured findings compatible with HarvestAmp's `AgentFinding` shape.

Each finding should preserve:

```text
agent_name
farm_id
topic
summary
recommendation
urgency
confidence
evidence_ids
assumptions
missing_data
human_review
source freshness / timestamp where relevant
role visibility level
proposed action type, if any
```

Every agent must distinguish:

```text
farm-specific decision anchor
public context
missing data
draft action
blocked action
human-review requirement
```

---

# 1. Weather + Fieldwork Agent

## Clean line

The Weather + Fieldwork Agent reports weather conditions, fieldwork windows, and weather-related risks. It does **not** prescribe field operations, spraying, treatment, planting decisions, or harvest commitments.

## Should handle

```text
fieldwork windows
rain / wind / heat / frost constraints
soil-workability context when available
drying-time context after rain
market-day weather risk
high-tunnel / greenhouse weather risk
irrigation-need signals during dry spells
weather freshness and fallback metadata
operation conflicts caused by weather
microclimate or field/site differences when available
```

## Should not handle

```text
spray timing instructions
pesticide recommendations
planting prescriptions
harvest commitments
crew scheduling commitments
irrigation orders
equipment dispatch
external messages
official record updates
```

## Inputs needed

```text
farm location
forecast evidence
forecast freshness
planned operations
field or site context
high-tunnel / greenhouse context
market-day or harvest-day context
recent rainfall, temperature, wind, humidity if available
user role
```

## Evidence required

```text
weather evidence ID
source name
forecast timestamp
connector mode
fallback status
freshness label
```

## Actions it may draft

Usually none.

It may surface internal watch items, such as:

```text
fieldwork window watch
market weather watch
frost/freeze watch
high-tunnel ventilation watch
```

## Review triggers

```text
fallback weather used
weather data stale
severe weather risk
weather-linked task may become safety-sensitive
user asks for spray/treatment timing
```

## Handoffs

```text
Weather -> Procurement:
Upcoming fieldwork window may affect fuel, parts, seed, fertilizer, packaging, or harvest-supply readiness.

Weather -> Records + Inventory:
Weather-dependent tasks may require checking equipment, PPE, fuel, irrigation supplies, harvest supplies, or storage readiness.

Weather -> Market + Sales:
Market-day weather or harvest-window risk may affect pack lists, delivery timing, or farmers market setup.

Weather -> Compliance:
Any spray/treatment/weather question is routed to compliance safety boundaries.

Weather -> Margin + Scenario:
Weather may be an assumption in what-if math, but not a decision.
```

## Acceptance examples

```text
PVF: identifies Friday as best fieldwork window.
GBO: identifies Saturday market/high-tunnel weather risk.
Forecast data older than threshold is flagged stale.
Primary weather source unavailable -> fallback labeled low-confidence.
User asks "when should I spray fungicide?" -> no spray-timing instruction; route to compliance refusal/safety boundary.
Planned harvest collides with forecast rain -> conflict flagged, no reschedule committed.
```

---

# 2. Procurement Agent

## Clean line

The Procurement Agent watches quotes, reorder needs, supplier terms, price context, and missing procurement data. It may draft quote or reorder messages, but it does **not** buy, select suppliers, send messages, or create financial commitments.

## Should handle

```text
fuel quote watch
fertilizer quote comparison
seed quote watch
packaging reorder watch
chemical/input quote watch
soil amendment quote watch
parts/equipment quote watch
irrigation supply quote watch
PPE/safety supply reorder watch
supplier lead times
quote expiration
quote-to-invoice mismatch
missing fees and terms
bulk/prepay/early-order context
supplier responsiveness/reliability notes
single-source dependency watch
role-based price visibility
```

## Should not handle

```text
placing orders
selecting suppliers automatically
sending supplier messages
approving purchases
making financial commitments
choosing pesticide products
choosing application rates
changing official inventory records
showing restricted pricing to unauthorized roles
```

## Inputs needed

```text
inventory thresholds from Records + Inventory
supplier quotes
document-extracted quote/invoice drafts
fuel/fertilizer/seed/packaging requirements
seasonal timing from Weather + Fieldwork
organic/restricted input flags from Compliance
budget or cost context from Margin + Scenario
user role
```

## Evidence required

```text
quote evidence IDs
invoice evidence IDs
inventory evidence IDs
supplier document references
public benchmark evidence where used
quote date and valid-until date
missing fee flags
```

## Actions it may draft

```text
draft supplier quote inquiry
draft reorder inquiry
draft request for missing delivery/application fees
draft request for OMRI/organic documentation
draft quote-to-invoice review note
```

All such actions require approval before sending.

## Review triggers

```text
financial action
new supplier
quote over approval threshold
missing fees
quote-to-invoice mismatch
organic/OMRI uncertainty
restricted input
field employee attempting to access pricing
```

## Handoffs

```text
Inventory -> Procurement:
Low stock, stale count, reorder threshold, lead time, missing quantity.

Compliance -> Procurement:
Organic status, restricted-use status, documentation requirements.

Procurement -> Scenario:
Actual input cost, quote terms, missing fee assumptions.

Procurement -> Synthesizer:
Draft quote/reorder actions and missing procurement data.
```

## Acceptance examples

```text
Fertilizer quote missing delivery/application fees -> flagged, no order.
Field employee requests supplier pricing -> denied or hidden.
Fuel quote inquiry -> draft only, needs owner approval.
Seed reorder needed before planting window -> draft/needs approval.
Chemical input quote with unverified OMRI status -> blocked pending documentation.
Invoice exceeds quote by 8% -> quote-to-invoice mismatch flagged.
```

---

# 3. Records + Inventory Agent

## Clean line

The Records + Inventory Agent owns the farm's inventory and record truth layer. It tracks what exists, where it is, how fresh it is, what is missing, and what records are draft or official. It does **not** buy, sell, apply, file, or commit official updates without approval.

## Should handle

```text
seeds and planting stock
fertilizers and soil amendments
pest/disease/weed-control materials
fuel and lubricants
equipment and machinery
spare parts
irrigation supplies
harvest and post-harvest supplies
packaging and sales materials
livestock inventory if applicable
greenhouse / infrastructure / consumables
safety and PPE
records and compliance documents
stored grain inventory
harvested-but-unsold produce
cooler inventory
bin inventory
document-extracted draft records
freshness/staleness
expiration and shelf-life
lot/batch tracking
traceability
duplicate-record detection
unit mismatches
negative-quantity prevention
```

## Should not handle

```text
placing reorders
selecting suppliers
sending messages
committing official inventory updates
recommending grain sales
recommending pesticide use
approving organic inputs
making financial decisions
```

## Inputs needed

```text
inventory fixtures
farm records
document-extracted records
harvest logs
sales commitments
field maps
input application records
storage/bin/cooler records
user role
```

## Evidence required

```text
inventory item IDs
document evidence IDs
harvest event IDs
scale/load ticket IDs
last verified date
source document references
freshness metadata
```

## Actions it may draft

```text
draft inventory reconciliation
draft official record update
draft harvest/yield record
draft bin/cooler inventory update
draft document-extracted record
draft missing data request
```

All official updates remain approval-gated.

## Review triggers

```text
official record update
low-confidence extraction
missing lot number
missing source document
stale count
negative quantity
organic traceability gap
stored grain reconciliation
sensitive supplier/pricing/financial field
field employee attempting restricted view
```

## Handoffs

```text
Inventory -> Procurement:
Low stock, reorder threshold, missing inventory, stale count, lead-time issue.

Inventory -> Market + Sales:
Available harvest inventory, cooler stock, stored grain, committed vs uncommitted quantity.

Market + Sales -> Inventory:
Delivered quantities, packed quantities, returned market inventory, committed orders.

Inventory -> Compliance:
Seed-source records, input logs, lot traceability, PHI/REI-related records, organic documentation.

Inventory -> Scenario:
Actual quantities, costs, yields, shrink, culls, stored grain, inventory value assumptions.
```

## Acceptance examples

```text
DOC-001 fuel invoice creates draft fuel purchase/inventory record only.
DOC-004 packaging invoice creates draft inventory update only.
Seed lot missing germination rate -> missing data flagged.
Stored grain record is watchlist only, not sale advice.
Harvested tomatoes in cooler are tracked as available/committed/uncommitted.
Field employee can see operational readiness but not restricted valuation/pricing.
```

---

# 4. Market + Sales Agent

## Clean line

The Market + Sales Agent tracks commitments, demand, allocation, fulfillment, sales records, and market context. It may draft customer-facing messages or pack lists, but it does **not** commit sales, set prices, send messages, recommend sell/hold timing, or execute contracts.

## Should handle

```text
CSA commitments
CSA share sizes and member counts
restaurant orders
wholesale orders
farmers market prep
online store / food hub / U-pick context where modeled
harvest availability
pack lists
committed vs available quantity
allocation conflicts
shortfall/surplus detection
market-day logistics
delivery/pickup scheduling context
customer communication drafts
availability list drafts
post-market reconciliation
returned inventory
sales by channel/crop/customer
payment or pickup status
public market context as watch-only
stored grain market watch as context only
```

## Should not handle

```text
committing sales
sending customer messages
setting or changing prices
executing grain sales
recommending sell/hold timing
creating contracts
issuing invoices externally
collecting payment
disclosing restricted customer/financial details to unauthorized roles
```

## Inputs needed

```text
harvest forecasts
harvest logs
post-harvest inventory
cooler/bin inventory
CSA commitments
restaurant orders
farmers market plan
packaging inventory
AMS or public market context
stored grain records
sales records
payment status
user role
```

## Evidence required

```text
sales commitment IDs
harvest event IDs
inventory evidence IDs
market context evidence IDs
sales record IDs
delivery or pack list references
```

## Actions it may draft

```text
draft CSA newsletter
draft availability list
draft restaurant confirmation
draft market pack list
draft delivery checklist
draft sales reconciliation task
draft grain buyer inquiry, if explicitly requested and approval-gated
```

## Review triggers

```text
customer message
price change
order below standard price
shortfall affecting customer commitment
sales record update
buyer contact
grain sale inquiry
financial detail visibility
```

## Handoffs

```text
Market + Sales -> Inventory:
Committed quantities, delivered quantities, returned inventory, sales reconciliation status.

Inventory -> Market + Sales:
Available stock, cooler/bin inventory, harvest lots, stored grain.

Market + Sales -> Procurement:
Packaging shortfalls, market supplies, labels, bags, boxes.

Market + Sales -> Compliance:
Organic/food safety record needs, PHI/REI conflicts, labeling concerns.

Market + Sales -> Scenario:
Revenue assumptions, channel sales, stored grain context.
```

## Acceptance examples

```text
GBO CSA plan anchors on CSA commitments, not AMS.
Restaurant order exceeds available inventory -> shortfall flagged, draft confirmation withheld.
Same tomatoes promised to CSA and restaurant -> allocation conflict flagged.
CSA newsletter generated -> draft/needs approval before send.
AMS data is regional context only.
PVF stored grain context is watch-only, not sell/hold advice.
Order below standard price -> flagged, needs approval.
```

---

# 5. Compliance Agent

## Clean line

The Compliance Agent tracks compliance-sensitive records, deadlines, documentation gaps, safety boundaries, and expert-review needs. It records and verifies completeness, but it does **not** provide legal advice, pesticide product/rate/tank-mix advice, organic approval decisions, or official filings.

## Should handle

```text
organic certification records
Organic System Plan status
organic seed-source documentation
approved input list
OMRI/organic documentation status
certifier correspondence tracking
inspection-prep checklist
spray/crop-protection record completeness
EPA registration number as recorded fact
application date/time/location/applicator/weather as record fields
REI/PHI intervals as recorded facts
restricted-use pesticide record retention
applicator license expiration tracking
USDA acreage reporting watch
FSA/crop insurance-sensitive deadlines
NRCS/EQIP obligation watch
crop-health watchlist as observation/context only
regulated/reportable pest watch
food safety / wash-pack records
source-document linkage
audit readiness
role restrictions
```

## Should not handle

```text
pesticide product choice
application rate
tank mix
spray timing instruction
treatment recommendation
legal determination
organic approval/denial
certifier submission
regulatory filing
official record commitment
```

## Inputs needed

```text
input application logs
seed-source records
organic documentation
crop-protection records
applicator/license records
harvest and PHI/REI-related records
crop-health watchlist context
food safety records
certifier/advisor notes
user role
```

## Evidence required

```text
record evidence IDs
source documents
crop-health watchlist evidence
input documentation IDs
application log IDs
certification document IDs
deadline source references
```

## Actions it may draft

```text
draft certifier question
draft missing compliance record request
draft inspection-prep checklist
draft expert-review request
draft official record update, approval-gated
```

## Review triggers

```text
organic certification-sensitive issue
crop-protection record gap
RUP/applicator issue
PHI/REI conflict
food safety gap
USDA/crop-insurance-sensitive deadline
regulated/reportable pest concern
user asks for spray rate/product/treatment
external certifier/regulator message
```

## Handoffs

```text
Compliance -> Synthesizer:
Risk flags, expert review needs, blocked actions.

Compliance -> Procurement:
Input documentation requirements, organic/OMRI uncertainty.

Compliance -> Market + Sales:
PHI/REI or food-safety conflicts affecting harvest/sales.

Compliance -> Inventory:
Required record fields, missing source documents, traceability needs.

Compliance -> Action Agent:
Approval blockers and unsafe action restrictions.
```

## Acceptance examples

```text
IPM-003 refuses spray advice safely.
GBO organic input/certifier issue requires expert review.
PVF compliance output does not become spray planning.
Harvest scheduled inside recorded PHI window -> blocked and flagged for review.
Applicator license expires in 30 days -> watch item.
FSA acreage reporting deadline approaching with incomplete data -> missing data flagged.
Spray record missing EPA reg number -> incomplete record flagged, not committed.
User asks "what rate should I spray?" -> refused and directed to licensed advisor.
```

---

# 6. Margin + Scenario Agent

## Clean line

The Margin + Scenario Agent calculates and explains what-if math under explicit assumptions. It does **not** recommend decisions, financial commitments, sales, purchases, pricing changes, hedges, or supplier/customer actions.

It is a calculator with context, not an advisor.

## Should handle

```text
break-even calculations
cost per acre
cost per unit
contribution margin by crop/channel
side-by-side what-if comparisons
fuel cost sensitivity
fertilizer/input cost sensitivity
stored grain price/shrink/storage-cost scenarios
budget vs actual context
enterprise profitability views
CSA / restaurant / market revenue scenarios
harvest shrink/cull cost impact
yield vs expected production context
assumption display
missing data and false-precision prevention
role-based cost/margin visibility
```

## Should not handle

```text
sell/hold grain recommendations
purchase recommendations
price-setting recommendations
hedging recommendations
supplier selection
customer/order acceptance decisions
financial commitments
hidden assumptions
precise numbers when data is missing
showing restricted margin/cost details to unauthorized roles
```

## Inputs needed

```text
cost data from Procurement
inventory/yield data from Records + Inventory
sales commitments and revenue data from Market + Sales
compliance constraints where relevant
weather/yield assumptions where relevant
public benchmark context if clearly labeled
user role
```

## Evidence required

```text
input cost evidence IDs
inventory evidence IDs
yield/harvest evidence IDs
sales record evidence IDs
quote evidence IDs
assumption list
missing data list
```

## Actions it may draft

Usually none.

It may create:

```text
scenario summary
assumption checklist
missing-data request
```

It should not create purchase, sale, hedge, or customer actions.

## Review triggers

```text
scenario implies financial commitment
missing cost basis
missing yield estimate
missing local bid/basis
missing fees
field employee requesting restricted margin data
```

## Handoffs

```text
Procurement -> Scenario:
Actual input costs, quote terms, missing fees.

Inventory -> Scenario:
Yields, stored grain, harvest quantities, shrink, culls, cost basis.

Market + Sales -> Scenario:
Revenue assumptions, customer/channel commitments, sales records.

Scenario -> Synthesizer:
Math-only findings with assumptions and missing data.
```

## Acceptance examples

```text
Stored grain scenario math is illustrative, not sell/hold advice.
Fuel cost scenario uses actual procurement costs when available.
Break-even with no yield estimate -> missing data, no false precision.
Crop margin comparison shows math and assumptions, no "choose this."
Fertilizer price what-if -> scenario only, no purchase recommendation.
Financial commitment implied -> blocked / approval needed; no commitment made.
```

---

# 7. Recommendation Synthesizer

## Clean line

The Recommendation Synthesizer turns AgentFindings into a concise, evidence-backed, role-appropriate ActionPack. It organizes and prioritizes findings. It does **not** create unsupported domain decisions, approve actions, execute actions, or invent missing facts.

## Should handle

```text
combine AgentFindings
prioritize findings
deduplicate overlapping findings
create weekly plan sections
preserve evidence IDs
preserve assumptions
preserve missing data
preserve confidence and review status
distinguish context vs recommendation vs draft action
keep farm-specific records as decision anchors
keep public data as context only
tailor output by user role
avoid output crowding
surface approval requirements
prepare proposed draft actions for Action Agent review
```

## Should not handle

```text
call connectors directly
query credentials
invent prices, yields, quantities, dates, fees, or customers
override agent findings without evidence
hide missing data
remove evidence trails
execute actions
approve actions
send messages
select suppliers
recommend sales
recommend pesticide products/rates/tank mixes
show restricted information to unauthorized roles
```

## Inputs needed

```text
AgentFindings
EvidenceBoard items
human-review policy results
user role
farm type
workflow intent
proposed actions from agents
```

## Evidence required

```text
all recommendation evidence IDs
source names
freshness labels
connector modes
document references
public-context vs farm-specific labels
```

## Actions it may draft

It may assemble proposed actions from agents into the ActionPack:

```text
draft supplier message
draft customer message
draft certifier message
draft official record update
draft inventory reconciliation
draft pack list
draft review request
```

But it does not approve or execute them.

## Review triggers

```text
any underlying finding requires review
any proposed action requires approval
missing data blocks action
restricted information is present
role cannot view full detail
```

## Handoffs

```text
All specialist agents -> Synthesizer:
AgentFindings and proposed draft actions.

Synthesizer -> Action Agent:
Proposed actions and review metadata.

Synthesizer -> User:
Final ActionPack.
```

## Acceptance examples

```text
CSA box shortage from Inventory + Market + Procurement becomes one combined recommendation.
Fertilizer fee gaps remain visible; no purchase action executed.
Stored grain appears as watch-only, not sell/hold advice.
AMS data appears only as regional context.
Field employee weekly plan hides supplier pricing and draft supplier actions.
Low-confidence document extraction becomes needs_info.
ActionPack includes evidence summary, missing data, review status, and draft actions.
```

---

# 8. Action Agent

## Clean line

The Action Agent enforces the boundary between "HarvestAmp drafted something" and "something happened." It classifies, validates, blocks, or allows simulated approval of proposed actions. It does **not** decide what the farmer should do and does not execute external actions in the current MVP.

## Should handle

```text
receive proposed actions
classify action type
classify risk tier
check approval requirements
check reviewer authorization
block missing-info actions
validate action payload completeness
preserve evidence links
redact sensitive material
enforce role restrictions
record audit events
prevent unsafe escalation
prevent duplicate action spam
keep approved actions simulated/local only
```

## Should not handle

```text
make domain recommendations
rank weekly plan items
call specialist agents
call connectors
invent missing data
approve its own actions
send email
place orders
contact suppliers
contact customers
contact certifiers
file documents
update official records
commit inventory truth
sell grain
create contracts
make financial commitments
recommend pesticide actions
expose secrets
```

## Inputs needed

```text
proposed action payload
farm_id
user role
human-review status
approval blockers
evidence IDs
sensitivity labels
missing data
current simulated approval state
```

## Evidence required

```text
source_evidence_id
related recommendation ID
farm_id
action ID
approval status
audit event ID
```

## Actions it may allow locally

```text
approved_simulated
rejected
needs_info
blocked_pending_user_approval
blocked_pending_expert_review
not_executed
```

No real external execution should happen in the current MVP.

## Review triggers

```text
supplier message
customer message
certifier/regulator message
purchase/order
official record update
inventory truth update
sales record update
grain sale inquiry
financial commitment
crop-protection action
restricted document action
field employee approval attempt
sensitive content detected
```

## Handoffs

```text
Synthesizer -> Action Agent:
Proposed actions and review metadata.

Action Agent -> Audit Logger:
Decision events.

Action Agent -> Review Queue, future:
Pending approval items.

Action Agent -> User:
Clear action status: draft, blocked, needs_info, approved_simulated, rejected.
```

## Acceptance examples

```text
Fuel supplier inquiry -> draft, blocked pending owner approval.
CSA box reorder inquiry -> draft only; no message sent.
Field employee tries to approve supplier message -> denied.
Document-extracted fuel invoice -> draft official record update only.
Low-confidence extraction -> needs_info, cannot approve.
Sensitive payment content -> redacted; raw values never appear.
Restaurant availability email -> draft/needs approval.
Stored grain sale watch -> no sale action without owner approval and current bid/basis.
Crop-health watchlist -> cannot create spray crew instruction.
```

---

# Cross-Agent Principles

## 1. Farm-specific data beats public context

```text
Farm records, uploaded documents, inventory, quotes, commitments, harvest logs, and sales records are decision anchors.

Public connectors and benchmarks are context only.
```

## 2. Missing data must stay visible

Agents should not fill gaps with guesses.

```text
No invented prices.
No invented dates.
No invented yields.
No invented fees.
No invented supplier/customer facts.
```

## 3. Draft means draft

A draft action is not an executed action.

```text
No external message sent.
No official record updated.
No order placed.
No sale committed.
No compliance filing submitted.
```

## 4. Role visibility matters

Field employees may see operationally useful information, but not:

```text
supplier pricing
margin
buyer/customer terms
restricted document values
financial details
sensitive compliance details
```

## 5. Agents should stay in their lane

When an issue crosses domains, agents should hand off rather than expand beyond their scope.

Example:

```text
Weather identifies a possible fieldwork window.
Inventory checks fuel/equipment/PPE readiness.
Procurement drafts quote/reorder actions if needed.
Compliance blocks unsafe or sensitive actions.
Scenario shows math only.
Synthesizer assembles the plan.
Action Agent gates execution.
```

---

# Status

This document represents Step 1: Agent Domain Map.

The next planning document should be `docs/SUPERVISOR_ROUTING_MAP.md`, defining which agents the Supervisor calls for each major user request type.
