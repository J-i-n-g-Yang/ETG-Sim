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
            70.0,
        )

    def test_place_bet_remains_after_win(self):
        state = craps_engine.new_state()
        state["point"] = 5

        first = self.roll(
            [("place_6", 60)],
            state,
            dice=(3, 3),
        )

        self.assertEqual(
            self.result(
                first,
                "place_6",
            )["return"],
            70.0,
        )

        self.assertEqual(
            first["state"]["bets"]["place_6"],
            60.0,
        )

        second = self.roll(
            [],
            first["state"],
            dice=(2, 3),
        )

        place = self.result(
            second,
            "place_6",
        )

        self.assertTrue(
            place["active"]
        )

        self.assertEqual(
            second["state"]["bets"]["place_6"],
            60.0,
        )

    def test_buy_bet_remains_after_win(self):
        state = craps_engine.new_state()
        state["point"] = 5

        first = self.roll(
            [("buy_4", 100)],
            state,
            dice=(2, 2),
        )

        self.assertEqual(
            self.result(
                first,
                "buy_4",
            )["return"],
            200.0,
        )

        self.assertEqual(
            first["state"]["bets"]["buy_4"],
            100.0,
        )

        second = self.roll(
            [],
            first["state"],
            dice=(2, 3),
        )

        buy = self.result(
            second,
            "buy_4",
        )

        self.assertTrue(
            buy["active"]
        )

        self.assertEqual(
            second["state"]["bets"]["buy_4"],
            100.0,
        )

    def test_lay_bet_remains_after_win(self):
        state = craps_engine.new_state()
        state["point"] = 5

        first = self.roll(
            [("lay_4", 100)],
            state,
            dice=(3, 4),
        )

        self.assertEqual(
            self.result(
                first,
                "lay_4",
            )["return"],
            50.0,
        )

        self.assertEqual(
            first["state"]["bets"]["lay_4"],
            100.0,
        )

        second = self.roll(
            [],
            first["state"],
            dice=(2, 3),
        )

        lay = self.result(
            second,
            "lay_4",
        )

        self.assertTrue(
            lay["active"]
        )

        self.assertEqual(
            second["state"]["bets"]["lay_4"],
            100.0,
        )

    def test_place_is_off_on_come_out_by_default(self):
        out = self.roll([("place_6", 60)], dice=(3,3))
        self.assertTrue(self.result(out, "place_6")["active"])
        self.assertEqual(self.result(out, "place_6")["note"], "OFF")

    def test_lay_is_working_on_come_out_by_default(self):
        out = self.roll([("lay_4", 100)], dice=(3,4))
        self.assertEqual(self.result(out, "lay_4")["return"], 50.0)

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

    def test_come_point_cannot_be_taken_down(self):
        state = craps_engine.new_state()
        state["point"] = 6
        state["come"]["5"] = Decimal("100")

        with self.assertRaises(ValueError):
            craps_engine.action(
                state,
                "come_point_5",
                "take_down",
            )

    def test_come_odds_can_be_taken_down(self):
        state = craps_engine.new_state()
        state["point"] = 6
        state["come"]["5"] = Decimal("100")
        state["come_odds"]["5"] = Decimal("75")

        out = craps_engine.action(
            state,
            "come_odds_5",
            "take_down",
        )

        self.assertEqual(
            out["refund"],
            75.0,
        )

        self.assertEqual(
            out["state"]["come"]["5"],
            100.0,
        )

        self.assertEqual(
            out["state"]["come_odds"]["5"],
            0.0,
        )

    def test_dont_come_odds_can_be_taken_down(self):
        state = craps_engine.new_state()
        state["point"] = 6
        state["dont_come"]["5"] = Decimal("100")
        state["dont_come_odds"]["5"] = Decimal("80")

        out = craps_engine.action(
            state,
            "dont_come_odds_5",
            "take_down",
        )

        self.assertEqual(
            out["refund"],
            80.0,
        )

        self.assertEqual(
            out["state"]["dont_come"]["5"],
            100.0,
        )

        self.assertEqual(
            out["state"]["dont_come_odds"]["5"],
            0.0,
        )

    def test_dont_come_point_take_down_refunds_flat_and_odds(self):
        state = craps_engine.new_state()
        state["point"] = 6
        state["dont_come"]["5"] = Decimal("100")
        state["dont_come_odds"]["5"] = Decimal("50")

        out = craps_engine.action(
            state,
            "dont_come_point_5",
            "take_down",
        )

        self.assertEqual(
            out["refund"],
            150.0,
        )

        self.assertEqual(
            out["state"]["dont_come"]["5"],
            0.0,
        )

        self.assertEqual(
            out["state"]["dont_come_odds"]["5"],
            0.0,
        )

    def test_dont_pass_cannot_be_replaced_after_take_down(self):
        state = craps_engine.new_state()

        state["bets"]["dont_pass"] = Decimal("100")

        removed = craps_engine.action(
            state,
            "dont_pass",
            "take_down",
        )

        self.assertEqual(
            removed["refund"],
            100.0,
        )

        with self.assertRaises(ValueError):
            self.roll(
                [("dont_pass", 100)],
                removed["state"],
                dice=(3, 4),
            )

    def test_dont_come_cannot_be_replaced_after_take_down(self):
        state = craps_engine.new_state()
        state["point"] = 6
        state["dont_come"]["5"] = Decimal("100")

        removed = craps_engine.action(
            state,
            "dont_come_point_5",
            "take_down",
        )

        self.assertEqual(
            removed["refund"],
            100.0,
        )

        with self.assertRaises(ValueError):
            self.roll(
                [("dont_come", 100)],
                removed["state"],
                dice=(2, 3),
            )

    def test_dont_pass_replacement_lock_clears_after_point_cycle(self):
        state = craps_engine.new_state()
        state["point"] = 6
        state["bets"]["dont_pass"] = Decimal("100")

        removed = craps_engine.action(
            state,
            "dont_pass",
            "take_down",
        )

        self.assertTrue(
            removed["state"]["dont_pass_replacement_locked"]
        )

        ended = self.roll(
            [],
            removed["state"],
            dice=(3, 4),
        )

        self.assertIsNone(
            ended["state"]["point"]
        )

        self.assertFalse(
            ended["state"]["dont_pass_replacement_locked"]
        )

        fresh = self.roll(
            [("dont_pass", 100)],
            ended["state"],
            dice=(2, 3),
        )

        self.assertEqual(
            fresh["state"]["bets"]["dont_pass"],
            100.0,
        )

    def test_dont_come_replacement_lock_clears_after_point_cycle(self):
        state = craps_engine.new_state()
        state["point"] = 6
        state["dont_come"]["5"] = Decimal("100")

        removed = craps_engine.action(
            state,
            "dont_come_point_5",
            "take_down",
        )

        self.assertTrue(
            removed["state"]["dont_come_replacement_locked"]
        )

        ended = self.roll(
            [],
            removed["state"],
            dice=(3, 4),
        )

        self.assertIsNone(
            ended["state"]["point"]
        )

        self.assertFalse(
            ended["state"]["dont_come_replacement_locked"]
        )

        fresh_point = self.roll(
            [("pass_line", 100)],
            ended["state"],
            dice=(4, 4),
        )

        fresh = self.roll(
            [("dont_come", 100)],
            fresh_point["state"],
            dice=(2, 3),
        )

        self.assertEqual(
            fresh["state"]["dont_come"]["5"],
            100.0,
        )

    def test_fresh_dont_pass_is_still_allowed(self):
        out = self.roll(
            [("dont_pass", 100)],
            dice=(2, 3),
        )

        self.assertEqual(
            out["state"]["point"],
            5,
        )

        self.assertEqual(
            out["state"]["bets"]["dont_pass"],
            100.0,
        )

    def test_fresh_dont_come_is_still_allowed(self):
        state = craps_engine.new_state()
        state["point"] = 6

        out = self.roll(
            [("dont_come", 100)],
            state,
            dice=(2, 3),
        )

        self.assertEqual(
            out["state"]["dont_come"]["5"],
            100.0,
        )


    def test_all_place_numbers_pay_correct_odds(self):
        cases = {
            4: ((2, 2), Decimal(9) / Decimal(5)),
            5: ((2, 3), Decimal(7) / Decimal(5)),
            6: ((3, 3), Decimal(7) / Decimal(6)),
            8: ((4, 4), Decimal(7) / Decimal(6)),
            9: ((4, 5), Decimal(7) / Decimal(5)),
            10: ((5, 5), Decimal(9) / Decimal(5)),
        }

        for number, (dice, odds) in cases.items():
            with self.subTest(number=number):
                state = craps_engine.new_state()
                state["point"] = 5

                amount = Decimal("60")

                out = self.roll(
                    [(f"place_{number}", amount)],
                    state,
                    dice=dice,
                )

                expected_profit = amount * odds

                self.assertAlmostEqual(
                    self.result(
                        out,
                        f"place_{number}",
                    )["return"],
                    float(expected_profit),
                )

                self.assertEqual(
                    out["state"]["bets"][f"place_{number}"],
                    float(amount),
                )

    def test_all_buy_numbers_pay_true_odds_and_remain(self):
        cases = {
            4: ((2, 2), Decimal("2")),
            5: ((2, 3), Decimal("1.5")),
            6: ((3, 3), Decimal("1.2")),
            8: ((4, 4), Decimal("1.2")),
            9: ((4, 5), Decimal("1.5")),
            10: ((5, 5), Decimal("2")),
        }

        for number, (dice, odds) in cases.items():
            with self.subTest(number=number):
                state = craps_engine.new_state()
                state["point"] = 5

                amount = Decimal("100")

                out = self.roll(
                    [(f"buy_{number}", amount)],
                    state,
                    dice=dice,
                )

                self.assertAlmostEqual(
                    self.result(
                        out,
                        f"buy_{number}",
                    )["return"],
                    float(amount * odds),
                )

                self.assertEqual(
                    out["state"]["bets"][f"buy_{number}"],
                    100.0,
                )

                self.assertEqual(
                    out["vigorish"],
                    5.0,
                )

    def test_all_lay_numbers_pay_true_odds_and_remain(self):
        cases = {
            4: Decimal("0.5"),
            5: Decimal(2) / Decimal(3),
            6: Decimal(5) / Decimal(6),
            8: Decimal(5) / Decimal(6),
            9: Decimal(2) / Decimal(3),
            10: Decimal("0.5"),
        }

        for number, odds in cases.items():
            with self.subTest(number=number):
                state = craps_engine.new_state()
                state["point"] = 5

                amount = Decimal("100")

                out = self.roll(
                    [(f"lay_{number}", amount)],
                    state,
                    dice=(3, 4),
                )

                self.assertAlmostEqual(
                    self.result(
                        out,
                        f"lay_{number}",
                    )["return"],
                    float(amount * odds),
                )

                self.assertEqual(
                    out["state"]["bets"][f"lay_{number}"],
                    100.0,
                )

                self.assertAlmostEqual(
                    out["vigorish"],
                    float(
                        amount
                        * odds
                        * Decimal("0.05")
                    ),
                )

    def test_all_hardway_payouts(self):
        cases = {
            4: ((2, 2), 800.0),
            6: ((3, 3), 1000.0),
            8: ((4, 4), 1000.0),
            10: ((5, 5), 800.0),
        }

        for number, (dice, expected) in cases.items():
            with self.subTest(number=number):
                state = craps_engine.new_state()
                state["point"] = 5

                out = self.roll(
                    [(f"hard_{number}", 100)],
                    state,
                    dice=dice,
                )

                self.assertEqual(
                    self.result(
                        out,
                        f"hard_{number}",
                    )["return"],
                    expected,
                )

    def test_one_roll_proposition_payouts(self):
        cases = [
            ("any_seven", (3, 4), 500.0),
            ("any_craps", (1, 1), 800.0),
            ("any_craps", (1, 2), 800.0),
            ("any_craps", (6, 6), 800.0),
            ("two_crap", (1, 1), 3100.0),
            ("three_crap", (1, 2), 1600.0),
            ("eleven", (5, 6), 1600.0),
            ("twelve_crap", (6, 6), 3100.0),
            ("craps_eleven", (1, 1), 400.0),
            ("craps_eleven", (1, 2), 400.0),
            ("craps_eleven", (6, 6), 400.0),
            ("craps_eleven", (5, 6), 800.0),
        ]

        for wager, dice, expected in cases:
            with self.subTest(
                wager=wager,
                dice=dice,
            ):
                out = self.roll(
                    [(wager, 100)],
                    dice=dice,
                )

                self.assertEqual(
                    self.result(
                        out,
                        wager,
                    )["return"],
                    expected,
                )

    def test_one_roll_propositions_lose_on_non_qualifying_roll(self):
        wagers = [
            "any_seven",
            "any_craps",
            "two_crap",
            "three_crap",
            "eleven",
            "twelve_crap",
            "craps_eleven",
        ]

        for wager in wagers:
            with self.subTest(wager=wager):
                out = self.roll(
                    [(wager, 100)],
                    dice=(2, 3),
                )

                self.assertEqual(
                    self.result(
                        out,
                        wager,
                    )["return"],
                    0.0,
                )

    def test_all_horn_outcomes(self):
        cases = {
            (1, 1): 775.0,
            (1, 2): 400.0,
            (5, 6): 400.0,
            (6, 6): 775.0,
        }

        for dice, expected in cases.items():
            with self.subTest(dice=dice):
                out = self.roll(
                    [("horn", 100)],
                    dice=dice,
                )

                self.assertEqual(
                    self.result(
                        out,
                        "horn",
                    )["return"],
                    expected,
                )

    def test_all_horn_high_selected_numbers(self):
        cases = [
            ("horn_high_2", (1, 1), 1240.0),
            ("horn_high_3", (1, 2), 640.0),
            ("horn_high_11", (5, 6), 640.0),
            ("horn_high_12", (6, 6), 1240.0),
        ]

        for wager, dice, expected in cases:
            with self.subTest(wager=wager):
                out = self.roll(
                    [(wager, 100)],
                    dice=dice,
                )

                self.assertEqual(
                    self.result(
                        out,
                        wager,
                    )["return"],
                    expected,
                )


    def test_on_off_override(self):
        state = craps_engine.new_state()
        state["bets"]["hard_6"] = Decimal("100")
        off = craps_engine.action(state, "hard_6", "off")
        self.assertFalse(off["state"]["working"]["hard_6"])
        on = craps_engine.action(off["state"], "hard_6", "on")
        self.assertTrue(on["state"]["working"]["hard_6"])


if __name__ == "__main__":
    unittest.main()
