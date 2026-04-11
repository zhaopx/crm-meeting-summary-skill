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


def validate_human_summary(final_text: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(final_text, str) or not final_text.strip():
        return ["final_text 不能为空"]

    for title in REQUIRED_SECTION_TITLES:
        if title not in final_text:
            errors.append(f"缺少总结章节: {title}")

    if "machine JSON" in final_text or "machine output" in final_text:
        errors.append("最终总结不应要求 machine output")

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


def validate_case_expectations(case_id: str, final_text: str, review_result: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []

    if case_id == "baseline-template-apply" and "会议快照" not in final_text:
        errors.append("template baseline case 必须输出模板重排后的会议快照")

    if case_id == "adversarial-template-no-fabrication" and "[missing]" not in final_text:
        errors.append("template no-fabrication case 必须显式保留缺失项")

    if case_id == "baseline-low-confidence-fallback":
        uncertain_markers = ("其他 / 不确定", "不确定", "待确认")
        if not any(marker in final_text for marker in uncertain_markers):
            errors.append("low confidence case 必须在总结中暴露不确定边界")

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

    return errors
