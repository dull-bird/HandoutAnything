# 代码块排版规范

讲义中出现代码时（可运行示例、命令、伪代码），统一按本规范排版。设计目标：**与现有盒子体系视觉一致、编译零额外依赖（不需要 `--shell-escape`）、跨平台（含 MiKTeX on-the-fly）可复现**。

## 1. 技术选型：listings（经 tcolorbox），不用 minted

- **用 `tcolorbox` 的 `listings` 库**（`tcblisting`）：tcolorbox 已是讲义的基础依赖，`listings` 是 TeX Live/MiKTeX 核心包，纯 TeX 实现语法高亮。
- **不用 `minted`**：它依赖外部 Pygments + `--shell-escape`，破坏"xelatex 两遍即出"的编译约定，对 Windows/MiKTeX 用户是多一个故障点。语法高亮够用即可，不追求 IDE 级配色。

## 2. Preamble 片段（原样粘贴，放在 tcolorbox 之后）

```latex
\tcbuselibrary{listings,skins}   % skins 提供 enhanced 皮肤（左侧竖条需要）

% 代码块配色（沿用讲义既有调色板，只新增两个色）
\definecolor{codebg}{HTML}{f7f7f8}      % 背景：比正文纸面略灰
\definecolor{codecomment}{HTML}{5f6368} % 注释：中性灰

\lstdefinestyle{handout}{
  basicstyle=\small\ttfamily,           % 比正文小一档的等宽
  keywordstyle=\color{accent}\bfseries, % 关键字 = 主题蓝加粗
  stringstyle=\color{calcframe},        % 字符串 = 绿
  commentstyle=\color{codecomment}\itshape, % 注释 = 灰斜体
  numberstyle=\tiny\color{codecomment}, % 行号（开启时）= 灰小字
  breaklines=true,                      % 长行折行，禁止溢出
  keepspaces=true,
  showstringspaces=false, upquote=true,
}

% 代码块环境（语言为必选参数，强制声明）：
%   \begin{codeblock}{Python} ... \end{codeblock}
% 可选标题条：\begin{codeblock}[title={文件名.py}]{Python}
\newtcblisting{codeblock}[2][]{
  enhanced, listing only,
  listing options={style=handout,language=#2},
  colback=codebg, colframe=codebg, boxrule=0pt, arc=2pt,
  borderline west={2pt}{0pt}{accent},   % 左侧 2pt 主题蓝竖条
  left=8pt, right=8pt, top=5pt, bottom=5pt,
  fonttitle=\small\bfseries, coltitle=darkgray,
  colbacktitle=codebg, toptitle=4pt,
  #1}

% 行内代码：\code{variable_name}（\detokenize 转义特殊字符，_ # % 可直接写）
\newcommand{\code}[1]{\colorbox{codebg}{\texttt{\detokenize{#1}}}}
```

注意事项（都是实测踩过的坑）：

- `listing style=` 这个 tcolorbox 键在部分版本下静默不生效，**必须**用 `listing options={style=handout,...}`。
- `borderline west` 只在 `enhanced` 皮肤下渲染，缺了 `enhanced` 竖条直接消失（不报错）。
- 不要加 `columns=fullflexible`：它会让 `breaklines` 失效，长行溢出盒子。

## 3. 使用规则

1. **必须声明语言**：`\begin{codeblock}{Python}`。语言是必选参数，写不出语言说明这段代码不该进 codeblock；纯文本/命令输出用 `\begin{codeblock}{}`（空语言）。
2. **代码块内只写 ASCII**：标识符、字符串、注释一律英文。中文讲解放在代码块外的正文，或标题条里。原因：listings 与 xeCJK 的 UTF-8 中文共存不可靠，会静默缺字形（lint 的 `Missing character` 检查正是防这个）。
3. **行号默认关闭**。只在两种情况下开：代码超过 15 行、或正文需要按行号引用讲解。开法：`\begin{codeblock}[listing options={language=Python,numbers=left}]{Python}`。
4. **长行折行的边界**：`breaklines` 能折普通代码行，但**折不动字符串内部的超长内容**（如长 URL）——这种情况改写代码本身（拆行、缩短内容），不允许缩小字号硬塞，也不允许溢出。
5. **命令行/终端输出**用 `{bash}`（命令）或 `{}`（输出），标题条注明"终端"。
6. **伪代码不进 codeblock**：伪代码是给"人读的结构"，用普通列表或 algorithm 类环境；codeblock 只装真实语言。
7. **行内代码**用 `\code{...}`（灰底等宽），不用裸 `\texttt`——视觉上与代码块呼应，且 `\detokenize` 让你可以直接写 `hub_concept` 而不用转义下划线。
8. **何时该有代码块**：只有当代码本身是教学对象（读者要读或要跑）才给代码块；能用一行 `\code{}` 说清的 API 名，不要拉一个块。

## 4. 与质量门的衔接

- `lint_handout.py` 已把 `codeblock`/`tcblisting` 环境当作 verbatim 类跳过（不查其中的引号、省略号）。
- 编译日志出现 `Missing character` 时，先怀疑代码块里混了中文——回到规则 2。
