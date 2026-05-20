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

## 4. Explicitly out of T027 deterministic scope

The deterministic v0 multi-camera config supports only configured `webcam`, `usb`, `continuity_camera`, and local `rtsp` sources. It does not perform ONVIF discovery, LAN scanning, Home Assistant entity lookup, Ring/Nest integration, cloud-camera API calls, or credential handling.

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
    uri: rtsp://user:password@192.168.1.50/stream1
    enabled: false

  - id: front_door
    name: Front Door
    type: home_assistant
    entity_id: camera.front_door
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
