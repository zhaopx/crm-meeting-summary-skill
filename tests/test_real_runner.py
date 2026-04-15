from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_RUNNER_PATH = REPO_ROOT / "tests" / "crm_meeting_summary" / "helpers" / "real_runner.py"
VALIDATOR_PATH = REPO_ROOT / "tests" / "crm_meeting_summary" / "helpers" / "contract_validator.py"
MOCK_BASE = REPO_ROOT / "tests" / "crm_meeting_summary" / "fixtures" / "mock-runtime"


def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


real_runner = load_module(REAL_RUNNER_PATH, "real_runner")
contract_validator = load_module(VALIDATOR_PATH, "contract_validator")


HUMAN_SUMMARY = """## 会议快照
- 会议目标：确认问题根因

## 核心总结与判断
- 当前判断：客户要先验证知识库更新机制。

## Knowhow 关注点
- 关注项：先做小范围验证。

## 建议的下一步动作
- 动作：补齐夜间转人工率样本。

## 风险与待确认问题
- 待确认：最终拍板人
"""

REVIEW_RESULT = {
    "pass": True,
    "review_status": "pass",
    "failure_reasons": [],
    "targeted_regeneration_instructions": [],
}

AUDIT_PAYLOAD = {
    "schema_version": "crm-meeting-summary-audit-v1",
    "scenario_decision": {
        "primary_scenario": "知识库优化",
        "scenario_slug": "knowledge-base-refresh",
        "scenario_confidence": "medium",
        "secondary_tags": [],
        "industry": None,
        "reasoning_signals": {
            "supporting": ["知识库", "转人工率"],
            "conflicting": [],
            "rejected_candidates": ["客户经营"],
        },
    },
    "meeting_state_features": {
        "relationship_state": "neutral",
        "decision_pressure": "medium",
        "trust_state": "neutral",
        "momentum_state": "forward",
    },
    "retrieval_trace": {
        "policy_version": "taxonomy-v2-runtime-v3",
        "scenario_mode": "normal",
        "allowed_request_groups": ["opportunity_progress_gap"],
        "requested_request_groups": ["opportunity_progress_gap"],
        "out_of_policy_requests": [],
    },
    "loaded_knowhow": ["common"],
    "claim_evidence_map": [
        {
            "claim_type": "judgment",
            "claim_text": "客户要先验证知识库更新机制",
            "evidence": [
                {
                    "source_type": "meeting",
                    "source_ref": "meeting-record.txt:1",
                    "excerpt": "客户要先验证知识库更新机制。",
                }
            ],
        }
    ],
    "missing_information": ["最终拍板人"],
    "memory_conflicts": [],
    "template_trace": {"template_path": None, "mapping_gaps": []},
    "review_trace": {
        "review_status": "pass",
        "failure_reasons": [],
        "targeted_regeneration_instructions": [],
        "regeneration_count": 0,
    },
}

CLI_SUCCESS_PAYLOAD = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": "无关中间说明",
                }
            ]
        },
    },
    {
        "type": "result",
        "result": HUMAN_SUMMARY,
    },
]

REVIEW_RESULT_PAYLOAD = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{HUMAN_SUMMARY}\n```json\n"
                        f"{json.dumps(REVIEW_RESULT, ensure_ascii=False, indent=2)}\n```"
                    ),
                }
            ]
        },
    }
]

REVIEW_ONLY_PAYLOAD = [
    {
        "type": "result",
        "result": (
            "```json\n"
            f"{json.dumps(REVIEW_RESULT, ensure_ascii=False, indent=2)}\n"
            "```"
        ),
    }
]


REVIEW_RESULT_IN_MIDDLE_PAYLOAD = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "中间说明\n```json\n"
                        f"{json.dumps(REVIEW_RESULT, ensure_ascii=False, indent=2)}\n```\n"
                        f"{HUMAN_SUMMARY}"
                    ),
                }
            ]
        },
    }
]


AUDIT_PAYLOAD_BLOCK = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{HUMAN_SUMMARY}\n```json\n"
                        f"{json.dumps(AUDIT_PAYLOAD, ensure_ascii=False, indent=2)}\n```"
                    ),
                }
            ]
        },
    }
]


