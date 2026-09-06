"""
Contract tests for the GitHub Pages / Pyodide browser bridge.

These tests intentionally exercise the public bridge boundary rather
than internal implementation details.

Their purpose is to protect the working Pages runtime while
solo_bridge.py is refactored into smaller modules.
"""

from __future__ import annotations

import json
import sys
import unittest

from decimal import Decimal
from pathlib import Path


# ================================================================
# IMPORT PAGES RUNTIME
# ================================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

RUNTIME = (
    ROOT
    / "pages"
    / "runtime"
)

runtime_string = str(
    RUNTIME
)

if runtime_string not in sys.path:
    sys.path.insert(
        0,
        runtime_string,
    )


import solo_bridge


# ================================================================
# EXPECTED PUBLIC OPERATIONS
# ================================================================

PUBLIC_OPERATIONS = {
    "runtime_info",

    "solo_spin",
    "baccarat_spin",

    "roulette_spin",
    "royal_three_pictures_deal",

    "craps_roll",
    "craps_action",

    "blackjack_deal",
    "blackjack_action",
    "blackjack_settle",

    "poker_deal",
    "poker_action",
    "poker_settle",

    "dueling_8s_deal",
    "dueling_8s_action",
    "dueling_8s_settle",
}


# ================================================================
# TESTS
# ================================================================

