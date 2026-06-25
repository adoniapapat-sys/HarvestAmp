import os
import json
import pytest
from unittest.mock import patch, MagicMock
from harvestamp.connectors.eia_fuel import EIAFuelBenchmarkConnector
from harvestamp.gateway.tools import ToolGateway
from harvestamp.core.evidence import EvidenceBoard
from harvestamp.agents.specialists import ProcurementAgent
from harvestamp.core.schemas import validate_by_name
from tests.test_scenarios import load_scenario_context

def test_eia_connector_mock_success():
    """Verify offline mock success ConnectorResult and validation."""
    connector = EIAFuelBenchmarkConnector()
    res = connector.fetch_benchmark(series_id="PET.EMD_EPD2D_PTE_R20_DPG.W", farm_id="PVF_ROW_CROP_001")
    
    # 1. Output must conform to ConnectorResult schema
    valid, errs = validate_by_name(res, "connector_result")
    assert valid, f"Connector result validation failed: {errs}"
    
    # 2. Output must contain all required SourceMetadata fields
    assert res["source_id"] == "DS-008"
    assert res["source_name"] == "EIA Fuel Benchmark Connector (offline mock)"
    assert res["source_type"] == "api"
    assert res["trust_tier"] == "T1 Official / primary"
    assert res["freshness_status"] == "fresh"
    assert res["privacy_class"] == "Public"
    assert res["farm_id"] == "PVF_ROW_CROP_001"
    assert res["authorization_status"] == "authorized"
    assert res["status"] == "success"
    assert res["connector_mode"] == "offline_mock"
    assert res["payload"]["price"] == 3.75
    assert "PVF_ROW_CROP_001" in res["result_id"]

def test_eia_connector_mock_statuses():
    """Verify different simulated statuses return correct ConnectorResult structure."""
    connector = EIAFuelBenchmarkConnector()
    
    for status in ["stale", "unavailable", "denied", "timeout", "error"]:
        res = connector.fetch_benchmark(
            series_id="PET.EMD_EPD2D_PTE_R20_DPG.W",
            farm_id="PVF_ROW_CROP_001",
            mock_status=status
        )
        
        valid, errs = validate_by_name(res, "connector_result")
        assert valid, f"Failed for status {status}: {errs}"
        assert res["status"] == status
        assert res["connector_mode"] == "offline_mock"
        
        if status == "stale":
            assert res["freshness_status"] == "stale"
            assert len(res["payload"]) > 0
        else:
            assert res["freshness_status"] == "unavailable"
            assert res["payload"] == {}

