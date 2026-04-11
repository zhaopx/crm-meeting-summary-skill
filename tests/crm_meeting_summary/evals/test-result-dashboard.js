const defaultReportMeta = {
  report_version: "N/A",
  generated_at: "N/A",
  skill_name: "crm-meeting-summary",
  source_case: "N/A",
  notes: "暂无备注。"
};

const defaultSkillContext = {
  output_required_fields: [],
  key_constraints: [],
  loaded_markdown: []
};

const safeArray = (value) => Array.isArray(value) ? value : [];
const getLength = (value) => safeArray(value).length;
const safeText = (value) => value === null || value === undefined || value === "" ? "N/A" : String(value);
const safeJoinedText = (value) => {
  const values = safeArray(value);
  return values.length ? values.join("\n") : "N/A";
};
const getElement = (id) => {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing required dashboard element: ${id}`);
  }
  return element;
};

const rawReport = window.__REPORT_DATA__ ?? {};
const report = {
  report_meta: {
    ...defaultReportMeta,
    ...(rawReport.report_meta ?? {})
  },
  skill_context: {
    ...defaultSkillContext,
    ...(rawReport.skill_context ?? {}),
    output_required_fields: safeArray(rawReport.skill_context?.output_required_fields),
    key_constraints: safeArray(rawReport.skill_context?.key_constraints),
    loaded_markdown: safeArray(rawReport.skill_context?.loaded_markdown)
  },
  runs: safeArray(rawReport.runs),
  comparison: rawReport.comparison ?? null
};

const currentRun = report.runs.length ? report.runs[report.runs.length - 1] : null;
const getScenarioResult = (run) => run?.scenario_result ?? {};
const getSummaryFields = (run) => run?.summary_fields ?? {};
const getRetryState = (run) => run?.retry_state ?? {};
const getLoadedKnowhow = (run) => run?.loaded_knowhow ?? {};
const getHumanSummary = (run) => run?.human_summary ?? {};
const getRunLoadedMarkdown = (run) => safeArray(run?.loaded_markdown);
const getTemplateOutput = (run) => run?.template_output ?? {};
const getTemplateTrace = (run) => run?.template_trace ?? {};

const renderHtmlList = (containerId, items) => {
  const container = getElement(containerId);
  container.replaceChildren(...items.map((item) => {
    const li = document.createElement("li");
    li.textContent = safeText(item);
    return li;
  }));
};

const renderSummaryList = (containerId, items) => {
  const values = safeArray(items);
  const normalizedValues = values.length ? values : ["N/A"];
  renderHtmlList(containerId, normalizedValues);
};

const renderMetaGrid = (containerId, entries) => {
  getElement(containerId).replaceChildren(...entries.map(([label, value]) => {
    const dl = document.createElement("dl");
    dl.className = "meta-item";

    const dt = document.createElement("dt");
    dt.textContent = label;

    const dd = document.createElement("dd");
    dd.textContent = safeText(value);

    dl.append(dt, dd);
    return dl;
  }));
};

const renderTemplateSections = (containerId, sections) => {
  const container = getElement(containerId);
  const values = safeArray(sections);
  if (!values.length) {
    container.replaceChildren(Object.assign(document.createElement("p"), { textContent: "N/A" }));
    return;
  }

  container.replaceChildren(...values.map((section) => {
    const wrapper = document.createElement("div");
    wrapper.className = "sub";

    const title = document.createElement("strong");
    title.textContent = safeText(section.title);

    const list = document.createElement("ul");
    list.className = "list";

    safeArray(section.items).forEach((item) => {
      const li = document.createElement("li");
      const value = item?.value_presence === "missing"
        ? "[missing]"
        : Array.isArray(item?.value)
          ? item.value.join("；")
          : safeText(item?.value);
      li.textContent = `${safeText(item?.label)}：${value}`;
      list.append(li);
    });

    wrapper.append(title, list);
    return wrapper;
  }));
};

const renderDetailList = (title, items) => {
  const block = document.createElement("div");
  block.className = "sub";

  const list = document.createElement("ul");
  list.className = "list list-compact";
  const normalizedItems = safeArray(items).length ? safeArray(items) : ["N/A"];
  normalizedItems.forEach((item) => list.append(Object.assign(document.createElement("li"), { textContent: safeText(item) })));

  block.append(
    Object.assign(document.createElement("strong"), { textContent: title }),
    list
  );

  return block;
};

const formatCellItems = (items) => {
  const values = safeArray(items);
  return values.length ? values.map((item) => `• ${safeText(item)}`).join("\n") : "N/A";
};

const normalizeComparison = () => {
  if (report.comparison) {
    return {
      sourceMaterial: report.comparison.source_material ?? {},
      summaries: safeArray(report.comparison.summaries),
      evaluation: report.comparison.evaluation ?? {},
      auxiliary: report.comparison.auxiliary ?? {}
    };
  }

  if (!currentRun) {
    return {
      sourceMaterial: {},
      summaries: [],
      evaluation: {},
      auxiliary: {}
    };
  }

  const scenarioResult = getScenarioResult(currentRun);
  const summaryFields = getSummaryFields(currentRun);
  const humanSummary = getHumanSummary(currentRun);
  const loadedKnowhow = getLoadedKnowhow(currentRun);
  const templateOutput = getTemplateOutput(currentRun);
  const templateTrace = getTemplateTrace(currentRun);

  const skillSummary = [
    safeText(currentRun.summary_sentence),
    safeText(summaryFields.decision_pressure),
    getLength(summaryFields.next_actions) ? `下一步动作：${safeArray(summaryFields.next_actions).join("；")}` : "N/A"
  ].filter((item) => item !== "N/A").join("\n\n");

  return {
    sourceMaterial: {
      source_case: report.report_meta.source_case,
      meeting_time: currentRun.machine_output?.base_context?.meeting_time,
      account: currentRun.machine_output?.base_context?.account?.name,
      opportunity: currentRun.machine_output?.base_context?.opportunity?.name,
      participant_count: getLength(currentRun.machine_output?.base_context?.participants),
      source_note: "当前示例为同一份 case-001 语料下的静态比较样本。"
    },
    summaries: [
      {
        summary_id: "human-summary",
        source_type: "human",
        source_label: "new-summay",
        version_label: "baseline",
        score: 9.2,
        verdict: "细节最完整，判断最稳定",
        focus_tags: ["基准版本", "业务判断清楚", "风险表达完整"],
        body_sections: [
          { title: "Meeting snapshot", content: humanSummary.meeting_snapshot },
          { title: "Core summary and judgment", content: humanSummary.core_summary_and_judgment }
        ],
        strengths: [
          "覆盖会议背景、判断和风险，信息闭环完整。",
          "能区分客户正向兴趣与真实推进条件，业务判断稳定。"
        ],
        weaknesses: [
          "篇幅最长，后续需要压缩到更适合平台侧展示的长度。"
        ],
        actions: safeArray(humanSummary.recommended_next_actions),
        risks: safeArray(humanSummary.risks_and_open_questions)
      },
      {
        summary_id: "skill-current",
        source_type: "skill",
        source_label: "Skill 总结",
        version_label: report.report_meta.report_version,
        score: 8.4,
        verdict: "结构化最强，但表达还偏 machine-oriented",
        focus_tags: [safeText(scenarioResult.primary_scenario), safeText(scenarioResult.industry), safeText(summaryFields.risk_level)],
        body_sections: [
          { title: "Summary sentence", content: currentRun.summary_sentence },
          { title: "Stage judgment", content: summaryFields.current_stage_judgment },
          { title: "Decision pressure", content: summaryFields.decision_pressure },
          { title: "Skill narrative", content: skillSummary }
        ],
        strengths: [
          "场景判断、结构化字段和缺失信息表达清楚。",
          "适合后续做自动评审、字段比对和版本回归。"
        ],
        weaknesses: [
          "可读性不如人工总结，读起来更像运行产物。",
          "对业务语义的压缩仍偏 schema 视角。"
        ],
        actions: safeArray(summaryFields.next_actions),
        risks: safeArray(summaryFields.missing_information)
      },
      {
        summary_id: "feishu-placeholder",
        source_type: "feishu",
        source_label: "飞书总结",
        version_label: "待接入",
        score: "N/A",
        verdict: "预留位置，后续接入同语料结果后直接比较",
        focus_tags: ["占位", "待补充"],
        body_sections: [
          { title: "Current status", content: "当前页面已预留飞书总结位置，等待同一语料的真实结果填入。" }
        ],
        strengths: ["N/A"],
        weaknesses: ["当前无实际内容。"],
        actions: ["待补充"],
        risks: ["当前无法参与质量比较。"]
      },
      {
        summary_id: "dingtalk-placeholder",
        source_type: "dingtalk",
        source_label: "钉钉总结",
        version_label: "待接入",
        score: "N/A",
        verdict: "预留位置，后续接入同语料结果后直接比较",
        focus_tags: ["占位", "待补充"],
        body_sections: [
          { title: "Current status", content: "当前页面已预留钉钉总结位置，等待同一语料的真实结果填入。" }
        ],
        strengths: ["N/A"],
        weaknesses: ["当前无实际内容。"],
        actions: ["待补充"],
        risks: ["当前无法参与质量比较。"]
      }
    ],
    evaluation: {
      winner_summary_id: "human-summary",
      reviewer_callout: "当前人工总结最适合作为基准版本。skill 总结已经适合做结构化回归，但在可读性和业务语义压缩上仍落后于人工总结。飞书和钉钉位置已经预留，后续填入真实结果后就能在同一页做横向评测。",
      overview: {
        primary_goal: "比较同一语料下多来源总结的质量，而不是回放单次执行过程。",
        best_current_version: "人工总结",
        machine_best_use: "skill 总结更适合作为结构化评测与版本回归样本。"
      },
      dimensions: [
        "完整性：是否覆盖背景、判断、行动、风险四层信息。",
        "准确性：是否忠实于原始语料，没有过度推断。",
        "可执行性：下一步动作是否能直接指导后续跟进。",
        "可读性：是否更像给业务团队看的总结，而不是机器产物。"
      ],
      ranking: [
        "人工总结：当前第一，完整性和业务判断最强。",
        "Skill 总结：当前第二，结构化最强，表达仍偏 machine-oriented。",
        "飞书总结：待接入。",
        "钉钉总结：待接入。"
      ],
      consensus: [
        "当前会议的核心不是价格谈判，而是需求澄清与能力边界确认。",
        "推进条件都指向作业覆盖度、外部接口和 seat 成本结构。"
      ],
      divergence: [
        "人工总结更强调业务语境和推进风险，skill 总结更强调结构化字段和缺失信息。",
        "后续平台总结需要重点比较：是否遗漏关键风险、是否把意向误判成成交信号。"
      ],
      reviewer_notes: [
        "当前页面的正确主角是多份总结本身，不是 execution result。",
        "辅助诊断信息保留，但必须退出首屏主视图。",
        "后续接入飞书/钉钉后，优先比较完整性、幻觉率和行动建议质量。"
      ]
    },
    auxiliary: {
      loaded_markdown: getRunLoadedMarkdown(currentRun).length ? getRunLoadedMarkdown(currentRun) : report.skill_context.loaded_markdown,
      loaded_knowhow: loadedKnowhow,
      template_output: templateOutput,
      template_trace: templateTrace,
      retry_state: getRetryState(currentRun),
      required_fields: report.skill_context.output_required_fields,
      skill_constraints: report.skill_context.key_constraints,
      machine_output: currentRun.machine_output ?? {}
    }
  };
};

const comparison = normalizeComparison();
const sourceMaterial = comparison.sourceMaterial ?? {};
const summaries = safeArray(comparison.summaries);
const evaluation = comparison.evaluation ?? {};
const auxiliary = comparison.auxiliary ?? {};

const renderOverviewMetrics = () => {
  const metrics = [
    { label: "比较对象", value: getLength(summaries), help: "当前页面中并列展示的总结数量" },
    { label: "当前最佳", value: safeText(evaluation.overview?.best_current_version), help: "按当前 AI 评审口径" }
  ];

  getElement("overview-metrics").replaceChildren(...metrics.map((metric) => {
    const card = document.createElement("div");
    card.className = "card metric-card";

    const label = document.createElement("div");
    label.className = "metric-label";
    label.textContent = metric.label;

    const value = document.createElement("div");
    value.className = "metric-value";
    value.textContent = safeText(metric.value);

    const help = document.createElement("div");
    help.className = "metric-help";
    help.textContent = safeText(metric.help);

    card.append(label, value, help);
    return card;
  }));
};

const renderSummaryCards = () => {
  const container = getElement("summary-cards");
  if (!summaries.length) {
    container.replaceChildren(Object.assign(document.createElement("p"), { textContent: "暂无可比较的总结。" }));
    return;
  }

  container.replaceChildren(...summaries.map((summary, summaryIndex) => {
    const card = document.createElement("section");
    card.className = "card card-section summary-card";

    const header = document.createElement("div");
    header.className = "summary-card-header";

    const sourceBlock = document.createElement("div");
    sourceBlock.className = "summary-card-source";

    const sourceType = document.createElement("div");
    sourceType.className = "card-kicker";
    sourceType.textContent = safeText(summary.source_type);

    const title = document.createElement("h3");
    title.className = "summary-card-title";
    title.textContent = safeText(summary.source_label);

    const version = document.createElement("div");
    version.className = "summary-card-version";
    version.textContent = `版本：${safeText(summary.version_label)}`;

    sourceBlock.append(sourceType, title, version);

    const score = document.createElement("div");
    score.className = "summary-score";
    score.textContent = `评分 ${safeText(summary.score)}`;

    header.append(sourceBlock, score);

    const tagList = document.createElement("div");
    tagList.className = "tag-list";
    safeArray(summary.focus_tags).forEach((tag) => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = safeText(tag);
      tagList.append(chip);
    });

    const body = document.createElement("div");
    body.className = "summary-body summary-body-limited";
    body.id = `summary-body-${summaryIndex}`;
    safeArray(summary.body_sections).forEach((section) => {
      const wrapper = document.createElement("div");
      wrapper.className = "sub";

      const sectionTitle = safeText(section.title);
      const numberedTitleMatch = /^(\d+\.)\s*(.+)$/.exec(sectionTitle);
      if (numberedTitleMatch) {
        wrapper.className = "sub summary-section";
        const heading = document.createElement("div");
        heading.className = "summary-section-heading";

        const index = document.createElement("span");
        index.className = "summary-section-index";
        index.textContent = numberedTitleMatch[1];

        const titleText = document.createElement("strong");
        titleText.textContent = numberedTitleMatch[2];

        heading.append(index, titleText);
        wrapper.append(heading);
      } else {
        const titleText = document.createElement("strong");
        titleText.textContent = sectionTitle;
        wrapper.append(titleText);
      }

      const isRawSection = summary.source_type !== "human" && safeArray(summary.body_sections).length === 1;
      if (isRawSection) {
        const sectionText = document.createElement("pre");
        sectionText.className = "summary-raw-block";
        sectionText.textContent = safeText(section.content).replace(/\n{3,}/g, "\n\n");
        wrapper.append(sectionText);
      } else {
        const richText = document.createElement("div");
        richText.className = "summary-rich-text";

        safeText(section.content)
          .split(/\n{2,}/)
          .filter((paragraph) => paragraph.trim())
          .forEach((paragraph) => {
            const p = document.createElement("p");
            const lines = paragraph.split("\n");
            lines.forEach((line, lineIndex) => {
              if (lineIndex > 0) {
                p.append(document.createElement("br"));
              }
              p.append(document.createTextNode(line));
            });
            richText.append(p);
          });

        wrapper.append(richText);
      }

      body.append(wrapper);
    });

    const footer = document.createElement("div");
    footer.className = "summary-card-footer";

    const hint = document.createElement("div");
    hint.className = "summary-card-hint";
    hint.textContent = "内容过长时卡片保持固定高度，滚动查看。";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "summary-inline-toggle";
    toggle.textContent = "展开全文";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", body.id);

    toggle.addEventListener("click", () => {
      const expanded = body.classList.toggle("summary-body-expanded");
      toggle.textContent = expanded ? "收起全文" : "展开全文";
      toggle.setAttribute("aria-expanded", String(expanded));
    });

    footer.append(hint, toggle);
    card.append(header, tagList, body, footer);
    return card;
  }));
};

const renderSummaryReviewTable = () => {
  const container = getElement("summary-review-table-body");
  if (!summaries.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 7;
    cell.textContent = "暂无评审数据。";
    row.append(cell);
    container.replaceChildren(row);
    return;
  }

  container.replaceChildren(...summaries.map((summary) => {
    const row = document.createElement("tr");
    const cells = [
      safeText(summary.source_label),
      safeText(summary.score),
      safeText(summary.verdict),
      formatCellItems(summary.strengths),
      formatCellItems(summary.weaknesses),
      formatCellItems(summary.actions),
      formatCellItems(summary.risks)
    ];

    cells.forEach((value, index) => {
      const cell = document.createElement(index === 0 ? "th" : "td");
      if (index === 0) {
        cell.scope = "row";
      }
      cell.textContent = value;
      row.append(cell);
    });

    return row;
  }));
};

getElement("hero-description").textContent = "当前页面服务同一份会议语料下的多来源总结对比。主看总结内容和 AI 评审，不再把 execution result 当成主角。";

const heroNote = getElement("hero-note");
heroNote.replaceChildren(
  document.createTextNode("当前输入包来自 "),
  Object.assign(document.createElement("span"), { className: "code-inline", textContent: safeText(sourceMaterial.source_case || report.report_meta.source_case) }),
  document.createTextNode("。页面已切换为 comparison-first 结构，execution / trace / machine JSON 退到辅助区。")
);

renderOverviewMetrics();
renderSummaryCards();
renderSummaryReviewTable();
renderHtmlList("evaluation-dimensions-list", safeArray(evaluation.dimensions).length ? evaluation.dimensions : ["N/A"]);
renderHtmlList("evaluation-ranking-list", safeArray(evaluation.ranking).length ? evaluation.ranking : ["N/A"]);
renderHtmlList("consensus-list", safeArray(evaluation.consensus).length ? evaluation.consensus : ["N/A"]);
renderHtmlList("divergence-list", safeArray(evaluation.divergence).length ? evaluation.divergence : ["N/A"]);
renderHtmlList("reviewer-notes-list", safeArray(evaluation.reviewer_notes).length ? evaluation.reviewer_notes : ["N/A"]);
getElement("evaluation-callout").textContent = safeText(evaluation.reviewer_callout);
