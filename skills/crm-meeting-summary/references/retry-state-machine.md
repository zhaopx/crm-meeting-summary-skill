# 再生成状态机

本文定义 `crm-meeting-summary` skill 的再生成循环。

## 设计目标

当 review 只在某个窄维度失败时，skill 必须保住强 summary 的主体。
retry 的目标是修复定向缺陷，不是让模型从头重写全部内容。

## 状态图

```text
input_ready
  |
  v
scenario_gate
  | high / medium confidence
  |-------------------------------> draft_generated(revision=0)
  |
  | low confidence
  v
conservative_path
  |
  v
draft_generated(revision=0, scenario_mode=uncertain)
  |
  v
review_evaluated
  | pass
  |-------------------------------> passed
  |
  | fail && revision=0
  v
review_failed_retry_1
  |
  v
draft_generated(revision=1)
  |
  v
review_evaluated
  | pass
  |-------------------------------> passed
  |
  | fail && revision=1
  v
review_failed_retry_2
  |
  v
draft_generated(revision=2)
  |
  v
review_evaluated
  | pass
  |-------------------------------> passed
  |
  | fail && revision=2
  v
manual_review_required
```

## 状态定义

### 1. `input_ready`

**目的**
- meeting package 已可用
- 基础 CRM context 已可用，或部分缺失
- 尚未生成任何 summary

**必需输入**
- raw meeting record
- meeting time，如有
- 已关联的 `person` / `account` / `opportunity` / `contact` objects，如可用

**退出条件**
- 基础归一化后进入 `scenario_gate`

### 2. `scenario_gate`

**目的**
- 将会议归类为一个 primary scenario
- 赋值 `scenario_confidence`
- 判断是否可以安全使用场景特定 retrieval

**规则**
- `high` / `medium`: 进入正常 retrieval 流程
- `low`: 不能假装高置信分类已经成立

**低置信回退**
- 除非某个 scenario 在弱证据下仍明显占优，否则将 `primary_scenario` 设为 `其他/不确定`
- 默认只加载 `common` knowhow
- 只允许最小的消歧 CRM request set
- 标记 `scenario_mode: uncertain`
- 降低下游判断置信度

**退出条件**
- 进入 `draft_generated(revision=0)`

### 3. `draft_generated`

**目的**
- 产出一份同步 summary package

**必需输出**
- human-readable summary
- machine-readable structure
- trace bundle

**硬性约束**
1. human-readable 与 machine-readable outputs 必须来自同一事实底座。
2. machine structure 是以下字段的 source of truth：
   - `meeting_goal`
   - `current_stage_judgment`
   - `next_actions`
   - `risk_level`
   - `missing_information`
3. human-readable prose 可以扩展措辞，但不能与 machine fields 矛盾。
4. 如果 `scenario_mode=uncertain`，draft 必须降低判断强度，并显式写出歧义。

**Trace bundle minimum**
- scenario evidence
- loaded knowhow IDs 或 paths
- CRM request reasons
- memory lookup results
- memory conflicts
- 传递给 review 的 evidence excerpts

**退出条件**
- 进入 `review_evaluated`

### 4. `review_evaluated`

**目的**
- 使用 review skill 对 draft 进行评估

**Review 输入包**
使用精简 review package，不要重新发送整份原始上下文。

只包含：
- generated human summary
- generated machine structure
- trace bundle
- 用于验证争议 claim 的最小支持证据摘录
- loaded knowhow identifiers

不要包含：
- 除非争议点需要，否则不要放完整 knowhow 正文
- 当窄摘录已足以证明时，不要放完整 CRM dumps
- 当只涉及一个 memory item 时，不要放完整 memory payloads

**Review 结果结构**
- `pass: true|false`
- `failure_reasons`
- `targeted_regeneration_instructions`
- `check_results`

**退出条件**
- `pass=true` -> `passed`
- `pass=false && revision=0` -> `review_failed_retry_1`
- `pass=false && revision=1` -> `review_failed_retry_2`
- `pass=false && revision=2` -> `manual_review_required`

### 5. `review_failed_retry_1`

**目的**
- 执行第一次定向修复

**输入补充**
- prior draft
- review failure reasons
- targeted regeneration instructions

**规则**
- 只改失败维度
- 保留通过维度
- 除非 failure reason 明确指出原事实无支撑，否则保留原 facts
- 保持相同 trace categories，只更新发生变化的部分

**退出条件**
- 进入 `draft_generated(revision=1)`

### 6. `review_failed_retry_2`

与 retry 1 相同，但更严格。

**Extra rule**
- 不允许大范围风格性重写
- 如果第二次修复需要改 scenario、knowhow set 或 CRM request scope，必须在 trace 中明确记录

**退出条件**
- 进入 `draft_generated(revision=2)`

### 7. `passed`

**目的**
- 最终交付物可安全返回

**必需输出**
- final human-readable summary
- final machine-readable structure
- `status: passed`
- final trace bundle

### 8. `manual_review_required`

**目的**
- 两次修复失败后停止自动化

**必需输出**
- 当前最佳 human-readable summary
- 当前最佳 machine-readable structure
- `status: manual_review_required`
- 上一次 review 的累计 failure reasons
- 上一次 targeted regeneration instructions
- 带 retry history 的 trace bundle

## 重试历史契约

发生任何 retry 时，在 machine output 中加入 retry history block。

```json
{
  "retry_state": {
    "revision": 2,
    "status": "manual_review_required",
    "history": [
      {
        "revision": 0,
        "review_status": "fail",
        "failed_checks": ["knowhow_coverage"]
      },
      {
        "revision": 1,
        "review_status": "fail",
        "failed_checks": ["machine_output_completeness"]
      }
    ]
  }
}
```

## 非目标

retry 不允许：
- 引入 evidence 中不存在的新事实
- 除非 review failure 已证明原范围不足，否则扩大 CRM retrieval scope
- 在 low-confidence 情况下静默地把 `其他/不确定` 改成高置信 scenario
- 仅为了风格而重写整份 summary
