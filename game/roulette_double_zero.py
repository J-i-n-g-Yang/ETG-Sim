import random
from .roulette_base import normalise_pocket,validate_standard_wager,settle_standard_wager
GAME_ID='roulette_double_zero'; NAME='Double Zero Roulette'; ICON="🎡"
POCKETS=tuple([0,"00"]+list(range(1,37)))
STRAIGHT_POCKETS=frozenset(POCKETS)
EXTRA_SPLITS=frozenset({(0,"00"),(0,1),(0,2),(0,3)})
EXTRA_STREETS=frozenset({(0,1,2),(0,2,3)})
EXTRA_CORNERS=frozenset({(0,1,2,3),(0,"00",1,2),(0,"00",2,3)})
def resolve():return {"number":random.choice(POCKETS)}
def validate_wager(w):return validate_standard_wager(w,STRAIGHT_POCKETS,extra_splits=EXTRA_SPLITS,extra_streets=EXTRA_STREETS,extra_corners=EXTRA_CORNERS)
def payout(w,a,o):
 n=normalise_pocket(o["number"] if isinstance(o,dict) else o)
 if not validate_wager(w):raise ValueError(f"Invalid Roulette wager: {w}")
 return settle_standard_wager(w,a,n)
