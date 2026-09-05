"""MBS Megalink Mississippi Stud Poker — w.e.f. 3 Feb 2025."""
GAME_ID="poker_mississippi"
NAME="Mississippi Stud Poker"; ICON="🌊"
HOLE_CARDS=2; COMMUNITY_CARDS=3
INITIAL_WAGERS=("ante","three_card_bonus","progressive")
STAGES=("initial","third","fourth","fifth","settle")
def legal_actions(stage, blind=False):
    return ("bet1",) if blind else ("fold","bet1","bet2","bet3")
def action_multiplier(action):
    return int(action[-1]) if action.startswith("bet") else 0
MAIN_PAY={8:100,7:40,6:10,5:6,4:4,3:3,2:2}
def main_odds(rank):
    cat=rank[0]
    if cat==8: return 500 if rank[1]==14 else 100
    if cat in MAIN_PAY:return MAIN_PAY[cat]
    if cat==1 and rank[1]>=11:return 1
    if cat==1 and rank[1]>=6:return 0
    return None
