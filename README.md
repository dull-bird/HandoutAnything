# HandoutAnything

把任何**本地材料**变成一份结构化、第一性原理的学习讲义：教材/书籍 PDF（数字版或扫描件）、本地视频与字幕、音频、Markdown/文本、论文（单篇或主题语料文件夹）。

> 网课平台下载（Coursera 等）不在本仓库范围内，请使用专用插件：
> [opencli-plugin-coursera](https://github.com/dull-bird/opencli-plugin-coursera) · [opencli-plugin-hf-learn](https://github.com/dull-bird/opencli-plugin-hf-learn)
> 下载得到的字幕/文本/视频可以作为本仓库的输入材料。

## 方法论

核心固化在 [`handout-anything/references/handout-methodology.md`](handout-anything/references/handout-methodology.md)：

- **适用性边界**：绿灯（教材/课程/论文）/ 黄灯（虚构作品用于研究、混合语料）/ 红灯（虚构作品欣赏目的等，拒做并建议替代产物）；判断必须显式写出。
- **知识量标定**：1 学习单元 = 60–90 分钟可消化（1 核心概念 + 3–5 要点 + 1 图/推导 + 2–4 题自测）；按学科分四类密度系数；按来源定策略（书不照章办事，混合语料先建问题树）；一周 7±2 单元。
- **枢纽概念识别**（一通百通判据）：被依赖度、衍生力、跨域复用、第一性深度。
- **讲解原则**：第一性原理（定义是被设计的）、费曼检验、推导替代背诵、客观对比、风险点视角。
- **图示规范**：定量自洽、由构造保证、记号有交代。
- **验证清单**：12 项交付前检查（编译 0 错误、无缺字形、逐页目检、覆盖检查、边界声明）。

## 安装

通过 [skills](https://www.npmjs.com/package/skills) CLI 一键安装到你的 agent（支持 Claude Code / Codex / Cursor / Kimi Code CLI 等 70+）：

```bash
npx skills add dull-bird/HandoutAnything
```

常用选项：`-g` 全局安装（跨项目可用）；`-a claude-code` 指定目标 agent；`--list` 只列出仓库内的 skill 不安装。

### Kimi Work（桌面端）

把下面这段提示词直接发给 Kimi Work，它会自己找到技能目录并完成安装：

```
帮我把 HandoutAnything 安装为你的本地技能：
1. 把 https://github.com/dull-bird/HandoutAnything 克隆（或下载 zip 解压）到一个临时目录；
2. 找到你自己的技能目录：你是 Kimi Code 内核，技能目录在你 home 下的 skills/（桌面端 home 通常在应用数据目录下的 kimi-code/home，如 macOS 的 ~/Library/Application Support/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home；CLI 则是 ~/.agents/skills）；不确定就先探测再向我确认；
3. 把仓库里的 handout-anything/ 目录整体复制到技能目录下（它是自包含的：SKILL.md + references/ + scripts/）；
4. 验证：确认技能目录下 handout-anything/SKILL.md 存在，读出 frontmatter 里的 name 和 description 报给我。
```

也可以在 Work 模式侧栏「技能」→ ➕ 手动上传 `handout-anything/` 文件夹。

也可以不用 CLI：直接 clone 本仓库，按下节提示词把 `handout-anything/SKILL.md` 交给 agent 即可。

## 使用

本仓库是一个 AI agent skill：把仓库交给支持工具调用的 agent，指向 `handout-anything/SKILL.md`，并给出本地材料路径即可。

```
阅读 handout-anything/SKILL.md 和 handout-anything/references/handout-methodology.md，
按照其中的流程把 <本地材料路径> 制作成一份讲义：
先做适用性判断与起飞前检查，拆出概念清单并与我确认单元规划，
然后按结构模板写作、编译、逐项执行验证清单。
```

## 目录结构

```
HandoutAnything/
├── handout-anything/            ← 自包含 agent skill 目录（可单独拷贝/上传）
│   ├── SKILL.md                 ← 输入路由 + 四步流程
│   ├── references/
│   │   ├── handout-methodology.md  ← 方法论模板（核心）
│   │   └── ...                     ← 其他参考资料
│   └── scripts/
│       ├── generate_handout.py  ← 字幕类材料 → LaTeX 讲义（manifest + content.json）
│       ├── lint_handout.py      ← 成品静默失败检查（直引号/省略号/引号配对/缺字形/编译错误）
│       ├── review_handout.py    ← 讲义结构审查（方法论 §5/§6 的硬指标，0 errors 才交付）
│       ├── vtt_keyframes.py     ← 从字幕语义推断关键帧时间戳
│       └── extract_frames.py    ← ffmpeg 按时间戳截帧（本地视频配图）
├── examples/                   ← 成品实例
│   ├── feynman-technique/      ← 视频字幕转录 → 费曼学习法讲义
│   ├── physics-handout/        ← 教材 PDF → 7 天物理讲义（LaTeX + TikZ）
│   ├── math-handout/           ← 教材 PDF → 9 天数学讲义（人教 A 版）
│   ├── naval-handout/          ← Naval 思想 → 主题讲义
│   ├── calculus-handout/       ← 大纲 + 开放资源 → 文科生 7 天微积分讲义
│   └── mathematical-thinking/  ← 课程字幕 → 数学思维讲义
├── docs/                       ← GitHub Pages 站点与 demo PDF
└── tests/
```

## 编译环境

讲义用 XeLaTeX 编译（ctexart + tcolorbox + TikZ）。实例目录内的 `texmf/` 自带兼容版宏包，编译时指定查找路径即可：

```bash
cd examples/physics-handout
TEXINPUTS="./texmf//:" xelatex physics-handout.tex && TEXINPUTS="./texmf//:" xelatex physics-handout.tex
```

编译后跑两道质量门（详见 `handout-anything/SKILL.md` 第 4 步）：

```bash
python3 handout-anything/scripts/lint_handout.py handout.tex handout.log   # 静默失败检查
python3 handout-anything/scripts/review_handout.py handout.tex             # 结构审查（0 errors 才交付）
```

## License

MIT
