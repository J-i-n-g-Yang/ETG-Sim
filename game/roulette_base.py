from decimal import Decimal

RED_NUMBERS=frozenset({1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36})
BLACK_NUMBERS=frozenset(set(range(1,37))-RED_NUMBERS)
STANDARD_ODDS={"straight":Decimal("35"),"split":Decimal("17"),"street":Decimal("11"),"corner":Decimal("8"),"sixline":Decimal("5"),"column":Decimal("2"),"dozen":Decimal("2"),"outside":Decimal("1")}
def to_decimal(v): return Decimal(str(v))
def win_return(a,o): return to_decimal(a)*(to_decimal(o)+1)
def lose_return(): return Decimal("0")
def normalise_pocket(v):
    if isinstance(v,int):
        if 0<=v<=36:return v
        raise ValueError("Invalid roulette pocket")
    v=str(v).strip().upper()
    if v in {"00","S"}:return v
    try:n=int(v)
    except ValueError as e:raise ValueError("Invalid roulette pocket") from e
    if 0<=n<=36:return n
    raise ValueError("Invalid roulette pocket")
def number_at(c,r):
    if not 0<=c<=11:raise ValueError("Invalid roulette column")
    if r==0:return 3*(c+1)
    if r==1:return 3*(c+1)-1
    if r==2:return 3*(c+1)-2
    raise ValueError("Invalid roulette row")
def standard_splits():
    s=set()
    for c in range(12):
        t,m,b=[number_at(c,r) for r in range(3)]
        s|={tuple(sorted((t,m))),tuple(sorted((m,b)))}
    for c in range(11):
        for r in range(3):s.add(tuple(sorted((number_at(c,r),number_at(c+1,r)))))
    return frozenset(s)
STANDARD_SPLITS=standard_splits()
STANDARD_STREETS=frozenset(tuple(sorted(number_at(c,r) for r in range(3))) for c in range(12))
STANDARD_CORNERS=frozenset(tuple(sorted((number_at(c,r),number_at(c,r+1),number_at(c+1,r),number_at(c+1,r+1)))) for c in range(11) for r in (0,1))
STANDARD_SIXLINES=frozenset(tuple(sorted(number_at(cc,r) for cc in (c,c+1) for r in range(3))) for c in range(11))
OUT=frozenset({"red","black","odd","even","low","high"}); DOZ=frozenset({"dozen_1","dozen_2","dozen_3"}); COL=frozenset({"column_1","column_2","column_3"})
def parse_number_wager(w,p):
    x=p+"_"
    if not str(w).startswith(x):return None
    try:return tuple(normalise_pocket(q) for q in str(w)[len(x):].split("_"))
    except ValueError:return None
def _extra(vals,extras): return bool(extras) and any(frozenset(vals)==frozenset(x) for x in extras)
def validate_standard_wager(w,allowed_straight_pockets,extra_splits=None,extra_streets=None,extra_corners=None,extra_sixlines=None):
    w=str(w)
    if w in OUT|DOZ|COL:return True
    v=parse_number_wager(w,"straight")
    if v is not None:return len(v)==1 and v[0] in allowed_straight_pockets
    for p,std,ex in (("split",STANDARD_SPLITS,extra_splits),("street",STANDARD_STREETS,extra_streets),("corner",STANDARD_CORNERS,extra_corners),("sixline",STANDARD_SIXLINES,extra_sixlines)):
        v=parse_number_wager(w,p)
        if v is not None:
            canon=tuple(sorted(v)) if all(isinstance(x,int) for x in v) else None
            return (canon in std if canon else False) or _extra(v,ex)
    return False
def settle_standard_wager(w,a,o):
    a=to_decimal(a);o=normalise_pocket(o)
    if w in OUT:
        ok=o not in (0,"00","S") and ((w=="red" and o in RED_NUMBERS) or (w=="black" and o in BLACK_NUMBERS) or (w=="odd" and o%2) or (w=="even" and o%2==0) or (w=="low" and 1<=o<=18) or (w=="high" and 19<=o<=36))
        return win_return(a,1) if ok else lose_return()
    if w in DOZ:
        ok=isinstance(o,int) and ((w=="dozen_1" and 1<=o<=12) or (w=="dozen_2" and 13<=o<=24) or (w=="dozen_3" and 25<=o<=36))
        return win_return(a,2) if ok else lose_return()
    if w in COL:
        ok=isinstance(o,int) and 1<=o<=36 and ((w=="column_1" and o%3==1) or (w=="column_2" and o%3==2) or (w=="column_3" and o%3==0))
        return win_return(a,2) if ok else lose_return()
    for p,n in (("straight",1),("split",2),("street",3),("corner",4),("sixline",6)):
        v=parse_number_wager(w,p)
        if v is not None:return win_return(a,STANDARD_ODDS[p]) if len(v)==n and o in v else lose_return()
    raise ValueError(f"Unknown roulette wager: {w}")
