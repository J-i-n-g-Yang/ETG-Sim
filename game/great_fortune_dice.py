"""
Great Fortune Dice (MBS) — server-side math.

Four dice, values 1-6 each.

Supported wager types per game rules (14 July 2026):
    small, big
    all_small, all_big
    two_pair
    fourteen                       (total == 14)
    straight                       (1234, 2345, 3456)
    any_triple
    any_quadruple
    specific_triple_N   N=1..6
    specific_quadruple_N N=1..6
    specific_double_N   N=1..6    (2+ dice show N)
    total_N             N=5,6,7..23  (four-dice totals excl. 4, 14, 24)
    specific14_AB       encoded specific-14 group (see below)
    combo_AB            two-dice combination (any two of four dice)
    four_from_five_ABCDE  four dice from five possible numbers
"""

import random
from decimal import Decimal
from itertools import combinations

# ── wager type helpers ─────────────────────────────────────────────────────────
def _combo_keys():
    return [f"combo_{a}{b}" for a, b in combinations(range(1, 7), 2)]

def _specific14_keys():
    """
    PDF 4.1.2 specific-14 groups (sorted, joined):
    group A: 1256/1346/2345 → pays 15
    group B: 1355/1445/2246 → pays 30
    group C: 2336/1166/2255 → pays 45
    group D: 3344/2444/3335 → pays 80
    """
    return ["specific14_A", "specific14_B", "specific14_C", "specific14_D"]

def _four_from_five_keys():
    return [
        "four_from_five_12345",
        "four_from_five_12346",
        "four_from_five_12356",
        "four_from_five_12456",
        "four_from_five_13456",
        "four_from_five_23456",
    ]

WAGER_TYPES = (
    ["small", "big", "all_small", "all_big",
     "two_pair", "fourteen", "straight",
     "any_triple", "any_quadruple"]
    + [f"specific_triple_{n}"    for n in range(1, 7)]
    + [f"specific_quadruple_{n}" for n in range(1, 7)]
    + [f"specific_double_{n}"    for n in range(1, 7)]
    + [f"total_{n}"              for n in range(5, 24) if n != 14]
    + _specific14_keys()
    + _combo_keys()
    + _four_from_five_keys()
)

# ── resolve ────────────────────────────────────────────────────────────────────
def resolve() -> dict:
    dice = [random.randint(1, 6) for _ in range(4)]
    total = sum(dice)
    counts = {n: dice.count(n) for n in range(1, 7)}
    sorted_dice = sorted(dice)

    return {
        "dice":   dice,
        "total":  total,
        "counts": counts,
        "sorted": sorted_dice,
    }

