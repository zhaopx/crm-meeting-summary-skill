# Memory 使用契约

版本: `v1`

将 memory 视为外部数据源。该 skill 只读取 memory，不负责定义 memory 系统如何产生或治理。

## Memory 对象范围
- person
- account
- opportunity
- contact

## CRM 对象关系提醒
- account / opportunity / contact 都可以有 owner
- owner 始终是 `person`
- 一条 sales record 可以在 account、opportunity 或 contact 下发起
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

## 适合的 skill 侧 memory 用法
- relationship continuity
- stakeholder preference patterns
- prior commitment history
- historical sensitivity or escalation context
- recurring objections or approval patterns

## 不适合的 skill 侧 memory 用法
- 不要把旧 memory 当成当前事实
- 不要仅凭 memory 推断缺失的 CRM fields
- 不要在缺少 source 支撑时用 memory 抬高置信度

## 冲突处理
如果 memory 与当前 evidence 冲突：
1. 优先信任当前 meeting/CRM evidence
2. 标记冲突用于 review
3. 如果冲突影响关键判断，降低置信度

## 建议的机器可读 trace

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
