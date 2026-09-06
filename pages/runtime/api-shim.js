/* ================================================================
   ETG SIM — GITHUB PAGES API SHIM

   Browser replacements for Flask Solo endpoints.

   Supported:

   POST /api/solo/spin

   POST /api/solo/dice/roll
   POST /api/solo/dice/craps/action

   POST /api/solo/blackjack/deal
   POST /api/solo/blackjack/action
   POST /api/solo/blackjack/settle

   POST /api/solo/poker/deal
   POST /api/solo/poker/action
   POST /api/solo/poker/settle

   POST /api/solo/dueling-8s/deal
   POST /api/solo/dueling-8s/action
   POST /api/solo/dueling-8s/settle
   ================================================================ */

import {
  pythonCall,
} from "./pyodide-runtime.js";


const nativeFetch =
  window.fetch.bind(
    window
  );


/* ================================================================
   JSON RESPONSE
   ================================================================ */

function jsonResponse(
  body,
  status = 200
) {

  return new Response(
    JSON.stringify(
      body
    ),
    {
      status,

      headers: {
        "Content-Type":
          "application/json",
      },
    }
  );
}


/* ================================================================
   PATH
   ================================================================ */

function requestPath(
  input
) {

  if (
    input instanceof Request
  ) {

    return new URL(
      input.url,
      window.location.href
    ).pathname;
  }


  return new URL(
    String(
      input
    ),
    window.location.href
  ).pathname;
}


/* ================================================================
   JSON BODY
   ================================================================ */

async function requestJSON(
  input,
  init
) {

  if (
    init?.body !==
    undefined
  ) {

    if (
      typeof init.body ===
      "string"
    ) {

      return JSON.parse(
        init.body
      );
    }


    if (
      init.body instanceof
      URLSearchParams
    ) {

      return Object.fromEntries(
        init.body.entries()
      );
    }
  }


  if (
    input instanceof Request
  ) {

    return input
      .clone()
      .json();
  }


  return {};
}


/* ================================================================
   PYTHON CALL
   ================================================================ */

async function pythonResponse(
  operation,
  payload
) {

  const response =
    await pythonCall(
      operation,
      payload
    );


  if (
    !response.ok
  ) {

    console.error(
      `[ETG PAGES] ${operation} failed:`,
      response
    );


    return jsonResponse(
      {
        error:
          response.error ||
          "ETG browser engine failed",
      },
      400
    );
  }


  return jsonResponse(
    response.result
  );
}


/* ================================================================
   FETCH INTERCEPTOR
   ================================================================ */

