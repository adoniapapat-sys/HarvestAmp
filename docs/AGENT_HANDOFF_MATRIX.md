# HarvestAmp Agent Handoff Matrix

## Purpose

This document defines how HarvestAmp agents pass findings, constraints, and context to one another without overlapping chaotically.

The handoff matrix complements:

```text
docs/AGENT_DOMAIN_MAP.md
docs/AGENT_DATA_SOURCE_MAP.md
docs/SUPERVISOR_ROUTING_MAP.md
```

- `AGENT_DOMAIN_MAP.md` defines what each agent owns.
- `AGENT_DATA_SOURCE_MAP.md` defines what each agent needs and where the data comes from.
- `SUPERVISOR_ROUTING_MAP.md` defines when the Supervisor calls each agent.
- `AGENT_HANDOFF_MATRIX.md` defines how agent findings should flow across agent boundaries.

Core rule:

```text
Agents do not take over each other's jobs.
Agents pass evidence-backed findings, constraints, and missing-data flags.
The Supervisor coordinates routing.
The Synthesizer assembles the final ActionPack.
The Action Agent gates proposed actions.
```

---

## Shared Handoff Contract

Every handoff should preserve enough structure that the receiving agent can use it without guessing.

Recommended handoff fields:

```yaml
handoff_id: string
from_agent: string
to_agent: string
farm_id: string
workflow_id: string
handoff_type: inventory_signal | market_commitment | compliance_constraint | weather_constraint | cost_context | scenario_context | proposed_action | missing_data | role_visibility
summary: string
details: {}
evidence_ids: []
source_freshness: current | recent | stale | unavailable | unknown
confidence: high | medium | low | insufficient_data
missing_data: []
assumptions: []
role_visibility:
  farm_owner: visible | restricted | hidden
  farm_manager: visible | restricted | hidden
  field_employee: visible | restricted | hidden
human_review:
  required: boolean
  review_type: none | soft_confirmation | user_approval | expert_review | admin_review | blocked
  status: review_not_required | needs_info | needs_user_approval | needs_expert_review | blocked
action_boundary:
  external_action_allowed: false
  draft_only: true
  approval_required_before: []
```

Minimum expectation:

```text
No handoff should lose evidence IDs, freshness, confidence, missing data, role visibility, or human-review state.
```

---

## Handoff Principles

### 1. The sender provides facts, not decisions outside its lane

Example:

```text
Records + Inventory may say CSA boxes are below threshold.
Procurement may draft a reorder inquiry.
Action Agent decides whether that draft is blocked or approval-gated.
```

### 2. The receiver must not treat context as permission

Example:

```text
Market + Sales may receive available inventory.
That does not mean it can commit a sale or send a customer message.
```

### 3. Public context stays public context

Example:

```text
AMS, EIA, NASS, weather, and crop-health watchlists can be handed off as context.
They do not override farm-specific records, quotes, inventory, harvest logs, or sales commitments.
```

### 4. Missing data should travel with the handoff

Example:

```text
Stored grain quantity may be known, but local bid/basis may be missing.
The Scenario Agent must preserve that missing-data flag and avoid false precision.
```

### 5. Role restrictions travel with the handoff

Example:

```text
Procurement can pass a supplier quote to Scenario for a farm_owner.
That same price detail must be hidden or summarized for a field_employee.
```

---

# Agent-to-Agent Handoff Matrix

## 1. Weather + Fieldwork Agent Handoffs

### Weather + Fieldwork → Records + Inventory

**Passes:**

```text
weather-dependent operation windows
weather-related readiness constraints
forecast freshness
fallback weather status
rain/wind/heat/frost constraints
high-tunnel or irrigation watch context
```

**Used by Records + Inventory to check:**

```text
fuel readiness
equipment readiness
harvest-supply readiness
PPE readiness
irrigation supplies
storage/cooler/bin risks if weather-sensitive
```

**Example:**

```text
Friday is the best fieldwork window.
Records + Inventory checks diesel, equipment, PPE, and parts readiness before that window.
```

**Boundary:**

Weather does not decide that the operation should happen.

---

### Weather + Fieldwork → Procurement

**Passes:**

```text
upcoming fieldwork windows
weather-sensitive seasonal timing
market-day weather constraints
harvest-window constraints
irrigation/dryness watch context
```

