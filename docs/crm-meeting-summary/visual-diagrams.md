# crm-meeting-summary

## 1. 总架构图

![总架构图参考草图](../../whiteboard_exported_image.png)

## 2. skill 关键流程图

```plantuml
@startuml
title crm-meeting-summary skill 关键流程图
skinparam shadowing false
skinparam defaultTextAlignment center
skinparam ArrowColor #475569
skinparam activity {
  BackgroundColor #f8fafc
  BorderColor #94a3b8
  DiamondBackgroundColor #fef3c7
  DiamondBorderColor #f59e0b
  FontColor #0f172a
}

start
:输入归一化\nrecord_text > record_text_path\n> input_bundle_path/meeting-record.txt;
:场景识别\ntaxonomy.md;
if (scenario_confidence\n是否 low?) then (是)
  #FFE9E9:进入 conservative mode\n默认只加载 common；\n行业有独立证据时补充 industry;
  #FFE9E9:只允许最小消歧请求\n不加载 scenario / patch / best-cases;
else (否)
  #FFE9E9:加载 common + scenario；\n按证据补充 industry / patch / best-cases;
  #FFE9E9:按 retrieval policy + request groups\n+ data_requirements 形成最小 crm_data_requests;
endif
:语义归一\nsemantic_normalization;
:提取通用会议状态\nmeeting_state_features;
:组装 memory 上下文\n只取最小子集;
if (memory 与当前 meeting / CRM\n证据冲突?) then (是)
  :优先保留当前证据；\n暴露冲突边界，必要时降低判断强度;
else (否)
endif
:生成原始 summary\n只写已确认内容;
:按单一 template 重排结构\n只重组已有内容，不新增事实;
:调用 review 子 skill\n提交 summary / loaded knowhow\n最小证据摘录 / 缺失信息\n必要的 template / memory conflict 说明;
:按固定顺序评审\n事实准确性 -> 风险覆盖 -> 业务价值;
if (review 通过?) then (pass)
  #FFE9E9:交付最终人类总结;
  stop
else (fail)
  :按 failure_reasons\n定向修复失败维度;
  :最多重试 2 轮;
  if (2 轮后仍不稳定?) then (是)
    #FFE9E9:要求人工复核\n保留当前最佳总结;
    stop
  else (否)
    :重新生成 summary 并复审;
  endif
endif
@enduml
```

## 3. 时序图

```plantuml
@startuml
title crm-meeting-summary 主执行时序

actor User
participant "Claude Code" as Claude
participant "crm-meeting-summary\nSKILL.md" as Skill
participant "runtime contract\n+ taxonomy + knowhow + template" as Knowledge
participant "crm-meeting-summary-review" as Review
participant "最终总结" as Output

User -> Claude: 请求生成会议总结
Claude -> Skill: 调用 crm-meeting-summary
Skill -> Skill: 输入归一化\nrecord_text > record_text_path > input_bundle_path/meeting-record.txt

alt scenario_confidence = high / medium
  Skill -> Knowledge: 读取 taxonomy / runtime-contract\n加载 common + scenario\n按证据补充 industry / patch / best-cases
  Knowledge --> Skill: 返回场景判断 / retrieval policy\ndata requirements / template 命中信息
else scenario_confidence = low
  Skill -> Knowledge: 读取 taxonomy / runtime-contract\n进入 conservative mode\n只加载 common，行业有证据时补充 industry
  Knowledge --> Skill: 返回保守场景判断 / 最小 retrieval policy\n降低判断强度 / template 命中信息
end

Skill -> Skill: 语义归一
Skill -> Skill: 提取通用会议状态
Skill -> Skill: 组装最小 memory 上下文\n冲突时优先当前 meeting / CRM 证据
Skill -> Skill: 生成原始 summary\n只写已确认内容
Skill -> Skill: 按 template 重排最终目录\n只重组已有内容，不新增事实
Skill -> Review: 提交 summary / loaded knowhow\n最小证据摘录 / 缺失信息\n必要的 template / memory conflict 说明
Review -> Review: 按固定顺序评审\n事实准确性 -> 风险覆盖 -> 业务价值
Review --> Skill: 返回 pass/fail\nfailure_reasons / targeted_regeneration_instructions

alt review pass
  Skill -> Output: 交付最终人类总结
else review fail 且可修复
  loop 最多 2 次定向修复
    Skill -> Skill: 只修失败维度后重生 summary
    Skill -> Review: 重新提交修复结果
    Review -> Review: 按固定顺序复审
    Review --> Skill: 返回最新评审结论
  end
  alt 2 轮内通过
    Skill -> Output: 交付最终人类总结
  else 2 轮后仍不稳定
    Skill -> Output: 保留当前最佳总结\n标注人工复核
  end
end

Output --> Claude: 返回最终总结或人工复核结论
Claude --> User: 展示结果
@enduml
```

## 4. 说明

- 本页只做结构示意，不作为运行时契约来源
- 正式口径以 `skills/crm-meeting-summary/references/runtime-contract.md`、`skills/crm-meeting-summary/SKILL.md`、`skills/crm-meeting-summary/review/SKILL.md` 为准
- 图中使用的 `semantic_normalization`、`meeting_state_features`、review loop 等词，仅表示内部流程阶段，不代表最终用户可见输出结构
