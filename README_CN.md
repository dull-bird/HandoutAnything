# HandoutAnything — 本地材料讲义生成器

把任何**本地材料**变成一份结构化、第一性原理的学习讲义：教材/书籍 PDF（数字版或扫描件）、本地视频与字幕、音频、Markdown/文本、论文（单篇或主题语料文件夹）。

> 网课平台下载（Coursera 等）不在本仓库范围内，请使用专用插件：
> [opencli-plugin-coursera](https://github.com/dull-bird/opencli-plugin-coursera) · [opencli-plugin-hf-learn](https://github.com/dull-bird/opencli-plugin-hf-learn)
> 下载得到的字幕/文本/视频可以作为本仓库的输入材料。

## 方法论亮点

核心固化在 [`references/handout-methodology.md`](references/handout-methodology.md)：

| 机制 | 一句话说明 |
|------|-----------|
| 适用性边界 | 不是什么材料都该做讲义：绿/黄/红灯判断，红灯给出替代产物 |
| 知识量标定 | 1 单元 = 60–90 分钟可消化；四类学科密度系数；一周 7±2 单元 |
| 来源策略 | 书不照章办事：按读者差集 + 枢纽概念重排，章可合可拆 |
| 枢纽概念 | 被依赖度 × 衍生力 × 跨域复用 × 第一性深度，打分排序 |
| 讲解原则 | 第一性原理 + 费曼检验 + 推导替代背诵 + 风险点视角 |
| 图示规范 | 定量自洽 · 由构造保证 · 记号有交代 |
| 验证清单 | 编译 0 错误、无缺字形、逐页目检、覆盖检查、边界声明 |

## 使用

本仓库是一个 AI agent skill：把仓库交给支持工具调用的 agent，指向 `handout-anything/SKILL.md`，并给出本地材料路径即可。

```
阅读 handout-anything/SKILL.md 和 references/handout-methodology.md，
按照其中的流程把 <本地材料路径> 制作成一份讲义：
先做适用性判断与起飞前检查，拆出概念清单并与我确认单元规划，
然后按结构模板写作、编译、逐项执行验证清单。
```

## 实例

- [`feynman-technique/`](feynman-technique/)：视频字幕转录 → 费曼学习法讲义
- [`physics-handout/`](physics-handout/)：教材 PDF → 7 天物理讲义（LaTeX + TikZ 矢量图）
- [`math-handout/`](math-handout/)：教材 PDF → 9 天数学讲义（人教 A 版，三角全覆盖）

在线 demo 与站点：<https://dull-bird.github.io/mooc2handout-skill/>

## License

MIT
