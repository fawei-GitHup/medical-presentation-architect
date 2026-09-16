# 发布与维护

## v1.4.0 发布说明

本版聚焦“低上下文执行 + 可恢复并行 + 最终 PPTX 感知质量”：新增 PPTX 媒体去重索引、最多 4 张一批的 contact sheet、选中素材按哈希提取、阶段 checkpoint/resume、定点修订 before 记录、长任务图片日志清理与心跳。构建器改用可读作者—年份页脚，流程节点按泳道宽度均分、connector 锚到节点边界。

新增 `source-map-check` 和 `perceptual-preflight` 两个发布门禁。真实 26 页 Kimi 成品回归不仅复现了第 4 页 `SRC*` 泄漏、0.021 英寸节点重叠和连接线遮挡，也发现第 12 页同类几何缺陷、其他流程页中心连线遮挡以及第 26 页参考文献字号风险。新增 10 项行为测试，全部 64 项回归通过。

发布前运行 `python scripts/release_check.py`、`python -m unittest discover -s tests -v`、`ruff check scripts tests`。首次真实环境运行还需用 LibreOffice 或 PowerPoint 回渲染并人工审图，记录在本地 QA 中。
1.4.0 发布还需把 `source-map-check` 与 `perceptual-preflight` 跑在真实 PPTX 上，确认内部 ID 泄漏、引用映射、节点间距与 connector 遮挡检查实际命中；不要用完整耗时生成代替这些确定性回归。
`python scripts/package.py --output ../medical-presentation-architect-v1.4.0.zip` 会根据明确允许目录构建 ZIP、同步 Codex Skill 副本，并把每个归档文件的 SHA-256 写入 `MANIFEST.sha256.json` 后逐项复验。不包含项目运行目录、图片/Office 文件/媒体、原始附件、`.git` 或临床运行产物；若检测到本地修改过生成副本的受管文件，会停止而不覆盖。

1.3.0 起按仓库中的 Medical Presentation Architect Non-Commercial License 1.0 提供；任何商业使用必须先取得版权所有者的单独书面授权。外部素材沿用各自许可，不能被本项目许可证覆盖。原稿、病例、品牌标识与附件代码不随仓库发布。维护者发布前确认贡献者权利；许可文本应由专业法律顾问按实际经营主体和适用法复核。

当前公开仓库为 [fawei-GitHup/medical-presentation-architect](https://github.com/fawei-GitHup/medical-presentation-architect)，当前版本 `v1.4.0`。下载和安装方式见 README；发布新版本的步骤见 [GitHub 发布指南](github.md)。
