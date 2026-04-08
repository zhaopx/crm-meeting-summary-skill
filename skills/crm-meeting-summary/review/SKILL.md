---
name: crm-meeting-summary-review
description: 当需要校验 crm-meeting-summary skill 的输出，判断一份 CRM 会议总结是否事实有据、风险充分、符合 knowhow 覆盖要求，并且可以安全交付时，应使用此 skill；凡是生成的 CRM meeting summary 需要 pass/fail 审核与定向再生成反馈，都应调用它。
---

# CRM 会议总结评审

按严格优先级顺序审查 CRM meeting summary：
1. 事实准确性
2. 风险覆盖
3. 业务价值

除非用户明确要求，不要重写 summary。只输出 pass/fail 判断和聚焦的修复指导。

## 评审输入

期望输入至少包含：
- generated human-readable summary
- generated machine-readable output
- loaded knowhow identifiers
- retrieval trace
- retry state
- 用于验证 claim 的最小支持证据摘录

review handoff 边界和状态分离见 `../references/runtime-contract.md`。

## 评审规则

### 优先级 1：事实准确性

出现以下任一情况立即 fail：
- claim 无法被 meeting notes、CRM data 或 memory 支撑
- fabricated account state、opportunity state、participant role 或 next step
- 混淆事实与推断
- 用 stale memory 覆盖当前 evidence
- machine-readable fields 与 human-readable summary 不一致
- `semantic_summary` labels 无证据支撑

### 优先级 2：风险覆盖

检查 summary 是否遗漏或弱化了 knowhow 或 source evidence 已支持的重要风险信号，包括：
- deal progression risk
- stakeholder risk
- commitment risk
- delivery or implementation risk
- compliance or policy boundary risk
- escalation, dissatisfaction, or churn risk

高显著性风险被遗漏、模糊化或错误标注时必须 fail。

### 优先级 3：业务价值

检查输出是否真正可用于行动：
- 主结论是否清楚
- next actions 是否 evidence-based
- knowhow focus items 是否被覆盖
- open questions 是否明确
- recommendations 是否足够具体、可以直接使用

如果输出技术上准确，但业务上空洞，也必须 fail。

## 必需检查项

至少返回以下检查项：
- scenario_self_consistency
- knowhow_coverage
- evidence_grounding
- memory_conflict_handling
- missing_information_handling
- policy_boundary_handling
- semantic_summary_consistency
- machine_output_completeness

summary machine output 中的 `review_ready_checks` 必须保持 boolean，并与 `references/output-schema.md` 一致。

## 输出格式

返回以下结构化结果：

```json
{
  "pass": true,
  "review_status": "pass",
  "failure_reasons": [],
  "targeted_regeneration_instructions": [],
  "check_results": {
    "scenario_self_consistency": "pass",
    "knowhow_coverage": "pass",
    "evidence_grounding": "pass",
    "memory_conflict_handling": "pass",
    "missing_information_handling": "pass",
    "policy_boundary_handling": "pass",
    "semantic_summary_consistency": "pass",
    "machine_output_completeness": "pass"
  },
  "notes": []
}
```

review 失败时：
- 将 `pass` 设为 `false`
- 将 `review_status` 设为 `fail`
- 列出具体 failure reasons
- 只针对失败维度提供 targeted regeneration instructions
- 除非整份输出都不可用，否则不要要求 full rewrite

## 评审方法

1. 将每个 major claim 与 evidence excerpts 和 machine fields 对照。
2. 验证 scenario classification 是否有依据，必要时是否使用了 low-confidence fallback。
3. 验证 knowhow-derived focus items 是否进入最终输出。
4. 验证 missing information 是否被显式暴露，而不是被隐藏。
5. 验证风险没有在缺乏证据时被降级。
6. 验证 `semantic_summary` 与 `summary_fields` 中的语义字段是否对齐且有证据支撑。
7. 验证 machine output 是否可被下游步骤消费。
8. 验证 human-readable summary 与 machine-readable output 在决策层表达的是同一件事。
9. 验证 contract 要求时，`retrieval_trace` 和 `retry_state` 是否存在。

## 升级规则

如果证据太弱，无法判断 summary 是否正确，应 fail，并明确请求所缺的具体上下文，而不是放过一份模糊输出。
