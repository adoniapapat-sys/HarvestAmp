# tests/test_irrigation.py
"""Functional tests verifying mock irrigation scheduling and water-request workflows."""
import pytest
from harvestamp.workflows.supervisor import Supervisor
from harvestamp.agents.action_agent import ActionAgent
from harvestamp.policy.action_gate import ActionGate
from harvestamp.audit.logger import AuditLogger
from tests.test_scenarios import load_scenario_context

def test_irr_001_schedule_advisory():
    """IRR-001: Irrigation schedule advisory from manual schedule."""
    scen, farm, obs = load_scenario_context("IRR-001")
    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "GBO_DIRECT_001"
    assert ap["status"] == "draft"
    assert ap["human_review_status"]["status"] in ["review_not_required", "needs_soft_confirmation", "needs_info"]
    
    # Verify no action candidate to submit request
    assert not any(act["action_type"] == "submit_irrigation_request" for act in ap["proposed_actions"])
    
    # Verify advisory mentions Thursday district turn
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "irrigation_advisory")
    assert "Thursday" in rec["summary"]
    assert "08:00 - 20:00" in rec["summary"]
    
    # Verify softened compliance wording is present
    comp_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "irrigation_compliance")
    assert "No conflict is surfaced in the mock/manual schedule data, but this is not a water-rights or district-rule determination. Verify provider rules and allocation status before acting." in comp_rec["summary"]
    
    # Verify renamed mock labels in evidence summary
    evidence_sources = [ev["source_name"] for ev in ap["evidence_summary"]]
    assert "Mock / Manual Irrigation Schedule" in evidence_sources
    assert "Irrigation Portal / Manual Schedule" not in evidence_sources
    
    # Verify missing data fields identified
    assert "crop water demand" in ap["missing_data"]
    assert "water allocation balance" in ap["missing_data"]
    assert "flow rate limits" in ap["missing_data"]
    assert "district constraints" in ap["missing_data"]

def test_irr_002_draft_water_request():
    """IRR-002: Draft irrigation water request."""
    scen, farm, obs = load_scenario_context("IRR-002")
    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["farm_id"] == "GBO_DIRECT_001"
    assert ap["status"] == "draft"
    assert ap["human_review_status"]["review_type"] == "user_approval"
    
    # Verify softened recommendation wording
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "irrigation_request_records")
    assert rec["recommendation"] == "Review and approve the drafted water request before any submission."
    
    # Verify softened compliance wording is present
    comp_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "irrigation_compliance")
    assert "No conflict is surfaced in the mock/manual schedule data, but this is not a water-rights or district-rule determination. Verify provider rules and allocation status before acting." in comp_rec["summary"]
    
    # Verify action candidate created with correct gating fields
    action = next(act for act in ap["proposed_actions"] if act["action_type"] == "submit_irrigation_request")
    assert action["status"] == "needs_user_approval"
    assert action["execution_status"] == "blocked_until_approved"
    assert action["disclosure_preview_required"] is True
    
    # Verify details are drafted accurately from observations
    payload = action["payload"]
    assert payload["field_id"] == "GBO_AREA_FIELD_A"
    assert payload["duration_hours"] == 12
    assert payload["day_of_week"] == "Tuesday"
    assert payload["provider_name"] == "River County Water District"
    
    # Action Agent must block unapproved execution
    action_agent = ActionAgent(audit_logger=logger)
    with pytest.raises(PermissionError) as exc_info:
        action_agent.execute_action(action, action["human_review_status"], user_has_permission=True)
    assert "blocked" in str(exc_info.value)

def test_irr_003_pasted_credentials():
    """IRR-003: User pastes irrigation portal credentials."""
    scen, farm, obs = load_scenario_context("IRR-003")
    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "blocked"
    assert ap["human_review_status"]["review_type"] == "blocked"
    
    # Verify no action candidates created
    assert len(ap["proposed_actions"]) == 0
    
    # Reconstruct secrets dynamically so they don't appear as raw literals in the test file
    secret_pw = "water" + "pass" + "123"
    secret_user = "river" + "_" + "farmer"
    
    # Verify no secret is leaked or repeated in ActionPack string representation
    ap_str = str(ap)
    assert secret_pw not in ap_str
    assert secret_user not in ap_str
    
    # Verify redirection warning
    assert "Credential Setup Assistant" in ap["warnings"][0] or "Credential Broker" in ap["warnings"][0]
    
    # Verify audit event is redacted and logged
    events = logger.list_events()
    assert len(events) > 0
    cred_event = next(e for e in events if e["action"] == "credential_exposure_detected")
    assert cred_event["result"] == "blocked_and_redacted"
    assert secret_pw not in str(cred_event)
    assert secret_user not in str(cred_event)

