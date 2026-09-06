"""
Sic Bo — server-side math.

Three dice, values 1-6 each.  Wager types cover the full standard Sic Bo table.

Payouts corrected per Version 7 PDF audit (2026-08-30):
  - Total 4/17:       62:1  (was 60)
  - Total 6/15:       18:1  (was 17)
  - Specific Doubles: 11:1  (was 10)
  - Any Triple:       31:1  (was 30)
  - Two Dice Combo:    6:1  (was 5)
  - Single die 3-of:  12:1  (was 3)
  + Added: three_single_NNN  (Rule 3.5.10 / 4.1.4) — e.g. three_single_126
  + Added: double_single_NNN (Rule 3.5.11 / 4.1.5) — e.g. double_single_113
  + Added: three_from_four_NNNN (Rule 3.5.13 / 4.1.7) — e.g. three_from_four_1234

Second audit pass (against the official Version 7 PDF, 2026-08-30):
  - Total 5/16:  31:1  (was incorrectly 30 — PDF 4.1.2 states 31 to 1)
  - Total 9/12:   7:1  (was incorrectly 6  — PDF 4.1.2 states 7 to 1)
  - three_from_four_NNNN: restricted to the 4 combinations actually listed in
    Rule 4.1.7 / Appendix A (1-2-3-4, 2-3-4-5, 2-3-5-6, 3-4-5-6). The previous
    version generated all 15 possible 4-number subsets of 1-6, which is not
    an approved wager under the GRA rules.
  - three_from_four win condition tightened to require the three dice show
    THREE DISTINCT values, all drawn from the specified four numbers ("the
    three dice matches three out of four numbers"). The previous version
    only checked that each die's value was *somewhere* in the four-number
    set, which also paid out on doubles/triples within that set — at 7:1
    that prices out to a ~2.4:1 fair-odds bet (hugely +EV for the player).
    The distinct-values reading prices out to ~8:1 fair odds, consistent
    with the quoted 7:1 payout.
"""

import random
from decimal import Decimal
from itertools import combinations

# ---- helpers ---------------------------------------------------------------

def _combo_keys():
    return [f"combo_{a}{b}" for a, b in combinations(range(1, 7), 2)]

def _three_single_keys():
    """
    Rule 3.5.10 / 4.1.4: Three Single Dice Combinations.
    All unordered triples from 1-6 where all three values are distinct.
    e.g. 123, 124, 125, 126, 134, 135, 136, 145, 146, 156, 234, 235, 236, 245, 246, 256, 345, 346, 356, 456
    Encoded as sorted digits: three_single_126, three_single_135, etc.
    """
    return [f"three_single_{''.join(map(str, t))}"
            for t in combinations(range(1, 7), 3)]

def _double_single_keys():
    """
    Rule 3.5.11 / 4.1.5: Double Numbers With Single Dice Combinations.
    A specific pair (d,d) plus a different single value s.
    e.g. double_single_113 means pair of 1s + a 3.
    Encoded as: double_single_NNS where NN=pair digit, S=single digit.
    """
    keys = []
    for pair in range(1, 7):
        for single in range(1, 7):
            if single != pair:
                keys.append(f"double_single_{pair}{pair}{single}")
    return keys

# Rule 3.5.13 / 4.1.7 + Appendix A: only these four specific four-number
# groups are approved wagers — NOT all C(6,4)=15 possible subsets.
THREE_FROM_FOUR_GROUPS = ["1234", "2345", "2356", "3456"]

def _three_from_four_keys():
    return [f"three_from_four_{g}" for g in THREE_FROM_FOUR_GROUPS]

# ---- wager type list -------------------------------------------------------
WAGER_TYPES = (
    ["big", "small", "odd", "even", "any_triple"]
    + [f"triple_{n}" for n in range(1, 7)]
    + [f"double_{n}" for n in range(1, 7)]
    + [f"total_{n}" for n in range(4, 18)]
    + [f"single_{n}" for n in range(1, 7)]
    + _combo_keys()
    + _three_single_keys()
    + _double_single_keys()
    + _three_from_four_keys()
)

# ---- payout multipliers (win-only, stake not included) ---------------------
# Fixed per audit: 4/17→62, 6/15→18 (were 60, 17); 5/16→31, 9/12→7 (were 30, 6)
_TOTAL_PAY = {
    4:  Decimal("62"), 17: Decimal("62"),   # PDF 4.1.2: 62:1
    5:  Decimal("31"), 16: Decimal("31"),   # PDF 4.1.2: 31:1  (was 30)
    6:  Decimal("18"), 15: Decimal("18"),   # PDF 4.1.2: 18:1  (was 17)
    7:  Decimal("12"), 14: Decimal("12"),
    8:  Decimal("8"),  13: Decimal("8"),
    9:  Decimal("7"),  12: Decimal("7"),    # PDF 4.1.2: 7:1  (was 6)
    10: Decimal("6"),  11: Decimal("6"),
}


