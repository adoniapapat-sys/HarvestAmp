# 05_AGENT_CONTRACTS.md

# Agent Contracts: HarvestAmp

**Version:** 0.1  
**Date:** 2026-06-22  
**Status:** Draft MVP planning document  
**Product name:** HarvestAmp  
**Related documents:** `01_PRODUCT_BRIEF.md`, `02_AGENT_ARCHITECTURE.md`, `03_FARM_PROFILES.md`, `04_DATA_SOURCES.md`  
**Intended use:** Source-of-truth contract document for Antigravity tasks, Google ADK agent definitions, tool design, test scenarios, evaluation criteria, and future implementation planning.

---

## 0. Important Note

This document is a planning document, not production code.

It defines the behavioral, privacy, input, output, tool, and human-review contracts for the HarvestAmp agents and supporting services. It should be treated as the source of truth when building agents in separate Antigravity tasks.

All farm examples, prices, supplier names, quotes, inventories, field records, and user profiles referenced by the MVP are synthetic unless explicitly connected to a real authorized customer environment in the future.

HarvestAmp must not provide final legal, tax, crop insurance, pesticide, veterinary, organic-certification, futures/options, or regulated financial advice. It may analyze, summarize, compare, draft, flag, and recommend scenarios. Human approval or expert review is required whenever a workflow crosses the risk thresholds defined in this document and in the future `06_RISK_AND_HUMAN_REVIEW_POLICY.md`.

---

## 1. Purpose of This Document

The purpose of this document is to define how each HarvestAmp agent or service should behave.

This document answers:

- What is each agent responsible for?
- What is each agent not responsible for?
- What inputs may each agent receive?
- What outputs must each agent return?
- What tools may each agent request?
- What farm data may each agent access?
- Which data classes are prohibited?
- When must the agent trigger human review?
- What should each agent do when data is missing, stale, conflicting, or restricted?
- What tests should verify that the agent behaves correctly?

The goal is to let individual agents be built in separate Antigravity tasks without losing architectural consistency.

---

## 2. Contract Philosophy

HarvestAmp should be built as a multi-agent system with strong contracts between agents.

The key principle is:

> Specialist agents should be independently buildable and testable, but they must all speak the same system language.

Every agent should:

1. Receive only task-scoped context.
2. Use only allowed tools.
3. Return source-labeled findings.
4. Include confidence, assumptions, missing data, and staleness.
5. Mark sensitive outputs with data-sensitivity and viewer permissions.
6. Trigger human review when required.
7. Avoid unauthorized disclosure.
8. Never receive raw credentials.
9. Never bypass the Credential Broker or Tool Gateway.
10. Return structured output that the Supervisor and Recommendation Synthesizer can combine.

HarvestAmp should not be one giant unrestricted chatbot. It should be a coordinated system of bounded agents, deterministic services, policy gates, tools, data stores, and user approval flows.

---

## 3. Universal Agent Rules

These rules apply to every HarvestAmp agent.

### 3.1 Task-scoped context only

Agents receive only the data needed for the active workflow.

Example:

If the user asks, "Should I buy diesel this month?", the Procurement Agent may need fuel quotes, tank level, tank capacity, expected fieldwork demand, delivery terms, and recent fuel history. It does not need unrelated organic certification documents, all crop insurance files, all field boundaries, or another farm's supplier quotes.

### 3.2 No raw credentials

No agent may receive, request, store, summarize, expose, or transmit raw credentials.

Prohibited credential data includes:

- Passwords.
- API keys.
- OAuth refresh tokens.
- Supplier portal credentials.
- Email tokens.
- Bank credentials.
- Private keys.
- Secret Manager values.

If a user pastes a credential into chat, the agent should refuse to process it as a credential, avoid repeating it, and route the user to a secure connection flow.

### 3.3 Capability requests, not credential requests

Agents should request capabilities through tools.

Bad:

```text
Procurement Agent asks user for supplier portal password.
```

Good:

```text
Procurement Agent requests get_latest_supplier_quotes(farm_id, input_category="fertilizer").
Credential Broker verifies authorization.
Tool Gateway retrieves only the approved normalized quote data.
```

### 3.4 No ambient open-web dependency

Agents should not rely on uncontrolled open-web browsing for production decisions.

HarvestAmp should use:

- Approved public APIs.
- Authorized supplier integrations.
- User uploads.
- Manual entries.
- Farm records.
- Licensed data feeds.
- Tool Gateway controlled connectors.

Open-web search, when enabled later, should be limited, source-labeled, cached, freshness-checked, and treated as lower-trust unless the source is official or licensed.

### 3.5 No cross-farm leakage

Agents must never use one farm's private data to answer another farm's question.

Examples of prohibited behavior:

- Revealing Prairie View Farms' fuel quote to Green Basket Organics.
- Using one tenant's fertilizer quote as another tenant's quote.
- Showing one farm's margin or break-even to a different farm.
- Sharing one supplier's quote with another supplier unless the user explicitly approves.
- Using identifiable customer farm data in demos, tests, or training without explicit authorization.

### 3.6 Source-labeled recommendations

Every recommendation should be traceable to source-labeled evidence.

A recommendation should not be stronger than the evidence supporting it.

If the evidence is stale, conflicting, missing, synthetic, or user-entered, the agent must say so in the structured output.

### 3.7 Human review for high-impact actions

Agents may analyze, summarize, compare, draft, and recommend.

Human approval or expert review is required before HarvestAmp:

- Sends a message externally.
- Creates a purchase order.
- Commits to buying inputs.
- Changes official records.
- Shares restricted data.
- Grants data access.
- Files or prepares regulated submissions as final.
- Makes high-risk pesticide, organic, livestock, crop-insurance, legal, tax, or financial decisions.

### 3.8 Deterministic math where possible

Do not use an LLM for simple arithmetic or unit conversions when deterministic calculators are available.

Examples that should be deterministic:

- Dollars per gallon.
- Dollars per ton.
- Dollars per acre.
- Cost per pound of nitrogen.
- Inventory days on hand.
- Fuel tank percent full.
- Gross revenue scenarios.
- Break-even calculations.

LLMs may explain the result and interpret tradeoffs, but math should be calculated with tools.

### 3.9 Sensitivity-aware output

Each agent must label outputs by data sensitivity and allowed viewer role.

Sensitive outputs should not be shown to unauthorized users or included in external drafts without explicit approval.

### 3.10 Ask for missing information when needed

If the agent lacks essential data, it should return `insufficient_data` or `needs_info` rather than hallucinating.

The agent may provide conditional recommendations if it clearly states assumptions.

---

## 4. Agent vs. Deterministic Service

Not every component in HarvestAmp should be an LLM agent.

Some functions are deterministic services that enforce security, permissions, data retrieval, redaction, scheduling, and tool execution.

| Component | Type | Reason |
|---|---|---|
| Credential Broker / Authorization Service | Deterministic service | Security boundary; should not be LLM-controlled |
| Tool Gateway | Deterministic service | Enforces allowlists, data minimization, permission checks, audit logging |
| Context Package Builder | Deterministic service with policy logic | Builds task-scoped context packages |
| Audit Logger | Deterministic service | Immutable access and approval records |
| Unit conversion calculators | Deterministic functions | Math must be reliable and repeatable |
| Margin calculators | Deterministic functions plus LLM explanation | Calculations should not be free-form |
| Scheduler / monitoring triggers | Deterministic services | Recurring jobs and event triggers |
| Supervisor / Orchestrator Agent | LLM agent or ADK workflow coordinator | Chooses workflow and coordinates agents |
| Specialist agents | LLM agents with tools | Interpret, summarize, reason, compare, and draft |

---

## 5. Shared Data Sensitivity Classes

HarvestAmp should use the sensitivity classes defined in `02_AGENT_ARCHITECTURE.md` and `04_DATA_SOURCES.md`.

| Class | Description | Examples |
|---|---|---|
| Public | Public or non-sensitive information | Public weather, public USDA reports, public market reports, extension articles |
| Farm Internal | Operational information with low to moderate sensitivity | General tasks, non-sensitive crop calendar, equipment reminders |
| Farm Confidential | Commercially sensitive farm operations data | Field boundaries, acreage, crop plans, supplier names, inventory, tank levels, yield estimates |
| Farm Restricted | Highly sensitive financial, compliance, supplier, or legal data | Supplier quotes, invoices, contracts, margins, break-even, marketing plans, crop insurance, organic certification docs |
| Credentials and Secrets | Data never exposed to LLM prompts | Passwords, API keys, OAuth tokens, private keys, supplier login credentials |

### 5.1 Universal data handling rule

Agents should receive derived or summarized data whenever raw data is not required.

Examples:

- Prefer "tank is 38% full" over complete tank telemetry history.
- Prefer "supplier quote is below the 60-day average" over full quote history when detailed values are not needed.
- Prefer "margin details are hidden from this role" over exposing break-even values to unauthorized users.

---

## 6. Shared Contract Template

Every agent contract in this document follows this template:

```text
Agent name:
Short name:
Type:
MVP status:
Primary purpose:
Primary users:
Triggered by:
Inputs:
Allowed data classes:
Prohibited data classes:
Allowed tools:
Outputs:
Human-review triggers:
Must do:
Must not do:
Failure behavior:
Evaluation criteria:
```

When Antigravity is asked to build an agent, the relevant contract should be copied into the task prompt.

---

## 7. Shared Input Object: WorkItem

The Supervisor should create a `WorkItem` for each agent or workflow stage.

```yaml
work_item:
  work_item_id: "wi_001"
  workflow_id: "wf_2026_06_22_001"
  requesting_user_id: "user_farm_owner_001"
  farm_id: "farm_prairie_view"
  agent_target: "procurement"
  trigger_type: "user_question | scheduled_monitor | uploaded_document | alert | user_approval"
  user_intent: "Evaluate whether to buy diesel this month"
  requested_output: "agent_finding"
  farm_context_package_id: "ctx_001"
  allowed_data_classes:
    - "Public"
    - "Farm Internal"
    - "Farm Confidential"
    - "Farm Restricted"
  prohibited_data_classes:
    - "Credentials and Secrets"
  allowed_tool_names:
    - "harvestamp-fuel-tool"
    - "harvestamp-inventory-tool"
    - "harvestamp-weather-tool"
  viewer_role: "farm_owner"
  deadline: "2026-06-22T18:00:00-05:00"
  human_review_policy_version: "draft_v0_1"
```

