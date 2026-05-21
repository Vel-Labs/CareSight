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

## Current local runner

Use `mlx-vlm.server` for the existing local Gemma 4 E2B MLX model:

```bash
python3 apps/caresight-hub/scripts/caresight_gemma_start.py
```

The endpoint is OpenAI-compatible enough for local `/v1/chat/completions` use at:

```text
http://127.0.0.1:8080/v1
```

`mlx_lm.server` is not the selected runner for the current local Gemma 4 packages because it failed the model-load check. Ollama and llama.cpp remain good local options for GGUF models, but the current CareSight Gemma files are MLX/safetensors artifacts.

## Example prompt

```text
You are CareSight's local event summarizer. Use only the evidence in the provided JSON. Do not claim a fall, injury, or medication ingestion. Choose a recommended action only from allowed_actions.
```

## Sources

- [Gemma 4 Model Overview](https://ai.google.dev/gemma/docs/core)
- [Gemma with MLX Integration](https://ai.google.dev/gemma/docs/integrations/mlx)
