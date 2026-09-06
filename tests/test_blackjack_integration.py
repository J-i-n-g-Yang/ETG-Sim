import unittest
from unittest.mock import patch

from flask import Flask

from api.solo import solo_bp, _dec, _enc


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


class TestBlackjackIntegration(unittest.TestCase):
    """
    Integration tests for the real Solo Blackjack endpoints:

        POST /api/solo/blackjack/deal
        POST /api/solo/blackjack/action
        POST /api/solo/blackjack/settle

    These tests intentionally use Flask's test client so they exercise
    the same API flow used by blackjack_solo.js.
    """

    def setUp(self):
        app = Flask(__name__)
        app.config.update(
            TESTING=True,
            MAX_BET=20000,
            STARTING_CREDITS=100000,
        )
        app.register_blueprint(solo_bp, url_prefix="/api/solo")
        self.app = app
        self.client = app.test_client()

    def post(self, path, payload):
        response = self.client.post(path, json=payload)
        data = response.get_json()
        return response, data

    def deal(self, game, bets):
        return self.post(
            "/api/solo/blackjack/deal",
            {"game": game, "bets": bets},
        )

    def action(self, token, seat, action):
        return self.post(
            "/api/solo/blackjack/action",
            {
                "state_token": token,
                "seat": seat,
                "action": action,
            },
        )

    def settle(self, token):
        return self.post(
            "/api/solo/blackjack/settle",
            {"state_token": token},
        )

    @staticmethod
    def main_bet(seat=0, amount=100):
        return {
            "seat": seat,
            "wager_type": f"seat{seat}_main",
            "amount": amount,
        }

    # ------------------------------------------------------------------
    # Endpoint validation
    # ------------------------------------------------------------------

    def test_unknown_blackjack_variant_rejected(self):
        response, data = self.deal(
            "not_a_game",
            [self.main_bet()],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    def test_no_bets_rejected(self):
        response, data = self.deal(
            "blackjack_lucky8",
            [],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    def test_invalid_action_rejected(self):
        # Construct a valid minimal state token directly so this test
        # is deterministic and only checks action validation.
        st = self._state(
            game="blackjack_lucky8",
            player=[C("10"), C("6", "H")],
            dealer=[C("9", "D"), C("7", "C")],
        )
        response, data = self.action(_enc(st), 0, "dance")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    def test_deal_rejects_wager_for_different_seat(self):
        for game in (
            "blackjack_lucky8",
            "blackjack_freebet",
            "blackjack_kingsbounty",
            "pontoon",
        ):
            with self.subTest(game=game):
                response = self.client.post(
                    "/api/solo/blackjack/deal",
                    json={
                        "game": game,
                        "bets": [
                            {
                                "seat": 1,
                                "wager_type": "seat0_main",
                                "amount": 100,
                            }
                        ],
                    },
                )

                self.assertEqual(
                    response.status_code,
                    400,
                )

                self.assertEqual(
                    response.get_json()["error"],
                    "Invalid bet",
                )

    def test_wrong_seat_cannot_act(self):
        st = self._state(
            game="blackjack_lucky8",
            player=[C("10"), C("6", "H")],
            dealer=[C("9", "D"), C("7", "C")],
        )
        response, data = self.action(_enc(st), 1, "stand")
        self.assertEqual(response.status_code, 400)
        self.assertIn("another seat", data["error"].lower())

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def _state(
        self,
        game,
        player,
        dealer,
        stake=100.0,
        shoe=None,
        status="playing",
        extra_hand_fields=None,
        bets_by_seat=None,
    ):
        """
        Build a state in the exact shape consumed by api.solo.
        This bypasses RNG while still driving the real /action and
        /settle endpoints.
        """
        extra_hand_fields = extra_hand_fields or {}
        shoe = list(shoe or [])

        h = {
            "cards": list(player),
            "status": status,
            "stake": float(stake),
            "paid_extra": 0.0,
            "free_marker": False,
            "from_split": False,
            "from_split_aces": False,
            "split_aces": False,
            "doubled": False,
            "surrendered": False,
            "double_withdrawn": False,
            "immediate_paid": 0.0,
        }
        h.update(extra_hand_fields)

        if bets_by_seat is None:
            bets_by_seat = {
                "0": {"seat0_main": float(stake)}
            }

        return {
            "game": game,
            "shoe": shoe,
            "dealer_up": dealer[0],
            "dealer_hole": dealer[1],
            "dealer_cards": list(dealer),
            "active_seats": [0],
            "bets_by_seat": bets_by_seat,
            "hands": {"0": [h]},
            "seat_pos": 0,
            "hand_pos": {"0": 0},
            "free_markers": {"0": 0},
            "initial_cards": {"0": list(player[:2])},
            "initial_total_wager": sum(
                float(v)
                for seatbets in bets_by_seat.values()
                for v in seatbets.values()
            ),
            "extra_wager": 0.0,
            "insurance_wagers": {"0": 0.0},
            "insurance_decisions": {"0": False},
            "insurance_pos": 0,
            "decision_phase": "play",
            "immediate_return": 0.0,
        }

    # ------------------------------------------------------------------
    # Basic action -> settlement flow
    # ------------------------------------------------------------------

    def test_stand_then_settle_regular_win(self):
        st = self._state(
            game="blackjack_lucky8",
            player=[C("10"), C("9", "H")],
            dealer=[C("10", "D"), C("8", "C")],
        )

        response, data = self.action(_enc(st), 0, "stand")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["all_done"])

        response, final = self.settle(data["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["outcome"]["seats"]["0"]["hands"][0]["result"], "win")
        self.assertEqual(final["total_wager"], 100.0)
        self.assertEqual(final["total_return"], 200.0)
        self.assertEqual(final["net"], 100.0)

    def test_hit_then_stand_then_settle(self):
        # shoe.pop() returns the final element, so 3H is the forced hit.
        st = self._state(
            game="blackjack_lucky8",
            player=[C("10"), C("6", "H")],
            dealer=[C("10", "D"), C("7", "C")],
            shoe=[C("3", "H")],
        )

        response, hit = self.action(_enc(st), 0, "hit")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(hit["seats"]["0"]["hands"][0]["total"], 19)

        response, stood = self.action(hit["state_token"], 0, "stand")
        self.assertEqual(response.status_code, 200)

        response, final = self.settle(stood["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["outcome"]["seats"]["0"]["hands"][0]["result"], "win")

    # ------------------------------------------------------------------
    # Free Bet Blackjack
    # ------------------------------------------------------------------

    def test_freebet_dealer_22_push_via_endpoint(self):
        # Player stands on 18.
        # Dealer begins 16 and is forced to draw 6 -> 22.
        st = self._state(
            game="blackjack_freebet",
            player=[C("10"), C("8", "H")],
            dealer=[C("10", "D"), C("6", "C")],
            shoe=[C("6", "H")],
        )

        response, stood = self.action(_enc(st), 0, "stand")
        self.assertEqual(response.status_code, 200)

        response, final = self.settle(stood["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["outcome"]["dealer_total"], 22)
        self.assertTrue(final["outcome"]["dealer_bust"])
        self.assertEqual(final["outcome"]["seats"]["0"]["hands"][0]["result"], "push")
        self.assertEqual(final["total_return"], 100.0)
        self.assertEqual(final["net"], 0.0)

    def test_freebet_free_double_has_zero_extra_stake(self):
        # Hard 11; forced double card 8 -> 19.
        st = self._state(
            game="blackjack_freebet",
            player=[C("5"), C("6", "H")],
            dealer=[C("10", "D"), C("8", "C")],
            shoe=[C("8", "H")],
        )

        response, data = self.action(_enc(st), 0, "double")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["extra_stake"], 0.0)
        self.assertTrue(data["seats"]["0"]["hands"][0]["free_marker"])

        decoded = _dec(data["state_token"])
        self.assertEqual(decoded["free_markers"]["0"], 1)

    def test_freebet_paid_ten_value_split_reports_extra_stake(self):
        # K + Q are both 10-point cards and may split, but not for free.
        # Two forced replacement cards are supplied.
        st = self._state(
            game="blackjack_freebet",
            player=[C("K"), C("Q", "H")],
            dealer=[C("9", "D"), C("7", "C")],
            shoe=[C("4", "D"), C("3", "H")],
        )

        response, data = self.action(_enc(st), 0, "split")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["extra_stake"], 100.0)

        decoded = _dec(data["state_token"])
        self.assertEqual(decoded["extra_wager"], 100.0)
        self.assertEqual(len(decoded["hands"]["0"]), 2)

    # ------------------------------------------------------------------
    # Paid double accounting
    # ------------------------------------------------------------------

    def test_paid_double_reports_extra_stake_and_total_wager(self):
        # Lucky 8 allows paid double. Force 10+6 + 3 = 19 vs dealer 18.
        st = self._state(
            game="blackjack_lucky8",
            player=[C("10"), C("6", "H")],
            dealer=[C("10", "D"), C("8", "C")],
            shoe=[C("3", "H")],
        )

        response, doubled = self.action(_enc(st), 0, "double")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(doubled["extra_stake"], 100.0)
        self.assertTrue(doubled["all_done"])

        response, final = self.settle(doubled["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["total_wager"], 200.0)
        self.assertEqual(final["total_return"], 400.0)
        self.assertEqual(final["net"], 200.0)

    # ------------------------------------------------------------------
    # Insurance and Even Money
    # ------------------------------------------------------------------

    def test_insurance_wins_at_two_to_one_profit(self):
        st = self._state(
            game="blackjack_lucky8",
            player=[C("10"), C("8", "H")],
            dealer=[C("A", "D"), C("K", "C")],
        )
        st["decision_phase"] = "insurance"

        response, insured = self.action(_enc(st), 0, "insurance")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(insured["extra_stake"], 50.0)

        # Insurance resolution advances into play; stand to finish.
        response, stood = self.action(insured["state_token"], 0, "stand")
        self.assertEqual(response.status_code, 200)

        response, final = self.settle(stood["state_token"])
        self.assertEqual(response.status_code, 200)

        insurance = next(
            r for r in final["results"]
            if r["wager_type"] == "seat0_insurance"
        )
        self.assertEqual(insurance["amount"], 50.0)
        self.assertEqual(insurance["return"], 150.0)
        self.assertTrue(insurance["win"])

    def test_pontoon_insurance_loses_on_removed_ten_value_card_rule(self):
        # The real Pontoon shoe has no rank "10", but this direct state test
        # proves insurance specifically only recognizes J/Q/K.
        st = self._state(
            game="pontoon",
            player=[C("9"), C("8", "H")],
            dealer=[C("A", "D"), C("10", "C")],
        )
        st["decision_phase"] = "insurance"

        response, insured = self.action(_enc(st), 0, "insurance")
        self.assertEqual(response.status_code, 200)

        response, stood = self.action(insured["state_token"], 0, "stand")
        self.assertEqual(response.status_code, 200)

        response, final = self.settle(stood["state_token"])
        self.assertEqual(response.status_code, 200)

        insurance = next(
            r for r in final["results"]
            if r["wager_type"] == "seat0_insurance"
        )
        self.assertEqual(insurance["return"], 0.0)
        self.assertFalse(insurance["win"])

    # ------------------------------------------------------------------
    # Pontoon Super Bonus
    # ------------------------------------------------------------------

    def _pontoon_super_bonus_state(
        self,
        stake=100.0,
        *,
        suits=("S", "S", "S"),
        dealer_up_rank="7",
        from_split=False,
        doubled=False,
    ):
        st = self._state(
            game="pontoon",
            player=[
                C("7", suits[0]),
                C("7", suits[1]),
                C("7", suits[2]),
            ],
            dealer=[
                C(dealer_up_rank, "H"),
                C("9", "D"),
            ],
            shoe=[
                C("2", "C"),
                C("2", "D"),
                C("2", "H"),
                C("2", "S"),
            ],
            stake=stake,
            status="stood",
            extra_hand_fields={
                "from_split": from_split,
                "doubled": doubled,
            },
        )

        st["initial_cards"]["0"] = [
            C("7", suits[0]),
            C("7", suits[1]),
        ]

        return st

    def _super_bonus_results(self, data):
        return [
            result
            for result in data["results"]
            if "super_bonus" in result["wager_type"]
        ]

    def test_pontoon_super_bonus_10_wager_pays_1000(self):
        st = self._pontoon_super_bonus_state(
            stake=10,
        )

        response, data = self.settle(
            _enc(st)
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        bonuses = self._super_bonus_results(
            data
        )

        self.assertEqual(
            len(bonuses),
            1,
        )

        self.assertEqual(
            bonuses[0]["wager_type"],
            "seat0_super_bonus",
        )

        self.assertEqual(
            bonuses[0]["return"],
            1000.0,
        )

    def test_pontoon_super_bonus_100_wager_pays_5000(self):
        st = self._pontoon_super_bonus_state(
            stake=100,
        )

        response, data = self.settle(
            _enc(st)
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        bonuses = self._super_bonus_results(
            data
        )

        self.assertEqual(
            len(bonuses),
            1,
        )

        self.assertEqual(
            bonuses[0]["return"],
            5000.0,
        )

    def test_pontoon_super_bonus_pays_50_to_other_original_wager(self):
        st = self._pontoon_super_bonus_state(
            stake=100,
        )

        # Add Seat 1 with an ordinary original Pontoon wager.
        st["active_seats"] = [
            0,
            1,
        ]

        st["bets_by_seat"]["1"] = {
            "seat1_main": 25.0,
        }

        st["hands"]["1"] = [
            {
                "cards": [
                    C("9", "C"),
                    C("8", "D"),
                ],
                "status": "stood",
                "stake": 25.0,
                "paid_extra": 0.0,
                "free_marker": False,
                "from_split": False,
                "from_split_aces": False,
                "split_aces": False,
                "doubled": False,
                "surrendered": False,
                "double_withdrawn": False,
                "immediate_paid": 0.0,
            }
        ]

        st["hand_pos"]["1"] = 0
        st["free_markers"]["1"] = 0

        st["initial_cards"]["1"] = [
            C("9", "C"),
            C("8", "D"),
        ]

        st["insurance_wagers"]["1"] = 0.0
        st["insurance_decisions"]["1"] = False

        st["initial_total_wager"] += 25.0

        response, data = self.settle(
            _enc(st)
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        bonuses = self._super_bonus_results(
            data
        )

        winner_bonus = next(
            result
            for result in bonuses
            if result["wager_type"]
            ==
            "seat0_super_bonus"
        )

        other_bonus = next(
            result
            for result in bonuses
            if result["wager_type"]
            ==
            "seat1_super_bonus_50"
        )

        self.assertEqual(
            winner_bonus["return"],
            5000.0,
        )

        self.assertEqual(
            other_bonus["return"],
            50.0,
        )

        self.assertTrue(
            other_bonus["win"]
        )

    def test_pontoon_super_bonus_requires_same_suit(self):
        st = self._pontoon_super_bonus_state(
            suits=("S", "H", "D"),
        )

        response, data = self.settle(
            _enc(st)
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self._super_bonus_results(data),
            [],
        )

    def test_pontoon_super_bonus_requires_dealer_seven(self):
        st = self._pontoon_super_bonus_state(
            dealer_up_rank="6",
        )

        response, data = self.settle(
            _enc(st)
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self._super_bonus_results(data),
            [],
        )

    def test_pontoon_super_bonus_rejects_split_hand(self):
        st = self._pontoon_super_bonus_state(
            from_split=True,
        )

        response, data = self.settle(
            _enc(st)
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self._super_bonus_results(data),
            [],
        )

    def test_pontoon_super_bonus_rejects_doubled_hand(self):
        st = self._pontoon_super_bonus_state(
            doubled=True,
        )

        response, data = self.settle(
            _enc(st)
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self._super_bonus_results(data),
            [],
        )

    # ------------------------------------------------------------------
    # Pontoon immediate payout accounting
    # ------------------------------------------------------------------

    def test_pontoon_immediate_21_not_double_counted_at_settlement(self):
        # Start on 11 and hit a King -> 21.
        st = self._state(
            game="pontoon",
            player=[C("5"), C("6", "H")],
            dealer=[C("9", "D"), C("8", "C")],
            shoe=[C("K", "H")],
        )

        response, hit = self.action(_enc(st), 0, "hit")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(hit["immediate_return"], 200.0)
        self.assertTrue(hit["all_done"])

        response, final = self.settle(hit["state_token"])
        self.assertEqual(response.status_code, 200)

        # Client has already credited 200 during /action.
        # Final settlement must not credit it a second time.
        self.assertEqual(final["immediate_return"], 200.0)
        self.assertEqual(final["total_return"], 0.0)
        self.assertEqual(final["net"], 100.0)

    # ------------------------------------------------------------------
    # Pontoon double withdrawal
    # ------------------------------------------------------------------

    def test_pontoon_double_withdrawal_returns_doubled_portion_only(self):
        # 9+7 doubles, forced 2 -> 18. Player then withdraws doubled portion.
        st = self._state(
            game="pontoon",
            player=[C("9"), C("7", "H")],
            dealer=[C("8", "D"), C("8", "C")],
            shoe=[C("2", "H")],
        )

        response, doubled = self.action(_enc(st), 0, "double")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(doubled["extra_stake"], 100.0)
        self.assertTrue(
            doubled["seats"]["0"]["hands"][0]["can_withdraw_double"]
        )

        response, withdrawn = self.action(
            doubled["state_token"],
            0,
            "withdraw_double",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(withdrawn["immediate_return"], 100.0)
        self.assertTrue(withdrawn["all_done"])

        response, final = self.settle(withdrawn["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["total_wager"], 200.0)
        self.assertEqual(final["immediate_return"], 100.0)
        self.assertEqual(final["total_return"], 0.0)
        self.assertEqual(final["net"], -100.0)

    # ------------------------------------------------------------------
    # Split hand is not Blackjack
    # ------------------------------------------------------------------

    def test_split_ace_ten_settles_as_regular_21_not_blackjack(self):
        st = self._state(
            game="blackjack_lucky8",
            player=[C("A"), C("K", "H")],
            dealer=[C("10", "D"), C("9", "C")],
            status="stood",
            extra_hand_fields={"from_split": True},
        )
        st["seat_pos"] = 1

        response, final = self.settle(_enc(st))
        self.assertEqual(response.status_code, 200)
        hand = final["outcome"]["seats"]["0"]["hands"][0]
        self.assertEqual(hand["result"], "win")
        self.assertNotEqual(hand["result"], "blackjack")


if __name__ == "__main__":
    unittest.main()
