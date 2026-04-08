# Mock 数据示例布局

在接入真实 CRM 之前，用 mock data 模拟 runtime retrieval。

## 目录结构

- `meeting-records/` - 原始 meeting input packages
- `crm/account/` - account CRM objects
- `crm/opportunity/` - opportunity CRM objects
- `crm/person/` - initiator/owner/stakeholder CRM objects
- `memory/person/` - person memory
- `memory/account/` - account memory
- `memory/opportunity/` - opportunity memory

## 关键规则
- 有 ID 时优先使用基于 ID 的文件
- 没有 ID 时回退到基于 name 的文件
- 同一 object 不要在没有记录优先级的情况下制造重复 truth sources

## 扩展建议
当需要 name-based fallback 时，使用规范化文件名，例如：
- `华东零售集团.json`
- `王敏.json`

无论 key style 如何变化，object content shape 都保持一致。
