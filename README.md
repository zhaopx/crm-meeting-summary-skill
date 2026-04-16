# summay-skill

## 文档入口

- [输入方式](docs/crm-meeting-summary/example-input.md)
- [执行链路示例](docs/crm-meeting-summary/case-execution-example.md)
- [评审说明](docs/crm-meeting-summary/review-rubric.md)
- [方法论](docs/crm-meeting-summary/meeting-methodology.md)
- [可视化图](docs/crm-meeting-summary/visual-diagrams.md)
- [运行时契约](skills/crm-meeting-summary/references/runtime-contract.md)
- [评审规则](skills/crm-meeting-summary/review/SKILL.md)
- [主 skill](skills/crm-meeting-summary/SKILL.md)

## 项目结构

### 运行时文件
- `skills/crm-meeting-summary/SKILL.md`
- `skills/crm-meeting-summary/review/SKILL.md`
- `skills/crm-meeting-summary/references/runtime-contract.md`
- `skills/crm-meeting-summary/references/taxonomy.md`
- `skills/crm-meeting-summary/references/knowhow/`
- `skills/crm-meeting-summary/references/templates/`

### 测试与验证文件
- `tests/crm_meeting_summary/helpers/real_runner.py`
- `tests/crm_meeting_summary/evals/run_real_evals.py`
- `tests/crm_meeting_summary/helpers/mock_runner.py`
- `tests/crm_meeting_summary/fixtures/mock-runtime/`
- `tests/crm_meeting_summary/evals/evals.json`

### 非运行时说明文件
- `docs/crm-meeting-summary/meeting-methodology.md`
- `docs/crm-meeting-summary/review-rubric.md`
- `docs/crm-meeting-summary/case-execution-example.md`
- `docs/crm-meeting-summary/example-input.md`
- `docs/crm-meeting-summary/visual-diagrams.md`

## 当前约束

- 最终正式口径以 `runtime-contract.md`、主 skill、review skill 为准
- `docs/` 下文档只做说明，不作为运行时单一事实来源
- mock runner 与 fixtures 只用于开发验证，不是生产运行路径
