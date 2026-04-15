# crm-meeting-summary 

## 1. 总架构图

```plantuml
@startuml
title crm-meeting-summary 总架构图
skinparam shadowing false
skinparam packageStyle rectangle
skinparam defaultTextAlignment center
skinparam ArrowColor #94a3b8
skinparam ArrowThickness 0.8
skinparam package {
  BorderColor #cbd5e1
  FontStyle bold
  BackgroundColor #ffffff
}
skinparam rectangle {
  RoundCorner 14
  BorderColor #94a3b8
  FontColor #0f172a
}
top to bottom direction

package "互动 agent" {

  package "主 skill" {
    package "总结&待办" {
      rectangle "跟进" as SummaryFollowup #FDE68A
      rectangle "风险" as SummaryRisk #FDE68A
      rectangle "总结" as SummaryGenerate #FDE68A
    }
    package "发言人洞察" {
      rectangle "唤醒" as SpeakerWakeup #FDE68A
      rectangle "查询" as SpeakerQuery #FDE68A
      rectangle "识别" as SpeakerIdentify #FDE68A
    }
    package "问题&需求" {
      rectangle "查询" as NeedPrimaryAsk #FDE68A
      rectangle "转待办" as NeedExtract #FDE68A
      rectangle "生成" as NeedClassify #FDE68A
    }
  }

  package "公用 子skill" {
    rectangle "场景识别" as SharedScenario #DCFCE7
    rectangle "人名匹配" as SharedPerson #DCFCE7
    rectangle "..." as SharedMore #DCFCE7
  }

  package "Tool" {
    rectangle "memory 操作" as ToolMemory #FCE7F3
    rectangle "CRM 操作" as ToolCRM #FCE7F3
  }
}

package "Memory 底座" {
  package "memory" {
    rectangle "对象 memory" as ObjectMemory #EDE9FE
    rectangle "用户 memory" as UserMemory #EDE9FE
    rectangle "agent memory" as AgentMemory #EDE9FE
  }

  package "自更新" {
    rectangle "memory 类型
→ 短记忆(平台)
→ 长记忆(业务)" as OutputActions #FEF3C7
    rectangle "更新机制：定时触发/实时触发" as OutputRefresh #FEF3C7
  }

  package "数据源" {
    rectangle "特征体系" as OutputProducts #FEF3C7
    rectangle "用户行为埋点" as OutputFields #FEF3C7
  }
}

ToolCRM -[hidden]right- SharedScenario

SharedMore ..> SummaryGenerate
SharedPerson ..> SpeakerIdentify
SharedScenario ..> NeedClassify

SummaryGenerate --> ToolMemory
SummaryGenerate --> ToolCRM
SpeakerIdentify --> ToolCRM
NeedClassify --> ToolCRM

ToolCRM --> ObjectMemory
ToolMemory --> ObjectMemory
ToolMemory --> UserMemory
ToolMemory --> AgentMemory

ToolMemory ..> OutputActions
ObjectMemory ..> OutputActions
UserMemory ..> OutputActions
AgentMemory ..> OutputActions
ObjectMemory --> OutputFields
UserMemory --> OutputFields
AgentMemory --> OutputFields
OutputFields --> OutputProducts

@enduml
```

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
:输入归一化\nmeeting / crm_context / constraints;
:场景识别\ntaxonomy.md;
if (scenario_confidence\n是否低?) then (是)
  #FFE9E9:进入 conservative mode\n只加载 common knowhow;
else (否)
  #FFE9E9:加载 common + scenario\n按证据补充 industry / patch / best-cases;
endif
#FFE9E9:形成最小 crm_data_requests;
:语义归一\nsemantic_normalization;
:提取当前会议特征\nmeeting_state_features;
#FFE9E9:组装 memory 上下文;
if (memory 与当前证据\n冲突?) then (是)
  :暴露冲突边界\n必要时降低判断强度;
else (否)
endif
#FFE9E9:生成原始总结;
#FFE9E9:按 template 重排结构;
#FFE9E9:调用 review 子 skill;
if (review 通过?) then (pass)
  #FFE9E9:交付最终总结;
  stop