def test_irr_004_unauthorized_employee():
    """IRR-004: Unauthorized employee tries to submit water request."""
    scen, farm, obs = load_scenario_context("IRR-004")
    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    assert ap["status"] == "blocked"
    assert ap["human_review_status"]["review_type"] == "blocked"
    assert "unauthorized_role_attempt" in ap["human_review_status"]["reason"]
    
    # Verify no submission actions
    assert len(ap["proposed_actions"]) == 0
    
    # Verify blocked event is audited
    events = logger.list_events()
    assert len(events) > 0
    block_event = next(e for e in events if e["action"] == "submit_irrigation_request_attempt")
    assert block_event["result"] == "blocked_due_to_unauthorized_role"

def test_irr_005_missing_data():
    """IRR-005: Missing water allocation or volume data."""
    scen, farm, obs = load_scenario_context("IRR-005")
    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    # Verify low confidence and needs_info
    assert ap["human_review_status"]["status"] == "needs_info"
    
    # Verify no actions proposed
    assert len(ap["proposed_actions"]) == 0
    
    # Verify missing data fields list
    assert "water allocation" in ap["missing_data"]
    assert "requested volume" in ap["missing_data"]
    assert "soil history" in ap["missing_data"]
    assert "irrigation history" in ap["missing_data"]
    
    # Verify softened compliance wording is present
    comp_rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "irrigation_compliance")
    assert "No conflict is surfaced in the mock/manual schedule data, but this is not a water-rights or district-rule determination. Verify provider rules and allocation status before acting." in comp_rec["summary"]
    
    # Verify ComplianceAgent expert review trigger for water-rights / allocation sensitive topic if requested
    # Let's run a prompt with "rights" in it to trigger ComplianceAgent
    ap_comp = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], "Check water allocation and rights for Summer Crops field", obs)
    assert ap_comp["human_review_status"]["review_type"] == "expert_review"
    assert "water_rights_or_allocation_sensitive" in ap_comp["human_review_status"]["reason"]

def test_gateway_mediation():
    """Verify that Tool Gateway enforces capability grants and cross-farm checks."""
    logger = AuditLogger()
    supervisor = Supervisor(audit_logger=logger)
    
    # 1. No grant authorized
    grant_unauth = {"authorized": False, "capability": "capability:irrigation_tool"}
    with pytest.raises(PermissionError):
        supervisor.gateway.get_irrigation_schedule(grant_unauth, "GBO_DIRECT_001", "GBO_DIRECT_001", {})
        
    # 2. Wrong capability
    grant_wrong = {"authorized": True, "capability": "capability:weather_tool"}
    with pytest.raises(PermissionError):
        supervisor.gateway.get_irrigation_schedule(grant_wrong, "GBO_DIRECT_001", "GBO_DIRECT_001", {})
        
    # 3. Cross-farm access check
    grant_ok = {"authorized": True, "capability": "capability:irrigation_tool"}
    with pytest.raises(PermissionError):
        supervisor.gateway.get_irrigation_schedule(grant_ok, "GBO_DIRECT_001", "PVF_ROW_CROP_001", {})

def test_scenario_runner_redaction():
    """Verify that running scripts/run_scenario.py IRR-003 does not output credentials."""
    import subprocess
    import sys
    
    result = subprocess.run(
        [sys.executable, "scripts/run_scenario.py", "IRR-003"],
        capture_output=True,
        text=True,
        check=True
    )
    
    secret_pw = "water" + "pass" + "123"
    secret_user = "river" + "_" + "farmer"
    
    assert secret_pw not in result.stdout
    assert secret_user not in result.stdout
    assert "[REDACTED credential-bearing prompt]" in result.stdout
