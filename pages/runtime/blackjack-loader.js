/* ================================================================
   ETG SIM — GITHUB PAGES BLACKJACK LOADER
   ================================================================ */


/*
 * Install the browser-side Flask API replacement before loading
 * the existing Blackjack controller.
 */

await import(
  "./api-shim.js"
);


/*
 * Run the normal production Blackjack frontend.
 */

await import(
  "../static/js/blackjack_solo.js"
);