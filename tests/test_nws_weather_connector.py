import os
import json
import pytest
from unittest.mock import patch, MagicMock
from harvestamp.connectors.nws_weather import NWSWeatherConnector
from harvestamp.gateway.tools import ToolGateway
from harvestamp.core.evidence import EvidenceBoard
from harvestamp.agents.specialists import WeatherAgent
from harvestamp.core.schemas import validate_by_name

def test_nws_connector_mock_success():
    """Verify offline mock success ConnectorResult and validation."""
    connector = NWSWeatherConnector()
    res = connector.fetch_weather(latitude=40.1164123, longitude=-88.2434123, farm_id="PVF_ROW_CROP_001")
    
    # 1. Output must conform to ConnectorResult schema
    valid, errs = validate_by_name(res, "connector_result")
    assert valid, f"Connector result validation failed: {errs}"
    
    # 2. Output must contain all required SourceMetadata fields
    assert res["source_id"] == "DS-006"
    assert res["source_name"] == "National Weather Service API (shadow/offline)"
    assert res["source_type"] == "api"
    assert res["connector_mode"] == "offline_mock"
    assert res["trust_tier"] == "T1 Official / primary"
    assert res["freshness_status"] == "fresh"
    assert res["privacy_class"] == "Public"
    assert res["farm_id"] == "PVF_ROW_CROP_001"
    assert res["authorization_status"] == "authorized"
    assert res["status"] == "success"
    assert len(res["payload"]["periods"]) > 0
    
    assert "PVF_ROW_CROP_001" in res["result_id"]

def test_nws_connector_mock_statuses():
    """Verify different simulated statuses return correct ConnectorResult structure."""
    connector = NWSWeatherConnector()
    
    for status in ["stale", "unavailable", "denied", "timeout", "error"]:
        res = connector.fetch_weather(
            latitude=40.1164,
            longitude=-88.2434,
            farm_id="PVF_ROW_CROP_001",
            mock_status=status
        )
        
        valid, errs = validate_by_name(res, "connector_result")
        assert valid, f"Failed for status {status}: {errs}"
        assert res["status"] == status
        
        if status == "stale":
            assert res["freshness_status"] == "stale"
            assert len(res["payload"]) > 0
        else:
            assert res["freshness_status"] == "unavailable"
            assert res["payload"] == {}

