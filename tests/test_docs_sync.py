from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
CASE_EXAMPLE_PATH = (
    REPO_ROOT / "skills" / "crm-meeting-summary" / "examples" / "case-execution-example.md"
)
EXAMPLE_INPUT_PATH = (
    REPO_ROOT / "skills" / "crm-meeting-summary" / "examples" / "example-input.md"
)
EXAMPLE_OUTPUT_PATH = (
    REPO_ROOT / "skills" / "crm-meeting-summary" / "examples" / "example-output.md"
)
RUNTIME_CONTRACT_PATH = (
    REPO_ROOT / "skills" / "crm-meeting-summary" / "references" / "runtime-contract.md"
)
OUTPUT_SCHEMA_PATH = (
    REPO_ROOT / "skills" / "crm-meeting-summary" / "references" / "output-schema.md"
)
SKILL_PATH = REPO_ROOT / "skills" / "crm-meeting-summary" / "SKILL.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")



def test_docs_describe_real_output_capture_surface():
    readme_text = read_text(README_PATH)
    case_example_text = read_text(CASE_EXAMPLE_PATH)

    assert "real_runner.py" in readme_text
    assert "run_real_evals.py" in readme_text
    assert "完整最终返回值" in case_example_text
    assert "raw_response" in case_example_text
    assert "extracted_machine_json" in case_example_text



def test_docs_keep_record_text_path_contract_in_sync():
    readme_text = read_text(README_PATH)
    skill_text = read_text(SKILL_PATH)
    runtime_contract_text = read_text(RUNTIME_CONTRACT_PATH)
    example_input_text = read_text(EXAMPLE_INPUT_PATH)
    case_example_text = read_text(CASE_EXAMPLE_PATH)

    required_markers = [
        "record_text_path",
        "record_text > record_text_path",
    ]

    for marker in required_markers:
        assert marker in readme_text
        assert marker in skill_text
        assert marker in runtime_contract_text

    assert "record_text_path" in example_input_text
    assert "record_text_path" in case_example_text




def test_docs_keep_input_bundle_path_contract_in_sync():
    readme_text = read_text(README_PATH)
    skill_text = read_text(SKILL_PATH)
    runtime_contract_text = read_text(RUNTIME_CONTRACT_PATH)
    example_input_text = read_text(EXAMPLE_INPUT_PATH)
    case_example_text = read_text(CASE_EXAMPLE_PATH)

    required_markers = [
        "input_bundle_path",
        "meeting-record.txt",
        "AccountObj.json",
        "NewOpportunityObj.json",
        "PersonnelObj.json",
        "record_text > record_text_path > input_bundle_path/meeting-record.txt",
    ]

    for marker in required_markers:
        assert marker in readme_text
        assert marker in skill_text
        assert marker in runtime_contract_text

    assert "input_bundle_path" in example_input_text
    assert "meeting-record.txt" in case_example_text
    assert "AccountObj.json" in case_example_text



def test_docs_keep_runtime_contract_and_example_output_in_sync():
    runtime_contract_text = read_text(RUNTIME_CONTRACT_PATH)
    example_output_text = read_text(EXAMPLE_OUTPUT_PATH)
    output_schema_text = read_text(OUTPUT_SCHEMA_PATH)

    required_markers = [
        "semantic_normalization",
        "meeting_state_features",
        "semantic_summary",
        "retrieval_trace",
        "retry_state",
        "review_ready_checks",
        "manual_review_required",
    ]

    for marker in required_markers:
        assert marker in runtime_contract_text
        assert marker in example_output_text
        assert marker in output_schema_text