**Used by Procurement to check:**

```text
fuel needs
parts and equipment supplies
harvest supplies
packaging and market setup supplies
irrigation supplies
```

**Example:**

```text
A dry fieldwork window is likely Friday.
Procurement checks whether fuel or parts require a quote/reorder draft.
```

**Boundary:**

Procurement may draft quote/reorder actions only; no purchase is made.

---

### Weather + Fieldwork → Market + Sales

**Passes:**

```text
market-day weather risk
harvest rain conflict
heat/frost risk affecting harvest timing
high-tunnel or greenhouse risk
delivery weather context
```

**Used by Market + Sales to check:**

```text
market setup risk
harvest/pack/delivery timing
farmers market packing plans
CSA pickup constraints
restaurant delivery concerns
```

**Example:**

```text
Saturday market has rain and wind risk.
Market + Sales adds tent weights and rain-cover needs to the market plan.
```

**Boundary:**

Weather does not change customer commitments or send messages.

---

### Weather + Fieldwork → Compliance

**Passes:**

```text
weather context relevant to records
weather freshness
weather conditions attached to application records
safety-sensitive weather conditions
```

**Used by Compliance to check:**

```text
application record completeness
weather-log completeness
PHI/REI or crop-protection record context
worker-safety concerns
```

**Example:**

```text
Application record is missing weather conditions.
Compliance flags incomplete recordkeeping.
```

**Boundary:**

Weather context must not become spray timing advice.

---

### Weather + Fieldwork → Margin + Scenario

**Passes:**

```text
weather assumptions
harvest delay context
fieldwork timing assumptions
irrigation/dryness assumptions
market-day disruption context
```

**Used by Scenario for:**

```text
what-if math under assumptions
weather-delay sensitivity
harvest loss/shrink assumptions if evidence-backed
```

**Boundary:**

Scenario labels assumptions and does not recommend operational decisions.

---

## 2. Records + Inventory Agent Handoffs

### Records + Inventory → Procurement

**Passes:**

```text
low stock
stale count
reorder threshold
target stock level
lead-time concern
lot constraints
missing quantity
storage location
expiration/shelf-life watch
draft record status
```

**Used by Procurement to:**

```text
draft quote inquiries
draft reorder inquiries
flag missing fees or supplier terms
compare quotes against actual inventory need
avoid reorder if inventory count is stale or uncertain
```

**Examples:**

```text
CSA boxes below threshold → Procurement drafts box reorder inquiry.
Diesel below operating need → Procurement drafts fuel quote inquiry.
Seed count stale → Procurement asks for count verification before reorder.
```

**Boundary:**

Inventory does not choose suppliers or buy. Procurement does not commit purchases.

---

### Records + Inventory → Market + Sales

**Passes:**

```text
available inventory
committed inventory
uncommitted inventory
harvest lots
cooler inventory
bin quantities
packed quantities
returned market inventory
stored grain quantity
quality grade
shelf-life watch
lot/batch traceability
```

**Used by Market + Sales to:**

```text
build pack lists
check CSA/restaurant fulfillment
flag shortfalls or oversold quantities
prepare draft availability lists
reconcile market returns
provide stored grain watch context
```

**Examples:**

```text
96 lb tomatoes available, 70 lb committed → Market + Sales flags 26 lb uncommitted.
42,000 bu corn stored → Market + Sales can show stored grain watch, not sell advice.
```

**Boundary:**

Market + Sales cannot commit sales or send customer messages without approval.

---

### Records + Inventory → Compliance

**Passes:**

```text
seed lot records
organic documentation status
input inventory records
application logs
harvest lot traceability
wash-pack or food-safety records
stored grain records
document-extracted draft records
official record status
missing fields
```

**Used by Compliance to:**

```text
flag certification gaps
flag incomplete crop-protection records
check traceability requirements
identify inspection-prep gaps
route official record updates to review
```

**Examples:**

```text
Organic seed lot lacks documentation → Compliance flags expert/certifier review.
Spray record missing EPA reg number → Compliance flags incomplete record.
Harvest lot lacks traceability → Compliance flags food-safety/organic gap.
```

**Boundary:**

Compliance flags gaps; it does not approve organic status or file records.

---

### Records + Inventory → Margin + Scenario

**Passes:**

