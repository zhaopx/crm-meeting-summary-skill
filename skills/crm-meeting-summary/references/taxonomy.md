# CRM Meeting Scenario Taxonomy

版本: `v1`

使用这份 taxonomy 来识别 CRM meeting 的 primary scenario。

## Primary scenarios

每个 scenario 都有一个用于 `references/knowhow/by-scenario/` 文件查找的 `slug`。

### 1. 首次接触 / 破冰
- Slug: `first-contact`
- Definition: 早期接触，目标是建立连接、理解高层背景，或开启关系。
- Positive signals: 自我介绍、背景交换、宽泛痛点探索、尚未进入详细方案对齐。
- Exclusion signals: 深入产品 walkthrough、项目范围已确认、活跃 procurement 讨论。
- Focus: 关系基础、问题 framing、stakeholder mapping、下一步 qualification。

### 2. 需求澄清
- Slug: `needs-clarification`
- Definition: 聚焦于澄清业务问题、范围、约束、优先级或成功标准的会议。
- Positive signals: 当前流程讨论、需求清单、问题深入、成功指标澄清。
- Exclusion signals: 价格谈判主导，或实施计划已经锁定。
- Focus: 真实需求、紧迫性、约束、决策因素、qualification 质量。

### 3. 方案介绍 / 演示
- Slug: `solution-demo`
- Definition: 以方案说明、产品 walkthrough、能力匹配或 demo 反馈为中心的会议。
- Positive signals: demo、能力映射、功能问题、fit-gap 分析。
- Exclusion signals: 合同/法务条款主导，或交付问题复盘主导。
- Focus: fit、异议、决策信心、缺失 proof points。

### 4. 商务推进 / 谈判
- Slug: `commercial-negotiation`
- Definition: 聚焦于价格、套餐、procurement、ROI 或 buying process 的商业推进会议。
- Positive signals: quote、budget、procurement path、对比、谈判条款、购买时间线。
- Exclusion signals: 主要仍是技术适配讨论，没有商业推进动作。
- Focus: buying intent、blockers、商业杠杆、审批路径、close risk。

### 5. 试点 / PoC 推进
- Slug: `poc-advance`
- Definition: 围绕试点设计、评估范围、成功标准、验证过程或 proof milestones 的会议。
- Positive signals: pilot scope、milestone、acceptance criteria、test plan、evaluation owner。
- Exclusion signals: 已经进入完整实施交付。
- Focus: success definition、adoption risk、evaluation fairness、timeline discipline。

### 6. 项目交付 / 实施沟通
- Slug: `delivery-implementation`
- Definition: 聚焦部署、实施进展、交付问题、enablement 或执行协同的会议。
- Positive signals: timeline、owner、dependency、rollout、问题解决、enablement。
- Exclusion signals: pre-sales qualification 或 pricing 仍是主话题。
- Focus: delivery risk、dependency risk、stakeholder alignment、unblock plan。

### 7. 续约 / 增购
- Slug: `renewal-expansion`
- Definition: 目标是续约、扩容、交叉销售、增购，或重新评估合同价值的会议。
- Positive signals: renewal timing、usage value、expansion need、额外 seats/modules。
- Exclusion signals: 没有现有关系基础的全新 discovery。
- Focus: retained value、expansion signal、churn risk、效果证明。

### 8. 风险 / 投诉 / 升级处理
- Slug: `risk-escalation`
- Definition: 由不满、升级、交付问题、信任受损或业务风险触发的会议。
- Positive signals: complaint、urgency、失望、escalation language、承诺未兑现。
- Exclusion signals: 没有实质担忧的普通状态同步。
- Focus: 根因风险、责任归属、止损、恢复方案、关系挽回。

### 9. 内部协同 / 复盘
- Slug: `internal-review`
- Definition: 面向内部的 CRM 讨论，用于 account strategy、handoff、决策支持或 deal review。
- Positive signals: 内部对齐、策略复盘、owner 协同、下一步规划。
- Exclusion signals: 以客户外部沟通内容为主。
- Focus: 决策清晰度、owner 清晰度、风险图谱、协同动作。

### 10. 其他 / 不确定
- Slug: `uncertain`
- Definition: 当证据不足以强支撑任一主场景时使用。
- Focus: 解释歧义，并列出完成可靠分类所缺的信号。

## Secondary tag dimensions

在证据支持时，可使用零个或多个 tags：
- industry
- customer_stage
- decision_chain_role
- risk
- compliance
- competitor

## Classification rules

1. 只能选一个 primary scenario。
2. 业务意图优先于字面会议标题。
3. 如果两个 scenario 竞争，选最能解释会议主决策压力的那个。
4. 证据弱时，降低 confidence，并使用 `其他/不确定`。
5. 记录用于分类的关键 evidence。
