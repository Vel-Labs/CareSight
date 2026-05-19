# Alert Templates

## High-priority safety event

```text
CareSight Alert — High Priority

Possible floor-stay event in {room}.
Duration: {duration_seconds} seconds.
Confidence: {confidence_label}.
Raw video remains local.

Actions:
[View Event] [Acknowledge] [FaceTime] [Mark False Positive]
```

## Medication routine

```text
CareSight Routine Update

Medication routine likely observed at {time}.
Evidence: {evidence_summary}.
Status: awaiting confirmation.

Actions:
[Confirm] [Dismiss] [Add Note]
```

## Missed routine

```text
CareSight Reminder

{routine_name} has not been observed within the expected window.
Expected: {window_start}–{window_end}.

Actions:
[Check In] [Mark Completed] [Snooze]
```

## Pet sitter event

```text
CareSight Pet Care

Pet food area activity observed at {time}.
Pet: {subject_name}.
Duration: {duration_seconds} seconds.

Actions:
[Confirm Fed] [Add Note]
```