```text
inventory quantities
actual yield records
stored grain quantities
harvested quantities
marketable/cull quantities
packout
shrink
cost basis where available
documented input usage
```

**Used by Scenario to:**

```text
calculate cost per acre
calculate cost per unit
calculate break-even math
model stored grain what-ifs
show shrink/cull impact
show enterprise/channel math
```

**Examples:**

```text
Field 12 corn yield and input costs → Scenario can calculate cost per bushel.
Tomato cull percentage → Scenario can show packout/shrink impact.
```

**Boundary:**

Scenario shows math only; no sell/buy/price recommendation.

---

### Records + Inventory → Action Agent

**Passes:**

```text
draft official record update
draft inventory reconciliation
draft document-extracted record
source evidence ID
confidence
missing fields
approval blockers
```

**Used by Action Agent to:**

```text
block official updates pending approval
deny approval when fields are missing
preserve audit trail
prevent low-confidence updates
```

**Example:**

```text
Fuel invoice extraction → draft fuel purchase record → Action Agent blocks until owner approval.
```

**Boundary:**

No official inventory or record update is committed in the MVP.

---

## 3. Procurement Agent Handoffs

### Procurement → Records + Inventory

**Passes:**

```text
quote terms
expected incoming quantity
delivery date if known
draft order quantity
quote-to-invoice mismatch
supplier documentation
missing fee/term flags
```

**Used by Records + Inventory to:**

```text
prepare draft receiving records
flag incoming inventory
link quote/invoice evidence
avoid duplicate records
identify record gaps
```

**Example:**

```text
CSA box reorder draft for 250 boxes → Inventory can prepare draft expected inventory, not commit stock.
```

**Boundary:**

Expected incoming inventory is not on-hand inventory until officially received/approved.

---

### Procurement → Compliance

**Passes:**

```text
input quote
supplier documentation
OMRI/organic status
restricted-use status
label/document availability
missing compliance documentation
```

**Used by Compliance to:**

```text
flag unverified organic inputs
flag restricted-use concerns
flag missing documentation
require expert/certifier review
```

**Example:**

```text
Organic fertilizer quote lacks OMRI documentation → Compliance flags expert/certifier review.
```

**Boundary:**

Compliance does not approve the input; Procurement does not buy it.

---

### Procurement → Margin + Scenario

**Passes:**

```text
actual quote prices
fuel costs
fertilizer costs
seed costs
packaging costs
delivery/application fees
missing fee assumptions
quote validity window
```

**Used by Scenario to:**

```text
calculate cost sensitivity
calculate cost per acre/unit
show break-even assumptions
compare input-cost scenarios
```

**Example:**

```text
Urea and UAN quotes with missing delivery fees → Scenario can show material-only comparison and flag missing fee assumptions.
```

**Boundary:**

Scenario math does not become purchase recommendation.

---

### Procurement → Synthesizer

**Passes:**

```text
procurement finding
draft supplier inquiry
missing fees
quote expiration
role visibility restriction
evidence IDs
approval requirement
```

**Used by Synthesizer to:**

```text
create concise procurement section
combine low inventory + quote needs
surface draft actions
preserve evidence and missing data
```

**Example:**

```text
Low diesel + valid quote + EIA context → Synthesizer shows fuel watch and draft quote inquiry.
```

---

### Procurement → Action Agent

**Passes:**

```text
draft supplier message
draft quote request
draft reorder inquiry
financial action metadata
approval threshold
source evidence
```

**Used by Action Agent to:**

```text
block sending until approval
deny unauthorized role approval
preserve draft-only status
```

**Example:**

```text
Supplier quote inquiry → Action Agent keeps it blocked pending owner approval.
```

---

## 4. Market + Sales Agent Handoffs

### Market + Sales → Records + Inventory

**Passes:**

```text
committed quantities
packed quantities
delivered quantities
returned inventory
unsold inventory
sales reconciliation status
customer/order commitments
channel allocation
```

**Used by Records + Inventory to:**

```text
update draft inventory reconciliation
track cooler/bin changes
track returned inventory
link sales to inventory movement
identify stock conflicts
```

**Examples:**

```text
Farmers market returns 18 lb tomatoes → Inventory drafts returned cooler inventory.
Restaurant delivery consumes 40 lb tomatoes → Inventory drafts committed/delivered quantity movement.
```

