# CRM Object Memory Schema

## 设计原则

这版不再以“单条 card”作为第一视角，而是以“对象 profile”作为第一视角。

也就是：
- 每个对象有自己的 memory profile
- profile 分成 `today` 和 `long_term`
- profile 下放对象专属字段，由对象语义决定

## 推荐结构

```json
{
  "scope": "account",
  "lookup_key": "account_id:CUST-001",
  "today": {
    "focus": ["服务质量异常"],
    "current_signal": ["当前优先解决夜间稳定性，不先谈续费"],
    "today_risks": ["预算优先级下降"],
    "today_relationship_shift": "谨慎，但未关闭后续合作"
  },
  "long_term": {
    "relationship_baseline": "愿意试点，但对扩量谨慎",
    "decision_style": "先业务 owner 认可，再走采购",
    "organization_pattern": ["运营主导问题确认", "采购后置"],
    "risk_sensitivities": ["稳定性", "服务质量考核"],
    "collaboration_preferences": ["先看到问题归因，再看扩展方案"],
    "recurring_blockers": ["效果验证不足会影响预算优先级"]
  },
  "evidence_ref": [
    "meeting:MEET-20260408",
    "meeting:MEET-20260320"
  ],
  "observed_at": "2026-03-20T10:00:00+08:00",
  "last_confirmed_at": "2026-04-08T11:00:00+08:00",
  "status": "active"
}
```

## 顶层字段

### 必填字段
- `scope`：`account | opportunity | contact | person`
- `lookup_key`：优先 `*_id`，回退 `*_name`
- `today`
- `long_term`
- `evidence_ref`
- `observed_at`
- `last_confirmed_at`
- `status`

### 状态字段
- `active`
- `stale`
- `contradicted`
- `archived`

## today 层

`today` 记录的是当前这次 interaction 之后，这个对象今天的状态。

约束：
- 必须站在对象视角表达
- 不是原始 meeting notes
- 可以更新快，但只代表“今天”
- 可以被后续新 evidence 替换或清空

## long_term 层

`long_term` 记录的是跨时间稳定下来的特性。

约束：
- 只放稳定特征、长期模式、结构性背景
- 不把单次会议即时状态塞进 long_term
- 如果长期特征被当前 evidence 反证，要降级为 `stale` 或 `contradicted`

## 各对象建议字段

### account
#### today
- `focus`
- `current_signal`
- `today_risks`
- `today_relationship_shift`

#### long_term
- `relationship_baseline`
- `decision_style`
- `organization_pattern`
- `risk_sensitivities`
- `collaboration_preferences`
- `recurring_blockers`

### opportunity
#### today
- `today_stage_signal`
- `today_blockers`
- `today_progress`
- `today_checkpoint`

#### long_term
- `stage_pattern`
- `blocker_pattern`
- `budget_pattern`
- `approval_path`
- `competitive_pressure`
- `progression_style`

### contact
#### today
- `today_stance`
- `today_role_signal`
- `today_preference_signal`
- `today_objection_signal`

#### long_term
- `role_in_motion`
- `influence_style`
- `communication_preference`
- `objection_pattern`
- `trust_signal`

### person
#### today
- `today_action_signal`
- `today_commitment`
- `today_followup_gap`
- `today_handoff_risk`

#### long_term
- `owner_style`
- `commitment_reliability`
- `followup_pattern`
- `handoff_risk`
- `coordination_strength`

## 与旧 card 模型的关系

如果后面仍要做单条 card 存储，可以把 profile 看成对象当前聚合结果，而不是否定 card。

也就是：
- card 可以是底层记录单元
- profile 是面向消费的对象 memory 视图

当前这版设计优先定义 profile 视角。
