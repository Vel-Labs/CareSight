# Camera Integration Strategy

## Principle

The MVP should support camera sources you control. Third-party consumer-camera APIs should be documented as future adapters unless they are already trivial in your environment.

---

# Source priority

## 1. Mac webcam / USB webcam

Best for hackathon reliability.

Pros:

- Easiest to run.
- No API keys.
- No cloud dependency.
- Easy for judges to reproduce.

Cons:

- Not a full home-system demonstration.

## 2. iPhone Continuity Camera

Good demo source if stable.

Pros:

- High-quality camera.
- Uses existing Apple ecosystem.
- No custom IP camera setup.

Cons:

- Requires Apple Continuity setup.
- May behave differently on other machines.

## 3. RTSP IP camera

Best local-home-camera direction.

Pros:

- Local feed path.
- Common in security cameras/NVRs.
- Strong home appliance story.

Cons:

- Camera-specific setup.
- Credentials/network configuration.

### Tapo C210/C210P2 local RTSP path

For the hackathon lane, Tapo cameras are treated as explicit local RTSP sources only.

- One-time Tapo app setup is still required to put the device on the LAN and create a dedicated camera account.
- CareSight runtime uses local RTSP directly after setup; it does not use the Tapo cloud account at runtime.
- High quality stream: `rtsp://camera-user:camera-password@camera-ip:554/stream1`.
- Standard quality stream: `rtsp://camera-user:camera-password@camera-ip:554/stream2`.
- RTSP uses port `554`; ONVIF service metadata normally uses port `2020`.
- Keep the camera on the same LAN as the CareSight machine.
- Do not expose RTSP publicly, port-forward it, commit camera IPs, commit usernames, or commit passwords.

Probe local ignored configs with:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo.local.json
```

The probe prints a redacted receipt with reachability, stream open state, first-frame state, dimensions, and FPS when available. Live probes should use the YOLO26 venv because it contains OpenCV. A failed probe is a camera-health blocker, not a care event.

To open a local operator preview window without running the detector:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_camera_view.py \
  --config apps/caresight-hub/config/tapo_living_room.local.json
```

Press `q` or Esc to close the preview. This viewer is a local camera-health and framing check only; the bounded event loop still runs through `v0_floor_stay_live.py`.

Current dual-camera detector approach:

- Run one `v0_floor_stay_live.py` process per active camera.
- Give each process a unique `--obs-browser-feed-port`.
- Add one OBS Browser Source per local feed URL.
- Avoid shared `--obs-live-preview` output unless each process has a distinct preview path.
- Use `caresight_detector_start.py --appearance-overlay --stop-existing` for the current operator-friendly start path; it detaches the two detector processes, writes PID/log files, and reports feed health.
- `--appearance-overlay` draws bounded clothing descriptor sub-boxes only when YOLO26 emits a `person` detection. It is visible review evidence, not true segmentation, and it will not run when the detector labels a seated or partial person as furniture.

Example OBS feed URLs:

```text
http://127.0.0.1:8766/live.html  # Living Room
http://127.0.0.1:8767/live.html  # Kitchen
```

This is less efficient than a future single ingest/restream worker, because YOLO26 loads once per process. It is the best current app path because it reuses the proven bounded detector loop, SQLite audit writes, and OBS MJPEG browser feed without introducing a new unvalidated multi-camera scheduler.

Current recovery status: the committed example proves redaction and command behavior through `--dry-run`; the ignored local Living Room and Kitchen configs have now also produced owner-authorized live RTSP probe receipts with first frames at `1920x1080@15fps`. Do not commit real camera IPs, usernames, passwords, or frames.

### Discovery-assisted local config

The primary CareSight discovery step is owner-specified. The operator supplies the camera host or IP, and CareSight checks the expected RTSP/ONVIF ports, writes an ignored local config template, then hands off to the probe command.

```bash
python3 apps/caresight-hub/scripts/caresight_camera_discover.py \
  --host 192.168.1.50 \
  --camera-id tapo_living_room \
  --name "Tapo Living Room" \
  --room-id living_room \
  --room-label "Living Room" \
  --write-config apps/caresight-hub/config/tapo.local.json
```

Then edit `apps/caresight-hub/config/tapo.local.json` to replace the local camera password placeholder and run:

