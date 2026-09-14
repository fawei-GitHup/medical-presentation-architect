# 发布与维护

发布前运行 `python scripts/release_check.py`、`python -m unittest discover -s tests -v`、`ruff check scripts tests`。首次真实环境运行还需用 LibreOffice 或 PowerPoint 回渲染并人工审图，记录在本地 QA 中。
`python scripts/package.py --output ../medical-presentation-architect-v1.1.3.zip` 会根据明确允许目录构建 ZIP、同步 Codex Skill 副本，并把每个归档文件的 SHA-256 写入 `MANIFEST.sha256.json` 后逐项复验。不包含项目运行目录、图片/Office 文件/媒体、原始附件、`.git` 或临床运行产物；若检测到本地修改过生成副本的受管文件，会停止而不覆盖。

原创代码与文档按仓库中的 MIT LICENSE 提供；外部素材沿用各自许可，不能被 MIT 覆盖。原稿、病例、品牌标识与附件代码不随仓库发布。维护者发布前确认贡献者权利；许可文本不构成法律鉴定。

当前公开仓库为 [fawei-GitHup/medical-presentation-architect](https://github.com/fawei-GitHup/medical-presentation-architect)，当前版本 `v1.1.3`。下载和安装方式见 README；发布新版本的步骤见 [GitHub 发布指南](github.md)。
