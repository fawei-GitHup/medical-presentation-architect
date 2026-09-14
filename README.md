# medical-presentation-architect

Medical PPT Suite · 1.1.0 · Kimi CLI 优先 · 中文界面与文档

可安装的医学演示规划 Skill 与工程工具：先访谈，后研究与叙事，选择恰当的内容和视觉形式，逐主张溯源，构建可编辑 PPTX，再回渲染、审核和导出。核心规则统一，Kimi / Claude Code / Codex 适配独立。

**公开仓库：** [fawei-GitHup/medical-presentation-architect](https://github.com/fawei-GitHup/medical-presentation-architect)。固定版本安装示例使用 `v1.1.0`。测试范围与限制见 [测试报告](docs/validation.md)。这不是医学知识库，不自动认证临床准确性。

## 一行安装

需要 Python 3.10+。命令会下载 `v1.1.0` Release、核对 SHA-256、解压并安装到 Kimi 的本地 skills 目录。

**Windows PowerShell：**

```powershell
irm https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.1.0/bootstrap.ps1 | iex
```

**macOS / Linux 终端：**

```sh
curl -fsSL https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.1.0/bootstrap.sh | sh
```

安装后，在 Kimi 输入：

```text
/skill:medical-presentation-architect 我要制作一份医学PPT，请先访谈，已知内容不要重复问。
```

## 打开本地中文界面

界面只监听本机，表单和上传资料写入本地 `projects`，不会自动上传服务器。

Windows：

```powershell
python "$env:USERPROFILE\.kimi-code\skills\medical-presentation-architect\scripts\ui_server.py"
```

macOS / Linux：

```sh
python3 "$HOME/.kimi-code/skills/medical-presentation-architect/scripts/ui_server.py"
```

浏览器会自动打开。填写访谈表单、添加本地资料、生成项目后，界面会给出可复制的 Kimi 启动命令。已有信息不会重复询问。

## 其他安装方式

克隆仓库安装：

可克隆并一键安装：

```sh
git clone https://github.com/fawei-GitHup/medical-presentation-architect.git
cd medical-presentation-architect
python scripts/install.py install --agent kimi
```

手工下载固定版本 ZIP：

```sh
curl --fail --location https://github.com/fawei-GitHup/medical-presentation-architect/archive/refs/tags/v1.1.0.zip -o mpa.zip
unzip mpa.zip
sh medical-presentation-architect-1.1.0/install.sh --agent kimi
```

```powershell
Invoke-WebRequest 'https://github.com/fawei-GitHup/medical-presentation-architect/archive/refs/tags/v1.1.0.zip' -OutFile mpa.zip
Expand-Archive -LiteralPath mpa.zip -DestinationPath mpa-download
& ./mpa-download/medical-presentation-architect-1.1.0/install.ps1 -Agent kimi
```

要先查看脚本再执行，可下载 [bootstrap.ps1](bootstrap.ps1) 或 [bootstrap.sh](bootstrap.sh)，检查内容后在本机运行。Claude Code、Codex、自定义安装目录和卸载方式见 [完整安装说明](docs/usage.md)。

|宿主|默认 skills 父目录|自定义|
|---|---|---|
|Kimi|`$KIMI_CODE_HOME/skills` 或 `~/.kimi-code/skills`|`--target` + `kimi --skills-dir`|
|Claude Code|`~/.claude/skills`|项目 `.claude/skills`|
|Codex|`~/.agents/skills`|项目 `.agents/skills`|
|generic|必须传 `--target`|任意用户拥有目录|

Windows 的 `~` 对应用户配置目录；PowerShell 示例用 `$env:USERPROFILE`，macOS/Linux 用 `$HOME`。安装目录最终加 `/medical-presentation-architect`。不会覆盖既有同名目录；卸载只删除安装清单内未修改文件，保留用户修改及额外文件。更新请先卸载或安装到新目录，不静默覆盖。

```sh
python scripts/install.py uninstall --agent kimi
```

## 使用与能力

[完整使用流程](docs/usage.md) · [Claude Code](docs/claude-code.md) · [Codex](docs/codex.md) · [发布说明](docs/release.md) · [输入材料审计](docs/input-audit.md) · [审计规则映射](docs/audit-integration.md)

- intake 收集受众、目的、时长/页数、机构/品牌、资料/联网、病例/隐私、证据标准、讲稿和输出；语言默认中文优先，专业术语和设备专名保留原文，可按听众需要中英并列。
- research → narrative → content opportunity scan → architecture → visual → evidence → build → render → QA → revise → export。
- 照片、病例/设备图、截图、示意图以及原生流程图、决策树、时间线、图表、表格、数字卡。数量与版式按教学任务决定。
- source/claim/asset 三份 ledger，页级引用和 speaker notes；失败门禁与内容哈希防止陈旧审核继续放行。
- scripts 可实际运行，schemas/tests/demo 随包。默认生成器是基线引擎，复杂医院模板需要单独适配并重新审核。

**通用本地 skills 安装器 + 可配置目标目录**是本项目安装方案。已验证 Kimi 的 Skills 与 `--skills-dir` 文档，不把自定义 manifest 描述为官方 Kimi 插件协议。未进行真实患者数据处理或多模型质量认证；不以自动检查替代医学/隐私/视觉判断。

Windows PowerPoint COM 渲染由 [pywin32](https://pypi.org/project/pywin32/) 提供；`requirements.txt` 按平台安装依赖。用户仍须安装 Microsoft PowerPoint，或改用 LibreOffice 渲染。

原创部分建议 MIT；外部医学图、论文图、品牌与病例各自授权。详见 LICENSE 与 [贡献指南](CONTRIBUTING.md)。
