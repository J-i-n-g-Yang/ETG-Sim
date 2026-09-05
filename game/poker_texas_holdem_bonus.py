"""MBS Megalink Texas Hold'em Bonus Progressive Version 10 — w.e.f. 3 Feb 2025."""
GAME_ID="poker_texas_bonus"; NAME="Texas Hold'em Bonus Progressive"; ICON="⭐"
HOLE_CARDS=2; COMMUNITY_CARDS=5
INITIAL_WAGERS=("ante","bonus","progressive")
STAGES=("initial","flop","turn","settle")
def legal_actions(stage, blind=False):
    if stage=="initial": return ("flop",) if blind else ("fold","flop")
    if stage=="flop": return ("check",) if blind else ("check","turn")
    if stage=="turn": return ("check",) if blind else ("check","river")
    return ()
FLOP_MULTIPLIER=2; TURN_MULTIPLIER=1; RIVER_MULTIPLIER=1
BONUS_PAY={"AA_both":1000,"AA_player":30,"AK_suited":25,"AQ_AJ_suited":20,"AK_unsuited":15,"KK_QQ_JJ":10,"AQ_AJ_unsuited":5,"TT_22":3}
