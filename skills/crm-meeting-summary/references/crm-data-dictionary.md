# CRM Data Dictionary

Use this dictionary to request only the CRM data needed to improve the summary.

## Customer fields
- customer_id
- customer_name
- industry
- lifecycle_stage
- account_tier
- current_products
- recent_health_status
- known_risks

## Opportunity fields
- opportunity_id
- opportunity_name
- stage
- amount
- expected_close_date
- competitor_presence
- next_milestone
- blocker_summary

## Interaction fields
- recent_interactions
- last_commitments
- open_followups
- prior_escalations

## Stakeholder fields
- initiator_role
- account_owner
- decision_makers
- procurement_owner
- implementation_owner

## Delivery / compliance fields
- implementation_status
- support_tickets
- contract_status
- procurement_status
- compliance_constraints

## Request rationale examples

### customer_profile_gap
Use when the meeting references account context but customer baseline is missing.

### opportunity_progress_gap
Use when the meeting discusses advancement, pricing, timeline, or blockers but current opportunity state is missing.

### stakeholder_gap
Use when influence map, owner map, or approval chain matters but key roles are unclear.

### history_gap
Use when the summary depends on previous commitments, repeated objections, or continuity across meetings.

### risk_validation_gap
Use when potential dissatisfaction, escalation, delivery, or compliance issues appear and require validation.

## Request output suggestion

```json
[
  {
    "reason": "opportunity_progress_gap",
    "fields": ["stage", "amount", "expected_close_date"],
    "why": "The meeting discusses budget and close timing, but current opportunity status is absent."
  }
]
```
