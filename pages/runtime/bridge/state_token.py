"""
Shared state-token codec for the ETG Sim GitHub Pages browser bridge.

Interactive browser games store their state inside a compact Base64
encoded JSON token so the static GitHub Pages edition can remain
serverless.
"""

from __future__ import annotations

import base64
import json


# ================================================================
# STATE TOKEN
# ================================================================

def encode_state(
    state: dict,
) -> str:

    raw = json.dumps(
        state,
        separators=(
            ",",
            ":",
        ),
    )

    return base64.b64encode(
        raw.encode()
    ).decode()


def decode_state(
    token: str,
) -> dict:

    if not token:

        raise ValueError(
            "Invalid state token"
        )

    try:

        raw = base64.b64decode(
            token.encode()
        ).decode()

        state = json.loads(
            raw
        )

    except Exception as exc:

        raise ValueError(
            "Invalid state token"
        ) from exc

    if not isinstance(
        state,
        dict,
    ):

        raise ValueError(
            "Invalid state token"
        )

    return state
