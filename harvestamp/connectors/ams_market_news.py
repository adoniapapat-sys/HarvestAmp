import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class AMSMarketNewsConnector:
    """Connector for the USDA Agricultural Marketing Service (AMS) MyMarketNews API."""

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
        # Redact any URL containing ams.usda.gov
        text = re.sub(r"https?://[^\s'\"<>\(\)]*(ams\.usda\.gov)[^\s'\"<>\(\)]*", "[REDACTED_URL]", text)
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

    def _load_report_config(self, slug_id: str) -> Optional[Dict[str, Any]]:
        """Loads the report configuration for a given slug_id."""
        config_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "configs", "ams_report_mapping.yaml"
        ))
        if not os.path.exists(config_path):
            return None
        try:
            import yaml
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            for r in config.get("reports", []):
                if str(r.get("slug_id")) == str(slug_id):
                    return r
        except Exception:
            pass
        return None

    def fetch_market_report(
        self,
        slug_id: str,
        farm_id: Optional[str] = None,
        mock_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches market report data from the USDA AMS MyMarketNews API.
        
        If HARVESTAMP_AMS_SHADOW_LIVE=1, performs live API calls.
        Otherwise, returns deterministic mocked results.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        live_mode = os.environ.get("HARVESTAMP_AMS_SHADOW_LIVE") == "1"
        
        if live_mode and not mock_status:
            api_key = os.environ.get("HARVESTAMP_AMS_API_KEY")
            if not api_key:
                return self._build_result(
                    status="denied",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    slug_id=slug_id,
                    missing_fields=["HARVESTAMP_AMS_API_KEY"],
                    assumptions=["Live mode requires HARVESTAMP_AMS_API_KEY environment variable."]
                )
                
            try:
                # Live MyMarketNews report detail URL
                url = f"https://mymarketnews.ams.usda.gov/services/v1.1/reports/{slug_id}?api_key={api_key}"
                req = urllib.request.Request(url)
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))
                
                # Dynamic parsing based on report mapping config
                config = self._load_report_config(slug_id)
                reports_data = {}
                
                # Locate records list in response
                records = []
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    for k in ["results", "data", "records"]:
                        if isinstance(data.get(k), list):
                            records = data[k]
                            break
                            
                # Extract and map matching commodities
                if config and "commodity_map" in config:
                    commodity_map = config["commodity_map"]
                    for key, mapped_name in commodity_map.items():
                        # Find matching records
                        matched_rec = None
                        for rec in records:
                            # Search in all string fields for mapped name
                            found = False
                            for rec_val in rec.values():
                                if isinstance(rec_val, str) and rec_val.upper() == mapped_name.upper():
                                    found = True
                                    break
                            if found:
                                matched_rec = rec
                                break
                        
                        if matched_rec:
                            # Put all attributes of matched record
                            reports_data[key] = dict(matched_rec)
                            # Derive price per lb if possible
                            if "regional_wholesale_price_per_lb" not in reports_data[key]:
                                # Try common keys
                                avg_price = matched_rec.get("price_average") or matched_rec.get("average")
                                if avg_price is not None:
                                    reports_data[key]["regional_wholesale_price_per_lb"] = float(avg_price)
                                else:
                                    min_p = matched_rec.get("price_min") or matched_rec.get("min")
                                    max_p = matched_rec.get("price_max") or matched_rec.get("max")
                                    if min_p is not None and max_p is not None:
                                        reports_data[key]["regional_wholesale_price_per_lb"] = (float(min_p) + float(max_p)) / 2.0
                            
                            # Market tone
                            if "market_tone" not in reports_data[key]:
                                reports_data[key]["market_tone"] = matched_rec.get("tone") or matched_rec.get("market_tone") or "steady"
                
                return self._build_result(
                    status="success",
                    payload={"reports": reports_data},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    slug_id=slug_id
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
                    slug_id=slug_id,
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
                    slug_id=slug_id,
                    assumptions=[f"URL Error: {err_msg}"]
                )
            except TimeoutError as e:
                self._scrub_exception(e, api_key)
                return self._build_result(
                    status="timeout",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    slug_id=slug_id,
                    assumptions=["USDA AMS request timed out."]
                )
            except Exception as e:
                self._scrub_exception(e, api_key)
                err_msg = self._redact_url_and_key(str(e), api_key)
                return self._build_result(
                    status="error",
                    payload={},
                    farm_id=farm_id,
                    retrieved_at=retrieved_at,
                    slug_id=slug_id,
                    assumptions=[f"Unexpected error: {err_msg}"]
                )
                
        # Offline/Mock/Simulation mode
        status = mock_status or "success"
        
        if status == "success":
            payload = self._get_mock_payload(slug_id)
            return self._build_result(
                status="success",
                payload=payload,
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                slug_id=slug_id
            )
        elif status == "stale":
            payload = self._get_mock_payload(slug_id)
            stale_time = "2026-06-15T08:00:00-05:00"
            return self._build_result(
                status="stale",
                payload=payload,
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                slug_id=slug_id,
                observed_at=stale_time.split("T")[0],
                freshness_status="stale"
            )
        elif status == "unavailable":
            return self._build_result(
                status="unavailable",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                slug_id=slug_id,
                freshness_status="unavailable"
            )
        elif status == "denied":
            return self._build_result(
                status="denied",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                slug_id=slug_id,
                freshness_status="unavailable"
            )
        elif status == "timeout":
            return self._build_result(
                status="timeout",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                slug_id=slug_id,
                freshness_status="unavailable"
            )
        else: # error
            return self._build_result(
                status="error",
                payload={},
                farm_id=farm_id,
                retrieved_at=retrieved_at,
                slug_id=slug_id,
                freshness_status="unavailable"
            )

    def _build_result(
        self,
        status: str,
        payload: Dict[str, Any],
        farm_id: Optional[str],
        retrieved_at: str,
        slug_id: str,
        observed_at: Optional[str] = None,
        freshness_status: Optional[str] = None,
        missing_fields: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Constructs a ConnectorResult dict conforming to schemas."""
        evidence_id = "res_benchmark_ams"
        
        if not freshness_status:
            if status == "success":
                freshness_status = "fresh"
            elif status == "stale":
                freshness_status = "stale"
            else:
                freshness_status = "unavailable"
                
        live_mode = os.environ.get("HARVESTAMP_AMS_SHADOW_LIVE") == "1"
        source_name = "USDA AMS MyMarketNews API (live)" if live_mode else "USDA AMS MyMarketNews Connector (offline mock)"
        connector_mode = "live" if live_mode else "offline_mock"
        
        api_key = os.environ.get("HARVESTAMP_AMS_API_KEY")
        
        result = {
            "result_id": evidence_id,
            "source_id": "DS-011",
            "retrieved_at": retrieved_at,
            "freshness_status": freshness_status,
            "trust_tier": "T1 Official / primary",
            "privacy_class": "Public",
            "payload": payload,
            "evidence_reference": f"ams_market_news_shadow_{farm_id or 'unknown'}",
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

    def _get_mock_payload(self, slug_id: str) -> Dict[str, Any]:
        """Returns mock AMS payload dynamically generated from config mapping."""
        config = self._load_report_config(slug_id)
        reports = {}
        if config and "commodity_map" in config:
            for key, val in config["commodity_map"].items():
                if key == "tomatoes":
                    reports[key] = {
                        "regional_wholesale_price_per_lb": 2.40,
                        "market_tone": "steady",
                        "commodity_name": val
                    }
                elif key == "salad_mix":
                    reports[key] = {
                        "regional_wholesale_price_per_lb": 3.80,
                        "market_tone": "strong",
                        "commodity_name": val
                    }
                else:
                    reports[key] = {
                        "regional_wholesale_price_per_lb": 1.50,
                        "market_tone": "stable",
                        "commodity_name": val
                    }
        else:
            # Fallback if no config matching slug_id is loaded
            reports = {
                "tomatoes": {
                    "regional_wholesale_price_per_lb": 2.40,
                    "market_tone": "steady",
                    "commodity_name": "TOMATOES"
                },
                "salad_mix": {
                    "regional_wholesale_price_per_lb": 3.80,
                    "market_tone": "strong",
                    "commodity_name": "SALAD MIX"
                }
            }
        return {"reports": reports}
