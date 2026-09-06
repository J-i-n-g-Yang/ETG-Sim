"""
api/solo.py — solo game endpoints, including interactive MBS blackjack variants.
"""
import json, base64, random
from decimal import Decimal
from flask import Blueprint, request, jsonify, current_app, render_template

import game.registry as registry
import game.roulette as roulette
import game.poker_engine as poker_engine
from game.blackjack_base import (
    build_shoe, hand_total, is_blackjack, is_bust, is_pair,
    complete_dealer_hand, card_point_value, is_soft,
)
import game.dice_engine as dice_engine
import game.craps_engine as craps_engine
import game.roulette_engine as roulette_engine
import game.dueling_8s_21 as dueling_8s
import game.royal_three_pictures as royal_three_pictures

solo_bp = Blueprint("solo", __name__)
_ALLOWED_GAMES = ("baccarat","baccarat_dragon_tiger","baccarat_immortal","baccarat_rising","sicbo","roulette","craps","great_fortune_dice")
_BACCARAT_GAMES = ("baccarat_dragon_tiger","baccarat_immortal","baccarat_rising")
_BLACKJACK_GAMES = ("blackjack_lucky8","blackjack_freebet","blackjack_kingsbounty","pontoon")


@solo_bp.route("/baccarat/<variant>", methods=["GET"])
def baccarat_game(variant):
    if variant not in _BACCARAT_GAMES:
        return "Unknown Baccarat variant", 404
    names = {
        "baccarat_dragon_tiger": ("🐉", "Dragon Tiger No Commission Baccarat"),
        "baccarat_immortal": ("♾️", "Immortal Dragon Tiger No Commission Baccarat"),
        "baccarat_rising": ("🔥", "Rising Dragon Tiger No Commission Baccarat"),
    }
    icon, name = names[variant]
    return render_template("baccarat_game.html", game=variant, game_name=name, game_icon=icon,
        max_bet=current_app.config.get("MAX_BET",20000),
        starting_credits=current_app.config.get("STARTING_CREDITS",100000))

@solo_bp.route("/spin", methods=["POST"])
def spin():
    data=request.get_json(silent=True) or {}
    game=str(data.get("game",""))
    if game not in _ALLOWED_GAMES: return jsonify({"error":"Unknown game"}),400
    bets=data.get("bets")
    if not isinstance(bets,list) or not bets: return jsonify({"error":"No bets supplied"}),400
    max_bet=float(current_app.config.get("MAX_BET",20000))
    clean=[]; total=0.0
    for b in bets:
        try: wt=str(b["wager_type"]); amt=float(b["amount"])
        except Exception: return jsonify({"error":"Malformed bet"}),400
        if amt!=amt or amt<=0 or amt>max_bet: return jsonify({"error":"Invalid amount"}),400
        if not registry.validate_wager(game,wt): return jsonify({"error":f"Invalid wager_type for {game}: {wt}"}),400
        total+=amt; clean.append((wt,amt))
    if total>max_bet: return jsonify({"error":f"Total stake per spin is capped at {int(max_bet)} credits"}),400
    mod=registry.get_module(game)
    outcome=mod.resolve(point=(data.get("state") or {}).get("point")) if game=="craps" else mod.resolve()
    lightning=roulette.draw_lightning() if game=="roulette" else None
    results=[]; tr=Decimal("0")
    for wt,amt in clean:
        ret=mod.payout(wt,Decimal(str(amt)),outcome,lightning=lightning) if game=="roulette" else mod.payout(wt,Decimal(str(amt)),outcome)
        rf=float(ret); tr+=Decimal(str(rf))
        results.append({"wager_type":wt,"amount":amt,"return":rf,"win":rf>amt})
    resp={"game":game,"outcome":outcome,"total_wager":total,"total_return":float(tr),"net":float(tr)-total,"results":results}
    if lightning is not None: resp["lightning"]={str(k):v for k,v in lightning.items()}
    return jsonify(resp)

_DICE_GAMES = dice_engine.GAMES


@solo_bp.route("/dice/<variant>", methods=["GET"])
def dice_game(variant):
    if variant not in _DICE_GAMES:
        return "Unknown Dice variant", 404

    return render_template(
        "dice_game.html",
        game=variant,
        game_name=dice_engine.NAMES[variant],
        game_icon=dice_engine.ICONS[variant],
        max_bet=current_app.config.get("MAX_BET", 20000),
        starting_credits=current_app.config.get("STARTING_CREDITS", 100000),
    )


@solo_bp.route("/dice/roll", methods=["POST"])
def dice_roll():
    data = request.get_json(silent=True) or {}

    game = str(data.get("game", ""))
    bets = data.get("bets")
    state = data.get("state") or {}

    if game not in _DICE_GAMES:
        return jsonify(
            {"error": "Unknown Dice game"}
        ), 400

    if bets is None:
        bets = []

    if not isinstance(bets, list):
        return jsonify(
            {"error": "Bets must be a list"}
        ), 400

    if not bets:
        if game != "craps":
            return jsonify(
                {"error": "No bets supplied"}
            ), 400

        has_active_craps_wager = False
        active_bets = state.get("bets") or {}

        if any(
            float(amount or 0) > 0
            for amount in active_bets.values()
        ):
            has_active_craps_wager = True

        for bucket_name in (
            "come",
            "dont_come",
            "come_odds",
            "dont_come_odds",
        ):
            bucket = state.get(bucket_name) or {}

            if any(
                float(amount or 0) > 0
                for amount in bucket.values()
            ):
                has_active_craps_wager = True
                break

        if not has_active_craps_wager:
            return jsonify(
                {"error": "No active Craps wagers on the table"}
            ), 400

    max_bet = float(current_app.config.get("MAX_BET", 20000))
    clean = []
    total = 0.0

    for bet in bets:
        try:
            wager_type = str(bet["wager_type"])
            amount = float(bet["amount"])
        except (KeyError, TypeError, ValueError):
            return jsonify({"error": "Malformed bet"}), 400

        if amount != amount or amount <= 0 or amount > max_bet:
            return jsonify({"error": "Invalid amount"}), 400

        if not dice_engine.validate_wager(game, wager_type):
            return jsonify(
                {"error": f"Invalid wager_type for {game}: {wager_type}"}
            ), 400

        total += amount
        clean.append((wager_type, amount))

    if total > max_bet:
        return jsonify(
            {"error": f"Total stake per roll is capped at {int(max_bet)} credits"}
        ), 400

    try:
        result = dice_engine.roll(game, clean, state=state)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


