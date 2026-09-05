import unittest
from decimal import Decimal

from game.baccarat_base import hand_total, is_pair, common_payout
import game.baccarat_dragon_tiger as dragon
import game.baccarat_immortal as immortal
import game.baccarat_rising as rising


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


class TestBaccaratRules(unittest.TestCase):

    def test_card_values_and_modulo_total(self):
        self.assertEqual(hand_total([C("A"), C("9"), C("K")]), 0)
        self.assertEqual(hand_total([C("7"), C("8")]), 5)

    def test_pair_same_number(self):
        self.assertTrue(is_pair([C("8", "S"), C("8", "H")]))

    def test_pair_same_face(self):
        self.assertTrue(is_pair([C("K", "S"), C("K", "H")]))

    def test_different_face_cards_not_pair(self):
        self.assertFalse(is_pair([C("K", "S"), C("Q", "H")]))

    def outcome(self, winner, pt, bt, pc=2, bc=2, **extra):
        player_cards = [C("2")] * pc
        banker_cards = [C("3")] * bc
        out = {
            "winner": winner,
            "player_total": pt,
            "banker_total": bt,
            "player_cards": player_cards,
            "banker_cards": banker_cards,
            "player_cards_count": pc,
            "banker_cards_count": bc,
            "total_cards": pc + bc,
            "player_pair": False,
            "banker_pair": False,
        }
        out.update(extra)
        return out

    def test_player_regular_win_pays_1_to_1(self):
        out = self.outcome("player", 8, 6)
        self.assertEqual(common_payout("player", Decimal("100"), out), Decimal("200"))

    def test_banker_win_on_six_pays_half(self):
        out = self.outcome("banker", 5, 6)
        self.assertEqual(common_payout("banker", Decimal("100"), out), Decimal("150.0"))

    def test_banker_other_win_pays_1_to_1(self):
        out = self.outcome("banker", 6, 8)
        self.assertEqual(common_payout("banker", Decimal("100"), out), Decimal("200"))

    def test_main_bets_push_on_tie(self):
        out = self.outcome("tie", 6, 6)
        self.assertEqual(common_payout("player", Decimal("100"), out), Decimal("100"))
        self.assertEqual(common_payout("banker", Decimal("100"), out), Decimal("100"))

    def test_tie_pays_8_to_1(self):
        out = self.outcome("tie", 4, 4)
        self.assertEqual(common_payout("tie", Decimal("100"), out), Decimal("900"))

    def test_tiger_tie_only_wins_on_six_six(self):
        six = self.outcome("tie", 6, 6)
        five = self.outcome("tie", 5, 5)
        self.assertEqual(common_payout("tiger_tie", Decimal("100"), six), Decimal("3600"))
        self.assertEqual(common_payout("tiger_tie", Decimal("100"), five), Decimal("0"))

    def test_small_dragon(self):
        out = self.outcome("player", 7, 5, pc=2, bc=2)
        self.assertEqual(common_payout("small_dragon", Decimal("100"), out), Decimal("1600"))

    def test_big_dragon(self):
        out = self.outcome("player", 7, 5, pc=3, bc=2)
        self.assertEqual(common_payout("big_dragon", Decimal("100"), out), Decimal("3100"))

    def test_small_tiger(self):
        out = self.outcome("banker", 5, 6, pc=2, bc=2)
        self.assertEqual(common_payout("small_tiger", Decimal("100"), out), Decimal("2300"))

    def test_big_tiger(self):
        out = self.outcome("banker", 5, 6, pc=2, bc=3)
        self.assertEqual(common_payout("big_tiger", Decimal("100"), out), Decimal("5100"))

    def test_dragon_tiger_2_2_pays_30_to_1(self):
        out = self.outcome("player", 7, 6, pc=2, bc=2)
        self.assertEqual(common_payout("dragon_tiger", Decimal("100"), out), Decimal("3100"))

    def test_dragon_tiger_3_2_pays_40_to_1(self):
        out = self.outcome("player", 7, 6, pc=3, bc=2)
        self.assertEqual(common_payout("dragon_tiger", Decimal("100"), out), Decimal("4100"))

    def test_dragon_tiger_3_3_pays_100_to_1(self):
        out = self.outcome("player", 7, 6, pc=3, bc=3)
        self.assertEqual(common_payout("dragon_tiger", Decimal("100"), out), Decimal("10100"))

    def test_immortal_player_seven_win_pays_half(self):
        out = self.outcome("player", 7, 6)
        self.assertEqual(
            common_payout("player", Decimal("100"), out, immortal_main=True),
            Decimal("150.0"),
        )

    def test_immortal_player_seven_loses_to_eight_pushes(self):
        out = self.outcome("banker", 7, 8)
        self.assertEqual(
            common_payout("player", Decimal("100"), out, immortal_main=True),
            Decimal("100"),
        )

    def test_immortal_player_seven_loses_to_nine_pushes(self):
        out = self.outcome("banker", 7, 9)
        self.assertEqual(
            common_payout("player", Decimal("100"), out, immortal_main=True),
            Decimal("100"),
        )

    def test_immortal_dragon_pays_25_to_1(self):
        out = self.outcome("banker", 7, 8)
        self.assertEqual(
            immortal.payout("immortal_dragon", Decimal("100"), out),
            Decimal("2600"),
        )

    def test_player_pair_pays_11_to_1(self):
        out = self.outcome("player", 8, 6, player_pair=True)
        self.assertEqual(
            immortal.payout("player_pair", Decimal("100"), out),
            Decimal("1200"),
        )

    def test_banker_pair_pays_11_to_1(self):
        out = self.outcome("banker", 6, 8, banker_pair=True)
        self.assertEqual(
            immortal.payout("banker_pair", Decimal("100"), out),
            Decimal("1200"),
        )

    def test_rising_dragon_four_cards(self):
        out = self.outcome("player", 8, 6, pc=2, bc=2)
        self.assertEqual(rising.payout("rising_dragon", Decimal("100"), out), Decimal("500"))

    def test_rising_dragon_five_cards(self):
        out = self.outcome("player", 8, 6, pc=3, bc=2)
        self.assertEqual(rising.payout("rising_dragon", Decimal("100"), out), Decimal("700"))

    def test_rising_dragon_six_cards(self):
        out = self.outcome("player", 8, 6, pc=3, bc=3)
        self.assertEqual(rising.payout("rising_dragon", Decimal("100"), out), Decimal("550.0"))

    def test_rising_tiger_four_cards(self):
        out = self.outcome("banker", 6, 8, pc=2, bc=2)
        self.assertEqual(rising.payout("rising_tiger", Decimal("100"), out), Decimal("500"))

    def test_rising_tiger_five_cards(self):
        out = self.outcome("banker", 6, 8, pc=2, bc=3)
        self.assertEqual(rising.payout("rising_tiger", Decimal("100"), out), Decimal("550.0"))

    def test_rising_tiger_six_cards(self):
        out = self.outcome("banker", 6, 8, pc=3, bc=3)
        self.assertEqual(rising.payout("rising_tiger", Decimal("100"), out), Decimal("650.0"))

    def test_rising_bets_push_on_tie(self):
        out = self.outcome("tie", 6, 6, pc=3, bc=3)
        self.assertEqual(rising.payout("rising_dragon", Decimal("100"), out), Decimal("100"))
        self.assertEqual(rising.payout("rising_tiger", Decimal("100"), out), Decimal("100"))

    def test_named_dragon_variant_accepts_common_payout(self):
        out = self.outcome("player", 7, 6, pc=2, bc=2)
        self.assertEqual(
            dragon.payout("dragon_tiger", Decimal("100"), out),
            Decimal("3100"),
        )


if __name__ == "__main__":
    unittest.main()
