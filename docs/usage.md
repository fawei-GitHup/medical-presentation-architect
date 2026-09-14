# 使用指南

需要 Python 3.10+。安装器仅用标准库；PPTX 构建/结构 QA/渲染需先安装 `requirements.txt`（Windows 会安装 PowerPoint COM 所需的 pywin32）。可选安装 `requirements-dev.txt` 做 lint。渲染使用 LibreOffice，或 Windows 上已安装且可由 COM 调用的 PowerPoint。中文幻灯片需有合法可用的 CJK 字体。

```sh
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python scripts/mpa.py doctor
python scripts/mpa.py init projects/my-talk --request "为团队准备一次关于主题的专业演示"
python scripts/mpa.py intake projects/my-talk
```

Kimi/Claude/Codex Skill 会先把 `intake/user_notice.md` 的理解、已知信息、缺项、暂定项和下一步实际展示给用户；再按回答更新 `intake/design_brief.json`，重编提示词，并重新展示更新后的通知。只在真正显示后才运行 `notice-sent --kind intake`。明确需求的用户不需多一轮重复确认；模糊需求先盘点资料与标签，再提出少量有针对性的选项；局部修订保持在指定范围。

```sh
python scripts/mpa.py notice-sent projects/my-talk --kind intake --channel codex_conversation
python scripts/mpa.py validate projects/my-talk
```

Intake 已完成且只要继续制作，就按顺序形成 `research.md`、`narrative.md`、`opportunities.json`、`slide-plan.json`、`visual-plan.json`、`sources.json`、`claims.json` 和 `assets.json`。具体契约见 schemas 与 workflows。资料检索、医学判断及病例隐私处理必须遵照当前 brief；来源或素材不够时停在相应门禁，不用一般知识冒充证据。完整 synthetic demo：`python scripts/mpa.py build examples/demo`。

```sh
python scripts/mpa.py validate projects/my-talk
python scripts/mpa.py build projects/my-talk
python scripts/mpa.py render projects/my-talk --engine libreoffice
python scripts/mpa.py qa projects/my-talk
python scripts/mpa.py review-template projects/my-talk
# 逐页检查所有 PNG、文字、speaker notes、证据和隐私；填写 review.json
python scripts/mpa.py qa projects/my-talk
```

QA 未通过人工审核时返回非零是预期行为。任何内容/素材/PPTX/渲染修改都会使审核指纹过期，须重新构建、回渲染并审核。审核通过后生成当前 brief 的交付通知，并先在会话中展示；再记录它已发出并导出：

```sh
python scripts/mpa.py prepare-delivery-notice projects/my-talk
# 将上一步生成的交付通知实际展示给用户后，才记录发送
python scripts/mpa.py notice-sent projects/my-talk --kind delivery --channel codex_conversation
python scripts/mpa.py export projects/my-talk
```

最终包含可编辑 PPTX、PDF、逐页 PNG 预览、计划、来源/主张/素材账本、交付通知、审核记录与 SHA-256 清单。导出默认不覆盖历史版本，请使用新的项目版本目录。

这个工具不是医学知识库，也没有后台自动检索或自动临床认证。机器检查覆盖 schema、引用关系、路径、边界、指纹和部分布局线索；临床专家、隐私负责人和制作者仍需实际审查证据与页面。
