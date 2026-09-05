"""Stateful Solo Poker engine for the six house-banked MBS poker games.

Pass 1 covers the five non-Pai-Gow games. Progressive Jackpot wagering is
intentionally unavailable in Solo until a real jackpot pool/system is modeled.
The MBS rules expressly permit play without Progressive when that system is
unavailable.

Fortune Pai Gow remains on the previous implementation until Pass 2.
"""
import base64
import json
from decimal import Decimal
from itertools import combinations

from .poker_base import *
from . import poker_mississippi_stud as mississippi
from . import poker_singapore_stud as singapore
from . import poker_texas_holdem_bonus as texas_bonus
from . import poker_three_card_xtreme as three_card
from . import poker_ultimate_texas as ultimate
from . import poker_fortune_pai_gow as pai_gow
from . import paigow_engine

RULES = {
    m.GAME_ID: m
    for m in (
        mississippi,
        singapore,
        texas_bonus,
        three_card,
        ultimate,
        pai_gow,
    )
}

GAMES = tuple(RULES)
NAMES = {k: m.NAME for k, m in RULES.items()}
ICONS = {k: m.ICON for k, m in RULES.items()}

PROGRESSIVE_ENABLED = False

SIDE_WAGERS = {
    "poker_three_card_xtreme": {"pair_plus", "six_card_bonus"},
    "poker_singapore_stud": set(),
    "poker_texas_bonus": {"bonus"},
    "poker_ultimate_texas": {"trips"},
    # Three Card Bonus is held for a follow-up because the uploaded PDF's
    # settlement table is image-only in the available extraction.
    "poker_mississippi": set(),
    "poker_fortune_pai_gow": {"fortune_bonus"},
}


def enc(state):
    return base64.b64encode(
        json.dumps(state, separators=(",", ":")).encode()
    ).decode()


def dec(token):
    return json.loads(base64.b64decode(token.encode()).decode())


def allowed_initial_wagers(game, seat):
    allowed = {f"seat{seat}_ante"}

    if game == "poker_ultimate_texas":
        allowed.add(f"seat{seat}_blind")

    for side in SIDE_WAGERS.get(game, set()):
        allowed.add(f"seat{seat}_{side}")

    return allowed


def _new_hand(cards, ante, blind=False, side=None):
    return {
        "cards": cards,
        "ante": ante,
        "blind_mode": blind,
        "side": side or {},
        "folded": False,
        "actions": [],
        "extra": 0.0,
    }


def _is_royal(rank):
    return rank[0] == 8 and rank[1] == 14


def _to_one(amount, odds):
    a = Decimal(str(amount))
    return a * (Decimal("1") + Decimal(str(odds)))


def _side_result(results, seat, wager_type, amount, ret):
    a = Decimal(str(amount))
    r = Decimal(str(ret))
    results.append(
        {
            "seat": seat,
            "wager_type": wager_type,
            "amount": float(a),
            "return": float(r),
            "win": r > a,
        }
    )
    return r


def _singapore_bet_odds(rank):
    if rank[0] == 8:
        return 250 if _is_royal(rank) else 50
    return {
        7: 20,
        6: 7,
        5: 5,
        4: 4,
        3: 3,
        2: 2,
        1: 1,
        0: 1,
    }[rank[0]]


def _six_card_odds(rank):
    if rank[0] == 8:
        return 500 if _is_royal(rank) else 100
    return {
        7: 50,
        6: 20,
        5: 15,
        4: 10,
        3: 7,
    }.get(rank[0])


def _ultimate_blind_odds(rank):
    if rank[0] == 8:
        return 500 if _is_royal(rank) else 50
    return {
        7: 10,
        6: 3,
        5: 1.5,
        4: 1,
    }.get(rank[0])


def _ultimate_trips_odds(rank):
    if rank[0] == 8:
        return 100 if _is_royal(rank) else 40
    return {
        7: 30,
        6: 8,
        5: 7,
        4: 4,
        3: 3,
    }.get(rank[0])


def _texas_bonus_category(player_cards, dealer_cards):
    p = sorted(player_cards, key=lambda c: RV[c["rank"]], reverse=True)
    d = sorted(dealer_cards, key=lambda c: RV[c["rank"]], reverse=True)

    p_ranks = [c["rank"] for c in p]
    d_ranks = [c["rank"] for c in d]
    suited = p[0]["suit"] == p[1]["suit"]

    if p_ranks == ["A", "A"]:
        if d_ranks == ["A", "A"]:
            return "AA_both"
        return "AA_player"

    ranks = set(p_ranks)

    if ranks == {"A", "K"}:
        return "AK_suited" if suited else "AK_unsuited"

    if ranks in ({"A", "Q"}, {"A", "J"}):
        return "AQ_AJ_suited" if suited else "AQ_AJ_unsuited"

    if p_ranks[0] == p_ranks[1] and p_ranks[0] in ("K", "Q", "J"):
        return "KK_QQ_JJ"

    if p_ranks[0] == p_ranks[1] and p_ranks[0] in (
        "10", "9", "8", "7", "6", "5", "4", "3", "2"
    ):
        return "TT_22"

    return None


