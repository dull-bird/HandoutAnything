# 文科生的微积分 · 七天讲义

一句话定位：面向文科背景读者（心理、经济、社会方向），用七天把微积分主干（函数 → 极限 → 导数 → 求导法则 → 导数应用 → 积分 → 基本定理）讲成"能用的工具"，每个概念都配文科场景的例子。

- **目标读者**：无高数基础的文科生；想看懂心理学/经济学定律里函数与统计背后的数学。
- **单元结构**：7 天（第 1–7 天），每天 = 核心问题 → 第一性讲解 → 易错点与失效边界 → 今日自测 → 本单元出处与拓展阅读；卷尾有参考文献（APA 风格、含 ISBN，在答案之前）、参考答案（给思路要点）、"7 句话讲给别人听"、资料注与后续学习指引。

## 参考资料清单（写作时查证过，与讲义内出处一致）

**输入材料**：

- `calculus-handout.md`——本讲义的原始 Markdown 稿（内容来源）。小型文本原件随讲义提交；大体积附件（原始 PDF/视频等）按约定放 `sources/` 保留本地不推送（方法论 §5.7），本讲义无此类附件。

**主教材**：《普林斯顿微积分读本》（Adrian Banner，人民邮电出版社中译本，修订版）。用到的章节：

| 讲义内容 | 对应章节 |
|---|---|
| 函数与增长性格（第 1 天） | 第 1 章 |
| 极限直觉与计算（第 2 天） | 第 3–4 章；连续与介值定理第 5 章 §5.1 |
| $e$ 的连续复利引入（第 2 天） | 第 9 章 §9.1–9.2 |
| 导数定义、可导与连续（第 3 天） | 第 6 章 §6.1；第 5 章 §5.2 |
| 和差/乘积/商/链式求导法则（第 4 天） | 第 6 章 §6.2（链式在 §6.2.5） |
| $e^x$、$\ln x$、$a^x$ 求导（第 4 天） | 第 9 章 §9.3 |
| 导数符号、单调性、驻点分类（第 5 天） | 第 11 章（§11.4–11.5） |
| 最优化应用（第 5 天） | 第 13 章 §13.1；画图流程第 12 章 |
| 定积分定义、原函数与 $+C$（第 6 天） | 第 15–16 章、第 17 章 |
| 换元积分（第 6 天） | 第 18 章 §18.1 |
| 微积分基本定理（第 7 天） | 第 17 章 |

**其他引用**（归属诚实声明见讲义卷尾"资料注"）：

- 韦伯–费希纳定律 $S=k\ln(I/I_0)$：Fechner《心理物理学纲要》（1860）。
- 史蒂文斯幂定律 $\psi=kI^a$：Stevens, *Psychophysical Review*（1957）。
- 对数效用与边际效用递减：Bernoulli《论赌博的度量》（1738）。
- 遗忘曲线 $R(t)=e^{-t/S}$：Woźniak 等（1995）的现代近似；艾宾浩斯 1885 年原始为对数型公式，当代复现见 Murre & Dros（2015）。
- "边际量即导数"的经济学表述：曼昆《经济学原理》第 2 章（讲义做了微积分化改写）。
- "概率 = 密度曲线下面积"：《普林斯顿概率论读本》连续型分布章节。

**配套资源**（讲义卷尾"配套资源"有逐天映射）：OpenStax *Calculus Volume 1*（Ch 1–5 对应第 1–7 天）、Paul's Online Math Notes（Calc I/II Practice Problems）、3Blue1Brown《微积分的本质》（第 1–2、4、7、8–9 集）、宋浩《微积分 I》（B 站 59 集）。

## 怎么重新编译与验证

```bash
cd examples/calculus-handout
xelatex -interaction=nonstopmode calculus-handout.tex   # 第一遍
xelatex -interaction=nonstopmode calculus-handout.tex   # 第二遍（交叉引用/目录）
python3 ../../handout-anything/scripts/lint_handout.py calculus-handout.tex calculus-handout.log
python3 ../../handout-anything/scripts/review_handout.py calculus-handout.tex
```

要求：编译 0 个 `!` 错误、无 Missing character、lint 通过、review 0 errors。出处排版组件（`\src` 行内标签、`reading` 盒、紫色系配色）定义在 tex 的 preamble，规范见 `../../handout-anything/references/citations.md`。

## 文件清单

| 文件 | 用途 |
|---|---|
| `calculus-handout.tex` | 讲义源文件（ctexart + tcolorbox + TikZ，含出处组件 preamble） |
| `calculus-handout.pdf` | 编译成品（23 页，含卷尾参考文献） |
| `calculus-handout.md` | 原始 Markdown 稿（输入材料） |
| `README.md` | 本交接说明 |

## 下一步可做的事

- 已知边界：讲义只覆盖一元微积分主干；严格 $\varepsilon$–$\delta$、多元微积分、泰勒展开明确留给后续（卷尾"后续学习指引"已声明）。
- 可延伸：把本讲义的出处机制当模板，推广到仓库其他 example 讲义（physics/math/naval/feynman 等目前还没有随单元出处盒）；或为第 8 天以后补"多元微积分入门"单元接回归推导。
- 注意事项：改 tex 后必须重编译两遍并同步提交 PDF；出处章节号若需增补，先查证再写（只列查证过的）。
