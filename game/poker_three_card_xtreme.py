"""MBS Megalink Three Card Poker Xtreme Version 2 — w.e.f. 3 Feb 2025."""
from .poker_base import dealer_qualifies_threecard
GAME_ID="poker_three_card_xtreme"; NAME="Three Card Poker Xtreme"; ICON="3️⃣"
HOLE_CARDS=3; DEALER_CARDS=3; COMMUNITY_CARDS=2
INITIAL_WAGERS=("ante","pair_plus","six_card_bonus","progressive")
def legal_actions(stage, blind=False): return ("play",) if blind else ("fold","play")
PLAY_MULTIPLIER=1
ANTE_BONUS={5:5,4:4,3:1}
PAIR_PLUS={5:40,4:30,3:5,2:4,1:1}
SIX_CARD={8:500,7:50,6:20,5:15,4:10,3:7}
def dealer_qualifies(cards): return dealer_qualifies_threecard(cards)