### 7.1 WorkItem rules

- Each agent should receive a WorkItem, not the full application state.
- WorkItems should be generated by the Supervisor or workflow layer.
- WorkItems should include allowed tools and data classes.
- WorkItems should never include credentials.
- WorkItems should include the current user's role because output visibility depends on role.

---

## 8. Shared Context Object: FarmContextPackage

A `FarmContextPackage` is the task-scoped context provided to an agent.

```yaml
farm_context_package:
  context_package_id: "ctx_001"
  farm_id: "farm_prairie_view"
  profile_name: "Prairie View Farms"
  farm_type: "large_row_crop"
  sales_channels:
    - "grain_elevator"
  organic_status: "conventional"
  user_role: "farm_owner"
  relevant_fields:
    - field_id: "north_160"
      crop: "corn"
      acres: 160
      planting_date: "2026-04-24"
  relevant_inventory:
    - item_type: "diesel"
      amount_summary: "38_percent_full"
      data_sensitivity_class: "Farm Confidential"
  relevant_quotes:
    - quote_id: "quote_fuel_001"
      input_category: "fuel"
      summary: "current delivered diesel quote available"
      exact_value_allowed: true
      data_sensitivity_class: "Farm Restricted"
  evidence_ids:
    - "ev_weather_001"
    - "ev_fuel_quote_001"
  prohibited_disclosures:
    - "do_not_share_supplier_quotes_externally_without_user_approval"
    - "do_not_include_margin_data_in_supplier_messages"
  redactions_applied:
    - "home_address_removed"
    - "credential_fields_excluded"
```

### 8.1 Context package rules

- Context packages are built by deterministic infrastructure.
- Agents should not expand context on their own unless they request a tool through the Supervisor and Tool Gateway.
- Context packages should include only relevant evidence summaries and references.
- Sensitive details should be included only when required and authorized.

---

## 9. Shared Output Object: AgentFinding

Every specialist agent should return an `AgentFinding`.

```yaml
agent_finding:
  finding_id: "finding_001"
  workflow_id: "wf_2026_06_22_001"
  agent_name: "procurement"
  farm_id: "farm_prairie_view"
  user_id: "user_farm_owner_001"
  topic: "diesel_purchase_window"
  summary: "Current diesel quote is below the recent farm quote average, but delivery fee is not confirmed. Upcoming fieldwork may increase fuel demand next week."
  recommendation: "Consider buying part of the expected 30-day need now and setting a price alert for the remainder."
  urgency: "this_week"
  confidence: "medium"
  impact_areas:
    - "fuel"
    - "fieldwork"
    - "margin"
  evidence_ids:
    - "ev_fuel_quote_001"
    - "ev_inventory_001"
    - "ev_weather_001"
  assumptions:
    - "Expected fieldwork proceeds next week if weather window holds."
  missing_data:
    - "confirmed supplier delivery fee"
  data_sensitivity_used:
    - "Farm Confidential"
    - "Farm Restricted"
  allowed_viewer_roles:
    - "farm_owner"
    - "farm_manager"
  prohibited_disclosures:
    - "supplier_quote"
    - "margin_details"
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
    missing_data:
      - "confirmed supplier delivery fee"
  suggested_actions:
    - action_type: "draft_supplier_message"
      summary: "Draft a message asking the fuel supplier to confirm delivered price and delivery fee."
  tool_calls_used:
    - "harvestamp-fuel-tool.get_latest_quote"
    - "harvestamp-inventory-tool.get_inventory_summary"
  source_timestamps:
    - source_name: "fuel_quote"
      retrieved_at: "2026-06-22T09:00:00-05:00"
  staleness_status: "recent"
```

### 9.1 AgentFinding rules

- Findings should be structured, not just prose.
- Findings should include missing data and assumptions.
- Findings should carry human-review metadata.
- Findings should carry sensitivity metadata.
- Findings should not include hidden or unauthorized details.

---

## 10. Shared Human Review Object

The `human_review` object is an architectural contract used by agents, the Supervisor, the Risk Gate, the Recommendation Synthesizer, and the Action Agent.

```yaml
human_review:
  required: true
  review_type: "user_approval | expert_review | admin_review | blocked"
  reason:
    - "financial_action"
    - "compliance_sensitive"
    - "pesticide_related"
    - "organic_certification_sensitive"
    - "external_disclosure"
    - "low_confidence"
  recommended_reviewer:
    - "farm_owner"
    - "farm_manager"
    - "agronomist"
    - "organic_certifier"
    - "veterinarian"
    - "crop_insurance_agent"
    - "account_admin"
  approval_required_before:
    - "send_message"
    - "create_purchase_order"
    - "update_official_record"
    - "share_report"
    - "execute_external_tool"
  confidence: "medium"
  missing_data:
    - "current tank level"
    - "supplier delivery fee"
```

### 10.1 Human review rules

- Low-risk informational responses may be shown without approval.
- Financial commitments require user approval.
- External disclosure requires user approval.
- Pesticide, organic, veterinary, legal, crop-insurance, and regulated compliance issues require expert or responsible-human review.
- Permission changes require admin review.
- Unsafe or unauthorized actions are blocked.

The detailed review rules should be defined later in `06_RISK_AND_HUMAN_REVIEW_POLICY.md` and eventually converted into a machine-readable configuration such as `configs/human_review_rules.yaml`.

---

## 11. Shared Evidence Request Object

Agents should request evidence through approved tools rather than directly querying arbitrary sources.

```yaml
evidence_request:
  request_id: "er_001"
  workflow_id: "wf_2026_06_22_001"
  requesting_agent: "procurement"
  requested_source_type: "supplier_quote"
  farm_id: "farm_prairie_view"
  purpose: "Compare current diesel quote against inventory and fieldwork need."
  minimum_required_fields:
    - "input_category"
    - "unit_price"
    - "unit"
    - "supplier_id"
    - "quote_timestamp"
    - "delivery_terms"
  maximum_data_classes_requested:
    - "Farm Restricted"
  prohibited_fields:
    - "raw_credentials"
    - "bank_account"
  approval_needed: false
```

### 11.1 Evidence request rules

- Agents may request evidence but may not bypass authorization.
- The Tool Gateway may deny, redact, or summarize evidence.
- Tool calls should include a stated purpose for auditability.
- If evidence is denied, the agent should proceed with an explicit missing-data note or ask the user for authorization.

---

## 12. Agent and Service Registry

| Name | Short name | Type | MVP status | Contract section |
|---|---:|---|---|---:|
| Credential Broker / Authorization Service | `credential_broker` | Deterministic service | Required | 13 |
| Tool Gateway | `tool_gateway` | Deterministic service | Required | 14 |
| Context Package Builder | `context_builder` | Deterministic service | Required | 15 |
| Supervisor / Orchestrator Agent | `supervisor` | LLM agent / workflow coordinator | Required | 16 |
| Intent Router | `intent_router` | LLM or deterministic classifier | Required | 17 |
| Farm Profile Agent | `farm_profile` | LLM agent | Required | 18 |
| Weather + Fieldwork Agent | `weather_fieldwork` | LLM agent with tools | Required | 19 |
| Input Procurement Agent | `procurement` | LLM agent with tools and calculators | Required | 20 |
| Records + Inventory Agent | `records_inventory` | LLM agent with tools | Required | 21 |
| Market + Sales Agent | `market_sales` | LLM agent with tools | Required | 22 |
| Compliance Agent | `compliance` | LLM agent with rules/tools | Required | 23 |
| Margin + Scenario Agent | `margin_scenario` | LLM agent plus deterministic calculators | Required | 24 |
| Recommendation Synthesizer | `synthesizer` | LLM agent | Required | 25 |
| Action Agent | `action` | LLM agent plus deterministic tools | Required, approval-gated | 26 |
| Document / Media Intake Agent | `document_intake` | LLM/OCR/document extraction service | Required for MVP uploads | 27 |
| Credential Setup Assistant | `credential_setup` | LLM assistant | Optional MVP | 28 |
| Crop / Livestock Risk Agent | `crop_livestock_risk` | LLM agent with tools | Optional MVP-lite / later | 29 |
| Advisor / Co-op Admin Agent | `advisor_admin` | LLM agent | Later | 30 |

---

## 13. Contract: Credential Broker / Authorization Service

**Short name:** `credential_broker`  
**Type:** Deterministic service, not an LLM agent  
**MVP status:** Required  
**Primary purpose:** Authenticate users, authorize data access, manage credential states, enforce tenant isolation, and provide audit metadata.

### 13.1 Primary users

- Farm owner.
- Farm manager.
- Authorized farm employee.
- Advisor or co-op user in later B2B deployments.
- Account administrator.

### 13.2 Triggered by

- User login.
- Agent tool request.
- Data-source connection flow.
- Permission change request.
- External action request.
- User revocation of access.
- Scheduled monitor that needs restricted data.

### 13.3 Inputs

- User identity.
- Farm ID.
- User role.
- Requested data class.
- Requested tool or integration.
- Requested action.
- Purpose of access.
- Credential state.
- Tenant boundaries.

### 13.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted.
- Credentials and Secrets, but only inside secure infrastructure and never into prompts.

### 13.5 Prohibited data classes for LLM exposure

- Credentials and Secrets.

### 13.6 Allowed tools

- Identity provider.
- IAM / role policy store.
- Secret Manager or auth manager.
- Audit logger.
- Integration registry.
- Permission database.

### 13.7 Outputs