else (fail)
  :定向修复;
  :最多重试 2 轮;
  if (仍不稳定?) then (是)
    #FFE9E9:要求人工复核\n保留当前最佳总结;
    stop
  else (否)
    :重新生成总结;
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
participant "runtime contract\n+ taxonomy + knowhow" as Knowledge
participant "crm-meeting-summary-review" as Review
participant "最终总结" as Output

User -> Claude: 请求生成会议总结
Claude -> Skill: 调用主 Skill
Skill -> Knowledge: 归一化输入并加载参考规则
Knowledge --> Skill: 返回场景、约束、模板与 knowhow
Skill -> Skill: 生成原始总结
Skill -> Review: 调用 review 子 skill
Review --> Skill: pass / fail + targeted fixes
Skill -> Skill: 最多 2 轮定向修复
Skill -> Output: 输出最终结果或人工复核结论
Output --> Claude: 返回结构化总结
Claude --> User: 展示最终总结
@enduml
```

## 4. 工程分层结构图

```plantuml
@startuml
title crm-meeting-summary 工程分层结构图
skinparam shadowing false
skinparam packageStyle rectangle
skinparam defaultTextAlignment center
skinparam ArrowColor #64748b
skinparam ArrowThickness 1.2
skinparam package {
  BorderColor #cbd5e1
  FontStyle bold
}
skinparam rectangle {
  RoundCorner 16
  BorderColor #94a3b8
}

top to bottom direction

rectangle "L1 使用入口层\n\nClaude Code / 用户请求 / Skill routing" as L1 #DBEAFE
rectangle "L2 Skill 定义层\n\nskills/crm-meeting-summary/SKILL.md\nskills/crm-meeting-summary/review/SKILL.md" as L2 #DCFCE7
rectangle "L3 参考与知识层\n\nruntime-contract.md / taxonomy.md\nknowhow/common / by-scenario / by-industry / patches / best-cases\ntemplates/profiles / common/default.md\nmeeting-methodology.md / review-rubric.md / example-input.md" as L3 #FEF3C7
rectangle "L4 测试辅助运行层\n\nreal_runner.py / mock_runner.py / contract_validator.py" as L4 #FCE7F3
rectangle "L5 测试数据与评测层\n\nfixtures/mock-runtime/meeting-records/*.json\nevals/evals.json / run_real_evals.py / test-result-dashboard.*\ntest_mock_runner.py / test_real_runner.py / test_run_real_evals.py" as L5 #EDE9FE

L1 -down-> L2
L2 -down-> L3
L3 -down-> L4
L4 -down-> L5
@enduml
```

## 5. README 中的旧 skill 架构图已并入第 2 张关键流程图

本节不再单独画新流程，README.md 里的旧 Mermaid skill 架构图已经合并到第 2 张图里。第 2 张图以原“处理流程图”为主干，同时保留了 README 旧图中的关键红框节点，用来标出真正决定质量和路径分叉的核心步骤。

关键红框节点保留为：
- conservative mode / 多层 knowhow 加载
- 最小 crm_data_requests
- memory 上下文组装
- 原始总结生成
- template 重排
- review 子 skill
- 最终交付 / 人工复核

## 6. eval 执行链路图

```plantuml
@startuml
title crm-meeting-summary eval 执行链路

actor Developer
participant "tests/test_run_real_evals.py" as Pytest
participant "tests/crm_meeting_summary/evals/run_real_evals.py" as EvalRunner
participant "tests/crm_meeting_summary/helpers/real_runner.py" as RealRunner
participant "crm-meeting-summary\nSKILL.md" as Skill
participant "crm-meeting-summary-review" as Review
participant "contract_validator.py" as Validator
participant "evals.json / result json" as Artifacts

Developer -> Pytest: 运行评测测试
Pytest -> EvalRunner: 调用 case 执行入口
EvalRunner -> Artifacts: 读取 evals.json case 定义
EvalRunner -> RealRunner: 按 case 组装输入并执行
RealRunner -> Skill: 调用主 skill
Skill -> Review: 执行 review 子 skill
Review --> Skill: 返回 pass/fail 与修复意见
Skill --> RealRunner: 返回最终输出
RealRunner -> Validator: 校验输出 contract
Validator --> RealRunner: contract 校验结果
RealRunner --> EvalRunner: 返回 case 结果
EvalRunner -> Artifacts: 写入 result json / 汇总结果
EvalRunner --> Pytest: 返回评测结果
@enduml
```
