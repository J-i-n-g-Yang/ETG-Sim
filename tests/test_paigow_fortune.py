import unittest
from decimal import Decimal

import game.paigow_engine as pg


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


class TestPaiGowFortune(unittest.TestCase):

    def test_seven_card_straight_flush_without_joker(self):
        cards = [
            C("8", "S"), C("9", "S"), C("10", "S"),
            C("J", "S"), C("Q", "S"), C("K", "S"), C("A", "S")
        ]
        self.assertEqual(
            pg.fortune_category(cards),
            "seven_card_straight_flush_no_joker",
        )
        self.assertEqual(
            pg.FORTUNE_PAYS["seven_card_straight_flush_no_joker"],
            Decimal("2500"),
        )

    def test_seven_card_straight_flush_with_joker(self):
        cards = [
            C("8", "H"), C("9", "H"), C("10", "H"),
            C("J", "H"), C("Q", "H"), C("K", "H"), C("JOKER", "X")
        ]
        self.assertEqual(
            pg.fortune_category(cards),
            "seven_card_straight_flush_with_joker",
        )

    def test_five_aces(self):
        cards = [
            C("A", "S"), C("A", "H"), C("A", "D"), C("A", "C"),
            C("JOKER", "X"), C("7", "S"), C("2", "H")
        ]
        self.assertEqual(pg.fortune_category(cards), "five_aces")

    def test_royal_flush(self):
        cards = [
            C("A", "S"), C("K", "S"), C("Q", "S"),
            C("J", "S"), C("10", "S"), C("4", "H"), C("2", "D")
        ]
        self.assertEqual(pg.fortune_category(cards), "royal_flush")

    def test_straight_flush(self):
        cards = [
            C("9", "S"), C("8", "S"), C("7", "S"),
            C("6", "S"), C("5", "S"), C("K", "H"), C("2", "D")
        ]
        self.assertEqual(pg.fortune_category(cards), "straight_flush")

    def test_four_kind(self):
        cards = [
            C("8", "S"), C("8", "H"), C("8", "D"), C("8", "C"),
            C("A", "S"), C("K", "H"), C("2", "D")
        ]
        self.assertEqual(pg.fortune_category(cards), "four_kind")

    def test_full_house(self):
        cards = [
            C("9", "S"), C("9", "H"), C("9", "D"),
            C("6", "C"), C("6", "S"), C("A", "H"), C("2", "D")
        ]
        self.assertEqual(pg.fortune_category(cards), "full_house")

    def test_flush(self):
        cards = [
            C("A", "S"), C("J", "S"), C("8", "S"),
            C("5", "S"), C("2", "S"), C("K", "H"), C("4", "D")
        ]
        self.assertEqual(pg.fortune_category(cards), "flush")

    def test_three_kind(self):
        cards = [
            C("8", "S"), C("8", "H"), C("8", "D"),
            C("A", "C"), C("K", "S"), C("5", "H"), C("2", "D")
        ]
        self.assertEqual(pg.fortune_category(cards), "three_kind")

    def test_straight(self):
        cards = [
            C("9", "S"), C("8", "H"), C("7", "D"),
            C("6", "C"), C("5", "S"), C("K", "H"), C("2", "D")
        ]
        self.assertEqual(pg.fortune_category(cards), "straight")

    def test_royal_match_requires_royal_flush_high_and_suited_kq_low(self):
        high = [
            C("A", "S"), C("K", "S"), C("Q", "S"), C("J", "S"), C("10", "S")
        ]
        low = [C("K", "H"), C("Q", "H")]
        cards = high + low
        self.assertEqual(pg.fortune_category(cards, low, high), "royal_match")

    def test_envy_tables(self):
        self.assertEqual(
            pg.ENVY_PAYS["seven_card_straight_flush_no_joker"],
            Decimal("250"),
        )
        self.assertEqual(pg.ENVY_PAYS["royal_match"], Decimal("50"))


if __name__ == "__main__":
    unittest.main()
