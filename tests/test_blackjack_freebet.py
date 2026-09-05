import unittest
from decimal import Decimal

import game.blackjack_freebet as freebet
from api.solo import _free_double, _free_split


def C(rank, suit):
    return {"rank": rank, "suit": suit}


class TestFreeBetBlackjack(unittest.TestCase):

    def hand(self, cards):
        return {"cards": cards, "status": "playing"}

    def test_hard_9_is_free_double(self):
        self.assertTrue(_free_double("blackjack_freebet", self.hand([C("4", "S"), C("5", "H")])))

    def test_hard_10_is_free_double(self):
        self.assertTrue(_free_double("blackjack_freebet", self.hand([C("4", "S"), C("6", "H")])))

    def test_hard_11_is_free_double(self):
        self.assertTrue(_free_double("blackjack_freebet", self.hand([C("5", "S"), C("6", "H")])))

    def test_soft_total_is_not_free_double(self):
        self.assertFalse(_free_double("blackjack_freebet", self.hand([C("A", "S"), C("8", "H")])))

    def test_hard_12_is_not_free_double(self):
        self.assertFalse(_free_double("blackjack_freebet", self.hand([C("6", "S"), C("6", "H")])))

    def test_non_ten_pair_is_free_split(self):
        self.assertTrue(_free_split("blackjack_freebet", self.hand([C("8", "S"), C("8", "H")])))

    def test_ten_value_pair_is_not_free_split(self):
        self.assertFalse(_free_split("blackjack_freebet", self.hand([C("K", "S"), C("Q", "H")])))

    def busted_outcome(self, cards):
        return {
            "dealer_bust": True,
            "dealer_bust_cards": cards,
            "seats": {0: {"free_markers": 0}},
        }

    def test_busted_three_cards_pays_1_to_1(self):
        self.assertEqual(freebet.payout("seat0_busted", Decimal("100"), self.busted_outcome(3)), Decimal("200"))

    def test_busted_four_cards_pays_2_to_1(self):
        self.assertEqual(freebet.payout("seat0_busted", Decimal("100"), self.busted_outcome(4)), Decimal("300"))

    def test_busted_five_cards_pays_6_to_1(self):
        self.assertEqual(freebet.payout("seat0_busted", Decimal("100"), self.busted_outcome(5)), Decimal("700"))

    def test_busted_six_cards_pays_50_to_1(self):
        self.assertEqual(freebet.payout("seat0_busted", Decimal("100"), self.busted_outcome(6)), Decimal("5100"))

    def test_busted_seven_plus_cards_pays_100_to_1(self):
        self.assertEqual(freebet.payout("seat0_busted", Decimal("100"), self.busted_outcome(7)), Decimal("10100"))

    def pot_outcome(self, markers):
        return {"seats": {0: {"free_markers": markers}}}

    def test_pot_gold_one_marker(self):
        self.assertEqual(freebet.payout("seat0_potofgold", Decimal("100"), self.pot_outcome(1)), Decimal("400"))

    def test_pot_gold_two_markers(self):
        self.assertEqual(freebet.payout("seat0_potofgold", Decimal("100"), self.pot_outcome(2)), Decimal("1100"))

    def test_pot_gold_three_markers(self):
        self.assertEqual(freebet.payout("seat0_potofgold", Decimal("100"), self.pot_outcome(3)), Decimal("2600"))

    def test_pot_gold_four_markers(self):
        self.assertEqual(freebet.payout("seat0_potofgold", Decimal("100"), self.pot_outcome(4)), Decimal("5100"))

    def test_pot_gold_five_plus_markers(self):
        self.assertEqual(freebet.payout("seat0_potofgold", Decimal("100"), self.pot_outcome(5)), Decimal("10100"))


if __name__ == "__main__":
    unittest.main()
