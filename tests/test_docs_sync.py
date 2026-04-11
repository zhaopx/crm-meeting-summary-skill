from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
CASE_EXAMPLE_PATH = (
    REPO_ROOT / "docs" / "skills" / "crm-meeting-summary" / "case-execution-example.md"
)
EXAMPLE_INPUT_PATH = (
    REPO_ROOT / "docs" / "skills" / "crm-meeting-summary" / "example-input.md"
)
RUNTIME_CONTRACT_PATH = (
    REPO_ROOT / "skills" / "crm-meeting-summary" / "references" / "runtime-contract.md"
)
SKILL_PATH = REPO_ROOT / "skills" / "crm-meeting-summary" / "SKILL.md"
REVIEW_SKILL_PATH = REPO_ROOT / "skills" / "crm-meeting-summary" / "review" / "SKILL.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")



def test_docs_describe_real_output_capture_surface():
    readme_text = read_text(README_PATH)
    case_example_text = read_text(CASE_EXAMPLE_PATH)

    assert "tests/crm_meeting_summary/helpers/real_runner.py" in readme_text
    assert "run_real_evals.py" in readme_text
    assert "raw_response" in case_example_text
    assert "final_text" in case_example_text
    assert "review_result" in case_example_text
    assert "extracted_machine_json" not in case_example_text



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



def test_case_example_step_titles_stay_unique_and_ordered():
    case_example_text = read_text(CASE_EXAMPLE_PATH)

    expected_titles = [
        "## 第 1 步：",
        "## 第 2 步：",
        "## 第 3 步：",
        "## 第 4 步：",
        "## 第 5 步：",
        "## 第 6 步：",
        "## 第 7 步：",
        "## 第 8 步：",
        "## 第 9 步：",
        "## 第 10 步：",
    ]

    positions = []
    for title in expected_titles:
        assert case_example_text.count(title) == 1
        positions.append(case_example_text.index(title))

    assert positions == sorted(positions)



def test_docs_keep_human_only_contract_in_sync():
    runtime_contract_text = read_text(RUNTIME_CONTRACT_PATH)
    case_example_text = read_text(CASE_EXAMPLE_PATH)
    skill_text = read_text(SKILL_PATH)
    review_skill_text = read_text(REVIEW_SKILL_PATH)

    runtime_required_markers = [
        "人类可读总结",
        "人工复核",
        "references/templates/",
    ]
    case_example_required_markers = [
        "review_result",
        "final_text",
        "人类可读总结",
    ]
    review_required_markers = [
        "targeted_regeneration_instructions",
        "template_no_fabrication",
    ]

    for marker in runtime_required_markers:
        assert marker in runtime_contract_text

    for marker in case_example_required_markers:
        assert marker in case_example_text

    assert "最终交付物" in skill_text
    assert "人类可读总结" in skill_text

    for marker in review_required_markers:
        assert marker in review_skill_text



def test_docs_remove_machine_output_contract_markers():
    readme_text = read_text(README_PATH)
    case_example_text = read_text(CASE_EXAMPLE_PATH)
    runtime_contract_text = read_text(RUNTIME_CONTRACT_PATH)
    skill_text = read_text(SKILL_PATH)

    forbidden_markers = [
        "output-schema.md",
        "retry-state-machine.md",
        "完整 machine JSON",
        "review_ready_checks",
        "machine_output_completeness",
    ]

    for marker in forbidden_markers:
        assert marker not in readme_text
        assert marker not in case_example_text
        assert marker not in runtime_contract_text
        assert marker not in skill_text



def test_example_input_uses_human_only_output_mode():
    example_input_text = read_text(EXAMPLE_INPUT_PATH)

    assert '"output_mode"' in example_input_text
    assert 'human_only' in example_input_text
    assert 'human_and_json' not in example_input_text
