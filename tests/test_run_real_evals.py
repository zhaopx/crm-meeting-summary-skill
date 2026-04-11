from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_REAL_EVALS_PATH = REPO_ROOT / "tests" / "crm_meeting_summary" / "evals" / "run_real_evals.py"


def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HUMAN_SUMMARY = """会议快照
- 会议目标：澄清方案覆盖范围

核心总结与判断
- 当前判断：客户先看短期验证结果。

风险与待确认问题
- 待确认：最终拍板人
"""

REVIEW_RESULT = {
    "pass": True,
    "review_status": "pass",
    "failure_reasons": [],
    "targeted_regeneration_instructions": [],
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
        }

    monkeypatch.setattr(run_real_evals, "run_case", fake_run_case)
    monkeypatch.setattr(run_real_evals, "validate_human_summary", lambda final_text: [])
    monkeypatch.setattr(run_real_evals, "validate_review_result", lambda review_result: [])
    monkeypatch.setattr(
        run_real_evals,
        "validate_case_expectations",
        lambda case_id, final_text, review_result: [],
    )

    result = run_real_evals.run_eval_case("baseline-low-confidence-fallback")

    assert result["final_text"].startswith("会议快照")
    assert result["review_result"] == REVIEW_RESULT
    assert result["summary_verdict"] == {"passed": True, "errors": []}
    assert result["review_verdict"] == {"passed": True, "errors": []}
    assert result["case_verdict"] == {"passed": True, "errors": []}
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
    monkeypatch.setattr(
        run_real_evals,
        "validate_case_expectations",
        lambda case_id, final_text, review_result: ["case 断言失败"],
    )

    result = run_real_evals.run_eval_case("baseline-template-apply")

    assert result["summary_verdict"] == {"passed": False, "errors": ["缺少章节"]}
    assert result["review_verdict"] == {"passed": False, "errors": ["review_result 非法"]}
    assert result["case_verdict"] == {"passed": False, "errors": ["case 断言失败"]}
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
        lambda case_id, final_text, review_result: [],
    )

    result = run_real_evals.run_eval_case("baseline-template-apply")

    assert result["raw_response"] == raw_response
