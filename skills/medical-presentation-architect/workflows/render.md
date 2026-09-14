# render

先运行 `python scripts/mpa.py doctor`，再运行 `python scripts/mpa.py render PROJECT --engine auto`（默认）。Windows 检测到 Microsoft PowerPoint COM 与 pywin32 时优先使用 PowerPoint；否则寻找 LibreOffice。也可明确指定 `--engine powerpoint` 或 `--engine libreoffice`。Windows 路线不使用 comtypes，不自行拼接 grep/sed 诊断命令。转换在独立临时目录，失败/超时返回非零，不复用旧成功结果。PDF 由 PyMuPDF 渲染为 PNG，保存实际引擎、页数、PPTX 哈希与每张图哈希。
打开每张图检查：标题、字体、文字溢出、图表标注、裁切、相邻关系和页脚。缩略图只用来观察节奏，不能替代逐页大图。没有渲染引擎则停止最终导出并给安装路径。
