# 输出示例

## 人类可读总结示例

### 会议快照
- 会议时间：2026-04-06 15:00 +08:00
- 发起人：王敏
- 客户：华东零售集团
- 商机：智能客服升级项目
- 主场景：需求澄清

### 核心总结与判断
本次会议核心不是确认采购，而是验证客户当前客服效果问题的根因，并判断是否值得进入下一阶段试点。客户已经明确把“效果改善能否被证明”与后续预算优先级绑定，说明当前机会仍处于资格验证而非实质推进阶段。会议中出现了明确推进信号：客户愿意等待我方提交问题诊断和优化路径建议，再决定是否进入试点；同时也出现了明显风险信号：6 月前客户内部将进行服务质量考核，若效果无改善，预算优先级会下降。

### 参考知识关注项
1. 真实需求与紧迫性
   - 已覆盖：客户指出夜间转人工率偏高，并将效果改善与 6 月前考核结果关联，存在真实业务压力。
2. 成功标准是否清晰
   - 部分覆盖：已明确要验证是否由知识库更新机制导致，但量化成功标准仍未完全明确。
3. 约束与阻塞因素
   - 已覆盖：IT 资源有限，需要尽量少改现有系统；预算优先级会受短期效果影响。

### 建议的下一步动作
1. 一周内提交问题诊断与优化路径建议，并显式说明低改造成本方案。
2. 在下轮沟通前补齐客户当前知识库更新机制、历史异常波动和服务质量考核标准。
3. 确认客户内部试点决策人和预算判断节点。

### 风险与待确认事项
- 风险：若短期内无法证明效果改善，客户可能不进入试点。
- 风险：接口改造资源有限，方案复杂度过高会直接压缩推进空间。
- 待确认：客户对“效果改善”的量化口径、试点评估负责人、预算审批链条。

## 机器可读示例

```json
{
  "status": "passed",
  "base_context": {
    "meeting_time": "2026-04-06T15:00:00+08:00",
    "initiator": {"id": "USR-101", "name": "王敏"},
    "account": {"id": "CUST-001", "name": "华东零售集团"},
    "opportunity": {"id": "OPP-9001", "name": "智能客服升级项目"},
    "participants": ["王敏", "李总", "陈经理"]
  },
  "scenario_result": {
    "primary_scenario": "需求澄清",
    "scenario_slug": "needs-clarification",
    "scenario_confidence": "high",
    "scenario_mode": "normal",
    "industry": "general-b2b",
    "secondary_tags": ["risk:budget-priority", "customer_stage:active_customer"],
    "evidence": [
      "客户希望先确认问题根因，再决定是否进入新一轮采购",
      "客户将效果改善与 6 月前考核及预算优先级绑定"
    ]
  },
  "loaded_knowhow": {
    "mapping_version": "v1",
    "common": ["references/knowhow/common/general.md"],
    "scenario": ["references/knowhow/by-scenario/needs-clarification.md"],
    "industry": ["references/knowhow/by-industry/general-b2b.md"],
    "patches": ["references/knowhow/patches/needs-clarification__general-b2b.md"],
    "best_cases": []
  },
  "crm_data_requests": [
    {
      "reason": "risk_validation_gap",
      "fields": ["recent_interactions", "last_commitments", "implementation_status"],
      "why": "需要验证效果问题是否持续存在，以及历史承诺是否影响当前信任。",
      "sources": ["knowhow:data_requirements"]
    }
  ],
  "memory_sources": [
    {
      "scope": "account",
      "lookup_key": "account_id:CUST-001",
      "used": true,
      "notes": ["客户过去续费前要求先看到量化效果改善。"]
    },
    {
      "scope": "opportunity",
      "lookup_key": "opportunity_id:OPP-9001",
      "used": true,
      "notes": ["客户内部预算竞争强，必须证明短期效果。"]
    }
  ],
  "memory_conflicts": [],
  "summary_fields": {
    "meeting_goal": "确认客服效果问题根因并判断是否值得进入试点",
    "relationship_state": "active-account, qualification-in-progress",
    "decision_pressure": "budget priority depends on short-term proof",
    "trust_state": "neutral-to-cautious",
    "momentum_state": "curious but not yet committed",
    "key_participants": ["李总", "陈经理"],
    "current_stage_judgment": "qualification",
    "next_actions": [
      "提交问题诊断与优化路径建议",
      "确认试点评估人与量化标准"
    ],
    "risk_level": "medium",
    "missing_information": [
      "效果改善量化标准",
      "预算审批链条",
      "试点决策人"
    ]
  },
  "semantic_summary": {
    "relationship_state": "active-account, qualification-in-progress",
    "decision_pressure": "budget priority depends on short-term proof",
    "trust_state": "neutral-to-cautious",
    "momentum_state": "curious but not yet committed"
  },
  "key_judgments": {
    "facts": [
      "客户对夜间转人工率偏高表示关注",
      "客户将是否进入试点与问题诊断结果绑定"
    ],
    "inferences": [
      "该机会仍处于资格验证阶段而非明确采购推进阶段"
    ],
    "open_questions": [
      "客户内部服务质量考核标准具体是什么"
    ]
  },
  "knowhow_focus_items": [
    {
      "item": "真实需求与紧迫性",
      "coverage": "covered",
      "evidence": ["客户将效果改善与 6 月前考核结果关联"],
      "recommended_action": "后续输出中继续量化业务压力和时间窗口"
    },
    {
      "item": "成功标准是否清晰",
      "coverage": "partial",
      "evidence": ["已明确要验证根因，但量化口径未明确"],
      "recommended_action": "补问量化标准与试点评估口径"
    }
  ],
  "retrieval_trace": {
    "mapping_version": "v1",
    "scenario_mode": "normal",
    "allowed_request_groups": ["account_profile_gap", "stakeholder_gap", "risk_validation_gap"],
    "requested_request_groups": ["risk_validation_gap"],
    "out_of_policy_requests": []
  },
  "retry_state": {
    "revision": 0,
    "status": "passed",
    "history": []
  },
  "review_ready_checks": {
    "scenario_self_consistency": true,
    "knowhow_coverage": true,
    "evidence_grounding": true,
    "memory_conflict_handling": true,
    "missing_information_handling": true,
    "policy_boundary_handling": true,
    "semantic_summary_consistency": true,
    "machine_output_completeness": true
  }
}
```
