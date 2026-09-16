# media-intake

对既有 PPTX 先运行 `media-index`，本地解析 ZIP 与 slide relationships，按 SHA-256 去重并记录尺寸、字节数、出现页和用途候选。索引只写小缩略图与每批最多 4 张的 contact sheet；不得把原始高分辨率图片或 data URI/Base64 写进主上下文、普通日志或公开包。

运行 `review-media --batch-size 4`，逐批填写用途、隐私、权利/许可和是否采用。`intake/media_review.json` 是可恢复记录；未完成批次保持 pending。患者或机构素材必须先按 `rules/privacy.md` 处理，联网许可不等于允许上传图片。

只有选定素材才运行 `media-extract --select ID`。导出后核对 SHA-256 与索引一致；原 PPTX 和未选素材保持只读。索引结论只是候选，不能把“看似图库图片”自动写成已授权。
