from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_RUNNER_PATH = REPO_ROOT / "skills" / "crm-meeting-summary" / "real_runner.py"
VALIDATOR_PATH = REPO_ROOT / "skills" / "crm-meeting-summary" / "devtools" / "contract_validator.py"
MOCK_BASE = REPO_ROOT / "skills" / "mock-runtime"


def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


real_runner = load_module(REAL_RUNNER_PATH, "real_runner")
contract_validator = load_module(VALIDATOR_PATH, "contract_validator")


CLI_SUCCESS_PAYLOAD = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": "会议快照\n...\n\n```json\n{\n  \"status\": \"passed\",\n  \"base_context\": {},\n  \"scenario_result\": {\n    \"primary_scenario\": \"需求澄清\",\n    \"scenario_slug\": \"needs-clarification\",\n    \"scenario_confidence\": \"high\",\n    \"industry\": \"general-b2b\",\n    \"scenario_mode\": \"normal\"\n  },\n  \"semantic_normalization\": {\n    \"object_aliases\": {},\n    \"lookup_keys\": {},\n    \"resolved_objects\": {},\n    \"relationship_map\": []\n  },\n  \"meeting_state_features\": {\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"short-term proof\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"curious\"\n  },\n  \"loaded_knowhow\": {},\n  \"crm_data_requests\": [],\n  \"memory_sources\": [],\n  \"memory_conflicts\": [],\n  \"summary_fields\": {\n    \"meeting_goal\": \"确认问题根因\",\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"short-term proof\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"curious\",\n    \"key_participants\": [],\n    \"current_stage_judgment\": \"qualification\",\n    \"next_actions\": [],\n    \"risk_level\": \"medium\",\n    \"missing_information\": []\n  },\n  \"semantic_summary\": {\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"short-term proof\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"curious\"\n  },\n  \"key_judgments\": {\n    \"facts\": [],\n    \"inferences\": [],\n    \"open_questions\": []\n  },\n  \"knowhow_focus_items\": [],\n  \"retrieval_trace\": {\n    \"mapping_version\": \"v1\",\n    \"scenario_mode\": \"normal\",\n    \"allowed_request_groups\": [],\n    \"requested_request_groups\": [],\n    \"out_of_policy_requests\": []\n  },\n  \"retry_state\": {\n    \"revision\": 0,\n    \"status\": \"passed\",\n    \"history\": []\n  },\n  \"review_ready_checks\": {\n    \"scenario_self_consistency\": true,\n    \"knowhow_coverage\": true,\n    \"evidence_grounding\": true,\n    \"memory_conflict_handling\": true,\n    \"missing_information_handling\": true,\n    \"policy_boundary_handling\": true,\n    \"semantic_normalization_consistency\": true,\n    \"meeting_state_feature_evidence\": true,\n    \"semantic_summary_consistency\": true,\n    \"machine_output_completeness\": true\n  }\n}\n```"
                }
            ]
        }
    },
    {
        "type": "result",
        "result": "会议快照\n...\n\n```json\n{\n  \"status\": \"passed\",\n  \"base_context\": {},\n  \"scenario_result\": {\n    \"primary_scenario\": \"需求澄清\",\n    \"scenario_slug\": \"needs-clarification\",\n    \"scenario_confidence\": \"high\",\n    \"industry\": \"general-b2b\",\n    \"scenario_mode\": \"normal\"\n  },\n  \"semantic_normalization\": {\n    \"object_aliases\": {},\n    \"lookup_keys\": {},\n    \"resolved_objects\": {},\n    \"relationship_map\": []\n  },\n  \"meeting_state_features\": {\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"short-term proof\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"curious\"\n  },\n  \"loaded_knowhow\": {},\n  \"crm_data_requests\": [],\n  \"memory_sources\": [],\n  \"memory_conflicts\": [],\n  \"summary_fields\": {\n    \"meeting_goal\": \"确认问题根因\",\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"short-term proof\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"curious\",\n    \"key_participants\": [],\n    \"current_stage_judgment\": \"qualification\",\n    \"next_actions\": [],\n    \"risk_level\": \"medium\",\n    \"missing_information\": []\n  },\n  \"semantic_summary\": {\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"short-term proof\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"curious\"\n  },\n  \"key_judgments\": {\n    \"facts\": [],\n    \"inferences\": [],\n    \"open_questions\": []\n  },\n  \"knowhow_focus_items\": [],\n  \"retrieval_trace\": {\n    \"mapping_version\": \"v1\",\n    \"scenario_mode\": \"normal\",\n    \"allowed_request_groups\": [],\n    \"requested_request_groups\": [],\n    \"out_of_policy_requests\": []\n  },\n  \"retry_state\": {\n    \"revision\": 0,\n    \"status\": \"passed\",\n    \"history\": []\n  },\n  \"review_ready_checks\": {\n    \"scenario_self_consistency\": true,\n    \"knowhow_coverage\": true,\n    \"evidence_grounding\": true,\n    \"memory_conflict_handling\": true,\n    \"missing_information_handling\": true,\n    \"policy_boundary_handling\": true,\n    \"semantic_normalization_consistency\": true,\n    \"meeting_state_feature_evidence\": true,\n    \"semantic_summary_consistency\": true,\n    \"machine_output_completeness\": true\n  }\n}\n```"
    },
]


