# harvestamp/agents/action_agent.py
"""Action Agent for HarvestAmp.

Responsible for executing actions. Utilizes ActionGate to verify approval status
prior to any external communication, ordering, or record updates.
"""
from typing import Any, Dict, Tuple
from harvestamp.policy.action_gate import ActionGate

class ActionAgent:
    """Action Agent. Executes permitted actions after passing the ActionGate."""

    def __init__(self, action_gate: ActionGate = None, audit_logger: Any = None):
        self.action_gate = action_gate or ActionGate()
        self.audit_logger = audit_logger

    def execute_action(
        self,
        action_payload: Dict[str, Any],
        human_review_status: Dict[str, Any],
        user_has_permission: bool = True
    ) -> Tuple[bool, str]:
        """Attempts to execute a proposed action.
        
        Returns (success, message). Raises PermissionError if blocked.
        """
        # Run Action Gate validation
        is_allowed, gate_msg = self.action_gate.verify_action_execution(
            action_payload,
            human_review_status,
            user_has_permission
        )
        
        action_type = action_payload.get("action_type", "unknown")
        
        if not is_allowed:
            # Audit log failure
            if self.audit_logger:
                self.audit_logger.log_access(
                    user_id=human_review_status.get("recommended_reviewer", ["unknown"])[0],
                    farm_id="unknown",
                    action=f"execute_action:{action_type}",
                    result=f"blocked: {gate_msg}"
                )
            raise PermissionError(f"Action Agent execution blocked: {gate_msg}")
            
        # If allowed, emulate execution
        exec_msg = f"Action '{action_type}' executed successfully. Sent payload: {action_payload.get('payload')}"
        
        if self.audit_logger:
            self.audit_logger.log_access(
                user_id=human_review_status.get("recommended_reviewer", ["unknown"])[0],
                farm_id="unknown",
                action=f"execute_action:{action_type}",
                result="executed"
            )
            
        return True, exec_msg
