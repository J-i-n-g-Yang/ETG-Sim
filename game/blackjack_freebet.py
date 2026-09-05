"""
Free Bet Blackjack (MBS) — Version 4, w.e.f. 10 June 2026.

Key differences from standard blackjack:
  - Free Double on hard 9/10/11 (no extra wager)
  - Free Split on non-10-value pairs (no extra wager)
  - Dealer busts on 22 → all non-busted hands PUSH (stand-off), not win
  - Dealer draws to soft 17, stands on hard 17
  - Busted wager: wins when dealer busts (pays by number of dealer cards)
  - Pot of Gold wager: wins if player uses Free Bet Markers
  - Pair wager: 11:1

In solo simulation: seats play basic strategy auto-resolve; side bets
are evaluated post-deal.

Wager types:
  seat0_main .. seat2_main
  seat0_pair .. seat2_pair
  seat0_busted .. seat2_busted   (wins on any dealer bust)
  seat0_potofgold .. seat2_potofgold
"""

from decimal import Decimal
from .blackjack_base import (
    build_shoe, is_blackjack, is_bust, hand_total, is_pair,
    complete_dealer_hand, seat_result, is_soft, card_point_value,
)

NUM_DECKS = 6

WAGER_TYPES = [
    "seat0_main",      "seat1_main",      "seat2_main",
    "seat0_pair",      "seat1_pair",      "seat2_pair",
    "seat0_busted",    "seat1_busted",    "seat2_busted",
    "seat0_potofgold", "seat1_potofgold", "seat2_potofgold",
]

_SEAT_IDX = {"seat0": 0, "seat1": 1, "seat2": 2}

# Busted wager pay table (Rule 4.2) — by number of dealer cards when busted
_BUST_PAYS = {
    3: Decimal("1"),
    4: Decimal("2"),
    5: Decimal("6"),
    6: Decimal("50"),
}
_BUST_PAYS_7PLUS = Decimal("100")

# Pot of Gold (Rule 4.3) — by number of Free Bet Markers used
_POG_PAYS = {
    1: Decimal("3"),
    2: Decimal("10"),
    3: Decimal("25"),
    4: Decimal("50"),
}
_POG_PAYS_5PLUS = Decimal("100")


def _hand_total_freebet(cards):
    return hand_total(cards)


def _is_hard(cards, target):
    """True if hand total == target and is a hard total."""
    t = hand_total(cards)
    return t == target and not is_soft(cards)


def _auto_play_seat(cards: list, dealer_up: dict, shoe: list):
    """
    Very simple basic strategy for simulation:
    Free Double on hard 9/10/11, otherwise stand on 17+.
    Returns (final_cards, free_bet_markers_used).
    """
    markers = 0
    total = hand_total(cards)

    # Free double opportunity (hard 9, 10, or 11 only)
    if len(cards) == 2 and total in (9, 10, 11) and not is_soft(cards):
        cards.append(shoe.pop())
        markers += 1
        return cards, markers

    # Draw to 17
    while hand_total(cards) < 17:
        cards.append(shoe.pop())

    return cards, markers


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
    dealer_cards_raw = [dealer_up, dealer_hole]

    initial_cards = {s: list(seat_cards[s]) for s in active_seats}

    # Auto-play each seat
    seat_markers = {}
    for s in active_seats:
        cards, markers = _auto_play_seat(list(seat_cards[s]), dealer_up, shoe)
        seat_cards[s] = cards
        seat_markers[s] = markers

    # Dealer draws to soft 17, stands on hard 17
    dealer_cards = list(dealer_cards_raw)
    while True:
        t = hand_total(dealer_cards)
        soft = is_soft(dealer_cards)
        if t > 21:
            break
        if t > 17:
            break
        if t == 17 and not soft:
            break
        dealer_cards.append(shoe.pop())

    # hand_total already applies the blackjack Ace adjustment, so this is the
    # exact total used for both bust detection and the special dealer-22 push.
    actual_dealer_total = hand_total(dealer_cards)

    seats_out = {}
    for s in active_seats:
        cards = seat_cards[s]
        p_bj = is_blackjack(cards)
        p_bust = is_bust(cards)
        d_bj = is_blackjack(dealer_cards)
        d_bust_exact = actual_dealer_total > 21
        d_bust_val = actual_dealer_total if d_bust_exact else None

        # Result per Rule 4.4 / 4.5 / 4.7
        if p_bust:
            result = "lose"
        elif d_bj and not p_bj:
            result = "lose"
        elif p_bj and d_bj:
            result = "push"
        elif p_bj and d_bust_exact:
            result = "blackjack"   # Rule 4.4.4
        elif p_bj:
            result = "blackjack"
        elif d_bust_exact:
            # Rule 4.7.3: dealer busts on 22 → non-busted hands push
            # any other bust value → player wins
            if d_bust_val == 22:
                result = "push"
            else:
                result = "win"
        else:
            p_total = hand_total(cards)
            d_total = hand_total(dealer_cards)
            if p_total > d_total:
                result = "win"
            elif p_total < d_total:
                result = "lose"
            else:
                result = "push"

        seats_out[s] = {
            "cards":         [{"rank": c["rank"], "suit": c["suit"]} for c in cards],
            "total":         hand_total(cards),
            "blackjack":     p_bj,
            "bust":          p_bust,
            "result":        result,
            "pair":          is_pair(initial_cards[s]),
            "free_markers":  seat_markers.get(s, 0),
        }

    # Dealer bust stats for Busted wager
    d_bust_count = len(dealer_cards) if actual_dealer_total > 21 else 0

    return {
        "game":              "blackjack_freebet",
        "dealer_up":         {"rank": dealer_up["rank"], "suit": dealer_up["suit"]},
        "dealer_cards":      [{"rank": c["rank"], "suit": c["suit"]} for c in dealer_cards],
        "dealer_total":      hand_total(dealer_cards),
        "dealer_blackjack":  is_blackjack(dealer_cards),
        "dealer_bust":       actual_dealer_total > 21,
        "dealer_bust_cards": d_bust_count,
        "seats":             seats_out,
        "active_seats":      active_seats,
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

    if bet_kind == "pair":
        return (amount + amount * Decimal("11")) if seat["pair"] else Decimal("0")

    if bet_kind == "busted":
        n = outcome.get("dealer_bust_cards", 0)
        if n == 0:
            return Decimal("0")
        mult = _BUST_PAYS.get(n, _BUST_PAYS_7PLUS if n >= 7 else Decimal("50"))
        return amount + amount * mult

    if bet_kind == "potofgold":
        m = seat.get("free_markers", 0)
        if m == 0:
            return Decimal("0")
        mult = _POG_PAYS.get(m, _POG_PAYS_5PLUS if m >= 5 else Decimal("50"))
        return amount + amount * mult

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
