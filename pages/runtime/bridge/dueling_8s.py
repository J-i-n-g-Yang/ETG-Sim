"""
Dueling 8's 21+ adapter for the ETG Sim GitHub Pages browser bridge.

Provides the browser-side deal, action and settlement operations while
continuing to use game.dueling_8s_21 as the authoritative game
implementation.
"""

from __future__ import annotations

from decimal import Decimal

from bridge.common import MAX_BET
from bridge.state_token import (
    encode_state,
    decode_state,
)

import game.dueling_8s_21 as dueling_8s


# ================================================================
# DUELING 8'S 21+
#
# Browser equivalents of:
#
#   POST /api/solo/dueling-8s/deal
#   POST /api/solo/dueling-8s/action
#   POST /api/solo/dueling-8s/settle
# ================================================================

_DUELING_8S_GAME = "dueling_8s_21"

_DUELING_8S_WAGERS = {
    "main",
    "678",
    "six_seven_eight",
    "superb_8s",
    "tie_18",
    "21_plus",
}


# ================================================================
# DUELING 8'S HELPERS
# ================================================================

def _d8_draw(state):

    if not state["shoe"]:

        raise ValueError(
            "Dueling 8's shoe exhausted"
        )

    return state[
        "shoe"
    ].pop(0)


def _d8_main_bet(
    state,
    seat,
):

    return float(
        (
            state.get(
                "bets_by_seat",
                {},
            )
            .get(
                str(seat),
                {},
            )
        )
        .get(
            "main",
            0,
        )
    )


def _d8_hand_status(
    hand,
):

    if hand.get(
        "surrendered"
    ):

        return "surrendered"

    total = dueling_8s.hand_total(
        hand[
            "cards"
        ]
    )

    if total > 21:

        return "bust"

    if total == 21:

        return "stood"

    return "playing"


# ================================================================
# DUELING 8'S PROGRESSION
# ================================================================

def _d8_advance(
    state,
):

    active_seats = state[
        "active_seats"
    ]

    while (
        state[
            "seat_pos"
        ]
        <
        len(
            active_seats
        )
    ):

        seat = active_seats[
            state[
                "seat_pos"
            ]
        ]

        seat_key = str(
            seat
        )

        hands = state[
            "hands"
        ][
            seat_key
        ]

        hand_pos = state[
            "hand_pos"
        ].get(
            seat_key,
            0,
        )

        while (
            hand_pos
            <
            len(
                hands
            )
            and
            hands[
                hand_pos
            ].get(
                "status"
            )
            !=
            "playing"
        ):

            hand_pos += 1

        state[
            "hand_pos"
        ][
            seat_key
        ] = hand_pos

        if (
            hand_pos
            <
            len(
                hands
            )
        ):

            return

        state[
            "seat_pos"
        ] += 1

    state[
        "stage"
    ] = "settle"


def _d8_current(
    state,
):

    _d8_advance(
        state
    )

    if (
        state.get(
            "stage"
        )
        !=
        "play"
    ):

        return (
            None,
            None,
        )

    active_seats = state[
        "active_seats"
    ]

    if (
        state[
            "seat_pos"
        ]
        >=
        len(
            active_seats
        )
    ):

        return (
            None,
            None,
        )

    seat = active_seats[
        state[
            "seat_pos"
        ]
    ]

    hand_index = state[
        "hand_pos"
    ][
        str(
            seat
        )
    ]

    return (
        seat,
        hand_index,
    )


# ================================================================
# DUELING 8'S CLIENT VIEW
# ================================================================

