/* ================================================================
   ETG SIM — GITHUB PAGES PYODIDE RUNTIME

   Loads the existing ETG Python game engines into the browser.

   The Flask/Docker edition does not use this file.
   ================================================================ */

const PYODIDE_VERSION = "0.28.2";

const PYODIDE_BASE =
  `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

let runtimePromise = null;


/* ================================================================
   PATH HELPERS
   ================================================================ */

function pagesRoot() {
  const url =
    new URL(
      import.meta.url
    );

  /*
   * Current file:
   *
   *   /ETG-Sim/runtime/pyodide-runtime.js
   *
   * Therefore ../ resolves to:
   *
   *   /ETG-Sim/
   */

  return new URL(
    "../",
    url
  );
}


/* ================================================================
   PYTHON SOURCE LOCATION

   Local development:
     repository/
       game/
       pages/

     page URL:
       http://localhost:8080/pages/

     Python URL:
       http://localhost:8080/game/


   GitHub Pages deployment:
     _site/
       python/game/
       runtime/

     page URL:
       https://.../ETG-Sim/

     Python URL:
       https://.../ETG-Sim/python/
   ================================================================ */

function isLocalRepositoryMode() {

  const path =
    window.location.pathname;

  return (
    path === "/pages/" ||
    path.startsWith("/pages/")
  );
}


function pythonRoot() {

  if (
    isLocalRepositoryMode()
  ) {

    /*
     * pyodide-runtime.js is being served directly from:
     *
     *   repository/pages/runtime/
     *
     * Existing Python engines live at:
     *
     *   repository/game/
     *
     * Our manifest entries already begin with "game/",
     * therefore the root must be the repository root.
     */

    return new URL(
      "../../",
      import.meta.url
    );
  }


  /*
   * GitHub Pages artifact:
   *
   *   /python/game/*
   */

  return new URL(
    "python/",
    pagesRoot()
  );
}

/* ================================================================
   LOAD EXTERNAL SCRIPT
   ================================================================ */

function loadScript(src) {

  return new Promise(
    (
      resolve,
      reject
    ) => {

      const existing =
        document.querySelector(
          `script[data-etg-src="${src}"]`
        );


      if (existing) {

        if (
          window.loadPyodide
        ) {

          resolve();

          return;
        }


        existing.addEventListener(
          "load",
          resolve,
          {
            once: true,
          }
        );


        existing.addEventListener(
          "error",
          reject,
          {
            once: true,
          }
        );


        return;
      }


      const script =
        document.createElement(
          "script"
        );


      script.src =
        src;


      script.async =
        true;


      script.dataset.etgSrc =
        src;


      script.addEventListener(
        "load",
        resolve,
        {
          once: true,
        }
      );


      script.addEventListener(
        "error",

        () => {

          reject(
            new Error(
              `Failed to load ${src}`
            )
          );
        },

        {
          once: true,
        }
      );


      document.head.appendChild(
        script
      );
    }
  );
}


/* ================================================================
   FETCH TEXT
   ================================================================ */

async function fetchText(url) {

  const response =
    await fetch(
      url,
      {
        cache:
          "no-store",
      }
    );


  if (
    !response.ok
  ) {

    throw new Error(
      `HTTP ${response.status} loading ${url}`
    );
  }


  return response.text();
}


/* ================================================================
   ENSURE DIRECTORY
   ================================================================ */

function ensureDir(
  FS,
  path
) {

  const parts =
    path
      .split("/")
      .filter(Boolean);


  let current =
    "";


  for (
    const part
    of parts
  ) {

    current +=
      `/${part}`;


    try {

      FS.mkdir(
        current
      );

    } catch {

      /*
       * Directory already exists.
       */

    }
  }
}


/* ================================================================
   PYTHON FILE MANIFEST

   These are copied from the deployed /python/game directory into
   Pyodide's in-memory filesystem.

   Keeping an explicit manifest makes failures obvious instead of
   silently discovering missing imports halfway through a game.
   ================================================================ */

const PYTHON_FILES = [

  "game/__init__.py",

  "game/registry.py",

  "game/baccarat.py",
  "game/baccarat_base.py",
  "game/baccarat_dragon_tiger.py",
  "game/baccarat_immortal.py",
  "game/baccarat_rising.py",

  "game/blackjack_base.py",
  "game/blackjack_freebet.py",
  "game/blackjack_kingsbounty.py",
  "game/blackjack_lucky8.py",
  "game/pontoon.py",

  "game/dice_base.py",
  "game/dice_engine.py",
  "game/sicbo.py",
  "game/great_fortune_dice.py",

  "game/craps.py",
  "game/craps_engine.py",

  "game/roulette.py",
  "game/roulette_base.py",
  "game/roulette_engine.py",
  "game/roulette_single_zero.py",
  "game/roulette_double_zero.py",
  "game/roulette_sands_roulette.py",

  "game/poker_base.py",
  "game/poker_engine.py",
  "game/poker_three_card_xtreme.py",
  "game/poker_singapore_stud.py",
  "game/poker_texas_holdem_bonus.py",
  "game/poker_ultimate_texas.py",
  "game/poker_mississippi_stud.py",
  "game/poker_fortune_pai_gow.py",
  "game/paigow_engine.py",

  "game/dueling_8s_21.py",

  "game/royal_three_pictures.py",
];


/* ================================================================
   INSTALL ETG PYTHON SOURCES
   ================================================================ */

async function installPythonSources(
  pyodide
) {

  ensureDir(
    pyodide.FS,
    "/etg"
  );


  for (
    const relativePath
    of PYTHON_FILES
  ) {

    const sourceURL =
      new URL(
        relativePath,
        pythonRoot()
      );


    const source =
      await fetchText(
        sourceURL
      );


    const destination =
      `/etg/${relativePath}`;


    const slash =
      destination.lastIndexOf(
        "/"
      );


    ensureDir(
      pyodide.FS,
      destination.slice(
        0,
        slash
      )
    );


    pyodide.FS.writeFile(
      destination,
      source
    );
  }


  await pyodide.runPythonAsync(`
