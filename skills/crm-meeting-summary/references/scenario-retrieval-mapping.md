# Scenario Retrieval Mapping

版本: `v1`

这份 mapping 让 scenario-driven retrieval 可审计。
它不会取消模型判断，只是限制模型默认允许拉取什么。

## Retrieval policy

1. 先识别 `primary_scenario` 与 `scenario_confidence`。
2. 在加载场景特定 retrieval 前，先应用 low-confidence fallback。
3. 只加载表中允许的最小 knowhow 和 CRM fields。
4. 如果模型请求表外字段，必须在 trace 中解释例外原因。

## Mapping table

| Scenario | Must-load knowhow | Optional knowhow | Default CRM request groups | Prohibited default pulls |
|---|---|---|---|---|
| 首次接触 / 破冰 | common, scenario | industry | stakeholder_gap, account_profile_gap | full interaction history, contract/procurement details |
| 需求澄清 | common, scenario | industry, patch | account_profile_gap, stakeholder_gap, risk_validation_gap | pricing/package details unless explicitly discussed |
| 方案介绍 / 演示 | common, scenario | industry, patch | stakeholder_gap, history_gap | full delivery/compliance status unless implementation risk appears |
| 商务推进 / 谈判 | common, scenario | industry, patch | opportunity_progress_gap, stakeholder_gap, risk_validation_gap | full support-ticket history unless trust risk appears |
| 试点 / PoC 推进 | common, scenario | industry, patch | opportunity_progress_gap, stakeholder_gap, risk_validation_gap | full procurement details unless evaluation already enters buying process |
| 项目交付 / 实施沟通 | common, scenario | industry | history_gap, risk_validation_gap, stakeholder_gap | quote / amount / close-date unless commercial motion reappears |
| 续约 / 增购 | common, scenario | industry, patch | account_profile_gap, opportunity_progress_gap, history_gap, risk_validation_gap | deep implementation data unless delivery risk affects renewal |
| 风险 / 投诉 / 升级处理 | common, scenario | industry | history_gap, risk_validation_gap, stakeholder_gap | broad commercial pulls unless churn/commercial impact is explicit |
| 内部协同 / 复盘 | common, scenario | industry | stakeholder_gap, history_gap, opportunity_progress_gap | full memory sweep across unrelated objects |
| 其他 / 不确定 | common only | industry only if independently evidenced | stakeholder_gap or one ambiguity-resolution request only | scenario patch, broad CRM pull, broad memory pull |

## Low-confidence fallback rules

如果 `scenario_confidence = low`：
- 只加载 `common` knowhow
- 只有行业有独立证据时才加载 `industry` knowhow
- 不加载 scenario patches
- CRM requests 限制为一个消歧 request bundle
- memory 限制为一个 object scope，除非当前事实要求更多
- 输出 `scenario_mode: uncertain`

## Trace requirements

每次运行都必须输出：

```json
{
  "retrieval_trace": {
    "mapping_version": "v1",
    "scenario_mode": "normal | uncertain",
    "allowed_request_groups": ["stakeholder_gap"],
    "requested_request_groups": ["stakeholder_gap"],
    "out_of_policy_requests": []
  }
}
```

## Exception policy

如果 skill 请求了表外 retrieval，trace 必须包含：
- requested group
- 为什么当前 scenario mapping 不够
- 迫使例外发生的精确 evidence

禁止 silent exceptions。
