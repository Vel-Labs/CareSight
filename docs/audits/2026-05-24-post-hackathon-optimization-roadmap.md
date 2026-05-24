# CareSight Post-Hackathon Optimization and Product Roadmap

Date: 2026-05-24

Scope: technical and product roadmap for turning the current CareSight hackathon prototype into a credible post-hackathon local-first caregiver awareness system.

Instruction boundary: this report proposes next steps only. No implementation changes were made.

## Current Baseline

CareSight currently has:

- Contract-first repo governance.
- YOLO26 MLX as the required vision lane.
- `possible_floor_stay` eventization with SQLite persistence.
- `missing_off_camera_extended` as the current second v1 demo event.
- Deterministic tracking and same-day non-biometric appearance foundations.
- OBS browser overlays as the current live visual intermediary.
- Local Gemma/Hermes/Holler lanes for drafting, no-send preflight, and TTS.
- Strong documentation around what the system must not claim.

CareSight does not yet have:

- A dedicated CareSight camera/review dashboard.
- Production-validated multi-day home operation.
- A formal clinical/regulatory strategy.
- A HIPAA-ready deployment model.
- A model evaluation harness across YOLO26 model sizes and camera perspectives.
- A privacy/security threat model suitable for a real business.
- A support/update/packaging model for non-technical households.

## External Technical Inspiration

### Frigate

Reference: https://github.com/blakeblackshear/frigate

Relevant patterns:

- Local realtime object detection for IP cameras.
- Low-overhead motion pass before object detection.
- Separate detection processes for FPS.
- MQTT integration for state/events.
- RTSP restreaming to reduce camera connection pressure.
- WebRTC/MSE low-latency live view.
- Retention settings tied to detected objects.
- Built-in mask and zone editor.

CareSight adaptation:

- Borrow camera operations, restreaming, zone editing, retention, and event review patterns.
- Do not become a generic NVR.
- Preserve CareSight's narrower loop: local observation -> bounded event -> human review -> journal/audit -> caregiver handoff.

### ByteTrack

Reference: https://github.com/FoundationVision/ByteTrack

Relevant patterns:

- Strong multi-object tracking baseline.
- Associates lower-confidence boxes to reduce fragmented trajectories.
- Useful comparison target for CareSight's deterministic IoU tracker.

CareSight adaptation:

- Keep current deterministic tracker as baseline.
- Add ByteTrack as an optional comparison backend after test fixtures exist.
- Evaluate track stability, ID switches, occlusion recovery, and CPU/GPU cost on Apple Silicon.

### Roboflow Supervision

Reference: https://github.com/roboflow/supervision

Relevant patterns:

- Model-agnostic detection utilities.
- Polygon zones.
- Detection rendering.
- Tracking and zone-counting examples.

CareSight adaptation:

- Consider using or mirroring its abstractions for zone math, annotation, and evaluation harnesses.
- Avoid pulling in a dependency if local code remains smaller and clearer.

## Roadmap Principles

1. Keep CareSight local-first by default.
2. Keep YOLO26 MLX as the primary vision lane.
3. Use larger models and specialized datasets as evaluation lanes before product claims.
4. Do not strengthen language beyond the evidence.
5. Separate caregiver operations from clinical claims.
6. Treat HIPAA readiness as an architecture and process program, not a label.
7. Preserve inspectable SQLite evidence and deterministic checks.
8. Add human-friendly review surfaces without making dashboards canonical truth.

## Phase 0 - Stabilize the Hackathon Cut

Goal: make the current prototype repeatable and honest.

Duration: 1-2 weeks.

Key work:

- Freeze a tagged hackathon release.
- Produce a single "known-good demo path" document.
- Record exactly which commands were proven on the current Mac.
- Split current status into implemented, staged, locally validated, and production-unvalidated.
- Add a short operator status page.

Action steps:

1. Add `docs/status/OPERATING_STATUS.md`.
2. Add a current proof matrix with columns: feature, source file, command, receipt, evidence level, remaining gate.
3. Add a "current safe demo command" and "do not run without approval" section.
4. Keep OBS as current intermediary and avoid implying a dedicated dashboard exists.

Acceptance tests:

- A new operator can identify the current demo command, current camera config, current blocker, and current proof event in under two minutes.
- `npm run check` remains green.

