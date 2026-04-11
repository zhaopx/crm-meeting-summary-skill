---
name: crm-meeting-summary-review
description: 当需要校验 crm-meeting-summary skill 的输出，判断一份 CRM 会议总结是否事实有据、风险覆盖充分、符合 knowhow 覆盖要求，并且可以安全交付时，应使用此 skill；凡是生成的 CRM meeting summary 需要 pass/fail 审核与定向修复反馈，都应调用它。
---

# CRM 会议总结评审

把这份 review skill 当成 `crm-meeting-summary` 的真实运行时质量闸门。
它只做三件事：
1. 判断 pass / fail
2. 输出具体 `failure_reasons`
3. 只对失败维度给出 `targeted_regeneration_instructions`

除非用户明确要求，不要重写 summary 正文。

## 输入要求

调用方至少应传入：
- 生成人类可读总结
- 已加载 knowhow 标识
- 用于验证 claim 的最小支持证据摘录
- 缺失信息清单

如已使用 template 或 memory，还应补充：
- 模板选择结果与明显映射缺口说明
- 必要的 memory conflict 简述

review handoff 边界见 `../references/runtime-contract.md`。
如果输入不满足最小评审条件：
- 直接 fail
- 明确指出缺失了哪些必需输入
- 不要假装可以完整评审

## 评审顺序

按固定优先级审查：
1. 事实准确性
2. 风险覆盖
3. 业务价值

评审判定口径以下列规则为准：
- `scenario_self_consistency`：summary 必须能清楚回答当前阶段、推进动能、第一阻塞点，且内部判断不能互相冲突。
- `knowhow_coverage`：summary 必须压缩出真正影响交易推进的门槛、qualification 信号与边界，不能只复述内部分析框架。
- `evidence_grounding`：主要结论都必须能回溯到最小证据摘录，不能把条件性能力、客户兴趣或历史记忆写成已确认事实。
- `memory_conflict_handling`：存在 memory 冲突时，必须优先信任当前 meeting / CRM evidence，并在关键判断受影响时暴露不确定边界。
- `missing_information_handling`：缺失信息必须显式暴露，不能把拍板人、预算、时间线、接口结论等未确认项写成确定性陈述。
- `policy_boundary_handling`：summary 必须显式呈现交付、合规、接口或升级边界，不能低估真实推进风险。
- `template_no_fabrication`：套模板后只能重组已有内容，缺失项必须 missing / 留空 / 待确认，不能补写新事实。
- `next_action_quality`：动作必须贴着当前阻塞点，至少说明动作本身、动作目的，以及不做会卡住什么。

## 必需检查项

至少返回以下检查项：
- `scenario_self_consistency`
- `knowhow_coverage`
- `evidence_grounding`
- `memory_conflict_handling`
- `missing_information_handling`
- `policy_boundary_handling`
- `template_no_fabrication`
- `next_action_quality`

说明：
- 没有使用 memory 时，`memory_conflict_handling` 可以 pass，但不能编造 memory 结论。
- 没有使用 template 时，`template_no_fabrication` 可以 pass，但不能因为没套模板就降低事实要求。
- `next_action_quality` 要重点检查动作是否真正贴着阻塞点，是否说明动作目的，以及不做会卡住什么。
- `knowhow_coverage` 不要求复述内部分析框架，而要检查 summary 是否把真正影响交易推进的门槛和 qualification 信号压缩出来。

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
    "template_no_fabrication": "pass",
    "next_action_quality": "pass"
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

## 真实运行时约束

当这份 review skill 被主 skill 调用时，必须遵守：
1. 只审查传入包，不主动扩大上下文范围
2. 当最小证据摘录已足够时，不要求完整 CRM dump 或完整 knowhow 正文
3. 不生成新的业务事实
4. 不把“风格不喜欢”当作 fail 原因
5. 如果存在 template，必须重点检查缺失项是否被硬编成确定性陈述

## 升级规则

如果证据太弱，无法判断 summary 是否正确：
- 必须 fail
- 明确请求所缺的具体上下文
- 不要放过一份模糊输出

如果已经做过 2 次定向修复且仍失败：
- 保持 fail
- 输出最后一轮最关键的 failure reasons
- 不要再建议无限重试
- 明确说明需要人工复核

## Template 专项检查

如果主 skill 输出按模板重排，review 必须额外检查：
- human-readable summary 的目录顺序是否与所选模板一致
- 模板缺失项是否被标记为 missing、留空或显式写成待确认
- 是否因为模板目录存在，就补写了 summary 里本来没有的新事实

以下情况直接 fail：
- 模板项无证据却有确定性内容
- 缺失项被硬编成确定性陈述
- 模板目录顺序与最终总结冲突，导致关键信息错位
