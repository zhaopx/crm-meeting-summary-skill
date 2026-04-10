# 案例执行示例

本文展示 `crm-meeting-summary` 作为**真实 Claude skill**的一次完整执行链路。
`skills/mock-runtime/` 和 `mock_runner.py` 仍可用于开发验证，但不是生产运行路径。

## 案例
- 会议输入：`skills/mock-runtime/meeting-records/meeting-001.json`
- 客户 CRM：`skills/mock-runtime/crm/account/CUST-001.json`
- 商机 CRM：`skills/mock-runtime/crm/opportunity/OPP-9001.json`
- 人员 CRM：`skills/mock-runtime/crm/person/USR-101.json`

## 真实 skill 调用方式

调用方在 Claude 中触发 `crm-meeting-summary`，并提供会议纪要与 CRM 上下文。输入可以是自然语言，也可以是归一化输入包。会议纪要既可以直接内联，也可以通过 `meeting.record_text_path` 指向文件，也可以通过 `input_bundle_path` 让 skill 按固定目录协议读取 `meeting-record.txt`、`AccountObj.json`、`NewOpportunityObj.json`、`PersonnelObj.json`、`ContactObj.json`。

示例：

```text
请使用 crm-meeting-summary skill。

meeting time: 2026-04-06T15:00:00+08:00
initiator: 王敏（USR-101）
客户: 华东零售集团（CUST-001）
opportunity: 智能客服升级项目（OPP-9001）
participants:
- 王敏 / 客户成功经理
- 李总 / 客户运营负责人
- 陈经理 / IT 负责人

meeting record:
客户反馈当前客服机器人命中率不稳定，夜间转人工率偏高。李总明确表示，希望先确认问题是不是知识库更新机制导致，再决定是否进入新一轮采购。客户提到 6 月前内部会做一次服务质量考核，如果效果没有改善，预算优先级会下降。陈经理提到接口改造资源有限，需要尽量少改现有系统。
```

如果会议纪要过长，也可以改为文件输入：

```json
{
  "meeting": {
    "meeting_time": "2026-04-06T15:00:00+08:00",
    "initiator": {"id": "USR-101", "name": "王敏"},
    "account": {"id": "CUST-001", "name": "华东零售集团"},
    "opportunity": {"id": "OPP-9001", "name": "智能客服升级项目"},
    "participants": [
      {"name": "王敏", "role": "客户成功经理"},
      {"name": "李总", "role": "客户运营负责人"},
      {"name": "陈经理", "role": "IT 负责人"}
    ],
    "record_text_path": "/abs/path/meeting-notes.txt"
  },
  "crm_context": {
    "account": {"account_id": "CUST-001", "account_name": "华东零售集团"},
    "opportunity": {"opportunity_id": "OPP-9001", "opportunity_name": "智能客服升级项目"},
    "person": {"person_id": "USR-101", "person_name": "王敏"}
  }
}
```

## 第 1 步：基础上下文

skill 先把输入归一化为最小基础上下文：

```json
{
  "meeting_time": "2026-04-06T15:00:00+08:00",
  "initiator": {"id": "USR-101", "name": "王敏"},
  "account": {"id": "CUST-001", "name": "华东零售集团"},
  "opportunity": {"id": "OPP-9001", "name": "智能客服升级项目"},
  "participants": [
    {"name": "王敏", "role": "客户成功经理"},
    {"name": "李总", "role": "客户运营负责人"},
    {"name": "陈经理", "role": "IT 负责人"}
  ]
}
```

## 第 2 步：场景识别

判断结果：
- primary_scenario: `需求澄清`
- scenario_slug: `needs-clarification`
- scenario_confidence: `high`
- industry: `general-b2b`
- scenario_mode: `normal`

原因：
- 会议核心是确认问题根因，以及是否进入试点
- 预算优先级被短期效果证明绑定
- IT 改造约束直接影响后续推进方式

## 第 3 步：加载参考知识

加载的 knowhow：
- `skills/crm-meeting-summary/references/knowhow/common/general.md`
- `skills/crm-meeting-summary/references/knowhow/by-scenario/needs-clarification.md`
- `skills/crm-meeting-summary/references/knowhow/by-industry/general-b2b.md`
- `skills/crm-meeting-summary/references/knowhow/patches/needs-clarification__general-b2b.md`
- `skills/crm-meeting-summary/references/knowhow/best-cases/needs-clarification__general-b2b__v1.md`

## 第 4 步：CRM 检索决策

mapping 允许的 request groups：
- 客户画像缺口（机器组名仍为 `account_profile_gap`）
- `stakeholder_gap`
- `risk_validation_gap`

实际请求决策：
- 客户画像已知，不补拉 `account_profile_gap`
- 核心参与者已出现，不补拉 `stakeholder_gap`
- `risk_validation_gap` 命中，因为当前 record 提到了效果、预算优先级、历史承诺风险
- 最终只请求缺失字段：`implementation_status`、`last_commitments`

