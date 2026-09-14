# Claude Code 适配

依据 [官方 Skills 文档](https://code.claude.com/docs/en/skills)，用户 skills 位于 ~/.claude/skills，项目级为 .claude/skills。
安装：`python scripts/install.py install --agent claude`。重启 Claude Code，在对话输入 `/medical-presentation-architect` 并描述任务；若未被识别，直接要求读取安装目录 SKILL.md。
adapters/claude-code/README.md 只管理发现和调用；所有医学、证据、QA 原则来自核心。无需额外 Anthropic 付费文档 Skill。插件宿主可使用仓库的 .claude-plugin/plugin.json；本包测试覆盖目录安装，不声称已测试所有插件市场客户端。
