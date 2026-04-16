---
name: crm-meeting-summary
description: 当用户要求总结 CRM 相关会议纪要、基于客户/商机/人员等结构化上下文生成会议回顾，或使用行业/场景 knowhow、memory 与 review 校验来产出高质量人类可读总结时，应使用此 skill。
---
# CRM 会议总结

把这份 skill 当成**真实运行时入口**，不是说明文档，也不是 Python 模拟器包装。

你的任务是在 Claude runtime 内直接完成：

1. 读取输入包
2. 识别场景并决定最小 retrieval
3. 生成同源的人类可读总结
4. 调用 `review/SKILL.md` 做评审
5. 在最多 2 次定向修复内完成收敛
6. 返回最终可交付的人类总结

禁止把 `tests/crm_meeting_summary/helpers/mock_runner.py` 当成真实运行路径。
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
    "output_mode": "human_only"
  }
}
```

### 最小必需输入

至少要有：

- meeting record text，或可读取的 `meeting.record_text_path`
- initiator，类型为 `person`
- 客户或商机关联

meeting time 如有则应保留；没有就显式视为未知，不编造。

如果用户只给自然语言纪要，而没有显式 JSON：

- 先在内部整理出 `meeting` / `crm_context` / `constraints`
- 如果用户给的是文件路径，先读取文件内容并归一到内部 `record_text`
- 如果用户给的是目录路径，且表示目录内已按固定命名准备好测试输入，则按 `input_bundle_path` 读取白名单文件装配输入包
- 再继续执行后续步骤

如果关键输入缺失：

- 不要编造
- 在最终总结的“风险与待确认问题”中明确写出缺失项
- 缺失到无法支撑主要判断时，直接按人工复核处理，不伪装成确定性总结

## 工作原则

1. 严格区分三类内容：
   - 来自会议纪要或 CRM data 的显式事实
   - 基于证据的判断
   - 仍需确认的未决事项
2. 当前会议纪要和当前 CRM 上下文优先于 memory。
3. memory 只用于补强背景理解，例如历史承诺、关键人偏好、长期张力或关系连续性。
4. knowhow 只是评估框架，不是事实来源。
5. 禁止编造 CRM data、政策、行动项或客户意图。
6. 最终交付物只有人类可读总结。
7. 真正交付给用户之前，必须经过 review skill。

## 运行时工作流

### 第 1 步：归一化基础上下文

先整理最小基础上下文，至少明确：

- meeting title，如果有
- meeting time
- initiator，表示为 `person` object
- 客户
- linked opportunity
- participants，如果有
- raw meeting record，仅作为输入来源，不直接原样贴进最终输出

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
- 读取失败、文件不存在或内容为空时，不得编造，必须把失败暴露到最终总结中

规则：

- 有 object ID 时优先使用 ID
- 没有 ID 时回退到名称
- 未知值写“未提供”或“待确认”，不要补写

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

- 除非某个场景明显占优，否则优先按“其他 / 不确定”处理
- 默认只加载 `references/knowhow/common/`
- 只有行业有独立证据时才加载 industry knowhow
- 不加载 scenario knowhow、patches、best-cases
- 只请求能消除歧义的最小 CRM 字段
- 降低后续判断强度
- 在最终总结中显式写出“不确定”的边界，而不是假装已识别清楚

场景判断补充要求：

- 如果当前会议证据不足以支撑明确场景结论，就按 low confidence 处理，不把弱信号硬解释成具体场景。
- 如果会议同时出现多类主题或多方诉求，优先保留保守结论，不在主 skill 层写死哪一类主题应优先压过另一类主题。
- 如果当前会议事实与 memory 冲突，必须保留当前会议结论，并在最终总结中简要说明冲突点；必要时降低判断强度。

### 第 3 步：加载参考知识

按以下顺序加载 knowhow：

1. `references/knowhow/common/`
2. `references/knowhow/by-scenario/<scenario_slug>.md`
3. 行业可识别时加载 `references/knowhow/by-industry/<industry>.md`
4. 场景和行业都可识别且补丁存在时，加载 `references/knowhow/patches/<scenario_slug>__<industry>.md`
5. best-cases 只在确有帮助时才加载

使用 knowhow 来决定：

- 需要重点关注的信号
- 总结必须覆盖的点
- 场景特定成功标准
- 场景特定风险或政策边界
- 可能的下一步预期

`template` 与 knowhow 平行：

- `knowhow` 负责判断框架
- `template` 负责最终目录模板
- `template` 不提供新事实，只在 summary 已生成后做重排

### 第 4 步：决定需要哪些额外 CRM 字段

不要默认拉取全部数据。只决定为了生成更好总结所需的最小缺失 CRM data。

必须同时遵守：

- `references/runtime-contract.md`
- `references/taxonomy.md`

决策顺序：

1. 先根据 `references/taxonomy.md` 中当前场景的 retrieval policy 计算允许请求范围
2. 再读取已加载 scenario / patch knowhow 中声明的 `data_requirements`
3. 只有当 meeting evidence 与当前 CRM 缺失共同支持时，才把这些字段加入候选请求
4. 对同一 request group 去重合并，形成最终最小请求清单
5. 如果 knowhow 声明超出允许范围，不执行该 retrieval，并记入 `out_of_policy_requests`，不要因为 knowhow 扩大 retrieval

硬性要求：

- `data_requirements` 只能细化允许范围内的字段
- 不能绕过 policy 扩大 retrieval scope
- 在 conservative mode 下，不执行 scenario / patch knowhow 的扩展请求

### 第 5 步：语义归一

先做对象、关系、字段口径统一。至少要做：

- 把 initiator、owner、stakeholder 统一映射到 `person`
- 把客户统一映射到 `account`
- 把“项目 / 商机 / 机会”等异构叫法统一映射到 `opportunity`
- 对参与人里被提及但不等于 initiator 的外部联系人，按证据映射为 `contact`
- mixed key lookup：优先 `*_id`，回退 `*_name`
- 显式梳理对象关系，例如 meeting 与 person / account / opportunity 的连接关系

约束：

- 这一步只解决对象口径，不输出状态判断
- 不把 `relationship_state / trust_state / decision_pressure / momentum_state` 塞进语义归一层
- 对象口径统一规则以 `references/runtime-contract.md` 为准

### 第 6 步：提取通用会议状态特征

在语义归一之后，再抽取当前会议的通用状态特征。这一步的目标不是做某个行业、某个角色或某条销售漏斗的专用判断，而是沉淀一组跨场景都成立的会议状态底座，供后续 summary、template 和 review 使用。

至少应覆盖以下几类状态：

- 当前互动 / 关系状态
- 当前推进 / 执行状态
- 当前信任 / 协作状态
- 当前阻塞 / 不确定性状态

如果现有 runtime contract 仍使用 `relationship_state`、`decision_pressure`、`trust_state`、`momentum_state` 这组字段名，则继续兼容这些字段名；但应把它们理解为当前通用会议状态的落点，而不是仅限于销售推进语境。

约束：

- 只能由当前会议纪要与当前 CRM context 支撑
- history memory 只能作为背景，不得覆盖当前会议特征
- 这一步只抽取通用会议状态，不负责行业化解释、场景化策略或模板结构
- 这一步的结果是后续判断的内部底座，不要和对象归一混写

### 第 7 步：组装记忆上下文

从可用的 CRM 关联 scope 加载最小 memory 子集：

- `person`
- `account`
- `opportunity`
- `contact`

规则：

- 只有 contact 在会议或 CRM 上下文中被明确提及时，才加载 contact memory
- 有 object ID 时优先用 object ID
- 否则用名称
- 命中多个候选时，标记歧义，不要猜
- memory 与当前 meeting/CRM 事实冲突时，优先信任当前证据
- 只读取实际判断所需的最小子集，不做 broad sweep
- 如果冲突影响当前会议的核心判断、关键阻塞、协作状态或主要不确定边界，必须在最终总结中暴露不确定边界

查找与优先级规则见 `references/runtime-contract.md` 的 Memory 使用契约章节。

### 第 8 步：先生成原始总结

先基于同一份事实底座生成原始 summary，要求是：

- 清楚区分事实、判断、待确认问题
- 缺项就写缺项，不补写
- 如果证据不足，不要把猜测写成结论

原始 summary 只负责先把已确认内容写出来，不在主 skill 中强绑固定章节、固定标题或具体栏目写法。
这些约束应由所选 template 及其注释负责定义。

### 第 9 步：按 template 模板重排

在原始 summary 已生成后，template 只选一份最终模板，不做多模板叠加。

选择规则：

1. 当 `scenario_mode = uncertain` 时，直接使用 `skills/crm-meeting-summary/references/templates/common/default.md`
2. 否则按以下顺序找第一份存在的模板：
   - `skills/crm-meeting-summary/references/templates/profiles/<scenario_slug>--<industry>.md`
   - `skills/crm-meeting-summary/references/templates/profiles/<scenario_slug>.md`
   - `skills/crm-meeting-summary/references/templates/common/default.md`

规则：

- `template` 与 knowhow 平行，但不复用 knowhow 的多层 merge 模型
- `common/` 只做兜底模板
- `profiles/` 中每个文件都代表一份最终模板
- 模板文件可以定义固定章节、标题、占位写法，以及各栏目具体写法要求
- 主 skill 只负责按所选模板重排；模板未要求的固定章节，不得在主 skill 层强制补齐
- 有对应内容就填入，没有对应内容就留空、标记 missing 或省略，不得编造
- 模板条目只能消费已有 summary 内容，不能引入新事实

### 第 10 步：调用评审流程

生成 draft 后，必须调用 `review/SKILL.md`。

传给 review 的包只包含：

- 生成人类可读总结
- 已加载 knowhow 标识
- 用于验证 claim 的最小支持证据摘录
- 缺失信息清单
- 如有必要，模板选择结果与 memory conflict 简述

不要重新发送完整原始上下文，除非争议检查项确实需要。

#### Review loop 规则

- 初稿失败后，只根据 `failure_reasons` 和 `targeted_regeneration_instructions` 定向修复
- 最多做 2 次定向修复
- 如果第 2 次后仍失败，返回当前最佳人类总结，并明确标注需要人工复核
- 不要无限重试

禁止：

- 为了风格整份重写
- 因为 review 失败而扩大无关 retrieval scope
- 引入 evidence 中不存在的新事实

### 第 11 步：组装最终输出

从这一步开始，不再补充过程说明、分析解释、调试备注或任何模板外结构。
你唯一要交付的是最终给用户看的 `final_summary_markdown`。

要求：

- `final_summary_markdown` 必须已经完成 template 重排与 review 定向修复
- `final_summary_markdown` 的目录结构、标题命名、栏目顺序、缺项占位，全部以所选 template 及其注释为准
- 主 skill 不单独规定固定的二级标题集合
- review_result 与 audit_payload 只允许作为内部调试/解析对象存在，不得拼进最终用户可见正文
- 即使 review 失败、需要人工复核，也只能在 template 已定义的栏目内表达“不确定 / 待确认 / 需人工复核”，不得额外新开标题

最终响应必须只输出一份人类可读总结正文，不允许追加任何 fenced json block 或解释语。

禁止：

- 输出 `review_result` 的 fenced json block
- 输出 `audit_payload` 的 fenced json block
- 输出 `### 事实`、`### 判断`、`## review 结果`、`## audit_payload`、`### 人工复核提示` 等模板外结构
- 在正文中写入 `semantic_normalization`、`meeting_state_features`、`retrieval_trace`、`template_trace`、`review_trace`、`audit_payload`、`regeneration` 等内部字段或过程说明
- 用“下面是机器结果”“machine output”“供 runner / review / eval 消费”“不属于正文”等过渡语或标签污染正文

