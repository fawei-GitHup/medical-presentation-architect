# 本地发布候选包验证

这是随本仓库源文件交付的可复现测试说明。版本更新后应重新运行，不应把上一次结果当作未来版本保证。

已运行/将随发布复跑的检查：

- 34 项单元与工作流测试，其中 20 项覆盖访谈/通知附录场景：`python -m unittest discover -s tests -v`
- Python lint：`ruff check scripts tests`
- 集中发布完整性检查：`python scripts/release_check.py`
- Windows PowerShell 安装/卸载脚本通过语法解析与实际 smoke test；通用安装器测试覆盖碰撞拒绝与保留用户修改；发布 ZIP 的文件清单与 SHA-256 校验通过。
- Kimi CLI 0.36.0 本地版本/help 检查；官方文档仅用于确认 Skills 与 `--skills-dir`，没有依赖未经核实的插件安装协议。
- 六页中文合成示例通过 Windows PowerPoint 回渲染为 PDF/逐页 PNG，手动检查全页构图；PowerPoint 原生流程/时间线、表格、图表和中文 notes 可读，机器 PPTX lint 通过。真实用户 PPTX 未公开，未打包。

限制：合成示例不含医学教学内容，不构成临床内容测试；不是所有 Office/LibreOffice 版本、字体、医院模板和宿主模型的兼容认证。Release check 验证文件/JSON schema/文档链接/安装流程/打包卫生，不会证明事实准确、图像有版权或临床审核真实发生。交付审核由具名审阅者对逐页记录负责，但本地记录并非数字签名或资质验证。
