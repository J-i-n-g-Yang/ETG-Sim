"""MBS Megalink Singapore Stud Poker Version 10 — w.e.f. 3 Feb 2025."""
from .poker_base import dealer_qualifies_singapore
GAME_ID="poker_singapore_stud"; NAME="Singapore Stud Poker"; ICON="🦁"
HOLE_CARDS=5; INITIAL_WAGERS=("ante","progressive")
def legal_actions(stage, blind=False): return ("play",) if blind else ("fold","play")
PLAY_MULTIPLIER=2
BET_PAY={8:250,7:20,6:7,5:5,4:4,3:3,2:2,1:1,0:1}
def dealer_qualifies(cards): return dealer_qualifies_singapore(cards)
