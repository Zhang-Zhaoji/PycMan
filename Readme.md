# PycMan

面向 2026–2027 学年 Introduction to Computation 的迷宫逃生大作业原型。游戏由 Python 和 pygame-ce 实现；学生通过完成基础规则，并选做进阶功能，练习状态管理、数据结构与搜索。

## 任务结构

| 部分 | 内容 | 分值 |
| --- | --- | ---: |
| 基础功能 | S1 通行与移动、S2 拾取与计时、S3 碰撞与胜负、S4 随机幽灵、S5 键盘与转弯缓存；按顺序累计完成 | 60 |
| 进阶功能 | A 道具机制、B 更强的幽灵、C 变化中的迷宫；每类两题，每题 15 分，跨类选做，最高计 30 分 | 30 |
| 实验报告 | 复现场景、行为观察、实现思路与调试记录 | 10 |

逐题行为要求和观察方法见[学生任务说明](student-assignment.md)；环境配置、Git、测试工具与框架阅读指导见[预备知识](Background.md)。

基础阶段的 GUI 与测试使用 `src/tasks/basic/s1.py` 至 `s5.py` 中的同一份实现；未完成的函数保持可运行的初始行为。学生可在 `src/controller.py` 中添加策略状态字段。进阶任务文件位于 `src/tasks/advanced/`，场景输入存于 `assets/scenarios/advanced/`。教师参考规则保存在 `src/teacher_reference.py` 和 `src/teacher_advanced_reference.py`，生成的学生包不包含它们及教师演示入口。

基础规则通过 `src/rules.py` 的 `GameRules` 接入核心游戏。`Env`、`Agent`、`Player`、`Controller` 和 `Game` 在相应规则启用时直接调用学生接口；阶段规则由 `src/rules.py` 选择，地图和控制器由 `src/game.py` 组装。`src/main.py` 默认运行 S1，教师演示使用 `src/teacher_main.py`。

## 运行游戏

需要 Python 3.10+。在项目根目录安装游戏依赖并启动：

```bash
python -m pip install -r requirements.txt
python src/main.py --stage S1
```

不指定阶段时默认运行 S1；将 `S1` 改为 `S2`～`S5` 可运行相应的累计阶段。未完成任务时，窗口可以打开，但对应游戏行为尚未实现。conda、venv 与 uv 的配置方法见[预备知识](Background.md)。

其他常用入口：

```bash
python src/main.py --stage S1 --map assets/maps/basic/corridor.txt
python src/main.py --scenario a1_freeze
python src/teacher_main.py
python src/teacher_main.py --terminal
```

`--scenario` 载入进阶场景的地图和参数。`teacher_main.py` 是教师演示入口，不包含在学生发布包中。

方向键 / WASD 移动，空格 / P 暂停，R 重开，Esc 退出。

## 测试

在项目根目录运行统一测试入口，无需额外安装 pytest：

```bash
python -m tests framework
python -m tests S3
python -m tests all
python -m tests A1
python -m tests A1 B2
```

`framework` 只检查框架；`S3` 在框架通过后评分 S1～S3；`all` 检查全部基础阶段。进阶命令先检查框架与完整基础游戏，再对指定题目运行场景和集成测试；每题全部通过得 15 分，进阶总分封顶 30 分。A2+C2、B1+B2、C1+C2 同时选做时还运行组合检查。框架测试未通过时不运行学生测试。未完成的学生任务出现失败是正常的。

公开测试位于 `tests/test_framework.py`、`tests/test_basic.py` 与 `tests/test_advanced.py`，具体行为约定以[学生任务说明](student-assignment.md)为准。

## 生成学生发布包

教师和维护者首次打包时，先安装文档构建依赖：

```bash
python -m pip install -r scripts/requirements-docs.txt
python scripts/build_student_package.py
```

输出为 `dist/PycMan-student.zip`，包含学生任务文件、游戏框架、配置、地图、资源、公开测试，以及下列文档：

| 学生包中的文件 | 来源或用途 |
| --- | --- |
| `README.md`、`student-assignment.md` | 学生任务说明 |
| `README.pdf` | 学生任务说明的 PDF 版本 |
| `Background.md`、`Background.pdf` | 预备知识及其 PDF 版本 |
| `imgs/` | Markdown 文档使用的配图 |
| `AGENTS.md` | 使用 `StudentAgents.md` 中面向学生的 AI 助手规则 |

脚本按明确的文件清单打包，排除教师参考实现与教师演示入口。PDF 或压缩包生成失败时，保留已有的学生压缩包。

只生成 PDF，或跳过 PDF 打包：

```bash
python scripts/build_docs.py
python scripts/build_student_package.py --skip-pdf
```

单独生成的 PDF 位于 `dist/pdf/`。文档构建使用 `markdown-pdf`、Pygments 与 Pillow，样式由 `scripts/pdf.css` 管理；学生运行游戏无需安装这些构建依赖。更多选项与文件用途见 [scripts 使用说明](scripts/README.md)。

发布前检查两份 PDF 的排版与学生包内容。`dist/` 已由 Git 忽略，生成的 PDF 和压缩包不随源码提交；交付学生时使用生成的学生包。

## AI 助手使用

根目录 [AGENTS.md](StudentAgents.md) 约定：面向学生时，助手可以解释概念和讨论调试思路，不直接编写可提交的任务答案；教师明确要求的框架、文档和测试维护可以正常进行。这些规则不能作为识别 AI 使用或判定违规的证据。课程正式发布时应进一步明确学生的 AI 使用范围及过程材料要求。
