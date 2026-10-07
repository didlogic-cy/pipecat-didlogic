#
# Copyright (c) 2026, DIDLogic
#
# SPDX-License-Identifier: BSD-2-Clause
#

"""server_utils.py

The Click2Call request that places an outbound call with a stream agent leg.
"""

import os

import httpx
from pydantic import BaseModel

API_BASE = "https://didlogic.com/api/v1"


class DialoutRequest(BaseModel):
    """The number to call, in E.164 digits without the leading plus."""

    b_number: str


async def place_call(b_number: str) -> dict:
    """Ask DIDLogic to dial a number with this server as the agent leg.

    Args:
        b_number: The number to call, E.164 digits without a leading plus.

    Returns:
        The call resource, in its initial ``accepted`` state.

    Raises:
        httpx.HTTPStatusError: If the API refuses the call.
    """
    payload = {
        "a_type": "stream",
        "a_endpoint": f"{os.environ['PUBLIC_WSS_URL']}/ws",
        "sip_account": os.environ["DIDLOGIC_SIP_ACCOUNT"],
        "b_number": b_number,
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
