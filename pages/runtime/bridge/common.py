"""
Shared helpers for the ETG Sim GitHub Pages browser bridge.

This module contains functionality shared by multiple browser-side
game adapters.

It is intentionally independent from solo_bridge.py so game-family
modules can import these helpers without creating circular imports.
"""

from __future__ import annotations

import importlib

from decimal import Decimal
from typing import Any

import game.registry as registry


# ================================================================
# LIMITS
# ================================================================

MAX_BET = Decimal(
    "20000"
)


# ================================================================
# JSON CONVERSION
# ================================================================

def json_safe(
    value: Any,
) -> Any:

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(
        value,
        Decimal,
    ):
        return float(
            value
        )

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key):
                json_safe(
                    item
                )

            for (
                key,
                item,
            )
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            json_safe(
                item
            )
            for item
            in value
        ]

    if hasattr(
        value,
        "__dict__",
    ):
        return json_safe(
            vars(
                value
            )
        )

    return str(
        value
    )


# ================================================================
# RUNTIME DIAGNOSTICS
# ================================================================

def runtime_info() -> dict:

    modules = [
        "game.registry",

        "game.baccarat_base",
        "game.baccarat_dragon_tiger",
        "game.baccarat_immortal",
        "game.baccarat_rising",

        "game.blackjack_base",
        "game.blackjack_lucky8",
        "game.blackjack_freebet",
        "game.blackjack_kingsbounty",
        "game.pontoon",

        "game.dice_engine",
        "game.sicbo",
        "game.great_fortune_dice",

        "game.craps",
        "game.craps_engine",

        "game.roulette_engine",
        "game.roulette_single_zero",
        "game.roulette_double_zero",
        "game.roulette_sands_roulette",

        "game.poker_base",
        "game.poker_engine",
        "game.poker_three_card_xtreme",
        "game.poker_singapore_stud",
        "game.poker_texas_holdem_bonus",
        "game.poker_ultimate_texas",
        "game.poker_mississippi_stud",
        "game.poker_fortune_pai_gow",
        "game.paigow_engine",

        "game.dueling_8s_21",
        "game.royal_three_pictures",
    ]

    imported = {}

    for module_name in modules:

        try:

            importlib.import_module(
                module_name
            )

            imported[
                module_name
            ] = True

        except Exception as exc:

            imported[
                module_name
            ] = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

    return {
        "ok":
            all(
                value is True
                for value
                in imported.values()
            ),

        "modules":
            imported,
    }


# ================================================================
# STATELESS BET VALIDATION
# ================================================================

def clean_bets(
    game: str,
    raw_bets: Any,
) -> tuple[
    list[
        tuple[
            str,
            Decimal,
        ]
    ],
    Decimal,
]:

    if not isinstance(
        raw_bets,
        list,
    ):
        raise ValueError(
            "Bets must be a list"
        )

    if not raw_bets:
        raise ValueError(
            "No bets supplied"
        )

    clean = []

    total = Decimal(
        "0"
    )

    for bet in raw_bets:

        if not isinstance(
            bet,
            dict,
        ):
            raise ValueError(
                "Malformed bet"
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
                "Malformed bet"
            )

        if (
            not amount.is_finite()
            or
            amount <= 0
            or
            amount > MAX_BET
        ):

            raise ValueError(
                "Invalid amount"
            )

        if not registry.validate_wager(
            game,
            wager_type,
        ):

            raise ValueError(
                f"Invalid wager_type for "
                f"{game}: {wager_type}"
            )

        total += amount

        clean.append(
            (
                wager_type,
                amount,
            )
        )

    if total > MAX_BET:

        raise ValueError(
            "Total stake per spin is "
            f"capped at {int(MAX_BET)} credits"
        )

    return (
        clean,
        total,
    )