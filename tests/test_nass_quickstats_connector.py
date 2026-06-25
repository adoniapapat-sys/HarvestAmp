import os
import json
import pytest
from unittest.mock import patch, MagicMock
from harvestamp.connectors.nass_quickstats import NASSQuickStatsConnector
from harvestamp.gateway.tools import ToolGateway
from harvestamp.core.evidence import EvidenceBoard
from harvestamp.agents.specialists import MarginAgent
from harvestamp.core.schemas import validate_by_name
from tests.test_scenarios import load_scenario_context

def test_nass_connector_mock_success():
    """Verify offline mock success ConnectorResult and validation."""
    connector = NASSQuickStatsConnector()
    res = connector.fetch_benchmark(commodity="CORN", statisticcat_desc="YIELD", state_alpha="IL", county_name="CHAMPAIGN", farm_id="PVF_ROW_CROP_001")
    
    # 1. Output must conform to ConnectorResult schema
    valid, errs = validate_by_name(res, "connector_result")
    assert valid, f"Connector result validation failed: {errs}"
    
    # 2. Output must contain all required SourceMetadata fields
    assert res["source_id"] == "DS-010"
    assert res["source_name"] == "USDA NASS Quick Stats Connector (offline mock)"
    assert res["source_type"] == "api"
    assert res["trust_tier"] == "T1 Official / primary"
    assert res["freshness_status"] == "fresh"
    assert res["privacy_class"] == "Public"
    assert res["farm_id"] == "PVF_ROW_CROP_001"
    assert res["authorization_status"] == "authorized"
    assert res["status"] == "success"
    assert res["connector_mode"] == "offline_mock"
    assert "crops" in res["payload"]
    assert "corn" in res["payload"]["crops"]
    assert res["payload"]["crops"]["corn"]["yield_county_bushels_per_acre"] == 195.0
    assert "PVF_ROW_CROP_001" in res["result_id"]

