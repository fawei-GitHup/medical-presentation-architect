# export

完成具名逐页 review 并通过 QA 后，先运行 `python scripts/mpa.py prepare-delivery-notice PROJECT`，在对话中实际展示生成的 `intake/delivery_notice.md`，再运行 `python scripts/mpa.py notice-sent PROJECT --kind delivery --channel <实际渠道>`。QA 未通过时前两步都会被阻止。只有绑定当前 QA 指纹和 brief 版本的交付通知登记为已展示，`export` 才能再次执行 QA 并在新的 final 目录复制 PPTX/PDF/预览、来源记录、slide/visual plans、notes、通知、QA 与 review。默认不会覆盖已有 final；另存版本后再执行。公开分发前按 privacy 复查：原始素材、病例、内部路径、token、原始附件不能进入公共 Git 或 ZIP。导出包含 SHA256SUMS.json 可核对结果。
