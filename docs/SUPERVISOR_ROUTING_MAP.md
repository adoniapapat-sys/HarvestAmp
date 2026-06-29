# HarvestAmp Supervisor Routing Map

## Purpose

This document defines how the HarvestAmp Supervisor should route user requests to specialist agents, the Recommendation Synthesizer, and the Action Agent.

The Supervisor is the coordinator. It should not become a giant domain agent. It should:

1. Interpret the user request.
2. Identify the farm, user role, workflow intent, and risk level.
3. Build a task-scoped context package.
4. Request only the capabilities needed for the workflow.
5. Route context to the relevant agents.
6. Collect AgentFindings.
7. Send findings to the Recommendation Synthesizer.
8. Apply review and approval policy.
9. Pass proposed actions to the Action Agent.
10. Return a role-appropriate ActionPack with evidence, missing data, review status, and draft action state.

Core rule:

```text
Supervisor orchestrates.
Specialist agents produce findings.
Synthesizer assembles the ActionPack.
Action Agent gates proposed actions.
Humans approve or reject actions.
```

The Supervisor should not directly buy, sell, send messages, file records, update official records, recommend pesticide actions, or make financial commitments.

---

## Routing Principles

### 1. Route by workflow intent

The Supervisor should route based on the user's actual request, not by always calling every agent.

A broad weekly-plan request may call all core farm-domain agents. A narrow inventory request should call only the agents needed for inventory and possible reorder context.

### 2. Use task-scoped context packages

Each agent should receive only the context it needs.

Examples:

```text
Weather + Fieldwork receives forecast, operation windows, freshness, and fallback status.
Procurement receives quote, inventory threshold, supplier, and fee data.
Records + Inventory receives inventory, document, harvest, yield, and record data.
Market + Sales receives commitments, available inventory, packout, sales, and fulfillment data.
Compliance receives certification, input, application, food-safety, and official-record context.
Margin + Scenario receives evidence-backed cost, quantity, yield, revenue, and assumption data.
```

### 3. Preserve the source of every claim

Every routed package should include evidence IDs and source metadata where possible:

```text
source name
evidence_id
freshness
connector mode
farm-specific vs public-context label
role visibility
missing-data flags
```

### 4. Farm-specific data beats public context

Farm-specific records, uploaded documents, inventory, quotes, harvest logs, sales commitments, and actual sales records are decision anchors.

Public data sources such as weather, AMS, EIA, NASS, crop-health watchlists, or extension context are awareness/context unless a farm-specific workflow explicitly uses them as assumptions.

### 5. Role visibility applies before and after routing

The Supervisor should consider role visibility before routing sensitive context. It should not pass restricted financial, supplier, customer, or margin details into an agent context package for a user who is not authorized to see them.

### 6. Missing data should constrain routing and output

If a workflow depends on missing data, the Supervisor should route enough context to identify the gap, but the Synthesizer should not hide the gap and the Action Agent should not allow action execution.

### 7. External actions are not executed in the MVP

The Supervisor may produce proposed draft actions through the Synthesizer and Action Agent, but the current MVP remains local/simulated.

### 8. External data, MCP, and credential boundaries

The Supervisor may request abstract capabilities, but it must not directly call external providers or handle credentials. External data access, including MCP servers, must be mediated through the ToolGateway and Credential Broker. Specialist agents receive scoped, sanitized, evidence-backed context only.

No specialist agent may import connector classes, MCP clients, API clients, OAuth clients, or secret managers directly.

---

## Broad Weekly Plan Routing

For a broad request such as:

```text
What should I know about my farm this week?
```

Recommended routing order:

```text
1. Weather + Fieldwork Agent
2. Records + Inventory Agent
3. Procurement Agent
4. Market + Sales Agent
5. Compliance Agent
6. Margin + Scenario Agent, optional/lightweight
7. Recommendation Synthesizer
8. Action Agent
```

Rationale:

- Weather affects fieldwork, harvest, market setup, irrigation watch, and operational timing.
- Records + Inventory provides the farm's current operational truth.
- Procurement uses inventory and seasonal windows to identify quote/reorder needs.
- Market + Sales uses harvest, inventory, commitments, delivery, and market context.
- Compliance reviews recordkeeping, organic, food safety, crop-protection, and official-record sensitivities.
- Margin + Scenario runs only math/context where evidence-backed inputs exist.
- Synthesizer turns findings into the ActionPack.
- Action Agent gates draft actions.

