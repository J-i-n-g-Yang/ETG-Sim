"""Immortal Dragon Tiger No Commission Baccarat (MBS), Version 3, w.e.f. 5 Aug 2026."""
from decimal import Decimal
from .baccarat_base import deal, common_payout, win_return
WAGER_TYPES=['player', 'banker', 'tie', 'dragon_tiger', 'big_dragon', 'small_dragon', 'big_tiger', 'small_tiger', 'tiger_tie', 'player_pair', 'banker_pair', 'immortal_dragon']
def resolve(): return deal("baccarat_immortal")
def payout(wager_type,amount,outcome,choice=None):
    a=Decimal(str(amount)); r=common_payout(wager_type,a,outcome,immortal_main=True)
    if r is not None: return r
    if wager_type=="player_pair": return win_return(a,11) if outcome["player_pair"] else Decimal("0")
    if wager_type=="banker_pair": return win_return(a,11) if outcome["banker_pair"] else Decimal("0")
    if wager_type=="immortal_dragon": return win_return(a,25) if outcome["winner"]=="banker" and outcome["player_total"]==7 else Decimal("0")
    return Decimal("0")
