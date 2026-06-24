# harvestamp/policy/action_gate.py
"""Deterministic Action Gate validation for HarvestAmp.

Verifies user authorization and approval state before allowing Action Agent execution.
"""
from typing import Any, Dict, Tuple

class ActionGate:
    """Deterministic validation gate for Action Agent execution."""

    def verify_action_execution(
        self,
        action_payload: Dict[str, Any],
        human_review_status: Dict[str, Any],
        user_has_permission: bool = True
    ) -> Tuple[bool, str]:
        """Validates whether an action is allowed to execute based on approval status.
        
        Returns (is_allowed, log_message).
        """
        # If action requires approval and status is not approved or review_not_required, block
        is_review_required = human_review_status.get("required", False)
        review_type = human_review_status.get("review_type", "none")
        status = human_review_status.get("status", "draft")
        
        action_type = action_payload.get("action_type", "unknown")
        
        # Check permissions first
        if not user_has_permission:
            return False, f"Action '{action_type}' blocked: user lacks required authorization."

        if review_type == "blocked":
            return False, f"Action '{action_type}' blocked by policy: unauthorized cross-farm or credential request."

        if is_review_required:
            allowed_statuses = ["approved", "approved_with_edits", "review_not_required"]
            if status not in allowed_statuses:
                return False, f"Action '{action_type}' blocked: human review required (current status: '{status}')."
                
        # Access preview check for external disclosures
        if human_review_status.get("disclosure_preview_required", False) or review_type in ["user_approval", "expert_review"]:
            # Emulate showing preview
            pass

        return True, f"Action '{action_type}' successfully verified and allowed to execute."
