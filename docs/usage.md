# 使用指南

需要 Python 3.10+。安装器仅用标准库；PPTX 构建/结构 QA/渲染需先安装 `requirements.txt`（Windows 会安装 PowerPoint COM 所需的 pywin32）。可选安装 `requirements-dev.txt` 做 lint。渲染使用 LibreOffice，或 Windows 上已安装且可由 COM 调用的 PowerPoint。中文幻灯片需有合法可用的 CJK 字体。

## 最快安装

Windows PowerShell：

```powershell
irm https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.3.0/bootstrap.ps1 | iex
```

macOS / Linux：

```sh
curl -fsSL https://raw.githubusercontent.com/fawei-GitHup/medical-presentation-architect/v1.3.0/bootstrap.sh | sh
```

脚本固定下载 `v1.3.0` Release，并在安装前核对随 Release 发布的 SHA-256。默认安装给 Kimi；可在执行前设置 `MPA_AGENT=claude`、`MPA_AGENT=codex`，或用 `MPA_TARGET` 指定 skills 父目录。Windows 使用 `$env:MPA_AGENT` / `$env:MPA_TARGET`。

## 本地中文界面

从仓库目录运行 `python scripts/ui_server.py`，或在 Windows 双击/运行 `./start-ui.ps1`，macOS/Linux 运行 `sh start-ui.sh`。默认地址为 `http://127.0.0.1:8765/`，并自动打开浏览器。

界面完成结构化访谈、创建项目、保存本地资料并生成 Kimi 启动命令。服务默认拒绝非本机监听；上传限制为单文件 50 MB，只接受演示文稿、PDF、常见 Office 文件、图片和文本。病例及机构资料仍须先去标识化。停止终端进程即可关闭界面。

自定义工作区：

```powershell
.\start-ui.ps1 -Workspace 'D:\Medical-PPT-Projects' -Port 8765
```

```sh
sh start-ui.sh --workspace "$HOME/Medical-PPT-Projects" --port 8765
```

## 命令行工作流

```sh
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python scripts/mpa.py doctor
python scripts/mpa.py init projects/my-talk --request "为团队准备一次关于主题的专业演示"
python scripts/mpa.py intake projects/my-talk
```

`projects/my-talk` 必须是不存在或为空的新目录。不要在装有原始 PPT、病例图片、Python 脚本或旧渲染图的目录中运行 `init .`；原素材目录只读，项目目录单独保存访谈、计划、构建和审核产物。`intake` 在仍需回答时显示 `INTAKE_PENDING` 并正常退出，供 Kimi 继续提问；自动化测试若需要用退出码阻断，请运行 `python scripts/mpa.py intake projects/my-talk --strict-exit`。

结构字段须以 JSON 写入，例如 `network_policy={"allow_public_web":true,"local_only":false}`、`privacy_constraints={"processing":"仅在本机处理","case_materials":"不使用病例材料","public_distribution":"仅科室内部"}`。脚本会先验证整份 brief，再一次性保存；输入错误时原 brief 和历史记录保持不变。

Kimi/Claude/Codex Skill 会先把 `intake/user_notice.md` 的理解、已知信息、缺项、暂定项和下一步实际展示给用户；再按回答更新 `intake/design_brief.json`，重编提示词，并重新展示更新后的通知。只在真正显示后才运行 `notice-sent --kind intake`。明确需求的用户不需多一轮重复确认；模糊需求先盘点资料与标签，再提出少量有针对性的选项；局部修订保持在指定范围。

```sh
python scripts/mpa.py notice-sent projects/my-talk --kind intake --channel codex_conversation
python scripts/mpa.py validate projects/my-talk
```

Intake 已完成且只要继续制作，就按顺序形成 `research.md`、`narrative.md`、`opportunities.json`、`slide-plan.json`、`visual-plan.json`、`sources.json`、`claims.json` 和 `assets.json`。具体契约见 schemas 与 workflows。资料检索、医学判断及病例隐私处理必须遵照当前 brief；来源或素材不够时停在相应门禁，不用一般知识冒充证据。完整 synthetic demo：`python scripts/mpa.py build examples/demo`。

```sh
python scripts/mpa.py validate projects/my-talk
python scripts/mpa.py build projects/my-talk
python scripts/mpa.py doctor
python scripts/mpa.py render projects/my-talk --engine auto
python scripts/mpa.py qa projects/my-talk
python scripts/mpa.py review-template projects/my-talk
# 逐页检查所有 PNG、文字、speaker notes、证据和隐私；填写 review.json
python scripts/mpa.py qa projects/my-talk
```

交互式 `qa` 未通过时会输出 `QA_PENDING` 并正常返回，详细进度在 `qa_report.json` 的 `summary`、`review_progress` 和 `next_actions`。CI 若需非零退出码可加 `--strict-exit`。`review-template` 仅生成空白表，实际逐页审阅后必须填写；QA 通过前，脚本拒绝生成或登记交付通知，也不会执行导出。

QA 未通过人工审核时返回非零是预期行为。任何内容/素材/PPTX/渲染修改都会使审核指纹过期，须重新构建、回渲染并审核。审核通过后生成当前 brief 的交付通知，并先在会话中展示；再记录它已发出并导出：

```sh
python scripts/mpa.py prepare-delivery-notice projects/my-talk
# 将上一步生成的交付通知实际展示给用户后，才记录发送
python scripts/mpa.py notice-sent projects/my-talk --kind delivery --channel codex_conversation
python scripts/mpa.py export projects/my-talk
```

最终包含可编辑 PPTX、PDF、逐页 PNG 预览、计划、来源/主张/素材账本、交付通知、审核记录与 SHA-256 清单。导出默认不覆盖历史版本，请使用新的项目版本目录。

这个工具不是医学知识库，也没有后台自动检索或自动临床认证。机器检查覆盖 schema、引用关系、路径、边界、指纹和部分布局线索；临床专家、隐私负责人和制作者仍需实际审查证据与页面。
