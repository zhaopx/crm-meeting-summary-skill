from __future__ import annotations

import importlib.util
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


def test_run_eval_case_keeps_final_text(monkeypatch):
    monkeypatch.syspath_prepend(str(RUN_REAL_EVALS_PATH.parent))
    run_real_evals = load_module(RUN_REAL_EVALS_PATH, "run_real_evals")

    def fake_run_case(case_id: str):
        return {
            "case": {"id": case_id},
            "raw_response": [{"type": "result", "result": "raw"}],
            "final_text": "会议快照\n```json\n{}\n```",
            "extracted_machine_json": {
                "status": "passed",
                "base_context": {},
                "scenario_result": {},
                "semantic_normalization": {
                    "object_aliases": {},
                    "lookup_keys": {},
                    "resolved_objects": {},
                    "relationship_map": [],
                },
                "meeting_state_features": {
                    "relationship_state": "x",
                    "decision_pressure": "x",
                    "trust_state": "x",
                    "momentum_state": "x",
                },
                "loaded_knowhow": {},
                "crm_data_requests": [],
                "memory_sources": [],
                "memory_conflicts": [],
                "summary_fields": {},
                "semantic_summary": {},
                "key_judgments": {},
                "knowhow_focus_items": [],
                "retrieval_trace": {},
                "retry_state": {},
                "review_ready_checks": {},
            },
            "extraction_meta": {"source": "fenced_json"},
        }

    monkeypatch.setattr(run_real_evals, "run_case", fake_run_case)
    monkeypatch.setattr(run_real_evals, "validate_machine_output", lambda output: [])
    monkeypatch.setattr(
        run_real_evals,
        "validate_case_expectations",
        lambda case_id, output: [],
    )

    result = run_real_evals.run_eval_case("baseline-low-confidence-fallback")

    assert result["final_text"].startswith("会议快照")
    assert result["extraction_meta"] == {"source": "fenced_json"}
    assert result["passed"] is True
