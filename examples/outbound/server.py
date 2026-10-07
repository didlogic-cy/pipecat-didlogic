#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""server.py

Server for outbound DIDLogic calls: ``POST /call`` places one through
Click2Call, and the platform connects the agent leg back to ``/ws``.
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket

from bot import run_bot
from server_utils import DialoutRequest, place_call

load_dotenv(override=True)

app = FastAPI()


@app.post("/call")
async def call(request: DialoutRequest):
    """Place an outbound call with this server as the agent leg."""
    return await place_call(request.b_number)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Run the bot on the agent leg the platform has connected."""
    await websocket.accept()
    await run_bot(websocket)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )
