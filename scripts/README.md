# 学生包与 PDF 文档

## 文件用途

| 文件 | 用途 |
| --- | --- |
| `build_student_package.py` | 学生包入口，默认生成并收录两份 PDF |
| `build_docs.py` | PDF 生成逻辑，也可单独运行 |
| `pdf.css` | 两份讲义共用的排版样式 |
| `requirements-docs.txt` | 文档构建依赖，与游戏依赖分开管理 |

## 使用方法

首次使用时安装文档构建依赖（可以直接安装到 conda base 环境），然后在项目根目录运行：

```bash
python -m pip install -r scripts/requirements-docs.txt
python scripts/build_student_package.py
```

生成 `dist/PycMan-student.zip`。打包会将 `student-assignment.md` 编译为
`README.pdf`，将 `Background.md` 编译为 `Background.pdf`，放在压缩包根目录。
同时保留 Markdown 和 `imgs/` 配图；任务说明也保留原文件名，以便背景文档中的链接可用。
生成过程使用临时目录，编译或打包失败时不会覆盖已有压缩包。

只编译文档（输出至 `dist/pdf/`）：

```bash
python scripts/build_docs.py
python scripts/build_docs.py --output-dir dist/handouts
```

不需要 PDF 时，可显式跳过编译：

```bash
python scripts/build_student_package.py --skip-pdf
```

## 编译依赖

使用 [markdown-pdf](https://pypi.org/project/markdown-pdf/) 将 Markdown 经 HTML/CSS
排版为 PDF，使用 Pygments 为代码块添加语法高亮，使用 Pillow 临时转换 WebP 图片。依赖单独记录在
`scripts/requirements-docs.txt`；学生运行游戏只需原有的 `requirements.txt`。
不再需要 Pandoc、LaTeX 或 ImageMagick。

排版由 `pdf.css` 控制，包含标题、引用、表格、代码块和图片样式。生成的 PDF
有标题书签和页码；讲义之间的链接指向对应 PDF。中文使用渲染器提供的字体回退。
CSS 支持范围由 PyMuPDF 决定，并不等同于浏览器；修改样式后应检查实际 PDF。

编译不修改原 Markdown 或图片。发布前应打开两份 PDF 检查中文、表格、代码换行和配图；
渲染失败会显示源文件名及错误原因。
