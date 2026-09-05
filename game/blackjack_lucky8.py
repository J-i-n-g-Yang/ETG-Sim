"""
Blackjack Lucky 8 (MBS) — Version 5, w.e.f. 27 September 2019.

Wager types:
  seat0_main, seat1_main, seat2_main       main wagers (3 seats)
  seat0_pair, seat1_pair, seat2_pair       pair side bets (11:1)
  seat0_lucky8, seat1_lucky8, seat2_lucky8 Lucky 8 side bets

Lucky 8 pay table (Rule 4.2):
  3 suited 8s      1000:1
  3 unsuited 8s     100:1
  2 suited 8s        10:1
  2 unsuited 8s       5:1
  Two of a Kind       3:1
"""

import random
from decimal import Decimal
from .blackjack_base import (
    build_shoe, is_blackjack, is_bust, hand_total, is_pair,
    complete_dealer_hand, seat_result, card_point_value,
)

NUM_DECKS = 6

WAGER_TYPES = [
    "seat0_main", "seat1_main", "seat2_main",
    "seat0_pair", "seat1_pair", "seat2_pair",
    "seat0_lucky8", "seat1_lucky8", "seat2_lucky8",
]

_SEAT_IDX = {"seat0": 0, "seat1": 1, "seat2": 2}


# --------------------------------------------------------------------------- #
# Lucky 8 evaluation                                                           #
# --------------------------------------------------------------------------- #

def _lucky8_result(p_cards: list, dealer_up: dict):
    """
    Evaluate Lucky 8 for one seat. Uses player's initial 2 cards and dealer up-card.
    Returns payout category name or None.
    """
    c1, c2, dc = p_cards[0], p_cards[1], dealer_up

    # --- 3-card combinations using p1, p2, dealer_up ---
    eights = [c for c in [c1, c2, dc] if c["rank"] == "8"]
    if len(eights) == 3:
        suits = {c["suit"] for c in eights}
        return "3_suited_8s" if len(suits) == 1 else "3_unsuited_8s"

    # --- 2-card combinations: check p1+p2, p1+dc, p2+dc ---
    for a, b in [(c1, c2), (c1, dc), (c2, dc)]:
        if a["rank"] == "8" and b["rank"] == "8":
            return "2_suited_8s" if a["suit"] == b["suit"] else "2_unsuited_8s"

    # --- Two of a Kind (same point value or same face card, excluding 8s) ---
    def is_two_of_a_kind(a, b):
        if a["rank"] == "8" or b["rank"] == "8":
            return False
        if a["rank"] in ("J", "Q", "K") and b["rank"] in ("J", "Q", "K"):
            return a["rank"] == b["rank"]
        return card_point_value(a["rank"]) == card_point_value(b["rank"])

    for a, b in [(c1, c2), (c1, dc), (c2, dc)]:
        if is_two_of_a_kind(a, b):
            return "two_of_a_kind"

    return None


_LUCKY8_PAYS = {
    "3_suited_8s":   Decimal("1000"),
    "3_unsuited_8s": Decimal("100"),
    "2_suited_8s":   Decimal("10"),
    "2_unsuited_8s": Decimal("5"),
    "two_of_a_kind": Decimal("3"),
}



def _auto_play(cards: list, shoe: list) -> list:
    """Legacy resolve policy: hit below 17, stand on 17+.

    Interactive choices (split/double/surrender/insurance) are handled by
    api/solo.py. This resolver must not settle untouched two-card hands.
    """
    cards = list(cards)
    while hand_total(cards) < 17 and not is_blackjack(cards):
        cards.append(shoe.pop())
    return cards

# --------------------------------------------------------------------------- #
# resolve()                                                                    #
# --------------------------------------------------------------------------- #

def resolve(active_seats=None) -> dict:
    """Simulate one round. active_seats defaults to all 3."""
    if active_seats is None:
        active_seats = [0, 1, 2]

    shoe = build_shoe(NUM_DECKS)

    # Deal: 1 card per seat (round 1), dealer up, 1 card per seat (round 2)
    seat_cards = {}
    for s in active_seats:
        seat_cards[s] = [shoe.pop()]
    dealer_up = shoe.pop()
    for s in active_seats:
        seat_cards[s].append(shoe.pop())
    dealer_hole = shoe.pop()

    initial_cards = {s: list(seat_cards[s]) for s in active_seats}
    for s in active_seats:
        seat_cards[s] = _auto_play(seat_cards[s], shoe)

    dealer_cards = [dealer_up, dealer_hole]
    dealer_cards = complete_dealer_hand(dealer_cards, shoe, soft17_stands=True)

    seats_out = {}
    for s in active_seats:
        cards = seat_cards[s]
        result = seat_result(cards, dealer_cards)
        seats_out[s] = {
            "cards":       [{"rank": c["rank"], "suit": c["suit"]} for c in cards],
            "total":       hand_total(cards),
            "blackjack":   is_blackjack(cards),
            "bust":        is_bust(cards),
            "result":      result,
            "pair":        is_pair(initial_cards[s]),
            "lucky8":      _lucky8_result(initial_cards[s], dealer_up),
        }

    return {
        "game":             "blackjack_lucky8",
        "dealer_up":        {"rank": dealer_up["rank"], "suit": dealer_up["suit"]},
        "dealer_cards":     [{"rank": c["rank"], "suit": c["suit"]} for c in dealer_cards],
        "dealer_total":     hand_total(dealer_cards),
        "dealer_blackjack": is_blackjack(dealer_cards),
        "seats":            seats_out,
        "active_seats":     active_seats,
    }


# --------------------------------------------------------------------------- #
# payout()                                                                     #
# --------------------------------------------------------------------------- #

def payout(wager_type: str, amount: Decimal, outcome: dict, choice=None) -> Decimal:
    amount = Decimal(str(amount))
    sep = wager_type.find("_", 5)   # skip "seat0" prefix
    if sep == -1:
        return Decimal("0")
    seat_key = wager_type[:5]       # "seat0"
    bet_kind = wager_type[6:]       # "main" / "pair" / "lucky8"
    seat_idx = _SEAT_IDX.get(seat_key)
    if seat_idx is None:
        return Decimal("0")

    seats = outcome.get("seats", {})
    if seat_idx not in seats:
        return Decimal("0")
    seat = seats[seat_idx]

    if bet_kind == "pair":
        return (amount + amount * Decimal("11")) if seat["pair"] else Decimal("0")

    if bet_kind == "lucky8":
        cat = seat.get("lucky8")
        if cat and cat in _LUCKY8_PAYS:
            return amount + amount * _LUCKY8_PAYS[cat]
        return Decimal("0")

    if bet_kind == "main":
        result = seat["result"]
        if result == "blackjack":
            return amount + amount * Decimal("1.5")
        if result == "win":
            return amount + amount * Decimal("1")
        if result == "push":
            return amount
        return Decimal("0")

    return Decimal("0")
