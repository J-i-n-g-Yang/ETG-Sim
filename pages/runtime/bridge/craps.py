"""
Craps adapter for the ETG Sim GitHub Pages browser bridge.

Provides the browser-side equivalents of the stateful Craps Solo
endpoints while continuing to use game.craps_engine as the
authoritative game implementation.
"""

from __future__ import annotations

from decimal import Decimal

from bridge.common import (
    MAX_BET,
    json_safe,
)

from game import craps_engine


# ================================================================
# CRAPS ROLL
# ================================================================

def craps_roll(
    payload: dict,
) -> dict:

    game = str(
        payload.get(
            "game",
            "",
        )
    )

    if game != "craps":

        raise ValueError(
            f"Invalid Craps game: {game}"
        )

    raw_bets = (
        payload.get(
            "bets"
        )
        or []
    )

    if not isinstance(
        raw_bets,
        list,
    ):

        raise ValueError(
            "Bets must be a list"
        )

    clean_bets = []

    pending_total = Decimal(
        "0"
    )

    for bet in raw_bets:

        if not isinstance(
            bet,
            dict,
        ):

            raise ValueError(
                "Malformed Craps bet"
            )

        try:

            wager_type = str(
                bet[
                    "wager_type"
                ]
            )

            amount = Decimal(
                str(
                    bet[
                        "amount"
                    ]
                )
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            raise ValueError(
                "Malformed Craps bet"
            )

        if (
            not amount.is_finite()
            or amount <= 0
        ):

            raise ValueError(
                "Invalid Craps amount"
            )

        if not craps_engine.validate_wager(
            wager_type
        ):

            raise ValueError(
                f"Invalid Craps wager: "
                f"{wager_type}"
            )

        pending_total += amount

        clean_bets.append(
            (
                wager_type,
                amount,
            )
        )

    if pending_total > MAX_BET:

        raise ValueError(
            "Total new Craps stake per roll is "
            f"capped at {int(MAX_BET)} credits"
        )

    raw_state = (
        payload.get(
            "state"
        )
        or {}
    )

    result = craps_engine.roll(
        clean_bets,
        raw_state=raw_state,
    )

    return json_safe(
        result
    )


# ================================================================
# CRAPS ACTION
# ================================================================

def craps_action(
    payload: dict,
) -> dict:

    raw_state = (
        payload.get(
            "state"
        )
        or {}
    )

    wager_type = str(
        payload.get(
            "wager_type",
            "",
        )
    )

    action_name = str(
        payload.get(
            "action",
            "",
        )
    )

    if not wager_type:

        raise ValueError(
            "Missing Craps wager_type"
        )

    if action_name not in (
        "on",
        "off",
        "take_down",
    ):

        raise ValueError(
            f"Unknown Craps action: "
            f"{action_name}"
        )

    result = craps_engine.action(
        raw_state,
        wager_type,
        action_name,
    )

    return json_safe(
        result
    )
