"""
ETG Sim — GitHub Pages browser bridge.

Runs entirely inside Pyodide.

This module reproduces selected /api/solo contracts inside the
browser while continuing to use the existing ETG Python game
engines as the authoritative implementation.

Supported:
- Stateless solo spin games
- Stateful Craps
- Interactive Blackjack family
- Interactive Poker family

This module is the public browser entry point for the GitHub Pages
runtime.

Game-family implementations live in bridge modules while this file
preserves the operation names and JSON boundary expected by the
JavaScript runtime.
"""

from __future__ import annotations

import json
import traceback

from bridge.common import (
    json_safe,
    runtime_info,
)
from bridge.stateless import (
    solo_spin,
)
from bridge.craps import (
    craps_roll,
    craps_action,
)
from bridge.roulette import (
    roulette_spin,
)
from bridge.royal_three_pictures import (
    royal_three_pictures_deal,
)
from bridge.poker import (
    poker_deal,
    poker_action,
    poker_settle,
)
from bridge.blackjack import (
    blackjack_deal,
    blackjack_action,
    blackjack_settle,
)
from bridge.dueling_8s import (
    dueling_8s_deal,
    dueling_8s_action,
    dueling_8s_settle,
)


# ================================================================
# COMMON BRIDGE COMPATIBILITY
#
# Keep the historical private JSON helper name because the existing
# Pages bridge contract tests exercise it directly.
# ================================================================

_json_safe = json_safe


# ================================================================
# DISPATCH
# ================================================================

def dispatch(
    operation: str,
    payload: dict | None = None,
) -> dict:

    payload = (
        payload
        if isinstance(
            payload,
            dict,
        )
        else
        {}
    )

    if operation == "runtime_info":

        return runtime_info()

    if operation in (
        "solo_spin",
        "baccarat_spin",
    ):

        return solo_spin(
            payload
        )

    if operation == "roulette_spin":

        return roulette_spin(
            payload
        )

    if operation == "royal_three_pictures_deal":

        return royal_three_pictures_deal(
            payload
        )

    if operation == "craps_roll":

        return craps_roll(
            payload
        )

    if operation == "craps_action":

        return craps_action(
            payload
        )

    if operation == "blackjack_deal":

        return blackjack_deal(
            payload
        )

    if operation == "blackjack_action":

        return blackjack_action(
            payload
        )

    if operation == "blackjack_settle":

        return blackjack_settle(
            payload
        )

    if operation == "poker_deal":

        return poker_deal(
            payload
        )

    if operation == "poker_action":

        return poker_action(
            payload
        )

    if operation == "poker_settle":

        return poker_settle(
            payload
        )

    if operation == "dueling_8s_deal":

        return dueling_8s_deal(
            payload
        )

    if operation == "dueling_8s_action":

        return dueling_8s_action(
            payload
        )

    if operation == "dueling_8s_settle":

        return dueling_8s_settle(
            payload
        )

    raise ValueError(
        "Unknown ETG browser operation: "
        f"{operation}"
    )


# ================================================================
# JSON BOUNDARY
# ================================================================

def dispatch_json(
    operation: str,
    payload_json: str,
) -> str:

    try:

        payload = (
            json.loads(
                payload_json
            )
            if payload_json
            else
            {}
        )

        result = dispatch(
            operation,
            payload,
        )

        response = {
            "ok":
                True,

            "result":
                _json_safe(
                    result
                ),
        }

    except Exception as exc:

        response = {
            "ok":
                False,

            "error":
                str(
                    exc
                ),

            "type":
                type(
                    exc
                ).__name__,

            "traceback":
                traceback.format_exc(),
        }

    return json.dumps(
        response,
        separators=(
            ",",
            ":",
        ),
    )
