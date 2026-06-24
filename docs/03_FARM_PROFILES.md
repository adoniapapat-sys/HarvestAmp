# 03_FARM_PROFILES.md

# Farm Profiles: HarvestAmp

**Version:** 0.2  
**Date:** 2026-06-22  
**Status:** Draft MVP planning document  
**Product name:** HarvestAmp  
**Related documents:** `01_PRODUCT_BRIEF.md`, `02_AGENT_ARCHITECTURE.md`  
**Intended use:** Source-of-truth farm profiles for Antigravity tasks, agent contracts, sample scenarios, evaluation tests, UI mockups, and early MVP demonstrations.

---

## 0. Revision Notes

### 0.2 HarvestAmp rename

Updated the working product name to **HarvestAmp** across the live source-of-truth documents. Farm profile data remains synthetic and unchanged.

---

## 0. Important Note

All farms, users, suppliers, quotes, prices, acreage, field names, inventory values, crop plans, and documents in this file are **synthetic test data**.

They are not real farms. They are not current market prices. They are not agricultural, legal, financial, insurance, organic, pesticide, or veterinary recommendations.

These profiles exist so HarvestAmp can be designed, tested, and evaluated against stable representative farm contexts before real customer data or real integrations are used.

---

## 1. Purpose of This Document

This document defines the two MVP farm profiles for **HarvestAmp**:

1. **Prairie View Farms** - a large conventional row-crop operation.
2. **Green Basket Organics** - a small organic direct-market farm.

The purpose is to give every later HarvestAmp component a common test context.

Future documents and build tasks should use these profiles when defining:

- Agent contracts.
- Data-source requirements.
- Sample scenarios.
- Evaluation tests.
- UI screens.
- Privacy and authorization behavior.
- Human-in-the-loop rules.
- Monitoring loops.
- Marketplace demo flows.

The profiles are intentionally different. HarvestAmp must prove that it can adapt to both:

- A large commodity crop farm focused on acres, input costs, weather windows, fieldwork, grain markets, and margin per acre or bushel.
- A smaller diversified organic farm focused on harvest planning, farmers markets, CSA, packaging, organic records, market-day weather, and many small operational decisions.

---

## 2. How to Use This Document

### 2.1 For Antigravity development tasks

Before building any HarvestAmp agent, connector, UI screen, or workflow, the relevant Antigravity task should read this file and use one or both profiles as test context.

Example task instruction:

```text
Read 01_PRODUCT_BRIEF.md, 02_AGENT_ARCHITECTURE.md, and 03_FARM_PROFILES.md.
Use Prairie View Farms and Green Basket Organics as the MVP test farms.
Do not invent new farm assumptions unless you update 03_FARM_PROFILES.md.
```

### 2.2 For agent contracts

`05_AGENT_CONTRACTS.md` should reference these profiles when specifying each agent's expected inputs and outputs.

For example:

- Weather Agent should be tested against Prairie View spray-window questions and Green Basket market-day weather questions.
- Procurement Agent should be tested against Prairie View fuel/fertilizer/seed workflows and Green Basket packaging/organic-input workflows.
- Compliance Agent should be tested against pesticide, USDA, organic certification, and food-safety questions.

### 2.3 For evaluation tests

`08_EVALUATION_TESTS.md` should convert many of the sample prompts in this file into formal test cases.

Each test should check:

- Correct agent routing.
- Proper use of farm context.
- Evidence-backed recommendations.
- Correct human-review flagging.
- No unauthorized disclosure.
- No raw credential exposure.
- No cross-farm leakage.

### 2.4 For UI design

UI screens should be tested against both farm types.

The row-crop dashboard should not look identical to the organic direct-market dashboard. They share platform concepts, but their priorities, labels, workflows, and alerts differ.

---

## 3. Design Principles for MVP Farm Profiles

### 3.1 Use realistic but synthetic data

The profiles should feel practical enough to support design decisions, but they must not include real customer data.

### 3.2 Create contrast between farm types

The two profiles should differ by:

- Scale.
- Crops.
- Sales channels.
- Procurement needs.
- Compliance needs.
- Human-review thresholds.
- Inventory categories.
- UI priorities.
- Language and recommendations.

### 3.3 Keep the profiles stable

These profiles should remain stable across early development. If an agent performs differently from week to week, the evaluation tests should reveal whether the change is intentional.

### 3.4 Do not overfit HarvestAmp to these profiles

The MVP should use these farms to prove the concept, but the architecture should still support later farm types:

- Specialty crop farms.
- Livestock farms.
- Greenhouse and nursery operations.
- Dairy operations.
- Mixed farms.
- Co-op or advisor-managed multi-farm accounts.

### 3.5 Preserve privacy boundaries

Even synthetic farm profiles should follow HarvestAmp's privacy design:

- Agents receive only task-scoped context.
- Supplier quotes are confidential.
- Field boundaries and inventory are confidential.
- Credentials never enter agent context.
- Farm A data must not be used to answer Farm B questions.

---

## 4. Shared MVP Assumptions

These assumptions apply to both profiles unless overridden.

### 4.1 Product stage

HarvestAmp is in MVP design.

The MVP should support:

- User-triggered workflows.
- Manual data entry.
- File upload and extraction.
- Synthetic or mock API data.
- Draft recommendations.
- Human approval before external actions.

The MVP should not yet require:

- Real supplier integrations.
- Real commodity trading execution.
- Automatic government filing.
- Automatic purchases.
- Automatic pesticide recommendations.
- Full farm-management-system integration.

### 4.2 Sample date context

For sample scenarios, use this planning week unless a scenario states otherwise:

```yaml
sample_week:
  week_start: "2026-06-22"
  week_end: "2026-06-28"
  season_context: "early summer growing season"
```

### 4.3 Human-in-the-loop default

HarvestAmp may analyze, summarize, compare, and draft recommendations.

HarvestAmp must require approval before:

- Sending supplier messages.
- Creating purchase orders.
- Sharing farm data outside the authorized account.
- Updating official records.
- Making regulated or high-impact recommendations.
- Taking actions that spend money or affect sales.

### 4.4 Data-source default

For MVP testing, HarvestAmp should use:

- Synthetic weather data.
- Synthetic supplier quotes.
- Synthetic inventory levels.
- Synthetic crop and market data.
- User-entered values.
- Uploaded sample documents.

Later versions can replace synthetic data with approved APIs, email ingestion, supplier integrations, and public data connectors.

---

## 5. MVP Profile Index

| Profile ID | Farm name | Farm type | Scale | Sales model | Core MVP emphasis |
|---|---|---|---|---|---|
| `PVF_ROW_CROP_001` | Prairie View Farms | Large conventional row-crop farm | 1,850 crop acres | Commodity grain channels | Weather windows, fuel, fertilizer, seed, grain marketing, fieldwork, margin |
| `GBO_DIRECT_001` | Green Basket Organics | Small organic direct-market farm | 8.5 total acres, 4.2 cropped acres | CSA, farmers market, restaurant, farm stand | Harvest planning, packaging, organic inputs, market-day prep, inventory, records |

---

## 6. Profile A: Prairie View Farms

## 6.1 Profile Summary

**Profile ID:** `PVF_ROW_CROP_001`  
**Farm name:** Prairie View Farms  
**Farm type:** Large conventional row-crop operation  
**Location for testing:** Central Illinois, United States  
**Operating scale:** 1,850 crop acres  
**Production model:** Conventional corn and soybean rotation with some winter wheat and cover crop acres  
**Sales model:** Commodity grain through elevators, co-op contracts, and stored grain  
**Primary HarvestAmp user:** Farm owner/operator and farm manager  
**MVP emphasis:** Fuel, fertilizer, seed, fieldwork weather windows, scouting, supplier quotes, grain marketing context, break-even scenarios, USDA/crop insurance reminders, task planning

### 6.1.1 HarvestAmp one-line value for this farm

> HarvestAmp helps Prairie View Farms protect margin and manage weekly fieldwork by combining weather, input costs, inventory, supplier quotes, grain-market context, crop risk, and deadlines into action recommendations.

---

## 6.2 Account and User Structure

