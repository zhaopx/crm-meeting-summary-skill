from __future__ import annotations

from typing import Any


REQUIRED_TOP_LEVEL_KEYS = (
    "status",
    "base_context",
    "scenario_result",
    "semantic_normalization",
    "meeting_state_features",
    "loaded_knowhow",
    "crm_data_requests",
    "memory_sources",
    "memory_conflicts",
    "summary_fields",
    "semantic_summary",
    "key_judgments",
    "knowhow_focus_items",
    "retrieval_trace",
    "retry_state",
    "review_ready_checks",
)
REQUIRED_SEMANTIC_KEYS = (
    "relationship_state",
    "decision_pressure",
    "trust_state",
    "momentum_state",
)
REQUIRED_REVIEW_KEYS = (
    "scenario_self_consistency",
    "knowhow_coverage",
    "evidence_grounding",
    "memory_conflict_handling",
    "missing_information_handling",
    "policy_boundary_handling",
    "semantic_normalization_consistency",
    "meeting_state_feature_evidence",
    "semantic_summary_consistency",
    "machine_output_completeness",
)
ALLOWED_STATUS = {"passed", "manual_review_required", "insufficient_context"}


def validate_machine_output(output: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in output:
            errors.append(f"缺少顶层字段: {key}")

    status = output.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"status 非法: {status}")

    semantic_normalization = output.get("semantic_normalization")
    if not isinstance(semantic_normalization, dict):
        errors.append("semantic_normalization 必须是对象")
    else:
        for key in ("object_aliases", "lookup_keys", "resolved_objects", "relationship_map"):
            if key not in semantic_normalization:
                errors.append(f"semantic_normalization 缺少字段: {key}")

    meeting_state_features = output.get("meeting_state_features")
    if not isinstance(meeting_state_features, dict):
        errors.append("meeting_state_features 必须是对象")
    else:
        for key in REQUIRED_SEMANTIC_KEYS:
            if key not in meeting_state_features:
                errors.append(f"meeting_state_features 缺少字段: {key}")

    semantic_summary = output.get("semantic_summary")
    if not isinstance(semantic_summary, dict):
        errors.append("semantic_summary 必须是对象")
    else:
        for key in REQUIRED_SEMANTIC_KEYS:
            if key not in semantic_summary:
                errors.append(f"semantic_summary 缺少字段: {key}")

    review_ready_checks = output.get("review_ready_checks")
    if not isinstance(review_ready_checks, dict):
        errors.append("review_ready_checks 必须是对象")
    else:
        for key in REQUIRED_REVIEW_KEYS:
            if key not in review_ready_checks:
                errors.append(f"review_ready_checks 缺少字段: {key}")

    retrieval_trace = output.get("retrieval_trace")
    if not isinstance(retrieval_trace, dict):
        errors.append("retrieval_trace 必须是对象")
    else:
        for key in (
            "mapping_version",
            "scenario_mode",
            "allowed_request_groups",
            "requested_request_groups",
            "out_of_policy_requests",
        ):
            if key not in retrieval_trace:
                errors.append(f"retrieval_trace 缺少字段: {key}")

    retry_state = output.get("retry_state")
    if not isinstance(retry_state, dict):
        errors.append("retry_state 必须是对象")
    else:
        for key in ("revision", "status", "history"):
            if key not in retry_state:
                errors.append(f"retry_state 缺少字段: {key}")

    return errors


def validate_case_expectations(case_id: str, output: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scenario_result = output.get("scenario_result", {})
    loaded_knowhow = output.get("loaded_knowhow", {})
    retrieval_trace = output.get("retrieval_trace", {})
    retry_state = output.get("retry_state", {})

    if case_id == "baseline-low-confidence-fallback":
        if scenario_result.get("scenario_mode") != "uncertain":
            errors.append("low confidence case 必须输出 scenario_mode=uncertain")
        if loaded_knowhow.get("scenario") not in ([], None):
            errors.append("uncertain 模式不应加载 scenario knowhow")
        if loaded_knowhow.get("patches") not in ([], None):
            errors.append("uncertain 模式不应加载 patch knowhow")
        if len(retrieval_trace.get("requested_request_groups", [])) > 1:
            errors.append("uncertain 模式最多只允许一个消歧 request bundle")

    if case_id == "regression-memory-conflict" and not output.get("memory_conflicts"):
        errors.append("memory conflict case 必须输出 memory_conflicts")

    if case_id == "regression-retry-exhausted":
        if output.get("status") != "manual_review_required":
            errors.append("retry exhausted case 必须停在 manual_review_required")
        if retry_state.get("revision") != 2:
            errors.append("retry exhausted case 的 retry_state.revision 必须等于 2")

    if case_id == "adversarial-overpull-trace" and retrieval_trace.get("out_of_policy_requests") not in ([], None):
        errors.append("overpull case 不应出现未解释的 out_of_policy_requests")

    return errors
