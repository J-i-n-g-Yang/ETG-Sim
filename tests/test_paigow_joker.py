import unittest

import game.paigow_engine as pg


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


class TestPaiGowJoker(unittest.TestCase):

    def test_joker_completes_royal_flush(self):
        rank = pg.rank5([
            C("A", "S"),
            C("K", "S"),
            C("Q", "S"),
            C("J", "S"),
            C("JOKER", "X"),
        ])
        self.assertEqual(rank, (8, 14))

    def test_joker_completes_straight_flush(self):
        rank = pg.rank5([
            C("9", "H"),
            C("8", "H"),
            C("7", "H"),
            C("6", "H"),
            C("JOKER", "X"),
        ])
        self.assertEqual(rank, (8, 10))

    def test_joker_completes_flush(self):
        rank = pg.rank5([
            C("A", "D"),
            C("J", "D"),
            C("8", "D"),
            C("4", "D"),
            C("JOKER", "X"),
        ])
        self.assertEqual(rank[0], 5)

    def test_joker_completes_straight(self):
        rank = pg.rank5([
            C("9", "S"),
            C("8", "H"),
            C("7", "D"),
            C("6", "C"),
            C("JOKER", "X"),
        ])
        self.assertEqual(rank, (4, 10))

    def test_joker_is_ace_when_not_needed_for_allowed_wild_hand(self):
        rank = pg.rank5([
            C("K", "S"),
            C("K", "H"),
            C("8", "D"),
            C("4", "C"),
            C("JOKER", "X"),
        ])
        self.assertEqual(rank[0], 1)
        self.assertEqual(rank[1], 13)
        self.assertIn(14, rank[2:])

    def test_four_aces_plus_joker_is_five_aces(self):
        rank = pg.rank5([
            C("A", "S"),
            C("A", "H"),
            C("A", "D"),
            C("A", "C"),
            C("JOKER", "X"),
        ])
        self.assertEqual(rank, (9, 14))

    def test_joker_does_not_create_four_of_kind(self):
        rank = pg.rank5([
            C("K", "S"),
            C("K", "H"),
            C("K", "D"),
            C("2", "C"),
            C("JOKER", "X"),
        ])
        self.assertEqual(rank[0], 3)

    def test_low_hand_joker_counts_as_ace(self):
        self.assertEqual(
            pg.rank2([C("JOKER", "X"), C("K", "H")]),
            (0, 14, 13),
        )


if __name__ == "__main__":
    unittest.main()
