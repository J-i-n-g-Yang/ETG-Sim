"""Shared poker-card helpers for ETG Sim Solo Poker."""
from itertools import combinations
from collections import Counter
import random

SUITS=("S","H","D","C")
RANKS=("2","3","4","5","6","7","8","9","10","J","Q","K","A")
RV={r:i+2 for i,r in enumerate(RANKS)}

def build_deck(joker=False):
    d=[{"rank":r,"suit":s} for s in SUITS for r in RANKS]
    if joker: d.append({"rank":"JOKER","suit":"X"})
    random.shuffle(d); return d

def _straight_high(vals):
    u=sorted(set(vals), reverse=True)
    if 14 in u: u.append(1)
    for i in range(len(u)-4):
        w=u[i:i+5]
        if w[0]-w[4]==4: return w[0]
    return None

def rank5(cards):
    """Comparable standard five-card poker rank tuple."""
    vals=sorted((RV[c["rank"]] for c in cards), reverse=True)
    cnt=Counter(vals); groups=sorted(((n,v) for v,n in cnt.items()), reverse=True)
    flush=len({c["suit"] for c in cards})==1
    sh=_straight_high(vals)
    if flush and sh: return (8,sh)
    if groups[0][0]==4:
        q=groups[0][1]; return (7,q,max(v for v in vals if v!=q))
    if sorted(cnt.values())==[2,3]:
        t=max(v for v,n in cnt.items() if n==3); p=max(v for v,n in cnt.items() if n==2); return (6,t,p)
    if flush: return (5,*vals)
    if sh: return (4,sh)
    if groups[0][0]==3:
        t=groups[0][1]; ks=sorted((v for v in vals if v!=t),reverse=True); return (3,t,*ks)
    pairs=sorted((v for v,n in cnt.items() if n==2),reverse=True)
    if len(pairs)>=2:
        hi,lo=pairs[:2]; k=max(v for v in vals if v not in (hi,lo)); return (2,hi,lo,k)
    if len(pairs)==1:
        p=pairs[0]; ks=sorted((v for v in vals if v!=p),reverse=True); return (1,p,*ks)
    return (0,*vals)

def best5(cards):
    """Return (best_rank, best_five_cards) without comparing card dictionaries.

    Multiple 5-card combinations can have identical rank tuples. Comparing
    ``(rank_tuple, cards)`` directly makes Python fall through to comparing
    the card dictionaries, which is invalid. Compare rank tuples only.
    """
    best_rank = None
    best_cards = None

    for combo in combinations(cards, 5):
        combo_cards = list(combo)
        combo_rank = rank5(combo_cards)

        if best_rank is None or combo_rank > best_rank:
            best_rank = combo_rank
            best_cards = combo_cards

    return best_rank, best_cards

def name5(rank):
    return ("High Card","Pair","Two Pair","Three of a Kind","Straight","Flush","Full House","Four of a Kind","Straight Flush")[rank[0]]

def rank3(cards):
    vals=sorted((RV[c["rank"]] for c in cards),reverse=True); cnt=Counter(vals)
    flush=len({c["suit"] for c in cards})==1
    u=sorted(set(vals),reverse=True)
    straight=False; high=0
    if len(u)==3:
        if u[0]-u[2]==2: straight=True; high=u[0]
        elif u==[14,3,2]: straight=True; high=3
    if straight and flush:return (5,high)
    if 3 in cnt.values(): return (4,max(v for v,n in cnt.items() if n==3))
    if straight:return (3,high)
    if flush:return (2,*vals)
    pairs=[v for v,n in cnt.items() if n==2]
    if pairs:
        p=pairs[0]; k=max(v for v in vals if v!=p); return (1,p,k)
    return (0,*vals)

def name3(r): return ("High Card","Pair","Flush","Straight","Three of a Kind","Straight Flush")[r[0]]

def dealer_qualifies_singapore(cards):
    r=rank5(cards)
    return r[0]>0 or (r[0]==0 and r[1]>=14 and r[2]>=13)

def dealer_qualifies_threecard(cards):
    r=rank3(cards)
    return r[0]>0 or (r[0]==0 and r[1]>=12)

def cards_json(cards): return [{"rank":c["rank"],"suit":c["suit"]} for c in cards]