@solo_bp.route("/dice/craps/action", methods=["POST"])
def dice_craps_action():
    data = request.get_json(silent=True) or {}

    try:
        result = craps_engine.action(
            data.get("state") or {},
            str(data.get("wager_type", "")),
            str(data.get("action", "")),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


# ================================================================
# ROULETTE
# ================================================================

_ROULETTE_GAMES = roulette_engine.GAMES


@solo_bp.route("/roulette/<variant>", methods=["GET"])
def roulette_game(variant):
    if variant not in _ROULETTE_GAMES:
        return "Unknown Roulette variant", 404

    return render_template(
        "roulette_game.html",
        game=variant,
        game_name=roulette_engine.NAMES[variant],
        game_icon=roulette_engine.ICONS[variant],
        max_bet=current_app.config.get("MAX_BET", 20000),
        starting_credits=current_app.config.get("STARTING_CREDITS", 100000),
    )


@solo_bp.route("/roulette/spin", methods=["POST"])
def roulette_spin():
    data = request.get_json(silent=True) or {}
    game = str(data.get("game", ""))
    bets = data.get("bets")

    if game not in _ROULETTE_GAMES:
        return jsonify({"error": "Unknown Roulette game"}), 400

    if not isinstance(bets, list) or not bets:
        return jsonify({"error": "No bets supplied"}), 400

    max_bet = float(current_app.config.get("MAX_BET", 20000))
    clean = []
    total = 0.0

    for bet in bets:
        try:
            wager_type = str(bet["wager_type"])
            amount = float(bet["amount"])
        except (KeyError, TypeError, ValueError):
            return jsonify({"error": "Malformed bet"}), 400

        if amount != amount or amount <= 0 or amount > max_bet:
            return jsonify({"error": "Invalid amount"}), 400

        if not roulette_engine.validate_wager(game, wager_type):
            return jsonify(
                {"error": f"Invalid wager_type for {game}: {wager_type}"}
            ), 400

        total += amount
        clean.append({"wager_type": wager_type, "amount": amount})

    if total > max_bet:
        return jsonify(
            {"error": f"Total stake per spin is capped at {int(max_bet)} credits"}
        ), 400

    try:
        result = roulette_engine.spin(game, clean)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


# ================================================================
# DUELING 8'S 21+ — THREE-SEAT INTERACTIVE SOLO
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


# ----------------------------------------------------------------
# BASIC HELPERS
# ----------------------------------------------------------------

def _d8_draw(st):
    if not st["shoe"]:
        raise ValueError(
            "Dueling 8's shoe exhausted"
        )

    return st["shoe"].pop(0)


def _d8_main_bet(st, seat):
    return float(
        (
            st.get(
                "bets_by_seat",
                {},
            ).get(
                str(seat),
                {},
            )
        ).get(
            "main",
            0,
        )
    )


def _d8_hand_status(hand):
    if hand.get("surrendered"):
        return "surrendered"

    total = dueling_8s.hand_total(
        hand["cards"]
    )

    if total > 21:
        return "bust"

    if total == 21:
        return "stood"

    return "playing"


# ----------------------------------------------------------------
# SEAT / HAND PROGRESSION
# ----------------------------------------------------------------

def _d8_advance(st):
    """
    Advance through:

        Seat 0 hands
        Seat 1 hands
        Seat 2 hands

    skipping inactive seats and completed hands.
    """

    active_seats = st[
        "active_seats"
    ]

    while (
        st["seat_pos"] <
        len(active_seats)
    ):
        seat = active_seats[
            st["seat_pos"]
        ]

        seat_key = str(seat)

        hands = st[
            "hands"
        ][seat_key]

        hand_pos = st[
            "hand_pos"
        ].get(
            seat_key,
            0,
        )

        while (
            hand_pos <
            len(hands)
            and hands[
                hand_pos
            ].get(
                "status"
            ) != "playing"
        ):
            hand_pos += 1

        st[
            "hand_pos"
        ][seat_key] = hand_pos

        if (
            hand_pos <
            len(hands)
        ):
            return

        st["seat_pos"] += 1

    st["stage"] = "settle"


def _d8_current(st):
    _d8_advance(st)

    if (
        st.get("stage") !=
        "play"
    ):
        return (
            None,
            None,
        )

    active_seats = st[
        "active_seats"
    ]

    if (
        st["seat_pos"] >=
        len(active_seats)
    ):
        return (
            None,
            None,
        )

    seat = active_seats[
        st["seat_pos"]
    ]

    hand_index = st[
        "hand_pos"
    ][str(seat)]

    return (
        seat,
        hand_index,
    )


# ----------------------------------------------------------------
# CLIENT-SAFE STATE
# ----------------------------------------------------------------

def _d8_visible(st):
    current_seat, current_hand = (
        _d8_current(st)
    )

    table_minimum = float(
        st.get(
            "table_minimum",
            1,
        )
    )

    seats = {}

    for seat in st[
        "active_seats"
    ]:
        seat_key = str(seat)

        visible_hands = []

        for (
            index,
            hand,
        ) in enumerate(
            st["hands"][
                seat_key
            ]
        ):
            actions = []

            if (
                st.get("stage") ==
                "play"
                and seat ==
                current_seat
                and index ==
                current_hand
                and hand.get(
                    "status"
                ) ==
                "playing"
            ):
                actions = (
                    dueling_8s
                    .available_actions(
                        hand,
                        total_hands=len(
                            st[
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
                st[
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
            _enc(st),

        "dealer_cards":
            st[
                "dealer_cards"
            ],

        "dealer_up":
            st[
                "dealer_cards"
            ][0],

        "active_seats":
            st[
                "active_seats"
            ],

        "seats":
            seats,

        "current_seat":
            current_seat,

        "current_hand":
            current_hand,

        "stage":
            st[
                "stage"
            ],

        "all_done":
            st[
                "stage"
            ] ==
            "settle",

        "initial_total_wager":
            float(
                st[
                    "initial_total_wager"
                ]
            ),

        "extra_wager":
            float(
                st[
                    "extra_wager"
                ]
            ),

        "total_wager":
            float(
                st[
                    "initial_total_wager"
                ]
            )
            +
            float(
                st[
                    "extra_wager"
                ]
            ),
    }


# ================================================================
# PAGE
# ================================================================

@solo_bp.route(
    "/dueling-8s",
    methods=["GET"],
)
def dueling_8s_game():
    return render_template(
        "dueling_8s_game.html",

        game=
            _DUELING_8S_GAME,

        game_name=
            "Dueling 8's 21+",

        game_icon=
            "8️⃣",

        max_bet=
            current_app.config.get(
                "MAX_BET",
                20000,
            ),

        starting_credits=
            current_app.config.get(
                "STARTING_CREDITS",
                100000,
            ),
    )


# ================================================================
# DEAL
# ================================================================

@solo_bp.route(
    "/dueling-8s/deal",
    methods=["POST"],
)
def dueling_8s_deal():
    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    game = str(
        data.get(
            "game",
            "",
        )
    )

    if (
        game and
        game !=
        _DUELING_8S_GAME
    ):
        return jsonify(
            {
                "error":
                    "Unknown Dueling 8's game"
            }
        ), 400

    bets = data.get(
        "bets"
    )

    if (
        not isinstance(
            bets,
            list,
        )
        or not bets
    ):
        return jsonify(
            {
                "error":
                    "No bets supplied"
            }
        ), 400

    max_bet = float(
        current_app.config.get(
            "MAX_BET",
            20000,
        )
    )

    try:
        table_minimum = float(
            data.get(
                "table_minimum",
                1,
            )
            or 1
        )
    except (
        TypeError,
        ValueError,
    ):
        return jsonify(
            {
                "error":
                    "Invalid table minimum"
            }
        ), 400

    if (
        table_minimum <= 0
    ):
        return jsonify(
            {
                "error":
                    "Invalid table minimum"
            }
        ), 400

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
        ):
            return jsonify(
                {
                    "error":
                        "Malformed bet"
                }
            ), 400

        if seat not in (
            0,
            1,
            2,
        ):
            return jsonify(
                {
                    "error":
                        "Invalid Dueling 8's seat"
                }
            ), 400

        wager_type = aliases.get(
            wager_type,
            wager_type,
        )

        if (
            wager_type not in
            _DUELING_8S_WAGERS
        ):
            return jsonify(
                {
                    "error":
                        f"Invalid Dueling 8's wager: "
                        f"{wager_type}"
                }
            ), 400

        if (
            amount != amount
            or amount <= 0
            or amount >
            max_bet
        ):
            return jsonify(
                {
                    "error":
                        "Invalid amount"
                }
            ), 400

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
        return jsonify(
            {
                "error":
                    f"Total initial stake capped at "
                    f"{int(max_bet)} credits"
            }
        ), 400

    # ------------------------------------------------------------
    # DETERMINE ACTIVE SEATS
    #
    # Main is required on every active seat.
    # ------------------------------------------------------------

    active_seats = []

    for seat_key in sorted(
        bets_by_seat.keys(),
        key=int,
    ):
        seat_bets = (
            bets_by_seat[
                seat_key
            ]
        )

        main = float(
            seat_bets.get(
                "main",
                0,
            )
        )

        if main <= 0:
            return jsonify(
                {
                    "error":
                        f"Seat {int(seat_key) + 1} "
                        f"requires a Main wager"
                }
            ), 400

        if (
            main <
            table_minimum
        ):
            return jsonify(
                {
                    "error":
                        f"Seat {int(seat_key) + 1} "
                        f"Main wager is below "
                        f"the table minimum"
                }
            ), 400

        active_seats.append(
            int(
                seat_key
            )
        )

    if not active_seats:
        return jsonify(
            {
                "error":
                    "At least one active seat is required"
            }
        ), 400

    # ------------------------------------------------------------
    # SHOE
    # ------------------------------------------------------------

    try:
        shoe = (
            dueling_8s
            .make_shoe(6)
        )

    except (
        ValueError,
        RuntimeError,
    ) as exc:
        return jsonify(
            {
                "error":
                    str(exc)
            }
        ), 400

    # ------------------------------------------------------------
    # DEAL
    #
    # Every active player receives:
    #
    # permanent 8♠
    # + one random card
    #
    # Dealer begins with permanent 8♠.
    # ------------------------------------------------------------

    hands = {}

    original_cards = {}

    try:
        for seat in (
            active_seats
        ):
            draw = shoe.pop(0)

            cards = (
                dueling_8s
                .initial_player_hand(
                    draw
                )
            )

            main = float(
                bets_by_seat[
                    str(seat)
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
                str(seat)
            ] = [
                hand
            ]

            original_cards[
                str(seat)
            ] = [
                dict(card)
                for card
                in cards
            ]

        dealer_cards = (
            dueling_8s
            .initial_dealer_hand()
        )

    except (
        ValueError,
        RuntimeError,
    ) as exc:
        return jsonify(
            {
                "error":
                    str(exc)
            }
        ), 400

    # ------------------------------------------------------------
    # STATE
    # ------------------------------------------------------------

    st = {
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

        "hand_pos": {
            str(seat):
                0
            for seat
            in active_seats
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

    _d8_advance(st)

    return jsonify(
        _d8_visible(st)
    )


# ================================================================
# ACTION
# ================================================================

@solo_bp.route(
    "/dueling-8s/action",
    methods=["POST"],
)
def dueling_8s_action():
    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    try:
        st = _dec(
            data.get(
                "state_token",
                "",
            )
        )

    except Exception:
        return jsonify(
            {
                "error":
                    "Invalid state token"
            }
        ), 400

    if (
        st.get("game") !=
        _DUELING_8S_GAME
    ):
        return jsonify(
            {
                "error":
                    "Invalid Dueling 8's state"
            }
        ), 400

    current_seat, current_hand = (
        _d8_current(st)
    )

    if (
        current_seat is None
    ):
        return jsonify(
            {
                "error":
                    "Player decisions are complete"
            }
        ), 400

    # ------------------------------------------------------------
    # VERIFY SEAT
    # ------------------------------------------------------------

    try:
        requested_seat = int(
            data.get(
                "seat",
                -1,
            )
        )

        requested_hand = int(
            data.get(
                "hand_index",
                -1,
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return jsonify(
            {
                "error":
                    "Invalid seat or hand index"
            }
        ), 400

    if (
        requested_seat !=
        current_seat
    ):
        return jsonify(
            {
                "error":
                    "It is another seat's turn"
            }
        ), 400

    if (
        requested_hand !=
        current_hand
    ):
        return jsonify(
            {
                "error":
                    "It is another hand's turn"
            }
        ), 400

    seat_key = str(
        current_seat
    )

    hands = st[
        "hands"
    ][seat_key]

    hand = hands[
        current_hand
    ]

    action = str(
        data.get(
            "action",
            "",
        )
    ).strip().lower()

    table_minimum = float(
        st.get(
            "table_minimum",
            1,
        )
    )

    allowed = (
        dueling_8s
        .available_actions(
            hand,
            total_hands=len(
                hands
            ),
            table_minimum=
                table_minimum,
        )
    )

    if (
        action not in
        allowed
    ):
        return jsonify(
            {
                "error":
                    f"Action is not available: "
                    f"{action}"
            }
        ), 400

    extra = 0.0

    max_bet = float(
        current_app.config.get(
            "MAX_BET",
            20000,
        )
    )

    try:

        # --------------------------------------------------------
        # HIT
        # --------------------------------------------------------

        if (
            action ==
            "hit"
        ):
            hand[
                "acted"
            ] = True

            hand[
                "cards"
            ].append(
                _d8_draw(st)
            )

            hand[
                "status"
            ] = _d8_hand_status(
                hand
            )

        # --------------------------------------------------------
        # STAND
        # --------------------------------------------------------

        elif (
            action ==
            "stand"
        ):
            hand[
                "acted"
            ] = True

            hand[
                "status"
            ] = "stood"

        # --------------------------------------------------------
        # SURRENDER
        # --------------------------------------------------------

        elif (
            action ==
            "surrender"
        ):
            hand[
                "acted"
            ] = True

            hand[
                "surrendered"
            ] = True

            hand[
                "status"
            ] = "surrendered"

        # --------------------------------------------------------
        # DOUBLE
        # --------------------------------------------------------

        elif (
            action ==
            "double"
        ):
            try:
                amount = float(
                    data.get(
                        "amount"
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                return jsonify(
                    {
                        "error":
                            "Double requires an amount"
                    }
                ), 400

            original_wager = float(
                hand[
                    "original_stake"
                ]
            )

            if (
                amount != amount
                or amount <= 0
                or not (
                    dueling_8s
                    .double_amount_valid(
                        amount,
                        original_wager,
                        table_minimum,
                    )
                )
            ):
                return jsonify(
                    {
                        "error":
                            "Double amount must be between "
                            "the table minimum and "
                            "the original wager"
                    }
                ), 400

            if (
                float(
                    st[
                        "initial_total_wager"
                    ]
                )
                +
                float(
                    st[
                        "extra_wager"
                    ]
                )
                +
                amount
                >
                max_bet
            ):
                return jsonify(
                    {
                        "error":
                            "Total stake exceeds "
                            "the table limit"
                    }
                ), 400

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

            st[
                "extra_wager"
            ] = (
                float(
                    st[
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
                _d8_draw(st)
            )

            hand[
                "status"
            ] = _d8_hand_status(
                hand
            )

            if (
                hand[
                    "status"
                ] ==
                "playing"
            ):
                hand[
                    "status"
                ] = "stood"

        # --------------------------------------------------------
        # SPLIT
        # --------------------------------------------------------

        elif (
            action ==
            "split"
        ):
            if not (
                dueling_8s
                .can_split(
                    hand,
                    total_hands=len(
                        hands
                    ),
                )
            ):
                return jsonify(
                    {
                        "error":
                            "Cannot split this hand"
                    }
                ), 400

            split_cost = float(
                hand[
                    "original_stake"
                ]
            )

            if (
                float(
                    st[
                        "initial_total_wager"
                    ]
                )
                +
                float(
                    st[
                        "extra_wager"
                    ]
                )
                +
                split_cost
                >
                max_bet
            ):
                return jsonify(
                    {
                        "error":
                            "Total stake exceeds "
                            "the table limit"
                    }
                ), 400

            (
                first_card,
                second_card,
            ) = hand[
                "cards"
            ]

            first_hand = {
                "cards": [
                    first_card,
                    _d8_draw(st),
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
                "cards": [
                    second_card,
                    _d8_draw(st),
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

            st[
                "extra_wager"
            ] = (
                float(
                    st[
                        "extra_wager"
                    ]
                )
                +
                split_cost
            )

            extra = split_cost

        else:
            return jsonify(
                {
                    "error":
                        "Invalid action"
                }
            ), 400

    except (
        ValueError,
        RuntimeError,
    ) as exc:
        return jsonify(
            {
                "error":
                    str(exc)
            }
        ), 400

    _d8_advance(st)

    view = _d8_visible(st)

    view[
        "extra_stake"
    ] = extra

    return jsonify(
        view
    )


# ================================================================
# SETTLE
# ================================================================

@solo_bp.route(
    "/dueling-8s/settle",
    methods=["POST"],
)
def dueling_8s_settle():
    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    try:
        st = _dec(
            data.get(
                "state_token",
                "",
            )
        )

    except Exception:
        return jsonify(
            {
                "error":
                    "Invalid state token"
            }
        ), 400

    if (
        st.get("game") !=
        _DUELING_8S_GAME
    ):
        return jsonify(
            {
                "error":
                    "Invalid Dueling 8's state"
            }
        ), 400

    current_seat, _ = (
        _d8_current(st)
    )

    if (
        current_seat is not None
    ):
        return jsonify(
            {
                "error":
                    "Player decisions are not complete"
            }
        ), 400

    shoe = st[
        "shoe"
    ]

    dealer = [
        dict(card)
        for card
        in st[
            "dealer_cards"
        ]
    ]

    # ------------------------------------------------------------
    # DEALER
    # ------------------------------------------------------------

    try:
        dealer = (
            dueling_8s
            .play_dealer(
                shoe,
                dealer,
            )
        )

    except RuntimeError as exc:
        return jsonify(
            {
                "error":
                    str(exc)
            }
        ), 400

    total_return = Decimal(
        "0"
    )

    results = []

    seats = {}

    # ============================================================
    # SETTLE EACH ACTIVE SEAT
    # ============================================================

    for seat in st[
        "active_seats"
    ]:
        seat_key = str(
            seat
        )

        seat_bets = st[
            "bets_by_seat"
        ][seat_key]

        hands = st[
            "hands"
        ][seat_key]

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

            if (
                hand.get(
                    "surrendered"
                )
            ):
                result = (
                    "surrender"
                )

                ret = (
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

                ret = (
                    dueling_8s
                    .regular_return(
                        stake,
                        result,
                    )
                )

            total_return += ret
            seat_return += ret

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
                            ret
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
                            ret
                        ),

                    "win":
                        float(
                            ret
                        )
                        >
                        float(
                            stake
                        ),
                }
            )

        # --------------------------------------------------------
        # IMPORTANT:
        #
        # Side wagers are evaluated against the ORIGINAL
        # unsplit starting hand / sequence for this seat.
        #
        # Do not accidentally use Seat 0's hand for all seats.
        # --------------------------------------------------------

        original_cards = st[
            "original_cards"
        ][seat_key]

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
            main_hand = hands[0]

            ret = (
                dueling_8s
                .six_seven_eight_bonus(
                    side_678,
                    main_hand["cards"],
                    from_split=bool(
                        main_hand.get(
                            "from_split"
                        )
                    ),
                )
            )

            total_return += ret
            seat_return += ret

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
                            ret
                        ),

                    "win":
                        ret > 0,
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
            # Tie on 18 is evaluated using this seat's
            # resulting original/main hand and the Dealer.
            tie_cards = hands[0]["cards"]

            ret = (
                dueling_8s
                .tie_on_18_return(
                    tie_18,
                    tie_cards,
                    dealer,
                )
            )

            total_return += ret
            seat_return += ret

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
                            ret
                        ),

                    "win":
                        ret > 0,
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
            ret = (
                dueling_8s
                .twenty_one_plus_return(
                    twenty_one_plus,
                    dealer,
                )
            )

            total_return += ret
            seat_return += ret

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
                            ret
                        ),

                    "win":
                        ret > 0,
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
            superb_cards = (
                hands[0][
                    "cards"
                ]
            )

            ret = (
                dueling_8s
                .superb_eights_return(
                    superb,
                    superb_cards,
                )
            )

            total_return += ret
            seat_return += ret

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
                            ret
                        ),

                    "win":
                        ret > 0,
                }
            )

        # --------------------------------------------------------
        # SEAT OUTCOME
        # --------------------------------------------------------

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
            st[
                "initial_total_wager"
            ]
        )
        +
        float(
            st[
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
            st[
                "active_seats"
            ],

        "seats":
            seats,

        # Alias retained for the current frontend.
        "hands_by_seat":
            seats,
    }

    return jsonify(
        {
            "game":
                _DUELING_8S_GAME,

            "outcome":
                outcome,

            "total_wager":
                total_wager,

            "extra_wager":
                float(
                    st[
                        "extra_wager"
                    ]
                ),

            "total_return":
                float(
                    total_return
                ),

            "net":
                float(
                    total_return
                )
                -
                total_wager,

            "results":
                results,
        }
    )


# ================================================================
# ROYAL THREE PICTURES — THREE-HAND SOLO
# ================================================================

_ROYAL_THREE_PICTURES_GAME = "royal_three_pictures"


@solo_bp.route("/royal-three-pictures", methods=["GET"])
def royal_three_pictures_game():
    return render_template(
        "royal_three_pictures_game.html",
        game=_ROYAL_THREE_PICTURES_GAME,
        game_name="Royal Three Pictures",
        game_icon="👑",
        max_bet=current_app.config.get("MAX_BET", 20000),
        starting_credits=current_app.config.get("STARTING_CREDITS", 100000),
    )


@solo_bp.route("/royal-three-pictures/deal", methods=["POST"])
def royal_three_pictures_deal():
    data = request.get_json(silent=True) or {}

    game = str(data.get("game", ""))
    if game and game != _ROYAL_THREE_PICTURES_GAME:
        return jsonify({"error": "Unknown Royal Three Pictures game"}), 400

    bets = data.get("bets")
    if not isinstance(bets, list) or not bets:
        return jsonify({"error": "No bets supplied"}), 400

    max_bet = float(current_app.config.get("MAX_BET", 20000))
    bets_by_seat = {}
    total_wager = 0.0

    for bet in bets:
        try:
            seat = int(bet["seat"])
            wager_type = str(bet["wager_type"]).strip().lower()
            amount = float(bet["amount"])
        except (KeyError, TypeError, ValueError):
            return jsonify({"error": "Malformed bet"}), 400

        if seat not in (0, 1, 2):
            return jsonify({"error": "Invalid Royal Three Pictures seat"}), 400

        if not royal_three_pictures.validate_wager(wager_type):
            return jsonify(
                {"error": f"Invalid Royal Three Pictures wager: {wager_type}"}
            ), 400

        if amount != amount or amount <= 0 or amount > max_bet:
            return jsonify({"error": "Invalid amount"}), 400

        seat_bets = bets_by_seat.setdefault(str(seat), {})
        seat_bets[wager_type] = float(seat_bets.get(wager_type, 0)) + amount
        total_wager += amount

    if total_wager > max_bet:
        return jsonify(
            {"error": f"Total initial stake capped at {int(max_bet)} credits"}
        ), 400

    active_seats = sorted(int(key) for key in bets_by_seat)

    for seat in active_seats:
        if float(bets_by_seat[str(seat)].get("main", 0)) <= 0:
            return jsonify(
                {"error": f"Seat {seat + 1} requires a Main wager"}
            ), 400

    try:
        deck = royal_three_pictures.make_deck()

        player_hands = {}
        for seat in active_seats:
            player_hands[str(seat)] = [
                deck.pop(0),
                deck.pop(0),
                deck.pop(0),
            ]

        dealer_cards = [
            deck.pop(0),
            deck.pop(0),
            deck.pop(0),
        ]
    except (ValueError, RuntimeError, IndexError) as exc:
        return jsonify({"error": str(exc)}), 400

    total_return = Decimal("0")
    results = []
    outcome_seats = {}
    visible_seats = {}

    for seat in active_seats:
        seat_key = str(seat)
        cards = player_hands[seat_key]
        seat_bets = bets_by_seat[seat_key]

        main_result = royal_three_pictures.compare_hands(
            cards,
            dealer_cards,
        )
        tie_result = royal_three_pictures.is_tie(
            cards,
            dealer_cards,
        )
        royal_result = royal_three_pictures.royal_pictures_result(
            cards
        )

        seat_return = Decimal("0")

        main_stake = Decimal(str(seat_bets["main"]))
        main_ret = royal_three_pictures.main_return(
            main_stake,
            cards,
            dealer_cards,
        )
        seat_return += main_ret
        total_return += main_ret

        results.append(
            {
                "seat": seat,
                "wager_type": "main",
                "amount": float(main_stake),
                "return": float(main_ret),
                "win": main_ret > main_stake,
                "result": main_result,
            }
        )

        tie_stake = Decimal(str(seat_bets.get("tie", 0)))
        if tie_stake > 0:
            tie_ret = royal_three_pictures.tie_return(
                tie_stake,
                cards,
                dealer_cards,
            )
            seat_return += tie_ret
            total_return += tie_ret

            results.append(
                {
                    "seat": seat,
                    "wager_type": "tie",
                    "amount": float(tie_stake),
                    "return": float(tie_ret),
                    "win": tie_ret > 0,
                }
            )

        royal_stake = Decimal(
            str(seat_bets.get("royal_pictures", 0))
        )
        if royal_stake > 0:
            royal_ret = royal_three_pictures.royal_pictures_return(
                royal_stake,
                cards,
            )
            seat_return += royal_ret
            total_return += royal_ret

            results.append(
                {
                    "seat": seat,
                    "wager_type": "royal_pictures",
                    "amount": float(royal_stake),
                    "return": float(royal_ret),
                    "win": royal_ret > 0,
                    "category": royal_result,
                }
            )

        hand_view = {
            "cards": cards,
            "point_total": royal_three_pictures.point_total(cards),
            "picture_count": royal_three_pictures.picture_count(cards),
            "hand_name": royal_three_pictures.hand_name(cards),
            "main_result": main_result,
            "tie": tie_result,
            "royal_pictures": royal_result,
            "total_return": float(seat_return),
        }

        outcome_seats[seat_key] = hand_view

        visible_seats[seat_key] = {
            **hand_view,
            "bets": seat_bets,
            # Frontend can display Seat 0 as the viewed hand and
            # additional active positions as blind positions.
            "viewed": seat == active_seats[0],
            "blind": seat != active_seats[0],
        }

    dealer_view = {
        "cards": dealer_cards,
        "point_total": royal_three_pictures.point_total(dealer_cards),
        "picture_count": royal_three_pictures.picture_count(dealer_cards),
        "hand_name": royal_three_pictures.hand_name(dealer_cards),
    }

    outcome = {
        "game": _ROYAL_THREE_PICTURES_GAME,
        "dealer_cards": dealer_cards,
        "dealer": dealer_view,
        "active_seats": active_seats,
        "seats": outcome_seats,
    }

    return jsonify(
        {
            "game": _ROYAL_THREE_PICTURES_GAME,
            "stage": "settled",
            "all_done": True,
            "active_seats": active_seats,
            "dealer_cards": dealer_cards,
            "dealer": dealer_view,
            "seats": visible_seats,
            "outcome": outcome,
            "total_wager": total_wager,
            "total_return": float(total_return),
            "net": float(total_return) - total_wager,
            "results": results,
        }
    )


_POKER_GAMES = poker_engine.GAMES

@solo_bp.route("/poker/<variant>", methods=["GET"])
def poker_game(variant):
    if variant not in _POKER_GAMES:
        return "Unknown Poker variant", 404

    return render_template(
        "poker_game.html",
        game=variant,
        game_name=poker_engine.NAMES[variant],
        game_icon=poker_engine.ICONS[variant],
        max_bet=current_app.config.get("MAX_BET", 20000),
        starting_credits=current_app.config.get("STARTING_CREDITS", 100000),
    )


@solo_bp.route("/poker/deal", methods=["POST"])
def poker_deal():
    data = request.get_json(silent=True) or {}
    game = str(data.get("game", ""))
    bets = data.get("bets") or []

    if game not in _POKER_GAMES:
        return jsonify({"error": "Unknown poker game"}), 400

    if not isinstance(bets, list) or not bets:
        return jsonify({"error": "No bets supplied"}), 400

    max_bet = float(current_app.config.get("MAX_BET", 20000))
    total = 0.0
    clean = []

    for b in bets:
        try:
            seat = int(b["seat"])
            wager_type = str(b["wager_type"])
            amount = float(b["amount"])
        except Exception:
            return jsonify({"error": "Malformed bet"}), 400

        if seat not in (0, 1, 2) or amount <= 0 or amount > max_bet:
            return jsonify({"error": "Invalid bet"}), 400

        allowed = poker_engine.allowed_initial_wagers(game, seat)

        if wager_type not in allowed:
            return jsonify(
                {"error": f"Invalid poker wager: {wager_type}"}
            ), 400

        total += amount
        clean.append(
            {
                "seat": seat,
                "wager_type": wager_type,
                "amount": amount,
            }
        )

    if total > max_bet:
        return jsonify(
            {"error": f"Total initial stake capped at {int(max_bet)} credits"}
        ), 400

    by_seat = {}
    for b in clean:
        by_seat.setdefault(b["seat"], {})[b["wager_type"]] = b["amount"]

    for seat, seat_bets in by_seat.items():
        ante = float(seat_bets.get(f"seat{seat}_ante", 0))

        if game == "poker_ultimate_texas":
            blind = float(seat_bets.get(f"seat{seat}_blind", 0))

            if ante <= 0 or blind != ante:
                return jsonify(
                    {"error": "Ultimate Texas Hold'em requires equal Ante and Blind"}
                ), 400

        elif game == "poker_three_card_xtreme":
            has_side = any(
                float(seat_bets.get(f"seat{seat}_{key}", 0)) > 0
                for key in ("pair_plus", "six_card_bonus")
            )

            if ante <= 0 and not has_side:
                return jsonify({"error": "No valid wager for seat"}), 400

        else:
            if ante <= 0:
                return jsonify(
                    {"error": "This Poker variant requires an Ante wager"}
                ), 400

    try:
        state = poker_engine.deal(game, clean)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    view = poker_engine.visible(state)
    view["total_wager"] = total
    view["progressive_available"] = poker_engine.PROGRESSIVE_ENABLED

    return jsonify(view)


@solo_bp.route("/poker/action", methods=["POST"])
def poker_action():
    data = request.get_json(silent=True) or {}

    try:
        state = poker_engine.dec(data.get("state_token", ""))
    except Exception:
        return jsonify({"error": "Invalid state token"}), 400

    try:
        extra = poker_engine.action(
            state,
            int(data.get("seat", -1)),
            str(data.get("action", "")),
            low_indices=data.get("low_indices"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    view = poker_engine.visible(state)
    view["extra_stake"] = extra

    return jsonify(view)


@solo_bp.route("/poker/settle", methods=["POST"])
def poker_settle():
    data = request.get_json(silent=True) or {}

    try:
        state = poker_engine.dec(data.get("state_token", ""))
    except Exception:
        return jsonify({"error": "Invalid state token"}), 400

    if state.get("stage") != "settle":
        return jsonify({"error": "Poker decisions are not complete"}), 400

    out = poker_engine.settle(state)

    initial = sum(
        float(value)
        for seat_bets in state["bets"].values()
        for value in seat_bets.values()
    )

    total_wager = initial + float(state.get("extra", 0))

    out.update(
        {
            "game": state["game"],
            "total_wager": total_wager,
            "net": float(out["total_return"]) - total_wager,
        }
    )

    return jsonify(out)


@solo_bp.route("/blackjack", methods=["POST"])
def blackjack_legacy():
    data=request.get_json(silent=True) or {}; game=str(data.get("game",""))
    if game not in _BLACKJACK_GAMES: return jsonify({"error":"Unknown blackjack variant"}),400
    bets=data.get("bets") or []; active=sorted({int(b.get("seat",-1)) for b in bets if int(b.get("seat",-1)) in (0,1,2)})
    mod=registry.get_module(game); outcome=mod.resolve(active_seats=active)
    results=[]; tr=Decimal("0"); tw=0.0
    for b in bets:
        amt=float(b["amount"]); ret=mod.payout(str(b["wager_type"]),Decimal(str(amt)),outcome)
        rf=float(ret); tr+=Decimal(str(rf)); tw+=amt
        results.append({"wager_type":b["wager_type"],"seat":int(b["seat"]),"amount":amt,"return":rf,"win":rf>amt})
    return jsonify({"game":game,"outcome":outcome,"total_wager":tw,"total_return":float(tr),"net":float(tr)-tw,"results":results})

def _enc(s):
    return base64.b64encode(json.dumps(s,separators=(",", ":")).encode()).decode()

def _dec(t):
    return json.loads(base64.b64decode(t.encode()).decode())

def _pontoon_shoe(n=6):
    ranks=["A","2","3","4","5","6","7","8","9","J","Q","K"]
    d=[{"rank":r,"suit":s} for s in ("S","H","D","C") for r in ranks]*n
    random.shuffle(d); return d

def _pair_value(cards):
    return len(cards)==2 and card_point_value(cards[0]["rank"])==card_point_value(cards[1]["rank"])

def _main_bet(st,s):
    return float(st["bets_by_seat"].get(str(s),{}).get(f"seat{s}_main",0))

def _pontoon_total(h):
    cards=h["cards"]
    if not h.get("pontoon_double_ace"):
        return hand_total(cards)
    total=0; flexible_aces=0
    for i,c in enumerate(cards):
        if c["rank"]=="A":
            if i < 2: total += 1
            else: total += 11; flexible_aces += 1
        else: total += card_point_value(c["rank"])
    while total>21 and flexible_aces:
        total-=10; flexible_aces-=1
    return total

def _total(game,h):
    return _pontoon_total(h) if game=="pontoon" else hand_total(h["cards"])

def _bust(game,h): return _total(game,h)>21

def _hand_status(game,h):
    if _bust(game,h): return "bust"
    if _total(game,h)==21 or h.get("split_aces"): return "stood"
    return "playing"

def _eligible_double(game,h):
    return h["status"]=="playing" and len(h["cards"])==2 and not h.get("split_aces")

def _eligible_split(st,s,h):
    if h["status"]!="playing" or len(h["cards"])!=2 or not _pair_value(h["cards"]): return False
    hs=st["hands"][str(s)]
    if len(hs)>=4: return False
    if h["cards"][0]["rank"]=="A" and any(x.get("from_split_aces") for x in hs): return False
    return True

def _free_double(game,h):
    return game=="blackjack_freebet" and len(h["cards"])==2 and hand_total(h["cards"]) in (9,10,11) and not is_soft(h["cards"])

def _free_split(game,h):
    return game=="blackjack_freebet" and card_point_value(h["cards"][0]["rank"]) != 10

def _can_surrender(st,h):
    if h["status"]!="playing" or len(h["cards"])!=2 or h.get("from_split"): return False
    up=st["dealer_up"]["rank"]
    if st["game"]=="pontoon": return up in ("A","K","Q","J")
    return up!="A"

def _advance(st):
    seats=st["active_seats"]
    while st["seat_pos"] < len(seats):
        s=str(seats[st["seat_pos"]]); hs=st["hands"][s]
        while st["hand_pos"].get(s,0)<len(hs) and hs[st["hand_pos"][s]]["status"]!="playing":
            st["hand_pos"][s]+=1
        if st["hand_pos"][s]<len(hs): return
        st["seat_pos"]+=1

def _current(st):
    _advance(st)
    if st.get("decision_phase")=="insurance":
        while st["insurance_pos"] < len(st["active_seats"]):
            s=st["active_seats"][st["insurance_pos"]]
            if not st["insurance_decisions"].get(str(s)): return s,None
            st["insurance_pos"]+=1
        st["decision_phase"]="play"
    _advance(st)
    if st["seat_pos"]>=len(st["active_seats"]): return None,None
    s=st["active_seats"][st["seat_pos"]]
    return s,st["hand_pos"][str(s)]

def _visible(st):
    cur_s,cur_h=_current(st)
    seats={}
    for s in st["active_seats"]:
        hs=st["hands"][str(s)]
        vh=[]
        for h in hs:
            vh.append({"cards":h["cards"],"total":_total(st["game"],h),"status":h["status"],
                "can_hit":h["status"]=="playing","can_stand":h["status"]=="playing",
                "can_double":_eligible_double(st["game"],h),"can_split":_eligible_split(st,s,h),
                "can_surrender":_can_surrender(st,h),
                "can_withdraw_double":st["game"]=="pontoon" and h.get("awaiting_double_withdraw",False),
                "free_double":_free_double(st["game"],h) if _eligible_double(st["game"],h) else False,
                "free_split":_free_split(st["game"],h) if _eligible_split(st,s,h) else False,
                "free_marker":bool(h.get("free_marker"))})
        seats[str(s)]={"hands":vh}
        if vh: seats[str(s)].update(vh[0])
    phase=st.get("decision_phase","play")
    insurance_offer=None
    if phase=="insurance" and cur_s is not None:
        h=st["hands"][str(cur_s)][0]
        insurance_offer={"seat":cur_s,"amount":_main_bet(st,cur_s)/2,
                         "even_money":st["game"]!="pontoon" and is_blackjack(h["cards"]) and not h.get("from_split")}
    return {"state_token":_enc(st),"dealer_up":st["dealer_up"],"active_seats":st["active_seats"],"seats":seats,
            "current_seat":cur_s,"current_hand":cur_h,"decision_phase":phase,"insurance_offer":insurance_offer,
            "all_done":cur_s is None and phase!="insurance"}

@solo_bp.route("/blackjack/deal",methods=["POST"])
def bj_deal():
    data=request.get_json(silent=True) or {}; game=str(data.get("game","")); bets=data.get("bets")
    if game not in _BLACKJACK_GAMES: return jsonify({"error":"Unknown blackjack variant"}),400
    if not isinstance(bets,list) or not bets: return jsonify({"error":"No bets supplied"}),400
    max_bet=float(current_app.config.get("MAX_BET",20000)); total=0; active=set(); bbs={}
    for b in bets:
        try: s=int(b["seat"]); wt=str(b["wager_type"]); amt=float(b["amount"])
        except Exception: return jsonify({"error":"Malformed bet"}),400
        if s not in (0,1,2) or not wt.startswith(f"seat{s}_") or amt<=0 or amt>max_bet or not registry.validate_wager(game,wt): return jsonify({"error":"Invalid bet"}),400
        total+=amt; active.add(s); bbs.setdefault(str(s),{})[wt]=amt
    if total>max_bet: return jsonify({"error":f"Total stake capped at {int(max_bet)} credits"}),400
    active=sorted(active); shoe=_pontoon_shoe() if game=="pontoon" else build_shoe(6)
    first={s:[shoe.pop()] for s in active}; up=shoe.pop()
    for s in active: first[s].append(shoe.pop())
    hole=shoe.pop(); hands={}
    for s in active:
        cards=first[s]; natural=is_blackjack(cards)
        status="blackjack" if natural else "playing"
        hands[str(s)]=[{"cards":cards,"status":status,"stake":_main_bet({"bets_by_seat":bbs},s),"paid_extra":0.0,
                       "free_marker":False,"from_split":False,"from_split_aces":False,"split_aces":False,
                       "doubled":False,"surrendered":False,"double_withdrawn":False,"immediate_paid":0.0}]
    insurance=(up["rank"]=="A")
    st={"game":game,"shoe":shoe,"dealer_up":up,"dealer_hole":hole,"dealer_cards":[up,hole],"active_seats":active,
        "bets_by_seat":bbs,"hands":hands,"seat_pos":0,"hand_pos":{str(s):0 for s in active},"free_markers":{str(s):0 for s in active},
        "initial_cards":{str(s):first[s] for s in active},"initial_total_wager":total,"extra_wager":0.0,
        "insurance_wagers":{str(s):0.0 for s in active},"insurance_decisions":{str(s):False for s in active},"insurance_pos":0,
        "decision_phase":"insurance" if insurance else "play","immediate_return":0.0}
    immediate=0.0
    if game=="pontoon":
        for s in active:
            h=st["hands"][str(s)][0]
            if is_blackjack(h["cards"]):
                val=_main_bet(st,s)*2.5; h["immediate_paid"]=val; h["status"]="paid21"; immediate+=val
    resp=_visible(st); resp["total_wager"]=total; resp["immediate_return"]=immediate
    return jsonify(resp)

@solo_bp.route("/blackjack/action",methods=["POST"])
def bj_action():
    data=request.get_json(silent=True) or {}; action=str(data.get("action","")).lower()
    allowed=("hit","stand","double","split","surrender","insurance","decline_insurance","even_money","withdraw_double","keep_double")
    if action not in allowed: return jsonify({"error":"Invalid action"}),400
    try: st=_dec(data.get("state_token",""))
    except Exception: return jsonify({"error":"Invalid state token"}),400
    s,hi=_current(st)
    if s is None: return jsonify({"error":"Round already complete"}),400
    if int(data.get("seat",-1))!=s: return jsonify({"error":"It is another seat's turn"}),400
    extra=0.0; immediate=0.0
    if st.get("decision_phase")=="insurance":
        h=st["hands"][str(s)][0]; base=_main_bet(st,s)
        if action=="insurance":
            amt=base/2
            if amt<=0: return jsonify({"error":"Insurance requires a main wager"}),400
            st["insurance_wagers"][str(s)]=amt; st["extra_wager"]+=amt; extra=amt
        elif action=="even_money":
            if not is_blackjack(h["cards"]): return jsonify({"error":"Even money is only available on a natural Blackjack/Pontoon"}),400
            immediate=base*2; h["immediate_paid"]+=immediate; h["status"]="paid_even_money"
        elif action!="decline_insurance":
            return jsonify({"error":"Resolve Insurance / Even Money first"}),400
        st["insurance_decisions"][str(s)]=True; st["insurance_pos"]+=1
    else:
        hs=st["hands"][str(s)]; h=hs[hi]
        if h.get("awaiting_double_withdraw"):
            if action=="withdraw_double":
                immediate=float(h.get("paid_extra",0)); h["immediate_paid"]+=immediate; h["double_withdrawn"]=True
                h["awaiting_double_withdraw"]=False; h["status"]="double_withdrawn"
            elif action=="keep_double":
                h["awaiting_double_withdraw"]=False; h["status"]="stood"
            else: return jsonify({"error":"Choose Keep Double or Withdraw Double"}),400
        elif action=="hit":
            if h["status"]!="playing": return jsonify({"error":"Hand is not playable"}),400
            h["cards"].append(st["shoe"].pop()); h["status"]=_hand_status(st["game"],h)
        elif action=="stand": h["status"]="stood"
        elif action=="surrender":
            if not _can_surrender(st,h): return jsonify({"error":"Surrender is not available on this hand"}),400
            h["surrendered"]=True; h["status"]="surrendered"
        elif action=="double":
            if not _eligible_double(st["game"],h): return jsonify({"error":"Cannot double on this hand"}),400
            free=_free_double(st["game"],h)
            if free:
                h["free_marker"]=True; st["free_markers"][str(s)]+=1
            else:
                extra=_main_bet(st,s); h["paid_extra"]+=extra; st["extra_wager"]+=extra
            if st["game"]=="pontoon" and any(c["rank"]=="A" for c in h["cards"][:2]): h["pontoon_double_ace"]=True
            h["cards"].append(st["shoe"].pop()); h["doubled"]=True
            if _bust(st["game"],h): h["status"]="bust"
            elif st["game"]=="pontoon" and not free and _total(st["game"],h)<21:
                h["awaiting_double_withdraw"]=True; h["status"]="playing"
            else: h["status"]="stood"
        elif action=="split":
            if not _eligible_split(st,s,h): return jsonify({"error":"Cannot split this hand"}),400
            free=_free_split(st["game"],h); c1,c2=h["cards"]; aces=c1["rank"]=="A"
            if not free: extra=_main_bet(st,s); st["extra_wager"]+=extra
            h1={"cards":[c1,st["shoe"].pop()],"status":"playing","stake":h["stake"],"paid_extra":0.0,"free_marker":h.get("free_marker",False),
                "from_split":True,"from_split_aces":aces,"split_aces":aces,"doubled":False,"surrendered":False,"double_withdrawn":False,"immediate_paid":0.0}
            h2={"cards":[c2,st["shoe"].pop()],"status":"playing","stake":0.0 if free else _main_bet(st,s),"paid_extra":0.0,"free_marker":free,
                "from_split":True,"from_split_aces":aces,"split_aces":aces,"doubled":False,"surrendered":False,"double_withdrawn":False,"immediate_paid":0.0}
            if free: st["free_markers"][str(s)]+=1
            h1["status"]=_hand_status(st["game"],h1); h2["status"]=_hand_status(st["game"],h2)
            hs[hi:hi+1]=[h1,h2]
        else: return jsonify({"error":"That action is not available now"}),400
    if st["game"]=="pontoon" and st.get("decision_phase")!="insurance":
        hs=st["hands"][str(s)]
        for hh in hs:
            if hh.get("immediate_paid",0) or hh.get("doubled") or hh.get("surrendered") or hh.get("double_withdrawn"): continue
            if _total("pontoon",hh)==21 and not _bust("pontoon",hh):
                stake=Decimal(str(hh.get("stake",0)))
                if is_blackjack(hh["cards"]) and not hh.get("from_split"): mult=Decimal("1.5")
                else:
                    import game.pontoon as pm
                    combo=pm._special_combo(hh["cards"])[0]; mult=pm._COMBO_PAYS.get(combo,Decimal("1")) if combo else Decimal("1")
                val=float(stake+stake*mult); hh["immediate_paid"]=val; immediate+=val; hh["status"]="paid21"
    resp=_visible(st); resp.update({"seat":s,"hand_index":hi,"extra_stake":extra,"immediate_return":immediate})
    return jsonify(resp)

def _pontoon_combo(cards):
    import game.pontoon as m
    return m._special_combo(cards)[0]

def _main_result(game,h,dealer):
    if h.get("double_withdrawn"): return "double_withdrawn"
    if h.get("surrendered"): return "surrender"
    if h.get("immediate_paid"): return "paid"
    cards=h["cards"]; pb=is_blackjack(cards) and not h.get("from_split"); db=is_blackjack(dealer)
    if _bust(game,h): return "lose"
    if game=="pontoon" and _total(game,h)==21: return "win"
    if pb and db: return "push"
    if pb: return "blackjack"
    if db: return "lose"
    dt=hand_total(dealer)
    if dt>21:
        if game=="blackjack_freebet" and dt==22: return "push"
        return "win"
    pt=_total(game,h)
    return "win" if pt>dt else "lose" if pt<dt else "push"

def _normal_hand_return(game,h,result,base,dealer_bj=False):
    stake=Decimal(str(h.get("stake",0))); paid=Decimal(str(h.get("paid_extra",0))); b=Decimal(str(base))
    if h.get("immediate_paid"): return Decimal("0")
    if result=="double_withdrawn": return Decimal("0")
    if result=="surrender":
        if game=="pontoon" and dealer_bj: return Decimal("0")
        return stake*Decimal("0.5")
    if result=="lose": return Decimal("0")
    if result=="push": return stake+paid
    if result in ("blackjack","pontoon"):
        mult=Decimal("1.2") if game=="blackjack_kingsbounty" else Decimal("1.5")
        return stake+stake*mult
    ret=(stake+paid)*Decimal("2")
    if h.get("free_marker"): ret += b
    if game=="pontoon" and not h.get("doubled"):
        combo=_pontoon_combo(h["cards"])
        if combo:
            import game.pontoon as pm
            mult=pm._COMBO_PAYS.get(combo)
            if mult is not None: ret=stake+stake*mult
    return ret

@solo_bp.route("/blackjack/settle",methods=["POST"])
def bj_settle():
    try: st=_dec((request.get_json(silent=True) or {}).get("state_token",""))
    except Exception: return jsonify({"error":"Invalid state token"}),400
    cur,_=_current(st)
    if cur is not None: return jsonify({"error":"Player decisions are not complete"}),400
    game=st["game"]; dealer=st["dealer_cards"]; shoe=st["shoe"]
    needs_dealer=any(any(not h.get("immediate_paid") and not h.get("double_withdrawn") and not (h.get("surrendered") and game!="pontoon") and not _bust(game,h) for h in st["hands"][str(s)]) for s in st["active_seats"])
    if needs_dealer:
        if game in ("blackjack_freebet","pontoon"):
            while hand_total(dealer)<17 or (hand_total(dealer)==17 and is_soft(dealer)): dealer.append(shoe.pop())
        else: complete_dealer_hand(dealer,shoe,soft17_stands=True)
    dealer_bj=is_blackjack(dealer); mod=registry.get_module(game); seats={}; results=[]; tr=Decimal("0")
    for s in st["active_seats"]:
        iw=Decimal(str(st["insurance_wagers"].get(str(s),0)))
        if iw:
            hole=st["dealer_hole"]["rank"]
            won=(hole in ("J","Q","K")) if game=="pontoon" else (hole in ("10","J","Q","K"))
            rr=iw*Decimal("3") if won else Decimal("0"); tr+=rr
            results.append({"wager_type":f"seat{s}_insurance","seat":s,"amount":float(iw),"return":float(rr),"win":won})
    for s in st["active_seats"]:
        base=_main_bet(st,s); handouts=[]; seat_ret=Decimal("0"); hs=st["hands"][str(s)]
        cap_loss=dealer_bj and any(h.get("from_split") or h.get("doubled") for h in hs)
        if cap_loss:
            paid_extras=sum(Decimal(str(h.get("paid_extra",0))) for h in hs)
            split_extras=sum(Decimal(str(h.get("stake",0))) for h in hs[1:])
            seat_ret += paid_extras+split_extras; tr += paid_extras+split_extras
        for h in hs:
            res=_main_result(game,h,dealer)
            if cap_loss and res=="lose": rr=Decimal("0")
            else: rr=_normal_hand_return(game,h,res,base,dealer_bj)
            tr+=rr; seat_ret+=rr
            handouts.append({"cards":h["cards"],"total":_total(game,h),"bust":_bust(game,h),"result":res,
                             "doubled":bool(h.get("doubled")),"free_marker":bool(h.get("free_marker")),
                             "surrendered":bool(h.get("surrendered")),"double_withdrawn":bool(h.get("double_withdrawn")),
                             "immediate_paid":float(h.get("immediate_paid",0))})
        init=st["initial_cards"][str(s)]; first=handouts[0]
        sd={"hands":handouts,"cards":first["cards"],"total":first["total"],"bust":first["bust"],"result":first["result"],
            "blackjack":first["result"]=="blackjack","pontoon":game=="pontoon" and is_blackjack(init),"pair":is_pair(init),"free_markers":st["free_markers"][str(s)]}
        if game=="blackjack_lucky8":
            import game.blackjack_lucky8 as m; sd["lucky8"]=m._lucky8_result(init,st["dealer_up"])
        elif game=="blackjack_kingsbounty":
            import game.blackjack_kingsbounty as m
            sd["kingsbounty"]=m._kings_bounty_result(init,st["dealer_up"],dealer); sd["bettheset"]=m._bet_the_set_result(init); sd["royalmatch"]=m._royal_match_result(init)
        elif game=="pontoon": sd["combo"]=_pontoon_combo(first["cards"])
        seats[s]=sd
        if base>0:
            stake_total=base+sum(float(h.get("stake",0)) for h in hs[1:])+sum(float(h.get("paid_extra",0)) for h in hs)
            results.append({"wager_type":f"seat{s}_main","seat":s,"amount":stake_total,"return":float(seat_ret),"win":float(seat_ret)>stake_total})
    outcome={"game":game,"dealer_up":st["dealer_up"],"dealer_cards":dealer,"dealer_total":hand_total(dealer),
             "dealer_blackjack":dealer_bj,"dealer_pontoon":dealer_bj if game=="pontoon" else False,"dealer_bust":is_bust(dealer),
             "dealer_bust_cards":len(dealer) if is_bust(dealer) else 0,"seats":seats,"active_seats":st["active_seats"]}
    for s in st["active_seats"]:
        for wt,amt in st["bets_by_seat"].get(str(s),{}).items():
            if wt.endswith("_main"): continue
            ret=mod.payout(wt,Decimal(str(amt)),outcome); tr+=ret
            results.append({"wager_type":wt,"seat":s,"amount":amt,"return":float(ret),"win":float(ret)>amt})
    if game == "pontoon":
        super_bonus_winners = []
        for s in st["active_seats"]:
            hs = st["hands"][str(s)]
            if not hs:
                continue
            h = hs[0]
            cards = h.get("cards", [])
            qualifies = (
                len(cards) >= 3
                and cards[0]["rank"] == "7"
                and cards[1]["rank"] == "7"
                and cards[2]["rank"] == "7"
                and cards[0]["suit"] == cards[1]["suit"] == cards[2]["suit"]
                and st["dealer_up"]["rank"] == "7"
                and not h.get("from_split")
                and not h.get("doubled")
            )
            if qualifies:
                super_bonus_winners.append(s)

        if super_bonus_winners:
            for s in super_bonus_winners:
                base = Decimal(str(_main_bet(st, s)))
                if base >= Decimal("100"):
                    bonus = Decimal("5000")
                elif base >= Decimal("10"):
                    bonus = Decimal("1000")
                else:
                    bonus = Decimal("0")
                if bonus > 0:
                    tr += bonus
                    results.append({
                        "wager_type": f"seat{s}_super_bonus",
                        "seat": s,
                        "amount": 0,
                        "return": float(bonus),
                        "win": True,
                    })

            for s in st["active_seats"]:
                if s in super_bonus_winners:
                    continue
                base = Decimal(str(_main_bet(st, s)))
                if base <= 0:
                    continue
                tr += Decimal("50")
                results.append({
                    "wager_type": f"seat{s}_super_bonus_50",
                    "seat": s,
                    "amount": 0,
                    "return": 50.0,
                    "win": True,
                })
    tw=float(st["initial_total_wager"])+float(st["extra_wager"])
    immediate_total=sum(float(h.get("immediate_paid",0)) for s in st["active_seats"] for h in st["hands"][str(s)])
    return jsonify({"game":game,"outcome":outcome,"total_wager":tw,"extra_wager":float(st["extra_wager"]),
                    "immediate_return":immediate_total,"total_return":float(tr),"net":float(tr)+immediate_total-tw,"results":results})
