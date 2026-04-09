# Memory Topic Taxonomy

当前版本只定义直接服务 `crm-meeting-summary` 的 5 类 topic。

## 1. relationship_continuity

用于记录客户关系或商机关系的连续变化。

适合内容：
- 信任变化趋势
- 关系温度变化
- 合作阶段的长期演进

常见 scope：
- `account`
- `opportunity`

## 2. stakeholder_preference

用于记录关键人的稳定沟通偏好和信息消费习惯。

适合内容：
- 偏好先摘要后细节
- 偏好书面材料还是口头同步
- 是否强调 ROI、风险、时间线、资源投入

常见 scope：
- `contact`
- `person`
- `account`

## 3. commitment_history

用于记录历史承诺及其兑现情况。

适合内容：
- 哪些承诺被反复提及
- 哪些承诺延期或未兑现
- 哪些 follow-up 总被推迟

常见 scope：
- `opportunity`
- `account`
- `person`

## 4. risk_pattern

用于记录重复出现的风险、投诉、升级或敏感点。

适合内容：
- 服务稳定性敏感点
- 历史升级背景
- 重复出现的阻塞与不满

常见 scope：
- `account`
- `opportunity`

## 5. approval_pattern

用于记录决策链、审批路径和推进机制。

适合内容：
- 谁推动、谁卡点、谁拍板
- 采购 / 法务 / IT 的典型顺序
- 哪类材料能推进审批

常见 scope：
- `opportunity`
- `account`
- `contact`

## topic 使用约束

- 一条 card 可以有多个 `topic_tags`，但第一版建议 1-2 个即可
- 如果 topic 太多，优先保留最直接影响 summary judgment 的那个
- topic 不是 scenario，不能替代场景分类
- topic 用于解释历史模式，不用于放当前 meeting 的主结论
