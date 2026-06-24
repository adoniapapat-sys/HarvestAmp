import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class NWSWeatherConnector:
    """Connector for the National Weather Service (NWS) Weather API."""

    def __init__(self):
        pass

    def fetch_weather(
        self,
        latitude: float,
        longitude: float,
        farm_id: Optional[str] = None,
        mock_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches weather forecast from NWS. Rounds coordinates to 4 decimal places.
        
        If HARVESTAMP_NWS_SHADOW_LIVE=1, performs live API calls.
        Otherwise, returns deterministic mocked results.
        """
        # Round coordinates to 4 decimal places for privacy and NWS constraints
        lat_rounded = round(latitude, 4)
        lon_rounded = round(longitude, 4)
        
        retrieved_at = datetime.now(timezone.utc).isoformat()
        
        # Check environment overrides first for live mode
        live_mode = os.environ.get("HARVESTAMP_NWS_SHADOW_LIVE") == "1"
        
        if live_mode and not mock_status:
            user_agent = os.environ.get("HARVESTAMP_NWS_USER_AGENT")
            if not user_agent:
                # Return denied/error status if User-Agent is missing
                return self._build_result(
                    status="denied",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    missing_fields=["User-Agent"],
                    assumptions=["Live mode requires HARVESTAMP_NWS_USER_AGENT environment variable."]
                )
            
            try:
                # Request 1: Get gridpoint URL from coordinates
                points_url = f"https://api.weather.gov/points/{lat_rounded},{lon_rounded}"
                req1 = urllib.request.Request(points_url, headers={"User-Agent": user_agent})
                
                # Add default timeout of 5 seconds to prevent hanging
                with urllib.request.urlopen(req1, timeout=5) as response1:
                    data1 = json.loads(response1.read().decode("utf-8"))
                
                forecast_url = data1.get("properties", {}).get("forecast")
                if not forecast_url:
                    return self._build_result(
                        status="error",
                        payload={},
                        farm_id=farm_id,
                        retrieved_at=retrieved_at,
                        missing_fields=["forecast_url"],
                        assumptions=["NWS points response was missing forecast link."]
                    )
                
                # Request 2: Get forecast periods from gridpoint URL
                req2 = urllib.request.Request(forecast_url, headers={"User-Agent": user_agent})
                with urllib.request.urlopen(req2, timeout=5) as response2:
                    data2 = json.loads(response2.read().decode("utf-8"))
                
                properties = data2.get("properties", {})
                periods = properties.get("periods", [])
                
                # Map periods to forecast payload
                forecast_payload = {"periods": periods}
                observed_at = properties.get("updateTime", retrieved_at)
                
                return self._build_result(
                    status="success",
                    payload=forecast_payload,
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    observed_at=observed_at
                )
                
            except urllib.error.HTTPError as e:
                status = "error"
                if e.code in [401, 403]:
                    status = "denied"
                elif e.code >= 500:
                    status = "unavailable"
                return self._build_result(
                    status=status,
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=[f"HTTP Error {e.code}: {e.reason}"]
                )
            except urllib.error.URLError as e:
                return self._build_result(
                    status="unavailable",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=[f"URL Error: {e.reason}"]
                )
            except TimeoutError as e:
                return self._build_result(
                    status="timeout",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=["NWS request timed out."]
                )
            except Exception as e:
                return self._build_result(
                    status="error",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=[f"Unexpected error: {str(e)}"]
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
        missing_fields: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Constructs a ConnectorResult dict conforming to schemas."""
        evidence_id = f"res_weather_nws_{farm_id or 'unknown'}"
        
        if not freshness_status:
            if status == "success":
                freshness_status = "fresh"
            elif status == "stale":
                freshness_status = "stale"
            else:
                freshness_status = "unavailable"
                
        return {
            "result_id": evidence_id,
            "source_id": "DS-006",
            "retrieved_at": retrieved_at,
            "freshness_status": freshness_status,
            "trust_tier": "T1 Official / primary",
            "privacy_class": "Public",
            "payload": payload,
            "evidence_reference": f"nws_weather_shadow_{farm_id or 'unknown'}",
            "status": status,
            "source_name": "National Weather Service API",
            "source_type": "api",
            "observed_at": observed_at or retrieved_at,
            "farm_id": farm_id,
            "authorization_status": "authorized" if status != "denied" else "denied",
            "evidence_id": evidence_id,
            "missing_fields": missing_fields or [],
            "assumptions": assumptions or []
        }

    def _get_mock_payload(self, farm_id: Optional[str]) -> Dict[str, Any]:
        """Returns mock NWS forecast periods structure."""
        if farm_id == "PVF_ROW_CROP_001":
            return {
                "periods": [
                    {"name": "Monday", "temperature": 78, "windSpeed": "6 to 12 mph", "detailedForecast": "Showers possible in evening."},
                    {"name": "Tuesday", "temperature": 82, "windSpeed": "7 to 14 mph", "detailedForecast": "Clear morning, storm chance evening."},
                    {"name": "Wednesday", "temperature": 75, "windSpeed": "12 to 20 mph", "detailedForecast": "Rain likely, heavy at times."},
                    {"name": "Thursday", "temperature": 72, "windSpeed": "10 to 18 mph", "detailedForecast": "Clear but windy."},
                    {"name": "Friday", "temperature": 77, "windSpeed": "5 to 10 mph", "detailedForecast": "Sunny and pleasant."},
                    {"name": "Saturday", "temperature": 80, "windSpeed": "8 to 15 mph", "detailedForecast": "Partly cloudy, storm chance."},
                    {"name": "Sunday", "temperature": 79, "windSpeed": "6 to 12 mph", "detailedForecast": "Mostly sunny."}
                ]
            }
        elif farm_id == "GBO_DIRECT_001":
            return {
                "periods": [
                    {"name": "Tuesday", "temperature": 80, "windSpeed": "5 to 10 mph", "detailedForecast": "Warm, scattered showers late."},
                    {"name": "Wednesday", "temperature": 84, "windSpeed": "8 to 12 mph", "detailedForecast": "Humid."},
                    {"name": "Thursday", "temperature": 82, "windSpeed": "6 to 10 mph", "detailedForecast": "Dry morning, storm chance evening."},
                    {"name": "Friday", "temperature": 88, "windSpeed": "5 to 8 mph", "detailedForecast": "Hot, heat advisory."},
                    {"name": "Saturday", "temperature": 76, "windSpeed": "10 to 16 mph", "detailedForecast": "Morning rain possible."}
                ]
            }
        else:
            return {
                "periods": [
                    {"name": "Today", "temperature": 70, "windSpeed": "5 to 10 mph", "detailedForecast": "Fair conditions."}
                ]
            }