def test_gateway_shadow_mediation_success():
    """Verify that ToolGateway runs NWS connector in shadow mode and records to EvidenceBoard."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:weather_tool"}
    observations = {"weather": {"PVF_ROW_CROP_001": {"forecast": {"monday": "sunny"}}}}
    
    res = gateway.get_weather(
        capability_grant=capability_grant,
        requesting_farm_id="PVF_ROW_CROP_001",
        target_farm_id="PVF_ROW_CROP_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Gateway returns the mock observations forecast payload for actual agent usage
    assert res["payload"] == {"monday": "sunny"}
    assert res["fallback_used"] is False
    assert res["status"] == "success"
    assert res["source_name"] == "National Weather Service API (shadow/offline)"
    assert res["connector_mode"] == "offline_mock"
    
    # Evidence board contains the shadow NWS connector result
    evidence_items = evidence_board.list_evidence()
    assert len(evidence_items) == 1
    nws_ev = evidence_items[0]
    assert nws_ev["source_id"] == "DS-006"
    assert nws_ev["source_name"] == "National Weather Service API (shadow/offline)"
    assert nws_ev["connector_mode"] == "offline_mock"

def test_gateway_shadow_mediation_failure():
    """Verify gateway behavior and EvidenceBoard logging when NWS connector fails."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:weather_tool"}
    # Observations containing mock fallback weather
    observations = {
        "weather": {"PVF_ROW_CROP_001": {"forecast": {"monday": "sunny"}}},
        "nws_mock_status": "unavailable"
    }
    
    res = gateway.get_weather(
        capability_grant=capability_grant,
        requesting_farm_id="PVF_ROW_CROP_001",
        target_farm_id="PVF_ROW_CROP_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Gateway returns mock observations as fallback, but flags it
    assert res["payload"] == {"monday": "sunny"}
    assert res["fallback_used"] is True
    assert "unavailable" in res["fallback_reason"]
    assert res["status"] == "unavailable"
    assert res["freshness_status"] == "unavailable"
    assert res["source_name"] == "Local Weather Fixture Fallback"
    assert res["connector_mode"] == "fixture_fallback"
    
    # Evidence board contains the failed shadow NWS connector result and the fallback weather evidence
    evidence_items = evidence_board.list_evidence()
    assert len(evidence_items) == 2
    
    fallback_ev = next(ev for ev in evidence_items if ev["source_name"] == "Local Weather Fixture Fallback")
    assert fallback_ev["connector_mode"] == "fixture_fallback"
    
    nws_ev = next(ev for ev in evidence_items if ev["source_name"] == "National Weather Service API (shadow/offline)")
    assert nws_ev["source_id"] == "DS-006"
    assert nws_ev["freshness_status"] == "unavailable"
    assert nws_ev["connector_mode"] == "offline_mock"
    assert "status: unavailable" in nws_ev["description"]

def test_weather_agent_fallback_lowers_confidence():
    """Verify WeatherAgent lowers confidence when NWS fails and fallback is used."""
    agent = WeatherAgent()
    work_item = {
        "work_item_id": "wi_we_test",
        "workflow_id": "wf_test",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    context = {"farm_type": "large_conventional_row_crop"}
    
    # Case 1: NWS Success
    weather_obs_success = {
        "result_id": "res_weather_PVF_ROW_CROP_001",
        "payload": {"monday": {"fieldwork_window": "good"}},
        "fallback_used": False,
        "status": "success",
        "freshness_status": "fresh"
    }
    finding_success = agent.run(work_item, context, weather_obs_success)
    assert finding_success["confidence"] == "medium"  # Normal confidence for weekly PVF plan
    
    # Case 2: NWS Failure / fallback used
    weather_obs_fallback = {
        "result_id": "res_weather_PVF_ROW_CROP_001",
        "payload": {"monday": {"fieldwork_window": "good"}},
        "fallback_used": True,
        "status": "unavailable",
        "freshness_status": "unavailable"
    }
    finding_fallback = agent.run(work_item, context, weather_obs_fallback)
    assert finding_fallback["confidence"] == "low"  # Confidence lowered to low
    assert "Warning: live weather data was unavailable" in finding_fallback["summary"]
    assert any("cached weather data" in ass for ass in finding_fallback["assumptions"])
    assert "Fresh weather forecast data" in finding_fallback["missing_data"]

def test_weather_agent_completely_unavailable():
    """Verify WeatherAgent output when no forecast payload is available."""
    agent = WeatherAgent()
    work_item = {
        "work_item_id": "wi_we_test",
        "workflow_id": "wf_test",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    context = {"farm_type": "large_conventional_row_crop"}
    
    weather_obs_empty = {
        "result_id": "res_weather_PVF_ROW_CROP_001",
        "payload": {},
        "fallback_used": True,
        "status": "unavailable",
        "freshness_status": "unavailable"
    }
    finding_empty = agent.run(work_item, context, weather_obs_empty)
    assert finding_empty["confidence"] == "low"
    assert "completely unavailable" in finding_empty["summary"]
    assert "Verify current local weather conditions manually" in finding_empty["recommendation"]

@patch("urllib.request.urlopen")
def test_live_mode_simulated(mock_urlopen):
    """Verify live HTTP request path using mocked urllib."""
    # Mock NWS points response
    mock_response1 = MagicMock()
    mock_response1.__enter__.return_value = mock_response1
    mock_response1.read.return_value = json.dumps({
        "properties": {
            "forecast": "https://api.weather.gov/gridpoints/ILX/95,73/forecast"
        }
    }).encode("utf-8")
    
    # Mock NWS forecast response
    mock_response2 = MagicMock()
    mock_response2.__enter__.return_value = mock_response2
    mock_response2.read.return_value = json.dumps({
        "properties": {
            "updateTime": "2026-06-24T12:00:00Z",
            "periods": [
                {"name": "Monday", "temperature": 75, "windSpeed": "10 mph", "detailedForecast": "Sunny."}
            ]
        }
    }).encode("utf-8")
    
    mock_urlopen.side_effect = [mock_response1, mock_response2]
    
    with patch.dict(os.environ, {"HARVESTAMP_NWS_SHADOW_LIVE": "1", "HARVESTAMP_NWS_USER_AGENT": "HarvestAmpTest/0.1"}):
        connector = NWSWeatherConnector()
        res = connector.fetch_weather(latitude=40.1164, longitude=-88.2434, farm_id="PVF_ROW_CROP_001")
        assert res["status"] == "success"
        assert res["freshness_status"] == "fresh"
        assert res["payload"]["periods"][0]["name"] == "Monday"
        assert res["observed_at"] == "2026-06-24T12:00:00Z"
        assert res["source_name"] == "National Weather Service API (live)"
        assert res["connector_mode"] == "live"

def test_live_mode_missing_user_agent():
    """Verify live request fails if User-Agent is missing from environment."""
    with patch.dict(os.environ, {"HARVESTAMP_NWS_SHADOW_LIVE": "1"}):
        if "HARVESTAMP_NWS_USER_AGENT" in os.environ:
            del os.environ["HARVESTAMP_NWS_USER_AGENT"]
            
        connector = NWSWeatherConnector()
        res = connector.fetch_weather(latitude=40.1164, longitude=-88.2434, farm_id="PVF_ROW_CROP_001")
        
        assert res["status"] == "denied"
        assert res["freshness_status"] == "unavailable"
        assert res["payload"] == {}
        assert "User-Agent" in res["missing_fields"]
        assert res["source_name"] == "National Weather Service API (live)"
        assert res["connector_mode"] == "live"

# Skips unless explicitly requested
@pytest.mark.skipif(os.environ.get("HARVESTAMP_NWS_SHADOW_LIVE") != "1", reason="Requires live NWS mode and network")
def test_real_live_nws_call():
    """Real live NWS integration test. Requires live internet and env vars."""
    user_agent = os.environ.get("HARVESTAMP_NWS_USER_AGENT")
    assert user_agent, "Live NWS test requires HARVESTAMP_NWS_USER_AGENT in environment."
    
    connector = NWSWeatherConnector()
    res = connector.fetch_weather(latitude=40.1164, longitude=-88.2434, farm_id="PVF_ROW_CROP_001")
    
    assert res["status"] in ["success", "unavailable", "error"]
