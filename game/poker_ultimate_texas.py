"""MBS Megalink Ultimate Texas Hold'em Version 2 — w.e.f. 3 Feb 2025."""
GAME_ID="poker_ultimate_texas"; NAME="Ultimate Texas Hold'em"; ICON="♠️"
HOLE_CARDS=2; COMMUNITY_CARDS=5
INITIAL_WAGERS=("ante","blind","trips","progressive")
STAGES=("initial","flop","river","settle")
def legal_actions(stage, blind=False):
    if stage=="initial": return ("check",) if blind else ("check","play3","play4")
    if stage=="flop": return ("check",) if blind else ("check","play2")
    if stage=="river": return ("play1",) if blind else ("fold","play1")
    return ()
BLIND_PAY={8:500,7:10,6:3,5:1.5,4:1}
TRIPS_PAY={8:100,7:40,6:30,5:8,4:7,3:4}
