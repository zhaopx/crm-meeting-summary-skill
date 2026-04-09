---
name: crm-meeting-summary-review
description: 当需要校验 crm-meeting-summary skill 的输出，判断一份 CRM 会议总结是否事实有据、风险充分、符合 knowhow 覆盖要求，并且可以安全交付时，应使用此 skill；凡是生成的 CRM meeting summary 需要 pass/fail 审核与定向再生成反馈，都应调用它。
---

# CRM 会议总结评审

把这份 review skill 当成 `crm-meeting-summary` 的**真实运行时质量闸门**。
它不是泛泛点评，也不是重写器。默认职责只有三个：
1. 判断 pass / fail
2. 指出具体 failure reasons
3. 只对失败维度给出 targeted regeneration instructions

除非用户明确要求，不要重写 summary 正文。

## 评审输入

调用方至少应传入：
- 生成人类可读总结
- 生成的机器可读输出
- 已加载 knowhow 标识
- retrieval trace
- retry state
- 用于验证 claim 的最小支持证据摘录

review handoff 边界和状态分离见 `../references/runtime-contract.md`。

如果输入不满足最小评审条件：
- 直接 fail
- 明确指出缺失了哪些必需输入
- 不要假装可以完整评审

## 评审规则

按严格优先级顺序审查：
1. 事实准确性
2. 风险覆盖
3. 业务价值

### 优先级 1：事实准确性

出现以下任一情况立即 fail：
- claim 无法被会议纪要、CRM data 或 memory 支撑
- fabricated 客户状态、opportunity state、participant role 或 next step
- 混淆事实与推断
- 用 stale memory 覆盖当前 evidence
- 机器可读字段与人类可读总结不一致
- `semantic_normalization` 的对象、别名、lookup 或关系口径自相矛盾
- `meeting_state_features` 无当前证据支撑
- `semantic_summary` 与 `meeting_state_features` 不一致

### 优先级 2：风险覆盖

检查 summary 是否遗漏或弱化了 knowhow 或 source evidence 已支持的重要风险信号，包括：
- deal progression risk
- stakeholder risk
- commitment risk
- delivery or implementation risk
- compliance or policy boundary risk
- escalation, dissatisfaction, or churn risk

高显著性风险被遗漏、模糊化或错误标注时必须 fail。

补充判定规则：
- 如果当前会议明确否定了旧叙事，例如否定“续费是当前主背景”，review 必须检查机器输出是否仍被 stale memory 带偏。
- 如果会议证据只支持模糊关系维护或笼统意向，不能把它包装成高置信商业推进、试点推进或交付推进。
- 如果输入显式说明存在大量无关诱饵上下文，review 必须把 retrieval 最小化也当作质量项检查。

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
- semantic_normalization_consistency
- meeting_state_feature_evidence
- semantic_summary_consistency
- machine_output_completeness

`review_ready_checks` 必须保持 boolean，并与 `../references/output-schema.md` 一致。

## 输出格式

始终返回以下结构化结果：

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
    "semantic_normalization_consistency": "pass",
    "meeting_state_feature_evidence": "pass",
    "semantic_summary_consistency": "pass",
    "machine_output_completeness": "pass"
  },
  "notes": []
}
```

review 失败时：
- `pass = false`
- `review_status = fail`
- 列出具体 `failure_reasons`
- 只针对失败维度给出 `targeted_regeneration_instructions`
- 除非整份输出都不可用，否则不要要求 full rewrite
- `review_status = fail` 不直接等于最终 summary `status = manual_review_required`，主 skill 必须先检查 `retry_state` 是否还有剩余重试次数

## 真实运行时约束

当这份 review skill 被主 skill 调用时，必须遵守：
1. 只审查传入包，不主动扩大上下文范围
2. 当最小证据摘录已足够时，不要求完整 CRM dump 或完整 knowhow 正文
3. 不把 `review_status` 和最终 summary 的 `status` 混为一体
4. 不生成新的业务事实
5. 不把“风格不喜欢”当作 fail 原因

## 评审方法

1. 将每个 major claim 与 evidence excerpts 和 machine fields 对照。
2. 验证 scenario classification 是否有依据，必要时是否使用了 low-confidence fallback。
3. 验证 knowhow-derived focus items 是否进入最终输出。
4. 验证 missing information 是否被显式暴露，而不是被隐藏。
5. 验证风险没有在缺乏证据时被降级。
6. 验证 `semantic_normalization` 是否只承载对象口径统一，而没有混入状态判断。
7. 验证 `meeting_state_features` 与 `summary_fields` 中的同名状态字段是否对齐且有证据支撑。
8. 验证 `semantic_summary` 是否只是 `meeting_state_features` 的兼容映射。
9. 验证机器输出是否可被下游步骤消费。
10. 验证人类可读总结与机器可读输出在决策层表达的是同一件事。
11. 验证 contract 要求时，`retrieval_trace` 和 `retry_state` 是否存在。

## 升级规则

如果证据太弱，无法判断 summary 是否正确：
- 必须 fail
- 明确请求所缺的具体上下文
- 不要放过一份模糊输出
- 如果 revision 已到 2，最终结果必须推动主 skill 输出 `status: manual_review_required`

如果 revision 已达到 2 且仍失败：
- 保持 fail
- 输出最后一轮最关键的 failure reasons
- 不要再建议无限重试