def deal(game, bets):
    if game not in GAMES:
        raise ValueError("Unknown poker game")

    active = sorted(
        {
            int(b["seat"])
            for b in bets
            if int(b["seat"]) in (0, 1, 2)
        }
    )

    if not active:
        raise ValueError("No active seats")

    by = {str(s): {} for s in active}

    for b in bets:
        seat = int(b["seat"])
        wager_type = str(b["wager_type"])
        amount = float(b["amount"])
        by[str(seat)][wager_type] = amount

    deck = build_deck(joker=(game == "poker_fortune_pai_gow"))
    hands = {}

    if game == "poker_fortune_pai_gow":
        for s in active:
            ante = by[str(s)].get(f"seat{s}_ante", 0)
            hands[str(s)] = _new_hand(
                [deck.pop() for _ in range(7)],
                ante,
                s != 0,
                by[str(s)],
            )
        dealer = [deck.pop() for _ in range(7)]
        community = []

    elif game == "poker_singapore_stud":
        for s in active:
            ante = by[str(s)].get(f"seat{s}_ante", 0)
            hands[str(s)] = _new_hand(
                [deck.pop() for _ in range(5)],
                ante,
                s != 0,
                by[str(s)],
            )
        dealer = [deck.pop() for _ in range(5)]
        community = []

    elif game == "poker_three_card_xtreme":
        for s in active:
            ante = by[str(s)].get(f"seat{s}_ante", 0)
            hands[str(s)] = _new_hand(
                [deck.pop() for _ in range(3)],
                ante,
                s != 0,
                by[str(s)],
            )
            # Pair Plus / Six Card Bonus may be played without Ante.
            if ante <= 0:
                hands[str(s)]["done"] = True

        dealer = [deck.pop() for _ in range(3)]
        community = [deck.pop(), deck.pop()]

    else:
        for s in active:
            ante = by[str(s)].get(f"seat{s}_ante", 0)
            hands[str(s)] = _new_hand(
                [deck.pop(), deck.pop()],
                ante,
                s != 0,
                by[str(s)],
            )

        if game in ("poker_texas_bonus", "poker_ultimate_texas"):
            dealer = [deck.pop(), deck.pop()]
            community = [deck.pop() for _ in range(5)]
        else:
            dealer = []
            community = [deck.pop() for _ in range(3)]

    state = {
        "game": game,
        "deck": deck,
        "hands": hands,
        "dealer": dealer,
        "community": community,
        "active": active,
        "bets": by,
        "seat_pos": 0,
        "stage": "set" if game == "poker_fortune_pai_gow" else "initial",
        "revealed": 0,
        "extra": 0.0,
    }

    if (
        game == "poker_three_card_xtreme"
        and all(hands[str(s)].get("done") for s in active)
    ):
        state["stage"] = "settle"

    return state


def _current(state):
    while state["seat_pos"] < len(state["active"]):
        seat = state["active"][state["seat_pos"]]
        hand = state["hands"][str(seat)]

        if hand["folded"] or hand.get("done"):
            state["seat_pos"] += 1
            continue

        return seat, hand

    return None, None


def _blind_action(game, stage):
    actions = RULES[game].legal_actions(stage, blind=True)
    return actions[0] if actions else "houseway"


