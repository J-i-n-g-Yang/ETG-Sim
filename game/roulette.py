"""
European Roulette — server-side math — ⚡ LIGHTNING EDITION

Single zero (0-36).  Full outside + inside bet coverage.

Bet types and payouts
----------------------
  Straight-up  straight_N          32:1  (⚡ boosted to 40/45/50/55/60:1 on Lightning numbers)
  Split        split_A_B           17:1
  Street       street_A_B_C        11:1
  Six Line     sixline_A_B          5:1
  Corner       corner_A_B_C_D       8:1
  Column       col1/col2/col3       2:1
  Dozen        dozen1/dozen2/dozen3 2:1
  Even-money   red/black/odd/even/low/high  1:1

⚡ LIGHTNING ROULETTE
----------------------
After bets lock, 5 random straight-up numbers get "struck" and their payout is
boosted from 32:1 to one of {40, 45, 50, 55, 60}:1.

  * The boost applies ONLY to straight-up (`straight_N`) bets.
  * A corner / split / street / six-line that happens to cover a Lightning
    number is NOT boosted — it always pays its normal odds.
  * Non-Lightning straight-ups still pay the normal 32:1.

The Lightning draw is produced by `draw_lightning()` at bet-lock time and must be
persisted on the round (so it can be broadcast to the clients AND fed back into
`payout()` at settlement). See the app-wiring notes in the integration guide.
"""

import random
from decimal import Decimal

# European roulette red numbers
_RED = frozenset([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36])

_COL1 = frozenset(range(1, 37, 3))     # 1,4,7,...,34  (bottom row of layout)
_COL2 = frozenset(range(2, 37, 3))     # 2,5,8,...,35  (middle row)
_COL3 = frozenset(range(3, 37, 3))     # 3,6,9,...,36  (top row)

# ---- ⚡ LIGHTNING config ----------------------------------------------------
LIGHTNING_COUNT       = 5              # how many numbers get struck
LIGHTNING_MULTIPLIERS = [40, 45, 50, 55, 60]  # the boosted payout tiers
BASE_STRAIGHT_PAYOUT  = 32             # normal straight-up odds
# ------------------------------------------------------------------------------

# ---- Layout helpers ----------------------------------------------------------
# The roulette layout columns run c=1..12.
# Row r=1 (top)→3c, r=2 (mid)→3c-1, r=3 (bot)→3c-2
def _num(c: int, r: int) -> int:
    return 3*c if r == 1 else (3*c - 1 if r == 2 else 3*c - 2)

# ---- Pre-compute all valid inside-bet sets ------------------------------------

# Splits: two adjacent numbers on the layout
_VALID_SPLITS: set[tuple] = set()
for _c in range(1, 12):                        # horizontal (same row, adj columns)
    for _r in range(1, 4):
        _VALID_SPLITS.add(tuple(sorted([_num(_c, _r), _num(_c+1, _r)])))
for _c in range(1, 13):                        # vertical (same column, adj rows)
    for _r in range(1, 3):
        _VALID_SPLITS.add(tuple(sorted([_num(_c, _r), _num(_c, _r+1)])))
_VALID_SPLITS.update({(0, 1), (0, 2), (0, 3)})  # zero splits

# Streets: one physical column of 3 numbers, e.g. (1,2,3),(4,5,6),...
_VALID_STREETS: set[tuple] = set()
for _c in range(1, 13):
    _VALID_STREETS.add(tuple(sorted([_num(_c, 1), _num(_c, 2), _num(_c, 3)])))

# Six Lines: two adjacent streets = 6 consecutive numbers, e.g. (1,6),(4,9),...
_VALID_SIXLINES: set[tuple] = set()
for _c in range(1, 12):
    _lo = 3*_c - 2
    _VALID_SIXLINES.add((_lo, _lo + 5))

# Corners: 2×2 block of 4 adjacent numbers
_VALID_CORNERS: set[tuple] = set()
for _c in range(1, 12):
    for _r in range(1, 3):
        _quad = tuple(sorted([_num(_c, _r), _num(_c, _r+1),
                               _num(_c+1, _r), _num(_c+1, _r+1)]))
        _VALID_CORNERS.add(_quad)

# ---- Full wager-type list (used by registry for validation) -----------------
def _build_wager_types() -> list:
    types = ["red", "black", "odd", "even", "low", "high",
             "dozen1", "dozen2", "dozen3",
             "col1", "col2", "col3"]
    types += [f"straight_{n}"                    for n in range(37)]
    types += [f"split_{a}_{b}"                    for a, b in sorted(_VALID_SPLITS)]
    types += [f"street_{'_'.join(map(str,s))}"    for s in sorted(_VALID_STREETS)]
    types += [f"sixline_{lo}_{hi}"                 for lo, hi in sorted(_VALID_SIXLINES)]
    types += [f"corner_{'_'.join(map(str,q))}"     for q in sorted(_VALID_CORNERS)]
    return types

WAGER_TYPES = _build_wager_types()


