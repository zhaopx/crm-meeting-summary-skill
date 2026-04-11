# 运行时契约

版本: `v3-human-only`

本文是 `crm-meeting-summary` runtime interface 的单一事实来源。
它定义输入规范、人类可读输出要求、最小审计边界、retrieval 边界、memory 使用规则，以及 review handoff。

## 目的

- 为调用方提供稳定、可审计的人类总结接口。
- 防止 `SKILL.md`、evals、review 规则与运行时边界漂移。
- 保持业务语义显式，而不是藏进自然语言套话。
- 明确 template 只负责目录重排，不负责制造新事实。

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
- 最终人类总结中的状态判断必须能回溯到这里

### 3. memory

职责：读取与当前对象判断相关的跨会议背景，并显式处理与当前证据的关系。

适合读取的内容：
- 对象的长期偏好
- 对象的长期敏感点
- 重复出现的 blocker 或 objection 模式
- 稳定审批路径
- 历史承诺兑现 / 失约模式
- 关系连续性与长期信任背景

不适合直接作为 memory 主体的内容：
- 单次会议瞬时状态
- 一次性 next action
- 未被当前证据确认的当前结论

该 skill 消费的 memory 采用 object-first 设计：
- scopes: `person / account / opportunity / contact`
- 时间层只分 `today` 和 `long_term`
- 当前 meeting / CRM evidence 优先于 memory

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
4. 三者都缺失时，按缺失关键输入处理，并在最终总结中暴露读取失败或缺失项

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
- 把缺失数据视为常态，并在最终总结中写明待确认项。
- runtime package 要足够小，保证每个主要输出 claim 仍可审计。

## CRM 最小字段与请求组规则

### 最小字段口径

#### 客户字段（底层对象：account）
- `account_id`
- `account_name`
- `industry`
- `lifecycle_stage`
- `account_tier`
- `current_products`（可选）
- `recent_health_status`（可选）
- `known_risks`（可选）

#### 商机字段
- `opportunity_id`
- `opportunity_name`
- `stage`
- `amount`
- `expected_close_date`
- `competitor_presence`（可选）
- `next_milestone`（可选）
- `blocker_summary`（可选）

#### 互动字段
- `recent_interactions`
- `last_commitments`
- `open_followups`
- `prior_escalations`

#### 干系人字段
- `person_role`
- `account_owner`
- `decision_makers`（可选）
- `procurement_owner`（可选）
- `implementation_owner`（可选）

#### 联系人字段
- `contact_id`
- `contact_name`
- `title`
- `role_in_account`
- `is_decision_maker`（可选）
- `influence_level`（可选）
- `mobile`
- `email`

#### 人员字段
- `person_id`
- `person_name`
- `person_role`
- `work_phone`
- `email`
- `leader`

#### 交付 / 合规字段
- `implementation_status`
- `support_tickets`
- `contract_status`
- `procurement_status`
- `compliance_constraints`

### request groups

- `account_profile_gap`：会议提到客户背景，但客户 baseline 缺失时使用
- `opportunity_progress_gap`：会议讨论推进、价格、时间线或 blockers，但当前 opportunity state 缺失时使用
- `stakeholder_gap`：当 influence map、owner map 或 approval chain 很关键，但核心角色不清晰时使用
- `history_gap`：当 summary 依赖历史承诺、重复异议或跨会议连续性时使用
- `risk_validation_gap`：当出现潜在不满、升级、交付或合规问题，且需要验证时使用

### 请求形成规则

1. 先按 `taxonomy.md` 中的场景 policy 计算 `allowed_request_groups`
2. 再看已加载 knowhow 中声明的 `data_requirements`
3. 只有 meeting evidence 与当前 CRM 缺失共同支持时，才把字段加入候选请求
4. 对同一 request group 去重合并，形成最终 `crm_data_requests`
5. 如果 knowhow 声明超出允许范围，只记入 `out_of_policy_requests`，不得真正扩大 retrieval

请求输出示例：

```json
[
  {
    "reason": "opportunity_progress_gap",
    "fields": ["stage", "amount", "expected_close_date"],
    "why": "会议讨论了预算与成交时间，但当前 opportunity status 缺失。"
  }
]
```

## 检索边界与 trace 契约

### 基本规则

