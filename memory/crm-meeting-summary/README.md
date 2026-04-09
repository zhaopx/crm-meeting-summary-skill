# CRM Object Memory Design

## 目标

CRM Memory 体系的目标，不是给某个 summary 组件补一层附属上下文。

它首先服务的是 **CRM 对象本身**。

也就是：
- `account`
- `opportunity`
- `contact`
- `person`

每个对象都应该有自己可持续积累的 memory，用来沉淀这个对象的稳定特性、关系模式、推进规律和当天状态。

`crm-meeting-summary` 只是其中一个消费方，不是这套 memory 的定义中心。

## 设计原则

1. 先定义对象特性，再定义消费方式
2. 每个对象都分成两层：`today` 和 `long_term`
3. `today` 记录当前这次 interaction 之后，对象今天的状态与信号
4. `long_term` 记录跨会议、跨时间稳定下来的特性与模式
5. memory 是对象记忆，不是会议纪要堆积

## 对象层

### 1. account
客户对象的组织级 memory。

它回答的问题是：
- 这个客户长期怎么决策
- 长期对什么敏感
- 长期怎么被推进、怎么卡住
- 今天这次会后，客户当前关注什么、态度有没有变化

### 2. opportunity
商机对象的推进级 memory。

它回答的问题是：
- 这笔机会长期怎么推进
- 常见卡点和预算节奏是什么
- 今天是否产生推进，当前卡在哪

### 3. contact
联系人对象的关键人 memory。

它回答的问题是：
- 这个人通常怎么影响事情
- 长期偏好和典型 objection 是什么
- 今天这次会里，他的态度和角色有没有变化

### 4. person
内部人员对象的协同级 memory。

它回答的问题是：
- 这个内部角色通常怎么推进客户
- 承诺和跟进风格如何
- 今天是否做出关键动作或留下协同风险

## 时间层

### today
`today` 不是原始 meeting notes。

它记录的是：
- 站在对象视角，今天这次 interaction 后形成的当前状态
- 今天暴露出的重点信号、风险、变化与推进情况

### long_term
`long_term` 记录的是：
- 跨多次互动稳定下来的对象特性
- 长期模式、偏好、敏感点、决策方式与推进规律

## 每类对象的推荐 memory 特性

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

## 使用边界

下面这些是 memory 的消费规则，不是 memory 体系定义本身：

1. 当前 meeting evidence 优先
2. 当前 CRM facts 次之
3. memory 不覆盖当前证据
4. 冲突时输出 `memory_conflicts`
5. `today` 服务当前状态判断，`long_term` 服务长期解释与模式补强

## 允许进入 memory 的内容
- 对象的稳定偏好
- 对象的长期敏感点
- 承诺兑现或失约的连续历史
- 重复出现的风险或 blocker 模式
- 稳定审批路径与角色关系
- 站在对象视角定义的当天状态与当天变化

## 具体实例

### account
#### today 示例
```json
{
  "focus": ["夜间服务稳定性"],
  "current_signal": ["本周先看故障归因，再决定是否推进续费讨论"],
  "today_risks": ["预算优先级暂时后移"],
  "today_relationship_shift": "态度转为谨慎，但未停止合作"
}
```

#### long_term 示例
```json
{
  "relationship_baseline": "愿意试点，但对扩量谨慎",
  "decision_style": "先业务 owner 认可，再走采购",
  "organization_pattern": ["运营主导问题确认", "采购后置"],
  "risk_sensitivities": ["稳定性", "服务质量考核"],
  "collaboration_preferences": ["先看到问题归因，再看扩展方案"],
  "recurring_blockers": ["效果验证不足会影响预算优先级"]
}
```

### opportunity
#### today 示例
```json
{
  "today_stage_signal": ["从意向确认推进到方案评估"],
  "today_blockers": ["客户要求补充 ROI 测算"],
  "today_progress": ["确认了下一轮技术评审时间"],
  "today_checkpoint": "等待客户内部财务 review"
}
```

#### long_term 示例
```json
{
  "stage_pattern": "POC 通过后才进入采购讨论",
  "blocker_pattern": ["财务测算不足时推进变慢"],
  "budget_pattern": "预算通常在季度末集中确认",
  "approval_path": ["业务负责人", "财务", "采购"],
  "competitive_pressure": ["客户会长期比价两家供应商"],
  "progression_style": "推进节奏偏慢，但一旦过评审会连续前进"
}
```

### contact
#### today 示例
```json
{
  "today_stance": "支持继续推进，但要求先解决数据准确性问题",
  "today_role_signal": ["从普通参与者转为内部推动人"],
  "today_preference_signal": ["希望后续沟通先给书面结论"],
  "today_objection_signal": ["担心切换成本过高"]
}
```

#### long_term 示例
```json
{
  "role_in_motion": "持续扮演业务推动人",
  "influence_style": "偏向用内部案例说服其他团队",
  "communication_preference": ["先书面，再开会"],
  "objection_pattern": ["每次都会先确认实施成本"],
  "trust_signal": "对数据口径一致性要求高，满足后配合度提升"
}
```

### person
#### today 示例
```json
{
  "today_action_signal": ["销售在会后 30 分钟内发出补充材料"],
  "today_commitment": ["承诺周五前补 ROI 版本"],
  "today_followup_gap": [],
  "today_handoff_risk": ["技术顾问尚未收到客户问题清单"]
}
```

#### long_term 示例
```json
{
  "owner_style": "推进主动，但依赖会议后快速跟进",
  "commitment_reliability": "高",
  "followup_pattern": ["会后当天会发纪要和材料"],
  "handoff_risk": ["跨团队交接时偶尔漏同步细节"],
  "coordination_strength": "客户侧关系维护稳定"
}
```

## CRM 事实与 memory 的边界

CRM 正常运营中的事实，不自动等于 memory。

区分规则：
1. **事实先写 CRM，不直接等于 memory**
2. **只有对对象形成可复用解释价值的内容，才进入 memory**
3. **单次事件通常只更新 `today`，重复成立后才考虑沉淀到 `long_term`**

### 典型判断

| CRM 事件 | 进入 CRM | 进入 today | 进入 long_term |
| --- | --- | --- | --- |
| 客户创建一笔订单 | 是 | 否 | 否 |
| 商机阶段前进一次 | 是 | 是，若这次前进反映当前推进状态 | 否 |
| 新建一条销售记录 | 是 | 否 | 否 |
| 客户今天明确表示先解决稳定性再谈续费 | 是 | 是 | 否 |
| 联系人连续多次要求先书面材料再开会 | 是 | 是 | 是，重复确认后可沉淀 |
| 某销售连续多次承诺后都按时跟进 | 是 | 是 | 是，形成长期执行风格 |

### 判断方法

- **只写 CRM，不写 memory**：纯事实记录、一次性操作、没有解释增量
- **写 `today`，不写 `long_term`**：这次互动后的当前状态、信号、风险、推进变化
- **先写 `today`，后续再升级到 `long_term`**：跨多次互动重复出现，已经表现为稳定模式

## 不允许进入 memory 的内容
- 原始会议纪要全文
- 仅供一次性执行的 next action 清单
- 没有对象归属的零散判断
- 未经确认的当前结论被直接写死到 long_term

## 推荐阅读顺序

1. `schema.md`
2. `lifecycle.md`
3. `topic-taxonomy.md`
4. `../../skills/crm-meeting-summary/references/memory-contract.md`
5. `../../skills/crm-meeting-summary/references/runtime-contract.md`