def _d8_visible(
    state,
):

    (
        current_seat,
        current_hand,
    ) = _d8_current(
        state
    )

    table_minimum = float(
        state.get(
            "table_minimum",
            1,
        )
    )

    seats = {}

    for seat in state[
        "active_seats"
    ]:

        seat_key = str(
            seat
        )

        visible_hands = []

        for (
            index,
            hand,
        ) in enumerate(
            state[
                "hands"
            ][
                seat_key
            ]
        ):

            actions = []

            if (
                state.get(
                    "stage"
                )
                ==
                "play"
                and
                seat
                ==
                current_seat
                and
                index
                ==
                current_hand
                and
                hand.get(
                    "status"
                )
                ==
                "playing"
            ):

                actions = (
                    dueling_8s
                    .available_actions(
                        hand,

                        total_hands=
                            len(
                                state[
                                    "hands"
                                ][
                                    seat_key
                                ]
                            ),

                        table_minimum=
                            table_minimum,
                    )
                )

            visible_hands.append(
                {
                    "cards":
                        hand[
                            "cards"
                        ],

                    "total":
                        dueling_8s
                        .hand_total(
                            hand[
                                "cards"
                            ]
                        ),

                    "soft":
                        dueling_8s
                        .is_soft(
                            hand[
                                "cards"
                            ]
                        ),

                    "bust":
                        dueling_8s
                        .is_bust(
                            hand[
                                "cards"
                            ]
                        ),

                    "status":
                        hand[
                            "status"
                        ],

                    "stake":
                        float(
                            hand[
                                "stake"
                            ]
                        ),

                    "original_stake":
                        float(
                            hand[
                                "original_stake"
                            ]
                        ),

                    "double_amount":
                        float(
                            hand.get(
                                "double_amount",
                                0,
                            )
                        ),

                    "double_extra":
                        float(
                            hand.get(
                                "double_amount",
                                0,
                            )
                        ),

                    "from_split":
                        bool(
                            hand.get(
                                "from_split"
                            )
                        ),

                    "surrendered":
                        bool(
                            hand.get(
                                "surrendered"
                            )
                        ),

                    "available_actions":
                        actions,
                }
            )

        seats[
            seat_key
        ] = {
            "hands":
                visible_hands,

            "bets":
                state[
                    "bets_by_seat"
                ].get(
                    seat_key,
                    {},
                ),
        }

    return {
        "game":
            _DUELING_8S_GAME,

        "state_token":
            encode_state(
                state
            ),

        "dealer_cards":
            state[
                "dealer_cards"
            ],

        "dealer_up":
            state[
                "dealer_cards"
            ][0],

        "active_seats":
            state[
                "active_seats"
            ],

        "seats":
            seats,

        "current_seat":
            current_seat,

        "current_hand":
            current_hand,

        "stage":
            state[
                "stage"
            ],

        "all_done":
            (
                state[
                    "stage"
                ]
                ==
                "settle"
            ),

        "initial_total_wager":
            float(
                state[
                    "initial_total_wager"
                ]
            ),

        "extra_wager":
            float(
                state[
                    "extra_wager"
                ]
            ),

        "total_wager":
            (
                float(
                    state[
                        "initial_total_wager"
                    ]
                )
                +
                float(
                    state[
                        "extra_wager"
                    ]
                )
            ),
    }


# ================================================================
# DUELING 8'S DEAL
# ================================================================