- 只请求真正能提升 summary judgment 质量的最小 CRM data
- 不能因为 knowhow、模板或记忆存在，就默认放大 retrieval
- 场景 policy 决定默认允许拉什么；knowhow 只能细化，不能突破
- 禁止 silent exceptions

### uncertain / low-confidence 模式

当 `scenario_confidence = low` 或进入 uncertain 模式时：
- 只加载 `common` knowhow
- 只有行业有独立证据时才加载 `industry` knowhow
- 不加载 scenario patches
- CRM requests 限制为一个消歧 request bundle
- memory 限制为一个 object scope，除非当前事实强制要求更多
- 最终总结必须显式表达不确定边界

### retrieval_trace 最小结构

如果 runtime 保留 retrieval 调试信息，至少应包含：

```json
{
  "retrieval_trace": {
    "policy_version": "taxonomy-v2-runtime-v3",
    "scenario_mode": "normal | uncertain",
    "allowed_request_groups": ["stakeholder_gap"],
    "requested_request_groups": ["stakeholder_gap"],
    "out_of_policy_requests": []
  }
}
```

### 例外记录规则

如果 skill 请求了 policy 之外的 retrieval，trace 必须记录：
- requested group
- 为什么当前场景 policy 不够
- 迫使例外发生的精确 evidence

不能只写“为了更完整”这种空话。

## Memory 使用契约

### 查找优先级

1. object ID
2. object name
3. ambiguous match -> 不猜，直接暴露歧义

Mixed key 规则：
- 有 `*_id` 时优先使用 `*_id`
- 没有 ID 时回退到 `*_name`
- 同一对象命中多个候选时，直接暴露歧义，不做猜测合并

### 使用规则

- 当前 meeting record 优先级最高
- 当前 CRM data 优先级第二
- memory 只做补充上下文，不能覆盖当前证据
- 如果 memory 提供的字段多于所需，只读最小相关子集
- memory 的读取目标是服务当前 summary judgment，而不是补全一套平行 CRM 事实库
- 只有 contact 在会议或 CRM context 中被明确提及时，才加载 contact memory
- runtime 读取 memory 时只取当前 scenario 与 object scope 需要的最小子集，不做 broad sweep

### 冲突处理

如果 memory 与当前 evidence 冲突：
1. 优先信任当前 meeting / CRM evidence
2. 标记冲突用于输出和 review
3. 如果冲突影响关键判断，降低对应判断强度
4. `contradicted` memory 只能用于说明冲突，不能再正向支撑 judgment

### 最小调试信息

如果 runtime 需要保留 memory 调试信息，可以继续使用 `memory_sources` 和 `memory_conflicts`：

```json
{
  "memory_sources": [
    {
      "scope": "account",
      "lookup_key": "account_id:CUST-001",
      "used": true,
      "notes": ["提供历史采购偏好上下文。"]
    }
  ],
  "memory_conflicts": [
    {
      "scope": "account",
      "field": "decision_style",
      "memory_claim": "通常先走采购评估",
      "current_evidence": "本次会议明确由业务 owner 先决策是否继续推进",
      "resolution": "优先使用当前会议证据"
    }
  ]
}
```

## 输出契约

### 唯一正式交付物

唯一正式交付物是一份**人类可读总结**。

这份总结必须覆盖：
1. Meeting snapshot
2. Core summary and judgment
3. Knowhow focus items
4. Recommended next actions
5. Risks and open questions

写法要求：
- 区分事实、判断、待确认问题
- 缺失项显式写缺失，不补写
- `Core summary and judgment` 应优先回答：当前阶段是什么、推进动能处于哪一档、第一阻塞点是什么、现在是否值得继续推进
- `Knowhow focus items` 用来压缩真正影响交易推进的门槛、边界和 qualification 信号，不复述内部推理过程
- `Recommended next actions` 必须可执行，且能被当前证据支持；优先写成任务单，而不是“继续跟进”这类空话
- `Risks and open questions` 要区分推进风险与交易缺口，避免把所有缺失信息都写成同一种问题
- 如果证据不足，必须降低判断强度或推动人工复核

### Template 模板输出要求

如果命中了 `template` 模板：
- 仍然必须覆盖以上五类信息
- 最终人类可读总结应按模板 section / item 顺序重排
- 模板只重组已有内容，不生成新事实
- 无法映射的模板项必须留空、标记 missing 或省略，不得补写

