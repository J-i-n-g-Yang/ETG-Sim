import unittest
from unittest.mock import patch

from app import app


def card(rank, suit="S"):
    return {"rank": rank, "suit": suit}


def fixed_deck(*draw_order):
    """
    royal_three_pictures.make_deck() is consumed with pop(0) by the
    API integration block below.

    draw_order therefore represents:
      Seat 0 x3, Seat 1 x3, Seat 2 x3, Dealer x3
    for whichever seats are active.
    """
    filler = [
        card("2", "C"), card("3", "D"), card("4", "H"),
        card("5", "C"), card("6", "D"), card("7", "H"),
        card("8", "C"), card("9", "D"), card("10", "H"),
        card("J", "C"), card("Q", "D"), card("K", "H"),
        card("A", "C"),
    ] * 10
    return [*draw_order, *filler]


class TestRoyalThreePicturesIntegration(unittest.TestCase):

    def setUp(self):
        app.config.update(
            TESTING=True,
            MAX_BET=20000,
            STARTING_CREDITS=100000,
        )
        self.client = app.test_client()

    def test_page_renders(self):
        r = self.client.get("/api/solo/royal-three-pictures")
        self.assertEqual(r.status_code, 200)

    def test_no_bets_rejected(self):
        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={"bets": []},
        )
        self.assertEqual(r.status_code, 400)

    def test_invalid_seat_rejected(self):
        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 7, "wager_type": "main", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_invalid_wager_rejected(self):
        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "not_a_bet", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_active_seat_requires_main(self):
        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "tie", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("Main wager", r.get_json()["error"])

    def test_total_stake_limit_enforced(self):
        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "main", "amount": 15000},
                    {"seat": 0, "wager_type": "tie", "amount": 6000},
                ]
            },
        )
        self.assertEqual(r.status_code, 400)

    @patch("api.solo.royal_three_pictures.make_deck")
    def test_three_seats_share_one_dealer_hand(self, mock_deck):
        mock_deck.return_value = fixed_deck(
            # Seat 0
            card("K"), card("5"), card("4"),
            # Seat 1
            card("Q"), card("7"), card("2"),
            # Seat 2
            card("J"), card("6"), card("2"),
            # Dealer
            card("9"), card("8"), card("1") if False else card("A"),
        )

        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "main", "amount": 100},
                    {"seat": 1, "wager_type": "main", "amount": 100},
                    {"seat": 2, "wager_type": "main", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["active_seats"], [0, 1, 2])
        self.assertEqual(set(data["seats"].keys()), {"0", "1", "2"})
        self.assertEqual(len(data["dealer_cards"]), 3)
        self.assertEqual(data["stage"], "settled")

    @patch("api.solo.royal_three_pictures.make_deck")
    def test_tie_can_win_while_main_also_wins(self, mock_deck):
        mock_deck.return_value = fixed_deck(
            # Player: Single Picture 8
            card("Q"), card("5"), card("3"),
            # Dealer: plain 8
            card("9"), card("2"), card("7"),
        )

        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "main", "amount": 100},
                    {"seat": 0, "wager_type": "tie", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()

        seat = data["outcome"]["seats"]["0"]
        self.assertEqual(seat["main_result"], "win")
        self.assertTrue(seat["tie"])

        by_wager = {
            x["wager_type"]: x
            for x in data["results"]
            if x["seat"] == 0
        }
        self.assertEqual(by_wager["main"]["return"], 200.0)
        self.assertEqual(by_wager["tie"]["return"], 900.0)
        self.assertEqual(data["total_wager"], 200.0)
        self.assertEqual(data["total_return"], 1100.0)
        self.assertEqual(data["net"], 900.0)

    @patch("api.solo.royal_three_pictures.make_deck")
    def test_six_point_main_win_pays_half_profit(self, mock_deck):
        mock_deck.return_value = fixed_deck(
            # Player: Single Picture 6
            card("Q"), card("4"), card("2"),
            # Dealer: plain 5
            card("5"), card("10"), card("10"),
        )

        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "main", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["total_return"], 150.0)
        self.assertEqual(data["net"], 50.0)

    @patch("api.solo.royal_three_pictures.make_deck")
    def test_main_standoff_pushes(self, mock_deck):
        mock_deck.return_value = fixed_deck(
            card("Q"), card("7"), card("2"),
            card("J"), card("7"), card("2"),
        )

        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "main", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["outcome"]["seats"]["0"]["main_result"], "standoff")
        self.assertEqual(data["total_return"], 100.0)
        self.assertEqual(data["net"], 0.0)

    @patch("api.solo.royal_three_pictures.make_deck")
    def test_royal_pictures_settles_per_seat(self, mock_deck):
        mock_deck.return_value = fixed_deck(
            # Seat 0: three Kings
            card("K", "S"), card("K", "H"), card("K", "D"),
            # Seat 1: no Royal Pictures win
            card("Q"), card("5"), card("6"),
            # Dealer
            card("9"), card("8"), card("7"),
        )

        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "main", "amount": 100},
                    {"seat": 0, "wager_type": "royal_pictures", "amount": 100},
                    {"seat": 1, "wager_type": "main", "amount": 100},
                    {"seat": 1, "wager_type": "royal_pictures", "amount": 100},
                ]
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()

        seat0 = data["outcome"]["seats"]["0"]
        seat1 = data["outcome"]["seats"]["1"]

        self.assertEqual(seat0["royal_pictures"], "three_kings")
        self.assertIsNone(seat1["royal_pictures"])

        royal_results = {
            x["seat"]: x
            for x in data["results"]
            if x["wager_type"] == "royal_pictures"
        }
        self.assertEqual(royal_results[0]["return"], 18900.0)
        self.assertEqual(royal_results[1]["return"], 0.0)

    @patch("api.solo.royal_three_pictures.make_deck")
    def test_side_bets_are_isolated_by_seat(self, mock_deck):
        mock_deck.return_value = fixed_deck(
            card("K"), card("5"), card("4"),
            card("Q"), card("7"), card("2"),
            card("9"), card("8"), card("7"),
        )

        r = self.client.post(
            "/api/solo/royal-three-pictures/deal",
            json={
                "bets": [
                    {"seat": 0, "wager_type": "main", "amount": 100},
                    {"seat": 0, "wager_type": "tie", "amount": 25},
                    {"seat": 1, "wager_type": "main", "amount": 100},
                    {"seat": 1, "wager_type": "royal_pictures", "amount": 50},
                ]
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()

        self.assertEqual(data["seats"]["0"]["bets"]["tie"], 25.0)
        self.assertNotIn("royal_pictures", data["seats"]["0"]["bets"])
        self.assertEqual(data["seats"]["1"]["bets"]["royal_pictures"], 50.0)
        self.assertNotIn("tie", data["seats"]["1"]["bets"])


if __name__ == "__main__":
    unittest.main()
