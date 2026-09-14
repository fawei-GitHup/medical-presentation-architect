# Kimi CLI

## 一行安装

Windows PowerShell：

```powershell
irm https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.1.0/bootstrap.ps1 | iex
```

macOS / Linux：

```sh
curl -fsSL https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.1.0/bootstrap.sh | sh
```

安装后启动 Kimi，并输入 `/skill:medical-presentation-architect` 加上你的主题。若希望先在界面中整理需求，运行安装目录下的 `scripts/ui_server.py`；浏览器表单会生成项目和可复制的 Kimi 启动命令。

优先使用通用本地 skills 安装器，本仓库的 plugin/manifest.json 是自身元数据，不冒充 Kimi 官方插件 manifest。不依赖未经验证的 kimi plugin install。

已核对 2026-09-14 官方 [Skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html) 和 [命令](https://www.kimi.com/code/docs/en/kimi-code-cli/reference/kimi-command.html)。本机 `kimi --version` 为 0.36.0；`kimi --help` 实测支持 `--skills-dir`、`-p`。文档描述用户目录为 `$KIMI_CODE_HOME/skills`（默认 `~/.kimi-code/skills`），也扫描 `~/.agents/skills`；旧版差异以本机 help 为准。

克隆后在仓库根目录：

```sh
python scripts/install.py install --agent kimi --target ./local-skills
kimi --skills-dir ./local-skills
```

在交互会话中输入：

```text
/skill:medical-presentation-architect 我要制作口腔科护士业务学习 PPT，中文，20 分钟，约 18 页。请先访谈，已知内容不要重问。病例暂不使用，是否联网请先问我。项目放在 ./projects/dental-training。
```

若 slash command 未出现，重启会话并使用自然语言：“读取 local-skills/medical-presentation-architect/SKILL.md，按其中流程先做访谈”。显式 `--skills-dir` 会替代自动发现目录；如果仍需其他技能，按本机支持情况重复传入目录。

项目已完整访谈后才适合批处理：

```sh
kimi --skills-dir ./local-skills -p '使用 medical-presentation-architect，继续 ./projects/dental-training；先验证 intake，如有缺项只输出问题清单，不臆测答案。'
```

默认不启用 --auto/--yolo，保留宿主本身的权限机制；技能规则不修改模型选择。没有联网工具或视觉工具时分别停在证据或审图门禁。CLI 在本地运行仍可能将提示词送到云端；仅使用机构允许入模的材料。
