# source-design-audit

现有 PPT 不只提供文字和图片，也提供可复用的设计事实。逐页渲染后同时建立 content inventory 与 design fingerprint，避免把“视觉更成熟的原稿”改成通用白底模板。

记录幻灯片尺寸、字体、主色与风险色、标题区、内容网格、页脚、图片处理方式、页面角色和构图家族。为 cover、section、content、evidence、workflow、safety、assessment、closing 选择代表页。明确三类结论：`preserve` 保留的设计 DNA，`repair` 需要修复的问题，`do_not_copy` 不得复制的缺陷。

观察值保持 `observed`。设计指纹说明参考事实，不代表用户已确认偏好。原稿存在多个版本时，说明每个版本适合继承的部分，并选定一个视觉基线。

运行 `python scripts/mpa.py design-audit PROJECT REFERENCE.pptx` 生成可复核的 `design-fingerprint.json`，再由设计者补充版本差异、保留项和修复项。原稿页与改稿页需要建立 mapping，便于 prototype 和最终 QA 做并排比较。
