from __future__ import annotations

from typing import Any


REQUIRED_SECTION_TITLES = (
    "会议快照",
    "核心总结与判断",
    "Knowhow 关注点",
    "建议的下一步动作",
    "风险与待确认问题",
)

REQUIRED_REVIEW_KEYS = (
    "pass",
    "review_status",
    "failure_reasons",
    "targeted_regeneration_instructions",
)

REQUIRED_REVIEW_MARKERS = (
    "```json",
    '"review_status"',
    '"failure_reasons"',
)

REQUIRED_INTERNAL_PROCESS_MARKERS = (
    "semantic_normalization",
    "meeting_state_features",
    "retrieval_trace",
    "loaded_knowhow",
    "template_trace",
    "review_trace",
    "audit_payload",
    '"review_status"',
    '"failure_reasons"',
    '"targeted_regeneration_instructions"',
    "语义归一",
    "定向修复",
    "regeneration",
)


REQUIRED_AUDIT_TOP_LEVEL_KEYS = (
    "schema_version",
    "scenario_decision",
    "meeting_state_features",
    "retrieval_trace",
    "loaded_knowhow",
    "claim_evidence_map",
    "missing_information",
    "memory_conflicts",
    "template_trace",
    "review_trace",
)


_TEMPLATE_ONLY_ALLOWED_TOKENS = (
    "会议快照",
    "核心总结与判断",
    "Knowhow 关注点",
    "建议的下一步动作",
    "风险与待确认问题",
    "待确认",
    "missing",
    "[missing]",
    "未提供",
)

_TEMPLATE_ONLY_FORBIDDEN_TOKENS = (
    "已确定",
    "已拍板",
    "明确结论",
    "直接推进",
    "必须立即",
)


