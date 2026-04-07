---
name: crm-meeting-summary
description: This skill should be used when the user asks to summarize CRM meeting notes, generate a meeting recap from customer or opportunity records, analyze a sales/customer meeting with CRM context, or produce a structured meeting summary using industry/scenario knowhow, memories, and review validation.
---

# CRM Meeting Summary

Create a high-quality CRM meeting summary from meeting notes plus CRM context. Preserve model reasoning space, but constrain evidence boundaries and output contract.

## Purpose

Produce two synchronized outputs from a CRM meeting record:
1. A human-readable meeting summary for sales, CS, delivery, or management consumption.
2. A machine-consumable intermediate structure for downstream workflow use.

Keep the workflow evidence-grounded. Use knowhow and memory as guidance and context, not as a license to invent facts.

## Inputs

Expect the input package to contain at least:
- meeting record text
- initiator information
- customer or opportunity association
- meeting time
- any directly provided CRM fields

Treat missing data as normal. Identify what is absent instead of forcing conclusions.

## Working Principles

1. Distinguish strictly between:
   - explicit facts from meeting notes or CRM data
   - high-confidence judgments inferred from evidence
   - unresolved items that require confirmation
2. Prefer current meeting notes and current CRM context over memory.
3. Use memory only to strengthen background understanding such as prior commitments, stakeholder preferences, historical tension, or relationship continuity.
4. Use knowhow as an evaluation frame:
   - what matters in this kind of meeting
   - what risk signals matter
   - what progress signals matter
   - what boundaries must not be crossed
5. Never fabricate CRM data, policies, actions, or customer intent.

## Workflow

### Step 1: Normalize the base context

Extract or organize the minimum base context:
- meeting title if present
- meeting time
- initiator
- linked customer
- linked opportunity
- participants if present
- raw meeting record

If object IDs exist, prefer IDs. If IDs do not exist, fall back to names.

### Step 2: Identify meeting scenario

Classify the meeting into one primary scenario and optional secondary tags.

Use scenario taxonomy from `references/taxonomy.md`.

Primary scenario should be chosen from business intent, not from literal wording alone. When evidence is weak, return `其他/不确定` and explain why.

Secondary tags may include:
- industry
- customer stage
- decision-chain role
- risk
- compliance
- competitor

### Step 3: Load knowhow

Load knowhow in this order:
1. `references/knowhow/common/`
2. `references/knowhow/by-scenario/<scenario>.md`
3. `references/knowhow/by-industry/<industry>.md` when industry is identifiable
4. `references/knowhow/patches/<scenario>__<industry>.md` when both scenario and industry are identifiable and the patch exists

Use knowhow to determine:
- key signals to focus on
- required coverage points in the summary
- scenario-specific success criteria
- scenario-specific risk or policy boundaries
- possible next-step expectations

### Step 4: Decide what additional CRM data is needed

Do not pull all data by default. Determine only the minimum missing CRM data needed to make a better summary.

Use the field dictionary in `references/crm-data-dictionary.md`.

Return a machine-readable list of requested CRM fields grouped by rationale, for example:
- customer profile gap
- opportunity stage gap
- risk validation gap
- historical interaction gap

If the runtime has only mock data, map the requested fields to mock sources under `examples/mock-data/`.

### Step 5: Assemble memory context

Load memory from three possible scopes:
- initiator memory
- customer memory
- opportunity memory

Use the following lookup rule:
1. use object ID when available
2. otherwise use name
3. if multiple candidates exist, mark ambiguity instead of guessing

Use memory only to add context. If memory conflicts with current meeting evidence or CRM context, trust current evidence and flag the conflict for review.

See `references/memory-contract.md` for lookup and priority rules.

### Step 6: Generate the summary

Generate both outputs together.

#### Human-readable output

Produce these sections:
1. Meeting snapshot
2. Core summary and judgment
3. Knowhow focus items
4. Recommended next actions
5. Risks and open questions

#### Machine-consumable output

Return a structured block that includes at minimum:
- base_context
- scenario_result
- loaded_knowhow
- crm_data_requests
- memory_sources
- summary_fields
- key_judgments
- knowhow_focus_items
- review_ready_checks

Use JSON when possible. If the environment does not support raw JSON cleanly, use a fenced JSON block.

### Step 7: Call review skill

Invoke the review skill in `review/SKILL.md` after generating the summary.

Pass to review:
- original input
- assembled context
- loaded knowhow identifiers
- generated human-readable summary
- generated machine-readable output

If review fails, regenerate using only the failure reasons. Do not drift by rewriting unrelated sections.

Maximum regeneration count: 2.

If review still fails after the retry limit, return:
- current best summary
- review failure reasons
- `status: manual_review_required`

## Output Contract

### Required standard fields

Always provide these fields in the machine output:
- meeting_time
- initiator
- customer
- opportunity
- primary_scenario
- scenario_confidence
- industry
- meeting_goal
- key_participants
- current_stage_judgment
- next_actions
- risk_level
- missing_information
- status

### Human summary expectations

The human summary must:
- state the main business conclusion clearly
- separate facts from inference
- identify the most important risk signals
- identify the most important opportunity or progress signals
- recommend next actions that follow from evidence
- explicitly cover the most relevant knowhow focus items

## Failure Handling

If the meeting record is too sparse to support a reliable summary:
1. still classify scenario if possible
2. reduce confidence appropriately
3. output missing information explicitly
4. request the smallest useful additional CRM data set
5. avoid pretending to know customer intent

## Reference Files

Read these files as needed:
- `references/taxonomy.md` - scenario taxonomy and tagging rules
- `references/crm-data-dictionary.md` - CRM field dictionary and request rationale examples
- `references/memory-contract.md` - memory lookup and conflict handling rules
- `references/output-schema.md` - machine-readable output contract
- `references/review-rubric.md` - review priorities and scoring dimensions

Read knowhow files selectively:
- `references/knowhow/common/`
- `references/knowhow/by-scenario/`
- `references/knowhow/by-industry/`
- `references/knowhow/patches/`

## Examples

See `examples/` for:
- mock meeting input
- mock CRM objects
- mock memory records
- expected output structure
