import unittest

import game.poker_engine as engine


def C(rank, suit):
    return {"rank": rank, "suit": suit}


def state(player, dealer, community, ante=100, extra=200, bonus=0, folded=False):
    bets = {"seat0_ante": ante}
    if bonus:
        bets["seat0_bonus"] = bonus

    return {
        "game": "poker_texas_bonus",
        "dealer": dealer,
        "community": community,
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
                "extra": extra,
            }
        },
        "extra": extra,
    }


class TestTexasHoldemBonus(unittest.TestCase):

    def test_bonus_categories(self):
        self.assertEqual(
            engine._texas_bonus_category(
                [C("A", "S"), C("A", "H")],
                [C("A", "D"), C("A", "C")],
            ),
            "AA_both",
        )
        self.assertEqual(
            engine._texas_bonus_category(
                [C("A", "S"), C("K", "S")],
                [C("9", "D"), C("8", "C")],
            ),
            "AK_suited",
        )
        self.assertEqual(
            engine._texas_bonus_category(
                [C("10", "S"), C("10", "H")],
                [C("9", "D"), C("8", "C")],
            ),
            "TT_22",
        )

    def test_bonus_aa_both_pays_1000_to_one(self):
        st = state(
            [C("A", "S"), C("A", "H")],
            [C("A", "D"), C("A", "C")],
            [C("2", "S"), C("4", "H"), C("6", "D"), C("8", "C"), C("9", "S")],
            ante=0,
            extra=0,
            bonus=100,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 100100.0)

    def test_bonus_loses_if_player_folds(self):
        st = state(
            [C("A", "S"), C("A", "H")],
            [C("9", "D"), C("8", "C")],
            [C("2", "S"), C("4", "H"), C("6", "D"), C("8", "D"), C("9", "S")],
            ante=100,
            extra=0,
            bonus=100,
            folded=True,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 0.0)

    def test_player_win_below_straight_ante_pushes_play_wins(self):
        st = state(
            [C("A", "S"), C("K", "H")],
            [C("Q", "D"), C("J", "C")],
            [C("2", "S"), C("4", "H"), C("6", "D"), C("8", "C"), C("9", "S")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 500.0)

    def test_player_win_with_straight_ante_and_play_win(self):
        st = state(
            [C("10", "S"), C("9", "H")],
            [C("A", "D"), C("2", "C")],
            [C("8", "S"), C("7", "H"), C("6", "D"), C("3", "C"), C("4", "S")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 600.0)

    def test_equal_final_hand_pushes(self):
        st = state(
            [C("2", "S"), C("3", "H")],
            [C("4", "D"), C("5", "C")],
            [C("A", "S"), C("K", "H"), C("Q", "D"), C("J", "C"), C("10", "S")],
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 300.0)


if __name__ == "__main__":
    unittest.main()
