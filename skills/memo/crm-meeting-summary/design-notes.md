# CRM Meeting Summary 设计议题文档

本文档只做设计说明，不执行实际动作。

## 1. Memory 设计

### 1.1 目标
memory 系统本身是独立系统，不是这个 skill 的一部分。这个 skill 只负责按需读取 memory 数据，不负责定义 memory 的真实生产流程。

因此这里的设计分两层：
1. memory 系统本身的对象模型与存储建议
2. skill 如何消费 memory

### 1.2 对象范围
建议支持 4 类对象：
- person
- account
- opportunity
- contact

说明：
- person：发起者和内部员工统一归到 person
- account：客户主体
- opportunity：商机主体
- contact：联系人

### 1.3 对象关系
建议按下面的关系理解：
- account / opportunity / contact 都会有负责人
- 负责人引用的是 person 对象
- 一条销售记录可以在 account、opportunity、contact 下发起
- 销售记录会关联这三个对象中的一个或多个
- 谁发起这条销售记录，就会关联对应的发起 person

也就是说，skill 在处理会议记录时，最终要能从销售记录或会议上下文里拿到：
- 发起 person
- 所属 account
- 所属 opportunity
- 所属 contact

### 1.4 skill 对 memory 的使用边界
对于这个 skill 来说，memory 只是外部输入源之一。

skill 只需要：
- 知道可以从哪些对象读取 memory
- 知道读取优先级
- 知道读取后如何与当前会议/CRM 事实做冲突处理

skill 不需要：
- 决定 memory 系统怎么生产
- 决定 memory 系统怎么长期治理
- 决定 memory 系统的真实存储架构

所以当前阶段完全可以先 mock memory 数据。

### 1.5 skill 读取的对象优先级
建议按以下顺序读取：
1. person（发起人 / 当前负责人）
2. account
3. opportunity
4. contact

实际读取时不要求四类对象都存在；谁有就读谁。

### 1.6 时间分层
如果 memory 系统后续需要做时间分层，建议分三层：

1. 短期 memory
- 生命周期：7-30 天
- 内容：近期会议结论、待跟进事项、短期风险、最新承诺
- 用途：提高连续几次会议之间的衔接质量

2. 中期 memory
- 生命周期：1-2 个季度
- 内容：客户偏好、采购习惯、协作阻力、关键人风格、常见 objections
- 用途：增强判断稳定性

3. 长期 memory
- 生命周期：半年以上
- 内容：组织结构特点、长期合作关系特征、持续存在的敏感边界
- 用途：做背景参考

### 1.7 memory 系统建议记录内容
如果单独设计 memory 系统，每条 memory 建议至少有：
- object_type
- object_key
- memory_type
- time_scope
- content
- source
- confidence
- created_at
- updated_at
- status

其中：
- object_type：person / account / opportunity / contact
- memory_type：preference / commitment / risk / relationship / process / org-context
- source：meeting-summary / manual / crm-derived
- confidence：high / medium / low
- status：active / stale / archived

### 1.8 短期方案
短期先不做复杂分层检索系统，先做：
- 一个统一 Mongo collection
- 同一对象多条 memory 记录
- 通过 `object_type + object_key + time_scope + status` 查询
- 上层读取时再做时间和置信度筛选

### 1.9 Mongo 表建议
建议短期用一个 collection：`crm_summary_memory`

最小结构：
```json
{
  "object_type": "account",
  "object_key": "CUST-001",
  "object_name": "华东零售集团",
  "memory_type": "risk",
  "time_scope": "mid",
  "content": "客户续费前通常要求先看到量化效果改善。",
  "source": "meeting-summary",
  "confidence": "high",
  "status": "active",
  "created_at": "2026-04-07T10:00:00+08:00",
  "updated_at": "2026-04-07T10:00:00+08:00"
}
```

---

## 2. Knowhow 如何自动拉取 / 如何蒸馏

### 2.1 先给结论
我建议先把 knowhow 看成一个分层检索系统，而不是一个静态文件堆。

目标不是“把所有知识都塞给模型”，而是：
- 在当前会议场景下
- 给模型最相关的一小批 knowhow
- 同时控制上下文长度和噪音

