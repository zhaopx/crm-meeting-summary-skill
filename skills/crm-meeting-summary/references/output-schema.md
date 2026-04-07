# Output Schema

Use this schema for the machine-consumable output.

```json
{
  "status": "pass | manual_review_required | insufficient_context",
  "base_context": {
    "meeting_time": "string | null",
    "initiator": {"id": "string | null", "name": "string | null"},
    "customer": {"id": "string | null", "name": "string | null"},
    "opportunity": {"id": "string | null", "name": "string | null"},
    "participants": []
  },
  "scenario_result": {
    "primary_scenario": "string",
    "scenario_confidence": "high | medium | low",
    "industry": "string | null",
    "secondary_tags": [] ,
    "evidence": []
  },
  "loaded_knowhow": {
    "common": [],
    "scenario": [],
    "industry": [],
    "patches": []
  },
  "crm_data_requests": [],
  "memory_sources": [],
  "memory_conflicts": [],
  "summary_fields": {
    "meeting_goal": "string",
    "key_participants": [],
    "current_stage_judgment": "string",
    "next_actions": [],
    "risk_level": "high | medium | low",
    "missing_information": []
  },
  "key_judgments": {
    "facts": [],
    "inferences": [],
    "open_questions": []
  },
  "knowhow_focus_items": [],
  "review_ready_checks": {
    "scenario_self_consistency": true,
    "knowhow_coverage": true,
    "evidence_grounding": true,
    "memory_conflict_handling": true,
    "missing_information_handling": true,
    "policy_boundary_handling": true,
    "machine_output_completeness": true
  }
}
```

## Notes

- Use empty arrays instead of omitted fields where possible.
- Mark unknown values as `null` rather than inventing values.
- Keep human-readable summary separate from this structure.