在最终输出前，必须逐项自检，任一项不满足都不得结束响应：
- [ ] 正文是否符合所选 template 的目录、标题与栏目命名
- [ ] 是否只输出一份最终正文
- [ ] 是否没有任何模板外标题或结构
- [ ] 是否没有把 review / audit / 内部过程字段写入正文
- [ ] 是否没有编造缺失信息

## 输出契约

必须遵守：
- `references/runtime-contract.md`
- `review/SKILL.md`

真实运行时，最终响应只有一段：最终交付给用户的人类可读总结正文。

正文必须：
- 清楚给出主要业务结论
- 区分事实与推断
- 标出最重要的风险信号
- 标出最重要的机会或推进信号
- 给出由证据支撑的下一步建议
- 明确覆盖最相关的 knowhow focus items
- 如果应用了 template，最终展示必须按模板目录组织
- 任何缺失项都不得编造成确定性陈述
- 标题与目录要求以所选 template 及其注释为准

正文禁止出现：
- semantic normalization / 语义归一 / object mapping 过程说明
- meeting_state_features / retrieval_trace / template_trace / review_trace 等内部字段名
- review loop、定向修复、regeneration 次数、审查过程解释
- “下面是 review JSON / audit JSON / machine output” 之类过渡文本
- 任何 review JSON 或 audit_payload 的字段散写进正文段落

