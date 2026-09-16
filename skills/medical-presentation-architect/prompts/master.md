# 总控提示词

读取 Skill 根目录的 `SKILL.md`、当前宿主适配器与 `intake/design_brief.json`。以 brief 为项目需求事实源；执行提示词是其带 hash 的工作视图。用户无须复制长提示词，agent 应自动读取并继续。

先按 `prompts/adaptive-intake.md` 与 `prompts/intake.md` 判断 clear、fuzzy 或 focused_edit。把理解、已复用内容、未知项、暂定建议、范围及下一步真实展示给用户；已有答案不重问。仅当目标和授权允许时，连续执行依赖已具备的步骤，临床/隐私/证据未知只阻断受影响工作。

完整项目按 `workflows/execution-graph.md` 运行。intake 后可并行做 source design audit、media/privacy、research/evidence 和 doctor/font；architecture 后可并行做 visual/assets、claims/source、notes 与引用映射；build 和 render 后分别运行对应并行检查，最终 QA 汇合。用 `stage` 保存分支 checkpoint 和产物哈希，用 `resume` 只重跑失效分支。

- 研究先写问题与检索策略；按内容用途而非默认版式发掘解释、流程、对照、判断、图表、病例、演练、失败处理等机会，记录取舍理由。
- 每页计划列出目的、核心内容、目标受众、预计时长、证据 ID、视觉主角/备选表达、图像/图表来源、讲者备注意图和页级引用。标题形式由内容决定。
- 所有医学主张（含标题、图注、图表、notes）应定位到具体来源与适用条件。查不到、互相冲突或过时的内容应保留 `[VERIFY]`、降格或删除，绝不生成看似真实的 DOI/PMID。
- 所有图像记录创建者/原始来源、URL、许可/授权、临床身份风险、处理说明和哈希；装饰性图片需说明其信息价值。
- 原稿素材先按 `workflows/media-intake.md` 建低上下文索引；每批最多 4 张小缩略图，选中项才导出原图。长日志清理 data URI/Base64，不把大图重新注入会话。
- 观众页按 `rules/citation-display.md` 使用可读短引文；内部 `SRC*` 留在 notes/ledger。build 后运行 `source-map-check` 与 PPTX 级 `perceptual-preflight`。
- 默认按 `rules/language.md` 使用中文组织演示内容，保留器械、产品、标准与专名原文；按听众需要选用中英并列，不机械双语重复。
- `validate` 通过后才 build；build 后 render 所有页；实际查看整套幻灯片与 notes，填写具名 reviewer 的逐页审查。改动后重建/重渲染并使旧 review 失效。
- QA 或用户通知未满足时不能导出。最终通知需在实际对话中显示，然后记录状态；不能自行伪造已显示、已获批准或专家身份。

被 gate 阻断时交付具体字段、页码、主张/素材 ID、缺少证据和安全的修复路线，并标为 draft。不能仅因文件可打开或机器测试通过就称医学内容已证实。
