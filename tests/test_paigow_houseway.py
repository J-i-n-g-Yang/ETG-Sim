import unittest

import game.paigow_engine as pg


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


def ranks(cards):
    return sorted(
        [14 if c["rank"] == "JOKER" else pg.RV[c["rank"]] for c in cards],
        reverse=True,
    )


class TestPaiGowHouseWay(unittest.TestCase):

    def assert_legal(self, cards):
        low, high = pg.house_way(cards)
        self.assertEqual(len(low), 2)
        self.assertEqual(len(high), 5)
        self.assertTrue(pg._legal_split(low, high))
        return low, high

    def test_no_pair_uses_second_and_third_highest_in_low(self):
        cards = [
            C("A", "S"), C("K", "H"), C("Q", "D"),
            C("9", "C"), C("7", "S"), C("4", "H"), C("2", "D")
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [13, 12])
        self.assertIn(14, ranks(high))

    def test_one_pair_keeps_pair_high_and_two_highest_kickers_low(self):
        cards = [
            C("9", "S"), C("9", "H"), C("A", "D"),
            C("K", "C"), C("7", "S"), C("4", "H"), C("2", "D")
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 13])
        self.assertEqual(pg.rank5(high)[0], 1)
        self.assertEqual(pg.rank5(high)[1], 9)

    def test_three_pairs_places_highest_pair_low(self):
        cards = [
            C("K", "S"), C("K", "H"),
            C("8", "D"), C("8", "C"),
            C("3", "S"), C("3", "H"),
            C("A", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [13, 13])

    def test_two_low_pairs_with_king_protector_stay_together(self):
        cards = [
            C("6", "S"), C("6", "H"),
            C("3", "D"), C("3", "C"),
            C("K", "S"), C("9", "H"), C("7", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [13, 9])
        self.assertEqual(pg.rank5(high)[0], 2)

    def test_low_and_high_pair_without_ace_split(self):
        cards = [
            C("K", "S"), C("K", "H"),
            C("4", "D"), C("4", "C"),
            C("Q", "S"), C("9", "H"), C("7", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [4, 4])
        self.assertEqual(pg.rank5(high)[0], 1)
        self.assertEqual(pg.rank5(high)[1], 13)

    def test_low_and_high_pair_with_ace_stay_together(self):
        cards = [
            C("K", "S"), C("K", "H"),
            C("4", "D"), C("4", "C"),
            C("A", "S"), C("9", "H"), C("7", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 9])
        self.assertEqual(pg.rank5(high)[0], 2)

    def test_two_trips_put_high_trip_pair_low(self):
        cards = [
            C("K", "S"), C("K", "H"), C("K", "D"),
            C("5", "S"), C("5", "H"), C("5", "D"),
            C("2", "C"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [13, 13])

    def test_trip_aces_split_one_ace_to_low(self):
        cards = [
            C("A", "S"), C("A", "H"), C("A", "D"),
            C("K", "C"), C("9", "S"), C("6", "H"), C("2", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 13])
        self.assertEqual(pg.rank5(high)[0], 1)
        self.assertEqual(pg.rank5(high)[1], 14)

    def test_full_house_places_pair_low(self):
        cards = [
            C("9", "S"), C("9", "H"), C("9", "D"),
            C("6", "C"), C("6", "S"),
            C("A", "H"), C("3", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [6, 6])
        self.assertEqual(pg.rank5(high)[0], 3)

    def test_full_house_pair_twos_with_ace_king_keeps_full_house(self):
        cards = [
            C("9", "S"), C("9", "H"), C("9", "D"),
            C("2", "C"), C("2", "S"),
            C("A", "H"), C("K", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 13])
        self.assertEqual(pg.rank5(high)[0], 6)

    def test_low_quads_stay_together(self):
        cards = [
            C("5", "S"), C("5", "H"), C("5", "D"), C("5", "C"),
            C("A", "S"), C("K", "H"), C("9", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 13])
        self.assertEqual(pg.rank5(high)[0], 7)

    def test_medium_quads_with_ace_stay_together(self):
        cards = [
            C("8", "S"), C("8", "H"), C("8", "D"), C("8", "C"),
            C("A", "S"), C("K", "H"), C("9", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 13])
        self.assertEqual(pg.rank5(high)[0], 7)

    def test_medium_quads_without_ace_split(self):
        cards = [
            C("8", "S"), C("8", "H"), C("8", "D"), C("8", "C"),
            C("K", "S"), C("Q", "H"), C("9", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [8, 8])

    def test_high_quads_always_split(self):
        cards = [
            C("Q", "S"), C("Q", "H"), C("Q", "D"), C("Q", "C"),
            C("A", "S"), C("K", "H"), C("9", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [12, 12])

    def test_quad_aces_split_unless_pair_kings(self):
        cards = [
            C("A", "S"), C("A", "H"), C("A", "D"), C("A", "C"),
            C("Q", "S"), C("9", "H"), C("7", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 14])

    def test_quad_aces_with_pair_kings_put_kings_low(self):
        cards = [
            C("A", "S"), C("A", "H"), C("A", "D"), C("A", "C"),
            C("K", "S"), C("K", "H"), C("7", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [13, 13])
        self.assertEqual(pg.rank5(high)[0], 7)

    def test_five_aces_with_pair_kings_put_kings_low(self):
        cards = [
            C("A", "S"), C("A", "H"), C("A", "D"), C("A", "C"),
            C("JOKER", "X"), C("K", "S"), C("K", "H"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [13, 13])
        self.assertEqual(pg.rank5(high), (9, 14))

    def test_five_aces_without_pair_kings_put_two_aces_low(self):
        cards = [
            C("A", "S"), C("A", "H"), C("A", "D"), C("A", "C"),
            C("JOKER", "X"), C("Q", "S"), C("9", "H"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(ranks(low), [14, 14])
        self.assertEqual(pg.rank5(high)[0], 3)

    def test_straight_is_preserved_when_possible(self):
        cards = [
            C("9", "S"), C("8", "H"), C("7", "D"), C("6", "C"), C("5", "S"),
            C("A", "H"), C("K", "D"),
        ]
        low, high = self.assert_legal(cards)
        self.assertEqual(pg.rank5(high)[0], 4)
        self.assertEqual(ranks(low), [14, 13])


if __name__ == "__main__":
    unittest.main()