# ── payout ─────────────────────────────────────────────────────────────────────
def payout(wager_type: str, amount: Decimal, outcome: dict, choice=None) -> Decimal:
    amount  = Decimal(str(amount))
    dice    = outcome["dice"]
    total   = outcome["total"]
    counts  = outcome["counts"]
    sorted_d = outcome["sorted"]

    def win(mult):
        return amount + amount * Decimal(str(mult))

    # ── Small (total 4-13) ────────────────────────────────────────────────────
    if wager_type == "small":
        # Wins on total 4-13; loses on any other total (14-24)
        # Note: 4 = 1+1+1+1, always all_small which also wins small
        return win(1) if 4 <= total <= 13 else Decimal("0")

    # ── Big (total 15-24) ─────────────────────────────────────────────────────
    if wager_type == "big":
        return win(1) if 15 <= total <= 24 else Decimal("0")

    # ── All Small (all dice are 1, 2, or 3) ───────────────────────────────────
    if wager_type == "all_small":
        return win(14) if all(d <= 3 for d in dice) else Decimal("0")

    # ── All Big (all dice are 4, 5, or 6) ─────────────────────────────────────
    if wager_type == "all_big":
        return win(14) if all(d >= 4 for d in dice) else Decimal("0")

    # ── Two Pair: two dice same value AND other two same different value,
    #    OR all four same ────────────────────────────────────────────────────
    if wager_type == "two_pair":
        pair_counts = [c for c in counts.values() if c >= 2]
        # all four same → quadruple counts as two pair too (per rules)
        if max(counts.values()) == 4:
            return win(11)
        # exactly two different pairs
        if sorted(c for c in counts.values() if c > 0) == [2, 2]:
            return win(11)
        return Decimal("0")

    # ── Fourteen (total == 14) ────────────────────────────────────────────────
    if wager_type == "fourteen":
        return win(7) if total == 14 else Decimal("0")

    # ── Straight (1234, 2345, or 3456) ───────────────────────────────────────
    if wager_type == "straight":
        if sorted_d in ([1,2,3,4], [2,3,4,5], [3,4,5,6]):
            return win(15)
        return Decimal("0")

    # ── Any Triple (3 or 4 dice same number) ─────────────────────────────────
    if wager_type == "any_triple":
        return win(8) if max(counts.values()) >= 3 else Decimal("0")

    # ── Any Quadruple (all 4 dice same) ──────────────────────────────────────
    if wager_type == "any_quadruple":
        return win(200) if max(counts.values()) == 4 else Decimal("0")

    # ── Specific Triple ───────────────────────────────────────────────────────
    if wager_type.startswith("specific_triple_"):
        n = int(wager_type.split("_")[2])
        return win(55) if counts[n] >= 3 else Decimal("0")

    # ── Specific Quadruple ────────────────────────────────────────────────────
    if wager_type.startswith("specific_quadruple_"):
        n = int(wager_type.split("_")[2])
        return win(1000) if counts[n] == 4 else Decimal("0")

    # ── Specific Double (2+ dice show N) ─────────────────────────────────────
    if wager_type.startswith("specific_double_"):
        n = int(wager_type.split("_")[2])
        return win(6) if counts[n] >= 2 else Decimal("0")

    # ── Four-Dice Totals ──────────────────────────────────────────────────────
    _TOTAL_PAY = {
        5: Decimal("280"), 23: Decimal("280"),
        6: Decimal("120"), 22: Decimal("120"),
        7: Decimal("55"),  21: Decimal("55"),
        8: Decimal("30"),  20: Decimal("30"),
        9: Decimal("20"),  19: Decimal("20"),
        10: Decimal("13"), 18: Decimal("13"),
        11: Decimal("10"), 17: Decimal("10"),
        12: Decimal("8"),  16: Decimal("8"),
        13: Decimal("7"),  15: Decimal("7"),
    }
    if wager_type.startswith("total_"):
        t = int(wager_type.split("_")[1])
        if total == t and t in _TOTAL_PAY:
            return win(_TOTAL_PAY[t])
        return Decimal("0")

    # ── Specific 14 (4.1.2) ──────────────────────────────────────────────────
    # Groups defined by sorted dice tuples
    _S14_GROUPS = {
        "specific14_A": {(1,2,5,6),(1,3,4,6),(2,3,4,5)},
        "specific14_B": {(1,3,5,5),(1,4,4,5),(2,2,4,6)},
        "specific14_C": {(2,3,3,6),(1,1,6,6),(2,2,5,5)},
        "specific14_D": {(3,3,4,4),(2,4,4,4),(3,3,3,5)},
    }
    _S14_PAY = {"specific14_A": 15, "specific14_B": 30, "specific14_C": 45, "specific14_D": 80}
    if wager_type in _S14_GROUPS:
        key = tuple(sorted_d)
        if key in _S14_GROUPS[wager_type]:
            return win(_S14_PAY[wager_type])
        return Decimal("0")

    # ── Two-Dice Combinations (any 2 of 4 dice show both values) ─────────────
    if wager_type.startswith("combo_"):
        ab = wager_type[6:]
        a, b = int(ab[0]), int(ab[1])
        if counts[a] >= 1 and counts[b] >= 1 and a != b:
            return win(3)
        return Decimal("0")

    # ── Four Dice From Five Possible Combinations ─────────────────────────────
    # Wins if 4 dice match any 4 of the 5 specified numbers (using multiset logic)
    if wager_type.startswith("four_from_five_"):
        nums_str = wager_type[len("four_from_five_"):]
        five = [int(c) for c in nums_str]
        # The four dice must be a sub-multiset of the five possible numbers
        five_counts = {n: five.count(n) for n in set(five)}
        # Check if sorted_d is covered by five (each die value appears ≤ times in five)
        dice_counts = {n: sorted_d.count(n) for n in set(sorted_d)}
        match = all(dice_counts.get(n, 0) <= five_counts.get(n, 0) for n in dice_counts)
        return win(9) if match else Decimal("0")

    return Decimal("0")