```yaml
authorization_decision:
  decision: "allow | deny | allow_with_redaction | needs_reauth | needs_admin_approval"
  user_id: "user_farm_owner_001"
  farm_id: "farm_prairie_view"
  allowed_data_classes:
    - "Public"
    - "Farm Internal"
    - "Farm Confidential"
  denied_data_classes:
    - "Farm Restricted"
  allowed_tools:
    - "harvestamp-weather-tool"
  redaction_rules:
    - "hide_margin_values"
  reason: "User is employee role and cannot view supplier quotes."
  audit_event_id: "audit_001"
```

### 13.8 Human-review triggers

- Granting new user access.
- Granting advisor or co-op access to a farm.
- Enabling new external integrations.
- Exporting restricted data.
- Revoking or changing tenant-level access.
- Connecting supplier portals.

### 13.9 Must do

- Enforce least privilege.
- Enforce tenant isolation.
- Store and access credentials securely.
- Return allow/deny/redaction decisions.
- Log access decisions.
- Support revocation.
- Prevent LLM agents from seeing secrets.

### 13.10 Must not do

- Send raw credentials to agents.
- Allow agents to self-authorize.
- Use chat transcripts as credential stores.
- Allow cross-tenant access without explicit role and policy support.

### 13.11 Failure behavior

If authorization cannot be verified, deny access and ask the user to re-authenticate or request appropriate permissions.

### 13.12 Evaluation criteria

- Denies employee access to margin and supplier quotes when not authorized.
- Allows farm owner access to restricted farm data when appropriate.
- Never exposes credentials to prompts.
- Logs allow and deny decisions.
- Correctly handles expired data-source connections.

---

## 14. Contract: Tool Gateway

**Short name:** `tool_gateway`  
**Type:** Deterministic service, not an LLM agent  
**MVP status:** Required  
**Primary purpose:** Enforce approved tool usage, data minimization, external disclosure controls, rate limits, redaction, and audit logging for tool calls.

### 14.1 Triggered by

- Agent request for weather, fuel, market, quote, document, inventory, or calendar data.
- Action Agent request to send a message or update records.
- Scheduled monitoring loop.

### 14.2 Inputs

- Tool name.
- Tool method.
- Farm ID.
- User ID.
- Agent ID.
- WorkItem ID.
- Purpose.
- Requested fields.
- Authorization decision.
- Human-review status if external action is requested.

### 14.3 Outputs

```yaml
tool_gateway_result:
  status: "success | denied | redacted | needs_approval | error"
  tool_name: "harvestamp-fuel-tool"
  method: "get_latest_quote"
  data_returned_summary: "latest authorized fuel quote returned"
  data_sensitivity_returned:
    - "Farm Restricted"
  redactions_applied:
    - "supplier_contact_hidden"
  audit_event_id: "audit_tool_001"
  error_message: null
```

### 14.4 Must do

- Verify tool allowlist.
- Enforce Credential Broker decisions.
- Redact unnecessary sensitive fields.
- Require human approval before external action.
- Log tool use.
- Block unauthorized external disclosure.
- Must mediate any irrigation portal or provider tool access.
- Must enforce role, farm, credential state, approval state, and audit logging.

### 14.5 Must not do

- Execute unapproved arbitrary web calls.
- Send supplier quotes externally without approval.
- Return raw credentials.
- Allow an agent to call a tool not listed in its WorkItem.

### 14.6 Evaluation criteria

- Blocks unauthorized supplier email send.
- Redacts restricted fields for employee-role users.
- Returns only requested minimum fields.
- Logs all external action attempts.

---

## 15. Contract: Context Package Builder

**Short name:** `context_builder`  
**Type:** Deterministic service with policy logic  
**MVP status:** Required  
**Primary purpose:** Build task-scoped FarmContextPackages for agents.

### 15.1 Triggered by

- Supervisor creates a WorkItem.
- Scheduled monitor requires an agent run.
- Uploaded document needs analysis.
- User changes farm profile, inventory, supplier, or sales channel data.

### 15.2 Inputs

- User request.
- Intent classification.
- Farm ID.
- User role.
- Agent target.
- Authorization decision.
- Relevant data sources.
- Redaction rules.

### 15.3 Outputs

- FarmContextPackage.
- Evidence references.
- Redaction summary.
- Prohibited disclosures.
- Missing required data flags.

### 15.4 Must do

- Minimize data sent to agents.
- Include source timestamps.
- Include data sensitivity labels.
- Include allowed viewer roles.
- Include prohibited disclosures.
- Exclude credentials and secrets.

### 15.5 Must not do

- Send full farm database snapshots to agents.
- Include unrelated supplier quotes.
- Include restricted data for unauthorized users.
- Include raw uploaded files when extracted summaries are sufficient.

### 15.6 Evaluation criteria

- Fuel question context excludes organic certification files.
- Market-day planning context excludes row-crop grain data.
- Employee-role context excludes break-even and supplier quote details.
- Context package includes staleness metadata.

---

## 16. Contract: Supervisor / Orchestrator Agent

**Agent name:** Supervisor / Orchestrator Agent  
**Short name:** `supervisor`  
**Type:** LLM agent or ADK workflow coordinator  
**MVP status:** Required  
**Primary purpose:** Coordinate workflows, select agents, gather findings, and enforce routing discipline.

### 16.1 Primary users

The Supervisor does not interact with users directly in a product sense, but it supports all HarvestAmp users.

### 16.2 Triggered by

- User chat or voice request.
- Scheduled daily or weekly briefing.
- Monitoring loop alert.
- Uploaded quote, invoice, image, or note.
- User approval event.

### 16.3 Inputs

- User request.
- Intent classification.
- Farm profile summary.
- User role.
- WorkItem.
- Authorization and context constraints.
- Prior findings in the workflow.

### 16.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted when necessary and authorized.

### 16.5 Prohibited data classes

- Credentials and Secrets.
- Unauthorized cross-farm data.

### 16.6 Allowed tools

- Agent registry.
- Workflow templates.
- Context Package Builder.
- Evidence Board.
- Human-review/risk policy checker.
- Tool Gateway only through approved paths.

### 16.7 Outputs

- Agent routing plan.
- WorkItems for specialist agents.
- Workflow pattern selection.
- Missing context request.
- Aggregated findings handoff to Synthesizer.

```yaml
routing_plan:
  workflow_id: "wf_001"
  pattern: "parallel_gather"
  agents_to_run:
    - "weather_fieldwork"
    - "procurement"
    - "records_inventory"
    - "margin_scenario"
  agents_not_run:
    - agent: "market_sales"
      reason: "No sales decision requested."
  privacy_notes:
    - "Do not route margin details to weather_fieldwork."
```

### 16.8 Human-review triggers

The Supervisor should flag human review whenever any involved agent or workflow indicates:

- Financial action.
- External disclosure.
- Compliance-sensitive issue.
- Low confidence in high-impact decision.
- User permission change.
- Record overwrite.
- High-risk recommendation.

### 16.9 Must do

- Route only necessary agents.
- Prevent unnecessary data sharing.
- Choose sequential, parallel, conditional, or loop workflow.
- Track workflow state.
- Preserve evidence links.
- Ensure synthesizer receives all relevant findings.

### 16.10 Must not do

- Invent specialist findings.
- Bypass specialist agents for high-risk domains.
- Bypass Credential Broker or Tool Gateway.
- Send full farm data to every agent.
- Override human-review requirements.

### 16.11 Failure behavior

If routing is uncertain, use a safe fallback:

1. Ask for clarifying information when low effort and necessary.
2. Run the least-risk, most relevant agents.
3. Mark missing data and low confidence.
4. Avoid external action.

### 16.12 Evaluation criteria

- Routes diesel-buying question to Procurement, Weather, Records, and Margin.
- Routes spray-window question to Weather and Compliance, not Market.
- Routes market-day question for Green Basket to Weather, Records, Market/Sales, and Procurement.
- Does not route restricted supplier quote data to unauthorized agents.
- Adds human-review flags when required.

---

## 17. Contract: Intent Router

**Agent name:** Intent Router  
**Short name:** `intent_router`  
**Type:** LLM classifier or deterministic/LLM hybrid  
**MVP status:** Required  
**Primary purpose:** Classify user requests into workflows and detect risk categories.

### 17.1 Triggered by

- User chat message.
- Voice transcript.
- Uploaded document metadata.
- Scheduled monitor event.

### 17.2 Inputs

- User message.
- Farm type.
- User role.
- Trigger type.
- Basic farm profile summary.

### 17.3 Allowed data classes

- Public.
- Farm Internal.
- Minimal Farm Confidential metadata if needed.

### 17.4 Prohibited data classes

- Credentials and Secrets.
- Full supplier quotes.
- Margin details.
- Full uploaded documents unless classification requires extracted metadata.

### 17.5 Output intents

```text
- daily_briefing
- weekly_plan
- weather_fieldwork
- spray_window
- fuel_procurement
- fertilizer_procurement
- seed_procurement
- packaging_procurement
- quote_comparison
- inventory_check
- crop_risk
- livestock_risk
- market_sales
- direct_market_planning
- compliance_deadline
- organic_compliance
- document_extraction
- record_update
- supplier_message
- access_or_credentials
- unknown_or_needs_clarification
```

### 17.6 Outputs

```yaml
intent_result:
  primary_intent: "fuel_procurement"
  secondary_intents:
    - "inventory_check"
    - "weather_fieldwork"
  risk_categories:
    - "financial_action"
  confidence: "high"
  suggested_workflow: "fuel_buy_window"
  needs_clarification: false
```

### 17.7 Must do

- Detect high-risk categories.
- Detect external action requests.
- Detect when credentials or secrets may be present.
- Detect the user's farm type and sales channel relevance.

### 17.8 Must not do

- Answer the user directly for complex requests.
- Access unnecessary restricted data.
- Treat pasted credentials as usable data.

### 17.9 Evaluation criteria

- Classifies "Should I buy diesel this month?" as fuel procurement.
- Classifies "Can I spray tomorrow?" as spray window and compliance-sensitive.
- Classifies "What should I bring to market Saturday?" as direct-market planning.
- Flags "Here is my supplier password" as credential-sensitive and routes to secure handling.

---

