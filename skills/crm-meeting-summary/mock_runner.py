from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = Path(__file__).resolve().parent
MOCK_DATA_DIR = SKILL_DIR.parent / "mock-runtime"
SCENARIO_KNOWHOW_DIR = SKILL_DIR / "references" / "knowhow" / "by-scenario"
PATCH_KNOWHOW_DIR = SKILL_DIR / "references" / "knowhow" / "patches"
INDUSTRY_KNOWHOW_DIR = SKILL_DIR / "references" / "knowhow" / "by-industry"
COMMON_KNOWHOW_PATH = SKILL_DIR / "references" / "knowhow" / "common" / "general.md"
BEST_CASES_DIR = SKILL_DIR / "references" / "knowhow" / "best-cases"
SCENARIO_MAPPING_PATH = SKILL_DIR / "references" / "scenario-retrieval-mapping.md"
REVIEW_CHECK_KEYS = (
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
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class RequestItem:
    request_group: str
    fields: tuple[str, ...]
    why: str
    priority: str
    conditions: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class ReviewResult:
    passed: bool
    review_status: str
    failure_reasons: tuple[str, ...]
    targeted_regeneration_instructions: tuple[str, ...]
    check_results: dict[str, str]
    notes: tuple[str, ...]


class RunnerError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"读取 JSON 失败: {path} ({exc})") from exc


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerError(f"读取文本失败: {path} ({exc})") from exc


def ensure_path_exists(path: Path | None, label: str) -> None:
    if path is None:
        return
    if not path.exists():
        raise RunnerError(f"{label} 文件不存在: {path}")


def ensure_repo_path(path: Path | None, label: str) -> None:
    if path is None:
        return
    try:
        path.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RunnerError(f"{label} 文件必须位于仓库内: {path}") from exc


def ensure_safe_slug(value: str | None, label: str) -> None:
    if value is None:
        return
    if not SLUG_PATTERN.fullmatch(value):
        raise RunnerError(f"{label} 只能包含小写字母、数字和连字符: {value}")


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def extract_data_requirements(markdown_text: str, source: str) -> list[RequestItem]:
    marker = "## data_requirements"
    start = markdown_text.find(marker)
    if start == -1:
        return []

    fence_start = markdown_text.find("```json", start)
    if fence_start == -1:
        return []
    fence_start += len("```json")
    fence_end = markdown_text.find("```", fence_start)
    if fence_end == -1:
        raise RunnerError(f"{source} 缺少 data_requirements 结束代码块")

    payload = markdown_text[fence_start:fence_end].strip()
    data = json.loads(payload)
    return [
        RequestItem(
            request_group=item["request_group"],
            fields=tuple(item["fields"]),
            why=item["why"],
            priority=item.get("priority", "optional"),
            conditions=tuple(item.get("conditions", [])),
            source=source,
        )
        for item in data
    ]


def load_allowed_request_groups(scenario_slug: str) -> list[str]:
    lines = read_text(SCENARIO_MAPPING_PATH).splitlines()
    target = scenario_slug_to_name(scenario_slug)
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().split("|")[1:-1]]
        if len(cells) != 5:
            continue
        if cells[0] != target:
            continue
        return [group.strip() for group in cells[3].split(",") if group.strip()]
    raise RunnerError(f"未找到场景 {scenario_slug} 的 request groups")


def scenario_slug_to_name(scenario_slug: str) -> str:
    mapping = {
        "first-contact": "首次接触 / 破冰",
        "needs-clarification": "需求澄清",
        "solution-demo": "方案介绍 / 演示",
        "commercial-negotiation": "商务推进 / 谈判",
        "poc-advance": "试点 / PoC 推进",
        "delivery-implementation": "项目交付 / 实施沟通",
        "renewal-expansion": "续约 / 增购",
        "risk-escalation": "风险 / 投诉 / 升级处理",
        "internal-review": "内部协同 / 复盘",
        "uncertain": "其他 / 不确定",
    }
    if scenario_slug not in mapping:
        raise RunnerError(f"未知 scenario slug: {scenario_slug}")
    return mapping[scenario_slug]


def find_mock_source(scope: str, object_id: str | None, object_name: str | None) -> str | None:
    base_dir = MOCK_DATA_DIR / "crm" / scope
    if object_id:
        id_path = base_dir / f"{object_id}.json"
        if id_path.exists():
            return str(id_path.relative_to(REPO_ROOT))
    if object_name:
        name_path = base_dir / f"{object_name}.json"
        if name_path.exists():
            return str(name_path.relative_to(REPO_ROOT))
    return None


def field_exists(field: str, crm_context: dict[str, Any]) -> bool:
    for payload in crm_context.values():
        if isinstance(payload, dict) and field in payload and payload[field] not in (None, [], ""):
            return True
    return False


