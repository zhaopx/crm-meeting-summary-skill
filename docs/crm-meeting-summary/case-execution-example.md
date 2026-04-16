# 案例执行示例

本文展示 `crm-meeting-summary` 作为**真实 Claude skill**的一次完整执行链路。
`tests/crm_meeting_summary/fixtures/mock-runtime/` 和 `tests/crm_meeting_summary/helpers/mock_runner.py` 仍可用于开发验证，但不是生产运行路径。

## 案例
- 开发验证输入：`tests/crm_meeting_summary/fixtures/mock-runtime/meeting-records/meeting-001.json`
- 开发验证客户 CRM：`tests/crm_meeting_summary/fixtures/mock-runtime/crm/account/CUST-001.json`
- 开发验证商机 CRM：`tests/crm_meeting_summary/fixtures/mock-runtime/crm/opportunity/OPP-9001.json`
- 开发验证人员 CRM：`tests/crm_meeting_summary/fixtures/mock-runtime/crm/person/USR-101.json`

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

说明：
- `general.md` 是当前 `common` 层实际文件名
- `best-cases` 仅在确有帮助时加载，用于增强总结质量，不参与 runtime 基础依赖判断

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

模板命中规则：
- 当 `scenario_mode=uncertain` 时，直接回退到 `skills/crm-meeting-summary/references/templates/common/default.md`
- 否则按顺序命中：
  - `skills/crm-meeting-summary/references/templates/profiles/<scenario_slug>--<industry>.md`
  - `skills/crm-meeting-summary/references/templates/profiles/<scenario_slug>.md`
  - `skills/crm-meeting-summary/references/templates/common/default.md`
- 模板只负责重排已有 summary 内容，不新增事实


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

## 第 7 步：生成人类可读总结

skill 基于同一份事实底座先生成原始 summary，再按 template 目录重排。

人类可读总结示例：

```text
## 会议快照
- 场景：需求澄清
- 模式：normal
- 目标：确认问题根因并判断是否进入试点

## 核心总结与判断
- 已确认事实：客户当前最关注的是效果不稳定和夜间转人工率偏高。
- 当前判断：客户愿意继续推进，但前提是先验证根因并看到短期效果改善。
- 当前阶段：qualification
- 决策压力：budget priority depends on short-term proof
- 风险等级：medium

## Knowhow 关注点
- 区分真实推进与礼貌性回应
- 缺失关键信息时只请求最小必要 CRM 字段
- 预算优先级与短期效果证明直接相关
- 实施复杂度会直接影响商业推进动能

## 建议的下一步动作
- 一周内提交问题诊断与优化路径建议
- 补齐试点评估负责人与预算审批链条

## 风险与待确认问题
- 待补：implementation_status
- 待补：last_commitments
- 拍板人确认：[missing]
```

## 第 8 步：调用 review skill

主 skill 生成 draft 后，调用 `crm-meeting-summary-review`。

这条 baseline case 的 review 结果会作为内部校验对象存在，用于决定是否继续定向修复；最终用户可见结果仍然只交付人类可读总结，不直接拼接 review JSON。

## 第 9 步：执行面捕获

为了确认每个 case 的最终人类总结输出，仓库内保留了一个最薄执行面：
- `tests/crm_meeting_summary/helpers/real_runner.py`：调用真实 skill，捕获完整最终返回值
- `tests/crm_meeting_summary/evals/run_real_evals.py`：批量执行关键 eval case

执行面可以捕获调试对象，例如：
- `raw_response`：CLI 返回的完整原始回包
- `final_text`：经筛选后的最终主 skill 文本
- `review_result` / `audit_payload`：仅在测试与调试链路中作为内部校验对象使用，不属于最终用户正文

这些对象属于验证链路，不代表最终用户可见交付格式。

## 第 10 步：失败样例如何停止自动化

当输入像 `meeting-hard-fail.json` 一样只剩“客户不满意”这种空壳信息时，真实 skill 也应遵循同一原则：
- 先产出当前最佳 draft
- 交给 review
- 最多做 2 次定向修复
- 仍失败则保留当前最佳总结，并标记需要人工复核

示例：

```json
{
  "pass": false,
  "review_status": "fail",
  "failure_reasons": [
    "会议原始证据过弱，无法支持可靠主结论。",
    "关键上下文缺失过多，当前总结仍不可安全交付。"
  ],
  "targeted_regeneration_instructions": [
    "明确缺失的客户背景、会议目标和可验证事实。",
    "如果无法补齐关键证据，保持人工复核结论，不要硬写推进判断。"
  ]
}
```

这表示当前不是“再润色一下”能解决的问题，必须补上下文。

## 开发验证路径

如果你只是想在本地验证 mock data 与契约是否一致，仍可以使用：

```bash
python3 tests/crm_meeting_summary/helpers/mock_runner.py \
  --meeting-file tests/crm_meeting_summary/fixtures/mock-runtime/meeting-records/meeting-001.json \
  --scenario-slug needs-clarification \
  --scenario-confidence high \
  --industry general-b2b \
  --account-file tests/crm_meeting_summary/fixtures/mock-runtime/crm/account/CUST-001.json \
  --opportunity-file tests/crm_meeting_summary/fixtures/mock-runtime/crm/opportunity/OPP-9001.json \
  --person-file tests/crm_meeting_summary/fixtures/mock-runtime/crm/person/USR-101.json
```

但这只是 dev harness，不是生产 skill 调用方式。