## 18. Contract: Farm Profile Agent

**Agent name:** Farm Profile Agent  
**Short name:** `farm_profile`  
**Type:** LLM agent  
**MVP status:** Required  
**Primary purpose:** Collect, maintain, and summarize the farm's operating context.

### 18.1 Primary users

- Farm owner.
- Farm manager.
- Advisor setting up a customer farm.
- Co-op/admin user later.

### 18.2 Triggered by

- New account onboarding.
- Farm profile update.
- Missing context in a workflow.
- User correction.
- Seasonal reset.

### 18.3 Inputs

- User-provided farm information.
- Existing farm profile.
- Farm type template.
- Data gaps.
- User role.

### 18.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted only when explicitly needed for setup and authorized.

### 18.5 Prohibited data classes

- Credentials and Secrets.
- Full financial statements unless a later workflow explicitly requires them and authorization exists.
- Other farms' profiles.

### 18.6 Allowed tools

- Farm profile database.
- Field/acreage database.
- Supplier registry.
- Sales channel registry.
- Inventory categories.
- Setup completeness checker.

### 18.7 Outputs

```yaml
farm_profile_update:
  farm_id: "farm_green_basket"
  profile_completeness_score: 0.78
  farm_type: "small_organic_direct_market"
  sales_channels:
    - "CSA"
    - "farmers_market"
  missing_profile_items:
    - "current packaging inventory"
    - "organic input approval list"
  recommended_next_questions:
    - "Which suppliers do you use for packaging?"
    - "Do you want market-day planning to use prior sales history?"
```

### 18.8 Human-review triggers

- Adding a new authorized user.
- Connecting a new supplier or external account.
- Marking a farm as certified organic without supporting records.
- Updating ownership, advisor access, or admin access.

### 18.9 Must do

- Ask only necessary onboarding questions.
- Support both MVP profiles: large row crop and small organic/direct-market.
- Track missing context.
- Maintain a concise profile summary for other agents.
- Respect role-based access.

### 18.10 Must not do

- Ask users for passwords.
- Treat unverified organic claims as certification proof.
- Share one farm's setup details with another farm.
- Overwrite existing profile data without confirmation.

### 18.11 Failure behavior

If data is missing, the agent should produce a profile gap list and allow workflows to proceed with clear assumptions where safe.

### 18.12 Evaluation criteria

- Correctly distinguishes Prairie View Farms from Green Basket Organics.
- Collects sales channel information, not just crops.
- Tracks supplier categories.
- Flags missing packaging inventory for the direct-market farm.
- Does not require irrelevant row-crop fields for the organic vegetable farm.

---

## 19. Contract: Weather + Fieldwork Agent

**Agent name:** Weather + Fieldwork Agent  
**Short name:** `weather_fieldwork`  
**Type:** LLM agent with weather tools  
**MVP status:** Required  
**Primary purpose:** Convert weather and forecast data into farm-specific operational implications.

### 19.1 Primary users

- Farm owner.
- Farm manager.
- Field employee.
- Advisor.

### 19.2 Triggered by

- Daily or weekly briefing.
- Spray, plant, harvest, irrigation, grazing, or market-day question.
- Weather monitoring alert.
- Procurement workflow needing demand timing.
- Direct-market planning workflow.

### 19.3 Inputs

- Field location or market location.
- Farm type.
- Crop/livestock context.
- Planned operation.
- Forecast data.
- Recent weather.
- Soil/wetness indicators when available.
- User question.

### 19.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential when field-level context is needed.

### 19.5 Prohibited data classes

- Credentials and Secrets.
- Supplier quotes unless needed only as a high-level workflow dependency.
- Margin details.
- Unrelated restricted documents.

### 19.6 Allowed tools

- `harvestamp-weather-tool`.
- Field location lookup.
- Weather history connector.
- Farm weather station integration later.
- Soil/field status connector later.

### 19.7 Outputs

```yaml
weather_fieldwork_finding:
  topic: "spray_window"
  summary: "Morning wind appears lower than afternoon wind, but rain risk increases overnight."
  recommendation: "If spraying is otherwise appropriate, review the product label and consider the morning window. Compliance review required before application guidance."
  urgency: "today"
  confidence: "medium"
  evidence_ids:
    - "ev_weather_forecast_001"
  human_review:
    required: true
    review_type: "expert_review"
    reason:
      - "pesticide_related"
      - "compliance_sensitive"
    recommended_reviewer:
      - "licensed_applicator"
      - "agronomist"
```

### 19.8 Human-review triggers

- Pesticide spray decisions.
- Restricted-use pesticide implications.
- Severe weather safety risks.
- Livestock heat stress emergencies.
- External crew instructions.
- High-cost fieldwork timing decisions when confidence is low.

### 19.9 Must do

- Translate weather into operational windows.
- Mention forecast uncertainty.
- Include wind, precipitation, temperature, frost, heat, storm, humidity, and field wetness when relevant.
- Route pesticide-related issues to Compliance.
- Use farm type and sales channel context.
- Use weather, heat, rain, wind, and fieldwork context to identify irrigation timing considerations.

### 19.10 Must not do

- Recommend pesticide product, rate, tank mix, or label interpretation as final advice.
- Pretend the forecast is certain.
- Ignore severe weather warnings.
- Use generic weather summaries when the user asks an operational question.
- Make water-rights or district-rule determinations.

### 19.11 Failure behavior

If weather data is unavailable, return `insufficient_data`, identify the missing source, and provide only general non-operational guidance.

### 19.12 Evaluation criteria

- For Prairie View, identifies fieldwork and spray windows without giving pesticide rates.
- For Green Basket, considers market-day weather, harvest timing, and heat/frost risk.
- Does not access supplier quotes unless routed through a procurement workflow.
- Marks pesticide-related outputs for human/expert review.

---

## 20. Contract: Input Procurement Agent

**Agent name:** Input Procurement Agent  
**Short name:** `procurement`  
**Type:** LLM agent with procurement tools and deterministic calculators  
**MVP status:** Required  
**Primary purpose:** Help users evaluate input needs, supplier quotes, inventory, purchase timing, and buy/wait/split scenarios.

### 20.1 Primary users

- Farm owner.
- Farm manager.
- Purchasing manager.
- Advisor with authorization.

### 20.2 Triggered by

- Fuel purchase question.
- Fertilizer quote comparison.
- Seed order planning.
- Packaging or market supply inventory check.
- Uploaded quote or invoice.
- Price monitoring alert.
- Weekly farm plan.

### 20.3 Inputs

- Input category.
- Supplier quote summaries.
- Inventory status.
- Tank/storage capacity.
- Demand forecast.
- Farm type.
- Sales channel.
- Weather timing dependency.
- Historical purchase data.
- User risk tolerance.
- Budget or purchase threshold if authorized.

### 20.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted when relevant and authorized.

### 20.5 Prohibited data classes

- Credentials and Secrets.
- Other farms' quotes.
- Unrelated supplier quotes.
- Bank credentials.
- Full financial records unless explicitly authorized and required.

### 20.6 Allowed tools

- `harvestamp-fuel-tool`.
- `harvestamp-fertilizer-tool`.
- `harvestamp-seed-tool`.
- `harvestamp-packaging-tool`.
- `harvestamp-inventory-tool`.
- `harvestamp-supplier-quotes-tool`.
- Unit conversion calculators.
- Nutrient cost calculators.
- Buy/wait/split scenario calculators.
- Weather tool when timing affects demand.
- Market/sales tool when margin context is needed.

### 20.7 Outputs

```yaml
procurement_finding:
  topic: "fertilizer_quote_comparison"
  summary: "Supplier A is lower per ton, but Supplier B may be lower per pound of nutrient after delivery and application fees if the listed fee is confirmed."
  recommendation: "Do not select a supplier until delivery and application terms are confirmed. Ask both suppliers to confirm delivered cost and application fee."
  urgency: "this_week"
  confidence: "medium"
  impact_areas:
    - "fertilizer"
    - "margin"
  missing_data:
    - "confirmed application fee"
    - "final nutrient target"
  human_review:
    required: true
    review_type: "user_approval"
    reason:
      - "financial_action"
      - "supplier_selection"
    approval_required_before:
      - "send_message"
      - "create_purchase_order"
```

### 20.8 Human-review triggers

- Any purchase recommendation.
- Supplier recommendation.
- Supplier-facing message.
- Purchase above user-defined threshold.
- Fertilizer, manure, or nutrient recommendation beyond arithmetic comparison.
- Organic input uncertainty.
- Pesticide or crop-protection product involvement.
- Low confidence with material financial impact.

### 20.9 Must do

- Use farmer's actual supplier quote over public benchmarks for farm-specific recommendations.
- Normalize units.
- Calculate cost per useful unit.
- Separate arithmetic comparison from agronomic recommendation.
- Include delivery, application, storage, discount, and timing assumptions when available.
- Protect supplier quotes from unauthorized disclosure.
- Provide buy now / wait / split / ask for more info options.

### 20.10 Must not do

- Commit to a purchase without approval.
- Send supplier messages without approval.
- Reveal one supplier's quote to another supplier without explicit approval.
- Invent current prices.
- Treat public benchmark prices as local delivered quotes.
- Make final organic or pesticide suitability decisions.

### 20.11 Failure behavior

If supplier quote data is missing, the agent should provide a quote request checklist or ask the user to enter/upload quotes. If inventory is missing, the agent should present scenarios with clear assumptions.

### 20.12 Evaluation criteria

- Correctly handles diesel buy/wait/split scenario for Prairie View.
- Correctly compares fertilizer quotes by nutrient cost, not just price per ton.
- Correctly checks packaging inventory for Green Basket.
- Triggers user approval for purchases.
- Does not disclose competitor quote details in supplier drafts.

---

## 21. Contract: Records + Inventory Agent

**Agent name:** Records + Inventory Agent  
**Short name:** `records_inventory`  
**Type:** LLM agent with deterministic tools  
**MVP status:** Required  
**Primary purpose:** Maintain farm records, inventory, field notes, invoice extractions, tasks, and operational memory.

