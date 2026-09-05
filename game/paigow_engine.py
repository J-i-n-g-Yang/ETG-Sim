"""MBS Fortune Pai Gow Poker Version 4 engine.

Dedicated engine for:
- restricted Joker handling
- Pai Gow five-card / two-card ranking
- Appendix A House Way
- copy-hand settlement
- 5% commission on winning Standard wagers
- Fortune Bonus
- Envy Bonus

The viewed-hand manual-setting UI is intentionally a later frontend step.
Until then, all hands are set by the MBS House Way.
"""

from collections import Counter
from decimal import Decimal
from itertools import combinations, product

from .poker_base import RV

JOKER = "JOKER"

FORTUNE_PAYS = {
    "seven_card_straight_flush_no_joker": Decimal("2500"),
    "royal_match": Decimal("1000"),
    "seven_card_straight_flush_with_joker": Decimal("500"),
    "five_aces": Decimal("250"),
    "royal_flush": Decimal("100"),
    "straight_flush": Decimal("50"),
    "four_kind": Decimal("20"),
    "full_house": Decimal("5"),
    "flush": Decimal("4"),
    "three_kind": Decimal("3"),
    "straight": Decimal("2"),
}

ENVY_PAYS = {
    "seven_card_straight_flush_no_joker": Decimal("250"),
    "royal_match": Decimal("50"),
}

SUITS = ("S", "H", "D", "C")
RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")


def _value(card):
    return 14 if card["rank"] == JOKER else RV[card["rank"]]


def _sorted(cards, reverse=True):
    return sorted(cards, key=lambda c: (_value(c), c.get("suit", "")), reverse=reverse)


def _straight_high(values):
    vals = sorted(set(values), reverse=True)
    if 14 in vals:
        vals.append(1)
    for high in range(14, 4, -1):
        needed = {high - i for i in range(5)}
        if needed.issubset(set(vals)):
            return high
    return None


def _rank5_plain(cards):
    """Rank five non-Joker cards using Pai Gow categories.

    Tuple order:
      9 Five Aces
      8 Royal/Straight Flush
      7 Four Kind
      6 Full House
      5 Flush
      4 Straight
      3 Trips
      2 Two Pair
      1 Pair
      0 High Card
    """
    vals = sorted((RV[c["rank"]] for c in cards), reverse=True)
    counts = Counter(vals)
    groups = sorted(((n, v) for v, n in counts.items()), reverse=True)
    flush = len({c["suit"] for c in cards}) == 1
    sh = _straight_high(vals)

    if flush and sh:
        return (8, sh)

    if groups[0][0] == 4:
        quad = groups[0][1]
        kicker = max(v for v in vals if v != quad)
        return (7, quad, kicker)

    if sorted(counts.values()) == [2, 3]:
        trip = max(v for v, n in counts.items() if n == 3)
        pair = max(v for v, n in counts.items() if n == 2)
        return (6, trip, pair)

    if flush:
        return (5, *vals)

    if sh:
        return (4, sh)

    if groups[0][0] == 3:
        trip = groups[0][1]
        kickers = sorted((v for v in vals if v != trip), reverse=True)
        return (3, trip, *kickers)

    pairs = sorted((v for v, n in counts.items() if n == 2), reverse=True)
    if len(pairs) == 2:
        kicker = max(v for v in vals if v not in pairs)
        return (2, pairs[0], pairs[1], kicker)

    if len(pairs) == 1:
        pair = pairs[0]
        kickers = sorted((v for v in vals if v != pair), reverse=True)
        return (1, pair, *kickers)

    return (0, *vals)


def rank5(cards):
    """Pai Gow five-card rank with the restricted MBS Joker.

    Joker may complete Straight, Flush, Straight Flush or Royal Flush.
    Otherwise it is an Ace. Four Aces + Joker is Five Aces.
    """
    if len(cards) != 5:
        raise ValueError("Pai Gow High Hand must contain five cards")

    jokers = [c for c in cards if c["rank"] == JOKER]
    if not jokers:
        return _rank5_plain(cards)

    non = [c for c in cards if c["rank"] != JOKER]

    if len(jokers) != 1:
        raise ValueError("Fortune Pai Gow uses exactly one Joker")

    if sum(c["rank"] == "A" for c in non) == 4:
        return (9, 14)

    # Restricted wild: test every real card replacement, but only accept
    # straight/flush/straight-flush categories. Otherwise Joker is Ace.
    best_wild = None
    for rank, suit in product(RANKS, SUITS):
        candidate = non + [{"rank": rank, "suit": suit}]
        r = _rank5_plain(candidate)
        if r[0] in (4, 5, 8):
            if best_wild is None or r > best_wild:
                best_wild = r

    ace_card = {"rank": "A", "suit": jokers[0].get("suit", "X")}
    ace_rank = _rank5_plain(non + [ace_card])

    if best_wild is not None and best_wild > ace_rank:
        return best_wild
    return ace_rank


def rank2(cards):
    if len(cards) != 2:
        raise ValueError("Pai Gow Low Hand must contain two cards")
    vals = sorted((_value(c) for c in cards), reverse=True)
    if vals[0] == vals[1]:
        return (1, vals[0])
    return (0, vals[0], vals[1])


def _legal_split(low, high):
    # Five-card High Hand must be equal to or higher than Low Hand.
    # Any made 5-card poker hand (pair+) outranks a 2-card pair/high-card.
    hr = rank5(high)
    lr = rank2(low)
    if hr[0] >= 1:
        return True
    # Both are high-card structures: compare the high hand's top cards
    # against the two-card low hand lexicographically.
    return (0, hr[1], hr[2]) >= lr


def _split_from_low(cards, low_cards):
    remaining = list(cards)
    low = []
    for target in low_cards:
        for i, card in enumerate(remaining):
            if card is target or card == target:
                low.append(remaining.pop(i))
                break
        else:
            raise ValueError("Low-hand card not found")
    return low, remaining


def _rank_groups(cards):
    by = {}
    for c in cards:
        r = "A" if c["rank"] == JOKER else c["rank"]
        by.setdefault(r, []).append(c)
    return by


def _pair_ranks(cards):
    groups = _rank_groups(cards)
    return sorted(
        (RV[r] for r, cs in groups.items() if len(cs) >= 2),
        reverse=True,
    )


def _cards_of_value(cards, value, count=None):
    found = [c for c in cards if _value(c) == value]
    return found if count is None else found[:count]


def _highest_excluding(cards, excluded, count):
    pool = list(cards)
    for e in excluded:
        for i, c in enumerate(pool):
            if c is e or c == e:
                pool.pop(i)
                break
    return _sorted(pool)[:count]


def _best_preserved_made_hand_split(cards):
    """Appendix A straight/flush family helper.

    Find legal splits whose High Hand preserves a Straight, Flush,
    Straight Flush or Royal Flush, then maximize the Low Hand.
    """
    candidates = []
    for idxs in combinations(range(7), 2):
        low = [cards[i] for i in idxs]
        high = [cards[i] for i in range(7) if i not in idxs]
        hr = rank5(high)
        if hr[0] not in (4, 5, 8):
            continue
        if not _legal_split(low, high):
            continue
        candidates.append((rank2(low), hr, low, high))

    if not candidates:
        return None

    # House Way wording prioritizes the highest possible Low Hand while
    # preserving one of these made categories.
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2], candidates[0][3]


