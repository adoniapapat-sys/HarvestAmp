# tests/test_action_gate.py
"""Tests for Action Agent execution gating."""
import pytest
from harvestamp.agents.action_agent import ActionAgent
from harvestamp.policy.action_gate import ActionGate

def test_action_agent_execution_gates():
    """Verify Action Agent executes only approved actions."""
    action_agent = ActionAgent()
    
    # 1. Action is draft, needs approval (Gate should block)
    action_payload = {
        "action_id": "act_order_fuel_1",
        "action_type": "supplier_message",
        "payload": {"body": "Order 2000 gallons"}
    }
    
    hr_needs_approval = {
        "required": True,
        "review_type": "user_approval",
        "status": "needs_user_approval"
    }
    
    with pytest.raises(PermissionError) as excinfo:
        action_agent.execute_action(action_payload, hr_needs_approval)
    assert "human review required" in str(excinfo.value)
    
    # 2. Action is approved (Gate should allow)
    hr_approved = {
        "required": True,
        "review_type": "user_approval",
        "status": "approved"
    }
    
    success, msg = action_agent.execute_action(action_payload, hr_approved)
    assert success
    assert "executed successfully" in msg
    
    # 3. Action is blocked by policy (Gate should block)
    hr_blocked = {
        "required": False,
        "review_type": "blocked",
        "status": "blocked"
    }
    
    with pytest.raises(PermissionError) as excinfo:
        action_agent.execute_action(action_payload, hr_blocked)
    assert "blocked by policy" in str(excinfo.value)
