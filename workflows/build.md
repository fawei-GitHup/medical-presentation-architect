# build

先 validate PROJECT，再运行 `python scripts/mpa.py design-preflight PROJECT`。读取 design-system 的 `quality_target`：

- `publication`：使用能执行页面角色、composition、style、图片裁切和专用 composer 的高保真构建器。基础 builder 只有在 prototype 已证明能够达到目标时才可继续。
- `engineering_draft`：基础 builder 可生成结构稿，文件和交付说明必须标明 wireframe。
- `custom`：允许宿主 presentations 工具、PowerPoint 或其他经过验证的引擎生成 `build/draft.pptx`，随后进入同一 render/QA。

构建器必须执行 `slide-plan.layout`、页面 role 与 visual-plan 的 composition/style。cover、workflow swimlane、clinical screenshot、safety、printable assessment 使用专用 composer。图片保持比例并执行 fit/crop；设备对照按对象尺度统一。

PPT notes 先写简洁 delivery notes，再写来源摘要；完整 claim/source 审计保留在 ledger，避免重复堆入讲稿。不得直接创建 final。
