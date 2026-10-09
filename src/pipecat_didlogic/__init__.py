#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""didlogic WebSocket call support for Pipecat.

Converts between Pipecat audio frames and the didlogic voice-stream protocol so
a Pipecat bot can answer and speak on a didlogic call.
"""

from .serializer import DidlogicFrameSerializer

__all__ = ["DidlogicFrameSerializer"]
__version__ = "1.0.2"
