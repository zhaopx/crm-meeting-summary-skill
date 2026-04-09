from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contract_validator import validate_case_expectations, validate_machine_output


EVALS_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from real_runner import run_case


DEFAULT_CASE_IDS = [
    "baseline-low-confidence-fallback",
    "regression-memory-conflict",
    "regression-retry-exhausted",
    "adversarial-overpull-trace",
]
OUTPUT_DIR = EVALS_DIR / "results"


def run_eval_case(case_id: str) -> dict:
    captured = run_case(case_id)
    machine_output = captured["extracted_machine_json"]
    contract_errors = validate_machine_output(machine_output)
    case_errors = validate_case_expectations(case_id, machine_output)
    verdict = not contract_errors and not case_errors
    return {
        "case_id": case_id,
        "raw_response": captured["raw_response"],
        "final_text": captured["final_text"],
        "extracted_machine_json": machine_output,
        "extraction_meta": captured["extraction_meta"],
        "contract_verdict": {"passed": not contract_errors, "errors": contract_errors},
        "case_verdict": {"passed": not case_errors, "errors": case_errors},
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
