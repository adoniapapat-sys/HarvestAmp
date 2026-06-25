import os
import json
import pytest
import re
from unittest.mock import patch, MagicMock
from harvestamp.connectors.ams_market_news import AMSMarketNewsConnector
from harvestamp.gateway.tools import ToolGateway
from harvestamp.core.evidence import EvidenceBoard
from harvestamp.agents.specialists import MarketAgent
from harvestamp.workflows.supervisor import Supervisor
from harvestamp.core.schemas import validate_by_name
from tests.test_scenarios import load_scenario_context

def test_ams_connector_mock_success():
    """Verify offline mock success ConnectorResult and validation."""
    connector = AMSMarketNewsConnector()
    res = connector.fetch_market_report(slug_id="2281", farm_id="GBO_DIRECT_001")
    
    # 1. Output must conform to ConnectorResult schema
    valid, errs = validate_by_name(res, "connector_result")
    assert valid, f"Connector result validation failed: {errs}"
    
    # 2. Output must contain all required SourceMetadata fields and expected labels
    assert res["source_id"] == "DS-011"
    assert res["source_name"] == "USDA AMS MyMarketNews Connector (offline mock)"
    assert res["source_type"] == "api"
    assert res["trust_tier"] == "T1 Official / primary"
    assert res["freshness_status"] == "fresh"
    assert res["privacy_class"] == "Public"
    assert res["farm_id"] == "GBO_DIRECT_001"
    assert res["authorization_status"] == "authorized"
    assert res["status"] == "success"
    assert res["connector_mode"] == "offline_mock"
    assert "reports" in res["payload"]
    assert "tomatoes" in res["payload"]["reports"]
    assert res["payload"]["reports"]["tomatoes"]["regional_wholesale_price_per_lb"] == 2.40
    assert "salad_mix" in res["payload"]["reports"]
    assert res["payload"]["reports"]["salad_mix"]["regional_wholesale_price_per_lb"] == 3.80
    assert res["result_id"] == "res_benchmark_ams"