# ==============================================================================
# ⚡ LIGHTNING DRAW
# ==============================================================================
def draw_lightning(count: int = LIGHTNING_COUNT) -> dict:
    """Pick `count` distinct straight-up numbers (0-36) and assign each a boosted
    multiplier. Returns {number: multiplier}, e.g. {7: 60, 22: 45, 0: 40, ...}.

    Call this ONCE per roulette round, the moment betting locks (No More Bets),
    then persist it on the round and broadcast it to the clients so the projector
    can animate the strikes before the wheel spins.

    When count == 5 (the default), each of the five tiers {40,45,50,55,60} is used
    exactly once, so every round shows the full spread of multipliers. For any
    other count, tiers are chosen at random (with repeats allowed).
    """
    count = max(1, min(count, 37))
    numbers = random.sample(range(0, 37), count)

    if count == len(LIGHTNING_MULTIPLIERS):
        tiers = LIGHTNING_MULTIPLIERS[:]      # exactly one of each tier
        random.shuffle(tiers)
    else:
        tiers = [random.choice(LIGHTNING_MULTIPLIERS) for _ in range(count)]

    return {n: m for n, m in zip(numbers, tiers)}


def _lightning_mult(lightning, n: int):
    """Return the boosted multiplier for number `n` if it is a Lightning number,
    else None. Accepts int-keyed OR str-keyed dicts (handy after JSON round-trips)."""
    if not lightning:
        return None
    if n in lightning:
        return int(lightning[n])
    if str(n) in lightning:
        return int(lightning[str(n)])
    return None


def resolve() -> dict:
    number = random.randint(0, 36)
    if number == 0:
        color = "green"
    elif number in _RED:
        color = "red"
    else:
        color = "black"
    return {"number": number, "color": color}


def payout(wager_type: str, amount: Decimal, outcome: dict,
           choice=None, lightning: dict | None = None) -> Decimal:
    """Return the TOTAL returned to the player (stake + winnings), or 0 on a loss.

    `lightning` is the {number: multiplier} map for THIS round (from draw_lightning).
    It only affects straight-up bets on a struck number; everything else is untouched.
    """
    amount = Decimal(str(amount))
    n      = outcome["number"]
    color  = outcome["color"]

    def win(mult) -> Decimal:
        return amount + amount * Decimal(str(mult))

    # Even-money outside bets — zero loses
    if wager_type == "red":
        return win(1) if color == "red" else Decimal("0")
    if wager_type == "black":
        return win(1) if color == "black" else Decimal("0")
    if wager_type == "odd":
        return win(1) if n > 0 and n % 2 == 1 else Decimal("0")
    if wager_type == "even":
        return win(1) if n > 0 and n % 2 == 0 else Decimal("0")
    if wager_type == "low":
        return win(1) if 1 <= n <= 18 else Decimal("0")
    if wager_type == "high":
        return win(1) if 19 <= n <= 36 else Decimal("0")

    # Dozens — 2:1
    if wager_type == "dozen1":
        return win(2) if 1 <= n <= 12 else Decimal("0")
    if wager_type == "dozen2":
        return win(2) if 13 <= n <= 24 else Decimal("0")
    if wager_type == "dozen3":
        return win(2) if 25 <= n <= 36 else Decimal("0")

    # Columns — 2:1
    if wager_type == "col1":
        return win(2) if n in _COL1 else Decimal("0")
    if wager_type == "col2":
        return win(2) if n in _COL2 else Decimal("0")
    if wager_type == "col3":
        return win(2) if n in _COL3 else Decimal("0")

    # ⚡ Straight-up — 32:1, boosted to 40/45/50/55/60:1 on a Lightning number
    if wager_type.startswith("straight_"):
        target = int(wager_type.split("_")[1])
        if n == target:
            mult = _lightning_mult(lightning, n)
            return win(mult if mult is not None else BASE_STRAIGHT_PAYOUT)
        return Decimal("0")

    # Split — 17:1  (NOT boosted, even if it covers a Lightning number)
    if wager_type.startswith("split_"):
        parts = wager_type.split("_")[1:]
        nums = tuple(sorted(int(x) for x in parts))
        if nums not in _VALID_SPLITS:
            return Decimal("0")
        return win(17) if n in nums else Decimal("0")

    # Street — 11:1  (NOT boosted)
    if wager_type.startswith("street_"):
        parts = wager_type.split("_")[1:]
        nums = tuple(sorted(int(x) for x in parts))
        if nums not in _VALID_STREETS:
            return Decimal("0")
        return win(11) if n in nums else Decimal("0")

    # Six Line — 5:1  (NOT boosted)
    if wager_type.startswith("sixline_"):
        parts = wager_type.split("_")[1:]
        lo, hi = int(parts[0]), int(parts[1])
        if (lo, hi) not in _VALID_SIXLINES:
            return Decimal("0")
        return win(5) if lo <= n <= hi else Decimal("0")

    # Corner — 8:1  (NOT boosted)
    if wager_type.startswith("corner_"):
        parts = wager_type.split("_")[1:]
        nums = tuple(sorted(int(x) for x in parts))
        if nums not in _VALID_CORNERS:
            return Decimal("0")
        return win(8) if n in nums else Decimal("0")

    return Decimal("0")
