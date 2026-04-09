---
name: crm-meeting-summary
description: 当用户要求总结 CRM 会议纪要、基于客户或商机记录生成会议回顾、结合 CRM 上下文分析销售/客户会议，或使用行业/场景 knowhow、memory 与 review 校验来产出结构化会议总结时，应使用此 skill。
---

# CRM 会议总结

把这份 skill 当成**真实运行时入口**，不是说明文档，也不是 Python 模拟器包装。

你的任务是在 Claude runtime 内直接完成：
1. 读取输入包
2. 识别场景并决定最小 retrieval
3. 生成同源的人类可读总结和机器可读 JSON
4. 调用 `review/SKILL.md` 做评审
5. 在最多 2 次 retry 内完成定向修复
6. 返回最终可交付结果

禁止把 `mock_runner.py` 当成真实运行路径。
如果需要参考 mock data、examples 或 evals，只把它们当作开发辅助，不当作运行时依赖。

## 调用输入

真实调用时，输入应尽量归一为以下包。用户可以直接给自然语言内容，你要先归一到这个结构再继续：

```json
{
  "input_bundle_path": "string | null",
  "meeting": {
    "title": "string | null",
    "meeting_time": "string | null",
    "initiator": {"id": "string | null", "name": "string | null"},
    "account": {"id": "string | null", "name": "string | null"},
    "opportunity": {"id": "string | null", "name": "string | null"},
    "participants": [],
    "record_text": "string | null",
    "record_text_path": "string | null"
  },
  "crm_context": {
    "account": {},
    "opportunity": {},
    "person": {},
    "contact": {}
  },
  "memory_snippets": [],
  "constraints": {
    "language": "zh-CN",
    "output_mode": "human_and_json"
  }
}
```

### 最小必需输入

至少要有：
- meeting record text，或可读取的 `meeting.record_text_path`
- meeting time，如有
- initiator，类型为 `person`
- 客户或商机关联

如果用户只给自然语言纪要，而没有显式 JSON：
- 先在内部整理出 `meeting` / `crm_context` / `constraints`
- 如果用户给的是文件路径，先读取文件内容并归一到内部 `record_text`
- 如果用户给的是目录路径，且表示目录内已按固定命名准备好测试输入，则按 `input_bundle_path` 读取白名单文件装配输入包
- 再继续执行后续步骤

如果关键输入缺失：
- 不要编造
- 在 `summary_fields.missing_information` 中明确写出
- 在必要时返回 `status: insufficient_context`

## 工作原则

1. 严格区分三类内容：
   - 来自会议纪要或 CRM data 的显式事实
   - 基于证据的高置信判断
   - 仍需确认的未决事项
2. 当前会议纪要和当前 CRM 上下文优先于 memory。
3. memory 只用于补强背景理解，例如历史承诺、关键人偏好、长期张力或关系连续性。
4. knowhow 只是评估框架，不是事实来源。
5. 禁止编造 CRM data、政策、行动项或客户意图。
6. 人类可读总结和机器可读 JSON 必须来自同一份事实底座。
7. 真正交付给用户之前，必须经过 review skill。

## 运行时工作流

### 第 1 步：归一化基础上下文

先整理最小基础上下文，生成 `base_context`：
- meeting title，如果有
- meeting time
- initiator，表示为 `person` object
- 客户
- linked opportunity
- participants，如果有
- raw meeting record，仅作为输入来源，不直接放进最终输出

会议纪要输入优先级：
1. `meeting.record_text` 非空时直接使用
2. 否则如果 `meeting.record_text_path` 存在，读取文件内容后填入内部 `record_text`
3. 否则如果提供了 `input_bundle_path`，读取 `meeting-record.txt`
4. 三者都缺失时，按关键输入缺失处理

也就是执行 `record_text > record_text_path > input_bundle_path/meeting-record.txt` 的归一化优先级。

目录输入包约束：
- `input_bundle_path` 必须由调用方显式提供，不自动猜测目录
- 只读取固定白名单文件，不扫描目录内其他文件
- 固定文件名为：`meeting-record.txt`、`AccountObj.json`、`NewOpportunityObj.json`、`PersonnelObj.json`、`ContactObj.json`
- `meeting-record.txt` 按纯文本读取
- `AccountObj.json` -> `crm_context.account`
- `NewOpportunityObj.json` -> `crm_context.opportunity`
- `PersonnelObj.json` -> `crm_context.person`
- `ContactObj.json` -> `crm_context.contact`
- 多余文件一律忽略，不参与归一化
- 显式 `crm_context.*` 优先于目录中的对象文件

文件读取约束：
- 路径必须由调用方显式提供，不自动猜测
- 只按纯文本读取，不引入额外格式解析
- 读取失败、文件不存在或内容为空时，不得编造，必须把失败暴露到 `missing_information`

规则：
- 有 object ID 时优先使用 ID
- 没有 ID 时回退到名称
- 未知值写 `null`，不要补写

### 第 2 步：识别会议场景

使用 `references/taxonomy.md` 判定：
- `primary_scenario`
- `scenario_slug`
- `scenario_confidence`
- `secondary_tags`
- `industry`

