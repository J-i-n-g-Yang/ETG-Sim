"""Dragon Tiger No Commission Baccarat (MBS), Version 4, w.e.f. 5 Aug 2026."""
from decimal import Decimal
from .baccarat_base import deal, common_payout
WAGER_TYPES=['player', 'banker', 'tie', 'dragon_tiger', 'big_dragon', 'small_dragon', 'big_tiger', 'small_tiger', 'tiger_tie']
def resolve(): return deal("baccarat_dragon_tiger")
def payout(wager_type,amount,outcome,choice=None):
    r=common_payout(wager_type,amount,outcome)
    return r if r is not None else Decimal("0")