def house_way(cards):
    """Set seven cards according to Appendix A of MBS Fortune Pai Gow V4."""
    if len(cards) != 7:
        raise ValueError("Pai Gow hand must contain seven cards")

    cards = list(cards)
    groups = _rank_groups(cards)
    pair_values = sorted(
        (RV[r] for r, cs in groups.items() if len(cs) == 2),
        reverse=True,
    )
    trip_values = sorted(
        (RV[r] for r, cs in groups.items() if len(cs) == 3),
        reverse=True,
    )
    quad_values = sorted(
        (RV[r] for r, cs in groups.items() if len(cs) == 4),
        reverse=True,
    )

    # Five Aces: four natural Aces + Joker.
    natural_aces = [c for c in cards if c["rank"] == "A"]
    joker = next((c for c in cards if c["rank"] == JOKER), None)
    if len(natural_aces) == 4 and joker:
        kings = _cards_of_value(cards, 13, 2)
        low = kings if len(kings) == 2 else natural_aces[:2]
        return _split_from_low(cards, low)

    # Four of a kind rules.
    if quad_values:
        q = quad_values[0]
        quad = _cards_of_value(cards, q, 4)
        other_pairs = [v for v in pair_values if v != q]
        other_trips = [v for v in trip_values if v != q]

        if q == 14:
            kings = _cards_of_value(cards, 13, 2)
            if len(kings) == 2:
                return _split_from_low(cards, kings)
            return _split_from_low(cards, quad[:2])

        if other_pairs or other_trips:
            v = max(other_pairs + other_trips)
            return _split_from_low(cards, _cards_of_value(cards, v, 2))

        if 2 <= q <= 6:
            return _split_from_low(cards, _highest_excluding(cards, quad, 2))

        if 7 <= q <= 10:
            ace_or_joker = [c for c in cards if _value(c) == 14 and c not in quad]
            if ace_or_joker:
                low = [ace_or_joker[0]] + _highest_excluding(cards, quad + [ace_or_joker[0]], 1)
                return _split_from_low(cards, low)
            return _split_from_low(cards, quad[:2])

        # Jacks, Queens, Kings always split.
        return _split_from_low(cards, quad[:2])

    # Two trips: lowest trip remains in High; highest pair goes Low.
    if len(trip_values) >= 2:
        high_trip = trip_values[0]
        return _split_from_low(cards, _cards_of_value(cards, high_trip, 2))

    # Full-house structures before generic straight/flush handling.
    if trip_values and pair_values:
        trip = trip_values[0]
        pair = pair_values[0]

        # Three of a kind + two pairs -> highest pair Low.
        if len(pair_values) >= 2:
            return _split_from_low(cards, _cards_of_value(cards, pair_values[0], 2))

        # Three of a kind + pair of 2s + A,K -> keep Full House, A-K Low.
        if pair == 2:
            ace = _cards_of_value(cards, 14, 1)
            king = _cards_of_value(cards, 13, 1)
            if ace and king:
                return _split_from_low(cards, [ace[0], king[0]])

        # Ordinary full house -> pair Low.
        return _split_from_low(cards, _cards_of_value(cards, pair, 2))

    # Three pairs -> highest pair Low.
    if len(pair_values) >= 3:
        return _split_from_low(cards, _cards_of_value(cards, pair_values[0], 2))

    # Two-pair rules.
    if len(pair_values) == 2:
        high_pair, low_pair = pair_values
        high_group = 0 if high_pair <= 6 else 1 if high_pair <= 10 else 2
        low_group = 0 if low_pair <= 6 else 1 if low_pair <= 10 else 2

        # Medium+High, High+High, or Aces+anything: always split.
        if (
            (low_group == 1 and high_group == 2)
            or (low_group == 2 and high_group == 2)
            or high_pair == 14
        ):
            return _split_from_low(cards, _cards_of_value(cards, low_pair, 2))

        # Low+Low or Low+Medium: keep together with K/A/Joker.
        # Low+High or Medium+Medium: keep together with A/Joker.
        keep_threshold = 13 if (low_group == 0 and high_group <= 1) else 14
        outside = [
            c for c in cards
            if _value(c) not in (high_pair, low_pair)
        ]
        has_protector = any(_value(c) >= keep_threshold for c in outside)

        if has_protector:
            low = _sorted(outside)[:2]
            return _split_from_low(cards, low)

        return _split_from_low(cards, _cards_of_value(cards, low_pair, 2))

    # Straights / flushes / straight flushes / royal flushes.
    preserved = _best_preserved_made_hand_split(cards)
    if preserved is not None:
        # Appendix A says two-pair/three-pair/full-house/four-kind rules
        # supersede this section; those were handled above.
        if trip_values:
            # With trips plus a preservable straight/flush, play a pair of
            # the trips in Low Hand.
            return _split_from_low(cards, _cards_of_value(cards, trip_values[0], 2))
        return preserved

    # Three of a kind.
    if trip_values:
        trip = trip_values[0]
        trip_cards = _cards_of_value(cards, trip, 3)
        if trip == 14:
            # Trip Aces -> pair Aces High, Ace + next highest Low.
            low = [trip_cards[0]] + _highest_excluding(cards, trip_cards, 1)
            return _split_from_low(cards, low)
        return _split_from_low(cards, _highest_excluding(cards, trip_cards, 2))

    # One pair.
    if len(pair_values) == 1:
        pair = _cards_of_value(cards, pair_values[0], 2)
        return _split_from_low(cards, _highest_excluding(cards, pair, 2))

    # No pair: highest card High; second and third highest Low.
    ordered = _sorted(cards)
    return _split_from_low(cards, [ordered[1], ordered[2]])


