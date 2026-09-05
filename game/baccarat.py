"""
Baccarat — Immortal Dragon Tiger Baccarat (MBS rules, w.e.f. 28 July 2025).

Wagers: player, banker, tie, dragon_tiger, big_dragon, small_dragon,
        big_tiger, small_tiger, tiger_tie, immortal_dragon.
"""

import random
from decimal import Decimal

SUITS = ["S", "H", "D", "C"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

WAGER_TYPES = [
    "player", "banker", "tie",
    "dragon_tiger",
    "big_dragon", "small_dragon",
    "big_tiger", "small_tiger",
    "tiger_tie",
    "immortal_dragon",
]


def _card_value(rank: str) -> int:
    if rank == "A":
        return 1
    if rank in ("10", "J", "Q", "K"):
        return 0
    return int(rank)


def _hand_total(cards: list) -> int:
    return sum(c["value"] for c in cards) % 10


def _banker_draws(b_total: int, p3_value) -> bool:
    """Standard baccarat third-card rule for Banker."""
    if p3_value is None:
        # Player stood (6 or 7) — Banker draws on 0-5
        return b_total <= 5
    if b_total <= 2:
        return True
    if b_total == 3:
        return p3_value != 8
    if b_total == 4:
        return p3_value in (2, 3, 4, 5, 6, 7)
    if b_total == 5:
        return p3_value in (4, 5, 6, 7)
    if b_total == 6:
        return p3_value in (6, 7)
    return False


def resolve() -> dict:
    """Deal a full Immortal Dragon Tiger Baccarat hand and return the outcome dict."""
    deck = [{"rank": r, "suit": s, "value": _card_value(r)}
            for s in SUITS for r in RANKS] * 8
    random.shuffle(deck)

    # Deal one card at a time in the traditional order: Player, Banker,
    # Player, Banker — so the recorded "deal order" (and any animation built
    # from it) matches how a live table actually deals.
    p_cards = [deck.pop()]
    b_cards = [deck.pop()]
    p_cards.append(deck.pop())
    b_cards.append(deck.pop())

    p_total = _hand_total(p_cards)
    b_total = _hand_total(b_cards)

    p3_value = None
    natural = p_total >= 8 or b_total >= 8

    if not natural:
        if p_total <= 5:
            # Player's third card
            p3 = deck.pop()
            p_cards.append(p3)
            p3_value = p3["value"]

        p_total = _hand_total(p_cards)
        b_total = _hand_total(b_cards)

        if _banker_draws(b_total, p3_value):
            # Banker's third card — dealt only after Player's third is resolved
            b_cards.append(deck.pop())
            b_total = _hand_total(b_cards)

    if p_total > b_total:
        winner = "player"
    elif b_total > p_total:
        winner = "banker"
    else:
        winner = "tie"

    return {
        "winner":              winner,
        "player_total":        p_total,
        "banker_total":        b_total,
        "player_cards_count":  len(p_cards),
        "banker_cards_count":  len(b_cards),
        "total_cards":         len(p_cards) + len(b_cards),
        "player_cards":        [{"rank": c["rank"], "suit": c["suit"]} for c in p_cards],
        "banker_cards":        [{"rank": c["rank"], "suit": c["suit"]} for c in b_cards],
        "natural":             natural,
    }


def payout(wager_type: str, amount: Decimal, outcome: dict, choice=None) -> Decimal:
    """
    Return total credited to player (stake + win) if they win, else Decimal('0').
    Push returns the stake only.
    """
    amount   = Decimal(str(amount))
    winner   = outcome["winner"]
    p_total  = outcome["player_total"]
    b_total  = outcome["banker_total"]
    p_count  = outcome["player_cards_count"]
    b_count  = outcome["banker_cards_count"]

    # — TIE wager —
    if wager_type == "tie":
        if winner == "tie":
            return amount + amount * Decimal("8")
        return Decimal("0")

    # — TIGER TIE — wins only on tie with point total 6
    if wager_type == "tiger_tie":
        if winner == "tie" and p_total == 6:
            return amount + amount * Decimal("35")
        return Decimal("0")

    # — PLAYER wager —
    if wager_type == "player":
        if winner == "tie":
            return amount  # push
        if winner == "player":
            if p_total == 7:
                # Player wins with 7 — half pay (1 to 2)
                return amount + amount * Decimal("0.5")
            return amount + amount * Decimal("1")
        # Banker wins — check Push rule 3.14.2
        if p_total == 7 and b_total in (8, 9):
            return amount  # push
        return Decimal("0")

    # — BANKER wager — Half pay on 6
    if wager_type == "banker":
        if winner == "tie":
            return amount  # push
        if winner == "banker":
            if b_total == 6:
                return amount + amount * Decimal("0.5")
            return amount + amount * Decimal("1")
        return Decimal("0")

    # — DRAGON TIGER — Player wins 7 over Banker 6
    if wager_type == "dragon_tiger":
        if winner == "player" and p_total == 7 and b_total == 6:
            if p_count == 3 and b_count == 3:
                return amount + amount * Decimal("100")
            elif p_count == 2 and b_count == 2:
                return amount + amount * Decimal("30")
            else:
                # one hand 3 cards, other 2 cards
                return amount + amount * Decimal("40")
        return Decimal("0")

    # — BIG DRAGON — Player wins with 7, three cards
    if wager_type == "big_dragon":
        if winner == "player" and p_total == 7 and p_count == 3:
            return amount + amount * Decimal("30")
        return Decimal("0")

    # — SMALL DRAGON — Player wins with 7, two cards
    if wager_type == "small_dragon":
        if winner == "player" and p_total == 7 and p_count == 2:
            return amount + amount * Decimal("15")
        return Decimal("0")

    # — BIG TIGER — Banker wins with 6, three cards
    if wager_type == "big_tiger":
        if winner == "banker" and b_total == 6 and b_count == 3:
            return amount + amount * Decimal("50")
        return Decimal("0")

    # — SMALL TIGER — Banker wins with 6, two cards
    if wager_type == "small_tiger":
        if winner == "banker" and b_total == 6 and b_count == 2:
            return amount + amount * Decimal("22")
        return Decimal("0")

    # — IMMORTAL DRAGON — Player hand loses with point total 7
    if wager_type == "immortal_dragon":
        if winner == "banker" and p_total == 7:
            return amount + amount * Decimal("25")
        return Decimal("0")

    # Unknown wager type — treat as loss
    return Decimal("0")