def test_nass_connector_mock_statuses():
    """Verify different simulated statuses return correct ConnectorResult structure."""
    connector = NASSQuickStatsConnector()
    
    for status in ["stale", "unavailable", "denied", "timeout", "error"]:
        res = connector.fetch_benchmark(
            commodity="CORN",
            statisticcat_desc="YIELD",
            state_alpha="IL",
            county_name="CHAMPAIGN",
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
    """Verify that ToolGateway runs NASS connector in shadow mode and records to EvidenceBoard."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:crop_benchmark"}
    observations = {
        "benchmarks": {
            "nass_crop_benchmarks": {
                "evidence_id": "res_benchmark_nass",
                "source_id": "DS-010",
                "timestamp": "2026-06-22T08:00:00-05:00",
                "trust_tier": "T1 Official / primary",
                "freshness_status": "fresh",
                "privacy_class": "Public",
                "crops": {
                    "corn": {
                        "yield_county_bushels_per_acre": 195.0,
                        "yield_state_bushels_per_acre": 203.0,
                        "acreage_state_acres": 11200000
                    },
                    "soybeans": {
                        "yield_county_bushels_per_acre": 61.0,
                        "yield_state_bushels_per_acre": 64.0,
                        "acreage_state_acres": 10800000
                    }
                }
            }
        }
    }
    
    res = gateway.get_crop_benchmark(
        capability_grant=capability_grant,
        requesting_farm_id="PVF_ROW_CROP_001",
        target_farm_id="PVF_ROW_CROP_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Gateway returns merged benchmark forecast payload
    assert "corn" in res["payload"]["crops"]
    assert "soybeans" in res["payload"]["crops"]
    assert res["fallback_used"] is False
    assert res["status"] == "success"
    assert res["source_name"] == "USDA NASS Quick Stats Connector (offline mock)"
    assert res["connector_mode"] == "offline_mock"
    
    # Evidence board contains the shadow NASS connector results (corn & soybean queried separately, but merged in description)
    evidence_items = evidence_board.list_evidence()
    assert len(evidence_items) > 0
    nass_ev = next(ev for ev in evidence_items if ev["source_id"] == "DS-010")
    assert nass_ev["source_name"] == "USDA NASS Quick Stats Connector (offline mock)"
    assert nass_ev["connector_mode"] == "offline_mock"

def test_gateway_shadow_mediation_failure():
    """Verify gateway behavior and EvidenceBoard logging when NASS connector fails."""
    gateway = ToolGateway()
    evidence_board = EvidenceBoard()
    
    capability_grant = {"authorized": True, "capability": "capability:crop_benchmark"}
    observations = {
        "benchmarks": {
            "nass_crop_benchmarks": {
                "evidence_id": "res_benchmark_nass",
                "source_id": "DS-010",
                "timestamp": "2026-06-22T08:00:00-05:00",
                "trust_tier": "T1 Official / primary",
                "freshness_status": "fresh",
                "privacy_class": "Public",
                "crops": {
                    "corn": {
                        "yield_county_bushels_per_acre": 195.0,
                        "yield_state_bushels_per_acre": 203.0,
                        "acreage_state_acres": 11200000
                    },
                    "soybeans": {
                        "yield_county_bushels_per_acre": 61.0,
                        "yield_state_bushels_per_acre": 64.0,
                        "acreage_state_acres": 10800000
                    }
                }
            }
        },
        "nass_mock_status": "unavailable"
    }
    
    res = gateway.get_crop_benchmark(
        capability_grant=capability_grant,
        requesting_farm_id="PVF_ROW_CROP_001",
        target_farm_id="PVF_ROW_CROP_001",
        observations=observations,
        evidence_board=evidence_board
    )
    
    # Gateway returns mock observations as fallback, but flags it
    assert "corn" in res["payload"]["crops"]
    assert res["fallback_used"] is True
    assert "unavailable" in res["fallback_reason"]
    assert res["status"] == "unavailable"
    assert res["freshness_status"] == "unavailable"
    assert res["source_name"] == "Local NASS Benchmark Fixture Fallback"
    assert res["connector_mode"] == "fixture_fallback"
    
    # Evidence board contains the failed shadow NASS connector result and fallback benchmark evidence
    evidence_items = evidence_board.list_evidence()
    assert len(evidence_items) >= 2
    
    fallback_nass = next(ev for ev in evidence_items if ev["source_name"] == "Local NASS Benchmark Fixture Fallback")
    assert fallback_nass["connector_mode"] == "fixture_fallback"
    
    nass_ev = next(ev for ev in evidence_items if ev["source_name"] == "USDA NASS Quick Stats Connector (offline mock)")
    assert nass_ev["source_id"] == "DS-010"
    assert nass_ev["freshness_status"] == "unavailable"
    assert nass_ev["connector_mode"] == "offline_mock"
    assert "Shadow NASS crop benchmarks status: unavailable" in nass_ev["description"]

def test_margin_agent_nass_context():
    """Verify MarginAgent uses NASS benchmark as regional context only and doesn't override records."""
    agent = MarginAgent()
    work_item = {
        "work_item_id": "wi_mr_test",
        "workflow_id": "wf_test",
        "farm_id": "PVF_ROW_CROP_001",
        "requesting_user_id": "pvf_owner_001",
        "topic": "weekly_plan_pvf"
    }
    context = {"farm_type": "large_conventional_row_crop", "user_role": "farm_owner"}
    
    crop_benchmark = {
        "result_id": "res_benchmark_nass_PVF_ROW_CROP_001",
        "payload": {
            "crops": {
                "corn": {
                    "yield_county_bushels_per_acre": 195.0,
                    "yield_state_bushels_per_acre": 203.0
                },
                "soybeans": {
                    "yield_county_bushels_per_acre": 61.0,
                    "yield_state_bushels_per_acre": 64.0
                }
            }
        },
        "fallback_used": False,
        "status": "success"
    }
    
    finding = agent.run(work_item, context, crop_benchmark)
    assert finding["confidence"] == "medium"
    assert "USDA NASS county/state benchmark data is included as regional context only" in finding["summary"]
    assert "Corn county yield 195.0 bu/acre" in finding["summary"]
    assert "Soybean county yield 61.0 bu/acre" in finding["summary"]
    assert "Prairie View's farm-specific records remain the decision anchor." in finding["summary"]

def test_agent_isolation():
    """Verify MarginAgent and MarketAgent do not import NASSQuickStatsConnector directly."""
    import harvestamp.agents.specialists as spec
    source_code = open(spec.__file__, "r").read()
    assert "NASSQuickStatsConnector" not in source_code
    assert "nass_quickstats" not in source_code

@patch("urllib.request.urlopen")
def test_live_mode_simulated(mock_urlopen):
    """Verify live HTTP request path using mocked urllib."""
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = json.dumps({
        "data": [
            {
                "year": 2025,
                "Value": "203.0",
                "agg_level_desc": "STATE",
                "unit_desc": "BU / ACRE"
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value = mock_response
    
    with patch.dict(os.environ, {"HARVESTAMP_NASS_SHADOW_LIVE": "1", "HARVESTAMP_NASS_API_KEY": "test_nass_key"}):
        connector = NASSQuickStatsConnector()
        res = connector.fetch_benchmark(commodity="CORN", statisticcat_desc="YIELD", state_alpha="IL", farm_id="PVF_ROW_CROP_001")
        assert res["status"] == "success"
        assert res["freshness_status"] == "fresh"
        assert res["payload"]["crops"]["corn"]["yield_state_bushels_per_acre"] == 203.0
        assert res["observed_at"] == "2025"
        assert res["source_name"] == "USDA NASS Quick Stats API (live)"
        assert res["connector_mode"] == "live"

def test_live_mode_missing_api_key():
    """Verify live request fails if API key is missing from environment."""
    with patch.dict(os.environ, {"HARVESTAMP_NASS_SHADOW_LIVE": "1"}):
        if "HARVESTAMP_NASS_API_KEY" in os.environ:
            del os.environ["HARVESTAMP_NASS_API_KEY"]
            
        connector = NASSQuickStatsConnector()
        res = connector.fetch_benchmark(commodity="CORN", statisticcat_desc="YIELD", state_alpha="IL", farm_id="PVF_ROW_CROP_001")
        
        assert res["status"] == "denied"
        assert res["freshness_status"] == "unavailable"
        assert res["payload"] == {}
        assert "HARVESTAMP_NASS_API_KEY" in res["missing_fields"]
        assert res["source_name"] == "USDA NASS Quick Stats API (live)"
        assert res["connector_mode"] == "live"

def test_pvf_weekly_plan_nass_context_and_evidence():
    """Verify that weekly plan for PVF incorporates NASS benchmark context and evidence correctly."""
    from harvestamp.workflows.supervisor import Supervisor
    scen, farm, obs = load_scenario_context("PVF-001")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    # 1. PVF weekly plan includes NASS benchmark context as regional context only
    rec = next(r for r in ap["recommendations"] if r["recommendation_type"] == "margin_scenario")
    assert "USDA NASS county/state benchmark data is included as regional context only" in rec["summary"]
    assert "Prairie View's farm-specific records remain the decision anchor." in rec["summary"]
    
    # 2. PVF weekly evidence includes NASS benchmark evidence
    ev_ids = [ev["evidence_id"] for ev in ap["evidence_summary"]]
    assert "res_benchmark_nass_PVF_ROW_CROP_001" in ev_ids
    
    # 3. Check that connector mode is present in evidence summary
    nass_ev = next(ev for ev in ap["evidence_summary"] if ev["evidence_id"] == "res_benchmark_nass_PVF_ROW_CROP_001")
    assert nass_ev["connector_mode"] == "offline_mock"
    assert nass_ev["fallback_used"] is False

def test_pvf_002_exclusion_of_nass():
    """Verify that NASS crop yield/acreage context is NOT requested or present in PVF-002 (diesel purchase window)."""
    from harvestamp.workflows.supervisor import Supervisor
    scen, farm, obs = load_scenario_context("PVF-002")
    supervisor = Supervisor()
    
    ap = supervisor.run_workflow(farm, scen["user_id"], scen["user_role"], scen["prompt"], obs)
    
    # 1. Check that res_benchmark_nass_PVF_ROW_CROP_001 does not appear in evidence list
    ev_ids = [ev["evidence_id"] for ev in ap["evidence_summary"]]
    assert "res_benchmark_nass_PVF_ROW_CROP_001" not in ev_ids
    
    # 2. Check that the output summary/recommendation does not contain NASS/Quick Stats/yield/acreage benchmark terms
    ap_str = json.dumps(ap).lower()
    assert "usda nass" not in ap_str
    assert "nass quick stats" not in ap_str
    assert "county yield benchmark" not in ap_str
    assert "acreage benchmark" not in ap_str

def test_api_key_exposure_prevention():
    """Verify that the NASS API key value and the full URL containing it do not appear in results, evidence, ActionPack, logs, or exceptions."""
    import urllib.error
    from harvestamp.workflows.supervisor import Supervisor
    from harvestamp.audit.logger import AuditLogger
    
    secret_key = "my_secret_nass_key_xyz_789"
    url_with_key = f"https://quickstats.nass.usda.gov/api/api_GET/?key={secret_key}&format=json&commodity_desc=CORN"
    
    with patch.dict(os.environ, {"HARVESTAMP_NASS_SHADOW_LIVE": "1", "HARVESTAMP_NASS_API_KEY": secret_key}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url=url_with_key,
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None
            )
            
            connector = NASSQuickStatsConnector()
            res = connector.fetch_benchmark(commodity="CORN", statisticcat_desc="YIELD", state_alpha="IL", farm_id="PVF_ROW_CROP_001")
            
            res_str = json.dumps(res)
            
            assert res["status"] == "denied"
            assert secret_key not in res_str
            assert url_with_key not in res_str
            
            # Ensure exceptions/assumptions are redacted
            for assumption in res["assumptions"]:
                assert secret_key not in assumption
                assert "quickstats.nass.usda.gov" not in assumption
                assert "key=" not in assumption

            # Verify Supervisor weekly plan execution doesn't leak
            scen, farm, obs = load_scenario_context("PVF-001")
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
            assert "quickstats.nass.usda.gov" not in ap_str
            assert "key=" not in ap_str

def test_exception_scrubbing():
    """Verify exception scrubbing for NASSQuickStatsConnector."""
    import urllib.error
    secret_key = "my_secret_nass_key_xyz_789"
    url_with_key = f"https://quickstats.nass.usda.gov/api/api_GET/?key={secret_key}&format=json"
    
    err = urllib.error.HTTPError(
        url=url_with_key,
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=None
    )
    
    connector = NASSQuickStatsConnector()
    scrubbed_err = connector._scrub_exception(err, secret_key)
    
    assert secret_key not in getattr(scrubbed_err, "url", "")
    assert "quickstats.nass.usda.gov" not in getattr(scrubbed_err, "url", "")
    assert "[REDACTED_URL]" in getattr(scrubbed_err, "url", "")
