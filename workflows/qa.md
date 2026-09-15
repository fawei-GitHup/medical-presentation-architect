# qa

先运行 `design-preflight`，再运行 qa 获得机器报告，并用 review-template 创建当前指纹的待审记录。机器视觉检查覆盖 composition 连续重复、几何重复、字号与框面积、内容预算、截图可读面积、安全警示、可打印清单和 notes 时长。warning 是需要查看的证据，不自动证明页面失败或通过。

审核顺序：先查看 contact sheet，确认整套节奏和页面角色；再逐页读取完整 PNG、PPTX 文本与 notes。视觉审核检查 hierarchy、rhythm、readability、reference_match；临床审核检查 medical、recommendations、parameters、local_sop；引用、隐私和 notes 独立记录。视觉设计审核人与临床专家可以是不同的人，不能强迫一个 reviewer 同时承担两种专业责任。
每个 warning ID 写 resolution，不能把所有 warning 标成“忽略”。脚本验证指纹、逐页覆盖与状态，无法替代事实或临床判断。未完成保持 pending。
QA 未通过时不得运行 `prepare-delivery-notice` 或将 delivery notice 标记为 sent。模型可以完成技术与视觉检查记录，但不得伪造用户姓名、临床专家身份或批准结果。
