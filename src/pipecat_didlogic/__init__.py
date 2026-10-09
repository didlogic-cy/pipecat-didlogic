#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""DIDLogic WebSocket call support for Pipecat.

Converts between Pipecat audio frames and the DIDLogic voice-stream protocol so
a Pipecat bot can answer and speak on a DIDLogic call.
"""

from .serializer import DidlogicFrameSerializer

__all__ = ["DidlogicFrameSerializer"]
__version__ = "1.0.1"