## Phase 1 - Safety and Audit Hardening

Goal: close authority-boundary gaps before expanding capability.

Duration: 2-4 weeks.

Key work:

- Live target allowlist hardening.
- Pre-execution audit logging.
- Media-sharing policy.
- Lifecycle transition enforcement.
- Local feed exposure policy.
- Runtime validation receipt schemas.

Action steps:

1. Add `media-sharing-policy` schema.
2. Add `runtime-validation-receipt` schema.
3. Add `reply-gated-handoff` schema.
4. Add pre-execution attempt rows for all live external actions.
5. Require explicit media approval before sending event snapshots.
6. Add loopback-only enforcement for MJPEG unless LAN exposure is explicitly approved.
7. Add lifecycle transition checks from `contracts/lifecycle.md`.

Acceptance tests:

- Explicit target mismatch is blocked.
- External action cannot occur if preflight audit row insertion fails.
- Snapshot attachment is blocked unless media policy is approved.
- Non-loopback MJPEG binding is blocked without an override.
- Re-review of final event requires amendment flow.

## Phase 2 - Runtime Boundary Refactor

Goal: make the system easier to trust and test.

Duration: 2-3 weeks.

Key work:

- Split `v0_floor_stay_live.py`.
- Split `sqlite_store.py`.
- Keep CLI command compatibility.
- Preserve all existing tests.

Target ownership:

- Detector loop: frame processing, event policy.
- Preview service: MJPEG and still preview.
- Post-event pipeline: dry-run and live handoff.
- Media policy: snapshot attachment handling.
- Storage services: event/review/agent/appearance/observation groups.

Acceptance tests:

- Existing 175 Python tests pass.
- CLI help works without OpenCV.
- A no-camera unit test can exercise post-event live gating.
- A storage migration fixture upgrades without destructive rewrites.

## Phase 3 - YOLO26 MLX Model Evaluation Ladder

Goal: move from "works with yolo26n" to evidence-backed model selection.

Duration: 2-4 weeks.

Current model:

- `yolo26n.npz` is the fast nano baseline.

Candidate lanes:

- YOLO26n: default realtime.
- YOLO26s: likely first accuracy comparison if MLX path supports it.
- Larger YOLO26 variants: evaluate only after speed and memory budgets are measured.
- Segmentation variant if available through YOLO26 MLX: evaluate for floor/person region quality.

Model evaluation matrix:

| Dimension | Required metric |
| --- | --- |
| FPS | median, p95, minimum over 10-minute run |
| Latency | frame capture to event decision |
| Memory | process RSS and GPU memory pressure where available |
| Person recall | floor, couch, seated, partial body, far person |
| False positives | furniture, pets, shadows, blankets, TV/person images |
| Track stability | ID switches, occlusion recovery |
| Event quality | event fired, event suppressed, dwell time accuracy |
| Operator clarity | overlay readable, posture label understood |

Action steps:

1. Create `apps/caresight-hub/config/model-manifest.example.json`.
2. Add a `model-doctor` command for path/hash/license/purpose validation.
3. Add `care_eval_model.py` to run the same video/image set across model variants.
4. Build a small local fixture set from owner-approved household scenes and public benchmark images.
5. Store only metadata and hashes in Git; keep images/videos local or use source manifests.

Acceptance tests:

- A model cannot be selected without a manifest.
- Evaluation output includes metrics and claim boundaries.
- Larger model recommendation is based on measured tradeoffs, not assumed accuracy.

## Phase 4 - Specialized Dataset and COCO Feed Strategy

Goal: improve real-world reliability without creating unsafe claims.

Dataset needs:

- Older adult home mobility scenes.
- Floor vs couch vs recliner vs seated-on-floor.
- Pets and blankets.
- Walkers/canes/wheelchairs.
- Night/low-light scenes.
- Multiple camera perspectives.
- Multi-person rooms.
- Kitchen counter routines without medication-confirmation claims.

COCO strategy:

- Keep base COCO labels for generic objects.
- Build a CareSight label map overlay that groups COCO labels into care-relevant concepts:
  - person
  - cup/bottle/bowl
  - chair/couch/bed
  - pet classes
  - mobility aids if a model supports them
  - household context objects
- Do not pretend COCO can detect medication administration.

