"""
Poker adapter for the ETG Sim GitHub Pages browser bridge.

Provides the browser-side equivalents of the stateful Poker Solo
endpoints while continuing to use game.poker_engine as the
authoritative game implementation.
"""

from __future__ import annotations

from bridge.common import (
    MAX_BET,
    json_safe,
)

from game import poker_engine


# ================================================================
# STATEFUL POKER
#
# Browser equivalents of:
#
#   POST /api/solo/poker/deal
#   POST /api/solo/poker/action
#   POST /api/solo/poker/settle
#
# poker_engine already owns the authoritative state machine.
# ================================================================

def poker_deal(
    payload: dict,
) -> dict:

    game = str(
        payload.get(
            "game",
            "",
        )
    )

    bets = (
        payload.get(
            "bets"
        )
        or []
    )

    if game not in poker_engine.GAMES:

        raise ValueError(
            "Unknown poker game"
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

    total = 0.0

    clean = []

    # ------------------------------------------------------------
    # VALIDATE INITIAL BETS
    # ------------------------------------------------------------

    for bet in bets:

        try:

            seat = int(
                bet[
                    "seat"
                ]
            )

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

        except Exception as exc:

            raise ValueError(
                "Malformed bet"
            ) from exc

        if (
            seat not in (
                0,
                1,
                2,
            )
            or
            amount != amount
            or
            amount <= 0
            or
            amount > max_bet
        ):

            raise ValueError(
                "Invalid bet"
            )

        allowed = (
            poker_engine
            .allowed_initial_wagers(
                game,
                seat,
            )
        )

        if wager_type not in allowed:

            raise ValueError(
                "Invalid poker wager: "
                f"{wager_type}"
            )

        total += amount

        clean.append(
            {
                "seat":
                    seat,

                "wager_type":
                    wager_type,

                "amount":
                    amount,
            }
        )

    if total > max_bet:

        raise ValueError(
            "Total initial stake capped at "
            f"{int(max_bet)} credits"
        )

    # ------------------------------------------------------------
    # GROUP BY SEAT
    # ------------------------------------------------------------

    by_seat = {}

    for bet in clean:

        by_seat.setdefault(
            bet[
                "seat"
            ],
            {},
        )[
            bet[
                "wager_type"
            ]
        ] = bet[
            "amount"
        ]

    # ------------------------------------------------------------
    # VARIANT-SPECIFIC REQUIREMENTS
    # ------------------------------------------------------------

    for (
        seat,
        seat_bets,
    ) in by_seat.items():

        ante = float(
            seat_bets.get(
                f"seat{seat}_ante",
                0,
            )
        )

        if game == "poker_ultimate_texas":

            blind = float(
                seat_bets.get(
                    f"seat{seat}_blind",
                    0,
                )
            )

            if (
                ante <= 0
                or
                blind != ante
            ):

                raise ValueError(
                    "Ultimate Texas Hold'em "
                    "requires equal Ante and Blind"
                )

        elif game == "poker_three_card_xtreme":

            has_side = any(
                float(
                    seat_bets.get(
                        f"seat{seat}_{key}",
                        0,
                    )
                )
                >
                0
                for key in (
                    "pair_plus",
                    "six_card_bonus",
                )
            )

            if (
                ante <= 0
                and
                not has_side
            ):

                raise ValueError(
                    "No valid wager for seat"
                )

        else:

            if ante <= 0:

                raise ValueError(
                    "This Poker variant "
                    "requires an Ante wager"
                )

    # ------------------------------------------------------------
    # AUTHORITATIVE ENGINE DEAL
    # ------------------------------------------------------------

    state = poker_engine.deal(
        game,
        clean,
    )

    view = poker_engine.visible(
        state
    )

    view[
        "total_wager"
    ] = total

    view[
        "progressive_available"
    ] = (
        poker_engine
        .PROGRESSIVE_ENABLED
    )

    return json_safe(
        view
    )


def poker_action(
    payload: dict,
) -> dict:

    try:

        state = poker_engine.dec(
            str(
                payload.get(
                    "state_token",
                    "",
                )
            )
        )

    except Exception as exc:

        raise ValueError(
            "Invalid state token"
        ) from exc

    try:

        seat = int(
            payload.get(
                "seat",
                -1,
            )
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            "Invalid poker seat"
        ) from exc

    action_name = str(
        payload.get(
            "action",
            "",
        )
    )

    low_indices = payload.get(
        "low_indices"
    )

    extra = poker_engine.action(
        state,
        seat,
        action_name,
        low_indices=low_indices,
    )

    view = poker_engine.visible(
        state
    )

    view[
        "extra_stake"
    ] = extra

    return json_safe(
        view
    )


def poker_settle(
    payload: dict,
) -> dict:

    try:

        state = poker_engine.dec(
            str(
                payload.get(
                    "state_token",
                    "",
                )
            )
        )

    except Exception as exc:

        raise ValueError(
            "Invalid state token"
        ) from exc

    if (
        state.get(
            "stage"
        )
        !=
        "settle"
    ):

        raise ValueError(
            "Poker decisions are not complete"
        )

    output = poker_engine.settle(
        state
    )

    initial = sum(
        float(
            value
        )
        for seat_bets in
        state[
            "bets"
        ].values()
        for value in
        seat_bets.values()
    )

    total_wager = (
        initial
        +
        float(
            state.get(
                "extra",
                0,
            )
        )
    )

    output.update(
        {
            "game":
                state[
                    "game"
                ],

            "total_wager":
                total_wager,

            "net":
                (
                    float(
                        output[
                            "total_return"
                        ]
                    )
                    -
                    total_wager
                ),
        }
    )

    return json_safe(
        output
    )
