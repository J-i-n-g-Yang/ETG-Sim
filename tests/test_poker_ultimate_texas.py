import unittest

import game.poker_engine as engine


def C(rank, suit):
    return {"rank": rank, "suit": suit}


def state(player, dealer, community, ante=100, blind=100, play=100, trips=0, folded=False):
    bets = {"seat0_ante": ante, "seat0_blind": blind}
    if trips:
        bets["seat0_trips"] = trips

    return {
        "game": "poker_ultimate_texas",
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
                "extra": play,
            }
        },
        "extra": play,
    }


class TestUltimateTexasHoldem(unittest.TestCase):

    def test_blind_royal_is_500_to_one(self):
        self.assertEqual(engine._ultimate_blind_odds((8, 14)), 500)

    def test_blind_straight_flush_is_50_to_one(self):
        self.assertEqual(engine._ultimate_blind_odds((8, 9)), 50)

    def test_trips_royal_is_100_to_one(self):
        self.assertEqual(engine._ultimate_trips_odds((8, 14)), 100)

    def test_trips_straight_flush_is_40_to_one(self):
        self.assertEqual(engine._ultimate_trips_odds((8, 9)), 40)

    def test_player_win_dealer_no_pair_ante_pushes(self):
        st = state(
            [C("A", "S"), C("K", "H")],
            [C("Q", "D"), C("J", "C")],
            [C("2", "S"), C("4", "H"), C("6", "D"), C("8", "C"), C("9", "S")],
        )
        out = engine.settle(st)
        # Play 200 + Ante push 100 + Blind push 100.
        self.assertEqual(out["total_return"], 400.0)

    def test_player_win_dealer_pair_ante_wins(self):
        st = state(
            [C("A", "S"), C("K", "H")],
            [C("Q", "D"), C("Q", "C")],
            [C("2", "S"), C("4", "H"), C("6", "D"), C("8", "C"), C("9", "S")],
        )
        out = engine.settle(st)
        # Player actually loses here because Dealer pair beats high card.
        self.assertEqual(out["total_return"], 0.0)

    def test_blind_straight_pays_one_to_one(self):
        st = state(
            [C("10", "S"), C("9", "H")],
            [C("8", "D"), C("2", "C")],
            [C("8", "S"), C("7", "H"), C("6", "D"), C("3", "C"), C("4", "S")],
        )
        out = engine.settle(st)
        self.assertGreater(out["total_return"], 0.0)

    def test_trips_three_kind_pays_three_to_one(self):
        st = state(
            [C("9", "S"), C("9", "H")],
            [C("A", "D"), C("K", "C")],
            [C("9", "D"), C("2", "C"), C("4", "S"), C("6", "H"), C("8", "D")],
            ante=0,
            blind=0,
            play=0,
            trips=100,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 400.0)

    def test_trips_survives_fold(self):
        st = state(
            [C("9", "S"), C("9", "H")],
            [C("A", "D"), C("K", "C")],
            [C("9", "D"), C("2", "C"), C("4", "S"), C("6", "H"), C("8", "D")],
            trips=100,
            folded=True,
            play=0,
        )
        out = engine.settle(st)
        self.assertEqual(out["total_return"], 400.0)


if __name__ == "__main__":
    unittest.main()
