# Alert Lifecycle Follow-Up Cadence

Status: requested follow-up behavior, not yet implemented.

CareSight should support alert lifecycle messaging after the first caregiver alert:

1. Initial alert: concise bounded observation with room and time relevance.
2. Follow-up cadence: if the event remains unresolved, produce a short update at configured intervals.
3. Resolution update: when the situation appears resolved or is human-confirmed resolved, produce a final update with estimated total duration.

Bounded example language:

```text
CareSight update. The possible floor stay in the Living Room is still awaiting review. First observed around 7:41 PM.
```

```text
CareSight update. The Living Room concern appears resolved after about 9 minutes. Please review the local record when available.
```

Safety boundaries:

- Do not say the person is stable.
- Do not diagnose injury or medical status.
- Do not imply emergency dispatch.
- Keep raw video local.
- Require human review for final event status changes.