```yaml
account:
  tenant_id: "tenant_pvf_demo"
  farm_id: "PVF_ROW_CROP_001"
  farm_name: "Prairie View Farms"
  subscription_type: "MVP demo"
  timezone: "America/Chicago"

users:
  - user_id: "pvf_owner_001"
    name: "Mason Reed"
    role: "farm_owner"
    permissions:
      - view_all_farm_data
      - approve_financial_actions
      - approve_supplier_messages
      - manage_users
      - connect_data_sources
      - export_reports

  - user_id: "pvf_manager_001"
    name: "Elena Carter"
    role: "farm_manager"
    permissions:
      - view_operational_data
      - view_supplier_quotes
      - create_tasks
      - approve_fieldwork_tasks
      - draft_supplier_messages
      - approve_purchases_under_threshold

  - user_id: "pvf_employee_001"
    name: "Field Crew User"
    role: "field_employee"
    permissions:
      - view_assigned_tasks
      - submit_field_notes
      - upload_photos
      - update_task_status
    restrictions:
      - cannot_view_supplier_quotes
      - cannot_view_margin_scenarios
      - cannot_approve_purchases
      - cannot_share_reports

  - user_id: "pvf_advisor_001"
    name: "External Agronomy Advisor"
    role: "authorized_advisor"
    permissions:
      - view_selected_fields
      - view_crop_notes
      - view_uploaded_scouting_images
      - comment_on_crop_risk
    restrictions:
      - cannot_view_fuel_quotes
      - cannot_view_grain_marketing_plan
      - cannot_view_full_margin_dashboard
```

### 6.2.1 Authorization design note

HarvestAmp must not assume that all users attached to Prairie View Farms can see all data.

For example:

- Field employees may submit field notes but should not see supplier quotes or break-even calculations.
- The external agronomy advisor may see crop-risk information for authorized fields but not fuel or grain-marketing data.
- Only the owner or authorized manager may approve external supplier messages.

---

## 6.3 Farm Data Sensitivity for Prairie View Farms

| Data type | Sensitivity | Notes |
|---|---|---|
| Public weather forecast | Public | Can be used freely in authorized farm workflows |
| Field names and acreages | Farm confidential | Do not disclose outside authorized account |
| Field boundaries | Farm confidential / restricted | Needed for weather and field-specific workflows, but should be minimized in prompts |
| Fuel tank level | Farm confidential | Reveals operational readiness |
| Supplier quotes | Farm restricted | Do not share with other suppliers unless user explicitly approves |
| Fertilizer program | Farm restricted | Commercial and agronomic sensitivity |
| Grain inventory and marketing plan | Farm restricted | Sensitive financial and competitive data |
| Break-even calculations | Farm restricted | Do not disclose outside authorized users |
| Crop insurance documents | Farm restricted | Expert/human review required for interpretation |
| User credentials | Credentials and secrets | Never exposed to LLM context |

---

## 6.4 Land and Field Structure

Prairie View Farms uses named fields. Exact boundaries are not required in early MVP tests; field names, acres, crop, and general conditions are sufficient.

```yaml
fields:
  - field_id: "PVF_FIELD_NORTH80"
    name: "North 80"
    acres: 80
    crop_2026: "soybeans"
    planting_date: "2026-05-08"
    drainage: "moderate"
    irrigation: "none"
    notes:
      - "Earlier soybean planting than most soybean acres"
      - "Scout first after extended leaf wetness"

  - field_id: "PVF_FIELD_HOME320"
    name: "Home 320"
    acres: 320
    crop_2026: "corn"
    planting_date: "2026-04-24"
    drainage: "good"
    irrigation: "none"
    notes:
      - "Near shop and main grain bins"
      - "Often used for quick field checks"

  - field_id: "PVF_FIELD_RIVER220"
    name: "River Bottom 220"
    acres: 220
    crop_2026: "corn"
    planting_date: "2026-04-29"
    drainage: "poor_to_moderate"
    irrigation: "none"
    notes:
      - "Flooding and ponding risk after heavy rain"
      - "Avoid heavy equipment if field is wet"

  - field_id: "PVF_FIELD_WESTRIDGE460"
    name: "West Ridge 460"
    acres: 460
    crop_2026: "soybeans"
    planting_date: "2026-05-12"
    drainage: "good"
    irrigation: "none"
    notes:
      - "Large field used for spray-window workflow tests"

  - field_id: "PVF_FIELD_SOUTH600"
    name: "South 600"
    acres: 600
    crop_2026: "corn"
    planting_date: "2026-04-26"
    drainage: "moderate"
    irrigation: "none"
    notes:
      - "Largest continuous corn acreage"
      - "High fuel demand during field operations"

  - field_id: "PVF_FIELD_WHEAT170"
    name: "Wheat 170"
    acres: 170
    crop_2026: "winter wheat"
    planting_date: "2025-10-11"
    drainage: "good"
    irrigation: "none"
    notes:
      - "Harvest and double-crop decision testing"
```

### 6.4.1 Acreage summary

```yaml
acreage_summary_2026:
  corn_acres: 1140
  soybean_acres: 540
  winter_wheat_acres: 170
  total_crop_acres: 1850
```

---

## 6.5 Crop and Season Context

For early summer scenarios, Prairie View Farms is in a period where the main decisions include:

- Post-emergence weed control.
- Fungicide scouting decisions.
- Nutrient side-dress or late nitrogen checks.
- Fuel planning for spraying, hauling, scouting, and upcoming wheat harvest.
- Grain storage and sales monitoring.
- Weather-sensitive fieldwork.
- Supplier quote comparison.
- USDA/crop insurance reminders.

```yaml
season_context:
  sample_week: "2026-06-22 to 2026-06-28"
  corn_stage_assumption: "vegetative growth, exact stage must be verified"
  soybean_stage_assumption: "vegetative growth, exact stage must be verified"
  wheat_stage_assumption: "approaching harvest readiness, exact stage must be verified"
  scouting_priorities:
    - corn_leaf_disease_watch
    - soybean_leaf_disease_watch
    - weed_escape_check
    - field_wetness_after_rain
    - wheat_harvest_readiness
```

### 6.5.1 Agronomic caution

HarvestAmp may suggest scouting priorities and field checks, but should not make definitive pesticide, rate, or tank-mix recommendations. Spray-related decisions must trigger label, advisor, and human-review guardrails.

---

## 6.6 Equipment and Fuel Context

Prairie View Farms has enough scale that diesel planning is financially meaningful.

```yaml
equipment_context:
  key_equipment:
    - "high-horsepower tractor"
    - "planter"
    - "self-propelled sprayer"
    - "combine"
    - "grain cart"
    - "semi truck"
    - "utility pickup"
  fuel_types:
    - "off-road diesel"
    - "on-road diesel"
    - "gasoline"
    - "propane for grain drying, seasonal"

fuel_inventory:
  diesel_tank_capacity_gallons: 4000
  current_diesel_gallons_estimate: 1350
  current_diesel_percent_full: 34
  last_manual_tank_update: "2026-06-21"
  expected_30_day_diesel_need_gallons: 3100
  supplier_delivery_minimum_gallons: 500
  preferred_minimum_reserve_gallons: 700
  data_quality: "user-entered estimate"
```

### 6.6.1 Fuel decision pattern

HarvestAmp should combine:

- Current supplier quote.
- Historical farm fuel prices.
- Public benchmark trend if available.
- Tank level.
- Tank capacity.
- Expected operations in the next 30 days.
- Weather windows.
- Delivery lead time.
- Cash-flow sensitivity.

HarvestAmp should prefer recommendations like:

> Consider buying enough fuel to cover the next fieldwork window and setting an alert for the remainder.

HarvestAmp should avoid overconfident predictions like:

> Diesel will be cheapest on Friday.

---

## 6.7 Suppliers and Procurement Context

Prairie View Farms buys from multiple supplier types.

```yaml
suppliers:
  - supplier_id: "PVF_SUPPLIER_COOP_001"
    display_name: "Prairie Central Co-op"
    supplier_type: "co-op"
    supplies:
      - fertilizer
      - crop_protection_products
      - custom_application
      - grain_marketing
    data_access_status: "manual_entry_and_uploaded_quotes_only"
    disclosure_rule: "Do not disclose competing supplier quotes unless owner approves"

  - supplier_id: "PVF_SUPPLIER_FUEL_001"
    display_name: "River County Fuel"
    supplier_type: "fuel_distributor"
    supplies:
      - off_road_diesel
      - on_road_diesel
      - propane
      - lubricants
    data_access_status: "manual_entry_only"
    disclosure_rule: "Supplier may receive purchase inquiries after user approval"

  - supplier_id: "PVF_SUPPLIER_SEED_001"
    display_name: "Heartland Seed Dealer"
    supplier_type: "seed_dealer"
    supplies:
      - corn_seed
      - soybean_seed
      - seed_treatments
    data_access_status: "uploaded_quotes_only"
    disclosure_rule: "Seed quote and discount terms are restricted"

  - supplier_id: "PVF_SUPPLIER_PARTS_001"
    display_name: "County Equipment"
    supplier_type: "equipment_dealer"
    supplies:
      - parts
      - service
      - repair
    data_access_status: "manual_entry_only"
    disclosure_rule: "No access to farm financials or input quotes"
```

