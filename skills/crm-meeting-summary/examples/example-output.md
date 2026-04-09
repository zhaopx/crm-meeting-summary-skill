# 输出示例

本文展示的是 **真实 `crm-meeting-summary` skill 的目标输出结构**。
其中 `mock_sources`、`missing_information_candidates` 这类字段如果只在开发验证中存在，应被视为 dev harness 附加信息，不是生产调用的必需字段。

## 人类可读总结示例

```text
会议快照
- 场景：需求澄清
- 模式：normal
- 目标：确认问题根因并判断是否进入试点

核心总结与判断
- 当前阶段：qualification
- 决策压力：budget priority depends on short-term proof
- 风险等级：medium

参考知识关注项
- 区分真实推进与礼貌性回应
- 缺失关键信息时只请求最小必要 CRM 字段
- 预算优先级与短期效果证明直接相关
- 实施复杂度会直接影响商业推进动能

建议下一步
- 一周内提交问题诊断与优化路径建议
- 补齐试点评估负责人与预算审批链条

风险与待确认问题
- 待补：implementation_status
- 待补：last_commitments
```

## 机器可读示例

```json
{
  "status": "passed",
  "human_summary": "会议快照\n- 场景：需求澄清\n- 模式：normal\n- 目标：确认问题根因并判断是否进入试点\n\n核心总结与判断\n- 当前阶段：qualification\n- 决策压力：budget priority depends on short-term proof\n- 风险等级：medium\n\n参考知识关注项\n- 区分真实推进与礼貌性回应\n- 缺失关键信息时只请求最小必要 CRM 字段\n- 预算优先级与短期效果证明直接相关\n- 实施复杂度会直接影响商业推进动能\n\n建议下一步\n- 一周内提交问题诊断与优化路径建议\n- 补齐试点评估负责人与预算审批链条\n\n风险与待确认问题\n- 待补：implementation_status\n- 待补：last_commitments",
  "review_result": {
    "pass": true,
    "review_status": "pass",
    "failure_reasons": [],
    "targeted_regeneration_instructions": [],
    "check_results": {
      "scenario_self_consistency": "pass",
      "knowhow_coverage": "pass",
      "evidence_grounding": "pass",
      "memory_conflict_handling": "pass",
      "missing_information_handling": "pass",
      "policy_boundary_handling": "pass",
      "semantic_normalization_consistency": "pass",
      "meeting_state_feature_evidence": "pass",
      "semantic_summary_consistency": "pass",
      "machine_output_completeness": "pass"
    },
    "notes": []
  },
  "base_context": {
    "meeting_time": "2026-04-06T15:00:00+08:00",
    "initiator": {"id": "USR-101", "name": "王敏"},
    "account": {"id": "CUST-001", "name": "华东零售集团"},
    "opportunity": {"id": "OPP-9001", "name": "智能客服升级项目"},
    "participants": [
      {"name": "王敏", "role": "客户成功经理"},
      {"name": "李总", "role": "客户运营负责人"},
      {"name": "陈经理", "role": "IT 负责人"}
    ]
  },
  "scenario_result": {
    "primary_scenario": "需求澄清",
    "scenario_slug": "needs-clarification",
    "scenario_confidence": "high",
    "scenario_mode": "normal",
    "industry": "general-b2b",
    "secondary_tags": ["risk:budget-priority", "risk:implementation-cost"],
    "evidence": [
      "客户反馈当前客服机器人命中率不稳定，夜间转人工率偏高",
      "李总明确表示，希望先确认问题是不是知识库更新机制导致，再决定是否进入新一轮采购",
      "客户提到 6 月前内部会做一次服务质量考核，如果效果没有改善，预算优先级会下降",
      "陈经理提到接口改造资源有限，需要尽量少改现有系统"
    ]
  },
  "semantic_normalization": {
    "object_aliases": {
      "customer": "account",
      "account": "account",
      "商机": "opportunity",
      "项目": "opportunity",
      "机会": "opportunity",
      "initiator": "person",
      "owner": "person",
      "联系人": "contact"
    },
    "lookup_keys": {
      "initiator": "person_id:USR-101",
      "account": "account_id:CUST-001",
      "opportunity": "opportunity_id:OPP-9001"
    },
    "resolved_objects": {
      "meeting": {
        "meeting_time": "2026-04-06T15:00:00+08:00",
        "title": null
      },
      "person": {
        "initiator": {
          "id": "USR-101",
          "name": "王敏",
          "role": "客户成功经理"
        }
      },
      "account": {
        "id": "CUST-001",
        "name": "华东零售集团",
        "owner": null
      },
      "opportunity": {
        "id": "OPP-9001",
        "name": "智能客服升级项目",
        "owner": null
      },
      "contact_mentions": [
        {"name": "李总", "role": "客户运营负责人", "mapped_scope": "contact"},
        {"name": "陈经理", "role": "IT 负责人", "mapped_scope": "contact"}
      ]
    },
    "relationship_map": [
      "meeting initiated_by person",
      "meeting linked_to account",
      "meeting linked_to opportunity",
      "account may_have_owner person",
      "opportunity may_have_owner person"
    ]
  },
  "meeting_state_features": {
    "relationship_state": "active-account, qualification-in-progress",
    "decision_pressure": "budget priority depends on short-term proof",
    "trust_state": "neutral-to-cautious",
    "momentum_state": "curious but not yet committed"
  },
  "loaded_knowhow": {
    "mapping_version": "v1",
    "common": ["skills/crm-meeting-summary/references/knowhow/common/general.md"],
    "scenario": ["skills/crm-meeting-summary/references/knowhow/by-scenario/needs-clarification.md"],
    "industry": ["skills/crm-meeting-summary/references/knowhow/by-industry/general-b2b.md"],
    "patches": ["skills/crm-meeting-summary/references/knowhow/patches/needs-clarification__general-b2b.md"],
    "best_cases": ["skills/crm-meeting-summary/references/knowhow/best-cases/needs-clarification__general-b2b__v1.md"]
  },
  "crm_data_requests": [
    {
      "reason": "risk_validation_gap",
      "fields": ["implementation_status", "last_commitments"],
      "why": "当 trust 或历史承诺成为风险点时，需要验证承诺是否兑现与实施状态。",
      "sources": ["knowhow:data_requirements:needs-clarification.md"]
    }
  ],
  "memory_sources": [],
  "memory_conflicts": [],
  "summary_fields": {
    "meeting_goal": "确认问题根因并判断是否进入试点",
    "relationship_state": "active-account, qualification-in-progress",
    "decision_pressure": "budget priority depends on short-term proof",
    "trust_state": "neutral-to-cautious",
    "momentum_state": "curious but not yet committed",
    "key_participants": ["王敏", "李总", "陈经理"],
    "current_stage_judgment": "qualification",
    "next_actions": ["一周内提交问题诊断与优化路径建议", "补齐试点评估负责人与预算审批链条"],
    "risk_level": "medium",
    "missing_information": ["implementation_status", "last_commitments"]
  },
  "semantic_summary": {
    "relationship_state": "active-account, qualification-in-progress",
    "decision_pressure": "budget priority depends on short-term proof",
    "trust_state": "neutral-to-cautious",
    "momentum_state": "curious but not yet committed"
  },
  "key_judgments": {
    "facts": [
      "会议主题：确认问题根因并判断是否进入试点",
      "会议中已经形成了我方需要补充诊断建议的明确动作。",
      "客户在 6 月前存在服务质量考核节点。"
    ],
    "inferences": ["当前阶段判断：qualification", "整体风险等级：medium"],
    "open_questions": ["缺失信息：implementation_status", "缺失信息：last_commitments"]
  },
  "knowhow_focus_items": [
    "区分真实推进与礼貌性回应",
    "缺失关键信息时只请求最小必要 CRM 字段",
    "预算优先级与短期效果证明直接相关",
    "实施复杂度会直接影响商业推进动能"
  ],
  "retrieval_trace": {
    "mapping_version": "v1",
    "scenario_mode": "normal",
    "allowed_request_groups": ["account_profile_gap", "stakeholder_gap", "risk_validation_gap"],
    "requested_request_groups": ["risk_validation_gap"],
    "out_of_policy_requests": []
  },
  "review_ready_checks": {
    "scenario_self_consistency": true,
    "knowhow_coverage": true,
    "evidence_grounding": true,
    "memory_conflict_handling": true,
    "missing_information_handling": true,
    "policy_boundary_handling": true,
    "semantic_normalization_consistency": true,
    "meeting_state_feature_evidence": true,
    "semantic_summary_consistency": true,
    "machine_output_completeness": true
  },
  "retry_state": {
    "revision": 0,
    "status": "passed",
    "history": []
  }
}
```

## review fail + manual_review_required 示例

```json
{
  "status": "manual_review_required",
  "review_result": {
    "pass": false,
    "review_status": "fail",
    "failure_reasons": [
      "会议原始证据过弱，无法支持可靠主结论。",
      "关键上下文缺失过多，机器输出仍不可安全下游消费。"
    ],
    "targeted_regeneration_instructions": [
      "不要补写新事实，只保留当前已知边界。",
      "明确请求客户问题、责任方、时间线和下一步 owner。"
    ]
  },
  "retry_state": {
    "revision": 2,
    "status": "manual_review_required",
    "history": [
      {
        "revision": 0,
        "review_status": "fail",
        "failed_checks": [
          "knowhow_coverage",
          "evidence_grounding",
          "missing_information_handling",
          "machine_output_completeness"
        ]
      },
      {
        "revision": 1,
        "review_status": "fail",
        "failed_checks": [
          "knowhow_coverage",
          "evidence_grounding",
          "missing_information_handling",
          "machine_output_completeness"
        ]
      }
    ]
  }
}
```

## 开发验证附加字段

如果通过 `mock_runner.py` 做本地验证，还可能出现：
- `mock_sources`
- `missing_information_candidates`

这些字段不属于真实 skill 调用的必需输出契约。