**Boundary:**

Inventory updates remain draft until reviewed/approved.

---

### Market + Sales → Procurement

**Passes:**

```text
packaging demand
market supplies demand
label/bag/box needs
harvest supply needs
customer/channel-driven reorder need
```

**Used by Procurement to:**

```text
draft packaging/supply reorder inquiries
check lead times
compare quote terms
```

**Example:**

```text
75 CSA shares + low CSA boxes → Procurement drafts CSA box reorder inquiry.
```

**Boundary:**

Procurement drafts only; no purchase.

---

### Market + Sales → Compliance

**Passes:**

```text
harvest schedule
customer/channel commitments
lot/batch destination
sales channel
delivery date
food safety record needs
organic label/claim context
potential PHI/REI conflict
```

**Used by Compliance to:**

```text
check harvest record requirements
flag PHI/REI conflicts
flag organic/food-safety documentation needs
flag labeling/claim concerns
```

**Example:**

```text
Tomatoes planned for restaurant delivery → Compliance checks lot traceability and organic/food-safety record status.
```

**Boundary:**

Compliance can block or flag; it does not send customer messages.

---

### Market + Sales → Margin + Scenario

**Passes:**

```text
channel revenue assumptions
sales records
commitments
standard prices
below-standard-price flags
payment status
returned inventory
packout/shrink from sales channel
```

**Used by Scenario to:**

```text
calculate channel margin
show budget vs actual
show revenue what-if
show shrink/returns impact
```

**Example:**

```text
Farmers market sales and returned inventory → Scenario can calculate channel revenue and shrink context.
```

**Boundary:**

Scenario does not recommend price changes or sales decisions.

---

### Market + Sales → Action Agent

**Passes:**

```text
draft customer message
draft availability list
draft order confirmation
draft delivery note
draft sales record update
grain buyer inquiry draft
approval requirement
```

**Used by Action Agent to:**

```text
block customer-facing messages until approval
block sales record updates pending approval
block grain buyer contact unless authorized
```

**Example:**

```text
CSA newsletter draft → Action Agent blocks send pending owner approval.
```

---

## 5. Compliance Agent Handoffs

### Compliance → Procurement

**Passes:**

```text
organic documentation requirement
OMRI status unknown
restricted-use flag
label/document requirement
expert review requirement
certifier review requirement
```

**Used by Procurement to:**

```text
block or qualify input/reorder drafts
request missing documentation
avoid unsafe supplier/order recommendations
```

**Example:**

```text
Input quote has unknown organic status → Procurement can request documentation, not order.
```

---

### Compliance → Records + Inventory

**Passes:**

```text
required record fields
missing documentation
retention requirement
traceability requirement
draft official record warning
inspection-prep gap
```

**Used by Records + Inventory to:**

```text
flag incomplete records
link missing documents
prepare draft record updates
track audit readiness
```

**Example:**

```text
Spray record missing weather conditions → Inventory/Records marks record incomplete.
```

---

### Compliance → Market + Sales

**Passes:**

```text
PHI/REI conflict
organic documentation requirement
food safety record gap
labeling/claim concern
regulated pest concern
harvest/sales restriction context
```

**Used by Market + Sales to:**

```text
flag fulfillment constraints
withhold draft confirmations
surface missing compliance information
avoid customer-facing claims without review
```

**Example:**

```text
Harvest scheduled inside recorded PHI window → Market + Sales cannot treat crop as available for sale.
```

**Boundary:**

Compliance flags constraints; Market + Sales does not override them.

---

### Compliance → Weather + Fieldwork

**Passes:**

```text
weather record requirement
application record completeness need
safety-sensitive context
fieldwork constraint from compliance record
```

**Used by Weather to:**

```text
surface conditions without turning them into treatment instructions
include weather freshness when a compliance record needs it
```

**Example:**

```text
Compliance needs weather conditions for record completeness → Weather provides evidence-backed weather context only.
```

---

### Compliance → Margin + Scenario

**Passes:**

```text
compliance constraint
record gap
expert review requirement
organic-sensitive limitation
official-record uncertainty
```

**Used by Scenario to:**

```text
mark numbers as incomplete
exclude non-compliant assumptions
label scenario as illustrative only
```

**Example:**

