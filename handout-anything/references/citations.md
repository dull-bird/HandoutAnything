# 出处与拓展阅读排版规范

讲义是浓缩讲解，但读者必须能**按图索骥**：定理证明想看完整版去哪翻、数据从哪来、想深造下一步读什么。本规范定义三样组件：**行内出处标签** `\src{}`、**拓展阅读盒** `reading`、**卷尾参考文献与拓展阅读章节**。设计目标与 code-blocks.md 一致：与现有盒子体系视觉一致、零额外依赖（不引入 BibTeX，xelatex 两遍即出）、跨平台可复现。

## 1. 什么内容必须有出处（方法论 §5.5）

| 必须有出处 | 不需要出处 |
|---|---|
| 定理、引理及其证明（非讲义作者原创推导） | 定义级常识（如"速度是位移的变化率"） |
| 数据、实验结论、统计结果 | 讲义自己当场完成的推导 |
| 转述材料的观点、主张 | 讲义作者自己的类比与讲解 |
| 引用的原文、图表、例题（改编自原书时点名） | |

出处要给**可翻到的定位**：章/节号、页码、或视频时间戳（`12:34`），只写书名不算合格。

## 2. Preamble 片段（原样粘贴，放在 tcolorbox 之后）

```latex
\tcbuselibrary{skins}   % reading 盒的左侧竖条需要 enhanced 皮肤（若已为 codeblock 引入则跳过）

% 出处/拓展阅读配色（讲义既有调色板之外只新增两色）
\definecolor{refaccent}{HTML}{7c3aed}  % 出处主色：紫（与蓝/橙/绿三色盒区分）
\definecolor{refbg}{HTML}{f3e8fd}      % 出处标签底：浅紫
\definecolor{readbg}{HTML}{faf5ff}     % 拓展阅读盒底：近白紫

% 行内出处标签：\src{[2]《微积分》第一册 §3.2 定理 2}
\newcommand{\src}[1]{%
  {\small\colorbox{refbg}{\color{refaccent}出处：#1}}}

% 拓展阅读盒（可选标题，与 keyconcept/exercise 同款写法，但必须给标题）：
%   \begin{reading}[想看更严谨的证明？] ... \end{reading}
\newtcolorbox{reading}[1][]{
  enhanced,
  colback=readbg, colframe=readbg, boxrule=0pt, arc=2pt,
  borderline west={2pt}{0pt}{refaccent},   % 左侧 2pt 紫竖条
  left=8pt, right=8pt, top=5pt, bottom=5pt,
  fonttitle=\small\bfseries, coltitle=refaccent,
  colbacktitle=readbg, toptitle=4pt,
  title={#1}}
```

注意事项（实测踩过的坑）：

- `borderline west` 只在 `enhanced` 皮肤下渲染，缺了竖条静默消失（不报错）。
- **`[...]` 里的标题只能出现在 `title={#1}` 这种"取值位置"**：若把 `#1` 平铺成选项列表里的独立一项（如 `title={拓展阅读}, #1`），中文标题会被 pgfkeys 当未知键直接报错。本片段已按正确写法固定，不要自行改回平铺式。
- **标题必须给**：省略 `[标题]` 会渲染出一条空标题栏；每个 reading 盒都要有向读者发问式的标题。
- 不加 `breakable`：它需要额外 `\tcbuselibrary{breakable}`，拓展盒体量小（规则 2 限制了内容量），跨页需求用拆盒解决。
- `\src{}` 内容走 LR 模式**不会折行**，只放短标签（编号 + 书名 + 章节号）；长说明写正文，不要塞进 `\src`。
- 紫色系刻意区别于现有盒子：蓝 = 核心概念、橙 = 自测、绿 = 计算、紫 = 出处/拓展，读者扫一眼颜色就知道这块是"往外指"的。

## 3. 使用规则

1. **出处就近标**：定理/数据/转述观点**首次出现处**紧跟 `\src{...}`；同一出处在后续单元复现时改用编号（见规则 3）。
2. **每个单元最多一个 reading 盒**：拓展阅读是甜点不是主食。盒子内写清三件事——读什么（书 + 章/节）、读多少（"读到 §4.3 即可，后面超纲"）、需要什么前置（"学完第 3 讲再来"）。写不出这三件事，说明这个盒子不该有。
3. **编号引用制**：卷尾参考文献按出现顺序编号 `[1], [2], …`，正文行内引用写作 `\src{[2]}` 或 `[2]`。一条文献只编一次号。
4. **拓展阅读只列把关过的书**：确认过版本、章节号真实存在、难度匹配目标读者。不确定章节号就去查证，查不到就不列——列错章节号比不列更糟。
5. **论文类来源**与 references/research-inserts.md 衔接：研究进展插入框的出处直接进编号文献表。
6. **禁用 BibTeX**：讲义是自包含单文件交付，文献量在个位数到十几条，手工 enumerate 比引入 `.bib` + bibtex 编译步骤更可靠。

## 4. 卷尾章节骨架（放在收尾"讲给别人听的 N 句话"之后）

```latex
\section*{参考文献与拓展阅读}
\addcontentsline{toc}{section}{参考文献与拓展阅读}

\subsection*{本讲义依据的来源}
本讲义主体依据《XXX》（版本/版次）第 X–X 章；单元 3 的实验数据来自文献 [4]。

\subsection*{编号文献}
\begin{enumerate}[label={[\arabic*]},leftmargin=2.6em,itemsep=4pt]
  \item 作者. \emph{书名}. 出版社, 年份. （对应本讲义：第 X 讲 §X.X）%
        \textbf{为什么读它}：一句话说明它和讲义的关系。
\end{enumerate}

\subsection*{拓展阅读路线}
按读者意图分条，每条给"读什么 + 读多少 + 前置"：
\begin{itemize}
  \item \textbf{想看更严谨的证明}：《A》第 5 章——把本讲义省略的严格论证细节全部补齐；学完第 4 讲后再读。
  \item \textbf{对应用感兴趣}：《B》§2.1–2.3——三个工程实例，只需本讲义第 1 讲的基础。
  \item \textbf{想继续深造}：《C》前三章——下一门课的标准入口。
\end{itemize}
```

## 5. 与质量门的衔接

- `review_handout.py` 检查卷尾是否有「参考文献」与「拓展阅读」章节（缺失记 warning——短讲义可有意省略，但要有意识地省略）。
- `\src{}` 与 `reading` 盒不影响 lint 的引号/省略号检查；书名号《》照常使用。
- 结构位置：参考文献与拓展阅读位于收尾呼应**之后**，是全讲义的最后一节——讲义以"往外指"结束。