def test_ams_connector_mock_statuses():
    """Verify different simulated statuses return correct ConnectorResult structure."""
    connector = AMSMarketNewsConnector()
    
    for status in ["stale", "unavailable", "denied", "timeout", "error"]:
        res = connector.fetch_market_report(
            slug_id="2281",
            farm_id="GBO_DIRECT_001",
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
    """Verify that ToolGateway runs AMS connector in shadow mode and records to EvidenceBoard."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:marketdata_tool"}
    observations = {
        "benchmarks": {
            "ams_market_reports": {
                "evidence_id": "res_benchmark_ams",
                "source_id": "DS-011",
                "timestamp": "2026-06-22T08:00:00-05:00",
                "trust_tier": "T1 Official / primary",
                "freshness_status": "fresh",
                "privacy_class": "Public",
                "reports": {
                    "tomatoes": {
                        "regional_wholesale_price_per_lb": 2.40,
                        "market_tone": "steady"
                    },
                    "salad_mix": {
                        "regional_wholesale_price_per_lb": 3.80,
                        "market_tone": "strong"
                    }
                }
            }
        }
    }
    
    res = gateway.get_market_report(
        capability_grant=capability_grant,
        requesting_farm_id="GBO_DIRECT_001",
        target_farm_id="GBO_DIRECT_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Assert result is from offline mock connector since live mode is off
    assert res["source_name"] == "USDA AMS MyMarketNews Connector (offline mock)"
    assert res["connector_mode"] == "offline_mock"
    assert res["fallback_used"] is False
    assert "reports" in res["payload"]
    
    # Assert recorded evidence is on EvidenceBoard
    ev = evidence_board.get_evidence("res_benchmark_ams")
    assert ev is not None
    assert ev["source_name"] == "USDA AMS MyMarketNews Connector (offline mock)"
    assert ev["connector_mode"] == "offline_mock"

def test_gateway_shadow_mediation_fallback():
    """Verify fallback to local fixture when mock connector returns error."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:marketdata_tool"}
    observations = {
        "ams_mock_status": "unavailable",
        "benchmarks": {
            "ams_market_reports": {
                "evidence_id": "res_benchmark_ams",
                "source_id": "DS-011",
                "timestamp": "2026-06-22T08:00:00-05:00",
                "trust_tier": "T1 Official / primary",
                "freshness_status": "fresh",
                "privacy_class": "Public",
                "reports": {
                    "tomatoes": {
                        "regional_wholesale_price_per_lb": 2.40,
                        "market_tone": "steady"
                    },
                    "salad_mix": {
                        "regional_wholesale_price_per_lb": 3.80,
                        "market_tone": "strong"
                    }
                }
            }
        }
    }
    
    res = gateway.get_market_report(
        capability_grant=capability_grant,
        requesting_farm_id="GBO_DIRECT_001",
        target_farm_id="GBO_DIRECT_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Should fall back
    assert res["source_name"] == "Local AMS Market Fixture Fallback"
    assert res["connector_mode"] == "fixture_fallback"
    assert res["fallback_used"] is True
    assert res["fallback_reason"] == "unavailable"
    assert res["payload"]["reports"]["tomatoes"]["regional_wholesale_price_per_lb"] == 2.40
    
    # Assert evidence is logged as fallback
    ev = evidence_board.get_evidence("res_benchmark_ams")
    assert ev is not None
    assert ev["source_name"] == "Local AMS Market Fixture Fallback"
    assert ev["connector_mode"] == "fixture_fallback"

def test_isolation():
    """Verify that specialists or workflows do not directly import the connector."""
    for path in ["harvestamp/agents/specialists.py", "harvestamp/workflows/supervisor.py"]:
        with open(path, "r") as f:
            content = f.read()
            assert "AMSMarketNewsConnector" not in content, f"Direct import/reference of AMSMarketNewsConnector found in {path}"

def test_exception_scrubbing():
    """Verify exception scrubbing for AMSMarketNewsConnector."""
    import urllib.error
    secret_key = "my_secret_ams_key_xyz_789"
    url_with_key = f"https://mymarketnews.ams.usda.gov/services/v1.1/reports/2281?api_key={secret_key}"
    
    err = urllib.error.HTTPError(
        url=url_with_key,
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=None
    )
    
    connector = AMSMarketNewsConnector()
    scrubbed_err = connector._scrub_exception(err, secret_key)
    
    # Attributes and string representation must be redacted
    assert secret_key not in getattr(scrubbed_err, "url", "")
    assert "mymarketnews.ams.usda.gov" not in getattr(scrubbed_err, "url", "")
    assert "[REDACTED_URL]" in getattr(scrubbed_err, "url", "")
    assert secret_key not in str(scrubbed_err)
    assert url_with_key not in str(scrubbed_err)

def test_live_shadow_mode_credential_scrubbing():
    """Verify that credentials and full URLs never leak into results, exceptions, or audit logs."""
    secret_key = "test_ams_api_key_456"
    url_with_key = f"https://mymarketnews.ams.usda.gov/services/v1.1/reports/2281?api_key={secret_key}"
    
    # Patch urllib to return HTTPError containing credentials
    import urllib.request
    import urllib.error
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url=url_with_key,
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None
        )
        
        with patch.dict(os.environ, {
            "HARVESTAMP_AMS_SHADOW_LIVE": "1",
            "HARVESTAMP_AMS_API_KEY": secret_key
        }):
            connector = AMSMarketNewsConnector()
            res = connector.fetch_market_report(slug_id="2281", farm_id="GBO_DIRECT_001")
            
            res_str = json.dumps(res)
            
            assert res["status"] == "denied"
            assert secret_key not in res_str
            assert url_with_key not in res_str
            
            # Ensure exceptions/assumptions are redacted
            for assumption in res["assumptions"]:
                assert secret_key not in assumption
                assert "mymarketnews.ams.usda.gov" not in assumption
                assert "api_key=" not in assumption

            # Verify Supervisor weekly plan execution doesn't leak credentials
            scen, farm, obs = load_scenario_context("GBO-002")
            from harvestamp.audit.logger import AuditLogger
            logger = AuditLogger()
            supervisor = Supervisor(audit_logger=logger)
            
            action_pack = supervisor.run_workflow(
                farm_profile=farm,
                user_id=scen["user_id"],
                user_role=scen["user_role"],
                prompt=scen["prompt"],
                observations=obs
            )
            
            ap_str = json.dumps(action_pack)
            assert secret_key not in ap_str
            assert url_with_key not in ap_str
            assert "mymarketnews.ams.usda.gov" not in ap_str
            assert "api_key=" not in ap_str
            
            # Audit logs check
            for event in logger.list_events():
                log_str = str(event)
                assert secret_key not in log_str
                assert url_with_key not in log_str