### 2.2 knowhow 来源
建议三类来源：
- 人工维护资料
- 最佳案例沉淀
- 大模型从历史会议/案例中蒸馏出的候选规则

注意：
- 正式 knowhow 不直接来自单次大模型输出
- 大模型只负责产出候选 knowhow
- 正式入库必须经过规则化和审核

### 2.3 knowhow 分层
建议按 5 层组织：
1. common knowhow
2. scenario knowhow
3. industry knowhow
4. scenario × industry patch
5. best cases（挂在 knowhow 下面）

其中：
- 前 4 层是规则层
- best cases 是案例层

### 2.4 自动拉取流程
建议按下面顺序拉取：

1. 读取基础上下文
- meeting text
- initiator person
- account
- opportunity
- contact

2. 做第一轮识别
- primary scenario
- secondary tags
- industry
- confidence

3. 拉取规则层 knowhow
- common
- scenario
- industry
- patch

4. 根据规则层 knowhow 再决定是否补拉案例层
- 如果当前会议是复杂场景、争议场景、风险场景，补拉 best cases
- 如果当前会议是高置信、标准场景，只拉规则层即可

5. 组装成 prompt context
- 规则层放前面
- 案例层放后面
- 案例数量控制在 1-3 个，不要无限追加

### 2.5 为什么这么做
原因有 4 个：

1. 模型真正需要的是“当前场景下最相关的判断框架”，不是完整知识库。
2. 规则层和案例层混在一起会导致 prompt 噪音高。
3. best case 的价值是给模型示例和证据，不是替代规则。
4. 自动拉取必须可控，否则上下文会迅速失真。

### 2.6 检索键设计
自动拉取至少要依赖这些键：
- primary_scenario
- industry
- risk_tags
- account_stage
- opportunity_stage
- meeting_goal_keywords

其中最核心的是：
- scenario
- industry

这和当前“场景优先，行业补丁”的方向一致。

### 2.7 推荐的正流方案
你问“如何正流”，我理解为：knowhow 如何从原始素材稳定流入正式知识层。

我建议走 4 段正流：

#### Stage 1：原始素材层
输入来源：
- 高质量会议记录
- 通过 review 的总结
- 人工标注的最佳案例
- 业务规则 / 政策边界

这一层不直接给模型用来做最终判断，只作为加工原料。

#### Stage 2：候选提炼层
让模型做候选提炼，输出：
- signal
- anti-signal
- risk pattern
- success pattern
- recommended action
- boundary

这里的产物叫“候选 knowhow”，不叫正式 knowhow。

#### Stage 3：归并与审核层
对候选 knowhow 做：
- 去重
- 聚类
- 合并相似模式
- 删除单次偶发现象
- 标记适用范围
- 人工审核

这一层决定哪些内容可以进入正式 knowhow。

#### Stage 4：正式发布层
发布到：
- common
- by-scenario
- by-industry
- patches
- best-cases

正式发布后的 knowhow 才允许进入 skill 的自动拉取链路。

### 2.8 蒸馏原则
蒸馏时建议坚持 5 个原则：

1. 单次样本不能直接升格为 knowhow
2. knowhow 必须表达“模式”，不是“事件”
3. 规则和案例必须分层
4. 风险和边界优先于漂亮结论
5. 没有稳定适用范围的内容不要入正式库

### 2.9 knowhow 条目结构
建议每条正式 knowhow 至少有：
- id
- level: common / scenario / industry / patch
- applicable_scope
- title
- signal
- anti_signal
- evaluation_rule
- action_guidance
- policy_boundary
- best_case_ids
- source_refs
- confidence
- status

### 2.10 短期方案
短期不要做自动写回正式库。先做：
- 人工维护正式 knowhow 文件
- 大模型只生成候选 knowhow 草稿
- 候选进入待审核目录
- 人工确认后再进入正式 knowhow

这样做的好处是：
- 不会让错误知识直接污染正式库
- 方便先把 retrieval 逻辑跑顺
- 方便后续补审核流

---

## 3. 最佳案例和 knowhow 的关系

### 3.1 定位区别
- knowhow：规则、模式、评价框架
- 最佳案例：挂在 knowhow 下面的实例材料