### 21.1 Primary users

- Farm owner.
- Farm manager.
- Field employee.
- Market manager.
- Advisor with access.

### 21.2 Triggered by

- User logs a field note.
- User uploads invoice or receipt.
- Procurement workflow needs inventory.
- Weekly planning workflow.
- User asks inventory question.
- Action Agent updates records after approval.

### 21.3 Inputs

- Voice or chat note.
- Uploaded document extraction.
- Existing inventory.
- Field/task context.
- User role.
- Approval status for official updates.

### 21.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted when relevant and authorized.

### 21.5 Prohibited data classes

- Credentials and Secrets.
- Unauthorized farm records.
- Restricted financials for employee roles.

### 21.6 Allowed tools

- Inventory database.
- Task database.
- Field records database.
- Document extraction output store.
- Quote/invoice history.
- Calendar tool through Tool Gateway after approval.

### 21.7 Outputs

```yaml
records_inventory_finding:
  topic: "packaging_inventory"
  summary: "Current clamshell inventory may be insufficient for the next two market days based on planned strawberry and tomato volume."
  recommendation: "Add clamshells to the purchase watchlist and confirm actual count before ordering."
  urgency: "this_week"
  confidence: "medium"
  missing_data:
    - "physical inventory count"
  suggested_actions:
    - action_type: "create_task"
      summary: "Count 1-pint clamshells before Thursday."
```

### 21.8 Human-review triggers

- Updating official records from uncertain extraction.
- Deleting or overwriting records.
- Marking compliance-sensitive records as complete.
- Sharing records externally.
- Changing inventory after financial invoice extraction if confidence is low.

### 21.9 Must do

- Preserve draft vs official record status.
- Flag uncertainty in extracted data.
- Track who made or approved changes.
- Maintain inventory history.
- Support role-specific views.
- Track irrigation events, water requests, field water history, pump/fuel/electricity notes, and missing records.

### 21.10 Must not do

- Silently overwrite official records.
- Treat OCR/extraction as always correct.
- Expose restricted records to unauthorized roles.
- Store raw credentials.

### 21.11 Failure behavior

If extraction confidence is low, create a draft record and ask for confirmation.

### 21.12 Evaluation criteria

- Creates draft record from uploaded fuel invoice.
- Does not update official inventory without approval when extraction is uncertain.
- Hides margin-linked records from employee role.
- Identifies low packaging inventory for Green Basket.

---

## 22. Contract: Market + Sales Agent

**Agent name:** Market + Sales Agent  
**Short name:** `market_sales`  
**Type:** LLM agent with market and sales tools  
**MVP status:** Required  
**Primary purpose:** Provide commodity market context and direct-market sales planning support.

### 22.1 Primary users

- Farm owner.
- Farm manager.
- Market manager.
- Advisor with access.

### 22.2 Triggered by

- Commodity pricing question.
- Local cash bid or basis context request.
- Weekly briefing.
- Direct-market planning request.
- Farmers market, CSA, wholesale, or restaurant sales question.
- Margin workflow.

### 22.3 Inputs

- Farm type.
- Sales channels.
- Inventory or expected production.
- Market prices or sales history.
- Weather for market day or delivery.
- User's marketing goals if authorized.
- Storage and logistics context when relevant.

### 22.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted when margins, contracts, or marketing plans are relevant and authorized.

### 22.5 Prohibited data classes

- Credentials and Secrets.
- Unauthorized margin data.
- Other farms' sales data.
- Supplier quote details unless needed and authorized for margin context.

### 22.6 Allowed tools

- `harvestamp-marketdata-tool`.
- `harvestamp-direct-market-sales-tool` later.
- `harvestamp-pos-sales-tool` later.
- Public market benchmark connectors.
- Licensed market data connectors later.
- Weather tool for market-day impacts.
- Margin tool for scenarios.

### 22.7 Outputs

```yaml
market_sales_finding:
  topic: "farmers_market_plan"
  summary: "Saturday weather may reduce customer traffic. Prior rainy markets had lower greens sales and higher leftover risk."
  recommendation: "Consider a conservative harvest for highly perishable greens and prepare customer messaging for CSA pickup reminders."
  urgency: "this_week"
  confidence: "medium"
  impact_areas:
    - "direct_market"
    - "inventory"
    - "weather"
  human_review:
    required: true
    review_type: "user_approval"
    reason:
      - "external_disclosure"
    approval_required_before:
      - "send_customer_message"
```

### 22.8 Human-review triggers

- Crop or livestock sale recommendation.
- Hedging, futures, options, or trading-related request.
- Changing marketing plan.
- Sharing availability sheets externally.
- Sending CSA/customer messages.
- Using restricted margin data.

### 22.9 Must do

- Provide scenarios rather than definitive trading advice.
- Distinguish public benchmark data from actual local bids or sales records.
- Respect sales channel differences.
- Incorporate weather for market-day planning.
- Protect customer and farm sales data.

### 22.10 Must not do

- Execute trades.
- Tell users definitively to sell, hedge, or speculate.
- Share marketing plans externally without approval.
- Invent local cash bids.
- Treat delayed/public prices as guaranteed executable prices.

### 22.11 Failure behavior

If market data is missing or stale, return context using available data and mark confidence as low or insufficient.

### 22.12 Evaluation criteria

- Gives row-crop market context without definitive trading advice.
- Produces direct-market plan for Green Basket.
- Requires approval before customer-facing messages.
- Does not expose restricted margin details to unauthorized users.

---

## 23. Contract: Compliance Agent

**Agent name:** Compliance Agent  
**Short name:** `compliance`  
**Type:** LLM agent with policy/rule tools  
**MVP status:** Required  
**Primary purpose:** Identify compliance, regulatory, certification, pesticide, food safety, crop insurance, USDA, and human-review risks.

### 23.1 Primary users

- Farm owner.
- Farm manager.
- Organic compliance manager.
- Advisor.
- Later: co-op or enterprise admin.

### 23.2 Triggered by

- Pesticide or spray-related request.
- Organic input or certification request.
- USDA/crop insurance deadline request.
- Food safety or audit record request.
- Livestock or veterinary risk request.
- External report or official record workflow.
- Any agent flags compliance sensitivity.

### 23.3 Inputs

- User question.
- Farm type.
- Organic status.
- Crop/livestock context.
- Planned action.
- Relevant extracted document data.
- Source labels.
- Human-review policy.

### 23.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted when relevant and authorized.

### 23.5 Prohibited data classes

- Credentials and Secrets.
- Unrelated restricted docs.
- Unauthorized compliance records.

### 23.6 Allowed tools

- Compliance rules registry.
- Pesticide label reference connectors through approved tools.
- Organic input/reference connectors.
- USDA/RMA deadline references.
- Food safety record templates.
- Human-review policy checker.

### 23.7 Outputs

```yaml
compliance_finding:
  topic: "organic_input_review"
  summary: "The uploaded fertilizer quote does not include enough evidence to confirm organic approval for this farm."
  recommendation: "Confirm the product with the farm's certifier before purchase or application."
  urgency: "high"
  confidence: "low"
  impact_areas:
    - "organic"
    - "compliance"
    - "procurement"
  human_review:
    required: true
    review_type: "expert_review"
    reason:
      - "organic_certification_sensitive"
      - "compliance_sensitive"
      - "low_confidence"
    recommended_reviewer:
      - "organic_certifier"
      - "farm_owner"
    approval_required_before:
      - "create_purchase_order"
      - "apply_to_field_plan"
```

### 23.8 Human-review triggers

Always trigger review for:

- Pesticide product/rate/tank mix/label guidance.
- Organic input eligibility uncertainty.
- Veterinary or animal-health treatment decisions.
- Crop insurance or USDA filings.
- Legal, tax, payroll, or contract-sensitive issues.
- Food safety compliance submissions.
- Official record changes.

### 23.9 Must do

- Flag risk and recommend appropriate human reviewer.
- Distinguish checklist/help from final determination.
- Route uncertain compliance questions to expert review.
- Avoid overconfident legal/regulatory claims.
- Include source and staleness metadata.
- Flag water-rights, district-rule, allocation, or reporting uncertainty.
- Require responsible-human or expert review when water rights, allocation, or legal/district rules are unclear.

### 23.10 Must not do

- Make final pesticide, organic, veterinary, insurance, tax, legal, or regulatory determinations.
- Recommend pesticide rates or restricted-use application decisions as final advice.
- Mark organic eligibility as confirmed unless verified by farm-specific approved documentation.
- Submit forms without explicit approval.

### 23.11 Failure behavior

If source data is missing, stale, or unclear, return a compliance caution and list the information needed for expert review.

### 23.12 Evaluation criteria

- Flags spray requests as pesticide-related.
- Requires certifier review for organic input uncertainty.
- Creates USDA deadline checklist without claiming eligibility.
- Blocks final legal/tax advice.

---

## 24. Contract: Margin + Scenario Agent

**Agent name:** Margin + Scenario Agent  
**Short name:** `margin_scenario`  
**Type:** LLM agent plus deterministic calculators  
**MVP status:** Required  
**Primary purpose:** Convert input costs, inventory, sales prices, production assumptions, and timing into margin and decision scenarios.

### 24.1 Primary users

- Farm owner.
- Farm manager.
- Advisor with restricted access.

### 24.2 Triggered by

- Buy/wait/split procurement workflow.
- Commodity market scenario.
- Direct-market pricing or harvest plan.
- Weekly action plan.
- User asks impact on break-even or margin.

### 24.3 Inputs

- Input prices.
- Quantity needed.
- Inventory.
- Expected yield or sales volume.
- Sales price or bid.
- Storage or delivery costs.
- User risk tolerance.
- Farm type and sales channel.

### 24.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.
- Farm Restricted when authorized.

### 24.5 Prohibited data classes

- Credentials and Secrets.
- Unauthorized margin or financial data.
- Other farms' financial data.

### 24.6 Allowed tools

