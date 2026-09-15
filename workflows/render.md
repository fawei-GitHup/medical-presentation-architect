# render

先运行 `python scripts/mpa.py doctor`，再运行 `python scripts/mpa.py render PROJECT --engine auto`（默认）。Windows 检测到 Microsoft PowerPoint COM 与 pywin32 时优先使用 PowerPoint；否则寻找 LibreOffice。也可明确指定 `--engine powerpoint` 或 `--engine libreoffice`。Windows 路线不使用 comtypes。

转换在独立临时目录，失败/超时返回非零，不复用旧成功结果。PDF 由 PyMuPDF 渲染为逐页 PNG，同时生成 `render/contact-sheet.png`。先查看 contact sheet 判断章节节奏、重复布局和密度变化，再以完整尺寸查看标题过长、截图细节、图注、裁切和风险页。
打开每张图检查：标题、字体、文字溢出、图表标注、裁切、相邻关系和页脚。缩略图只用来观察节奏，不能替代逐页大图。没有渲染引擎则停止最终导出并给安装路径。