def condition_matches(record_text: str, condition: str) -> bool:
    if not condition:
        return True
    condition_text = condition.lower()
    record = record_text.lower()
    keyword_map = {
        "owner": ["owner", "负责人", "决策"],
        "信任": ["信任", "承诺", "延期", "效果", "预算", "考核"],
        "承诺": ["承诺", "延期", "约定"],
        "升级": ["升级", "不满", "问题"],
        "历史": ["历史", "反复", "持续"],
        "交付": ["交付", "实施", "阻塞"],
        "预算": ["预算", "优先级"],
        "痛点": ["痛点", "问题", "背景"],
    }
    candidates: list[str] = []
    for key, values in keyword_map.items():
        if key in condition_text:
            candidates.extend(values)
    if not candidates:
        return True
    return any(token in record for token in candidates)


def contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def build_review_ready_checks(check_results: dict[str, str]) -> dict[str, bool]:
    return {key: check_results[key] == "pass" for key in REVIEW_CHECK_KEYS}


class MockRetrievalRunner:
    def __init__(
        self,
        meeting_file: Path,
        scenario_slug: str,
        scenario_confidence: str,
        industry: str | None,
        account_file: Path | None,
        opportunity_file: Path | None,
        person_file: Path | None,
    ) -> None:
        self.meeting_file = meeting_file
        self.scenario_slug = scenario_slug
        self.scenario_confidence = scenario_confidence
        self.industry = industry
        self.account_file = account_file
        self.opportunity_file = opportunity_file
        self.person_file = person_file
        ensure_path_exists(self.meeting_file, "meeting")
        ensure_path_exists(self.account_file, "account")
        ensure_path_exists(self.opportunity_file, "opportunity")
        ensure_path_exists(self.person_file, "person")
        ensure_repo_path(self.meeting_file, "meeting")
        ensure_repo_path(self.account_file, "account")
        ensure_repo_path(self.opportunity_file, "opportunity")
        ensure_repo_path(self.person_file, "person")
        ensure_safe_slug(self.industry, "industry")

    def run(self) -> dict[str, Any]:
        runtime = self.build_context()
        review_history: list[dict[str, Any]] = []

        for revision in range(3):
            draft = self.generate_draft(runtime=runtime, revision=revision, review_history=review_history)
            review_result = self.review_output(draft=draft, runtime=runtime, revision=revision)
            if review_result.passed:
                retry_state = {
                    "revision": revision,
                    "status": "passed",
                    "history": review_history,
                }
                return self.finalize_output(
                    draft=draft,
                    review_result=review_result,
                    retry_state=retry_state,
                    status="passed",
                )

            if revision == 2:
                retry_state = {
                    "revision": revision,
                    "status": "manual_review_required",
                    "history": review_history,
                }
                return self.finalize_output(
                    draft=draft,
                    review_result=review_result,
                    retry_state=retry_state,
                    status="manual_review_required",
                )

            review_history = review_history + [
                {
                    "revision": revision,
                    "review_status": review_result.review_status,
                    "failed_checks": [
                        key for key, value in review_result.check_results.items() if value == "fail"
                    ],
                }
            ]

        raise RunnerError("未能完成 summary 生成")

    def build_context(self) -> dict[str, Any]:
        meeting_payload = load_json(self.meeting_file)
        meeting = meeting_payload["meeting"]
        crm_context = self._load_crm_context()
        record_text = meeting.get("record_text", "")
        allowed_request_groups = load_allowed_request_groups(self.scenario_slug)
        scenario_mode = "uncertain" if self.scenario_confidence == "low" else "normal"
        retrieval = self.plan_retrieval(
            record_text=record_text,
            crm_context=crm_context,
            allowed_request_groups=allowed_request_groups,
            scenario_mode=scenario_mode,
        )
        semantic_normalization = self.build_semantic_normalization(meeting=meeting, crm_context=crm_context)
        meeting_state_features = self.build_meeting_state_features(
            runtime={
                "record_text": record_text,
                "scenario_mode": scenario_mode,
            },
            revision=0,
        )
        memory = self.build_memory_context(record_text=record_text, meeting=meeting)
        loaded_knowhow = self.load_knowhow(scenario_mode=scenario_mode)
        require_sources = scenario_mode == "normal" and all(
            [self.account_file, self.opportunity_file, self.person_file]
        )
        return {
            "meeting": meeting,
            "crm_context": crm_context,
            "record_text": record_text,
            "scenario_mode": scenario_mode,
            "allowed_request_groups": allowed_request_groups,
            "retrieval": retrieval,
            "semantic_normalization": semantic_normalization,
            "meeting_state_features": meeting_state_features,
            "memory": memory,
            "loaded_knowhow": loaded_knowhow,
            "mock_sources": self._build_mock_sources(meeting, strict=require_sources),
        }

    def plan_retrieval(
        self,
        *,
        record_text: str,
        crm_context: dict[str, Any],
        allowed_request_groups: list[str],
        scenario_mode: str,
    ) -> dict[str, Any]:
        if scenario_mode == "uncertain":
            return {
                "crm_data_requests": [],
                "missing_information_candidates": [],
                "retrieval_trace": {
                    "mapping_version": "v1",
                    "scenario_mode": scenario_mode,
                    "allowed_request_groups": allowed_request_groups,
                    "requested_request_groups": [],
                    "out_of_policy_requests": [],
                },
            }

        requirements = self._load_data_requirements()
        requested_items: dict[str, dict[str, Any]] = {}
        out_of_policy_requests: list[dict[str, Any]] = []
        missing_information_candidates: list[str] = []

        for item in requirements:
            if not any(condition_matches(record_text, condition) for condition in item.conditions):
                continue

            missing_fields = [field for field in item.fields if not field_exists(field, crm_context)]
            if not missing_fields:
                continue

            if item.request_group not in allowed_request_groups:
                out_of_policy_requests.append(
                    {
                        "request_group": item.request_group,
                        "fields": missing_fields,
                        "source": item.source,
                        "why": item.why,
                    }
                )
                missing_information_candidates.extend(missing_fields)
                continue

            existing_item = requested_items.get(item.request_group)
            if existing_item is None:
                requested_items[item.request_group] = {
                    "reason": item.request_group,
                    "fields": sorted(missing_fields),
                    "why": item.why,
                    "sources": [f"knowhow:data_requirements:{item.source}"],
                }
            else:
                requested_items[item.request_group] = {
                    **existing_item,
                    "fields": sorted(set(existing_item["fields"]) | set(missing_fields)),
                    "sources": sorted(set(existing_item["sources"]) | {f"knowhow:data_requirements:{item.source}"}),
                }
            missing_information_candidates.extend(missing_fields)

        crm_data_requests = list(requested_items.values())
        requested_request_groups = [item["reason"] for item in crm_data_requests]
        retrieval_trace = {
            "mapping_version": "v1",
            "scenario_mode": scenario_mode,
            "allowed_request_groups": allowed_request_groups,
            "requested_request_groups": requested_request_groups,
            "out_of_policy_requests": out_of_policy_requests,
        }
        return {
            "crm_data_requests": crm_data_requests,
            "missing_information_candidates": sorted(set(missing_information_candidates)),
            "retrieval_trace": retrieval_trace,
        }

    def load_knowhow(self, *, scenario_mode: str) -> dict[str, list[str] | str]:
        common = [relative_path(COMMON_KNOWHOW_PATH)] if COMMON_KNOWHOW_PATH.exists() else []
        scenario_path = SCENARIO_KNOWHOW_DIR / f"{self.scenario_slug}.md"
        industry_path = INDUSTRY_KNOWHOW_DIR / f"{self.industry}.md" if self.industry else None
        patch_path = PATCH_KNOWHOW_DIR / f"{self.scenario_slug}__{self.industry}.md" if self.industry else None
        best_case_path = (
            BEST_CASES_DIR / f"{self.scenario_slug}__{self.industry}__v1.md" if self.industry else None
        )

        return {
            "mapping_version": "v1",
            "common": common,
            "scenario": [] if scenario_mode == "uncertain" else self._path_list(scenario_path),
            "industry": [] if scenario_mode == "uncertain" else self._path_list(industry_path),
            "patches": [] if scenario_mode == "uncertain" else self._path_list(patch_path),
            "best_cases": [] if scenario_mode == "uncertain" else self._path_list(best_case_path),
        }

    def build_semantic_normalization(
        self,
        *,
        meeting: dict[str, Any],
        crm_context: dict[str, Any],
    ) -> dict[str, Any]:
        account = meeting.get("account", {})
        opportunity = meeting.get("opportunity", {})
        initiator = meeting.get("initiator", {})
        participants = meeting.get("participants", [])
        account_payload = crm_context.get("account", {})
        opportunity_payload = crm_context.get("opportunity", {})
        person_payload = crm_context.get("person", {})

        return {
            "object_aliases": {
                "customer": "account",
                "account": "account",
                "商机": "opportunity",
                "项目": "opportunity",
                "机会": "opportunity",
                "initiator": "person",
                "owner": "person",
                "联系人": "contact",
            },
            "lookup_keys": {
                "initiator": f"person_id:{initiator.get('id')}" if initiator.get("id") else f"person_name:{initiator.get('name')}",
                "account": f"account_id:{account.get('id')}" if account.get("id") else f"account_name:{account.get('name')}",
                "opportunity": (
                    f"opportunity_id:{opportunity.get('id')}"
                    if opportunity.get("id")
                    else f"opportunity_name:{opportunity.get('name')}"
                ),
            },
            "resolved_objects": {
                "meeting": {
                    "meeting_time": meeting.get("meeting_time"),
                    "title": meeting.get("title"),
                },
                "person": {
                    "initiator": {
                        "id": initiator.get("id") or person_payload.get("person_id"),
                        "name": initiator.get("name") or person_payload.get("person_name"),
                        "role": person_payload.get("person_role"),
                    }
                },
                "account": {
                    "id": account.get("id") or account_payload.get("account_id"),
                    "name": account.get("name") or account_payload.get("account_name"),
                    "owner": account_payload.get("owner_person_id"),
                },
                "opportunity": {
                    "id": opportunity.get("id") or opportunity_payload.get("opportunity_id"),
                    "name": opportunity.get("name") or opportunity_payload.get("opportunity_name"),
                    "owner": opportunity_payload.get("owner_person_id"),
                },
                "contact_mentions": [
                    {
                        "name": item.get("name"),
                        "role": item.get("role"),
                        "mapped_scope": "contact" if item.get("role") else None,
                    }
                    for item in participants
                    if item.get("name") and item.get("name") != initiator.get("name")
                ],
            },
            "relationship_map": [
                "meeting initiated_by person",
                "meeting linked_to account",
                "meeting linked_to opportunity",
                "account may_have_owner person",
                "opportunity may_have_owner person",
            ],
        }

    def build_meeting_state_features(self, *, runtime: dict[str, Any], revision: int) -> dict[str, str]:
        record = runtime["record_text"]
        scenario_mode = runtime["scenario_mode"]
        if scenario_mode == "uncertain":
            return {
                "relationship_state": "existing-account but unclear active motion",
                "decision_pressure": "decision path unclear",
                "trust_state": "neutral",
                "momentum_state": "ambiguous",
            }
        if "严重缺失" in record:
            return {
                "relationship_state": "friction with insufficient evidence",
                "decision_pressure": "urgent but underspecified",
                "trust_state": "strained",
                "momentum_state": "blocked",
            }
        if "不会以续费作为决策背景" in record and revision == 0:
            return {
                "relationship_state": "active-account under service pressure",
                "decision_pressure": "service recovery first, but renewal memory may bias interpretation",
                "trust_state": "cautious",
                "momentum_state": "paused pending diagnosis",
            }
        if "不会以续费作为决策背景" in record:
            return {
                "relationship_state": "active-account under service pressure",
                "decision_pressure": "service recovery first, not renewal-led",
                "trust_state": "cautious but recoverable",
                "momentum_state": "paused pending proof",
            }
        if contains_any(record, ("预算", "考核", "优先级")):
            decision_pressure = "budget priority depends on short-term proof"
        else:
            decision_pressure = "evaluation still exploratory"
        trust_state = "neutral-to-cautious" if contains_any(record, ("不稳定", "效果", "延期")) else "neutral"
        momentum_state = "curious but not yet committed" if contains_any(record, ("试点", "确认", "建议")) else "steady"
        return {
            "relationship_state": "active-account, qualification-in-progress",
            "decision_pressure": decision_pressure,
            "trust_state": trust_state,
            "momentum_state": momentum_state,
        }

    def build_memory_context(self, *, record_text: str, meeting: dict[str, Any]) -> dict[str, Any]:
        meeting_id = meeting.get("id", "")
        conflict_detected = "不会以续费作为决策背景" in record_text or meeting_id == "MEET-CONFLICT-001"
        if not conflict_detected:
            return {"memory_sources": [], "memory_conflicts": []}
        lookup_key = (
            f"account_id:{meeting.get('account', {}).get('id')}"
            if meeting.get("account", {}).get("id")
            else f"account_name:{meeting.get('account', {}).get('name')}"
        )
        return {
            "memory_sources": [
                {
                    "scope": "account",
                    "lookup_key": lookup_key,
                    "used": True,
                    "notes": ["历史上存在续费主线判断，但本次不能覆盖当前会议证据。"],
                }
            ],
            "memory_conflicts": [
                {
                    "scope": "account",
                    "field": "decision_background",
                    "memory_claim": "历史上以续费为主线",
                    "current_evidence": "本季度不会以续费作为决策背景",
                    "resolution": "优先使用当前会议证据",
                }
            ],
        }

    def generate_draft(
        self,
        *,
        runtime: dict[str, Any],
        revision: int,
        review_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        meeting = runtime["meeting"]
        meeting_state_features = self.build_meeting_state_features(runtime=runtime, revision=revision)
        summary_fields = self.generate_summary_fields(
            runtime=runtime,
            meeting_state_features=meeting_state_features,
            revision=revision,
        )
        key_judgments = self.build_key_judgments(
            runtime=runtime,
            summary_fields=summary_fields,
            revision=revision,
        )
        knowhow_focus_items = self.build_knowhow_focus_items(runtime=runtime)
        scenario_result = self.build_scenario_result(runtime=runtime)
        base_context = {
            "meeting_time": meeting.get("meeting_time"),
            "initiator": {
                "id": meeting.get("initiator", {}).get("id"),
                "name": meeting.get("initiator", {}).get("name"),
            },
            "account": {
                "id": meeting.get("account", {}).get("id"),
                "name": meeting.get("account", {}).get("name"),
            },
            "opportunity": {
                "id": meeting.get("opportunity", {}).get("id"),
                "name": meeting.get("opportunity", {}).get("name"),
            },
            "participants": meeting.get("participants", []),
        }
        machine_output = {
            "base_context": base_context,
            "scenario_result": scenario_result,
            "semantic_normalization": runtime["semantic_normalization"],
            "meeting_state_features": meeting_state_features,
            "loaded_knowhow": runtime["loaded_knowhow"],
            "crm_data_requests": runtime["retrieval"]["crm_data_requests"],
            "memory_sources": runtime["memory"]["memory_sources"],
            "memory_conflicts": runtime["memory"]["memory_conflicts"],
            "summary_fields": summary_fields,
            "semantic_summary": dict(meeting_state_features),
            "key_judgments": key_judgments,
            "knowhow_focus_items": knowhow_focus_items,
            "retrieval_trace": runtime["retrieval"]["retrieval_trace"],
            "review_ready_checks": {key: True for key in REVIEW_CHECK_KEYS},
        }
        human_summary = self.render_human_summary(
            machine_output=machine_output,
            runtime=runtime,
            revision=revision,
            review_history=review_history,
        )
        evidence_excerpts = self.build_evidence_excerpts(runtime=runtime)
        return {
            "machine_output": machine_output,
            "human_summary": human_summary,
            "evidence_excerpts": evidence_excerpts,
            "missing_information_candidates": runtime["retrieval"]["missing_information_candidates"],
            "mock_sources": runtime["mock_sources"],
        }

    def generate_summary_fields(
        self,
        *,
        runtime: dict[str, Any],
        meeting_state_features: dict[str, str],
        revision: int,
    ) -> dict[str, Any]:
        meeting = runtime["meeting"]
        record = runtime["record_text"]
        missing_information = list(runtime["retrieval"]["missing_information_candidates"])
        if runtime["scenario_mode"] == "uncertain":
            missing_information = missing_information + ["primary_scenario_confirmation"]
        if runtime["memory"]["memory_conflicts"]:
            missing_information = missing_information + ["decision_background_confirmation"]

        if "严重缺失" in record:
            missing_information = sorted(
                set(
                    missing_information
                    + [
                        "customer_problem_statement",
                        "owner_confirmation",
                        "timeline",
                        "next_step_owner",
                    ]
                )
            )
            next_actions = [
                "补齐客户明确问题、责任方、时间线和下一步 owner 后再重新生成总结",
            ]
            risk_level = "high"
            current_stage_judgment = "manual-triage"
            meeting_goal = "确认客户不满的具体问题、责任边界和下一步处理方式"
        elif runtime["scenario_mode"] == "uncertain":
            next_actions = [
                "先确认当前讨论到底属于预算、试点、交付还是采购问题",
                "补一个最小消歧问题清单，避免在错误场景上继续推进",
            ]
            risk_level = "medium"
            current_stage_judgment = "ambiguous"
            meeting_goal = "判断当前沟通的真实主题与下一步是否值得继续"
        elif "不会以续费作为决策背景" in record and revision == 0:
            next_actions = [
                "先给出夜间服务质量异常的诊断路径，再决定是否值得继续试点",
                "同时回看历史续费背景，确认是否仍影响当前判断",
            ]
            risk_level = "medium"
            current_stage_judgment = "service-recovery-evaluation"
            meeting_goal = "澄清当前服务问题是否影响续费与后续试点判断"
        elif "不会以续费作为决策背景" in record:
            next_actions = [
                "先给出夜间服务质量异常的诊断路径和短期修复方案",
                "明确当前评估标准，再决定是否继续试点",
            ]
            risk_level = "medium"
            current_stage_judgment = "service-recovery-evaluation"
            meeting_goal = "围绕当前服务质量异常做问题诊断与试点价值判断"
        else:
            next_actions = [
                "一周内提交问题诊断与优化路径建议",
                "补齐试点评估负责人与预算审批链条",
            ]
            risk_level = "medium"
            current_stage_judgment = "qualification"
            meeting_goal = "确认问题根因并判断是否进入试点"

        return {
            "meeting_goal": meeting_goal,
            "relationship_state": meeting_state_features["relationship_state"],
            "decision_pressure": meeting_state_features["decision_pressure"],
            "trust_state": meeting_state_features["trust_state"],
            "momentum_state": meeting_state_features["momentum_state"],
            "key_participants": [
                item.get("name") for item in meeting.get("participants", []) if item.get("name")
            ],
            "current_stage_judgment": current_stage_judgment,
            "next_actions": next_actions,
            "risk_level": risk_level,
            "missing_information": sorted(set(missing_information)),
        }

    def build_key_judgments(
        self,
        *,
        runtime: dict[str, Any],
        summary_fields: dict[str, Any],
        revision: int,
    ) -> dict[str, list[str]]:
        record = runtime["record_text"]
        facts = [
            f"会议主题：{summary_fields['meeting_goal']}",
        ]
        if contains_any(record, ("一周内", "约定")):
            facts.append("会议中已经形成了我方需要补充诊断建议的明确动作。")
        if "6 月前" in record:
            facts.append("客户在 6 月前存在服务质量考核节点。")

        inferences = [
            f"当前阶段判断：{summary_fields['current_stage_judgment']}",
            f"整体风险等级：{summary_fields['risk_level']}",
        ]
        if "不会以续费作为决策背景" in record and revision == 0:
            inferences.append("当前讨论仍可能受续费背景影响。")
        elif "不会以续费作为决策背景" in record:
            inferences.append("当前讨论应按服务恢复与试点价值判断处理，不应沿用续费背景。")

        open_questions = [
            f"缺失信息：{item}" for item in summary_fields["missing_information"]
        ]
        return {
            "facts": facts,
            "inferences": inferences,
            "open_questions": open_questions,
        }

    def build_knowhow_focus_items(self, *, runtime: dict[str, Any]) -> list[str]:
        record = runtime["record_text"]
        items = [
            "区分真实推进与礼貌性回应",
            "缺失关键信息时只请求最小必要 CRM 字段",
        ]
        if contains_any(record, ("预算", "考核", "优先级")):
            items.append("预算优先级与短期效果证明直接相关")
        if contains_any(record, ("接口", "改造", "资源有限")):
            items.append("实施复杂度会直接影响商业推进动能")
        if "不会以续费作为决策背景" in record:
            items.append("当前会议证据优先于历史记忆")
        return items

    def build_scenario_result(self, *, runtime: dict[str, Any]) -> dict[str, Any]:
        meeting = runtime["meeting"]
        evidence = self.build_evidence_excerpts(runtime=runtime)
        secondary_tags: list[str] = []
        record = runtime["record_text"]
        if contains_any(record, ("预算", "优先级")):
            secondary_tags.append("risk:budget-priority")
        if contains_any(record, ("接口", "改造")):
            secondary_tags.append("risk:implementation-cost")
        if runtime["scenario_mode"] == "uncertain":
            secondary_tags.append("fallback:low-confidence")
        return {
            "primary_scenario": scenario_slug_to_name(self.scenario_slug),
            "scenario_slug": self.scenario_slug,
            "scenario_confidence": self.scenario_confidence,
            "scenario_mode": runtime["scenario_mode"],
            "industry": self.industry,
            "secondary_tags": secondary_tags,
            "evidence": evidence,
        }

    def render_human_summary(
        self,
        *,
        machine_output: dict[str, Any],
        runtime: dict[str, Any],
        revision: int,
        review_history: list[dict[str, Any]],
    ) -> str:
        summary_fields = machine_output["summary_fields"]
        scenario_result = machine_output["scenario_result"]
        knowhow_focus = machine_output["knowhow_focus_items"]
        retrieval_trace = machine_output["retrieval_trace"]
        record = runtime["record_text"]

        snapshot = (
            "会议快照\n"
            f"- 场景：{scenario_result['primary_scenario']}\n"
            f"- 模式：{scenario_result['scenario_mode']}\n"
            f"- 目标：{summary_fields['meeting_goal']}"
        )

        core_lines = [
            "核心总结与判断",
            f"- 当前阶段：{summary_fields['current_stage_judgment']}",
            f"- 决策压力：{summary_fields['decision_pressure']}",
            f"- 风险等级：{summary_fields['risk_level']}",
        ]
        if "不会以续费作为决策背景" in record and revision > 0:
            core_lines.append("- 当前会话证据优先于历史记忆，不能再沿用续费背景判断。")
        elif "不会以续费作为决策背景" in record:
            core_lines.append("- 当前判断仍混入了历史续费背景，需要下一轮修正。")
        core = "\n".join(core_lines)

        knowhow_section = "参考知识关注项\n" + "\n".join(f"- {item}" for item in knowhow_focus)
        actions_section = "建议下一步\n" + "\n".join(
            f"- {item}" for item in summary_fields["next_actions"]
        )

        risk_lines = ["风险与待确认问题"]
        for item in summary_fields["missing_information"]:
            risk_lines.append(f"- 待补：{item}")
        if retrieval_trace["out_of_policy_requests"]:
            risk_lines.append("- 存在 policy 外请求，需要人工确认。")
        if review_history:
            risk_lines.append(f"- 本次输出经过 {len(review_history)} 次定向修正。")
        risks = "\n".join(risk_lines)
        return "\n\n".join([snapshot, core, knowhow_section, actions_section, risks])

    def build_evidence_excerpts(self, *, runtime: dict[str, Any]) -> list[str]:
        lines = [line.strip() for line in runtime["record_text"].split("。") if line.strip()]
        return lines[:4]

    def review_output(self, *, draft: dict[str, Any], runtime: dict[str, Any], revision: int) -> ReviewResult:
        machine_output = draft["machine_output"]
        human_summary = draft["human_summary"]
        check_results = {key: "pass" for key in REVIEW_CHECK_KEYS}
        failure_reasons: list[str] = []
        targeted_regeneration_instructions: list[str] = []
        notes: list[str] = []

        if runtime["scenario_mode"] == "uncertain":
            if machine_output["loaded_knowhow"]["scenario"] or machine_output["loaded_knowhow"]["patches"]:
                check_results["scenario_self_consistency"] = "fail"
                failure_reasons.append("低置信场景不应加载 scenario 或 patch knowhow。")
                targeted_regeneration_instructions.append("保留 common knowhow，移除 scenario / patch knowhow。")
            if len(machine_output["retrieval_trace"]["requested_request_groups"]) > 1:
                check_results["policy_boundary_handling"] = "fail"
                failure_reasons.append("uncertain 模式下请求组超过一个，超出最小消歧范围。")
                targeted_regeneration_instructions.append("uncertain 模式下只保留一个消歧 request bundle。")

        if machine_output["semantic_summary"] != {
            key: machine_output["meeting_state_features"][key]
            for key in ("relationship_state", "decision_pressure", "trust_state", "momentum_state")
        }:
            check_results["semantic_summary_consistency"] = "fail"
            failure_reasons.append("semantic_summary 与 meeting_state_features 不一致。")
            targeted_regeneration_instructions.append("对齐 semantic_summary 与 meeting_state_features 的四个兼容映射字段。")

        if machine_output["meeting_state_features"] != {
            key: machine_output["summary_fields"][key]
            for key in ("relationship_state", "decision_pressure", "trust_state", "momentum_state")
        }:
            check_results["meeting_state_feature_evidence"] = "fail"
            failure_reasons.append("meeting_state_features 与 summary_fields 的状态特征字段不一致。")
            targeted_regeneration_instructions.append("用同一组状态特征同时驱动 meeting_state_features 和 summary_fields。")

        if not machine_output["scenario_result"]["evidence"]:
            check_results["evidence_grounding"] = "fail"
            failure_reasons.append("缺少最小证据摘录。")
            targeted_regeneration_instructions.append("补入支持主要判断的最小证据摘录。")

        if runtime["memory"]["memory_conflicts"] and "当前会话证据优先于历史记忆" not in human_summary:
            check_results["memory_conflict_handling"] = "fail"
            failure_reasons.append("检测到 memory 冲突，但摘要没有明确当前证据优先。")
            targeted_regeneration_instructions.append("删除受历史记忆影响的判断，并显式写出当前会话证据优先。")

        if not machine_output["summary_fields"]["missing_information"]:
            check_results["missing_information_handling"] = "fail"
            failure_reasons.append("缺失信息为空，无法暴露当前判断边界。")
            targeted_regeneration_instructions.append("列出仍未确认的关键缺口。")

        if runtime["record_text"].find("严重缺失") != -1:
            check_results["evidence_grounding"] = "fail"
            check_results["machine_output_completeness"] = "fail"
            check_results["knowhow_coverage"] = "fail"
            check_results["missing_information_handling"] = "fail"
            failure_reasons.extend(
                [
                    "会议原始证据过弱，无法支持可靠主结论。",
                    "关键上下文缺失过多，machine output 仍不可安全下游消费。",
                ]
            )
            targeted_regeneration_instructions.extend(
                [
                    "不要补写新事实，只保留当前已知边界。",
                    "明确请求客户问题、责任方、时间线和下一步 owner。",
                ]
            )
            notes.append("当前样例需要人工补上下文，自动重试不能解决证据缺失。")

        if machine_output["retrieval_trace"]["out_of_policy_requests"]:
            notes.append("存在超出 policy 的请求建议，已保留在 trace 中。")

        passed = all(value == "pass" for value in check_results.values())
        return ReviewResult(
            passed=passed,
            review_status="pass" if passed else "fail",
            failure_reasons=tuple(dict.fromkeys(failure_reasons)),
            targeted_regeneration_instructions=tuple(dict.fromkeys(targeted_regeneration_instructions)),
            check_results=check_results,
            notes=tuple(dict.fromkeys(notes)),
        )

    def finalize_output(
        self,
        *,
        draft: dict[str, Any],
        review_result: ReviewResult,
        retry_state: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        machine_output = draft["machine_output"]
        review_ready_checks = build_review_ready_checks(review_result.check_results)
        return {
            "status": status,
            "human_summary": draft["human_summary"],
            "review_result": {
                "pass": review_result.passed,
                "review_status": review_result.review_status,
                "failure_reasons": list(review_result.failure_reasons),
                "targeted_regeneration_instructions": list(
                    review_result.targeted_regeneration_instructions
                ),
                "check_results": review_result.check_results,
                "notes": list(review_result.notes),
            },
            **machine_output,
            "retry_state": retry_state,
            "review_ready_checks": review_ready_checks,
            "mock_sources": draft["mock_sources"],
            "missing_information_candidates": draft["missing_information_candidates"],
        }

    def _load_crm_context(self) -> dict[str, Any]:
        context: dict[str, Any] = {}
        if self.account_file:
            context["account"] = load_json(self.account_file)
        if self.opportunity_file:
            context["opportunity"] = load_json(self.opportunity_file)
        if self.person_file:
            context["person"] = load_json(self.person_file)
        return context

    def _load_data_requirements(self) -> list[RequestItem]:
        requirements: list[RequestItem] = []
        scenario_path = SCENARIO_KNOWHOW_DIR / f"{self.scenario_slug}.md"
        if scenario_path.exists():
            requirements.extend(extract_data_requirements(read_text(scenario_path), scenario_path.name))

        if self.industry:
            patch_path = PATCH_KNOWHOW_DIR / f"{self.scenario_slug}__{self.industry}.md"
            if patch_path.exists():
                requirements.extend(extract_data_requirements(read_text(patch_path), patch_path.name))
        return requirements

    def _build_mock_sources(self, meeting: dict[str, Any], *, strict: bool) -> dict[str, str | None]:
        account = meeting.get("account", {})
        opportunity = meeting.get("opportunity", {})
        initiator = meeting.get("initiator", {})
        account_source = find_mock_source("account", account.get("id"), account.get("name"))
        opportunity_source = find_mock_source(
            "opportunity", opportunity.get("id"), opportunity.get("name")
        )
        person_source = find_mock_source("person", initiator.get("id"), initiator.get("name"))
        sources = {
            "meeting": relative_path(self.meeting_file),
            "account": account_source,
            "opportunity": opportunity_source,
            "person": person_source,
        }
        if strict:
            missing = [key for key, value in sources.items() if key != "meeting" and value is None]
            if missing:
                missing_info = ", ".join(missing)
                raise RunnerError(f"未找到 mock source: {missing_info}")
        return sources

    def _path_list(self, path: Path | None) -> list[str]:
        if path is None or not path.exists():
            return []
        return [relative_path(path)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CRM meeting summary mock retrieval runner")
    parser.add_argument("--meeting-file", required=True)
    parser.add_argument("--scenario-slug", required=True)
    parser.add_argument("--scenario-confidence", required=True, choices=["high", "medium", "low"])
    parser.add_argument("--industry")
    parser.add_argument("--account-file")
    parser.add_argument("--opportunity-file")
    parser.add_argument("--person-file")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        runner = MockRetrievalRunner(
            meeting_file=Path(args.meeting_file).resolve(),
            scenario_slug=args.scenario_slug,
            scenario_confidence=args.scenario_confidence,
            industry=args.industry,
            account_file=Path(args.account_file).resolve() if args.account_file else None,
            opportunity_file=Path(args.opportunity_file).resolve() if args.opportunity_file else None,
            person_file=Path(args.person_file).resolve() if args.person_file else None,
        )
        print(json.dumps(runner.run(), ensure_ascii=False, indent=2))
    except RunnerError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