### 6.7.1 Input categories for row-crop MVP

```yaml
row_crop_input_categories:
  fuel:
    - off_road_diesel
    - on_road_diesel
    - propane
    - gasoline
    - lubricants
  fertilizer:
    - anhydrous_ammonia
    - urea
    - uan
    - dap
    - map
    - potash
    - lime
    - micronutrients
  seed:
    - corn_seed
    - soybean_seed
    - wheat_seed
    - cover_crop_seed
  crop_protection:
    - herbicide
    - fungicide
    - insecticide
    - adjuvant
    - seed_treatment
  equipment_and_parts:
    - filters
    - oil
    - tires
    - belts
    - wear_parts
    - sprayer_parts
    - combine_parts
  services:
    - soil_testing
    - custom_application
    - trucking
    - grain_drying
    - crop_consulting
```

---

## 6.8 Synthetic Supplier Quotes

All values are synthetic. They are included only for workflow testing.

```yaml
supplier_quotes:
  - quote_id: "PVF_QUOTE_DIESEL_2026_06_21"
    supplier_id: "PVF_SUPPLIER_FUEL_001"
    input_type: "off_road_diesel"
    quoted_price: 3.68
    unit: "USD_per_gallon"
    minimum_delivery_gallons: 500
    delivery_fee: 0
    quote_date: "2026-06-21"
    valid_until: "2026-06-25"
    data_source: "manual_entry"
    sensitivity: "farm_restricted"

  - quote_id: "PVF_QUOTE_UREA_2026_06_20"
    supplier_id: "PVF_SUPPLIER_COOP_001"
    input_type: "urea"
    quoted_price: 475
    unit: "USD_per_ton"
    delivery_fee: "not_provided"
    application_fee: "not_provided"
    quote_date: "2026-06-20"
    valid_until: "2026-06-27"
    data_source: "uploaded_pdf"
    sensitivity: "farm_restricted"

  - quote_id: "PVF_QUOTE_UAN32_2026_06_20"
    supplier_id: "PVF_SUPPLIER_COOP_001"
    input_type: "uan_32"
    quoted_price: 340
    unit: "USD_per_ton"
    delivery_fee: "not_provided"
    application_fee: "not_provided"
    quote_date: "2026-06-20"
    valid_until: "2026-06-27"
    data_source: "uploaded_pdf"
    sensitivity: "farm_restricted"

  - quote_id: "PVF_QUOTE_SEED_CORN_2026_PRESEASON"
    supplier_id: "PVF_SUPPLIER_SEED_001"
    input_type: "corn_seed"
    quoted_price: 292
    unit: "USD_per_bag"
    treatment_included: true
    replant_policy: "included_with_conditions"
    quote_date: "2025-11-15"
    data_source: "uploaded_pdf"
    sensitivity: "farm_restricted"
```

### 6.8.1 Quote-comparison rule

For row-crop inputs, HarvestAmp should not compare only sticker prices.

HarvestAmp should consider:

- Unit conversion.
- Nutrient content for fertilizer.
- Delivery fees.
- Application fees.
- Discounts.
- Minimum delivery quantities.
- Timing constraints.
- Inventory already on hand.
- Weather window.
- Cash-flow impact.
- Human-review threshold.

---

## 6.9 Inventory and Records Context

```yaml
inventory:
  fuel:
    off_road_diesel_gallons: 1350
    on_road_diesel_gallons: 250
    propane_gallons: 0
    last_updated: "2026-06-21"
    data_quality: "manual_estimate"

  seed:
    corn_seed_bags_remaining: 8
    soybean_seed_units_remaining: 12
    wheat_seed_units_remaining: 0
    cover_crop_seed_units_remaining: 0
    last_updated: "2026-06-10"
    data_quality: "manual_entry"

  fertilizer:
    urea_tons_booked: 0
    uan_32_tons_booked: 0
    potash_tons_booked: 0
    last_updated: "2026-06-20"
    data_quality: "quote_extraction"

  crop_protection:
    herbicide_inventory_status: "partial"
    fungicide_inventory_status: "unknown"
    adjuvant_inventory_status: "low"
    last_updated: "2026-06-18"
    data_quality: "manual_entry"

  grain_storage:
    corn_storage_capacity_bushels: 120000
    soybean_storage_capacity_bushels: 30000
    current_stored_corn_bushels: 42000
    current_stored_soybean_bushels: 9000
    data_quality: "manual_entry"
```

### 6.9.1 Inventory logic expectations

HarvestAmp should be able to say:

- Whether the farm has enough diesel for the next planned fieldwork window.
- Whether fertilizer quotes are missing delivery or application fees.
- Whether crop-protection inventory is too incomplete to support a spray recommendation.
- Whether stored grain decisions should route to the Market + Sales Agent and require user approval.

---

## 6.10 Sales and Market Context

Prairie View Farms sells primarily through commodity grain channels.

```yaml
sales_channels:
  - channel_id: "PVF_MARKET_ELEVATOR_001"
    channel_type: "grain_elevator"
    display_name: "Prairie Central Elevator"
    crops:
      - corn
      - soybeans
      - wheat
    data_access_status: "manual_price_entry_for_mvp"

  - channel_id: "PVF_MARKET_CONTRACT_001"
    channel_type: "forward_contract"
    display_name: "Existing grain contracts"
    crops:
      - corn
      - soybeans
    data_access_status: "uploaded_documents_only"

marketing_context:
  strategy_style: "balanced"
  risk_tolerance: "medium"
  current_focus:
    - monitor_cash_bids
    - compare_basis
    - evaluate_storage_cost
    - protect_margin_above_break_even
  human_review_required_for:
    - sale_recommendations
    - hedging_discussion
    - contract_changes
    - supplier_or_buyer_messages
```

### 6.10.1 Market guidance rule

HarvestAmp may provide scenarios, calculations, summaries, and watchlist alerts.

HarvestAmp must not execute trades, make binding sale commitments, or provide definitive financial advice. Grain sale recommendations should be framed as scenarios requiring user approval.

---

## 6.11 Compliance and Deadline Context

```yaml
compliance_context:
  pesticide_license_status: "not_stored_in_mvp"
  crop_insurance_agent: "not_connected_in_mvp"
  usda_service_center: "not_connected_in_mvp"
  acreage_reporting_status: "unknown_for_sample_week"
  organic_status: "not_organic"
  food_safety_program: "not_applicable_for_row_crop_mvp"

watch_items:
  - "acreage reporting reminders"
  - "crop insurance date reminders"
  - "restricted-use pesticide guardrails"
  - "spray recordkeeping"
  - "worker safety reminders"
```

### 6.11.1 Compliance behavior

HarvestAmp may:

- Remind the user about potential deadlines.
- Create checklists.
- Flag missing documents.
- Draft questions to advisors.

HarvestAmp should require human or expert review for:

- Crop insurance interpretation.
- USDA eligibility questions.
- Pesticide label details.
- Official form filing.
- Regulated chemical recommendations.

---

## 6.12 Prairie View Pain Points

Top pain points for this farm profile:

1. Input costs can move quickly and materially affect margin.
2. Diesel purchasing must align with fieldwork windows and tank capacity.
3. Fertilizer quotes require normalization by nutrient, delivery, and application cost.
4. Spray decisions depend on weather, crop stage, label constraints, inventory, and drift risk.
5. Grain sales require careful scenario framing, not overconfident advice.
6. Field tasks and scouting priorities change with weather.
7. Different users need different data permissions.
8. Supplier quotes must not leak to other suppliers.

---

## 6.13 Prairie View Routine Workflows

### 6.13.1 Weekly farm action plan

User asks:

> What should I know about Prairie View Farms this week?

Expected HarvestAmp routing:

```yaml
route_to_agents:
  - Supervisor Agent
  - Weather + Fieldwork Agent
  - Input Procurement Agent
  - Records + Inventory Agent
  - Market + Sales Agent
  - Compliance Agent
  - Margin + Scenario Agent
  - Recommendation Synthesizer
```

Expected output categories:

- This week's fieldwork windows.
- Fuel status and buy/watch recommendation.
- Fertilizer quote gaps and comparison needs.
- Crop scouting priorities.
- Stored grain or cash-bid watchlist.
- Compliance/deadline watchlist.
- Missing data.
- Human-review flags.

