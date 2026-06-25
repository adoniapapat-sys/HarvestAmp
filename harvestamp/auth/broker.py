# harvestamp/auth/broker.py
"""Credential Broker stub for HarvestAmp.

The Credential Broker decides whether an agent request is authorized.
It returns capability grants only and never provides raw credentials, keys, or secrets.
"""
from typing import Any, Dict, Optional
from harvestamp.auth.roles import is_authorized

# Mapping of tools to required permission permissions
TOOL_PERMISSIONS = {
    "fuel_tool": "view_supplier_quotes",
    "fertilizer_tool": "view_supplier_quotes",
    "records_tool": "view_operational_data",
    "weather_tool": "view_operational_data",
    "marketdata_tool": "view_operational_data",
    "crop_benchmark": "view_operational_data",
    "crop_health_watchlist": "view_operational_data",
    "auth_tool": "manage_users"
}

class CredentialBroker:
    """Credential Broker stub. Mediates authorization decisions."""
    
    def __init__(self, audit_logger: Optional[Any] = None):
        self.audit_logger = audit_logger

    def request_capability_grant(self, farm_profile: Dict[str, Any], user_id: str, tool_name: str) -> Dict[str, Any]:
        """Evaluates whether to grant tool access capability.
        
        Returns a capability grant dictionary. NEVER returns raw secrets.
        """
        # Audit logging of capability request
        if self.audit_logger:
            self.audit_logger.log_access(
                user_id=user_id,
                farm_id=farm_profile.get("farm_id", "unknown"),
                action=f"request_capability:{tool_name}",
                result="requested"
            )
            
        required_perm = TOOL_PERMISSIONS.get(tool_name, "view_operational_data")
        
        # Check permissions
        has_access = is_authorized(farm_profile, user_id, required_perm)
        
        if not has_access:
            if self.audit_logger:
                self.audit_logger.log_access(
                    user_id=user_id,
                    farm_id=farm_profile.get("farm_id", "unknown"),
                    action=f"request_capability:{tool_name}",
                    result="denied"
                )
            return {
                "authorized": False,
                "reason": f"User {user_id} lacks permission '{required_perm}' required for tool '{tool_name}'",
                "capability": None
            }
            
        if self.audit_logger:
            self.audit_logger.log_access(
                user_id=user_id,
                farm_id=farm_profile.get("farm_id", "unknown"),
                action=f"request_capability:{tool_name}",
                result="granted"
            )
            
        return {
            "authorized": True,
            "reason": "Authorization succeeded.",
            "capability": f"capability:{tool_name}"
        }
