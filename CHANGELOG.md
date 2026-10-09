# Changelog

All notable changes to **pipecat-didlogic** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-10-09

### Changed

- The company name is written `didlogic` throughout the README, examples and
  docstrings, matching how the brand is styled.
- Copyright notices name the legal entity, `DID Logic PTE. LTD.`, as the main
  website does.

## [1.0.1] - 2026-10-09

### Fixed

- The `DidlogicFrameSerializer` docstring no longer points at
  `parse_telephony_websocket` as a way to read the handshake. That function cannot
  detect a didlogic call, because the runner support for it stayed out of Pipecat
  core. Documentation only, no behaviour change.
- The class docstring was indented one level too deep, so it rendered as a
  blockquote in tooltips and generated docs.

## [1.0.0] - 2026-10-09

### Added

- `DidlogicFrameSerializer`, which converts between Pipecat audio frames and the
  didlogic voice-stream WebSocket protocol: PCM16 at 24 kHz in 10 ms frames,
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