REVIEW_RESULT_PAYLOAD = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "Skill",
                    "input": {
                        "skill": "crm-meeting-summary-review",
                        "args": "【generated machine-readable output】\n{\n  \"status\": \"passed\",\n  \"base_context\": {},\n  \"scenario_result\": {\n    \"primary_scenario\": \"其他/不确定\",\n    \"scenario_slug\": \"uncertain\",\n    \"scenario_confidence\": \"low\",\n    \"scenario_mode\": \"uncertain\"\n  },\n  \"semantic_normalization\": {\n    \"object_aliases\": {},\n    \"lookup_keys\": {},\n    \"resolved_objects\": {},\n    \"relationship_map\": []\n  },\n  \"meeting_state_features\": {\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"low\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"weak\"\n  },\n  \"loaded_knowhow\": {\n    \"scenario\": [],\n    \"patches\": []\n  },\n  \"crm_data_requests\": [],\n  \"memory_sources\": [],\n  \"memory_conflicts\": [],\n  \"summary_fields\": {\n    \"meeting_goal\": \"确认场景\",\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"low\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"weak\",\n    \"key_participants\": [],\n    \"current_stage_judgment\": \"uncertain\",\n    \"next_actions\": [],\n    \"risk_level\": \"medium\",\n    \"missing_information\": []\n  },\n  \"semantic_summary\": {\n    \"relationship_state\": \"active-account\",\n    \"decision_pressure\": \"low\",\n    \"trust_state\": \"neutral\",\n    \"momentum_state\": \"weak\"\n  },\n  \"key_judgments\": {\n    \"facts\": [],\n    \"inferences\": [],\n    \"open_questions\": []\n  },\n  \"knowhow_focus_items\": [],\n  \"retrieval_trace\": {\n    \"mapping_version\": \"v1\",\n    \"scenario_mode\": \"uncertain\",\n    \"allowed_request_groups\": [\"stakeholder_gap\"],\n    \"requested_request_groups\": [\"stakeholder_gap\"],\n    \"out_of_policy_requests\": []\n  },\n  \"retry_state\": {\n    \"revision\": 0,\n    \"status\": \"draft_generated\",\n    \"history\": []\n  },\n  \"review_ready_checks\": {\n    \"scenario_self_consistency\": true,\n    \"knowhow_coverage\": true,\n    \"evidence_grounding\": true,\n    \"memory_conflict_handling\": true,\n    \"missing_information_handling\": true,\n    \"policy_boundary_handling\": true,\n    \"semantic_normalization_consistency\": true,\n    \"meeting_state_feature_evidence\": true,\n    \"semantic_summary_consistency\": true,\n    \"machine_output_completeness\": true\n  }\n}"
                    },
                }
            ]
        },
    },
    {
        "type": "result",
        "result": "{\n  \"pass\": true,\n  \"review_status\": \"pass\",\n  \"failure_reasons\": [],\n  \"targeted_regeneration_instructions\": [],\n  \"check_results\": {\n    \"scenario_self_consistency\": \"pass\"\n  },\n  \"notes\": []\n}",
    },
]


