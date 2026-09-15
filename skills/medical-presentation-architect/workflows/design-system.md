# design-system

在 architecture 后、visual planning 前生成 `design-system.json`。设计系统必须能被构建器执行，至少包含：

- `quality_target`: publication、engineering_draft 或 custom。
- 字体与字号层级、色彩 token、网格和内容区。
- 页面角色与至少四种正文构图家族；15 页以上的培训稿通常准备至少六种。
- 证据图、临床截图、产品图和氛围图的不同 fit/crop 规则。
- 高风险、安全警示和“科室确认项”的视觉与文字规则。
- 封面、章节页、评估页、参考页和结束页的专用处理。

如果有参考 PPT，将 design fingerprint 中的 preserve 项转为 token 或 composer 规则；repair 项进入 QA，禁止复制的问题不能写入设计系统。

设计系统不是模板图库。它定义视觉层级和决策规则，让不同页面保持一致，又能根据内容改变构图。

旧项目可运行 `python scripts/mpa.py normalize-design PROJECT`，把 role、composition、阅读顺序、字体角色、图片 fit、表格分带和安全语义写回 visual plan。该命令只补足设计语义和最低可读字号，不代替逐页重构或视觉审核。