### 6.13.2 Fuel buy-window workflow

User asks:

> Should I buy diesel this month?

Expected HarvestAmp behavior:

- Check tank level.
- Check tank capacity.
- Check expected 30-day fuel need.
- Check supplier quote age and validity.
- Check upcoming fieldwork weather windows.
- Compare against historical farm price if available.
- Use public benchmark only as context, not as the decision anchor.
- Recommend buy, wait, or split purchase with confidence level.
- Require user approval before supplier contact or purchase order.

### 6.13.3 Fertilizer quote comparison workflow

User asks:

> Compare the urea and UAN quotes.

Expected HarvestAmp behavior:

- Extract product, unit, quote date, validity, and missing fees.
- Normalize cost by nutrient where enough data is available.
- Flag missing delivery/application fees.
- Ask for soil test targets or planned application if needed.
- Route agronomic rate decisions to human/expert review.
- Do not disclose quote details to other suppliers unless explicitly approved.

### 6.13.4 Spray-window workflow

User asks:

> Can I spray West Ridge tomorrow morning?

Expected HarvestAmp behavior:

- Check field, crop, forecast wind, rain, temperature, and field wetness.
- Ask for product label or planned operation if needed.
- Flag that pesticide label and local restrictions must be checked.
- Avoid product-specific rates or tank mixes unless routed to expert review.
- Require approval before scheduling crew instructions.

### 6.13.5 Grain market workflow

User asks:

> Should I sell some stored corn this week?

Expected HarvestAmp behavior:

- Check stored quantity.
- Check user-entered cash bid or benchmark data if available.
- Check break-even and storage-cost assumptions if available.
- Provide scenarios rather than definitive sell advice.
- Require user approval for any buyer message or sale action.

---

## 6.14 Prairie View Sample Prompts

```text
What should I know about the farm this week?
Should I buy diesel this month?
Do I have enough diesel for next week's fieldwork?
Compare these fertilizer quotes.
Which quote is cheaper per pound of nitrogen?
Can I spray West Ridge tomorrow morning?
What should I scout this week?
Are we missing any crop insurance or USDA deadlines?
What does the new urea quote do to my corn break-even?
Draft a message to River County Fuel asking for a 2,000 gallon diesel quote.
Do not send it until I approve.
Summarize my stored grain position.
Create a field task list for Elena and the crew.
```

---

## 6.15 Prairie View Human-Review Defaults

```yaml
human_review_defaults:
  purchase_approval:
    required_for_all_external_purchases: true
    manager_soft_threshold_usd: 10000
    owner_required_threshold_usd: 25000

  supplier_messages:
    approval_required_before_send: true
    quote_disclosure_requires_explicit_approval: true

  pesticide_related:
    expert_review_required_for:
      - product_choice
      - application_rate
      - tank_mix
      - restricted_use_questions
      - label_interpretation
      - re_entry_interval
      - pre_harvest_interval
      - drift_sensitive_conditions

  market_sales:
    user_approval_required_for:
      - buyer_message
      - sale_recommendation
      - contract_change
      - hedging_or_futures_discussion

  records:
    approval_required_for:
      - official_record_update
      - crop_insurance_document_changes
      - acreage_report_submission
```

---

## 6.16 Prairie View Out of Scope for MVP

The MVP should not attempt to support:

- Automatic grain trades.
- Automatic supplier purchases.
- Fully automated pesticide recommendations.
- Full precision-ag yield-map analysis.
- Live equipment telematics.
- Live bank account integration.
- Crop insurance claim submission.
- Government form filing.
- Real-time co-op portal integration.

---

## 7. Profile B: Green Basket Organics

## 7.1 Profile Summary

**Profile ID:** `GBO_DIRECT_001`  
**Farm name:** Green Basket Organics  
**Farm type:** Small organic direct-market farm  
**Location for testing:** Hudson Valley, New York, United States  
**Operating scale:** 8.5 total acres, 4.2 cropped acres, two high tunnels  
**Production model:** Certified organic diversified vegetables, herbs, flowers, and small fruit  
**Sales model:** CSA, farmers market, farm stand, restaurants, and small local wholesale  
**Primary HarvestAmp user:** Owner/operator who also handles sales and records  
**MVP emphasis:** Weekly harvest planning, market-day weather, CSA box planning, organic input documentation, packaging inventory, seed orders, irrigation, labor task lists, customer-facing drafts

### 7.1.1 HarvestAmp one-line value for this farm

> HarvestAmp helps Green Basket Organics plan harvests, manage market and CSA commitments, monitor organic-approved inputs and packaging inventory, prepare weekly tasks, and avoid missing weather, compliance, or supply risks.

---

## 7.2 Account and User Structure

```yaml
account:
  tenant_id: "tenant_gbo_demo"
  farm_id: "GBO_DIRECT_001"
  farm_name: "Green Basket Organics"
  subscription_type: "MVP demo"
  timezone: "America/New_York"

users:
  - user_id: "gbo_owner_001"
    name: "Ari Morgan"
    role: "farm_owner"
    permissions:
      - view_all_farm_data
      - approve_purchases
      - approve_customer_messages
      - approve_supplier_messages
      - manage_users
      - connect_data_sources
      - export_reports

  - user_id: "gbo_field_lead_001"
    name: "Seasonal Field Lead"
    role: "field_lead"
    permissions:
      - view_assigned_tasks
      - update_harvest_counts
      - update_packaging_counts
      - submit_pest_notes
      - upload_crop_photos
    restrictions:
      - cannot_view_full_financials
      - cannot_approve_external_messages
      - cannot_change_certification_records

  - user_id: "gbo_market_staff_001"
    name: "Market Staff User"
    role: "market_staff"
    permissions:
      - view_market_pack_list
      - update_market_sales_notes
      - report_leftover_inventory
    restrictions:
      - cannot_view_supplier_quotes
      - cannot_view_certification_documents
      - cannot_approve_purchases

  - user_id: "gbo_certifier_contact_001"
    name: "Organic Certifier Reviewer"
    role: "external_reviewer"
    permissions:
      - view_certification_packet_when_shared
      - comment_on_input_records_when_shared
    restrictions:
      - no_default_access
      - access_requires_explicit_owner_share
```

### 7.2.1 Authorization design note

Green Basket Organics has a small team, but data boundaries still matter.

For example:

- Market staff can see pack lists but not supplier invoices or certification documents.
- A certifier contact should not have ongoing access to all farm data by default.
- Customer-facing messages must be approved before sending.

---

## 7.3 Farm Data Sensitivity for Green Basket Organics

| Data type | Sensitivity | Notes |
|---|---|---|
| Public weather forecast | Public | Can support market-day and frost/heat workflows |
| Crop list and harvest plan | Farm confidential | May reveal sales strategy and availability |
| CSA member count | Farm confidential | Customer and business sensitivity |
| Restaurant orders | Farm confidential | Buyer relationship data |
| Organic input records | Farm restricted | Certification-sensitive |
| Supplier invoices | Farm restricted | Commercial data |
| Packaging inventory | Farm confidential | Operational readiness |
| Customer emails | Farm restricted | Customer privacy applies |
| Certifier communications | Farm restricted | External sharing requires owner approval |
| User credentials | Credentials and secrets | Never exposed to LLM context |

---

## 7.4 Land, Growing Areas, and Infrastructure

Green Basket Organics uses smaller production areas and bed-based planning instead of large acreage-only field planning.

```yaml
growing_areas:
  - area_id: "GBO_AREA_FIELD_A"
    name: "Field A - Market Garden"
    area_type: "outdoor_beds"
    cropped_acres: 1.4
    bed_count: 52
    primary_crops:
      - lettuce
      - kale
      - carrots
      - beets
      - radishes
      - herbs
    irrigation: "drip_and_overhead"
    notes:
      - "Main weekly harvest area"
      - "High priority for market and CSA planning"

  - area_id: "GBO_AREA_FIELD_B"
    name: "Field B - Summer Crops"
    area_type: "outdoor_beds"
    cropped_acres: 1.8
    bed_count: 44
    primary_crops:
      - tomatoes
      - peppers
      - cucumbers
      - summer_squash
      - basil
      - cut_flowers
    irrigation: "drip"
    notes:
      - "Heat and disease monitoring important"
      - "Staking, trellis, and harvest labor sensitive"

  - area_id: "GBO_AREA_HIGHTUNNEL_1"
    name: "High Tunnel 1"
    area_type: "high_tunnel"
    cropped_acres: 0.3
    bed_count: 6
    primary_crops:
      - tomatoes
      - basil
      - cucumbers
    irrigation: "drip"
    notes:
      - "Humidity and ventilation risk"
      - "High-value harvest area"

  - area_id: "GBO_AREA_HIGHTUNNEL_2"
    name: "High Tunnel 2"
    area_type: "high_tunnel"
    cropped_acres: 0.2
    bed_count: 5
    primary_crops:
      - salad_mix
      - herbs
      - transplants
    irrigation: "drip"
    notes:
      - "Succession planting and transplant timing"

  - area_id: "GBO_AREA_BERRY_PATCH"
    name: "Berry Patch"
    area_type: "small_fruit"
    cropped_acres: 0.5
    primary_crops:
      - strawberries
      - raspberries
    irrigation: "drip"
    notes:
      - "Harvest timing and clamshell inventory important"
```

