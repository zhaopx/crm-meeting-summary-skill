# 评审标准

本文是 `crm-meeting-summary-review` 的**人工阅读说明**。
真实运行时判定口径以 `skills/crm-meeting-summary/review/SKILL.md` 为准；这里的作用是把 review 为什么 pass / fail 讲清楚，避免文档理解漂移。

review 优先级顺序：
1. 事实准确性
2. 风险覆盖
3. 业务价值

## 必需检查项判定口径

### 1. `scenario_self_consistency`
通过条件：
- summary 能清楚回答当前阶段、推进动能、第一阻塞点
- summary 内部不存在互相冲突的阶段、风险、推进状态表述
- 事实、判断、待确认问题三者边界清楚

失败示例：
- 一边说“客户只是继续了解”，一边又写成“已进入采购推进”
- 一边说“核心问题待澄清”，一边又给出确定性立项判断

### 2. `knowhow_coverage`
通过条件：
- 已加载 knowhow 对当前场景最关键的门槛、qualification 信号与边界，都在 summary 中被压缩表达
- 不把 knowhow 写成内部分析框架复述，而是写成影响推进的业务判断

失败示例：
- summary 只复述客户说了什么，没有指出真正影响推进的门槛
- 已出现集成、交付、审批等关键约束，但总结没有压缩出来

### 3. `evidence_grounding`
通过条件：
- 所有主要结论都能回溯到最小证据摘录
- 没有 fabricated CRM facts、memory facts 或客户意图
- 不把条件性能力、模糊兴趣或礼貌性回应写成已确认事实

失败示例：
- 客户只是表示“可以继续看”，summary 写成“客户明确准备采购”
- 售前只说“如果有标准接口可以对接”，summary 写成“已确认可直接打通”

### 4. `memory_conflict_handling`
通过条件：
- 如有 memory 冲突，优先信任当前 meeting / CRM evidence
- 冲突若影响关键判断，summary 已显式暴露不确定边界或降低判断强度
- 没有使用 memory 时，该项可 pass，但不能编造 memory 结论

失败示例：
- 当前会议已否定旧判断，summary 仍沿用旧 memory 下结论
- memory 与当前证据冲突，但总结里完全不暴露冲突

### 5. `missing_information_handling`
通过条件：
- 缺失信息被显式暴露
- 没有把拍板人、预算、时间线、接口结论、实施范围等未确认项写成确定性陈述
- 缺失项被正确放入风险或待确认问题，而不是被藏掉

失败示例：
- 没确认拍板人，却直接写“客户管理层已认可方案”
- 没确认预算，却写“预算已基本锁定”

### 6. `policy_boundary_handling`
通过条件：
- 交付、合规、接口、升级、外部系统依赖等边界被显式呈现
- 没有因为会议气氛正向，就低估真实推进风险
- 当客户需求超出标准能力时，summary 能诚实表达边界

失败示例：
- 客户核心问题是能否替代外部作业系统，但总结只写成“客户对方案认可度较高”
- 需要外部接口条件才能成立的能力，被写成标准现成功能

### 7. `template_no_fabrication`
通过条件：
- 模板只重组已有内容，不生成新事实
- 模板缺失项被留空、标记 missing 或写成待确认
- 模板目录顺序没有把关键信息错位

失败示例：
- 模板里有“拍板人确认”，但实际证据没有，summary 却补写具体人名
- 为了让模板看起来完整，硬补预算、时间线或结论

### 8. `next_action_quality`
通过条件：
- 动作贴着当前阻塞点
- 至少说明动作本身、动作目的，以及不做会卡住什么
- next action 是任务单，不是“继续跟进”“内部再看看”这类空话

失败示例：
- 只写“安排下次沟通”，没有说明下一次沟通要关闭什么不确定性
- 动作与当前最大阻塞点无关

## 总体通过条件

### 事实准确性
- `scenario_self_consistency` 通过
- `evidence_grounding` 通过
- `missing_information_handling` 通过
- 如涉及 memory，`memory_conflict_handling` 通过

### 风险覆盖
- `policy_boundary_handling` 通过
- 风险没有被低估
- 关键缺口没有被藏起来

### 业务价值
- `knowhow_coverage` 通过
- `next_action_quality` 通过
- `template_no_fabrication` 通过
- 读者能快速知道当前推进状态、阻塞点和该做什么

## Best-case 使用规范
- best-cases 是参考增强，不是事实来源
- 如果加载 best-case，它的作用是提升 judgment quality，不是为无证据 claim 背书
- 当前 meeting evidence 永远高于 best-case patterns
- best-cases 不能覆盖当前 meeting evidence，也不能替代 review

## 再生成指导规则
review fail 时，只针对失败维度提供修复指令。
指令必须具体，且必须贴着证据、缺失项或边界问题。
不要为了“更好看”整份重写，也不要因为 review fail 去扩大无关 retrieval。
