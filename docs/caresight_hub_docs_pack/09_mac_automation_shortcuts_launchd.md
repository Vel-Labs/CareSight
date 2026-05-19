# macOS Automation: Shortcuts, FaceTime, launchd, Notes

## Automation philosophy

macOS integrations are excellent for demo polish and household workflows, but they should be adapters around the core engine.

Core engine:

```text
camera → YOLO26 MLX → event → SQLite
```

macOS adapters:

```text
SQLite event → Shortcut / FaceTime / Notes / notification / OBS
```

---

# Apple Shortcuts

Shortcuts can be invoked from Terminal with the `shortcuts` command. This makes it useful for:

- sending a message or notification
- appending to a note
- creating a reminder
- running a scripted handoff
- saving output to a file

## Example CLI commands

```bash
shortcuts list
shortcuts run "CareSight Alert" --input-path ./latest_alert.json
shortcuts run "CareSight Journal Append" --input-path ./daily_journal.md
```

## Recommended shortcuts

### CareSight Alert

Input: JSON alert.

Action:

- parse text
- send message to configured caregiver or show notification
- optionally open event dashboard URL

### CareSight Journal Append

Input: Markdown journal entry.

Action:

- append to shared note or create a daily note

### CareSight FaceTime

Input: caregiver handle.

Action:

- open FaceTime link

---

# FaceTime URL handoff

A FaceTime handoff can be represented as:

```bash
open "facetime:caregiver@example.com"
```

or:

```bash
open "facetime:+15551234567"
```

Do not guarantee fully automated connection. macOS may prompt. The demo can show the handoff opening FaceTime.

---

# Apple Notes / shared journal

## Recommended strategy

- Generate daily Markdown from SQLite.
- Optionally append the Markdown to Apple Notes with a Shortcut.
- Keep SQLite as the source of truth.

## Why not make Notes the database?

Notes is excellent for humans but weak for structured event queries, permissions, and audit trails.

---

# launchd startup

The base unit should behave like an appliance.

```text
Mac boots
  → launchd starts CareSight core
  → user-session LaunchAgent starts OBS/Shortcuts-dependent helpers
  → cameras reconnect
  → dashboard starts
  → monitoring begins
```

## LaunchDaemon vs LaunchAgent

### LaunchDaemon

Good for:

- non-UI services
- local API
- database maintenance
- health checks

### LaunchAgent

Good for:

- OBS
- FaceTime handoff
- Shortcuts
- Notes automation
- anything requiring user session permissions

---

# Suggested base-unit setup

- Dedicated macOS user: `caresight`.
- Non-admin if possible.
- Auto-start CareSight services.
- Lock down OBS WebSocket.
- Grant required camera permissions.
- Configure FaceTime camera once to OBS Virtual Camera if using OBS.
- Keep all raw video local by default.

---

# Health checks

CareSight should monitor:

- camera frame freshness
- YOLO loop FPS
- SQLite write success
- dashboard health
- OBS WebSocket connectivity
- virtual camera status when available
- Shortcut execution result

---

# Example action adapter design

```python
class ShortcutAction:
    def __init__(self, shortcut_name: str):
        self.shortcut_name = shortcut_name

    def run(self, input_path: str) -> int:
        return subprocess.run([
            "shortcuts", "run", self.shortcut_name,
            "--input-path", input_path,
        ]).returncode
```

---

# MVP recommendation

Implement only one macOS action for v1. The simplest choices are:

1. macOS notification
2. Shortcut-driven journal append
3. Shortcut-driven message alert

Add FaceTime/OBS only after the core demo is stable.
