# Changelog

## 1.1.2 — 2026-09-15

修复 Windows 渲染器探测：`doctor` 直接检查 PowerPoint COM 注册与当前 Python 的 pywin32，并输出实际可用引擎和推荐命令；`render` 默认改为 `--engine auto`，Windows 优先 PowerPoint，其他环境回退 LibreOffice。Kimi 适配器明确禁止误用未依赖的 comtypes 以及 Windows 下易失败的 grep/sed 源码诊断。新增 3 项渲染选择回归测试，并用本机 PowerPoint 16.0 完成真实 PDF/逐页 PNG 渲染验证。

## 1.1.1 — 2026-09-14

修复默认交付物字段的嵌套结构错误；将联网、隐私和交付物改为受 Schema 约束的结构化字段；字段更新先校验后落盘，失败不会污染 brief 或历史；观察值与模型推断不再绕过关键访谈确认。`init` 现在拒绝非空素材目录、用户主目录和磁盘根目录，并写入项目标记；交互式 `intake` 使用 `INTAKE_PENDING` 正常返回，`--strict-exit` 保留给自动化。同步更新 Kimi 指引、独立项目目录规则和 6 项回归测试。

## 1.1.0 — 2026-09-14

加入仅在本机运行的中文 PPT 设计界面、结构化访谈表单、项目初始化、资料上传和 Kimi 启动命令；首页增加 Windows/macOS/Linux 一行安装命令，bootstrap 自动下载 Release、核对 SHA-256、解压并安装。

## 1.0.0 — 2026-09-14

首次版本：访谈与缺项检测；统一研究/叙事/视觉/证据工作流；三宿主适配；JSON Schema 与跨文件关系检查；可编辑 PPTX 构建；PDF/PNG 回渲染；人工审核指纹与导出门禁；安全安装卸载与发布打包；合成示例、负向测试、原稿审计记录。
