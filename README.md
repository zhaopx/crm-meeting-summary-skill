# summay-skill

## crm-meeting-summary skill 可视化图集

- 浏览器入口：[visual-diagrams.md](./docs/crm-meeting-summary/visual-diagrams.md)
- 仓库相对路径：`docs/crm-meeting-summary/visual-diagrams.md`
- 内容包含：总架构图、skill 关键流程图、主执行时序图、工程分层结构图、eval 执行链路图

## crm-meeting-summary skill 关键流程图

```mermaid
flowchart TD
    A[用户输入\n自然语言纪要或显式输入包] --> B[crm-meeting-summary 主 Skill]

    B --> B1[1. 输入归一化\nmeeting / crm_context / constraints]
    B1 --> B2[2. 场景识别\ntaxonomy.md]
    B2 --> G{scenario_confidence}

    G -->|high / medium| KH[3. 加载 knowhow\ncommon + scenario\n按证据加载 industry / patch / best-cases]
    G -->|low| KHU[3'. conservative mode\n只加载 common\n不加载 scenario / patch / best-cases]

    KH --> R[4. 决定最小 CRM 请求\nretrieval policy + data_requirements\n=> crm_data_requests]
    KHU --> R

    R --> N[5. 语义归一\nsemantic_normalization\n对象 / 关系 / 字段口径统一]
    N --> M[6. 当前会议特征提取\nmeeting_state_features\n只基于当前 meeting + CRM]
    M --> MM[7. 组装 memory 上下文\n当前会议 / CRM 优先\n冲突时保留当前证据]
    MM --> C{memory 是否冲突}
    C -->|否| S[8. 生成原始总结\n会议快照 / 核心判断\n下一步 / 风险待确认]
    C -->|是| MC[记录 memory conflict\n必要时降低判断强度]
    MC --> S

    S --> T[9. 按 template 重排\ntemplate 与 knowhow 平行\n只重排结构, 不新增事实]
    T --> RV[10. crm-meeting-summary-review 子 Skill]
    RV --> RV1[校验事实准确性]
    RV1 --> RV2[校验风险覆盖]
    RV2 --> RV3[校验业务可行动性]
    RV3 --> D{review 是否通过}

    D -->|pass| E[最终交付\n人类可读总结]
    D -->|fail,可修复| F[定向修复\n只修失败维度后重生总结]
    F --> S
    D -->|fail,仍不稳| H[人工接管\n保留当前最佳总结并标注人工复核]

    E --> I[输出给调用方\nhuman summary]
    H --> I

    classDef core fill:#ffe9e9,stroke:#cf222e,stroke-width:3px,color:#cf222e;
    classDef detail fill:#eefaf1,stroke:#2da44e,stroke-width:1.5px,color:#0f2d1b;
    classDef decision fill:#fff3cd,stroke:#b7791f,stroke-width:2px,color:#4a2f00;

    class B,B2,KH,KHU,MM,S,T,RV,I core;
    class A,N,MC,M,E,F,H,B1,R,RV1,RV2,RV3 detail;
    class G,C,D decision;
```

## 组件说明

### 1. 主 Skill
- 文件：`skills/crm-meeting-summary/SKILL.md`
- 职责：
  - 归一化输入
  - 识别场景
  - 约束最小 retrieval
  - 生成人类可读总结
  - 调用 review skill
  - 控制定向修复与人工复核

### 2. Review Skill
- 文件：`skills/crm-meeting-summary/review/SKILL.md`
- 职责：
  - 判断 pass / fail
  - 给出 `failure_reasons`
  - 给出 `targeted_regeneration_instructions`
  - 不重写正文，只做质量闸门
- 运行时判定口径以 `skills/crm-meeting-summary/review/SKILL.md` 为准；`docs/crm-meeting-summary/review-rubric.md` 只作为人工阅读说明，不是 runtime 依赖

### 3. 参考契约层
- `skills/crm-meeting-summary/references/taxonomy.md`：定义场景分类与默认 retrieval policy
- `skills/crm-meeting-summary/references/runtime-contract.md`：运行时输入输出契约、request groups、memory 使用边界与审计规则的单一事实来源

