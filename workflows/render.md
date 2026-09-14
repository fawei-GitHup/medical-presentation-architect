# render

运行 python scripts/mpa.py render PROJECT --engine libreoffice（默认）或 Windows 上 --engine powerpoint。LibreOffice 要求 soffice 可执行文件，PowerPoint 要求本机安装及 COM 注册。转换在独立临时目录，失败/超时返回非零，不复用旧成功结果。PDF 由 PyMuPDF 渲染为 PNG，保存页数、PPTX 哈希与每张图哈希。
打开每张图检查：标题、字体、文字溢出、图表标注、裁切、相邻关系和页脚。缩略图只用来观察节奏，不能替代逐页大图。没有渲染引擎则停止最终导出并给安装路径。