- Cost-per-acre calculator.
- Cost-per-bushel calculator.
- Cost-per-market-day calculator.
- Cost-per-CSA-box calculator.
- Break-even calculator.
- Storage cost calculator.
- Unit conversion tools.
- Scenario generator.

### 24.7 Outputs

```yaml
margin_scenario_finding:
  topic: "diesel_purchase_scenario"
  summary: "Buying 50% of expected 30-day diesel need now reduces near-term shortage risk while preserving some flexibility if prices change."
  recommendation: "Use a split-purchase scenario unless the user prioritizes price certainty over flexibility."
  urgency: "this_week"
  confidence: "medium"
  impact_areas:
    - "fuel"
    - "margin"
  scenario_options:
    - option: "buy_now"
      summary: "Highest certainty, less price flexibility."
    - option: "wait"
      summary: "More price flexibility, higher shortage and delivery risk."
    - option: "split"
      summary: "Balances operational risk and price uncertainty."
  human_review:
    required: true
    review_type: "user_approval"
    reason:
      - "financial_action"
```

### 24.8 Human-review triggers

- Any scenario involving major spending.
- Any scenario involving crop/livestock sale timing.
- Hedging, futures, options, or storage marketing decisions.
- Margin output visible outside farm owner/manager/advisor roles.
- Low confidence with material financial impact.

### 24.9 Must do

- Use deterministic math.
- Clearly state assumptions.
- Provide scenarios, not certainties.
- Respect role-based access to margins.
- Avoid definitive financial/trading advice.

### 24.10 Must not do

- Invent yields, bids, or prices without labeling them assumptions.
- Execute financial actions.
- Show restricted margin data to unauthorized users.
- Guarantee price outcomes.

### 24.11 Failure behavior

If essential data is missing, return a scenario template and ask for missing values.

### 24.12 Evaluation criteria

- Calculates fuel purchase scenarios without guaranteeing future price changes.
- Separates quote comparison from agronomic fertilizer rate advice.
- Produces direct-market pricing context without exposing restricted data.
- Marks financial actions for user approval.

---

## 25. Contract: Recommendation Synthesizer

**Agent name:** Recommendation Synthesizer  
**Short name:** `synthesizer`  
**Type:** LLM agent  
**MVP status:** Required  
**Primary purpose:** Convert specialist findings into a clear, prioritized, farmer-friendly Action Pack.

### 25.1 Primary users

- Farm owner.
- Farm manager.
- Field employee with restricted view.
- Market manager.
- Advisor with authorization.

### 25.2 Triggered by

- Completion of specialist agent findings.
- Daily or weekly briefing workflow.
- User asks for summary.
- Monitoring alert needs user-facing output.

### 25.3 Inputs

- AgentFindings.
- Evidence Board summary.
- User role.
- Farm type.
- Sales channel.
- Human-review flags.
- Prohibited disclosures.
- Output channel: chat, dashboard, alert, report, email draft.

### 25.4 Allowed data classes

- Same as authorized viewer role.

### 25.5 Prohibited data classes

- Credentials and Secrets.
- Any data the current user is not authorized to see.
- Hidden competitor/supplier details in external-facing drafts.

### 25.6 Allowed tools

- Evidence Board reader.
- Role-based redaction tool.
- Action Pack generator.
- Human-review policy checker.
- Localization/formatting tools later.

### 25.7 Outputs

```yaml
action_pack:
  title: "This Week at Prairie View Farms"
  executive_summary: "Fuel and fieldwork timing are the main issues this week. Fertilizer quote details need confirmation before supplier selection."
  today_actions:
    - "Confirm current fuel tank level."
  this_week_actions:
    - "Ask fuel supplier to confirm delivered price and delivery fee."
  watchlist:
    - "Rain may reduce fieldwork options late week."
  buy_alerts:
    - "Diesel split-purchase scenario needs owner approval."
  compliance_items:
    - "No final pesticide guidance provided. Confirm label and advisor guidance before spraying."
  missing_information:
    - "confirmed supplier delivery fee"
  human_review_items:
    - "User approval required before contacting supplier."
  privacy_notes:
    - "Supplier quote details are restricted to owner and manager roles."
```

### 25.8 Human-review triggers

The Synthesizer does not create new high-risk actions without preserving or adding review flags.

It should add human review if final phrasing includes:

- Purchase recommendation.
- Supplier message.
- External report.
- Compliance-sensitive conclusion.
- Low-confidence high-impact recommendation.

### 25.9 Must do

- Prioritize by urgency and impact.
- Keep farmer language practical and concise.
- Preserve evidence and confidence.
- Preserve human-review flags.
- Apply role-based redaction.
- Clearly separate recommendations from approved actions.

### 25.10 Must not do

- Remove human-review flags.
- Overstate confidence.
- Hide missing data.
- Include restricted details in outputs to unauthorized users.
- Make specialist claims not supported by findings.

### 25.11 Failure behavior

If findings conflict, present the conflict and ask for review or more data rather than forcing a false conclusion.

### 25.12 Evaluation criteria

- Produces clear weekly plan from parallel agent findings.
- Does not expose restricted supplier quote values to unauthorized users.
- Preserves pesticide/organic review flags.
- Separates Today, This Week, Watchlist, Buy Alerts, Compliance, and Missing Information.

---

## 26. Contract: Action Agent

**Agent name:** Action Agent  
**Short name:** `action`  
**Type:** LLM agent plus deterministic tools  
**MVP status:** Required, approval-gated  
**Primary purpose:** Convert approved recommendations into tasks, reminders, draft messages, reports, and record updates.

### 26.1 Primary users

- Farm owner.
- Farm manager.
- Market manager.
- Advisor with authorization.

### 26.2 Triggered by

- User approves an action.
- User asks to draft a message.
- User asks to create a task or reminder.
- User approves record update.
- User asks to generate a report.

### 26.3 Inputs

- Action Pack.
- Approved action IDs.
- Human-review status.
- User role.
- Tool Gateway authorization.
- Disclosure preview.

### 26.4 Allowed data classes

- Only data required to perform the approved action.

### 26.5 Prohibited data classes

- Credentials and Secrets.
- Hidden sensitive data not approved for disclosure.
- Unapproved supplier quotes, margins, or field data.

### 26.6 Allowed tools

- Task tool.
- Calendar tool.
- Email/draft tool.
- Report generator.
- Record update tool.
- Inventory update tool.
- Supplier message draft tool.
- Tool Gateway for external execution.

### 26.7 Outputs

```yaml
action_result:
  action_id: "act_001"
  action_type: "draft_supplier_message"
  status: "draft_created | executed | needs_approval | blocked | failed"
  summary: "Draft supplier message created but not sent."
  disclosure_preview:
    includes_sensitive_data: true
    sensitive_data_categories:
      - "supplier_quote"
    user_approval_required: true
  audit_event_id: "audit_action_001"
```

### 26.8 Human-review triggers

The Action Agent must require approval before:

- Sending external messages.
- Creating purchase orders.
- Updating official records.
- Sharing reports.
- Changing access permissions.
- Exporting restricted data.
- Deleting or overwriting records.

### 26.9 Must do

- Check `human_review` before execution.
- Show disclosure previews before external send.
- Create drafts rather than send automatically during MVP.
- Log actions.
- Respect role-based permissions.
- May prepare draft irrigation requests.

### 26.10 Must not do

- Send messages without approval.
- Include hidden restricted data in drafts.
- Bypass Tool Gateway.
- Execute blocked actions.
- Make unauthorized record changes.
- Submit a water request, change irrigation schedule, or send external irrigation messages without approval.

### 26.11 Failure behavior

If approval is missing, return `needs_approval` and show what approval is needed.

### 26.12 Evaluation criteria

- Blocks supplier message send without approval.
- Creates internal task from approved recommendation.
- Shows disclosure preview for external messages.
- Does not include competitor quote details unless explicitly approved.

---

## 27. Contract: Document / Media Intake Agent

**Agent name:** Document / Media Intake Agent  
**Short name:** `document_intake`  
**Type:** LLM/OCR/document extraction service with human confirmation gates  
**MVP status:** Required for uploaded quotes, invoices, and records  
**Primary purpose:** Extract structured data from user uploads and route extracted information to the correct agent.

### 27.1 Primary users

- Farm owner.
- Farm manager.
- Market manager.
- Advisor with authorization.

### 27.2 Triggered by

- Uploaded fuel quote.
- Uploaded fertilizer quote.
- Uploaded seed quote.
- Uploaded invoice or receipt.
- Uploaded organic document.
- Uploaded crop/field photo later.
- Voice note or chat note needing structuring.

### 27.3 Inputs

- Uploaded file.
- File metadata.
- User role.
- Farm ID.
- Declared document type if provided.
- Extraction schema.

### 27.4 Allowed data classes

- Farm Internal.
- Farm Confidential.
- Farm Restricted when authorized.

### 27.5 Prohibited data classes

- Credentials and Secrets should be detected and redacted.
- Bank details and payment data should be masked unless explicitly needed and authorized.

### 27.6 Allowed tools

- Document extraction/OCR tool.
- Sensitive-data classifier.
- Redaction tool.
- Quote parser.
- Invoice parser.
- Records draft writer.
- Evidence Board.

### 27.7 Outputs

```yaml
document_extraction_result:
  document_id: "doc_quote_001"
  detected_document_type: "fertilizer_quote"
  extraction_confidence: "medium"
  extracted_fields:
    supplier_name: "synthetic supplier"
    product_name: "urea"
    unit_price: "redacted_in_example"
    unit: "per_ton"
    delivery_terms: "not_found"
  missing_fields:
    - "application fee"
  redactions_applied:
    - "payment_account_removed"
  recommended_route:
    - "procurement"
    - "records_inventory"
  official_record_update_allowed: false
```

### 27.8 Human-review triggers

- Low-confidence extraction.
- Updating official records.
- Extracted payment/bank data.
- Compliance-sensitive documents.
- Organic certification documents.
- Pesticide labels.
- Crop insurance or USDA documents.

### 27.9 Must do

