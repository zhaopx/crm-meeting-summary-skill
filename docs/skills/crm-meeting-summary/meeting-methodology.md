# 会议方法论

版本: `v1`

本文只回答一个问题：为什么 `crm-meeting-summary` 不是普通 transcript summarizer。
它是产品层方法论，不定义运行时字段；输入输出与状态语义以 `runtime-contract.md` 为准。

## 核心判断

好的 CRM 会议总结，不是把会议内容整理得更顺眼。
它必须把这次会议放回 CRM 业务语境里，回答：
- 这是谁的会
- 当前关系或商机处在哪个阶段
- 这次会议改变了什么判断
- 哪些风险、推进条件、历史模式值得进入最终结论

如果做不到这些，就只是另一种 transcript summary。

## 方法论原则

### 1. 从会议事实出发，不从模板出发
先判断这次会真实在讨论什么，再决定输出结构。
禁止为了统一样式，把所有会议压成同一种模板。

### 2. 上下文要组装，不要倾倒
推荐公式：

`会议事实 + 客户画像 + relationship/stage + 当前风险因素 + relevant memory + meeting 类型参考`

要求：
- 只取最小必要上下文
- 每类上下文都有单独职责
- 缺失时显式暴露，不拿其他材料硬补

### 3. 语义层是产品价值，不是装饰
原始 CRM 字段本身没有价值。
真正有价值的是把原始字段归一成可判断、可审查的业务状态。

语义层至少要让下游能稳定理解：
- relationship state
- decision pressure
- trust state
- momentum state

同时保持边界：
- `semantic_normalization` 负责对象、关系、字段口径统一
- `meeting_state_features` 负责当前会议状态判断
- 这些中间语义层服务于内部分析、review 与调试，不是对用户承诺的正式交付物

### 4. Flow 与 knowhow 必须分层
稳定的是 flow，变化的是 knowhow。

稳定 flow：
1. 识别 meeting type / scenario
2. 加载合适 knowhow
3. 决定最小 CRM retrieval
4. 加载最小 memory
5. 构建语义上下文
6. 生成人类可读总结
7. 必要时 review 与定向修复

变化 knowhow：
- 场景参考
- 行业补充
- patch 规则
- best-case anchors
- memory 使用精度

不要把流程规则写进 knowhow，也不要把 knowhow 判断写成固定流程模板。

### 5. Best-case 是判断锚点，不是输出模板
best-case 的作用是提升 judgment quality，不是统一措辞。
它只能帮助模型理解“什么样的总结更强”，不能替代当前会议证据。

## 适用边界

`crm-meeting-summary` 应优于通用总结器的前提是：
- 会议与客户 / 商机 / 关系推进有关
- CRM 上下文与 meeting 类型会影响结论
- 风险、owner、决策压力、历史模式对下一步动作有真实影响

如果只是纯信息同步或无业务语境的会议记录整理，这套方法论收益会下降。

## 反模式

避免以下错误：
- 固定模板把所有会议压成同一个形状
- 无节制拉取 CRM 数据
- 用 stale memory 覆盖当前 meeting evidence
- 把 `semantic_normalization` 当成状态判断层
- 把内部分析层写成另一套平行语义系统
- 把 best-cases 当成风格模板
- 总结看起来完整，但忽略客户阶段、推进条件或关键风险

## 产品判断标准

只有满足以下条件，才说明这套方法论在生效：
- 总结明显因为 CRM 上下文而更强
- 关键人重复关注点被显式呈现
- 下一步动作与当前业务状态绑定，而不是只复述 transcript
- 内部分析层能稳定支撑业务判断，而不是零散句子
- 用户能一眼看出这是 CRM 总结，不是通用会议纪要