### 7.4.1 Acreage summary

```yaml
acreage_summary_2026:
  total_acres: 8.5
  cropped_acres: 4.2
  outdoor_cropped_acres: 3.7
  high_tunnel_cropped_acres: 0.5
  non_cropped_acres: 4.3
```

---

## 7.5 Crop and Season Context

For early summer scenarios, Green Basket Organics is managing many concurrent activities:

- Weekly CSA harvest.
- Saturday farmers market preparation.
- Restaurant availability list.
- Successive salad, herb, and root crop plantings.
- Irrigation scheduling.
- Organic pest and disease scouting.
- Packaging and ice inventory.
- Wash/pack labor planning.
- Organic input documentation.
- High tunnel ventilation and humidity monitoring.

```yaml
season_context:
  sample_week: "2026-06-22 to 2026-06-28"
  crop_groups:
    leafy_greens:
      status: "active_harvest"
      risks:
        - heat_stress
        - bolting
        - harvest_quality_loss
    fruiting_crops:
      status: "early_harvest_or_near_harvest"
      risks:
        - humidity_disease_pressure
        - trellis_labor_shortage
    root_crops:
      status: "staggered_harvest"
      risks:
        - wash_pack_time
        - bunching_supply_shortage
    herbs:
      status: "active_harvest"
      risks:
        - heat_stress
        - market_demand_variability
    berries:
      status: "active_or_peak_harvest_assumption"
      risks:
        - rain_damage
        - clamshell_shortage
```

### 7.5.1 Organic caution

HarvestAmp may help identify documentation needs and flag whether an input appears to require organic review. HarvestAmp should not make final organic-certification determinations unless a verified farm-specific approved input list is available and the workflow is designed for that purpose.

---

## 7.6 Equipment, Fuel, and Infrastructure Context

Green Basket Organics uses smaller equipment and more hand labor than Prairie View Farms.

```yaml
equipment_context:
  key_equipment:
    - "compact tractor"
    - "walk-behind tractor"
    - "delivery van"
    - "wash-pack station"
    - "walk-in cooler"
    - "irrigation pump"
    - "market tents and tables"
    - "hand tools"
  fuel_types:
    - "gasoline"
    - "diesel"
    - "propane for greenhouse heat, seasonal"
  infrastructure:
    - "walk-in cooler"
    - "wash-pack area"
    - "two high tunnels"
    - "farm stand"
    - "drip irrigation system"

fuel_inventory:
  gasoline_gallons_estimate: 22
  diesel_gallons_estimate: 38
  propane_status: "not_active_for_sample_week"
  delivery_van_fuel_status: "half_tank"
  last_manual_fuel_update: "2026-06-21"
  data_quality: "manual_estimate"
```

### 7.6.1 Fuel decision pattern

Fuel matters to Green Basket Organics, but not in the same way it matters to Prairie View Farms.

HarvestAmp should focus on:

- Market delivery readiness.
- Irrigation pump fuel.
- Small equipment fuel.
- Whether fuel inventory is enough for the week.
- Whether market-day travel or harvest logistics are at risk.

HarvestAmp should not over-prioritize commodity-style diesel-buy-window analysis for this profile unless the user asks.

---

## 7.7 Suppliers and Procurement Context

Green Basket Organics buys from a mix of local and specialty suppliers.

```yaml
suppliers:
  - supplier_id: "GBO_SUPPLIER_SEED_001"
    display_name: "Northeast Organic Seed Co."
    supplier_type: "seed_supplier"
    supplies:
      - organic_seed
      - cover_crop_seed
      - transplants
    data_access_status: "manual_entry_and_uploaded_orders"
    disclosure_rule: "Do not disclose crop plan or restaurant demand without owner approval"

  - supplier_id: "GBO_SUPPLIER_COMPOST_001"
    display_name: "Hudson Valley Compost"
    supplier_type: "soil_amendment_supplier"
    supplies:
      - compost
      - potting_mix
      - organic_soil_amendments
    data_access_status: "manual_entry_only"
    disclosure_rule: "Organic documentation should be verified before application"

  - supplier_id: "GBO_SUPPLIER_PACKAGING_001"
    display_name: "FarmPack Supply"
    supplier_type: "packaging_supplier"
    supplies:
      - clamshells
      - paper_bags
      - labels
      - CSA_boxes
      - twist_ties
      - rubber_bands
    data_access_status: "uploaded_invoices_and_manual_inventory"
    disclosure_rule: "No access to customer list or sales data"

  - supplier_id: "GBO_SUPPLIER_MARKET_001"
    display_name: "Saturday Village Market"
    supplier_type: "market_organization"
    supplies:
      - market_stall_information
      - market_rules
      - vendor_schedule
    data_access_status: "manual_entry_only"
    disclosure_rule: "Customer sales and inventory are not shared by default"

  - supplier_id: "GBO_SUPPLIER_CERTIFIER_001"
    display_name: "Organic Certifier"
    supplier_type: "certifier"
    supplies:
      - certification_review
      - approved_input_guidance
    data_access_status: "explicit_owner_share_only"
    disclosure_rule: "Share only owner-approved certification packet or input question"
```

### 7.7.1 Input categories for direct-market organic MVP

```yaml
direct_market_input_categories:
  seeds_and_transplants:
    - organic_vegetable_seed
    - herb_seed
    - flower_seed
    - cover_crop_seed
    - greenhouse_transplants
  soil_and_fertility:
    - compost
    - potting_mix
    - organic_fertilizer
    - fish_emulsion
    - mineral_amendments
    - cover_crop_seed
  crop_protection:
    - organic_approved_pest_control
    - insect_netting
    - row_cover
    - traps
    - beneficial_insects
  irrigation:
    - drip_tape
    - fittings
    - filters
    - pump_parts
    - timers
  harvest_and_packaging:
    - clamshells
    - paper_bags
    - CSA_boxes
    - labels
    - rubber_bands
    - twist_ties
    - harvest_crates
    - ice
  market_supplies:
    - tent_weights
    - tablecloths
    - signs
    - price_cards
    - receipt_paper
    - card_reader_supplies
  infrastructure_and_tools:
    - hand_tools
    - wash_pack_supplies
    - cooler_supplies
    - greenhouse_supplies
```

---

## 7.8 Synthetic Supplier Quotes and Inventory Signals

All values are synthetic. They are included only for workflow testing.

```yaml
supplier_quotes:
  - quote_id: "GBO_QUOTE_CLAMSHELLS_2026_06_18"
    supplier_id: "GBO_SUPPLIER_PACKAGING_001"
    input_type: "pint_clamshells"
    quoted_price: 72
    unit: "USD_per_case"
    case_quantity: 500
    delivery_fee: 18
    quote_date: "2026-06-18"
    valid_until: "2026-06-30"
    data_source: "uploaded_invoice"
    sensitivity: "farm_restricted"

  - quote_id: "GBO_QUOTE_CSA_BOXES_2026_06_18"
    supplier_id: "GBO_SUPPLIER_PACKAGING_001"
    input_type: "CSA_boxes"
    quoted_price: 1.15
    unit: "USD_per_box"
    minimum_order_quantity: 250
    delivery_fee: 25
    quote_date: "2026-06-18"
    valid_until: "2026-06-30"
    data_source: "uploaded_invoice"
    sensitivity: "farm_restricted"

  - quote_id: "GBO_QUOTE_COMPOST_2026_06_19"
    supplier_id: "GBO_SUPPLIER_COMPOST_001"
    input_type: "screened_compost"
    quoted_price: 48
    unit: "USD_per_cubic_yard"
    delivery_fee: 95
    organic_documentation_status: "not_verified"
    quote_date: "2026-06-19"
    valid_until: "2026-06-26"
    data_source: "manual_entry"
    sensitivity: "farm_restricted"

  - quote_id: "GBO_QUOTE_ORGANIC_FERT_2026_06_20"
    supplier_id: "GBO_SUPPLIER_COMPOST_001"
    input_type: "organic_granular_fertilizer"
    quoted_price: 38
    unit: "USD_per_50lb_bag"
    organic_documentation_status: "uncertain"
    quote_date: "2026-06-20"
    valid_until: "2026-06-27"
    data_source: "manual_entry"
    sensitivity: "farm_restricted"
```

