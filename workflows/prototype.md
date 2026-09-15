# prototype

正式生成整套之前，先运行 `python scripts/mpa.py prototype PROJECT --engine auto`。默认抽取封面、信息最复杂的正文页、风险最高的安全/证据页；也可用三个或更多 `--slide ID` 明确指定。命令生成 `prototype/prototype.pptx`、逐页 PNG、contact sheet 和 `prototype/approval.json`。原稿改造项目将参考页和样稿并排渲染。

检查：

1. 设计 DNA 是否保留，标题和正文是否保持可编辑。
2. 主视觉、临床截图和证据是否达到投影可读尺寸。
3. 页面角色是否真正不同，安全页是否形成明确警示层级。
4. 字号、留白、对齐、图注和来源是否适合实际场景。
5. 该视觉方向能否扩展到全套，而不依赖重复卡片或固定左右分栏。

用户已经委托自主设计时，可由模型完成原型选择并记录理由；用户明确要求先确认样稿时，等待确认后再扩展。只有在真实查看渲染图并获得相应确认后，才将 `prototype/approval.json` 的 reviewer、reviewed_at、status 和 findings 写实；不得自动填写“approved”。publication 模式会校验设计指纹、设计系统、slide plan 和 visual plan 的哈希，任何变化都会使原型批准失效。原型未通过时修改 design system 或 composer，不要直接生成整套后逐页打补丁。
