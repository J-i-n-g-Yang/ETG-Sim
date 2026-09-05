"""Craps (MBS Version 4) - stateless rules/math layer."""
import random
from decimal import Decimal

POINTS = (4, 5, 6, 8, 9, 10)
HARDWAYS = (4, 6, 8, 10)
PASS_ODDS = {4:Decimal('2'),5:Decimal('1.5'),6:Decimal('1.2'),8:Decimal('1.2'),9:Decimal('1.5'),10:Decimal('2')}
DONT_ODDS = {4:Decimal('.5'),5:Decimal(2)/Decimal(3),6:Decimal(5)/Decimal(6),8:Decimal(5)/Decimal(6),9:Decimal(2)/Decimal(3),10:Decimal('.5')}
PLACE_PAY = {4:Decimal(9)/Decimal(5),5:Decimal(7)/Decimal(5),6:Decimal(7)/Decimal(6),8:Decimal(7)/Decimal(6),9:Decimal(7)/Decimal(5),10:Decimal(9)/Decimal(5)}
BUY_PAY = PASS_ODDS.copy()
LAY_PAY = DONT_ODDS.copy()
HARD_PAY = {4:Decimal('7'),6:Decimal('9'),8:Decimal('9'),10:Decimal('7')}
ONE_ROLL = {'any_seven','any_craps','two_crap','three_crap','twelve_crap','eleven','craps_eleven','field','horn','horn_high_2','horn_high_3','horn_high_11','horn_high_12'}
WAGER_TYPES = tuple(['pass_line','dont_pass','pass_odds','dont_pass_odds','come','dont_come'] + sorted(ONE_ROLL) + [f'hard_{n}' for n in HARDWAYS] + [f'place_{n}' for n in POINTS] + [f'buy_{n}' for n in POINTS] + [f'lay_{n}' for n in POINTS] + [f'come_odds_{n}' for n in POINTS] + [f'dont_come_odds_{n}' for n in POINTS])

def outcome_from_dice(d1,d2,point=None):
    d1,d2=int(d1),int(d2)
    if d1 not in range(1,7) or d2 not in range(1,7): raise ValueError('Dice must be between 1 and 6')
    total=d1+d2
    if point is None:
        if total in (7,11): event,point_out='natural',None
        elif total in (2,3,12): event,point_out='craps',None
        else: event,point_out='point_set',total
    elif total==point: event,point_out='point_hit',None
    elif total==7: event,point_out='seven_out',None
    else: event,point_out='rolling',point
    return {'dice':[d1,d2],'total':total,'is_hard':d1==d2,'point_in':point,'point_out':point_out,'event':event}

def resolve(point=None):
    return outcome_from_dice(random.randint(1,6),random.randint(1,6),point)

def to_one(amount,odds):
    a=Decimal(str(amount)); return a*(Decimal('1')+Decimal(str(odds)))

def buy_vig(amount): return Decimal(str(amount))*Decimal('.05')
def lay_vig(amount,number): return Decimal(str(amount))*LAY_PAY[int(number)]*Decimal('.05')

def one_roll_return(wt,amount,outcome):
    a=Decimal(str(amount)); total=int(outcome['total']); win=lambda odds:to_one(a,odds)
    if wt=='any_seven': return win(4) if total==7 else Decimal('0')
    if wt=='any_craps': return win(7) if total in (2,3,12) else Decimal('0')
    if wt=='two_crap': return win(30) if total==2 else Decimal('0')
    if wt=='three_crap': return win(15) if total==3 else Decimal('0')
    if wt=='twelve_crap': return win(30) if total==12 else Decimal('0')
    if wt=='eleven': return win(15) if total==11 else Decimal('0')
    if wt=='craps_eleven':
        if total in (2,3,12): return win(3)
        if total==11: return win(7)
        return Decimal('0')
    if wt=='field':
        if total in (3,4,9,10,11): return win(1)
        if total in (2,12): return win(2)
        return Decimal('0')
    if wt=='horn':
        unit=a/Decimal('4')
        if total in (2,12): return unit*Decimal('31')
        if total in (3,11): return unit*Decimal('16')
        return Decimal('0')
    if wt.startswith('horn_high_'):
        high=int(wt.rsplit('_',1)[1]); unit=a/Decimal('5')
        if total not in (2,3,11,12): return Decimal('0')
        odds=Decimal('30') if total in (2,12) else Decimal('15')
        units=Decimal('2') if total==high else Decimal('1')
        return units*unit*(Decimal('1')+odds)
    return None

def payout(wt,amount,outcome,choice=None):
    """Legacy compatibility for /api/solo/spin. New Dice Craps uses craps_engine."""
    a=Decimal(str(amount)); one=one_roll_return(wt,a,outcome)
    if one is not None: return one
    total=outcome['total']; hard=outcome['is_hard']; point=outcome['point_in']; event=outcome['event']
    if wt=='pass_line':
        if point is None:
            if total in (7,11): return to_one(a,1)
            if total in (2,3,12): return Decimal('0')
            return a
        if event=='point_hit': return to_one(a,1)
        if event=='seven_out': return Decimal('0')
        return a
    if wt=='dont_pass':
        if point is None:
            if total in (2,3): return to_one(a,1)
            if total==12: return a
            if total in (7,11): return Decimal('0')
            return a
        if event=='seven_out': return to_one(a,1)
        if event=='point_hit': return Decimal('0')
        return a
    if wt.startswith('hard_'):
        n=int(wt.split('_')[1])
        if total==n and hard: return to_one(a,HARD_PAY[n])
        if total==7 or total==n: return Decimal('0')
        return a
    for prefix,table,seven_wins in [('place_',PLACE_PAY,False),('buy_',BUY_PAY,False),('lay_',LAY_PAY,True)]:
        if wt.startswith(prefix):
            n=int(wt.split('_')[1])
            if seven_wins:
                if total==7:return to_one(a,table[n])
                if total==n:return Decimal('0')
            else:
                if total==n:return to_one(a,table[n])
                if total==7:return Decimal('0')
            return a
    return Decimal('0')
