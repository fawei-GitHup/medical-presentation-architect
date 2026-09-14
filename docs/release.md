# 发布与维护

发布前运行 `python scripts/release_check.py`、`python -m unittest discover -s tests -v`、`ruff check scripts tests`。首次真实环境运行还需用 LibreOffice 或 PowerPoint 回渲染并人工审图，记录在本地 QA 中。
`python scripts/package.py --output ../medical-presentation-architect-1.0.0.zip` 会根据明确允许目录构建 ZIP、同步 Codex Skill 副本，并把每个归档文件的 SHA-256 写入 `MANIFEST.sha256.json` 后逐项复验。不包含项目运行目录、图片/Office 文件/媒体、原始附件、`.git` 或临床运行产物；若检测到本地修改过生成副本的受管文件，会停止而不覆盖。

建议将原创代码与文档使用 MIT（已提供 LICENSE）；外部素材沿用各自许可，不能被 MIT 覆盖。原稿、病例、品牌标识与附件代码不随仓库发布。维护者发布前确认贡献者权利；提供的是许可建议与文本，不是法律鉴定。

仓库计划名 medical-presentation-architect。远端未创建前 README 下载 URL 是计划地址，发布成功后才能使用；不要声称已上线。若没有合适仓库且可见性未指定，先交本地包，最后询问 public/private。远端发布命令见 docs/github.md。