def validate_human_summary(final_text: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(final_text, str) or not final_text.strip():
        return ["final_text 不能为空"]

    for title in REQUIRED_SECTION_TITLES:
        if title not in final_text:
            errors.append(f"缺少总结章节: {title}")

    if "machine JSON" in final_text or "machine output" in final_text:
        errors.append("最终总结不应要求 machine output")

    leaked_markers = [marker for marker in REQUIRED_INTERNAL_PROCESS_MARKERS if marker in final_text]
    if leaked_markers:
        errors.append(f"最终总结混入内部过程字段: {', '.join(leaked_markers)}")

    return errors


def validate_review_result(review_result: dict[str, Any] | None) -> list[str]:
    if review_result is None:
        return []

    errors: list[str] = []
    for key in REQUIRED_REVIEW_KEYS:
        if key not in review_result:
            errors.append(f"review_result 缺少字段: {key}")
    review_status = review_result.get("review_status")
    if review_status not in {"pass", "fail"}:
        errors.append(f"review_status 非法: {review_status}")
    return errors


def validate_review_presence(final_text: str, review_result: dict[str, Any] | None) -> list[str]:
    if review_result is not None:
        return []

    if not isinstance(final_text, str) or not final_text.strip():
        return ["缺少最终总结，无法验证 review 输出"]

    if all(marker in final_text for marker in REQUIRED_REVIEW_MARKERS):
        return []

    return ["真实 skill 输出缺少 review JSON 结果"]


def validate_audit_presence(final_text: str, audit_payload: dict[str, Any] | None) -> list[str]:
    if audit_payload is not None:
        return []

    if not isinstance(final_text, str) or not final_text.strip():
        return ["缺少最终总结，无法验证 audit 输出"]

    if "```json" in final_text and '"schema_version": "crm-meeting-summary-audit-v1"' in final_text:
        return []

    return ["真实 skill 输出缺少 audit JSON 结果"]


def validate_audit_payload(audit_payload: dict[str, Any] | None) -> list[str]:
    if audit_payload is None:
        return []

    errors: list[str] = []
    if not isinstance(audit_payload, dict):
        return ["audit_payload 必须是对象"]

    for key in REQUIRED_AUDIT_TOP_LEVEL_KEYS:
        if key not in audit_payload:
            errors.append(f"audit_payload 缺少字段: {key}")

    if audit_payload.get("schema_version") != "crm-meeting-summary-audit-v1":
        errors.append(f"audit_payload schema_version 非法: {audit_payload.get('schema_version')}")

    claim_evidence_map = audit_payload.get("claim_evidence_map")
    if not isinstance(claim_evidence_map, list):
        errors.append("audit_payload.claim_evidence_map 必须是数组")
    else:
        for index, item in enumerate(claim_evidence_map):
            if not isinstance(item, dict):
                errors.append(f"claim_evidence_map[{index}] 必须是对象")
                continue
            if item.get("claim_type") not in {"fact", "judgment", "open_question"}:
                errors.append(f"claim_evidence_map[{index}].claim_type 非法")
            if not isinstance(item.get("claim_text"), str) or not item.get("claim_text", "").strip():
                errors.append(f"claim_evidence_map[{index}].claim_text 不能为空")
            evidence = item.get("evidence")
            if not isinstance(evidence, list):
                errors.append(f"claim_evidence_map[{index}].evidence 必须是数组")
                continue
            if item.get("claim_type") in {"fact", "judgment"} and not evidence:
                errors.append(f"claim_evidence_map[{index}] 的高价值结论必须有 evidence")

    review_trace = audit_payload.get("review_trace")
    if isinstance(review_trace, dict):
        if review_trace.get("review_status") not in {"pass", "fail", "not_run"}:
            errors.append(f"review_trace.review_status 非法: {review_trace.get('review_status')}")
    elif "review_trace" in audit_payload:
        errors.append("audit_payload.review_trace 必须是对象")

    scenario_decision = audit_payload.get("scenario_decision")
    if isinstance(scenario_decision, dict):
        confidence = scenario_decision.get("scenario_confidence")
        if confidence not in {"high", "medium", "low"}:
            errors.append(f"scenario_decision.scenario_confidence 非法: {confidence}")
    elif "scenario_decision" in audit_payload:
        errors.append("audit_payload.scenario_decision 必须是对象")

    return errors


def _validate_template_only_output(final_text: str) -> list[str]:
    errors: list[str] = []
    for token in _TEMPLATE_ONLY_FORBIDDEN_TOKENS:
        if token in final_text:
            errors.append(f"template no-fabrication case 不应新增确定性判断: {token}")

    if "[missing]" not in final_text and "missing" not in final_text and "待确认" not in final_text:
        errors.append("template no-fabrication case 必须显式保留缺失项")

    content_lines = [
        line.strip()
        for line in final_text.splitlines()
        if line.strip() and line.strip() not in _TEMPLATE_ONLY_ALLOWED_TOKENS
    ]
    disallowed_lines = [line for line in content_lines if not line.startswith("-")]
    if disallowed_lines:
        errors.append("template no-fabrication case 只允许重排既有条目，不应新增自由发挥段落")

    return errors


def validate_case_expectations(
    case_id: str,
    final_text: str,
    review_result: dict[str, Any] | None,
    audit_payload: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []

    if case_id == "baseline-template-apply" and "会议快照" not in final_text:
        errors.append("template baseline case 必须输出模板重排后的会议快照")

    if case_id == "adversarial-template-no-fabrication":
        errors.extend(_validate_template_only_output(final_text))

    if case_id == "baseline-low-confidence-fallback":
        uncertain_markers = ("其他 / 不确定", "不确定", "待确认")
        if not any(marker in final_text for marker in uncertain_markers):
            errors.append("low confidence case 必须在总结中暴露不确定边界")

    if case_id == "baseline-case002-hotel-operations":
        required_markers = (
            "客户经营",
            "联系人",
            "拜访",
            "评分模型",
            "预警",
            "CEO",
            "立项",
        )
        missing_markers = [marker for marker in required_markers if marker not in final_text]
        if missing_markers:
            errors.append(f"case002 必须覆盖酒店经营场景关键语义: {', '.join(missing_markers)}")

        forbidden_markers = (
            "客服机器人",
            "知识库",
            "夜间转人工率",
            "试点优化",
            "转人工",
        )
        leaked_markers = [marker for marker in forbidden_markers if marker in final_text]
        if leaked_markers:
            errors.append(f"case002 不应复用旧 case 话术: {', '.join(leaked_markers)}")

        if "已正式立项" in final_text or "已确定成交" in final_text or "已拍板" in final_text:
            errors.append("case002 不应把未完成拍板/立项写成已确定结论")

    if case_id == "regression-memory-conflict":
        conflict_markers = ("冲突", "当前会议证据优先", "待确认")
        if not any(marker in final_text for marker in conflict_markers):
            errors.append("memory conflict case 必须暴露冲突或降置信边界")

    if case_id == "regression-retry-exhausted":
        if review_result is None or review_result.get("pass") is not False:
            errors.append("retry exhausted case 必须保留失败 review 结果")

    if case_id == "adversarial-human-summary-consistency":
        if "高风险" in final_text and "已确定成交" in final_text:
            errors.append("人类总结内部结论冲突")

    if audit_payload is not None and case_id == "baseline-case002-hotel-operations":
        scenario_decision = audit_payload.get("scenario_decision") if isinstance(audit_payload, dict) else None
        if isinstance(scenario_decision, dict):
            rejected_candidates = scenario_decision.get("reasoning_signals", {}).get("rejected_candidates", [])
            if not isinstance(rejected_candidates, list):
                errors.append("case002 的 audit payload 必须记录 rejected_candidates")

    return errors

