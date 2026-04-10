from pathlib import Path

import json
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "skills" / "crm-meeting-summary" / "mock_runner.py"
MOCK_BASE = REPO_ROOT / "skills" / "mock-runtime"


BASELINE_ARGS = [
    "--meeting-file",
    str(MOCK_BASE / "meeting-records" / "meeting-001.json"),
    "--scenario-slug",
    "needs-clarification",
    "--scenario-confidence",
    "high",
    "--industry",
    "general-b2b",
    "--account-file",
    str(MOCK_BASE / "crm" / "account" / "CUST-001.json"),
    "--opportunity-file",
    str(MOCK_BASE / "crm" / "opportunity" / "OPP-9001.json"),
    "--person-file",
    str(MOCK_BASE / "crm" / "person" / "USR-101.json"),
]


UNCERTAIN_ARGS = [
    "--meeting-file",
    str(MOCK_BASE / "meeting-records" / "meeting-ambiguous.json"),
    "--scenario-slug",
    "uncertain",
    "--scenario-confidence",
    "low",
]


RETRY_PASS_ARGS = [
    "--meeting-file",
    str(MOCK_BASE / "meeting-records" / "meeting-memory-conflict.json"),
    "--scenario-slug",
    "needs-clarification",
    "--scenario-confidence",
    "high",
    "--account-file",
    str(MOCK_BASE / "crm" / "account" / "CUST-001.json"),
    "--opportunity-file",
    str(MOCK_BASE / "crm" / "opportunity" / "OPP-9001.json"),
    "--person-file",
    str(MOCK_BASE / "crm" / "person" / "USR-101.json"),
]


MANUAL_REVIEW_ARGS = [
    "--meeting-file",
    str(MOCK_BASE / "meeting-records" / "meeting-hard-fail.json"),
    "--scenario-slug",
    "risk-escalation",
    "--scenario-confidence",
    "high",
]


REVIEW_CHECK_KEYS = {
    "scenario_self_consistency",
    "knowhow_coverage",
    "evidence_grounding",
    "memory_conflict_handling",
    "missing_information_handling",
    "policy_boundary_handling",
    "semantic_normalization_consistency",
    "meeting_state_feature_evidence",
    "semantic_summary_consistency",
    "machine_output_completeness",
}


def run_runner(args: list[str]) -> dict:
    result = subprocess.run(
        [sys.executable, str(RUNNER), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


@pytest.mark.unit
def test_execute_returns_full_output_schema_when_review_passes():
    output = run_runner(BASELINE_ARGS)

    assert output["status"] == "passed"
    assert output["review_result"]["pass"] is True
    assert output["retry_state"] == {"revision": 0, "status": "passed", "history": []}
    assert output["human_summary"]
    assert len(output["human_summary"].split("\n\n")) == 5

    assert output["scenario_result"]["scenario_mode"] == "normal"
    assert output["scenario_result"]["scenario_slug"] == "needs-clarification"
    assert output["scenario_result"]["industry"] == "general-b2b"
    assert output["scenario_result"]["evidence"]
    assert set(output["semantic_normalization"].keys()) == {
        "object_aliases",
        "lookup_keys",
        "resolved_objects",
        "relationship_map",
    }
    assert set(output["meeting_state_features"].keys()) == {
        "relationship_state",
        "decision_pressure",
        "trust_state",
        "momentum_state",
    }

    assert output["crm_data_requests"], "crm_data_requests 应该非空"
    sources = output["crm_data_requests"][0].get("sources", [])
    assert any("knowhow:data_requirements" in item for item in sources)

    assert set(output["review_ready_checks"].keys()) == REVIEW_CHECK_KEYS
    assert all(output["review_ready_checks"].values())
    assert set(output["review_result"]["check_results"].keys()) == REVIEW_CHECK_KEYS
    assert set(output["semantic_summary"].keys()) == {
        "relationship_state",
        "decision_pressure",
        "trust_state",
        "momentum_state",
    }
    assert output["semantic_summary"] == output["meeting_state_features"]
    assert output["summary_fields"]["missing_information"] == output["missing_information_candidates"]


@pytest.mark.unit
def test_execute_uses_uncertain_path_when_scenario_confidence_low():
    output = run_runner(UNCERTAIN_ARGS)

    assert output["status"] == "passed"
    assert output["scenario_result"]["scenario_mode"] == "uncertain"
    assert output["scenario_result"]["scenario_confidence"] == "low"
    assert output["crm_data_requests"] == []
    assert len(output["retrieval_trace"]["requested_request_groups"]) <= 1
    assert output["loaded_knowhow"]["scenario"] == []
    assert output["loaded_knowhow"]["patches"] == []
    assert output["review_result"]["pass"] is True


@pytest.mark.unit
def test_execute_retries_once_with_targeted_regeneration_then_passes():
    output = run_runner(RETRY_PASS_ARGS)

    assert output["status"] == "passed"
    assert output["review_result"]["pass"] is True
    assert output["retry_state"]["revision"] == 1
    assert output["retry_state"]["history"] == [
        {
            "revision": 0,
            "review_status": "fail",
            "failed_checks": ["memory_conflict_handling"],
        }
    ]
    assert "当前会话证据优先于历史记忆" in output["human_summary"]


@pytest.mark.unit
def test_execute_stops_at_manual_review_required_after_two_retries_fail():
    output = run_runner(MANUAL_REVIEW_ARGS)

    assert output["status"] == "manual_review_required"
    assert output["review_result"]["pass"] is False
    assert output["review_result"]["review_status"] == "fail"
    assert output["retry_state"]["revision"] == 2
    assert output["retry_state"]["status"] == "manual_review_required"
    assert len(output["retry_state"]["history"]) == 2
    assert all(item["review_status"] == "fail" for item in output["retry_state"]["history"])
    assert output["review_result"]["failure_reasons"]
    assert output["review_result"]["targeted_regeneration_instructions"]



@pytest.mark.unit
def test_mock_source_mapping_prefers_id():
    output = run_runner(
        [
            "--meeting-file",
            str(MOCK_BASE / "meeting-records" / "meeting-001.json"),
            "--scenario-slug",
            "needs-clarification",
            "--scenario-confidence",
            "high",
            "--account-file",
            str(MOCK_BASE / "crm" / "account" / "CUST-001.json"),
        ]
    )

    mock_sources = output["mock_sources"]
    assert mock_sources["account"].endswith("crm/account/CUST-001.json")


@pytest.mark.unit
def test_rejects_repo_external_paths():
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--meeting-file",
            "/tmp/outside.json",
            "--scenario-slug",
            "needs-clarification",
            "--scenario-confidence",
            "high",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "文件不存在" in result.stderr or "必须位于仓库内" in result.stderr


@pytest.mark.unit
def test_rejects_invalid_industry_slug():
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--meeting-file",
            str(MOCK_BASE / "meeting-records" / "meeting-001.json"),
            "--scenario-slug",
            "needs-clarification",
            "--scenario-confidence",
            "high",
            "--industry",
            "../escape",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "只能包含小写字母、数字和连字符" in result.stderr
