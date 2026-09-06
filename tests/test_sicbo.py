import unittest
from decimal import Decimal
from unittest.mock import patch

from game import sicbo


class TestSicBo(unittest.TestCase):

    def out(self, *dice):
        total = sum(dice)
        return {
            "dice": list(dice),
            "total": total,
            "triple": len(set(dice)) == 1,
        }

    def ret(self, wager, dice, amount=100):
        return sicbo.payout(wager, Decimal(str(amount)), self.out(*dice))

    def test_resolve_returns_three_dice(self):
        with patch("game.sicbo.random.randint", side_effect=[1, 4, 6]):
            out = sicbo.resolve()
        self.assertEqual(out["dice"], [1, 4, 6])
        self.assertEqual(out["total"], 11)
        self.assertFalse(out["triple"])

    def test_small_pays_one_to_one(self):
        self.assertEqual(self.ret("small", (1, 3, 4)), Decimal("200"))

    def test_big_pays_one_to_one(self):
        self.assertEqual(self.ret("big", (4, 5, 6)), Decimal("200"))

    def test_small_loses_on_triple(self):
        self.assertEqual(self.ret("small", (2, 2, 2)), Decimal("0"))

    def test_big_loses_on_triple(self):
        self.assertEqual(self.ret("big", (4, 4, 4)), Decimal("0"))

    def test_odd_pays_one_to_one(self):
        self.assertEqual(self.ret("odd", (1, 2, 4)), Decimal("200"))

    def test_even_pays_one_to_one(self):
        self.assertEqual(self.ret("even", (1, 2, 3)), Decimal("200"))

    def test_odd_even_lose_on_triple(self):
        self.assertEqual(self.ret("even", (2, 2, 2)), Decimal("0"))
        self.assertEqual(self.ret("odd", (3, 3, 3)), Decimal("0"))

    def test_any_triple_pays_31_to_one(self):
        self.assertEqual(self.ret("any_triple", (5, 5, 5)), Decimal("3200"))

    def test_specific_triple_pays_180_to_one(self):
        self.assertEqual(self.ret("triple_3", (3, 3, 3)), Decimal("18100"))
        self.assertEqual(self.ret("triple_3", (2, 2, 2)), Decimal("0"))

    def test_specific_double_pays_11_to_one(self):
        self.assertEqual(self.ret("double_4", (4, 4, 2)), Decimal("1200"))
        self.assertEqual(self.ret("double_4", (4, 2, 1)), Decimal("0"))

    def test_total_payout_table(self):
        cases = {
            4: 62, 5: 31, 6: 18, 7: 12, 8: 8, 9: 7, 10: 6,
            11: 6, 12: 7, 13: 8, 14: 12, 15: 18, 16: 31, 17: 62,
        }
        dice_for_total = {
            4:(1,1,2), 5:(1,1,3), 6:(1,2,3), 7:(1,2,4),
            8:(1,2,5), 9:(1,2,6), 10:(1,3,6), 11:(1,4,6),
            12:(1,5,6), 13:(2,5,6), 14:(3,5,6), 15:(4,5,6),
            16:(5,5,6), 17:(5,6,6),
        }
        for total, odds in cases.items():
            with self.subTest(total=total):
                self.assertEqual(
                    self.ret(f"total_{total}", dice_for_total[total]),
                    Decimal("100") * Decimal(str(odds + 1)),
                )

    def test_totals_qualify_on_triples(self):
        cases = {
            6: ((2, 2, 2), Decimal("1900")),
            9: ((3, 3, 3), Decimal("800")),
            12: ((4, 4, 4), Decimal("800")),
            15: ((5, 5, 5), Decimal("1900")),
        }

        for total, (dice, expected) in cases.items():
            with self.subTest(
                total=total,
                dice=dice,
            ):
                self.assertEqual(
                    self.ret(
                        f"total_{total}",
                        dice,
                    ),
                    expected,
                )

    def test_single_die_one_match_pays_one_to_one(self):
        self.assertEqual(self.ret("single_5", (5, 2, 3)), Decimal("200"))

    def test_single_die_two_matches_pays_two_to_one(self):
        self.assertEqual(self.ret("single_5", (5, 5, 3)), Decimal("300"))

    def test_single_die_three_matches_pays_twelve_to_one(self):
        self.assertEqual(self.ret("single_5", (5, 5, 5)), Decimal("1300"))

    def test_two_dice_combination_pays_six_to_one(self):
        self.assertEqual(self.ret("combo_16", (1, 4, 6)), Decimal("700"))
        self.assertEqual(self.ret("combo_16", (1, 4, 5)), Decimal("0"))

    def test_three_single_combination_pays_30_to_one(self):
        self.assertEqual(self.ret("three_single_146", (6, 1, 4)), Decimal("3100"))
        self.assertEqual(self.ret("three_single_146", (1, 4, 5)), Decimal("0"))

    def test_double_single_combination_pays_50_to_one(self):
        self.assertEqual(self.ret("double_single_225", (2, 5, 2)), Decimal("5100"))
        self.assertEqual(self.ret("double_single_225", (2, 5, 5)), Decimal("0"))

    def test_three_from_four_pays_seven_to_one(self):
        self.assertEqual(self.ret("three_from_four_1234", (1, 3, 4)), Decimal("800"))
        self.assertEqual(self.ret("three_from_four_1234", (1, 2, 5)), Decimal("0"))


    def test_all_two_dice_combinations(self):
        for first in range(1, 7):
            for second in range(first + 1, 7):
                wager = f"combo_{first}{second}"

                third = next(
                    n
                    for n in range(1, 7)
                    if n not in (first, second)
                )

                with self.subTest(
                    wager=wager,
                ):
                    self.assertEqual(
                        self.ret(
                            wager,
                            (
                                first,
                                second,
                                third,
                            ),
                        ),
                        Decimal("700"),
                    )

                    missing = next(
                        n
                        for n in range(1, 7)
                        if n not in (first, second)
                    )

                    self.assertEqual(
                        self.ret(
                            wager,
                            (
                                first,
                                missing,
                                missing,
                            ),
                        ),
                        Decimal("0"),
                    )

    def test_all_three_single_combinations(self):
        for first in range(1, 5):
            for second in range(first + 1, 6):
                for third in range(second + 1, 7):
                    wager = (
                        f"three_single_"
                        f"{first}{second}{third}"
                    )

                    with self.subTest(
                        wager=wager,
                    ):
                        self.assertEqual(
                            self.ret(
                                wager,
                                (
                                    third,
                                    first,
                                    second,
                                ),
                            ),
                            Decimal("3100"),
                        )

                        replacement = next(
                            n
                            for n in range(1, 7)
                            if n not in (
                                first,
                                second,
                                third,
                            )
                        )

                        self.assertEqual(
                            self.ret(
                                wager,
                                (
                                    first,
                                    second,
                                    replacement,
                                ),
                            ),
                            Decimal("0"),
                        )

    def test_all_double_single_combinations(self):
        for pair in range(1, 7):
            for single in range(1, 7):
                if pair == single:
                    continue

                wager = (
                    f"double_single_"
                    f"{pair}{pair}{single}"
                )

                with self.subTest(
                    wager=wager,
                ):
                    self.assertEqual(
                        self.ret(
                            wager,
                            (
                                pair,
                                single,
                                pair,
                            ),
                        ),
                        Decimal("5100"),
                    )

                    self.assertEqual(
                        self.ret(
                            wager,
                            (
                                pair,
                                single,
                                single,
                            ),
                        ),
                        Decimal("0"),
                    )

    def test_all_approved_three_from_four_groups(self):
        groups = (
            "1234",
            "2345",
            "2356",
            "3456",
        )

        for group in groups:
            wager = (
                f"three_from_four_{group}"
            )

            values = [
                int(value)
                for value in group
            ]

            winning_dice = tuple(
                values[:3]
            )

            outside = next(
                n
                for n in range(1, 7)
                if n not in values
            )

            losing_dice = (
                values[0],
                values[1],
                outside,
            )

            with self.subTest(
                wager=wager,
            ):
                self.assertEqual(
                    self.ret(
                        wager,
                        winning_dice,
                    ),
                    Decimal("800"),
                )

                self.assertEqual(
                    self.ret(
                        wager,
                        losing_dice,
                    ),
                    Decimal("0"),
                )

                # Repeated values do not satisfy
                # "three dice from four numbers".
                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            values[0],
                            values[0],
                            values[1],
                        ),
                    ),
                    Decimal("0"),
                )

    def test_all_wager_ids_are_registered(self):
        self.assertTrue(sicbo.WAGER_TYPES)

        self.assertEqual(
            len(sicbo.WAGER_TYPES),
            len(set(sicbo.WAGER_TYPES)),
        )

        for wager in sicbo.WAGER_TYPES:
            with self.subTest(wager=wager):
                self.assertIsInstance(wager, str)
                self.assertTrue(wager)


if __name__ == "__main__":
    unittest.main()
