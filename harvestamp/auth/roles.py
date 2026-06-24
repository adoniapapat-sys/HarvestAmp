# harvestamp/auth/roles.py
"""Role-based access control and farm isolation for HarvestAmp."""
from typing import Any, Dict, Optional

def get_user_profile(farm_profile: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    """Helper to find user within a farm profile."""
    for user in farm_profile.get("users", []):
        if user.get("user_id") == user_id:
            return user
    return None

def is_authorized(farm_profile: Dict[str, Any], user_id: str, permission: str) -> bool:
    """Checks if a user is authorized for a specific permission in a farm profile."""
    user = get_user_profile(farm_profile, user_id)
    if not user:
        return False
        
    permissions = user.get("permissions", [])
    restrictions = user.get("restrictions", [])
    
    # Check if there is an explicit restriction first
    restricted_name = f"cannot_{permission}"
    if restricted_name in restrictions:
        return False
        
    # If the permission is explicitly allowed
    if permission in permissions or "view_all_farm_data" in permissions:
        return True
        
    # Implicit operational access to basic operational data for all roles
    role = user.get("role", "")
    if permission == "view_operational_data":
        if role in ["farm_owner", "farm_manager", "field_employee", "field_lead", "market_staff", "authorized_advisor"]:
            return True
            
    return False

def check_cross_farm_block(requesting_farm_id: str, target_farm_id: str) -> bool:
    """Verifies that requesting farm matches target farm.
    
    Returns True if allowed (same farm), False if blocked (cross-farm leakage).
    """
    if not requesting_farm_id or not target_farm_id:
        return False
    return requesting_farm_id == target_farm_id

