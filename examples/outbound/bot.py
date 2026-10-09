#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""bot.py

The pipeline for the agent leg of an outbound didlogic call.

The one thing that differs from inbound: the platform answers this leg as soon as
it has sent ``start``, which is before the customer's phone has rung. A bot that
greets on connect talks to an empty line and loses its opening words, so
``GreetWhenAnswered`` holds the first turn until the ``answered`` event arrives.
"""

import os

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
from pipecat_didlogic import DidlogicFrameSerializer

SYSTEM_PROMPT = (
    "You are calling on behalf of a shop to confirm a delivery time. Open by "
    "saying who you are and why you are calling. Keep every answer to one or two "
    "sentences, and speak them plainly: everything you say is read aloud."
)


class GreetWhenAnswered(FrameProcessor):
    """Start the conversation when the customer picks up, not when the socket opens."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Pass every frame through, and queue the first turn on ``answered``."""
        await super().process_frame(frame, direction)

        if (
            isinstance(frame, InputTransportMessageFrame)
            and frame.message.get("event") == "answered"
        ):
            logger.info("Customer answered - starting the conversation")
            await self.push_frame(LLMRunFrame())

        await self.push_frame(frame, direction)


async def run_bot(websocket):
    """Run the bot on the agent leg didlogic has just connected.

    Args:
        websocket: The accepted FastAPI WebSocket the platform connected.
    """
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
