import unittest
from decimal import Decimal

import game.blackjack_lucky8 as lucky8
from game.blackjack_base import is_pair


def C(rank, suit):
    return {"rank": rank, "suit": suit}


class TestBlackjackLucky8(unittest.TestCase):

    def test_pair_same_number(self):
        self.assertTrue(is_pair([C("8", "S"), C("8", "H")]))

    def test_pair_same_face(self):
        self.assertTrue(is_pair([C("K", "S"), C("K", "H")]))

    def test_pair_different_face_cards_is_not_pair(self):
        self.assertFalse(is_pair([C("K", "S"), C("Q", "H")]))

    def test_three_suited_eights(self):
        self.assertEqual(
            lucky8._lucky8_result([C("8", "S"), C("8", "S")], C("8", "S")),
            "3_suited_8s",
        )

    def test_three_unsuited_eights(self):
        self.assertEqual(
            lucky8._lucky8_result([C("8", "S"), C("8", "H")], C("8", "D")),
            "3_unsuited_8s",
        )

    def test_two_suited_eights_player_cards(self):
        self.assertEqual(
            lucky8._lucky8_result([C("8", "S"), C("8", "S")], C("4", "H")),
            "2_suited_8s",
        )

    def test_two_suited_eights_player_and_dealer(self):
        self.assertEqual(
            lucky8._lucky8_result([C("8", "S"), C("5", "H")], C("8", "S")),
            "2_suited_8s",
        )

    def test_two_unsuited_eights(self):
        self.assertEqual(
            lucky8._lucky8_result([C("8", "S"), C("5", "H")], C("8", "D")),
            "2_unsuited_8s",
        )

    def test_two_of_a_kind_player_cards(self):
        self.assertEqual(
            lucky8._lucky8_result([C("6", "S"), C("6", "H")], C("3", "D")),
            "two_of_a_kind",
        )

    def test_two_of_a_kind_player_and_dealer(self):
        self.assertEqual(
            lucky8._lucky8_result([C("6", "S"), C("3", "H")], C("6", "D")),
            "two_of_a_kind",
        )

    def test_eights_take_priority_over_two_kind(self):
        self.assertEqual(
            lucky8._lucky8_result([C("8", "S"), C("8", "H")], C("4", "D")),
            "2_unsuited_8s",
        )

    def test_no_lucky8_combination(self):
        self.assertIsNone(
            lucky8._lucky8_result([C("4", "S"), C("7", "H")], C("K", "D"))
        )

    def test_pair_pays_11_to_1(self):
        outcome = {"seats": {0: {"pair": True}}}
        self.assertEqual(
            lucky8.payout("seat0_pair", Decimal("100"), outcome),
            Decimal("1200"),
        )

    def test_three_suited_eights_pays_1000_to_1(self):
        outcome = {"seats": {0: {"lucky8": "3_suited_8s"}}}
        self.assertEqual(
            lucky8.payout("seat0_lucky8", Decimal("100"), outcome),
            Decimal("100100"),
        )


if __name__ == "__main__":
    unittest.main()
