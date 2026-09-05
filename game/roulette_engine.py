from decimal import Decimal
from . import roulette_single_zero,roulette_double_zero,roulette_sands_roulette
RULES={m.GAME_ID:m for m in (roulette_single_zero,roulette_double_zero,roulette_sands_roulette)}
GAMES=tuple(RULES);NAMES={g:m.NAME for g,m in RULES.items()};ICONS={g:m.ICON for g,m in RULES.items()}
def validate_wager(game,w):return bool(RULES.get(game) and RULES[game].validate_wager(w))
def spin(game,bets):
 m=RULES.get(game)
 if m is None:raise ValueError("Unknown Roulette game")
 if not bets:raise ValueError("No bets supplied")
 out=m.resolve();tw=Decimal("0");tr=Decimal("0");results=[]
 for b in bets:
  w=str(b["wager_type"] if isinstance(b,dict) else b[0]);a=Decimal(str(b["amount"] if isinstance(b,dict) else b[1]))
  if a<=0:raise ValueError("Invalid wager amount")
  if not m.validate_wager(w):raise ValueError(f"Invalid wager_type for {game}: {w}")
  r=m.payout(w,a,out);tw+=a;tr+=r;results.append({"wager_type":w,"amount":float(a),"return":float(r),"win":r>a})
 return {"game":game,"outcome":{"number":out["number"]},"results":results,"total_wager":float(tw),"total_return":float(tr),"net":float(tr-tw)}
