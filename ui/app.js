(() => {
  "use strict";

  const STORAGE_KEY = "mpa-local-workbench-v1";
  const VIEW_LABELS = {
    intake: "需求访谈",
    slides: "页面架构",
    evidence: "证据与风险",
    export: "生成与导出",
  };
  const VIEW_ORDER = ["intake", "slides", "evidence", "export"];
  const REQUIRED_FIELDS = [
    "topic",
    "audience",
    "purpose",
    "outcomes",
    "duration",
    "slideCount",
    "evidenceLevel",
  ];
  const VISUALS = [
    ["photo", "▧", "临床 / 设备照片"],
    ["case", "◫", "病例图"],
    ["diagram", "◇", "示意图"],
    ["flow", "→", "流程图"],
    ["chart", "▥", "数据图表"],
    ["table", "▦", "表格"],
    ["decision", "⑂", "决策树"],
    ["timeline", "↦", "时间线"],
    ["screenshot", "⌗", "界面截图"],
    ["number", "42", "数字卡"],
    ["comparison", "⇄", "对照"],
    ["text", "文", "重点文字"],
  ];
  const TYPE_LABELS = {
    clinical: "临床结论",
    numeric: "数字 / 统计",
    guideline: "指南建议",
    device: "设备 / 参数",
    local_sop: "院内 SOP",
    image: "图片来源",
    experience: "讲者经验",
  };
  const STATUS_LABELS = {
    pending: "待验证",
    verified: "已验证",
    synthetic: "合成示例",
  };

  const emptyState = () => ({
    version: 1,
    updatedAt: null,
    activeView: "intake",
    selectedSlideId: null,
    intake: {},
    files: [],
    slides: [],
    claims: [],
    service: { online: false, project: null, command: null },
  });

  let state = loadState();
  let selectedFiles = [];
  let saveTimer = null;
  let toastTimer = null;

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return emptyState();
      const parsed = JSON.parse(raw);
      return {
        ...emptyState(),
        ...parsed,
        intake: parsed.intake || {},
        files: Array.isArray(parsed.files) ? parsed.files : [],
        slides: Array.isArray(parsed.slides) ? parsed.slides : [],
        claims: Array.isArray(parsed.claims) ? parsed.claims : [],
        service: { ...emptyState().service, ...(parsed.service || {}), online: false },
      };
    } catch (_error) {
      return emptyState();
    }
  }

  function persistState(immediate = false) {
    clearTimeout(saveTimer);
    const write = () => {
      state.updatedAt = new Date().toISOString();
      const persisted = { ...state, service: { ...state.service, online: false } };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
      const time = new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit" }).format(new Date());
      $("#saveStatus").textContent = `已于 ${time} 保存到本机`;
    };
    if (immediate) write();
    else {
      $("#saveStatus").textContent = "正在保存…";
      saveTimer = setTimeout(write, 450);
    }
  }

  function escapeHtml(value) {
    const node = document.createElement("div");
    node.textContent = String(value ?? "");
    return node.innerHTML;
  }

  function valueList(name) {
    return $$(`input[name="${name}"]:checked`).map((input) => input.value);
  }

  function radioValue(name) {
    return $(`input[name="${name}"]:checked`)?.value || "";
  }

  function readIntakeForm() {
    const form = $("#intakeForm");
    const values = {};
    for (const element of $$('input:not([type="file"]), select, textarea', form)) {
      if (!element.name || element.type === "radio" || element.type === "checkbox") continue;
      values[element.name] = element.value.trim();
    }
    values.style = radioValue("style");
    values.network = radioValue("network");
    values.assets = valueList("assets");
    values.privacy = valueList("privacy");
    values.outputs = valueList("outputs");
    state.intake = values;
  }

  function fillIntakeForm() {
    const values = state.intake || {};
    for (const [name, value] of Object.entries(values)) {
      if (Array.isArray(value)) {
        $$(`input[name="${name}"]`).forEach((input) => {
          input.checked = value.includes(input.value);
        });
        continue;
      }
      const controls = $$(`[name="${name}"]`);
      for (const control of controls) {
        if (control.type === "radio") control.checked = control.value === value;
        else if (control.type !== "checkbox" && control.type !== "file") control.value = value;
      }
    }
    updateFilesLabel();
  }

  function completion() {
    const complete = REQUIRED_FIELDS.filter((name) => String(state.intake[name] || "").trim()).length;
    return Math.round((complete / REQUIRED_FIELDS.length) * 100);
  }

  function updateProgress() {
    const percent = completion();
    $("#completionValue").textContent = `${percent}%`;
    $("#completionRing").style.background = `conic-gradient(var(--teal-500) ${percent}%, #d9dedb ${percent}%)`;
    $("#completionRing").setAttribute("aria-label", `需求完成度 ${percent}%`);
    $("#sideProgressBar").style.width = `${percent}%`;
    $("#sideProgressText").textContent = `需求信息 ${percent}% 完整`;
    $("#sideProjectTitle").textContent = state.intake.topic || "未命名演示";
    updateReadiness();
  }

  function changeView(view) {
    if (!VIEW_ORDER.includes(view)) return;
    state.activeView = view;
    $$("[data-view-panel]").forEach((panel) => {
      const active = panel.dataset.viewPanel === view;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    $$(".nav-item").forEach((item) => {
      const active = item.dataset.view === view;
      item.classList.toggle("is-active", active);
      if (active) item.setAttribute("aria-current", "page");
      else item.removeAttribute("aria-current");
    });
    $("#currentViewLabel").textContent = VIEW_LABELS[view];
    const nextIndex = VIEW_ORDER.indexOf(view) + 1;
    if (nextIndex < VIEW_ORDER.length) {
      $("#nextButton").hidden = false;
      $("#nextButton").textContent = `继续：${VIEW_LABELS[VIEW_ORDER[nextIndex]]}`;
    } else {
      $("#nextButton").hidden = true;
    }
    if (view === "slides") renderSlides();
    if (view === "evidence") renderEvidence();
    if (view === "export") {
      updateExport();
      checkService();
    }
    persistState();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function nextView() {
    const current = VIEW_ORDER.indexOf(state.activeView);
    if (current === 0 && completion() < 100) {
      const missing = REQUIRED_FIELDS.map((name) => $(`[name="${name}"]`)).filter((field) => field && !field.value.trim());
      if (missing.length) {
        missing[0].focus();
        missing[0].reportValidity();
        showToast("请先补齐带星号的核心需求");
        return;
      }
    }
    if (current < VIEW_ORDER.length - 1) changeView(VIEW_ORDER[current + 1]);
  }

  function updateFiles(files) {
    selectedFiles = [...files];
    state.files = selectedFiles.map((file) => ({ name: file.name, size: file.size, type: file.type || "unknown" }));
    updateFilesLabel();
    persistState();
  }

  function updateFilesLabel() {
    const target = $("#selectedFiles");
    if (!state.files.length) {
      target.textContent = "尚未选择文件";
      return;
    }
    const total = state.files.reduce((sum, file) => sum + Number(file.size || 0), 0);
    target.textContent = `已选择 ${state.files.length} 个文件 · ${formatBytes(total)}`;
  }

  function formatBytes(bytes) {
    if (!bytes) return "0 KB";
    const units = ["B", "KB", "MB", "GB"];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
  }

  function makeSlide(overrides = {}) {
    return {
      id: `S${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`,
      title: "未命名页面",
      objective: "",
      takeaway: "",
      visual: "diagram",
      layout: "单一视觉主角",
      notes: "",
      duration: 60,
      ...overrides,
    };
  }

  function addSlide(overrides = {}) {
    const slide = makeSlide(overrides);
    state.slides.push(slide);
    state.selectedSlideId = slide.id;
    renderSlides();
    persistState();
  }

  function selectedSlide() {
    return state.slides.find((slide) => slide.id === state.selectedSlideId) || null;
  }

  function renderSlides() {
    if (state.slides.length && !selectedSlide()) state.selectedSlideId = state.slides[0].id;
    $("#slideList").innerHTML = state.slides
      .map((slide, index) => `<li class="${slide.id === state.selectedSlideId ? "is-active" : ""}">
        <button class="slide-select" type="button" data-slide-id="${escapeHtml(slide.id)}">
          <span class="slide-no">${String(index + 1).padStart(2, "0")}</span>
          <span class="slide-label"><strong>${escapeHtml(slide.title || "未命名页面")}</strong><small>${escapeHtml(visualLabel(slide.visual))}</small></span>
        </button></li>`)
      .join("");

    const slide = selectedSlide();
    if (!slide) {
      $("#slideEditor").innerHTML = `<div class="empty-state"><div class="empty-illustration" aria-hidden="true"><span></span><span></span><span></span></div><h2>从第一张页面开始</h2><p>载入示例，或添加一个页面并说明它要让听众理解什么。</p><button class="button button-outline" type="button" data-action="add-slide">添加页面</button></div>`;
    } else {
      const index = state.slides.findIndex((item) => item.id === slide.id);
      $("#slideEditor").innerHTML = `<div class="editor-heading"><div><small>第 ${index + 1} 页 · ${escapeHtml(slide.id)}</small><h2>这一页要完成什么？</h2></div><div class="editor-controls">
        <button class="icon-button" type="button" data-action="move-up" aria-label="向上移动" ${index === 0 ? "disabled" : ""}>↑</button>
        <button class="icon-button" type="button" data-action="move-down" aria-label="向下移动" ${index === state.slides.length - 1 ? "disabled" : ""}>↓</button>
        <button class="icon-button is-danger" type="button" data-action="delete-slide" aria-label="删除页面">×</button>
      </div></div>
      <div class="form-grid">
        <label class="field field-wide"><span>页面标题</span><input type="text" data-slide-field="title" value="${escapeHtml(slide.title)}" placeholder="使用结论式标题，避免只写章节名"></label>
        <label class="field"><span>页面任务</span><textarea rows="3" data-slide-field="objective" placeholder="观众看完这一页要理解什么？">${escapeHtml(slide.objective)}</textarea></label>
        <label class="field"><span>核心结论</span><textarea rows="3" data-slide-field="takeaway" placeholder="一句话写清最重要的信息">${escapeHtml(slide.takeaway)}</textarea></label>
        <label class="field"><span>预计讲述（秒）</span><input type="number" min="15" max="600" data-slide-field="duration" value="${Number(slide.duration) || 60}"></label>
        <label class="field"><span>版式说明</span><input type="text" data-slide-field="layout" value="${escapeHtml(slide.layout)}" placeholder="例如：左图右文，图片占 60%"></label>
        <label class="field field-wide"><span>讲者备注</span><textarea rows="3" data-slide-field="notes" placeholder="讲述要点、转场、时间提醒或引用说明">${escapeHtml(slide.notes)}</textarea></label>
      </div>
      <div class="visual-chooser"><h3>选择视觉主角</h3><p>图片数量服从信息需要。临床照片、病例图和设备图必须登记来源、授权与隐私状态。</p>
        <div class="visual-grid">${VISUALS.map(([value, icon, label]) => `<label class="visual-option"><input type="radio" name="slideVisual" value="${value}" ${slide.visual === value ? "checked" : ""}><span><i>${icon}</i>${label}</span></label>`).join("")}</div>
        <div class="visual-note">连续页面应避免重复同一种构图；只有比较任务或固定栏目可以有理由地复用版式。</div>
      </div>`;
    }
    updateSlideSummary();
  }

  function visualLabel(value) {
    return VISUALS.find(([key]) => key === value)?.[2] || "未选择";
  }

  function updateSlideSummary() {
    const kinds = new Set(state.slides.map((slide) => slide.visual).filter(Boolean));
    const seconds = state.slides.reduce((sum, slide) => sum + (Number(slide.duration) || 0), 0);
    $("#slideTotal").textContent = state.slides.length;
    $("#visualVariety").textContent = kinds.size;
    $("#estimatedMinutes").textContent = Math.max(0, Math.round(seconds / 60));
    let hint = "添加页面后，这里会检查版式变化与节奏。";
    if (state.slides.length) {
      const ideal = Math.max(2, Math.ceil(state.slides.length / 3));
      hint = kinds.size < ideal ? "视觉形式略单一，可把部分文字页改为流程、病例图或证据图表。" : "视觉类型具有变化；请继续检查每页是否只有一个主要信息焦点。";
    }
    $("#rhythmHint").textContent = hint;
  }

  function updateSlideField(target) {
    const slide = selectedSlide();
    if (!slide) return;
    const field = target.dataset.slideField;
    slide[field] = field === "duration" ? Number(target.value) : target.value;
    if (field === "title") renderSlideListOnly();
    updateSlideSummary();
    persistState();
  }

  function renderSlideListOnly() {
    const scroll = $("#slideList").scrollTop;
    const slide = selectedSlide();
    $("#slideList").innerHTML = state.slides.map((item, index) => `<li class="${item.id === state.selectedSlideId ? "is-active" : ""}"><button class="slide-select" type="button" data-slide-id="${escapeHtml(item.id)}"><span class="slide-no">${String(index + 1).padStart(2, "0")}</span><span class="slide-label"><strong>${escapeHtml(item.title || "未命名页面")}</strong><small>${escapeHtml(visualLabel(item.visual))}</small></span></button></li>`).join("");
    $("#slideList").scrollTop = scroll;
    if (slide) updateSlideSummary();
  }

  function moveSlide(direction) {
    const index = state.slides.findIndex((slide) => slide.id === state.selectedSlideId);
    const next = index + direction;
    if (index < 0 || next < 0 || next >= state.slides.length) return;
    [state.slides[index], state.slides[next]] = [state.slides[next], state.slides[index]];
    renderSlides();
    persistState();
  }

  function deleteSelectedSlide() {
    const index = state.slides.findIndex((slide) => slide.id === state.selectedSlideId);
    if (index < 0) return;
    state.slides.splice(index, 1);
    state.selectedSlideId = state.slides[Math.min(index, state.slides.length - 1)]?.id || null;
    renderSlides();
    persistState();
  }

  function renderEvidence() {
    const tbody = $("#claimTableBody");
    tbody.innerHTML = state.claims.map((claim) => `<tr>
      <td>${escapeHtml(claim.text)}</td><td>${escapeHtml(TYPE_LABELS[claim.type] || claim.type)}</td>
      <td>${escapeHtml(claim.source || "—")}</td><td><span class="status-pill status-${escapeHtml(claim.status)}">${escapeHtml(STATUS_LABELS[claim.status] || claim.status)}</span></td>
      <td><button class="row-delete" type="button" data-claim-delete="${escapeHtml(claim.id)}" aria-label="删除证据项">×</button></td></tr>`).join("");
    $("#claimEmpty").hidden = state.claims.length > 0;
    updateGates();
  }

  function addClaim() {
    const text = $("#claimText").value.trim();
    if (!text) {
      $("#claimText").focus();
      return;
    }
    state.claims.push({
      id: `C${Date.now().toString(36)}`,
      text,
      type: $("#claimType").value,
      status: $("#claimStatus").value,
      source: $("#claimSource").value.trim(),
    });
    $("#claimForm").reset();
    $("#claimDialog").close();
    renderEvidence();
    persistState();
  }

  function updateGates() {
    const pending = state.claims.filter((claim) => claim.status === "pending" || (claim.status === "verified" && !claim.source)).length;
    const evidencePass = state.claims.length > 0 && pending === 0;
    const privacyPass = (state.intake.privacy || []).includes("所有患者信息必须去标识化") && (state.intake.privacy || []).includes("临床图片必须记录授权状态");
    const hasImages = state.slides.some((slide) => ["photo", "case", "screenshot"].includes(slide.visual));
    const visualClaims = state.claims.filter((claim) => claim.type === "image");
    const visualPass = !hasImages || (visualClaims.length > 0 && visualClaims.every((claim) => claim.status === "verified" && claim.source));
    setGate("claims", evidencePass ? "pass" : pending ? "block" : "pending", evidencePass ? "已通过" : pending ? `${pending} 项未完成` : "待登记");
    setGate("privacy", privacyPass ? "pass" : "block", privacyPass ? "已设置" : "需补充");
    setGate("visuals", visualPass ? "pass" : "block", visualPass ? "已通过" : "需补充");
    setGate("render", "pending", "构建后执行");
    const blocked = pending + (privacyPass ? 0 : 1) + (visualPass ? 0 : 1) + (state.claims.length ? 0 : 1);
    $("#riskCount").textContent = blocked;
    $("#riskTitle").textContent = blocked ? "仍有项目会阻止最终导出" : "构建前门禁已满足";
    $("#riskMessage").textContent = blocked ? "完成来源定位、隐私设置与图片 provenance 后再进入最终构建。" : "构建后仍需完成回渲染检查与临床人工审核。";
    $("#gateBadge").textContent = blocked ? "尚未就绪" : "可进入构建";
    $("#gateBadge").className = `gate-badge ${blocked ? "is-pending" : "is-ready"}`;
    updateReadiness();
  }

  function setGate(name, status, label) {
    const item = $(`[data-gate="${name}"]`);
    if (!item) return;
    item.classList.toggle("is-pass", status === "pass");
    item.classList.toggle("is-block", status === "block");
    $("b", item).textContent = label;
  }

  function isReady() {
    const pending = state.claims.some((claim) => claim.status === "pending" || (claim.status === "verified" && !claim.source));
    return completion() === 100 && state.slides.length > 0 && state.claims.length > 0 && !pending;
  }

  function updateReadiness() {
    const ready = isReady();
    const panel = $("#readinessPanel");
    panel.classList.toggle("is-ready", ready);
    $("#readinessTitle").textContent = ready ? "可以创建本地项目" : "项目尚未达到构建条件";
    let text = "需求信息、页面计划和证据台账已齐备；构建后仍需回渲染与人工临床审核。";
    if (completion() < 100) text = "回到需求访谈，填写主题、受众、用途、目标和证据等级。";
    else if (!state.slides.length) text = "请先建立页面架构，并为每页选择一个主要视觉表达。";
    else if (!state.claims.length) text = "请登记关键医学主张、数字或图片来源。";
    else if (state.claims.some((claim) => claim.status === "pending")) text = "仍有待验证证据项；它们会阻止最终导出。";
    $("#readinessText").textContent = text;
    $("#createProjectButton").disabled = !(ready && state.service.online);
  }

  function projectName() {
    const base = (state.intake.topic || "医学演示项目")
      .replace(/[\\/:*?"<>|]/g, "")
      .replace(/\s+/g, "-")
      .slice(0, 40);
    return base || "医学演示项目";
  }

  function apiFields() {
    const intake = state.intake;
    return {
      topic: intake.topic || "",
      audience: intake.audience || "",
      baseline_knowledge: intake.baseline || "",
      learning_outcomes: lines(intake.outcomes),
      purpose: intake.purpose || "",
      delivery_context: intake.context || "",
      duration_minutes: Number(intake.duration) || 0,
      slide_count: Number(intake.slideCount) || 0,
      language: intake.language || "中文优先，专有名词保留英文",
      institution_context: [intake.institution, intake.department].filter(Boolean).join(" · "),
      scope: intake.acceptance || "",
      template_brand: [intake.brand, intake.style, intake.aspect, intake.termPolicy].filter(Boolean).join("；"),
      source_policy: intake.sourcePolicy || "",
      allow_public_web: intake.network === "允许公开网络",
      assets_available: intake.assets || [],
      patient_materials: (intake.assets || []).some((value) => ["病例资料", "临床照片", "影像 / 检验"].includes(value)),
      public_distribution: (intake.privacy || []).includes("项目材料不得离开本机") ? "仅限本机与授权人员" : "由用户确认发布范围",
      evidence_requirements: intake.evidenceLevel || "",
      notes_profile: intake.notesProfile || "",
      outputs: intake.outputs || [],
      acceptance_criteria: lines(intake.acceptance),
      existing_materials: [...lines(intake.sources), ...state.files.map((file) => file.name)],
    };
  }

  function lines(value) {
    return String(value || "").split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
  }

  function projectPayload() {
    return {
      projectName: projectName(),
      route: "clear",
      fields: apiFields(),
    };
  }

  function exportPayload() {
    return {
      format: "medical-presentation-architect-ui-project",
      version: 1,
      exported_at: new Date().toISOString(),
      project_name: projectName(),
      route: "clear",
      intake: apiFields(),
      slides: state.slides.map((slide, index) => ({
        id: `S${String(index + 1).padStart(2, "0")}`,
        title: slide.title,
        objective: slide.objective,
        takeaway: slide.takeaway,
        content_type: slide.visual,
        visual_type: visualLabel(slide.visual),
        layout: slide.layout,
        duration_seconds: Number(slide.duration) || 60,
        notes: slide.notes,
      })),
      claims: state.claims,
      files: state.files.map(({ name, size, type }) => ({ name, size, type })),
      privacy_notice: "所列文件仅为本地文件元数据，导出内容不包含文件正文。",
    };
  }

  function executionPrompt() {
    const intake = state.intake;
    const slideLines = state.slides.length
      ? state.slides.map((slide, index) => `${index + 1}. ${slide.title}｜任务：${slide.objective || "待完善"}｜视觉：${visualLabel(slide.visual)}｜结论：${slide.takeaway || "待完善"}`).join("\n")
      : "尚未制定；请在完成研究和叙事后提出页面计划供确认。";
    const claimLines = state.claims.length
      ? state.claims.map((claim) => `- [${STATUS_LABELS[claim.status]}] ${claim.text}${claim.source ? `｜来源：${claim.source}` : ""}`).join("\n")
      : "- 尚未登记；所有强医学结论、数字、设备参数与图片均需建立来源记录。";
    return `请使用 medical-presentation-architect Skill 继续这个本地项目。已完成的信息不得重复追问；只有真正影响后续工作的缺失项才可以询问。\n\n项目主题：${intake.topic || "未填写"}\n主要受众：${intake.audience || "未填写"}\n用途：${intake.purpose || "未填写"}\n讲述场景：${intake.context || "未填写"}\n时长与页数：${intake.duration || "?"} 分钟，约 ${intake.slideCount || "?"} 页\n学习目标：\n${lines(intake.outcomes).map((item) => `- ${item}`).join("\n") || "- 未填写"}\n语言：${intake.language || "中文优先"}\n术语规则：${intake.termPolicy || "流程与说明使用中文；设备和专有名词保留英文，必要时中英并列"}\n机构：${[intake.institution, intake.department].filter(Boolean).join(" · ") || "未指定"}\n模板与品牌：${[intake.brand, intake.style, intake.aspect].filter(Boolean).join("；") || "未指定"}\n联网政策：${intake.network || "未指定"}\n来源政策：${intake.sourcePolicy || "未指定"}\n证据等级：${intake.evidenceLevel || "未填写"}\n隐私要求：${(intake.privacy || []).join("；") || "未填写"}\n讲者备注：${intake.notesProfile || "未指定"}\n输出：${(intake.outputs || []).join("、") || "PPTX"}\n\n页面计划：\n${slideLines}\n\n证据台账：\n${claimLines}\n\n请按 research → narrative → content opportunity scan → slide architecture → visual planning → evidence planning → build → render → QA → revise → export 执行。每页只设一个视觉主角，图片数量由信息价值决定；禁止装饰性医疗图片和无法溯源的事实图。任何未证实主张保留 [VERIFY]，不得补写为事实。构建完成后必须回渲染逐页检查，并输出来源、图片 provenance、QA 报告和讲者备注。`;
  }

  function updateExport() {
    updateReadiness();
    $("#promptPreview").textContent = executionPrompt();
    const snapshot = [
      ["项目", state.intake.topic || "未填写"],
      ["受众", state.intake.audience || "未填写"],
      ["时长", `${state.intake.duration || "?"} 分钟`],
      ["页面", `${state.slides.length || 0} 页已规划`],
      ["证据", `${state.claims.length || 0} 项，${state.claims.filter((claim) => claim.status === "pending").length} 项待验证`],
      ["本地材料", `${state.files.length || 0} 个文件`],
      ["语言", state.intake.language || "中文优先"],
    ];
    $("#snapshotList").innerHTML = snapshot.map(([term, value]) => `<div><dt>${escapeHtml(term)}</dt><dd title="${escapeHtml(value)}">${escapeHtml(value)}</dd></div>`).join("");
  }

  async function checkService() {
    const dot = $("#serviceDot");
    try {
      const response = await fetch("/api/health", { headers: { Accept: "application/json" }, cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.service.online = true;
      dot.className = "service-dot is-online";
      $("#serviceStatus").textContent = "本地服务已连接";
      $("#serviceDetail").textContent = "配置与所选材料只会写入本机项目目录";
    } catch (_error) {
      state.service.online = false;
      dot.className = "service-dot is-offline";
      $("#serviceStatus").textContent = "当前为静态模式";
      $("#serviceDetail").textContent = "仍可下载配置和提示词；启动本地服务后可直接创建项目";
    }
    updateReadiness();
  }

  async function createLocalProject() {
    if (!state.service.online || !isReady()) return;
    const button = $("#createProjectButton");
    button.disabled = true;
    button.textContent = "正在创建…";
    try {
      const response = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(projectPayload()),
      });
      const result = await readApiResponse(response);
      const createdName = result.project?.name || result.project?.project_name || result.brief?.project_name || projectName();
      state.service.project = createdName;
      state.service.command = result.command || null;

      let uploaded = 0;
      if (state.files.length && !selectedFiles.length) {
        showToast("项目已创建；如需写入材料，请重新选择本地文件");
      } else {
        for (const file of selectedFiles) {
          const upload = await fetch(`/api/projects/${encodeURIComponent(createdName)}/files`, {
            method: "POST",
            headers: { "Content-Type": "application/octet-stream", "X-Filename": encodeURIComponent(file.name) },
            body: file,
          });
          await readApiResponse(upload);
          uploaded += 1;
        }
        showToast(`本地项目已创建${uploaded ? `，并写入 ${uploaded} 个文件` : ""}`);
      }
      if (result.command) $("#promptPreview").textContent = result.command;
      persistState(true);
      $("#serviceStatus").textContent = `本地项目已创建：${createdName}`;
      $("#serviceDetail").textContent = result.command ? "已返回 Kimi CLI 启动命令" : "可在本机项目目录继续工作";
    } catch (error) {
      showToast(`创建失败：${error.message}`);
    } finally {
      button.textContent = "创建本地项目";
      updateReadiness();
    }
  }

  async function readApiResponse(response) {
    let body = {};
    try { body = await response.json(); } catch (_error) { body = {}; }
    if (!response.ok) throw new Error(body.error || body.message || `本地服务返回 ${response.status}`);
    return body;
  }

  function download(name, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function copyPrompt() {
    const text = $("#promptPreview").textContent;
    try {
      await navigator.clipboard.writeText(text);
      showToast("已复制到剪贴板");
    } catch (_error) {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents($("#promptPreview"));
      selection.removeAllRanges();
      selection.addRange(range);
      showToast("已选中提示词，请按 Ctrl/Cmd + C 复制");
    }
  }

  function loadExample() {
    state = emptyState();
    state.intake = {
      topic: "ICU 中心静脉导管维护的规范化培训",
      audience: "护士",
      purpose: "业务学习 / 科室培训",
      outcomes: "识别导管维护中的感染风险\n按院内流程完成评估与操作\n发现异常时知道如何升级处理",
      baseline: "熟悉基础，需要突出更新与应用",
      context: "线下现场讲述",
      duration: "20",
      slideCount: "12",
      language: "中文优先，专有名词保留英文",
      aspect: "16:9 宽屏",
      termPolicy: "流程和说明使用中文；设备、产品、标准和专有名词保留英文，首次出现可中英并列",
      institution: "示例医院（虚构）",
      department: "重症医学科",
      brand: "沿用院内深青色；不使用真实院徽",
      style: "专业克制",
      sources: "示例院内 SOP（待替换）\n相关指南（待检索）",
      network: "允许公开网络",
      sourcePolicy: "优先指南与同行评议文献",
      assets: ["科室流程", "设备图片"],
      privacy: ["所有患者信息必须去标识化", "临床图片必须记录授权状态", "项目材料不得离开本机"],
      evidenceLevel: "业务培训级：核心结论需可靠来源",
      notesProfile: "标准：讲述要点、转场与引用",
      outputs: ["PPTX", "sources.json", "qa_report.md"],
      acceptance: "所有示例信息均明确标注；设备图片不得显示患者身份；最终内容须经科室审核",
    };
    state.slides = [
      makeSlide({ title: "为什么要规范维护", objective: "用一个临床场景建立问题紧迫性", takeaway: "维护动作会直接影响导管相关风险", visual: "photo", layout: "大图占 60%，右侧单句结论", duration: 70 }),
      makeSlide({ title: "风险发生在完整维护链条中", objective: "展示从评估到记录的关键环节", takeaway: "感染预防依赖连续、可执行的流程", visual: "flow", layout: "横向五步流程", duration: 100 }),
      makeSlide({ title: "操作前先做风险分层", objective: "帮助听众判断何时可以常规处理，何时升级", takeaway: "异常征象优先触发评估与上报", visual: "decision", layout: "二层决策树", duration: 120 }),
      makeSlide({ title: "关键操作点按证据与院内 SOP 对齐", objective: "并列展示证据要求和本地操作", takeaway: "外部证据需要转换为本地可执行步骤", visual: "comparison", layout: "左右对照，底部风险提示", duration: 110 }),
      makeSlide({ title: "交付前逐项确认", objective: "结束并提供行动清单", takeaway: "识别、操作、记录、升级形成闭环", visual: "table", layout: "四行检查表", duration: 80 }),
    ];
    state.selectedSlideId = state.slides[0].id;
    state.claims = [
      { id: "C_DEMO_1", text: "示例培训中的核心操作要求需与最新版指南及院内 SOP 对齐", type: "guideline", status: "pending", source: "待检索并定位到章节" },
      { id: "C_DEMO_2", text: "示例设备图片仅用于版式占位，不代表真实产品", type: "image", status: "synthetic", source: "本地合成占位图" },
    ];
    selectedFiles = [];
    fillIntakeForm();
    updateProgress();
    renderSlides();
    renderEvidence();
    persistState(true);
    showToast("已载入虚构示例；其中待验证内容不能直接用于临床");
  }

  function showToast(message) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 3200);
  }

  function resetProject() {
    if (!window.confirm("确定清空这个浏览器中保存的项目吗？下载的文件和已创建的本地项目不会被删除。")) return;
    localStorage.removeItem(STORAGE_KEY);
    state = emptyState();
    selectedFiles = [];
    $("#intakeForm").reset();
    $("#duration").value = "20";
    $("#slideCount").value = "18";
    readIntakeForm();
    fillIntakeForm();
    renderSlides();
    renderEvidence();
    updateProgress();
    changeView("intake");
    showToast("浏览器中的项目数据已清空");
  }

  function bindEvents() {
    $$(".nav-item").forEach((button) => button.addEventListener("click", () => changeView(button.dataset.view)));
    $("#nextButton").addEventListener("click", nextView);
    $("#saveButton").addEventListener("click", () => { readIntakeForm(); persistState(true); showToast("已保存到当前浏览器"); });
    $("#loadExampleButton").addEventListener("click", loadExample);
    $("#resetButton").addEventListener("click", resetProject);
    $("#addSlideButton").addEventListener("click", () => addSlide());
    $("#addClaimButton").addEventListener("click", () => $("#claimDialog").showModal());
    $("#saveClaimButton").addEventListener("click", (event) => { event.preventDefault(); addClaim(); });
    $("#copyPromptButton").addEventListener("click", copyPrompt);
    $("#downloadProjectButton").addEventListener("click", () => download("medical-presentation-project.json", `${JSON.stringify(exportPayload(), null, 2)}\n`, "application/json;charset=utf-8"));
    $("#downloadPromptButton").addEventListener("click", () => download("execution-prompt.md", `${executionPrompt()}\n`, "text/markdown;charset=utf-8"));
    $("#createProjectButton").addEventListener("click", createLocalProject);

    $("#intakeForm").addEventListener("input", () => { readIntakeForm(); updateProgress(); persistState(); });
    $("#intakeForm").addEventListener("change", () => { readIntakeForm(); updateProgress(); persistState(); });
    $("#materialFiles").addEventListener("change", (event) => updateFiles(event.target.files));

    const dropZone = $("#materialDropZone");
    ["dragenter", "dragover"].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.add("is-dragging"); }));
    ["dragleave", "drop"].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.remove("is-dragging"); }));
    dropZone.addEventListener("drop", (event) => updateFiles(event.dataTransfer.files));

    $("#slideList").addEventListener("click", (event) => {
      const button = event.target.closest("[data-slide-id]");
      if (!button) return;
      state.selectedSlideId = button.dataset.slideId;
      renderSlides();
      persistState();
    });
    $("#slideEditor").addEventListener("click", (event) => {
      const action = event.target.closest("[data-action]")?.dataset.action;
      if (action === "add-slide") addSlide();
      if (action === "move-up") moveSlide(-1);
      if (action === "move-down") moveSlide(1);
      if (action === "delete-slide") deleteSelectedSlide();
    });
    $("#slideEditor").addEventListener("input", (event) => {
      if (event.target.dataset.slideField) updateSlideField(event.target);
    });
    $("#slideEditor").addEventListener("change", (event) => {
      if (event.target.name !== "slideVisual") return;
      const slide = selectedSlide();
      if (!slide) return;
      slide.visual = event.target.value;
      renderSlides();
      persistState();
    });
    $("#claimTableBody").addEventListener("click", (event) => {
      const id = event.target.closest("[data-claim-delete]")?.dataset.claimDelete;
      if (!id) return;
      state.claims = state.claims.filter((claim) => claim.id !== id);
      renderEvidence();
      persistState();
    });
  }

  function init() {
    fillIntakeForm();
    readIntakeForm();
    bindEvents();
    updateProgress();
    renderSlides();
    renderEvidence();
    changeView(state.activeView || "intake");
    checkService();
    if (state.updatedAt) {
      const time = new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(state.updatedAt));
      $("#saveStatus").textContent = `已恢复 ${time} 的本地项目`;
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
