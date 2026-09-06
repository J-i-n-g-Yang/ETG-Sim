/*
 * Install the Pages API compatibility layer first.
 */
await import(
  "./api-shim.js"
);


/*
 * Then run the normal production Baccarat controller.
 *
 * From:
 *   /runtime/baccarat-loader.js
 *
 * to:
 *   /static/js/baccarat_solo.js
 */
await import(
  "../static/js/baccarat_solo.js"
);