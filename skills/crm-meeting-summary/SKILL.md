---
name: crm-meeting-summary
description: 当用户要求总结 CRM 会议纪要、基于客户或商机记录生成会议回顾、结合 CRM 上下文分析销售/客户会议，或使用行业/场景 knowhow、memory 与 review 校验来产出结构化会议总结时，应使用此 skill。
---

# CRM 会议总结

基于会议纪要和 CRM 上下文生成高质量 CRM 会议总结。保留模型推理空间，但严格约束证据边界与输出契约。

## 目的

从一条 CRM 会议记录中产出两份同步结果：
1. 面向销售、CS、交付或管理角色的人类可读会议总结。
2. 供下游流程使用的机器可消费中间结构。

整个流程必须 evidence-grounded。knowhow 和 memory 只能作为指导与上下文，不能成为编造事实的依据。

## 输入

输入包至少应包含：
- meeting record text
- initiator information
- account or opportunity association
- meeting time
- any directly provided CRM fields

缺失数据是常态。要明确指出缺失项，而不是强行下结论。

## 工作原则

1. 严格区分以下三类内容：
   - 来自 meeting notes 或 CRM data 的显式事实
   - 基于证据的高置信判断
   - 仍需确认的未决事项
2. 当前 meeting notes 和当前 CRM context 优先于 memory。
3. memory 只用于补强背景理解，例如历史承诺、关键人偏好、长期张力或关系连续性。
4. 把 knowhow 当作评估框架：
   - 这类会议真正重要的点是什么
   - 哪些风险信号重要
   - 哪些推进信号重要
   - 哪些边界不能跨
5. 禁止编造 CRM data、政策、行动项或客户意图。

## 工作流

### 第 1 步：归一化基础上下文

提取或整理最小基础上下文：
- meeting title，如果有
- meeting time
- initiator，表示为 `person` object
- account
- linked opportunity
- participants，如果有
- raw meeting record，仅作为输入

如果存在 object ID，优先使用 ID。没有 ID 时回退到名称。

### 第 2 步：识别会议场景

将会议归类为一个主场景，并可附带若干次级标签。

使用 `references/taxonomy.md` 中的场景体系。

主场景应依据业务意图判定，不能只看字面措辞。证据弱时，返回 `其他/不确定`，并解释原因。

次级标签可包括：
- industry
- customer_stage
- decision_chain_role
- risk
- compliance
- competitor

在 retrieval 前先做置信度闸门：
- `high` / `medium`：按正常场景驱动 retrieval 继续
- `low`：切换到 conservative mode

Conservative mode 规则：
- 除非某个场景仍然明显占优，否则优先使用 `其他/不确定`
- 默认只加载 `references/knowhow/common/`
- 只有行业有独立证据时才加载 industry knowhow
- 只请求能消除歧义的 CRM fields
- 除非当前事实强制要求第二个 scope，否则 memory 限制在单一 object scope
- 降低后续判断置信度
- 在 machine output 中标记 `scenario_mode: uncertain`

状态迁移与回退行为见 `references/retry-state-machine.md`。

### 第 3 步：加载参考知识

按以下顺序加载 knowhow：
1. `references/knowhow/common/`
2. `references/knowhow/by-scenario/<scenario_slug>.md`
3. 行业可识别时加载 `references/knowhow/by-industry/<industry>.md`
4. 场景和行业都可识别且补丁存在时，加载 `references/knowhow/patches/<scenario_slug>__<industry>.md`

使用 `references/taxonomy.md` 将 primary scenario 映射为文件查找所需的 `scenario_slug`。

`references/scenario-retrieval-mapping.md` 是默认 retrieval policy。

用 knowhow 来决定：
- 需要重点关注的信号
- 总结必须覆盖的点
- 场景特定成功标准
- 场景特定风险或政策边界
- 可能的下一步预期

### 第 4 步：决定需要哪些额外 CRM 字段

不要默认拉取全部数据。只决定为了生成更好总结所需的最小缺失 CRM data。

使用 `references/crm-data-dictionary.md` 中的字段字典。
使用 `references/scenario-retrieval-mapping.md` 限制默认允许的 CRM request groups。
如果 skill 请求了 mapping 之外的字段，要在 `retrieval_trace` 中记录例外及其证据。

具体决策顺序：
1. 先根据 scenario retrieval mapping 计算 `allowed_request_groups`
2. 再读取已加载的 scenario / patch knowhow 中声明的 `data_requirements`
3. 只有当 meeting evidence 与当前 CRM 缺失共同支持时，才把这些字段加入候选请求
4. 对同一 `request_group` 做去重合并，形成最终 `crm_data_requests`
5. 如果 knowhow 声明超出 `allowed_request_groups`，只能写入 `retrieval_trace.out_of_policy_requests`，不能默认拉取

`data_requirements` 只能细化 mapping 允许范围内的字段，不能绕过 policy 扩大默认 retrieval scope。
在 `scenario_mode = uncertain` 时，不执行 scenario / patch knowhow 的 `data_requirements`，仍按 mapping 的单个消歧 request bundle 降级。