REVIEW_FAIL_RESULT_PAYLOAD = [
    {
        "type": "result",
        "result": "```json\n{\n  \"pass\": false,\n  \"review_status\": \"fail\",\n  \"generated_machine_output\": {\n    \"status\": \"passed\",\n    \"base_context\": {},\n    \"scenario_result\": {\n      \"scenario_slug\": \"uncertain\",\n      \"scenario_mode\": \"uncertain\"\n    },\n    \"loaded_knowhow\": {},\n    \"crm_data_requests\": [],\n    \"memory_sources\": [],\n    \"memory_conflicts\": [],\n    \"summary_fields\": {},\n    \"semantic_summary\": {},\n    \"key_judgments\": {},\n    \"knowhow_focus_items\": [],\n    \"retrieval_trace\": {},\n    \"retry_state\": {},\n    \"review_ready_checks\": {}\n  }\n}\n```"
    }
]


def test_extract_final_text_prefers_result_block():
    final_text = real_runner.extract_final_text(CLI_SUCCESS_PAYLOAD)

    assert final_text.startswith("会议快照")
    assert '"status": "passed"' in final_text


def test_extract_machine_json_from_fenced_block():
    final_text = real_runner.extract_final_text(CLI_SUCCESS_PAYLOAD)
    extracted, meta = real_runner.extract_machine_json(final_text)

    assert extracted["status"] == "passed"
    assert extracted["scenario_result"]["scenario_slug"] == "needs-clarification"
    assert meta["source"] == "fenced_json"


def test_extract_final_text_skips_review_skill_result():
    final_text = real_runner.extract_final_text(REVIEW_RESULT_PAYLOAD)
    extracted, meta = real_runner.extract_machine_json(final_text)

    assert "generated machine-readable output" in final_text
    assert extracted["status"] == "passed"
    assert extracted["scenario_result"]["scenario_mode"] == "uncertain"
    assert meta["source"] == "embedded_machine_output"


def test_extract_machine_json_from_review_handoff_result():
    final_text = real_runner.extract_final_text(REVIEW_FAIL_RESULT_PAYLOAD)
    extracted, meta = real_runner.extract_machine_json(final_text)

    assert extracted["status"] == "passed"
    assert extracted["scenario_result"]["scenario_mode"] == "uncertain"
    assert meta["source"] == "review_handoff_json"


def test_parse_cli_payload_ignores_log_prefix():
    stdout = "(eval):1: bad pattern\n" + json.dumps(CLI_SUCCESS_PAYLOAD, ensure_ascii=False)

    parsed = real_runner.parse_cli_payload(stdout)

    assert parsed[-1]["type"] == "result"
    assert '"status": "passed"' in parsed[-1]["result"]


def test_build_skill_prompt_uses_input_file_reference(tmp_path: Path):
    input_path = tmp_path / "bundle.json"
    input_path.write_text("{}", encoding="utf-8")

    prompt = real_runner.build_skill_prompt(input_path)

    assert str(input_path) in prompt
    assert "按 skill 契约完成输出" in prompt
    assert "完整 machine JSON" in prompt
    assert "meeting_time" not in prompt
    assert "输入包是 JSON 文件，不是 PDF" in prompt
    assert "非 PDF 的 Read 调用不要传 pages 字段" in prompt
    assert 'pages: ""' not in prompt
    assert '"pages": ""' not in prompt


def test_invoke_real_skill_timeout_raises_clear_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(real_runner.subprocess, "run", fake_run)

    try:
        real_runner.invoke_real_skill({"meeting": {"record_text": "x"}})
    except real_runner.RealRunnerError as exc:
        assert "超时" in str(exc)
    else:
        raise AssertionError("expected RealRunnerError")