---

## Request-Type Routing Table

| User request type | Primary agents | Supporting agents | Usually do not call | Routing notes |
|---|---|---|---|---|
| Weekly farm plan | Weather, Records + Inventory, Procurement, Market + Sales, Compliance | Margin + Scenario | None, if broad request | Full ActionPack with evidence, missing data, role scoping, and draft actions. |
| Weather / fieldwork window | Weather | Records + Inventory, Compliance if crop-protection or safety-sensitive | Procurement, Market + Sales, Scenario unless relevant | Weather reports windows and constraints only. |
| Harvest planning | Weather, Records + Inventory, Market + Sales, Compliance | Procurement, Scenario | None if broad harvest workflow | Handles harvest window, available inventory, commitments, PHI/REI/food-safety context. |
| Harvest result entry | Records + Inventory | Market + Sales, Compliance, Scenario | Procurement unless reorder/packaging affected | Creates draft harvest/yield/post-harvest inventory record only. |
| Yield summary | Records + Inventory | Scenario, Compliance | Procurement unless input-cost context requested | Field/block/bin/crop yield records; no official production filing without approval. |
| Cooler or bin inventory check | Records + Inventory | Market + Sales, Procurement, Scenario | Weather unless storage risk/weather relevant | Inventory truth layer; may trigger reorder or sales-fulfillment context. |
| CSA pack list | Market + Sales, Records + Inventory | Weather, Compliance, Procurement | Scenario unless cost/margin asked | Uses commitments and available inventory; customer messages draft only. |
| Restaurant or wholesale order | Market + Sales, Records + Inventory | Compliance, Procurement | Scenario unless margin asked | Checks availability, shortfall, delivery status; no customer message without approval. |
| Farmers market prep | Market + Sales, Records + Inventory, Weather | Procurement, Compliance | Scenario unless performance/cost asked | Pack list, setup supplies, weather risk, returned inventory reconciliation. |
| Sales reconciliation | Market + Sales, Records + Inventory | Scenario, Compliance | Weather, Procurement unless follow-up needed | Payment/delivery/returned inventory tracking; reporting only. |
| Stored grain watch | Records + Inventory, Market + Sales, Scenario | Compliance | Weather, Procurement unless storage/input context needed | Watch-only; never sell/hold advice. |
| Input quote review | Procurement | Records + Inventory, Compliance, Scenario | Market + Sales unless channel/harvest supplies affected | Draft quote inquiry only; no purchase. |
| Fuel/fertilizer sensitivity | Scenario | Procurement, Records + Inventory | Market + Sales unless revenue/channel context needed | Scenario math only with visible assumptions. |
| Inventory check | Records + Inventory | Procurement if low stock, Compliance if regulated/organic item | Market + Sales unless sales inventory involved | May produce missing data or draft reconciliation; no official update without approval. |
| Equipment / spare parts readiness | Records + Inventory | Procurement, Weather | Market + Sales unless harvest/market affected | Focus on availability, service status, missing parts, reorder draft if needed. |
| Irrigation supplies / water readiness | Records + Inventory, Weather | Procurement, Compliance if records/permits involved | Market + Sales unless crop delivery affected | No real irrigation portal or water request unless future approved integration exists. |
| Seed lot / planting stock check | Records + Inventory | Procurement, Compliance, Scenario | Market + Sales unless crop availability planning relevant | Seed lots, germination, lot numbers, organic docs, reorder watch. |
| Packaging / market supply check | Records + Inventory, Market + Sales | Procurement | Weather if market-day setup relevant | Packaging is inventory truth plus channel demand; reorder draft requires approval. |
| Organic documentation issue | Compliance | Records + Inventory, Procurement, Market + Sales if sales affected | Scenario unless cost implication asked | Expert/certifier review; no organic approval/denial by agent. |
| Crop-health / scouting watch | Compliance | Weather, Records + Inventory | Procurement, Market + Sales, Scenario unless requested | Watch/scout/record context only; no treatment advice. |
| Spray / treatment question | Compliance | Weather only if conditions requested safely | Procurement, Market + Sales, Scenario | Safety-bound refusal/redirect; no product/rate/tank-mix/treatment instruction. |
| Document extraction: quote/invoice | Records + Inventory | Procurement for quote/reorder, Compliance for sensitive/organic/restricted items | Weather, Market + Sales, Scenario unless relevant | Extracted values are draft, evidence-backed, Farm Restricted where appropriate. |
| Document extraction: sales/harvest record | Records + Inventory, Market + Sales | Compliance, Scenario | Procurement unless supplies/reorder affected | Draft record only; no official update without approval. |
| Margin / break-even / what-if | Scenario | Procurement, Records + Inventory, Market + Sales, Compliance if constraints matter | Weather unless weather is an assumption | Math only; no buy/sell/hold/price recommendation. |
| Approval / review status | Action Agent | Synthesizer, Compliance, relevant source agent | Weather, Scenario unless needed | Shows pending, blocked, needs_info, approved_simulated, rejected. |
| Role/permission question | Supervisor/Auth, Action Agent | Compliance | All domain agents unless data-specific | Clarifies what the role can see or approve. |
| Unknown or ambiguous request | Supervisor | Minimal relevant agent after clarification | All others until intent clarified | Ask for clarification or provide safe overview. |

