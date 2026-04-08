# Output Schema

使用这份 schema 作为 machine-consumable output 的结构定义。
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
  "loaded_knowhow": {
    "mapping_version": "v1",
    "common": [],
    "scenario": [],
    "industry": [],
    "patches": [],
    "best_cases": []
  },
  "crm_data_requests": [],
  "memory_sources": [],
  "memory_conflicts": [],
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
    "semantic_summary_consistency": true,
    "machine_output_completeness": true
  }
}
```

## Notes

- 能用空数组时，优先输出空数组，不要省略字段。
- 未知值使用 `null`，不要编造。
- 人类可读总结与该结构分开输出。