Specialized feeds:

- Use source manifests for public image sets.
- Add a private local fixture pack for household calibration.
- Evaluate with negative examples as aggressively as positive examples.

Action steps:

1. Create `docs/evaluation/dataset_policy.md`.
2. Create `apps/caresight-hub/config/coco-care-label-map.example.json`.
3. Add false-positive fixture categories.
4. Add explicit "not suitable for training claim" labels for public internet images.
5. Investigate pose/segmentation datasets only as evaluation material unless licensing permits training.

Acceptance tests:

- Every evaluation source has license/provenance metadata.
- No third-party media is committed without permission.
- Evaluation report separates sourced still images, owner local footage, and synthetic/demo fixtures.

## Phase 5 - Posture, Pose, Segmentation, and Depth

Goal: reduce ambiguity between seated, lying, crouched, couch, and floor.

Current limitation:

- The current `posture_evidence()` is YOLO-box geometry. It is cheap and bounded but brittle.

Options:

- Add pose estimation as an advisory model.
- Add segmentation if YOLO26 MLX supports a segmentation path.
- Add monocular depth or floor-plane calibration for camera-specific geometry.
- Add multi-camera corroboration instead of trying to infer everything from one camera.

Recommended path:

1. Keep box-derived posture as baseline.
2. Add calibrated floor polygon editor.
3. Add optional pose advisory lane.
4. Add segmentation comparison if MLX support is practical.
5. Add camera-perspective-specific thresholds.

Acceptance tests:

- Seated-on-floor does not trigger `possible_floor_stay`.
- Lying-low in floor zone triggers after dwell.
- Couch/recliner posture is suppressed or downgraded.
- Small/far person false positives are reduced.
- Multi-person scenes preserve the correct active track.

## Phase 6 - Dedicated CareSight Dashboard

Goal: replace OBS-as-review-surface with a CareSight-owned local dashboard while keeping OBS available for recording/demo composition.

Dashboard principles:

- SQLite is canonical.
- Dashboard is a read model plus approved action surface.
- Review mutations go through `ReviewService`.
- External actions require staged request plus approval.

Core screens:

1. Live camera review with local feed.
2. Floor-zone calibration editor.
3. Event inbox.
4. Event detail with snapshot, evidence, audit chain.
5. Human review packet.
6. Daily journal.
7. Alert draft and handoff staging.
8. Runtime status board.
9. Model and camera health.
10. Retention/privacy settings.

Dashboard implementation options:

- FastAPI + HTMX: simple local appliance UI.
- FastAPI + React: richer review/calibration surface.
- Streamlit: fast prototype, but less suitable for final household appliance.
- Native macOS SwiftUI: strongest appliance feel on Mac mini, but heavier engineering path.

Recommended first path:

- FastAPI + HTMX or React, local-only bind by default.
- Use SQLite read services.
- Add websocket/SSE for live event updates.

Acceptance tests:

- Dashboard cannot confirm/dismiss without reviewer entry.
- Dashboard cannot dispatch.
- Dashboard cannot silently send messages.
- Dashboard shows current event and audit chain from SQLite.
- Dashboard has a visible privacy indicator when any feed is exposed beyond loopback.

## Phase 7 - Camera Operations Layer

Goal: make camera setup reliable for households without turning CareSight into a cloud camera platform.

Borrow from Frigate:

- RTSP restreaming.
- Substream for detection, main stream for evidence clip.
- Per-camera health checks.
- Retention settings.
- Zone/mask editor.
- Low-latency live view.

CareSight-specific additions:

- Care-event calibration wizard.
- Room naming and camera purpose.
- Privacy mode and schedule.
- "This camera is not used for emergency dispatch" boundary.

Action steps:

1. Add restreaming layer evaluation: go2rtc, mediamtx, or FFmpeg-managed local proxy.
2. Add per-camera health table.
3. Add camera privacy metadata table.
4. Add event-scoped local clip capture with retention policy.
5. Add camera setup receipts.

Acceptance tests:

- Camera reconnect works.
- Detector does not open the same camera twice unnecessarily.
- Event clip creation is local and retention-bounded.
- Credentials never appear in Git or logs.

## Phase 8 - Local LLM and Agent Assist Maturity

Goal: turn Gemma/Hermes from demo scaffolding into a reliable draft-only assistant.

