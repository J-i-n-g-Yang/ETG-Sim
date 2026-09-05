import unittest
from decimal import Decimal

import game.poker_engine as engine
from game.poker_base import rank3, dealer_qualifies_threecard


def C(rank, suit):
    return {"rank": rank, "suit": suit}


def state(player, dealer, ante=100, play=100, pair_plus=0, six_card_bonus=0, folded=False):
    bets = {"seat0_ante": ante}
    if pair_plus:
        bets["seat0_pair_plus"] = pair_plus
    if six_card_bonus:
        bets["seat0_six_card_bonus"] = six_card_bonus

    return {
        "game": "poker_three_card_xtreme",
        "dealer": dealer,
        "community": [],
        "active": [0],
        "bets": {"0": bets},
        "hands": {
            "0": {
                "cards": player,
                "ante": ante,
                "blind_mode": False,
                "side": bets,
                "folded": folded,
                "actions": [],
                "extra": play,
            }
        },
        "extra": play,
    }


class TestThreeCardPokerXtreme(unittest.TestCase):

    def test_three_card_rank_order(self):
        self.assertGreater(
            rank3([C("9", "H"), C("8", "H"), C("7", "H")]),
            rank3([C("8", "S"), C("8", "H"), C("8", "D")]),
        )
        self.assertGreater(
            rank3([C("8", "S"), C("8", "H"), C("8", "D")]),
            rank3([C("9", "S"), C("8", "H"), C("7", "D")]),
        )

    def test_ace_2_3_is_low_straight(self):
        self.assertEqual(rank3([C("A", "S"), C("2", "H"), C("3", "D")]), (3, 3))

    def test_dealer_qualifies_with_queen_high(self):
        self.assertTrue(
            dealer_qualifies_threecard([C("Q", "S"), C("9", "H"), C("4", "D")])
        )

    def test_dealer_does_not_qualify_with_jack_high(self):
        self.assertFalse(
            dealer_qualifies_threecard([C("J", "S"), C("9", "H"), C("4", "D")])
        )

    def test_dealer_no_qualify_ante_wins_play_pushes(self):
        st = state(
            [C("K", "S"), C("9", "H"), C("4", "D")],
            [C("J", "S"), C("8", "H"), C("3", "D")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 300.0)

    def test_player_win_ante_and_play_both_pay_one_to_one(self):
        st = state(
            [C("K", "S"), C("K", "H"), C("4", "D")],
            [C("Q", "S"), C("9", "H"), C("4", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 400.0)

    def test_ante_bonus_straight_pays_one_to_one_profit(self):
        st = state(
            [C("6", "S"), C("5", "H"), C("4", "D")],
            [C("Q", "S"), C("9", "H"), C("4", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 500.0)

    def test_ante_bonus_three_kind_pays_four_to_one_profit(self):
        st = state(
            [C("8", "S"), C("8", "H"), C("8", "D")],
            [C("Q", "S"), C("9", "H"), C("4", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 800.0)

    def test_ante_bonus_straight_flush_pays_five_to_one_profit(self):
        st = state(
            [C("8", "S"), C("7", "S"), C("6", "S")],
            [C("Q", "H"), C("9", "D"), C("4", "C")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 900.0)

    def test_pair_plus_straight_flush_pays_40_to_one(self):
        st = state(
            [C("8", "S"), C("7", "S"), C("6", "S")],
            [C("Q", "H"), C("9", "D"), C("4", "C")],
            ante=0,
            play=0,
            pair_plus=100,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 4100.0)

    def test_pair_plus_pair_pays_one_to_one(self):
        st = state(
            [C("8", "S"), C("8", "H"), C("3", "D")],
            [C("Q", "H"), C("9", "D"), C("4", "C")],
            ante=0,
            play=0,
            pair_plus=100,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 200.0)

    def test_pair_plus_survives_fold(self):
        st = state(
            [C("8", "S"), C("8", "H"), C("3", "D")],
            [C("Q", "H"), C("9", "D"), C("4", "C")],
            ante=100,
            play=0,
            pair_plus=100,
            folded=True,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 200.0)

    def test_six_card_bonus_royal_flush_pays_500_to_one(self):
        st = state(
            [C("A", "S"), C("K", "S"), C("Q", "S")],
            [C("J", "S"), C("10", "S"), C("2", "H")],
            ante=0,
            play=0,
            six_card_bonus=100,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 50100.0)

    def test_six_card_bonus_straight_flush_pays_100_to_one(self):
        st = state(
            [C("9", "S"), C("8", "S"), C("7", "S")],
            [C("6", "S"), C("5", "S"), C("2", "H")],
            ante=0,
            play=0,
            six_card_bonus=100,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 10100.0)


if __name__ == "__main__":
    unittest.main()
