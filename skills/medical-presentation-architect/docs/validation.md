# 发布验证

这是随本仓库源文件交付的可复现测试说明。版本更新后应重新运行，不应把上一次结果当作未来版本保证。

已运行/将随发布复跑的检查：

- 67 项单元与工作流测试；1.4.0 的 10 项覆盖媒体去重/缩略图/按需提取、引用泄漏与末页映射、流程节点重叠/connector 缺失与遮挡、孤字行/低信息卡/过密参考页、checkpoint 失效传播、Base64 清理、日志凭据脱敏和新构建器可读引文；1.4.1 再覆盖跨进程 checkpoint 不丢更新、组合/表格引用、超大压缩成员拒绝：`python -m unittest discover -s tests -v`
- Python lint：`ruff check scripts tests`
- 集中发布完整性检查：`python scripts/release_check.py`
- Windows PowerShell 安装/卸载脚本通过语法解析与实际 smoke test；通用安装器测试覆盖碰撞拒绝与保留用户修改；发布 ZIP 的文件清单与 SHA-256 校验通过。
- Kimi CLI 0.36.0 本地版本/help 检查；官方文档仅用于确认 Skills 与 `--skills-dir`，没有依赖未经核实的插件安装协议。
- 六页公开合成示例通过 Windows PowerPoint 回渲染为 PDF/逐页 PNG。另以 25 页医学培训测试稿验证完整节奏、语义构图、contact sheet、三页样稿选择和 publication 门禁。1.4.0/1.4.1 对 26 页真实 Kimi 成品做确定性回归：source-map-check 捕获正文 `SRC*` 泄漏与不完整映射；perceptual-preflight 捕获第 4、12 页节点重叠/过小 gap、多个流程页中心连线遮挡及第 26 页参考文献字号风险。1.4.1 本机一次计时分别为 0.227 秒与 0.283 秒；这是机器检查耗时，不是完整生成提速结论。真实用户 PPTX 与测试素材未公开、未打包。
- 本地界面后端只监听回环地址，拒绝目录穿越和不支持的上传类型；发布前以真实 HTTP 请求复验表单建项、资料上传和 Kimi 命令生成。

限制：合成示例不含医学教学内容，不构成临床内容测试；不是所有 Office/LibreOffice/Keynote 版本、字体、医院模板和宿主模型的兼容认证。依赖图只声明可并行性，实际并发取决于宿主能力。静态检查不能完整还原组合形状变换、SmartArt、动态 connector 重路由、PowerPoint 字体替换和真实文本换行；这些仍须回渲染人工审图。Release check 验证文件/JSON schema/文档链接/安装流程/打包卫生，不会证明事实准确、图像有版权或临床审核真实发生。交付审核由具名审阅者对逐页记录负责，但本地记录并非数字签名或资质验证。
