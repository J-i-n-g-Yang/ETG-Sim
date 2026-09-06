/* ================================================================
   ETG SIM — GITHUB PAGES DUELING 8'S LOADER

   Installs the browser API replacement before loading the
   existing production Dueling 8's controller.
   ================================================================ */


/*
 * Install browser-side Flask endpoint replacements.
 */

await import(
  "./api-shim.js"
);


/*
 * Load the existing production frontend unchanged.
 */

await import(
  "../static/js/dueling_8s_solo.js"
);