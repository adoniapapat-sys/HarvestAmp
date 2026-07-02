"""HarvestAmp local pilot Streamlit UI.

A polished, farmer-facing product demo interface wrapping HarvestAmp workflows.
Uses custom styled CSS, cards, badges, and layout structures for a premium SaaS feel.
"""

import os
import yaml
import json
import tempfile
import textwrap
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional

from harvestamp.workflows.supervisor import Supervisor
from harvestamp.audit.logger import AuditLogger

# ---------------------------------------------------------------------------
# UI Helpers & Custom Styling
# ---------------------------------------------------------------------------

def render_html(markup: str):
    """Safely render HTML markup by stripping leading whitespace from each line to prevent code block parsing."""
    cleaned = "\n".join(line.lstrip() for line in markup.splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)



def inject_custom_css():
    """Inject custom CSS to establish a premium, trustworthy SaaS visual palette."""
    render_html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Literata:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Work+Sans:wght@400;500;600;700&family=Courier+Prime&display=swap');
    
    /* Color Palette & Base App Styling */
    .stApp {
        background-color: #fbf9f4; /* Warm off-white background matching Stitch */
        color: #1b1c19; /* Charcoal on-surface text */
        font-family: 'Work Sans', sans-serif;
    }
    
    /* Headers and titles */
    h1, h2, h3, h4, h5, .serif-heading {
        color: #334537 !important; /* Deep Green primary accents */
        font-family: 'Literata', serif !important;
        font-weight: 600;
    }
    
    /* Dark Hero Banner */
    .dark-hero-bg {
        background: linear-gradient(135deg, #334537 0%, #1a251e 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 4px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(51, 69, 55, 0.15);
        border: 1px solid #334537;
    }
    .dark-hero-bg h1, .dark-hero-bg h2, .dark-hero-bg h3, .dark-hero-bg h4, .dark-hero-bg p {
        color: white !important;
    }

    /* Light Hero Banner */
    .light-hero-bg {
        background: linear-gradient(135deg, #f5efe6 0%, #e8dec9 100%);
        color: #1b1c19;
        padding: 2.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(51, 69, 55, 0.05);
        border: 1px solid #e4e2dd;
        text-align: center;
    }
    .light-hero-bg h1, .light-hero-bg h2, .light-hero-bg h3, .light-hero-bg h4, .light-hero-bg p {
        color: #334537 !important;
    }

    /* Style for local farm stock image */
    [data-testid="stImage"] img {
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border: 1px solid #e4e2dd;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f0eee9 !important; /* Surface container */
        border-right: 1px solid #c3c8c1;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #334537 !important;
    }

    /* Buttons custom style */
    div.stButton > button:first-child {
        background-color: #334537 !important;
        color: #ffffff !important;
        border-radius: 9999px !important;
        border: 1px solid #334537 !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.25rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-color: #cca830 !important; /* Gold hover */
        border-color: #cca830 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar button overrides */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent !important;
        color: #1b1c19 !important;
        border: 1px solid transparent !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        margin-bottom: 0.25rem !important;
        border-radius: 4px !important;
    }

    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #e4e2dd !important;
        color: #334537 !important;
    }

    /* Active sidebar button override (when type="primary") */
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #334537 !important;
        color: #ffffff !important;
        border-color: #334537 !important;
        font-weight: 600 !important;
    }

    /* Card Section containers */
    .custom-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 4px;
        border: 1px solid #c3c8c1;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        height: 100%;
    }
    
    /* Collage capability tiles */
    .collage-tile {
        background-color: #ffffff;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        border-left: 4px solid #334537;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        color: #1b1c19 !important;
        margin-bottom: 0.75rem;
    }
    .collage-tile-gold {
        background-color: #ffffff;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        border-left: 4px solid #cca830;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        color: #1b1c19 !important;
        margin-bottom: 0.75rem;
    }
    .collage-tile strong, .collage-tile-gold strong {
        color: #1b1c19 !important;
        font-size: 0.85rem;
    }
    
    /* Custom Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.4rem;
        font-size: 0.65rem;
        font-weight: 700;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-right: 0.5rem;
    }
    .badge-live {
        background-color: #e2e2e5;
        color: #334537;
        border: 1px solid #c3c8c1;
    }
    .badge-partial {
        background-color: #ffe088;
        color: #735c00;
        border: 1px solid #e9c349;
    }
    .badge-preview {
        background-color: #d3e8d5;
        color: #334537;
        border: 1px solid #b7ccb9;
    }
    .badge-soon {
        background-color: #eae8e3;
        color: #737872;
        border: 1px solid #c3c8c1;
    }
    .badge-urgent {
        background-color: #ffd9d9;
        color: #ba1a1a;
        border: 1px solid #ffb4ab;
    }
    .badge-important {
        background-color: #ffe088;
        color: #735c00;
        border: 1px solid #e9c349;
    }
    .badge-notice {
        background-color: #e8f5e9;
        color: #2e7d32;
        border: 1px solid #a5d6a7;
    }
    .badge-info {
        background-color: #d3e8d5;
        color: #334537;
        border: 1px solid #b7ccb9;
    }
    </style>
    """)


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


def run_scenario_for_ui(scenario_id: str, role_override: Optional[str] = None) -> Dict[str, Any]:
    """Run a scenario by ID, applying special scenario runner rules.

    Args:
        scenario_id: The scenario fixture ID to run.
        role_override: If provided, overrides the scenario-defined user role
            and resolves a matching user_id from the farm profile.
    """
    scenarios = load_scenarios()
    scenario = next((s for s in scenarios if s.get("scenario_id") == scenario_id), None)
    if not scenario:
        raise ValueError(f"Scenario ID {scenario_id} not found.")

    farm_profile = load_farm_profile(scenario["farm_profile"])
    observations = load_observations()

    # Determine effective role: override or scenario-defined
    effective_role = role_override if role_override else scenario["user_role"]

    # Resolve user_id for the effective role
    user_id = scenario.get("user_id", "user_001")
    if role_override:
        for user in farm_profile.get("users", []):
            if user.get("role") == role_override:
                user_id = user.get("user_id")
                break

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
        user_id=user_id,
        user_role=effective_role,
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

def _text_to_bullets(text: str, max_bullets: int = 6) -> List[str]:
    """Break a long backend paragraph into readable bullet points.

    The backend often concatenates related statements with '. ' or ' - '.
    We split on those separators, keep the sentences readable, and cap the count.
    """
    if not text:
        return []
    # Normalize the two common separators into a single split token
    normalized = text.replace(" - ", ". ").replace("—", ". ")
    parts = [p.strip(" .") for p in normalized.split(". ") if p.strip(" .")]
    # De-duplicate while preserving order, and drop tiny fragments
    seen = set()
    out = []
    for p in parts:
        if len(p) < 8:
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p + ("." if not p.endswith((".", "!", "?", ")")) else ""))
        if len(out) >= max_bullets:
            break
    return out


def _first_sentence(text: str, max_chars: int = 140) -> str:
    """Extract a short 1-line summary from a longer paragraph."""
    if not text:
        return ""
    for sep in [". ", " - ", "—"]:
        if sep in text:
            first = text.split(sep, 1)[0].strip(" .")
            if 20 <= len(first) <= max_chars:
                return first + "."
    return (text[:max_chars].rstrip() + "…") if len(text) > max_chars else text


# ---------------------------------------------------------------------------
# Focused Report Helpers
# ---------------------------------------------------------------------------

FOCUS_KEYWORDS: Dict[str, List[str]] = {
    "diesel": ["diesel", "fuel", "tank", "eia", "gallon", "purchase", "supplier quote"],
    "spray_guardrail": ["spray", "pesticide", "wind", "label", "applicator", "guardrail", "weather"],
    "harvest_grain": ["harvest", "grain", "load ticket", "bin", "yield", "settlement"],
    "packaging": ["packaging", "clamshell", "csa box", "label", "bag", "pack"],
    "organic_input": ["organic", "certifier", "input", "documentation", "omri", "compliance"],
    "market_csa": ["market", "csa", "restaurant", "delivery", "packout", "customer"],
    "document": ["document", "quote", "invoice", "receipt", "load ticket", "count sheet", "extracted"],
    "weekly": [],
}


def _stringify_for_match(value: Any) -> str:
    """Convert nested ActionPack fragments into searchable lower-case text."""
    if value is None:
        return ""
    try:
        return json.dumps(value, sort_keys=True, default=str).lower()
    except TypeError:
        return str(value).lower()


def _matches_focus(value: Any, focus: Optional[str]) -> bool:
    """Return True if a recommendation/action/evidence item matches the focus keywords."""
    if not focus or focus == "weekly":
        return True
    keywords = FOCUS_KEYWORDS.get(focus, [])
    if not keywords:
        return True
    haystack = _stringify_for_match(value)
    return any(keyword.lower() in haystack for keyword in keywords)


def _filter_by_focus(items: List[Dict[str, Any]], focus: Optional[str]) -> List[Dict[str, Any]]:
    """Filter ActionPack lists by focus keywords, with safe fallbacks."""
    if not items:
        return []
    if not focus or focus == "weekly":
        return items
    filtered = [item for item in items if _matches_focus(item, focus)]
    return filtered


def _evidence_ids_from(items: List[Dict[str, Any]]) -> set:
    """Collect evidence IDs from recommendations/actions when available."""
    ids = set()
    for item in items:
        for key in ("evidence_ids", "related_evidence"):
            val = item.get(key)
            if isinstance(val, list):
                ids.update(str(v) for v in val)
            elif isinstance(val, str):
                ids.add(val)
        payload = item.get("payload", {})
        if isinstance(payload, dict):
            for key in ("source_evidence_id", "evidence_id"):
                if payload.get(key):
                    ids.add(str(payload[key]))
            related = payload.get("related_evidence")
            if isinstance(related, list):
                ids.update(str(v) for v in related)
    return ids


def _filter_evidence_for_focus(
    evidence: List[Dict[str, Any]],
    focus: Optional[str],
    matched_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Show evidence most relevant to the focused report, with useful fallback behavior."""
    if not evidence:
        return []
    if not focus or focus == "weekly":
        return evidence

    matched_ids = _evidence_ids_from(matched_items)
    if matched_ids:
        by_id = [ev for ev in evidence if str(ev.get("evidence_id")) in matched_ids]
        if by_id:
            return by_id

    by_keyword = [ev for ev in evidence if _matches_focus(ev, focus)]
    return by_keyword if by_keyword else evidence[:8]


def set_report(action_pack: Dict[str, Any], focus: Optional[str] = None, title: Optional[str] = None):
    """Store the latest report and route to the report page."""
    st.session_state.last_action_pack = action_pack
    st.session_state.report_focus = focus
    st.session_state.report_title = title
    st.session_state.current_page = "view_report"
    st.rerun()


def render_focused_action_report(action_pack: Dict[str, Any], focus: str, title: Optional[str] = None):
    all_recs = action_pack.get("recommendations", []) or []
    all_actions = action_pack.get("proposed_actions", []) or []
    all_missing = action_pack.get("missing_data", []) or []
    all_warnings = action_pack.get("warnings", []) or []
    all_evidence = action_pack.get("evidence_summary", []) or []

    recs = _filter_by_focus(all_recs, focus)
    actions = _filter_by_focus(all_actions, focus)
    evidence = _filter_evidence_for_focus(all_evidence, focus, recs + actions)

    if not recs and not actions:
        st.info("No focused items matched this report category. Showing the full ActionPack instead.")
        render_farm_action_report(action_pack, title=title)
        return

    status = str(action_pack.get("status", "draft")).upper()
    report_title = title or "Focused Farm Action Report"
    farm_name = "Prairie View Farms" if st.session_state.selected_farm == "PVF_ROW_CROP_001" else "Green Basket Organics"

    render_html(f"""
    <div style="background-color: #334537; color: white; padding: 1.25rem 1.5rem; border-radius: 4px; margin-bottom: 1.5rem; border-left: 5px solid #cca830;">
        <h2 class="serif-heading" style="color: white !important; margin: 0; font-size: 1.45rem; font-weight: 600;">[Report] {report_title}</h2>
        <p style="margin: 0.4rem 0 0 0; font-size: 0.9rem; opacity: 0.95;">
            Farm Workspace: <strong>{farm_name}</strong> | Status: <strong style="color: #cca830;">{status}</strong>
        </p>
        <div style="display: flex; gap: 1.2rem; margin-top: 0.75rem; flex-wrap: wrap; font-size: 0.85rem;">
            <div><strong>{len(recs)}</strong> Focused Findings</div>
            <div><strong>{len(actions)}</strong> Draft Actions</div>
            <div><strong>{len(all_missing)}</strong> Missing Items</div>
            <div><strong>{len(evidence)}</strong> Evidence Sources</div>
        </div>
    </div>
    """)

    st.markdown("<h3 class='serif-heading' style='color:#334537; margin-bottom:0.5rem;'>What HarvestAmp Found</h3>", unsafe_allow_html=True)
    for rec in recs:
        title_txt = rec.get("title", "Finding")
        urgency = str(rec.get("urgency", "info")).lower()
        badge = {
            "high": "Urgent",
            "medium": "Important",
            "low": "Notice",
        }.get(urgency, "Info")
        badge_cls = {
            "high": "badge-urgent",
            "medium": "badge-important",
            "low": "badge-notice",
        }.get(urgency, "badge-info")
        with st.expander(f"{badge.upper()} — {title_txt}", expanded=True):
            if rec.get("summary"):
                st.markdown(f"**At a glance:** {_first_sentence(rec.get('summary', ''))}")
                details = _text_to_bullets(rec.get("summary", ""), max_bullets=6)
                if details:
                    st.markdown("**Details:**")
                    for detail in details:
                        st.markdown(f"- {detail}")
            if rec.get("recommendation"):
                st.markdown("**Recommended review path:**")
                for step in _text_to_bullets(rec.get("recommendation", ""), max_bullets=6):
                    st.markdown(f"- {step}")
            hr = rec.get("human_review_status", {}) or {}
            if hr.get("required"):
                st.caption(
                    f"Review required: {hr.get('status', 'needs_review')} | "
                    f"Reviewer: {', '.join(hr.get('recommended_reviewer', []) or ['—'])}"
                )

    if all_missing:
        st.markdown("<h3 class='serif-heading' style='color:#334537; margin:1rem 0 0.5rem 0;'>Needed before action</h3>", unsafe_allow_html=True)
        with st.expander(f"Show Missing Information — {len(all_missing)} item(s)", expanded=False):
            for item in all_missing:
                st.markdown(f"- {item}")

    if all_warnings:
        st.markdown("<h3 class='serif-heading' style='color:#334537; margin:1rem 0 0.5rem 0;'>Caution Alerts</h3>", unsafe_allow_html=True)
        with st.expander(f"Show Warnings — {len(all_warnings)} item(s)", expanded=False):
            for warning in all_warnings:
                st.markdown(f"- {warning}")

    st.markdown("<h3 class='serif-heading' style='color:#334537; margin:1rem 0 0.5rem 0;'>Draft-Only Next Steps</h3>", unsafe_allow_html=True)
    if not actions:
        st.info("No focused draft actions were staged for this review.")
    else:
        st.caption("These remain draft/review items. Nothing has been executed.")
        for action in actions:
            with st.expander(f"Draft: {action.get('action_type', 'action')}", expanded=False):
                st.markdown(f"**Status:** {action.get('status', 'draft')}")
                st.markdown(f"**Action ID:** `{action.get('action_id', '—')}`")
                hr = action.get("human_review_status", {}) or {}
                if hr:
                    st.markdown(f"**Review status:** {hr.get('status', 'review_not_required')}")
                with st.expander("Technical draft details", expanded=False):
                    st.write(action.get("payload", {}))

    st.markdown("<h3 class='serif-heading' style='color:#334537; margin:1rem 0 0.5rem 0;'>Evidence Used</h3>", unsafe_allow_html=True)
    if evidence:
        rows = [
            {
                "Evidence ID": ev.get("evidence_id"),
                "Source": ev.get("source_name"),
                "Trust": ev.get("trust_tier"),
                "Freshness": ev.get("freshness_status"),
                "Privacy": ev.get("privacy_class"),
            }
            for ev in evidence
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No focused evidence records were linked to this report.")

    st.markdown("---")
    with st.expander("Technical full ActionPack", expanded=False):
        st.json(action_pack)

def render_farm_action_report(action_pack: Dict[str, Any], title: Optional[str] = None):
    """Renders a farmer-facing report: collapsed by default, with bullet-ified details."""
    recs = action_pack.get("recommendations", [])
    actions = action_pack.get("proposed_actions", [])
    missing = action_pack.get("missing_data", [])
    warnings = action_pack.get("warnings", [])
    evidence = action_pack.get("evidence_summary", [])
    status = action_pack.get("status", "unknown").upper()

    # Unique key prefix so multiple reports on the same page (Owner vs Crew) don't collide
    key_prefix = title.replace(" ", "_") if title else "report"

    # Resolve farm name
    farm_name = "Prairie View Farms" if st.session_state.selected_farm == "PVF_ROW_CROP_001" else "Green Basket Organics"

    # A. Report Header Banner
    render_html(f"""
    <div style="background-color: #334537; color: white; padding: 1.25rem 1.5rem; border-radius: 4px; margin-bottom: 1.5rem; border-left: 5px solid #cca830;">
        <h2 class="serif-heading" style="color: white !important; margin: 0; font-size: 1.5rem; font-weight: 600;">[Report] {title or 'Weekly Farm Action Report'}</h2>
        <p style="margin: 0.4rem 0 0 0; font-size: 0.9rem; opacity: 0.95;">
            Farm Workspace: <strong>{farm_name}</strong> | Execution Status: <strong style="color: #cca830;">{status}</strong>
        </p>
        <div style="display: flex; gap: 1.5rem; margin-top: 0.75rem; flex-wrap: wrap; font-size: 0.85rem;">
            <div><strong>{len(recs)}</strong> Recommendations</div>
            <div><strong>{len(actions)}</strong> Draft Actions</div>
            <div><strong>{len(missing)}</strong> Gaps Identified</div>
            <div><strong>{len(warnings)}</strong> Alerts</div>
        </div>
    </div>
    """)

    # B. Key Recommendations — each recommendation is a COLLAPSED expander
    st.subheader("Key Recommendations")
    if not recs:
        st.info("No active recommendations for this period.")
    else:
        st.caption("Click any recommendation to expand full details.")
        urgency_label = {"high": "Urgent", "medium": "Important", "low": "Notice"}
        for i, rec in enumerate(recs):
            urgency = rec.get("urgency", "info").lower()
            label = urgency_label.get(urgency, "Info")
            hr = rec.get("human_review_status", {})
            approval_tag = " · Approval Required" if hr.get("required") else " · Ready"
            header = f"{label.upper()}{approval_tag}  —  {rec.get('title', 'Recommendation')}"

            with st.expander(header, expanded=False):
                # Short 1-line summary
                summary_full = rec.get("summary", "") or ""
                plan_full = rec.get("recommendation", "") or ""

                st.markdown(f"**At a glance:** {_first_sentence(summary_full)}")
                st.caption(f"Confidence: {rec.get('confidence', 'medium').upper()}")

                # Full summary as bullets (nested expander)
                if summary_full:
                    with st.expander("Full summary details", expanded=False):
                        bullets = _text_to_bullets(summary_full, max_bullets=10)
                        for b in bullets:
                            st.markdown(f"- {b}")

                # Plan action as bullets (nested expander)
                if plan_full:
                    with st.expander("Recommended plan actions", expanded=False):
                        bullets = _text_to_bullets(plan_full, max_bullets=10)
                        for b in bullets:
                            st.markdown(f"- {b}")

                # Approval gating info
                if hr.get("required"):
                    st.caption(
                        f"Gated by: {', '.join(hr.get('recommended_reviewer', []) or ['—'])}  |  "
                        f"Reason: {', '.join(hr.get('reason', []) or ['—'])}"
                    )

    st.markdown("<br>", unsafe_allow_html=True)

    # C. Missing Information Checklist — collapsed
    if missing:
        with st.expander(f"Needed Before Action — {len(missing)} items to resolve", expanded=False):
            st.caption("Resolve these before the proposed drafts can execute:")
            for m in missing:
                st.markdown(f"- **Resolve:** {m}")

    # D. Caution Alerts — collapsed (only if there are any)
    if warnings:
        with st.expander(f"Caution Alerts — {len(warnings)} items", expanded=False):
            for w in warnings:
                st.markdown(f"- {w}")

    # E. Draft Actions — collapsed
    with st.expander(f"Proposed System Actions (Drafts Only) — {len(actions)}", expanded=False):
        if not actions:
            st.info("No draft actions staged.")
        else:
            st.caption("Drafts remain in review state until a human approves them.")
            for j, act in enumerate(actions):
                hr = act.get("human_review_status", {})
                status_txt = "Blocked / Needs Review" if hr.get("required") else "Staged / Awaiting Approval"
                st.markdown(
                    f"**{status_txt}**  —  `{act.get('action_type', 'action')}`"
                )
                st.caption(f"Action ID: `{act.get('action_id', '—')}`  ·  Status: **Not executed** (pending approval)")
                with st.expander("Technical draft details", expanded=False):
                    st.write(act.get("payload", {}))
                if j < len(actions) - 1:
                    st.markdown("---")

    # F. Reference Evidence — collapsed
    with st.expander(f"Reference Evidence Records — {len(evidence)} sources", expanded=False):
        if not evidence:
            st.info("No reference evidence linked.")
        else:
            rows = []
            for ev in evidence:
                rows.append({
                     "Evidence ID": ev.get("evidence_id"),
                     "Source Name": ev.get("source_name"),
                     "Trust Tier": ev.get("trust_tier"),
                     "Freshness": ev.get("freshness_status"),
                     "Privacy Class": ev.get("privacy_class"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # G. Developer Audit — collapsed
    with st.expander("Developer Audit Panel (raw JSON)", expanded=False):
        st.json(action_pack)


def render_document_extraction_result(res_dict: Dict[str, Any]):
    """Renders extraction details with a compact summary + collapsed detail expanders."""
    st.subheader("Document Review Upload")
    st.warning("⚠️ Draft-only extraction — no actual file storage or farm-system record change.")

    # Top-line metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document Type", res_dict.get("document_type", "unknown").replace("_", " ").title())
    with col2:
        st.metric("Confidence", res_dict.get("extraction_confidence", "low").upper())
    with col3:
        st.metric("Review Status", res_dict.get("decision_anchor_status", "draft_pending_review").replace("_", " ").title())

    fields = res_dict.get("extracted_fields", {})
    missing = res_dict.get("missing_fields", [])
    notes = res_dict.get("notes", [])
    redactions = res_dict.get("redactions_applied", [])
    hr = res_dict.get("human_review", {})

    # 1. Extracted fields — collapsed
    with st.expander(f"Extracted Data Fields — {len(fields)} fields", expanded=False):
        if not fields:
            st.info("No fields extracted from the text.")
        else:
            rows = [{"Parameter": k, "Extracted Value": str(v)} for k, v in fields.items()]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 2. Missing fields — collapsed
    if missing:
        with st.expander(f"Missing Fields — {len(missing)} to resolve", expanded=False):
            for m in missing:
                st.markdown(f"- **Missing:** {m}")

    # 3. Security & review metadata — collapsed
    with st.expander("Security & Review Metadata", expanded=False):
        st.markdown(f"- **Evidence ID:** `{res_dict.get('evidence_id', '—')}`")
        if redactions:
            st.markdown("**Redactions applied:**")
            for red in redactions:
                st.markdown(f"- Redacted pattern: {red}")
        else:
            st.markdown("- No sensitive data redacted.")
        if hr.get("required"):
            st.markdown("**Review requirements:**")
            st.markdown(f"- **Reason:** {', '.join(hr.get('reason', []) or ['—'])}")
            st.markdown(f"- **Authorized reviewers:** {', '.join(hr.get('recommended_reviewer', []) or ['—'])}")

    # 4. Operational notes — collapsed
    if notes:
        with st.expander(f"Operational Notes — {len(notes)}", expanded=False):
            for note in notes:
                st.markdown(f"- {note}")

    # 5. Developer audit — collapsed
    with st.expander("Developer Audit (raw JSON)", expanded=False):
        st.json(res_dict)


# ---------------------------------------------------------------------------
# Navigation Bar / Helper Header
# ---------------------------------------------------------------------------

def render_top_navigation_bar(show_dashboard_btn: bool = True, key_suffix: str = ""):
    """Renders a consistent workspace bar at the top of farm pages."""
    farm_id = st.session_state.selected_farm
    if not farm_id:
        return
    farm_name = "Prairie View Farms" if farm_id == "PVF_ROW_CROP_001" else "Green Basket Organics"
    role = st.session_state.selected_role
    role_label = {
        "farm_owner": "Farm Owner",
        "farm_manager": "Farm Manager",
        "field_employee": "Field Crew"
    }.get(role, role)
    
    # We resolve location from profile
    profile = load_farm_profile(farm_id)
    location = profile.get("location", "US")

    # Layout using grid columns
    render_html(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; 
                background-color: #ffffff; padding: 0.6rem 1.25rem; border-radius: 4px; 
                border: 1px solid #c3c8c1; margin-bottom: 1.25rem; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
                flex-wrap: wrap; gap: 1rem;">
        <div style="display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;">
            <div>
                <span style="font-size: 0.65rem; font-weight: 700; color: #737872; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.1rem;">Current Workspace</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #334537; font-family: 'Courier Prime', monospace;">{farm_id}</span>
            </div>
            <div style="width: 1px; height: 28px; background-color: #c3c8c1;" class="hidden md:block"></div>
            <div>
                <span style="font-size: 0.65rem; font-weight: 700; color: #737872; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.1rem;">Location</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #334537;">{location}</span>
            </div>
            <div style="width: 1px; height: 28px; background-color: #c3c8c1;" class="hidden md:block"></div>
            <div>
                <span style="font-size: 0.65rem; font-weight: 700; color: #737872; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.1rem;">Perspective Role</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #334537;">{role_label}</span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span class="status-badge badge-preview" style="font-size: 0.65rem; padding: 0.25rem 0.5rem; margin: 0; letter-spacing: 0.08em;">Local Pilot</span>
        </div>
    </div>
    """)

    if show_dashboard_btn:
        col_dash, _ = st.columns([3, 9])
        with col_dash:
            if st.button("⬅ Dashboard", key=f"btn_top_dash{key_suffix}"):
                st.session_state.current_page = "dashboard"
                st.rerun()
        st.markdown("<hr style='margin: 0.75rem 0; border: 0; border-top: 1px solid #c3c8c1;'>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Page Renderers
# ---------------------------------------------------------------------------

def render_home_page():
    """Renders the polished emoji-free single-screen product landing page with local farm image."""

    # Handle sign in / log in info messages
    if "auth_msg" in st.session_state and st.session_state.auth_msg:
        st.info(st.session_state.auth_msg)
        st.session_state.auth_msg = None

    # ---- 1. Header bar (logo left, account/links right) -------------------
    col_logo, col_signin, col_login, col_learn = st.columns([5, 1.5, 1.5, 2])
    with col_logo:
        render_html("""
        <div style="display: flex; flex-direction: column; align-items: start; padding-top: 0.15rem;">
            <span style="font-size: 1.5rem; font-family: 'Literata', serif; font-weight: 700; color: #334537; line-height: 1.1;">HarvestAmp</span>
            <span style="font-size: 0.72rem; font-weight: 600; color: #737872; letter-spacing: 0.05em; text-transform: uppercase;">Harvest Amplifier AI Tool</span>
        </div>
        """)
    with col_signin:
        if st.button("Sign In", key="brand_signin"):
            st.session_state.auth_msg = "Account creation is not included in the local pilot demo."
            st.rerun()
    with col_login:
        if st.button("Log In", key="brand_login"):
            st.session_state.auth_msg = "Authentication is not included in the local pilot demo."
            st.rerun()
    with col_learn:
        if st.button("Learn More", key="brand_overview", type="primary"):
            st.session_state.current_page = "platform_overview"
            st.rerun()

    # ---- 2. Hero: 2-column layout (Left: brand copy + CTAs, Right: Stock Farm Image)
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    col_hl, col_hr = st.columns([6, 5])

    with col_hl:
        render_html("""
        <div style="text-align: left; padding-top: 0.5rem;">
            <span style="font-size: 0.8rem; font-weight: 700; color: #cca830; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.5rem;">
                HarvestAmp is a Harvest Amplifier — an AI tool for farm operations intelligence.
            </span>
            <h2 style="font-family: 'Literata', serif; font-size: 2.3rem; font-weight: 700; color: #334537; margin: 0 0 0.75rem 0; line-height: 1.2;">
                Amplify every harvest decision.
            </h2>
            <p style="font-size: 0.98rem; color: #4a544b; margin-bottom: 0.75rem; line-height: 1.55; font-family: 'Work Sans', sans-serif;">
                Turn weather, fieldwork, inventory, procurement, documents, and compliance into evidence-backed weekly action plans for farms and co-ops.
            </p>
            <p style="font-size: 0.8rem; font-weight: 700; color: #ba1a1a; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 0.05em;">
                External actions remain draft-only until a human approves them.
            </p>
        </div>
        """)
        
        # Compact CTAs grouped
        hcol1, hcol2, hcol3 = st.columns([1.2, 1.2, 0.8])
        with hcol1:
            if st.button("Open Prairie View Demo", key="hero_pvf_btn", type="primary", use_container_width=True):
                st.session_state.selected_farm = "PVF_ROW_CROP_001"
                st.session_state.current_page = "dashboard"
                st.rerun()
        with hcol2:
            if st.button("Open Green Basket Demo", key="hero_gbo_btn", type="primary", use_container_width=True):
                st.session_state.selected_farm = "GBO_DIRECT_001"
                st.session_state.current_page = "dashboard"
                st.rerun()
        with hcol3:
            if st.button("Learn More", key="hero_learn_btn", use_container_width=True):
                st.session_state.current_page = "platform_overview"
                st.rerun()

    with col_hr:
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        st.image("adobe_stock/AdobeStock_207353542.jpeg", use_container_width=True)

    # ---- 3. Capability Strip ---------------------------------------------
    st.markdown("<h3 class='serif-heading' style='text-align: center; color: #334537; margin: 2rem 0 1rem 0;'>Farm operations intelligence</h3>", unsafe_allow_html=True)
    
    cap_cols = st.columns(6)
    caps = [
        ("Weekly planning", "Coordinated weekly action reports."),
        ("Weather and fieldwork", "Fieldwork windows and weather context."),
        ("Inventory and procurement", "Stock tracking and purchase reviews."),
        ("Document intake", "OCR extraction of invoices and receipts."),
        ("Compliance guardrails", "Organic rules and safety boundaries."),
        ("Role-safe views", "Visibility gated by workspace role.")
    ]
    for col, (title, desc) in zip(cap_cols, caps):
        with col:
            render_html(f"""
            <div class="custom-card" style="border-top: 3px solid #334537; padding: 0.75rem; min-height: 110px;">
                <strong style="font-size: 0.85rem; color: #334537; display: block; margin-bottom: 0.25rem;">{title}</strong>
                <span style="font-size: 0.75rem; color: #737872; line-height: 1.35;">{desc}</span>
            </div>
            """)

    # ---- 4. Footer and Disclaimer ----------------------------------------
    render_html("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #c3c8c1; padding-top: 0.6rem; margin-top: 1.5rem; flex-wrap: wrap; gap: 0.5rem;">
        <span style="font-size: 0.72rem; color: #737872;">
            Local pilot: synthetic farm data only. No emails, orders, payments, outside contacts, or farm-system changes occur during this demo.
        </span>
        <span style="font-size: 0.72rem; color: #737872; font-weight: 600;">
            HarvestAmp | Harvest Amplifier AI Tool
        </span>
    </div>
    """)


def render_platform_overview_page():
    """Renders a condensed, single-screen Platform Overview with expandable detail sections."""

    # HOME button up top (overview has no farm context, so keep it minimal)
    col_home, _ = st.columns([2, 8])
    with col_home:
        if st.button("🏠 HOME", key="overview_home_btn", type="primary"):
            st.session_state.current_page = "home"
            st.rerun()
    st.markdown("---")

    st.title("🌾 What HarvestAmp Does")
    st.markdown(
        "<p style='font-size:1.05rem; color:#334537; font-weight:600; margin-bottom:0.4rem;'>"
        "HarvestAmp is your farm's operations co-pilot.</p>"
        "<p style='font-size:0.95rem; color:#334155; max-width: 820px;'>"
        "It reads weather, inventory, documents, and field conditions across organic farms, row-crop "
        "operations, and co-ops — then turns them into a clear weekly plan for owners, managers, and crew. "
        "Nothing leaves the farm without a human approving it first.</p>",
        unsafe_allow_html=True
    )

    # Condensed single-row value props
    st.markdown("<div style='margin: 1rem 0;'>", unsafe_allow_html=True)
    props = [
        ("🌤️", "Weather & Fieldwork", "Rain, wind, and field-access windows"),
        ("📦", "Inventory & Procurement", "Reorder timing and vendor quotes"),
        ("📄", "Documents", "Invoices, receipts, and load tickets"),
        ("🛡️", "Compliance", "Organic rules and safety guardrails"),
        ("👥", "Role-Safe Views", "Owners, managers, and crew see the right slice"),
    ]
    cols = st.columns(len(props))
    for col, (icon, title, desc) in zip(cols, props):
        with col:
            render_html(f"""
            <div class="custom-card" style="text-align:center; padding: 0.85rem 0.5rem;">
                <div style="font-size:1.3rem;">{icon}</div>
                <strong style="font-size:0.8rem; color:#334537; display:block; margin: 0.3rem 0;">{title}</strong>
                <span style="font-size:0.72rem; color:#64748b;">{desc}</span>
            </div>
            """)
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("Every action is evidence-backed and approval-gated. Details below ⬇️")

    # ---- Expandable detail sections (collapsed by default) ----------------
    with st.expander("🤖 How the AI works"):
        st.markdown(
            "A supervisor coordinates specialist agents for weather, fieldwork, procurement, inventory, "
            "compliance, records, and documents. A synthesizer turns their findings into a single ActionPack: "
            "recommendations, missing information, warnings, draft actions, and evidence."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                """
                * **Farm-specific workspaces** — each farm's data stays isolated; no cross-farm contamination of records or credentials.
                * **Strict role assignments** — field workers never see supplier pricing, margins, or restricted evidence.
                * **Evidence-backed recommendations** — every suggestion links back to the record or source that supported it.
                """
            )
        with col_b:
            st.markdown(
                """
                * **Human approval before action** — emails, purchases, payments, and record updates stay in draft form until approved.
                * **Read-only integrations first** — email, Drive, and accounting connections start as read-only ingestion before any action-capable integration.
                """
            )

    with st.expander("💡 Why it matters"):
        col_why1, col_why2 = st.columns(2)
        with col_why1:
            st.markdown(
                """
                * **Protect margins** — catch shortages, price changes, and bottlenecks earlier.
                * **Cut admin work** — turn quotes, invoices, and tickets into structured, review-ready records.
                * **Improve timing** — connect weather, pests, labor, and inventory into a practical weekly plan.
                """
            )
        with col_why2:
            st.markdown(
                """
                * **Support procurement** — know what to reorder and what's missing before you buy.
                * **Protect yields** — reduce preventable delays and improve visibility into moving parts.
                * **Keep teams aligned** — the right view for each person, without exposing sensitive data.
                """
            )

    with st.expander("🥬 See it in action: an organic farm's Monday"):
        st.markdown(
            """
            A small organic vegetable farm is prepping for CSA packing, market deliveries, and transplanting.
            HarvestAmp flags that packaging is running low before market weekend, that a supplier quote is
            missing a delivery date, and that one input record needs review before it can support compliance
            documentation. It also spots a narrow fieldwork window before rain, and recommends prioritizing
            transplanting over lower-priority cleanup.

            The owner sees the full picture — suppliers, inventory, draft quote language. The crew sees a
            simpler view: what to do next, and what's blocked until the owner reviews it. Nothing is
            purchased, no email is sent, and no record changes — everything stays in draft until approved.
            """
        )

    with st.expander("🚀 What's coming next"):
        col_srv1, col_srv2 = st.columns(2)
        with col_srv1:
            st.markdown(
                """
                * Gmail and Drive ingestion for quotes, invoices, and supplier messages
                * Supplier quote comparison and quote-request drafting
                * Billing and invoice organization
                """
            )
        with col_srv2:
            st.markdown(
                """
                * Irrigation, soil sensor, and equipment-system integrations
                * Accounting/POS synchronization
                * Carefully scoped action-capable workflows, always after human approval
                """
            )

    st.markdown("---")

    # CTA Buttons
    col_cta1, col_cta2, col_cta3 = st.columns(3)
    with col_cta1:
        if st.button("Open Prairie View Demo", key="overview_pvf", type="primary"):
            st.session_state.selected_farm = "PVF_ROW_CROP_001"
            st.session_state.current_page = "dashboard"
            st.rerun()
    with col_cta2:
        if st.button("Open Green Basket Demo", key="overview_gbo", type="primary"):
            st.session_state.selected_farm = "GBO_DIRECT_001"
            st.session_state.current_page = "dashboard"
            st.rerun()
    with col_cta3:
        if st.button("🏠 HOME", key="overview_back"):
            st.session_state.current_page = "home"
            st.rerun()


def render_demo_card(icon: str, title: str, desc: str, accent_color: str, badge_text: str = "Live Demo", badge_class: str = "badge-live"):
    """Renders a single demo action card with a consistent type scale (fixes huge-title/tiny-badge mismatch)."""
    render_html(f"""
    <div class="custom-card" style="border-top: 3px solid {accent_color}; padding: 1rem;">
        <div style="font-size: 1.3rem; margin-bottom: 0.2rem;">{icon}</div>
        <div style="font-size: 0.95rem; font-weight: 700; color: #334537; margin-bottom: 0.35rem; line-height: 1.25;">{title}</div>
        <div style="font-size: 0.78rem; color: #64748b; min-height: 38px; margin-bottom: 0.6rem; line-height: 1.35;">{desc}</div>
        <span class="status-badge {badge_class}" style="font-size: 0.68rem;">{badge_text}</span>
    </div>
    """)


def render_bento_card(icon: str, title: str, desc: str, badge_text: str, badge_class: str, button_label: str, button_key: str, handler_fn, accent_color: str = "#334537"):
    """Renders a clean bento card using CSS styles from the Stitch mockup and containing the action button."""
    render_html(f"""
    <div class="custom-card" style="border-top: 3px solid {accent_color}; padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between; height: 180px; margin-bottom: 0.5rem;">
        <div>
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <span style="font-size: 1.25rem;">{icon}</span>
                <span class="status-badge {badge_class}" style="font-size: 0.62rem; margin: 0;">{badge_text}</span>
            </div>
            <h4 class="serif-heading" style="font-size: 0.95rem; font-weight: 600; color: #334537; margin: 0 0 0.25rem 0; line-height: 1.3;">{title}</h4>
            <p style="font-size: 0.78rem; color: #737872; margin: 0; line-height: 1.35; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">{desc}</p>
        </div>
    </div>
    """)
    if st.button(button_label, key=button_key):
        handler_fn()


def render_farm_dashboard():
    """Renders the active Farm Demo Dashboard."""
    render_top_navigation_bar(show_dashboard_btn=False)
    farm_id = st.session_state.selected_farm
    farm_name = "Prairie View Farms" if farm_id == "PVF_ROW_CROP_001" else "Green Basket Organics"
    accent = "#334537" if farm_id == "PVF_ROW_CROP_001" else "#cca830"
    profile = load_farm_profile(farm_id)

    col_header, col_header_img = st.columns([9.5, 2.5])
    with col_header:
        render_html(f"""
        <h2 class="serif-heading" style="color: #334537; margin-bottom: 0.25rem; font-size: 1.8rem; font-weight: 600;">{farm_name} Dashboard</h2>
        <p style="font-size: 0.9rem; color: #737872; margin-bottom: 1.25rem;">
            Precision management and heritage data logging for active production cycle.
        </p>
        """)
    with col_header_img:
        image_path = "adobe_stock/AdobeStock_303214121.jpeg" if farm_id == "PVF_ROW_CROP_001" else "adobe_stock/AdobeStock_70087442.jpeg"
        st.image(image_path, use_container_width=True)

    # Perspective selector card compactly styled
    col_lbl, col_sel = st.columns([2, 8])
    with col_lbl:
        st.markdown(
            "<div style='padding-top: 6px; font-weight: 600; color: #334537; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em;'>Perspective View:</div>",
            unsafe_allow_html=True
        )
    with col_sel:
        role_map = {
            "farm_owner": "Farm Owner View (Full access: financials, margins, and draft actions)",
            "farm_manager": "Farm Manager View (Access: operations, recommendations, and fieldwork)",
            "field_employee": "Field Crew View (Restricted: safety, fieldwork task list only)"
        }
        selected_role = st.selectbox(
            "Current Active Role",
            ["farm_owner", "farm_manager", "field_employee"],
            index=["farm_owner", "farm_manager", "field_employee"].index(st.session_state.selected_role),
            format_func=lambda x: role_map[x],
            label_visibility="collapsed",
            key="dashboard_role_selector"
        )
        if selected_role != st.session_state.selected_role:
            st.session_state.selected_role = selected_role
            st.rerun()

    st.markdown("<hr style='margin: 1rem 0; border: 0; border-top: 1px solid #c3c8c1;'>", unsafe_allow_html=True)

    role = st.session_state.selected_role

    # Main Row Bento Grid (Left Priority Card + Right Context Card)
    col_left, col_right = st.columns([5, 7])

    with col_left:
        if farm_id == "PVF_ROW_CROP_001":
            stock_label = "Nitrogen Stock (UAN 32%)"
            stock_pct = 12
            stock_color = "#ba1a1a"
            window_title = "Planting Window"
            window_status = "Optimal: Next 48 Hours"
            window_desc = "Soil moisture 18.2%, Wind &lt; 12mph. High efficiency forecasted."
        else:
            stock_label = "CSA Packaging Clamshells"
            stock_pct = 18
            stock_color = "#cca830"
            window_title = "Harvest Window"
            window_status = "Optimal: Next 36 Hours"
            window_desc = "Ideal dewpoint and temperature. High efficiency forecasted."

        render_html(f"""
        <div class="custom-card" style="border-top: 4px solid #334537; padding: 1.5rem; height: 350px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 1rem;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 0.65rem; font-weight: 700; color: #ffffff; background-color: #334537; padding: 0.2rem 0.5rem; border-radius: 2px; text-transform: uppercase; letter-spacing: 0.08em;">Active Priority</span>
                </div>
                <h3 class="serif-heading" style="font-size: 1.25rem; font-weight: 600; color: #334537; margin: 0 0 0.15rem 0;">Weekly Action Report</h3>
                <p style="font-size: 0.8rem; color: #737872; margin: 0 0 1.25rem 0;">Fieldwork & Logistics Windows</p>
                
                <div style="background-color: #fbf9f4; border-left: 3px solid #334537; padding: 0.6rem 0.75rem; border-radius: 0 4px 4px 0; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.15rem;">
                        <span style="font-size: 0.65rem; font-weight: 700; color: #334537; text-transform: uppercase; letter-spacing: 0.08em;">{window_title}</span>
                        <span style="font-size: 0.9rem;">🌤️</span>
                    </div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #334537;">{window_status}</div>
                    <div style="font-size: 0.75rem; color: #737872; line-height: 1.3;">{window_desc}</div>
                </div>
                
                <div style="background-color: #fbf9f4; border: 1px solid #c3c8c1; padding: 0.6rem 0.75rem; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #737872; margin-bottom: 0.2rem;">
                        <span>{stock_label}</span>
                        <span style="font-weight: 700; color: {stock_color};">{stock_pct}% Remaining</span>
                    </div>
                    <div style="width: 100%; background-color: #e4e2dd; height: 6px; border-radius: 3px; overflow: hidden;">
                        <div style="width: {stock_pct}%; background-color: {stock_color}; height: 100%;"></div>
                    </div>
                </div>
            </div>
        </div>
        """)
        
        # Action button to trigger report
        if st.button("Generate Weekly Action Report", key="weekly_report_bento_btn", type="primary", use_container_width=True):
            run_action_with_spinner(
                lambda: run_weekly_plan_for_ui(farm_id, role),
                "Weekly Action Report",
                focus="weekly",
                title=f"{farm_name} Weekly Action Report"
            )

    with col_right:
        render_html(f"""
        <div class="custom-card" style="border-top: 4px solid #cca830; padding: 1.5rem; height: 350px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 1rem; background-color: #ffffff; position: relative; overflow: hidden;">
            <div style="position: absolute; inset: 0; opacity: 0.03; background-image: radial-gradient(#1b1c19 1px, transparent 1px); background-size: 16px 16px; pointer-events: none;"></div>
            
            <div style="position: relative; z-index: 1;">
                <h3 class="serif-heading" style="font-size: 1.25rem; font-weight: 600; color: #334537; margin: 0 0 0.15rem 0;">Operations Context</h3>
                <p style="font-size: 0.8rem; color: #737872; margin: 0 0 1.25rem 0;">Unified System Coordination Modules</p>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem;">
                    <div style="background-color: #fbf9f4; border: 1px solid #c3c8c1; padding: 0.6rem; border-radius: 4px;">
                        <div style="font-size: 0.75rem; font-weight: 700; color: #334537; margin-bottom: 0.15rem;">Weather & Fieldwork</div>
                        <div style="font-size: 0.68rem; color: #737872; line-height: 1.25; margin-bottom: 0.4rem;">Coordinated weather checking and fieldwork window evaluation.</div>
                        <span class="status-badge badge-partial" style="font-size: 0.55rem; padding: 0.05rem 0.25rem;">Workflow Context</span>
                    </div>
                    <div style="background-color: #fbf9f4; border: 1px solid #c3c8c1; padding: 0.6rem; border-radius: 4px;">
                        <div style="font-size: 0.75rem; font-weight: 700; color: #334537; margin-bottom: 0.15rem;">Inventory Watch</div>
                        <div style="font-size: 0.68rem; color: #737872; line-height: 1.25; margin-bottom: 0.4rem;">Ledger counts and reorder thresholds.</div>
                        <span class="status-badge badge-partial" style="font-size: 0.55rem; padding: 0.05rem 0.25rem;">Workflow Context</span>
                    </div>
                    <div style="background-color: #fbf9f4; border: 1px solid #c3c8c1; padding: 0.6rem; border-radius: 4px;">
                        <div style="font-size: 0.75rem; font-weight: 700; color: #334537; margin-bottom: 0.15rem;">Document Review</div>
                        <div style="font-size: 0.68rem; color: #737872; line-height: 1.25; margin-bottom: 0.4rem;">OCR ingestion check for quotes and receipts.</div>
                        <span class="status-badge badge-live" style="font-size: 0.55rem; padding: 0.05rem 0.25rem;">Live Demo</span>
                    </div>
                    <div style="background-color: #fbf9f4; border: 1px solid #c3c8c1; padding: 0.6rem; border-radius: 4px;">
                        <div style="font-size: 0.75rem; font-weight: 700; color: #334537; margin-bottom: 0.15rem;">Approval Queue</div>
                        <div style="font-size: 0.68rem; color: #737872; line-height: 1.25; margin-bottom: 0.4rem;">Human authorization gates for draft actions.</div>
                        <span class="status-badge badge-soon" style="font-size: 0.55rem; padding: 0.05rem 0.25rem;">Coming Soon</span>
                    </div>
                </div>
            </div>
        </div>
        """)

    st.markdown("<hr style='margin: 1.5rem 0 1rem 0; border: 0; border-top: 1px solid #c3c8c1;'>", unsafe_allow_html=True)
    st.markdown(
        """
        <h3 class="serif-heading" style="color: #334537; margin-bottom: 0.25rem; font-size: 1.3rem; font-weight: 600;">Operations Sandbox Actions</h3>
        <p style="font-size: 0.85rem; color: #737872; margin-bottom: 1.25rem;">
            Run individual specialist agent scenarios, audit compliance, or review receipts.
        </p>
        """,
        unsafe_allow_html=True
    )

    # Secondary cards layout in 3 columns
    if farm_id == "PVF_ROW_CROP_001":
        col1, col2, col3 = st.columns(3)
        with col1:
            render_bento_card(
                icon="🚜",
                title="Review Diesel Purchase Window",
                desc="Evaluate low fuel stock and identify optimal purchase window.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Evaluate Diesel Scenario",
                button_key="btn_diesel_scen",
                handler_fn=lambda: run_action_with_spinner(lambda: run_scenario_for_ui("PVF-002", role_override=role), "Diesel Purchase Window", focus="diesel", title="Diesel Purchase Window Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="💬",
                title="Review Supplier Quote",
                desc="Review OCR-extracted supplier quotes and find missing fields.",
                badge_text="Live Demo",
                badge_class="badge-live",
                button_label="Review Quote Document",
                button_key="btn_quote_doc",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui("PVF_ROW_CROP_001", role, "Review the supplier quote."), "Supplier Quote Review", focus="document", title="Supplier Quote Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🌤️",
                title="Review Weather & Fieldwork",
                desc="Review current fieldwork weather windows from the weekly action plan.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Review Weather",
                button_key="btn_weather_page_nav",
                handler_fn=lambda: (st.session_state.__setitem__("current_page", "weather"), st.rerun()),
                accent_color=accent
            )
        with col2:
            render_bento_card(
                icon="🌾",
                title="Review Grain Records",
                desc="Verify grain storage volume against bin ticket records.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Verify Grain Scenario",
                button_key="btn_grain_scen",
                handler_fn=lambda: run_action_with_spinner(lambda: run_scenario_for_ui("HARV-101", role_override=role), "Harvest / Grain Record Demo", focus="harvest_grain", title="Harvest / Grain Record Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🌱",
                title="Review Spray-Window Guardrail",
                desc="Review weather and compliance guardrails for field operations.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Check Spray Guardrails",
                button_key="btn_spray_scen",
                handler_fn=lambda: run_action_with_spinner(lambda: run_scenario_for_ui("PVF-005", role_override=role), "Spray-Window Guardrail", focus="spray_guardrail", title="Spray-Window Guardrail Review"),
                accent_color=accent
            )
        with col3:
            render_bento_card(
                icon="🛡️",
                title="Compare Owner vs Crew View",
                desc="Compare the owner view with the restricted crew view side-by-side.",
                badge_text="Live Demo",
                badge_class="badge-live",
                button_label="Compare Side-by-Side",
                button_key="btn_owner_crew_comp",
                handler_fn=lambda: (st.session_state.__setitem__("current_page", "role_comparison"), st.rerun()),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🎛️",
                title="Review Safety Boundaries",
                desc="Inspect the human-in-the-loop safety gating and simulation policy.",
                badge_text="Live Demo",
                badge_class="badge-live",
                button_label="Review Safety Gate",
                button_key="btn_safety_gate_scen",
                handler_fn=lambda: (st.session_state.__setitem__("current_page", "safety_gate"), st.rerun()),
                accent_color=accent
            )
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            render_bento_card(
                icon="📦",
                title="Review Packaging Reorder Need",
                desc="Evaluate low packaging stock and identify reorder triggers.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Evaluate Packaging Scenario",
                button_key="btn_pack_scen",
                handler_fn=lambda: run_action_with_spinner(lambda: run_scenario_for_ui("GBO-004", role_override=role), "Packaging Reorder Demo", focus="packaging", title="Packaging Reorder Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="📄",
                title="Review Packaging Receipt",
                desc="Review OCR-extracted packaging receipts and check pricing.",
                badge_text="Live Demo",
                badge_class="badge-live",
                button_label="Review Receipt Document",
                button_key="btn_pack_receipt_doc",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui("GBO_DIRECT_001", role, "Review the packaging receipt."), "Packaging Receipt Review", focus="document", title="Packaging Receipt Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🌤️",
                title="Review Weather & Fieldwork",
                desc="Review current fieldwork weather windows from the weekly action plan.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Review Weather",
                button_key="btn_weather_page_nav_gbo",
                handler_fn=lambda: (st.session_state.__setitem__("current_page", "weather"), st.rerun()),
                accent_color=accent
            )
        with col2:
            render_bento_card(
                icon="🥬",
                title="Review Market / CSA Readiness",
                desc="Evaluate direct-to-market CSA shares and delivery records.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Verify CSA Scenario",
                button_key="btn_csa_scen",
                handler_fn=lambda: run_action_with_spinner(lambda: run_scenario_for_ui("GBO-002", role_override=role), "Market / CSA Demo", focus="market_csa", title="Market / CSA Readiness Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🥗",
                title="Review Organic Input Documentation",
                desc="Check fertilizer inputs against organic certification rules.",
                badge_text="Workflow Context",
                badge_class="badge-partial",
                button_label="Verify Organic Inputs",
                button_key="btn_org_input_scen",
                handler_fn=lambda: run_action_with_spinner(lambda: run_scenario_for_ui("GBO-005", role_override=role), "Organic Input Review", focus="organic_input", title="Organic Input Documentation Review"),
                accent_color=accent
            )
        with col3:
            render_bento_card(
                icon="🛡️",
                title="Compare Owner vs Crew View",
                desc="Compare the owner view with the restricted crew view side-by-side.",
                badge_text="Live Demo",
                badge_class="badge-live",
                button_label="Compare Side-by-Side",
                button_key="btn_owner_crew_comp_gbo",
                handler_fn=lambda: (st.session_state.__setitem__("current_page", "role_comparison"), st.rerun()),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🎛️",
                title="Review Safety Boundaries",
                desc="Inspect the human-in-the-loop safety gating and simulation policy.",
                badge_text="Live Demo",
                badge_class="badge-live",
                button_label="Review Safety Gate",
                button_key="btn_safety_gate_scen_gbo",
                handler_fn=lambda: (st.session_state.__setitem__("current_page", "safety_gate"), st.rerun()),
                accent_color=accent
            )

    st.markdown("<hr style='margin: 1.5rem 0 1rem 0; border: 0; border-top: 1px solid #c3c8c1;'>", unsafe_allow_html=True)

    crop = "Corn & Soybeans" if farm_id == "PVF_ROW_CROP_001" else "Organic Mixed Produce"
    acreage = "1,240 Acres" if farm_id == "PVF_ROW_CROP_001" else "45 Acres"

    render_html(f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; 
                background-color: #f0eee9; border: 1px solid #c3c8c1; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;">
        <div style="text-align: center;">
            <div style="font-size: 0.65rem; font-weight: 700; color: #737872; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem;">Active Workspace</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #334537; font-family: 'Courier Prime', monospace;">{farm_id}</div>
        </div>
        <div style="text-align: center; border-left: 1px solid #c3c8c1;">
            <div style="font-size: 0.65rem; font-weight: 700; color: #737872; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem;">Primary Crop Focus</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #334537;">{crop}</div>
        </div>
        <div style="text-align: center; border-left: 1px solid #c3c8c1;">
            <div style="font-size: 0.65rem; font-weight: 700; color: #737872; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem;">Total Cultivated Area</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #334537;">{acreage}</div>
        </div>
        <div style="text-align: center; border-left: 1px solid #c3c8c1;">
            <div style="font-size: 0.65rem; font-weight: 700; color: #737872; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem;">Outbound API Connections</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #cca830;">0 Active (Simulated)</div>
        </div>
    </div>
    """)



def run_action_with_spinner(action_lambda, action_name, focus: Optional[str] = None, title: Optional[str] = None):
    """Execute a workflow action, store focused report metadata, and route to report view."""
    with st.spinner("HarvestAmp is analyzing farm records, evidence, and workflow rules..."):
        try:
            action_pack = action_lambda()
            st.success("ActionPack generated.")
            set_report(action_pack, focus=focus, title=title or action_name)
            st.rerun()
        except Exception as e:
            st.error(f"Execution failed: {str(e)}")


def render_report_view_page():
    """Renders the generated report along with a collapsed 'What HarvestAmp just did' summary."""
    render_top_navigation_bar()

    if not st.session_state.get("last_action_pack"):
        st.info("No ActionPack available. Return to the dashboard to execute an action.")
        return

    focus = st.session_state.get("report_focus")
    report_title = st.session_state.get("report_title")
    if focus and focus != "weekly":
        render_focused_action_report(st.session_state.last_action_pack, focus=focus, title=report_title)
    else:
        render_farm_action_report(st.session_state.last_action_pack, title=report_title)

    # Collapsed "What HarvestAmp just did" block
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚡ What HarvestAmp Just Did (behind the scenes)", expanded=False):
        st.markdown(
            """
            - 📂 **Loaded the selected farm profile** — crop types, acreage, and operator roles
            - 📝 **Retrieved local fixture records** — fuel stocks, grain bin inventories, observations
            - 🔀 **Routed the request through the Supervisor** — parsed intent and checked tenant-isolation boundaries
            - 🤖 **Ran specialist agents** — Records and Procurement Agents mapped to the operational topic
            - 🛡️ **Synthesized an evidence-backed ActionPack** — warnings, gaps, and evidence consolidated
            - 🔒 **Kept risky actions in draft/review state** — flagged procurement updates for human review
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_dash, col_another, _ = st.columns([3, 3, 6])
    with col_dash:
        if st.button("⬅️ Back to Farm Dashboard", key="btn_report_dash"):
            st.session_state.current_page = "dashboard"
            st.rerun()
    with col_another:
        if st.button("🔄 Run Another Demo / Action", key="btn_report_another"):
            st.session_state.current_page = "dashboard"
            st.rerun()


def render_weekly_plan_page():
    """Renders the Weekly Plan Page."""
    render_top_navigation_bar()
    farm_id = st.session_state.selected_farm
    farm_name = "Prairie View Farms" if farm_id == "PVF_ROW_CROP_001" else "Green Basket Organics"

    st.markdown(
        f"""
        <h2 class="serif-heading" style="color: #334537; margin-bottom: 0.5rem;">📅 Weekly Farm Plan Generator</h2>
        <p style="font-size: 0.95rem; color: #737872; margin-bottom: 1.5rem;">
            Generate the weekly coordination report for <strong>{farm_name}</strong>.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="custom-card" style="border-top: 3px solid #334537; padding: 1.5rem; margin-bottom: 1.5rem;">
            <h4 class="serif-heading" style="color: #334537; margin-bottom: 0.5rem;">Run Supervised Coordination</h4>
            <p style="font-size: 0.82rem; color: #737872; line-height: 1.4; margin-bottom: 0;">
                The Supervisor Agent will request telemetry from weather adapters, scan inventory stocks, 
                check certifier compliance rules, and draft a structured weekly operations report.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    role = st.selectbox(
        "Select User Perspective for Plan Generation", 
        ["farm_owner", "farm_manager", "field_employee"],
        index=["farm_owner", "farm_manager", "field_employee"].index(st.session_state.selected_role),
        format_func=lambda x: {
            "farm_owner": "Farm Owner View",
            "farm_manager": "Farm Manager View",
            "field_employee": "Field Crew View"
        }[x]
    )

    if st.button("Generate Weekly Action Report", type="primary"):
        with st.spinner("Executing supervisor weekly coordination..."):
            action_pack = run_weekly_plan_for_ui(farm_id, role)
            set_report(action_pack, focus="weekly", title=f"{farm_name} Weekly Action Report")
            st.rerun()


def render_role_comparison_page():
    """Renders the side-by-side Role Comparison View."""
    render_top_navigation_bar()
    farm_id = st.session_state.selected_farm

    render_html(f"""
    <h2 class="serif-heading" style="color: #334537; margin-bottom: 0.5rem;">🛡️ Owner vs Field Employee View</h2>
    <p style="font-size: 0.95rem; color: #737872; margin-bottom: 1.5rem;">
        HarvestAmp generates different ActionPack views based on the user’s role. 
        Farm owners can see restricted financial, supplier, and draft-action context. 
        Field employees receive only authorized operational information.
    </p>
    """)

    st.info(
        "Field employee view hides supplier pricing, customer/payment details, restricted evidence, and draft external actions."
    )

    if st.button("Compare Views Side-by-Side", type="primary"):
        col1, col2 = st.columns(2)
        
        with col1:
            render_html("""
            <div style="background-color: #334537; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1rem;">
                <h3 class="serif-heading" style="color: white !important; margin: 0; font-size: 1.15rem; font-weight: 600;">👑 Farm Owner View</h3>
                <p style="color: #eae8e3; font-size: 0.8rem; margin: 0.25rem 0 0 0;">Unrestricted access: finances, supplier quotes, draft actions.</p>
            </div>
            """)
            with st.spinner("Running owner plan..."):
                owner_pack = run_weekly_plan_for_ui(farm_id, "farm_owner")
                render_farm_action_report(owner_pack, title="Weekly Report - Owner")
        
        with col2:
            render_html("""
            <div style="background-color: #737872; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1rem;">
                <h3 class="serif-heading" style="color: white !important; margin: 0; font-size: 1.15rem; font-weight: 600;">🚜 Field Employee View</h3>
                <p style="color: #f0eee9; font-size: 0.8rem; margin: 0.25rem 0 0 0;">Restricted access: operational fieldwork tasks, safety notes, redacted financials.</p>
            </div>
            """)
            with st.spinner("Running employee plan..."):
                employee_pack = run_weekly_plan_for_ui(farm_id, "field_employee")
                render_farm_action_report(employee_pack, title="Weekly Report - Field Employee")


def render_scenario_runner_page():
    """Renders the Scenario Sandbox Runner."""
    render_top_navigation_bar()
    st.title("🚀 Scenario Sandbox Runner")
    st.write("Select and run any validated MVP scenarios from the fixture registry.")

    scenarios = load_scenarios()
    farm_id = st.session_state.selected_farm
    filtered_scenarios = [s for s in scenarios if s.get("farm_profile") == farm_id or s.get("farm_profile") == "multi_tenant"]
    
    options = [s["scenario_id"] for s in filtered_scenarios]
    
    selected_id = st.selectbox("Select Scenario", options, format_func=lambda x: next(f"{s['scenario_id']} - {s['name']}" for s in filtered_scenarios if s['scenario_id'] == x))

    scenario = next(s for s in filtered_scenarios if s["scenario_id"] == selected_id)
    
    with st.expander("Scenario Details", expanded=True):
        st.markdown(f"**Scenario ID**: `{scenario.get('scenario_id')}`")
        st.markdown(f"**Name**: {scenario.get('name')}")
        st.markdown(f"**Scenario-Defined Role**: `{scenario.get('user_role')}`")
        st.markdown(f"**Prompt**: *\"{scenario.get('prompt')}\"*")
        st.markdown(f"**Expected Agents**: {', '.join(scenario.get('expected_agents', []))}")

    # Role override selector
    st.markdown("#### Role Override")
    use_override = st.checkbox(
        "Override the scenario-defined role with a different user perspective",
        value=False,
        key="scenario_role_override_toggle"
    )
    role_override = None
    if use_override:
        role_override = st.selectbox(
            "Select role override",
            ["farm_owner", "farm_manager", "field_employee"],
            format_func=lambda x: {
                "farm_owner": "Farm Owner",
                "farm_manager": "Farm Manager",
                "field_employee": "Field Employee"
            }[x],
            key="scenario_role_override_select"
        )
        st.caption(f"Scenario will run as **{role_override}** instead of the scenario-defined role `{scenario.get('user_role')}`.")
    else:
        st.caption(f"Scenario will run with its defined role: `{scenario.get('user_role')}`.")

    if st.button("Run Scenario", type="primary"):
        with st.spinner("Simulating scenario..."):
            action_pack = run_scenario_for_ui(selected_id, role_override=role_override)
            st.session_state.last_action_pack = action_pack
            st.session_state.current_page = "view_report"
            st.rerun()


def render_document_review_page():
    """Renders the Document Review Intake Hub."""
    render_top_navigation_bar()
    farm_id = st.session_state.selected_farm
    farm_name = "Prairie View Farms" if farm_id == "PVF_ROW_CROP_001" else "Green Basket Organics"
    accent = "#334537" if farm_id == "PVF_ROW_CROP_001" else "#cca830"

    render_html(f"""
    <h2 class="serif-heading" style="color: #334537; margin-bottom: 0.5rem;">📄 Document Intake & Review</h2>
    <p style="font-size: 0.95rem; color: #737872; margin-bottom: 1.5rem;">
        Process physical farm files or quotes into draft structured records for <strong>{farm_name}</strong>.
    </p>
    """)

    tab_sample, tab_upload = st.tabs(["📂 Select Sample Documents", "📤 Preview: Extract Uploaded Text"])

    with tab_sample:
        render_html("""
        <h4 class="serif-heading" style="color: #334537; margin-bottom: 0.5rem;">Preset Document Review Ingestion</h4>
        <p style="font-size: 0.85rem; color: #737872; margin-bottom: 1.5rem;">
            Select an OCR-ingested document draft to run validation checks and compile structured metadata.
        </p>
        """)
        
        role = st.session_state.selected_role
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_bento_card(
                icon="📑",
                title="Review All Documents",
                desc="Run batch extraction on all local documents: quotes, receipts, invoices, and tickets.",
                badge_text="Batch Ingestion",
                badge_class="badge-info",
                button_label="Run Batch Review",
                button_key="btn_presets_all",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui(farm_id, role, "Review my local extracted documents."), "All Extracted Documents Review", focus="document", title="All Extracted Documents Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🧾",
                title="Supplier Invoice",
                desc="Extract billing data, line items, and payment instructions from UAN 32% nitrogen invoice.",
                badge_text="Invoice Ingestion",
                badge_class="badge-live",
                button_label="Review Invoice",
                button_key="btn_presets_invoice",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui(farm_id, role, "Review the supplier invoice."), "Supplier Invoice Review", focus="document", title="Supplier Invoice Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="🚜",
                title="Harvest Ticket",
                desc="Verify grain load weights and bin assignments against digital scale tickets.",
                badge_text="Logistics Ingestion",
                badge_class="badge-live",
                button_label="Review Load Ticket",
                button_key="btn_presets_ticket",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui(farm_id, role, "Review the harvest load ticket."), "Harvest Load Ticket Review", focus="document", title="Harvest Load Ticket Review"),
                accent_color=accent
            )
        with col2:
            render_bento_card(
                icon="💬",
                title="Supplier Quote",
                desc="Review diesel supplier quotes. Validates pricing, dates, and terms against requirements.",
                badge_text="Quote Review",
                badge_class="badge-live",
                button_label="Review Quote",
                button_key="btn_presets_quote",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui(farm_id, role, "Review the supplier quote."), "Supplier Quote Review", focus="document", title="Supplier Quote Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="⛽",
                title="Fuel Receipt",
                desc="Verify fuel delivery records against transaction receipt for off-road diesel.",
                badge_text="Receipt Ingestion",
                badge_class="badge-live",
                button_label="Review Fuel Receipt",
                button_key="btn_presets_fuel",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui(farm_id, role, "Review the fuel receipt."), "Fuel Receipt Review", focus="document", title="Fuel Receipt Review"),
                accent_color=accent
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            render_bento_card(
                icon="📝",
                title="Inventory Count Sheet",
                desc="Verify physical storage stock counts against inventory ledger records.",
                badge_text="Inventory Audit",
                badge_class="badge-live",
                button_label="Review Count Sheet",
                button_key="btn_presets_count",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui(farm_id, role, "Review the inventory count sheet."), "Inventory Count Sheet Review", focus="document", title="Inventory Count Sheet Review"),
                accent_color=accent
            )
        with col3:
            render_bento_card(
                icon="📦",
                title="Packaging Receipt",
                desc="Verify clamshell delivery invoice details and record item quantities.",
                badge_text="Receipt Ingestion",
                badge_class="badge-live",
                button_label="Review Packaging Receipt",
                button_key="btn_presets_pkg",
                handler_fn=lambda: run_action_with_spinner(lambda: run_document_review_for_ui(farm_id, role, "Review the packaging receipt."), "Packaging Receipt Review", focus="document", title="Packaging Receipt Review"),
                accent_color=accent
            )

    with tab_upload:
        st.markdown("#### Option B: Preview — Extract Uploaded Text")
        st.warning(
            "⚠️ **Session-only preview. Does not update records or create official changes.** "
            "Uploaded text extraction is a draft preview. It does not update records, "
            "does not enter the weekly plan, and does not create an ActionPack unless "
            "reviewed through a supervised workflow."
        )
        st.markdown("Upload a raw `.txt` or `.md` file to preview the extractor's parsing logic:")
        
        uploaded_file = st.file_uploader(
            "Upload a local text document for demo extraction. Files are processed in session only and are not saved.",
            type=["txt", "md"]
        )

        if uploaded_file is not None:
            text = uploaded_file.read().decode("utf-8")
            st.info("File loaded successfully. Extractor ready.")
            
            if st.button("Extract Uploaded File", type="primary"):
                with st.spinner("Parsing text content..."):
                    from harvestamp.extraction.document_extractor import DocumentExtractor
                    extractor = DocumentExtractor()
                    try:
                        result = extractor.extract_text(
                            text=text,
                            farm_id=farm_id,
                            document_id=f"uploaded_{uploaded_file.name.split('.')[0]}",
                            source_file_reference=uploaded_file.name,
                            source_name="Live UI Upload"
                        )
                        st.session_state.last_extraction_result = result.to_dict()
                    except Exception as e:
                        st.error(f"Extraction failed: {str(e)}")

        if st.session_state.get("last_extraction_result"):
            render_document_extraction_result(st.session_state.last_extraction_result)


def render_weather_page():
    """Renders the Weather Page using supervised weekly-plan workflow context."""
    render_top_navigation_bar()
    farm_id = st.session_state.selected_farm
    farm_name = "Prairie View Farms" if farm_id == "PVF_ROW_CROP_001" else "Green Basket Organics"

    st.title("🌤️ Weather & Fieldwork Context")
    st.markdown(
        "Weather context is demonstrated through HarvestAmp's supervised weekly-plan workflow. "
        "The Supervisor coordinates specialist agents that incorporate weather and field conditions "
        "into the farm's weekly action plan."
    )

    st.warning(
        "⚠️ **Safety Notice**: Weather context is advisory only. HarvestAmp does not recommend "
        "pesticide products, rates, tank mixes, treatment timing, or spray instructions."
    )

    st.markdown("---")

    st.subheader("📅 Weather and Fieldwork Context from Weekly Report")
    st.markdown(
        f"Run the weekly action plan for **{farm_name}** to review weather and fieldwork context "
        "as part of the supervised workflow:"
    )

    if st.button("Review Weather & Fieldwork Context", key="btn_eval_weather_plan", type="primary"):
        with st.spinner("Running supervised weekly-plan workflow..."):
            action_pack = run_weekly_plan_for_ui(farm_id, st.session_state.selected_role)
            recs = action_pack.get("recommendations", [])
            weather_recs = [r for r in recs if any(k in r.get("title", "").lower() or k in r.get("summary", "").lower() for k in ["weather", "rain", "fieldwork", "friday", "precipitation", "wind", "temperature"])]
            st.session_state.last_weather_recs = weather_recs

    if st.session_state.get("last_weather_recs") is not None:
        weather_recs = st.session_state.last_weather_recs
        if not weather_recs:
            st.info("No weather-specific context identified in the current weekly plan.")
        else:
            for wr in weather_recs:
                render_html(f"""
                <div class="custom-card">
                    <h4 class="serif-heading" style="margin:0 0 0.5rem 0; color: #334537; font-size: 1.05rem; font-weight: 600;">{wr.get('title')}</h4>
                    <p style="font-size: 0.9rem;"><strong>Summary</strong>: {wr.get('summary')}</p>
                    <p style="font-size: 0.9rem;"><strong>Plan Action</strong>: {wr.get('recommendation')}</p>
                </div>
                """)


def render_safety_gate_page():
    """Renders the Safety & Approval Gate Policy Page."""
    render_top_navigation_bar()
    
    render_html(f"""
    <h2 class="serif-heading" style="color: #334537; margin-bottom: 0.5rem;">🎛️ Safety & Approval Boundaries</h2>
    <p style="font-size: 0.95rem; color: #737872; margin-bottom: 1.5rem;">
        HarvestAmp operates under a strict "Human-in-the-loop" authorization protocol. 
        No system action is ever executed autonomously.
    </p>
    """)
    
    st.warning("⚠️ **Safety Principle**: HarvestAmp coordinates draft-only actions. No automated system can directly execute changes without explicit approval.")

    # Show design points as columns/cards
    col1, col2 = st.columns(2)
    
    with col1:
        render_html("""
        <div class="custom-card" style="border-top: 3px solid #334537; padding: 1.25rem; margin-bottom: 1rem;">
            <h4 class="serif-heading" style="color: #334537; font-size: 1.05rem; margin-bottom: 0.5rem;">🔒 Draft-Only Action Protocol</h4>
            <p style="font-size: 0.82rem; color: #737872; line-height: 1.4; margin-bottom: 0.75rem;">
                Every external operation (e.g. drafting supplier messages, certifier sharing, or resource requests) is generated strictly as a <strong>draft action</strong>.
            </p>
            <p style="font-size: 0.82rem; color: #737872; line-height: 1.4; margin-bottom: 0;">
                Staged actions remain labeled as <code>blocked_pending_user_approval</code> or <code>needs_user_approval</code>. They are never transmitted or processed automatically.
            </p>
        </div>
        <div style="height: 0.5rem;"></div>
        <div class="custom-card" style="border-top: 3px solid #737872; padding: 1.25rem; margin-bottom: 1rem;">
            <h4 class="serif-heading" style="color: #334537; font-size: 1.05rem; margin-bottom: 0.5rem;">🛡️ Role Authorization Gating</h4>
            <p style="font-size: 0.82rem; color: #737872; line-height: 1.4; margin-bottom: 0;">
                Action visibility and approval privileges are strictly bound to user roles. Restricted roles (like <code>field_employee</code>) are prevented from viewing or approving procurement, financials, or draft outbound changes.
            </p>
        </div>
        """)
        
    with col2:
        render_html("""
        <div class="custom-card" style="border-top: 3px solid #cca830; padding: 1.25rem; margin-bottom: 1rem;">
            <h4 class="serif-heading" style="color: #334537; font-size: 1.05rem; margin-bottom: 0.5rem;">🚫 Simulation & Isolation Gating</h4>
            <p style="font-size: 0.82rem; color: #737872; line-height: 1.4; margin-bottom: 0.75rem;">
                The Local Pilot MVP has <strong>zero active connectors</strong> to real-world communication channels (e.g., Gmail, Drive, Banks, POS, or supplier portals).
            </p>
            <p style="font-size: 0.82rem; color: #737872; line-height: 1.4; margin-bottom: 0;">
                All external interactions are simulated within the local session context to ensure zero operational risk. No emails are sent, no orders are placed, and no official systems are updated.
            </p>
        </div>
        <div style="height: 0.5rem;"></div>
        <div class="custom-card" style="border-top: 3px solid #ba1a1a; padding: 1.25rem; margin-bottom: 1rem;">
            <h4 class="serif-heading" style="color: #334537; font-size: 1.05rem; margin-bottom: 0.5rem;">📝 Verification & Logs</h4>
            <p style="font-size: 0.82rem; color: #737872; line-height: 1.4; margin-bottom: 0;">
                Every proposed action, data validation result, and agent routing decision is recorded transparently in the session audit ledger. This creates a paper trail for all coordinated actions.
            </p>
        </div>
        """)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.info("No backend changes are made in the local pilot. All actions remain as ActionPack draft payloads for audit review.")


# ---------------------------------------------------------------------------
# Main Routing entry
# ---------------------------------------------------------------------------

def main():
    # Session State Initialization
    if "selected_farm" not in st.session_state:
        st.session_state.selected_farm = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    if "selected_role" not in st.session_state:
        st.session_state.selected_role = "farm_owner"
    if "selected_scenario_id" not in st.session_state:
        st.session_state.selected_scenario_id = "PVF-002"
    if "report_focus" not in st.session_state:
        st.session_state.report_focus = None
    if "report_title" not in st.session_state:
        st.session_state.report_title = None

    st.set_page_config(
        page_title="HarvestAmp Platform Vision",
        page_icon="🌾",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    # Conditionally Hide Sidebar on Home & Platform Overview pages
    if st.session_state.current_page in ["home", "platform_overview"]:
        render_html("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        </style>
        """)

    # Sidebar branding
    st.sidebar.markdown(
        "\n".join(line.lstrip() for line in """
        <div style="text-align: center; padding: 0.5rem 0; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
            <span style="font-size: 1.6rem; line-height: 1;">🌾</span>
            <h2 style="margin: 0; color: #334537; font-size: 1.45rem; font-family: 'Literata', serif; font-weight: 600;">HarvestAmp</h2>
        </div>
        <div style="text-align: center; font-size: 0.75rem; color: #737872; margin-top: -0.25rem;">Farm Operations Intelligence</div>
        """.splitlines()),
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")

    # Sidebar Navigation logic based on whether a farm is selected
    if st.session_state.selected_farm:
        farm_name = "Prairie View Farms" if st.session_state.selected_farm == "PVF_ROW_CROP_001" else "Green Basket Organics"
        st.sidebar.info(f"📍 **{farm_name}**")

        page_options = {
            "dashboard": "Dashboard",
            "weekly_plan": "Weekly Plan",
            "document_review": "Review Documents",
            "scenario_runner": "Scenario Demo",
            "role_comparison": "Compare Roles",
            "safety_gate": "Safety / Approval Gate",
        }

        # Display buttons as menu items in sidebar
        for page_key, page_label in page_options.items():
            is_active = st.session_state.current_page == page_key
            if st.sidebar.button(page_label, key=f"nav_{page_key}", type="primary" if is_active else "secondary"):
                st.session_state.current_page = page_key
                st.session_state.last_action_pack = None
                st.session_state.report_focus = None
                st.session_state.report_title = None
                st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.markdown(
            "<div style='font-size:0.72rem; font-weight:700; color:#737872; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.4rem;'>Coming Soon</div>",
            unsafe_allow_html=True
        )
        st.sidebar.button("Upload Documents", key="future_upload", disabled=True)
        st.sidebar.caption("Future Function")
        st.sidebar.button("Search Records", key="future_search", disabled=True)
        st.sidebar.caption("Future Function")

        st.sidebar.markdown("---")
        if st.sidebar.button("Home", key="exit_farm_btn", type="secondary"):
            st.session_state.selected_farm = None
            st.session_state.current_page = "home"
            st.rerun()
    else:
        st.sidebar.info("Select a farm on the homepage to start the working demo.")
        if st.session_state.current_page != "home" and st.session_state.current_page != "platform_overview":
            if st.sidebar.button("Home", key="go_home_sidebar", type="primary"):
                st.session_state.current_page = "home"
                st.rerun()

    # Route current page
    if st.session_state.current_page == "home" or not st.session_state.selected_farm:
        if st.session_state.current_page == "platform_overview":
            render_platform_overview_page()
        else:
            render_home_page()
    elif st.session_state.current_page == "dashboard":
        render_farm_dashboard()
    elif st.session_state.current_page == "weekly_plan":
        render_weekly_plan_page()
    elif st.session_state.current_page == "role_comparison":
        render_role_comparison_page()
    elif st.session_state.current_page == "scenario_runner":
        render_scenario_runner_page()
    elif st.session_state.current_page == "document_review":
        render_document_review_page()
    elif st.session_state.current_page == "weather":
        render_weather_page()
    elif st.session_state.current_page == "safety_gate":
        render_safety_gate_page()
    elif st.session_state.current_page == "view_report":
        render_report_view_page()


if __name__ == "__main__":
    main()
