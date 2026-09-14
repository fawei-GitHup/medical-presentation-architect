# qa

先运行 qa 获得机器报告，再 review-template 创建当前指纹的待审记录。审核人逐页读取 PNG 与 PPTX 文本/notes：visual、medical、citations、privacy、notes 五项分别勾验，含每页发现及修复证据。reviewer 填真实姓名或可追责 ID，role 区分视觉审核与临床专家；按项目 evidence_standard 决定是否需专科专家签署。
每个 warning ID 写 resolution，不能把所有 warning 标成“忽略”。脚本验证指纹、逐页覆盖与状态，无法替代事实或临床判断。未完成保持 pending。