REVIEW_AND_AUDIT_WITH_TAIL_TEXT_PAYLOAD = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{HUMAN_SUMMARY}\n```json\n"
                        f"{json.dumps(REVIEW_RESULT, ensure_ascii=False, indent=2)}\n```\n"
                        f"```json\n{json.dumps(AUDIT_PAYLOAD, ensure_ascii=False, indent=2)}\n```\n"
                        "review loop: 已完成"
                    ),
                }
            ]
        },
    }
]


TAIL_HINT_ONLY_PAYLOAD = [
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{HUMAN_SUMMARY}\n"
                        "### 结构化审计载荷（供 runner / review / eval 消费，不属于正文）"
                    ),
                }
            ]
        },
    }
]



def test_extract_final_text_prefers_human_summary_block():
    final_text = real_runner.extract_final_text(CLI_SUCCESS_PAYLOAD)

    assert final_text.startswith("## 会议快照")
    assert "核心总结与判断" in final_text
    assert "风险与待确认问题" in final_text



def test_extract_review_result_from_summary_trailer():
    final_text = real_runner.extract_final_text(REVIEW_RESULT_PAYLOAD)
    review_result = real_runner.extract_review_result(REVIEW_RESULT_PAYLOAD[0]["message"]["content"][0]["text"])

    assert final_text == HUMAN_SUMMARY.rstrip()
    assert "```json" not in final_text
    assert review_result == REVIEW_RESULT



def test_extract_review_result_from_payload_falls_back_to_non_trailing_json():
    review_result = real_runner.extract_review_result_from_payload(REVIEW_RESULT_IN_MIDDLE_PAYLOAD)

    assert review_result == REVIEW_RESULT



def test_extract_audit_payload_from_payload_reads_structured_audit_block():
    audit_payload = real_runner.extract_audit_payload_from_payload(AUDIT_PAYLOAD_BLOCK)

    assert audit_payload == AUDIT_PAYLOAD



def test_extract_final_text_cuts_at_first_structured_block_even_with_tail_text():
    final_text = real_runner.extract_final_text(REVIEW_AND_AUDIT_WITH_TAIL_TEXT_PAYLOAD)

    assert final_text == HUMAN_SUMMARY.rstrip()
    assert "review loop" not in final_text
    assert "review_status" not in final_text



def test_validate_human_summary_rejects_tail_hint_text():
    final_text = real_runner.extract_final_text(TAIL_HINT_ONLY_PAYLOAD)
    errors = contract_validator.validate_human_summary(final_text)

    assert any("最终总结混入内部过程字段" in item for item in errors)



def test_extract_review_result_from_payload_prefers_review_over_audit_payload():
    with pytest.raises(real_runner.RealRunnerError, match="未找到人类可读总结正文"):
        real_runner.extract_final_text(REVIEW_ONLY_PAYLOAD)



def test_extract_final_text_raises_for_review_only_payload():
    with pytest.raises(real_runner.RealRunnerError, match="未找到人类可读总结正文"):
        real_runner.extract_final_text(REVIEW_ONLY_PAYLOAD)



def test_extract_review_and_audit_payloads_still_work_without_summary_body():
    review_result = real_runner.extract_review_result_from_payload(REVIEW_ONLY_PAYLOAD)

    assert review_result == REVIEW_RESULT



def test_extract_review_result_returns_none_for_non_review_json():
    review_result = real_runner.extract_review_result("会议快照\n```json\n{}\n```")

    assert review_result is None



def test_parse_cli_payload_ignores_log_prefix():
    stdout = "(eval):1: bad pattern\n" + json.dumps(CLI_SUCCESS_PAYLOAD, ensure_ascii=False)

    parsed = real_runner.parse_cli_payload(stdout)

    assert parsed[-1]["type"] == "result"
    assert parsed[-1]["result"].startswith("## 会议快照")



def test_build_skill_prompt_uses_template_first_contract(tmp_path: Path):
    input_path = tmp_path / "bundle.json"
    input_path.write_text("{}", encoding="utf-8")

    prompt = real_runner.build_skill_prompt(input_path)

    assert str(input_path) in prompt
    assert "按 skill 契约完成输出" in prompt
    assert "最终正文必须以命中的 template 为准" in prompt
    assert "不要自行追加 template 之外的结构" in prompt
    assert "review_result 或 audit_payload" in prompt
    assert "固定五章节" not in prompt
    assert "两个 JSON fenced block" not in prompt
    assert "输入包是 JSON 文件，不是 PDF" in prompt
    assert "非 PDF 的 Read 调用不要传 pages 字段" in prompt



