"""
blackjack_base.py — shared card/deck/hand logic for all 4 MBS blackjack variants.

Deck model
----------
Each deck is 52 standard cards (no jokers). Multiple decks are shuffled together.
Cards are represented as {"rank": "A"|"2"…"9"|"10"|"J"|"Q"|"K", "suit": "S"|"H"|"D"|"C"}.

Seat model
----------
Three player seats (0, 1, 2) + one dealer seat.
Only seats with a wager are dealt cards.
Dealer shows exactly 1 card face-up; hole card is hidden until reveal.
"""

import random
from decimal import Decimal

SUITS = ["S", "H", "D", "C"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
NUM_SEATS = 3


def build_shoe(num_decks: int = 6) -> list:
    deck = [{"rank": r, "suit": s} for s in SUITS for r in RANKS] * num_decks
    random.shuffle(deck)
    return deck


def card_point_value(rank: str) -> int:
    """Standard blackjack point value (Ace = 11 or 1 handled by hand_total)."""
    if rank == "A":
        return 11
    if rank in ("10", "J", "Q", "K"):
        return 10
    return int(rank)


def hand_total(cards: list) -> int:
    """Compute best total ≤ 21; reduce Aces as needed."""
    total = sum(card_point_value(c["rank"]) for c in cards)
    aces = sum(1 for c in cards if c["rank"] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_soft(cards: list) -> bool:
    """True if hand contains an Ace counted as 11."""
    total = sum(card_point_value(c["rank"]) for c in cards)
    aces = sum(1 for c in cards if c["rank"] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return aces > 0 and total <= 21


def is_blackjack(cards: list) -> bool:
    """Exactly 2 cards, total 21 (Ace + 10-value)."""
    return (
        len(cards) == 2
        and hand_total(cards) == 21
        and any(c["rank"] == "A" for c in cards)
        and any(c["rank"] in ("10", "J", "Q", "K") for c in cards)
    )


def is_bust(cards: list) -> bool:
    return hand_total(cards) > 21


def is_pair(cards: list) -> bool:
    """First two cards: same point value, or identical face cards."""
    if len(cards) < 2:
        return False
    r1, r2 = cards[0]["rank"], cards[1]["rank"]
    # Face cards: must be the same face card
    if r1 in ("J", "Q", "K") and r2 in ("J", "Q", "K"):
        return r1 == r2
    return card_point_value(r1) == card_point_value(r2)


def dealer_should_draw(dealer_cards: list, soft17_stands: bool = True) -> bool:
    """
    Standard MBS dealer rule:
      soft17_stands=True  → stand on soft 17 (most variants)
      soft17_stands=False → draw to soft 17 (Free Bet BJ)
    """
    total = hand_total(dealer_cards)
    soft = is_soft(dealer_cards)
    if total < 17:
        return True
    if total == 17 and soft and not soft17_stands:
        return True
    return False


def deal_initial(shoe: list, active_seats: list) -> dict:
    """
    Deal 2 cards to each active seat + 2 to dealer (1 face-up, 1 face-down).
    Returns state dict ready for resolution.
    """
    seats = {}
    for s in active_seats:
        seats[s] = [shoe.pop(), shoe.pop()]

    dealer_up = shoe.pop()
    dealer_hole = shoe.pop()

    return {
        "seats": seats,          # {seat_idx: [card, card]}
        "dealer_up": dealer_up,
        "dealer_hole": dealer_hole,
        "dealer_cards": [dealer_up, dealer_hole],  # full hand, revealed at end
    }


def complete_dealer_hand(dealer_cards: list, shoe: list, soft17_stands: bool = True) -> list:
    """Draw cards to dealer until rules say stop."""
    while dealer_should_draw(dealer_cards, soft17_stands):
        dealer_cards.append(shoe.pop())
    return dealer_cards


def seat_result(seat_cards: list, dealer_cards: list) -> str:
    """
    Return 'blackjack'|'win'|'lose'|'push' for a non-busted seat vs dealer.
    Caller must handle surrender / bust / special rules before calling this.
    """
    p_bj = is_blackjack(seat_cards)
    d_bj = is_blackjack(dealer_cards)

    if p_bj and d_bj:
        return "push"
    if p_bj:
        return "blackjack"
    if d_bj:
        return "lose"

    p_total = hand_total(seat_cards)
    d_total = hand_total(dealer_cards)

    if is_bust(seat_cards):
        return "lose"
    if is_bust(dealer_cards):
        return "win"
    if p_total > d_total:
        return "win"
    if p_total < d_total:
        return "lose"
    return "push"
