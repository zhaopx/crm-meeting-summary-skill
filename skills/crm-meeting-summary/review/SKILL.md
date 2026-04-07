---
name: crm-meeting-summary-review
description: This skill should be used when validating output from the crm-meeting-summary skill, checking whether a CRM meeting summary is factually grounded, risk-aware, complete against knowhow, and safe to deliver; use it whenever a generated CRM meeting summary needs pass/fail review and targeted regeneration feedback.
---

# CRM Meeting Summary Review

Review a CRM meeting summary with strict priority order:
1. fact accuracy
2. risk coverage
3. business value

Do not rewrite the summary unless explicitly asked. Produce pass/fail judgment and focused repair guidance.

## Review Inputs

Expect these inputs:
- original meeting record
- CRM context used by generation
- memory context used by generation
- loaded knowhow identifiers or content summary
- human-readable summary
- machine-readable output

## Review Rules

### Priority 1: Fact Accuracy

Fail immediately if any of the following occurs:
- claims unsupported by meeting notes, CRM data, or memory
- fabricated customer state, opportunity state, participant role, or next step
- confusion between fact and inference
- stale memory overriding current evidence
- machine-readable fields inconsistent with human-readable summary

### Priority 2: Risk Coverage

Check whether the summary missed or weakened important risk signals that knowhow or source evidence supports, including:
- deal progression risk
- stakeholder risk
- commitment risk
- delivery or implementation risk
- compliance or policy boundary risk
- escalation, dissatisfaction, or churn risk

Fail when high-salience risks are omitted, blurred, or mislabeled.

### Priority 3: Business Value

Check whether the output is useful for action:
- main conclusion is clear
- next actions are evidence-based
- knowhow focus items are covered
- open questions are explicit
- recommendations are concrete enough to use

Fail when the output is technically accurate but operationally empty.

## Required Checks

Return checks for at least:
- scenario_self_consistency
- knowhow_coverage
- evidence_grounding
- memory_conflict_handling
- missing_information_handling
- policy_boundary_handling
- machine_output_completeness

## Output Format

Return a structured result:

```json
{
  "pass": true,
  "status": "pass",
  "failure_reasons": [],
  "targeted_regeneration_instructions": [],
  "check_results": {
    "scenario_self_consistency": "pass",
    "knowhow_coverage": "pass",
    "evidence_grounding": "pass",
    "memory_conflict_handling": "pass",
    "missing_information_handling": "pass",
    "policy_boundary_handling": "pass",
    "machine_output_completeness": "pass"
  },
  "notes": []
}
```

When review fails:
- set `pass` to `false`
- set `status` to `fail`
- list concrete failure reasons
- provide targeted regeneration instructions only for failed dimensions
- do not ask for a full rewrite unless the whole output is unusable

## Review Method

1. Compare every major claim against evidence.
2. Verify the scenario classification is supported.
3. Verify knowhow-derived focus items appear in the output.
4. Verify missing information is surfaced instead of hidden.
5. Verify risks are not downgraded without evidence.
6. Verify the machine output can be consumed by downstream steps.

## Escalation Rule

If evidence is too weak to judge whether the summary is correct, fail with a request for specific missing context rather than passing a vague output.