先做置信度闸门：
- `high` / `medium`：继续正常 retrieval
- `low`：进入 conservative mode

Conservative mode 规则：
- 除非某个场景明显占优，否则优先返回 `其他/不确定`
- `primary_scenario` 必须写成 `其他 / 不确定`
- `scenario_slug` 必须写成 `uncertain`
- 默认只加载 `references/knowhow/common/`
- 只有行业有独立证据时才加载 industry knowhow
- 不加载 scenario knowhow、patches、best-cases
- 只请求能消除歧义的 CRM fields
- `requested_request_groups` 最多只允许一个消歧 bundle
- 除非当前事实强制要求第二个 scope，否则 memory 限制在单一 object scope
- 降低后续判断置信度
- 在机器输出中标记 `scenario_mode: uncertain`

场景判断补充要求：
- 如果会议只表达了“再看看”“后面再评估”“可能有优化空间”这类弱信号，且无法区分预算、采购、试点、交付，就按 low confidence 处理。
- 如果会议同时出现服务质量异常、承诺落空、不满或升级语气，优先检查是否应归入 `风险 / 投诉 / 升级处理` 或 `项目交付 / 实施沟通`，不要被历史续费叙事带偏。
- 如果当前会议事实与 memory 冲突，必须保留当前会议结论，并在 `memory_conflicts` 中显式记录冲突内容；必要时把 `scenario_confidence` 或相关 judgment 降低一档。

状态迁移与回退行为见 `references/retry-state-machine.md`。

### 第 3 步：加载参考知识

按以下顺序加载 knowhow：
1. `references/knowhow/common/`
2. `references/knowhow/by-scenario/<scenario_slug>.md`
3. 行业可识别时加载 `references/knowhow/by-industry/<industry>.md`
4. 场景和行业都可识别且补丁存在时，加载 `references/knowhow/patches/<scenario_slug>__<industry>.md`
5. best-cases 仅在确有帮助时才加载，并记录到 `loaded_knowhow.best_cases`

使用 knowhow 来决定：
- 需要重点关注的信号
- 总结必须覆盖的点
- 场景特定成功标准
- 场景特定风险或政策边界
- 可能的下一步预期

### 第 4 步：决定需要哪些额外 CRM 字段

不要默认拉取全部数据。只决定为了生成更好总结所需的最小缺失 CRM data。

必须同时遵守：
- `references/crm-data-dictionary.md`
- `references/scenario-retrieval-mapping.md`

决策顺序：
1. 先根据 scenario retrieval mapping 计算 `allowed_request_groups`
2. 再读取已加载 scenario / patch knowhow 中声明的 `data_requirements`
3. 只有当 meeting evidence 与当前 CRM 缺失共同支持时，才把这些字段加入候选请求
4. 对同一 `request_group` 去重合并，形成最终 `crm_data_requests`
5. 如果 knowhow 声明超出 `allowed_request_groups`，只能写入 `retrieval_trace.out_of_policy_requests`

硬性要求：
- `data_requirements` 只能细化 mapping 允许范围内的字段
- 不能绕过 policy 扩大 retrieval scope
- 在 `scenario_mode = uncertain` 时，不执行 scenario / patch knowhow 的 `data_requirements`

### 第 5 步：语义归一

先构造 `semantic_normalization`，只负责对象、关系、字段口径统一。

最少要做：
- 把 initiator、owner、stakeholder 统一映射到 `person`
- 把客户统一映射到 `account`
- 把“项目 / 商机 / 机会”等异构叫法统一映射到 `opportunity`
- 对参与人里被提及但不等于 initiator 的外部联系人，按证据映射为 `contact`
- mixed key lookup：优先 `*_id`，回退 `*_name`
- 显式产出对象关系，例如：
  - `meeting initiated_by person`
  - `meeting linked_to account`
  - `meeting linked_to opportunity`
  - `account may_have_owner person`
  - `opportunity may_have_owner person`

约束：
- 这一步不输出状态判断
- 不把 `relationship_state / trust_state / decision_pressure / momentum_state` 塞进语义归一层
- 对象口径统一规则以 `references/runtime-contract.md` 为准

### 第 6 步：当前会议特征提取

在 `semantic_normalization` 之后，再生成 `meeting_state_features`。

推荐字段：
- `relationship_state`
- `decision_pressure`
- `trust_state`
- `momentum_state`

约束：
- 只能由当前会议纪要与当前 CRM context 支撑
- history memory 只能作为背景，不得覆盖当前会议特征
- `summary_fields` 中可以冗余复制这四个字段，但来源仍是 `meeting_state_features`

### 第 7 步：组装记忆上下文

从可用的 CRM 关联 scope 加载最小 memory 子集：
- `person`
- `account`（对外业务语义：客户）
- `opportunity`
- `contact`