- Extract structured data with confidence.
- Label sensitivity.
- Redact credentials/secrets.
- Keep document data tied to the correct farm.
- Route to appropriate agent.
- Create draft records, not official records, until approved.

### 27.10 Must not do

- Treat OCR as infallible.
- Send raw documents to unrelated agents.
- Expose sensitive fields unnecessarily.
- Store credentials found in documents.

### 27.11 Failure behavior

If extraction fails, preserve file metadata, mark status as failed, and ask the user for manual entry or a clearer upload.

### 27.12 Evaluation criteria

- Extracts fuel quote fields from synthetic upload.
- Extracts fertilizer quote fields and flags missing application fee.
- Redacts sensitive payment data.
- Does not update inventory officially without approval.

---

## 28. Contract: Credential Setup Assistant

**Agent name:** Credential Setup Assistant  
**Short name:** `credential_setup`  
**Type:** LLM assistant, not credential handler  
**MVP status:** Optional MVP  
**Primary purpose:** Help users understand and complete secure data-source connection flows.

### 28.1 Triggered by

- User wants to connect Gmail, Drive, Calendar, supplier account, market data, or another integration.
- Credential is expired.
- User asks what permissions mean.
- User wants to revoke access.

### 28.2 Inputs

- Integration type.
- Permission explanation.
- Credential state summary.
- User role.
- Secure connection URL or UI flow state.

### 28.3 Allowed data classes

- Public.
- Farm Internal.
- Credential state metadata, but not credentials.

### 28.4 Prohibited data classes

- Raw credentials.
- OAuth tokens.
- API keys.
- Supplier passwords.

### 28.5 Allowed tools

- Integration registry.
- Credential state checker.
- Secure connection flow launcher.
- Permission explanation templates.

### 28.6 Outputs

```yaml
credential_setup_guidance:
  integration: "gmail_quote_ingestion"
  status: "needs_connection"
  explanation: "HarvestAmp can look for supplier quote emails only after you connect Gmail through the secure authorization flow. Do not paste your password into chat."
  next_step: "open_secure_connection_flow"
```

### 28.7 Human-review triggers

- Connecting new data source.
- Granting access to farm data.
- Revoking access.
- Admin-level permission changes.

### 28.8 Must do
 
- Explain permissions in plain language.
- Direct users to secure flows.
- Explain revocation.
- Never ask for credentials in chat.
- If a user needs to connect an irrigation portal, route to secure credential setup.
- Never ask for irrigation portal username/password in chat.

### 28.9 Must not do

- Handle raw credentials.
- Encourage users to paste passwords or tokens.
- Circumvent denied permissions.

### 28.10 Evaluation criteria

- Refuses pasted passwords.
- Routes user to secure OAuth/API setup flow.
- Explains why Gmail access is requested.
- Explains how to revoke an integration.

---

## 29. Contract: Crop / Livestock Risk Agent

**Agent name:** Crop / Livestock Risk Agent  
**Short name:** `crop_livestock_risk`  
**Type:** LLM agent with risk tools  
**MVP status:** Optional MVP-lite / later  
**Primary purpose:** Identify crop disease, pest, scouting, crop-stage, pasture, and livestock risk signals.

### 29.1 MVP position

For the first MVP, this agent may be implemented as a lightweight stub or limited scouting-risk workflow. Full crop disease diagnosis, image triage, and livestock health support should be later-stage features.

### 29.2 Triggered by

- User asks what to scout.
- User uploads crop image.
- Weather pattern increases disease risk.
- Weekly briefing.
- Livestock heat/stress/water/feed concern later.

### 29.3 Inputs

- Crop or livestock type.
- Field or herd context.
- Planting date or growth stage.
- Weather conditions.
- Local/regional risk source if available.
- User-submitted photo or observation later.

### 29.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential.

### 29.5 Prohibited data classes

- Credentials and Secrets.
- Unrelated supplier quotes.
- Margin data.
- Veterinary medical records unless authorized and specifically needed later.

### 29.6 Allowed tools

- Crop risk reference tools.
- Extension alert sources.
- Weather tool.
- Field records.
- Image triage tools later.
- Livestock risk references later.

### 29.7 Outputs

```yaml
crop_livestock_risk_finding:
  topic: "soybean_scouting_priority"
  summary: "Recent humidity and canopy conditions suggest scouting early-planted soybean fields first."
  recommendation: "Scout lower canopy and low-lying areas first. Treat this as a scouting priority, not a diagnosis."
  urgency: "this_week"
  confidence: "medium"
  human_review:
    required: false
```

### 29.8 Human-review triggers

- Product treatment recommendations.
- Pesticide use.
- Veterinary treatment.
- Livestock illness.
- Food safety risk.
- Low-confidence image diagnosis.

### 29.9 Must do

- Frame disease/pest outputs as scouting priorities or possible issues.
- Ask for agronomist/vet review when appropriate.
- Use weather and field context.
- Avoid definitive diagnosis from limited evidence.

### 29.10 Must not do

- Make final disease diagnosis from image alone.
- Recommend pesticide or veterinary treatment as final advice.
- Replace agronomist, crop advisor, or veterinarian.

### 29.11 Evaluation criteria

- Produces scouting checklist without treatment recommendation.
- Routes pesticide-related next steps to Compliance.
- Marks image triage as low-confidence if evidence is limited.

---

## 30. Contract: Advisor / Co-op Admin Agent

**Agent name:** Advisor / Co-op Admin Agent  
**Short name:** `advisor_admin`  
**Type:** LLM agent  
**MVP status:** Later  
**Primary purpose:** Support authorized advisors, co-ops, crop consultants, and ag retailers managing multiple farms.

### 30.1 MVP position

This is not part of the first farmer-facing MVP, but it matters for future Google Marketplace monetization because co-ops, crop consultants, and ag retailers may be strong B2B buyers.

### 30.2 Triggered by

- Advisor asks for multi-farm summary.
- Co-op wants grower alerts.
- Consultant wants scouting report drafts.
- Admin wants usage or account summary.

### 30.3 Inputs

- Authorized farm list.
- Advisor role.
- Aggregated or farm-specific data depending on permission.
- Human-review status.

### 30.4 Allowed data classes

- Public.
- Farm Internal.
- Farm Confidential or Farm Restricted only for farms explicitly authorized for that advisor/user.
- De-identified aggregated data when aggregation rules are satisfied.

### 30.5 Prohibited data classes

- Credentials and Secrets.
- Unauthorized farms.
- Individually identifiable farm data in aggregate summaries unless authorized.

### 30.6 Must do

- Enforce farm-level authorization.
- Prevent cross-farm leakage.
- Use de-identification for aggregate insights.
- Show source and permission basis.

### 30.7 Must not do

- Reveal one farmer's quotes or margins to another farmer.
- Create cross-farm benchmarks from identifiable data without permission.
- Give supplier competitive intelligence using private farm data.

### 30.8 Evaluation criteria

- Advisor sees only authorized farms.
- Aggregates are de-identified.
- Supplier quote details are not exposed across farms.

---

## 31. Workflow Contract: Weekly Farm Action Plan

**Workflow name:** Weekly Farm Action Plan  
**MVP status:** Required  
**Primary purpose:** Produce a farm-specific weekly plan using multiple agents in parallel and then synthesizing the results.

### 31.1 Triggered by

- User asks, "What should I do this week?"
- Scheduled weekly briefing.
- Advisor requests weekly summary.

### 31.2 Agents involved

Parallel:

- Weather + Fieldwork Agent.
- Input Procurement Agent.
- Records + Inventory Agent.
- Market + Sales Agent.
- Compliance Agent.

Then:

- Margin + Scenario Agent if economic decisions are present.
- Recommendation Synthesizer.
- Action Agent after approval.

### 31.3 Output sections

- Today.
- This Week.
- Watchlist.
- Buy Alerts.
- Market / Sales Actions.
- Compliance Items.
- Missing Information.
- Approval Required.
- Privacy Notes.

### 31.4 Required guardrails

- Role-based output redaction.
- Human review for high-risk items.
- No external messages without approval.
- Stale data labels.

---

## 32. Workflow Contract: Fuel Buy Window

**Workflow name:** Fuel Buy Window  
**MVP status:** Required for Prairie View profile  
**Primary purpose:** Evaluate whether the farmer should buy now, wait, split, or request more information.

### 32.1 Triggered by

- "Should I buy diesel this month?"
- Fuel price alert.
- Weekly briefing.
- Tank level update.

### 32.2 Agents involved

- Procurement Agent.
- Weather + Fieldwork Agent.
- Records + Inventory Agent.
- Margin + Scenario Agent.
- Recommendation Synthesizer.
- Action Agent after approval.

### 32.3 Required inputs

- Current quote or benchmark.
- Tank level.
- Tank capacity.
- Expected fuel demand.
- Upcoming fieldwork.
- Delivery terms.
- Risk tolerance.

### 32.4 Required outputs

- Buy now / wait / split / ask for more info.
- Confidence.
- Missing data.
- Suggested alert threshold.
- Approval required before supplier action.

### 32.5 Required guardrails

- Do not guarantee future fuel price movement.
- Treat public benchmark as benchmark, not local delivered quote.
- Require user approval before contacting supplier or creating order.

---

## 33. Workflow Contract: Fertilizer Quote Comparison

**Workflow name:** Fertilizer Quote Comparison  
**MVP status:** Required for Prairie View profile  
**Primary purpose:** Compare fertilizer quotes by useful cost and operational constraints.

### 33.1 Triggered by

- Uploaded fertilizer quote.
- User asks to compare quotes.
- Weekly procurement review.

### 33.2 Agents involved

Sequential:

1. Document / Media Intake Agent.
2. Procurement Agent.
3. Records + Inventory Agent.
4. Weather + Fieldwork Agent if application timing matters.
5. Compliance Agent if manure, organic, environmental, pesticide, or regulated issue appears.
6. Margin + Scenario Agent.
7. Recommendation Synthesizer.
8. Action Agent after approval.

### 33.3 Required inputs

- Product.
- Unit price.
- Unit.
- Nutrient analysis.
- Quantity.
- Delivery terms.
- Application cost.
- Acres or target area.
- Existing inventory.
- Crop need or soil test target if available.

