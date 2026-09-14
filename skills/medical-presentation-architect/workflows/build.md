# build

先 validate PROJECT。默认工程参考构建器基于 python-pptx，支持原生文本、表格、图表、流程/树/时间线与授权图片，图片保持比例。复杂图/模板继承可换自定义构建器，但输出须为 build/draft.pptx 并重新 gate；不得直接创建 final。
运行 python scripts/mpa.py build PROJECT。输出 notes.md 与 draft，所有 slide ID、claim 与 source 写入 notes；不自动下载第三方图片。用户模板若不能可靠继承需显式说明，不能声称已经匹配。
