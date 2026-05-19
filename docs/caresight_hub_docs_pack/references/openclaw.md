# OpenClaw Reference

## Role in CareSight

OpenClaw can act as an optional local gateway for message channels, hooks, and agent workflows.

## Possible CareSight uses

- event-driven hooks
- iMessage experimentation
- multi-channel alert routing
- daily memory snapshots
- caregiver reply workflows

## Security cautions

- Treat inbound messages as untrusted.
- Avoid host-level tool access for care workflows.
- Use strict allow-listed actions.
- Log all actions.
- Prefer CareSight's own policy guard before executing anything.

## Suggested integration stage

- v1: no dependency.
- v2: optional hook demo.
- v3+: serious gateway integration.

## Sources

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw Hooks Docs](https://docs.openclaw.ai/automation/hooks)
- [OpenClaw iMessage Docs](https://docs.openclaw.ai/channels/imessage)
