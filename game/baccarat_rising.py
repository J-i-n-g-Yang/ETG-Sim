"""Rising Dragon Tiger No Commission Baccarat (MBS), w.e.f. 4 May 2026."""
from decimal import Decimal
from .baccarat_base import deal, common_payout, win_return
WAGER_TYPES=['player', 'banker', 'tie', 'dragon_tiger', 'big_dragon', 'small_dragon', 'big_tiger', 'small_tiger', 'tiger_tie', 'rising_dragon', 'rising_tiger']
RISING_DRAGON={4:Decimal("4"),5:Decimal("6"),6:Decimal("4.5")}
RISING_TIGER={4:Decimal("4"),5:Decimal("4.5"),6:Decimal("5.5")}
def resolve(): return deal("baccarat_rising")
def payout(wager_type,amount,outcome,choice=None):
    a=Decimal(str(amount)); r=common_payout(wager_type,a,outcome)
    if r is not None: return r
    if wager_type in ("rising_dragon","rising_tiger"):
        if outcome["winner"]=="tie": return a
        side="player" if wager_type=="rising_dragon" else "banker"
        if outcome["winner"]!=side: return Decimal("0")
        odds=(RISING_DRAGON if side=="player" else RISING_TIGER).get(outcome["total_cards"])
        return win_return(a,odds) if odds is not None else Decimal("0")
    return Decimal("0")