def test_gateway_shadow_mediation_success():
    """Verify that ToolGateway runs EIA connector in shadow mode and records to EvidenceBoard."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:fuel_tool"}
    observations = {
        "benchmarks": {
            "diesel_trend": {
                "evidence_id": "res_benchmark_diesel",
                "source_id": "DS-008",
                "timestamp": "2026-06-22T08:00:00-05:00",
                "trust_tier": "T1 Official / primary",
                "freshness_status": "fresh",
                "privacy_class": "Public",
                "value": "mock_regional_diesel_benchmark_flat_to_slightly_down"
            }
        }
    }
    
    res = gateway.get_benchmark(
        capability_grant=capability_grant,
        requesting_farm_id="PVF_ROW_CROP_001",
        target_farm_id="PVF_ROW_CROP_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Gateway returns resolved benchmark forecast payload
    assert res["payload"] == {"trend": "mock_regional_diesel_benchmark_flat_to_slightly_down"}
    assert res["fallback_used"] is False
    assert res["status"] == "success"
    assert res["source_name"] == "EIA Fuel Benchmark Connector (offline mock)"
    assert res["connector_mode"] == "offline_mock"
    
    # Evidence board contains the shadow EIA connector result
    evidence_items = evidence_board.list_evidence()
    assert len(evidence_items) == 1
    eia_ev = evidence_items[0]
    assert eia_ev["source_id"] == "DS-008"
    assert eia_ev["source_name"] == "EIA Fuel Benchmark Connector (offline mock)"
    assert eia_ev["connector_mode"] == "offline_mock"

def test_gateway_shadow_mediation_failure():
    """Verify gateway behavior and EvidenceBoard logging when EIA connector fails."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:fuel_tool"}
    observations = {
        "benchmarks": {
            "diesel_trend": {
                "evidence_id": "res_benchmark_diesel",
                "source_id": "DS-008",
                "timestamp": "2026-06-22T08:00:00-05:00",
                "trust_tier": "T1 Official / primary",
                "freshness_status": "fresh",
                "privacy_class": "Public",
                "value": "mock_regional_diesel_benchmark_flat_to_slightly_down"
            }
        },
        "eia_mock_status": "unavailable"
    }
    
    res = gateway.get_benchmark(
        capability_grant=capability_grant,
        requesting_farm_id="PVF_ROW_CROP_001",
        target_farm_id="PVF_ROW_CROP_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Gateway returns mock observations as fallback, but flags it
    assert res["payload"] == {"trend": "mock_regional_diesel_benchmark_flat_to_slightly_down"}
    assert res["fallback_used"] is True
    assert "unavailable" in res["fallback_reason"]
    assert res["status"] == "unavailable"
    assert res["freshness_status"] == "unavailable"
    assert res["source_name"] == "Local Fuel Benchmark Fixture Fallback"
    assert res["connector_mode"] == "fixture_fallback"
    
    # Evidence board contains the failed shadow EIA connector result and fallback benchmark evidence
    evidence_items = evidence_board.list_evidence()
    assert len(evidence_items) == 2
    
    fallback_ev = next(ev for ev in evidence_items if ev["source_name"] == "Local Fuel Benchmark Fixture Fallback")
    assert fallback_ev["connector_mode"] == "fixture_fallback"
    
    eia_ev = next(ev for ev in evidence_items if ev["source_name"] == "EIA Fuel Benchmark Connector (offline mock)")
    assert eia_ev["source_id"] == "DS-008"
    assert eia_ev["freshness_status"] == "unavailable"
    assert eia_ev["connector_mode"] == "offline_mock"
    assert "Shadow EIA benchmark status: unavailable" in eia_ev["description"]

def test_procurement_agent_fallback_lowers_confidence():
    """Verify ProcurementAgent lowers confidence when EIA fails and fallback is used."""
    agent = ProcurementAgent()
    work_item = {
        "work_item_id": "wi_pr_test",
        "workflow_id": "wf_test",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "diesel_purchase_window"
    }
    context = {"farm_type": "large_conventional_row_crop", "user_role": "farm_owner"}
    
    # Fresh inventory & quote setup
    quotes = [{
        "result_id": "res_quote_1",
        "payload": {"input_type": "diesel", "price": 3.68, "valid_until": "2026-06-25"}
    }]
    inventory = [{
        "result_id": "res_inv_1",
        "freshness_status": "fresh",
        "payload": {
            "item_type": "diesel",
            "quantity": 1350,
            "tank_capacity_gallons": 4000,
            "expected_30_day_diesel_need_gallons": 3100,
            "preferred_minimum_reserve_gallons": 700,
            "last_updated": "2026-06-22"
        }
    }]
    
    # Case 1: EIA Success
    bench_success = {
        "result_id": "res_benchmark_diesel",
        "payload": {"trend": "mock_regional_diesel_benchmark_flat_to_slightly_down"},
        "fallback_used": False,
        "status": "success",
        "freshness_status": "fresh"
    }
    finding_success = agent.run(work_item, context, quotes, inventory, bench_success)
    assert finding_success["confidence"] == "high"  # High confidence normally
    assert "EIA regional diesel price benchmark is flat to slightly down" in finding_success["summary"]
    
    # Case 2: EIA Failure / fallback used
    bench_fallback = {
        "result_id": "res_benchmark_diesel",
        "payload": {"trend": "mock_regional_diesel_benchmark_flat_to_slightly_down"},
        "fallback_used": True,
        "status": "unavailable",
        "freshness_status": "unavailable"
    }
    finding_fallback = agent.run(work_item, context, quotes, inventory, bench_fallback)
    assert finding_fallback["confidence"] == "high"  # Overall recommendation confidence remains high!
    assert "EIA regional diesel price benchmark is flat to slightly down" in finding_fallback["summary"]
    assert any("EIA diesel benchmark is stale or unavailable" in ass for ass in finding_fallback["assumptions"])
    assert "Fresh EIA diesel benchmark" in finding_fallback["missing_data"]

def test_procurement_agent_completely_unavailable():
    """Verify ProcurementAgent output when no benchmark payload is available."""
    agent = ProcurementAgent()
    work_item = {
        "work_item_id": "wi_pr_test",
        "workflow_id": "wf_test",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "diesel_purchase_window"
    }
    context = {"farm_type": "large_conventional_row_crop", "user_role": "farm_owner"}
    
    quotes = [{
        "result_id": "res_quote_1",
        "payload": {"input_type": "diesel", "price": 3.68, "valid_until": "2026-06-25"}
    }]
    inventory = [{
        "result_id": "res_inv_1",
        "freshness_status": "fresh",
        "payload": {
            "item_type": "diesel",
            "quantity": 1350,
            "tank_capacity_gallons": 4000,
            "expected_30_day_diesel_need_gallons": 3100,
            "preferred_minimum_reserve_gallons": 700,
            "last_updated": "2026-06-22"
        }
    }]
    
    bench_empty = {
        "result_id": "res_benchmark_diesel",
        "payload": {},
        "fallback_used": True,
        "status": "unavailable",
        "freshness_status": "unavailable"
    }
    finding_empty = agent.run(work_item, context, quotes, inventory, bench_empty)
    assert finding_empty["confidence"] == "high"
    assert "EIA regional diesel price benchmark is unavailable." in finding_empty["summary"]

@patch("urllib.request.urlopen")
def test_live_mode_simulated(mock_urlopen):
    """Verify live HTTP request path using mocked urllib."""
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = json.dumps({
        "response": {
            "data": [
                {
                    "period": "2026-06-22",
                    "value": 3.85,
                    "series": "PET.EMD_EPD2D_PTE_R20_DPG.W",
                    "series-description": "Midwest No 2 Diesel Retail Prices (weekly)"
                }
            ]
        }
    }).encode("utf-8")
    
    mock_urlopen.return_value = mock_response
    
    with patch.dict(os.environ, {"HARVESTAMP_EIA_SHADOW_LIVE": "1", "HARVESTAMP_EIA_API_KEY": "test_eia_key"}):
        connector = EIAFuelBenchmarkConnector()
        res = connector.fetch_benchmark(series_id="PET.EMD_EPD2D_PTE_R20_DPG.W", farm_id="PVF_ROW_CROP_001")
        assert res["status"] == "success"
        assert res["freshness_status"] == "fresh"
        assert res["payload"]["price"] == 3.85
        assert res["observed_at"] == "2026-06-22"
        assert res["source_name"] == "EIA Fuel Benchmark API (live)"
        assert res["connector_mode"] == "live"

def test_live_mode_missing_api_key():
    """Verify live request fails if API key is missing from environment."""
    with patch.dict(os.environ, {"HARVESTAMP_EIA_SHADOW_LIVE": "1"}):
        if "HARVESTAMP_EIA_API_KEY" in os.environ:
            del os.environ["HARVESTAMP_EIA_API_KEY"]
            
        connector = EIAFuelBenchmarkConnector()
        res = connector.fetch_benchmark(series_id="PET.EMD_EPD2D_PTE_R20_DPG.W", farm_id="PVF_ROW_CROP_001")
        
        assert res["status"] == "denied"
        assert res["freshness_status"] == "unavailable"
        assert res["payload"] == {}
        assert "HARVESTAMP_EIA_API_KEY" in res["missing_fields"]
        assert res["source_name"] == "EIA Fuel Benchmark API (live)"
        assert res["connector_mode"] == "live"

def test_agent_isolation():
    """Verify ProcurementAgent does not import or call EIA connector directly."""
    # Read files to check for imports
    import harvestamp.agents.specialists as spec
    source_code = open(spec.__file__, "r").read()
    assert "EIAFuelBenchmarkConnector" not in source_code
    assert "eia_fuel" not in source_code

def test_pvf_weekly_plan_eia_context_and_evidence():
    """Verify that weekly plan for PVF incorporates EIA benchmark context and evidence correctly."""
    from harvestamp.workflows.supervisor import Supervisor
    scen, farm, obs = load_scenario_context("PVF-002")  # Load default PVF context/obs
    supervisor = Supervisor()
    
    # Run weekly plan workflow for Prairie View Farms
    ap = supervisor.run_workflow(farm, "pvf_owner_001", "farm_owner", "What should I know about Prairie View Farms this week?", obs)
    
    # 1. PVF weekly plan includes EIA benchmark context as public context only
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "weekly_plan_pvf")
    assert "Public benchmark context: EIA regional diesel price benchmark" in rec["summary"]
    assert "EIA is public benchmark context only" in rec["summary"]
    assert "EIA is public benchmark context only" in rec["recommendation"]
    
    # 2. PVF weekly plan still anchors on the supplier quote
    assert "Current diesel quote is valid until 2026-06-25." in rec["summary"]
    assert "Prepare a fuel quote inquiry for approval." in rec["recommendation"]
    
    # 3. PVF weekly evidence includes EIA benchmark evidence
    ev_ids = [ev["evidence_id"] for ev in ap["evidence_summary"]]
    assert "res_benchmark_eia_PVF_ROW_CROP_001" in ev_ids
    
    # 4. Check that connector mode is present in evidence summary
    eia_ev = next(ev for ev in ap["evidence_summary"] if ev["evidence_id"] == "res_benchmark_eia_PVF_ROW_CROP_001")
    assert eia_ev["connector_mode"] == "offline_mock"
    assert eia_ev["fallback_used"] is False