### 4. 方法论、Knowhow 与 Template 层
- [docs/crm-meeting-summary/meeting-methodology.md](docs/crm-meeting-summary/meeting-methodology.md)：解释为什么这是 CRM 总结产品，而不是通用 transcript summarizer
- [skills/crm-meeting-summary/references/knowhow/common/](skills/crm-meeting-summary/references/knowhow/common/)：第一层，所有 case 默认加载，提供跨场景共用的评估框架、基础判断边界与通用风险提醒，不是事实来源
- [skills/crm-meeting-summary/references/knowhow/by-scenario/](skills/crm-meeting-summary/references/knowhow/by-scenario/)：第二层，在场景已识别时按 `scenario_slug` 加载，补充该场景专属的关注点、风险信号、成功标准与 `data_requirements`，参与 CRM 请求决策与总结生成，不是事实来源
- [skills/crm-meeting-summary/references/knowhow/by-industry/](skills/crm-meeting-summary/references/knowhow/by-industry/)：第三层，在行业有独立证据时加载，补充行业语境、行业常见约束与行业化判断边界，不是事实来源
- [skills/crm-meeting-summary/references/knowhow/patches/](skills/crm-meeting-summary/references/knowhow/patches/)：第四层，只在“场景 + 行业”组合有特殊规则时加载，用来修正前面三层在特定组合下不够准确的地方，不是事实来源
- [skills/crm-meeting-summary/references/knowhow/best-cases/](skills/crm-meeting-summary/references/knowhow/best-cases/)：可选层，不承担分类、检索或 policy 约束职责，只在确有帮助时加载，用来补充高质量总结框架、表达结构和 coverage checklist，不是事实来源
- [skills/crm-meeting-summary/references/templates/](skills/crm-meeting-summary/references/templates/)：模板层，与 knowhow 平行，在原始 summary 生成后才介入，只负责目录重排，不提供新事实

加载关系：
- knowhow 基础顺序是 `common -> by-scenario -> by-industry -> patches`
- `best-cases` 是独立可选增强层，不参与前面的规则链
- `templates` 不走 knowhow 的多层 merge 模型，只在 summary 已生成后选一份最终模板做结构重排
- `template` 命中顺序是 `profiles/<scenario_slug>--<industry> -> profiles/<scenario_slug> -> common/default`

### 5. 开发辅助层
- `tests/crm_meeting_summary/helpers/real_runner.py`
- `tests/crm_meeting_summary/evals/run_real_evals.py`
- `tests/crm_meeting_summary/helpers/mock_runner.py`
- `tests/crm_meeting_summary/fixtures/mock-runtime/`
- `tests/crm_meeting_summary/evals/evals.json`

作用：
- 通过 `tests/crm_meeting_summary/helpers/real_runner.py` 调用真实 skill，并捕获完整最终返回值
- 通过 `run_real_evals.py` 批量跑关键 case
- 用 `tests/crm_meeting_summary/helpers/mock_runner.py` 做本地回归验证
- 用 mock data 演练输入
- 做文档与行为对齐验证

不是生产运行路径。

## 当前真实运行链路

真实调用时，`meeting record` 可以直接内联到输入里，也可以通过 `meeting.record_text_path` 指向文本文件，也可以通过 `input_bundle_path` 指向目录输入包。目录输入包只允许读取 `meeting-record.txt`、`AccountObj.json`、`NewOpportunityObj.json`、`PersonnelObj.json`、`ContactObj.json`。主 skill 在归一化阶段按 `record_text > record_text_path > input_bundle_path/meeting-record.txt` 的优先级得到最终会议纪要内容，再进入后续流程。

1. 调用 `crm-meeting-summary`
2. 主 skill 在 Claude runtime 内完成输入归一化与场景识别
3. 按 `scenario_confidence` 决定是否进入 conservative mode，并据此加载最小 knowhow 集合
4. 主 skill 按 `taxonomy.md` 的 retrieval policy、`runtime-contract.md` 的 request groups，以及已加载 knowhow 的 `data_requirements`，形成最小 `crm_data_requests`
5. 主 skill 先产出 `semantic_normalization`，统一对象、关系、字段口径
6. 主 skill 再从当前 meeting + CRM 提取 `meeting_state_features`
7. 主 skill 组装 memory 上下文；如果 memory 与当前会议或当前 CRM 冲突，优先保留当前证据，并在需要时降低判断强度
8. 主 skill 先生成原始人类总结，覆盖会议快照、核心总结与判断、Knowhow 关注点、建议的下一步动作、风险与待确认问题
9. 主 skill 再选择单一 template，把已有 summary 重排成最终目录格式；template 只重组已有内容，不新增事实
10. 主 skill 调用 `crm-meeting-summary-review`
11. review pass 则交付最终人类总结
12. review 最多允许 2 次定向修复；若仍不稳定，则保留当前最佳总结并要求人工复核

## 本轮补强点

本轮针对回归 case 收紧了这些约束：
- low confidence 必须落到 `其他 / 不确定` 或等价保守结论
- uncertain 模式不得加载 scenario knowhow / patches / best-cases
- uncertain 模式下只允许最小消歧请求
- memory 与当前会议冲突时必须在总结中暴露冲突边界
- 弱证据输入在两轮定向修复后必须进入人工复核
- 模板缺失项不得编造成确定性陈述

## 文档入口

- 输入方式：`docs/crm-meeting-summary/example-input.md`
- 完整执行链路与标准输出样例：`docs/crm-meeting-summary/case-execution-example.md`
- 运行时单一事实来源：`skills/crm-meeting-summary/references/runtime-contract.md`
- 运行时评审规则：`skills/crm-meeting-summary/review/SKILL.md`
- 评审说明文档：`docs/crm-meeting-summary/review-rubric.md`
- 产品方法论：`docs/crm-meeting-summary/meeting-methodology.md`
