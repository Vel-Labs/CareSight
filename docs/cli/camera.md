# Camera Commands

Camera commands are operator-owned unless explicitly dry-run. They may touch local network resources, local camera streams, OpenCV windows, detector workers, or MJPEG feeds.

## Manual Operator

| Command | Purpose | Boundary |
| --- | --- | --- |
| `python3 apps/caresight-hub/scripts/caresight_camera_discover.py --host <camera_ip> --camera-id <camera_id> --write-config apps/caresight-hub/config/<camera_id>.local.json` | Check an owner-specified host for expected camera/service ports and write an ignored local config template. | No credential guessing, no network-range scan, no stream open. |
| `python3 apps/caresight-hub/scripts/caresight_camera_discover.py --subnet <local_subnet_cidr> --allow-lan-scan --scan-timeout-seconds 0.08 --progress-every 32` | Scan an explicitly authorized subnet for camera-candidate ports. | Refuses subnet scan without `--allow-lan-scan`; does not try credentials. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_camera_probe.py --config apps/caresight-hub/config/<camera_id>.local.json` | Probe one explicit local RTSP config and emit a redacted `runtime-validation-receipt`. | Does not create events, send messages, call FaceTime, play TTS, or export raw video. |
| `python3 apps/caresight-hub/scripts/caresight_camera_probe.py --config apps/caresight-hub/config/tapo.local.example.json --dry-run` | Prove config parsing and URI redaction only. | Dry-run is not live camera proof. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_camera_view.py --config apps/caresight-hub/config/<camera_id>.local.json` | Open one owner-authorized local camera in an OpenCV preview window. | No YOLO26, no events, no video storage. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_detector_start.py --appearance-overlay --stop-existing` | Start detached Living Room and Kitchen detector browser feeds for OBS. | Writes PID/log files and serves loopback feeds. |

## Local Feed Exposure

Detector browser feeds bind to loopback by default. LAN exposure is blocked unless all three flags are present:

```bash
--allow-lan-preview --preview-token <token> --ack-lan-preview-risk
```

LAN startup must emit a `local-feed-exposure` receipt with bind scope, token requirement, operator approval, expiration, and privacy-warning acknowledgement.

## Proof Boundary

`--dry-run` proves config parsing and redaction only. Live camera claims require an ignored local config plus a probe that receives a first frame or records a precise redacted blocker.
