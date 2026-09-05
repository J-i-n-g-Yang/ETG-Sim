"""
Pontoon (MBS) — Version 6, w.e.f. 27 September 2019.

Key differences from standard blackjack:
  - 4–8 decks with four 10s REMOVED per deck (48 cards per deck)
  - Pontoon = Ace + 10-point card (same as Blackjack but named differently)
  - Insurance wins only on J/Q/K (not 10, since 10s are removed)
  - 5-card 21 pays 3:2; 6-card 21 pays 2:1; 7+ card 21 pays 3:1
  - Special combos: 6-7-8 / 7-7-7 with suit-based pay
  - Super Bonus: player 7-7-7 same suit + dealer up-card is any 7
  - Dealer draws to Hard 16 / Soft 17 (stands on hard 17)
  - Surrender only when dealer shows A/K/Q/J
  - Pair wager: 11:1

Wager types:
  seat0_main .. seat2_main
  seat0_pair .. seat2_pair
"""

from decimal import Decimal
import random

SUITS = ["S", "H", "D", "C"]
RANKS_PONTOON = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "J", "Q", "K"]  # no 10s

NUM_DECKS = 6

WAGER_TYPES = [
    "seat0_main", "seat1_main", "seat2_main",
    "seat0_pair", "seat1_pair", "seat2_pair",
]

_SEAT_IDX = {"seat0": 0, "seat1": 1, "seat2": 2}

_SUPER_BONUS_FLAT = {
    (10, 99): 1000,
    (100, 10**9): 5000,
}


def _build_pontoon_shoe(num_decks: int = 6) -> list:
    deck = [{"rank": r, "suit": s} for s in SUITS for r in RANKS_PONTOON] * num_decks
    random.shuffle(deck)
    return deck


def _card_value(rank: str) -> int:
    if rank == "A":
        return 11
    if rank in ("J", "Q", "K"):
        return 10
    return int(rank)


