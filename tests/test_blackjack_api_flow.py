import unittest
from decimal import Decimal

from api.solo import (
    _main_result,
    _normal_hand_return,
    _pontoon_total,
    _free_double,
    _free_split,
)
from game.blackjack_base import is_soft


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


def H(cards, **extra):
    h = {
        "cards": cards,
        "status": "playing",
        "stake": 100.0,
        "paid_extra": 0.0,
        "free_marker": False,
        "from_split": False,
        "from_split_aces": False,
        "split_aces": False,
        "doubled": False,
        "surrendered": False,
        "double_withdrawn": False,
        "immediate_paid": 0.0,
    }
    h.update(extra)
    return h


class TestBlackjackInteractiveRules(unittest.TestCase):

    def test_freebet_dealer_22_pushes_non_busted_hand(self):
        h = H([C("10"), C("8", "H")])
        dealer = [C("10"), C("6", "H"), C("6", "D")]
        self.assertEqual(_main_result("blackjack_freebet", h, dealer), "push")

    def test_freebet_blackjack_beats_dealer_22(self):
        h = H([C("A"), C("K", "H")])
        dealer = [C("10"), C("6", "H"), C("6", "D")]
        self.assertEqual(_main_result("blackjack_freebet", h, dealer), "blackjack")

    def test_freebet_hard_11_is_free_double(self):
        h = H([C("5"), C("6", "H")])
        self.assertTrue(_free_double("blackjack_freebet", h))

    def test_freebet_soft_total_is_not_free_double(self):
        h = H([C("A"), C("8", "H")])
        self.assertTrue(is_soft(h["cards"]))
        self.assertFalse(_free_double("blackjack_freebet", h))

    def test_freebet_ten_value_split_is_paid_not_free(self):
        h = H([C("K"), C("Q", "H")])
        self.assertFalse(_free_split("blackjack_freebet", h))

    def test_normal_blackjack_pushes_against_dealer_blackjack(self):
        h = H([C("A"), C("K", "H")])
        dealer = [C("A", "D"), C("Q", "C")]
        self.assertEqual(_main_result("blackjack_lucky8", h, dealer), "push")

    def test_kings_bounty_blackjack_return_is_6_to_5(self):
        h = H([C("A"), C("K", "H")])
        ret = _normal_hand_return(
            "blackjack_kingsbounty",
            h,
            "blackjack",
            100,
            False,
        )
        self.assertEqual(ret, Decimal("220.0"))

    def test_lucky8_blackjack_return_is_3_to_2(self):
        h = H([C("A"), C("K", "H")])
        ret = _normal_hand_return(
            "blackjack_lucky8",
            h,
            "blackjack",
            100,
            False,
        )
        self.assertEqual(ret, Decimal("250.00"))

    def test_surrender_returns_half_original_stake(self):
        h = H([C("10"), C("6", "H")], surrendered=True)
        ret = _normal_hand_return(
            "blackjack_lucky8",
            h,
            "surrender",
            100,
            False,
        )
        self.assertEqual(ret, Decimal("50.00"))

    def test_pontoon_surrender_loses_all_if_dealer_has_pontoon(self):
        h = H([C("9"), C("7", "H")], surrendered=True)
        ret = _normal_hand_return(
            "pontoon",
            h,
            "surrender",
            100,
            True,
        )
        self.assertEqual(ret, Decimal("0"))

    def test_pontoon_surrender_returns_half_without_dealer_pontoon(self):
        h = H([C("9"), C("7", "H")], surrendered=True)
        ret = _normal_hand_return(
            "pontoon",
            h,
            "surrender",
            100,
            False,
        )
        self.assertEqual(ret, Decimal("50.00"))

    def test_pontoon_doubled_first_two_ace_is_one(self):
        h = H(
            [C("A"), C("7", "H"), C("K", "D")],
            doubled=True,
            pontoon_double_ace=True,
        )
        self.assertEqual(_pontoon_total(h), 18)

    def test_split_hand_ace_ten_is_not_blackjack(self):
        h = H([C("A"), C("K", "H")], from_split=True)
        dealer = [C("9", "D"), C("8", "C")]
        self.assertEqual(_main_result("blackjack_lucky8", h, dealer), "win")

    def test_free_marker_winning_hand_adds_original_wager_value(self):
        h = H([C("10"), C("9", "H")], stake=0.0, free_marker=True)
        dealer = [C("10", "D"), C("8", "C")]
        result = _main_result("blackjack_freebet", h, dealer)
        self.assertEqual(result, "win")
        ret = _normal_hand_return(
            "blackjack_freebet",
            h,
            result,
            100,
            False,
        )
        self.assertEqual(ret, Decimal("100.0"))


if __name__ == "__main__":
    unittest.main()
