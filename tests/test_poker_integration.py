import unittest
from unittest.mock import patch

from flask import Flask

from api.solo import solo_bp
from game import poker_engine
from game import paigow_engine


def C(rank, suit="S"):
    return {"rank": rank, "suit": suit}


class TestPokerIntegration(unittest.TestCase):

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
        return response, response.get_json()

    def deal(self, game, bets):
        return self.post(
            "/api/solo/poker/deal",
            {"game": game, "bets": bets},
        )

    def action(self, token, seat, action, **extra):
        payload = {
            "state_token": token,
            "seat": seat,
            "action": action,
        }
        payload.update(extra)
        return self.post("/api/solo/poker/action", payload)

    def settle(self, token):
        return self.post(
            "/api/solo/poker/settle",
            {"state_token": token},
        )

    def bet(self, seat, key, amount=100):
        return {
            "seat": seat,
            "wager_type": f"seat{seat}_{key}",
            "amount": amount,
        }

    # --------------------------------------------------------------
    # Route validation
    # --------------------------------------------------------------

    def test_unknown_poker_game_rejected(self):
        response, data = self.deal(
            "not_a_poker_game",
            [self.bet(0, "ante")],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    def test_no_bets_rejected(self):
        response, data = self.deal("poker_singapore_stud", [])
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    def test_invalid_wager_type_rejected(self):
        response, data = self.deal(
            "poker_singapore_stud",
            [self.bet(0, "banana")],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid poker wager", data["error"])

    def test_ultimate_requires_equal_ante_and_blind(self):
        response, data = self.deal(
            "poker_ultimate_texas",
            [
                self.bet(0, "ante", 100),
                self.bet(0, "blind", 200),
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("equal Ante and Blind", data["error"])

    def test_settle_before_decisions_complete_rejected(self):
        st = poker_engine.deal(
            "poker_singapore_stud",
            [self.bet(0, "ante", 100)],
        )
        response, data = self.settle(poker_engine.enc(st))
        self.assertEqual(response.status_code, 400)
        self.assertIn("not complete", data["error"])

    # --------------------------------------------------------------
    # Three Card Poker Xtreme
    # --------------------------------------------------------------

    def test_three_card_side_only_deal_is_allowed(self):
        response, data = self.deal(
            "poker_three_card_xtreme",
            [self.bet(0, "pair_plus", 100)],
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["all_done"])
        self.assertEqual(data["stage"], "settle")
        self.assertEqual(data["total_wager"], 100.0)

    def test_three_card_play_adds_one_ante(self):
        response, data = self.deal(
            "poker_three_card_xtreme",
            [self.bet(0, "ante", 100)],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["current_seat"], 0)

        response, acted = self.action(
            data["state_token"], 0, "play"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(acted["extra_stake"], 100.0)
        self.assertTrue(acted["all_done"])

        response, final = self.settle(acted["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["total_wager"], 200.0)
        self.assertAlmostEqual(
            final["net"],
            final["total_return"] - 200.0,
        )

    def test_three_card_fold_keeps_side_wager_in_settlement(self):
        st = {
            "game": "poker_three_card_xtreme",
            "deck": [],
            "hands": {
                "0": {
                    "cards": [C("8", "S"), C("8", "H"), C("3", "D")],
                    "ante": 100.0,
                    "blind_mode": False,
                    "side": {
                        "seat0_ante": 100.0,
                        "seat0_pair_plus": 100.0,
                    },
                    "folded": False,
                    "actions": [],
                    "extra": 0.0,
                }
            },
            "dealer": [C("Q", "S"), C("9", "H"), C("4", "D")],
            "community": [C("2", "C"), C("5", "C")],
            "active": [0],
            "bets": {
                "0": {
                    "seat0_ante": 100.0,
                    "seat0_pair_plus": 100.0,
                }
            },
            "seat_pos": 0,
            "stage": "initial",
            "revealed": 0,
            "extra": 0.0,
        }

        response, folded = self.action(
            poker_engine.enc(st), 0, "fold"
        )
        self.assertEqual(response.status_code, 200)

        response, final = self.settle(folded["state_token"])
        self.assertEqual(response.status_code, 200)

        pair_plus = next(
            r for r in final["results"]
            if r["wager_type"] == "seat0_pair_plus"
        )
        self.assertEqual(pair_plus["return"], 200.0)
        self.assertEqual(final["total_wager"], 200.0)

    # --------------------------------------------------------------
    # Singapore Stud
    # --------------------------------------------------------------

    def test_singapore_play_costs_two_times_ante(self):
        response, data = self.deal(
            "poker_singapore_stud",
            [self.bet(0, "ante", 100)],
        )
        self.assertEqual(response.status_code, 200)

        response, acted = self.action(
            data["state_token"], 0, "play"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(acted["extra_stake"], 200.0)
        self.assertTrue(acted["all_done"])

        response, final = self.settle(acted["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["total_wager"], 300.0)
        self.assertAlmostEqual(
            final["net"],
            final["total_return"] - 300.0,
        )

    # --------------------------------------------------------------
    # Texas Hold'em Bonus
    # --------------------------------------------------------------

    def test_texas_bonus_flop_turn_river_progression(self):
        response, data = self.deal(
            "poker_texas_bonus",
            [
                self.bet(0, "ante", 100),
                self.bet(0, "bonus", 100),
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["stage"], "initial")

        response, flop = self.action(
            data["state_token"], 0, "flop"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(flop["extra_stake"], 200.0)
        self.assertEqual(flop["stage"], "flop")
        self.assertEqual(len(flop["community"]), 3)

        response, turn = self.action(
            flop["state_token"], 0, "turn"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(turn["extra_stake"], 100.0)
        self.assertEqual(turn["stage"], "turn")
        self.assertEqual(len(turn["community"]), 4)

        response, river = self.action(
            turn["state_token"], 0, "river"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(river["extra_stake"], 100.0)
        self.assertEqual(river["stage"], "settle")
        self.assertTrue(river["all_done"])

        response, final = self.settle(river["state_token"])
        self.assertEqual(response.status_code, 200)

        # Ante 100 + Bonus 100 + Flop 200 + Turn 100 + River 100.
        self.assertEqual(final["total_wager"], 600.0)
        self.assertAlmostEqual(
            final["net"],
            final["total_return"] - 600.0,
        )

    def test_texas_bonus_checks_cost_nothing(self):
        response, data = self.deal(
            "poker_texas_bonus",
            [self.bet(0, "ante", 100)],
        )

        response, flop = self.action(
            data["state_token"], 0, "flop"
        )
        self.assertEqual(flop["extra_stake"], 200.0)

        response, turn = self.action(
            flop["state_token"], 0, "check"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(turn["extra_stake"], 0.0)

        response, river = self.action(
            turn["state_token"], 0, "check"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(river["extra_stake"], 0.0)

        response, final = self.settle(river["state_token"])
        self.assertEqual(final["total_wager"], 300.0)

    # --------------------------------------------------------------
    # Ultimate Texas Hold'em
    # --------------------------------------------------------------

    def test_ultimate_preflop_play4_adds_four_ante_and_finishes_decisions(self):
        response, data = self.deal(
            "poker_ultimate_texas",
            [
                self.bet(0, "ante", 100),
                self.bet(0, "blind", 100),
                self.bet(0, "trips", 100),
            ],
        )
        self.assertEqual(response.status_code, 200)

        response, acted = self.action(
            data["state_token"], 0, "play4"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(acted["extra_stake"], 400.0)
        self.assertEqual(acted["stage"], "settle")
        self.assertTrue(acted["all_done"])

        response, final = self.settle(acted["state_token"])
        self.assertEqual(response.status_code, 200)

        # Ante + Blind + Trips + 4x Play.
        self.assertEqual(final["total_wager"], 700.0)
        self.assertAlmostEqual(
            final["net"],
            final["total_return"] - 700.0,
        )

    def test_ultimate_check_then_play2(self):
        response, data = self.deal(
            "poker_ultimate_texas",
            [
                self.bet(0, "ante", 100),
                self.bet(0, "blind", 100),
            ],
        )

        response, checked = self.action(
            data["state_token"], 0, "check"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(checked["extra_stake"], 0.0)
        self.assertEqual(checked["stage"], "flop")
        self.assertEqual(len(checked["community"]), 3)

        response, played = self.action(
            checked["state_token"], 0, "play2"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(played["extra_stake"], 200.0)
        self.assertEqual(played["stage"], "settle")

        response, final = self.settle(played["state_token"])
        self.assertEqual(final["total_wager"], 400.0)

    def test_ultimate_check_check_then_play1(self):
        response, data = self.deal(
            "poker_ultimate_texas",
            [
                self.bet(0, "ante", 100),
                self.bet(0, "blind", 100),
            ],
        )

        response, flop = self.action(
            data["state_token"], 0, "check"
        )
        response, river = self.action(
            flop["state_token"], 0, "check"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(river["stage"], "river")
        self.assertEqual(len(river["community"]), 5)

        response, played = self.action(
            river["state_token"], 0, "play1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(played["extra_stake"], 100.0)
        self.assertEqual(played["stage"], "settle")

        response, final = self.settle(played["state_token"])
        self.assertEqual(final["total_wager"], 300.0)

    # --------------------------------------------------------------
    # Mississippi Stud
    # --------------------------------------------------------------

    def test_mississippi_three_street_progression_and_accounting(self):
        response, data = self.deal(
            "poker_mississippi",
            [self.bet(0, "ante", 100)],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["stage"], "initial")

        response, third = self.action(
            data["state_token"], 0, "bet1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(third["extra_stake"], 100.0)
        self.assertEqual(third["stage"], "third")
        self.assertEqual(len(third["community"]), 1)

        response, fourth = self.action(
            third["state_token"], 0, "bet2"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fourth["extra_stake"], 200.0)
        self.assertEqual(fourth["stage"], "fourth")
        self.assertEqual(len(fourth["community"]), 2)

        response, fifth = self.action(
            fourth["state_token"], 0, "bet3"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fifth["extra_stake"], 300.0)
        self.assertEqual(fifth["stage"], "fifth")
        self.assertEqual(len(fifth["community"]), 3)

        # The engine has one final stage transition after fifth street.
        response, done = self.action(
            fifth["state_token"], 0, "bet1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(done["stage"], "settle")

        response, final = self.settle(done["state_token"])
        self.assertEqual(response.status_code, 200)

        # Ante + 1x + 2x + 3x + final 1x according to current engine stages.
        self.assertEqual(final["total_wager"], 800.0)
        self.assertAlmostEqual(
            final["net"],
            final["total_return"] - 800.0,
        )

    # --------------------------------------------------------------
    # Fortune Pai Gow
    # --------------------------------------------------------------

    def _paigow_state(self, cards, dealer=None, active=None):
        if dealer is None:
            dealer = [
                C("A", "H"), C("K", "D"), C("J", "C"),
                C("9", "S"), C("7", "H"), C("5", "D"), C("3", "C"),
            ]
        if active is None:
            active = [0]

        hands = {}
        bets = {}
        for seat in active:
            hand_cards = cards if seat == 0 else [
                C("K", "S"), C("Q", "H"), C("10", "D"),
                C("8", "C"), C("6", "S"), C("4", "H"), C("2", "D"),
            ]
            hands[str(seat)] = {
                "cards": hand_cards,
                "ante": 100.0,
                "blind_mode": seat != 0,
                "side": {f"seat{seat}_ante": 100.0},
                "folded": False,
                "actions": [],
                "extra": 0.0,
            }
            bets[str(seat)] = {f"seat{seat}_ante": 100.0}

        return {
            "game": "poker_fortune_pai_gow",
            "deck": [],
            "hands": hands,
            "dealer": dealer,
            "community": [],
            "active": active,
            "bets": bets,
            "seat_pos": 0,
            "stage": "set",
            "revealed": 0,
            "extra": 0.0,
        }

    def test_paigow_viewed_seat_exposes_manual_set(self):
        cards = [
            C("A", "S"), C("K", "H"), C("Q", "D"),
            C("9", "C"), C("7", "S"), C("4", "H"), C("2", "D"),
        ]
        view = poker_engine.visible(self._paigow_state(cards))
        self.assertEqual(view["current_seat"], 0)
        self.assertTrue(view["seats"]["0"]["manual_set_allowed"])
        self.assertIn("set_hand", view["actions"])
        self.assertIn("houseway", view["actions"])

    def test_paigow_manual_set_accepts_two_low_indices(self):
        cards = [
            C("9", "S"), C("9", "H"), C("A", "D"),
            C("K", "C"), C("7", "S"), C("4", "H"), C("2", "D"),
        ]
        st = self._paigow_state(cards)

        response, data = self.action(
            poker_engine.enc(st),
            0,
            "set_hand",
            low_indices=[2, 3],
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["all_done"])

        decoded = poker_engine.dec(data["state_token"])
        hand = decoded["hands"]["0"]
        self.assertEqual(len(hand["low"]), 2)
        self.assertEqual(len(hand["high"]), 5)
        self.assertFalse(hand["foul"])
        self.assertTrue(hand["manual_set"])

    def test_paigow_manual_set_requires_exactly_two_indices(self):
        cards = [
            C("9", "S"), C("9", "H"), C("A", "D"),
            C("K", "C"), C("7", "S"), C("4", "H"), C("2", "D"),
        ]
        st = self._paigow_state(cards)

        response, data = self.action(
            poker_engine.enc(st),
            0,
            "set_hand",
            low_indices=[2],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("exactly two", data["error"])

    def test_paigow_foul_manual_set_resets_to_house_way(self):
        # A,K,Q,J,9,8,7. Selecting A,K as Low leaves Q-high High,
        # so the Low Hand outranks the High Hand and is foul.
        cards = [
            C("A", "S"), C("K", "H"), C("Q", "D"),
            C("J", "C"), C("9", "S"), C("8", "H"), C("7", "D"),
        ]
        st = self._paigow_state(cards)

        expected_low, expected_high = paigow_engine.house_way(cards)

        response, data = self.action(
            poker_engine.enc(st),
            0,
            "set_hand",
            low_indices=[0, 1],
        )
        self.assertEqual(response.status_code, 200)

        decoded = poker_engine.dec(data["state_token"])
        hand = decoded["hands"]["0"]

        self.assertTrue(hand["foul"])
        self.assertEqual(hand["low"], expected_low)
        self.assertEqual(hand["high"], expected_high)

    def test_paigow_houseway_action_sets_viewed_hand(self):
        cards = [
            C("A", "S"), C("K", "H"), C("Q", "D"),
            C("9", "C"), C("7", "S"), C("4", "H"), C("2", "D"),
        ]
        st = self._paigow_state(cards)

        expected_low, expected_high = paigow_engine.house_way(cards)

        response, data = self.action(
            poker_engine.enc(st), 0, "houseway"
        )
        self.assertEqual(response.status_code, 200)

        decoded = poker_engine.dec(data["state_token"])
        hand = decoded["hands"]["0"]
        self.assertEqual(hand["low"], expected_low)
        self.assertEqual(hand["high"], expected_high)
        self.assertFalse(hand["manual_set"])

    def test_paigow_blind_seat_uses_houseway_automatically(self):
        viewed = [
            C("9", "S"), C("9", "H"), C("A", "D"),
            C("K", "C"), C("7", "S"), C("4", "H"), C("2", "D"),
        ]
        st = self._paigow_state(viewed, active=[0, 1])

        # Finish viewed Seat 1 first.
        response, first = self.action(
            poker_engine.enc(st),
            0,
            "set_hand",
            low_indices=[2, 3],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(first["current_seat"], 1)
        self.assertEqual(first["actions"], ["houseway"])

        # Client can send any action string for a blind hand; engine replaces
        # it with the blind House Way action.
        response, second = self.action(
            first["state_token"], 1, "houseway"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(second["all_done"])

        decoded = poker_engine.dec(second["state_token"])
        blind = decoded["hands"]["1"]
        self.assertEqual(len(blind["low"]), 2)
        self.assertEqual(len(blind["high"]), 5)
        self.assertFalse(blind["manual_set"])

    def test_paigow_fortune_bonus_is_counted_in_total_wager(self):
        cards = [
            C("8", "S"), C("9", "S"), C("10", "S"),
            C("J", "S"), C("Q", "S"), C("K", "S"), C("A", "S"),
        ]
        st = self._paigow_state(cards)
        st["bets"]["0"]["seat0_fortune_bonus"] = 10.0
        st["hands"]["0"]["side"]["seat0_fortune_bonus"] = 10.0

        response, acted = self.action(
            poker_engine.enc(st), 0, "houseway"
        )
        self.assertEqual(response.status_code, 200)

        response, final = self.settle(acted["state_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["total_wager"], 110.0)

        fortune = next(
            r for r in final["results"]
            if r["wager_type"] == "seat0_fortune_bonus"
        )
        self.assertEqual(
            fortune["category"],
            "seven_card_straight_flush_no_joker",
        )
        self.assertEqual(fortune["return"], 25010.0)

    def test_paigow_final_net_matches_return_minus_all_stakes(self):
        cards = [
            C("A", "S"), C("K", "H"), C("Q", "D"),
            C("9", "C"), C("7", "S"), C("4", "H"), C("2", "D"),
        ]
        st = self._paigow_state(cards)

        response, acted = self.action(
            poker_engine.enc(st), 0, "houseway"
        )
        response, final = self.settle(acted["state_token"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(final["total_wager"], 100.0)
        self.assertAlmostEqual(
            final["net"],
            final["total_return"] - 100.0,
        )


if __name__ == "__main__":
    unittest.main()