---

## 7.9 Inventory and Records Context

```yaml
inventory:
  packaging:
    pint_clamshells_on_hand: 160
    quart_clamshells_on_hand: 85
    paper_bags_on_hand: 420
    CSA_boxes_on_hand: 110
    labels_on_hand: 260
    rubber_bands_on_hand: 900
    twist_ties_on_hand: 300
    last_updated: "2026-06-21"
    data_quality: "manual_count"

  harvest_supplies:
    harvest_crates_available: 42
    ice_bags_reserved_for_market: 8
    market_tent_status: "available"
    tent_weights_status: "needs_check"
    card_reader_status: "available"
    receipt_paper_status: "low"

  soil_and_fertility:
    compost_cubic_yards_on_hand: 2
    potting_mix_bags_on_hand: 9
    organic_fertilizer_bags_on_hand: 4
    fish_emulsion_gallons_on_hand: 1.5
    organic_documentation_complete: false

  seeds_and_transplants:
    fall_carrot_seed_status: "needs_order"
    lettuce_seed_status: "adequate_for_two_successions"
    basil_seed_status: "low"
    cover_crop_seed_status: "not_ordered"

  customer_commitments:
    CSA_member_count: 75
    Saturday_market_expected: true
    restaurant_orders_active: 4
    farm_stand_open_days:
      - Friday
      - Sunday
```

### 7.9.1 Inventory logic expectations

HarvestAmp should be able to say:

- Whether packaging is sufficient for the next CSA pack and farmers market.
- Whether organic input documentation is incomplete.
- Whether rain or heat may change harvest quantities.
- Whether market-day supplies are incomplete.
- Whether seed order deadlines may affect fall succession planting.

---

## 7.10 Sales and Market Context

Green Basket Organics sells through multiple local channels.

```yaml
sales_channels:
  - channel_id: "GBO_CHANNEL_CSA_001"
    channel_type: "CSA"
    display_name: "Summer CSA"
    member_count: 75
    pickup_day: "Thursday"
    communication_method: "email_newsletter"
    approval_required_before_customer_send: true

  - channel_id: "GBO_CHANNEL_MARKET_001"
    channel_type: "farmers_market"
    display_name: "Saturday Village Market"
    market_day: "Saturday"
    market_start_time: "08:00"
    market_end_time: "13:00"
    travel_time_minutes: 35
    approval_required_before_public_availability_post: true

  - channel_id: "GBO_CHANNEL_RESTAURANT_001"
    channel_type: "restaurant"
    display_name: "Local restaurant accounts"
    active_accounts: 4
    availability_list_day: "Tuesday"
    delivery_day: "Wednesday"
    approval_required_before_send: true

  - channel_id: "GBO_CHANNEL_FARMSTAND_001"
    channel_type: "farm_stand"
    display_name: "On-farm stand"
    open_days:
      - Friday
      - Sunday
    approval_required_before_public_hours_change: true
```

### 7.10.1 Sales guidance rule

HarvestAmp may draft:

- CSA box plans.
- Market pack lists.
- Restaurant availability sheets.
- Farm stand prep lists.
- Customer emails.

HarvestAmp must require user approval before sending customer-facing or buyer-facing messages.

---

## 7.11 Compliance and Organic Context

```yaml
compliance_context:
  organic_status: "certified_organic"
  certifier_connection_status: "manual_share_only_for_mvp"
  approved_input_list_status: "partial"
  organic_system_plan_status: "not_stored_in_full_for_mvp"
  food_safety_plan_status: "basic_internal_records"
  worker_safety_status: "not_stored_in_mvp"
  pesticide_license_status: "not_applicable_for_mvp_assumption"

watch_items:
  - organic_input_documentation
  - seed_source_documentation
  - compost_and_manure_records
  - harvest_lot_records
  - wash_pack_sanitation_logs
  - CSA_and_market_customer_communications
  - food_safety_checklists
```

### 7.11.1 Organic behavior

HarvestAmp may:

- Flag that an input requires organic documentation.
- Prepare a question for the certifier.
- Organize uploaded input records.
- Track whether documentation is complete.
- Create internal audit-prep checklists.

HarvestAmp must not:

- Certify that an input is organic-approved unless a verified, farm-specific approved list is available.
- Send records to the certifier without user approval.
- Change official certification records without owner approval.

---

## 7.12 Green Basket Pain Points

Top pain points for this farm profile:

1. Many crops, harvest windows, and sales commitments happen at once.
2. Market-day weather affects harvest quantity, product quality, staffing, tent setup, and customer traffic.
3. Packaging shortages can disrupt CSA, restaurant, and market sales.
4. Organic input compliance requires documentation discipline.
5. Labor is limited, so weekly task prioritization matters.
6. Customer-facing messages need to be accurate and timely.
7. Small purchases may still matter because cash flow is tight.
8. The owner does not have time to manually reconcile notes, inventory, weather, and orders.

---

## 7.13 Green Basket Routine Workflows

### 7.13.1 Weekly farm action plan

User asks:

> What should I know about Green Basket this week?

Expected HarvestAmp routing:

```yaml
route_to_agents:
  - Supervisor Agent
  - Weather + Fieldwork Agent
  - Input Procurement Agent
  - Records + Inventory Agent
  - Market + Sales Agent
  - Compliance Agent
  - Recommendation Synthesizer
```

Expected output categories:

- CSA harvest and pack priorities.
- Farmers market weather and pack-list risks.
- Packaging inventory warnings.
- Organic input documentation gaps.
- Irrigation or heat-stress watchlist.
- High tunnel humidity or ventilation reminders.
- Restaurant availability draft needs.
- Missing data.
- Human-review flags.

### 7.13.2 Farmers market planning workflow

User asks:

> What should I bring to market Saturday?

Expected HarvestAmp behavior:

- Check expected harvest availability.
- Check market-day weather.
- Check packaging inventory.
- Check prior market notes if available.
- Create draft pack list.
- Flag tent weights, ice, receipt paper, and card reader status.
- Require approval before publishing availability or customer messages.

### 7.13.3 CSA box workflow

User asks:

> Build this week's CSA box plan.

Expected HarvestAmp behavior:

- Use member count.
- Check crop availability.
- Check weather impact on harvest.
- Check packaging supply.
- Draft box contents.
- Draft member email.
- Require approval before sending email.

### 7.13.4 Organic input workflow

User asks:

> Can I use this fertilizer on my organic fields?

Expected HarvestAmp behavior:

- Extract product name and documentation if uploaded.
- Check farm's approved input list if available.
- If not verified, flag certifier review.
- Draft a question to the certifier.
- Require user approval before sharing documentation externally.
- Avoid final certification determination.

### 7.13.5 Packaging procurement workflow

User asks:

> Do I have enough clamshells and CSA boxes for the next two weeks?

Expected HarvestAmp behavior:

- Check packaging inventory.
- Estimate usage from CSA member count, market plan, berries, and restaurant orders.
- Compare reorder quantities and delivery timing.
- Recommend order/watch/urgent reorder with confidence level.
- Require approval before placing order or sending supplier message.

---

## 7.14 Green Basket Sample Prompts

```text
What should I know about the farm this week?
What should I bring to market Saturday?
Build this week's CSA box plan.
Do I have enough CSA boxes and clamshells for the next two weeks?
Draft a restaurant availability list for Tuesday.
Do not send it until I approve.
Can I use this fertilizer on organic fields?
Prepare a question to send to my certifier.
What harvest tasks should the field lead do tomorrow?
What does the Saturday weather mean for market setup?
Are we low on any market supplies?
Create a harvest and wash-pack checklist for Friday.
Summarize missing organic documentation.
```

---

## 7.15 Green Basket Human-Review Defaults

