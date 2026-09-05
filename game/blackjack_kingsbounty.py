"""
King's Bounty Blackjack (MBS) — Version 1, w.e.f. 17 January 2025.

Key differences:
  - Blackjack pays 6:5 (not 3:2)
  - King's Bounty side bet (based on player's first 2 cards + dealer up)
  - Bet the Set 21 side bet (pair pays 15:1 suited / 10:1 unsuited)
  - Royal Match 21 side bet (KQ suited = 25:1, any suited = 5:2)
  - 2–8 decks, dealer stands on 17

Wager types:
  seat0_main .. seat2_main
  seat0_kingsbounty .. seat2_kingsbounty
  seat0_bettheset .. seat2_bettheset
  seat0_royalmatch .. seat2_royalmatch
"""

from decimal import Decimal
from .blackjack_base import (
    build_shoe, is_blackjack, is_bust, hand_total, is_pair,
    complete_dealer_hand, seat_result, card_point_value,
)

NUM_DECKS = 6

WAGER_TYPES = [
    "seat0_main",        "seat1_main",        "seat2_main",
    "seat0_kingsbounty", "seat1_kingsbounty", "seat2_kingsbounty",
    "seat0_bettheset",   "seat1_bettheset",   "seat2_bettheset",
    "seat0_royalmatch",  "seat1_royalmatch",  "seat2_royalmatch",
]

_SEAT_IDX = {"seat0": 0, "seat1": 1, "seat2": 2}


def _kings_bounty_result(p_cards: list, dealer_up: dict, dealer_cards: list):
    """
    Evaluate King's Bounty wager. Returns category or None.
    Only highest paying combination paid (Rule 1.1.9.3.1).
    """
    c1, c2 = p_cards[0], p_cards[1]
    d_bj = is_blackjack(dealer_cards)

    # 2 Kings of Spades + Dealer Blackjack (1000:1)
    if c1["rank"] == "K" and c1["suit"] == "S" and \
       c2["rank"] == "K" and c2["suit"] == "S" and d_bj:
        return "2_kings_spades_dealer_bj"

    # 2 Kings of Spades (100:1)
    if c1["rank"] == "K" and c1["suit"] == "S" and \
       c2["rank"] == "K" and c2["suit"] == "S":
        return "2_kings_spades"

    # 2 Suited Kings (other than spades) (30:1)
    if c1["rank"] == "K" and c2["rank"] == "K" and c1["suit"] == c2["suit"]:
        return "2_suited_kings"

    # 2 Suited Q/J/10 (20:1)
    if c1["rank"] in ("Q", "J", "10") and c2["rank"] in ("Q", "J", "10") and \
       c1["rank"] == c2["rank"] and c1["suit"] == c2["suit"]:
        return "2_suited_QJ10"

    # Suited 20 (9:1) — same suit, total 20, not counted above
    total = card_point_value(c1["rank"]) + card_point_value(c2["rank"])
    if total == 20 and c1["suit"] == c2["suit"]:
        return "suited_20"

    # 2 Kings (any suit) (6:1)
    if c1["rank"] == "K" and c2["rank"] == "K":
        return "2_kings"

    # Unsuited 20 (4:1)
    if total == 20:
        return "unsuited_20"

    return None


_KB_PAYS = {
    "2_kings_spades_dealer_bj": Decimal("1000"),
    "2_kings_spades":           Decimal("100"),
    "2_suited_kings":           Decimal("30"),
    "2_suited_QJ10":            Decimal("20"),
    "suited_20":                Decimal("9"),
    "2_kings":                  Decimal("6"),
    "unsuited_20":              Decimal("4"),
}


def _bet_the_set_result(p_cards: list):
    """Pair: same point value or same face card."""
    c1, c2 = p_cards[0], p_cards[1]
    if not is_pair(p_cards):
        return None
    return "suited_pair" if c1["suit"] == c2["suit"] else "unsuited_pair"


def _royal_match_result(p_cards: list):
    c1, c2 = p_cards[0], p_cards[1]
    same_suit = c1["suit"] == c2["suit"]
    if not same_suit:
        return None
    # Royal Match 21: K + Q same suit
    ranks = {c1["rank"], c2["rank"]}
    if ranks == {"K", "Q"}:
        return "royal_match"
    return "suited"



def _auto_play(cards: list, shoe: list) -> list:
    """Legacy resolve policy: hit below 17, stand on 17+.

    Interactive choices (split/double/surrender/insurance) are handled by
    api/solo.py. This resolver must not settle untouched two-card hands.
    """
    cards = list(cards)
    while hand_total(cards) < 17 and not is_blackjack(cards):
        cards.append(shoe.pop())
    return cards


def resolve(active_seats=None) -> dict:
    if active_seats is None:
        active_seats = [0, 1, 2]

    shoe = build_shoe(NUM_DECKS)

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
            "cards":        [{"rank": c["rank"], "suit": c["suit"]} for c in cards],
            "total":        hand_total(cards),
            "blackjack":    is_blackjack(cards),
            "bust":         is_bust(cards),
            "result":       result,
            "kingsbounty":  _kings_bounty_result(initial_cards[s], dealer_up, dealer_cards),
            "bettheset":    _bet_the_set_result(initial_cards[s]),
            "royalmatch":   _royal_match_result(initial_cards[s]),
        }

    return {
        "game":             "blackjack_kingsbounty",
        "dealer_up":        {"rank": dealer_up["rank"], "suit": dealer_up["suit"]},
        "dealer_cards":     [{"rank": c["rank"], "suit": c["suit"]} for c in dealer_cards],
        "dealer_total":     hand_total(dealer_cards),
        "dealer_blackjack": is_blackjack(dealer_cards),
        "seats":            seats_out,
        "active_seats":     active_seats,
    }


def payout(wager_type: str, amount: Decimal, outcome: dict, choice=None) -> Decimal:
    amount = Decimal(str(amount))
    seat_key = wager_type[:5]
    bet_kind = wager_type[6:]
    seat_idx = _SEAT_IDX.get(seat_key)
    if seat_idx is None:
        return Decimal("0")

    seats = outcome.get("seats", {})
    if seat_idx not in seats:
        return Decimal("0")
    seat = seats[seat_idx]

    if bet_kind == "kingsbounty":
        cat = seat.get("kingsbounty")
        if cat and cat in _KB_PAYS:
            return amount + amount * _KB_PAYS[cat]
        return Decimal("0")

    if bet_kind == "bettheset":
        cat = seat.get("bettheset")
        if cat == "suited_pair":
            return amount + amount * Decimal("15")
        if cat == "unsuited_pair":
            return amount + amount * Decimal("10")
        return Decimal("0")

    if bet_kind == "royalmatch":
        cat = seat.get("royalmatch")
        if cat == "royal_match":
            return amount + amount * Decimal("25")
        if cat == "suited":
            return amount + amount * Decimal("2.5")
        return Decimal("0")

    if bet_kind == "main":
        result = seat["result"]
        if result == "blackjack":
            return amount + amount * Decimal("1.2")   # 6:5
        if result == "win":
            return amount + amount * Decimal("1")
        if result == "push":
            return amount
        return Decimal("0")

    return Decimal("0")