def _hand_total(cards: list) -> int:
    total = sum(_card_value(c["rank"]) for c in cards)
    aces = sum(1 for c in cards if c["rank"] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total



def doubled_hand_total(cards: list) -> int:
    """Rule 3.4.2: Aces in the initial two cards count as 1 when doubled."""
    total = 0
    flexible_aces = 0
    for i, c in enumerate(cards):
        if c["rank"] == "A":
            if i < 2:
                total += 1
            else:
                total += 11
                flexible_aces += 1
        else:
            total += _card_value(c["rank"])
    while total > 21 and flexible_aces:
        total -= 10
        flexible_aces -= 1
    return total


def _is_pontoon(cards: list) -> bool:
    return (
        len(cards) == 2
        and _hand_total(cards) == 21
        and any(c["rank"] == "A" for c in cards)
        and any(c["rank"] in ("J", "Q", "K") for c in cards)
    )


def _is_pair(cards: list) -> bool:
    if len(cards) < 2:
        return False
    r1, r2 = cards[0]["rank"], cards[1]["rank"]
    if r1 in ("J", "Q", "K") and r2 in ("J", "Q", "K"):
        return r1 == r2
    return _card_value(r1) == _card_value(r2)


def _special_combo(cards: list):
    """
    Check for 5-card 21, 6-card 21, 7+-card 21, 6-7-8, 7-7-7.
    Returns (category, suit_detail) or (None, None).
    """
    total = _hand_total(cards)
    n = len(cards)
    ranks = sorted(c["rank"] for c in cards)
    suits = [c["suit"] for c in cards]

    # 6-7-8 combo (3 cards)
    if n == 3 and sorted(ranks) == ["6", "7", "8"]:
        if len(set(suits)) == 1:
            cat = "678_all_spades" if suits[0] == "S" else "678_same_suit"
        else:
            cat = "678_mixed"
        return cat, suits

    # 7-7-7 combo (3 cards)
    if n == 3 and all(r == "7" for r in ranks):
        if len(set(suits)) == 1:
            cat = "777_all_spades" if suits[0] == "S" else "777_same_suit"
        else:
            cat = "777_mixed"
        return cat, suits

    # Multi-card 21
    if total == 21:
        if n == 5:
            return "5_card_21", suits
        if n == 6:
            return "6_card_21", suits
        if n >= 7:
            return "7plus_card_21", suits

    return None, None


_COMBO_PAYS = {
    "678_all_spades":  Decimal("3"),
    "777_all_spades":  Decimal("3"),
    "678_same_suit":   Decimal("2"),
    "777_same_suit":   Decimal("2"),
    "678_mixed":       Decimal("1.5"),
    "777_mixed":       Decimal("1.5"),
    "5_card_21":       Decimal("1.5"),
    "6_card_21":       Decimal("2"),
    "7plus_card_21":   Decimal("3"),
}


def _dealer_should_draw(cards):
    total = _hand_total(cards)
    aces = sum(1 for c in cards if c["rank"] == "A")
    raw = sum(_card_value(c["rank"]) for c in cards)
    actual_aces = aces
    t = raw
    while t > 21 and actual_aces:
        t -= 10
        actual_aces -= 1
    soft = actual_aces > 0 and t <= 21
    # Draw to hard 16 or soft 17; stand on hard 17
    if t < 17:
        return True
    if t == 17 and soft:
        return True
    return False


def resolve(active_seats=None) -> dict:
    if active_seats is None:
        active_seats = [0, 1, 2]

    shoe = _build_pontoon_shoe(NUM_DECKS)

    seat_cards = {}
    for s in active_seats:
        seat_cards[s] = [shoe.pop()]
    dealer_up = shoe.pop()
    for s in active_seats:
        seat_cards[s].append(shoe.pop())
    dealer_hole = shoe.pop()
    dealer_cards = [dealer_up, dealer_hole]

    while _dealer_should_draw(dealer_cards):
        dealer_cards.append(shoe.pop())

    dealer_pontoon = _is_pontoon(dealer_cards)
    dealer_total = _hand_total(dealer_cards)
    dealer_bust = dealer_total > 21

    seats_out = {}
    for s in active_seats:
        cards = list(seat_cards[s])
        # Simple: draw to hard 16
        while _hand_total(cards) < 17 and not _is_pontoon(cards):
            cards.append(shoe.pop())

        p_pontoon = _is_pontoon(cards)
        p_total = _hand_total(cards)
        p_bust = p_total > 21

        combo, _ = _special_combo(cards)

        if p_bust:
            result = "lose"
        elif dealer_pontoon and not p_pontoon and p_total != 21:
            result = "lose"
        elif p_pontoon and dealer_pontoon:
            result = "push"
        elif p_pontoon or p_total == 21:
            result = "win"   # paid immediately per rule 3.29
        elif dealer_bust:
            result = "win"
        elif p_total > dealer_total:
            result = "win"
        elif p_total < dealer_total:
            result = "lose"
        else:
            result = "push"

        # Super Bonus check: player 7-7-7 same suit + dealer up is any 7
        super_bonus = (
            len(cards) == 3
            and all(c["rank"] == "7" for c in cards)
            and len({c["suit"] for c in cards}) == 1
            and dealer_up["rank"] == "7"
        )

        seats_out[s] = {
            "cards":       [{"rank": c["rank"], "suit": c["suit"]} for c in cards],
            "total":       p_total,
            "pontoon":     p_pontoon,
            "bust":        p_bust,
            "result":      result,
            "pair":        _is_pair(seat_cards[s][:2]),
            "combo":       combo,
            "super_bonus": super_bonus,
        }

    return {
        "game":           "pontoon",
        "dealer_up":      {"rank": dealer_up["rank"], "suit": dealer_up["suit"]},
        "dealer_cards":   [{"rank": c["rank"], "suit": c["suit"]} for c in dealer_cards],
        "dealer_total":   dealer_total,
        "dealer_pontoon": dealer_pontoon,
        "dealer_bust":    dealer_bust,
        "seats":          seats_out,
        "active_seats":   active_seats,
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

    if bet_kind == "main":
        result = seat["result"]
        if result == "lose":
            return Decimal("0")
        if result == "push":
            return amount

        combo = seat.get("combo")
        if seat.get("super_bonus"):
            # Rule 4.1.1: $10-$99 pays a $1,000 Super Bonus; $100+ pays $5,000.
            # It is paid in addition to the normal 7-7-7 all-Spades/suited payout.
            combo = seat.get("combo")
            mult = _COMBO_PAYS.get(combo, Decimal("1"))
            base_return = amount + amount * mult
            bonus = Decimal("5000") if amount >= Decimal("100") else (
                Decimal("1000") if amount >= Decimal("10") else Decimal("0")
            )
            return base_return + bonus

        if combo and combo in _COMBO_PAYS:
            mult = _COMBO_PAYS[combo]
            return amount + amount * mult

        if seat.get("pontoon"):
            return amount + amount * Decimal("1.5")

        return amount + amount * Decimal("1")

    return Decimal("0")
