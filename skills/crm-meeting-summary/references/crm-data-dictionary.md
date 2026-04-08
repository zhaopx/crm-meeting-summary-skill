# CRM Data Dictionary

使用这份字典，只请求真正能提升 summary 质量的 CRM data。

## Account fields
- account_id
- account_name
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
- person_role
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

### account_profile_gap
当会议提到了 account context，但 account baseline 缺失时使用。

### opportunity_progress_gap
当会议讨论推进、价格、时间线或 blockers，但当前 opportunity state 缺失时使用。

### stakeholder_gap
当 influence map、owner map 或 approval chain 很关键，但核心角色不清晰时使用。

### history_gap
当 summary 依赖历史承诺、重复异议或跨会议连续性时使用。

### risk_validation_gap
当出现潜在不满、升级、交付或合规问题，且需要验证时使用。

## Request output suggestion

```json
[
  {
    "reason": "opportunity_progress_gap",
    "fields": ["stage", "amount", "expected_close_date"],
    "why": "会议讨论了预算与成交时间，但当前 opportunity status 缺失。"
  }
]
```
