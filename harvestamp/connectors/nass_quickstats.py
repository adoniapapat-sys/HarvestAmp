import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class NASSQuickStatsConnector:
    """Connector for the USDA NASS Quick Stats API."""

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
        # Redact api_key parameter value or key parameter value
        text = re.sub(r"key=[a-zA-Z0-9_\-]+", "key=[REDACTED_API_KEY]", text)
        text = re.sub(r"api_key=[a-zA-Z0-9_\-]+", "api_key=[REDACTED_API_KEY]", text)
        # Redact any URL containing nass.usda.gov
        text = re.sub(r"https?://[^\s'\"<>\(\)]*(nass\.usda\.gov)[^\s'\"<>\(\)]*", "[REDACTED_URL]", text)
        return text

    def _scrub_exception(self, exc: Optional[BaseException], api_key: Optional[str] = None, visited=None) -> Optional[BaseException]:
        """Sanitizes an exception object's attributes recursively to prevent URL or API key exposure."""
        if exc is None:
            return None
            
        if visited is None:
            visited = set()
            
        if id(exc) in visited:
            return exc
        visited.add(id(exc))
        
        for attr in ["url", "filename"]:
            if hasattr(exc, attr):
                val = getattr(exc, attr)
                if isinstance(val, str):
                    try:
                        setattr(exc, attr, self._redact_url_and_key(val, api_key))
                    except (AttributeError, TypeError):
                        pass
                    
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

        if hasattr(exc, "args") and exc.args:
            try:
                exc.args = tuple(self._redact_url_and_key(str(arg), api_key) for arg in exc.args)
            except (AttributeError, TypeError):
                pass
                
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
        commodity: str,
        statisticcat_desc: str,
        state_alpha: str,
        county_name: Optional[str] = None,
        year: Optional[int] = None,
        agg_level_desc: Optional[str] = None,
        farm_id: Optional[str] = None,
        mock_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches crop statistics from USDA NASS Quick Stats API.
        
        If HARVESTAMP_NASS_SHADOW_LIVE=1, performs live API calls.
        Otherwise, returns deterministic mocked results.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        live_mode = os.environ.get("HARVESTAMP_NASS_SHADOW_LIVE") == "1"
        
        if live_mode and not mock_status:
            api_key = os.environ.get("HARVESTAMP_NASS_API_KEY")
            if not api_key:
                return self._build_result(
                    status="denied",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    missing_fields=["HARVESTAMP_NASS_API_KEY"],
                    assumptions=["Live mode requires HARVESTAMP_NASS_API_KEY environment variable."]
                )
                
            try:
                # Build USDA NASS Quick Stats URL
                url = f"https://quickstats.nass.usda.gov/api/api_GET/?key={api_key}&format=json&commodity_desc={commodity}&statisticcat_desc={statisticcat_desc}&state_alpha={state_alpha}"
                if county_name:
                    url += f"&county_name={county_name.upper()}"
                if year:
                    url += f"&year={year}"
                if agg_level_desc:
                    url += f"&agg_level_desc={agg_level_desc.upper()}"
                    
                req = urllib.request.Request(url)
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    
                records = data.get("data", [])
                if not records:
                    return self._build_result(
                        status="error",
                        payload={},
                        farm_id=farm_id,
                        retrieved_at=retrieved_at,
                        assumptions=["USDA NASS Quick Stats response records were empty."]
                    )
                    
                latest_rec = sorted(records, key=lambda r: int(r.get("year", 0)), reverse=True)[0]
                val_str = latest_rec.get("Value", "0").replace(",", "")
                try:
                    val = float(val_str)
                except ValueError:
                    val = val_str
                    
                observed_at = str(latest_rec.get("year", retrieved_at.split("T")[0]))
                
                payload = {
                    "crops": {
                        commodity.lower(): {
                            "yield_county_bushels_per_acre": val if latest_rec.get("agg_level_desc") == "COUNTY" else None,
                            "yield_state_bushels_per_acre": val if latest_rec.get("agg_level_desc") == "STATE" else None,
                            "unit": latest_rec.get("unit_desc", "BU / ACRE")
                        }
                    }
                }
                
                return self._build_result(
                    status="success",
                    payload=payload,
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    observed_at=observed_at
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
                    assumptions=["USDA NASS request timed out."]
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
            payload = self._get_mock_payload(commodity, state_alpha, county_name)
            return self._build_result(
                status="success",
                payload=payload,
                farm_id=farm_id,
                retrieved_at=retrieved_at
            )
        elif status == "stale":
            payload = self._get_mock_payload(commodity, state_alpha, county_name)
            stale_time = "2024-12-31"
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
        evidence_id = f"res_benchmark_nass_{farm_id or 'unknown'}"
        
        if not freshness_status:
            if status == "success":
                freshness_status = "fresh"
            elif status == "stale":
                freshness_status = "stale"
            else:
                freshness_status = "unavailable"
                
        live_mode = os.environ.get("HARVESTAMP_NASS_SHADOW_LIVE") == "1"
        source_name = "USDA NASS Quick Stats API (live)" if live_mode else "USDA NASS Quick Stats Connector (offline mock)"
        connector_mode = "live" if live_mode else "offline_mock"
        
        api_key = os.environ.get("HARVESTAMP_NASS_API_KEY")
        
        result = {
            "result_id": evidence_id,
            "source_id": "DS-010",
            "retrieved_at": retrieved_at,
            "freshness_status": freshness_status,
            "trust_tier": "T1 Official / primary",
            "privacy_class": "Public",
            "payload": payload,
            "evidence_reference": f"nass_quickstats_shadow_{farm_id or 'unknown'}",
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

    def _get_mock_payload(self, commodity: str, state_alpha: str, county_name: Optional[str]) -> Dict[str, Any]:
        """Returns mock NASS Quick Stats payload matching crops."""
        corn_yield_co = 195.0
        corn_yield_st = 203.0
        soy_yield_co = 61.0
        soy_yield_st = 64.0
        
        if state_alpha == "IL":
            corn_yield_st = 203.0
            soy_yield_st = 64.0
            if county_name and "CHAMPAIGN" in county_name.upper():
                corn_yield_co = 195.0
                soy_yield_co = 61.0
        
        commodity_lower = commodity.lower()
        if commodity_lower == "corn":
            return {
                "crops": {
                    "corn": {
                        "yield_county_bushels_per_acre": corn_yield_co,
                        "yield_state_bushels_per_acre": corn_yield_st,
                        "acreage_state_acres": 11200000
                    }
                }
            }
        elif commodity_lower == "soybeans":
            return {
                "crops": {
                    "soybeans": {
                        "yield_county_bushels_per_acre": soy_yield_co,
                        "yield_state_bushels_per_acre": soy_yield_st,
                        "acreage_state_acres": 10800000
                    }
                }
            }
        else: # return both for default mock regional crop benchmarks query
            return {
                "crops": {
                    "corn": {
                        "yield_county_bushels_per_acre": corn_yield_co,
                        "yield_state_bushels_per_acre": corn_yield_st,
                        "acreage_state_acres": 11200000
                    },
                    "soybeans": {
                        "yield_county_bushels_per_acre": soy_yield_co,
                        "yield_state_bushels_per_acre": soy_yield_st,
                        "acreage_state_acres": 10800000
                    }
                }
            }
