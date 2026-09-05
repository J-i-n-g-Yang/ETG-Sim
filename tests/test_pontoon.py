import unittest
from decimal import Decimal

import game.pontoon as pontoon
from api.solo import _pontoon_shoe, _pontoon_total


def C(rank, suit):
    return {"rank": rank, "suit": suit}


class TestPontoon(unittest.TestCase):

    def test_pontoon_shoe_has_no_tens(self):
        self.assertFalse(any(card["rank"] == "10" for card in _pontoon_shoe(4)))

    def test_four_deck_pontoon_shoe_has_192_cards(self):
        self.assertEqual(len(_pontoon_shoe(4)), 192)

    def test_first_two_aces_count_as_one_when_doubled(self):
        h = {
            "cards": [C("A", "S"), C("7", "H"), C("K", "D")],
            "pontoon_double_ace": True,
        }
        self.assertEqual(_pontoon_total(h), 18)

    def assert_combo(self, cards, expected_category, expected_mult):
        category, _ = pontoon._special_combo(cards)
        self.assertEqual(category, expected_category)
        self.assertEqual(pontoon._COMBO_PAYS[category], Decimal(expected_mult))

    def test_678_mixed_suits(self):
        self.assert_combo([C("6", "S"), C("7", "H"), C("8", "D")], "678_mixed", "1.5")

    def test_777_mixed_suits(self):
        self.assert_combo([C("7", "S"), C("7", "H"), C("7", "D")], "777_mixed", "1.5")

    def test_678_same_suit_non_spades(self):
        self.assert_combo([C("6", "H"), C("7", "H"), C("8", "H")], "678_same_suit", "2")

    def test_777_same_suit_non_spades(self):
        self.assert_combo([C("7", "D"), C("7", "D"), C("7", "D")], "777_same_suit", "2")

    def test_678_all_spades(self):
        self.assert_combo([C("6", "S"), C("7", "S"), C("8", "S")], "678_all_spades", "3")

    def test_777_all_spades(self):
        self.assert_combo([C("7", "S"), C("7", "S"), C("7", "S")], "777_all_spades", "3")

    def test_five_card_21(self):
        self.assert_combo(
            [C("A", "S"), C("2", "H"), C("3", "D"), C("6", "C"), C("9", "S")],
            "5_card_21",
            "1.5",
        )

    def test_six_card_21(self):
        self.assert_combo(
            [C("A", "S"), C("2", "H"), C("3", "D"), C("4", "C"), C("5", "S"), C("6", "H")],
            "6_card_21",
            "2",
        )

    def test_seven_card_21(self):
        self.assert_combo(
            [C("A", "S"), C("2", "H"), C("2", "D"), C("3", "C"), C("3", "S"), C("4", "H"), C("6", "D")],
            "7plus_card_21",
            "3",
        )

    def test_pair_pays_11_to_1(self):
        outcome = {"seats": {0: {"pair": True}}}
        self.assertEqual(
            pontoon.payout("seat0_pair", Decimal("100"), outcome),
            Decimal("1200"),
        )


if __name__ == "__main__":
    unittest.main()
