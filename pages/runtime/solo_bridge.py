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
"""

from __future__ import annotations

import importlib
import json
import random
import traceback

from decimal import Decimal
from typing import Any

from bridge.common import (
    MAX_BET,
    clean_bets,
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
from bridge.state_token import (
    encode_state,
    decode_state,
)

import game.registry as registry


from game.blackjack_base import (
    build_shoe,
    hand_total,
    is_blackjack,
    is_bust,
    is_pair,
    complete_dealer_hand,
    card_point_value,
    is_soft,
)


# ================================================================
# GAME GROUPS
# ================================================================

BLACKJACK_GAMES = (
    "blackjack_lucky8",
    "blackjack_freebet",
    "blackjack_kingsbounty",
    "pontoon",
)


# ================================================================
# COMMON BRIDGE COMPATIBILITY
#
# Shared implementations now live in bridge modules.
#
# Keep the old private names temporarily so the remaining monolithic
# game-family code does not need to be rewritten during this stage
# of the refactor.
# ================================================================

_json_safe = json_safe
_clean_bets = clean_bets

_bj_enc = encode_state
_bj_dec = decode_state


# ================================================================
# BLACKJACK HELPERS
# ================================================================

def _pontoon_shoe(
    num_decks: int = 6,
):

    ranks = [
        "A",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "J",
        "Q",
        "K",
    ]

    deck = [
        {
            "rank":
                rank,

            "suit":
                suit,
        }
        for suit in (
            "S",
            "H",
            "D",
            "C",
        )
        for rank in ranks
    ] * num_decks

    random.shuffle(
        deck
    )

    return deck


def _pair_value(
    cards,
):

    return (
        len(
            cards
        )
        ==
        2
        and
        card_point_value(
            cards[0][
                "rank"
            ]
        )
        ==
        card_point_value(
            cards[1][
                "rank"
            ]
        )
    )


def _main_bet(
    state,
    seat,
):

    return float(
        state[
            "bets_by_seat"
        ]
        .get(
            str(
                seat
            ),
            {},
        )
        .get(
            f"seat{seat}_main",
            0,
        )
    )


def _pontoon_total(
    hand,
):

    cards = hand[
        "cards"
    ]

    if not hand.get(
        "pontoon_double_ace"
    ):

        return hand_total(
            cards
        )

    total = 0

    flexible_aces = 0

    for (
        index,
        card,
    ) in enumerate(
        cards
    ):

        if (
            card[
                "rank"
            ]
            ==
            "A"
        ):

            if index < 2:

                total += 1

            else:

                total += 11

                flexible_aces += 1

        else:

            total += card_point_value(
                card[
                    "rank"
                ]
            )

    while (
        total > 21
        and
        flexible_aces
    ):

        total -= 10

        flexible_aces -= 1

    return total


def _bj_total(
    game,
    hand,
):

    if game == "pontoon":

        return _pontoon_total(
            hand
        )

    return hand_total(
        hand[
            "cards"
        ]
    )


def _bj_bust(
    game,
    hand,
):

    return (
        _bj_total(
            game,
            hand,
        )
        >
        21
    )


def _hand_status(
    game,
    hand,
):

    if _bj_bust(
        game,
        hand,
    ):

        return "bust"

    if (
        _bj_total(
            game,
            hand,
        )
        ==
        21
        or
        hand.get(
            "split_aces"
        )
    ):

        return "stood"

    return "playing"


def _eligible_double(
    game,
    hand,
):

    return (
        hand[
            "status"
        ]
        ==
        "playing"
        and
        len(
            hand[
                "cards"
            ]
        )
        ==
        2
        and
        not hand.get(
            "split_aces"
        )
    )


def _eligible_split(
    state,
    seat,
    hand,
):

    if (
        hand[
            "status"
        ]
        !=
        "playing"
        or
        len(
            hand[
                "cards"
            ]
        )
        !=
        2
        or
        not _pair_value(
            hand[
                "cards"
            ]
        )
    ):

        return False

    hands = state[
        "hands"
    ][
        str(
            seat
        )
    ]

    if len(
        hands
    ) >= 4:

        return False

    if (
        hand[
            "cards"
        ][0][
            "rank"
        ]
        ==
        "A"
        and
        any(
            item.get(
                "from_split_aces"
            )
            for item in hands
        )
    ):

        return False

    return True


def _free_double(
    game,
    hand,
):

    return (
        game
        ==
        "blackjack_freebet"
        and
        len(
            hand[
                "cards"
            ]
        )
        ==
        2
        and
        hand_total(
            hand[
                "cards"
            ]
        )
        in (
            9,
            10,
            11,
        )
        and
        not is_soft(
            hand[
                "cards"
            ]
        )
    )


def _free_split(
    game,
    hand,
):

    return (
        game
        ==
        "blackjack_freebet"
        and
        card_point_value(
            hand[
                "cards"
            ][0][
                "rank"
            ]
        )
        !=
        10
    )


def _can_surrender(
    state,
    hand,
):

    if (
        hand[
            "status"
        ]
        !=
        "playing"
        or
        len(
            hand[
                "cards"
            ]
        )
        !=
        2
        or
        hand.get(
            "from_split"
        )
    ):

        return False

    dealer_rank = state[
        "dealer_up"
    ][
        "rank"
    ]

    if (
        state[
            "game"
        ]
        ==
        "pontoon"
    ):

        return dealer_rank in (
            "A",
            "K",
            "Q",
            "J",
        )

    return (
        dealer_rank
        !=
        "A"
    )


def _advance(
    state,
):

    seats = state[
        "active_seats"
    ]

    while (
        state[
            "seat_pos"
        ]
        <
        len(
            seats
        )
    ):

        seat = str(
            seats[
                state[
                    "seat_pos"
                ]
            ]
        )

        hands = state[
            "hands"
        ][
            seat
        ]

        while (
            state[
                "hand_pos"
            ].get(
                seat,
                0,
            )
            <
            len(
                hands
            )
            and
            hands[
                state[
                    "hand_pos"
                ][
                    seat
                ]
            ][
                "status"
            ]
            !=
            "playing"
        ):

            state[
                "hand_pos"
            ][
                seat
            ] += 1

        if (
            state[
                "hand_pos"
            ][
                seat
            ]
            <
            len(
                hands
            )
        ):

            return

        state[
            "seat_pos"
        ] += 1


def _current(
    state,
):

    _advance(
        state
    )

    if (
        state.get(
            "decision_phase"
        )
        ==
        "insurance"
    ):

        while (
            state[
                "insurance_pos"
            ]
            <
            len(
                state[
                    "active_seats"
                ]
            )
        ):

            seat = state[
                "active_seats"
            ][
                state[
                    "insurance_pos"
                ]
            ]

            if not state[
                "insurance_decisions"
            ].get(
                str(
                    seat
                )
            ):

                return (
                    seat,
                    None,
                )

            state[
                "insurance_pos"
            ] += 1

        state[
            "decision_phase"
        ] = "play"

    _advance(
        state
    )

    if (
        state[
            "seat_pos"
        ]
        >=
        len(
            state[
                "active_seats"
            ]
        )
    ):

        return (
            None,
            None,
        )

    seat = state[
        "active_seats"
    ][
        state[
            "seat_pos"
        ]
    ]

    return (
        seat,
        state[
            "hand_pos"
        ][
            str(
                seat
            )
        ],
    )


def _visible(
    state,
):

    (
        current_seat,
        current_hand,
    ) = _current(
        state
    )

    seats = {}

    for seat in state[
        "active_seats"
    ]:

        hands = state[
            "hands"
        ][
            str(
                seat
            )
        ]

        visible_hands = []

        for hand in hands:

            visible_hands.append(
                {
                    "cards":
                        hand[
                            "cards"
                        ],

                    "total":
                        _bj_total(
                            state[
                                "game"
                            ],
                            hand,
                        ),

                    "status":
                        hand[
                            "status"
                        ],

                    "can_hit":
                        (
                            hand[
                                "status"
                            ]
                            ==
                            "playing"
                        ),

                    "can_stand":
                        (
                            hand[
                                "status"
                            ]
                            ==
                            "playing"
                        ),

                    "can_double":
                        _eligible_double(
                            state[
                                "game"
                            ],
                            hand,
                        ),

                    "can_split":
                        _eligible_split(
                            state,
                            seat,
                            hand,
                        ),

                    "can_surrender":
                        _can_surrender(
                            state,
                            hand,
                        ),

                    "can_withdraw_double":
                        (
                            state[
                                "game"
                            ]
                            ==
                            "pontoon"
                            and
                            hand.get(
                                "awaiting_double_withdraw",
                                False,
                            )
                        ),

                    "free_double":
                        (
                            _free_double(
                                state[
                                    "game"
                                ],
                                hand,
                            )
                            if
                            _eligible_double(
                                state[
                                    "game"
                                ],
                                hand,
                            )
                            else
                            False
                        ),

                    "free_split":
                        (
                            _free_split(
                                state[
                                    "game"
                                ],
                                hand,
                            )
                            if
                            _eligible_split(
                                state,
                                seat,
                                hand,
                            )
                            else
                            False
                        ),

                    "free_marker":
                        bool(
                            hand.get(
                                "free_marker"
                            )
                        ),
                }
            )

        seats[
            str(
                seat
            )
        ] = {
            "hands":
                visible_hands,
        }

        if visible_hands:

            seats[
                str(
                    seat
                )
            ].update(
                visible_hands[0]
            )

    phase = state.get(
        "decision_phase",
        "play",
    )

    insurance_offer = None

    if (
        phase
        ==
        "insurance"
        and
        current_seat
        is not None
    ):

        hand = state[
            "hands"
        ][
            str(
                current_seat
            )
        ][0]

        insurance_offer = {
            "seat":
                current_seat,

            "amount":
                (
                    _main_bet(
                        state,
                        current_seat,
                    )
                    /
                    2
                ),

            "even_money":
                (
                    state[
                        "game"
                    ]
                    !=
                    "pontoon"
                    and
                    is_blackjack(
                        hand[
                            "cards"
                        ]
                    )
                    and
                    not hand.get(
                        "from_split"
                    )
                ),
        }

    return {
        "state_token":
            _bj_enc(
                state
            ),

        "dealer_up":
            state[
                "dealer_up"
            ],

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

        "decision_phase":
            phase,

        "insurance_offer":
            insurance_offer,

        "all_done":
            (
                current_seat
                is None
                and
                phase
                !=
                "insurance"
            ),
    }


# ================================================================
# BLACKJACK DEAL
# ================================================================

def blackjack_deal(
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

    if game not in BLACKJACK_GAMES:

        raise ValueError(
            "Unknown blackjack variant"
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

    active = set()

    bets_by_seat = {}

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
            or
            not registry.validate_wager(
                game,
                wager_type,
            )
        ):

            raise ValueError(
                "Invalid bet"
            )

        total += amount

        active.add(
            seat
        )

        seat_bets = (
            bets_by_seat
            .setdefault(
                str(
                    seat
                ),
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

    if total > max_bet:

        raise ValueError(
            f"Total stake capped at "
            f"{int(max_bet)} credits"
        )

    active = sorted(
        active
    )

    if game == "pontoon":

        shoe = _pontoon_shoe()

    else:

        shoe = build_shoe(
            6
        )

    first = {
        seat: [
            shoe.pop()
        ]
        for seat in active
    }

    dealer_up = shoe.pop()

    for seat in active:

        first[
            seat
        ].append(
            shoe.pop()
        )

    dealer_hole = shoe.pop()

    hands = {}

    for seat in active:

        cards = first[
            seat
        ]

        natural = is_blackjack(
            cards
        )

        status = (
            "blackjack"
            if natural
            else
            "playing"
        )

        hands[
            str(
                seat
            )
        ] = [
            {
                "cards":
                    cards,

                "status":
                    status,

                "stake":
                    _main_bet(
                        {
                            "bets_by_seat":
                                bets_by_seat,
                        },
                        seat,
                    ),

                "paid_extra":
                    0.0,

                "free_marker":
                    False,

                "from_split":
                    False,

                "from_split_aces":
                    False,

                "split_aces":
                    False,

                "doubled":
                    False,

                "surrendered":
                    False,

                "double_withdrawn":
                    False,

                "immediate_paid":
                    0.0,
            }
        ]

    insurance = (
        dealer_up[
            "rank"
        ]
        ==
        "A"
    )

    state = {
        "game":
            game,

        "shoe":
            shoe,

        "dealer_up":
            dealer_up,

        "dealer_hole":
            dealer_hole,

        "dealer_cards":
            [
                dealer_up,
                dealer_hole,
            ],

        "active_seats":
            active,

        "bets_by_seat":
            bets_by_seat,

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
                for seat in active
            },

        "free_markers":
            {
                str(
                    seat
                ):
                    0
                for seat in active
            },

        "initial_cards":
            {
                str(
                    seat
                ):
                    first[
                        seat
                    ]
                for seat in active
            },

        "initial_total_wager":
            total,

        "extra_wager":
            0.0,

        "insurance_wagers":
            {
                str(
                    seat
                ):
                    0.0
                for seat in active
            },

        "insurance_decisions":
            {
                str(
                    seat
                ):
                    False
                for seat in active
            },

        "insurance_pos":
            0,

        "decision_phase":
            (
                "insurance"
                if insurance
                else
                "play"
            ),

        "immediate_return":
            0.0,
    }

    immediate = 0.0

    if game == "pontoon":

        for seat in active:

            hand = state[
                "hands"
            ][
                str(
                    seat
                )
            ][0]

            if is_blackjack(
                hand[
                    "cards"
                ]
            ):

                value = (
                    _main_bet(
                        state,
                        seat,
                    )
                    *
                    2.5
                )

                hand[
                    "immediate_paid"
                ] = value

                hand[
                    "status"
                ] = "paid21"

                immediate += value

    response = _visible(
        state
    )

    response[
        "total_wager"
    ] = total

    response[
        "immediate_return"
    ] = immediate

    return response


# ================================================================
# BLACKJACK ACTION
# ================================================================

def blackjack_action(
    payload: dict,
) -> dict:

    action = str(
        payload.get(
            "action",
            "",
        )
    ).lower()

    allowed = (
        "hit",
        "stand",
        "double",
        "split",
        "surrender",
        "insurance",
        "decline_insurance",
        "even_money",
        "withdraw_double",
        "keep_double",
    )

    if action not in allowed:

        raise ValueError(
            "Invalid action"
        )

    state = _bj_dec(
        str(
            payload.get(
                "state_token",
                "",
            )
        )
    )

    (
        seat,
        hand_index,
    ) = _current(
        state
    )

    if seat is None:

        raise ValueError(
            "Round already complete"
        )

    try:

        requested_seat = int(
            payload.get(
                "seat",
                -1,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        requested_seat = -1

    if requested_seat != seat:

        raise ValueError(
            "It is another seat's turn"
        )

    extra = 0.0

    immediate = 0.0

    # ------------------------------------------------------------
    # INSURANCE / EVEN MONEY
    # ------------------------------------------------------------

    if (
        state.get(
            "decision_phase"
        )
        ==
        "insurance"
    ):

        hand = state[
            "hands"
        ][
            str(
                seat
            )
        ][0]

        base = _main_bet(
            state,
            seat,
        )

        if action == "insurance":

            amount = (
                base /
                2
            )

            if amount <= 0:

                raise ValueError(
                    "Insurance requires a main wager"
                )

            state[
                "insurance_wagers"
            ][
                str(
                    seat
                )
            ] = amount

            state[
                "extra_wager"
            ] += amount

            extra = amount

        elif action == "even_money":

            if not is_blackjack(
                hand[
                    "cards"
                ]
            ):

                raise ValueError(
                    "Even money is only available "
                    "on a natural Blackjack/Pontoon"
                )

            immediate = (
                base *
                2
            )

            hand[
                "immediate_paid"
            ] += immediate

            hand[
                "status"
            ] = "paid_even_money"

        elif action != "decline_insurance":

            raise ValueError(
                "Resolve Insurance / "
                "Even Money first"
            )

        state[
            "insurance_decisions"
        ][
            str(
                seat
            )
        ] = True

        state[
            "insurance_pos"
        ] += 1

    # ------------------------------------------------------------
    # NORMAL PLAYER ACTION
    # ------------------------------------------------------------

    else:

        hands = state[
            "hands"
        ][
            str(
                seat
            )
        ]

        hand = hands[
            hand_index
        ]

        # --------------------------------------------------------
        # PONTOON DOUBLE RESCUE
        # --------------------------------------------------------

        if hand.get(
            "awaiting_double_withdraw"
        ):

            if action == "withdraw_double":

                immediate = float(
                    hand.get(
                        "paid_extra",
                        0,
                    )
                )

                hand[
                    "immediate_paid"
                ] += immediate

                hand[
                    "double_withdrawn"
                ] = True

                hand[
                    "awaiting_double_withdraw"
                ] = False

                hand[
                    "status"
                ] = "double_withdrawn"

            elif action == "keep_double":

                hand[
                    "awaiting_double_withdraw"
                ] = False

                hand[
                    "status"
                ] = "stood"

            else:

                raise ValueError(
                    "Choose Keep Double or "
                    "Withdraw Double"
                )

        # --------------------------------------------------------
        # HIT
        # --------------------------------------------------------

        elif action == "hit":

            if (
                hand[
                    "status"
                ]
                !=
                "playing"
            ):

                raise ValueError(
                    "Hand is not playable"
                )

            hand[
                "cards"
            ].append(
                state[
                    "shoe"
                ].pop()
            )

            hand[
                "status"
            ] = _hand_status(
                state[
                    "game"
                ],
                hand,
            )

        # --------------------------------------------------------
        # STAND
        # --------------------------------------------------------

        elif action == "stand":

            hand[
                "status"
            ] = "stood"

        # --------------------------------------------------------
        # SURRENDER
        # --------------------------------------------------------

        elif action == "surrender":

            if not _can_surrender(
                state,
                hand,
            ):

                raise ValueError(
                    "Surrender is not available "
                    "on this hand"
                )

            hand[
                "surrendered"
            ] = True

            hand[
                "status"
            ] = "surrendered"

        # --------------------------------------------------------
        # DOUBLE
        # --------------------------------------------------------

        elif action == "double":

            if not _eligible_double(
                state[
                    "game"
                ],
                hand,
            ):

                raise ValueError(
                    "Cannot double on this hand"
                )

            free = _free_double(
                state[
                    "game"
                ],
                hand,
            )

            if free:

                hand[
                    "free_marker"
                ] = True

                state[
                    "free_markers"
                ][
                    str(
                        seat
                    )
                ] += 1

            else:

                extra = _main_bet(
                    state,
                    seat,
                )

                hand[
                    "paid_extra"
                ] += extra

                state[
                    "extra_wager"
                ] += extra

            if (
                state[
                    "game"
                ]
                ==
                "pontoon"
                and
                any(
                    card[
                        "rank"
                    ]
                    ==
                    "A"
                    for card in
                    hand[
                        "cards"
                    ][:2]
                )
            ):

                hand[
                    "pontoon_double_ace"
                ] = True

            hand[
                "cards"
            ].append(
                state[
                    "shoe"
                ].pop()
            )

            hand[
                "doubled"
            ] = True

            if _bj_bust(
                state[
                    "game"
                ],
                hand,
            ):

                hand[
                    "status"
                ] = "bust"

            elif (
                state[
                    "game"
                ]
                ==
                "pontoon"
                and
                not free
                and
                _bj_total(
                    state[
                        "game"
                    ],
                    hand,
                )
                <
                21
            ):

                hand[
                    "awaiting_double_withdraw"
                ] = True

                hand[
                    "status"
                ] = "playing"

            else:

                hand[
                    "status"
                ] = "stood"

        # --------------------------------------------------------
        # SPLIT
        # --------------------------------------------------------

        elif action == "split":

            if not _eligible_split(
                state,
                seat,
                hand,
            ):

                raise ValueError(
                    "Cannot split this hand"
                )

            free = _free_split(
                state[
                    "game"
                ],
                hand,
            )

            (
                card1,
                card2,
            ) = hand[
                "cards"
            ]

            aces = (
                card1[
                    "rank"
                ]
                ==
                "A"
            )

            if not free:

                extra = _main_bet(
                    state,
                    seat,
                )

                state[
                    "extra_wager"
                ] += extra

            hand1 = {
                "cards":
                    [
                        card1,
                        state[
                            "shoe"
                        ].pop(),
                    ],

                "status":
                    "playing",

                "stake":
                    hand[
                        "stake"
                    ],

                "paid_extra":
                    0.0,

                "free_marker":
                    hand.get(
                        "free_marker",
                        False,
                    ),

                "from_split":
                    True,

                "from_split_aces":
                    aces,

                "split_aces":
                    aces,

                "doubled":
                    False,

                "surrendered":
                    False,

                "double_withdrawn":
                    False,

                "immediate_paid":
                    0.0,
            }

            hand2 = {
                "cards":
                    [
                        card2,
                        state[
                            "shoe"
                        ].pop(),
                    ],

                "status":
                    "playing",

                "stake":
                    (
                        0.0
                        if free
                        else
                        _main_bet(
                            state,
                            seat,
                        )
                    ),

                "paid_extra":
                    0.0,

                "free_marker":
                    free,

                "from_split":
                    True,

                "from_split_aces":
                    aces,

                "split_aces":
                    aces,

                "doubled":
                    False,

                "surrendered":
                    False,

                "double_withdrawn":
                    False,

                "immediate_paid":
                    0.0,
            }

            if free:

                state[
                    "free_markers"
                ][
                    str(
                        seat
                    )
                ] += 1

            hand1[
                "status"
            ] = _hand_status(
                state[
                    "game"
                ],
                hand1,
            )

            hand2[
                "status"
            ] = _hand_status(
                state[
                    "game"
                ],
                hand2,
            )

            hands[
                hand_index:
                hand_index + 1
            ] = [
                hand1,
                hand2,
            ]

        else:

            raise ValueError(
                "That action is not available now"
            )

    # ------------------------------------------------------------
    # PONTOON IMMEDIATE 21 SETTLEMENT
    # ------------------------------------------------------------

    if (
        state[
            "game"
        ]
        ==
        "pontoon"
        and
        state.get(
            "decision_phase"
        )
        !=
        "insurance"
    ):

        hands = state[
            "hands"
        ][
            str(
                seat
            )
        ]

        for hand in hands:

            if (
                hand.get(
                    "immediate_paid",
                    0,
                )
                or
                hand.get(
                    "doubled"
                )
                or
                hand.get(
                    "surrendered"
                )
                or
                hand.get(
                    "double_withdrawn"
                )
            ):

                continue

            if (
                _bj_total(
                    "pontoon",
                    hand,
                )
                ==
                21
                and
                not _bj_bust(
                    "pontoon",
                    hand,
                )
            ):

                stake = Decimal(
                    str(
                        hand.get(
                            "stake",
                            0,
                        )
                    )
                )

                if (
                    is_blackjack(
                        hand[
                            "cards"
                        ]
                    )
                    and
                    not hand.get(
                        "from_split"
                    )
                ):

                    multiplier = Decimal(
                        "1.5"
                    )

                else:

                    import game.pontoon as pontoon_module

                    combo = (
                        pontoon_module
                        ._special_combo(
                            hand[
                                "cards"
                            ]
                        )[0]
                    )

                    multiplier = (
                        pontoon_module
                        ._COMBO_PAYS
                        .get(
                            combo,
                            Decimal(
                                "1"
                            ),
                        )
                        if combo
                        else
                        Decimal(
                            "1"
                        )
                    )

                value = float(
                    stake
                    +
                    stake *
                    multiplier
                )

                hand[
                    "immediate_paid"
                ] = value

                immediate += value

                hand[
                    "status"
                ] = "paid21"

    response = _visible(
        state
    )

    response.update(
        {
            "seat":
                seat,

            "hand_index":
                hand_index,

            "extra_stake":
                extra,

            "immediate_return":
                immediate,
        }
    )

    return response


# ================================================================
# BLACKJACK SETTLEMENT HELPERS
# ================================================================

def _pontoon_combo(
    cards,
):

    import game.pontoon as module

    return module._special_combo(
        cards
    )[0]


def _main_result(
    game,
    hand,
    dealer,
):

    if hand.get(
        "double_withdrawn"
    ):

        return "double_withdrawn"

    if hand.get(
        "surrendered"
    ):

        return "surrender"

    if hand.get(
        "immediate_paid"
    ):

        return "paid"

    cards = hand[
        "cards"
    ]

    player_blackjack = (
        is_blackjack(
            cards
        )
        and
        not hand.get(
            "from_split"
        )
    )

    dealer_blackjack = is_blackjack(
        dealer
    )

    if _bj_bust(
        game,
        hand,
    ):

        return "lose"

    if (
        game
        ==
        "pontoon"
        and
        _bj_total(
            game,
            hand,
        )
        ==
        21
    ):

        return "win"

    if (
        player_blackjack
        and
        dealer_blackjack
    ):

        return "push"

    if player_blackjack:

        return "blackjack"

    if dealer_blackjack:

        return "lose"

    dealer_total = hand_total(
        dealer
    )

    if dealer_total > 21:

        if (
            game
            ==
            "blackjack_freebet"
            and
            dealer_total
            ==
            22
        ):

            return "push"

        return "win"

    player_total = _bj_total(
        game,
        hand,
    )

    if player_total > dealer_total:

        return "win"

    if player_total < dealer_total:

        return "lose"

    return "push"


def _normal_hand_return(
    game,
    hand,
    result,
    base,
    dealer_blackjack=False,
):

    stake = Decimal(
        str(
            hand.get(
                "stake",
                0,
            )
        )
    )

    paid = Decimal(
        str(
            hand.get(
                "paid_extra",
                0,
            )
        )
    )

    base_amount = Decimal(
        str(
            base
        )
    )

    if hand.get(
        "immediate_paid"
    ):

        return Decimal(
            "0"
        )

    if result == "double_withdrawn":

        return Decimal(
            "0"
        )

    if result == "surrender":

        if (
            game
            ==
            "pontoon"
            and
            dealer_blackjack
        ):

            return Decimal(
                "0"
            )

        return (
            stake *
            Decimal(
                "0.5"
            )
        )

    if result == "lose":

        return Decimal(
            "0"
        )

    if result == "push":

        return (
            stake +
            paid
        )

    if result in (
        "blackjack",
        "pontoon",
    ):

        multiplier = (
            Decimal(
                "1.2"
            )
            if
            game
            ==
            "blackjack_kingsbounty"
            else
            Decimal(
                "1.5"
            )
        )

        return (
            stake
            +
            stake *
            multiplier
        )

    returned = (
        stake +
        paid
    ) * Decimal(
        "2"
    )

    if hand.get(
        "free_marker"
    ):

        returned += base_amount

    if (
        game
        ==
        "pontoon"
        and
        not hand.get(
            "doubled"
        )
    ):

        combo = _pontoon_combo(
            hand[
                "cards"
            ]
        )

        if combo:

            import game.pontoon as pontoon_module

            multiplier = (
                pontoon_module
                ._COMBO_PAYS
                .get(
                    combo
                )
            )

            if multiplier is not None:

                returned = (
                    stake
                    +
                    stake *
                    multiplier
                )

    return returned


# ================================================================
# BLACKJACK SETTLE
# ================================================================

def blackjack_settle(
    payload: dict,
) -> dict:

    state = _bj_dec(
        str(
            payload.get(
                "state_token",
                "",
            )
        )
    )

    (
        current,
        _,
    ) = _current(
        state
    )

    if current is not None:

        raise ValueError(
            "Player decisions are not complete"
        )

    game = state[
        "game"
    ]

    dealer = state[
        "dealer_cards"
    ]

    shoe = state[
        "shoe"
    ]

    needs_dealer = any(
        any(
            (
                not hand.get(
                    "immediate_paid"
                )
                and
                not hand.get(
                    "double_withdrawn"
                )
                and
                not (
                    hand.get(
                        "surrendered"
                    )
                    and
                    game
                    !=
                    "pontoon"
                )
                and
                not _bj_bust(
                    game,
                    hand,
                )
            )
            for hand in
            state[
                "hands"
            ][
                str(
                    seat
                )
            ]
        )
        for seat in
        state[
            "active_seats"
        ]
    )

    if needs_dealer:

        if game in (
            "blackjack_freebet",
            "pontoon",
        ):

            while (
                hand_total(
                    dealer
                )
                <
                17
                or
                (
                    hand_total(
                        dealer
                    )
                    ==
                    17
                    and
                    is_soft(
                        dealer
                    )
                )
            ):

                dealer.append(
                    shoe.pop()
                )

        else:

            complete_dealer_hand(
                dealer,
                shoe,
                soft17_stands=True,
            )

    dealer_blackjack = is_blackjack(
        dealer
    )

    module = registry.get_module(
        game
    )

    seats = {}

    results = []

    total_return = Decimal(
        "0"
    )

    # ------------------------------------------------------------
    # INSURANCE
    # ------------------------------------------------------------

    for seat in state[
        "active_seats"
    ]:

        insurance_wager = Decimal(
            str(
                state[
                    "insurance_wagers"
                ].get(
                    str(
                        seat
                    ),
                    0,
                )
            )
        )

        if insurance_wager:

            hole_rank = state[
                "dealer_hole"
            ][
                "rank"
            ]

            if game == "pontoon":

                won = (
                    hole_rank
                    in (
                        "J",
                        "Q",
                        "K",
                    )
                )

            else:

                won = (
                    hole_rank
                    in (
                        "10",
                        "J",
                        "Q",
                        "K",
                    )
                )

            returned = (
                insurance_wager *
                Decimal(
                    "3"
                )
                if won
                else
                Decimal(
                    "0"
                )
            )

            total_return += returned

            results.append(
                {
                    "wager_type":
                        f"seat{seat}_insurance",

                    "seat":
                        seat,

                    "amount":
                        float(
                            insurance_wager
                        ),

                    "return":
                        float(
                            returned
                        ),

                    "win":
                        won,
                }
            )

    # ------------------------------------------------------------
    # MAIN HANDS
    # ------------------------------------------------------------

    for seat in state[
        "active_seats"
    ]:

        base = _main_bet(
            state,
            seat,
        )

        hand_outputs = []

        seat_return = Decimal(
            "0"
        )

        hands = state[
            "hands"
        ][
            str(
                seat
            )
        ]

        cap_loss = (
            dealer_blackjack
            and
            any(
                hand.get(
                    "from_split"
                )
                or
                hand.get(
                    "doubled"
                )
                for hand in hands
            )
        )

        if cap_loss:

            paid_extras = sum(
                (
                    Decimal(
                        str(
                            hand.get(
                                "paid_extra",
                                0,
                            )
                        )
                    )
                    for hand in hands
                ),
                Decimal(
                    "0"
                ),
            )

            split_extras = sum(
                (
                    Decimal(
                        str(
                            hand.get(
                                "stake",
                                0,
                            )
                        )
                    )
                    for hand in
                    hands[1:]
                ),
                Decimal(
                    "0"
                ),
            )

            seat_return += (
                paid_extras +
                split_extras
            )

            total_return += (
                paid_extras +
                split_extras
            )

        for hand in hands:

            result = _main_result(
                game,
                hand,
                dealer,
            )

            if (
                cap_loss
                and
                result
                ==
                "lose"
            ):

                returned = Decimal(
                    "0"
                )

            else:

                returned = _normal_hand_return(
                    game,
                    hand,
                    result,
                    base,
                    dealer_blackjack,
                )

            total_return += returned

            seat_return += returned

            hand_outputs.append(
                {
                    "cards":
                        hand[
                            "cards"
                        ],

                    "total":
                        _bj_total(
                            game,
                            hand,
                        ),

                    "bust":
                        _bj_bust(
                            game,
                            hand,
                        ),

                    "result":
                        result,

                    "doubled":
                        bool(
                            hand.get(
                                "doubled"
                            )
                        ),

                    "free_marker":
                        bool(
                            hand.get(
                                "free_marker"
                            )
                        ),

                    "surrendered":
                        bool(
                            hand.get(
                                "surrendered"
                            )
                        ),

                    "double_withdrawn":
                        bool(
                            hand.get(
                                "double_withdrawn"
                            )
                        ),

                    "immediate_paid":
                        float(
                            hand.get(
                                "immediate_paid",
                                0,
                            )
                        ),
                }
            )

        initial_cards = state[
            "initial_cards"
        ][
            str(
                seat
            )
        ]

        first = hand_outputs[
            0
        ]

        seat_data = {
            "hands":
                hand_outputs,

            "cards":
                first[
                    "cards"
                ],

            "total":
                first[
                    "total"
                ],

            "bust":
                first[
                    "bust"
                ],

            "result":
                first[
                    "result"
                ],

            "blackjack":
                (
                    first[
                        "result"
                    ]
                    ==
                    "blackjack"
                ),

            "pontoon":
                (
                    game
                    ==
                    "pontoon"
                    and
                    is_blackjack(
                        initial_cards
                    )
                ),

            "pair":
                is_pair(
                    initial_cards
                ),

            "free_markers":
                state[
                    "free_markers"
                ][
                    str(
                        seat
                    )
                ],
        }

        if game == "blackjack_lucky8":

            import game.blackjack_lucky8 as lucky8

            seat_data[
                "lucky8"
            ] = lucky8._lucky8_result(
                initial_cards,
                state[
                    "dealer_up"
                ],
            )

        elif game == "blackjack_kingsbounty":

            import game.blackjack_kingsbounty as kings

            seat_data[
                "kingsbounty"
            ] = kings._kings_bounty_result(
                initial_cards,
                state[
                    "dealer_up"
                ],
                dealer,
            )

            seat_data[
                "bettheset"
            ] = kings._bet_the_set_result(
                initial_cards
            )

            seat_data[
                "royalmatch"
            ] = kings._royal_match_result(
                initial_cards
            )

        elif game == "pontoon":

            seat_data[
                "combo"
            ] = _pontoon_combo(
                first[
                    "cards"
                ]
            )

        seats[
            seat
        ] = seat_data

        if base > 0:

            stake_total = (
                base
                +
                sum(
                    float(
                        hand.get(
                            "stake",
                            0,
                        )
                    )
                    for hand in
                    hands[1:]
                )
                +
                sum(
                    float(
                        hand.get(
                            "paid_extra",
                            0,
                        )
                    )
                    for hand in hands
                )
            )

            results.append(
                {
                    "wager_type":
                        f"seat{seat}_main",

                    "seat":
                        seat,

                    "amount":
                        stake_total,

                    "return":
                        float(
                            seat_return
                        ),

                    "win":
                        (
                            float(
                                seat_return
                            )
                            >
                            stake_total
                        ),
                }
            )

    # ------------------------------------------------------------
    # OUTCOME
    # ------------------------------------------------------------

    outcome = {
        "game":
            game,

        "dealer_up":
            state[
                "dealer_up"
            ],

        "dealer_cards":
            dealer,

        "dealer_total":
            hand_total(
                dealer
            ),

        "dealer_blackjack":
            dealer_blackjack,

        "dealer_pontoon":
            (
                dealer_blackjack
                if
                game
                ==
                "pontoon"
                else
                False
            ),

        "dealer_bust":
            is_bust(
                dealer
            ),

        "dealer_bust_cards":
            (
                len(
                    dealer
                )
                if
                is_bust(
                    dealer
                )
                else
                0
            ),

        "seats":
            seats,

        "active_seats":
            state[
                "active_seats"
            ],
    }

    # ------------------------------------------------------------
    # SIDE BETS
    # ------------------------------------------------------------

    for seat in state[
        "active_seats"
    ]:

        for (
            wager_type,
            amount,
        ) in (
            state[
                "bets_by_seat"
            ]
            .get(
                str(
                    seat
                ),
                {},
            )
            .items()
        ):

            if wager_type.endswith(
                "_main"
            ):

                continue

            returned = module.payout(
                wager_type,
                Decimal(
                    str(
                        amount
                    )
                ),
                outcome,
            )

            total_return += returned

            results.append(
                {
                    "wager_type":
                        wager_type,

                    "seat":
                        seat,

                    "amount":
                        amount,

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
                            amount
                        ),
                }
            )

    # ------------------------------------------------------------
    # PONTOON SUPER BONUS
    # ------------------------------------------------------------

    if game == "pontoon":

        super_bonus_winners = []

        for seat in state[
            "active_seats"
        ]:

            hands = state[
                "hands"
            ][
                str(
                    seat
                )
            ]

            if not hands:

                continue

            hand = hands[
                0
            ]

            cards = hand.get(
                "cards",
                [],
            )

            qualifies = (
                len(
                    cards
                )
                >=
                3
                and
                cards[0][
                    "rank"
                ]
                ==
                "7"
                and
                cards[1][
                    "rank"
                ]
                ==
                "7"
                and
                cards[2][
                    "rank"
                ]
                ==
                "7"
                and
                cards[0][
                    "suit"
                ]
                ==
                cards[1][
                    "suit"
                ]
                ==
                cards[2][
                    "suit"
                ]
                and
                state[
                    "dealer_up"
                ][
                    "rank"
                ]
                ==
                "7"
                and
                not hand.get(
                    "from_split"
                )
                and
                not hand.get(
                    "doubled"
                )
            )

            if qualifies:

                super_bonus_winners.append(
                    seat
                )

        if super_bonus_winners:

            for seat in super_bonus_winners:

                base = Decimal(
                    str(
                        _main_bet(
                            state,
                            seat,
                        )
                    )
                )

                if base >= Decimal(
                    "100"
                ):

                    bonus = Decimal(
                        "5000"
                    )

                elif base >= Decimal(
                    "10"
                ):

                    bonus = Decimal(
                        "1000"
                    )

                else:

                    bonus = Decimal(
                        "0"
                    )

                if bonus > 0:

                    total_return += bonus

                    results.append(
                        {
                            "wager_type":
                                f"seat{seat}_super_bonus",

                            "seat":
                                seat,

                            "amount":
                                0,

                            "return":
                                float(
                                    bonus
                                ),

                            "win":
                                True,
                        }
                    )

            for seat in state[
                "active_seats"
            ]:

                if seat in super_bonus_winners:

                    continue

                base = Decimal(
                    str(
                        _main_bet(
                            state,
                            seat,
                        )
                    )
                )

                if base <= 0:

                    continue

                total_return += Decimal(
                    "50"
                )

                results.append(
                    {
                        "wager_type":
                            f"seat{seat}_super_bonus_50",

                        "seat":
                            seat,

                        "amount":
                            0,

                        "return":
                            50.0,

                        "win":
                            True,
                    }
                )

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

    immediate_total = sum(
        float(
            hand.get(
                "immediate_paid",
                0,
            )
        )
        for seat in
        state[
            "active_seats"
        ]
        for hand in
        state[
            "hands"
        ][
            str(
                seat
            )
        ]
    )

    return {
        "game":
            game,

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

        "immediate_return":
            immediate_total,

        "total_return":
            float(
                total_return
            ),

        "net":
            (
                float(
                    total_return
                )
                +
                immediate_total
                -
                total_wager
            ),

        "results":
            results,
    }


from bridge.dueling_8s import (
    dueling_8s_deal,
    dueling_8s_action,
    dueling_8s_settle,
)


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
