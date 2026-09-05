import unittest

import game.poker_mississippi_stud as mississippi
from game.poker_base import rank5


def C(rank, suit):
    return {"rank": rank, "suit": suit}


class TestMississippiStud(unittest.TestCase):

    def odds(self, cards):
        return mississippi.main_odds(rank5(cards))

    def test_royal_flush_pays_500_to_one(self):
        self.assertEqual(
            self.odds([
                C("A", "S"), C("K", "S"), C("Q", "S"), C("J", "S"), C("10", "S")
            ]),
            500,
        )

    def test_straight_flush_pays_100_to_one(self):
        self.assertEqual(
            self.odds([
                C("9", "S"), C("8", "S"), C("7", "S"), C("6", "S"), C("5", "S")
            ]),
            100,
        )

    def test_four_kind_pays_40_to_one(self):
        self.assertEqual(
            self.odds([
                C("8", "S"), C("8", "H"), C("8", "D"), C("8", "C"), C("2", "S")
            ]),
            40,
        )

    def test_full_house_pays_10_to_one(self):
        self.assertEqual(
            self.odds([
                C("8", "S"), C("8", "H"), C("8", "D"), C("2", "C"), C("2", "S")
            ]),
            10,
        )

    def test_flush_pays_6_to_one(self):
        self.assertEqual(
            self.odds([
                C("A", "S"), C("J", "S"), C("8", "S"), C("5", "S"), C("2", "S")
            ]),
            6,
        )

    def test_straight_pays_4_to_one(self):
        self.assertEqual(
            self.odds([
                C("9", "S"), C("8", "H"), C("7", "D"), C("6", "C"), C("5", "S")
            ]),
            4,
        )

    def test_three_kind_pays_3_to_one(self):
        self.assertEqual(
            self.odds([
                C("8", "S"), C("8", "H"), C("8", "D"), C("4", "C"), C("2", "S")
            ]),
            3,
        )

    def test_two_pair_pays_2_to_one(self):
        self.assertEqual(
            self.odds([
                C("8", "S"), C("8", "H"), C("4", "D"), C("4", "C"), C("2", "S")
            ]),
            2,
        )

    def test_jacks_or_better_pair_pays_one_to_one(self):
        self.assertEqual(
            self.odds([
                C("J", "S"), C("J", "H"), C("8", "D"), C("4", "C"), C("2", "S")
            ]),
            1,
        )

    def test_pair_sixes_through_tens_pushes(self):
        self.assertEqual(
            self.odds([
                C("8", "S"), C("8", "H"), C("5", "D"), C("4", "C"), C("2", "S")
            ]),
            0,
        )

    def test_pair_fives_or_lower_loses(self):
        self.assertIsNone(
            self.odds([
                C("5", "S"), C("5", "H"), C("8", "D"), C("4", "C"), C("2", "S")
            ])
        )

    def test_high_card_loses(self):
        self.assertIsNone(
            self.odds([
                C("A", "S"), C("J", "H"), C("8", "D"), C("4", "C"), C("2", "S")
            ])
        )

    def test_street_actions_offer_fold_or_1x_2x_3x(self):
        self.assertEqual(
            mississippi.legal_actions("initial", blind=False),
            ("fold", "bet1", "bet2", "bet3"),
        )
        self.assertEqual(
            mississippi.legal_actions("third", blind=False),
            ("fold", "bet1", "bet2", "bet3"),
        )
        self.assertEqual(
            mississippi.legal_actions("fourth", blind=False),
            ("fold", "bet1", "bet2", "bet3"),
        )


if __name__ == "__main__":
    unittest.main()