def dueling_8s_deal(
    payload: dict,
) -> dict:

    game = str(
        payload.get(
            "game",
            "",
        )
    )

    if (
        game
        and
        game
        !=
        _DUELING_8S_GAME
    ):

        raise ValueError(
            "Unknown Dueling 8's game"
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

    try:

        table_minimum = float(
            payload.get(
                "table_minimum",
                1,
            )
            or
            1
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            "Invalid table minimum"
        ) from exc

    if table_minimum <= 0:

        raise ValueError(
            "Invalid table minimum"
        )

    aliases = {
        "six_seven_eight":
            "678",
    }

    bets_by_seat = {}

    total = 0.0

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
                "Invalid Dueling 8's seat"
            )

        wager_type = aliases.get(
            wager_type,
            wager_type,
        )

        if (
            wager_type
            not in
            _DUELING_8S_WAGERS
        ):

            raise ValueError(
                "Invalid Dueling 8's wager: "
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

        total += amount

    if total > max_bet:

        raise ValueError(
            "Total initial stake capped at "
            f"{int(max_bet)} credits"
        )

    # ------------------------------------------------------------
    # ACTIVE SEATS
    # ------------------------------------------------------------

    active_seats = []

    for seat_key in sorted(
        bets_by_seat.keys(),
        key=int,
    ):

        seat_bets = bets_by_seat[
            seat_key
        ]

        main = float(
            seat_bets.get(
                "main",
                0,
            )
        )

        if main <= 0:

            raise ValueError(
                f"Seat {int(seat_key) + 1} "
                "requires a Main wager"
            )

        if (
            main
            <
            table_minimum
        ):

            raise ValueError(
                f"Seat {int(seat_key) + 1} "
                "Main wager is below "
                "the table minimum"
            )

        active_seats.append(
            int(
                seat_key
            )
        )

    if not active_seats:

        raise ValueError(
            "At least one active seat is required"
        )

    # ------------------------------------------------------------
    # SHOE
    # ------------------------------------------------------------

    shoe = dueling_8s.make_shoe(
        6
    )

    # ------------------------------------------------------------
    # INITIAL HANDS
    # ------------------------------------------------------------

    hands = {}

    original_cards = {}

    for seat in active_seats:

        if not shoe:

            raise ValueError(
                "Dueling 8's shoe exhausted"
            )

        draw = shoe.pop(
            0
        )

        cards = (
            dueling_8s
            .initial_player_hand(
                draw
            )
        )

        main = float(
            bets_by_seat[
                str(
                    seat
                )
            ][
                "main"
            ]
        )

        hand = {
            "cards":
                cards,

            "stake":
                main,

            "original_stake":
                main,

            "double_amount":
                0.0,

            "from_split":
                False,

            "acted":
                False,

            "surrendered":
                False,

            "status":
                "playing",
        }

        hand[
            "status"
        ] = _d8_hand_status(
            hand
        )

        hands[
            str(
                seat
            )
        ] = [
            hand
        ]

        original_cards[
            str(
                seat
            )
        ] = [
            dict(
                card
            )
            for card in cards
        ]

    dealer_cards = (
        dueling_8s
        .initial_dealer_hand()
    )

    state = {
        "game":
            _DUELING_8S_GAME,

        "shoe":
            shoe,

        "dealer_cards":
            dealer_cards,

        "active_seats":
            active_seats,

        "bets_by_seat":
            bets_by_seat,

        "original_cards":
            original_cards,

        "hands":
            hands,

        "seat_pos":
            0,

        "hand_pos":
            {
                str(
                    seat
                ):
                    0
                for seat in
                active_seats
            },

        "table_minimum":
            table_minimum,

        "initial_total_wager":
            total,

        "extra_wager":
            0.0,

        "stage":
            "play",
    }

    _d8_advance(
        state
    )

    return _d8_visible(
        state
    )


# ================================================================
# DUELING 8'S ACTION
# ================================================================

def dueling_8s_action(
    payload: dict,
) -> dict:

    try:

        state = decode_state(
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
            "game"
        )
        !=
        _DUELING_8S_GAME
    ):

        raise ValueError(
            "Invalid Dueling 8's state"
        )

    (
        current_seat,
        current_hand,
    ) = _d8_current(
        state
    )

    if current_seat is None:

        raise ValueError(
            "Player decisions are complete"
        )

    # ------------------------------------------------------------
    # VERIFY SEAT / HAND
    # ------------------------------------------------------------

    try:

        requested_seat = int(
            payload.get(
                "seat",
                -1,
            )
        )

        requested_hand = int(
            payload.get(
                "hand_index",
                -1,
            )
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            "Invalid seat or hand index"
        ) from exc

    if (
        requested_seat
        !=
        current_seat
    ):

        raise ValueError(
            "It is another seat's turn"
        )

    if (
        requested_hand
        !=
        current_hand
    ):

        raise ValueError(
            "It is another hand's turn"
        )

    seat_key = str(
        current_seat
    )

    hands = state[
        "hands"
    ][
        seat_key
    ]

    hand = hands[
        current_hand
    ]

    action_name = str(
        payload.get(
            "action",
            "",
        )
    ).strip().lower()

    table_minimum = float(
        state.get(
            "table_minimum",
            1,
        )
    )

    allowed = (
        dueling_8s
        .available_actions(
            hand,

            total_hands=
                len(
                    hands
                ),

            table_minimum=
                table_minimum,
        )
    )

    if (
        action_name
        not in
        allowed
    ):

        raise ValueError(
            "Action is not available: "
            f"{action_name}"
        )

    extra = 0.0

    max_bet = float(
        MAX_BET
    )

    # ------------------------------------------------------------
    # HIT
    # ------------------------------------------------------------

    if action_name == "hit":

        hand[
            "acted"
        ] = True

        hand[
            "cards"
        ].append(
            _d8_draw(
                state
            )
        )

        hand[
            "status"
        ] = _d8_hand_status(
            hand
        )

    # ------------------------------------------------------------
    # STAND
    # ------------------------------------------------------------

    elif action_name == "stand":

        hand[
            "acted"
        ] = True

        hand[
            "status"
        ] = "stood"

    # ------------------------------------------------------------
    # SURRENDER
    # ------------------------------------------------------------

    elif action_name == "surrender":

        hand[
            "acted"
        ] = True

        hand[
            "surrendered"
        ] = True

        hand[
            "status"
        ] = "surrendered"

    # ------------------------------------------------------------
    # DOUBLE
    # ------------------------------------------------------------

    elif action_name == "double":

        try:

            amount = float(
                payload.get(
                    "amount"
                )
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Double requires an amount"
            ) from exc

        original_wager = float(
            hand[
                "original_stake"
            ]
        )

        if (
            amount != amount
            or
            amount <= 0
            or
            not (
                dueling_8s
                .double_amount_valid(
                    amount,
                    original_wager,
                    table_minimum,
                )
            )
        ):

            raise ValueError(
                "Double amount must be between "
                "the table minimum and "
                "the original wager"
            )

        if (
            float(
                state[
                    "initial_total_wager"
                ]
            )
            +
            float(
                state[
                    "extra_wager"
                ]
            )
            +
            amount
            >
            max_bet
        ):

            raise ValueError(
                "Total stake exceeds "
                "the table limit"
            )

        hand[
            "acted"
        ] = True

        hand[
            "double_amount"
        ] = amount

        hand[
            "stake"
        ] = (
            float(
                hand[
                    "stake"
                ]
            )
            +
            amount
        )

        state[
            "extra_wager"
        ] = (
            float(
                state[
                    "extra_wager"
                ]
            )
            +
            amount
        )

        extra = amount

        hand[
            "cards"
        ].append(
            _d8_draw(
                state
            )
        )

        hand[
            "status"
        ] = _d8_hand_status(
            hand
        )

        if (
            hand[
                "status"
            ]
            ==
            "playing"
        ):

            hand[
                "status"
            ] = "stood"

    # ------------------------------------------------------------
    # SPLIT
    # ------------------------------------------------------------

    elif action_name == "split":

        if not (
            dueling_8s
            .can_split(
                hand,
                total_hands=
                    len(
                        hands
                    ),
            )
        ):

            raise ValueError(
                "Cannot split this hand"
            )

        split_cost = float(
            hand[
                "original_stake"
            ]
        )

        if (
            float(
                state[
                    "initial_total_wager"
                ]
            )
            +
            float(
                state[
                    "extra_wager"
                ]
            )
            +
            split_cost
            >
            max_bet
        ):

            raise ValueError(
                "Total stake exceeds "
                "the table limit"
            )

        (
            first_card,
            second_card,
        ) = hand[
            "cards"
        ]

        first_hand = {
            "cards":
                [
                    first_card,
                    _d8_draw(
                        state
                    ),
                ],

            "stake":
                split_cost,

            "original_stake":
                split_cost,

            "double_amount":
                0.0,

            "from_split":
                True,

            "acted":
                False,

            "surrendered":
                False,

            "status":
                "playing",
        }

        second_hand = {
            "cards":
                [
                    second_card,
                    _d8_draw(
                        state
                    ),
                ],

            "stake":
                split_cost,

            "original_stake":
                split_cost,

            "double_amount":
                0.0,

            "from_split":
                True,

            "acted":
                False,

            "surrendered":
                False,

            "status":
                "playing",
        }

        first_hand[
            "status"
        ] = _d8_hand_status(
            first_hand
        )

        second_hand[
            "status"
        ] = _d8_hand_status(
            second_hand
        )

        hands[
            current_hand:
            current_hand + 1
        ] = [
            first_hand,
            second_hand,
        ]

        state[
            "extra_wager"
        ] = (
            float(
                state[
                    "extra_wager"
                ]
            )
            +
            split_cost
        )

        extra = split_cost

    else:

        raise ValueError(
            "Invalid action"
        )

    _d8_advance(
        state
    )

    view = _d8_visible(
        state
    )

    view[
        "extra_stake"
    ] = extra

    return view


# ================================================================
# DUELING 8'S SETTLE
# ================================================================

def dueling_8s_settle(
    payload: dict,
) -> dict:

    try:

        state = decode_state(
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
            "game"
        )
        !=
        _DUELING_8S_GAME
    ):

        raise ValueError(
            "Invalid Dueling 8's state"
        )

    (
        current_seat,
        _,
    ) = _d8_current(
        state
    )

    if current_seat is not None:

        raise ValueError(
            "Player decisions are not complete"
        )

    shoe = state[
        "shoe"
    ]

    dealer = [
        dict(
            card
        )
        for card in
        state[
            "dealer_cards"
        ]
    ]

    dealer = (
        dueling_8s
        .play_dealer(
            shoe,
            dealer,
        )
    )

    total_return = Decimal(
        "0"
    )

    results = []

    seats = {}

    # ============================================================
    # SETTLE EACH ACTIVE SEAT
    # ============================================================

    for seat in state[
        "active_seats"
    ]:

        seat_key = str(
            seat
        )

        seat_bets = state[
            "bets_by_seat"
        ][
            seat_key
        ]

        hands = state[
            "hands"
        ][
            seat_key
        ]

        seat_return = Decimal(
            "0"
        )

        hand_results = []

        # --------------------------------------------------------
        # MAIN / SPLIT HANDS
        # --------------------------------------------------------

        for (
            index,
            hand,
        ) in enumerate(
            hands
        ):

            stake = Decimal(
                str(
                    hand[
                        "stake"
                    ]
                )
            )

            if hand.get(
                "surrendered"
            ):

                result = "surrender"

                returned = (
                    dueling_8s
                    .surrender_return(
                        hand[
                            "original_stake"
                        ]
                    )
                )

            else:

                result = (
                    dueling_8s
                    .regular_result(
                        hand[
                            "cards"
                        ],
                        dealer,
                    )
                )

                returned = (
                    dueling_8s
                    .regular_return(
                        stake,
                        result,
                    )
                )

            total_return += returned

            seat_return += returned

            hand_results.append(
                {
                    "hand_index":
                        index,

                    "cards":
                        hand[
                            "cards"
                        ],

                    "total":
                        dueling_8s
                        .hand_total(
                            hand[
                                "cards"
                            ]
                        ),

                    "soft":
                        dueling_8s
                        .is_soft(
                            hand[
                                "cards"
                            ]
                        ),

                    "bust":
                        dueling_8s
                        .is_bust(
                            hand[
                                "cards"
                            ]
                        ),

                    "from_split":
                        bool(
                            hand.get(
                                "from_split"
                            )
                        ),

                    "surrendered":
                        bool(
                            hand.get(
                                "surrendered"
                            )
                        ),

                    "stake":
                        float(
                            stake
                        ),

                    "double_amount":
                        float(
                            hand.get(
                                "double_amount",
                                0,
                            )
                        ),

                    "double_extra":
                        float(
                            hand.get(
                                "double_amount",
                                0,
                            )
                        ),

                    "status":
                        hand.get(
                            "status"
                        ),

                    "result":
                        result,

                    "return":
                        float(
                            returned
                        ),
                }
            )

            results.append(
                {
                    "wager_type":
                        (
                            "main"
                            if index == 0
                            else
                            f"split_hand_{index + 1}"
                        ),

                    "seat":
                        seat,

                    "hand_index":
                        index,

                    "amount":
                        float(
                            stake
                        ),

                    "return":
                        float(
                            returned
                        ),

                    "win":
                        (
                            float(
                                returned
                            )
                            >
                            float(
                                stake
                            )
                        ),
                }
            )

        # --------------------------------------------------------
        # 6-7-8
        # --------------------------------------------------------

        side_678 = Decimal(
            str(
                seat_bets.get(
                    "678",
                    0,
                )
            )
        )

        if side_678 > 0:

            main_hand = hands[
                0
            ]

            returned = (
                dueling_8s
                .six_seven_eight_bonus(
                    side_678,

                    main_hand[
                        "cards"
                    ],

                    from_split=
                        bool(
                            main_hand.get(
                                "from_split"
                            )
                        ),
                )
            )

            total_return += returned

            seat_return += returned

            results.append(
                {
                    "wager_type":
                        "678",

                    "seat":
                        seat,

                    "amount":
                        float(
                            side_678
                        ),

                    "return":
                        float(
                            returned
                        ),

                    "win":
                        returned > 0,
                }
            )

        # --------------------------------------------------------
        # TIE ON 18
        # --------------------------------------------------------

        tie_18 = Decimal(
            str(
                seat_bets.get(
                    "tie_18",
                    0,
                )
            )
        )

        if tie_18 > 0:

            returned = (
                dueling_8s
                .tie_on_18_return(
                    tie_18,
                    hands[0][
                        "cards"
                    ],
                    dealer,
                )
            )

            total_return += returned

            seat_return += returned

            results.append(
                {
                    "wager_type":
                        "tie_18",

                    "seat":
                        seat,

                    "amount":
                        float(
                            tie_18
                        ),

                    "return":
                        float(
                            returned
                        ),

                    "win":
                        returned > 0,
                }
            )

        # --------------------------------------------------------
        # 21+
        # --------------------------------------------------------

        twenty_one_plus = Decimal(
            str(
                seat_bets.get(
                    "21_plus",
                    0,
                )
            )
        )

        if twenty_one_plus > 0:

            returned = (
                dueling_8s
                .twenty_one_plus_return(
                    twenty_one_plus,
                    dealer,
                )
            )

            total_return += returned

            seat_return += returned

            results.append(
                {
                    "wager_type":
                        "21_plus",

                    "seat":
                        seat,

                    "amount":
                        float(
                            twenty_one_plus
                        ),

                    "return":
                        float(
                            returned
                        ),

                    "win":
                        returned > 0,
                }
            )

        # --------------------------------------------------------
        # SUPERB 8s
        # --------------------------------------------------------

        superb = Decimal(
            str(
                seat_bets.get(
                    "superb_8s",
                    0,
                )
            )
        )

        if superb > 0:

            returned = (
                dueling_8s
                .superb_eights_return(
                    superb,
                    hands[0][
                        "cards"
                    ],
                )
            )

            total_return += returned

            seat_return += returned

            results.append(
                {
                    "wager_type":
                        "superb_8s",

                    "seat":
                        seat,

                    "amount":
                        float(
                            superb
                        ),

                    "return":
                        float(
                            returned
                        ),

                    "win":
                        returned > 0,
                }
            )

        seats[
            seat_key
        ] = {
            "hands":
                hand_results,

            "total_return":
                float(
                    seat_return
                ),

            "bets":
                seat_bets,
        }

    # ============================================================
    # FINAL OUTCOME
    # ============================================================

    total_wager = (
        float(
            state[
                "initial_total_wager"
            ]
        )
        +
        float(
            state[
                "extra_wager"
            ]
        )
    )

    outcome = {
        "game":
            _DUELING_8S_GAME,

        "dealer_cards":
            dealer,

        "dealer_total":
            dueling_8s
            .hand_total(
                dealer
            ),

        "dealer_bust":
            dueling_8s
            .is_bust(
                dealer
            ),

        "dealer_card_count":
            len(
                dealer
            ),

        "active_seats":
            state[
                "active_seats"
            ],

        "seats":
            seats,

        "hands_by_seat":
            seats,
    }

    return {
        "game":
            _DUELING_8S_GAME,

        "outcome":
            outcome,

        "total_wager":
            total_wager,

        "extra_wager":
            float(
                state[
                    "extra_wager"
                ]
            ),

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
