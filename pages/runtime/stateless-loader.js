/*
 * ETG Sim — generic stateless Pages loader.
 *
 * The generated HTML sets:
 *
 *     window.ETG_PAGES_CONTROLLER
 *
 * before this module executes.
 */


/*
 * Install the Flask API compatibility layer first.
 */

await import(
  "./api-shim.js"
);


const controller =
  window.ETG_PAGES_CONTROLLER;


if (!controller) {

  throw new Error(
    "ETG_PAGES_CONTROLLER was not configured."
  );
}


/*
 * Resolve against /runtime/stateless-loader.js:
 *
 * ../static/js/...
 */

const url =
  new URL(
    `../static/js/${controller}`,
    import.meta.url
  );


await import(
  url.href
);