import sys

if "/etg" not in sys.path:
    sys.path.insert(0, "/etg")
  `);
}


/* ================================================================
   BRIDGE FILE MANIFEST

   solo_bridge.py remains the public browser entry point.

   Shared bridge modules are installed first so solo_bridge.py can
   import them normally from /etg/bridge.

   Add game-family bridge modules here only after each extraction
   has independently passed the bridge contract tests.
   ================================================================ */

const BRIDGE_FILES = [
  "bridge/__init__.py",
  "bridge/common.py",
  "bridge/stateless.py",
  "bridge/craps.py",
  "bridge/roulette.py",
  "bridge/royal_three_pictures.py",
  "bridge/poker.py",
];


/* ================================================================
   INSTALL BRIDGE
   ================================================================ */

async function installBridge(
  pyodide
) {

  /*
   * Ensure the bridge package exists inside Pyodide.
   */

  ensureDir(
    pyodide.FS,
    "/etg/bridge"
  );


  /*
   * Install modular bridge files first.
   *
   * These URLs resolve relative to:
   *
   *   /runtime/pyodide-runtime.js
   *
   * therefore:
   *
   *   bridge/common.py
   *
   * resolves to:
   *
   *   /runtime/bridge/common.py
   */

  for (
    const relativePath
    of BRIDGE_FILES
  ) {

    const sourceURL =
      new URL(
        relativePath,
        import.meta.url
      );


    const source =
      await fetchText(
        sourceURL
      );


    const destination =
      `/etg/${relativePath}`;


    const slash =
      destination.lastIndexOf(
        "/"
      );


    ensureDir(
      pyodide.FS,
      destination.slice(
        0,
        slash
      )
    );


    pyodide.FS.writeFile(
      destination,
      source
    );
  }


  /*
   * Install the public bridge entry point.
   */

  const bridgeURL =
    new URL(
      "solo_bridge.py",
      import.meta.url
    );


  const bridgeSource =
    await fetchText(
      bridgeURL
    );


  pyodide.FS.writeFile(
    "/etg/solo_bridge.py",
    bridgeSource
  );


  /*
   * Import only after both the package and entry point exist.
   */

  await pyodide.runPythonAsync(`
import sys

if "/etg" not in sys.path:
    sys.path.insert(0, "/etg")

import bridge.common
import solo_bridge
  `);
}


/* ================================================================
   CREATE RUNTIME
   ================================================================ */

async function createRuntime() {

  await loadScript(
    `${PYODIDE_BASE}pyodide.js`
  );


  if (
    typeof window.loadPyodide !==
    "function"
  ) {

    throw new Error(
      "Pyodide loader did not initialise."
    );
  }


  const pyodide =
    await window.loadPyodide({
      indexURL:
        PYODIDE_BASE,
    });


  await installPythonSources(
    pyodide
  );


  await installBridge(
    pyodide
  );


  return pyodide;
}


/* ================================================================
   PUBLIC API
   ================================================================ */

export function getPyodideRuntime() {

  if (
    !runtimePromise
  ) {

    runtimePromise =
      createRuntime();
  }


  return runtimePromise;
}


export async function pythonCall(
  operation,
  payload = {}
) {

  const pyodide =
    await getPyodideRuntime();


  pyodide.globals.set(
    "__etg_operation",
    operation
  );


  pyodide.globals.set(
    "__etg_payload_json",
    JSON.stringify(
      payload
    )
  );


  try {

    const result =
      await pyodide.runPythonAsync(`
import solo_bridge

solo_bridge.dispatch_json(
    __etg_operation,
    __etg_payload_json
)
    `);


    return JSON.parse(
      result
    );


  } finally {

    pyodide.globals.delete(
      "__etg_operation"
    );


    pyodide.globals.delete(
      "__etg_payload_json"
    );
  }
}