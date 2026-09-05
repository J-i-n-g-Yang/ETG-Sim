import unittest
from unittest.mock import patch

from app import app


def card(rank, suit="S"):
    return {
        "rank": rank,
        "suit": suit,
    }


def shoe_with(*front_cards):
    """
    Dueling 8s consumes the shoe with pop(0).

    Put deterministic cards first, followed by
    enough harmless filler for player/dealer draws.
    """
    filler = [
        card("2", "C"),
        card("3", "D"),
        card("4", "H"),
        card("5", "C"),
        card("6", "D"),
        card("7", "H"),
        card("9", "C"),
        card("J", "H"),
        card("Q", "C"),
        card("K", "D"),
        card("A", "H"),
    ] * 30

    return [
        *front_cards,
        *filler,
    ]


class TestDueling8sSoloIntegration(
    unittest.TestCase
):

    def setUp(self):
        app.config.update(
            TESTING=True,
            MAX_BET=20000,
            STARTING_CREDITS=100000,
        )

        self.client = app.test_client()

    # ============================================================
    # HELPERS
    # ============================================================

    def deal(self, bets, **extra):
        payload = {
            "game": "dueling_8s_21",
            "bets": bets,
        }

        payload.update(extra)

        return self.client.post(
            "/api/solo/dueling-8s/deal",
            json=payload,
        )

    def action(
        self,
        state_token,
        seat,
        hand_index,
        action,
        **extra,
    ):
        payload = {
            "state_token": state_token,
            "seat": seat,
            "hand_index": hand_index,
            "action": action,
        }

        payload.update(extra)

        return self.client.post(
            "/api/solo/dueling-8s/action",
            json=payload,
        )

    def settle(self, state_token):
        return self.client.post(
            "/api/solo/dueling-8s/settle",
            json={
                "state_token": state_token,
            },
        )

    @staticmethod
    def result_for(data, seat, wager_type):
        return next(
            result
            for result in data["results"]
            if (
                result.get("seat") == seat
                and
                result.get("wager_type") == wager_type
            )
        )

    # ============================================================
    # PAGE
    # ============================================================

    def test_page_renders(self):
        response = self.client.get(
            "/api/solo/dueling-8s"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def test_deal_requires_main(self):
        response = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "678",
                    "amount": 100,
                },
            ]
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Main wager",
            response.get_json()["error"],
        )

    def test_invalid_wager_rejected(self):
        response = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "not_a_bet",
                    "amount": 100,
                },
            ]
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_invalid_seat_rejected(self):
        response = self.deal(
            [
                {
                    "seat": 7,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_unknown_game_rejected(self):
        response = self.client.post(
            "/api/solo/dueling-8s/deal",
            json={
                "game": "wrong_game",
                "bets": [
                    {
                        "seat": 0,
                        "wager_type": "main",
                        "amount": 100,
                    },
                ],
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_total_initial_stake_limit_enforced(self):
        response = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 15000,
                },
                {
                    "seat": 1,
                    "wager_type": "main",
                    "amount": 6000,
                },
            ]
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # ============================================================
    # DEAL / PERMANENT EIGHTS
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_deal_returns_permanent_eights(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("5", "H"),
        )

        response = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertIn(
            "state_token",
            data,
        )

        self.assertEqual(
            data["active_seats"],
            [0],
        )

        hand = (
            data["seats"]["0"]
            ["hands"][0]
        )

        self.assertEqual(
            hand["cards"][0]["rank"],
            "8",
        )

        self.assertEqual(
            hand["cards"][0]["suit"],
            "S",
        )

        self.assertTrue(
            hand["cards"][0].get(
                "permanent"
            )
        )

        self.assertEqual(
            data["dealer_cards"][0]["rank"],
            "8",
        )

        self.assertEqual(
            data["dealer_cards"][0]["suit"],
            "S",
        )

        self.assertTrue(
            data["dealer_cards"][0].get(
                "permanent"
            )
        )

    # ============================================================
    # THREE SEATS
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_three_seats_can_be_active(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("2", "C"),
            card("3", "D"),
            card("4", "H"),
        )

        response = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 1,
                    "wager_type": "main",
                    "amount": 200,
                },
                {
                    "seat": 2,
                    "wager_type": "main",
                    "amount": 300,
                },
            ]
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["active_seats"],
            [0, 1, 2],
        )

        self.assertEqual(
            data["current_seat"],
            0,
        )

        for seat in (
            "0",
            "1",
            "2",
        ):
            self.assertIn(
                seat,
                data["seats"],
            )

            self.assertEqual(
                data["seats"][seat]
                ["hands"][0]
                ["cards"][0]["rank"],
                "8",
            )

    # ============================================================
    # TURN ORDER
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_turn_progresses_across_seats(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("2", "C"),
            card("3", "D"),
            card("4", "H"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 1,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 2,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        ).get_json()

        self.assertEqual(
            deal["current_seat"],
            0,
        )

        first = self.action(
            deal["state_token"],
            0,
            0,
            "stand",
        ).get_json()

        self.assertEqual(
            first["current_seat"],
            1,
        )

        second = self.action(
            first["state_token"],
            1,
            0,
            "stand",
        ).get_json()

        self.assertEqual(
            second["current_seat"],
            2,
        )

        third = self.action(
            second["state_token"],
            2,
            0,
            "stand",
        ).get_json()

        self.assertTrue(
            third["all_done"]
        )

        self.assertEqual(
            third["stage"],
            "settle",
        )

    # ============================================================
    # WRONG SEAT
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_wrong_seat_cannot_act(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("2"),
            card("3"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 1,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        ).get_json()

        response = self.action(
            deal["state_token"],
            1,
            0,
            "stand",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "another seat",
            response.get_json()[
                "error"
            ].lower(),
        )

    # ============================================================
    # PARTIAL DOUBLE
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_partial_double_charges_requested_amount(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("2", "C"),
            card("3", "D"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
            ],
            table_minimum=10,
        ).get_json()

        response = self.action(
            deal["state_token"],
            0,
            0,
            "double",
            amount=40,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["extra_stake"],
            40,
        )

        self.assertEqual(
            data["extra_wager"],
            40,
        )

        hand = (
            data["seats"]["0"]
            ["hands"][0]
        )

        self.assertEqual(
            hand["stake"],
            140,
        )

        self.assertEqual(
            hand["double_amount"],
            40,
        )

    def test_double_below_table_minimum_rejected(self):
        with patch(
            "api.solo.dueling_8s.make_shoe"
        ) as mock_shoe:
            mock_shoe.return_value = shoe_with(
                card("2"),
                card("3"),
            )

            deal = self.deal(
                [
                    {
                        "seat": 0,
                        "wager_type": "main",
                        "amount": 100,
                    },
                ],
                table_minimum=25,
            ).get_json()

            response = self.action(
                deal["state_token"],
                0,
                0,
                "double",
                amount=20,
            )

        self.assertEqual(
            response.status_code,
            400,
        )

    # ============================================================
    # SPLIT
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_split_only_when_second_card_is_eight(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("8", "H"),
            card("2", "C"),
            card("3", "D"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        ).get_json()

        actions = (
            deal["seats"]["0"]
            ["hands"][0]
            ["available_actions"]
        )

        self.assertIn(
            "split",
            actions,
        )

        response = self.action(
            deal["state_token"],
            0,
            0,
            "split",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["extra_stake"],
            100,
        )

        self.assertEqual(
            len(
                data["seats"]["0"]
                ["hands"]
            ),
            2,
        )

        self.assertEqual(
            data["current_seat"],
            0,
        )

        self.assertEqual(
            data["current_hand"],
            0,
        )

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_non_eight_pair_cannot_split(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("7", "H"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        ).get_json()

        actions = (
            deal["seats"]["0"]
            ["hands"][0]
            ["available_actions"]
        )

        self.assertNotIn(
            "split",
            actions,
        )

    # ============================================================
    # SURRENDER
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_surrender_and_settle(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("5", "H"),
            card("K", "D"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        ).get_json()

        action = self.action(
            deal["state_token"],
            0,
            0,
            "surrender",
        )

        self.assertEqual(
            action.status_code,
            200,
        )

        action_data = action.get_json()

        self.assertTrue(
            action_data["all_done"]
        )

        settled = self.settle(
            action_data["state_token"]
        )

        self.assertEqual(
            settled.status_code,
            200,
        )

        data = settled.get_json()

        hand = (
            data["outcome"]
            ["seats"]["0"]
            ["hands"][0]
        )

        self.assertEqual(
            hand["result"],
            "surrender",
        )

        self.assertEqual(
            hand["return"],
            50.0,
        )

    # ============================================================
    # SIDE BET STORAGE
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_side_bets_are_stored_per_seat(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("2", "C"),
            card("3", "D"),
        )

        response = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "21_plus",
                    "amount": 25,
                },
                {
                    "seat": 1,
                    "wager_type": "main",
                    "amount": 200,
                },
                {
                    "seat": 1,
                    "wager_type": "tie_18",
                    "amount": 50,
                },
            ]
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["seats"]["0"]
            ["bets"]["21_plus"],
            25,
        )

        self.assertNotIn(
            "tie_18",
            data["seats"]["0"][
                "bets"
            ],
        )

        self.assertEqual(
            data["seats"]["1"]
            ["bets"]["tie_18"],
            50,
        )

        self.assertNotIn(
            "21_plus",
            data["seats"]["1"][
                "bets"
            ],
        )

    # ============================================================
    # 6-7-8 ENDPOINT
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_678_wins_through_endpoint(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            # Player initial:
            # permanent 8S + 6C
            card("6", "C"),

            # Player hit -> 7D
            card("7", "D"),

            # Dealer:
            # permanent 8S + KC = 18
            card("K", "C"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "678",
                    "amount": 25,
                },
            ]
        ).get_json()

        action = self.action(
            deal["state_token"],
            0,
            0,
            "hit",
        )

        self.assertEqual(
            action.status_code,
            200,
        )

        action_data = (
            action.get_json()
        )

        # 8 + 6 + 7 = 21.
        self.assertTrue(
            action_data["all_done"]
        )

        settled = self.settle(
            action_data[
                "state_token"
            ]
        )

        self.assertEqual(
            settled.status_code,
            200,
        )

        data = settled.get_json()

        result = self.result_for(
            data,
            0,
            "678",
        )

        self.assertTrue(
            result["win"]
        )

        # Mixed-suit 6-7-8 is 1:1 profit in the
        # current rules layer. six_seven_eight_bonus()
        # currently returns the bonus/profit amount.
        self.assertEqual(
            result["return"],
            25.0,
        )

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_678_all_spades_pays_five_to_one(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("6", "S"),
            card("7", "S"),
            card("K", "C"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "678",
                    "amount": 20,
                },
            ]
        ).get_json()

        action = self.action(
            deal["state_token"],
            0,
            0,
            "hit",
        ).get_json()

        data = self.settle(
            action["state_token"]
        ).get_json()

        result = self.result_for(
            data,
            0,
            "678",
        )

        self.assertTrue(
            result["win"]
        )

        self.assertEqual(
            result["return"],
            100.0,
        )

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_678_loses_after_split(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            # Initial second 8 -> split available.
            card("8", "H"),

            # First split hand:
            # 8S + 6C
            card("6", "C"),

            # Second split hand:
            card("2", "D"),

            # Hit first split hand -> 7D.
            card("7", "D"),

            # Dealer draw.
            card("K", "C"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "678",
                    "amount": 25,
                },
            ]
        ).get_json()

        split = self.action(
            deal["state_token"],
            0,
            0,
            "split",
        ).get_json()

        first = self.action(
            split["state_token"],
            0,
            0,
            "hit",
        ).get_json()

        # First split hand is now 21.
        # Finish second split hand.
        if not first["all_done"]:
            second = self.action(
                first["state_token"],
                0,
                first["current_hand"],
                "stand",
            ).get_json()
        else:
            second = first

        data = self.settle(
            second["state_token"]
        ).get_json()

        result = self.result_for(
            data,
            0,
            "678",
        )

        self.assertFalse(
            result["win"]
        )

        self.assertEqual(
            result["return"],
            0.0,
        )

    # ============================================================
    # SUPERB 8s ENDPOINT
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_superb_8s_two_eights(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            # Permanent 8S + 8H.
            card("8", "H"),

            # Split replacement cards aren't used
            # because player will stand.
            card("K", "C"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "superb_8s",
                    "amount": 10,
                },
            ]
        ).get_json()

        action = self.action(
            deal["state_token"],
            0,
            0,
            "stand",
        ).get_json()

        data = self.settle(
            action["state_token"]
        ).get_json()

        result = self.result_for(
            data,
            0,
            "superb_8s",
        )

        self.assertTrue(
            result["win"]
        )

        # 3:1 profit + stake = 40 total return.
        self.assertEqual(
            result["return"],
            40.0,
        )

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_superb_8s_three_eights(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("8", "H"),
            card("8", "D"),
            card("K", "C"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "superb_8s",
                    "amount": 10,
                },
            ]
        ).get_json()

        # Do NOT split. Hit the 8+8 hand.
        action = self.action(
            deal["state_token"],
            0,
            0,
            "hit",
        ).get_json()

        # 24 busts, so player decisions finish.
        self.assertTrue(
            action["all_done"]
        )

        data = self.settle(
            action["state_token"]
        ).get_json()

        result = self.result_for(
            data,
            0,
            "superb_8s",
        )

        self.assertTrue(
            result["win"]
        )

        # 8:1 profit + stake.
        self.assertEqual(
            result["return"],
            90.0,
        )

    # ============================================================
    # TIE ON 18
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_tie_on_18_wins_through_endpoint(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            # Player: 8 + K = 18.
            card("K", "H"),

            # Dealer: 8 + Q = 18.
            card("Q", "D"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "tie_18",
                    "amount": 10,
                },
            ]
        ).get_json()

        action = self.action(
            deal["state_token"],
            0,
            0,
            "stand",
        ).get_json()

        data = self.settle(
            action["state_token"]
        ).get_json()

        result = self.result_for(
            data,
            0,
            "tie_18",
        )

        self.assertTrue(
            result["win"]
        )

        self.assertEqual(
            result["return"],
            90.0,
        )

    # ============================================================
    # 21+
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_21_plus_in_endpoint(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            # Player: 8 + K = 18.
            card("K", "H"),

            # Dealer:
            # 8 + 6 = 14
            # + K = 24 bust
            #
            # Total dealer cards = 3.
            card("6", "C"),
            card("K", "D"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "21_plus",
                    "amount": 10,
                },
            ]
        ).get_json()

        action = self.action(
            deal["state_token"],
            0,
            0,
            "stand",
        ).get_json()

        data = self.settle(
            action["state_token"]
        ).get_json()

        result = self.result_for(
            data,
            0,
            "21_plus",
        )

        self.assertTrue(
            result["win"]
        )

        # Three-card dealer bust = 2:1 profit,
        # plus returned stake = 30.
        self.assertEqual(
            result["return"],
            30.0,
        )

        self.assertTrue(
            data["outcome"][
                "dealer_bust"
            ]
        )

        self.assertEqual(
            data["outcome"][
                "dealer_card_count"
            ],
            3,
        )

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_21_plus_loses_without_dealer_bust(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("K", "H"),
            card("Q", "D"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "21_plus",
                    "amount": 10,
                },
            ]
        ).get_json()

        action = self.action(
            deal["state_token"],
            0,
            0,
            "stand",
        ).get_json()

        data = self.settle(
            action["state_token"]
        ).get_json()

        result = self.result_for(
            data,
            0,
            "21_plus",
        )

        self.assertFalse(
            result["win"]
        )

        self.assertEqual(
            result["return"],
            0.0,
        )

    # ============================================================
    # MULTI-SEAT SIDE-BET ISOLATION
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_side_bet_results_remain_seat_specific(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            # Seat 0: 8 + K = 18.
            card("K", "H"),

            # Seat 1: 8 + 2 = 10.
            card("2", "C"),

            # Dealer: 8 + Q = 18.
            card("Q", "D"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "tie_18",
                    "amount": 10,
                },
                {
                    "seat": 1,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 1,
                    "wager_type": "tie_18",
                    "amount": 10,
                },
            ]
        ).get_json()

        seat0 = self.action(
            deal["state_token"],
            0,
            0,
            "stand",
        ).get_json()

        seat1 = self.action(
            seat0["state_token"],
            1,
            0,
            "stand",
        ).get_json()

        data = self.settle(
            seat1["state_token"]
        ).get_json()

        result0 = self.result_for(
            data,
            0,
            "tie_18",
        )

        result1 = self.result_for(
            data,
            1,
            "tie_18",
        )

        self.assertTrue(
            result0["win"]
        )

        self.assertFalse(
            result1["win"]
        )

    # ============================================================
    # ACCOUNTING
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_net_equals_return_minus_all_stakes(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("2", "C"),
            card("3", "D"),
            card("K", "H"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
                {
                    "seat": 0,
                    "wager_type": "21_plus",
                    "amount": 25,
                },
            ],
            table_minimum=10,
        ).get_json()

        doubled = self.action(
            deal["state_token"],
            0,
            0,
            "double",
            amount=40,
        ).get_json()

        data = self.settle(
            doubled["state_token"]
        ).get_json()

        self.assertEqual(
            data["total_wager"],
            165.0,
        )

        self.assertEqual(
            data["extra_wager"],
            40.0,
        )

        self.assertAlmostEqual(
            data["net"],
            data["total_return"]
            -
            data["total_wager"],
        )

    # ============================================================
    # SETTLEMENT GUARD
    # ============================================================

    @patch(
        "api.solo.dueling_8s.make_shoe"
    )
    def test_cannot_settle_before_player_decision(
        self,
        mock_shoe,
    ):
        mock_shoe.return_value = shoe_with(
            card("2", "C"),
        )

        deal = self.deal(
            [
                {
                    "seat": 0,
                    "wager_type": "main",
                    "amount": 100,
                },
            ]
        ).get_json()

        response = self.settle(
            deal["state_token"]
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "decisions",
            response.get_json()[
                "error"
            ].lower(),
        )


if __name__ == "__main__":
    unittest.main()