# visual-planning

先读取 design-fingerprint.json、design-system.json 和已通过的 prototype。按 rules/visual-policy.md 选择表达，在 visual-plan.json 为每页记录 role、composition、visual_anchor、reading_order、reference_slides 与 elements。`layout` 和 `composition` 必须是构建器可执行的选择，不能只是自由文本标签。

使用 text/image/table/chart/flow/timeline/decision/number/checklist；所有元素有 x/y/w/h、z、purpose、alt、claim_ids，并按需要记录 style、image、table_style 与 safety。image 引用 assets.json 的 ID；证据图优先 contain，氛围图才可 cover/crop；产品对照使用 object_scale_group 统一对象视觉尺度。原生图表保留 values/categories、轴、单位与统计出处；流程/树保留 nodes、有标签 edges、责任主体和停止条件。

每页先写 visual_anchor，说明听众第一眼应看到什么。选择构图时查看前两页，第三页不得机械重复同一 composition。以英寸描述位置，构建前运行 `design-preflight` 检查比例、密度、字号、截图可读面积、风险层级和 notes 时长。