def test_invoke_real_skill_command_not_found_raises_clear_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("claude")

    monkeypatch.setattr(real_runner.subprocess, "run", fake_run)

    try:
        real_runner.invoke_real_skill({"meeting": {"record_text": "x"}})
    except real_runner.RealRunnerError as exc:
        assert "未找到 claude CLI" in str(exc)
    else:
        raise AssertionError("expected RealRunnerError")


def test_build_input_bundle_from_eval_files():
    bundle = real_runner.build_input_bundle(
        [
            MOCK_BASE / "meeting-records" / "meeting-001.json",
            MOCK_BASE / "crm" / "account" / "CUST-001.json",
            MOCK_BASE / "crm" / "opportunity" / "OPP-9001.json",
            MOCK_BASE / "crm" / "person" / "USR-101.json",
            MOCK_BASE / "memory" / "account" / "CUST-001-conflict.json",
        ]
    )

    assert bundle["meeting"]["account"]["id"] == "CUST-001"
    assert bundle["crm_context"]["account"]["account_id"] == "CUST-001"
    assert bundle["crm_context"]["opportunity"]["opportunity_id"] == "OPP-9001"
    assert bundle["crm_context"]["person"]["person_id"] == "USR-101"
    assert bundle["memory_snippets"][0]["scope"] == "account"
    assert bundle["constraints"] == {"language": "zh-CN", "output_mode": "human_and_json"}


