# Gemma 4 + MLX Reference

## Role in CareSight

Gemma is the local language engine for summaries and approved action routing. It is not the vision model.

## Good uses

- event summary
- caregiver-friendly alert text
- daily journal drafting
- prior-context summary
- parsing caregiver replies
- choosing from allowed action templates

## Avoid

- raw emergency decisions
- medical conclusions
- arbitrary shell/tool execution
- hallucinating visual evidence

## Local endpoint pattern

```text
CareSight event JSON → local Gemma endpoint → structured JSON summary → policy guard → action adapter
```

## Example prompt

```text
You are CareSight's local event summarizer. Use only the evidence in the provided JSON. Do not claim a fall, injury, or medication ingestion. Choose a recommended action only from allowed_actions.
```

## Sources

- [Gemma 4 Model Overview](https://ai.google.dev/gemma/docs/core)
- [Gemma with MLX Integration](https://ai.google.dev/gemma/docs/integrations/mlx)
