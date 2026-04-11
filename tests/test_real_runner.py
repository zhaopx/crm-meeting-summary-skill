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


HUMAN_SUMMARY = """会议快照
- 会议目标：确认问题根因

核心总结与判断
- 当前判断：客户要先验证知识库更新机制。

Knowhow 关注点
- 关注项：先做小范围验证。

建议的下一步动作
- 动作：补齐夜间转人工率样本。

风险与待确认问题
- 待确认：最终拍板人
"""

REVIEW_RESULT = {
    "pass": True,
    "review_status": "pass",
    "failure_reasons": [],
    "targeted_regeneration_instructions": [],
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



def test_extract_final_text_prefers_human_summary_block():
    final_text = real_runner.extract_final_text(CLI_SUCCESS_PAYLOAD)

    assert final_text.startswith("会议快照")
    assert "核心总结与判断" in final_text
    assert "风险与待确认问题" in final_text



def test_extract_review_result_from_summary_trailer():
    final_text = real_runner.extract_final_text(REVIEW_RESULT_PAYLOAD)
    review_result = real_runner.extract_review_result(REVIEW_RESULT_PAYLOAD[0]["message"]["content"][0]["text"])

    assert final_text == HUMAN_SUMMARY.rstrip()
    assert "```json" not in final_text
    assert review_result == REVIEW_RESULT



def test_extract_final_text_falls_back_when_no_summary_exists():
    final_text = real_runner.extract_final_text(REVIEW_ONLY_PAYLOAD)

    assert "review_status" in final_text



def test_extract_review_result_returns_none_for_non_review_json():
    review_result = real_runner.extract_review_result("会议快照\n```json\n{}\n```")

    assert review_result is None



def test_parse_cli_payload_ignores_log_prefix():
    stdout = "(eval):1: bad pattern\n" + json.dumps(CLI_SUCCESS_PAYLOAD, ensure_ascii=False)

    parsed = real_runner.parse_cli_payload(stdout)

    assert parsed[-1]["type"] == "result"
    assert parsed[-1]["result"].startswith("会议快照")



def test_build_skill_prompt_uses_human_only_contract(tmp_path: Path):
    input_path = tmp_path / "bundle.json"
    input_path.write_text("{}", encoding="utf-8")

    prompt = real_runner.build_skill_prompt(input_path)

    assert str(input_path) in prompt
    assert "按 skill 契约完成输出" in prompt
    assert "最终结果只保留人类可读总结" in prompt
    assert "不要输出 machine JSON" in prompt
    assert "完整 machine JSON" not in prompt
    assert "输入包是 JSON 文件，不是 PDF" in prompt
    assert "非 PDF 的 Read 调用不要传 pages 字段" in prompt



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
    assert bundle["constraints"] == {"language": "zh-CN", "output_mode": "human_only"}



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
    assert bundle["constraints"] == {"language": "zh-CN", "output_mode": "human_only"}



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
    assert result["final_text"].startswith("会议快照")
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