---

## Task-Scoped Context Packages

The Supervisor should construct a context package for each routed agent. These packages should be smaller than the full farm record.

### Weather + Fieldwork Context Package

```yaml
farm_id: string
user_role: string
workflow_intent: string
location:
  lat: number
  lon: number
  state: string
  county: string
forecast:
  evidence_id: string
  source_name: string
  freshness: string
  connector_mode: string
  fallback_used: boolean
  periods: []
planned_operations:
  - operation_type: planting | cultivation | harvest | mowing | transplanting | market_setup | irrigation_watch | other
    date_window: string
constraints:
  wind_sensitive: boolean
  rain_sensitive: boolean
  heat_or_frost_sensitive: boolean
missing_data: []
```

### Procurement Context Package

```yaml
farm_id: string
user_role: string
workflow_intent: string
inventory_signals:
  - item_id: string
    category: string
    quantity_on_hand: number | unknown
    reorder_threshold: number | missing
    freshness: string
quotes:
  - quote_id: string
    supplier: string
    item: string
    unit_price: number | missing
    unit: string
    valid_until: date | missing
    evidence_id: string
    missing_terms: []
compliance_flags:
  - organic_status: approved | unknown | not_applicable
    restricted_use: true | false | unknown
public_context:
  - source: EIA | other
    evidence_id: string
missing_data: []
role_visibility:
  pricing_visible: boolean
```

### Records + Inventory Context Package

```yaml
farm_id: string
user_role: string
workflow_intent: string
inventory_items:
  - item_id: string
    category: string
    item_name: string
    quantity_on_hand: number | unknown
    unit: string
    storage_location: string | missing
    last_verified: date | missing
    evidence_id: string
records:
  - record_type: inventory | harvest | yield | sales | compliance | document_extraction
    record_id: string
    status: official | draft_pending_review | missing | stale
    evidence_id: string
missing_data: []
role_visibility:
  restricted_fields_hidden: boolean
```

### Market + Sales Context Package

```yaml
farm_id: string
user_role: string
workflow_intent: string
commitments:
  - channel: CSA | restaurant | farmers_market | wholesale | grain | other
    customer_or_channel: string
    item: string
    committed_quantity: number
    unit: string
    due_date: date | missing
inventory_available:
  - item: string
    quantity_available: number | unknown
    unit: string
    lot_or_batch: string | missing
market_context:
  - source_name: string
    evidence_id: string
    context_only: true
sales_records:
  - sale_id: string
    channel: string
    status: draft | delivered | invoiced | paid | partially_reconciled | missing
missing_data: []
role_visibility:
  financial_details_visible: boolean
  customer_details_visible: boolean
```

### Compliance Context Package

```yaml
farm_id: string
user_role: string
workflow_intent: string
compliance_records:
  - record_type: organic | crop_protection | food_safety | acreage_reporting | crop_insurance | regulatory_watch
    status: complete | incomplete | missing | stale | unknown
    evidence_id: string
watchlists:
  - type: crop_health | regulatory_pest | deadline | safety
    evidence_id: string
    context_only: true
sensitive_actions:
  - action_type: official_record_update | certifier_message | pesticide_related | external_sharing
missing_data: []
review_flags: []
```

### Margin + Scenario Context Package

