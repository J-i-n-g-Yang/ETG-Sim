"""
Stateless game adapter for the ETG Sim GitHub Pages browser bridge.

Handles games whose complete round can be resolved in a single
browser-side operation.

The underlying ETG game modules remain authoritative for wager
validation, outcome generation and payouts.
"""

from __future__ import annotations

from decimal import Decimal

import game.registry as registry

from bridge.common import (
    clean_bets,
    json_safe,
)


# ================================================================
# SUPPORTED STATELESS GAMES
# ================================================================

STATELESS_GAMES = {
    # Baccarat
    "baccarat_dragon_tiger",
    "baccarat_immortal",
    "baccarat_rising",

    # Dice
    "sicbo",
    "great_fortune_dice",

    # Roulette
    "roulette_single_zero",
    "roulette_double_zero",
    "roulette_sands",

    # Royal Three Pictures
    "royal_three_pictures",
}


# ================================================================
# STATELESS SOLO SPIN
# ================================================================

def solo_spin(
    payload: dict,
) -> dict:

    game = str(
        payload.get(
            "game",
            "",
        )
    )

    if game not in STATELESS_GAMES:

        raise ValueError(
            "Game is not available through "
            f"stateless spin: {game}"
        )

    bets, total_wager = clean_bets(
        game,
        payload.get(
            "bets"
        ),
    )

    module = registry.get_module(
        game
    )

    outcome = module.resolve()

    results = []

    total_return = Decimal(
        "0"
    )

    for (
        wager_type,
        amount,
    ) in bets:

        returned = module.payout(
            wager_type,
            amount,
            outcome,
        )

        returned = Decimal(
            str(
                returned
            )
        )

        total_return += returned

        results.append(
            {
                "wager_type":
                    wager_type,

                "amount":
                    float(
                        amount
                    ),

                "return":
                    float(
                        returned
                    ),

                "win":
                    returned >
                    amount,
            }
        )

    return {
        "game":
            game,

        "outcome":
            json_safe(
                outcome
            ),

        "total_wager":
            float(
                total_wager
            ),

        "total_return":
            float(
                total_return
            ),

        "net":
            float(
                total_return -
                total_wager
            ),

        "results":
            results,
    }