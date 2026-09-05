"""Shared MBS Dragon Tiger No Commission Baccarat dealing and payout helpers."""
import random
from decimal import Decimal
SUITS=("S","H","D","C"); RANKS=("A","2","3","4","5","6","7","8","9","10","J","Q","K"); NUM_DECKS=8
def card_value(rank):
    if rank=="A": return 1
    if rank in ("10","J","Q","K"): return 0
    return int(rank)
def hand_total(cards): return sum(card_value(c["rank"]) for c in cards)%10
def banker_draws(total,p3):
    if p3 is None: return total<=5
    if total<=2: return True
    if total==3: return p3!=8
    if total==4: return p3 in (2,3,4,5,6,7)
    if total==5: return p3 in (4,5,6,7)
    if total==6: return p3 in (6,7)
    return False
def is_pair(cards):
    if len(cards)<2: return False
    a,b=cards[0]["rank"],cards[1]["rank"]; faces={"J","Q","K"}
    if a in faces or b in faces: return a==b
    return card_value(a)==card_value(b)
def deal(game):
    shoe=[{"rank":r,"suit":s} for s in SUITS for r in RANKS]*NUM_DECKS; random.shuffle(shoe)
    p=[shoe.pop()]; b=[shoe.pop()]; p.append(shoe.pop()); b.append(shoe.pop())
    initial_p=list(p); initial_b=list(b); pt,bt=hand_total(p),hand_total(b); natural=pt in (8,9) or bt in (8,9); p3=None
    if not natural:
        if pt<=5:
            c=shoe.pop(); p.append(c); p3=card_value(c["rank"])
        bt=hand_total(b)
        if banker_draws(bt,p3): b.append(shoe.pop())
    pt,bt=hand_total(p),hand_total(b); winner="player" if pt>bt else "banker" if bt>pt else "tie"
    return {"game":game,"winner":winner,"player_total":pt,"banker_total":bt,"player_cards_count":len(p),"banker_cards_count":len(b),
      "total_cards":len(p)+len(b),"natural":natural,"player_cards":[{"rank":c["rank"],"suit":c["suit"]} for c in p],
      "banker_cards":[{"rank":c["rank"],"suit":c["suit"]} for c in b],"player_pair":is_pair(initial_p),"banker_pair":is_pair(initial_b)}
def win_return(amount,odds):
    a=Decimal(str(amount)); return a+a*Decimal(str(odds))
def common_payout(wager,amount,o,immortal_main=False):
    a=Decimal(str(amount)); w=o["winner"]; pt=o["player_total"]; bt=o["banker_total"]; pc=o["player_cards_count"]; bc=o["banker_cards_count"]
    if wager=="tie": return win_return(a,8) if w=="tie" else Decimal("0")
    if wager=="tiger_tie": return win_return(a,35) if w=="tie" and pt==6 else Decimal("0")
    if wager=="player":
        if w=="tie": return a
        if immortal_main and pt==7 and bt in (8,9): return a
        if w!="player": return Decimal("0")
        return win_return(a,Decimal("0.5") if immortal_main and pt==7 else 1)
    if wager=="banker":
        if w=="tie": return a
        if w!="banker": return Decimal("0")
        return win_return(a,Decimal("0.5") if bt==6 else 1)
    if wager=="dragon_tiger":
        if w=="player" and pt==7 and bt==6:
            odds=100 if pc==3 and bc==3 else 30 if pc==2 and bc==2 else 40
            return win_return(a,odds)
        return Decimal("0")
    if wager=="big_dragon": return win_return(a,30) if w=="player" and pt==7 and pc==3 else Decimal("0")
    if wager=="small_dragon": return win_return(a,15) if w=="player" and pt==7 and pc==2 else Decimal("0")
    if wager=="big_tiger": return win_return(a,50) if w=="banker" and bt==6 and bc==3 else Decimal("0")
    if wager=="small_tiger": return win_return(a,22) if w=="banker" and bt==6 and bc==2 else Decimal("0")
    return None
