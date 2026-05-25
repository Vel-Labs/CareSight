# CareSight Vertical Demo Voiceover

Target asset: `/Users/steven/Downloads/caresight_vertical.mp4`

Target duration: about 52 seconds, plus optional title and fade-out cards.

Recommended voice: Holler `dakota`.

Pronunciation note: keep visual copy as `YOLO26 MLX`, but use `Yo Low 26 M L X` in the TTS source.

## Voiceover

CareSight Hub is a local-first caregiver awareness loop.

In this journey demo, the bottom half shows the framework coming online: camera, policy, review state, and audit trail.

The top half shows the local camera view, where YOLO26 MLX turns motion into structured observations instead of streaming the home to the cloud.

When the system sees a possible floor stay, it does not decide what happened. It stores the event, drafts a caregiver alert, and waits for human review.

The escalation stays bounded: text first, then a reply-gated FaceTime handoff when the caregiver asks to see more.

The goal is simple: notice care-relevant moments, preserve local privacy, and keep the final call with a person.

## TTS Command

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py \
  --voice dakota \
  --text-file hackathon/video_assets/caresight_vertical_voiceover.txt \
  --output-dir hackathon/video_assets \
  --file-prefix caresight_vertical_voiceover \
  --max-tokens 700
```
