# kimi-cli

仅维护宿主发现路径、调用语法与能力检测；不复制核心规则。详见 [使用说明](../../docs/kimi-cli.md)。安装器将本文件写为宿主说明，核心 SKILL.md 与资源原样复制。

Kimi 显示“Run this command / Approve”是宿主自身的命令权限提示，不代表 Skill 出错，Skill 不绕过该机制。执行时直接把独立项目目录传给 `mpa.py`，不要先切换到素材目录再运行 `init .`。交互访谈使用默认 `intake`；它以 `INTAKE_PENDING` 返回待确认问题且退出码为 0。只有批处理或 CI 才加 `--strict-exit`。
