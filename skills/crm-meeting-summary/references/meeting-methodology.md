# Meeting Methodology

版本: `v1`

本文解释 `crm-meeting-summary` 如何优于通用会议总结器。
这是产品层方法论，不是运行时 schema。

## 目标

好的 CRM 会议总结不是更顺眼的会议记录。
它是一个业务判断层，来源包括：
- meeting facts
- CRM business context
- meeting-type reference
- object memory

## 产品边界

这个 skill 不只是一个 prompt。
它是封装的 CRM 能力，包含四个稳定层：
1. runtime input and output contract
2. semantic interpretation layer
3. knowhow and case-reference layer
4. review and retry layer

流程保持稳定，knowhow、案例与业务语义不断增强。
这决定它是产品基础能力，不是一次性总结提示词。

## 为什么 CRM 总结更强

通用会议工具知道说了什么。
CRM meeting skill 还必须知道：
1. 这个 account 是谁
2. 这段关系或机会处在什么阶段
3. 现在哪些风险或评分因子最重要
4. 这个参与者或对象过去反复关注什么

这就是全部优势。
如果不用这些，就只是另一个 transcript summarizer。

## 核心方法论

### 1. 从会议出发，不从模板出发

第一件事是理解这次会议真实是什么。
不要把输出硬塞进固定模板。
不要提前锁定固定标题或固定章节逻辑。

skill 应做到：
- 忠实总结会议
- 识别会议类型与主场景
- 结构专业但保持弹性

### 2. 用公式组装上下文，而不是把所有东西倒进去

使用以下上下文组装公式：

`meeting facts + account profile + relationship/stage + current risk/score factors + participant/object memory + meeting-type reference`

每个部分各司其职：
- **meeting facts**: 来源事实
- **account profile**: 客户是谁
- **relationship/stage**: 关系或机会当前所处阶段
- **risk/score factors**: 影响推进、续费或流失的关键因素
- **memory**: 过往反复重要的内容
- **meeting-type reference**: 这一类会议应该关注什么

不要超过最小可用上下文。
上下文要被选择，而不是被倾倒。

### 3. 在 raw CRM data 与最终表达之间加入语义层

原始 CRM 字段不是产品价值。
价值来自把原始输入归一为业务语义，例如：
- relationship state
- decision pressure
- trust state
- momentum state

语义层避免两个失败模式：
- 把 CRM 字段直接塞进总结而没有意义
- 写了漂亮的 prose 却掩盖了真实业务状态

语义层必须小而可审计。
它让 summary 生成与 review 更尖锐。

### 4. Reference 是指导，不是刚性模板

reference 文件要短且语义化。
每个文件回答：
- 这是什么类型的会议
- 这类会议通常关注什么
- 哪些 CRM data 值得拉
- 哪些风险信号最重要
- 哪些下一步动作有意义
- 什么是伪进展

reference 不应要求：
- 固定 7 个要点
- 永远使用标题 A/B/C
- 不管内容如何都输出相同标题

### 5. Memory 是差异点，不是装饰

memory 在相关时必须改变总结含义。
例子：
- 某关键人第三次重复同一异议
- 客户反复关注价格或实施风险
- 发起人倾向先稳关系再推进商业动作

当重复性重要时，summary 必须明确表达。
这是最强的 CRM 原生优势之一。

### 6. Flow 与 knowhow 是不同层

flow 是稳定的：
1. 识别 meeting type / scenario
2. 加载正确的 reference / knowhow
3. 决定最小 CRM fields 拉取
4. 加载最小 memory
5. 构建语义上下文
6. 生成同步的 human + machine output
7. 需要时 review 与 retry

knowhow 会随时间变化：
- meeting-type reference 增长
- industry patches 改进
- sample cases 增加
- memory 使用更精准

不要把稳定流程与变化的知识层混为一谈。

## Meeting-type reference 设计规则

系统应演进为很多短小的 meeting-type references。
例子：
- first introduction meeting
- demand clarification meeting
- executive alignment meeting
- commercial negotiation meeting
- pilot / PoC review
- renewal expansion review
- escalation / complaint handling

每个 reference 要紧凑且可操作。
它告诉模型该注意什么，而不是要求固定文案。

## Best-case 设计规则

best-cases 是对照锚点，不是输出模板。
一个 best-case 应记录：
- 代表哪类会议
- 为什么这份总结很强
- 哪些 evidence-to-judgment 的转换做得好
- 哪些风险或推进信号被正确呈现

best-case 不能变成复制目标。
它是为了提升判断质量，不是为了统一措辞。

## Summary 质量规则

好的 CRM meeting summary 必须做到：
1. 忠实总结发生了什么
2. 解释这次会议在 account/opportunity 语境中的意义
3. 识别真实进展与表面礼貌
4. 识别关键风险与未决阻塞
5. 给出与证据绑定的下一步动作
6. 当历史支持时，体现关键人重复关注点
7. 用紧凑语义层表达当前业务状态

如果只是把会议说清楚，还不够。

## 产品评估规则

只有满足以下条件，skill 才算在正确轨道上：
- 总结明显更好，因为理解了客户与业务上下文
- 关键人反复关注点被显式呈现，而不是被埋掉
- 下一步动作因为 CRM 状态而更强，而不是只基于 transcript
- machine output 捕捉到可复用业务语义，不是零散 prose
- 用户能一眼看出这是 CRM 总结，不是通用会议工具

## Anti-patterns

避免以下错误：
- 固定模板把所有会议压成同一个形状
- 无节制拉取 CRM 数据
- memory 作为装饰而非判断信号
- 总结看起来精致但忽略 account stage 或风险
- 把 flow 当成 knowhow
- semantic labels 缺少证据支撑
- 把 best-cases 当成风格模板而不是判断参考

## 产品测试

产品只有在这些条件成立时才算对：
- 总结明显更好，因为理解了客户与业务上下文
- 关键人反复关注点被显式呈现，而不是被埋掉
- 下一步动作因为 CRM 状态而更强，而不是只基于 transcript
- 用户能一眼看出这是 CRM 总结，不是通用会议工具