```yaml
human_review_defaults:
  purchase_approval:
    required_for_all_external_purchases: true
    owner_soft_threshold_usd: 500
    owner_required_threshold_usd: 1500

  customer_messages:
    approval_required_before_send: true
    applies_to:
      - CSA_newsletters
      - restaurant_availability_lists
      - market_posts
      - farm_stand_updates

  organic_related:
    expert_review_required_for:
      - input_approval_uncertain
      - seed_substitution_documentation
      - compost_or_manure_timing
      - certifier_packet_submission
      - organic_system_plan_changes

  food_safety_related:
    user_or_expert_review_required_for:
      - sanitation_record_changes
      - recall_or_contamination_risk
      - customer_health_or_safety_issue

  records:
    approval_required_for:
      - official_certification_record_update
      - customer_data_export
      - certifier_share
      - invoice_deletion
```

---

## 7.16 Green Basket Out of Scope for MVP

The MVP should not attempt to support:

- Full organic certification filing.
- Full POS integration.
- Automated customer emailing without approval.
- Automatic certifier submission.
- Full farm accounting.
- Labor payroll.
- Food safety audit submission.
- Live greenhouse sensor integration.
- Automatic ordering from suppliers.
- Final organic input approval without verified certifier data.

---

## 8. Comparison Matrix

| Dimension | Prairie View Farms | Green Basket Organics |
|---|---|---|
| Profile ID | `PVF_ROW_CROP_001` | `GBO_DIRECT_001` |
| Farm type | Large row-crop | Small organic direct-market |
| Scale | 1,850 crop acres | 8.5 total acres, 4.2 cropped acres |
| Main crops | Corn, soybeans, wheat | Vegetables, herbs, berries, flowers |
| Production style | Conventional | Certified organic |
| Main sales channels | Grain elevator, co-op, contracts, storage | CSA, farmers market, restaurants, farm stand |
| Main procurement focus | Diesel, fertilizer, seed, chemicals, parts | Packaging, organic seed, compost, organic inputs, market supplies |
| Main weather use | Spray, fieldwork, harvest, field trafficability | Harvest quality, irrigation, market day, high tunnel humidity |
| Main market use | Commodity prices, basis, storage, break-even | Pack lists, CSA commitments, restaurant availability, customer communication |
| Main compliance risks | Pesticide labels, crop insurance, USDA deadlines | Organic documentation, food safety, customer data |
| Main human-review triggers | Large purchases, pesticide, grain sales, supplier disclosures | Organic inputs, customer messages, packaging purchases, certifier sharing |
| Dashboard priority | Weather windows, input watch, margin, field tasks | Harvest plan, market plan, packaging inventory, organic records |

---

## 9. Shared HarvestAmp Behavior Across Both Profiles

HarvestAmp should adapt language and workflows by farm type, but certain principles are universal.

## 9.1 Universal behavior

HarvestAmp should:

- Use farm-specific context whenever available.
- Show source and data freshness.
- Identify missing information.
- Give confidence levels.
- Use human-review flags.
- Ask for approval before external actions.
- Preserve privacy and tenant isolation.
- Avoid pretending uncertain data is certain.
- Route regulated or high-risk topics to human or expert review.

## 9.2 Universal prohibited behavior

HarvestAmp must not:

- Reveal one farm's data to another farm.
- Expose supplier quotes to other suppliers without explicit approval.
- Put raw credentials into an LLM prompt.
- Send emails, supplier messages, or customer messages without approval.
- Make definitive pesticide or organic-certification determinations without proper verified authority.
- Execute purchases, trades, filings, or official submissions automatically in the MVP.
- Use customer farm data for model training, demos, or evaluation datasets without explicit authorization.

---

## 10. Agent Routing Expectations by Profile

## 10.1 Prairie View routing tendencies

Prairie View prompts will commonly route to:

- Weather + Fieldwork Agent.
- Input Procurement Agent.
- Records + Inventory Agent.
- Margin + Scenario Agent.
- Market + Sales Agent.
- Compliance Agent.

High-priority route triggers:

```yaml
prairie_view_route_triggers:
  fuel_purchase_question:
    agents:
      - Input Procurement Agent
      - Weather + Fieldwork Agent
      - Records + Inventory Agent
      - Margin + Scenario Agent
      - Recommendation Synthesizer

  fertilizer_quote_question:
    agents:
      - Input Procurement Agent
      - Records + Inventory Agent
      - Compliance Agent
      - Margin + Scenario Agent
      - Recommendation Synthesizer

  spray_window_question:
    agents:
      - Weather + Fieldwork Agent
      - Crop Risk Agent
      - Compliance Agent
      - Records + Inventory Agent
      - Recommendation Synthesizer

  grain_sale_question:
    agents:
      - Market + Sales Agent
      - Records + Inventory Agent
      - Margin + Scenario Agent
      - Recommendation Synthesizer
```

## 10.2 Green Basket routing tendencies

Green Basket prompts will commonly route to:

- Weather + Fieldwork Agent.
- Input Procurement Agent.
- Records + Inventory Agent.
- Market + Sales Agent.
- Compliance Agent.
- Recommendation Synthesizer.

High-priority route triggers:

```yaml
green_basket_route_triggers:
  market_day_question:
    agents:
      - Weather + Fieldwork Agent
      - Records + Inventory Agent
      - Market + Sales Agent
      - Recommendation Synthesizer

  CSA_box_question:
    agents:
      - Records + Inventory Agent
      - Market + Sales Agent
      - Weather + Fieldwork Agent
      - Recommendation Synthesizer

  organic_input_question:
    agents:
      - Compliance Agent
      - Input Procurement Agent
      - Records + Inventory Agent
      - Recommendation Synthesizer

  packaging_shortage_question:
    agents:
      - Input Procurement Agent
      - Records + Inventory Agent
      - Market + Sales Agent
      - Recommendation Synthesizer
```

---

## 11. Sample Context Packages

These are abbreviated examples of the task-scoped data HarvestAmp should pass to agents.

## 11.1 Prairie View fuel-buying context package

```yaml
context_package:
  farm_id: "PVF_ROW_CROP_001"
  tenant_id: "tenant_pvf_demo"
  user_id: "pvf_owner_001"
  user_role: "farm_owner"
  workflow: "fuel_buy_window"
  task: "Evaluate whether to buy diesel this month"
  allowed_data_classes:
    - public
    - farm_confidential
    - farm_restricted
  excluded_data_classes:
    - credentials_and_secrets
    - unrelated_crop_insurance_documents
    - unrelated_supplier_contracts
  task_scoped_data:
    current_diesel_gallons_estimate: 1350
    diesel_tank_capacity_gallons: 4000
    expected_30_day_diesel_need_gallons: 3100
    preferred_minimum_reserve_gallons: 700
    latest_supplier_quote_id: "PVF_QUOTE_DIESEL_2026_06_21"
    upcoming_operations:
      - spraying
      - wheat_harvest_preparation
      - field_scouting
    human_review_policy:
      approval_required_before:
        - send_supplier_message
        - create_purchase_order
```

## 11.2 Green Basket market-day context package

```yaml
context_package:
  farm_id: "GBO_DIRECT_001"
  tenant_id: "tenant_gbo_demo"
  user_id: "gbo_owner_001"
  user_role: "farm_owner"
  workflow: "farmers_market_plan"
  task: "Prepare Saturday market recommendation"
  allowed_data_classes:
    - public
    - farm_confidential
    - farm_restricted
  excluded_data_classes:
    - credentials_and_secrets
    - certifier_private_notes_unless_shared
    - customer_personal_data_not_needed_for_task
  task_scoped_data:
    market_day: "Saturday"
    market_channel_id: "GBO_CHANNEL_MARKET_001"
    travel_time_minutes: 35
    packaging_inventory:
      pint_clamshells_on_hand: 160
      quart_clamshells_on_hand: 85
      paper_bags_on_hand: 420
      labels_on_hand: 260
    harvest_supply_status:
      ice_bags_reserved_for_market: 8
      tent_weights_status: "needs_check"
      receipt_paper_status: "low"
    active_crop_groups:
      - leafy_greens
      - herbs
      - berries
      - summer_crops
    human_review_policy:
      approval_required_before:
        - send_customer_message
        - post_public_availability
        - send_restaurant_availability
```

---

## 12. Profile-Specific UI Implications

## 12.1 Prairie View dashboard priorities

Prairie View's dashboard should prioritize:

1. Weather and fieldwork windows.
2. Fuel status and buy/watch alerts.
3. Fertilizer and seed quote comparisons.
4. Crop scouting priorities.
5. Grain market watchlist.
6. Stored grain and margin scenario cards.
7. Compliance and deadline reminders.
8. Crew task list.

