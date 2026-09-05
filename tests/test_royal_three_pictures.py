import unittest
from decimal import Decimal

import game.royal_three_pictures as rtp


def c(rank, suit="S"):
    return {"rank": rank, "suit": suit}


class TestRoyalThreePictures(unittest.TestCase):

    def test_deck_is_standard_52_without_jokers(self):
        deck = rtp.make_deck(shuffle=False)
        self.assertEqual(len(deck), 52)
        self.assertEqual(len({(x["rank"], x["suit"]) for x in deck}), 52)
        self.assertNotIn("JOKER", {x["rank"] for x in deck})

    def test_card_values(self):
        self.assertEqual(rtp.card_value(c("A")), 1)
        self.assertEqual(rtp.card_value(c("2")), 2)
        self.assertEqual(rtp.card_value(c("9")), 9)
        self.assertEqual(rtp.card_value(c("10")), 0)
        self.assertEqual(rtp.card_value(c("J")), 0)
        self.assertEqual(rtp.card_value(c("Q")), 0)
        self.assertEqual(rtp.card_value(c("K")), 0)

    def test_only_j_q_k_are_pictures(self):
        self.assertFalse(rtp.is_picture(c("10")))
        self.assertTrue(rtp.is_picture(c("J")))
        self.assertTrue(rtp.is_picture(c("Q")))
        self.assertTrue(rtp.is_picture(c("K")))

    def test_point_total_uses_right_digit(self):
        self.assertEqual(rtp.point_total([c("9"), c("8"), c("7")]), 4)
        self.assertEqual(rtp.point_total([c("6"), c("9"), c("4")]), 9)

    def test_hand_names(self):
        self.assertEqual(
            rtp.hand_name([c("K"), c("J"), c("Q")]),
            "Three Pictures",
        )
        self.assertEqual(
            rtp.hand_name([c("Q"), c("J"), c("9")]),
            "Double Picture Nine",
        )
        self.assertEqual(
            rtp.hand_name([c("Q"), c("7"), c("2")]),
            "Single Picture Nine",
        )
        self.assertEqual(
            rtp.hand_name([c("6"), c("9"), c("4")]),
            "Nine",
        )

    def test_three_pictures_beats_every_point_hand(self):
        three_pictures = [c("K"), c("J"), c("Q")]
        double_picture_nine = [c("Q"), c("J"), c("9")]
        self.assertEqual(
            rtp.compare_hands(three_pictures, double_picture_nine),
            "win",
        )

    def test_same_points_more_pictures_wins(self):
        single_picture_eight = [c("Q"), c("5"), c("3")]
        plain_eight = [c("9"), c("2"), c("7")]
        self.assertEqual(
            rtp.compare_hands(single_picture_eight, plain_eight),
            "win",
        )

    def test_picture_ranks_do_not_break_standoff(self):
        player = [c("K"), c("Q"), c("5")]
        dealer = [c("J", "H"), c("Q", "D"), c("5", "C")]
        self.assertEqual(rtp.compare_hands(player, dealer), "standoff")

    def test_suits_do_not_break_standoff(self):
        player = [c("Q", "S"), c("7", "C"), c("2", "H")]
        dealer = [c("Q", "D"), c("7", "D"), c("2", "S")]
        self.assertEqual(rtp.compare_hands(player, dealer), "standoff")

    def test_tie_is_point_total_only_and_can_coexist_with_main_win(self):
        player = [c("Q"), c("5"), c("3")]       # single-picture 8
        dealer = [c("9"), c("2"), c("7")]      # plain 8

        self.assertTrue(rtp.is_tie(player, dealer))
        self.assertEqual(rtp.compare_hands(player, dealer), "win")

    def test_main_regular_win_pays_one_to_one(self):
        stake = Decimal("100")
        player = [c("Q"), c("7"), c("2")]       # single-picture 9
        dealer = [c("9"), c("2"), c("7")]      # plain 8
        self.assertEqual(rtp.main_return(stake, player, dealer), Decimal("200"))

    def test_main_win_on_six_pays_one_to_two(self):
        stake = Decimal("100")
        player = [c("Q"), c("4"), c("2")]       # single-picture 6
        dealer = [c("5"), c("10"), c("10")]    # plain 5
        self.assertEqual(rtp.main_return(stake, player, dealer), Decimal("150.0"))

    def test_main_standoff_returns_stake(self):
        stake = Decimal("100")
        player = [c("Q"), c("7"), c("2")]
        dealer = [c("J"), c("7"), c("2")]
        self.assertEqual(rtp.main_return(stake, player, dealer), Decimal("100"))

    def test_main_loss_returns_zero(self):
        stake = Decimal("100")
        player = [c("5"), c("10"), c("10")]
        dealer = [c("Q"), c("4"), c("2")]
        self.assertEqual(rtp.main_return(stake, player, dealer), Decimal("0"))

    def test_tie_pays_eight_to_one(self):
        stake = Decimal("100")
        player = [c("Q"), c("5"), c("3")]
        dealer = [c("9"), c("2"), c("7")]
        self.assertEqual(rtp.tie_return(stake, player, dealer), Decimal("900"))

    def test_tie_loses_on_different_points(self):
        self.assertEqual(
            rtp.tie_return(
                100,
                [c("Q"), c("5"), c("3")],
                [c("9"), c("2"), c("6")],
            ),
            Decimal("0"),
        )

    def test_royal_three_kings(self):
        cards = [c("K"), c("K", "H"), c("K", "D")]
        self.assertEqual(rtp.royal_pictures_result(cards), "three_kings")
        self.assertEqual(rtp.royal_pictures_return(100, cards), Decimal("18900"))

    def test_royal_three_queens(self):
        cards = [c("Q"), c("Q", "H"), c("Q", "D")]
        self.assertEqual(rtp.royal_pictures_result(cards), "three_queens")
        self.assertEqual(rtp.royal_pictures_return(100, cards), Decimal("12900"))

    def test_royal_three_jacks(self):
        cards = [c("J"), c("J", "H"), c("J", "D")]
        self.assertEqual(rtp.royal_pictures_result(cards), "three_jacks")
        self.assertEqual(rtp.royal_pictures_return(100, cards), Decimal("8900"))

    def test_royal_three_pictures(self):
        cards = [c("K"), c("Q", "H"), c("J", "D")]
        self.assertEqual(rtp.royal_pictures_result(cards), "three_pictures")
        self.assertEqual(rtp.royal_pictures_return(100, cards), Decimal("1900"))

    def test_royal_any_picture_pair(self):
        cards = [c("Q"), c("Q", "H"), c("5")]
        self.assertEqual(rtp.royal_pictures_result(cards), "any_picture_pair")
        self.assertEqual(rtp.royal_pictures_return(100, cards), Decimal("900"))

    def test_royal_any_king_with_two_nonpictures(self):
        cards = [c("K"), c("5"), c("10")]
        self.assertEqual(rtp.royal_pictures_result(cards), "any_king")
        self.assertEqual(rtp.royal_pictures_return(100, cards), Decimal("200"))

    def test_royal_any_king_with_queen_and_nonpicture(self):
        cards = [c("K"), c("Q"), c("5")]
        self.assertEqual(rtp.royal_pictures_result(cards), "any_king")

    def test_royal_any_king_with_jack_and_nonpicture(self):
        cards = [c("K"), c("J"), c("5")]
        self.assertEqual(rtp.royal_pictures_result(cards), "any_king")

    def test_king_queen_jack_is_three_pictures_not_any_king(self):
        cards = [c("K"), c("Q"), c("J")]
        self.assertEqual(rtp.royal_pictures_result(cards), "three_pictures")

    def test_king_queen_queen_is_three_pictures_not_picture_pair(self):
        cards = [c("K"), c("Q"), c("Q")]
        self.assertEqual(rtp.royal_pictures_result(cards), "three_pictures")

    def test_picture_pair_requires_nonpicture_third_card(self):
        cards = [c("J"), c("J"), c("Q")]
        self.assertEqual(rtp.royal_pictures_result(cards), "three_pictures")

    def test_nonpicture_pair_does_not_win_royal_pictures(self):
        cards = [c("Q"), c("5"), c("5", "H")]
        self.assertIsNone(rtp.royal_pictures_result(cards))

    def test_queen_without_king_or_pair_does_not_win(self):
        cards = [c("Q"), c("5"), c("6")]
        self.assertIsNone(rtp.royal_pictures_result(cards))

    def test_wager_validation(self):
        self.assertTrue(rtp.validate_wager("main"))
        self.assertTrue(rtp.validate_wager("tie"))
        self.assertTrue(rtp.validate_wager("royal_pictures"))
        self.assertFalse(rtp.validate_wager("something_else"))

    def test_deal_supports_three_active_seats(self):
        outcome = rtp.deal((0, 1, 2))
        self.assertEqual(outcome["active_seats"], [0, 1, 2])
        self.assertEqual(len(outcome["dealer_cards"]), 3)
        for seat in (0, 1, 2):
            self.assertEqual(len(outcome["player_hands"][seat]), 3)

    def test_invalid_hand_length_rejected(self):
        with self.assertRaises(ValueError):
            rtp.point_total([c("A"), c("2")])

    def test_invalid_active_seat_rejected(self):
        with self.assertRaises(ValueError):
            rtp.deal((7,))


if __name__ == "__main__":
    unittest.main()
