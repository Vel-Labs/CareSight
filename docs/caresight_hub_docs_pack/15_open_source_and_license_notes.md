# Open Source and License Notes

## Important disclaimer

This file is a planning checklist, not legal advice. Verify all licenses before publishing or commercializing.

---

# Components to verify

## YOLO26 MLX

Check the repository license and any model weight license/terms. The getting-started material references AGPL implications for hosted/web-app usage, so read the repo license carefully before deciding how to publish or commercialize.

Checklist:

- Repository license.
- Model weights/license.
- Whether modifications must be published.
- Whether network/service use triggers obligations.
- Compatibility with your chosen app license.

## Apple MLX

Verify license from the MLX repo/docs before bundling code.

## Gemma

Gemma open weights have their own terms. Verify:

- accepted use policy
- redistribution terms
- commercial use terms
- model variant license
- whether generated summaries create any additional obligations

## OpenClaw

Verify repository license and extension/hook license compatibility.

## OBS / obs-websocket

Verify OBS and obs-websocket licenses. If you only control OBS externally through WebSocket and do not bundle modified OBS, obligations may differ from embedding code. Confirm before distribution.

## SQLite

SQLite is public domain according to official documentation, but still verify how your packaging handles it.

## OpenCV

OpenCV is Apache-2.0 licensed according to the project repository, but verify for the version used.

## FastAPI / Streamlit / uv

Verify package licenses before distribution.

## Apple Shortcuts / FaceTime / Notes

These are platform integrations, not open-source dependencies. Consider platform terms, automation limitations, and user permissions.

## Ring / Nest / Google / Home Assistant

Do not ship integrations without reviewing API terms, certification requirements, privacy/security requirements, and branding rules.

---

# Recommended repo policy for hackathon

- Include no personal credentials.
- Include no private camera URLs.
- Include no private video footage without consent.
- Include `.env.example`, not `.env`.
- Document license uncertainty honestly.
- Add a safety disclaimer.
- Add a privacy statement.

---

# Suggested `LICENSE` decision

For a hackathon repo, choose a license only after checking upstream obligations. If uncertain, include:

```text
License: TBD pending upstream license compatibility review.
```

But many hackathons require open-source code, so resolve this before submission.

---

# Source references

See `references/source_index.md`.
