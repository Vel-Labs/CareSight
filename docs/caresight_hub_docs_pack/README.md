# CareSight Hub Documentation Pack

This pack is a planning and implementation reference for **CareSight Hub**: a local-first care event engine designed around YOLO26 MLX, Apple Silicon, local camera feeds, SQLite event memory, OBS live-view routing, and event-driven caregiver escalation.

The pack is intentionally scoped for a six-day hackathon while preserving a credible product roadmap beyond the challenge.

## Product thesis

> CareSight Hub is a set-and-forget care appliance: a Mac mini or MacBook-based local safety layer that watches for care-relevant events, documents them locally, and escalates to the right person without requiring the person at home to operate anything.

## Pack contents

### Roadmap and architecture

- `01_product_roadmap.md` — staged roadmap from v0 smoke test through facility/enterprise versions.
- `02_six_day_hackathon_plan.md` — day-by-day build plan for the challenge window.
- `03_architecture.md` — system architecture, module boundaries, and data flow.
- `04_scope_decisions.md` — what to build now, what to fake, what to cut.
- `05_data_model_sqlite.md` — local database model and recommended schema.
- `06_event_engine_confidence_escalation.md` — event logic, confidence scoring, and escalation chain.
- `07_roles_permissions_journal.md` — delegated access, caregivers, temporary roles, and care journal design.
- `08_obs_facetime_live_view.md` — OBS as live-view switchboard and FaceTime handoff layer.
- `09_mac_automation_shortcuts_launchd.md` — macOS automation via Shortcuts, FaceTime URLs, launchd, and journals.
- `10_agent_orchestration_gemma_openclaw.md` — local LLM/action orchestration boundaries.
- `11_camera_integration_strategy.md` — webcam, RTSP, ONVIF, Home Assistant, Ring, and Nest strategy.
- `12_security_privacy_compliance.md` — privacy, safety, non-medical-device framing, and future compliance needs.
- `13_demo_script_and_storytelling.md` — 60-second demo story, pitch, screenshots, and social post ideas.
- `14_project_readme_template.md` — challenge-ready README template.
- `15_open_source_and_license_notes.md` — open-source and license considerations to verify before release.

### References

The `references/` directory contains focused summaries and links for each toolbase.

### Templates

The `templates/` directory contains JSON schemas, SQL schema, alert templates, daily journal templates, OBS scene plan, and submission checklist.

## Design principle

The hackathon version should not try to implement every integration. It should demonstrate the **engine**:

```text
camera → YOLO26 MLX → event engine → SQLite → alert/journal/dashboard → optional OBS/FaceTime handoff
```

## Safety disclaimer

This project should be described as a **caregiver awareness and care-documentation prototype**, not a medical device, clinical fall detector, alarm service, or emergency dispatch product. The MVP should use language such as “possible floor-stay event,” “routine likely observed,” and “awaiting confirmation.”

## Master source index

- [YOLO26 MLX Build Challenge](https://webai.discourse.group/t/the-yolo26-mlx-build-challenge-may-2026/16)
- [YOLO26 MLX Getting Started Guide](https://webai.discourse.group/t/getting-started-guide-yolo26-mlx-build-challenge/20)
- [YOLO26 MLX GitHub Repository](https://github.com/thewebAI/yolo-mlx)
- [webAI YOLO26 MLX Announcement Blog](https://www.webai.com/blog/running-yolo26-natively-on-apple-silicon-with-mlx)
- [Apple MLX Project](https://opensource.apple.com/projects/mlx/)
- [MLX Docs](https://ml-explore.github.io/mlx/build/html/index.html)
- [Gemma 4 Model Overview](https://ai.google.dev/gemma/docs/core)
- [Gemma with MLX Integration](https://ai.google.dev/gemma/docs/integrations/mlx)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw Hooks Docs](https://docs.openclaw.ai/automation/hooks)
- [OpenClaw iMessage Docs](https://docs.openclaw.ai/channels/imessage)
- [OBS Virtual Camera Guide](https://obsproject.com/kb/virtual-camera-guide)
- [OBS Developer Guide](https://obsproject.com/kb/developer-guide)
- [OBS Remote Control Guide](https://obsproject.com/kb/remote-control-guide)
- [obs-websocket GitHub](https://github.com/obsproject/obs-websocket)
- [Apple Shortcuts CLI](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)
- [Apple FaceTime URL Scheme](https://developer.apple.com/library/archive/featuredarticles/iPhoneURLScheme_Reference/FacetimeLinks/FacetimeLinks.html)
- [Apple launchd Overview](https://support.apple.com/guide/terminal/script-management-with-launchd-apdc6c1077b-5d5d-4d35-9c19-60f2397b2369/mac)
- [Apple FaceTime Camera Selection](https://support.apple.com/guide/facetime/choose-a-camera-or-microphone-fctm26739220/mac)
- [SQLite Main Docs](https://sqlite.org/docs.html)
- [SQLite FTS5](https://sqlite.org/fts5.html)
- [SQLite JSON Functions](https://sqlite.org/json1.html)
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html)
- [ONVIF Profiles](https://www.onvif.org/profiles/)
- [Home Assistant Generic Camera](https://www.home-assistant.io/integrations/generic/)
- [Ring Partner API Documentation](https://developer.amazon.com/docs/ring/api-documentation.html)
- [Ring Partner API Getting Started](https://developer.amazon.com/docs/ring/get-started.html)
- [Google Nest Device Access](https://developers.google.com/nest/device-access)
- [Google Nest Camera API](https://developers.google.com/nest/device-access/api/camera)
- [Google Nest Wired Camera API](https://developers.google.com/nest/device-access/api/camera-wired)
- [OpenCV Video Capture Tutorial](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)
- [OpenCV GitHub](https://github.com/opencv/opencv)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [uv Docs](https://docs.astral.sh/uv/)
- [HHS HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html)