def visible(state):
    seat, hand = _current(state)
    game = state["game"]
    stage = state["stage"]
    seats = {}

    for s in state["active"]:
        h = state["hands"][str(s)]
        show = (s == 0) or stage == "settle"

        seats[str(s)] = {
            "cards": h["cards"] if show else [],
            "card_count": len(h["cards"]),
            "blind_mode": h["blind_mode"],
            "folded": h["folded"],
            "done": bool(h.get("done")),
            "actions": h["actions"],
        }

        if game == "poker_fortune_pai_gow":
            seats[str(s)]["manual_set_allowed"] = (
                s == 0
                and not h["blind_mode"]
                and stage == "set"
                and not h.get("done")
            )
            if h.get("low"):
                seats[str(s)]["low"] = h["low"]
            if h.get("high"):
                seats[str(s)]["high"] = h["high"]
            if h.get("foul"):
                seats[str(s)]["foul"] = True

        if h.get("result"):
            seats[str(s)]["result"] = h["result"]

    dealer_visible = []

    if game == "poker_singapore_stud" and state["dealer"]:
        dealer_visible = [state["dealer"][-1]]

    community = state["community"][: state["revealed"]]
    actions = []

    if seat is not None:
        if game == "poker_fortune_pai_gow":
            actions = ["houseway"] if hand["blind_mode"] else ["set_hand", "houseway"]
        elif game == "poker_ultimate_texas" and hand.get("play_made"):
            actions = []
        else:
            actions = list(
                RULES[game].legal_actions(
                    stage,
                    blind=hand["blind_mode"],
                )
            )

    return {
        "state_token": enc(state),
        "game": game,
        "stage": stage,
        "active_seats": state["active"],
        "current_seat": seat,
        "seats": seats,
        "dealer_cards": dealer_visible,
        "community": community,
        "actions": actions,
        "all_done": seat is None,
    }


def action(state, seat, act, low_indices=None):
    current_seat, hand = _current(state)

    if current_seat is None or current_seat != seat:
        raise ValueError("It is another seat's turn")

    if hand["blind_mode"]:
        act = _blind_action(state["game"], state["stage"])

    game = state["game"]
    ante = hand["ante"]
    extra = 0.0

    legal = set(RULES[game].legal_actions(state["stage"], blind=hand["blind_mode"]))

    if game != "poker_fortune_pai_gow" and act not in legal:
        raise ValueError("Invalid action")

    if act == "fold":
        hand["folded"] = True
        hand["done"] = True

    elif game == "poker_mississippi" and act in ("bet1", "bet2", "bet3"):
        mult = int(act[-1])
        extra = ante * mult
        hand["extra"] += extra
        hand["actions"].append((state["stage"], act))
        state["extra"] += extra
        hand["done"] = True

    elif game in ("poker_singapore_stud", "poker_three_card_xtreme") and act == "play":
        mult = 2 if game == "poker_singapore_stud" else 1
        extra = ante * mult
        hand["extra"] += extra
        state["extra"] += extra
        hand["actions"].append((state["stage"], act))
        hand["done"] = True

    elif game == "poker_texas_bonus":
        if state["stage"] == "initial" and act == "flop":
            extra = ante * 2
            hand["extra"] += extra
            state["extra"] += extra
            hand["actions"].append(("flop", "bet"))
            hand["done"] = True

        elif state["stage"] in ("flop", "turn") and act in ("check", "turn", "river"):
            if act != "check":
                extra = ante
                hand["extra"] += extra
                state["extra"] += extra

            hand["actions"].append((state["stage"], act))
            hand["done"] = True

        else:
            raise ValueError("Invalid action")

    elif game == "poker_ultimate_texas":
        if hand.get("play_made"):
            raise ValueError("Play wager has already been made on this hand")

        if act.startswith("play"):
            mult = int(act[-1])
            extra = ante * mult
            hand["extra"] += extra
            state["extra"] += extra
            hand["actions"].append((state["stage"], act))
            hand["done"] = True
            hand["play_made"] = True

        elif act == "check":
            hand["actions"].append((state["stage"], act))
            hand["done"] = True

        elif act == "fold":
            hand["folded"] = True
            hand["done"] = True

    elif game == "poker_fortune_pai_gow":
        if act == "houseway":
            low, high = paigow_engine.house_way(hand["cards"])
            hand["low"] = low
            hand["high"] = high
            hand["foul"] = False
            hand["manual_set"] = False
            hand["done"] = True
            hand["actions"].append(("set", "houseway"))

        elif act == "set_hand":
            if hand["blind_mode"]:
                raise ValueError("Blind Pai Gow hands must use House Way")
            paigow_engine.set_manual_hand(hand, low_indices)

        else:
            raise ValueError("Invalid action")

    else:
        raise ValueError("Invalid action")

    state["seat_pos"] += 1

    if state["seat_pos"] >= len(state["active"]):
        _next_stage(state)

    return extra


