import {
  getPyodideRuntime,
  pythonCall,
} from "./pyodide-runtime.js";


const $ = (id) =>
  document.getElementById(
    id
  );


function setStatus(
  message,
  state = ""
) {

  const element =
    $("runtimeStatus");


  if (!element) {
    return;
  }


  element.className =
    `runtime-status ${state}`;


  element.textContent =
    message;
}


async function boot() {

  setStatus(
    "Loading casino engine…",
    "loading"
  );


  try {

    await getPyodideRuntime();


    setStatus(
      "Checking ETG game engines…",
      "loading"
    );


    const response =
      await pythonCall(
        "runtime_info"
      );


    if (
      !response.ok
    ) {

      throw new Error(
        response.error ||
        "Python bridge failed."
      );
    }


    const info =
      response.result;


    if (
      !info.ok
    ) {

      console.error(
        "[ETG PAGES] Engine check failed:",
        info.modules
      );


      const failures =
        Object.entries(
          info.modules
        )
          .filter(
            (
              [, result]
            ) =>
              result !== true
          )
          .map(
            (
              [
                moduleName,
                result,
              ]
            ) =>
              `${moduleName}: ${result}`
          );


      throw new Error(
        failures.join(
          " | "
        )
      );
    }


    console.log(
      "[ETG PAGES] Runtime ready:",
      info
    );


    document.documentElement
      .classList
      .add(
        "etg-runtime-ready"
      );


    setStatus(
      "SOLO ENGINE READY",
      "ready"
    );


    document
      .querySelectorAll(
        "[data-requires-runtime]"
      )
      .forEach(
        (element) => {

          element.removeAttribute(
            "aria-disabled"
          );


          element.classList.remove(
            "disabled"
          );
        }
      );


  } catch (error) {

    console.error(
      "[ETG PAGES] Runtime startup failed:",
      error
    );


    setStatus(
      `ENGINE ERROR · ${error.message}`,
      "error"
    );
  }
}


boot();