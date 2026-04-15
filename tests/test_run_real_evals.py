from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_REAL_EVALS_PATH = REPO_ROOT / "tests" / "crm_meeting_summary" / "evals" / "run_real_evals.py"
VALIDATOR_PATH = REPO_ROOT / "tests" / "crm_meeting_summary" / "helpers" / "contract_validator.py"



def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def load_validator(module_name: str):
    return load_module(VALIDATOR_PATH, module_name)


def test_validate_human_summary_rejects_internal_process_markers():
    validator = load_validator("contract_validator_internal_process_markers")
    final_text = """会议快照
- 会议目标：确认问题根因

核心总结与判断
- 当前判断：客户要先验证知识库更新机制。

Knowhow 关注点
- retrieval_trace: 不应出现在正文

建议的下一步动作
- 动作：补齐夜间转人工率样本。

风险与待确认问题
- 待确认：最终拍板人
"""

    errors = validator.validate_human_summary(final_text)

    assert errors == ["最终总结混入内部过程字段: retrieval_trace"]



def test_validate_review_presence_accepts_embedded_review_json_block():
    validator = load_validator("contract_validator_review_embedded")
    final_text = """# 会议快照\n- 已输出总结\n\n```json\n{\"pass\": true, \"review_status\": \"pass\", \"failure_reasons\": [], \"targeted_regeneration_instructions\": []}\n```"""

    errors = validator.validate_review_presence(final_text, None)

    assert errors == []



def test_validate_audit_presence_rejects_missing_audit_payload():
    validator = load_validator("contract_validator_audit_presence_missing")

    errors = validator.validate_audit_presence(HUMAN_SUMMARY, None)

    assert errors == ["真实 skill 输出缺少 audit JSON 结果"]



def test_validate_audit_presence_accepts_embedded_audit_json_block():
    validator = load_validator("contract_validator_audit_presence_embedded")
    final_text = (
        HUMAN_SUMMARY
        + "\n```json\n"
        + json.dumps(AUDIT_PAYLOAD, ensure_ascii=False, indent=2)
        + "\n```"
    )

    errors = validator.validate_audit_presence(final_text, None)

    assert errors == []


HUMAN_SUMMARY = """会议快照
- 会议目标：澄清方案覆盖范围

核心总结与判断
- 当前判断：客户先看短期验证结果。

风险与待确认问题
- 待确认：最终拍板人
"""

