# TODOS

## CRM Meeting Summary Skill

### Add runtime contract document

**What:** Create `skills/crm-meeting-summary/references/runtime-contract.md` as the single source of truth for skill input, object shapes, trace fields, output statuses, and review handoff.

**Why:** Current runtime expectations are split across the main skill, output schema, retry state machine, and examples, which will drift as the skill gets more sophisticated.

**Context:** Done. The contract now consolidates four-object model, trace fields, retry semantics, and review handoff boundaries in one file. Future schema/example changes should update this file first.

**Effort:** M
**Priority:** P1
**Depends on:** retry-state-machine.md, scenario-retrieval-mapping.md