Required boundaries:

- LLM receives structured event JSON, not raw video.
- Drafts are validated before storage.
- Unsafe claims are blocked.
- Every draft has provenance.
- Every action request is staged.
- Live actions need human approval and durable audit rows.

Action steps:

1. Add prompt/version registry.
2. Add draft quality rubric.
3. Add deterministic JSON schema validation for all LLM outputs.
4. Add model fallback behavior.
5. Add local model latency/quality benchmark.
6. Add caregiver tone approval workflow.

Acceptance tests:

- Draft with "fall detected" is blocked or rewritten.
- Draft with "medication was taken" is blocked.
- Draft cannot request raw video.
- Draft cannot confirm/dismiss/delete/dispatch.
- Local model unavailable produces a clear blocked receipt.

## Phase 9 - Privacy, Security, and HIPAA-Readiness Program

Goal: prepare for regulated or semi-regulated deployments without claiming compliance prematurely.

Regulatory source notes:

- HHS states HIPAA Privacy Rule applies to covered entities such as health plans, health care clearinghouses, and certain providers, and business associates when they handle protected health information on behalf of covered entities.
- FTC Health Breach Notification Rule amendments effective July 29, 2024 underscore coverage for many health apps and similar technologies that are not HIPAA-covered.
- FDA recommends using its Digital Health Policy Navigator to determine whether software functions are regulated device functions.

CareSight implication:

- Direct-to-consumer home use may not automatically be HIPAA-covered.
- Selling to providers, home-health agencies, assisted living, or care facilities can create business-associate and PHI obligations.
- Claims that CareSight detects falls, diagnoses risk, or guides clinical decisions increase FDA and clinical validation risk.
- Even outside HIPAA, privacy, breach notification, state privacy laws, consumer protection, and product-liability issues remain.

Required workstreams:

1. Legal classification memo.
2. HIPAA applicability matrix.
3. FTC health app breach rule review.
4. FDA device-function review by feature.
5. State privacy review.
6. Security risk assessment.
7. Data retention and deletion policy.
8. Incident response plan.
9. Business associate agreement readiness if selling to covered entities.
10. Accessibility and caregiver consent review.

Technical controls:

- Encryption at rest for SQLite and snapshots.
- Local key management.
- Role-based access control.
- Audit log integrity.
- Retention schedules.
- Export controls.
- Consent records.
- Local network exposure controls.
- Secure update path.
- Signed releases.
- Dependency and model SBOM.

Acceptance tests:

- Threat model exists.
- Security control matrix exists.
- Privacy policy draft exists.
- BAA readiness checklist exists.
- No HIPAA compliance claim appears in product copy before legal review.

## Phase 10 - Pilot Readiness

Goal: run controlled non-clinical household pilots.

Pilot constraints:

- Use "caregiver awareness prototype" language.
- No medical device claim.
- No emergency dispatch.
- No fall-detection guarantee.
- Raw media local by default.
- Written participant consent.
- Clear uninstall/delete path.

Pilot metrics:

- False positives per day.
- False negatives from staged scenarios.
- Alert fatigue.
- Caregiver comprehension.
- Setup time.
- Camera reliability.
- Review time.
- Privacy concerns.
- Support burden.

Pilot stages:

1. Internal household pilot.
2. Friends/family pilot with consent.
3. Caregiver advisory pilot.
4. Partner home-care agency shadow pilot with legal review.
5. Facility workflow simulation, not production facility deployment.

Acceptance tests:

- Every pilot has consent, data handling, and support plan.
- Every incident has a review note.
- Every product claim is traceable to pilot evidence or marked aspirational.

## Phase 11 - Business-Ready Product Packaging

Goal: make CareSight deployable by non-developers.

Packaging options:

- Mac mini appliance bundle.
- Bring-your-own Mac installer.
- Managed local appliance plus subscription.
- Open-source community edition plus paid support.
- Home-care agency managed deployment.

Recommended first product:

- CareSight Home Pilot Kit:
  - Mac mini-class local hub.
  - 1-2 supported RTSP cameras.
  - Local dashboard.
  - Setup wizard.
  - No cloud raw video.
  - Optional encrypted remote caregiver summaries.
  - Paid install/support.

Critical product requirements:

