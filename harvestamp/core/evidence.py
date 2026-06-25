# harvestamp/core/evidence.py
"""Evidence Board and collector module for HarvestAmp.

Every recommendation must trace back to evidence collected here.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

class EvidenceBoard:
    """Manages the lifecycle of EvidenceItems retrieved during a workflow task."""
    
    def __init__(self):
        self.evidence_store: Dict[str, Dict[str, Any]] = {}
        
    def add_evidence(
        self,
        evidence_id: str,
        source_id: str,
        source_name: str,
        trust_tier: str,
        freshness_status: str,
        privacy_class: str,
        data_payload: Dict[str, Any],
        description: str = "",
        retrieved_at: Optional[str] = None,
        timestamp: Optional[str] = None,
        farm_id: Optional[str] = None,
        authorization_status: Optional[str] = None,
        connector_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates and stores an EvidenceItem."""
        if not retrieved_at:
            retrieved_at = datetime.now(timezone.utc).isoformat()
        if not timestamp:
            timestamp = retrieved_at
            
        evidence_item = {
            "evidence_id": evidence_id,
            "source_id": source_id,
            "source_name": source_name,
            "trust_tier": trust_tier,
            "freshness_status": freshness_status,
            "privacy_class": privacy_class,
            "retrieved_at": retrieved_at,
            "timestamp": timestamp,
            "farm_id": farm_id,
            "authorization_status": authorization_status or "authorized",
            "data_payload": data_payload,
            "description": description
        }
        if connector_mode:
            evidence_item["connector_mode"] = connector_mode
            
        self.evidence_store[evidence_id] = evidence_item
        return evidence_item
        
    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an EvidenceItem by ID."""
        return self.evidence_store.get(evidence_id)
        
    def list_evidence(self) -> List[Dict[str, Any]]:
        """Lists all collected evidence items."""
        return list(self.evidence_store.values())
        
    def clear(self):
        """Clears the Evidence Board."""
        self.evidence_store.clear()
