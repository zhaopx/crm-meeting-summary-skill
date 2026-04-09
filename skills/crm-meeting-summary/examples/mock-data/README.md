# Mock 数据示例布局

在接入真实 CRM 之前，用 mock data 模拟 runtime retrieval。

## 目录结构

- `meeting-records/` - 原始 meeting input packages
- `crm/account/` - 客户 CRM 对象（底层目录名保留 `account`）
- `crm/opportunity/` - 商机 CRM 对象
- `crm/person/` - 发起人 / owner / stakeholder CRM 对象
- `memory/person/` - 人员 memory
- `memory/account/` - 客户 memory（底层目录名保留 `account`）
- `memory/opportunity/` - 商机 memory
- `memory/contact/` - 可选目录；联系人 memory 只有在明确需要时才读取，默认可以不存在

## 关键规则
- 有 ID 时优先使用基于 ID 的文件
- 没有 ID 时回退到基于 name 的文件
- 同一 object 不要在没有记录优先级的情况下制造重复 truth sources

## 扩展建议
- 当需要 name-based fallback 时，使用规范化文件名，例如：
  - `华东零售集团.json`
  - `王敏.json`
- 无论 key style 如何变化，object content shape 都保持一致。
- 如果要模拟新体系，优先用 card 结构表达单条 memory，并显式带上 `horizon`、`status`、`topic_tags` 与 `evidence_ref`。
