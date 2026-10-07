# pipecat-didlogic

DIDLogic WebSocket call support for [Pipecat](https://github.com/pipecat-ai/pipecat).

`DidlogicFrameSerializer` converts between Pipecat audio frames and the DIDLogic
voice-stream protocol, so a Pipecat bot can take a call on a DIDLogic number — or
be the agent leg of an outbound call — and speak on it.

Maintained by DIDLogic. We run the platform this talks to.

## What it handles

- **Audio both ways.** PCM16 at 24 kHz in 10 ms frames, base64-encoded inside
  JSON messages, resampled to and from whatever rate your pipeline runs at.
- **Inbound and outbound calls.** The serializer reads the `start` message off
  the socket, so the call id, the two numbers and the direction do not have to be
  known before the pipeline is built.
- **DTMF**, delivered to the pipeline as `InputDTMFFrame`.
- **Interruptions**, by sending `clear` so the platform drops audio it has
  buffered but not yet played.
- **Hanging up**, by sending `hangup` on `EndFrame` or `CancelFrame`. No
  credentials needed — it is one more message on the socket that is already open.
- **`answered`**, surfaced as an `InputTransportMessageFrame`. On an outbound
  call the platform answers your leg as soon as it has sent `start`, which is
  before the person has picked up; `answered` is what says they are there.

The protocol itself is documented at
[docs.didlogic.com](https://docs.didlogic.com/docs/guides/apps-developer-tools/websocket-calls).

## Install

```bash
uv add pipecat-didlogic
```

or:

```bash
pip install pipecat-didlogic
```

Tested with Pipecat 1.12.0.

## Use with a Pipecat pipeline

The serializer goes on the WebSocket transport's params. Telephony audio carries
no WAV header, so `add_wav_header` must be `False`:

```python
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from pipecat_didlogic import DidlogicFrameSerializer

transport = FastAPIWebsocketTransport(
    websocket=websocket,
    params=FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        add_wav_header=False,
        vad_analyzer=SileroVADAnalyzer(),
        serializer=DidlogicFrameSerializer(),
    ),
)
```

That is the whole integration. Everything else in the pipeline — STT, LLM, TTS —
is ordinary Pipecat.

### Options

```python
DidlogicFrameSerializer(
    DidlogicFrameSerializer.InputParams(
        didlogic_sample_rate=24000,  # what the platform sends and expects
        sample_rate=None,  # override the pipeline input rate
        auto_hang_up=True,  # send hangup on EndFrame / CancelFrame
    )
)
```

Pass `call_id`, `from_number`, `to_number` or `direction` to the constructor if
your server reads `start` before building the serializer. Leave them unset and
all four are learned from `start`.

### Waiting for an outbound call to be picked up

On an outbound call, hold the greeting until `answered` arrives:

```python
from pipecat.frames.frames import InputTransportMessageFrame, LLMRunFrame
from pipecat.processors.frame_processor import FrameProcessor


class GreetWhenAnswered(FrameProcessor):
    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if (
            isinstance(frame, InputTransportMessageFrame)
            and frame.message.get("event") == "answered"
        ):
            await self.push_frame(LLMRunFrame())

        await self.push_frame(frame, direction)
```

## Run the example

[`examples/inbound_bot.py`](examples/inbound_bot.py) is a complete inbound voice
bot in one file: Deepgram for speech-to-text, OpenAI for the reply, Cartesia for
speech.

1. Install the example's extra dependencies:

   ```bash
   uv sync --extra examples
   ```

2. Copy `.env.example` to `.env` and fill in the three API keys.

3. Run it:

   ```bash
   uv run examples/inbound_bot.py
   ```

4. Give it a public `wss://` address. The platform dials your endpoint, so it has
   to be reachable from the internet — in development, a tunnel is the usual way:

   ```bash
   ngrok http 8080
   ```

5. In the DIDLogic portal, add a **WebSocket** destination to one of your numbers
   pointing at `wss://<your-tunnel-host>/ws`.

Call the number. You should see the `start` message logged, then the transcript
of what you say, and hear the bot reply.

WebSocket destinations are enabled per account. If the type is missing from the
destination list, ask support to turn on voice streaming for your account.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## License

BSD 2-Clause. See [LICENSE](LICENSE).