def _next_stage(state):
    game = state["game"]

    if game == "poker_mississippi":
        if state["stage"] == "initial":
            state["stage"] = "third"
            state["revealed"] = 1
        elif state["stage"] == "third":
            state["stage"] = "fourth"
            state["revealed"] = 2
        elif state["stage"] == "fourth":
            state["stage"] = "fifth"
            state["revealed"] = 3
        else:
            state["stage"] = "settle"

    elif game == "poker_texas_bonus":
        if state["stage"] == "initial":
            state["stage"] = "flop"
            state["revealed"] = 3
        elif state["stage"] == "flop":
            state["stage"] = "turn"
            state["revealed"] = 4
        elif state["stage"] == "turn":
            state["stage"] = "settle"
            state["revealed"] = 5

    elif game == "poker_ultimate_texas":
        if state["stage"] == "initial":
            state["stage"] = "flop"
            state["revealed"] = 3
        elif state["stage"] == "flop":
            state["stage"] = "river"
            state["revealed"] = 5
        else:
            state["stage"] = "settle"

    else:
        state["stage"] = "settle"

    state["seat_pos"] = 0

    for s in state["active"]:
        hand = state["hands"][str(s)]

        if hand["folded"]:
            hand["done"] = True
            continue

        if state["stage"] == "settle":
            hand["done"] = True
            continue

        if game == "poker_ultimate_texas" and hand.get("play_made"):
            hand["done"] = True
        else:
            hand.pop("done", None)

    if game == "poker_ultimate_texas" and state["stage"] != "settle":
        if all(
            state["hands"][str(s)].get("folded")
            or state["hands"][str(s)].get("play_made")
            for s in state["active"]
        ):
            state["stage"] = "settle"
            state["revealed"] = 5
            state["seat_pos"] = 0

            for s in state["active"]:
                state["hands"][str(s)]["done"] = True


def _settle_three_card_side_bets(state, seat, hand, results):
    total = Decimal("0")
    bets = state["bets"][str(seat)]

    pair_amount = Decimal(str(bets.get(f"seat{seat}_pair_plus", 0)))
    if pair_amount > 0:
        rank = rank3(hand["cards"])
        odds = three_card.PAIR_PLUS.get(rank[0])
        ret = _to_one(pair_amount, odds) if odds is not None else Decimal("0")
        total += _side_result(
            results,
            seat,
            f"seat{seat}_pair_plus",
            pair_amount,
            ret,
        )

    six_amount = Decimal(str(bets.get(f"seat{seat}_six_card_bonus", 0)))
    if six_amount > 0:
        rank, _ = best5(hand["cards"] + state["dealer"])
        odds = _six_card_odds(rank)
        ret = _to_one(six_amount, odds) if odds is not None else Decimal("0")
        total += _side_result(
            results,
            seat,
            f"seat{seat}_six_card_bonus",
            six_amount,
            ret,
        )

    return total


def _settle_texas_bonus_side(state, seat, hand, results):
    amount = Decimal(
        str(state["bets"][str(seat)].get(f"seat{seat}_bonus", 0))
    )

    if amount <= 0:
        return Decimal("0")

    if hand["folded"]:
        ret = Decimal("0")
    else:
        category = _texas_bonus_category(hand["cards"], state["dealer"])
        odds = texas_bonus.BONUS_PAY.get(category)
        ret = _to_one(amount, odds) if odds is not None else Decimal("0")

    return _side_result(
        results,
        seat,
        f"seat{seat}_bonus",
        amount,
        ret,
    )


def _settle_ultimate_trips(state, seat, hand, results):
    amount = Decimal(
        str(state["bets"][str(seat)].get(f"seat{seat}_trips", 0))
    )

    if amount <= 0:
        return Decimal("0")

    rank, _ = best5(hand["cards"] + state["community"])
    odds = _ultimate_trips_odds(rank)
    ret = _to_one(amount, odds) if odds is not None else Decimal("0")

    return _side_result(
        results,
        seat,
        f"seat{seat}_trips",
        amount,
        ret,
    )