### 正确 / 错误示例

正确示例（仅示意结构，不代表真实内容）：

```text
## 会议快照
...
## 核心总结与判断
...
## Knowhow 关注点
...
## 建议的下一步动作
...
## 风险与待确认问题
...
```

错误示例：
- 在正文后追加 `review_result` json block
- 在正文后追加 `audit_payload` json block
- 在正文后写“下面是 review 结果”
- 把 `## Knowhow 关注点` 改写成 `参考知识关注项`
- 把 `## 建议的下一步动作` 改写成 `建议下一步动作`
- 额外输出 `### 人工复核提示`

### 稳定性要求

- 不得把 review / audit 结果输出到最终用户正文
- 不得把 review / audit 结果混入正文代替模板栏目
- 如果 review 无法正常完成，也要回到 template 定义的栏目内表达不确定边界，而不是增加模板外结构


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
    "output_mode": "human_only"
  }
}
```

## 开发辅助文件说明

以下内容只用于开发验证，不代表真实 skill 运行方式：

- `tests/crm_meeting_summary/helpers/mock_runner.py`
- `tests/crm_meeting_summary/fixtures/mock-runtime/`
- `docs/crm-meeting-summary/` 中的示例文档
- `tests/crm_meeting_summary/evals/evals.json` 中引用 mock data 的 case

如果引用这些文件，必须明确说明它们是 dev harness，而不是生产运行路径。