window.fetch =
  async function etgPagesFetch(
    input,
    init = {}
  ) {

    const path =
      requestPath(
        input
      );


    /* ============================================================
       STATELESS

       Browser equivalent of:

           POST /api/solo/spin
       ============================================================ */

    if (
      path ===
      "/api/solo/spin"
    ) {

      try {

        return pythonResponse(
          "solo_spin",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Stateless spin failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Invalid spin request",
          },
          400
        );
      }
    }


    /* ============================================================
       DICE

       All three Dice-family controllers use:

           POST /api/solo/dice/roll

       Craps is stateful and therefore uses craps_roll.

       Sic Bo and Great Fortune Dice are stateless and therefore
       use solo_spin.

       IMPORTANT:
       Do NOT fall through to nativeFetch for the stateless Dice
       games. GitHub Pages has no Flask server to receive that POST.
       ============================================================ */

    if (
      path ===
      "/api/solo/dice/roll"
    ) {

      try {

        const payload =
          await requestJSON(
            input,
            init
          );


        if (
          payload.game ===
          "craps"
        ) {

          return pythonResponse(
            "craps_roll",
            payload
          );
        }


        if (
          payload.game ===
            "sicbo"
          ||
          payload.game ===
            "great_fortune_dice"
        ) {

          return pythonResponse(
            "solo_spin",
            payload
          );
        }


        return jsonResponse(
          {
            error:
              `Unsupported Dice game: ${
                payload.game ||
                "(missing)"
              }`,
          },
          400
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Dice roll failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Dice roll failed",
          },
          400
        );
      }
    }


    /* ============================================================
       CRAPS ACTION

       Browser equivalent of:

           POST /api/solo/dice/craps/action
       ============================================================ */

    if (
      path ===
      "/api/solo/dice/craps/action"
    ) {

      try {

        return pythonResponse(
          "craps_action",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Craps action failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Craps action failed",
          },
          400
        );
      }
    }


    /* ============================================================
       ROULETTE

       Browser equivalent of:

           POST /api/solo/roulette/spin
       ============================================================ */

    if (
      path ===
      "/api/solo/roulette/spin"
    ) {

      try {

        return pythonResponse(
          "roulette_spin",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Roulette spin failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Roulette spin failed",
          },
          400
        );
      }
    }


    /* ============================================================
       ROYAL THREE PICTURES

       Browser equivalent of:

           POST /api/solo/royal-three-pictures/deal
       ============================================================ */

    if (
      path ===
      "/api/solo/royal-three-pictures/deal"
    ) {

      try {

        return pythonResponse(
          "royal_three_pictures_deal",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Royal Three Pictures deal failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Royal Three Pictures deal failed",
          },
          400
        );
      }
    }


    /* ============================================================
       BLACKJACK — DEAL
       ============================================================ */

    if (
      path ===
      "/api/solo/blackjack/deal"
    ) {

      try {

        return pythonResponse(
          "blackjack_deal",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Blackjack deal failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Blackjack deal failed",
          },
          400
        );
      }
    }


    /* ============================================================
       BLACKJACK — ACTION
       ============================================================ */

    if (
      path ===
      "/api/solo/blackjack/action"
    ) {

      try {

        return pythonResponse(
          "blackjack_action",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Blackjack action failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Blackjack action failed",
          },
          400
        );
      }
    }


    /* ============================================================
       BLACKJACK — SETTLE
       ============================================================ */

    if (
      path ===
      "/api/solo/blackjack/settle"
    ) {

      try {

        return pythonResponse(
          "blackjack_settle",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Blackjack settlement failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Blackjack settlement failed",
          },
          400
        );
      }
    }


    /* ============================================================
       POKER — DEAL
       ============================================================ */

    if (
      path ===
      "/api/solo/poker/deal"
    ) {

      try {

        return pythonResponse(
          "poker_deal",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Poker deal failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Poker deal failed",
          },
          400
        );
      }
    }


    /* ============================================================
       POKER — ACTION
       ============================================================ */

    if (
      path ===
      "/api/solo/poker/action"
    ) {

      try {

        return pythonResponse(
          "poker_action",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Poker action failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Poker action failed",
          },
          400
        );
      }
    }


    /* ============================================================
       POKER — SETTLE
       ============================================================ */

    if (
      path ===
      "/api/solo/poker/settle"
    ) {

      try {

        return pythonResponse(
          "poker_settle",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Poker settlement failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Poker settlement failed",
          },
          400
        );
      }
    }


    /* ============================================================
       DUELING 8'S 21+ — DEAL
       ============================================================ */

    if (
      path ===
      "/api/solo/dueling-8s/deal"
    ) {

      try {

        return pythonResponse(
          "dueling_8s_deal",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Dueling 8s deal failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Dueling 8's deal failed",
          },
          400
        );
      }
    }


    /* ============================================================
       DUELING 8'S 21+ — ACTION
       ============================================================ */

    if (
      path ===
      "/api/solo/dueling-8s/action"
    ) {

      try {

        return pythonResponse(
          "dueling_8s_action",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Dueling 8s action failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Dueling 8's action failed",
          },
          400
        );
      }
    }


    /* ============================================================
       DUELING 8'S 21+ — SETTLE
       ============================================================ */

    if (
      path ===
      "/api/solo/dueling-8s/settle"
    ) {

      try {

        return pythonResponse(
          "dueling_8s_settle",
          await requestJSON(
            input,
            init
          )
        );

      } catch (error) {

        console.error(
          "[ETG PAGES] Dueling 8s settlement failed:",
          error
        );


        return jsonResponse(
          {
            error:
              error.message ||
              "Dueling 8's settlement failed",
          },
          400
        );
      }
    }


    /* ============================================================
       UNPORTED REQUEST

       Anything not explicitly supported above is allowed to use
       the browser's native fetch.

       During local GitHub Pages testing, an unexpected POST under
       /api/solo will therefore be visible immediately as a 501
       from python -m http.server.
       ============================================================ */

    return nativeFetch(
      input,
      init
    );
  };


console.log(
  "[ETG PAGES] Browser API shim installed."
);