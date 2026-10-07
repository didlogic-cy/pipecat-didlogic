#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""server.py

WebSocket server for inbound DIDLogic calls. A WebSocket destination on one of
your numbers points at ``/ws``; every call that arrives gets a bot.
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket

from bot import run_bot

load_dotenv(override=True)

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accept one call and run the bot on it."""
    await websocket.accept()
    await run_bot(websocket)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )
