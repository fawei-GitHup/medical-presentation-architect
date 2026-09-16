# 发布与维护

## v1.4.1 发布说明

本补丁补齐“可恢复并行”的工程语义：阶段状态使用跨进程文件锁、锁内重读和原子替换，避免两个 ready 分支互相覆盖。`resume.ready` 表示依赖上可并行，而不是内置模型调度器；只有宿主明确提供并行 agent/任务能力时才同时派发，否则顺序运行并保留 checkpoint/resume 收益。

`source-map-check` 新增表格和嵌套组合形状文字读取；`perceptual-preflight` 将组合形状文字计入密度/参考页判断，并对组变换要求渲染复核。`media-index` 在解压前限制单成员、媒体总量与异常压缩比。新增 3 项行为测试，全套 67 项；真实 26 页成品的 source-map 与感知检查在本机一次测量合计约 0.51 秒。

发布前运行 `python scripts/release_check.py`、`python -m unittest discover -s tests -v`、`ruff check scripts tests`。首次真实环境运行还需用 LibreOffice 或 PowerPoint 回渲染并人工审图，记录在本地 QA 中。
`python scripts/package.py --output ../medical-presentation-architect-v1.4.1.zip` 会根据明确允许目录构建 ZIP、同步 Codex Skill 副本，并把每个归档文件的 SHA-256 写入 `MANIFEST.sha256.json` 后逐项复验。不包含项目运行目录、图片/Office 文件/媒体、原始附件、`.git` 或临床运行产物；若检测到本地修改过生成副本的受管文件，会停止而不覆盖。

1.3.0 起按仓库中的 Medical Presentation Architect Non-Commercial License 1.0 提供；任何商业使用必须先取得版权所有者的单独书面授权。外部素材沿用各自许可，不能被本项目许可证覆盖。原稿、病例、品牌标识与附件代码不随仓库发布。维护者发布前确认贡献者权利；许可文本应由专业法律顾问按实际经营主体和适用法复核。

当前公开仓库为 [fawei-GitHup/medical-presentation-architect](https://github.com/fawei-GitHup/medical-presentation-architect)，当前版本 `v1.4.1`。下载和安装方式见 README；发布新版本的步骤见 [GitHub 发布指南](github.md)。