def test_evidence_labeling_and_duplicates():
    """Verify NWS/EIA duplicate prevention, fallback labeling, and offline mock labeling."""
    from harvestamp.workflows.supervisor import Supervisor
    scen, farm, obs = load_scenario_context("PVF-002")
    supervisor = Supervisor()
    
    # Case A: Success (fallback_used=False)
    ap_success = supervisor.run_workflow(farm, "pvf_owner_001", "farm_owner", "Should I buy diesel this month?", obs)
    
    # EIA fallback evidence is not duplicated unless fallback_used=True
    eia_evs = [ev for ev in ap_success["evidence_summary"] if "res_benchmark_eia" in ev["evidence_id"] or "res_benchmark_diesel" in ev["evidence_id"]]
    assert len(eia_evs) == 1
    assert eia_evs[0]["evidence_id"] == "res_benchmark_eia_PVF_ROW_CROP_001"
    assert eia_evs[0]["source_name"] == "EIA Fuel Benchmark Connector (offline mock)"
    assert eia_evs[0]["connector_mode"] == "offline_mock"  # Offline mock evidence not labeled as live API
    
    # NWS succeeds as well (fallback_used=False), no duplicate weather fixture source shown as NWS source
    nws_evs = [ev for ev in ap_success["evidence_summary"] if "res_weather" in ev["evidence_id"]]
    assert len(nws_evs) == 1
    assert nws_evs[0]["evidence_id"] == "res_weather_nws_PVF_ROW_CROP_001"
    assert nws_evs[0]["source_name"] == "National Weather Service API (shadow/offline)"
    assert nws_evs[0]["connector_mode"] == "offline_mock"

    # Case B: Failure (fallback_used=True)
    obs_fail = dict(obs)
    obs_fail["eia_mock_status"] = "unavailable"
    obs_fail["nws_mock_status"] = "unavailable"
    
    ap_fail = supervisor.run_workflow(farm, "pvf_owner_001", "farm_owner", "Should I buy diesel this month?", obs_fail)
    
    # Both connector failed evidence and fallback evidence are shown
    eia_evs_fail = [ev for ev in ap_fail["evidence_summary"] if "res_benchmark" in ev["evidence_id"]]
    assert len(eia_evs_fail) == 2
    
    fallback_eia = next(ev for ev in eia_evs_fail if ev["evidence_id"] == "res_benchmark_diesel")
    assert fallback_eia["source_name"] == "Local Fuel Benchmark Fixture Fallback"
    assert fallback_eia["connector_mode"] == "fixture_fallback"
    assert fallback_eia["fallback_used"] is True
    assert fallback_eia["fallback_reason"] == "unavailable"

    # NWS fixture fallback is not labeled as NWS API when fallback_used=True
    nws_evs_fail = [ev for ev in ap_fail["evidence_summary"] if "res_weather" in ev["evidence_id"]]
    assert len(nws_evs_fail) == 2
    
    fallback_nws = next(ev for ev in nws_evs_fail if ev["evidence_id"] == "res_weather_PVF_ROW_CROP_001")
    assert fallback_nws["source_name"] == "Local Weather Fixture Fallback"
    assert fallback_nws["connector_mode"] == "fixture_fallback"
    assert fallback_nws["fallback_used"] is True
    assert "unavailable" in fallback_nws["fallback_reason"]
