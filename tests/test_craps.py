import unittest
from decimal import Decimal

from game import craps
from game import craps_engine


class TestStatefulCraps(unittest.TestCase):

    def roll(self, bets=(), state=None, dice=(3, 3)):
        return craps_engine.roll(bets, state, forced_dice=dice)

    def result(self, out, wager):
        return next(r for r in out["results"] if r["wager_type"] == wager)

    def test_come_out_natural_pass_wins(self):
        out = self.roll([("pass_line", 100)], dice=(3, 4))
        self.assertEqual(self.result(out, "pass_line")["return"], 200.0)
        self.assertIsNone(out["state"]["point"])

    def test_come_out_craps_pass_loses(self):
        out = self.roll([("pass_line", 100)], dice=(1, 2))
        self.assertEqual(self.result(out, "pass_line")["return"], 0.0)

    def test_dont_pass_wins_on_two_or_three(self):
        for dice in ((1,1), (1,2)):
            with self.subTest(dice=dice):
                out = self.roll([("dont_pass", 100)], dice=dice)
                self.assertEqual(self.result(out, "dont_pass")["return"], 200.0)

    def test_dont_pass_pushes_on_twelve(self):
        out = self.roll([("dont_pass", 100)], dice=(6,6))
        self.assertEqual(self.result(out, "dont_pass")["return"], 100.0)
        self.assertTrue(self.result(out, "dont_pass")["push"])

    def test_point_is_established_and_pass_stays_active(self):
        out = self.roll([("pass_line", 100)], dice=(3,3))
        self.assertEqual(out["state"]["point"], 6)
        self.assertEqual(out["state"]["bets"]["pass_line"], 100.0)
        self.assertTrue(self.result(out, "pass_line")["active"])

    def test_pass_line_wins_when_point_repeats(self):
        first = self.roll([("pass_line", 100)], dice=(3,3))
        second = self.roll([], first["state"], dice=(2,4))
        self.assertEqual(self.result(second, "pass_line")["return"], 200.0)
        self.assertIsNone(second["state"]["point"])

    def test_pass_line_loses_on_seven_out(self):
        first = self.roll([("pass_line", 100)], dice=(3,3))
        second = self.roll([], first["state"], dice=(3,4))
        self.assertEqual(self.result(second, "pass_line")["return"], 0.0)
        self.assertIsNone(second["state"]["point"])

    def test_dont_pass_wins_on_seven_out(self):
        first = self.roll([("dont_pass", 100)], dice=(2,3))
        second = self.roll([], first["state"], dice=(3,4))
        self.assertEqual(self.result(second, "dont_pass")["return"], 200.0)

    def test_come_requires_table_point(self):
        with self.assertRaises(ValueError):
            self.roll([("come", 100)], dice=(2,3))

    def test_come_moves_to_come_point(self):
        first = self.roll([("pass_line", 100)], dice=(3,3))
        second = self.roll([("come", 100)], first["state"], dice=(2,3))
        self.assertEqual(second["state"]["come"]["5"], 100.0)
        self.assertEqual(self.result(second, "come")["status"], "active")

    def test_come_point_wins_when_repeated(self):
        first = self.roll([("pass_line", 100)], dice=(3,3))
        second = self.roll([("come", 100)], first["state"], dice=(2,3))
        third = self.roll([], second["state"], dice=(1,4))
        self.assertEqual(self.result(third, "come_point_5")["return"], 200.0)
        self.assertEqual(third["state"]["come"]["5"], 0.0)

    def test_come_point_loses_on_seven(self):
        first = self.roll([("pass_line", 100)], dice=(3,3))
        second = self.roll([("come", 100)], first["state"], dice=(2,3))
        third = self.roll([], second["state"], dice=(3,4))
        self.assertEqual(self.result(third, "come_point_5")["return"], 0.0)

    def test_dont_come_moves_to_come_point_and_wins_on_seven(self):
        first = self.roll([("pass_line", 100)], dice=(3,3))
        second = self.roll([("dont_come", 100)], first["state"], dice=(2,3))
        third = self.roll([], second["state"], dice=(3,4))
        self.assertEqual(self.result(third, "dont_come_point_5")["return"], 200.0)

    def test_pass_odds_true_odds(self):
        cases = {
            4: ((2,2), 300.0),
            5: ((2,3), 250.0),
            6: ((3,3), 220.0),
            8: ((4,4), 220.0),
            9: ((4,5), 250.0),
            10: ((5,5), 300.0),
        }
        for point, (dice, expected) in cases.items():
            with self.subTest(point=point):
                state = craps_engine.new_state()
                state["point"] = point
                state["bets"]["pass_line"] = Decimal("100")
                out = self.roll([("pass_odds", 100)], state, dice=dice)
                self.assertEqual(self.result(out, "pass_odds")["return"], expected)

    def test_dont_pass_odds_true_odds_on_seven(self):
        cases = {4:150.0, 5:166.66666666666666, 6:183.33333333333334,
                 8:183.33333333333334, 9:166.66666666666666, 10:150.0}
        for point, expected in cases.items():
            with self.subTest(point=point):
                state = craps_engine.new_state()
                state["point"] = point
                state["bets"]["dont_pass"] = Decimal("100")
                out = self.roll([("dont_pass_odds", 100)], state, dice=(3,4))
                self.assertAlmostEqual(self.result(out, "dont_pass_odds")["return"], expected)

    def test_place_bet_persists_until_number_or_seven(self):
        state = craps_engine.new_state()
        state["point"] = 5

        # Roll 4:
        # does not hit Point 5,
        # does not hit Place 6,
        # and is not a seven.
        first = self.roll(
            [("place_6", 60)],
            state,
            dice=(2, 2),
        )

        place = self.result(
            first,
            "place_6",
        )

        self.assertTrue(
            place["active"]
        )

        self.assertEqual(
            first["state"]["bets"]["place_6"],
            60.0,
        )

        self.assertEqual(
            first["state"]["point"],
            5,
        )

        # Now roll hard 6.
        second = self.roll(
            [],
            first["state"],
            dice=(3, 3),
        )

        self.assertEqual(
            self.result(
                second,
                "place_6",
            )["return"],
            130.0,
        )

    def test_place_is_off_on_come_out_by_default(self):
        out = self.roll([("place_6", 60)], dice=(3,3))
        self.assertTrue(self.result(out, "place_6")["active"])
        self.assertEqual(self.result(out, "place_6")["note"], "OFF")

    def test_lay_is_working_on_come_out_by_default(self):
        out = self.roll([("lay_4", 100)], dice=(3,4))
        self.assertEqual(self.result(out, "lay_4")["return"], 150.0)

    def test_hardway_wins_hard_and_loses_easy(self):
        state = craps_engine.new_state()
        state["point"] = 5
        hard = self.roll([("hard_6", 100)], state, dice=(3,3))
        self.assertEqual(self.result(hard, "hard_6")["return"], 1000.0)

        state = craps_engine.new_state()
        state["point"] = 5
        easy = self.roll([("hard_6", 100)], state, dice=(1,5))
        self.assertEqual(self.result(easy, "hard_6")["return"], 0.0)

    def test_buy_vig_is_five_percent_of_wager(self):
        self.assertEqual(craps.buy_vig(100), Decimal("5.00"))
        state = craps_engine.new_state()
        state["point"] = 5
        out = self.roll([("buy_4", 100)], state, dice=(2,3))
        self.assertEqual(out["vigorish"], 5.0)
        self.assertEqual(out["new_wager"], 105.0)

    def test_lay_vig_is_five_percent_of_possible_win(self):
        self.assertEqual(craps.lay_vig(100, 4), Decimal("2.500"))
        self.assertEqual(craps.lay_vig(100, 6), Decimal(100) * Decimal(5) / Decimal(6) * Decimal("0.05"))

    def test_field_payouts(self):
        for dice, expected in (((1,1),300.0), ((6,6),300.0), ((1,2),200.0), ((4,5),200.0)):
            with self.subTest(dice=dice):
                out = self.roll([("field", 100)], dice=dice)
                self.assertEqual(self.result(out, "field")["return"], expected)

    def test_horn_requires_four_units(self):
        with self.assertRaises(ValueError):
            self.roll([("horn", 101)], dice=(1,1))

    def test_horn_pays_only_winning_leg_return(self):
        out = self.roll([("horn", 100)], dice=(1,1))
        self.assertEqual(self.result(out, "horn")["return"], 775.0)

    def test_horn_high_requires_five_units(self):
        with self.assertRaises(ValueError):
            self.roll([("horn_high_12", 101)], dice=(6,6))

    def test_horn_high_selected_number_has_two_winning_units(self):
        out = self.roll([("horn_high_12", 100)], dice=(6,6))
        self.assertEqual(self.result(out, "horn_high_12")["return"], 1240.0)

    def test_take_down_place_refunds_stake(self):
        state = craps_engine.new_state()
        state["point"] = 5
        state["bets"]["place_6"] = Decimal("60")
        out = craps_engine.action(state, "place_6", "take_down")
        self.assertEqual(out["refund"], 60.0)
        self.assertNotIn("place_6", out["state"]["bets"])

    def test_pass_line_cannot_be_taken_down(self):
        state = craps_engine.new_state()
        state["bets"]["pass_line"] = Decimal("100")
        with self.assertRaises(ValueError):
            craps_engine.action(state, "pass_line", "take_down")

    def test_on_off_override(self):
        state = craps_engine.new_state()
        state["bets"]["hard_6"] = Decimal("100")
        off = craps_engine.action(state, "hard_6", "off")
        self.assertFalse(off["state"]["working"]["hard_6"])
        on = craps_engine.action(off["state"], "hard_6", "on")
        self.assertTrue(on["state"]["working"]["hard_6"])


if __name__ == "__main__":
    unittest.main()
