# Ring and Google Nest Reference

## Role in CareSight

Ring and Nest are important roadmap adapters because many homes already have them. They should not be the hackathon MVP dependency.

## Ring notes

Ring's Partner API supports OAuth, device discovery, notifications, live video streaming, and media access through official API flows. Treat Ring as a cloud/API-mediated adapter, not as a pure local RTSP camera source.

## Nest / Google notes

Google Device Access supports supported Nest camera livestreams, events, and device data, with project registration and certification paths depending on use. Legacy Nest and Google Home camera behavior can differ.

## MVP recommendation

Document adapters and maybe create stubs, but demo with webcam/RTSP.

## Sources

- [Ring Partner API Documentation](https://developer.amazon.com/docs/ring/api-documentation.html)
- [Ring Partner API Getting Started](https://developer.amazon.com/docs/ring/get-started.html)
- [Google Nest Device Access](https://developers.google.com/nest/device-access)
- [Google Nest Camera API](https://developers.google.com/nest/device-access/api/camera)
- [Google Nest Wired Camera API](https://developers.google.com/nest/device-access/api/camera-wired)
