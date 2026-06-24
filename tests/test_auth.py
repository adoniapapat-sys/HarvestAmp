# tests/test_auth.py
"""Tests for role-based access control and credential security."""
import os
import yaml
from harvestamp.auth.roles import is_authorized, check_cross_farm_block
from harvestamp.auth.broker import CredentialBroker
from harvestamp.audit.logger import AuditLogger

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def test_role_based_permissions():
    """Verify owner, manager, and employee permission levels."""
    pvf_path = os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")
    farm_profile = yaml.safe_load(open(pvf_path))

    # Mason Reed (Owner) permissions
    assert is_authorized(farm_profile, "pvf_owner_001", "approve_financial_actions")
    assert is_authorized(farm_profile, "pvf_owner_001", "view_supplier_quotes")

    # Elena Carter (Manager) permissions
    assert is_authorized(farm_profile, "pvf_manager_001", "view_supplier_quotes")
    assert not is_authorized(farm_profile, "pvf_manager_001", "approve_financial_actions")

    # Field Crew User (Employee) restrictions
    assert not is_authorized(farm_profile, "pvf_employee_001", "view_supplier_quotes")
    assert not is_authorized(farm_profile, "pvf_employee_001", "approve_financial_actions")

def test_cross_farm_blocking():
    """Verify tenant isolation blocks access to another farm's records."""
    # PVF and GBO must be blocked from cross-access
    assert not check_cross_farm_block("PVF_ROW_CROP_001", "GBO_DIRECT_001")
    assert check_cross_farm_block("PVF_ROW_CROP_001", "PVF_ROW_CROP_001")

def test_credential_broker_never_returns_secrets():
    """Verify Credential Broker returns capability grants, never secrets or keys."""
    pvf_path = os.path.join(FIXTURES_DIR, "farms", "prairie_view_farms.yaml")
    farm_profile = yaml.safe_load(open(pvf_path))
    
    logger = AuditLogger()
    broker = CredentialBroker(audit_logger=logger)
    
    # Authorized request
    grant = broker.request_capability_grant(farm_profile, "pvf_owner_001", "fuel_tool")
    assert grant["authorized"]
    assert grant["capability"] == "capability:fuel_tool"
    # Ensure no passwords, keys, or secrets are returned in the dict
    for k, v in grant.items():
        assert "password" not in str(v).lower()
        assert "secret" not in str(v).lower()
        assert "key" not in str(v).lower()
        
    # Unauthorized request
    grant_denied = broker.request_capability_grant(farm_profile, "pvf_employee_001", "fuel_tool")
    assert not grant_denied["authorized"]
    assert grant_denied["capability"] is None
