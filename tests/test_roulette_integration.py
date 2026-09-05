import unittest
from unittest.mock import patch

from app import create_app


class TestRouletteIntegration(unittest.TestCase):

    def setUp(self):
        self.app = create_app()

        self.app.config.update(
            TESTING=True,
            MAX_BET=20000,
        )

        self.client = self.app.test_client()

    # ============================================================
    # HELPERS
    # ============================================================

    def spin(
        self,
        game,
        bets,
    ):
        response = self.client.post(
            "/api/solo/roulette/spin",
            json={
                "game": game,
                "bets": bets,
            },
        )

        return (
            response,
            response.get_json(),
        )

    def bet(
        self,
        wager_type,
        amount=100,
    ):
        return {
            "wager_type":
                wager_type,

            "amount":
                amount,
        }

    # ============================================================
    # VALIDATION
    # ============================================================

    def test_unknown_roulette_game_rejected(self):
        response, data = self.spin(
            "not_a_roulette_game",
            [
                self.bet(
                    "straight_17"
                )
            ],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Unknown Roulette game",
            data["error"],
        )

    def test_no_bets_rejected(self):
        response, data = self.spin(
            "roulette_single_zero",
            [],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "No bets supplied",
            data["error"],
        )

    def test_invalid_wager_type_rejected(self):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "banana"
                )
            ],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Invalid wager_type",
            data["error"],
        )

    def test_negative_amount_rejected(self):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "red",
                    -100,
                )
            ],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            data["error"],
            "Invalid amount",
        )

    def test_zero_amount_rejected(self):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "red",
                    0,
                )
            ],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_single_wager_above_limit_rejected(self):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "red",
                    20001,
                )
            ],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_total_stake_above_limit_rejected(self):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "red",
                    11000,
                ),
                self.bet(
                    "black",
                    10000,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Total stake per spin",
            data["error"],
        )

    # ============================================================
    # SINGLE ZERO
    # ============================================================

    @patch(
        "game.roulette_single_zero.random.choice",
        return_value=17,
    )
    def test_single_zero_endpoint_uses_one_shared_outcome(
        self,
        mock_choice,
    ):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "straight_17",
                    100,
                ),
                self.bet(
                    "black",
                    100,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            data["game"],
            "roulette_single_zero",
        )

        self.assertEqual(
            data["outcome"]["number"],
            17,
        )

        self.assertEqual(
            data["total_wager"],
            200.0,
        )

        results = {
            result["wager_type"]:
                result
            for result in data["results"]
        }

        self.assertEqual(
            results[
                "straight_17"
            ]["return"],
            3600.0,
        )

        # 17 is black.
        self.assertEqual(
            results[
                "black"
            ]["return"],
            200.0,
        )

        self.assertEqual(
            data["total_return"],
            3800.0,
        )

        self.assertEqual(
            data["net"],
            3600.0,
        )

        self.assertEqual(
            mock_choice.call_count,
            1,
        )

    # ============================================================
    # DOUBLE ZERO
    # ============================================================

    @patch(
        "game.roulette_double_zero.random.choice",
        return_value="00",
    )
    def test_double_zero_endpoint_can_land_on_double_zero(
        self,
        mock_choice,
    ):
        response, data = self.spin(
            "roulette_double_zero",
            [
                self.bet(
                    "straight_00",
                    100,
                ),
                self.bet(
                    "split_0_00",
                    100,
                ),
                self.bet(
                    "red",
                    100,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            data["outcome"]["number"],
            "00",
        )

        results = {
            result["wager_type"]:
                result
            for result in data["results"]
        }

        self.assertEqual(
            results[
                "straight_00"
            ]["return"],
            3600.0,
        )

        self.assertEqual(
            results[
                "split_0_00"
            ]["return"],
            1800.0,
        )

        self.assertEqual(
            results[
                "red"
            ]["return"],
            0.0,
        )

        self.assertEqual(
            mock_choice.call_count,
            1,
        )

    # ============================================================
    # SANDS ROULETTE
    # ============================================================

    @patch(
        "game.roulette_sands_roulette.random.choice",
        return_value="S",
    )
    def test_sands_endpoint_can_land_on_s(
        self,
        mock_choice,
    ):
        response, data = self.spin(
            "roulette_sands",
            [
                self.bet(
                    "straight_S",
                    100,
                ),
                self.bet(
                    "green",
                    100,
                ),
                self.bet(
                    "top_line",
                    100,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            data["game"],
            "roulette_sands",
        )

        self.assertEqual(
            data["outcome"]["number"],
            "S",
        )

        results = {
            result["wager_type"]:
                result
            for result in data["results"]
        }

        self.assertEqual(
            results[
                "straight_S"
            ]["return"],
            3600.0,
        )

        self.assertEqual(
            results[
                "green"
            ]["return"],
            1200.0,
        )

        self.assertEqual(
            results[
                "top_line"
            ]["return"],
            600.0,
        )

        self.assertEqual(
            mock_choice.call_count,
            1,
        )

    # ============================================================
    # ACCOUNTING
    # ============================================================

    @patch(
        "game.roulette_single_zero.random.choice",
        return_value=1,
    )
    def test_endpoint_net_is_return_minus_total_wager(
        self,
        mock_choice,
    ):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "red",
                    100,
                ),
                self.bet(
                    "straight_1",
                    100,
                ),
                self.bet(
                    "black",
                    100,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            data["total_wager"],
            300.0,
        )

        # Red:
        # 100 stake + 100 profit = 200
        #
        # Straight 1:
        # 100 stake + 3500 profit = 3600
        #
        # Black:
        # loses = 0

        self.assertEqual(
            data["total_return"],
            3800.0,
        )

        self.assertEqual(
            data["net"],
            3500.0,
        )

    # ============================================================
    # RESPONSE CONTRACT
    # ============================================================

    @patch(
        "game.roulette_single_zero.random.choice",
        return_value=8,
    )
    def test_response_contains_expected_fields(
        self,
        mock_choice,
    ):
        response, data = self.spin(
            "roulette_single_zero",
            [
                self.bet(
                    "black",
                    100,
                )
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        for key in (
            "game",
            "outcome",
            "results",
            "total_wager",
            "total_return",
            "net",
        ):
            self.assertIn(
                key,
                data,
            )

        self.assertIn(
            "number",
            data["outcome"],
        )

        self.assertEqual(
            len(
                data["results"]
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()