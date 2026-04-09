# Memory 使用契约

版本: `v1`

将 memory 视为外部数据源。该 skill 在 runtime 中只读 memory，但需要明确约束哪些信息适合被读入、如何解释、以及何时必须让位给当前证据。

## Memory 对象范围
- person
- account（对外业务语义：客户）
- opportunity
- contact

## CRM 对象关系提醒
- 客户 / opportunity / contact 都可以有 owner
- owner 始终是 `person`
- 一条 sales record 可以在客户、opportunity 或 contact 下发起
- 一条 sales record 可能同时关联多个 objects
- initiator 是 `person`

## 查找优先级
1. object ID
2. object name
3. ambiguous match -> 不猜，直接返回歧义

## 关键策略
在 mock 与 runtime contracts 中使用 mixed keys：
- 有 `*_id` 时优先使用
- 没有 ID 时回退到 `*_name`

## Skill 侧使用规则
1. 当前 meeting record 优先级最高。
2. 当前 CRM data 优先级第二。
3. memory 只做补充上下文，不能覆盖当前证据。
4. 如果 memory 提供的字段多于所需，只读最小相关子集。
5. memory 的读取目标是服务当前 summary judgment，而不是补全一套平行 CRM 事实库。

## 允许读取与沉淀的 memory 类型
适合被读取、也适合作为后续 memory card 候选的内容：
- relationship continuity
- stakeholder preference patterns
- prior commitment history
- historical sensitivity or escalation context
- recurring objections or approval patterns

更具体地说，可落在以下 topic：
- `relationship_continuity`
- `stakeholder_preference`
- `commitment_history`
- `risk_pattern`
- `approval_pattern`

## 不允许作为 memory 主体的内容
以下内容不应作为 memory 主体正向支撑当前总结：
- 单次会议瞬时状态
- 一次性 next action
- 未被当前证据确认的当前结论
- 仅属于当前会议的场景判断
- 为了补齐当前 CRM 缺口而臆造的历史结论

## 推荐的分层模型

### 时间层
- `short`：0-30 天，近期承诺、当前阻塞、短期决策压力
- `mid`：1-2 个季度，阶段性推进模式、预算节奏、组织协同习惯
- `long`：2 个季度以上，长期敏感点、结构性偏好、重大升级历史

### 推荐状态
- `active`
- `stale`
- `contradicted`
- `archived`

这些分层用于约束 memory 如何被读取与解释。

## 冲突处理
如果 memory 与当前 evidence 冲突：
1. 优先信任当前 meeting/CRM evidence
2. 标记冲突用于 review
3. 如果冲突影响关键判断，降低置信度
4. `contradicted` memory 只能用于说明冲突，不能再正向支撑 judgment

## 机器可读 trace

runtime 侧继续复用 `memory_sources` 和 `memory_conflicts` 作为最小 trace。

`memory_sources` 建议最少包含：
- `scope`
- `lookup_key`
- `used`
- `notes`

`memory_conflicts` 建议最少包含：
- `scope`
- `field`
- `memory_claim`
- `current_evidence`
- `resolution`

```json
{
  "memory_sources": [
    {
      "scope": "account",
      "lookup_key": "account_id:CUST-001",
      "used": true,
      "notes": ["提供历史采购偏好上下文。"]
    }
  ],
  "memory_conflicts": []
}
```
