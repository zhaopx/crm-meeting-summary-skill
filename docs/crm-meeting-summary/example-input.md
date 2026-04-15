# 输入示例

本文只展示 **真实 skill 的输入方式**。
- `tests/crm_meeting_summary/helpers/mock_runner.py` 仅用于开发验证，不代表生产运行路径
- 详见：`docs/crm-meeting-summary/case-execution-example.md`
- 顶级总结的目标不是把会议复述完整，而是压缩出交易判断、推进门槛、动作任务单和风险/缺口

## 真实 skill 最小输入示例

适用于：
- 直接在 Claude 中调用 `crm-meeting-summary`
- 用户只提供会议纪要和少量 CRM 上下文
- 会议纪要较短，适合直接内联

```text
请使用 crm-meeting-summary skill，基于以下输入生成会议总结。

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

## 真实 skill 显式输入包示例

适用于：
- 调用方已经把会议内容 / CRM 上下文做了预归一化
- 希望稳定控制输入字段
- 会议纪要可以直接内联到 `record_text`

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
    "record_text": "客户反馈当前客服机器人命中率不稳定，夜间转人工率偏高。李总明确表示，希望先确认问题是不是知识库更新机制导致，再决定是否进入新一轮采购。客户提到 6 月前内部会做一次服务质量考核，如果效果没有改善，预算优先级会下降。陈经理提到接口改造资源有限，需要尽量少改现有系统。"
  },
  "crm_context": {
    "account": {
      "account_id": "CUST-001",
      "account_name": "华东零售集团"
    },
    "opportunity": {
      "opportunity_id": "OPP-9001",
      "opportunity_name": "智能客服升级项目"
    },
    "person": {
      "person_id": "USR-101",
      "person_name": "王敏",
      "person_role": "客户成功经理"
    }
  },
  "constraints": {
    "language": "zh-CN",
    "output_mode": "human_only"
  }
}
```

## 长会议纪要文件输入示例

适用于：
- meeting record 很长，不适合直接贴进对话
- 调用方已经把纪要保存为本地文本文件
- 希望保持真实 skill 调用路径，不借助 dev harness

```text
请使用 crm-meeting-summary skill，基于以下输入生成会议总结。

meeting time: 2026-04-06T15:00:00+08:00
initiator: 王敏（USR-101）
客户: 华东零售集团（CUST-001）
opportunity: 智能客服升级项目（OPP-9001）
meeting record file: /abs/path/meeting-notes.txt
```

对应显式输入包也可以写成：

```json
{
  "meeting": {
    "meeting_time": "2026-04-06T15:00:00+08:00",
    "initiator": {"id": "USR-101", "name": "王敏"},
    "account": {"id": "CUST-001", "name": "华东零售集团"},
    "opportunity": {"id": "OPP-9001", "name": "智能客服升级项目"},
    "record_text_path": "/abs/path/meeting-notes.txt"
  },
  "crm_context": {
    "account": {
      "account_id": "CUST-001",
      "account_name": "华东零售集团"
    },
    "opportunity": {
      "opportunity_id": "OPP-9001",
      "opportunity_name": "智能客服升级项目"
    },
    "person": {
      "person_id": "USR-101",
      "person_name": "王敏"
    }
  },
  "constraints": {
    "language": "zh-CN",
    "output_mode": "human_only"
  }
}
```

归一化规则：
- `record_text` 非空时优先使用 `record_text`
- 只有 `record_text` 缺失时才读取 `record_text_path`
- 再缺失时，如果提供 `input_bundle_path`，读取目录中的 `meeting-record.txt`
- 路径不可读或 `meeting-record.txt` 为空时必须显式暴露，不得编造会议内容
- 目录模式只读取固定白名单文件：`meeting-record.txt`、`AccountObj.json`、`NewOpportunityObj.json`、`PersonnelObj.json`、`ContactObj.json`

## 目录输入包示例

适用于：
- 用户自己准备一整套测试数据
- 不想手工粘贴 CRM 对象 JSON
- 希望目录内文件名符合内部 CRM 命名规范

```text
请使用 crm-meeting-summary skill，基于以下输入生成会议总结。

input bundle path: /abs/path/case-001
meeting time: 2026-04-06T15:00:00+08:00
initiator: 王敏（USR-101）
客户: 华东零售集团（CUST-001）
opportunity: 智能客服升级项目（OPP-9001）
```

目录内容固定为：
- `meeting-record.txt`
- `AccountObj.json`
- `NewOpportunityObj.json`
- `PersonnelObj.json`
- `ContactObj.json`（可选）

对应显式输入包也可以写成：

```json
{
  "input_bundle_path": "/abs/path/case-001",
  "meeting": {
    "meeting_time": "2026-04-06T15:00:00+08:00",
    "initiator": {"id": "USR-101", "name": "王敏"},
    "account": {"id": "CUST-001", "name": "华东零售集团"},
    "opportunity": {"id": "OPP-9001", "name": "智能客服升级项目"}
  },
  "constraints": {
    "language": "zh-CN",
    "output_mode": "human_only"
  }
}
```

## 开发验证：Mock runner 示例

仅在本地做 contract regression 或 mock data 演练时，才使用：

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

这个 runner 输出的是开发期可回归结构，例如：
- `allowed_request_groups`
- `requested_request_groups`
- `crm_data_requests`
- `out_of_policy_requests`
- `mock_sources`
- `missing_information_candidates`

它不是 Claude runtime 中的真实 skill 调用路径。

## 相关文档
- `case-execution-example.md` - 完整执行链路与标准输出样例
- `tests/crm_meeting_summary/helpers/mock_runner.py` - 开发验证工具
