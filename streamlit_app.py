"""HarvestAmp local pilot Streamlit UI.

Integrates weekly plan, scenario runner, document review, and safety approval gates
using existing Supervisor, ToolGateway, and agent helpers.
"""

import os
import yaml
import json
import streamlit as st
from typing import Any, Dict, List, Optional

from harvestamp.workflows.supervisor import Supervisor
from harvestamp.audit.logger import AuditLogger

# ---------------------------------------------------------------------------
# Core YAML and Fixture Helpers
# ---------------------------------------------------------------------------

def load_yaml(path: str) -> Any:
    """Helper to load a YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fixture path not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_farm_profile(farm_key: str) -> Dict[str, Any]:
    """Load the farm profile YAML based on a farm key."""
    filename = "prairie_view_farms.yaml" if "PVF" in farm_key else "green_basket_organics.yaml"
    path = os.path.join("fixtures", "farms", filename)
    return load_yaml(path)


def load_observations() -> Dict[str, Any]:
    """Load the observations YAML fixture."""
    path = os.path.join("fixtures", "data_observations.yaml")
    return load_yaml(path)


def load_scenarios() -> List[Dict[str, Any]]:
    """Load the scenarios YAML fixture."""
    path = os.path.join("fixtures", "scenarios.yaml")
    return load_yaml(path)


def get_supervisor() -> Supervisor:
    """Instantiate the Supervisor with the AuditLogger."""
    logger = AuditLogger()
    return Supervisor(audit_logger=logger)


# ---------------------------------------------------------------------------
# Workflow Execution Wrappers
# ---------------------------------------------------------------------------

def run_weekly_plan_for_ui(farm_key: str, role: str) -> Dict[str, Any]:
    """Run the weekly plan workflow."""
    farm_profile = load_farm_profile(farm_key)
    observations = load_observations()
    supervisor = get_supervisor()

    user_id = "user_001"
    for user in farm_profile.get("users", []):
        if user.get("role") == role:
            user_id = user.get("user_id")
            break

    prompt = f"What should I know about {farm_profile['farm_name']} this week?"

    action_pack = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id=user_id,
        user_role=role,
        prompt=prompt,
        observations=observations,
    )
    return action_pack


def run_scenario_for_ui(scenario_id: str) -> Dict[str, Any]:
    """Run a scenario by ID, applying special scenario runner rules."""
    scenarios = load_scenarios()
    scenario = next((s for s in scenarios if s.get("scenario_id") == scenario_id), None)
    if not scenario:
        raise ValueError(f"Scenario ID {scenario_id} not found.")

    farm_profile = load_farm_profile(scenario["farm_profile"])
    observations = load_observations()

    target_farm_id = None
    if scenario_id == "SYS-002":
        target_farm_id = "GBO_DIRECT_001"

    prompt_str = scenario["prompt"]
    if scenario_id == "SYS-005":
        prompt_str = scenario["prompt"] + " (stale-trigger)"
    elif scenario_id == "IPM-004":
        observations["crop_health_mock_status"] = "unavailable"

    supervisor = get_supervisor()
    action_pack = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id=scenario.get("user_id", "user_001"),
        user_role=scenario["user_role"],
        prompt=prompt_str,
        observations=observations,
        target_farm_id=target_farm_id,
    )
    return action_pack


def run_document_review_for_ui(farm_key: str, role: str, prompt: str) -> Dict[str, Any]:
    """Run the explicit document review workflow."""
    farm_profile = load_farm_profile(farm_key)
    observations = load_observations()
    supervisor = get_supervisor()

    user_id = "user_001"
    for user in farm_profile.get("users", []):
        if user.get("role") == role:
            user_id = user.get("user_id")
            break

    action_pack = supervisor.run_workflow(
        farm_profile=farm_profile,
        user_id=user_id,
        user_role=role,
        prompt=prompt,
        observations=observations,
    )
    return action_pack


# ---------------------------------------------------------------------------
# UI Rendering Helpers
# ---------------------------------------------------------------------------

def render_recommendations(action_pack: Dict[str, Any]):
    """Renders recommendations cards."""
    st.subheader("Recommendations")
    recs = action_pack.get("recommendations", [])
    if not recs:
        st.write("No recommendations generated.")
        return

    for rec in recs:
        # Style based on urgency
        urgency = rec.get("urgency", "info").lower()
        title_prefix = {
            "high": "🔴 Urgent",
            "medium": "🟡 Important",
            "low": "⚪ Notice",
        }.get(urgency, "🔵 Info")

        with st.container():
            st.markdown(f"### {title_prefix}: {rec.get('title')}")
            st.markdown(f"**Summary**: {rec.get('summary')}")
            st.markdown(f"**Recommendation**: {rec.get('recommendation')}")
            
            # Display human review policy
            hr = rec.get("human_review_status", {})
            if hr.get("required"):
                st.info(f"**Review Required**: {hr.get('review_type')} | Status: {hr.get('status')} | Reason: {', '.join(hr.get('reason', []))}")
            else:
                st.success("Auto-approve (Review not required)")
            
            st.divider()


def render_proposed_actions(action_pack: Dict[str, Any]):
    """Renders proposed draft actions."""
    st.subheader("Proposed Actions (Drafts only)")
    actions = action_pack.get("proposed_actions", [])
    if not actions:
        st.write("No proposed actions.")
        return

    for act in actions:
        with st.expander(f"Draft Action: {act.get('action_type')} ({act.get('action_id')})"):
            st.markdown(f"**Action Type**: {act.get('action_type')}")
            st.markdown(f"**Payload Details**:")
            st.write(act.get("payload", {}))
            
            hr = act.get("human_review_status", {})
            if hr:
                st.info(f"**Review Status**: {hr.get('status')} | Reason: {', '.join(hr.get('reason', []))}")


def render_evidence(action_pack: Dict[str, Any]):
    """Renders the evidence summary table."""
    st.subheader("Evidence Summary")
    evidence = action_pack.get("evidence_summary", [])
    if not evidence:
        st.write("No evidence associated with this run.")
        return

    import pandas as pd
    rows = []
    for ev in evidence:
        rows.append({
            "Evidence ID": ev.get("evidence_id"),
            "Source": ev.get("source_name"),
            "Trust Tier": ev.get("trust_tier"),
            "Freshness": ev.get("freshness_status"),
            "Privacy Class": ev.get("privacy_class"),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)


def render_warnings_and_missing_data(action_pack: Dict[str, Any]):
    """Renders warnings and missing data sections."""
    warnings = action_pack.get("warnings", [])
    missing = action_pack.get("missing_data", [])

    if warnings:
        st.subheader("⚠️ Warnings")
        for w in warnings:
            st.warning(w)

    if missing:
        st.subheader("❌ Missing Data Needed")
        for m in missing:
            st.error(f"Missing context: {m}")


def render_action_pack(action_pack: Dict[str, Any]):
    """Orchestrates rendering the entire ActionPack."""
    st.success(f"Action Pack Generated: {action_pack.get('action_pack_id')} | Status: {action_pack.get('status', '').upper()}")
    
    render_warnings_and_missing_data(action_pack)
    render_recommendations(action_pack)
    render_proposed_actions(action_pack)
    render_evidence(action_pack)

    st.subheader("Raw Output JSON")
    st.json(action_pack)


# ---------------------------------------------------------------------------
# Streamlit App Navigation and Pages
# ---------------------------------------------------------------------------

def main():
    st.sidebar.title("HarvestAmp Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Home", "Weekly Plan", "Role Safety Comparison", "Scenario Runner", "Document Review", "Safety / Approval Gate"]
    )

    if page == "Home":
        st.title("🌾 HarvestAmp Local Pilot Demo")
        st.markdown("A supervised multi-agent farm operations assistant using local/synthetic farm data.")
        
        st.error("🔒 **Local demo only**: No emails, purchases, payments, external messages, or official record changes are executed.")

        st.markdown("### Included Workflows")
        st.markdown("""
        - **Weekly Plans**: Generates custom operations plans based on farm profile and role.
        - **Role-Safe Outputs**: Automatically redacts sensitive fields (prices, customer emails, margins) for field employees.
        - **Scenario Workflows**: Demonstrates targeted operations (diesel reorder, spray windows, organic compliance).
        - **Document Review**: Scans and surfaces local extracted documents cleanly as read-only context.
        - **Draft-only Action Gating**: Proves that every external action remains a draft pending human verification.
        """)

    elif page == "Weekly Plan":
        st.title("📅 Weekly Plan Generator")
        st.write("Generate a custom weekly operations dashboard combining weather, input lists, compliance, and stored grain indicators.")

        col1, col2 = st.columns(2)
        with col1:
            farm = st.selectbox("Farm Profile", ["PVF_ROW_CROP_001", "GBO_DIRECT_001"], format_func=lambda x: "Prairie View Farms" if x == "PVF_ROW_CROP_001" else "Green Basket Organics")
        with col2:
            role = st.selectbox("User Role", ["farm_owner", "farm_manager", "field_employee"])

        if st.button("Run Weekly Plan", type="primary"):
            with st.spinner("Executing supervisor weekly coordination..."):
                action_pack = run_weekly_plan_for_ui(farm, role)
                render_action_pack(action_pack)

    elif page == "Role Safety Comparison":
        st.title("🛡️ Role Safety & Privacy Comparison")
        st.write("Compare the output of the same Weekly Plan prompt side-by-side between the Farm Owner and the Field Employee role.")

        farm = st.selectbox("Farm Profile", ["PVF_ROW_CROP_001", "GBO_DIRECT_001"], format_func=lambda x: "Prairie View Farms" if x == "PVF_ROW_CROP_001" else "Green Basket Organics")

        st.info("Field employee output should hide supplier pricing, customer/payment details, restricted evidence, and draft external actions.")

        if st.button("Compare Owner vs Field Employee", type="primary"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👑 Farm Owner View")
                with st.spinner("Running owner plan..."):
                    owner_pack = run_weekly_plan_for_ui(farm, "farm_owner")
                    render_action_pack(owner_pack)
            
            with col2:
                st.subheader("🚜 Field Employee View")
                with st.spinner("Running employee plan..."):
                    employee_pack = run_weekly_plan_for_ui(farm, "field_employee")
                    render_action_pack(employee_pack)

    elif page == "Scenario Runner":
        st.title("🚀 Scenario Sandbox Runner")
        st.write("Select and run any validated MVP scenarios from the fixture registry.")

        scenarios = load_scenarios()
        options = [s["scenario_id"] for s in scenarios]
        
        # Ensure targeted options are listed clearly or sorted
        selected_id = st.selectbox("Select Scenario", options, format_func=lambda x: next(f"{s['scenario_id']} - {s['name']}" for s in scenarios if s['scenario_id'] == x))

        scenario = next(s for s in scenarios if s["scenario_id"] == selected_id)
        
        with st.expander("Scenario Details", expanded=True):
            st.markdown(f"**Scenario ID**: {scenario.get('scenario_id')}")
            st.markdown(f"**Name**: {scenario.get('name')}")
            st.markdown(f"**Farm**: {scenario.get('farm_profile')}")
            st.markdown(f"**Role**: {scenario.get('user_role')}")
            st.markdown(f"**Prompt**: {scenario.get('prompt')}")
            st.markdown(f"**Expected Agents**: {', '.join(scenario.get('expected_agents', []))}")

        if st.button("Run Scenario", type="primary"):
            with st.spinner("Simulating scenario..."):
                action_pack = run_scenario_for_ui(selected_id)
                render_action_pack(action_pack)

    elif page == "Document Review":
        st.title("📄 Explicit Document Review")
        st.write("Explicitly request the Supervisor to parse and surface local extracted documents.")

        col1, col2 = st.columns(2)
        with col1:
            farm = st.selectbox("Farm Profile", ["PVF_ROW_CROP_001", "GBO_DIRECT_001"], format_func=lambda x: "Prairie View Farms" if x == "PVF_ROW_CROP_001" else "Green Basket Organics")
            role = st.selectbox("Simulated Role", ["farm_owner", "farm_manager", "field_employee"])
        with col2:
            prompt = st.selectbox(
                "Document Review Prompt",
                [
                    "Review my local extracted documents.",
                    "Review the supplier quote.",
                    "Review the supplier invoice.",
                    "Review the fuel receipt.",
                    "Review the packaging receipt.",
                    "Review the harvest load ticket.",
                    "Review the inventory count sheet.",
                    "What is missing from the extracted document?"
                ]
            )

        if st.button("Review Documents", type="primary"):
            with st.spinner("Analyzing document context..."):
                action_pack = run_document_review_for_ui(farm, role, prompt)
                render_action_pack(action_pack)

    elif page == "Safety / Approval Gate":
        st.title("🎛️ Safety / Approval Gate Policy")
        
        st.warning("⚠️ **Safety Principle**: HarvestAmp coordinates draft-only actions. No automated system can directly execute changes without explicit approval.")

        st.markdown("### Safety System Design")
        st.markdown("""
        - **Draft-only Actions**: The multi-agent system creates proposed actions (e.g. `supplier_message`, `share_with_certifier`, `submit_irrigation_request`) but marks them as `blocked_pending_user_approval` or `needs_user_approval`.
        - **Auth Role Boundary**: Restricted roles like `field_employee` cannot view or approve draft procurement or financial updates.
        - **Execution Blocked**: The MVP has no actual connectors to emails, banks, POS systems, or official certifiers. All external calls are gated and simulated.
        """)

        st.info("No backend changes are made in the local pilot. All actions remain as ActionPack draft payloads for audit review.")


if __name__ == "__main__":
    main()