def test_gbo_weekly_plan_integration():
    """Verify that Green Basket Organics weekly plan incorporates AMS context as regional context only."""
    scen, farm, obs = load_scenario_context("GBO-002")
    supervisor = Supervisor()
    
    # We want to run with GBO_DIRECT_001 weekly plan
    # GBO-002 uses GBO_DIRECT_001 farm, prompt is: "Review Saturday farmers market pack list"
    action_pack = supervisor.run_workflow(
        farm_profile=farm,
        user_id=scen["user_id"],
        user_role=scen["user_role"],
        prompt=scen["prompt"],
        observations=obs
    )
    
    print("\nDEBUG ACTION_PACK RECOMMENDATIONS:", action_pack["recommendations"])
    print("\nDEBUG ACTION_PACK EVIDENCE SUMMARY:", action_pack["evidence_summary"])
    
    # Verify recommendations/findings contain the regional warning and evidence IDs
    evidence_ids = []
    found_ams = False
    decision_anchor_warned = False
    
    for rec in action_pack["recommendations"]:
        if "res_benchmark_ams" in rec.get("evidence_ids", []):
            evidence_ids.append("res_benchmark_ams")
            
        desc = rec.get("description", "")
        if "USDA AMS regional produce market report context" in desc:
            found_ams = True
        if "Green Basket’s CSA commitments, restaurant orders, and farm-specific sales records remain the decision anchor." in desc:
            decision_anchor_warned = True
            
    assert "res_benchmark_ams" in [ev["evidence_id"] for ev in action_pack["evidence_summary"]]
    
    # Check that it appears in recommendations as regional context
    found_in_recommendations = False
    for rec in action_pack["recommendations"]:
        if "res_benchmark_ams" in rec.get("evidence_ids", []):
            summary = rec.get("summary", "")
            if "USDA AMS regional produce market report context" in summary:
                found_in_recommendations = True
                assert "Green Basket’s CSA commitments, restaurant orders, and farm-specific sales records remain the decision anchor." in summary
                # Ensure no final price changes or buyer-facing messages are drafted
                assert "price change recommended" not in summary.lower()
                assert "send message" not in summary.lower()
                
                # Verify that human review is not required for this internal pack list
                hr_rec = rec["human_review_status"]
                assert not hr_rec["required"]
                assert hr_rec["review_type"] == "none"
                assert hr_rec["status"] == "review_not_required"
                assert hr_rec["reason"] == []
                assert hr_rec["approval_required_before"] == []

    assert found_in_recommendations, "AMS context not found in recommendations"
    
    # Verify overall human review is not required for this task with no external actions
    hr_overall = action_pack["human_review_status"]
    assert not hr_overall["required"]
    assert hr_overall["review_type"] == "none"
    assert hr_overall["status"] == "review_not_required"
    assert hr_overall["reason"] == []
    assert hr_overall["approval_required_before"] == []

def test_pvf_exclusion():
    """Confirm PVF-002 remains fuel-focused and does NOT contain AMS."""
    scen, farm, obs = load_scenario_context("PVF-002")
    supervisor = Supervisor()
    
    action_pack = supervisor.run_workflow(
        farm_profile=farm,
        user_id=scen["user_id"],
        user_role=scen["user_role"],
        prompt=scen["prompt"],
        observations=obs
    )
    
    ap_str = json.dumps(action_pack)
    assert "res_benchmark_ams" not in ap_str
    assert "USDA AMS" not in ap_str
    assert "MyMarketNews" not in ap_str
    assert "market_report_data" not in ap_str
