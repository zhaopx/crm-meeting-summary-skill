# 运行时契约

版本: `v1`

本文是 `crm-meeting-summary` runtime interface 的单一事实来源。
它定义 inputs、outputs、trace fields 和 review handoff。

## 目的

- 为调用方提供稳定、可审计的接口。
- 防止 SKILL.md、examples、evals 与 schema 漂移。
- 让业务语义保持显式，而不是被藏进 prose。

## 对象模型

支持四类 CRM 关联 object scopes：
- `person`（initiator、internal owner、stakeholders）
- `account`（customer）
- `opportunity`
- `contact`

关系提醒：
- account / opportunity / contact 都可以有 owner，owner 始终是 `person`
- 一条 sales record 可以同时关联多个 objects
- meeting initiator 始终是 `person`

## 语义解释层

runtime 在生成最终措辞前，应先把原始 meeting 与 CRM inputs 归一为紧凑的业务语义层。
这不是 free-form prose。
它是可复用的 semantic summary，用来提升 review、retry 与下游自动化的可靠性。

建议语义维度：
- `relationship_state`
- `decision_pressure`
- `trust_state`
- `momentum_state`

推荐表示方式：
- 在 `summary_fields` 中复制这些语义字段，便于下游必需访问
- 必须同时输出单独的 `semantic_summary` block，供机器直接消费

`semantic_summary` 是必需顶层结构；`summary_fields` 中的同名字段是冗余访问层，不可替代它。

## 输入契约

### 必需输入

runtime 至少必须提供：
- meeting record text
- meeting time
- initiator，类型为 `person`
- account 或 opportunity association

### 可选输入

- meeting title
- participants list
- 已可用的 CRM fields
- 预取的 memory snippets

### 输入示例

```json
{
  "meeting": {
    "id": "MEET-001",
    "title": "需求澄清会 - 智能客服升级",
    "meeting_time": "2026-04-06T15:00:00+08:00",
    "initiator": {"id": "USR-101", "name": "王敏"},
    "account": {"id": "CUST-001", "name": "华东零售集团"},
    "opportunity": {"id": "OPP-9001", "name": "智能客服升级项目"},
    "participants": [
      {"name": "王敏", "role": "客户成功经理"},
      {"name": "李总", "role": "客户运营负责人"}
    ],
    "record_text": "..."
  },
  "crm_context": {
    "account": {
      "account_id": "CUST-001",
      "account_name": "华东零售集团"
    },
    "person": {
      "person_id": "USR-101",
      "person_name": "王敏",
      "person_role": "客户成功经理"
    }
  }
}
```

### 关键规则

- 有 ID 时优先使用基于 ID 的 key，没有 ID 时回退到 name。
- 禁止编造缺失的 CRM fields。
- 把缺失数据视为常态，并写入 `missing_information`。
- runtime package 要足够小，保证每个主要输出 claim 仍可审计。

## 输出契约

### 人类可读输出

必需部分：
1. Meeting snapshot
2. Core summary and judgment
3. Knowhow focus items
4. Recommended next actions
5. Risks and open questions

### 机器可读输出

使用 `references/output-schema.md` 中的 schema。
顶层 `status` 允许值：
- `passed`
- `manual_review_required`
- `insufficient_context`

### 输出示例

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
    "secondary_tags": ["risk:budget-priority"],
    "evidence": ["..."]
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
  "memory_sources": [],
  "memory_conflicts": [],
  "summary_fields": {
    "meeting_goal": "...",
    "relationship_state": "active-account, qualification-in-progress",
    "decision_pressure": "budget priority depends on short-term proof",
    "trust_state": "neutral-to-cautious",
    "momentum_state": "curious but not yet committed",
    "key_participants": [],
    "current_stage_judgment": "qualification",
    "next_actions": [],
    "risk_level": "medium",
    "missing_information": []
  },
  "semantic_summary": {
    "relationship_state": "active-account, qualification-in-progress",
    "decision_pressure": "budget priority depends on short-term proof",
    "trust_state": "neutral-to-cautious",
    "momentum_state": "curious but not yet committed"
  },
  "key_judgments": {
    "facts": [],
    "inferences": [],
    "open_questions": []
  },
  "knowhow_focus_items": [],
  "retrieval_trace": {
    "mapping_version": "v1",
    "scenario_mode": "normal",
    "allowed_request_groups": [],
    "requested_request_groups": [],
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

## 检索 Trace 契约

每次运行都必须输出 `retrieval_trace`：
- `mapping_version`
- `scenario_mode`
- `allowed_request_groups`
- `requested_request_groups`
- `out_of_policy_requests`

以 `references/scenario-retrieval-mapping.md` 作为 policy baseline。
如果请求了 policy 外字段，必须附带精确 evidence 与理由。

`crm_data_requests` 的形成顺序是：
1. 先由 scenario retrieval mapping 给出 `allowed_request_groups`
2. 再读取已加载 scenario / patch knowhow 中的 `data_requirements`
3. 只有 meeting evidence 与当前 CRM 缺失共同支持时，才允许把对应字段并入请求
4. 如果 knowhow 声明超出 `allowed_request_groups`，只能进入 `out_of_policy_requests`

`data_requirements` 只能细化允许组内的字段，不能直接扩大默认 retrieval scope。
当 `scenario_mode = uncertain` 时，不执行 scenario / patch knowhow 的 `data_requirements`，仍按 low-confidence fallback 只保留一个消歧 request bundle。

## 记忆契约使用

- 对该 skill 而言，memory 是只读的。
- scopes: person/account/opportunity/contact。
- 如果 memory 与当前 evidence 冲突，优先当前 evidence，并记录到 `memory_conflicts`。
- 使用 mixed keys：优先 `*_id`，回退到 `*_name`。

## Best-case 使用规范

- best-cases 是可选 reference，不是强制 retrieval。
- 只有在它们能提升已识别场景或行业的判断质量时才加载。
- 如果加载，需在 `loaded_knowhow.best_cases` 中记录标识。
- best-cases 绝不能覆盖当前 meeting evidence。

## 评审交接契约

调用 review skill 时，只传精简包：
- generated human summary
- generated machine output
- retrieval trace
- retry state
- loaded knowhow identifiers
- 最小支持证据摘录

review output 必须使用：
- `pass: true|false`
- `review_status: pass|fail`
- `failure_reasons`
- `targeted_regeneration_instructions`
- `check_results`

review output 与 summary output status 不是同一个概念。

## 失败与重试契约

- 状态迁移使用 `references/retry-state-machine.md`。
- 最多 2 次 targeted retries。
- 超过后返回 `status: manual_review_required`，并附最后一次 failure reasons。

## 参考文件

- `references/output-schema.md`
- `references/retry-state-machine.md`
- `references/scenario-retrieval-mapping.md`
- `references/memory-contract.md`
- `references/knowhow/best-cases/README.md`
- `review/SKILL.md`