规则：
- 只有 contact 在会议或 CRM 上下文中被明确提及时，才加载 contact memory
- 有 object ID 时优先用 object ID
- 否则用名称
- 命中多个候选时，标记歧义，不要猜
- memory 与当前 meeting/CRM 事实冲突时，优先信任当前证据，并记录到 `memory_conflicts`
- `memory_sources` 只记录实际读取并参与判断的最小子集；没有使用就输出空数组
- 冲突记录至少包含：冲突 scope、被旧 memory 支撑的旧说法、当前会议/CRM 的相反证据
- 如果冲突影响主场景、风险等级、decision pressure、current_stage_judgment 中任一项，必须同步降低对应判断置信度或在 open questions 中暴露不确定边界

查找与优先级规则见 `references/memory-contract.md`。

### 第 8 步：生成总结

基于同一份事实底座同时生成两类输出。

#### 人类可读输出

必须输出以下 5 段：
1. 会议快照
2. 核心总结与判断
3. Knowhow 关注点
4. 建议的下一步动作
5. 风险与待确认问题

#### 机器可读输出

返回至少包含以下字段：
- `status`
- `base_context`
- `scenario_result`
- `semantic_normalization`
- `meeting_state_features`
- `loaded_knowhow`
- `crm_data_requests`
- `memory_sources`
- `memory_conflicts`
- `summary_fields`
- `semantic_summary`
- `key_judgments`
- `knowhow_focus_items`
- `retrieval_trace`
- `retry_state`
- `review_ready_checks`

优先使用原生 JSON；如果环境不适合，就用 fenced JSON block。

人类可读文本必须来自机器输出中同一份：
- `summary_fields`
- `meeting_state_features`
- `semantic_summary`
- `key_judgments`
- `knowhow_focus_items`

可以扩展措辞，不能与机器输出矛盾。

### 第 7 步：调用评审流程

生成 draft 后，必须调用 `review/SKILL.md`。

传给 review 的包只包含：
- 生成人类可读总结
- 生成的机器可读输出
- retrieval trace 和 retry state
- 已加载 knowhow 标识
- 用于验证 claim 的最小支持证据摘录

不要重新发送完整原始上下文，除非争议检查项确实需要。

#### Review loop 规则

- revision 0 draft 失败后，只根据 `failure_reasons` 和 `targeted_regeneration_instructions` 定向修复
- revision 1 失败后，再做一次更严格的定向修复
- maximum regeneration count: 2
- revision 2 仍失败时，返回：
  - 当前最佳总结
  - 当前最佳机器可读结构
  - review failure reasons
  - 最后一轮 `targeted_regeneration_instructions`
  - 带 `retry_state.history` 的追踪包
  - `status: manual_review_required`
  - `retry_state.revision = 2`

失败路径硬性要求：
- 如果证据过弱，导致主结论、建议的下一步动作或风险判断无法被稳定支撑，不得继续伪装成 `passed`，必须沿状态机进入 `manual_review_required`。
- `review_ready_checks` 在 fail 路径下必须按实际失败项写成 boolean，不能默认全 `true`。
- `retry_state.history` 必须逐轮记录失败的 checks；不得省略。

禁止：
- 为了风格整份重写
- 因为 retry 而扩大无关 retrieval scope
- 引入 evidence 中不存在的新事实

## 输出契约

必须遵守：
- `references/runtime-contract.md`
- `references/output-schema.md`
- `references/retry-state-machine.md`

### 必需标准字段

机器输出必须始终提供以下字段：
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
- `semantic_summary.relationship_state`
- `semantic_summary.decision_pressure`
- `semantic_summary.trust_state`
- `semantic_summary.momentum_state`
- `status`

### 人类总结要求

人类总结必须：
- 清楚给出主要业务结论
- 区分事实与推断
- 标出最重要的风险信号
- 标出最重要的机会或推进信号
- 给出由证据支撑的下一步建议
- 明确覆盖最相关的 knowhow focus items

## 真实调用示例

### 示例 1：直接给自然语言会议纪要

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
客户反馈当前客服机器人命中率不稳定，夜间转人工率偏高。李总表示，希望先确认问题是不是知识库更新机制导致，再决定是否进入新一轮采购。客户提到 6 月前内部会做一次服务质量考核，如果效果没有改善，预算优先级会下降。陈经理提到接口改造资源有限，需要尽量少改现有系统。
```

### 示例 2：显式输入包

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
    "record_text": "客户反馈当前客服机器人命中率不稳定，夜间转人工率偏高……"
  },
  "crm_context": {
    "account": {"account_id": "CUST-001", "account_name": "华东零售集团"},
    "opportunity": {"opportunity_id": "OPP-9001", "opportunity_name": "智能客服升级项目"},
    "person": {"person_id": "USR-101", "person_name": "王敏"}
  },
  "constraints": {
    "language": "zh-CN",
    "output_mode": "human_and_json"
  }
}
```

## 开发辅助文件说明

以下内容只用于开发验证，不代表真实 skill 运行方式：
- `mock_runner.py`
- `examples/mock-data/`
- `examples/` 中基于 Python CLI 的片段
- `evals/evals.json` 中引用 mock data 的 case

如果引用这些文件，必须明确说明它们是 dev harness，而不是生产运行路径。
