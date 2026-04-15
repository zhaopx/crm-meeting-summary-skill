from pathlib import Path

import json
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "tests" / "crm_meeting_summary" / "helpers" / "mock_runner.py"
MOCK_BASE = REPO_ROOT / "tests" / "crm_meeting_summary" / "fixtures" / "mock-runtime"


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
    "template_no_fabrication",
    "next_action_quality",
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
def test_execute_returns_review_checked_runtime_output_when_review_passes():
    output = run_runner(BASELINE_ARGS)

    assert output["status"] == "passed"
    assert output["review_result"]["pass"] is True
    assert output["retry_state"] == {"revision": 0, "status": "passed", "history": []}
    assert output["human_summary"]
    assert "会议快照" in output["human_summary"]
    assert "核心总结与判断" in output["human_summary"]
    assert "风险与待确认问题" in output["human_summary"]

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

    assert output["retrieval_trace"]["policy_version"] == "taxonomy-v2-runtime-v3"
    assert output["loaded_knowhow"]["policy_version"] == "taxonomy-v2-runtime-v3"
    assert output["crm_data_requests"], "crm_data_requests 应该非空"
    sources = output["crm_data_requests"][0].get("sources", [])
    assert any("knowhow:data_requirements" in item for item in sources)

    assert output["template_output"]["applied"] is True
    assert output["template_output"]["template_id_chain"] == [
        "template-needs-clarification-general-b2b",
    ]
    section_titles = [section["title"] for section in output["template_output"]["sections"]]
    assert section_titles == [
        "会议快照",
        "核心总结与判断",
        "Knowhow 关注点",
        "建议的下一步动作",
        "风险与待确认问题",
    ]
    assert output["template_trace"]["selected_templates"] == [
        "skills/crm-meeting-summary/references/templates/profiles/needs-clarification--general-b2b.md"
    ]
    assert output["template_trace"]["merge_order"] == ["matched-profile"]
    assert output["template_trace"]["strict_no_fabrication"] is True

    assert set(output["review_result"]["check_results"].keys()) == REVIEW_CHECK_KEYS
    assert all(value == "pass" for value in output["review_result"]["check_results"].values())
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
    assert output["template_output"]["template_id_chain"] == ["template-common-default"]
    assert output["template_trace"]["selected_templates"] == [
        "skills/crm-meeting-summary/references/templates/common/default.md"
    ]
    assert output["template_trace"]["merge_order"] == ["fallback-common"]
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
    assert output["review_result"]["check_results"]["template_no_fabrication"] == "pass"


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
def test_template_missing_content_stays_missing_without_fabrication():
    output = run_runner(BASELINE_ARGS)

    missing_items = output["template_output"]["unmapped_or_missing_items"]
    assert missing_items
    missing_labels = {item["label"] for item in missing_items}
    assert "拍板人确认" in missing_labels
    assert "拍板人确认：[missing]" in output["human_summary"]
    assert "拍板人确认：已确认" not in output["human_summary"]


@pytest.mark.unit
def test_next_action_quality_exposes_task_purpose_and_blocker_in_summary_fields():
    output = run_runner(BASELINE_ARGS)

    summary_fields = output["summary_fields"]
    assert summary_fields["next_action_task"] == "一周内提交问题诊断与优化路径建议"
    assert "效果不稳定" in summary_fields["next_action_purpose"]
    assert "无法判断是否进入试点" in summary_fields["next_action_blocker"]

    mapping_by_label = {
        item["label"]: item
        for section in output["template_output"]["sections"]
        for item in section["items"]
    }
    assert mapping_by_label["动作"]["resolved_source_path"] == "summary_fields.next_action_task"
    assert mapping_by_label["目的"]["resolved_source_path"] == "summary_fields.next_action_purpose"
    assert mapping_by_label["不做会卡住什么"]["resolved_source_path"] == "summary_fields.next_action_blocker"
    assert "动作：[missing]" not in output["human_summary"]
    assert "目的：[missing]" not in output["human_summary"]
    assert "不做会卡住什么：[missing]" not in output["human_summary"]
    assert output["review_result"]["check_results"]["next_action_quality"] == "pass"


@pytest.mark.unit
def test_uncertain_path_still_provides_structured_next_action_triplet():
    output = run_runner(UNCERTAIN_ARGS)

    summary_fields = output["summary_fields"]
    assert summary_fields["next_action_task"] == "先确认当前讨论到底属于预算、试点、交付还是采购问题"
    assert "会议主题消歧" in summary_fields["next_action_purpose"]
    assert "retrieval、判断和跟进动作都会继续跑偏" in summary_fields["next_action_blocker"]
    assert output["review_result"]["check_results"]["next_action_quality"] == "pass"


@pytest.mark.unit
def test_human_summary_follows_template_section_order():
    output = run_runner(BASELINE_ARGS)

    human_summary = output["human_summary"]
    expected_order = [
        "会议快照",
        "核心总结与判断",
        "Knowhow 关注点",
        "建议的下一步动作",
        "风险与待确认问题",
    ]
    positions = [human_summary.index(title) for title in expected_order]
    assert positions == sorted(positions)


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
