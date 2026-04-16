# CRM 会议场景分类

版本: `v1`

使用这份 taxonomy 来识别 CRM 会议的主场景。

## 主场景

每个场景都有一个用于 `references/knowhow/by-scenario/` 文件查找的 `slug`。
每个场景同时定义默认 retrieval policy，用来约束默认允许拉取的 request groups 与默认禁止的 broad pull。

### 1. 首次接触 / 破冰
- Slug: `first-contact`
- 定义：早期接触，目标是建立连接、理解高层背景，或开启关系。
- 正向信号：自我介绍、背景交换、宽泛痛点探索、尚未进入详细方案对齐。
- 排除信号：深入产品 walkthrough、项目范围已确认、活跃 procurement 讨论。
- 关注点：关系基础、问题 framing、stakeholder mapping、下一步 qualification。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`
  - Allowed request groups：`stakeholder_gap`、`account_profile_gap`
  - Prohibited default pulls：完整 interaction history、合同/采购细节

### 2. 需求澄清
- Slug: `needs-clarification`
- 定义：聚焦于澄清业务问题、范围、约束、优先级或成功标准的会议。
- 正向信号：当前流程讨论、需求清单、问题深入、成功指标澄清。
- 排除信号：价格谈判主导，或实施计划已经锁定。
- 关注点：真实需求、紧迫性、约束、决策因素、qualification 质量。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`、`patch`
  - Allowed request groups：`account_profile_gap`、`stakeholder_gap`、`risk_validation_gap`
  - Prohibited default pulls：未被明确讨论的 pricing/package 细节

### 3. 方案介绍 / 演示
- Slug: `solution-demo`
- 定义：以方案说明、产品 walkthrough、能力匹配或 demo 反馈为中心的会议。
- 正向信号：demo、能力映射、功能问题、fit-gap 分析。
- 排除信号：合同/法务条款主导，或交付问题复盘主导。
- 关注点：适配度、异议、决策信心、缺失 proof points。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`、`patch`
  - Allowed request groups：`stakeholder_gap`、`history_gap`
  - Prohibited default pulls：完整 delivery/compliance status，除非实施风险已经显性出现

### 4. 商务推进 / 谈判
- Slug: `commercial-negotiation`
- 定义：聚焦于价格、套餐、procurement、ROI 或 buying process 的商业推进会议。
- 正向信号：quote、budget、procurement path、对比、谈判条款、购买时间线。
- 排除信号：主要仍是技术适配讨论，没有商业推进动作。
- 关注点：购买意向、阻塞点、商业杠杆、审批路径、close risk。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`、`patch`
  - Allowed request groups：`opportunity_progress_gap`、`stakeholder_gap`、`risk_validation_gap`
  - Prohibited default pulls：完整 support-ticket history，除非信任风险已显性出现

### 5. 试点 / PoC 推进
- Slug: `poc-advance`
- 定义：围绕试点设计、评估范围、成功标准、验证过程或 proof milestones 的会议。
- 正向信号：pilot scope、milestone、acceptance criteria、test plan、evaluation owner。
- 排除信号：已经进入完整实施交付。
- 关注点：成功定义、采用风险、评估公平性、时间线纪律。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`、`patch`
  - Allowed request groups：`opportunity_progress_gap`、`stakeholder_gap`、`risk_validation_gap`
  - Prohibited default pulls：完整 procurement 细节，除非评估已经进入购买流程

### 6. 项目交付 / 实施沟通
- Slug: `delivery-implementation`
- 定义：聚焦部署、实施进展、交付问题、enablement 或执行协同的会议。
- 正向信号：timeline、owner、dependency、rollout、问题解决、enablement。
- 排除信号：pre-sales qualification 或 pricing 仍是主话题。
- 关注点：交付风险、依赖风险、干系人对齐、解除阻塞计划。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`
  - Allowed request groups：`history_gap`、`risk_validation_gap`、`stakeholder_gap`
  - Prohibited default pulls：quote / amount / close-date，除非商业推进重新出现

### 7. 续约 / 增购
- Slug: `renewal-expansion`
- 定义：目标是续约、扩容、交叉销售、增购，或重新评估合同价值的会议。
- 正向信号：renewal timing、usage value、expansion need、额外 seats/modules。
- 排除信号：没有现有关系基础的全新 discovery。
- 关注点：留存价值、扩展信号、流失风险、效果证明。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`、`patch`
  - Allowed request groups：`account_profile_gap`、`opportunity_progress_gap`、`history_gap`、`risk_validation_gap`
  - Prohibited default pulls：深度 implementation 数据，除非交付风险影响续约

### 8. 风险 / 投诉 / 升级处理
- Slug: `risk-escalation`
- 定义：由不满、升级、交付问题、信任受损或业务风险触发的会议。
- 正向信号：complaint、urgency、失望、escalation language、承诺未兑现。
- 排除信号：没有实质担忧的普通状态同步。
- 关注点：根因风险、责任归属、止损、恢复方案、关系挽回。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`
  - Allowed request groups：`history_gap`、`risk_validation_gap`、`stakeholder_gap`
  - Prohibited default pulls：宽泛商业字段，除非 churn/commercial impact 已显性出现

### 9. 内部协同 / 复盘
- Slug: `internal-review`
- 定义：面向内部的 CRM 讨论，用于客户策略、handoff、决策支持或 deal review。
- 正向信号：内部对齐、策略复盘、owner 协同、下一步规划。
- 排除信号：以客户外部沟通内容为主。
- 关注点：决策清晰度、owner 清晰度、风险图谱、协同动作。
- 默认 retrieval policy：
  - Must-load knowhow：`common`、对应 `scenario`
  - Optional knowhow：`industry`
  - Allowed request groups：`stakeholder_gap`、`history_gap`、`opportunity_progress_gap`
  - Prohibited default pulls：跨无关对象的整库 memory sweep

### 10. 其他 / 不确定
- Slug: `uncertain`
- 定义：当证据不足以强支撑任一主场景时使用。
- 关注点：解释歧义，并列出完成可靠分类所缺的信号。
- 默认 retrieval policy：
  - Must-load knowhow：`common` only
  - Optional knowhow：`industry` only if independently evidenced
  - Allowed request groups：`stakeholder_gap` 或单一消歧 request bundle
  - Prohibited default pulls：scenario patch、broad CRM pull、broad memory pull

## 次级标签维度

在证据支持时，可使用零个或多个 tags：
- industry
- customer_stage
- decision_chain_role
- risk
- compliance
- competitor

## 分类规则

1. 只能选一个 primary scenario。
2. 业务意图优先于字面会议标题。
3. 如果两个 scenario 竞争，选最能解释会议主决策压力的那个。
4. 证据弱时，降低 confidence，并使用 `其他/不确定`。
5. 记录用于分类的关键 evidence。

## low-confidence fallback

如果 `scenario_confidence = low`：
- 只加载 `common` knowhow
- 只有行业有独立证据时才加载 `industry` knowhow
- 不加载 scenario patches
- CRM requests 限制为一个消歧 request bundle
- memory 限制为一个 object scope，除非当前事实要求更多
- 输出 `scenario_mode: uncertain`

## 使用规则

- taxonomy 负责定义场景与默认 retrieval policy
- runtime 必须先按 taxonomy 的 allowed request groups 收紧默认检索范围
- knowhow 的 `data_requirements` 只能细化 taxonomy 已允许的范围，不能新增默认 request groups
- 如果运行时需要例外检索，必须在 retrieval trace 中记录 evidence 与原因
