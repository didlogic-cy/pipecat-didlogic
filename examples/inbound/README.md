# didlogic chatbot: inbound

A bot that answers calls to one of your didlogic numbers.

## How it works

1. Someone calls your number.
2. didlogic opens a WebSocket to `/ws` on this server and sends `start`.
3. Accepting the connection answers the call — the caller is already on the line,
   so the bot greets straight away.
4. Audio flows both ways until either side hangs up.

## Architecture

```
Caller <-> didlogic <-> WebSocket <-> server.py -> bot.py -> Deepgram / OpenAI / Cartesia
```

- `server.py` accepts the WebSocket
- `bot.py` builds and runs the pipeline

## Prerequisites

### didlogic

- An account with voice streaming enabled. If **WebSocket** is missing from the
  destination types in the portal, ask support to turn it on.
- A number you can route.

### AI services

Keys for [Deepgram](https://deepgram.com), [OpenAI](https://openai.com) and
[Cartesia](https://cartesia.ai).

### System

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- A way to expose this server publicly — didlogic dials your endpoint, so
  `localhost` is not reachable. [ngrok](https://ngrok.com) is the usual choice in
  development.

## Setup

```bash
uv sync
cp env.example .env     # then fill in the three API keys
```

## Run it

```bash
uv run server.py
```

Expose it:

```bash
ngrok http 8080
```

Then in the didlogic portal, open the number's routing and add a **WebSocket**
destination pointing at `wss://<your-ngrok-host>/ws`.

Call the number. You should see `start` logged, then the transcript of what you
say, and hear the reply.

## Troubleshooting

**The call connects but there is silence.** Check `add_wav_header=False` is set on
the transport params. Telephony audio carries no WAV header, and with one the
platform plays noise or nothing.

**Nothing reaches the server.** The destination URL has to be `wss://`, publicly
resolvable, and valid TLS. didlogic refuses a destination it cannot reach when you
save it, so a destination that saved but never connects usually means the tunnel
moved — ngrok gives a new host each restart on the free plan.
