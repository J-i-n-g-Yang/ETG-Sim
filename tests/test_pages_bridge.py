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
    # API SHIM ↔ BRIDGE CONTRACT
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


    def test_common_bridge_runtime_is_installed(self):

        """
        The first modular bridge extraction installs only the shared
        bridge package.

        solo_bridge.py remains the public Pyodide entry point while
        bridge.common provides shared helpers.
        """

        runtime = (
            RUNTIME
            / "pyodide-runtime.js"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "BRIDGE_FILES",
            runtime,
        )

        self.assertIn(
            '"bridge/__init__.py"',
            runtime,
        )

        self.assertIn(
            '"bridge/common.py"',
            runtime,
        )

        self.assertIn(
            "import bridge.common",
            runtime,
        )

        self.assertIn(
            "import solo_bridge",
            runtime,
        )


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":

    unittest.main()