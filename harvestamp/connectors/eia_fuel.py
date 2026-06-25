import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class EIAFuelBenchmarkConnector:
    """Connector for the U.S. Energy Information Administration (EIA) API."""

    def __init__(self):
        pass

    def _redact_url_and_key(self, text: str, api_key: Optional[str] = None) -> str:
        if not text:
            return ""
        import re
        if not isinstance(text, str):
            text = str(text)
        if api_key:
            text = text.replace(api_key, "[REDACTED_API_KEY]")
        # Redact api_key parameter value
        text = re.sub(r"api_key=[a-zA-Z0-9_\-]+", "api_key=[REDACTED_API_KEY]", text)
        # Redact any URL containing eia.gov
        text = re.sub(r"https?://[^\s'\"<>\(\)]*(eia\.gov)[^\s'\"<>\(\)]*", "[REDACTED_URL]", text)
        return text

    def _scrub_exception(self, exc: Optional[BaseException], api_key: Optional[str] = None, visited=None) -> Optional[BaseException]:
        """Sanitizes an exception object's attributes recursively to prevent URL or API key exposure."""
        if exc is None:
            return None
            
        if visited is None:
            visited = set()
            
        # Prevent infinite recursion in case of cycles
        if id(exc) in visited:
            return exc
        visited.add(id(exc))
        
        # Redact attributes that commonly hold the URL or raw query parameters
        for attr in ["url", "filename"]:
            if hasattr(exc, attr):
                val = getattr(exc, attr)
                if isinstance(val, str):
                    try:
                        setattr(exc, attr, self._redact_url_and_key(val, api_key))
                    except (AttributeError, TypeError):
                        pass
                    
        # Redact reason if it is a string or has args
        if hasattr(exc, "reason"):
            reason = getattr(exc, "reason")
            if isinstance(reason, str):
                try:
                    setattr(exc, "reason", self._redact_url_and_key(reason, api_key))
                except (AttributeError, TypeError):
                    try:
                        setattr(exc, "_reason", self._redact_url_and_key(reason, api_key))
                    except (AttributeError, TypeError):
                        pass
            elif hasattr(reason, "args"):
                try:
                    reason.args = tuple(self._redact_url_and_key(str(arg), api_key) for arg in reason.args)
                except (AttributeError, TypeError):
                    pass
            elif isinstance(reason, BaseException):
                self._scrub_exception(reason, api_key, visited)

        # Redact args
        if hasattr(exc, "args") and exc.args:
            try:
                exc.args = tuple(self._redact_url_and_key(str(arg), api_key) for arg in exc.args)
            except (AttributeError, TypeError):
                pass
                
        # Recursively scrub context and cause
        if hasattr(exc, "__context__") and exc.__context__:
            self._scrub_exception(exc.__context__, api_key, visited)
        if hasattr(exc, "__cause__") and exc.__cause__:
            self._scrub_exception(exc.__cause__, api_key, visited)
            
        return exc

    def _scrub_dict_or_list(self, obj: Any, api_key: Optional[str] = None) -> Any:
        """Recursively redacts URLs and API keys from a dict, list, or string."""
        if isinstance(obj, str):
            return self._redact_url_and_key(obj, api_key)
        elif isinstance(obj, dict):
            return {k: self._scrub_dict_or_list(v, api_key) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._scrub_dict_or_list(item, api_key) for item in obj]
        return obj

    def fetch_benchmark(
        self,
        series_id: str,
        farm_id: Optional[str] = None,
        mock_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches energy benchmark price from EIA API.
        
        If HARVESTAMP_EIA_SHADOW_LIVE=1, performs live API calls.
        Otherwise, returns deterministic mocked results.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        
        # Check environment overrides first for live mode
        live_mode = os.environ.get("HARVESTAMP_EIA_SHADOW_LIVE") == "1"
        
        if live_mode and not mock_status:
            api_key = os.environ.get("HARVESTAMP_EIA_API_KEY")
            if not api_key:
                return self._build_result(
                    status="denied",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    missing_fields=["HARVESTAMP_EIA_API_KEY"],
                    assumptions=["Live mode requires HARVESTAMP_EIA_API_KEY environment variable."]
                )
            
            try:
                # Request latest series data from EIA API v2
                url = f"https://api.eia.gov/v2/seriesid/{series_id}?api_key={api_key}"
                req = urllib.request.Request(url)
                
                # Add default timeout of 5 seconds to prevent hanging
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))
                
                # Parse EIA v2 response structure
                response_data = data.get("response", {})
                data_list = response_data.get("data", [])
                if not data_list:
                    return self._build_result(
                        status="error",
                        payload={},
                        farm_id=farm_id,
                        retrieved_at=retrieved_at,
                        assumptions=["EIA response data list was empty."]
                    )
                
                # Get the latest data point
                latest_point = data_list[0]
                val = latest_point.get("value")
                period = latest_point.get("period")
                desc = latest_point.get("series-description", "EIA Diesel Retail Price")
                
                payload = {
                    "price": val,
                    "period": period,
                    "trend": "mock_regional_diesel_benchmark_flat_to_slightly_down",
                    "description": desc
                }
                
                return self._build_result(
                    status="success",
                    payload=payload,
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    observed_at=period
                )
                
            except urllib.error.HTTPError as e:
                self._scrub_exception(e, api_key)
                status = "error"
                if e.code in [401, 403]:
                    status = "denied"
                elif e.code >= 500:
                    status = "unavailable"
                err_msg = self._redact_url_and_key(str(e), api_key)
                return self._build_result(
                    status=status,
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=[f"HTTP Error {e.code}: {err_msg}"]
                )
            except urllib.error.URLError as e:
                self._scrub_exception(e, api_key)
                err_msg = self._redact_url_and_key(str(e), api_key)
                return self._build_result(
                    status="unavailable",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=[f"URL Error: {err_msg}"]
                )
            except TimeoutError as e:
                self._scrub_exception(e, api_key)
                return self._build_result(
                    status="timeout",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=["EIA request timed out."]
                )
            except Exception as e:
                self._scrub_exception(e, api_key)
                err_msg = self._redact_url_and_key(str(e), api_key)
                return self._build_result(
                    status="error",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    assumptions=[f"Unexpected error: {err_msg}"]
                )
        
        # Offline/Mock/Simulation mode
        status = mock_status or "success"
        
        if status == "success":
            payload = self._get_mock_payload(series_id)
            return self._build_result(
                status="success",
                payload=payload,
                farm_id=farm_id,
                retrieved_at=retrieved_at
            )
        elif status == "stale":
            payload = self._get_mock_payload(series_id)
            stale_time = "2026-05-29"
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
        evidence_id = f"res_benchmark_eia_{farm_id or 'unknown'}"
        
        if not freshness_status:
            if status == "success":
                freshness_status = "fresh"
            elif status == "stale":
                freshness_status = "stale"
            else:
                freshness_status = "unavailable"
                
        # Determine connector mode and source name dynamically based on shadow live env var
        live_mode = os.environ.get("HARVESTAMP_EIA_SHADOW_LIVE") == "1"
        source_name = "EIA Fuel Benchmark API (live)" if live_mode else "EIA Fuel Benchmark Connector (offline mock)"
        connector_mode = "live" if live_mode else "offline_mock"
                
        api_key = os.environ.get("HARVESTAMP_EIA_API_KEY")
        result = {
            "result_id": evidence_id,
            "source_id": "DS-008",
            "retrieved_at": retrieved_at,
            "freshness_status": freshness_status,
            "trust_tier": "T1 Official / primary",
            "privacy_class": "Public",
            "payload": payload,
            "evidence_reference": f"eia_fuel_shadow_{farm_id or 'unknown'}",
            "status": status,
            "source_name": source_name,
            "source_type": "api",
            "observed_at": observed_at or retrieved_at.split("T")[0],
            "farm_id": farm_id,
            "authorization_status": "authorized" if status != "denied" else "denied",
            "evidence_id": evidence_id,
            "missing_fields": missing_fields or [],
            "assumptions": assumptions or [],
            "connector_mode": connector_mode
        }
        return self._scrub_dict_or_list(result, api_key)

    def _get_mock_payload(self, series_id: str) -> Dict[str, Any]:
        """Returns mock EIA series payload."""
        price = 3.85
        desc = "U.S. No 2 Diesel Retail Prices (weekly)"
        if "R20" in series_id:
            price = 3.75
            desc = "Midwest No 2 Diesel Retail Prices (weekly)"
        elif "R10" in series_id:
            price = 3.95
            desc = "East Coast No 2 Diesel Retail Prices (weekly)"
            
        return {
            "price": price,
            "period": "2026-06-22",
            "trend": "mock_regional_diesel_benchmark_flat_to_slightly_down",
            "description": desc
        }
