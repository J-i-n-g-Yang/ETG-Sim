"""Stateful Solo Craps engine for MBS Craps Version 4."""
from decimal import Decimal
from . import craps
POINTS=craps.POINTS

def D(v): return Decimal(str(v))
def new_state():
    return {
        'point':None,
        'bets':{},
        'come':{str(n):0.0 for n in POINTS},
        'dont_come':{str(n):0.0 for n in POINTS},
        'come_odds':{str(n):0.0 for n in POINTS},
        'dont_come_odds':{str(n):0.0 for n in POINTS},
        'working':{},
        'dont_pass_replacement_locked':False,
        'dont_come_replacement_locked':False,
    }
def load(raw):
    s=new_state(); raw=raw or {}; s['point']=raw.get('point')
    s['bets']={k:D(v) for k,v in (raw.get('bets') or {}).items()}
    for b in ('come','dont_come','come_odds','dont_come_odds'):
        s[b]={str(n):D((raw.get(b) or {}).get(str(n),0)) for n in POINTS}
    s['working']=dict(raw.get('working') or {})
    s['dont_pass_replacement_locked']=bool(
        raw.get(
            'dont_pass_replacement_locked',
            False,
        )
    )
    s['dont_come_replacement_locked']=bool(
        raw.get(
            'dont_come_replacement_locked',
            False,
        )
    )
    return s
def plain(v):
    if isinstance(v,Decimal): return float(v)
    if isinstance(v,dict): return {k:plain(x) for k,x in v.items()}
    if isinstance(v,list): return [plain(x) for x in v]
    return v
def validate_wager(wt): return wt in craps.WAGER_TYPES

def can_place(wt,s):
    p=s['point']

    if (
        wt=='dont_pass'
        and s.get(
            'dont_pass_replacement_locked',
            False,
        )
    ):
        raise ValueError(
            "Don't Pass cannot be replaced or increased "
            "after removal or reduction"
        )

    if (
        wt=='dont_come'
        and s.get(
            'dont_come_replacement_locked',
            False,
        )
    ):
        raise ValueError(
            "Don't Come cannot be replaced or increased "
            "after removal or reduction"
        )
    if wt=='pass_line' and p is not None and s['bets'].get('pass_line',0)<=0: raise ValueError('Pass Line may only be established before a Come Out Roll')
    if wt=='dont_pass' and p is not None and s['bets'].get('dont_pass',0)<=0: raise ValueError("Don't Pass may only be established before a Come Out Roll")
    if wt in ('come','dont_come') and p is None: raise ValueError("Come and Don't Come require an established Point")
    if wt=='pass_odds' and (p is None or s['bets'].get('pass_line',0)<=0): raise ValueError('Pass Line Odds requires Pass Line and an established Point')
    if wt=='dont_pass_odds' and (p is None or s['bets'].get('dont_pass',0)<=0): raise ValueError("Don't Pass Odds requires Don't Pass and an established Point")
    if wt.startswith('come_odds_'):
        n=wt.rsplit('_',1)[1]
        if s['come'][n]<=0: raise ValueError('Come Odds requires a Come wager on that Come Point')
    if wt.startswith('dont_come_odds_'):
        n=wt.rsplit('_',1)[1]
        if s['dont_come'][n]<=0: raise ValueError("Don't Come Odds requires a Don't Come wager on that Come Point")

def add_bets(s,bets):
    outlay=vig=Decimal('0')
    for wt,raw in bets:
        if not validate_wager(wt): raise ValueError(f'Invalid Craps wager: {wt}')
        a=D(raw)
        if a<=0: raise ValueError('Craps wager must be positive')
        can_place(wt,s)
        if wt=='horn' and a%4!=0: raise ValueError('Horn wager must be divisible by 4')
        if wt.startswith('horn_high_') and a%5!=0: raise ValueError('Horn High wager must be divisible by 5')
        if wt.startswith('come_odds_'): s['come_odds'][wt.rsplit('_',1)[1]]+=a
        elif wt.startswith('dont_come_odds_'): s['dont_come_odds'][wt.rsplit('_',1)[1]]+=a
        else: s['bets'][wt]=s['bets'].get(wt,Decimal('0'))+a
        v=craps.buy_vig(a) if wt.startswith('buy_') else craps.lay_vig(a,int(wt.split('_')[1])) if wt.startswith('lay_') else Decimal('0')
        vig+=v; outlay+=a+v
    return outlay,vig

def working(s,wt):
    if wt in s['working']: return bool(s['working'][wt])
    if wt.startswith('lay_') or wt.startswith('dont_come_odds_'): return True
    if s['point'] is None and (wt.startswith('place_') or wt.startswith('buy_') or wt.startswith('hard_') or wt.startswith('come_odds_')): return False
    return True

