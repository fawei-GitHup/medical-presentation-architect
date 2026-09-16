# revise

将 QA 缺陷按阻断/重要/可优化排序。结构化 findings 必须含 `slide_id`、`issue`、`evidence`、`requested_change`、`severity`；运行 `revise PROJECT --findings findings.json` 保存目标页 before 证据，只使目标页与依赖阶段审核失效。修正文案与 ledger、视觉计划或素材，不直接篡改审核报告；然后 rebuild、rerender，复查目标页与整套 contact sheet，并保存 after 证据。

同一问题连续两轮无法修复时报告根因和可选方案，不无限盲试；仍未过门禁可交付标 draft 的内部评审材料，不能宣称 final。脚本不能把“已生成修订计划”误报为“已完成语义修改或人工复核”。