def _settle_standard(state):
    game = state["game"]
    results = []
    total_return = Decimal("0")

    for seat in state["active"]:
        hand = state["hands"][str(seat)]
        ante = Decimal(str(hand["ante"]))
        extra = Decimal(str(hand["extra"]))
        ret = Decimal("0")

        if not hand["folded"] and ante > 0:
            if game == "poker_singapore_stud":
                player_rank = rank5(hand["cards"])
                dealer_rank = rank5(state["dealer"])
                dealer_qualifies = dealer_qualifies_singapore(state["dealer"])

                if not dealer_qualifies:
                    # Ante wins 1:1; Bet pushes.
                    ret = ante * 2 + extra

                elif player_rank > dealer_rank:
                    odds = _singapore_bet_odds(player_rank)
                    # Ante wins 1:1; Bet wins according to pay table.
                    ret = ante * 2 + extra * (Decimal("1") + Decimal(str(odds)))

                elif player_rank == dealer_rank:
                    ret = ante + extra

                hand["result"] = (
                    "win"
                    if ret > ante + extra
                    else "push"
                    if ret == ante + extra
                    else "lose"
                )

            elif game == "poker_three_card_xtreme":
                player_rank = rank3(hand["cards"])
                dealer_rank = rank3(state["dealer"])
                dealer_qualifies = dealer_qualifies_threecard(state["dealer"])

                if not dealer_qualifies:
                    # Ante wins 1:1; Play pushes.
                    ret = ante * 2 + extra

                elif player_rank > dealer_rank:
                    ret = (ante + extra) * 2

                elif player_rank == dealer_rank:
                    ret = ante + extra

                if player_rank[0] >= 3:
                    ret += ante * Decimal(
                        str(three_card.ANTE_BONUS[player_rank[0]])
                    )

                hand["result"] = (
                    "win"
                    if ret > ante + extra
                    else "push"
                    if ret == ante + extra
                    else "lose"
                )

            elif game == "poker_texas_bonus":
                player_rank, _ = best5(hand["cards"] + state["community"])
                dealer_rank, _ = best5(state["dealer"] + state["community"])

                if player_rank > dealer_rank:
                    # Flop / Turn / River all pay 1:1.
                    ret += extra * 2
                    # Ante wins only on Straight or better; otherwise pushes.
                    ret += ante * 2 if player_rank[0] >= 4 else ante
                    hand["result"] = "win"

                elif player_rank == dealer_rank:
                    ret = ante + extra
                    hand["result"] = "push"

                else:
                    hand["result"] = "lose"

            elif game == "poker_ultimate_texas":
                player_rank, _ = best5(hand["cards"] + state["community"])
                dealer_rank, _ = best5(state["dealer"] + state["community"])
                blind = Decimal(
                    str(
                        state["bets"][str(seat)].get(
                            f"seat{seat}_blind",
                            hand["ante"],
                        )
                    )
                )

                if player_rank > dealer_rank:
                    # Play always wins 1:1.
                    ret += extra * 2

                    # Ante wins only if Dealer qualifies with Pair+; otherwise push.
                    ret += ante * 2 if dealer_rank[0] >= 1 else ante

                    # Blind wins only on Straight+; otherwise push.
                    blind_odds = _ultimate_blind_odds(player_rank)
                    if blind_odds is None:
                        ret += blind
                    else:
                        ret += blind * (
                            Decimal("1") + Decimal(str(blind_odds))
                        )

                    hand["result"] = "win"

                elif player_rank == dealer_rank:
                    # Rule 3.10.8: neither hand wins.
                    ret = ante + blind + extra
                    hand["result"] = "push"

                else:
                    hand["result"] = "lose"

            elif game == "poker_mississippi":
                player_rank = rank5(hand["cards"] + state["community"])
                odds = mississippi.main_odds(player_rank)
                stake = ante + extra

                if odds == 0:
                    ret = stake
                    hand["result"] = "push"
                elif odds is not None:
                    ret = stake * (
                        Decimal("1") + Decimal(str(odds))
                    )
                    hand["result"] = "win"
                else:
                    hand["result"] = "lose"

        elif hand["folded"]:
            hand["result"] = "fold"

        main_amount = ante + extra

        if game == "poker_ultimate_texas":
            main_amount += Decimal(
                str(
                    state["bets"][str(seat)].get(
                        f"seat{seat}_blind",
                        0,
                    )
                )
            )

        if main_amount > 0:
            total_return += ret
            results.append(
                {
                    "seat": seat,
                    "wager_type": f"seat{seat}_main",
                    "amount": float(main_amount),
                    "return": float(ret),
                    "win": ret > main_amount,
                }
            )

        # Independent / variant-specific initial side wagers.
        if game == "poker_three_card_xtreme":
            side_ret = _settle_three_card_side_bets(
                state, seat, hand, results
            )
            total_return += side_ret

        elif game == "poker_texas_bonus":
            side_ret = _settle_texas_bonus_side(
                state, seat, hand, results
            )
            total_return += side_ret

        elif game == "poker_ultimate_texas":
            side_ret = _settle_ultimate_trips(
                state, seat, hand, results
            )
            total_return += side_ret

    return results, total_return


def settle(state):
    if state["game"] == "poker_fortune_pai_gow":
        return paigow_engine.settle(state)

    results, total_return = _settle_standard(state)

    return {
        "outcome": {
            "game": state["game"],
            "dealer_cards": state["dealer"],
            "community": state["community"],
            "seats": state["hands"],
            "progressive_available": PROGRESSIVE_ENABLED,
        },
        "results": results,
        "total_return": float(total_return),
        "extra_wager": state["extra"],
    }
