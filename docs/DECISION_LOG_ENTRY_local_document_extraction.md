## D-LOCAL-DOC-001: Local uploaded document extraction remains draft until review

Status: proposed for acceptance
Date: 2026-06-25
Owner: Product / architecture owner
Related docs: `04_DATA_SOURCES.md`, `05_AGENT_CONTRACTS.md`, `06_RISK_AND_HUMAN_REVIEW_POLICY.md`

### Context

Farm-specific invoices and supplier quotes are more actionable than public benchmarks, but they can contain commercially sensitive pricing, payment details, and ambiguous fields.

### Decision

HarvestAmp will initially parse local files and synthetic fixtures only. Extracted fields are source-labeled and Farm Restricted, but they remain draft pending review. Official record updates, supplier selection, external messages, and purchases require explicit approval.

### Consequences

The first document extraction milestone improves farm-specific usefulness without introducing Drive, Gmail, supplier portals, OAuth, payment handling, or automatic record mutation.