class PagesBridgeContractTests(
    unittest.TestCase
):

    # ------------------------------------------------------------
    # IMPORT
    # ------------------------------------------------------------

    def test_bridge_imports(self):

        self.assertTrue(
            callable(
                solo_bridge.dispatch
            )
        )

        self.assertTrue(
            callable(
                solo_bridge.dispatch_json
            )
        )


    # ------------------------------------------------------------
    # JSON SAFE
    # ------------------------------------------------------------

    def test_json_safe_primitives(self):

        values = [
            None,
            True,
            False,
            0,
            1,
            1.5,
            "ETG",
        ]

        for value in values:

            with self.subTest(
                value=value
            ):

                self.assertEqual(
                    solo_bridge._json_safe(
                        value
                    ),
                    value,
                )


    def test_json_safe_decimal(self):

        self.assertEqual(
            solo_bridge._json_safe(
                Decimal(
                    "123.45"
                )
            ),
            123.45,
        )


    def test_json_safe_nested_values(self):

        value = {
            "amount":
                Decimal(
                    "10.50"
                ),

            "items": [
                Decimal(
                    "1.25"
                ),

                {
                    "value":
                        Decimal(
                            "2.75"
                        ),
                },
            ],

            "tuple":
                (
                    Decimal(
                        "3.50"
                    ),
                    "ok",
                ),
        }

        converted = (
            solo_bridge
            ._json_safe(
                value
            )
        )

        self.assertEqual(
            converted[
                "amount"
            ],
            10.5,
        )

        self.assertEqual(
            converted[
                "items"
            ][0],
            1.25,
        )

        self.assertEqual(
            converted[
                "items"
            ][1][
                "value"
            ],
            2.75,
        )

        self.assertEqual(
            converted[
                "tuple"
            ],
            [
                3.5,
                "ok",
            ],
        )

        # Most importantly, the result must actually cross
        # the browser JSON boundary successfully.

        json.dumps(
            converted
        )


    # ------------------------------------------------------------
    # RUNTIME INFO
    # ------------------------------------------------------------

    def test_runtime_info_contract(self):

        result = (
            solo_bridge
            .dispatch(
                "runtime_info",
                {},
            )
        )

        self.assertIsInstance(
            result,
            dict,
        )

        self.assertIn(
            "ok",
            result,
        )

        self.assertIn(
            "modules",
            result,
        )

        self.assertIsInstance(
            result[
                "modules"
            ],
            dict,
        )

        self.assertTrue(
            result[
                "ok"
            ],
            msg=(
                "One or more Python game "
                "modules failed to import: "
                f"{result['modules']}"
            ),
        )

        expected_modules = {
            "game.registry",

            "game.baccarat_dragon_tiger",
            "game.baccarat_immortal",
            "game.baccarat_rising",

            "game.blackjack_lucky8",
            "game.blackjack_freebet",
            "game.blackjack_kingsbounty",
            "game.pontoon",

            "game.sicbo",
            "game.great_fortune_dice",

            "game.craps",
            "game.craps_engine",

            "game.roulette_engine",
            "game.roulette_single_zero",
            "game.roulette_double_zero",
            "game.roulette_sands_roulette",

            "game.poker_engine",
            "game.poker_three_card_xtreme",
            "game.poker_singapore_stud",
            "game.poker_texas_holdem_bonus",
            "game.poker_ultimate_texas",
            "game.poker_mississippi_stud",
            "game.poker_fortune_pai_gow",
            "game.paigow_engine",

            "game.dueling_8s_21",
            "game.royal_three_pictures",
        }

        self.assertTrue(
            expected_modules
            .issubset(
                result[
                    "modules"
                ].keys()
            )
        )


    # ------------------------------------------------------------
    # DISPATCH ERRORS
    # ------------------------------------------------------------

    def test_unknown_operation_raises(self):

        with self.assertRaises(
            ValueError
        ):

            solo_bridge.dispatch(
                "definitely_not_an_etg_operation",
                {},
            )


    def test_non_dict_payload_becomes_empty_dict(self):

        with self.assertRaises(
            ValueError
        ) as context:

            solo_bridge.dispatch(
                "definitely_not_an_etg_operation",
                [
                    "not",
                    "a",
                    "dict",
                ],
            )

        self.assertIn(
            "Unknown ETG browser operation",
            str(
                context.exception
            ),
        )


    # ------------------------------------------------------------
    # JSON BOUNDARY
    # ------------------------------------------------------------

    def test_dispatch_json_runtime_info(self):

        raw = (
            solo_bridge
            .dispatch_json(
                "runtime_info",
                "{}",
            )
        )

        response = (
            json.loads(
                raw
            )
        )

        self.assertTrue(
            response[
                "ok"
            ]
        )

        self.assertIn(
            "result",
            response,
        )

        self.assertTrue(
            response[
                "result"
            ][
                "ok"
            ]
        )

        self.assertIn(
            "modules",
            response[
                "result"
            ],
        )


    def test_dispatch_json_empty_payload(self):

        raw = (
            solo_bridge
            .dispatch_json(
                "runtime_info",
                "",
            )
        )

        response = (
            json.loads(
                raw
            )
        )

        self.assertTrue(
            response[
                "ok"
            ]
        )


    def test_dispatch_json_invalid_json(self):

        raw = (
            solo_bridge
            .dispatch_json(
                "runtime_info",
                "{this is not json}",
            )
        )

        response = (
            json.loads(
                raw
            )
        )

        self.assertFalse(
            response[
                "ok"
            ]
        )

        self.assertEqual(
            response[
                "type"
            ],
            "JSONDecodeError",
        )

        self.assertIn(
            "error",
            response,
        )

        self.assertIn(
            "traceback",
            response,
        )


    def test_dispatch_json_unknown_operation(self):

        raw = (
            solo_bridge
            .dispatch_json(
                "unknown_operation",
                "{}",
            )
        )

        response = (
            json.loads(
                raw
            )
        )

        self.assertFalse(
            response[
                "ok"
            ]
        )

        self.assertEqual(
            response[
                "type"
            ],
            "ValueError",
        )

        self.assertIn(
            "Unknown ETG browser operation",
            response[
                "error"
            ],
        )

        self.assertTrue(
            response[
                "traceback"
            ]
        )


    # ------------------------------------------------------------
    # PUBLIC OPERATION NAMES
    # ------------------------------------------------------------

    def test_public_operation_contract(self):

        """
        Verify that every operation expected by api-shim.js remains
        represented by the dispatcher.

        This is deliberately a source-level contract check because
        invoking every stateful operation requires valid game state.
        """

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        for operation in (
            PUBLIC_OPERATIONS
            -
            {
                "runtime_info",
            }
        ):

            with self.subTest(
                operation=operation
            ):

                self.assertIn(
                    f'"{operation}"',
                    source,
                )


    # ------------------------------------------------------------
    # API SHIM <-> BRIDGE CONTRACT
    # ------------------------------------------------------------

    def test_api_shim_operations_exist_in_bridge(self):

        shim = (
            RUNTIME
            / "api-shim.js"
        ).read_text(
            encoding="utf-8"
        )

        bridge = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        expected = {
            "solo_spin",

            "craps_roll",
            "craps_action",

            "roulette_spin",

            "royal_three_pictures_deal",

            "blackjack_deal",
            "blackjack_action",
            "blackjack_settle",

            "poker_deal",
            "poker_action",
            "poker_settle",

            "dueling_8s_deal",
            "dueling_8s_action",
            "dueling_8s_settle",
        }

        for operation in expected:

            with self.subTest(
                operation=operation
            ):

                self.assertIn(
                    f'"{operation}"',
                    shim,
                    msg=(
                        f"{operation} missing "
                        "from api-shim.js"
                    ),
                )

                self.assertIn(
                    f'"{operation}"',
                    bridge,
                    msg=(
                        f"{operation} missing "
                        "from solo_bridge.py"
                    ),
                )


    # ------------------------------------------------------------
    # STATIC BUILD CONTRACT
    # ------------------------------------------------------------

    def test_pyodide_runtime_loads_solo_bridge(self):

        runtime = (
            RUNTIME
            / "pyodide-runtime.js"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "solo_bridge.py",
            runtime,
        )

        self.assertIn(
            "import solo_bridge",
            runtime,
        )

        self.assertIn(
            "solo_bridge.dispatch_json",
            runtime,
        )


    def test_modular_bridge_runtime_is_installed(self):

        """
        Verify that every extracted bridge module is installed into
        Pyodide before solo_bridge.py is imported.

        solo_bridge.py remains the public browser entry point.
        """

        runtime = (
            RUNTIME
            / "pyodide-runtime.js"
        ).read_text(
            encoding="utf-8"
        )

        expected_bridge_files = {
            "bridge/__init__.py",
            "bridge/common.py",
            "bridge/stateless.py",
            "bridge/craps.py",
            "bridge/roulette.py",
            "bridge/royal_three_pictures.py",
            "bridge/poker.py",
            "bridge/state_token.py",
            "bridge/dueling_8s.py",
            "bridge/blackjack.py",
        }

        self.assertIn(
            "BRIDGE_FILES",
            runtime,
        )

        for filename in expected_bridge_files:

            with self.subTest(
                filename=filename
            ):

                self.assertIn(
                    f'"{filename}"',
                    runtime,
                    msg=(
                        f"{filename} missing "
                        "from BRIDGE_FILES"
                    ),
                )

        self.assertIn(
            "import bridge.common",
            runtime,
        )

        self.assertIn(
            "import solo_bridge",
            runtime,
        )


    # ------------------------------------------------------------
    # STATE TOKEN EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_state_token_codec_is_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        state_token = (
            RUNTIME
            / "bridge"
            / "state_token.py"
        ).read_text(
            encoding="utf-8"
        )

        # The codec itself must live in its extracted module.

        self.assertIn(
            "def encode_state(",
            state_token,
        )

        self.assertIn(
            "def decode_state(",
            state_token,
        )

        # The thin public bridge should no longer own or alias
        # Blackjack-specific state-token helpers.

        self.assertNotIn(
            "def _bj_enc(",
            source,
        )

        self.assertNotIn(
            "def _bj_dec(",
            source,
        )

        self.assertNotIn(
            "_bj_enc = encode_state",
            source,
        )

        self.assertNotIn(
            "_bj_dec = decode_state",
            source,
        )

        self.assertNotIn(
            "encode_state",
            source,
        )

        self.assertNotIn(
            "decode_state",
            source,
        )


    # ------------------------------------------------------------
    # STATELESS EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_stateless_operation_is_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        stateless = (
            RUNTIME
            / "bridge"
            / "stateless.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "from bridge.stateless import",
            source,
        )

        self.assertNotIn(
            "def solo_spin(",
            source,
        )

        self.assertNotIn(
            "STATELESS_GAMES =",
            source,
        )

        self.assertIn(
            "def solo_spin(",
            stateless,
        )

        self.assertIn(
            "STATELESS_GAMES =",
            stateless,
        )


    # ------------------------------------------------------------
    # CRAPS EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_craps_operations_are_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        craps = (
            RUNTIME
            / "bridge"
            / "craps.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "from bridge.craps import",
            source,
        )

        self.assertNotIn(
            "def craps_roll(",
            source,
        )

        self.assertNotIn(
            "def craps_action(",
            source,
        )

        self.assertNotIn(
            "from game import craps_engine",
            source,
        )

        self.assertIn(
            "def craps_roll(",
            craps,
        )

        self.assertIn(
            "def craps_action(",
            craps,
        )

        self.assertIn(
            "from game import craps_engine",
            craps,
        )


    # ------------------------------------------------------------
    # ROULETTE EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_roulette_operation_is_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        roulette = (
            RUNTIME
            / "bridge"
            / "roulette.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "from bridge.roulette import",
            source,
        )

        self.assertNotIn(
            "def roulette_spin(",
            source,
        )

        self.assertNotIn(
            "import game.roulette_engine as roulette_engine",
            source,
        )

        self.assertIn(
            "def roulette_spin(",
            roulette,
        )

        self.assertIn(
            "import game.roulette_engine as roulette_engine",
            roulette,
        )


    # ------------------------------------------------------------
    # ROYAL THREE PICTURES EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_royal_three_pictures_operation_is_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        royal = (
            RUNTIME
            / "bridge"
            / "royal_three_pictures.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "from bridge.royal_three_pictures import",
            source,
        )

        self.assertNotIn(
            "def royal_three_pictures_deal(",
            source,
        )

        self.assertNotIn(
            "import game.royal_three_pictures as royal_three_pictures",
            source,
        )

        self.assertIn(
            "def royal_three_pictures_deal(",
            royal,
        )

        self.assertIn(
            "import game.royal_three_pictures as royal_three_pictures",
            royal,
        )


    # ------------------------------------------------------------
    # POKER EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_poker_operations_are_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        poker = (
            RUNTIME
            / "bridge"
            / "poker.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "from bridge.poker import",
            source,
        )

        self.assertNotIn(
            "def poker_deal(",
            source,
        )

        self.assertNotIn(
            "def poker_action(",
            source,
        )

        self.assertNotIn(
            "def poker_settle(",
            source,
        )

        self.assertNotIn(
            "from game import poker_engine",
            source,
        )

        self.assertIn(
            "def poker_deal(",
            poker,
        )

        self.assertIn(
            "def poker_action(",
            poker,
        )

        self.assertIn(
            "def poker_settle(",
            poker,
        )

        self.assertIn(
            "from game import poker_engine",
            poker,
        )


    # ------------------------------------------------------------
    # DUELING 8'S EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_dueling_8s_operations_are_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        dueling = (
            RUNTIME
            / "bridge"
            / "dueling_8s.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "from bridge.dueling_8s import",
            source,
        )

        self.assertNotIn(
            "def dueling_8s_deal(",
            source,
        )

        self.assertNotIn(
            "def dueling_8s_action(",
            source,
        )

        self.assertNotIn(
            "def dueling_8s_settle(",
            source,
        )

        self.assertNotIn(
            "def _d8_draw(",
            source,
        )

        self.assertNotIn(
            "def _d8_main_bet(",
            source,
        )

        self.assertNotIn(
            "def _d8_hand_status(",
            source,
        )

        self.assertNotIn(
            "def _d8_advance(",
            source,
        )

        self.assertNotIn(
            "def _d8_current(",
            source,
        )

        self.assertNotIn(
            "def _d8_visible(",
            source,
        )

        self.assertNotIn(
            "import game.dueling_8s_21 as dueling_8s",
            source,
        )

        self.assertIn(
            "def dueling_8s_deal(",
            dueling,
        )

        self.assertIn(
            "def dueling_8s_action(",
            dueling,
        )

        self.assertIn(
            "def dueling_8s_settle(",
            dueling,
        )

        self.assertIn(
            "def _d8_draw(",
            dueling,
        )

        self.assertIn(
            "def _d8_main_bet(",
            dueling,
        )

        self.assertIn(
            "def _d8_hand_status(",
            dueling,
        )

        self.assertIn(
            "def _d8_advance(",
            dueling,
        )

        self.assertIn(
            "def _d8_current(",
            dueling,
        )

        self.assertIn(
            "def _d8_visible(",
            dueling,
        )

        self.assertIn(
            "import game.dueling_8s_21 as dueling_8s",
            dueling,
        )

        self.assertIn(
            "from bridge.state_token import",
            dueling,
        )

        self.assertIn(
            "encode_state(",
            dueling,
        )

        self.assertIn(
            "decode_state(",
            dueling,
        )

        self.assertNotIn(
            "_bj_enc(",
            dueling,
        )

        self.assertNotIn(
            "_bj_dec(",
            dueling,
        )


    # ------------------------------------------------------------
    # BLACKJACK EXTRACTION CONTRACT
    # ------------------------------------------------------------

    def test_blackjack_operations_are_extracted(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        blackjack = (
            RUNTIME
            / "bridge"
            / "blackjack.py"
        ).read_text(
            encoding="utf-8"
        )

        # Public operations must be imported by the thin
        # compatibility/dispatch layer.

        self.assertIn(
            "from bridge.blackjack import",
            source,
        )

        # Public Blackjack implementations must no longer live
        # inside solo_bridge.py.

        self.assertNotIn(
            "def blackjack_deal(",
            source,
        )

        self.assertNotIn(
            "def blackjack_action(",
            source,
        )

        self.assertNotIn(
            "def blackjack_settle(",
            source,
        )

        # Blackjack-specific helpers and constants must also have
        # moved with the implementation.

        blackjack_helpers = {
            "def _pontoon_shoe(",
            "def _pair_value(",
            "def _main_bet(",
            "def _pontoon_total(",
            "def _bj_total(",
            "def _bj_bust(",
            "def _hand_status(",
            "def _eligible_double(",
            "def _eligible_split(",
            "def _free_double(",
            "def _free_split(",
            "def _can_surrender(",
            "def _advance(",
            "def _current(",
            "def _visible(",
            "def _pontoon_combo(",
            "def _main_result(",
            "def _normal_hand_return(",
        }

        for helper in blackjack_helpers:

            with self.subTest(
                helper=helper
            ):

                self.assertNotIn(
                    helper,
                    source,
                )

                self.assertIn(
                    helper,
                    blackjack,
                )

        self.assertNotIn(
            "BLACKJACK_GAMES =",
            source,
        )

        self.assertIn(
            "BLACKJACK_GAMES =",
            blackjack,
        )

        # The extracted module owns all three public operations.

        self.assertIn(
            "def blackjack_deal(",
            blackjack,
        )

        self.assertIn(
            "def blackjack_action(",
            blackjack,
        )

        self.assertIn(
            "def blackjack_settle(",
            blackjack,
        )

        # Game-specific implementation dependencies must no longer
        # leak into the public dispatcher.

        self.assertNotIn(
            "import game.registry as registry",
            source,
        )

        self.assertNotIn(
            "from game.blackjack_base import",
            source,
        )

        self.assertIn(
            "import game.registry as registry",
            blackjack,
        )

        self.assertIn(
            "from game.blackjack_base import",
            blackjack,
        )

        # Blackjack must use the extracted shared state-token
        # codec rather than reaching back into solo_bridge.py.
        #
        # The extracted adapter deliberately keeps the historical
        # _bj_enc / _bj_dec private names as local aliases so the
        # implementation can be extracted without changing the
        # established Blackjack state-machine behaviour.

        self.assertIn(
            "from bridge.state_token import",
            blackjack,
        )

        self.assertIn(
            "_bj_enc = encode_state",
            blackjack,
        )

        self.assertIn(
            "_bj_dec = decode_state",
            blackjack,
        )

        self.assertIn(
            "_bj_enc(",
            blackjack,
        )

        self.assertIn(
            "_bj_dec(",
            blackjack,
        )

        # Those compatibility aliases belong to bridge.blackjack,
        # not to the thin solo_bridge dispatch layer.

        self.assertNotIn(
            "_bj_enc = encode_state",
            source,
        )

        self.assertNotIn(
            "_bj_dec = decode_state",
            source,
        )

        self.assertNotIn(
            "from bridge.state_token import",
            source,
        )


    # ------------------------------------------------------------
    # THIN PUBLIC BRIDGE CONTRACT
    # ------------------------------------------------------------

    def test_solo_bridge_remains_thin_dispatch_layer(self):

        source = (
            RUNTIME
            / "solo_bridge.py"
        ).read_text(
            encoding="utf-8"
        )

        # After all game-family extractions, the public bridge should
        # contain only the dispatcher and JSON boundary functions.

        self.assertIn(
            "def dispatch(",
            source,
        )

        self.assertIn(
            "def dispatch_json(",
            source,
        )

        forbidden_definitions = {
            "def solo_spin(",
            "def craps_roll(",
            "def craps_action(",
            "def roulette_spin(",
            "def royal_three_pictures_deal(",
            "def poker_deal(",
            "def poker_action(",
            "def poker_settle(",
            "def blackjack_deal(",
            "def blackjack_action(",
            "def blackjack_settle(",
            "def dueling_8s_deal(",
            "def dueling_8s_action(",
            "def dueling_8s_settle(",
        }

        for definition in forbidden_definitions:

            with self.subTest(
                definition=definition
            ):

                self.assertNotIn(
                    definition,
                    source,
                )


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":

    unittest.main()
    