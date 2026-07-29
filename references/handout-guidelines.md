# Handout guidelines

## What to number

Use numbered lists for:

- ordered procedures
- conceptual sequences
- section roadmaps
- exercise items
- answer keys

Use bullets for:

- attributes
- examples
- implications
- exceptions
- notes

## Heading style

- For Chinese handouts, prefer manual, review-friendly headings like `\section*{1. 颜色知觉}` or `\section*{1. 感知如何组织世界}`.
- For English handouts, keep all structural labels English, including `Contents`, `Overview`, `Knowledge Map`, and `Answer Key`.
- Keep `0. 概要` as the only synthetic overview heading.
- If a heading already carries a manual number, do not use the numbered section form.
- Keep subsection numbering aligned with the same rule: either manual numbers everywhere or automatic numbers everywhere, not both.
- If the PDF should look quiet and academic, use `\pagestyle{plain}`.

## Coursera links

- Use lecture-page URLs for review links.
- Put one visible video symbol on the title line or directly beneath it.
- If a chapter is built from several lectures, keep the title official and attach any extra lecture links in one compact line.
- Keep the visible link text short enough to scan quickly.

## Official titles

- Use the official lecture title from the course metadata as the source anchor.
- If the course is in Chinese, you may collapse neighboring lectures into a clearer review heading when that helps the reader.
- If the course is in English, keep the original English title unchanged unless you are placing it as the source anchor under a synthesized review heading.
- For Chinese output on foreign courses, prefer the original English course title and technical terms over machine-translated labels whenever the official English term is standard or clearer.
- The overview may be synthetic and may be numbered `0`.

## Exercise provenance

- Put source labels at the end of the question stem.
- Example: `题目内容【来源：第三节】`
- Example: `题目内容【综合：第二节-第四节】`
- Use `综合` only when the question really depends on more than one section.

## Historical inserts

- Use one short anecdote to explain why a concept became important in the field.
- Good anchors: Helmholtz for unconscious inference, Ebbinghaus for the forgetting curve, Sperling for iconic memory, Loftus for false memory.
- Keep historical inserts brief; they should support the concept, not replace it.

## AI and embodied intelligence bridge

- Use this only when the unit is about perception, memory, consciousness, or action.
- Keep the bridge to one short paragraph.
- Use it to connect the classic psychology point to modern AI through sensorimotor loops, predictive processing, memory-guided action, or human-AI hybrid thinking.
- Good anchors: hybrid thinking systems, embodied cognition in robots, and the embodied Turing test.

## Merge policy

- Merge lectures when they are examples, subcases, or complementary parts of one concept.
- Keep lectures separate when they introduce distinct mechanisms, distinct experimental findings, or distinct review goals.
- A good handout usually has fewer sections than the raw lecture list.
- If a merged heading would become vague, split it back into two clearer headings.

## Good default layout

0. 概要
1. 主题一（可合并若干讲）
2. 主题二（可合并若干讲）
3. 主题三（可合并若干讲）
4. 主题四（可合并若干讲）
5. 主题五（可合并若干讲）
6. 主题六（可合并若干讲）
7. 主题七（可合并若干讲）
8. 主题八（可合并若干讲）
9. 练习题
10. 参考答案
