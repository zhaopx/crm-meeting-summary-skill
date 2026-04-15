from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[2]
HELPERS_DIR = REPO_ROOT / "tests" / "crm_meeting_summary" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from contract_validator import (  # noqa: E402
    validate_audit_payload,
    validate_audit_presence,
    validate_case_expectations,
    validate_human_summary,
    validate_review_presence,
    validate_review_result,
)
from real_runner import run_case  # noqa: E402


DEFAULT_CASE_IDS = [
    "baseline-low-confidence-fallback",
    "baseline-template-apply",
    "regression-memory-conflict",
    "regression-retry-exhausted",
    "regression-template-uncertain-fallback",
    "adversarial-overpull-trace",
    "adversarial-template-no-fabrication",
]
OUTPUT_DIR = EVALS_DIR / "results"


def safe_text(value: Any) -> str:
    if value in (None, ""):
        return "N/A"
    return str(value)


def safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def build_dashboard_report(eval_result: dict[str, Any]) -> dict[str, Any]:
    final_text = safe_text(eval_result.get("final_text"))
    review_result = eval_result.get("review_result")
    review_status = review_result.get("review_status") if isinstance(review_result, dict) else "N/A"
    failure_reasons = (
        safe_list(review_result.get("failure_reasons"))
        if isinstance(review_result, dict)
        else []
    )

    return {
        "report_meta": {
            "report_version": "human-summary-from-real-evals",
            "generated_at": "N/A",
            "skill_name": "crm-meeting-summary",
            "source_case": safe_text(eval_result.get("case_id")),
            "notes": "由 run_real_evals.py 基于单 case 输出自动生成 human-summary dashboard 数据。",
        },
        "comparison": {
            "source_material": {
                "source_case": safe_text(eval_result.get("case_id")),
                "source_note": "当前 dashboard 聚焦最终人类总结与 review 结果。",
            },
            "summaries": [
                {
                    "summary_id": "skill-current",
                    "source_type": "skill",
                    "source_label": "Skill 总结",
                    "version_label": "real-eval-output",
                    "body_sections": [
                        {
                            "title": "Summary",
                            "content": final_text,
                        }
                    ],
                    "review_status": review_status,
                    "failure_reasons": failure_reasons,
                }
            ],
            "evaluation": {
                "winner_summary_id": "skill-current",
                "reviewer_callout": "当前 report 由单 case 自动转换生成，适合诊断，不代表多来源比较结论。",
                "ranking": ["Skill 总结：当前唯一自动接入版本。"],
            },
            "auxiliary": {
                "review_result": review_result if isinstance(review_result, dict) else {},
                "passed": bool(eval_result.get("passed")),
            },
        },
    }


def serialize_dashboard_report(report: dict[str, Any]) -> str:
    return f"window.__REPORT_DATA__ = {json.dumps(report, ensure_ascii=False, indent=2)};\n"


def build_accuracy_report(
    summary_errors: list[str],
    review_errors: list[str],
    case_errors: list[str],
    audit_errors: list[str],
) -> dict[str, Any]:
    checks = {
        "summary_accuracy": not summary_errors,
        "review_accuracy": not review_errors,
        "case_accuracy": not case_errors,
        "audit_accuracy": not audit_errors,
    }
    passed_checks = sum(1 for passed in checks.values() if passed)
    total_checks = len(checks)
    return {
        **checks,
        "overall_accuracy": passed_checks == total_checks,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "accuracy_breakdown": {
            "summary_errors": summary_errors,
            "review_errors": review_errors,
            "case_errors": case_errors,
            "audit_errors": audit_errors,
        },
    }


def run_eval_case(case_id: str) -> dict[str, Any]:
    captured = run_case(case_id)
    final_text = safe_text(captured.get("final_text"))
    review_result = captured.get("review_result")
    audit_payload = captured.get("audit_payload")
    summary_errors = validate_human_summary(final_text)
    review_presence_errors = validate_review_presence(final_text, review_result)
    review_errors = [
        *review_presence_errors,
        *validate_review_result(review_result),
    ]
    audit_presence_errors = validate_audit_presence(final_text, audit_payload)
    audit_errors = [
        *audit_presence_errors,
        *validate_audit_payload(audit_payload),
    ]
    try:
        case_errors = validate_case_expectations(case_id, final_text, review_result, audit_payload)
    except TypeError:
        case_errors = validate_case_expectations(case_id, final_text, review_result)
    accuracy = build_accuracy_report(summary_errors, review_errors, case_errors, audit_errors)
    verdict = accuracy["overall_accuracy"]
    return {
        "case_id": case_id,
        "raw_response": captured.get("raw_response"),
        "final_text": final_text,
        "review_result": review_result,
        "audit_payload": audit_payload,
        "summary_verdict": {"passed": not summary_errors, "errors": summary_errors},
        "review_verdict": {"passed": not review_errors, "errors": review_errors},
        "audit_verdict": {"passed": not audit_errors, "errors": audit_errors},
        "case_verdict": {"passed": not case_errors, "errors": case_errors},
        "accuracy": accuracy,
        "passed": verdict,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real crm-meeting-summary eval cases")
    parser.add_argument("case_ids", nargs="*", default=DEFAULT_CASE_IDS)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_eval_case(case_id) for case_id in args.case_ids]
    for result in results:
        output_path = OUTPUT_DIR / f"{result['case_id']}.json"
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
