# 运行时契约

版本: `v1`

本文是 `crm-meeting-summary` runtime interface 的单一事实来源。
它定义 inputs、outputs、trace fields 和 review handoff。

## 目的

- 为调用方提供稳定、可审计的接口。
- 防止 SKILL.md、examples、evals 与 schema 漂移。
- 让业务语义保持显式，而不是被藏进自然语言表述。

## 对象模型

支持四类 CRM 关联 object scopes：
- `person`（initiator、internal owner、stakeholders）
- `account`（底层对象 key；对外业务语义统一视为“客户”）
- `opportunity`
- `contact`

关系提醒：
- 客户 / opportunity / contact 都可以有 owner，owner 始终是 `person`
- 一条 sales record 可以同时关联多个 objects
- meeting initiator 始终是 `person`

## 三层运行时边界

runtime 在生成最终措辞前，必须先把输入拆成三个边界清晰的层：
1. `semantic_normalization`
2. `meeting_state_features`
3. `memory`

这三层职责不同，不能混写。

### 1. semantic_normalization

职责：统一 CRM 对象、关系、字段别名与 lookup 口径。

最少应覆盖：
- 对象标准名：`person / account / opportunity / contact / meeting`
- 对象别名映射，例如“客户 -> account”，“项目/商机/机会 -> opportunity”
- mixed key lookup：优先 `*_id`，回退 `*_name`
- 关系口径：如 `initiated_by / linked_to / belongs_to / owner`
- 已解析对象集合 `resolved_objects`

`semantic_normalization` 是对象语义归一层，不负责输出业务状态判断。

### 2. meeting_state_features

职责：从当前 meeting evidence + 当前 CRM context 中抽取当前会议状态特征。

推荐字段：
- `relationship_state`
- `decision_pressure`
- `trust_state`
- `momentum_state`

约束：
- 只能由当前会议证据与当前 CRM 上下文支撑
- 不能把历史 memory 当作主证据
- 可被 `summary_fields` 冗余复制，供下游直接消费

### 3. memory

职责：读取跨会议稳定背景，并显式处理与当前证据的关系。

适合读取的内容：
- relationship continuity
- stakeholder preference
- commitment history
- recurring risk pattern
- approval pattern

不适合直接作为 memory 主体的内容：
- 单次会议瞬时状态
- 一次性 next action
- 未被当前证据确认的当前结论

`memory_sources` 和 `memory_conflicts` 是 memory 层在输出侧的最小 trace，不替代 `semantic_normalization` 或 `meeting_state_features`。

## 兼容字段

为兼容旧版下游，允许继续输出 `semantic_summary`，但它只是 `meeting_state_features` 的兼容映射层。

约束：
- `semantic_summary` 不能再被定义为“语义归一层”
- `semantic_summary` 内容必须与 `meeting_state_features` 一致
- 语义归一信息必须进入 `semantic_normalization`，不能塞回 `semantic_summary`

## 输入契约

### 必需输入

runtime 至少必须提供：
- meeting record text，或可读取的 meeting record file path
- initiator，类型为 `person`
- 客户或商机关联

推荐提供：
- meeting time，如有

### 可选输入

- `input_bundle_path`
- meeting title
- participants list
- 已可用的 CRM fields
- 预取的 memory snippets
- `meeting.record_text_path`

### 输入字段规则

`meeting` 下与会议纪要相关的字段：
- `record_text: string | null`
- `record_text_path: string | null`

顶层可选字段：
- `input_bundle_path: string | null`

归一化优先级：
1. `record_text` 非空时，直接作为会议纪要来源
2. 否则如果 `record_text_path` 存在，runtime 读取该文件内容并填充内部 `record_text`
3. 否则如果 `input_bundle_path` 存在，runtime 读取目录中的 `meeting-record.txt`
4. 三者都缺失时，按缺失关键输入处理，并在 `missing_information` 中暴露

也就是执行 `record_text > record_text_path > input_bundle_path/meeting-record.txt` 的归一化优先级。

读取约束：
- 路径必须由调用方显式提供，runtime 不猜测路径
- 只把文件当纯文本读取，不引入额外格式解析
- 文件不存在、不可读或读取结果为空时，不得编造内容，必须显式暴露读取失败
- 如果同时提供 `record_text` 和 `record_text_path`，始终以 `record_text` 为准
- 如果目录输入存在对象文件，只允许读取：`AccountObj.json`、`NewOpportunityObj.json`、`PersonnelObj.json`、`ContactObj.json`
- 对象文件映射固定为：`AccountObj.json -> crm_context.account`、`NewOpportunityObj.json -> crm_context.opportunity`、`PersonnelObj.json -> crm_context.person`、`ContactObj.json -> crm_context.contact`
- runtime 不扫描目录中的其他文件，多余文件直接忽略
- 显式 `crm_context.*` 优先于目录中的对象文件

### 输入示例

```json
{
  "input_bundle_path": "/abs/path/case-001",
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
    "record_text_path": "/abs/path/meeting-notes.txt"
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

路径表示统一使用**仓库根目录相对路径**。例如：`skills/crm-meeting-summary/references/...`。
不要混用绝对路径、`references/...` 短路径和仓库相对路径。

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
    "common": ["skills/crm-meeting-summary/references/knowhow/common/general.md"],
    "scenario": ["skills/crm-meeting-summary/references/knowhow/by-scenario/needs-clarification.md"],
    "industry": ["skills/crm-meeting-summary/references/knowhow/by-industry/general-b2b.md"],
    "patches": ["skills/crm-meeting-summary/references/knowhow/patches/needs-clarification__general-b2b.md"],
    "best_cases": ["skills/crm-meeting-summary/references/knowhow/best-cases/needs-clarification__general-b2b__v1.md"]
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
    "semantic_normalization_consistency": true,
    "meeting_state_feature_evidence": true,
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
- scopes: person/account/opportunity/contact（其中 `account` 对外业务语义为“客户”）。
- 如果 memory 与当前 evidence 冲突，优先当前 evidence，并记录到 `memory_conflicts`。
- 使用 mixed keys：优先 `*_id`，回退到 `*_name`。
- 推荐把 memory 视为带时间层和状态的 memory cards，而不是无结构长文本。
- runtime 读取 memory 时只取当前 scenario 与 object scope 需要的最小子集，不做 broad sweep。
- `stale` memory 不得单独抬高关键 judgment 置信度；`contradicted` memory 只能用于冲突说明，不作正向支撑。

## Best-cases 使用规范

- best-cases 是可选 reference，不是强制 retrieval。
- 只有在它们能提升已识别场景或行业的判断质量时才加载。
- 如果加载，需在 `loaded_knowhow.best_cases` 中记录标识。
- best-cases 绝不能覆盖当前 meeting evidence。

## 评审交接契约

调用 review skill 时，只传精简包：
- 生成人类可读总结
- 生成的机器可读输出
- retrieval trace
- retry state
- 已加载 knowhow 标识
- 最小支持证据摘录

review 输出必须使用：
- `pass: true|false`
- `review_status: pass|fail`
- `failure_reasons`
- `targeted_regeneration_instructions`
- `check_results`

review 输出与 summary 输出状态不是同一个概念。

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