```text
Organic input status unknown → Scenario can show cost math but must flag certification uncertainty.
```

---

### Compliance → Action Agent

**Passes:**

```text
approval blocker
expert review requirement
blocked action reason
unsafe request flag
restricted disclosure warning
official-record sensitivity
```

**Used by Action Agent to:**

```text
block unsafe proposed actions
require expert review
deny unauthorized approval
prevent external messages or official filings
```

**Example:**

```text
User asks for spray rate → Compliance refusal → Action Agent receives no executable action.
```

---

## 6. Margin + Scenario Agent Handoffs

### Margin + Scenario → Synthesizer

**Passes:**

```text
scenario math
assumptions
sensitivity drivers
missing data
confidence
evidence IDs
role visibility constraints
watch-only label
```

**Used by Synthesizer to:**

```text
show concise scenario context
avoid false precision
keep math separate from recommendations
```

**Example:**

```text
Stored grain price-level math with missing local basis → Synthesizer shows watch-only scenario and missing-data note.
```

---

### Margin + Scenario → Procurement

**Passes:**

```text
cost sensitivity context
input cost driver
break-even sensitivity
missing fee impact
budget-vs-actual context
```

**Used by Procurement to:**

```text
prioritize quote completeness
flag missing fees
show cost sensitivity without making purchase decision
```

**Example:**

```text
Fertilizer delivery fee materially changes cost per acre → Procurement requests fee clarification.
```

**Boundary:**

Scenario does not tell Procurement to buy.

---

### Margin + Scenario → Market + Sales

**Passes:**

```text
channel margin context
stored grain math-only context
price-level what-if
sales reconciliation math
return/shrink impact
```

**Used by Market + Sales to:**

```text
surface context in sales planning
flag missing bid/basis
show math without price-setting or sell/hold advice
```

**Example:**

```text
Scenario shows stored corn value at multiple price points → Market + Sales presents watch-only context.
```

**Boundary:**

No sell/hold/price-setting recommendation.

---

### Margin + Scenario → Action Agent

**Passes:**

Usually none.

If a scenario output is attached to a proposed financial action, it passes:

```text
financial implication
missing data
approval requirement
assumption list
```

**Used by Action Agent to:**

```text
block financial commitments without approval
block false-precision actions when data is missing
```

**Example:**

```text
Scenario attached to grain buyer inquiry → Action Agent blocks until owner approval and current bid/basis are available.
```

---

## 7. Synthesizer Handoffs

### Synthesizer → Action Agent

**Passes:**

```text
proposed actions
action payloads
source evidence IDs
related recommendation IDs
human-review metadata
role visibility
approval blockers
missing-data blockers
sensitivity labels
```

**Used by Action Agent to:**

```text
classify action type
validate payload completeness
block or mark draft
record audit events
enforce review and role boundaries
```

**Examples:**

```text
Draft fuel inquiry → Action Agent blocks pending owner approval.
Draft official record update → Action Agent blocks pending review.
Draft customer newsletter → Action Agent blocks pending approval.
```

---

### Synthesizer → User

**Passes:**

```text
final ActionPack
recommendations
evidence summary
missing data
assumptions
review status
draft actions and statuses
privacy notes
audit-event summary
```

**Boundary:**

Synthesizer must not imply that draft actions were executed.

---

## 8. Action Agent Handoffs

### Action Agent → Audit Logger

**Passes:**

```text
action_id
farm_id
user_id
action_type
decision
approval status
blocked reason
timestamp
evidence IDs
```

**Used by Audit Logger to:**

```text
record approval, block, rejection, needs_info, approved_simulated, or draft decisions
```

---

### Action Agent → Review Queue, future

**Passes:**

```text
pending action
required reviewer
approval blockers
evidence IDs
sensitivity labels
payload preview
redaction status
```

**Used by Review Queue to:**

```text
list pending approvals
support approve/reject/needs_info
preserve audit trail
```

**Boundary:**

Review Queue approval remains local/simulated until real integrations are intentionally built.

---

### Action Agent → User

**Passes:**

```text
draft
blocked_pending_user_approval
needs_info
needs_expert_review
approved_simulated
rejected
not_executed
```

**Boundary:**

The user sees clear action state. No external execution is implied.

---

# Common Cross-Agent Handoff Scenarios