CASE002_SUMMARY = """会议快照
- 会议目标：澄清酒店客户经营与高层推进范围

核心总结与判断
- 当前判断：客户经营推进已进入关键识别阶段，CEO 关注是否具备立项条件，但正式立项时间待确认。

Knowhow 关注点
- 关注项：围绕联系人经营、拜访动作、评分模型与预警机制收敛高层推进路径。

建议的下一步动作
- 动作：结合 CEO 关注点补齐联系人经营现状、拜访计划和评分模型预警方案，支撑后续立项讨论。

风险与待确认问题
- 待确认：正式立项时间与最终拍板节奏。
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
        "primary_scenario": "客户经营 / 高层推进",
        "scenario_slug": "hotel-operations",
        "scenario_confidence": "medium",
        "secondary_tags": ["联系人管理"],
        "industry": "hotel",
        "reasoning_signals": {
            "supporting": ["联系人", "CEO", "立项"],
            "conflicting": [],
            "rejected_candidates": ["知识库优化"],
        },
    },
    "meeting_state_features": {
        "relationship_state": "active",
        "decision_pressure": "medium",
        "trust_state": "neutral",
        "momentum_state": "forward",
    },
    "retrieval_trace": {
        "policy_version": "taxonomy-v2-runtime-v3",
        "scenario_mode": "normal",
        "allowed_request_groups": ["stakeholder_gap"],
        "requested_request_groups": ["stakeholder_gap"],
        "out_of_policy_requests": [],
    },
    "loaded_knowhow": ["common", "by-scenario/hotel-operations"],
    "claim_evidence_map": [
        {
            "claim_type": "judgment",
            "claim_text": "客户更关注联系人管理与评分预警",
            "evidence": [
                {
                    "source_type": "meeting",
                    "source_ref": "meeting-record.txt:1",
                    "excerpt": "客户更关注联系人管理、拜访计划和评分预警。",
                }
            ],
        }
    ],
    "missing_information": ["正式立项时间"],
    "memory_conflicts": [],
    "template_trace": {"template_path": None, "mapping_gaps": []},
    "review_trace": {
        "review_status": "pass",
        "failure_reasons": [],
        "targeted_regeneration_instructions": [],
        "regeneration_count": 0,
    },
}



def test_run_eval_case_keeps_final_text_and_review_result(monkeypatch):
    monkeypatch.syspath_prepend(str(RUN_REAL_EVALS_PATH.parent))
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals")

    def fake_run_case(case_id: str):
        return {
            "case": {"id": case_id},
            "raw_response": [{"type": "result", "result": "raw"}],
            "final_text": HUMAN_SUMMARY,
            "review_result": REVIEW_RESULT,
            "audit_payload": AUDIT_PAYLOAD,
        }

    monkeypatch.setattr(run_real_evals, "run_case", fake_run_case)
    monkeypatch.setattr(run_real_evals, "validate_human_summary", lambda final_text: [])
    monkeypatch.setattr(run_real_evals, "validate_review_result", lambda review_result: [])
    monkeypatch.setattr(
        run_real_evals,
        "validate_case_expectations",
        lambda case_id, final_text, review_result, audit_payload=None: [],
    )

    result = run_real_evals.run_eval_case("baseline-low-confidence-fallback")

    assert result["final_text"].startswith("会议快照")
    assert result["review_result"] == REVIEW_RESULT
    assert result["audit_payload"] == AUDIT_PAYLOAD
    assert result["summary_verdict"] == {"passed": True, "errors": []}
    assert result["review_verdict"] == {"passed": True, "errors": []}
    assert result["audit_verdict"] == {"passed": True, "errors": []}
    assert result["case_verdict"] == {"passed": True, "errors": []}
    assert result["accuracy"]["audit_accuracy"] is True
    assert result["passed"] is True



def test_run_eval_case_marks_failed_verdicts(monkeypatch):
    monkeypatch.syspath_prepend(str(RUN_REAL_EVALS_PATH.parent))
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_failures")

    monkeypatch.setattr(
        run_real_evals,
        "run_case",
        lambda case_id: {
            "case": {"id": case_id},
            "raw_response": [],
            "final_text": HUMAN_SUMMARY,
            "review_result": REVIEW_RESULT,
        },
    )
    monkeypatch.setattr(run_real_evals, "validate_human_summary", lambda final_text: ["缺少章节"])
    monkeypatch.setattr(run_real_evals, "validate_review_result", lambda review_result: ["review_result 非法"])
    monkeypatch.setattr(run_real_evals, "validate_audit_presence", lambda final_text, audit_payload: ["缺少 audit"])
    monkeypatch.setattr(run_real_evals, "validate_audit_payload", lambda audit_payload: ["audit_payload 非法"])
    monkeypatch.setattr(
        run_real_evals,
        "validate_case_expectations",
        lambda case_id, final_text, review_result: ["case 断言失败"],
    )

    result = run_real_evals.run_eval_case("baseline-template-apply")

    assert result["summary_verdict"] == {"passed": False, "errors": ["缺少章节"]}
    assert result["review_verdict"] == {"passed": False, "errors": ["review_result 非法"]}
    assert result["audit_verdict"] == {"passed": False, "errors": ["缺少 audit", "audit_payload 非法"]}
    assert result["case_verdict"] == {"passed": False, "errors": ["case 断言失败"]}
    assert result["accuracy"]["audit_accuracy"] is False
    assert result["passed"] is False



def test_build_dashboard_report_outputs_summary_only_payload():
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_dashboard_report")
    eval_result = {
        "case_id": "baseline-template-apply",
        "final_text": HUMAN_SUMMARY,
        "review_result": REVIEW_RESULT,
        "passed": True,
    }

    report = run_real_evals.build_dashboard_report(eval_result)

    assert report["comparison"]["source_material"]["source_case"] == "baseline-template-apply"
    assert report["comparison"]["summaries"][0]["summary_id"] == "skill-current"
    assert report["comparison"]["summaries"][0]["body_sections"][0]["content"] == HUMAN_SUMMARY
    assert report["comparison"]["summaries"][0]["review_status"] == "pass"
    assert report["comparison"]["summaries"][0]["failure_reasons"] == []
    assert report["comparison"]["auxiliary"]["review_result"] == REVIEW_RESULT
    assert report["comparison"]["auxiliary"]["passed"] is True



def test_serialize_dashboard_report_wraps_window_assignment():
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_dashboard_js")
    report = {
        "report_meta": {"skill_name": "crm-meeting-summary"},
        "comparison": {"source_material": {"source_case": "case-001"}, "summaries": [], "evaluation": {}, "auxiliary": {}},
    }

    js_payload = run_real_evals.serialize_dashboard_report(report)

    assert js_payload.startswith("window.__REPORT_DATA__ = ")
    assert js_payload.strip().endswith(";")
    encoded = js_payload.removeprefix("window.__REPORT_DATA__ = ").rstrip(";\n")
    assert json.loads(encoded) == report



def test_build_dashboard_report_tolerates_missing_review_result():
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_dashboard_safe")
    eval_result = {
        "case_id": "case-002",
        "final_text": None,
        "review_result": None,
        "passed": False,
    }

    report = run_real_evals.build_dashboard_report(eval_result)

    assert report["comparison"]["source_material"]["source_case"] == "case-002"
    assert report["comparison"]["summaries"][0]["body_sections"][0]["content"] == "N/A"
    assert report["comparison"]["summaries"][0]["review_status"] == "N/A"
    assert report["comparison"]["summaries"][0]["failure_reasons"] == []
    assert report["comparison"]["auxiliary"]["review_result"] == {}
    assert report["comparison"]["auxiliary"]["passed"] is False



def test_run_eval_case_preserves_raw_response(monkeypatch):
    monkeypatch.syspath_prepend(str(RUN_REAL_EVALS_PATH.parent))
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_raw_response")
    raw_response = [{"type": "result", "result": "raw"}]

    monkeypatch.setattr(
        run_real_evals,
        "run_case",
        lambda case_id: {
            "case": {"id": case_id},
            "raw_response": raw_response,
            "final_text": HUMAN_SUMMARY,
            "review_result": REVIEW_RESULT,
        },
    )
    monkeypatch.setattr(run_real_evals, "validate_human_summary", lambda final_text: [])
    monkeypatch.setattr(run_real_evals, "validate_review_result", lambda review_result: [])
    monkeypatch.setattr(
        run_real_evals,
        "validate_case_expectations",
        lambda case_id, final_text, review_result, audit_payload=None: [],
    )

    result = run_real_evals.run_eval_case("baseline-template-apply")

    assert result["raw_response"] == raw_response



def test_run_eval_case_tolerates_legacy_three_arg_case_validator(monkeypatch):
    monkeypatch.syspath_prepend(str(RUN_REAL_EVALS_PATH.parent))
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_legacy_case_validator")

    monkeypatch.setattr(
        run_real_evals,
        "run_case",
        lambda case_id: {
            "case": {"id": case_id},
            "raw_response": [],
            "final_text": HUMAN_SUMMARY,
            "review_result": REVIEW_RESULT,
            "audit_payload": AUDIT_PAYLOAD,
        },
    )
    monkeypatch.setattr(run_real_evals, "validate_human_summary", lambda final_text: [])
    monkeypatch.setattr(run_real_evals, "validate_review_result", lambda review_result: [])
    monkeypatch.setattr(run_real_evals, "validate_audit_payload", lambda audit_payload: [])
    monkeypatch.setattr(
        run_real_evals,
        "validate_case_expectations",
        lambda case_id, final_text, review_result: [],
    )

    result = run_real_evals.run_eval_case("baseline-template-apply")

    assert result["case_verdict"] == {"passed": True, "errors": []}
    assert result["audit_verdict"] == {"passed": True, "errors": []}



def test_run_eval_case_keeps_case_specific_verdict_for_case002(monkeypatch):
    monkeypatch.syspath_prepend(str(RUN_REAL_EVALS_PATH.parent))
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_case002")

    monkeypatch.setattr(
        run_real_evals,
        "run_case",
        lambda case_id: {
            "case": {"id": case_id},
            "raw_response": [],
            "final_text": CASE002_SUMMARY,
            "review_result": REVIEW_RESULT,
        },
    )

    result = run_real_evals.run_eval_case("baseline-case002-hotel-operations")

    assert result["case_verdict"] == {"passed": True, "errors": []}
    assert result["passed"] is True



def test_run_eval_case_surfaces_case002_overfitting_failure(monkeypatch):
    monkeypatch.syspath_prepend(str(RUN_REAL_EVALS_PATH.parent))
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals_case002_failure")

    overfit_summary = """会议快照