### 3.2 关系定义
这里建议明确成：
- knowhow 是主结构
- 最佳案例是 knowhow 下的一批案例
- 案例不是与 knowhow 平行的体系
- 案例的作用是说明某条 knowhow 在真实业务里如何体现

也就是说，从结构上看：
- 一个 knowhow 条目下面可以挂多个 best cases
- 一个 best case 必须能回指到它归属的 knowhow 条目

### 3.3 为什么这样更合适
这样做的好处是：
1. 模型先拿到规则，再看案例，不会被案例细节带偏。
2. knowhow 与案例天然形成主从关系，便于自动拉取。
3. 后续蒸馏时，可以从案例反向更新 knowhow，但不会把两层混成一层。

### 3.4 推荐做法
每条 knowhow 建议挂：
- best_case_ids
- example_snippets
- best_case_summary

每个 best case 建议至少带：
- id
- knowhow_id
- scenario
- industry
- case_title
- why_it_is_best
- key_pattern
- reusable_snippet
- risk_handling
- outcome

### 3.5 skill 里的使用方式
在 skill 自动拉取里：
- 先拉 knowhow 规则层
- 再按 knowhow_id 补拉 1-3 个最佳案例
- 最佳案例只作为补充示例，不替代规则层

---

## 4. 自动识别场景

### 4.1 目标
给每次会议识别：
- 一个主场景
- 多个辅助标签
- 一个置信度

### 4.2 方法
建议分两层：

1. taxonomy rule layer
- 用场景定义中的 signal / anti-signal 做初筛
- 先缩小候选范围

2. LLM judgment layer
- 在候选范围内做语义判断
- 输出主场景、辅助标签、证据、置信度

### 4.3 为什么不用纯规则
纯规则会漏掉复杂表达、隐含目标和业务意图。会议标题和关键词经常不准。

### 4.4 为什么不用纯大模型
纯大模型可解释性差，后续难维护，且场景扩展时漂移大。

### 4.5 推荐输出
```json
{
  "primary_scenario": "需求澄清",
  "secondary_tags": ["industry:general-b2b", "risk:budget-priority"],
  "confidence": "high",
  "evidence": [
    "客户要求先确认问题根因，再决定是否进入采购",
    "预算优先级与效果改善绑定"
  ]
}
```

### 4.6 冲突处理
如果两个场景冲突：
- 先看会议核心决策压力落在哪
- 选最能解释下一步动作的那个作为主场景
- 次要场景转成 secondary_tags
- 证据不足时返回 `其他/不确定`

---

## 5. 自动匹配到人员，怎么处理

### 5.1 目标
把会议记录里出现的人物，尽量映射到 CRM 中真实 person 对象。

### 5.2 匹配优先级
1. 显式 person_id
2. name + company
3. name + role
4. name only

### 5.3 风险点
- 同名
- 角色变化
- 简称 / 别名
- 一条记录里提到但不在 CRM 的外部人员

### 5.4 推荐处理流程
1. 先做 deterministic match
   - id 命中直接通过
   - name + company 精确匹配优先

2. 再做 heuristic match
   - role、组织、上下文共同判断

3. 最后做 ambiguity handling
   - 多候选时不硬选
   - 输出候选列表和不确定状态

### 5.5 建议输出
```json
{
  "person_mentions": [
    {
      "raw_name": "李总",
      "matched": true,
      "person_id": "P-1008",
      "confidence": "medium",
      "match_basis": ["name", "company", "role"]
    }
  ],
  "unresolved_mentions": []
}
```

### 5.6 短期方案
短期不要做复杂 entity resolution 系统，先做：
- 有 id 用 id
- 没 id 用 `name + company` 规则匹配
- 匹配不到就保留原文，不强行落 CRM person
- 匹配冲突时输出 ambiguity，不自动写回

---

## 6. 推荐的落地顺序

第一阶段：
- 场景识别
- knowhow 手工维护
- mock 数据驱动总结
- review 闭环

第二阶段：
- memory 单 collection 落地
- 人员基础匹配
- 自动生成补拉字段建议

第三阶段：
- knowhow 候选自动蒸馏
- 最佳案例库
- 场景与人员匹配优化