def test_build_allowed_tools_includes_repo_and_skill_paths():
    allowed_tools = real_runner.build_allowed_tools()

    assert f"Read(//{str(real_runner.REPO_ROOT).lstrip('/')}/**)" in allowed_tools
    assert f"Read(//{str(real_runner.CRM_SKILL_DIR).lstrip('/')}/**)" in allowed_tools
    assert f"Read(//{str(real_runner.CRM_SKILL_DIR / 'references').lstrip('/')}/**)" in allowed_tools
    assert f"Read(//{str(real_runner.CRM_SKILL_DIR / 'review').lstrip('/')}/**)" in allowed_tools
    assert "Skill(crm-meeting-summary)" in allowed_tools



def test_invoke_real_skill_timeout_raises_clear_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(real_runner.subprocess, "run", fake_run)

    with pytest.raises(real_runner.RealRunnerError, match="超时"):
        real_runner.invoke_real_skill({"meeting": {"record_text": "x"}})



def test_invoke_real_skill_command_not_found_raises_clear_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("claude")

    monkeypatch.setattr(real_runner.subprocess, "run", fake_run)

    with pytest.raises(real_runner.RealRunnerError, match="未找到 claude CLI"):
        real_runner.invoke_real_skill({"meeting": {"record_text": "x"}})



