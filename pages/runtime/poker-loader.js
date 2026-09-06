/* ================================================================
   ETG SIM — GITHUB PAGES POKER LOADER

   Installs the browser API shim before executing the existing
   production Poker controller.
   ================================================================ */


/*
 * Install browser replacements for Flask endpoints.
 */

await import(
  "./api-shim.js"
);


/*
 * Run the existing Poker frontend unchanged.
 */

await import(
  "../static/js/poker_solo.js"
);