路径表示统一使用**仓库根目录相对路径**。例如：`skills/crm-meeting-summary/references/...`。
不要混用绝对路径、`references/...` 短路径和仓库相对路径。

### 最小审计信息

虽然不再要求机器可读 schema，但总结背后仍必须保留最小审计信息，供 review 与调试使用。最小审计信息至少包括：
- 场景判定：`primary_scenario / scenario_slug / scenario_confidence / industry`
- 当前会议特征：`relationship_state / decision_pressure / trust_state / momentum_state`
- 已加载 knowhow 标识
- 关键结论对应的最小证据摘录
- 缺失信息清单
- 如有 memory 冲突，冲突说明
- 如有模板，模板选择结果与映射缺口说明

这些信息可以作为内部草稿、review handoff 或开发验证产物存在，但**不是最终对用户承诺的正式输出 schema**。

## Template 模板契约

`template` 是与 `knowhow` 平行的参考资源类型，用来定义最终总结的目录结构，而不是提供新事实。

资源组织：
- `references/templates/common/`
- `references/templates/profiles/`

补充说明：
- `common/` 只放兜底模板
- `profiles/` 只放最终模板文件，命名为 `<scenario_slug>.md` 或 `<scenario_slug>--<industry>.md`
- template 不保留 `by-scenario/`、`by-industry/`、`patches/` 这类多层目录，因为 template 只需要最终命中一份，不做多模板叠加
- 模板文件使用 Markdown + frontmatter；frontmatter 只保留最小元数据，正文只写 section 标题和目录项，不写字段映射配置

模板选择规则：
1. 当 `scenario_mode = uncertain` 时，只允许使用 `skills/crm-meeting-summary/references/templates/common/default.md`
2. 否则按以下顺序选择第一份存在的模板：
   - `skills/crm-meeting-summary/references/templates/profiles/<scenario_slug>--<industry>.md`
   - `skills/crm-meeting-summary/references/templates/profiles/<scenario_slug>.md`
   - `skills/crm-meeting-summary/references/templates/common/default.md`

约束：
- `template` 只选一份最终模板，不做多模板合并
- `common` 只做兜底模板
- `profiles` 下每个文件都表示一份最终模板
- 模板作者只写 section 标题和目录项，不写字段映射配置
- `template` 只能消费已生成 summary 中已有内容
- 主 skill 最后必须根据该目录，把已生成 summary 中已有内容整合成一份符合该目录格式的最终文档
- 有内容就填入，没有内容就留空、标记 missing 或省略，不得编造
- `template` 不得覆盖当前 meeting evidence，也不得替代 review

## Best-cases 使用规范

- 只有在它们能提升已识别场景或行业的判断质量时才加载。
- 如果加载，需在内部审计信息里记录标识。
- best-cases 绝不能覆盖当前 meeting evidence。
- best-cases 的目录说明文档不是 runtime 依赖，不应被主 skill 或 runtime-contract 当成参考入口。
- best-cases 是 judgment anchors，不是 templates，也不是事实来源。
- 单个 best-case 应展示：最小会议上下文、关键 evidence excerpts、由 evidence 派生的关键判断、风险信号、下一步动作和缺失信息。
- best-cases 用于提升 judgment quality，不用于为无证据 claim 背书，也不应诱导 copy-paste 最终措辞。

## 评审交接契约

调用 review skill 时，只传精简包：
- 生成人类可读总结
- 已加载 knowhow 标识
- 模板选择结果与映射缺口说明（如果已应用模板）
- 最小支持证据摘录
- 缺失信息清单
- 必要的 memory conflict 说明

review 输出必须使用：
- `pass: true|false`
- `review_status: pass|fail`
- `failure_reasons`
- `targeted_regeneration_instructions`
- `check_results`

review 输出与最终总结交付不是同一个概念。

## 失败与人工复核契约

- 最多允许 2 次定向修复。
- 超过后必须保留当前最佳人类总结，并显式标注需要人工复核。
- 当原始证据过弱、关键上下文缺失过多、或核心判断无法稳定支撑时，不得伪装成已通过。
- 失败原因必须具体，不允许只写“信息不足”这类空话。

## 参考文件

- `skills/crm-meeting-summary/references/taxonomy.md`
- `skills/crm-meeting-summary/review/SKILL.md`
