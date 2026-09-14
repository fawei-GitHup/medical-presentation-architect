# qa

先运行 qa 获得机器报告，再 review-template 创建当前指纹的待审记录。`qa_report.json` 用 `summary`、`review_progress` 与 `next_actions` 汇总进度，不把每页未勾选重复成几十条错误。审核人逐页读取 PNG 与 PPTX 文本/notes：visual、medical、citations、privacy、notes 五项分别勾验，含每页发现及修复证据。reviewer 填真实姓名或可追责 ID，role 区分视觉审核与临床专家；按项目 evidence_standard 决定是否需专科专家签署。
每个 warning ID 写 resolution，不能把所有 warning 标成“忽略”。脚本验证指纹、逐页覆盖与状态，无法替代事实或临床判断。未完成保持 pending。
QA 未通过时不得运行 `prepare-delivery-notice` 或将 delivery notice 标记为 sent。模型可以完成技术与视觉检查记录，但不得伪造用户姓名、临床专家身份或批准结果。