## Scenario A: Low CSA boxes before packing

```text
Records + Inventory:
CSA boxes are below threshold.

Market + Sales:
75 CSA shares require packing Thursday.

Procurement:
Draft CSA box reorder inquiry.

Compliance:
No compliance blocker unless organic/labeling/certifier issue exists.

Synthesizer:
One combined packaging recommendation.

Action Agent:
Blocks supplier message pending owner approval.
```

---

## Scenario B: Fertilizer quote missing fees

```text
Procurement:
Urea and UAN quotes available, but delivery/application fees missing.

Records + Inventory:
Current fertilizer/amendment stock and need context.

Scenario:
Material-only cost comparison possible; full cost comparison blocked by missing fees.

Compliance:
No agronomic rate/timing recommendation.

Synthesizer:
Shows missing fee gap and no purchase action.

Action Agent:
No order; any supplier inquiry is draft/approval-gated.
```

---

## Scenario C: Harvest inventory for restaurant order

```text
Records + Inventory:
150 lb marketable tomatoes harvested, 96 lb in cooler.

Market + Sales:
40 lb committed to restaurant, 50 lb planned for CSA.

Compliance:
Organic/food-safety/lot traceability required.

Procurement:
Packaging or harvest supply reorder if short.

Scenario:
Optional channel math if user is authorized.

Synthesizer:
Pack/fulfillment plan with missing data and evidence.

Action Agent:
Blocks customer message or sales record update until approval.
```

---

## Scenario D: Stored grain watch

```text
Records + Inventory:
42,000 bu corn stored, last reconciled date known or stale.

Market + Sales:
Stored grain watch context only.

Scenario:
Price-level math only if assumptions or local bid/basis are available.

Compliance:
Crop insurance / production record caution if official records are involved.

Synthesizer:
Watch-only stored grain section.

Action Agent:
No sale, buyer contact, hedge, or contract without owner approval.
```

---

## Scenario E: User asks what to spray

```text
Supervisor:
Routes to Compliance safety boundary.

Compliance:
Refuses product/rate/tank-mix/treatment advice.
May suggest scouting, diagnosis confirmation, extension guidance, label/legal review, and qualified advisor review.

Weather:
May provide weather conditions only if explicitly requested and scoped safely.

Procurement:
Not called for product selection.

Scenario:
Not called for treatment economics.

Synthesizer:
Safe refusal/redirect.

Action Agent:
No proposed executable action.
```

---

# Handoff Anti-Patterns

Avoid these patterns:

```text
Weather → Compliance:
Weather says "spray tomorrow morning."

Inventory → Market + Sales:
Inventory availability becomes automatic customer commitment.

Market + Sales → Action Agent:
Customer message is marked sent without approval.

Procurement → Inventory:
Expected order quantity becomes on-hand inventory.

Scenario → Market + Sales:
Price-level math becomes "sell now."

Crop-health watchlist → Procurement:
Pest watch becomes chemical purchase suggestion.

Compliance → Procurement:
Unverified organic input is treated as approved.

Synthesizer → User:
Draft action wording implies execution.

Action Agent → External system:
External write occurs without explicit integration and approval.
```

---

# Acceptance Criteria

A correct implementation of this handoff model should satisfy:

```text
Evidence IDs survive every handoff.
Missing data survives every handoff.
Role restrictions survive every handoff.
Human-review requirements survive every handoff.
Farm-specific data remains the decision anchor.
Public context remains context only.
Inventory owns stock truth.
Procurement owns quote/reorder drafts.
Market + Sales owns commitments, fulfillment, and sales context.
Compliance owns recordkeeping, certification, safety, and regulatory constraints.
Scenario owns math-only context.
Synthesizer owns ActionPack assembly.
Action Agent owns action gating.
No handoff creates external execution by itself.
No handoff turns context into a recommendation outside the receiver's lane.
```

---

# Relationship to Future Work

This handoff matrix should guide the next implementation slices:

```text
1. Harvest + Yield + Post-Harvest Inventory + Sales
2. Full Inventory Taxonomy Expansion
3. Agent-specific hardening tests
4. Review Queue + Approval Simulation
5. Google Drive read-only ingestion
6. Gmail ingestion later
```

Before hardening individual agents, use this matrix to decide what each agent may pass and receive.
