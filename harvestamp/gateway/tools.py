# harvestamp/gateway/tools.py
"""Tool Gateway for HarvestAmp.

All tool calls are mediated here. Employs capability grants to return data
and isolates tenants to prevent cross-farm data leakage.
"""
from typing import Any, Dict, List, Optional
from harvestamp.auth.roles import check_cross_farm_block

class ToolGateway:
    """Tool Gateway stub. Ensures all queries are authorized by capability grants."""

    def __init__(self, audit_logger: Optional[Any] = None):
        self.audit_logger = audit_logger

    def _verify_grant(self, capability_grant: Dict[str, Any], tool_name: str) -> bool:
        """Helper to check if the grant is valid for the requested tool."""
        if not capability_grant.get("authorized"):
            return False
        expected_cap = f"capability:{tool_name}"
        return capability_grant.get("capability") == expected_cap

    def get_weather(
        self,
        capability_grant: Dict[str, Any],
        requesting_farm_id: str,
        target_farm_id: str,
        observations: Dict[str, Any],
        farm_profile: Optional[Dict[str, Any]] = None,
        evidence_board: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Fetches weather forecast for a farm in shadow mode, invoking NWS connector."""
        if not check_cross_farm_block(requesting_farm_id, target_farm_id):
            raise PermissionError("Cross-farm data access blocked.")
            
        if not self._verify_grant(capability_grant, "weather_tool"):
            raise PermissionError("Unauthorized tool access capability.")

        # Resolve farm coordinates (Farm Confidential, task-scoped)
        # Rounding is done inside the connector.
        # Synthetic coarse representative coordinates for MVP farms
        farm_coords = {
            "PVF_ROW_CROP_001": (40.1164, -88.2434),
            "GBO_DIRECT_001": (41.7004, -73.9210)
        }
        
        # Check location string in profile if ID not directly in coordinates mapping
        lat, lon = (40.0, -89.0)  # Default coarse coordinates
        if target_farm_id in farm_coords:
            lat, lon = farm_coords[target_farm_id]
        elif farm_profile and farm_profile.get("location"):
            loc = farm_profile["location"].lower()
            if "illinois" in loc:
                lat, lon = farm_coords["PVF_ROW_CROP_001"]
            elif "new york" in loc or "hudson" in loc:
                lat, lon = farm_coords["GBO_DIRECT_001"]

        # Call NWS connector in shadow mode
        from harvestamp.connectors.nws_weather import NWSWeatherConnector
        connector = NWSWeatherConnector()
        
        nws_mock_status = observations.get("nws_mock_status")
        nws_res = connector.fetch_weather(
            latitude=lat,
            longitude=lon,
            farm_id=target_farm_id,
            mock_status=nws_mock_status
        )

        # Record NWS-derived evidence in EvidenceBoard if available
        if evidence_board is not None:
            evidence_board.add_evidence(
                evidence_id=nws_res["result_id"],
                source_id=nws_res["source_id"],
                source_name=nws_res.get("source_name", "National Weather Service API"),
                trust_tier=nws_res["trust_tier"],
                freshness_status=nws_res["freshness_status"],
                privacy_class=nws_res["privacy_class"],
                data_payload=nws_res["payload"],
                description=f"Shadow NWS weather forecast status: {nws_res.get('status')}",
                timestamp=nws_res.get("retrieved_at"),
                farm_id=nws_res.get("farm_id"),
                authorization_status=nws_res.get("authorization_status"),
                connector_mode=nws_res.get("connector_mode")
            )

        # Retrieve local mock weather fixture payload
        weather_data = observations.get("weather", {}).get(target_farm_id, {})
        
        nws_status = nws_res.get("status", "success")
        nws_failed = nws_status in ["stale", "unavailable", "error", "timeout", "denied"]
        
        if nws_failed:
            fallback_used = True
            fallback_reason = f"NWS connector status: {nws_status}"
            returned_status = nws_status
            returned_freshness = nws_res.get("freshness_status", "unavailable")
        else:
            fallback_used = False
            fallback_reason = ""
            returned_status = "success"
            returned_freshness = "fresh"

        if not weather_data:
            payload = {}
            returned_freshness = "unavailable"
            if not nws_failed:
                fallback_used = True
                fallback_reason = "No mock weather fixture available."
        else:
            payload = weather_data.get("forecast", {})

        # Record fallback weather as evidence if fallback is used and weather data is present
        if fallback_used and evidence_board is not None and weather_data:
            evidence_board.add_evidence(
                evidence_id=weather_data.get("evidence_id", f"res_weather_{target_farm_id}"),
                source_id=weather_data.get("source_id", "DS-006"),
                source_name="Local Weather Fixture Fallback",
                trust_tier=weather_data.get("trust_tier", "T1 Official / primary"),
                freshness_status=returned_freshness,
                privacy_class=weather_data.get("privacy_class", "Public"),
                data_payload=payload,
                description=f"Local weather fixture fallback used due to NWS status: {nws_status}",
                timestamp=weather_data.get("timestamp", nws_res.get("retrieved_at")),
                farm_id=target_farm_id,
                authorization_status=weather_data.get("authorization_status", "authorized"),
                connector_mode="fixture_fallback"
            )

        return {
            "result_id": weather_data.get("evidence_id", f"res_weather_{target_farm_id}") if weather_data else f"res_weather_nws_{target_farm_id}",
            "source_id": weather_data.get("source_id", "DS-006") if weather_data else "DS-006",
            "source_name": "Local Weather Fixture Fallback" if fallback_used else nws_res["source_name"],
            "retrieved_at": weather_data.get("timestamp", nws_res.get("retrieved_at")) if weather_data else nws_res.get("retrieved_at"),
            "freshness_status": returned_freshness,
            "trust_tier": weather_data.get("trust_tier", "T1 Official / primary") if weather_data else "T1 Official / primary",
            "privacy_class": weather_data.get("privacy_class", "Public") if weather_data else "Public",
            "payload": payload,
            "evidence_reference": f"weather_forecast_{target_farm_id}",
            "timestamp": weather_data.get("timestamp", nws_res.get("retrieved_at")) if weather_data else nws_res.get("retrieved_at"),
            "farm_id": target_farm_id,
            "authorization_status": weather_data.get("authorization_status", "authorized") if weather_data else "authorized",
            
            # Shadow mode metadata
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "status": returned_status,
            "connector_mode": "fixture_fallback" if fallback_used else nws_res["connector_mode"]
        }

    def get_quotes(
        self,
        capability_grant: Dict[str, Any],
        requesting_farm_id: str,
        target_farm_id: str,
        farm_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetches quotes for a farm."""
        if not check_cross_farm_block(requesting_farm_id, target_farm_id):
            raise PermissionError("Cross-farm data access blocked.")
            
        if not self._verify_grant(capability_grant, "fertilizer_tool") and not self._verify_grant(capability_grant, "fuel_tool"):
            raise PermissionError("Unauthorized tool access capability.")

        raw_quotes = farm_profile.get("quotes", [])
        connector_results = []
        for q in raw_quotes:
            connector_results.append({
                "result_id": f"res_quote_{q['quote_id']}",
                "source_id": "DS-004",
                "retrieved_at": "2026-06-22T08:00:00-05:00",
                "freshness_status": "fresh",
                "trust_tier": "T1 Official / primary",
                "privacy_class": "Farm Restricted",
                "payload": q,
                "evidence_reference": q["quote_id"],
                "timestamp": "2026-06-22T08:00:00-05:00",
                "farm_id": target_farm_id,
                "authorization_status": "authorized"
            })
        return connector_results

    def get_inventory(
        self,
        capability_grant: Dict[str, Any],
        requesting_farm_id: str,
        target_farm_id: str,
        farm_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetches inventory items for a farm."""
        if not check_cross_farm_block(requesting_farm_id, target_farm_id):
            raise PermissionError("Cross-farm data access blocked.")
            
        if not self._verify_grant(capability_grant, "records_tool"):
            raise PermissionError("Unauthorized tool access capability.")

        raw_inv = farm_profile.get("inventory", [])
        connector_results = []
        for item in raw_inv:
            connector_results.append({
                "result_id": f"res_inv_{item['item_id']}",
                "source_id": "DS-003",
                "retrieved_at": "2026-06-22T08:00:00-05:00",
                "freshness_status": "fresh",
                "trust_tier": "T3 User-entered",
                "privacy_class": "Farm Confidential",
                "payload": item,
                "evidence_reference": item["item_id"],
                "timestamp": "2026-06-22T08:00:00-05:00",
                "farm_id": target_farm_id,
                "authorization_status": "authorized"
            })
        return connector_results

    def get_benchmark(
        self,
        capability_grant: Dict[str, Any],
        observations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetches energy benchmark trends."""
        if not self._verify_grant(capability_grant, "fuel_tool"):
            raise PermissionError("Unauthorized tool access capability.")

        benchmark = observations.get("benchmarks", {}).get("diesel_trend", {})
        
        return {
            "result_id": benchmark.get("evidence_id", "res_benchmark_diesel"),
            "source_id": benchmark.get("source_id", "DS-008"),
            "retrieved_at": benchmark.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "freshness_status": benchmark.get("freshness_status", "fresh"),
            "trust_tier": benchmark.get("trust_tier", "T1 Official / primary"),
            "privacy_class": benchmark.get("privacy_class", "Public"),
            "payload": {"trend": benchmark.get("value")},
            "evidence_reference": "diesel_trend",
            "timestamp": benchmark.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "farm_id": benchmark.get("farm_id"),
            "authorization_status": benchmark.get("authorization_status", "authorized")
        }

    def get_irrigation_schedule(
        self,
        capability_grant: Dict[str, Any],
        requesting_farm_id: str,
        target_farm_id: str,
        observations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetches irrigation schedule for a farm."""
        if not check_cross_farm_block(requesting_farm_id, target_farm_id):
            raise PermissionError("Cross-farm data access blocked.")
            
        if not self._verify_grant(capability_grant, "irrigation_tool"):
            raise PermissionError("Unauthorized tool access capability.")

        sched = observations.get("irrigation_schedules", {}).get(target_farm_id, {})
        if not sched:
            return {}

        return {
            "result_id": sched.get("evidence_id", f"res_irr_sched_{target_farm_id}"),
            "source_id": sched.get("source_id", "DS-029"),
            "retrieved_at": sched.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "freshness_status": sched.get("freshness_status", "fresh"),
            "trust_tier": sched.get("trust_tier", "T3 User-entered"),
            "privacy_class": sched.get("privacy_class", "Farm Restricted"),
            "payload": sched.get("schedule", {}),
            "evidence_reference": f"irrigation_schedule_{target_farm_id}",
            "timestamp": sched.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "farm_id": target_farm_id,
            "authorization_status": sched.get("authorization_status", "authorized")
        }

    def get_irrigation_request_context(
        self,
        capability_grant: Dict[str, Any],
        requesting_farm_id: str,
        target_farm_id: str,
        observations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetches irrigation request context for a farm."""
        if not check_cross_farm_block(requesting_farm_id, target_farm_id):
            raise PermissionError("Cross-farm data access blocked.")
            
        if not self._verify_grant(capability_grant, "irrigation_tool"):
            raise PermissionError("Unauthorized tool access capability.")

        req = observations.get("irrigation_requests", {}).get(target_farm_id, {})
        if not req:
            return {}

        return {
            "result_id": req.get("evidence_id", f"res_irr_req_{target_farm_id}"),
            "source_id": req.get("source_id", "DS-029"),
            "retrieved_at": req.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "freshness_status": req.get("freshness_status", "fresh"),
            "trust_tier": req.get("trust_tier", "T1 Official / primary"),
            "privacy_class": req.get("privacy_class", "Farm Restricted"),
            "payload": req.get("request_context", {}),
            "evidence_reference": f"irrigation_request_{target_farm_id}",
            "timestamp": req.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "farm_id": target_farm_id,
            "authorization_status": req.get("authorization_status", "authorized")
        }

