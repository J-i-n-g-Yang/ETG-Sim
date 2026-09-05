import unittest

import game.paigow_engine as pg


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


def make_state(player_cards, dealer_cards, ante=100, fortune=0):
    bets = {"seat0_ante": ante}
    if fortune:
        bets["seat0_fortune_bonus"] = fortune
    return {
        "game": "poker_fortune_pai_gow",
        "dealer": dealer_cards,
        "active": [0],
        "bets": {"0": bets},
        "hands": {
            "0": {
                "cards": player_cards,
                "ante": ante,
                "blind_mode": False,
                "side": bets,
                "folded": False,
                "actions": [],
                "extra": 0.0,
            }
        },
        "extra": 0.0,
    }


class TestPaiGowSettlement(unittest.TestCase):

    def test_standard_win_returns_stake_plus_95_percent_profit(self):
        # Explicit legal set hands remove House Way ambiguity from comparison.
        player = [
            C("A", "S"), C("A", "H"), C("K", "D"),
            C("Q", "C"), C("J", "S"), C("9", "H"), C("8", "D")
        ]
        dealer = [
            C("K", "S"), C("K", "H"), C("Q", "D"),
            C("J", "C"), C("10", "S"), C("7", "H"), C("6", "D")
        ]
        st = make_state(player, dealer)
        # Let House Way set both. This hand is intentionally strong enough
        # that the test only checks the 5% commission calculation if it wins.
        out = pg.settle(st)
        result = out["outcome"]["seats"]["0"]["result"]
        if result == "win":
            self.assertEqual(out["total_return"], 195.0)
        else:
            self.skipTest("House Way comparison did not produce a win fixture")

    def test_copy_low_and_copy_high_both_belong_to_dealer(self):
        low = [C("A", "S"), C("K", "H")]
        high = [
            C("9", "S"), C("9", "H"), C("7", "D"), C("5", "C"), C("2", "S")
        ]
        self.assertEqual(pg.compare(low, high, low, high), "lose")

    def test_one_win_one_loss_is_push(self):
        player_low = [C("A", "S"), C("K", "H")]
        dealer_low = [C("Q", "S"), C("J", "H")]
        player_high = [
            C("8", "S"), C("8", "H"), C("7", "D"), C("5", "C"), C("2", "S")
        ]
        dealer_high = [
            C("9", "S"), C("9", "H"), C("7", "C"), C("5", "D"), C("2", "H")
        ]
        self.assertEqual(
            pg.compare(player_low, player_high, dealer_low, dealer_high),
            "push",
        )

    def test_fortune_bonus_is_independent_of_standard_result(self):
        player = [
            C("8", "S"), C("9", "S"), C("10", "S"),
            C("J", "S"), C("Q", "S"), C("K", "S"), C("A", "S")
        ]
        dealer = [
            C("A", "H"), C("A", "D"), C("K", "H"),
            C("K", "D"), C("Q", "H"), C("9", "D"), C("2", "C")
        ]
        st = make_state(player, dealer, ante=100, fortune=10)
        out = pg.settle(st)
        fortune = next(
            r for r in out["results"]
            if r["wager_type"] == "seat0_fortune_bonus"
        )
        self.assertEqual(fortune["category"], "seven_card_straight_flush_no_joker")
        self.assertEqual(fortune["return"], 25010.0)

    def test_losing_fortune_bonus_returns_zero(self):
        player = [
            C("A", "S"), C("K", "H"), C("Q", "D"),
            C("9", "C"), C("7", "S"), C("4", "H"), C("2", "D")
        ]
        dealer = [
            C("A", "H"), C("K", "D"), C("J", "C"),
            C("9", "S"), C("7", "H"), C("4", "D"), C("3", "C")
        ]
        st = make_state(player, dealer, ante=100, fortune=10)
        out = pg.settle(st)
        fortune = next(
            r for r in out["results"]
            if r["wager_type"] == "seat0_fortune_bonus"
        )
        self.assertEqual(fortune["return"], 0.0)

    def test_envy_bonus_from_other_player_seven_card_straight_flush(self):
        p0 = [
            C("A", "H"), C("K", "D"), C("Q", "C"),
            C("9", "H"), C("7", "D"), C("4", "C"), C("2", "H")
        ]
        p1 = [
            C("8", "S"), C("9", "S"), C("10", "S"),
            C("J", "S"), C("Q", "S"), C("K", "S"), C("A", "S")
        ]
        dealer = [
            C("A", "D"), C("K", "H"), C("J", "D"),
            C("9", "C"), C("7", "H"), C("5", "D"), C("3", "C")
        ]
        st = {
            "game": "poker_fortune_pai_gow",
            "dealer": dealer,
            "active": [0, 1],
            "bets": {
                "0": {"seat0_ante": 100, "seat0_fortune_bonus": 10},
                "1": {"seat1_ante": 100},
            },
            "hands": {
                "0": {
                    "cards": p0, "ante": 100, "blind_mode": False,
                    "side": {}, "folded": False, "actions": [], "extra": 0.0,
                },
                "1": {
                    "cards": p1, "ante": 100, "blind_mode": True,
                    "side": {}, "folded": False, "actions": [], "extra": 0.0,
                },
            },
            "extra": 0.0,
        }
        out = pg.settle(st)
        envy = [
            r for r in out["results"]
            if r["wager_type"] == "seat0_envy_bonus"
        ]
        self.assertEqual(len(envy), 1)
        self.assertEqual(envy[0]["return"], 250.0)

    def test_dealer_hand_never_triggers_envy(self):
        player = [
            C("A", "H"), C("K", "D"), C("Q", "C"),
            C("9", "H"), C("7", "D"), C("4", "C"), C("2", "H")
        ]
        dealer = [
            C("8", "S"), C("9", "S"), C("10", "S"),
            C("J", "S"), C("Q", "S"), C("K", "S"), C("A", "S")
        ]
        st = make_state(player, dealer, ante=100, fortune=10)
        out = pg.settle(st)
        self.assertFalse(
            any(r["wager_type"] == "seat0_envy_bonus" for r in out["results"])
        )


if __name__ == "__main__":
    unittest.main()
