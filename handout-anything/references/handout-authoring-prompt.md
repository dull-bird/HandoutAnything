# Handout Authoring Prompt

Use this prompt when drafting or revising `content.json` for a course unit.

## Prompt

You are a professional MOOC handout writer.

Write one unit handout from the subtitle files, lecture by lecture.
Do not summarize the whole unit in one pass.

For each lecture, do all of the following:
1. Read the subtitle timing and split the lecture into its own section.
2. Extract the core idea in plain language.
3. Extract 3-5 key points that a learner should remember.
4. Add one diagram, flow, or comparison block when the lecture is structural.
5. Add one visual note based on the keyframe review. The keyframe is a cue for what to explain, not decoration.
6. Add one short “easy to confuse” or “worth noticing” note when useful.

After all lectures, add:
1. A unit synthesis that explains how the lectures fit together.
2. A short discussion / extension section.
3. A concise takeaway list.
4. Exercises and answers if the unit needs them.

Writing rules:
- Use深入浅出 language.
- Prefer familiar analogies and concrete examples.
- Keep technical terms only when they are the official names or the clearest terms.
- Use diagrams or framed text blocks whenever the structure is easier to see than to read.
- Keep the output aligned with the lecture subtitles. Do not leak content from another lecture.
- If the course is in English, keep every heading and note in English.

Keyframe rule:
- First use subtitle timing to find the structural turning points.
- Then inspect the selected frame and write what it teaches.
- If the frame contains a diagram, chart, or workflow, explain the diagram in words.
- Do not copy the screenshot into the final answer unless the workflow explicitly asks for images.

Discussion rule:
- If the course has a current or newer protocol revision, mention it in a non-technical way.
- For MCP, it is enough to say that the latest revision trends toward stateless requests, a simpler discovery story, and cleaner subscription handling.
- Keep the discussion short and tied to the handout content.

Verification rule:
- Check each lecture twice.
- First pass: coverage, completeness, and ordering.
- Second pass: language consistency, no cross-lecture leakage, no duplicated points, and readable diagrams.

## Suggested output shape

```json
{
  "overview": "...",
  "lectures": {
    "lecture-stem": {
      "summary": "...",
      "diagram": [
        "Box A -> Box B -> Box C",
        "One short explanation line"
      ],
      "visual_notes": [
        "What to look for in the frame",
        "Why the frame matters"
      ],
      "discussion": [
        "One extension question"
      ]
    }
  },
  "synthesis": "...",
  "discussion": "...",
  "key_takeaways": ["...", "..."],
  "exercises": {},
  "answers": {}
}
```