def action(raw,wt,act):
    s=load(raw)
    if act in ('on','off'):
        s['working'][wt]=(act=='on'); return {'state':plain(s),'refund':0.0}
    if act!='take_down': raise ValueError('Unknown Craps action')

    if wt=='pass_line':
        raise ValueError('Pass Line is a contract wager and cannot be removed')

    if wt.startswith('come_point_'):
        raise ValueError('Come is a contract wager and cannot be removed')

    refund=Decimal('0')

    if wt.startswith('come_odds_'):
        n=wt.rsplit('_',1)[1]
        refund=s['come_odds'][n]
        s['come_odds'][n]=Decimal('0')

    elif wt.startswith('dont_come_odds_'):
        n=wt.rsplit('_',1)[1]
        refund=s['dont_come_odds'][n]
        s['dont_come_odds'][n]=Decimal('0')

    elif wt.startswith('dont_come_point_'):
        n=wt.rsplit('_',1)[1]
        refund=s['dont_come'][n]+s['dont_come_odds'][n]
        s['dont_come'][n]=Decimal('0')
        s['dont_come_odds'][n]=Decimal('0')
        s['dont_come_replacement_locked']=True

    else:
        a=s['bets'].pop(wt,Decimal('0'))

        if (
            wt=='dont_pass'
            and a>0
        ):
            s['dont_pass_replacement_locked']=True

        refund=a+(craps.buy_vig(a) if wt.startswith('buy_') else Decimal('0'))

    s['working'].pop(wt,None)
    return {'state':plain(s),'refund':float(refund)}

def result(rows,wt,a,ret,status,note=None):
    r={'wager_type':wt,'amount':float(a),'return':float(ret),'status':status,'win':status=='win','push':status=='push','active':status=='active'}
    if note:r['note']=note
    rows.append(r)

def settle_lines(s,o,rows):
    tr=Decimal('0'); total=o['total']; pin=o['point_in']; event=o['event']
    for wt,dont in [('pass_line',False),('dont_pass',True)]:
        a=s['bets'].get(wt,Decimal('0'))
        if a<=0:continue
        decided=True
        if pin is None:
            if not dont:
                if total in (7,11): ret,status=craps.to_one(a,1),'win'
                elif total in (2,3,12): ret,status=Decimal('0'),'lose'
                else: decided=False
            else:
                if total in (2,3):ret,status=craps.to_one(a,1),'win'
                elif total==12:ret,status=a,'push'
                elif total in (7,11):ret,status=Decimal('0'),'lose'
                else:decided=False
        else:
            if event not in ('point_hit','seven_out'):decided=False
            elif (event=='seven_out')==dont:ret,status=craps.to_one(a,1),'win'
            else:ret,status=Decimal('0'),'lose'
        if not decided: result(rows,wt,a,0,'active','Point established' if pin is None else None); continue
        tr+=ret; result(rows,wt,a,ret,status); s['bets'].pop(wt,None)
    if pin in POINTS:
        for wt,dont in [('pass_odds',False),('dont_pass_odds',True)]:
            a=s['bets'].get(wt,Decimal('0'))
            if a<=0:continue
            if event not in ('point_hit','seven_out'):result(rows,wt,a,0,'active');continue
            won=(event=='seven_out') if dont else (event=='point_hit'); ret=craps.to_one(a,craps.DONT_ODDS[pin] if dont else craps.PASS_ODDS[pin]) if won else Decimal('0')
            tr+=ret; result(rows,wt,a,ret,'win' if won else 'lose'); s['bets'].pop(wt,None)
    return tr

def settle_come_points(s,o,rows):
    tr=Decimal('0'); total=o['total']
    for n in POINTS:
        k=str(n)
        for bucket,ob,dont in [('come','come_odds',False),('dont_come','dont_come_odds',True)]:
            a=s[bucket][k]; odds=s[ob][k]
            if a<=0 and odds<=0:continue
            if total not in (n,7):
                if a>0:result(rows,f'{bucket}_point_{n}',a,0,'active')
                if odds>0:result(rows,f'{ob}_{n}',odds,0,'active','OFF' if not working(s,f'{ob}_{n}') else None)
                continue
            won=(total==7) if dont else (total==n)
            if a>0:
                ret=craps.to_one(a,1) if won else Decimal('0'); tr+=ret; result(rows,f'{bucket}_point_{n}',a,ret,'win' if won else 'lose'); s[bucket][k]=Decimal('0')
            if odds>0:
                wt=f'{ob}_{n}'
                if working(s,wt):
                    ret=craps.to_one(odds,craps.DONT_ODDS[n] if dont else craps.PASS_ODDS[n]) if won else Decimal('0'); tr+=ret; result(rows,wt,odds,ret,'win' if won else 'lose'); s[ob][k]=Decimal('0')
                else: result(rows,wt,odds,0,'active','OFF')
    return tr

