# kimi-cli

仅维护宿主发现路径、调用语法与能力检测；不复制核心规则。详见 [使用说明](../../docs/kimi-cli.md)。安装器将本文件写为宿主说明，核心 SKILL.md 与资源原样复制。

Kimi 显示“Run this command / Approve”是宿主自身的命令权限提示，不代表 Skill 出错，Skill 不绕过该机制。执行时直接把独立项目目录传给 `mpa.py`，不要先切换到素材目录再运行 `init .`。交互访谈使用默认 `intake`；它以 `INTAKE_PENDING` 返回待确认问题且退出码为 0。只有批处理或 CI 才加 `--strict-exit`。

渲染时只运行 `python scripts/mpa.py doctor` 与 `python scripts/mpa.py render PROJECT --engine auto`。Windows 渲染器使用 requirements.txt 中的 pywin32/win32com；不要检查或安装 comtypes。不要用 grep、sed、shell 命令替换去反查 Python 源码；需要命令语法时运行 `python scripts/mpa.py render --help`。`doctor` 已明确报告实际 Python、PowerPoint COM、LibreOffice 和推荐引擎。

`review-template` 只会生成全部为 false 的空白审核表。必须先实际查看每张 PNG，再把已完成的检查和具体发现写入 review.json；不得因为“已看过”就跳过记录，也不得编造 reviewer 或 clinical_expert。`qa` 默认用 `QA_PENDING` 正常返回并在 `review_progress` 汇总待办；只有它显示 passed=true 后才能运行 prepare-delivery-notice、notice-sent delivery 和 export。

既有 PPTX 使用 `media-index`/`review-media` 分批审素材，不把原始大图 Base64 放入上下文；只有采用项才 `media-extract`。长任务用 `capture_run.py --scrub-images --heartbeat 60`，分支完成后用 `stage` 记录产物哈希，失败后用 `resume` 接续。build 后的 PPTX lint、`source-map-check`、`perceptual-preflight`、notes 与隐私/权利检查在依赖上可并行；Kimi 当前宿主只有明确提供并行 agent/任务能力时才同时派发，否则顺序运行并在 render 后汇合 contact sheet 和逐页视觉审核。
