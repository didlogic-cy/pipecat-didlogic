#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""Helpers for setting up frame processors outside a pipeline."""

from pipecat.clocks.system_clock import SystemClock
from pipecat.processors.frame_processor import FrameProcessorSetup
from pipecat.utils.asyncio.task_manager import BaseTaskManager


def frame_processor_setup(
    task_manager: BaseTaskManager | None = None, **kwargs
) -> FrameProcessorSetup:
    """Build a setup configuration for a processor used outside a pipeline.

    Args:
        task_manager: The task manager the processor should run its tasks on.
            Omit it when the processor under test creates no tasks.
        **kwargs: Any FrameProcessorSetup field to override.

    Returns:
        A setup carrying a system clock and no pipeline worker.
    """
    kwargs.setdefault("clock", SystemClock())
    kwargs.setdefault("pipeline_worker", None)
    return FrameProcessorSetup(task_manager=task_manager, **kwargs)  # pyright: ignore[reportArgumentType]
