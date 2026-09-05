import random
from decimal import Decimal
from .roulette_base import normalise_pocket,validate_standard_wager,settle_standard_wager,win_return,lose_return
GAME_ID="roulette_sands";NAME="Sands Roulette";ICON="🎡";POCKETS=tuple(["S","00",0]+list(range(1,37)));STRAIGHT_POCKETS=frozenset(POCKETS)
TOP_LINE=frozenset({"S","00",0,1,2,3});GREEN=frozenset({"S","00",0})
EXTRA_SPLITS=frozenset({("S","00"),("S",0),("00",0),(0,1),(0,2),("00",2),("00",3)})
EXTRA_STREETS=frozenset({("S","00",0),("00",0,2),(0,1,2),("00",2,3)})
EXTRA_CORNERS=frozenset({("S","00",0,2),("00",0,2,3),(0,1,2,"00")})
def resolve():return {"number":random.choice(POCKETS)}
def validate_wager(w):
 return str(w) in {"top_line","green"} or validate_standard_wager(w,STRAIGHT_POCKETS,extra_splits=EXTRA_SPLITS,extra_streets=EXTRA_STREETS,extra_corners=EXTRA_CORNERS)
def payout(w,a,o):
 n=normalise_pocket(o["number"] if isinstance(o,dict) else o)
 if not validate_wager(w):raise ValueError(f"Invalid Sands Roulette wager: {w}")
 if w=="top_line":return win_return(a,5) if n in TOP_LINE else lose_return()
 if w=="green":return win_return(a,11) if n in GREEN else lose_return()
 return settle_standard_wager(w,a,n)