- One-command install.
- Signed update.
- Backup/restore.
- Camera setup wizard.
- Local admin password.
- Recovery mode.
- Exportable audit bundle.
- Clear privacy controls.
- Support diagnostics that do not upload raw media by default.

## Phase 12 - Facility and Clinical Adjacent Lane

Goal: explore higher-value markets without drifting into unsupported claims.

Facility requirements:

- Multi-room dashboards.
- Staff roles and shift handoff.
- Audit export.
- Retention schedules.
- IT deployment controls.
- SSO and RBAC.
- Device fleet management.
- Formal incident workflow.
- Legal and compliance review.

Avoid until validated:

- Fall detection claims.
- Clinical diagnosis.
- Autonomous emergency dispatch.
- EHR integration.
- HIPAA-compliant marketing language.

Recommended facility wedge:

- "Local care observation and review queue" for operational awareness, not clinical decision support.

## Prioritized 90-Day Plan

### Days 1-14

- Close high-risk bug findings F001-F003.
- Add media-sharing and runtime-receipt contracts.
- Freeze demo release and proof matrix.
- Rename/replace tracked `v0.local.json`.

### Days 15-30

- Split live loop and storage.
- Add model manifest and model doctor.
- Add real-runtime validation receipts.
- Add dashboard product spec.

### Days 31-45

- Build model evaluation harness.
- Compare YOLO26n vs YOLO26s if available.
- Build false-positive fixture matrix.
- Add camera health and retention policy.

### Days 46-60

- Start local dashboard MVP.
- Add floor-zone editor.
- Add event inbox and review detail.
- Add local model draft review screen.

### Days 61-75

- Run internal multi-day household pilot.
- Record false positives/false negatives.
- Improve thresholds and camera setup.
- Draft privacy/security threat model.

### Days 76-90

- Prepare pilot kit.
- Build grant/business package.
- Draft legal/regulatory questions for counsel.
- Recruit 3-5 caregiver discovery interviews.
- Build NSF/NIH/AARP application drafts if fit is confirmed.

## Longer-Term Roadmap

### 3-6 Months

- Household pilot kit.
- Local dashboard.
- Model evaluation reports.
- Encrypted local storage.
- Signed installer.
- Basic support/update path.
- Privacy/security control matrix.

### 6-12 Months

- Paid pilot with support.
- Multiple camera support.
- Remote caregiver summaries with consent.
- Advisory board of caregivers, clinicians, and privacy/security reviewers.
- SBIR/STTR or accelerator applications.
- Formal compliance counsel review.

### 12-24 Months

- Commercial appliance.
- Managed support subscription.
- Home-care agency pilots.
- HIPAA-ready architecture if provider/facility route is pursued.
- Regulatory strategy by feature.
- Longitudinal evidence base for reliability and caregiver outcomes.

## Recommended Technical Backlog

1. Contact allowlist enforcement hardening.
2. Pre-execution audit rows.
3. Media-sharing policy contract.
4. Runtime receipt schema.
5. Model manifest.
6. Retention policy.
7. Local feed exposure policy.
8. Live loop refactor.
9. Storage refactor.
10. Model evaluation harness.
11. False-positive fixture matrix.
12. YOLO26 larger model comparison.
13. Optional ByteTrack backend.
14. Optional pose advisory backend.
15. Dashboard MVP.
16. Floor-zone editor.
17. Event review inbox.
18. Daily journal UI.
19. Camera health monitor.
20. RTSP restream evaluation.
21. Event-scoped clips.
22. Encrypted SQLite/snapshots.
23. Local admin/RBAC.
24. Signed updates.
25. Pilot consent/export/delete tooling.

## Sources

- Frigate GitHub: https://github.com/blakeblackshear/frigate
- ByteTrack GitHub: https://github.com/FoundationVision/ByteTrack
- Roboflow Supervision GitHub: https://github.com/roboflow/supervision
- HHS Business Associates guidance: https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/business-associates/index.html
- FTC Health Breach Notification Rule: https://www.ftc.gov/business-guidance/resources/health-breach-notification-rule-basics-business
- FDA Digital Health Policy Navigator FAQ context: https://www.fda.gov/medical-devices/software-medical-device-samd/clinical-decision-support-software-frequently-asked-questions-faqs