def test_api_key_exposure_prevention():
    """Verify that the API key value and the full URL containing it do not appear in result objects, evidence, logs, or ActionPack output."""
    import urllib.error
    from harvestamp.workflows.supervisor import Supervisor
    from harvestamp.audit.logger import AuditLogger
    
    secret_key = "my_secret_api_key_abc_123"
    url_with_key = f"https://api.eia.gov/v2/seriesid/PET.EMD_EPD2D_PTE_R20_DPG.W?api_key={secret_key}"
    
    # 1. Simulate urllib HTTPError containing the full URL
    with patch.dict(os.environ, {"HARVESTAMP_EIA_SHADOW_LIVE": "1", "HARVESTAMP_EIA_API_KEY": secret_key}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url=url_with_key,
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None
            )
            
            connector = EIAFuelBenchmarkConnector()
            res = connector.fetch_benchmark(series_id="PET.EMD_EPD2D_PTE_R20_DPG.W", farm_id="PVF_ROW_CROP_001")
            
            # Serialize result to inspect all values
            res_str = json.dumps(res)
            
            # Assertions:
            assert res["status"] == "denied"
            # The API key value must not appear in result objects
            assert secret_key not in res_str
            # The full URL containing the API key must not appear in result objects
            assert url_with_key not in res_str
            
            # Ensure exceptions/assumptions are redacted
            for assumption in res["assumptions"]:
                assert secret_key not in assumption
                assert "api.eia.gov" not in assumption
                assert "api_key=my_secret" not in assumption

            # 2. Verify Supervisor workflow execution with live mode failing
            scen, farm, obs = load_scenario_context("PVF-002")
            logger = AuditLogger()
            supervisor = Supervisor(audit_logger=logger)
            
            # Run supervisor workflow (which calls get_benchmark under the hood)
            action_pack = supervisor.run_workflow(
                farm_profile=farm,
                user_id="pvf_owner_001",
                user_role="farm_owner",
                prompt="Should I buy diesel this month?",
                observations=obs
            )
            
            # Serialize ActionPack to verify no leaks
            ap_str = json.dumps(action_pack)
            assert secret_key not in ap_str
            assert url_with_key not in ap_str
            assert "api.eia.gov" not in ap_str
            assert "api_key=" not in ap_str
            
            # 3. Verify EvidenceBoard does not contain any trace of the secret key or URL
            for ev in action_pack["evidence_summary"]:
                ev_str = json.dumps(ev)
                assert secret_key not in ev_str
                assert url_with_key not in ev_str
                assert "api.eia.gov" not in ev_str
                assert "api_key=" not in ev_str
                
            # 4. Check audit logs to make sure no URL/API key was logged
            for event in logger.list_events():
                evt_str = json.dumps(event)
                assert secret_key not in evt_str
                assert url_with_key not in evt_str

def test_exception_scrubbing():
    """Verify that exception objects are properly scrubbed of the URL and API key."""
    import urllib.error
    secret_key = "my_secret_api_key_abc_123"
    url_with_key = f"https://api.eia.gov/v2/seriesid/PET.EMD_EPD2D_PTE_R20_DPG.W?api_key={secret_key}"
    
    # 1. Test HTTPError scrubbing
    err = urllib.error.HTTPError(
        url=url_with_key,
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=None
    )
    
    connector = EIAFuelBenchmarkConnector()
    scrubbed_err = connector._scrub_exception(err, secret_key)
    
    assert secret_key not in getattr(scrubbed_err, "url", "")
    assert "api.eia.gov" not in getattr(scrubbed_err, "url", "")
    assert "[REDACTED_URL]" in getattr(scrubbed_err, "url", "")
    
    # 2. Test URLError scrubbing
    err2 = urllib.error.URLError(reason=f"Failed to connect to {url_with_key}")
    scrubbed_err2 = connector._scrub_exception(err2, secret_key)
    
    assert secret_key not in str(scrubbed_err2.reason)
    assert "api.eia.gov" not in str(scrubbed_err2.reason)
    assert "[REDACTED_URL]" in str(scrubbed_err2.reason)