```yaml
farm_id: string
user_role: string
workflow_intent: string
scenario_question: string
cost_inputs:
  - item: string
    cost: number | missing
    unit: string
    evidence_id: string
quantity_inputs:
  - item: string
    quantity: number | missing
    unit: string
    evidence_id: string
revenue_inputs:
  - channel_or_crop: string
    revenue_or_price: number | missing
    unit: string
    evidence_id: string
assumptions:
  - string
missing_data: []
role_visibility:
  margin_visible: boolean
```

---

## Capability / ToolGateway Request Guidance

The Supervisor should request capabilities only when the workflow needs them.

| Capability | Use when | Avoid when |
|---|---|---|
| `weather_tool` | Weather, fieldwork, market-day risk, harvest windows, high-tunnel context | Pure document extraction, pure procurement quote review, sales reconciliation without weather |
| `records_tool` | Inventory, records, document extraction, compliance, harvest/yield, sales records | Pure public-context lookup |
| `fuel_tool` | Fuel inventory, fuel quotes, fuel procurement, fuel scenario math | Field employee restricted pricing workflow unless authorized |
| `fertilizer_tool` | Fertilizer quotes, input comparison, fertilizer scenario math | Non-input workflows |
| `marketdata_tool` | AMS/direct-market context, stored grain context if implemented | Inventory-only checks unless market context needed |
| `crop_benchmark` | Regional crop benchmark context, scenario context | Farm-specific yield truth or fuel-buy workflow |
| `crop_health_watchlist` | Crop-health, scouting, regulatory/invasive watch, weekly crop watch | Fuel, document extraction, packaging, supplier-only workflows |
| `document_extraction` or local document tool | User-uploaded/local quote, invoice, delivery ticket, record | Public connector workflows |
| future `review_queue` | User asks to approve/reject/list pending actions | Normal recommendation generation unless action review requested |

---

## Human-Review Routing Rules

The Supervisor should preserve review triggers from every agent and avoid downgrading review state.

### Usually review not required

```text
read-only weather context
read-only market context
watchlist-only scouting context
internal pack list with no customer message
math-only scenario with no commitment
```

### Usually needs user approval

```text
supplier message
customer message
official record update
inventory truth update
purchase/reorder
certifier message
sales record update
grain buyer inquiry
```

### Usually needs expert review

```text
organic certification-sensitive issue
pesticide/crop-protection record issue
regulated/reportable pest concern
crop-insurance-sensitive or USDA filing-sensitive workflow
food safety record gap
```

### Usually needs info

```text
missing supplier fees
missing local bid/basis
missing yield estimate
missing harvest quantity
missing lot number
low-confidence document extraction
missing organic documentation
stale inventory count
```

---

## Role-Based Routing Rules

### Farm owner

May see:

```text
supplier quotes
pricing
margin/context math
buyer/customer terms
draft actions
approval requirements
Farm Restricted documents
```

May approve within policy limits.

### Farm manager

May see many operational details and may approve some operational actions depending on policy.

Still requires owner or expert approval for sensitive financial, compliance, or official-record workflows if policy says so.

### Field employee

Should see:

```text
role-safe weather/fieldwork guidance
operational task context
PPE/safety reminders
non-sensitive inventory readiness
non-sensitive crop-health/scouting watch items
```

Should not see:

```text
supplier pricing
restricted quote details
margin
buyer/customer financial terms
Farm Restricted document values
sale strategy
official record approval controls
```

Should not approve supplier messages, financial actions, official record updates, or restricted document actions.

---

## Routing Anti-Patterns

The Supervisor should avoid these patterns:

```text
Calling every connector for every request.
Calling every agent for a narrow task.
Passing full farm records to all agents.
Letting public context override farm-specific records.
Letting weather output become spray/treatment guidance.
Letting crop-health watchlists become pesticide recommendations.
Letting market context become sell/hold advice.
Letting scenario math become a financial recommendation.
Letting draft actions look executed.
Letting field employees see restricted pricing or margin details.
Letting low-confidence document extraction update official records.
```

---

## Example Routing Flows

### Flow 1: Weekly plan for Prairie View Farms

