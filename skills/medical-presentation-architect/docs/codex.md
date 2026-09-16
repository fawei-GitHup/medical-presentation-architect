# Codex 适配

依据 [官方 Skills 文档](https://developers.openai.com/codex/skills) 和本机 plugin-creator schema，提供 `.codex-plugin/plugin.json` 与生成的 `skills/medical-presentation-architect`。
使用通用目录安装：`python scripts/install.py install --agent codex`。目标为 `~/.agents/skills/medical-presentation-architect`；在 Codex 输入 `$medical-presentation-architect` 并描述任务。若你的版本采用不同路径，用 `--target` 指定 skills 父目录。
不自动修改个人 marketplace、AGENTS.md、模型或 MCP 配置。核心不依赖 Codex 私有工具；adapter 不引入 Kimi 的 slash 语法。
