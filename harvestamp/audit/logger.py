# harvestamp/audit/logger.py
"""Audit Logger for HarvestAmp.

Creates and stores AuditEvent structures for compliance and security monitoring.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

class AuditLogger:
    """Logs security, permission, and access events."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log_access(
        self,
        user_id: str,
        farm_id: str,
        action: str,
        result: str,
        data_category: str = "Farm Restricted",
        workflow_id: str = ""
    ) -> Dict[str, Any]:
        """Creates, records, and returns an AuditEvent."""
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "workflow_id": workflow_id,
            "user_id": user_id,
            "farm_id": farm_id,
            "action": action,
            "data_category": data_category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result
        }
        self.events.append(event)
        return event

    def list_events(self) -> List[Dict[str, Any]]:
        """Returns all recorded audit events."""
        return self.events
        
    def clear(self):
        """Clears audit logs."""
        self.events.clear()