```bash
python3 apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo.local.json
```

This gives a one-command path into testing/configuration once the operator knows the camera's local IP. It still avoids unauthorized network discovery, credential guessing, and committed secrets.

If the operator does not know the local IP, CareSight now supports an explicit owner-authorized subnet scan:

```bash
python3 apps/caresight-hub/scripts/caresight_camera_discover.py \
  --subnet 10.0.0.0/24 \
  --allow-lan-scan \
  --scan-timeout-seconds 0.08 \
  --progress-every 32
```

This checks camera-candidate port reachability, reports ARP-visible hosts, and prints candidate next commands. If no camera ports are open, ARP-visible devices are listed as `unclassified_arp_hosts` with owner-specified follow-up commands, but they are not treated as confirmed cameras. The scan does not try credentials, open streams, identify camera brands, or write configs from a scan result. The expected flow is scan for candidates, choose the owned camera host, then rerun the host-specific config writer.

Latest local scan receipts:

- `192.168.1.0/24`: wrong subnet for this Mac; the active Wi-Fi address is `10.0.0.111`.
- `10.0.0.0/24`: 254 hosts checked with `--scan-timeout-seconds 0.12`; zero service-port candidates after excluding the Mac itself, but ARP-visible devices were present and surfaced as unclassified local hosts.
- Tapo C210 Living Room: ping reachable and ARP-visible; after Camera Account setup, host discovery is `rtsp_ready` with ports `554`, `2020`, and `443` open.
- Tapo C210 Kitchen: ping reachable and ARP-visible; after Camera Account setup, host discovery is `rtsp_ready` with ports `554`, `2020`, and `443` open.

That means the cameras may be on the LAN but not exposing the checked ports, RTSP/ONVIF may be disabled in the camera app, the cameras may be on a guest/VLAN-isolated SSID, or the actual camera IPs use a vendor-specific setup path before local RTSP is enabled.

### Tapo C210 local stream setup

Official Tapo guidance says wired Tapo cameras such as C210 support third-party RTSP and ONVIF, but not from the normal TP-Link/Tapo login alone. The operator must create a separate local Camera Account in the Tapo app before CareSight, VLC, Agent DVR, or another local client can authenticate to the stream.

App setup path:

1. Open the Tapo app and select the camera.
2. Open the camera's Device Settings.
3. Go to Advanced Settings.
4. Select Camera Account.
5. Create a local camera username and password distinct from the TP-Link cloud login.
6. Keep the laptop and camera on the same local network.
7. Rerun `caresight_camera_discover.py --host <camera-ip>` and expect RTSP `554` and/or ONVIF `2020` to become reachable before claiming live camera support.

Expected Tapo stream URLs after the Camera Account exists:

```text
rtsp://<camera-username>:<camera-password>@10.0.0.20:554/stream1
rtsp://<camera-username>:<camera-password>@10.0.0.20:554/stream2
rtsp://<camera-username>:<camera-password>@10.0.0.104:554/stream1
rtsp://<camera-username>:<camera-password>@10.0.0.104:554/stream2
```

`stream1` is the high-quality stream and `stream2` is the standard-quality stream. Tapo lists ONVIF service port `2020` and RTSP service port `554`; CareSight should continue to store credentials only in ignored `.local.json` files.

### Frigate architecture lessons

