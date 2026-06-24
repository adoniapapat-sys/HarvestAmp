# HarvestAmp

HarvestAmp is a Google AI / Google Cloud agriculture agent MVP designed to help conventional row-crop operations and organic direct-market farms optimize operations and protect margins.

## Overview

HarvestAmp is designed with a multi-agent hub-and-spoke architecture. It uses a Supervisor agent to coordinate specialist agents (Weather, Procurement, Records, Market, Compliance, Margin, Synthesizer, Action) while enforcing strict privacy, credential safety, and human-review policy boundaries.

## Directory Structure

```text
harvestamp-mvp/
├── README.md                      # Product overview and developer instructions
├── ANTIGRAVITY_TASKS.md           # Developer task list and progress tracking
├── docs/                          # Source-of-truth MVP documentation
│   ├── 01_PRODUCT_BRIEF.md
│   ├── 02_AGENT_ARCHITECTURE.md
│   ├── 03_FARM_PROFILES.md
│   ├── 04_DATA_SOURCES.md
│   ├── 05_AGENT_CONTRACTS.md
│   ├── 06_RISK_AND_HUMAN_REVIEW_POLICY.md
│   ├── 07_SAMPLE_SCENARIOS.md
│   ├── 08_EVALUATION_TESTS.md
│   ├── 09_MVP_SCOPE.md
│   ├── 10_BUILD_PLAN.md
│   ├── DECISION_LOG.md
│   └── CHANGELOG.md
├── configs/                       # Configuration files
│   └── human_review_rules.yaml    # Machine-readable human review policy rules
├── schemas/                       # YAML schemas defining agent and data contracts
│   ├── common_defs.schema.yaml
│   ├── work_item.schema.yaml
│   ├── farm_context_package.schema.yaml
│   ├── agent_finding.schema.yaml
│   ├── evidence_item.schema.yaml
│   ├── human_review.schema.yaml
│   ├── action_pack.schema.yaml
│   ├── audit_event.schema.yaml
│   ├── source_metadata.schema.yaml
│   ├── connector_result.schema.yaml
│   ├── recommendation.schema.yaml
│   ├── farm_profile.schema.yaml
│   ├── quote.schema.yaml
│   ├── inventory_item.schema.yaml
│   └── scenario.schema.yaml
├── fixtures/                      # Synthetic data fixtures representing farm states
│   ├── farms/
│   │   ├── prairie_view_farms.yaml
│   │   └── green_basket_organics.yaml
│   ├── source_metadata.yaml
│   ├── data_observations.yaml
│   └── scenarios.yaml
├── harvestamp/                    # Core Python modules
│   ├── core/                      # Shared helpers (math, schema validation, Evidence Board)
│   ├── auth/                      # Role checks and Credential Broker
│   ├── gateway/                   # Tool Gateway stub
│   ├── context/                   # Context Package Builder
│   ├── policy/                    # Human Review and Action Gate policies
│   ├── agents/                    # Specialist agent stubs
│   ├── workflows/                 # Supervisor coordination logic
│   ├── tools/                     # System tools and connectors
│   └── audit/                     # Deterministic audit logging
├── scripts/                       # Local execution and runner scripts
│   ├── run_scenario.py            # Local mock scenario runner
│   ├── run_weekly_plan.py         # Weekly farm plan runner
│   └── validate_fixtures.py       # Fixture validation script
└── tests/                         # Pytest test suite
    ├── test_schemas.py
    ├── test_auth.py
    ├── test_freshness.py
    ├── test_human_review.py
    ├── test_math_utils.py
    ├── test_context_minimization.py
    ├── test_routing.py
    ├── test_action_gate.py
    ├── test_scenarios.py
    ├── test_brand_consistency.py
    └── test_source_metadata.py
```

## Running Scenarios

The `run_scenario.py` script allows executing a specific synthetic mock scenario by its ID:

```bash
python scripts/run_scenario.py PVF-001
```

To run a weekly plan directly:

```bash
python scripts/run_weekly_plan.py --farm PVF_ROW_CROP_001 --role farm_owner
```

## Running Tests

To run the automated test suite, execute the following from the root directory:

```bash
python -m pytest tests/
```

To validate all fixtures:

```bash
python scripts/validate_fixtures.py
```

## Constraints and Safety Policies

1. **Only HarvestAmp Name**: The product name "HarvestAmp" is used exclusively throughout the repository, tests, and outputs.
2. **Strict Identity Isolation**: Access control is enforced at the farm boundary (no cross-tenant leakage).
3. **Task-Scoped Minimization**: LLM agents are provided with task-scoped data context only.
4. **No Raw Credentials**: Raw passwords or API tokens are managed via the Credential Broker and Tool Gateway, never exposed directly.
5. **Human Approval Gates**: Any external action (sending emails, placing orders, updating official records) must go through the deterministic approval gating layer.
