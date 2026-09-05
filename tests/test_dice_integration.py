import unittest
from unittest.mock import patch

from flask import Flask

from api.solo import solo_bp


class TestDiceIntegration(unittest.TestCase):

    def setUp(self):
        app = Flask(__name__)
        app.config.update(TESTING=True, MAX_BET=20000, STARTING_CREDITS=100000)
        app.register_blueprint(solo_bp, url_prefix="/api/solo")
        self.client = app.test_client()

    def post(self, path, payload):
        response = self.client.post(path, json=payload)
        return response, response.get_json()

    def roll(self, game, bets, state=None):
        return self.post("/api/solo/dice/roll", {
            "game": game,
            "bets": [{"wager_type": w, "amount": a} for w, a in bets],
            "state": state or {},
        })

    def test_unknown_dice_game_rejected(self):
        response, data = self.roll("banana", [("small", 100)])
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    def test_sicbo_endpoint_uses_one_shared_three_dice_outcome(self):
        with patch("game.sicbo.random.randint", side_effect=[1, 2, 4]):
            response, data = self.roll("sicbo", [("odd", 100), ("total_7", 100)])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["outcome"]["dice"], [1, 2, 4])
        self.assertEqual(data["total_return"], 1500.0)
        self.assertEqual(data["total_wager"], 200.0)

    def test_gfd_endpoint_uses_one_shared_four_dice_outcome(self):
        with patch("game.great_fortune_dice.random.randint", side_effect=[1, 2, 3, 4]):
            response, data = self.roll(
                "great_fortune_dice",
                [("small", 100), ("straight", 100)]
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["outcome"]["dice"], [1, 2, 3, 4])
        self.assertEqual(data["total_return"], 1800.0)

    def test_craps_point_state_survives_between_api_rolls(self):
        with patch("game.craps.random.randint", side_effect=[3, 3]):
            response, first = self.roll("craps", [("pass_line", 100)])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(first["state"]["point"], 6)
        self.assertEqual(first["state"]["bets"]["pass_line"], 100.0)

        with patch("game.craps.random.randint", side_effect=[2, 4]):
            response, second = self.roll("craps", [], first["state"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            next(r for r in second["results"] if r["wager_type"] == "pass_line")["return"],
            200.0
        )
        self.assertIsNone(second["state"]["point"])

    def test_craps_come_point_survives_between_api_rolls(self):
        with patch("game.craps.random.randint", side_effect=[3, 3]):
            _, first = self.roll("craps", [("pass_line", 100)])

        with patch("game.craps.random.randint", side_effect=[2, 3]):
            response, second = self.roll("craps", [("come", 100)], first["state"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(second["state"]["come"]["5"], 100.0)

        with patch("game.craps.random.randint", side_effect=[1, 4]):
            response, third = self.roll("craps", [], second["state"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            next(r for r in third["results"] if r["wager_type"] == "come_point_5")["return"],
            200.0
        )

    def test_craps_action_endpoint_toggles_working_status(self):
        state = {
            "point": None,
            "bets": {"hard_6": 100},
            "working": {},
        }
        response, data = self.post("/api/solo/dice/craps/action", {
            "state": state,
            "wager_type": "hard_6",
            "action": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["state"]["working"]["hard_6"])


if __name__ == "__main__":
    unittest.main()
