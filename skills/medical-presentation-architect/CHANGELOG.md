# Changelog

## 1.3.0 — 2026-09-15

新增 source design audit、可执行 design system、三页代表样稿与批准哈希、语义视觉计划、contact sheet、版式质量检查、publication 构建门禁，以及相互独立的视觉复核与临床复核。完整 PowerPoint 回渲染测试覆盖 25 页示例，设计预检无警告，行为测试 7 项通过。

本版本改用 **Medical Presentation Architect Non-Commercial License 1.0**：个人学习与非商业用途按 LICENSE 许可；收费服务、公司内部使用、商业产品、转售及其他营利用途必须事先取得版权所有者的单独书面授权。新增商业授权 Issue 模板、NOTICE 和第三方材料说明；已合法取得旧 MIT 版本的权利不追溯撤销。

## 1.1.3 — 2026-09-15

修复 QA 对 `render/draft.pdf` 相对路径的解析，使任何工作目录下运行结果一致。空白 review 不再展开成每页一条错误，`qa_report.json` 新增汇总、完整审核进度与下一步；交互式 `qa` 用 `QA_PENDING` 正常返回，CI 可用 `--strict-exit`。QA 未通过时禁止准备或登记交付通知；通知绑定当前 QA 指纹，旧通知不能放行新审核结果。新增 4 项回归测试并将测试总数增至 50。

## 1.1.2 — 2026-09-15

修复 Windows 渲染器探测：`doctor` 直接检查 PowerPoint COM 注册与当前 Python 的 pywin32，并输出实际可用引擎和推荐命令；`render` 默认改为 `--engine auto`，Windows 优先 PowerPoint，其他环境回退 LibreOffice。Kimi 适配器明确禁止误用未依赖的 comtypes 以及 Windows 下易失败的 grep/sed 源码诊断。新增 3 项渲染选择回归测试，并用本机 PowerPoint 16.0 完成真实 PDF/逐页 PNG 渲染验证。

## 1.1.1 — 2026-09-14

修复默认交付物字段的嵌套结构错误；将联网、隐私和交付物改为受 Schema 约束的结构化字段；字段更新先校验后落盘，失败不会污染 brief 或历史；观察值与模型推断不再绕过关键访谈确认。`init` 现在拒绝非空素材目录、用户主目录和磁盘根目录，并写入项目标记；交互式 `intake` 使用 `INTAKE_PENDING` 正常返回，`--strict-exit` 保留给自动化。同步更新 Kimi 指引、独立项目目录规则和 6 项回归测试。

## 1.1.0 — 2026-09-14

加入仅在本机运行的中文 PPT 设计界面、结构化访谈表单、项目初始化、资料上传和 Kimi 启动命令；首页增加 Windows/macOS/Linux 一行安装命令，bootstrap 自动下载 Release、核对 SHA-256、解压并安装。

## 1.0.0 — 2026-09-14

首次版本：访谈与缺项检测；统一研究/叙事/视觉/证据工作流；三宿主适配；JSON Schema 与跨文件关系检查；可编辑 PPTX 构建；PDF/PNG 回渲染；人工审核指纹与导出门禁；安全安装卸载与发布打包；合成示例、负向测试、原稿审计记录。