对应机器输出：

```json
{
  "crm_data_requests": [
    {
      "reason": "risk_validation_gap",
      "fields": ["implementation_status", "last_commitments"],
      "why": "当 trust 或历史承诺成为风险点时，需要验证承诺是否兑现与实施状态。",
      "sources": ["knowhow:data_requirements:needs-clarification.md"]
    }
  ],
  "retrieval_trace": {
    "mapping_version": "v1",
    "scenario_mode": "normal",
    "allowed_request_groups": ["account_profile_gap", "stakeholder_gap", "risk_validation_gap"],
    "requested_request_groups": ["risk_validation_gap"],
    "out_of_policy_requests": []
  }
}
```

## 第 5 步：语义归一

skill 先产出 `semantic_normalization`，统一对象、关系、字段口径：

```json
{
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
  "relationship_map": [
    "meeting initiated_by person",
    "meeting linked_to account",
    "meeting linked_to opportunity",
    "account may_have_owner person",
    "opportunity may_have_owner person"
  ]
}
```

解释：
- 这里解决的是对象统一，不是状态判断
- “项目 / 商机 / 机会” 被归一到 `opportunity`
- owner、initiator 等人相关角色统一归到 `person`

## 第 6 步：当前会议特征提取

在语义归一之后，再生成 `meeting_state_features`：

```json
{
  "relationship_state": "active-account, qualification-in-progress",
  "decision_pressure": "budget priority depends on short-term proof",
  "trust_state": "neutral-to-cautious",
  "momentum_state": "curious but not yet committed"
}
```

解释：
- 这是存量客户，不是首次接触
- 当前仍是 qualification，不是采购确认
- 客户愿意继续看，但前提是先证明效果、控制改造成本

## 第 7 步：生成人类可读总结，并展示最终机器输出快照

skill 先基于同一份事实底座生成 summary draft；本节同时展示 review 通过后的**最终交付快照**，因此下面的机器可读输出已包含 `review_result`。

最终交付包含：
- 人类可读总结
- 机器可读输出

人类可读总结示例：

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

对应机器可读输出示例：

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

## 第 8 步：调用 review skill

主 skill 生成 draft 后，调用 `crm-meeting-summary-review`。

这条 baseline case 的 review 结果：

```json
{
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
  }
}
```

因为 review 通过，所以不会进入 retry。

## 第 9 步：最终机器可读输出与执行面捕获

关键结果：
- `status = passed`
- `retry_state = {"revision": 0, "status": "passed", "history": []}`
- `review_ready_checks` 全为 `true`

这表示：
- 真实 skill 已完成总结
- review 已通过
- 可以安全交付

为了真正确认每个 case 的最终 JSON 输出，仓库内新增了一个最薄执行面：
- `skills/crm-meeting-summary/real_runner.py`：调用真实 skill，捕获完整最终返回值
- `tests/crm_meeting_summary/evals/run_real_evals.py`：批量执行关键 eval case
- `skills/crm-meeting-summary/devtools/contract_validator.py`：校验机器可读 JSON 是否满足 contract

执行面至少保留这些产物：
- `raw_response`：CLI 返回的完整原始回包
- `final_text`：经筛选后的最终主 skill 文本，不取 review skill 的 pass/fail JSON
- `extracted_machine_json`：从最终文本或 review handoff 中嵌入的 `【生成的机器可读输出】` 提取出的机器可读 JSON
- `extraction_meta`：提取来源，例如 `fenced_json`、`embedded_machine_output`

## 第 10 步：失败样例如何停止自动化

当输入像 `meeting-hard-fail.json` 一样只剩“客户不满意”这种空壳信息时，真实 skill 也应遵循同一状态机：
- 先产出当前最佳 draft
- 交给 review
- 最多 2 次 targeted regeneration
- 仍失败则输出 `manual_review_required`

示例：

```json
{
  "status": "manual_review_required",
  "retry_state": {
    "revision": 2,
    "status": "manual_review_required"
  },
  "review_result": {
    "pass": false,
    "review_status": "fail",
    "failure_reasons": [
      "会议原始证据过弱，无法支持可靠主结论。",
      "关键上下文缺失过多，机器可读输出仍不可安全下游消费。"
    ]
  }
}
```

这表示当前不是“再润色一下”能解决的问题，必须补上下文。

## 开发验证路径

如果你只是想在本地验证 mock data 与 contract 是否一致，仍可以使用：

```bash
python3 skills/crm-meeting-summary/mock_runner.py \
  --meeting-file skills/mock-runtime/meeting-records/meeting-001.json \
  --scenario-slug needs-clarification \
  --scenario-confidence high \
  --industry general-b2b \
  --account-file skills/mock-runtime/crm/account/CUST-001.json \
  --opportunity-file skills/mock-runtime/crm/opportunity/OPP-9001.json \
  --person-file skills/mock-runtime/crm/person/USR-101.json
```

但这只是 dev harness，不是生产 skill 调用方式。
