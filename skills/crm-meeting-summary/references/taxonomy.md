# CRM Meeting Scenario Taxonomy

Use this taxonomy to classify the primary scenario of a CRM meeting.

## Primary scenarios

### 1. 首次接触 / 破冰
- Definition: Early-stage contact intended to establish connection, understand high-level context, or open the relationship.
- Positive signals: self-introduction, background exchange, broad pain-point exploration, no detailed solution alignment yet.
- Exclusion signals: deep product walkthrough, confirmed project scope, active procurement discussion.
- Focus: relationship basis, problem framing, stakeholder mapping, next qualification step.

### 2. 需求澄清
- Definition: Meeting focused on clarifying business problems, scope, constraints, priorities, or success criteria.
- Positive signals: current process discussion, requirement list, problem deepening, success metric clarification.
- Exclusion signals: price negotiation dominates, implementation plan already locked.
- Focus: real need, urgency, constraints, decision factors, qualification quality.

### 3. 方案介绍 / 演示
- Definition: Meeting centered on solution explanation, product walkthrough, capability matching, or demo feedback.
- Positive signals: demo, capability mapping, feature questions, fit-gap analysis.
- Exclusion signals: contract/legal terms dominate, delivery issue review dominates.
- Focus: fit, objections, decision confidence, missing proof points.

### 4. 商务推进 / 谈判
- Definition: Meeting focused on commercial advancement such as pricing, package, procurement, ROI, or buying process.
- Positive signals: quote, budget, procurement path, comparison, negotiation terms, buying timeline.
- Exclusion signals: mostly technical fit discussion with no commercial motion.
- Focus: buying intent, blockers, commercial leverage, approval path, close risk.

### 5. 试点 / PoC 推进
- Definition: Meeting around pilot design, evaluation scope, success criteria, validation process, or proof milestones.
- Positive signals: pilot scope, milestone, acceptance criteria, test plan, evaluation owner.
- Exclusion signals: already in full implementation delivery.
- Focus: success definition, adoption risk, evaluation fairness, timeline discipline.

### 6. 项目交付 / 实施沟通
- Definition: Meeting focused on deployment, implementation progress, delivery issues, enablement, or execution coordination.
- Positive signals: timeline, owner, dependency, rollout, issue resolution, enablement.
- Exclusion signals: pre-sales qualification or pricing is still the main topic.
- Focus: delivery risk, dependency risk, stakeholder alignment, unblock plan.

### 7. 续约 / 增购
- Definition: Meeting intended to renew, expand scope, cross-sell, upsell, or revisit contract value.
- Positive signals: renewal timing, usage value, expansion need, additional seats/modules.
- Exclusion signals: fresh net-new discovery without existing relationship base.
- Focus: retained value, expansion signal, churn risk, proof of outcome.

### 8. 风险 / 投诉 / 升级处理
- Definition: Meeting triggered by dissatisfaction, escalation, delivery issue, trust damage, or business risk.
- Positive signals: complaint, urgency, disappointment, escalation language, missed commitments.
- Exclusion signals: normal status sync with no material concern.
- Focus: root risk, accountability, containment, recovery plan, relationship salvage.

### 9. 内部协同 / 复盘
- Definition: Internal CRM-related discussion for account strategy, handoff, decision support, or deal review.
- Positive signals: internal alignment, strategy review, owner coordination, next-step planning.
- Exclusion signals: customer-facing content dominates.
- Focus: decision clarity, owner clarity, risk map, coordinated action.

### 10. 其他 / 不确定
- Definition: Use when evidence does not strongly support any main scenario.
- Focus: explain ambiguity and list missing signals required for confident classification.

## Secondary tag dimensions

Use zero or more tags as evidence supports:
- industry
- customer_stage
- decision_chain_role
- risk
- compliance
- competitor

## Classification rules

1. Pick one primary scenario only.
2. Prefer business intent over literal meeting title.
3. If two scenarios compete, choose the one that best explains the main decision pressure in the meeting.
4. When evidence is weak, reduce confidence and use `其他/不确定`.
5. Record key evidence for the classification.
