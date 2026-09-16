# medical-presentation-architect

Medical PPT Suite · 1.4.0 · Kimi CLI 优先 · 中文界面与文档

可安装的医学演示规划 Skill 与工程工具：先访谈，后研究与叙事，选择恰当的内容和视觉形式，逐主张溯源，构建可编辑 PPTX，再回渲染、审核和导出。核心规则统一，Kimi / Claude Code / Codex 适配独立。

**公开仓库：** [fawei-GitHup/medical-presentation-architect](https://github.com/fawei-GitHup/medical-presentation-architect)。固定版本安装示例使用 `v1.4.0`。测试范围与限制见 [测试报告](docs/validation.md)。这不是医学知识库，不自动认证临床准确性。

本项目为 **source-available** 软件。个人学习、非商业研究和非商业教学可按 [LICENSE](LICENSE) 使用；收费服务、公司内部使用、商业产品或其他营利用途，必须事先取得版权所有者的单独书面许可。申请方式见 [商业授权说明](COMMERCIAL-LICENSING.md)。

## 一行安装

需要 Python 3.10+。命令会下载 `v1.4.0` Release、核对 SHA-256、解压并安装到 Kimi 的本地 skills 目录。

**Windows PowerShell：**

```powershell
irm https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.4.0/bootstrap.ps1 | iex
```

**macOS / Linux 终端：**

```sh
curl -fsSL https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.4.0/bootstrap.sh | sh
```

安装后，在 Kimi 输入：

```text
/skill:medical-presentation-architect 我要制作一份医学PPT，请先访谈，已知内容不要重复问。
```

为每次任务指定一个新的独立项目目录，例如 `./mpa-projects/my-talk`。原始 PPT、病例、脚本和旧渲染图所在目录只用于读取，不要在其中执行 `init .`。Kimi 出现命令审批界面属于其正常权限保护；访谈缺项会显示 `INTAKE_PENDING`，由 Skill 继续提问。

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
curl --fail --location https://github.com/fawei-GitHup/medical-presentation-architect/archive/refs/tags/v1.4.0.zip -o mpa.zip
unzip mpa.zip
sh medical-presentation-architect-1.4.0/install.sh --agent kimi
```

```powershell
Invoke-WebRequest 'https://github.com/fawei-GitHup/medical-presentation-architect/archive/refs/tags/v1.4.0.zip' -OutFile mpa.zip
Expand-Archive -LiteralPath mpa.zip -DestinationPath mpa-download
& ./mpa-download/medical-presentation-architect-1.4.0/install.ps1 -Agent kimi
```

要先查看脚本再执行，可下载 [bootstrap.ps1](bootstrap.ps1) 或 [bootstrap.sh](bootstrap.sh)，检查内容后在本机运行。Claude Code、Codex、自定义安装目录和卸载方式见 [完整安装说明](docs/usage.md)。

|宿主|默认 skills 父目录|自定义|
|---|---|---|
|Kimi|`$KIMI_CODE_HOME/skills` 或 `~/.kimi-code/skills`|`--target` + `kimi --skills-dir`|
|Claude Code|`~/.claude/skills`|项目 `.claude/skills`|
|Codex|`~/.agents/skills`|项目 `.agents/skills`|
|generic|必须传 `--target`|任意用户拥有目录|

Windows 的 `~` 对应用户配置目录；PowerShell 示例用 `$env:USERPROFILE`，macOS/Linux 用 `$HOME`。安装目录最终加 `/medical-presentation-architect`。首次安装不会覆盖既有同名目录；受管安装可运行 `python scripts/install.py update --agent codex`（或相应宿主）安全更新。安装器发现本地改动时会停止，卸载也只删除清单内未修改文件。

```sh
python scripts/install.py uninstall --agent kimi
```

## 使用与能力

[完整使用流程](docs/usage.md) · [Claude Code](docs/claude-code.md) · [Codex](docs/codex.md) · [发布说明](docs/release.md) · [输入材料审计](docs/input-audit.md) · [审计规则映射](docs/audit-integration.md)

- intake 收集受众、目的、时长/页数、机构/品牌、资料/联网、病例/隐私、证据标准、讲稿和输出；语言默认中文优先，专业术语和设备专名保留原文，可按听众需要中英并列。
- intake 后按依赖图并行推进 research、design audit、media/privacy 与环境检查；关键路径经 architecture → prototype → build → render → QA join gate → revise/export，并用哈希 checkpoint 恢复。
- 照片、病例/设备图、截图、示意图以及原生流程图、决策树、时间线、图表、表格、数字卡。数量与版式按教学任务决定。
- source/claim/asset 三份 ledger，页级引用和 speaker notes；失败门禁与内容哈希防止陈旧审核继续放行。
- media-index 只生成小缩略图和每批最多 4 张的 contact sheet，选中项才导出原图；长任务日志会清理 data URI/Base64 并输出空闲心跳。
- 观众页使用作者—年份短引文；source-map-check 阻止内部 `SRC*` 泄漏并验证末页映射。PPTX 级 perceptual-preflight 检查文字密度、低信息卡片、参考字号、节点重叠与 connector 遮挡。
- source design audit 把参考稿转成可执行设计指纹，区分保留、修复和禁止复制的特征。
- 三页代表样稿先验证标题页、典型内容页和复杂页；正式发布绑定样稿批准记录与内容哈希。
- scripts 可实际运行，schemas/tests/demo 随包。正式稿默认走 publication 或经过样稿验证的 custom 引擎；工程草稿不能冒充最终成品。

**通用本地 skills 安装器 + 可配置目标目录**是本项目安装方案。已验证 Kimi 的 Skills 与 `--skills-dir` 文档，不把自定义 manifest 描述为官方 Kimi 插件协议。未进行真实患者数据处理或多模型质量认证；不以自动检查替代医学/隐私/视觉判断。

Windows PowerPoint COM 渲染由 [pywin32](https://pypi.org/project/pywin32/) 提供，不使用 `comtypes`；`python scripts/mpa.py render PROJECT --engine auto` 会在 Windows 优先选择 PowerPoint，其他系统寻找 LibreOffice。`requirements.txt` 按平台安装依赖。

## 许可、商业使用与第三方材料

1.3.0 起采用自定义的 **Medical Presentation Architect Non-Commercial License 1.0**。商业使用必须先取得书面授权；提交 Issue 仅表示申请，并不自动获得许可。详见 [LICENSE](LICENSE)、[商业授权说明](COMMERCIAL-LICENSING.md) 与 [第三方材料说明](THIRD-PARTY-NOTICES.md)。

版本 1.2.0 曾在本地候选包中使用 MIT 文本；已经合法取得旧 MIT 副本的权利不能通过后续换证追溯撤销。仓库中的病例、患者资料、参考 PPT、下载图片和字体仍须分别核验授权，不因本项目许可证而获得使用权。
