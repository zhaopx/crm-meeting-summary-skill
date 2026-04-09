# CRM 数据字典

使用这份字典，只请求真正能提升 summary 质量的 CRM data。

说明：
- 对外业务语义统一使用“客户”，底层对象 key 仍保留 `account`
- 以下映射基于用户提供的对象描述文件整理，只保留当前 skill 真正会用到的最小字段
- 抽象字段名保持稳定；右侧“推荐来源”用于说明建议映射到哪个对象字段

## 客户字段（底层对象：account）
- `account_id` ← 记录主键 / 系统 ID
- `account_name` ← `AccountObj.name`
- `industry` ← `AccountObj.industry_level1` / `AccountObj.industry_level2`
- `lifecycle_stage` ← 归一自 `AccountObj.life_status` / `AccountObj.biz_status` / `AccountObj.account_status`
- `account_tier` ← `AccountObj.account_level`
- `current_products` ← 可选；仅当客户对象中存在明确产品/订阅字段时映射
- `recent_health_status` ← 可选；仅当客户对象中存在明确健康状态字段时映射，不用 `enable_risk_portrait` 直接替代
- `known_risks` ← 可归一 `AccountObj.is_blacklist` 与其他风险字段；不能把黑名单直接当全部风险

## 商机字段
- `opportunity_id` ← 记录主键 / 系统 ID
- `opportunity_name` ← `NewOpportunityObj.name`
- `stage` ← `NewOpportunityObj.sales_stage`
- `amount` ← `NewOpportunityObj.amount`
- `expected_close_date` ← `NewOpportunityObj.close_date`
- `competitor_presence` ← 可选；仅当商机对象中存在明确竞品字段时映射
- `next_milestone` ← 可选；仅当商机对象中存在明确里程碑字段时映射
- `blocker_summary` ← 可选；仅当商机对象中存在明确阻塞说明字段时映射

## 互动字段
- `recent_interactions`
- `last_commitments`
- `open_followups`
- `prior_escalations`

## 干系人字段
- `person_role` ← `PersonnelObj.position`
- `account_owner` ← `AccountObj.owner`
- `decision_makers` ← 可选；仅当联系人对象中存在明确决策链字段时映射
- `procurement_owner` ← 可选；仅当 CRM 中存在明确采购负责人字段时映射
- `implementation_owner` ← 可选；仅当 CRM 中存在明确实施负责人字段时映射

## 联系人字段
- `contact_id` ← 记录主键 / 系统 ID
- `contact_name` ← `ContactObj.name`
- `title` ← `ContactObj.job_title`
- `role_in_account` ← 可由 `ContactObj.job_title` 归一
- `is_decision_maker` ← 可选；仅当联系人对象中存在明确布尔/标签字段时映射
- `influence_level` ← 可选；仅当联系人对象中存在明确影响力字段时映射
- `mobile` ← `ContactObj.mobile`
- `email` ← `ContactObj.email`

## 人员字段
- `person_id` ← 记录主键 / 系统 ID
- `person_name` ← `PersonnelObj.name`
- `person_role` ← `PersonnelObj.position`
- `work_phone` ← `PersonnelObj.work_phone`
- `email` ← `PersonnelObj.email`
- `leader` ← `PersonnelObj.leader`，可作为组织关系补充，不进入最小必需集合

## 交付 / 合规字段
- `implementation_status`
- `support_tickets`
- `contract_status`
- `procurement_status`
- `compliance_constraints`

## 请求理由示例

### account_profile_gap
当会议提到了客户上下文，但客户 baseline 缺失时使用。

### opportunity_progress_gap
当会议讨论推进、价格、时间线或 blockers，但当前 opportunity state 缺失时使用。

### stakeholder_gap
当 influence map、owner map 或 approval chain 很关键，但核心角色不清晰时使用。

### history_gap
当 summary 依赖历史承诺、重复异议或跨会议连续性时使用。

### risk_validation_gap
当出现潜在不满、升级、交付或合规问题，且需要验证时使用。

## 请求输出示例

```json
[
  {
    "reason": "opportunity_progress_gap",
    "fields": ["stage", "amount", "expected_close_date"],
    "why": "会议讨论了预算与成交时间，但当前 opportunity status 缺失。"
  }
]
```
