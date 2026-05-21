# CareSight Hermes Config

This directory is the workspace-local Hermes setup surface for CareSight. It is intentionally a template, not a live `~/.hermes` install.

## Boundary

CareSight remains the policy and audit boundary:

- SQLite remains canonical for events, drafts, and staged action requests.
- Hermes may only receive validated draft payloads after a CareSight action request has been staged.
- No command in this repo sends iMessage, writes Apple Notes, starts FaceTime, plays TTS, confirms events, dismisses events, or dispatches emergency services.
- Raw video and snapshots must not be sent to Hermes as the decision-maker.

## Local Model Serving

Hermes can use a local OpenAI-compatible endpoint directly. The default CareSight route is:

```text
CareSight staged action request
  -> validated draft payload
  -> Hermes custom endpoint config
  -> local OpenAI-compatible server
  -> Gemma MLX reasoning lane
```

OpenRouter is not required for the default route. Treat OpenRouter or any hosted router as an explicit cloud fallback only, because care context may leave the local machine.

## Files

- `config.caresight.local.yaml`: safe Hermes config template for a local OpenAI-compatible endpoint.
- `env.caresight.example`: secret-free environment template for local endpoint and BlueBubbles variables.
- `model-routes.json`: inspectable CareSight model lane and routing policy.

Copy or merge these into `~/.hermes/` only during a human-approved harness trial.