def settle_new_come(s,o,rows):
    tr=Decimal('0'); total=o['total']
    for wt,bucket,dont in [('come','come',False),('dont_come','dont_come',True)]:
        a=s['bets'].get(wt,Decimal('0'))
        if a<=0:continue
        if not dont:
            if total in (7,11):ret,status=craps.to_one(a,1),'win'
            elif total in (2,3,12):ret,status=Decimal('0'),'lose'
            else:s[bucket][str(total)]+=a;s['bets'].pop(wt,None);result(rows,wt,a,0,'active',f'Moved to Come Point {total}');continue
        else:
            if total in (2,3):ret,status=craps.to_one(a,1),'win'
            elif total==12:ret,status=a,'push'
            elif total in (7,11):ret,status=Decimal('0'),'lose'
            else:s[bucket][str(total)]+=a;s['bets'].pop(wt,None);result(rows,wt,a,0,'active',f'Moved to Come Point {total}');continue
        tr+=ret;result(rows,wt,a,ret,status);s['bets'].pop(wt,None)
    return tr

def settle_persistent(s,o,rows):
    tr=Decimal('0'); total=o['total']; hard=o['is_hard']
    for wt,a in list(s['bets'].items()):
        if not any(wt.startswith(p) for p in ('place_','buy_','lay_','hard_')):continue
        if not working(s,wt):result(rows,wt,a,0,'active','OFF');continue
        n=int(wt.split('_')[1]); decided=False;won=False;odds=Decimal('0')
        if wt.startswith('place_'):decided=total in (n,7);won=total==n;odds=craps.PLACE_PAY[n]
        elif wt.startswith('buy_'):decided=total in (n,7);won=total==n;odds=craps.BUY_PAY[n]
        elif wt.startswith('lay_'):decided=total in (n,7);won=total==7;odds=craps.LAY_PAY[n]
        else:decided=total==7 or total==n;won=total==n and hard;odds=craps.HARD_PAY[n]
        if not decided:result(rows,wt,a,0,'active');continue
        if won and (
            wt.startswith('place_')
            or wt.startswith('buy_')
            or wt.startswith('lay_')
        ):
            # Place / Buy / Lay remain on the table after a win.
            # Only the profit is returned because the original stake
            # remains committed in state.
            ret = a * odds
            tr += ret
            result(rows, wt, a, ret, 'win')
            continue

        ret = craps.to_one(a, odds) if won else Decimal('0')
        tr += ret
        result(rows, wt, a, ret, 'win' if won else 'lose')
        s['bets'].pop(wt, None)
        s['working'].pop(wt, None)
    return tr

def settle_one_roll(s,o,rows):
    tr=Decimal('0')
    for wt,a in list(s['bets'].items()):
        if wt not in craps.ONE_ROLL:continue
        ret=craps.one_roll_return(wt,a,o);tr+=ret;result(rows,wt,a,ret,'win' if ret>0 else 'lose');s['bets'].pop(wt,None)
    return tr

def roll(bets,raw_state=None,forced_dice=None):
    s=load(raw_state); point_before=s['point']; outlay,vig=add_bets(s,bets)
    o=craps.resolve(point_before) if forced_dice is None else craps.outcome_from_dice(forced_dice[0],forced_dice[1],point_before)
    rows=[];tr=Decimal('0')
    tr+=settle_come_points(s,o,rows);tr+=settle_lines(s,o,rows);tr+=settle_new_come(s,o,rows);tr+=settle_persistent(s,o,rows);tr+=settle_one_roll(s,o,rows)
    s['point']=o['point_out']

    # Don't Pass / Don't Come removal restrictions apply only
    # to the current point cycle.  Once an established point
    # ends, the next roll begins a fresh Come Out cycle and
    # those replacement locks no longer apply.
    if (
        point_before is not None
        and o['point_out'] is None
    ):
        s['dont_pass_replacement_locked']=False
        s['dont_come_replacement_locked']=False

    active=sum(s['bets'].values(),Decimal('0'))+sum((sum(s[b].values(),Decimal('0')) for b in ('come','dont_come','come_odds','dont_come_odds')),Decimal('0'))
    return {'game':'craps','outcome':o,'results':rows,'total_wager':float(outlay),'new_wager':float(outlay),'vigorish':float(vig),'total_return':float(tr),'net':float(tr-outlay),'active_stake':float(active),'state':plain(s)}
