import unittest

import game.poker_engine as engine
from game.poker_base import dealer_qualifies_singapore


def C(rank, suit):
    return {"rank": rank, "suit": suit}


def state(player, dealer, ante=100, bet=200, folded=False):
    return {
        "game": "poker_singapore_stud",
        "dealer": dealer,
        "community": [],
        "active": [0],
        "bets": {"0": {"seat0_ante": ante}},
        "hands": {
            "0": {
                "cards": player,
                "ante": ante,
                "blind_mode": False,
                "side": {},
                "folded": folded,
                "actions": [],
                "extra": bet,
            }
        },
        "extra": bet,
    }


class TestSingaporeStud(unittest.TestCase):

    def test_dealer_qualifies_with_ace_king_high(self):
        self.assertTrue(
            dealer_qualifies_singapore([
                C("A", "S"), C("K", "H"), C("9", "D"), C("6", "C"), C("3", "S")
            ])
        )

    def test_dealer_does_not_qualify_with_ace_queen_high(self):
        self.assertFalse(
            dealer_qualifies_singapore([
                C("A", "S"), C("Q", "H"), C("9", "D"), C("6", "C"), C("3", "S")
            ])
        )

    def test_dealer_no_hand_ante_wins_bet_pushes(self):
        st = state(
            [C("K", "S"), C("K", "H"), C("8", "D"), C("6", "C"), C("2", "S")],
            [C("A", "S"), C("Q", "H"), C("9", "D"), C("6", "H"), C("3", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 400.0)

    def test_regular_pair_win_bet_pays_one_to_one(self):
        st = state(
            [C("K", "S"), C("K", "H"), C("8", "D"), C("6", "C"), C("2", "S")],
            [C("Q", "S"), C("Q", "H"), C("9", "D"), C("6", "H"), C("3", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 600.0)

    def test_royal_flush_bet_pays_250_to_one(self):
        st = state(
            [C("A", "S"), C("K", "S"), C("Q", "S"), C("J", "S"), C("10", "S")],
            [C("K", "H"), C("K", "D"), C("9", "C"), C("6", "H"), C("3", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 50400.0)

    def test_straight_flush_bet_pays_50_to_one(self):
        st = state(
            [C("9", "S"), C("8", "S"), C("7", "S"), C("6", "S"), C("5", "S")],
            [C("K", "H"), C("K", "D"), C("9", "C"), C("6", "H"), C("3", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 10400.0)

    def test_equal_hand_pushes_ante_and_bet(self):
        cards1 = [C("A", "S"), C("K", "H"), C("9", "D"), C("6", "C"), C("3", "S")]
        cards2 = [C("A", "H"), C("K", "D"), C("9", "C"), C("6", "S"), C("3", "H")]
        out = engine.settle(state(cards1, cards2))
        self.assertEqual(out["total_return"], 300.0)


if __name__ == "__main__":
    unittest.main()