def resolve() -> dict:
    d1, d2, d3 = random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)
    total = d1 + d2 + d3
    is_triple = (d1 == d2 == d3)
    return {
        "dice":   [d1, d2, d3],
        "total":  total,
        "triple": is_triple,
    }


def payout(wager_type: str, amount: Decimal, outcome: dict, choice=None) -> Decimal:
    amount    = Decimal(str(amount))
    dice      = outcome["dice"]
    total     = outcome["total"]
    is_triple = outcome["triple"]
    counts    = {n: dice.count(n) for n in range(1, 7)}
    sorted_d  = sorted(dice)

    def win(mult: Decimal) -> Decimal:
        return amount + amount * mult

    if wager_type == "big":
        if not is_triple and total >= 11:
            return win(Decimal("1"))
        return Decimal("0")

    if wager_type == "small":
        if not is_triple and total <= 10:
            return win(Decimal("1"))
        return Decimal("0")

    if wager_type == "odd":
        if not is_triple and total % 2 == 1:
            return win(Decimal("1"))
        return Decimal("0")

    if wager_type == "even":
        if not is_triple and total % 2 == 0:
            return win(Decimal("1"))
        return Decimal("0")

    if wager_type == "any_triple":
        # Fixed: 31:1 (was 30)
        return win(Decimal("31")) if is_triple else Decimal("0")

    if wager_type.startswith("triple_") and not wager_type.startswith("triple_"):
        pass  # handled below

    # Specific Triple: triple_N  → 180:1
    if wager_type.startswith("triple_") and "_single_" not in wager_type and "from" not in wager_type:
        # Guard: must be exactly "triple_N"
        parts = wager_type.split("_")
        if len(parts) == 2 and parts[1].isdigit():
            n = int(parts[1])
            return win(Decimal("180")) if is_triple and dice[0] == n else Decimal("0")

    # Specific Double: double_N → 11:1 (Fixed: was 10)
    if wager_type.startswith("double_") and "_single_" not in wager_type:
        parts = wager_type.split("_")
        if len(parts) == 2 and parts[1].isdigit():
            n = int(parts[1])
            return win(Decimal("11")) if counts[n] >= 2 else Decimal("0")

    if wager_type.startswith("total_"):
        t = int(wager_type.split("_")[1])
        if total == t and t in _TOTAL_PAY:
            return win(_TOTAL_PAY[t])
        return Decimal("0")

    if wager_type.startswith("single_"):
        n = int(wager_type.split("_")[1])
        c = counts[n]
        if c == 0:
            return Decimal("0")
        if c == 1:
            return win(Decimal("1"))    # 1:1
        if c == 2:
            return win(Decimal("2"))    # 2:1
        # c == 3: Fixed 12:1 (was 3:1)
        return win(Decimal("12"))

    # Two Dice Combination: combo_AB → 6:1 (Fixed: was 5)
    if wager_type.startswith("combo_") and len(wager_type) == 8:
        ab = wager_type[6:]
        a, b = int(ab[0]), int(ab[1])
        if not is_triple and a in dice and b in dice and a != b:
            return win(Decimal("6"))
        return Decimal("0")

    # ── Rule 3.5.10 / 4.1.4: Three Single Dice Combinations → 30:1 ──────────
    # three_single_ABC: dice must show all three distinct values A, B, C (any order)
    if wager_type.startswith("three_single_"):
        vals_str = wager_type[len("three_single_"):]   # e.g. "126"
        if len(vals_str) == 3:
            req = sorted([int(c) for c in vals_str])
            return win(Decimal("30")) if sorted_d == req else Decimal("0")
        return Decimal("0")

    # ── Rule 3.5.11 / 4.1.5: Double Numbers With Single Dice Combination → 50:1 ─
    # double_single_NNS: dice must show exactly pair of N plus one S (not triple)
    if wager_type.startswith("double_single_"):
        code = wager_type[len("double_single_"):]      # e.g. "113"
        if len(code) == 3:
            pair_n = int(code[0])   # both first digits are the pair value
            single_s = int(code[2])
            # counts[pair_n] == 2 and counts[single_s] >= 1 and not a triple
            if counts[pair_n] == 2 and counts[single_s] == 1 and not is_triple:
                return win(Decimal("50"))
        return Decimal("0")

    # ── Rule 3.5.13 / 4.1.7: Three Dice From Four Possible Combinations → 7:1 ─
    # three_from_four_ABCD: the three dice must show THREE DISTINCT values,
    # all drawn from {A,B,C,D} ("the three dice matches three out of four
    # numbers"). Doubles/triples within the set do NOT count — see audit
    # note above for why (7:1 only makes sense as a ~11% / ~8:1-fair bet).
    if wager_type.startswith("three_from_four_"):
        vals_str = wager_type[len("three_from_four_"):]   # e.g. "1234"
        if len(vals_str) == 4:
            allowed = set(int(c) for c in vals_str)
            if len(set(dice)) == 3 and set(dice) <= allowed:
                return win(Decimal("7"))
        return Decimal("0")

    return Decimal("0")
