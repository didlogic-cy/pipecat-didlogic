#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""Inbound voice bot on a DIDLogic WebSocket destination.

Run it, point a DIDLogic WebSocket destination at ``wss://<your-host>/ws``, and
call the number. The bot greets the caller and answers in speech.

The pipeline is the usual telephony shape::

    WebSocket in -> Deepgram STT -> OpenAI LLM -> Cartesia TTS -> WebSocket out

``DidlogicFrameSerializer`` reads the ``start`` message off the socket itself, so
nothing has to be parsed before the pipeline is built.
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from pipecat_didlogic import DidlogicFrameSerializer

load_dotenv()

app = FastAPI()

SYSTEM_PROMPT = (
    "You are a helpful telephone assistant. Keep your answers to one or two "
    "sentences, and speak them plainly: everything you say is read aloud."
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Answer one DIDLogic call and run the bot on it."""
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
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=True))

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        await task.queue_frames([LLMRunFrame()])

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