```text
User: What should I know about Prairie View Farms this week?

Supervisor:
- identifies broad weekly plan intent
- builds PVF context package for farm_owner
- requests weather_tool, records_tool, fuel_tool, fertilizer_tool, crop_benchmark, crop_health_watchlist as relevant
- routes to Weather, Records + Inventory, Procurement, Market + Sales, Compliance, optional Scenario
- sends findings to Synthesizer
- sends proposed actions to Action Agent

Output:
- weather/fieldwork windows
- fuel and input watch
- fertilizer/seed watch
- market/stored grain context
- compliance/records
- missing data
- draft fuel inquiry, blocked pending approval
```

### Flow 2: Weekly plan for Green Basket Organics

```text
User: What should I know about Green Basket Organics this week?

Supervisor:
- identifies broad weekly direct-market plan
- requests weather_tool, marketdata_tool, crop_health_watchlist, records_tool as relevant
- routes to Weather, Records + Inventory, Procurement, Market + Sales, Compliance, optional Scenario
- preserves CSA/restaurant commitments as decision anchors
- treats AMS as regional context only

Output:
- CSA/market plan
- harvest and wash-pack priorities
- packaging inventory
- weather/high-tunnel watch
- organic records/input caution
- draft CSA box reorder and certifier message, blocked pending approval
```

### Flow 3: Field employee weekly plan

```text
User role: field_employee

Supervisor:
- restricts quote, pricing, margin, customer, and financial context
- requests only authorized capabilities
- routes role-safe context to agents

Output:
- fieldwork windows
- safety/PPE guidance
- non-sensitive inventory readiness
- no supplier pricing
- no draft supplier/customer/financial actions
```

### Flow 4: Fuel invoice extraction

```text
User uploads or selects a local fuel invoice.

Supervisor:
- identifies document extraction / records workflow
- requests document extraction and records_tool
- routes to Records + Inventory
- routes to Procurement only if quote/reorder context is relevant
- does not route Weather, Crop Health, or Market unless user asks

Output:
- extracted fields as draft
- evidence ID linked to document
- official record update blocked pending approval
- no external action
```

### Flow 5: What should I spray?

```text
User: What should I spray?

Supervisor:
- identifies spray/treatment request
- routes to Compliance safety boundary
- may include crop-health watchlist only as context if relevant
- does not route Procurement for product selection
- does not route Weather to produce spray timing
- does not route Scenario for treatment economics

Output:
- no product/rate/tank-mix/treatment instruction
- scouting/diagnosis/extension/advisor review redirect
- no proposed action
```

### Flow 6: Stored grain sale watch

```text
User asks about stored grain.

Supervisor:
- routes to Records + Inventory for stored grain quantities
- routes to Market + Sales for watch context
- routes to Scenario for math-only price-level examples if local bid/basis available or user supplies assumptions
- routes to Compliance if official or crop-insurance-sensitive record implications exist

Output:
- watch-only context
- missing local bid/basis if absent
- no sell/hold recommendation
- no buyer contact without approval
```

---

## Acceptance Criteria for Supervisor Routing

A correct Supervisor implementation should satisfy these checks:

```text
Weekly plan routes to all expected farm-domain agents.
Narrow workflows do not call unrelated agents.
Agents receive task-scoped context, not unrestricted full farm records.
Connector/tool access is mediated by ToolGateway and authorization.
Evidence IDs are preserved through the final ActionPack.
Role restrictions are applied before output.
Farm-specific data remains the decision anchor.
Public data remains context only.
Missing data is explicit.
Draft actions are passed to the Action Agent.
External actions remain blocked unless approved.
Field employees cannot see restricted pricing/margin/customer/supplier details.
Spray/treatment requests are safety-bounded.
Stored grain scenarios remain watch/math only, not sell/hold advice.
Document extraction remains isolated from unrelated crop-health/weather/market context.
```

---

## Relationship to Other Planning Documents

This routing map should be read together with:

```text
docs/AGENT_DOMAIN_MAP.md
docs/AGENT_DATA_SOURCE_MAP.md
docs/AGENT_HANDOFF_MATRIX.md, future
docs/AGENT_COVERAGE_MATRIX.md, future
```

- `AGENT_DOMAIN_MAP.md` defines what each agent owns.
- `AGENT_DATA_SOURCE_MAP.md` defines what data each agent needs and where it comes from.
- `SUPERVISOR_ROUTING_MAP.md` defines when and how the Supervisor routes work to agents.
- `AGENT_HANDOFF_MATRIX.md` should define how agents pass findings to each other without overlap.
- `AGENT_COVERAGE_MATRIX.md` should compare desired domain scope against what the repo currently supports.
