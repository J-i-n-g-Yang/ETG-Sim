"""Dedicated Solo Dice family orchestrator."""
from decimal import Decimal
import game.registry as registry
from .dice_base import GAMES,NAMES,ICONS,DICE_COUNTS,FELT_TEMPLATES
from . import craps_engine

def validate_game(game): return game in GAMES
def wager_types(game):
    if game=='craps':
        from . import craps
        return tuple(craps.WAGER_TYPES)
    if game not in GAMES:return ()
    return tuple(getattr(registry.get_module(game),'WAGER_TYPES',()))
def validate_wager(game,wager_type):
    if game=='craps':return craps_engine.validate_wager(wager_type)
    return game in GAMES and registry.validate_wager(game,wager_type)
def roll(game,bets,state=None):
    if game not in GAMES:raise ValueError('Unknown Dice game')
    if game=='craps':return craps_engine.roll(bets,state)
    mod=registry.get_module(game);outcome=mod.resolve();results=[];tr=Decimal('0');tw=Decimal('0')
    for wt,raw in bets:
        a=Decimal(str(raw))
        if not validate_wager(game,wt):raise ValueError(f'Invalid wager_type for {game}: {wt}')
        ret=mod.payout(wt,a,outcome);tw+=a;tr+=ret;results.append({'wager_type':wt,'amount':float(a),'return':float(ret),'win':ret>a,'push':ret==a})
    return {'game':game,'outcome':outcome,'results':results,'total_wager':float(tw),'total_return':float(tr),'net':float(tr-tw),'state':{}}
