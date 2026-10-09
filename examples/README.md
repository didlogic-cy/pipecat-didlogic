# didlogic voice bot examples

Two voice bots built on `pipecat-didlogic`, covering both directions a didlogic
stream call can run in.

## Examples

### [Inbound](./inbound/)

Someone calls one of your numbers and talks to the bot. A WebSocket destination on
the number points at your server.

### [Outbound](./outbound/)

The bot places the call. Your server asks Click2Call to dial a number, didlogic
connects the bot as the agent leg, and the bot speaks once the customer picks up.

## Architecture

Both share the same shape:

```
Phone call <-> didlogic <-> voice stream (WebSocket) <-> Pipecat <-> AI services
```

- **didlogic** routes the call and carries the audio
- **The voice stream** is PCM16 at 24 kHz in 10 ms frames, base64 inside JSON
- **`DidlogicFrameSerializer`** translates that to and from Pipecat frames
- **AI services** here are Deepgram (STT), OpenAI (LLM) and Cartesia (TTS)

## The difference that matters

Inbound, the caller is already on the line when the socket opens, so the bot can
greet immediately.

Outbound, didlogic answers the bot's leg as soon as it has sent `start` — before
the customer's phone has rung. Greeting then means talking to nobody. The
outbound example waits for the `answered` event instead, which is what says the
person has picked up.

## Getting help

- Per-example setup: the README in [`inbound/`](./inbound/) and [`outbound/`](./outbound/)
- Protocol reference: [didlogic WebSocket calls](https://docs.didlogic.com/docs/guides/apps-developer-tools/websocket-calls)
- Pipecat documentation: [docs.pipecat.ai](https://docs.pipecat.ai)