def fortune_category(cards, low=None, high=None):
    """Return the highest Fortune Bonus category for the seven cards."""
    if len(cards) != 7:
        raise ValueError("Fortune Bonus evaluates seven cards")

    has_joker = any(c["rank"] == JOKER for c in cards)

    # Seven-card straight flush.
    suits = {c["suit"] for c in cards if c["rank"] != JOKER}
    for suit in SUITS:
        suited = [c for c in cards if c["rank"] == JOKER or c["suit"] == suit]
        if len(suited) == 7:
            vals = [RV[c["rank"]] for c in suited if c["rank"] != JOKER]
            needed_missing = 1 if has_joker else 0
            for high7 in range(14, 7, -1):
                seq = set(range(high7 - 6, high7 + 1))
                actual = set(vals)
                if 14 in actual and 1 in seq:
                    actual = actual | {1}
                missing = seq - actual
                if len(missing) <= needed_missing:
                    return (
                        "seven_card_straight_flush_with_joker"
                        if has_joker
                        else "seven_card_straight_flush_no_joker"
                    )

    # Royal Match depends on the actual setting.
    if low is not None and high is not None:
        if _is_royal_match(low, high):
            return "royal_match"

    if has_joker and sum(c["rank"] == "A" for c in cards) == 4:
        return "five_aces"

    best = None
    for combo in combinations(cards, 5):
        r = rank5(list(combo))
        if best is None or r > best:
            best = r

    if best[0] == 8:
        return "royal_flush" if best[1] == 14 else "straight_flush"
    if best[0] == 7:
        return "four_kind"
    if best[0] == 6:
        return "full_house"
    if best[0] == 5:
        return "flush"
    if best[0] == 3:
        return "three_kind"
    if best[0] == 4:
        return "straight"
    return None


def _is_royal_match(low, high):
    if len(low) != 2 or len(high) != 5:
        return False
    if any(c["rank"] == JOKER for c in low):
        return False
    if {c["rank"] for c in low} != {"K", "Q"}:
        return False
    if low[0]["suit"] != low[1]["suit"]:
        return False
    hr = rank5(high)
    return hr == (8, 14)



def set_manual_hand(hand, low_indices):
    """Set exactly two cards as the viewed Player's Low Hand.

    If the submitted setting is foul (Low Hand outranks High Hand), the
    hand is reset to House Way as required by the MBS procedure.
    Returns True for a valid manual setting and False for a foul reset.
    """
    cards = list(hand["cards"])

    if len(cards) != 7:
        raise ValueError("Pai Gow hand must contain seven cards")

    try:
        indices = [int(i) for i in low_indices]
    except (TypeError, ValueError):
        raise ValueError("Select exactly two cards for the Low Hand")

    if len(indices) != 2 or len(set(indices)) != 2:
        raise ValueError("Select exactly two different cards for the Low Hand")

    if any(i < 0 or i >= 7 for i in indices):
        raise ValueError("Invalid Pai Gow card selection")

    chosen = set(indices)
    low = [cards[i] for i in range(7) if i in chosen]
    high = [cards[i] for i in range(7) if i not in chosen]

    valid = _legal_split(low, high)

    if not valid:
        low, high = house_way(cards)

    hand["low"] = low
    hand["high"] = high
    hand["foul"] = not valid
    hand["manual_set"] = True
    hand["done"] = True
    hand.setdefault("actions", []).append(
        ("set", "manual" if valid else "houseway_foul")
    )

    return valid


def compare(player_low, player_high, dealer_low, dealer_high):
    """Return win/push/lose. Copy hands belong to Dealer."""
    ph = rank5(player_high)
    dh = rank5(dealer_high)
    pl = rank2(player_low)
    dl = rank2(dealer_low)

    high_win = ph > dh
    low_win = pl > dl

    if high_win and low_win:
        return "win"

    # Any copy is a Dealer win for that component, so two non-wins means loss.
    high_loss = ph <= dh
    low_loss = pl <= dl

    if high_loss and low_loss:
        return "lose"

    return "push"


