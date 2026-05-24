# Detection Commands

Detection commands run the YOLO26 MLX path or the floor-stay live loop. They are operator-owned because they use the local runtime, local model files, camera frames, preview windows, snapshots, or SQLite event writes.

## Manual Operator

| Command | Purpose | Validation |
| --- | --- | --- |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_image_smoke.py` | Run the CareSight YOLO26 MLX inference harness against the bundled image fixture. | v0 smoke checkpoint and `test_inference_harness.py`. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_webcam_smoke.py` | Verify live webcam capture and YOLO26 person labels through the adapter boundary. | Deterministic adapter tests; camera behavior remains manual. |
| `python apps/caresight-hub/scripts/v0_floor_stay_live.py` | Create a local `possible_floor_stay` event after configured floor/low-zone dwell. | `npm run py:check` covers deterministic policy/storage; live camera remains manual. |
| `python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room_usb --no-window --max-seconds 120` | Select one configured local camera source. | `test_v0_config.py` verifies deterministic source selection and provider rejection. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --max-seconds 60 --stop-after-event` | Collect one bounded event or no-event receipt. | Emits `event_persisted` or `no_event_persisted`. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --appearance-sampling --max-seconds 600` | Store capped, quality-gated local appearance samples. | `test_appearance_profiles.py`, `test_sqlite_store.py`, and `test_care_console.py`. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --auto-agent-dry-run --max-seconds 600 --no-window` | After each event, update OBS, draft locally, stage an allowlisted action, and run Hermes no-send preflight. | `test_v0_floor_stay_live.py`. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --debug-floor-stay --max-seconds 90 --stop-after-event --no-window` | Print floor-stay rejection/dwell diagnostics during bounded live validation. | Operator receipt plus deterministic tracking tests. |
| `python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --help` | Verify CLI parsing without camera, OpenCV, or YOLO imports. | Help output only. |

## Event Boundary

`possible_floor_stay` remains a possible event. It requires the configured floor zone plus same-track dwell and human review; seated-on-floor context does not confirm a floor-stay event by itself.
