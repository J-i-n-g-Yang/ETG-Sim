"""
game/royal_three_pictures.py

Royal Three Pictures (MBS)
Version 2, effective 24 March 2020.

Rules engine only. API / frontend integration is handled separately.
"""
from collections import Counter
from decimal import Decimal
import random


GAME = "royal_three_pictures"
NAME = "Royal Three Pictures"
ICON = "👑"

SUITS = ("S", "H", "D", "C")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
PICTURE_RANKS = frozenset(("J", "Q", "K"))

WAGERS = frozenset(("main", "tie", "royal_pictures"))

ROYAL_PICTURES_PROFIT = {
    "three_kings": Decimal("188"),
    "three_queens": Decimal("128"),
    "three_jacks": Decimal("88"),
    "three_pictures": Decimal("18"),
    "any_picture_pair": Decimal("8"),
    "any_king": Decimal("1"),
}


def make_deck(shuffle=True):
    """Return one standard 52-card deck without jokers."""
    deck = [
        {"rank": rank, "suit": suit}
        for suit in SUITS
        for rank in RANKS
    ]
    if shuffle:
        random.shuffle(deck)
    return deck


def validate_wager(wager_type):
    return str(wager_type) in WAGERS


def card_value(card):
    """
    A=1, 2-9 face value, 10/J/Q/K=0.
    Only J/Q/K are Picture cards.
    """
    rank = str(card["rank"]).upper()

    if rank == "A":
        return 1
    if rank in ("10", "J", "Q", "K"):
        return 0
    if rank in ("2", "3", "4", "5", "6", "7", "8", "9"):
        return int(rank)

    raise ValueError(f"Invalid Royal Three Pictures rank: {rank}")


def is_picture(card):
    return str(card["rank"]).upper() in PICTURE_RANKS


def picture_count(cards):
    _require_three(cards)
    return sum(1 for card in cards if is_picture(card))


def point_total(cards):
    """Three-card point total: units digit of the summed card values."""
    _require_three(cards)
    return sum(card_value(card) for card in cards) % 10


def _require_three(cards):
    if not isinstance(cards, (list, tuple)) or len(cards) != 3:
        raise ValueError("Royal Three Pictures hands must contain exactly three cards")


def hand_rank(cards):
    """
    Return a comparable rank.

    Rules 3.20-3.22:
      - Three Pictures is highest.
      - Otherwise higher point total ranks higher.
      - At the same point total, more Picture cards rank higher.
      - Picture ranks and suits do not break ties.

    Tuple comparison therefore gives the required order:
        (point total, picture count)

    Three Pictures is represented separately so it ranks above every
    point-total hand.
    """
    _require_three(cards)

    pictures = picture_count(cards)
    points = point_total(cards)

    if pictures == 3:
        return (1, 0, 0)

    return (0, points, pictures)


def hand_name(cards):
    """Human-readable MBS hand-ranking label."""
    pictures = picture_count(cards)
    points = point_total(cards)

    if pictures == 3:
        return "Three Pictures"

    words = (
        "Zero", "One", "Two", "Three", "Four",
        "Five", "Six", "Seven", "Eight", "Nine",
    )
    point_word = words[points]

    if pictures == 2:
        return f"Double Picture {point_word}"
    if pictures == 1:
        return f"Single Picture {point_word}"
    return point_word


def compare_hands(player_cards, dealer_cards):
    """
    Return 'win', 'lose', or 'standoff'.

    A standoff requires identical hand rank: same point total and same
    number of Picture cards (or both Three Pictures).
    """
    player = hand_rank(player_cards)
    dealer = hand_rank(dealer_cards)

    if player > dealer:
        return "win"
    if player < dealer:
        return "lose"
    return "standoff"


def is_tie(player_cards, dealer_cards):
    """
    Tie wager is based ONLY on equal point totals.

    This is deliberately different from a Main-wager standoff.
    """
    return point_total(player_cards) == point_total(dealer_cards)


def royal_pictures_result(cards):
    """
    Return the Royal Pictures winning category, or None.

    Categories are mutually exclusive and checked from highest payout
    downward.
    """
    _require_three(cards)

    ranks = [str(card["rank"]).upper() for card in cards]
    counts = Counter(ranks)
    pictures = sum(rank in PICTURE_RANKS for rank in ranks)

    if counts["K"] == 3:
        return "three_kings"
    if counts["Q"] == 3:
        return "three_queens"
    if counts["J"] == 3:
        return "three_jacks"

    if pictures == 3:
        return "three_pictures"

    # One pair of Picture cards plus one Non-Picture card.
    if pictures == 2:
        for rank in PICTURE_RANKS:
            if counts[rank] == 2:
                return "any_picture_pair"

    # Exactly one King with either:
    # - two Non-Pictures; or
    # - one Q + one Non-Picture; or
    # - one J + one Non-Picture.
    if counts["K"] == 1:
        other = [rank for rank in ranks if rank != "K"]
        other_pictures = sum(rank in PICTURE_RANKS for rank in other)

        if other_pictures == 0:
            return "any_king"

        if other_pictures == 1 and any(
            rank not in PICTURE_RANKS for rank in other
        ):
            return "any_king"

    return None


def main_return(stake, player_cards, dealer_cards):
    """
    Total return (stake + profit).

    Player win on six points: 1:2.
    Other Player wins:        1:1.
    Standoff:                  stake returned.
    Loss:                      0.
    """
    stake = Decimal(str(stake))
    result = compare_hands(player_cards, dealer_cards)

    if result == "standoff":
        return stake
    if result == "lose":
        return Decimal("0")

    if point_total(player_cards) == 6:
        return stake * Decimal("1.5")

    return stake * Decimal("2")


def tie_return(stake, player_cards, dealer_cards):
    """Tie pays 8:1, so a winning total return is 9x stake."""
    stake = Decimal(str(stake))
    return stake * Decimal("9") if is_tie(player_cards, dealer_cards) else Decimal("0")


def royal_pictures_return(stake, cards):
    """Royal Pictures returns stake + the applicable listed profit."""
    stake = Decimal(str(stake))
    category = royal_pictures_result(cards)

    if category is None:
        return Decimal("0")

    return stake * (Decimal("1") + ROYAL_PICTURES_PROFIT[category])


def deal(active_seats=(0,)):
    """
    Deal three cards to each active position, then three to Dealer.

    This models the automated-device distribution at hand level.
    Blind/viewed presentation is a frontend/API concern.
    """
    seats = sorted(set(int(seat) for seat in active_seats))

    if not seats or any(seat not in (0, 1, 2) for seat in seats):
        raise ValueError("Active seats must be one or more of 0, 1 and 2")

    deck = make_deck()

    player_hands = {}
    for seat in seats:
        player_hands[seat] = [deck.pop() for _ in range(3)]

    dealer = [deck.pop() for _ in range(3)]

    return {
        "game": GAME,
        "active_seats": seats,
        "player_hands": player_hands,
        "dealer_cards": dealer,
    }


def settle_hand(player_cards, dealer_cards):
    """Convenient outcome description for later API integration."""
    result = compare_hands(player_cards, dealer_cards)
    return {
        "cards": player_cards,
        "point_total": point_total(player_cards),
        "picture_count": picture_count(player_cards),
        "hand_name": hand_name(player_cards),
        "result": result,
        "tie": is_tie(player_cards, dealer_cards),
        "royal_pictures": royal_pictures_result(player_cards),
    }