def settle(state):
    dealer_low, dealer_high = house_way(state["dealer"])
    results = []
    total_return = Decimal("0")
    set_hands = {}

    # First set every Player hand so Fortune/Envy can inspect all hands.
    for seat in state["active"]:
        h = state["hands"][str(seat)]
        if h.get("low") and h.get("high") and not h.get("foul"):
            low, high = h["low"], h["high"]
            if not _legal_split(low, high):
                low, high = house_way(h["cards"])
                h["foul"] = True
        else:
            low, high = house_way(h["cards"])
        set_hands[seat] = (low, high)

    categories = {
        seat: fortune_category(
            state["hands"][str(seat)]["cards"],
            *set_hands[seat],
        )
        for seat in state["active"]
    }

    dealer_category = fortune_category(
        state["dealer"],
        dealer_low,
        dealer_high,
    )

    for seat in state["active"]:
        h = state["hands"][str(seat)]
        low, high = set_hands[seat]
        ante = Decimal(str(h["ante"]))
        result = compare(low, high, dealer_low, dealer_high)

        if result == "win":
            # 1:1 less 5% commission = original stake + 95% profit.
            main_return = ante + ante * Decimal("0.95")
        elif result == "push":
            main_return = ante
        else:
            main_return = Decimal("0")

        total_return += main_return
        h.update(
            {
                "low": low,
                "high": high,
                "result": result,
                "fortune_category": categories[seat],
            }
        )

        results.append(
            {
                "seat": seat,
                "wager_type": f"seat{seat}_main",
                "amount": float(ante),
                "return": float(main_return),
                "win": result == "win",
            }
        )

        fortune_amount = Decimal(
            str(
                state["bets"][str(seat)].get(
                    f"seat{seat}_fortune_bonus",
                    0,
                )
            )
        )

        if fortune_amount > 0:
            category = categories[seat]
            odds = FORTUNE_PAYS.get(category)
            fortune_return = (
                fortune_amount * (Decimal("1") + odds)
                if odds is not None
                else Decimal("0")
            )
            total_return += fortune_return
            results.append(
                {
                    "seat": seat,
                    "wager_type": f"seat{seat}_fortune_bonus",
                    "amount": float(fortune_amount),
                    "return": float(fortune_return),
                    "win": fortune_return > fortune_amount,
                    "category": category,
                }
            )

    # Envy Bonus: only seated Players who themselves wagered Fortune Bonus.
    # Dealer qualifying hands never trigger Envy.
    for receiver in state["active"]:
        fortune_amount = Decimal(
            str(
                state["bets"][str(receiver)].get(
                    f"seat{receiver}_fortune_bonus",
                    0,
                )
            )
        )
        if fortune_amount <= 0:
            continue

        receiver_category = categories[receiver]

        for source in state["active"]:
            if source == receiver:
                continue

            source_category = categories[source]
            envy = ENVY_PAYS.get(source_category)
            if envy is None:
                continue

            # Rule 3.24.2: a Player with 7-card SF cannot receive Envy.
            if receiver_category == "seven_card_straight_flush_no_joker":
                continue

            # Rule 3.24.3: Royal Match holder only receives Envy if another
            # Player has a 7-card straight flush without Joker.
            if (
                receiver_category == "royal_match"
                and source_category != "seven_card_straight_flush_no_joker"
            ):
                continue

            total_return += envy
            results.append(
                {
                    "seat": receiver,
                    "source_seat": source,
                    "wager_type": f"seat{receiver}_envy_bonus",
                    "amount": 0.0,
                    "return": float(envy),
                    "win": True,
                    "category": source_category,
                }
            )

    return {
        "outcome": {
            "game": state["game"],
            "dealer_cards": state["dealer"],
            "dealer_low": dealer_low,
            "dealer_high": dealer_high,
            "dealer_fortune_category": dealer_category,
            "seats": state["hands"],
        },
        "results": results,
        "total_return": float(total_return),
        "extra_wager": 0.0,
    }
