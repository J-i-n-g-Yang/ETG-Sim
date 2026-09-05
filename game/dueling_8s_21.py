"""Dueling 8's 21+ (MBS Version 2) rules/math layer."""
import random
from decimal import Decimal

RANKS = ("A","2","3","4","5","6","7","8","9","J","Q","K")
SUITS = ("S","H","D","C")
MAX_SPLIT_HANDS = 4
SUPERB_8_ODDS = {
    "two_eights": Decimal("3"), "three_eights": Decimal("8"),
    "four_eights": Decimal("800"), "four_spade_eights": Decimal("8000"),
}
TWENTY_ONE_PLUS_ODDS = {
    3: Decimal("2"), 4: Decimal("3"), 5: Decimal("8"),
    6: Decimal("35"), 7: Decimal("80"), 8: Decimal("800"),
}

def D(v): return Decimal(str(v))

def card(rank, suit, permanent=False):
    rank, suit = str(rank).upper(), str(suit).upper()
    if rank not in RANKS: raise ValueError(f"Invalid rank: {rank}")
    if suit not in SUITS: raise ValueError(f"Invalid suit: {suit}")
    c = {"rank": rank, "suit": suit}
    if permanent: c["permanent"] = True
    return c

def permanent_eight():
    return card("8", "S", permanent=True)

def make_shoe(decks=6, shuffle=True, rng=None):
    decks = int(decks)
    if not 3 <= decks <= 8:
        raise ValueError("Dueling 8's 21+ uses 3 to 8 decks")
    shoe = [card(r,s) for _ in range(decks) for s in SUITS for r in RANKS]
    if shuffle: (rng or random).shuffle(shoe)
    return shoe

def card_value(rank):
    rank = str(rank).upper()
    if rank == "A": return 11
    if rank in ("J","Q","K"): return 10
    if rank in RANKS: return int(rank)
    raise ValueError(f"Invalid rank: {rank}")

def hand_total(cards):
    total = sum(card_value(c["rank"]) for c in cards)
    aces = sum(str(c["rank"]).upper() == "A" for c in cards)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def is_soft(cards):
    raw = sum(card_value(c["rank"]) for c in cards)
    aces = sum(str(c["rank"]).upper() == "A" for c in cards)
    while raw > 21 and aces:
        raw -= 10
        aces -= 1
    return aces > 0 and raw <= 21

def is_bust(cards): return hand_total(cards) > 21
def dealer_should_hit(cards): return hand_total(cards) <= 16

def play_dealer(shoe, cards=None):
    hand = [dict(c) for c in (cards or [permanent_eight()])]
    while dealer_should_hit(hand):
        if not shoe: raise RuntimeError("Shoe exhausted")
        hand.append(shoe.pop(0))
    return hand

def initial_player_hand(drawn): return [permanent_eight(), dict(drawn)]
def initial_dealer_hand(): return [permanent_eight()]

def can_surrender(hand):
    return (not hand.get("from_split", False) and not hand.get("acted", False)
            and len(hand.get("cards", ())) == 2)

def can_split(hand, total_hands=1):
    cards = hand.get("cards", ())
    return (total_hands < MAX_SPLIT_HANDS and len(cards) == 2
            and all(str(c["rank"]).upper() == "8" for c in cards)
            and not hand.get("acted", False))

def double_amount_valid(amount, original_wager, table_minimum):
    return D(table_minimum) <= D(amount) <= D(original_wager)

def can_double(hand, table_minimum=1):
    return (len(hand.get("cards", ())) == 2 and not hand.get("acted", False)
            and hand_total(hand["cards"]) < 21
            and D(hand.get("stake",0)) >= D(table_minimum))

def surrender_return(wager): return D(wager) / Decimal("2")

def regular_result(player, dealer):
    p, d = hand_total(player), hand_total(dealer)
    if p > 21: return "lose"
    if d > 21 or p > d: return "win"
    if p < d: return "lose"
    return "push"

def regular_return(stake, result):
    stake = D(stake)
    if result == "win": return stake * 2
    if result == "push": return stake
    if result == "lose": return Decimal("0")
    raise ValueError(result)

def six_seven_eight_odds(cards, from_split=False):
    if from_split or len(cards) != 3: return None
    permanent = [c for c in cards if c.get("permanent") and c["rank"]=="8" and c["suit"]=="S"]
    if len(permanent) != 1: return None
    drawn = [c for c in cards if not c.get("permanent")]
    if sorted(c["rank"] for c in drawn) != ["6","7"]: return None
    return Decimal("5") if all(c["suit"]=="S" for c in drawn) else Decimal("1")

def six_seven_eight_bonus(wager, cards, from_split=False):
    odds = six_seven_eight_odds(cards, from_split)
    return Decimal("0") if odds is None else D(wager) * odds

def tie_on_18_wins(player, dealer):
    return hand_total(player) == 18 and hand_total(dealer) == 18

def tie_on_18_return(wager, player, dealer):
    return D(wager) * Decimal("9") if tie_on_18_wins(player,dealer) else Decimal("0")

def superb_eights_result(sequence):
    count, all_spades = 0, True
    for c in sequence:
        if str(c["rank"]).upper() != "8": break
        count += 1
        all_spades = all_spades and str(c["suit"]).upper()=="S"
    if count >= 4: return "four_spade_eights" if all_spades else "four_eights"
    if count == 3: return "three_eights"
    if count == 2: return "two_eights"
    return None

def superb_eights_return(wager, sequence):
    result = superb_eights_result(sequence)
    return Decimal("0") if result is None else D(wager)*(Decimal("1")+SUPERB_8_ODDS[result])

def twenty_one_plus_odds(dealer):
    return TWENTY_ONE_PLUS_ODDS.get(len(dealer)) if is_bust(dealer) else None

def twenty_one_plus_return(wager, dealer):
    odds = twenty_one_plus_odds(dealer)
    return Decimal("0") if odds is None else D(wager)*(Decimal("1")+odds)

def available_actions(hand, total_hands=1, table_minimum=1):
    cards = hand.get("cards", ())
    if hand.get("surrendered") or hand.get("status") in ("stood","bust","done"): return []
    total = hand_total(cards)
    if total >= 21: return ["stand"] if total == 21 else []
    actions = ["hit","stand"]
    if can_surrender(hand): actions.append("surrender")
    if can_split(hand,total_hands): actions.append("split")
    if can_double(hand,table_minimum): actions.append("double")
    return actions
