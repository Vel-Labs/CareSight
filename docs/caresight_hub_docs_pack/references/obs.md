# OBS Reference

## Role in CareSight

OBS is the live-view presentation layer. It can route the right event scene into OBS Virtual Camera so FaceTime or another app sees the relevant camera/context.

## CareSight split

```text
CareSight analyzes raw camera feeds.
OBS presents selected scenes to humans.
```

## Key pieces

- OBS scenes for each camera/event view.
- obs-websocket for programmatic scene switching.
- OBS Virtual Camera for FaceTime/live video handoff.
- Overlay text source for event summary.

## Security

- Enable WebSocket password.
- Keep WebSocket local.
- Do not expose publicly.

## Sources

- [OBS Virtual Camera Guide](https://obsproject.com/kb/virtual-camera-guide)
- [OBS Developer Guide](https://obsproject.com/kb/developer-guide)
- [OBS Remote Control Guide](https://obsproject.com/kb/remote-control-guide)
- [obs-websocket GitHub](https://github.com/obsproject/obs-websocket)
