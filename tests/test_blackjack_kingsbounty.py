import unittest
from decimal import Decimal

import game.blackjack_kingsbounty as kb


def C(rank, suit):
    return {"rank": rank, "suit": suit}


class TestKingsBountyBlackjack(unittest.TestCase):

    def test_two_kings_spades_plus_dealer_blackjack(self):
        self.assertEqual(
            kb._kings_bounty_result(
                [C("K", "S"), C("K", "S")],
                C("A", "H"),
                [C("A", "H"), C("K", "D")],
            ),
            "2_kings_spades_dealer_bj",
        )

    def test_two_kings_spades(self):
        self.assertEqual(
            kb._kings_bounty_result(
                [C("K", "S"), C("K", "S")],
                C("6", "H"),
                [C("6", "H"), C("9", "D")],
            ),
            "2_kings_spades",
        )

    def test_two_suited_kings(self):
        self.assertEqual(
            kb._kings_bounty_result(
                [C("K", "H"), C("K", "H")],
                C("6", "S"),
                [C("6", "S"), C("9", "D")],
            ),
            "2_suited_kings",
        )

    def test_two_suited_queens(self):
        self.assertEqual(
            kb._kings_bounty_result(
                [C("Q", "D"), C("Q", "D")],
                C("6", "S"),
                [C("6", "S"), C("9", "C")],
            ),
            "2_suited_QJ10",
        )

    def test_suited_twenty(self):
        self.assertEqual(
            kb._kings_bounty_result(
                [C("Q", "H"), C("J", "H")],
                C("6", "S"),
                [C("6", "S"), C("9", "C")],
            ),
            "suited_20",
        )

    def test_two_kings(self):
        self.assertEqual(
            kb._kings_bounty_result(
                [C("K", "S"), C("K", "H")],
                C("6", "D"),
                [C("6", "D"), C("9", "C")],
            ),
            "2_kings",
        )

    def test_unsuited_twenty(self):
        self.assertEqual(
            kb._kings_bounty_result(
                [C("Q", "S"), C("J", "H")],
                C("6", "D"),
                [C("6", "D"), C("9", "C")],
            ),
            "unsuited_20",
        )

    def test_bet_set_suited_pair(self):
        self.assertEqual(kb._bet_the_set_result([C("8", "S"), C("8", "S")]), "suited_pair")

    def test_bet_set_unsuited_pair(self):
        self.assertEqual(kb._bet_the_set_result([C("8", "S"), C("8", "H")]), "unsuited_pair")

    def test_royal_match(self):
        self.assertEqual(kb._royal_match_result([C("K", "H"), C("Q", "H")]), "royal_match")

    def test_other_suited_cards(self):
        self.assertEqual(kb._royal_match_result([C("8", "D"), C("4", "D")]), "suited")

    def test_unsuited_cards_lose(self):
        self.assertIsNone(kb._royal_match_result([C("8", "D"), C("4", "C")]))

    def test_blackjack_pays_six_to_five(self):
        outcome = {"seats": {0: {"result": "blackjack"}}}
        self.assertEqual(
            kb.payout("seat0_main", Decimal("100"), outcome),
            Decimal("220"),
        )


if __name__ == "__main__":
    unittest.main()