### 33.4 Required outputs

- Normalized price.
- Cost per pound of nutrient.
- Cost per acre if data is sufficient.
- Missing quote fields.
- Supplier comparison.
- User approval before selection or message.

### 33.5 Required guardrails

- Separate arithmetic comparison from agronomic recommendation.
- Require review for nutrient rate, manure, organic, or environmental decisions.
- Do not reveal competitor quotes externally without explicit approval.

---

## 34. Workflow Contract: Direct-Market Weekly Plan

**Workflow name:** Direct-Market Weekly Plan  
**MVP status:** Required for Green Basket profile  
**Primary purpose:** Help a small organic/direct-market farm plan harvest, market, CSA, packaging, and weather-sensitive tasks.

### 34.1 Triggered by

- "What should I bring to market Saturday?"
- "Plan this week's CSA box."
- Weekly briefing.
- Weather alert.
- Packaging inventory alert.

### 34.2 Agents involved

- Weather + Fieldwork Agent.
- Records + Inventory Agent.
- Market + Sales Agent.
- Input Procurement Agent.
- Compliance Agent if organic or food safety issue appears.
- Recommendation Synthesizer.
- Action Agent after approval.

### 34.3 Required inputs

- Market or CSA date.
- Crop availability.
- Harvest estimates.
- Packaging inventory.
- Weather forecast.
- Past sales if authorized.
- Customer commitments.
- Organic status.

### 34.4 Required outputs

- Harvest priorities.
- Packaging check.
- Market-day weather implications.
- CSA/customer message drafts if requested.
- Purchase watchlist.
- Food safety/organic reminders.

### 34.5 Required guardrails

- User approval before customer-facing messages.
- Human review for organic input/compliance issues.
- Do not expose customer data unnecessarily.

---

## 35. Workflow Contract: Record Update from Upload

**Workflow name:** Record Update from Upload  
**MVP status:** Required  
**Primary purpose:** Extract useful data from uploaded documents and create draft records for user approval.

### 35.1 Triggered by

- Uploaded invoice.
- Uploaded quote.
- Uploaded receipt.
- Uploaded organic document.
- Uploaded field note.

### 35.2 Agents involved

1. Document / Media Intake Agent.
2. Records + Inventory Agent.
3. Procurement Agent if input quote/invoice.
4. Compliance Agent if sensitive document.
5. Action Agent after approval.

### 35.3 Required outputs

- Extracted fields.
- Confidence.
- Missing fields.
- Redactions.
- Draft record.
- Approval requirement.

### 35.4 Required guardrails

- Never update official records from uncertain extraction without approval.
- Redact credentials and secrets.
- Preserve original document reference securely.
- Track audit metadata.

---

## 35b. Workflow Contract: Irrigation Schedule / Water Request Advisor

**Workflow name:** Irrigation Schedule / Water Request Advisor  
**MVP status:** Tier 2 / post-first-slice mock workflow using manual or uploaded schedule data.  
**Primary purpose:** Help a farmer review irrigation timing, identify missing data, and draft a water-request action using field/crop context, weather, provider schedule, allocation status, and user approval.

### 35b.1 Triggered by
- Irrigation question or schedule request.
- Stored weather alerts indicating soil moisture or heat stress.

### 35b.2 Agents involved
1. Weather + Fieldwork Agent.
2. Records + Inventory Agent.
3. Compliance Agent.
4. Action Agent.

### 35b.3 Required outputs
- Minimized task context (soil, field, crop).
- Irrigation timing considerations.
- Missing crop water demand/allocation data.
- Draft water-request action.
- Human review status.

### 35b.4 Required guardrails
- Must not submit portal request without approval.
- Must not ask for credentials in chat.
- Must not interpret water rights as legal advice.
- Must not override district/provider rules.

---

## 36. Agent Handoff Rules

### 36.1 Supervisor to specialist

The Supervisor should pass:

- WorkItem.
- FarmContextPackage.
- Allowed tool list.
- Data-sensitivity constraints.
- Output requirements.

The Supervisor should not pass unrelated findings or unnecessary raw documents.

### 36.2 Specialist to Evidence Board

Each specialist should return an AgentFinding with:

- Summary.
- Recommendation.
- Evidence IDs.
- Confidence.
- Missing data.
- Assumptions.
- Human-review requirements.
- Sensitivity labels.

### 36.3 Evidence Board to Synthesizer

The Evidence Board should pass structured findings and evidence summaries, not raw unrestricted data.

### 36.4 Synthesizer to Action Agent

The Synthesizer should pass an Action Pack with explicit action candidates and human-review requirements.

### 36.5 Action Agent to Tool Gateway

The Action Agent should pass only approved actions, purpose, payload, disclosure preview, and required audit metadata.

---

## 37. Evaluation Requirements by Agent

Every agent should be evaluated using synthetic scenarios from `03_FARM_PROFILES.md` and future scenarios from `07_SAMPLE_SCENARIOS.md`.

### 37.1 Universal evaluation tests

Each agent must pass tests that verify:

- Uses HarvestAmp name, not prior working names.
- Does not request or expose credentials.
- Does not cross farm boundaries.
- Respects user role permissions.
- Marks missing data.
- Marks stale data.
- Preserves evidence IDs.
- Includes human-review fields when required.
- Avoids unsupported claims.
- Avoids final regulated advice.

### 37.2 Privacy and authorization tests

- Employee cannot see supplier quotes or margin.
- Advisor cannot access unauthorized farms.
- Supplier-facing draft excludes competitor quotes unless approved.
- Prompt context excludes raw credentials.
- External action is blocked without approval.

### 37.3 Domain tests

- Weather Agent handles spray-window question with compliance flag.
- Procurement Agent handles diesel buy/wait/split recommendation.
- Procurement Agent compares fertilizer quotes by nutrient cost.
- Market Agent handles direct-market harvest planning.
- Compliance Agent flags organic input uncertainty.
- Records Agent creates draft inventory update from invoice.
- Synthesizer produces a clean weekly plan.

---

## 38. Antigravity Build Instructions

When building any HarvestAmp agent in Antigravity, start the task with:

```text
The product/agent is named HarvestAmp. Treat `01_PRODUCT_BRIEF.md`, `02_AGENT_ARCHITECTURE.md`, `03_FARM_PROFILES.md`, `04_DATA_SOURCES.md`, and `05_AGENT_CONTRACTS.md` as the current source-of-truth files. Do not use prior working names in code, docs, prompts, UI labels, schemas, connectors, or marketplace copy.
```

Then provide the specific agent contract from this file.

### 38.1 Recommended build order

1. Shared schemas and test fixtures.
2. Credential Broker / Authorization Service skeleton.
3. Tool Gateway skeleton.
4. Context Package Builder.
5. Supervisor / Orchestrator skeleton with mock agents.
6. Intent Router.
7. Farm Profile Agent.
8. Weather + Fieldwork Agent.
9. Records + Inventory Agent.
10. Input Procurement Agent.
11. Margin + Scenario Agent.
12. Recommendation Synthesizer.
13. Document / Media Intake Agent.
14. Market + Sales Agent.
15. Compliance Agent.
16. Action Agent with approval gates.
17. Weekly Farm Action Plan workflow.
18. Fuel Buy Window workflow.
19. Fertilizer Quote Comparison workflow.
20. Direct-Market Weekly Plan workflow.

### 38.2 Antigravity task template

```text
Task: Build or refine the [AGENT NAME] for HarvestAmp.

Read first:
- 01_PRODUCT_BRIEF.md
- 02_AGENT_ARCHITECTURE.md
- 03_FARM_PROFILES.md
- 04_DATA_SOURCES.md
- 05_AGENT_CONTRACTS.md

Use this agent contract:
[Paste relevant section]

Use synthetic farms:
- Prairie View Farms
- Green Basket Organics

Acceptance criteria:
- Passes universal privacy and authorization checks.
- Returns the required structured output.
- Uses task-scoped context only.
- Does not expose credentials or cross-farm data.
- Adds human-review flags when required.
- Updates tests or examples if behavior changes.
```

---

## 39. Open Questions

These questions should be resolved in later documents or implementation planning.

1. Should the Intent Router be a standalone agent, a deterministic classifier, or part of the Supervisor in MVP?
2. Should Document / Media Intake be implemented before or after the first working weekly-plan workflow?
3. What minimum structured schemas should be implemented first: AgentFinding, EvidenceItem, ActionPack, WorkItem, or all together?
4. Should direct-market POS sales be manual-entry only in MVP?
5. Should fuel price monitoring use only public benchmark data at first or allow manual supplier quote entry first?
6. What dollar thresholds should trigger purchase approval by default?
7. Which user roles are needed in MVP: owner, manager, employee, advisor, market manager?
8. Should crop/livestock risk be a stub in MVP or a true specialist agent?
9. How should HarvestAmp represent confidence in price forecasts or market scenarios?
10. Which external data sources require license review before even a demo integration?

---

## 40. Current Contract Decision

The current HarvestAmp MVP should treat the following as required:

- Credential Broker / Authorization Service.
- Tool Gateway.
- Context Package Builder.
- Supervisor / Orchestrator Agent.
- Intent Router.
- Farm Profile Agent.
- Weather + Fieldwork Agent.
- Input Procurement Agent.
- Records + Inventory Agent.
- Market + Sales Agent.
- Compliance Agent.
- Margin + Scenario Agent.
- Recommendation Synthesizer.
- Action Agent with approval gates.
- Document / Media Intake Agent for uploaded quotes and invoices.

The first MVP should prove these workflows:

1. Weekly Farm Action Plan.
2. Fuel Buy Window.
3. Fertilizer Quote Comparison.
4. Direct-Market Weekly Plan.
5. Record Update from Upload.

The next recommended source-of-truth document is:

```text
06_RISK_AND_HUMAN_REVIEW_POLICY.md
```

That file should turn the human-review concepts in this contract into a more detailed risk policy and eventually a machine-readable rule set.