def test_build_input_bundle_from_input_bundle_path_success(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "case-001"
    bundle_dir.mkdir()
    (bundle_dir / "meeting-record.txt").write_text("客户反馈夜间转人工率偏高。", encoding="utf-8")
    (bundle_dir / "AccountObj.json").write_text(
        json.dumps({"account_id": "CUST-001", "account_name": "华东零售集团"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (bundle_dir / "NewOpportunityObj.json").write_text(
        json.dumps({"opportunity_id": "OPP-9001", "opportunity_name": "智能客服升级项目"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (bundle_dir / "PersonnelObj.json").write_text(
        json.dumps({"person_id": "USR-101", "person_name": "王敏"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (bundle_dir / "ContactObj.json").write_text(
        json.dumps({"contact_id": "CNT-001", "contact_name": "李总"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (bundle_dir / "ignored.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(real_runner, "ensure_repo_path", lambda path: None)

    bundle = real_runner.build_input_bundle_from_path(bundle_dir)

    assert bundle["meeting"]["record_text"] == "客户反馈夜间转人工率偏高。"
    assert bundle["meeting"]["record_text_path"] is None
    assert bundle["crm_context"]["account"]["account_id"] == "CUST-001"
    assert bundle["crm_context"]["opportunity"]["opportunity_id"] == "OPP-9001"
    assert bundle["crm_context"]["person"]["person_id"] == "USR-101"
    assert bundle["crm_context"]["contact"]["contact_id"] == "CNT-001"
    assert bundle["constraints"] == {"language": "zh-CN", "output_mode": "human_and_json"}


def test_build_input_bundle_from_input_bundle_path_missing_meeting_record(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "case-001"
    bundle_dir.mkdir()
    (bundle_dir / "AccountObj.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(real_runner, "ensure_repo_path", lambda path: None)

    with pytest.raises(real_runner.RealRunnerError, match="meeting-record.txt"):
        real_runner.build_input_bundle_from_path(bundle_dir)


def test_build_input_bundle_from_input_bundle_path_invalid_json(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "case-001"
    bundle_dir.mkdir()
    (bundle_dir / "meeting-record.txt").write_text("纪要", encoding="utf-8")
    (bundle_dir / "AccountObj.json").write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(real_runner, "ensure_repo_path", lambda path: None)

    with pytest.raises(real_runner.RealRunnerError, match="AccountObj.json"):
        real_runner.build_input_bundle_from_path(bundle_dir)


def test_build_input_bundle_from_input_bundle_path_empty_meeting_record(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "case-001"
    bundle_dir.mkdir()
    (bundle_dir / "meeting-record.txt").write_text("\n\n", encoding="utf-8")
    monkeypatch.setattr(real_runner, "ensure_repo_path", lambda path: None)

    with pytest.raises(real_runner.RealRunnerError, match="meeting-record.txt"):
        real_runner.build_input_bundle_from_path(bundle_dir)


def test_build_input_bundle_from_input_bundle_path_rejects_file_outside_repo(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "case-001"
    bundle_dir.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "meeting-record.txt").write_text("外部会议纪要", encoding="utf-8")
    (bundle_dir / "meeting-record.txt").symlink_to(outside_dir / "meeting-record.txt")
    monkeypatch.setattr(real_runner, "ensure_repo_path", lambda path: None)

    with pytest.raises(real_runner.RealRunnerError, match="符号链接文件"):
        real_runner.build_input_bundle_from_path(bundle_dir)


def test_build_input_bundle_from_input_bundle_path_rejects_non_repo_directory(tmp_path: Path):
    bundle_dir = tmp_path / "case-001"
    bundle_dir.mkdir()
    (bundle_dir / "meeting-record.txt").write_text("客户反馈夜间转人工率偏高。", encoding="utf-8")

    with pytest.raises(real_runner.RealRunnerError, match="文件必须位于仓库内"):
        real_runner.build_input_bundle_from_path(bundle_dir)


def test_run_case_rejects_invalid_input_bundle_path_value(monkeypatch):
    monkeypatch.setattr(real_runner, "load_eval_case", lambda case_id: {"id": case_id, "input_bundle_path": 123})

    with pytest.raises(real_runner.RealRunnerError, match="input_bundle_path 必须是非空字符串"):
        real_runner.run_case("bundle-path-case")


def test_run_case_rejects_empty_input_bundle_path_value(monkeypatch):
    monkeypatch.setattr(real_runner, "load_eval_case", lambda case_id: {"id": case_id, "input_bundle_path": "   "})

    with pytest.raises(real_runner.RealRunnerError, match="input_bundle_path 必须是非空字符串"):
        real_runner.run_case("bundle-path-case")


def test_run_case_supports_input_bundle_path_protocol(monkeypatch, tmp_path: Path):
    bundle_dir = tmp_path / "case-001"
    bundle_dir.mkdir()
    (bundle_dir / "meeting-record.txt").write_text("客户反馈夜间转人工率偏高。", encoding="utf-8")
    (bundle_dir / "AccountObj.json").write_text(
        json.dumps({"account_id": "CUST-001", "account_name": "华东零售集团"}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(real_runner, "ensure_repo_path", lambda path: None)
    monkeypatch.setattr(
        real_runner,
        "load_eval_case",
        lambda case_id: {"id": case_id, "input_bundle_path": str(bundle_dir)},
    )
    monkeypatch.setattr(
        real_runner,
        "invoke_real_skill",
        lambda bundle: {"bundle": bundle, "status": "stubbed"},
    )

    result = real_runner.run_case("bundle-path-case")

    assert result["case"]["id"] == "bundle-path-case"
    assert result["status"] == "stubbed"
    assert result["bundle"]["meeting"]["record_text"] == "客户反馈夜间转人工率偏高。"
    assert result["bundle"]["crm_context"]["account"]["account_id"] == "CUST-001"


def test_validate_machine_output_requires_runtime_contract_fields():
    errors = contract_validator.validate_machine_output({"status": "passed"})

    assert errors
    assert any("base_context" in item for item in errors)
    assert any("semantic_summary" in item for item in errors)


def test_validate_case_rules_for_uncertain_mode():
    output = {
        "status": "passed",
        "scenario_result": {"scenario_mode": "uncertain"},
        "loaded_knowhow": {"scenario": [], "patches": []},
        "retrieval_trace": {"requested_request_groups": ["stakeholder_gap"]},
        "memory_conflicts": [],
        "retry_state": {"revision": 0, "status": "passed", "history": []},
    }

    errors = contract_validator.validate_case_expectations(
        "baseline-low-confidence-fallback",
        output,
    )

    assert errors == []
