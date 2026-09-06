"""
Roulette adapter for the ETG Sim GitHub Pages browser bridge.

Provides the browser-side equivalent of the Roulette Solo spin
endpoint while continuing to use game.roulette_engine as the
authoritative game implementation.
"""

from __future__ import annotations

from bridge.common import (
    MAX_BET,
    json_safe,
)

import game.roulette_engine as roulette_engine


# ================================================================
# ROULETTE
#
# Browser equivalent of:
#
#   POST /api/solo/roulette/spin
#
# Keep roulette_engine.spin authoritative so the Pages edition
# matches the Flask Solo endpoint.
# ================================================================

def roulette_spin(
    payload: dict,
) -> dict:

    game = str(
        payload.get(
            "game",
            "",
        )
    )

    bets = payload.get(
        "bets"
    )

    valid_games = (
        "roulette_single_zero",
        "roulette_double_zero",
        "roulette_sands",
    )

    if game not in valid_games:

        raise ValueError(
            "Unknown Roulette game"
        )

    if (
        not isinstance(
            bets,
            list,
        )
        or
        not bets
    ):

        raise ValueError(
            "No bets supplied"
        )

    max_bet = float(
        MAX_BET
    )

    clean = []

    total = 0.0

    for bet in bets:

        try:

            wager_type = str(
                bet[
                    "wager_type"
                ]
            )

            amount = float(
                bet[
                    "amount"
                ]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Malformed bet"
            ) from exc

        if (
            amount != amount
            or
            amount <= 0
            or
            amount > max_bet
        ):

            raise ValueError(
                "Invalid amount"
            )

        if not roulette_engine.validate_wager(
            game,
            wager_type,
        ):

            raise ValueError(
                f"Invalid wager_type for "
                f"{game}: {wager_type}"
            )

        total += amount

        clean.append(
            {
                "wager_type":
                    wager_type,

                "amount":
                    amount,
            }
        )

    if total > max_bet:

        raise ValueError(
            "Total stake per spin is capped at "
            f"{int(max_bet)} credits"
        )

    result = roulette_engine.spin(
        game,
        clean,
    )

    return json_safe(
        result
    )
