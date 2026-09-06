import unittest
from decimal import Decimal
from unittest.mock import patch

from game import great_fortune_dice as gfd
from game import dice_engine


class TestGreatFortuneDice(unittest.TestCase):

    def out(self, *dice):
        dice = list(dice)

        counts = {
            n: dice.count(n)
            for n in range(1, 7)
        }

        return {
            "dice": dice,
            "total": sum(dice),
            "counts": counts,
            "sorted": sorted(dice),
        }
    
    def ret(self, wager, dice, amount=100):
        return gfd.payout(wager, Decimal(str(amount)), self.out(*dice))

    def test_resolve_returns_four_dice(self):
        with patch("game.great_fortune_dice.random.randint", side_effect=[1, 3, 5, 6]):
            out = gfd.resolve()
        self.assertEqual(out["dice"], [1, 3, 5, 6])
        self.assertEqual(out["total"], 15)

    def test_small_pays_one_to_one(self):
        self.assertEqual(self.ret("small", (1, 2, 4, 6)), Decimal("200"))

    def test_big_pays_one_to_one(self):
        self.assertEqual(self.ret("big", (3, 5, 5, 6)), Decimal("200"))

    def test_all_small_pays_14_to_one(self):
        self.assertEqual(self.ret("all_small", (1, 2, 2, 3)), Decimal("1500"))

    def test_all_big_pays_14_to_one(self):
        self.assertEqual(self.ret("all_big", (4, 5, 6, 6)), Decimal("1500"))

    def test_any_triple_pays_eight_to_one(self):
        self.assertEqual(self.ret("any_triple", (3, 3, 3, 6)), Decimal("900"))

    def test_any_quadruple_pays_200_to_one(self):
        self.assertEqual(self.ret("any_quadruple", (4, 4, 4, 4)), Decimal("20100"))

    def test_specific_double_pays_six_to_one(self):
        self.assertEqual(self.ret("specific_double_2", (2, 2, 4, 6)), Decimal("700"))

    def test_specific_triple_pays_55_to_one(self):
        self.assertEqual(self.ret("specific_triple_5", (5, 5, 5, 1)), Decimal("5600"))

    def test_specific_quadruple_pays_1000_to_one(self):
        self.assertEqual(self.ret("specific_quadruple_6", (6, 6, 6, 6)), Decimal("100100"))

    def test_two_pair_pays_11_to_one(self):
        self.assertEqual(self.ret("two_pair", (2, 2, 5, 5)), Decimal("1200"))

    def test_straight_pays_15_to_one(self):
        for dice in ((1,2,3,4), (2,3,4,5), (3,4,5,6)):
            with self.subTest(dice=dice):
                self.assertEqual(self.ret("straight", dice), Decimal("1600"))

    def test_total_14_pays_seven_to_one(self):
        self.assertEqual(self.ret("fourteen", (1, 2, 5, 6)), Decimal("800"))

    def test_total_payout_table(self):
        cases = {
            5:280, 6:120, 7:55, 8:30, 9:20, 10:13, 11:10, 12:8, 13:7,
            15:7, 16:8, 17:10, 18:13, 19:20, 20:30, 21:55, 22:120, 23:280,
        }
        dice_for_total = {
            5:(1,1,1,2), 6:(1,1,1,3), 7:(1,1,1,4), 8:(1,1,1,5),
            9:(1,1,1,6), 10:(1,1,2,6), 11:(1,1,3,6), 12:(1,1,4,6),
            13:(1,1,5,6), 15:(1,3,5,6), 16:(1,4,5,6), 17:(1,5,5,6),
            18:(1,5,6,6), 19:(2,5,6,6), 20:(3,5,6,6), 21:(4,5,6,6),
            22:(5,5,6,6), 23:(5,6,6,6),
        }
        for total, odds in cases.items():
            with self.subTest(total=total):
                self.assertEqual(
                    self.ret(f"total_{total}", dice_for_total[total]),
                    Decimal("100") * Decimal(str(odds + 1)),
                )

    def test_specific_14_groups(self):
        cases = {
            "specific14_A": ((1,2,5,6), 15),
            "specific14_B": ((1,3,5,5), 30),
            "specific14_C": ((2,3,3,6), 45),
            "specific14_D": ((3,3,4,4), 80),
        }
        for wager, (dice, odds) in cases.items():
            with self.subTest(wager=wager):
                self.assertEqual(
                    self.ret(wager, dice),
                    Decimal("100") * Decimal(str(odds + 1)),
                )

    def test_two_dice_combination_pays_three_to_one(self):
        self.assertEqual(self.ret("combo_16", (1, 2, 4, 6)), Decimal("400"))

    def test_four_from_five_pays_nine_to_one(self):
        self.assertEqual(self.ret("four_from_five_12345", (1, 2, 4, 5)), Decimal("1000"))
        self.assertEqual(self.ret("four_from_five_12345", (1, 2, 5, 6)), Decimal("0"))

    def test_all_specific_doubles(self):
        for number in range(1, 7):
            wager = f"specific_double_{number}"

            other = (
                1
                if number != 1
                else 2
            )

            with self.subTest(
                wager=wager
            ):
                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            number,
                            number,
                            other,
                            other,
                        ),
                    ),
                    Decimal("700"),
                )

                # Three matching dice still qualify.
                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            number,
                            number,
                            number,
                            other,
                        ),
                    ),
                    Decimal("700"),
                )

                # Four matching dice still qualify.
                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            number,
                            number,
                            number,
                            number,
                        ),
                    ),
                    Decimal("700"),
                )

    def test_all_specific_triples(self):
        for number in range(1, 7):
            wager = f"specific_triple_{number}"

            other = (
                1
                if number != 1
                else 2
            )

            with self.subTest(
                wager=wager
            ):
                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            number,
                            number,
                            number,
                            other,
                        ),
                    ),
                    Decimal("5600"),
                )

                # Four matching dice also qualify.
                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            number,
                            number,
                            number,
                            number,
                        ),
                    ),
                    Decimal("5600"),
                )

    def test_all_specific_quadruples(self):
        for number in range(1, 7):
            wager = (
                f"specific_quadruple_{number}"
            )

            other = (
                1
                if number != 1
                else 2
            )

            with self.subTest(
                wager=wager
            ):
                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            number,
                            number,
                            number,
                            number,
                        ),
                    ),
                    Decimal("100100"),
                )

                self.assertEqual(
                    self.ret(
                        wager,
                        (
                            number,
                            number,
                            number,
                            other,
                        ),
                    ),
                    Decimal("0"),
                )

    def test_all_two_dice_combinations(self):
        for first in range(1, 7):
            for second in range(
                first + 1,
                7,
            ):
                wager = (
                    f"combo_{first}{second}"
                )

                filler = next(
                    number
                    for number in range(1, 7)
                    if number not in (
                        first,
                        second,
                    )
                )

                with self.subTest(
                    wager=wager
                ):
                    self.assertEqual(
                        self.ret(
                            wager,
                            (
                                first,
                                second,
                                filler,
                                filler,
                            ),
                        ),
                        Decimal("400"),
                    )

                    self.assertEqual(
                        self.ret(
                            wager,
                            (
                                first,
                                filler,
                                filler,
                                filler,
                            ),
                        ),
                        Decimal("0"),
                    )

    def test_all_specific_14_outcomes(self):
        groups = {
            "specific14_A": (
                (
                    (1, 2, 5, 6),
                    (1, 3, 4, 6),
                    (2, 3, 4, 5),
                ),
                Decimal("1600"),
            ),
            "specific14_B": (
                (
                    (1, 3, 5, 5),
                    (1, 4, 4, 5),
                    (2, 2, 4, 6),
                ),
                Decimal("3100"),
            ),
            "specific14_C": (
                (
                    (2, 3, 3, 6),
                    (1, 1, 6, 6),
                    (2, 2, 5, 5),
                ),
                Decimal("4600"),
            ),
            "specific14_D": (
                (
                    (3, 3, 4, 4),
                    (2, 4, 4, 4),
                    (3, 3, 3, 5),
                ),
                Decimal("8100"),
            ),
        }

        for (
            wager,
            (
                outcomes,
                expected,
            ),
        ) in groups.items():

            for dice in outcomes:
                with self.subTest(
                    wager=wager,
                    dice=dice,
                ):
                    self.assertEqual(
                        self.ret(
                            wager,
                            dice,
                        ),
                        expected,
                    )

    def test_all_four_from_five_groups(self):
        groups = (
            "12345",
            "12346",
            "12356",
            "12456",
            "13456",
            "23456",
        )

        for group in groups:
            wager = (
                f"four_from_five_{group}"
            )

            values = [
                int(value)
                for value in group
            ]

            winning = tuple(
                values[:4]
            )

            outside = next(
                number
                for number in range(1, 7)
                if number not in values
            )

            losing = (
                values[0],
                values[1],
                values[2],
                outside,
            )

            duplicate = (
                values[0],
                values[0],
                values[1],
                values[2],
            )

            with self.subTest(
                wager=wager
            ):
                self.assertEqual(
                    self.ret(
                        wager,
                        winning,
                    ),
                    Decimal("1000"),
                )

                self.assertEqual(
                    self.ret(
                        wager,
                        losing,
                    ),
                    Decimal("0"),
                )

                # The five-number section contains
                # each displayed number once. A
                # duplicated die therefore cannot
                # match four of those five numbers.
                self.assertEqual(
                    self.ret(
                        wager,
                        duplicate,
                    ),
                    Decimal("0"),
                )

    def test_two_pair_accepts_quadruple(self):
        for number in range(1, 7):
            with self.subTest(
                number=number
            ):
                self.assertEqual(
                    self.ret(
                        "two_pair",
                        (
                            number,
                            number,
                            number,
                            number,
                        ),
                    ),
                    Decimal("1200"),
                )

    def test_small_and_big_include_extreme_quadruples(self):
        self.assertEqual(
            self.ret(
                "small",
                (1, 1, 1, 1),
            ),
            Decimal("200"),
        )

        self.assertEqual(
            self.ret(
                "big",
                (6, 6, 6, 6),
            ),
            Decimal("200"),
        )


    def test_all_wager_ids_are_registered(self):
        self.assertTrue(
            gfd.WAGER_TYPES
        )

        self.assertEqual(
            len(gfd.WAGER_TYPES),
            len(set(gfd.WAGER_TYPES)),
        )

        for wager in gfd.WAGER_TYPES:
            with self.subTest(
                wager=wager
            ):
                self.assertTrue(
                    dice_engine.validate_wager(
                        "great_fortune_dice",
                        wager,
                    )
                )


if __name__ == "__main__":
    unittest.main()
