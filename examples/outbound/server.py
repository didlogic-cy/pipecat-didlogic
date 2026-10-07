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

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from loguru import logger

from bot import run_bot
from server_utils import DialoutRequest, place_call

load_dotenv(override=True)

app = FastAPI()


def _upstream_body(response: httpx.Response):
    """Return the API's error body as JSON when it is JSON, else as text."""
    try:
        return response.json()
    except ValueError:
        return response.text


@app.post("/call")
async def call(request: DialoutRequest):
    """Place an outbound call with this server as the agent leg.

    A refusal from the API is reported as itself rather than as a crash: the
    response carries the upstream status and body, so a wrong token or an
    unreachable endpoint says so instead of surfacing a traceback.
    """
    try:
        return await place_call(request.b_number)
    except httpx.HTTPStatusError as error:
        status = error.response.status_code
        body = _upstream_body(error.response)
        logger.error(f"Click2Call refused the call: {status} {body}")

        return JSONResponse(status_code=status, content={"error": body})


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
