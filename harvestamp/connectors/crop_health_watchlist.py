import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class CropHealthWatchlistConnector:
    """Connector for Crop Health Watchlist (Extension, Regional IPM Centers, APHIS)."""

    def __init__(self):
        pass

    def fetch_watchlist(
        self,
        farm_id: Optional[str] = None,
        mock_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches crop health watchlist.
        
        If HARVESTAMP_CROP_HEALTH_SHADOW_LIVE=1, live mode is stubbed and returns live_mode_not_implemented fallback.
        Otherwise, returns deterministic mocked results from fixtures context.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        
        # Check environment overrides first for live mode
        live_mode = os.environ.get("HARVESTAMP_CROP_HEALTH_SHADOW_LIVE") == "1"
        
        if live_mode and not mock_status:
            return self._build_result(
                status="unavailable",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                fallback_used=True,
                fallback_reason="live_mode_not_implemented",
                assumptions=["Live mode is requested but not implemented in shadow mode."]
            )
            
        # Offline/Mock/Simulation mode
        status = mock_status or "success"
        
        if status == "success":
            payload = self._get_mock_payload(farm_id)
            return self._build_result(
                status="success",
                payload=payload,
                farm_id=farm_id,
                retrieved_at=retrieved_at
            )
        elif status == "stale":
            payload = self._get_mock_payload(farm_id)
            stale_time = "2026-05-29T08:00:00Z"
            return self._build_result(
                status="stale",
                payload=payload,
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                observed_at=stale_time,
                freshness_status="stale"
            )
        elif status == "unavailable":
            return self._build_result(
                status="unavailable",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                freshness_status="unavailable"
            )
        elif status == "denied":
            return self._build_result(
                status="denied",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                freshness_status="unavailable"
            )
        elif status == "timeout":
            return self._build_result(
                status="timeout",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                freshness_status="unavailable"
            )
        else: # error
            return self._build_result(
                status="error",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                freshness_status="unavailable"
            )

    def _build_result(
        self,
        status: str,
        payload: Dict[str, Any],
        farm_id: Optional[str],
        retrieved_at: str,
        observed_at: Optional[str] = None,
        freshness_status: Optional[str] = None,
        fallback_used: bool = False,
        fallback_reason: Optional[str] = None,
        missing_fields: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Constructs a ConnectorResult dict conforming to schemas."""
        evidence_id = f"res_crop_health_{farm_id or 'unknown'}"
        
        if not freshness_status:
            if status == "success":
                freshness_status = "fresh"
            elif status == "stale":
                freshness_status = "stale"
            else:
                freshness_status = "unavailable"
                
        # Determine connector mode dynamically based on shadow live env var
        live_mode = os.environ.get("HARVESTAMP_CROP_HEALTH_SHADOW_LIVE") == "1"
        source_name = "Crop Health Watchlist API (live)" if live_mode else "Crop Health Watchlist Connector (offline mock)"
        connector_mode = "live" if live_mode else "offline_mock"
                
        return {
            "result_id": evidence_id,
            "source_id": "DS-016",
            "retrieved_at": retrieved_at,
            "freshness_status": freshness_status,
            "trust_tier": "T1 Official / primary",
            "privacy_class": "Public",
            "payload": payload,
            "evidence_reference": f"crop_health_shadow_{farm_id or 'unknown'}",
            "status": status,
            "source_name": source_name,
            "source_type": "api",
            "observed_at": observed_at or retrieved_at,
            "farm_id": farm_id,
            "authorization_status": "authorized" if status != "denied" else "denied",
            "evidence_id": evidence_id,
            "missing_fields": missing_fields or [],
            "assumptions": assumptions or [],
            "connector_mode": connector_mode,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason
        }

    def _get_mock_payload(self, farm_id: Optional[str]) -> Dict[str, Any]:
        """Returns mock watchlist payload structure."""
        if farm_id == "PVF_ROW_CROP_001":
            return {
                "watchlist": [
                    {
                        "crop": "corn",
                        "region": "Midwest",
                        "state": "IL",
                        "issue_name": "Tar Spot",
                        "issue_type": "disease",
                        "source_category": "crop_protection_network",
                        "alert_scope": "regional_watchlist",
                        "risk_level": "watch",
                        "regulatory_relevance": "none",
                        "report_date": "2026-06-22",
                        "observation_window": "Coming week",
                        "source_name": "Crop Protection Network",
                        "source_reference": "CPN-2026-06",
                        "source_url": "https://cropprotectionnetwork.org",
                        "connector_mode": "offline_mock",
                        "fallback_used": False,
                        "fallback_reason": None,
                        "limitations": "Public context only, not a field diagnosis, not a pesticide recommendation, does not override farm records or scouting notes."
                    },
                    {
                        "crop": "soybeans",
                        "region": "Midwest",
                        "state": "IL",
                        "issue_name": "Japanese Beetle",
                        "issue_type": "pest",
                        "source_category": "regional_ipm_center",
                        "alert_scope": "pest_alert",
                        "risk_level": "moderate",
                        "regulatory_relevance": "none",
                        "report_date": "2026-06-22",
                        "observation_window": "Coming week",
                        "source_name": "North Central IPM Center",
                        "source_reference": "NCIPM-2026-06",
                        "source_url": "https://ncipmc.org",
                        "connector_mode": "offline_mock",
                        "fallback_used": False,
                        "fallback_reason": None,
                        "limitations": "Public context only, not a field diagnosis, not a pesticide recommendation, does not override farm records or scouting notes."
                    },
                    {
                        "crop": "soybeans",
                        "region": "Midwest",
                        "state": "IL",
                        "issue_name": "Brown Marmorated Stink Bug",
                        "issue_type": "regulated_pest",
                        "source_category": "aphis_ppq_caps",
                        "alert_scope": "regulated_pest_alert",
                        "risk_level": "low",
                        "regulatory_relevance": "watch",
                        "report_date": "2026-06-22",
                        "observation_window": "Coming week",
                        "source_name": "USDA APHIS PPQ",
                        "source_reference": "APHIS-PPQ-2026-06",
                        "source_url": "https://aphis.usda.gov",
                        "connector_mode": "offline_mock",
                        "fallback_used": False,
                        "fallback_reason": None,
                        "limitations": "Public context only, not a field diagnosis, not a pesticide recommendation, does not override farm records or scouting notes."
                    }
                ]
            }
        elif farm_id == "GBO_DIRECT_001":
            return {
                "watchlist": [
                    {
                        "crop": "tomatoes",
                        "region": "Northeast",
                        "state": "NY",
                        "issue_name": "Late Blight",
                        "issue_type": "disease",
                        "source_category": "crop_protection_network",
                        "alert_scope": "regional_watchlist",
                        "risk_level": "watch",
                        "regulatory_relevance": "none",
                        "report_date": "2026-06-22",
                        "observation_window": "Coming week",
                        "source_name": "Cornell Cooperative Extension",
                        "source_reference": "Cornell-EXT-2026-06",
                        "source_url": "https://cals.cornell.edu",
                        "connector_mode": "offline_mock",
                        "fallback_used": False,
                        "fallback_reason": None,
                        "limitations": "Public context only, not a field diagnosis, not a pesticide recommendation, does not override farm records, scouting notes, or organic certification requirements."
                    }
                ]
            }
        else:
            return {
                "watchlist": []
            }
