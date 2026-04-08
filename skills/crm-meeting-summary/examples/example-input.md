# 输入示例

使用 `mock-data/meeting-records/meeting-001.json` 作为主示例输入。

## 场景预期
- primary_scenario: `需求澄清`
- industry: `general-b2b`
- likely risk level: `medium` 或 `high`，取决于 evidence weighting

## 为什么这个示例重要
这个示例用于验证 skill 是否能：
- 不把友好表述误判为采购承诺
- 识别 budget-priority risk
- 只请求最小必要 CRM fields
- 把 memory 用作背景，而不是主证据

## 相关文档
- `example-output.md` - 期望的同步输出结构
- `case-execution-example.md` - 场景识别、retrieval、memory、semantic、output 与 review 的完整演练
