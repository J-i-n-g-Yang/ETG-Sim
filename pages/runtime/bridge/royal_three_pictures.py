"""
Royal Three Pictures adapter for the ETG Sim GitHub Pages browser bridge.

Provides the browser-side equivalent of the Royal Three Pictures
Solo deal endpoint while continuing to use game.royal_three_pictures
as the authoritative game implementation.
"""

from __future__ import annotations

from decimal import Decimal

from bridge.common import (
    MAX_BET,
)

import game.royal_three_pictures as royal_three_pictures


# ================================================================
# ROYAL THREE PICTURES
#
# Browser equivalent of:
#
#   POST /api/solo/royal-three-pictures/deal
#
# This intentionally mirrors the Flask Solo endpoint because
# Royal Three Pictures uses a three-seat response contract.
# ================================================================

def royal_three_pictures_deal(
    payload: dict,
) -> dict:

    game = str(
        payload.get(
            "game",
            "",
        )
    )

    game_id = (
        "royal_three_pictures"
    )

    if (
        game
        and
        game != game_id
    ):

        raise ValueError(
            "Unknown Royal Three Pictures game"
        )

    bets = payload.get(
        "bets"
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

    bets_by_seat = {}

    total_wager = 0.0

    # ------------------------------------------------------------
    # VALIDATE BETS
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
            ).strip().lower()

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

        if seat not in (
            0,
            1,
            2,
        ):

            raise ValueError(
                "Invalid Royal Three Pictures seat"
            )

        if not royal_three_pictures.validate_wager(
            wager_type
        ):

            raise ValueError(
                "Invalid Royal Three Pictures wager: "
                f"{wager_type}"
            )

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

        seat_key = str(
            seat
        )

        seat_bets = (
            bets_by_seat
            .setdefault(
                seat_key,
                {},
            )
        )

        seat_bets[
            wager_type
        ] = (
            float(
                seat_bets.get(
                    wager_type,
                    0,
                )
            )
            +
            amount
        )

        total_wager += amount

    if total_wager > max_bet:

        raise ValueError(
            "Total initial stake capped at "
            f"{int(max_bet)} credits"
        )

    active_seats = sorted(
        int(
            key
        )
        for key in
        bets_by_seat
    )

    for seat in active_seats:

        if (
            float(
                bets_by_seat[
                    str(
                        seat
                    )
                ].get(
                    "main",
                    0,
                )
            )
            <=
            0
        ):

            raise ValueError(
                f"Seat {seat + 1} "
                "requires a Main wager"
            )

    # ------------------------------------------------------------
    # DEAL
    # ------------------------------------------------------------

    deck = royal_three_pictures.make_deck()

    player_hands = {}

    for seat in active_seats:

        player_hands[
            str(
                seat
            )
        ] = [
            deck.pop(0),
            deck.pop(0),
            deck.pop(0),
        ]

    dealer_cards = [
        deck.pop(0),
        deck.pop(0),
        deck.pop(0),
    ]

    total_return = Decimal(
        "0"
    )

    results = []

    outcome_seats = {}

    visible_seats = {}

    # ------------------------------------------------------------
    # SETTLE SEATS
    # ------------------------------------------------------------

    for seat in active_seats:

        seat_key = str(
            seat
        )

        cards = player_hands[
            seat_key
        ]

        seat_bets = bets_by_seat[
            seat_key
        ]

        main_result = (
            royal_three_pictures
            .compare_hands(
                cards,
                dealer_cards,
            )
        )

        tie_result = (
            royal_three_pictures
            .is_tie(
                cards,
                dealer_cards,
            )
        )

        royal_result = (
            royal_three_pictures
            .royal_pictures_result(
                cards
            )
        )

        seat_return = Decimal(
            "0"
        )

        # --------------------------------------------------------
        # MAIN
        # --------------------------------------------------------

        main_stake = Decimal(
            str(
                seat_bets[
                    "main"
                ]
            )
        )

        main_return = (
            royal_three_pictures
            .main_return(
                main_stake,
                cards,
                dealer_cards,
            )
        )

        seat_return += main_return

        total_return += main_return

        results.append(
            {
                "seat":
                    seat,

                "wager_type":
                    "main",

                "amount":
                    float(
                        main_stake
                    ),

                "return":
                    float(
                        main_return
                    ),

                "win":
                    main_return >
                    main_stake,

                "result":
                    main_result,
            }
        )

        # --------------------------------------------------------
        # TIE
        # --------------------------------------------------------

        tie_stake = Decimal(
            str(
                seat_bets.get(
                    "tie",
                    0,
                )
            )
        )

        if tie_stake > 0:

            tie_return = (
                royal_three_pictures
                .tie_return(
                    tie_stake,
                    cards,
                    dealer_cards,
                )
            )

            seat_return += tie_return

            total_return += tie_return

            results.append(
                {
                    "seat":
                        seat,

                    "wager_type":
                        "tie",

                    "amount":
                        float(
                            tie_stake
                        ),

                    "return":
                        float(
                            tie_return
                        ),

                    "win":
                        tie_return > 0,
                }
            )

        # --------------------------------------------------------
        # ROYAL PICTURES
        # --------------------------------------------------------

        royal_stake = Decimal(
            str(
                seat_bets.get(
                    "royal_pictures",
                    0,
                )
            )
        )

        if royal_stake > 0:

            royal_return = (
                royal_three_pictures
                .royal_pictures_return(
                    royal_stake,
                    cards,
                )
            )

            seat_return += royal_return

            total_return += royal_return

            results.append(
                {
                    "seat":
                        seat,

                    "wager_type":
                        "royal_pictures",

                    "amount":
                        float(
                            royal_stake
                        ),

                    "return":
                        float(
                            royal_return
                        ),

                    "win":
                        royal_return > 0,

                    "category":
                        royal_result,
                }
            )

        # --------------------------------------------------------
        # VISIBLE HAND
        # --------------------------------------------------------

        hand_view = {
            "cards":
                cards,

            "point_total":
                royal_three_pictures
                .point_total(
                    cards
                ),

            "picture_count":
                royal_three_pictures
                .picture_count(
                    cards
                ),

            "hand_name":
                royal_three_pictures
                .hand_name(
                    cards
                ),

            "main_result":
                main_result,

            "tie":
                tie_result,

            "royal_pictures":
                royal_result,

            "total_return":
                float(
                    seat_return
                ),
        }

        outcome_seats[
            seat_key
        ] = hand_view

        visible_seats[
            seat_key
        ] = {
            **hand_view,

            "bets":
                seat_bets,

            "viewed":
                (
                    seat
                    ==
                    active_seats[
                        0
                    ]
                ),

            "blind":
                (
                    seat
                    !=
                    active_seats[
                        0
                    ]
                ),
        }

    # ------------------------------------------------------------
    # DEALER / OUTCOME
    # ------------------------------------------------------------

    dealer_view = {
        "cards":
            dealer_cards,

        "point_total":
            royal_three_pictures
            .point_total(
                dealer_cards
            ),

        "picture_count":
            royal_three_pictures
            .picture_count(
                dealer_cards
            ),

        "hand_name":
            royal_three_pictures
            .hand_name(
                dealer_cards
            ),
    }

    outcome = {
        "game":
            game_id,

        "dealer_cards":
            dealer_cards,

        "dealer":
            dealer_view,

        "active_seats":
            active_seats,

        "seats":
            outcome_seats,
    }

    return {
        "game":
            game_id,

        "stage":
            "settled",

        "all_done":
            True,

        "active_seats":
            active_seats,

        "dealer_cards":
            dealer_cards,

        "dealer":
            dealer_view,

        "seats":
            visible_seats,

        "outcome":
            outcome,

        "total_wager":
            total_wager,

        "total_return":
            float(
                total_return
            ),

        "net":
            (
                float(
                    total_return
                )
                -
                total_wager
            ),

        "results":
            results,
    }