Suggested top cards:

```text
Today / This Week
Fieldwork Windows
Input Watch
Fuel Tank
Fertilizer Quotes
Crop Scouting
Grain Watchlist
Deadlines
Tasks
```

## 12.2 Green Basket dashboard priorities

Green Basket's dashboard should prioritize:

1. Weekly harvest plan.
2. CSA pack plan.
3. Farmers market prep.
4. Packaging inventory.
5. Organic documentation gaps.
6. Market-day weather.
7. Restaurant availability drafts.
8. Field and high tunnel tasks.

Suggested top cards:

```text
This Week
Harvest Plan
CSA Box
Market Prep
Packaging
Organic Records
Irrigation / Weather
Restaurant Availability
Tasks
```

---

## 13. Profile-Specific Evaluation Criteria

## 13.1 Prairie View evaluation criteria

HarvestAmp should pass evaluation if it can:

- Produce a weekly row-crop action plan using farm-specific data.
- Distinguish between public fuel benchmarks and actual supplier quotes.
- Recommend buy/wait/split fuel actions without overclaiming price forecasts.
- Compare fertilizer quotes while flagging missing delivery/application fees.
- Use cost-per-nutrient logic where enough information exists.
- Flag pesticide and spray-related decisions for label/human review.
- Protect supplier quote confidentiality.
- Avoid exposing restricted data to field employee users.
- Provide market scenarios without executing sales or trading decisions.

## 13.2 Green Basket evaluation criteria

HarvestAmp should pass evaluation if it can:

- Produce a weekly direct-market action plan using farm-specific data.
- Create a market pack-list recommendation that accounts for weather and packaging.
- Draft a CSA box plan and member message requiring approval before sending.
- Flag organic input uncertainty for certifier review.
- Identify packaging shortages before CSA or market commitments.
- Avoid treating fuel buying as the central issue unless the prompt requires it.
- Protect customer, certifier, and supplier data.
- Avoid exposing financial or certification records to unauthorized staff.

---

## 14. Data Gaps to Track During MVP

The following data gaps should be represented in tests because real farms often have incomplete data.

## 14.1 Prairie View data gaps

```yaml
prairie_view_common_gaps:
  - exact_crop_growth_stage
  - current_field_wetness
  - confirmed_product_label
  - current_spray_inventory
  - delivery_fee_on_fertilizer_quote
  - application_fee_on_fertilizer_quote
  - updated_cash_bid
  - exact_storage_cost
  - current_crop_insurance_deadline
  - verified_fuel_tank_reading
```

## 14.2 Green Basket data gaps

```yaml
green_basket_common_gaps:
  - exact_harvestable_quantity_by_crop
  - latest_market_sales_history
  - current_customer_order_changes
  - verified_organic_input_status
  - complete_approved_input_list
  - updated_packaging_count
  - wash_pack_labor_availability
  - exact_weather_impact_on_harvest_quality
  - current_food_safety_log_status
  - restaurant_order_final_quantities
```

HarvestAmp should not hide uncertainty. It should state what is missing and how that affects confidence.

---

## 15. Privacy and Disclosure Examples

## 15.1 Supplier quote disclosure

If Prairie View asks HarvestAmp to draft a message to River County Fuel, HarvestAmp must not include fertilizer quotes, grain inventory, margin targets, or competing fuel supplier prices unless the user explicitly approves that disclosure.

Bad:

```text
Supplier B quoted us $3.59, and we are short on diesel because we have only 1,350 gallons left for 1,850 acres.
```

Better:

```text
Please provide a delivered quote for 2,000 gallons of off-road diesel this week, including any delivery fees and the quote expiration date.
```

## 15.2 Certifier disclosure

If Green Basket asks HarvestAmp to draft a certifier question, HarvestAmp should include only the input and field records relevant to that question.

Bad:

```text
Here is our full sales plan, customer list, cash flow issue, and all supplier invoices.
```

Better:

```text
Can you confirm whether the attached product documentation is acceptable for use on certified organic vegetable fields under our Organic System Plan?
```

## 15.3 Cross-farm isolation

HarvestAmp must never say:

```text
Another farm nearby received a lower fertilizer quote from its co-op.
```

unless that information is public, de-identified, properly aggregated, and allowed by policy.

---

## 16. Recommended Use in Later Documents

## 16.1 `04_DATA_SOURCES.md`

Use these profiles to define required source categories:

- Weather source for fieldwork and market-day planning.
- Fuel benchmark and local supplier quote handling.
- Fertilizer quote extraction.
- Seed and packaging inventory tracking.
- Commodity market and direct-market sales data.
- Organic and compliance document storage.

## 16.2 `05_AGENT_CONTRACTS.md`

Each agent contract should include examples from both profiles.

Example:

```text
Weather Agent must support:
1. Prairie View: spray-window and fieldwork timing.
2. Green Basket: market-day, harvest quality, irrigation, high tunnel humidity.
```

## 16.3 `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

Use the profile-specific human-review defaults as the first policy examples.

## 16.4 `07_SAMPLE_SCENARIOS.md`

Convert the workflows and prompts in this file into detailed scenario scripts.

## 16.5 `08_EVALUATION_TESTS.md`

Turn the evaluation criteria into test cases.

## 16.6 Future Farm Profile Schema and Optional Irrigation Fields

For future schema development and platform expansion, the following optional irrigation fields should be recognized in the farm profile schema and profile field list:
- `irrigation_status`: Indicates whether fields support irrigation (e.g., active, none, inactive).
- `water_source`: The source of water (e.g., district, canal, groundwater, surface water).
- `irrigation_district_or_provider`: The name of the irrigation district or canal provider.
- `portal_connection_status`: Connection status of the water provider's portal.
- `turnout_or_field_delivery_ids`: Identifiers for the gate, turnout, or delivery point.
- `allocation_units`: The units of allocation (e.g., acre-feet, shares, miner's inches).
- `usual_request_lead_time`: Required advance notice for delivery requests (e.g., 24h, 48h).
- `irrigation_method`: The delivery method (e.g., drip, overhead sprinkler, flood).
- `irrigation_record_status`: Status of current irrigation recordkeeping (e.g., complete, missing).

Note: Do not force irrigation onto Prairie View Farms fields (which remain non-irrigated). For Green Basket Organics, preserve existing drip/overhead irrigation context and only add provider/portal fields if clearly marked synthetic/future.

---

## 17. Open Questions

These questions do not block the MVP, but they should be resolved before moving from mock data to real users.

## 17.1 General open questions

1. What is the first buyer persona for HarvestAmp: individual farmer, co-op, crop consultant, ag retailer, or enterprise farm operator?
2. Should the MVP UI support both farm profiles equally, or should the first demo lead with one profile?
3. Should HarvestAmp use one shared dashboard that adapts by farm type, or two separate dashboard templates?
4. What approval thresholds should be configurable by each farm?
5. What is the minimum farm profile needed before HarvestAmp can produce useful recommendations?
6. How will HarvestAmp represent uncertainty and stale data in the UI?
7. Should all generated supplier/customer messages require approval in MVP, even low-risk messages?

## 17.2 Prairie View open questions

1. Which state/region should be used for final demo consistency?
2. Which crop pair should be the first row-crop default: corn/soybeans, wheat, cotton, rice, or another crop system?
3. Should crop disease workflows be included in MVP or deferred until after procurement/weather workflows?
4. Should stored grain and break-even scenarios be included in MVP, or kept as a simple market watchlist?
5. What is the default purchase approval threshold for large row-crop farms?

## 17.3 Green Basket open questions

1. Should Green Basket be certified organic, transitioning organic, or organic-practice but uncertified for the first demo?
2. Should CSA planning or farmers market planning be the lead direct-market workflow?
3. Should customer data be represented in the MVP, or should it stay abstract as counts and commitments?
4. Should HarvestAmp support crop-by-bed planning in MVP, or use crop-group summaries first?
5. What is the default purchase approval threshold for small direct-market farms?

---

## 18. Current Profile Decision

For MVP planning, HarvestAmp should proceed with these two test profiles:

1. `PVF_ROW_CROP_001` - Prairie View Farms, large conventional row-crop operation.
2. `GBO_DIRECT_001` - Green Basket Organics, small certified organic direct-market farm.

These profiles should remain the default test farms until intentionally revised.

The next recommended document is:

```text
04_DATA_SOURCES.md
```

That document should define what data HarvestAmp needs, which data can be mocked for MVP, which data should come from public APIs, which data should come from user entry or uploads, and which data should later come from supplier or farm-management integrations.
