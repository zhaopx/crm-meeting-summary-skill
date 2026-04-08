# 场景 knowhow：需求澄清

版本: `v1`

## 这类会议的目的
这类会议的目标，是判断业务问题是否真实、紧迫、具体，并且是否值得继续推进到解决方案或试点阶段。

## 关注点
- 底层业务问题是否真实且紧迫？
- 痛点是否具体，还是仍停留在泛泛描述？
- 成功标准是否可见？
- 阻塞、约束或依赖是否被明确说出？
- 当前体现的是购买严肃度，还是仅仅探索性好奇？
- 当前 account/opportunity stage 是否支持继续推进，还是讨论已经跑在 qualification reality 前面？

## 正向信号
- 具体的 current-state pain
- 可度量的成功标准
- 明确点名的 owner 或决策参与者
- 时间线或不行动的后果
- 问题与业务优先级之间的明确连接

## 风险信号
- 需求模糊且没有紧迫性
- 下一步没有 owner
- 痛点与预算或优先级没有连接
- 在需求尚未明确前就进入方案讨论
- 历史会议中的重复关注点仍未解决

## 值得拉取的 CRM 字段
优先只拉能关闭真实不确定性的字段：

```json
[
  {
    "request_group": "account_profile_gap",
    "fields": ["industry", "lifecycle_stage", "current_products"],
    "why": "当会议只出现模糊业务背景时，需要 account baseline 来判断问题是否真实且紧迫。",
    "conditions": ["meeting 中只出现泛化痛点，缺少 account context 证据"],
    "priority": "optional"
  },
  {
    "request_group": "stakeholder_gap",
    "fields": ["decision_makers", "account_owner"],
    "why": "当 owner 或决策链不清晰时，需要验证是否存在明确负责人与审批路径。",
    "conditions": ["会议提及推进但未出现明确 owner 或决策角色"],
    "priority": "high"
  },
  {
    "request_group": "risk_validation_gap",
    "fields": ["last_commitments", "implementation_status"],
    "why": "当 trust 或历史承诺成为风险点时，需要验证承诺是否兑现与实施状态。",
    "conditions": ["会议出现信任/延期/承诺兑现问题，但当前 CRM 缺失历史承诺与实施状态"],
    "priority": "high"
  }
]
```

## 伪进展预警
以下信号除非有更强证据支撑，否则都视为弱信号：
- stakeholder enthusiasm，但没有 owner accountability
- 对 features 感兴趣，但问题并不紧迫
- 同意“看看 proposal”，但没有 success criteria 或下一次 checkpoint

## 建议的下一步逻辑
优先选择能提升 qualification 质量的动作：stakeholder mapping、success criteria confirmation、blocker clarification、timeline validation。
