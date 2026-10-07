#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""Outbound voice bot: the bot is the agent leg of a DIDLogic Click2Call.

Where the inbound example waits for a call, this one places it. POST to
``/call`` with a number and DIDLogic dials two legs: your WebSocket endpoint as
the agent, and the number as the customer. Once the customer picks up, the two
are bridged and the bot talks to them.

Why this is not just the inbound example with a REST call bolted on:

DIDLogic answers the bot's leg as soon as it has sent ``start``, which is before
the customer's phone has even rung. Greeting on connect would mean talking to an
empty line and losing the opening line. ``answered`` is the event that says the
customer is on, so the greeting waits for it — that is what ``GreetWhenAnswered``
below is for.
"""

import os

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import Frame, InputTransportMessageFrame, LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pydantic import BaseModel

from pipecat_didlogic import DidlogicFrameSerializer

load_dotenv()

app = FastAPI()

API_BASE = "https://didlogic.com/api/v1"

SYSTEM_PROMPT = (
    "You are calling on behalf of a shop to confirm a delivery time. Open by "
    "saying who you are and why you are calling. Keep every answer to one or two "
    "sentences, and speak them plainly: everything you say is read aloud."
)


class GreetWhenAnswered(FrameProcessor):
    """Start the conversation when the customer picks up, not when the socket opens.

    On an outbound call the platform answers the bot's leg before the customer's
    phone rings, so ``on_client_connected`` is too early to greet. This waits for
    the ``answered`` event and queues the first LLM turn then.
    """

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Pass every frame through, and greet once ``answered`` arrives."""
        await super().process_frame(frame, direction)

        if (
            isinstance(frame, InputTransportMessageFrame)
            and frame.message.get("event") == "answered"
        ):
            logger.info("Customer answered — starting the conversation")
            await self.push_frame(LLMRunFrame())

        await self.push_frame(frame, direction)


class CallRequest(BaseModel):
    """The number to call, in E.164 without the leading plus."""

    b_number: str


@app.post("/call")
async def place_call(request: CallRequest):
    """Ask DIDLogic to dial the customer, with this bot as the agent leg."""
    payload = {
        "a_type": "stream",
        "a_endpoint": f"{os.environ['PUBLIC_WSS_URL']}/ws",
        "sip_account": os.environ["DIDLOGIC_SIP_ACCOUNT"],
        "b_number": request.b_number,
    }

    stream_token = os.getenv("DIDLOGIC_STREAM_TOKEN")
    if stream_token:
        payload["stream_token"] = stream_token

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/click2call",
            json=payload,
            headers={"Authorization": f"Bearer {os.environ['DIDLOGIC_API_TOKEN']}"},
            timeout=30,
        )

    response.raise_for_status()

    return response.json()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Run the bot on the agent leg DIDLogic has just connected."""
    await websocket.accept()

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

    stt = DeepgramSTTService(api_key=os.environ["DEEPGRAM_API_KEY"])
    llm = OpenAILLMService(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o-mini")
    tts = CartesiaTTSService(
        api_key=os.environ["CARTESIA_API_KEY"],
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",
    )

    context = LLMContext([{"role": "system", "content": SYSTEM_PROMPT}])
    context_aggregator = LLMContextAggregatorPair(context)

    pipeline = Pipeline(
        [
            transport.input(),
            GreetWhenAnswered(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=True))

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await task.cancel()

    await PipelineRunner(handle_sigint=False).run(task)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )
