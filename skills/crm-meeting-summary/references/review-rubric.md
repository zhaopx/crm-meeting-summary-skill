# 评审标准

review 优先级顺序：
1. 事实准确性
2. 风险覆盖
3. 业务价值

## 通过条件

### 事实准确性
- 所有主要结论都能追溯到 source evidence
- scenario classification 可被支撑
- 没有 fabricated CRM 或 memory facts
- human-readable 与 machine-readable outputs 一致
- `semantic_summary` labels 有证据支撑

### 风险覆盖
- evidence 或 knowhow 隐含的主要风险都被显式呈现
- risk level 没有被低估
- policy 或 compliance boundaries 没有被忽略

### 业务价值
- summary 可行动
- next actions 足够具体
- knowhow focus items 被明确回应
- missing information 可见
- `semantic_summary` 能帮助下游理解当前业务状态

## Best-case 使用规范
- best-cases 是 reference anchors，不是 templates
- 如果加载 best-case，它的作用是提升 judgment quality，不是为无证据 claim 背书
- 当前 meeting evidence 永远高于 best-case patterns

## 失败示例
- 无证据断言 customer intent
- 描述了 opportunity stage，但没有 source 支撑
- notes 里有 escalation signals，输出却省略
- `semantic_summary` 说 momentum 很强，但 evidence 只显示礼貌性兴趣
- summary 看起来完整，但没有可执行 next action

## 再生成指导规则
review fail 时，只针对失败维度提供修复指令。指令必须具体，并且面向证据。
