# 输出 Schema

使用这份 schema 作为机器可读输出的结构定义。
字段语义以 `runtime-contract.md` 为准。

```json
{
  "status": "passed | manual_review_required | insufficient_context",
  "base_context": {
    "meeting_time": "string | null",
    "initiator": {"id": "string | null", "name": "string | null"},
    "account": {"id": "string | null", "name": "string | null"},
    "opportunity": {"id": "string | null", "name": "string | null"},
    "participants": []
  },
  "scenario_result": {
    "primary_scenario": "string",
    "scenario_slug": "string",
    "scenario_confidence": "high | medium | low",
    "scenario_mode": "normal | uncertain",
    "industry": "string | null",
    "secondary_tags": [],
    "evidence": []
  },
  "semantic_normalization": {
    "object_aliases": {},
    "lookup_keys": {},
    "resolved_objects": {},
    "relationship_map": []
  },
  "meeting_state_features": {
    "relationship_state": "string",
    "decision_pressure": "string",
    "trust_state": "string",
    "momentum_state": "string"
  },
  "loaded_knowhow": {
    "mapping_version": "v1",
    "common": [],
    "scenario": [],
    "industry": [],
    "patches": [],
    "best_cases": []
  },
  "crm_data_requests": [
    {
      "reason": "string",
      "fields": [],
      "why": "string",
      "sources": []
    }
  ],
  "memory_sources": [
    {
      "scope": "person | account | opportunity | contact",
      "lookup_key": "string",
      "used": true,
      "notes": []
    }
  ],
  "memory_conflicts": [
    {
      "scope": "person | account | opportunity | contact",
      "field": "string",
      "memory_claim": "string",
      "current_evidence": "string",
      "resolution": "优先使用当前会议证据"
    }
  ],
  "summary_fields": {
    "meeting_goal": "string",
    "relationship_state": "string",
    "decision_pressure": "string",
    "trust_state": "string",
    "momentum_state": "string",
    "key_participants": [],
    "current_stage_judgment": "string",
    "next_actions": [],
    "risk_level": "high | medium | low",
    "missing_information": []
  },
  "semantic_summary": {
    "relationship_state": "string",
    "decision_pressure": "string",
    "trust_state": "string",
    "momentum_state": "string"
  },
  "key_judgments": {
    "facts": [],
    "inferences": [],
    "open_questions": []
  },
  "knowhow_focus_items": [],
  "retrieval_trace": {
    "mapping_version": "v1",
    "scenario_mode": "normal | uncertain",
    "allowed_request_groups": [],
    "requested_request_groups": [],
    "out_of_policy_requests": []
  },
  "retry_state": {
    "revision": 0,
    "status": "draft_generated | passed | review_failed_retry_1 | review_failed_retry_2 | manual_review_required",
    "history": []
  },
  "review_ready_checks": {
    "scenario_self_consistency": true,
    "knowhow_coverage": true,
    "evidence_grounding": true,
    "memory_conflict_handling": true,
    "missing_information_handling": true,
    "policy_boundary_handling": true,
    "semantic_normalization_consistency": true,
    "meeting_state_feature_evidence": true,
    "semantic_summary_consistency": true,
    "machine_output_completeness": true
  }
}
```

## 说明

- `semantic_normalization` 只承载对象、关系、字段口径统一，不承载状态判断。
- `meeting_state_features` 只承载当前会议状态特征，必须由当前会议证据与当前 CRM 支撑。
- `semantic_summary` 是兼容字段，内容必须与 `meeting_state_features` 一致，不能代替 `semantic_normalization`。
- `crm_data_requests[*].sources` 用于标明请求来源，例如 `knowhow:data_requirements`。
- `memory_sources` 只记录实际读取且被使用的 memory 子集；没有使用就输出空数组。
- 能用空数组时，优先输出空数组，不要省略字段。
- 未知值使用 `null`，不要编造。
- 人类可读总结与该结构分开输出。