- 会议目标：定位客服机器人问题

核心总结与判断
- 当前判断：客户担心夜间转人工率，需要先做知识库试点优化，项目已确定成交。

Knowhow 关注点
- 关注项：继续诊断知识库。

建议的下一步动作
- 动作：补齐夜间转人工率样本。

风险与待确认问题
- 待确认：无。
"""

    monkeypatch.setattr(
        run_real_evals,
        "run_case",
        lambda case_id: {
            "case": {"id": case_id},
            "raw_response": [],
            "final_text": overfit_summary,
            "review_result": REVIEW_RESULT,
        },
    )

    result = run_real_evals.run_eval_case("baseline-case002-hotel-operations")

    assert result["case_verdict"]["passed"] is False
    assert any("旧 case 话术" in error or "已确定结论" in error for error in result["case_verdict"]["errors"])
    assert result["passed"] is False



def test_validate_case_expectations_flags_template_expansion():
    validator = load_validator("contract_validator_template_expansion")
    final_text = """会议快照
- 会议目标：确认问题根因

核心总结与判断
- 当前判断：客户要先验证知识库更新机制。
- 明确结论：已确定直接推进。

Knowhow 关注点
- 关注项：[missing]

建议的下一步动作
- 动作：必须立即上线。

风险与待确认问题
- 待确认：最终拍板人
补充说明：这里新增了一段模板扩写。
"""

    errors = validator.validate_case_expectations(
        "adversarial-template-no-fabrication",
        final_text,
        REVIEW_RESULT,
    )

    assert any("不应新增确定性判断" in error for error in errors)
    assert any("不应新增自由发挥段落" in error for error in errors)



def test_validate_case_expectations_accepts_template_reorder_without_new_claims():
    validator = load_validator("contract_validator_template_allowed")
    final_text = """会议快照
- 会议目标：确认问题根因

核心总结与判断
- 当前判断：客户要先验证知识库更新机制。

Knowhow 关注点
- 关注项：[missing]

建议的下一步动作
- 动作：补齐夜间转人工率样本。

风险与待确认问题
- 待确认：最终拍板人
"""

    errors = validator.validate_case_expectations(
        "adversarial-template-no-fabrication",
        final_text,
        REVIEW_RESULT,
    )

    assert errors == []