Frigate is a useful reference for the broader camera lane: config-first camera definitions, local RTSP/FFmpeg ingest, stream roles, health/retry behavior, restreaming to reduce camera connections, and optional ONVIF/go2rtc capabilities. Reference sources: [Frigate introduction](https://docs.frigate.video/) and [Frigate+ models](https://docs.frigate.video/plus/).

CareSight should borrow those concepts in this order:

1. Explicit camera registry with rooms, roles, privacy policy, and health.
2. Owner-specified discovery helper that creates ignored local configs.
3. Probe receipts that classify connection/auth/frame blockers.
4. Explicit owner-authorized subnet scan that identifies RTSP/ONVIF/service-port candidates without credentials and separately lists unclassified ARP-visible devices.
5. Optional local restream layer so YOLO, OBS, and review surfaces do not each open their own camera connection.
6. ONVIF metadata/discovery only after the operator explicitly enables it for owned cameras.
7. Event-scoped local recording clips with retention policy, attached to review packets as local evidence.
8. Low-latency browser live view, likely via a local restream/WebRTC/MSE-capable bridge rather than each surface opening the camera directly.
9. Optional local MQTT publishing for internal integration events, disabled by default and never used for emergency dispatch.
10. Separate detector process/queue so YOLO26 MLX inference does not block camera ingest, OBS feed serving, or caregiver review surfaces.

Frigate-derived features must be adapted to CareSight's bounded loop:

| Frigate concept | CareSight adaptation | Boundary |
| --- | --- | --- |
| go2rtc/restream | One local camera connection fan-outs to YOLO26, OBS, review UI, and optional browser live view. | Local-only; no cloud camera APIs by default. |
| MSE/WebRTC live view | Low-latency local review surface for operator/caregiver handoff. | Human-review surface, not automatic diagnosis. |
| MQTT events | Optional local state bus for OBS/dashboard/automation adapters. | Disabled by default; no autonomous dispatch topic. |
| Recording retention | Event-triggered clip around `possible_floor_stay` or missing-off-camera events. | Retain locally with configured days/size; clip is evidence, not confirmation. |
| Separate detector process | YOLO26 MLX worker pulls frames from queue and emits bounded observations. | Fail closed if worker lags; camera health is not a care event by itself. |
| Frigate+ attributes | Visible object/attribute boxes in Sprint 03 review artifacts. | No face recognition or named identity. |

CareSight should not become a full NVR in the hackathon lane. Frigate records and manages security-camera workflows; CareSight turns selected local observations into bounded caregiver review records.

## 4. Explicitly out of T027 deterministic scope

The deterministic v0 multi-camera config supports only configured `webcam`, `usb`, `continuity_camera`, and local `rtsp` sources. It does not perform unattended ONVIF discovery, unattended LAN scanning, Home Assistant entity lookup, Ring/Nest integration, cloud-camera API calls, or committed credential handling.

## Future: Ring / Nest

Valuable roadmap adapters, but not the MVP path.

Pros:

- Huge installed base.
- Familiar home devices.

Cons:

- Often cloud/API mediated.
- OAuth/certification/API restrictions.
- Live stream limits and account permissions.
- Not pure local LAN camera access in many cases.

---

# Camera adapter interface

```python
class CameraSource:
    camera_id: str
    room: str
    source_type: str

    def open(self) -> None: ...
    def read_frame(self) -> Frame: ...
    def health(self) -> CameraHealth: ...
    def close(self) -> None: ...
```

---

# Camera config example

```yaml
cameras:
  - id: living_room
    name: Living Room
    type: webcam
    device_index: 0
    enabled: true

  - id: kitchen_med_station
    name: Kitchen Medication Station
    type: rtsp
    uri: rtsp://192.0.2.55:554/stream1
    enabled: false
```

---

# Health checks

Each camera should expose:

- online/offline
- last frame timestamp
- FPS
- reconnect attempts
- dropped frames
- resolution
- source type

Camera offline should itself be a care event if the camera is critical.

For Sprint 05, camera open failure is represented as source health/blocker state first. It must not synthesize a `possible_floor_stay` or missing-person event.

---

# Ring adapter notes

Ring's official API supports OAuth, device discovery, notifications, WebRTC/WHEP live video, and historical media. However, this is a partner/API integration path, not simply a local RTSP feed from a doorbell.

Recommended product language:

> CareSight can process a Ring-authorized stream locally once delivered to the base unit, but Ring devices should be treated as optional cloud-mediated adapters, not the pure local MVP path.

---

# Nest / Google Home adapter notes

Google's Device Access APIs expose camera events and livestream capabilities for supported Nest devices, with registration and certification paths depending on usage. Legacy Nest camera paths may differ from Google Home migrated devices.

Recommended product language:

> CareSight can integrate with supported Nest/Google camera APIs in future versions, but the local-first home pilot should prioritize configured webcam, USB, Continuity Camera, and local RTSP sources.

---

# Hackathon recommendation

Implement:

- deterministic config entries for webcam, USB, Continuity Camera, and local RTSP sources
- source selection by configured `camera_id`
- SQLite-backed event provenance that carries the selected camera and room labels
- operator proof after camera authorization is granted

Do not spend challenge time on third-party cloud camera authentication.