返回一个按理由分组的 machine-readable CRM field 请求列表，例如：
- account_profile_gap
- opportunity_progress_gap
- risk_validation_gap
- history_gap

如果 runtime 只有 mock data，就把请求字段映射到 `examples/mock-data/` 下的 mock sources。

### 第 5 步：组装记忆上下文

从可用的 CRM 关联 scope 加载 memory：
- `person`
- `account`
- `opportunity`
- `contact`

只有当 contact 在会议或 CRM context 中被明确提及时，才加载 contact memory。

使用以下查找规则：
1. 有 object ID 时用 object ID
2. 否则用名称
3. 如果命中多个候选，标记歧义，不要猜

memory 只用于补充上下文。如果 memory 与当前 meeting evidence 或 CRM context 冲突，优先信任当前证据，并为 review 标记冲突。

只读取当前场景所需的最小相关子集，并记录每个 memory scope 的使用原因。

查找与优先级规则见 `references/memory-contract.md`。

### 第 6 步：生成总结

基于同一份事实底座同时生成两类输出。

#### Human-readable output

输出这些部分：
1. Meeting snapshot
2. Core summary and judgment
3. Knowhow focus items
4. Recommended next actions
5. Risks and open questions

#### Machine-consumable output

返回至少包含以下字段的结构化块：
- base_context
- scenario_result
- loaded_knowhow
- crm_data_requests
- memory_sources
- memory_conflicts
- summary_fields
- key_judgments
- knowhow_focus_items
- retrieval_trace
- retry_state
- review_ready_checks

优先使用 JSON。如果环境对原生 JSON 支持不好，就使用 fenced JSON block。

人类可读文本必须来自 machine output 中同一份 `summary_fields`、`key_judgments` 和 `knowhow_focus_items`。措辞可以展开，但不能与 machine output 矛盾。

### 第 7 步：调用评审流程

生成总结后，调用 `review/SKILL.md` 中的 review skill。

传给 review 的包要尽量精简，只包含：
- generated human-readable summary
- generated machine-readable output
- retrieval trace and retry state
- loaded knowhow identifiers
- 用于验证 claim 的最小支持证据摘录

除非某个争议检查项确实需要，不要重新发送完整原始上下文。

如果 review 失败，只根据 failure reasons 进行再生成。不要因为重写而漂移到无关部分。

Maximum regeneration count: 2。
使用 `references/retry-state-machine.md` 中的状态迁移。

如果超过重试上限后 review 仍失败，返回：
- current best summary
- review failure reasons
- `status: manual_review_required`

## 输出契约

### 必需标准字段

machine output 必须始终提供以下字段：
- `base_context.meeting_time`
- `base_context.initiator`
- `base_context.account`
- `base_context.opportunity`
- `scenario_result.primary_scenario`
- `scenario_result.scenario_slug`
- `scenario_result.scenario_confidence`
- `scenario_result.industry`
- `summary_fields.meeting_goal`
- `summary_fields.relationship_state`
- `summary_fields.decision_pressure`
- `summary_fields.trust_state`
- `summary_fields.momentum_state`
- `summary_fields.key_participants`
- `summary_fields.current_stage_judgment`
- `summary_fields.next_actions`
- `summary_fields.risk_level`
- `summary_fields.missing_information`
- `status`

### 人类总结要求

人类总结必须：
- 清楚给出主要业务结论
- 区分事实与推断
- 标出最重要的风险信号
- 标出最重要的机会或推进信号
- 给出由证据支撑的下一步建议
- 明确覆盖最相关的 knowhow focus items

## 失败处理

如果 meeting record 过于稀疏，无法支撑可靠总结：
1. 仍然尽量做场景分类
2. 相应降低置信度
3. 明确输出 missing information
4. 请求最小可用的额外 CRM data 集
5. 不要假装知道客户意图

## 参考文件

按需读取这些文件：
- `references/runtime-contract.md` - 输入、输出、trace 与 review handoff 的规范接口
- `references/taxonomy.md` - 场景分类体系与 tagging 规则
- `references/crm-data-dictionary.md` - CRM 字段字典与请求理由示例
- `references/memory-contract.md` - memory 查找与冲突处理规则
- `references/output-schema.md` - machine-readable output contract
- `references/review-rubric.md` - review 优先级与评分维度
- `references/retry-state-machine.md` - 再生成状态迁移与保守回退策略
- `references/scenario-retrieval-mapping.md` - 可审计的 scenario-to-retrieval policy

选择性读取 knowhow 文件：
- `references/knowhow/common/`
- `references/knowhow/by-scenario/`
- `references/knowhow/by-industry/`
- `references/knowhow/patches/`
- `references/knowhow/best-cases/`（有案例时作为参考）

## 示例

`examples/` 中包含：
- mock meeting input
- mock CRM objects
- mock memory records
- expected output structure