def test_run_case_appends_real_run_log(monkeypatch, tmp_path: Path):
    case = {
        "id": "baseline-input-bundle-path",
        "input_bundle_path": ".local/crm-meeting-summary-test-data/case-001",
    }
    monkeypatch.setattr(real_runner, "load_eval_case", lambda case_id: case)
    monkeypatch.setattr(real_runner, "build_input_bundle_from_path", lambda bundle_path: {"meeting": {"record_text": "纪要"}})
    monkeypatch.setattr(
        real_runner,
        "invoke_real_skill",
        lambda bundle: {
            "raw_response": [{"type": "result", "result": "raw"}],
            "final_text": "## 会议快照\n- x",
            "review_result": {"review_status": "pass"},
            "audit_payload": {"schema_version": "crm-meeting-summary-audit-v1"},
        },
    )
    monkeypatch.setattr(real_runner, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(real_runner, "REAL_RUN_LOG_PATH", tmp_path / "real-runs.jsonl")

    result = real_runner.run_case("baseline-input-bundle-path")

    log_lines = (tmp_path / "real-runs.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert result["case"] == case
    assert len(log_lines) == 1
    payload = json.loads(log_lines[0])
    assert payload["case_id"] == "baseline-input-bundle-path"
    assert payload["input_bundle_path"] == ".local/crm-meeting-summary-test-data/case-001"
    assert payload["final_text"] == "## 会议快照\n- x"



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
    (bundle_dir / "account-memory.json").write_text(
        json.dumps(
            {
                "scope": "account",
                "lookup_key": "account_id:CUST-001",
                "memory": ["客户过去两次续费前都要求先看到量化效果改善。"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (bundle_dir / "person-memory.json").write_text(
        json.dumps(
            {
                "scope": "person",
                "lookup_key": "person_id:USR-101",
                "memory": ["王敏过去在该客户沟通中偏向先稳定关系，再推进商业动作。"],
            },
            ensure_ascii=False,
        ),
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
    assert bundle["memory_snippets"] == [
        {
            "scope": "account",
            "lookup_key": "account_id:CUST-001",
            "memory": ["客户过去两次续费前都要求先看到量化效果改善。"],
        },
        {
            "scope": "person",
            "lookup_key": "person_id:USR-101",
            "memory": ["王敏过去在该客户沟通中偏向先稳定关系，再推进商业动作。"],
        },
    ]
    assert bundle["constraints"] == {"language": "zh-CN", "output_mode": "human_only"}



def test_build_input_bundle_from_input_bundle_path_allows_missing_contact(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "case-002"
    bundle_dir.mkdir()
    (bundle_dir / "meeting-record.txt").write_text("客户更关注联系人管理、拜访计划和评分预警。", encoding="utf-8")
    (bundle_dir / "AccountObj.json").write_text(
        json.dumps({"account_id": "CUST-002", "account_name": "某酒店数字化运营集团"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (bundle_dir / "NewOpportunityObj.json").write_text(
        json.dumps({"opportunity_id": "OPP-9002", "opportunity_name": "酒店客户经营与项目管理一体化评估项目"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (bundle_dir / "PersonnelObj.json").write_text(
        json.dumps({"person_id": "USR-101", "person_name": "陈小艳"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (bundle_dir / "opportunity-memory.json").write_text(
        json.dumps(
            {
                "scope": "opportunity",
                "lookup_key": "opportunity_id:OPP-9002",
                "memory": ["该项目核心不是新客获客，而是提升酒店私域经营效果。"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(real_runner, "ensure_repo_path", lambda path: None)

    bundle = real_runner.build_input_bundle_from_path(bundle_dir)

    assert bundle["meeting"]["record_text"] == "客户更关注联系人管理、拜访计划和评分预警。"
    assert bundle["crm_context"]["account"]["account_id"] == "CUST-002"
    assert bundle["crm_context"]["opportunity"]["opportunity_id"] == "OPP-9002"
    assert bundle["crm_context"]["person"]["person_id"] == "USR-101"
    assert "contact" not in bundle["crm_context"]
    assert bundle["memory_snippets"] == [
        {
            "scope": "opportunity",
            "lookup_key": "opportunity_id:OPP-9002",
            "memory": ["该项目核心不是新客获客，而是提升酒店私域经营效果。"],
        }
    ]



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
        lambda bundle: {"bundle": bundle, "final_text": HUMAN_SUMMARY},
    )

    result = real_runner.run_case("bundle-path-case")

    assert result["case"]["id"] == "bundle-path-case"
    assert result["final_text"].startswith("## 会议快照")
    assert result["bundle"]["meeting"]["record_text"] == "客户反馈夜间转人工率偏高。"
    assert result["bundle"]["crm_context"]["account"]["account_id"] == "CUST-001"



def test_validate_human_summary_requires_all_sections():
    errors = contract_validator.validate_human_summary("会议快照\n- 只有一段")

    assert errors
    assert any("核心总结与判断" in item for item in errors)
    assert any("Knowhow 关注点" in item for item in errors)
    assert any("建议的下一步动作" in item for item in errors)
    assert any("风险与待确认问题" in item for item in errors)



def test_validate_human_summary_accepts_complete_sections():
    errors = contract_validator.validate_human_summary(HUMAN_SUMMARY)

    assert errors == []



def test_validate_review_result_accepts_expected_shape():
    errors = contract_validator.validate_review_result(REVIEW_RESULT)

    assert errors == []



def test_validate_review_result_rejects_missing_keys_and_bad_status():
    errors = contract_validator.validate_review_result(
        {
            "pass": True,
            "review_status": "ok",
            "failure_reasons": [],
        }
    )

    assert any("targeted_regeneration_instructions" in item for item in errors)
    assert any("review_status 非法" in item for item in errors)



def test_validate_audit_payload_accepts_expected_shape():
    errors = contract_validator.validate_audit_payload(AUDIT_PAYLOAD)

    assert errors == []



def test_validate_audit_payload_rejects_missing_keys_and_bad_values():
    errors = contract_validator.validate_audit_payload(
        {
            "schema_version": "bad-version",
            "scenario_decision": {"scenario_confidence": "certain"},
            "meeting_state_features": {},
            "retrieval_trace": {},
            "loaded_knowhow": [],
            "claim_evidence_map": [{"claim_type": "judgment", "claim_text": "结论", "evidence": []}],
            "missing_information": [],
            "memory_conflicts": [],
            "template_trace": {},
            "review_trace": {"review_status": "maybe"},
        }
    )

    assert any("schema_version 非法" in item for item in errors)
    assert any("scenario_confidence 非法" in item for item in errors)
    assert any("高价值结论必须有 evidence" in item for item in errors)
    assert any("review_trace.review_status 非法" in item for item in errors)



def test_validate_case_rules_for_uncertain_mode_summary():
    final_text = """会议快照
- 场景：其他 / 不确定

核心总结与判断
- 当前判断：证据不足，待确认。

风险与待确认问题
- 待确认：客户真实优先级
"""

    errors = contract_validator.validate_case_expectations(
        "baseline-low-confidence-fallback",
        final_text,
        None,
    )

    assert errors == []
