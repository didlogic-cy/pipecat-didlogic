# Changelog

All notable changes to **pipecat-didlogic** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-07

### Added

- `DidlogicFrameSerializer`, which converts between Pipecat audio frames and the
  DIDLogic voice-stream WebSocket protocol: PCM16 at 24 kHz in 10 ms frames,
  base64-encoded inside JSON messages.
- Inbound and outbound calls. The serializer reads `start` off the socket, so the
  call id, the two numbers and the direction need not be supplied up front.
- DTMF input as `InputDTMFFrame`, and `answered` surfaced to the pipeline as an
  `InputTransportMessageFrame` so a bot can hold its greeting until the far end
  picks up on an outbound call.
- Interruption handling via `clear`, and `hangup` on `EndFrame` or `CancelFrame`
  when `auto_hang_up` is left on.
- Two single-file examples: an inbound bot that answers a number, and an outbound
  bot that places a Click2Call and holds its greeting until `answered`.

Tested against Pipecat 1.12.0.
