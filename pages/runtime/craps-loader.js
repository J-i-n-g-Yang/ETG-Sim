/* ================================================================
   ETG SIM — GITHUB PAGES CRAPS LOADER

   The API shim must be installed before the normal Craps
   controller executes.
   ================================================================ */


/*
 * Install browser replacements for Flask endpoints.
 */

await import(
  "./api-shim.js"
);


/*
 * Run the existing production Craps controller.
 */

await import(
  "../static/js/craps_solo.js"
);