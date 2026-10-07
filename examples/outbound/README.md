# DIDLogic chatbot: outbound

A bot that places the call: your server asks DIDLogic to dial a number, and the
bot is the agent leg.

## How it works

1. You `POST /call` with a number.
2. The server calls Click2Call with `a_type: stream`, pointing `a_endpoint` at its
   own `/ws`.
3. DIDLogic opens a WebSocket to `/ws` and sends `start`, then dials the customer.
4. **The bot's leg is answered before the customer's phone rings.** The bot stays
   quiet until the `answered` event says the customer picked up, then opens the
   conversation.
5. Audio flows both ways until either side hangs up.

Step 4 is the whole reason this example exists. Greeting when the socket opens
means the opening words are spoken to a line nobody is on yet.

## Architecture

```
POST /call -> server.py -> Click2Call API
                                  |
Customer <-> DIDLogic <-> WebSocket <-> server.py -> bot.py -> Deepgram / OpenAI / Cartesia
```

- `server.py` places calls and accepts the WebSocket
- `server_utils.py` holds the Click2Call request
- `bot.py` builds the pipeline, including `GreetWhenAnswered`

## Prerequisites

### DIDLogic

- An account with voice streaming enabled. If the API answers
  `422 a_type_unsupported`, it is not on yet — ask support.
- An API token from the portal.
- A five-digit SIP account. A stream call still bills and routes against one,
  even though the audio goes to your endpoint instead of a phone.

### AI services

Keys for [Deepgram](https://deepgram.com), [OpenAI](https://openai.com) and
[Cartesia](https://cartesia.ai).

### System

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- A public address for this server, since DIDLogic dials it.
  [ngrok](https://ngrok.com) is the usual choice in development.

## Setup

```bash
uv sync
cp env.example .env
```

Fill in `.env`: the three AI keys, `DIDLOGIC_API_TOKEN`, `DIDLOGIC_SIP_ACCOUNT`,
and `PUBLIC_WSS_URL` — the `wss://` base the platform should dial back on, with no
trailing slash.

## Run it

```bash
uv run server.py
```

Expose it, and put that host in `PUBLIC_WSS_URL`:

```bash
ngrok http 8080
```

## Make a call

```bash
curl -X POST http://localhost:8080/call \
  -H 'Content-Type: application/json' \
  -d '{"b_number": "12065550123"}'
```

`b_number` is E.164 digits with no leading plus. The response is the call in its
initial `accepted` state; `GET /api/v1/click2call/{id}` follows its progress.

You should see `start` logged at once, then `Customer answered` when the phone is
picked up, and the bot opens the conversation.

## Testing against a staging environment

Set `DIDLOGIC_API_BASE` in `.env` to that environment's API, and use a token
issued there. Left unset, calls go to production.

## Troubleshooting

**`401 Unauthorized`.** The token does not belong to the environment in
`DIDLOGIC_API_BASE` — most often a staging token sent to production, which is the
default. The response body says which status came back, so check it rather than
the server log.


**The bot talks to itself and the customer hears nothing of the opening.**
`GreetWhenAnswered` is missing or in the wrong place. It belongs directly after
`transport.input()`, so it sees the `answered` event before anything else.

**`422 invalid_a_endpoint`.** `PUBLIC_WSS_URL` must be a `wss://` URL on a public
host. DIDLogic checks it is reachable before placing the call, so a stale tunnel
host fails here rather than silently.

**`422 unknown_sip_account`.** `DIDLOGIC_SIP_ACCOUNT` must be one of your own
five-digit SIP accounts.
