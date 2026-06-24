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
        observations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetches weather forecast for a farm."""
        if not check_cross_farm_block(requesting_farm_id, target_farm_id):
            raise PermissionError("Cross-farm data access blocked.")
            
        if not self._verify_grant(capability_grant, "weather_tool"):
            raise PermissionError("Unauthorized tool access capability.")

        weather_data = observations.get("weather", {}).get(target_farm_id, {})
        
        return {
            "result_id": weather_data.get("evidence_id", f"res_weather_{target_farm_id}"),
            "source_id": weather_data.get("source_id", "DS-006"),
            "retrieved_at": weather_data.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "freshness_status": weather_data.get("freshness_status", "fresh"),
            "trust_tier": weather_data.get("trust_tier", "T1 Official / primary"),
            "privacy_class": weather_data.get("privacy_class", "Public"),
            "payload": weather_data.get("forecast", {}),
            "evidence_reference": f"weather_forecast_{target_farm_id}",
            "timestamp": weather_data.get("timestamp", "2026-06-22T08:00:00-05:00"),
            "farm_id": weather_data.get("farm_id", target_farm_id),
            "authorization_status": weather_data.get("authorization_status", "authorized")
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
