/* ================================================================
   ETG SIM — ROULETTE SOLO

   Variants:
   - roulette_single_zero
   - roulette_double_zero
   - roulette_sands

   Features:
   - proper SVG roulette wheel
   - real annular wheel pockets
   - readable pocket numbers
   - independently animated roulette ball
   - slower multi-stage wheel spin
   - ball drops toward winning pocket
   - backend-selected authoritative result
   - straight bets
   - split hotspots
   - street hotspots
   - corner hotspots
   - six-line hotspots
   - zero-area wagers integrated into physical table
   - Sands Green / Top Line wagers
   - hover coverage highlighting
   ================================================================ */

const GAME = window.ROULETTE_GAME;
const MAX_BET = Number(window.ROULETTE_MAX);
const STARTING_CREDITS = Number(window.ROULETTE_START);

const $ = (id) =>
  document.getElementById(id);

const fmt = (value) =>
  Number(value).toLocaleString(
    undefined,
    {
      maximumFractionDigits: 2,
    }
  );


/* ================================================================
   STANDARD COLOURS
   ================================================================ */

const RED_NUMBERS = new Set([
  1, 3, 5, 7, 9,
  12, 14, 16, 18,
  19, 21, 23, 25, 27,
  30, 32, 34, 36,
]);


/* ================================================================
   WHEEL ORDERS
   ================================================================ */

const SINGLE_ZERO_WHEEL = [
  0,
  32,
  15,
  19,
  4,
  21,
  2,
  25,
  17,
  34,
  6,
  27,
  13,
  36,
  11,
  30,
  8,
  23,
  10,
  5,
  24,
  16,
  33,
  1,
  20,
  14,
  31,
  9,
  22,
  18,
  29,
  7,
  28,
  12,
  35,
  3,
  26,
];

const DOUBLE_ZERO_WHEEL = [
  0,
  28,
  9,
  26,
  30,
  11,
  7,
  20,
  32,
  17,
  5,
  22,
  34,
  15,
  3,
  24,
  36,
  13,
  1,
  "00",
  27,
  10,
  25,
  29,
  12,
  8,
  19,
  31,
  18,
  6,
  21,
  33,
  16,
  4,
  23,
  35,
  14,
  2,
];

/*
 * Sands visual rotor.
 *
 * Server result remains authoritative.
 */

const SANDS_WHEEL = [
  "S",
  0,
  32,
  15,
  19,
  4,
  21,
  2,
  25,
  17,
  34,
  6,
  27,
  13,
  36,
  11,
  30,
  8,
  23,
  10,
  5,
  24,
  16,
  33,
  1,
  "00",
  20,
  14,
  31,
  9,
  22,
  18,
  29,
  7,
  28,
  12,
  35,
  3,
  26,
];

function wheelOrder() {
  if (GAME === "roulette_double_zero") {
    return DOUBLE_ZERO_WHEEL;
  }

  if (GAME === "roulette_sands") {
    return SANDS_WHEEL;
  }

  return SINGLE_ZERO_WHEEL;
}


/* ================================================================
   CHIPS
   ================================================================ */

const CHIPS = [
  100,
  250,
  500,
  1000,
  2500,
  5000,
  10000,
  20000,
];

const CHIP_COLORS = {
  100: "#315b7b",
  250: "#315d2b",
  500: "#8c2929",
  1000: "#49449a",
  2500: "#87520d",
  5000: "#1d6969",
  10000: "#762176",
  20000: "#746b1c",
};


/* ================================================================
   STORAGE
   ================================================================ */

const BALANCE_KEY =
  `etg_roulette_bal_${GAME}`;

const HISTORY_KEY =
  `etg_roulette_history_${GAME}`;


/* ================================================================
   STATE
   ================================================================ */

let selectedChip = 1000;
let pendingBets = {};
let busy = false;

let balance =
  Number(
    localStorage.getItem(BALANCE_KEY) ??
    STARTING_CREDITS
  );

if (!Number.isFinite(balance)) {
  balance = STARTING_CREDITS;
}

let history = [];

try {
  history =
    JSON.parse(
      localStorage.getItem(HISTORY_KEY) ||
      "[]"
    );
} catch {
  history = [];
}


/* ================================================================
   ANIMATION STATE
   ================================================================ */

let wheelAngle = 0;
let ballAngle = 0;
let animationFrame = null;


/* ================================================================
   HELPERS
   ================================================================ */

function sleep(ms) {
  return new Promise(
    (resolve) =>
      setTimeout(resolve, ms)
  );
}

function chipLabel(value) {
  return (
    value >= 1000
      ? `${value / 1000}K`
      : String(value)
  );
}

function pendingTotal() {
  return Object
    .values(pendingBets)
    .reduce(
      (total, value) =>
        total + Number(value),
      0
    );
}

function saveBalance() {
  localStorage.setItem(
    BALANCE_KEY,
    String(balance)
  );

  const display =
    $("balanceDisplay");

  if (display) {
    display.textContent =
      fmt(balance);
  }
}

function saveHistory() {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(history)
  );
}

function normalisePocket(value) {
  if (
    value === 0 ||
    value === "0"
  ) {
    return "0";
  }

  return String(value);
}

function pocketColour(value) {
  const pocket =
    normalisePocket(value);

  if (
    pocket === "0" ||
    pocket === "00" ||
    pocket === "S"
  ) {
    return "green";
  }

  return RED_NUMBERS.has(
    Number(pocket)
  )
    ? "red"
    : "black";
}

function pocketLabel(value) {
  const pocket =
    normalisePocket(value);

  return (
    `${pocket} ${
      pocketColour(pocket)
        .toUpperCase()
    }`
  );
}


/* ================================================================
   CSS
   ================================================================ */

function installRouletteStyles() {
  if (
    document.getElementById(
      "etgRouletteStyles"
    )
  ) {
    return;
  }

  const style =
    document.createElement("style");

  style.id =
    "etgRouletteStyles";

  style.textContent = `

    /* ============================================================
       WHEEL
       ============================================================ */

    .roulette-wheel-svg {
      width: 100%;
      height: 100%;
      display: block;
      overflow: visible;
    }

    .roulette-wheel-pocket {
      stroke: #d9b54c;
      stroke-width: 0.8;
      transition:
        filter .2s ease,
        opacity .2s ease;
    }

    .roulette-wheel-pocket.red {
      fill: #a62828;
    }

    .roulette-wheel-pocket.black {
      fill: #121514;
    }

    .roulette-wheel-pocket.green {
      fill: #08733f;
    }

    .roulette-wheel-pocket.winning-pocket {
      filter:
        drop-shadow(
          0 0 7px #fff3a0
        )
        drop-shadow(
          0 0 13px #e7bb37
        );
    }

    .roulette-wheel-number {
      fill: #fffbe8;
      font-family:
        Georgia,
        "Times New Roman",
        serif;
      font-weight: 900;
      text-anchor: middle;
      dominant-baseline: middle;
      pointer-events: none;
      paint-order: stroke;
      stroke: #000;
      stroke-width: .55px;
    }

    .roulette-wheel-separator {
      stroke: #e2c15b;
      stroke-width: 1.2;
      pointer-events: none;
    }

    .roulette-wheel-inner-ring {
      fill: #8f5b0b;
      stroke: #efcf67;
      stroke-width: 2.5;
    }

    .roulette-wheel-hub-ring {
      fill:
        url(#rouletteHubGradient);
      stroke: #f1cc59;
      stroke-width: 2.5;
    }

    .roulette-wheel-hub {
      fill:
        url(#rouletteHubInnerGradient);
      stroke: #7a4a06;
      stroke-width: 2;
    }

    .roulette-wheel-cross {
      stroke: #8b5b10;
      stroke-width: 4;
      stroke-linecap: round;
      opacity: .8;
    }

    .roulette-wheel-logo {
      fill: #281700;
      font-family:
        Georgia,
        "Times New Roman",
        serif;
      font-size: 15px;
      font-weight: 900;
      text-anchor: middle;
      dominant-baseline: middle;
    }

    /* ============================================================
       INSIDE TABLE
       ============================================================ */

    .roulette-inside {
      display: grid;
      grid-template-columns:
        minmax(90px, .95fr)
        minmax(900px, 12fr);
      gap: 0;
      position: relative;
    }

    .zero-area {
      position: relative;
      display: grid;
      border:
        1px solid #d1aa3e;
      border-right: 0;
      border-radius:
        7px 0 0 7px;
      overflow: visible;
      z-index: 5;
    }

    .zero-area.single {
      grid-template-rows: 1fr;
    }

    .zero-area.double {
      grid-template-rows:
        repeat(2, 1fr);
    }

    .zero-area.sands {
      grid-template-rows:
        repeat(3, 1fr);
    }

    .roulette-zero {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;

      min-height: 100%;

      background:
        linear-gradient(
          145deg,
          #087642,
          #03502c
        );

      border-bottom:
        1px solid #d1aa3e;

      color: #fff;
      font-size: 25px;
      font-weight: 900;
      cursor: pointer;
    }

    .roulette-zero:last-child {
      border-bottom: 0;
    }

    .roulette-zero:hover,
    .roulette-zero.covered {
      filter:
        brightness(1.3);
      box-shadow:
        inset 0 0 16px #f8dc6a88;
    }

    .roulette-number-grid {
      position: relative;

      display: grid;

      grid-template-columns:
        repeat(12, 1fr);

      grid-template-rows:
        repeat(3, 1fr);

      min-height: 258px;

      overflow: visible;
    }

    .roulette-number {
      position: relative;

      display: flex;
      align-items: center;
      justify-content: center;

      min-height: 86px;

      border:
        1px solid #d1aa3e;

      color: #fff;
      font-size: 25px;
      font-weight: 900;

      cursor: pointer;

      transition:
        filter .15s ease,
        box-shadow .15s ease,
        transform .15s ease;
    }

    .roulette-number.red {
      background:
        linear-gradient(
          145deg,
          #b52b2b,
          #821c1c
        );
    }

    .roulette-number.black {
      background:
        linear-gradient(
          145deg,
          #202221,
          #0c0e0d
        );
    }

    .roulette-number:hover,
    .roulette-number.covered {
      filter:
        brightness(1.35);

      box-shadow:
        inset 0 0 15px #f7dc6980;
    }

    .roulette-number.winner,
    .roulette-zero.winner {
      box-shadow:
        inset 0 0 0 4px #fff4a4,
        inset 0 0 20px #ffd83d,
        0 0 18px #ffd83d;
      z-index: 9;
    }

    /* ============================================================
       STANDARD HOTSPOTS
       ============================================================ */

    .roulette-hotspot {
      position: absolute;
      z-index: 25;

      transform:
        translate(-50%, -50%);

      cursor: pointer;

      background:
        transparent;

      border-radius: 50%;
    }

    .roulette-hotspot:hover {
      background:
        rgba(
          255,
          226,
          95,
          .78
        );

      box-shadow:
        0 0 10px
        rgba(
          255,
          220,
          80,
          .95
        );
    }

    .roulette-hotspot.split-vertical {
      width: 42px;
      height: 14px;
      border-radius: 8px;
    }

    .roulette-hotspot.split-horizontal {
      width: 14px;
      height: 42px;
      border-radius: 8px;
    }

    .roulette-hotspot.corner {
      width: 21px;
      height: 21px;
    }

    .roulette-hotspot.street {
      width: 52px;
      height: 20px;
      border-radius: 10px;
    }

    .roulette-hotspot.sixline {
      width: 20px;
      height: 20px;
    }

    /* ============================================================
       ZERO-AREA HOTSPOTS

       These sit physically across the zero-number boundaries
       instead of appearing as a detached special-wager row.
       ============================================================ */

    .roulette-zero-hotspot {
      position: absolute;

      z-index: 40;

      transform:
        translate(-50%, -50%);

      cursor: pointer;

      background:
        transparent;

      border-radius: 50%;
    }

    .roulette-zero-hotspot:hover {
      background:
        rgba(
          255,
          224,
          88,
          .86
        );

      box-shadow:
        0 0 11px
        rgba(
          255,
          220,
          80,
          1
        );
    }

    .roulette-zero-hotspot.edge {
      width: 18px;
      height: 42px;
      border-radius: 9px;
    }

    .roulette-zero-hotspot.horizontal-edge {
      width: 48px;
      height: 17px;
      border-radius: 9px;
    }

    .roulette-zero-hotspot.intersection {
      width: 23px;
      height: 23px;
    }

    .roulette-zero-hotspot.street-zone {
      width: 42px;
      height: 23px;
      border-radius: 10px;
    }

    .roulette-zero-hotspot.topline-zone {
      width: 28px;
      height: 28px;
    }

    /* ============================================================
       BADGES
       ============================================================ */

    .bet-badge,
    .hotspot-badge {
      position: absolute;

      z-index: 70;

      min-width: 25px;

      padding: 2px 5px;

      border-radius: 999px;

      background:
        #e4bb36;

      color: #111;

      font-family:
        Arial,
        sans-serif;

      font-size: 9px;
      font-weight: 900;

      text-align: center;

      box-shadow:
        0 2px 5px #0008;

      pointer-events: none;
    }

    .bet-badge {
      top: 3px;
      right: 3px;
    }

    .hotspot-badge {
      left: 50%;
      top: 50%;
      transform:
        translate(-50%, -50%);
    }

    /* ============================================================
       OUTSIDE TABLE
       ============================================================ */

    .roulette-columns,
    .roulette-dozens,
    .roulette-outside {
      display: grid;
      gap: 4px;
      margin-top: 4px;
    }

    .roulette-columns {
      grid-template-columns:
        repeat(3, 1fr);
    }

    .roulette-dozens {
      grid-template-columns:
        repeat(3, 1fr);
    }

    .roulette-outside {
      grid-template-columns:
        repeat(6, 1fr);
    }

    .roulette-special {
      display: grid;
      grid-template-columns:
        repeat(2, 1fr);
      gap: 4px;
      margin-top: 4px;
    }

    .red-bet {
      background:
        #9e2424 !important;
    }

    .black-bet {
      background:
        #151817 !important;
    }

    /* ============================================================
       RESPONSIVE
       ============================================================ */

    @media(max-width: 1200px) {
      .roulette-inside {
        grid-template-columns:
          80px minmax(840px, 12fr);
      }

      .roulette-number-grid {
        min-height: 235px;
      }

      .roulette-number {
        min-height: 78px;
      }
    }
  `;

  document.head.appendChild(style);
}


/* ================================================================
   WAGER ID HELPERS
   ================================================================ */

function numericWager(
  prefix,
  numbers
) {
  const sorted =
    [...numbers]
      .map(Number)
      .sort(
        (a, b) =>
          a - b
      );

  return (
    `${prefix}_${sorted.join("_")}`
  );
}


/* ================================================================
   GENERIC BET CELL
   ================================================================ */

function betCell(
  wager,
  main,
  sub = "",
  extraClass = "",
  covers = []
) {
  const coverData =
    covers.length
      ? `data-covers="${covers.join(",")}"`
      : "";

  return `
    <div
      class="
        bet
        ${extraClass}
      "
      data-wager="${wager}"
      ${coverData}
    >
      ${main}

      ${
        sub
          ? `
            <small>
              ${sub}
            </small>
          `
          : ""
      }
    </div>
  `;
}


/* ================================================================
   SVG GEOMETRY
   ================================================================ */

function polarPoint(
  cx,
  cy,
  radius,
  degrees
) {
  const radians =
    (
      degrees -
      90
    ) *
    Math.PI /
    180;

  return {
    x:
      cx +
      radius *
      Math.cos(radians),

    y:
      cy +
      radius *
      Math.sin(radians),
  };
}

function annularSectorPath(
  cx,
  cy,
  innerRadius,
  outerRadius,
  startAngle,
  endAngle
) {
  const outerStart =
    polarPoint(
      cx,
      cy,
      outerRadius,
      startAngle
    );

  const outerEnd =
    polarPoint(
      cx,
      cy,
      outerRadius,
      endAngle
    );

  const innerEnd =
    polarPoint(
      cx,
      cy,
      innerRadius,
      endAngle
    );

  const innerStart =
    polarPoint(
      cx,
      cy,
      innerRadius,
      startAngle
    );

  const span =
    endAngle -
    startAngle;

  const largeArc =
    span > 180
      ? 1
      : 0;

  return [
    `M ${outerStart.x} ${outerStart.y}`,

    `A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${outerEnd.x} ${outerEnd.y}`,

    `L ${innerEnd.x} ${innerEnd.y}`,

    `A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${innerStart.x} ${innerStart.y}`,

    "Z",
  ].join(" ");
}


/* ================================================================
   PROPER SVG WHEEL
   ================================================================ */

function renderWheel() {
  const rotor =
    $("rouletteRotor");

  const pockets =
    wheelOrder();

  const count =
    pockets.length;

  const step =
    360 / count;

  const cx = 180;
  const cy = 180;

  const pocketOuter =
    165;

  const pocketInner =
    121;

  const numberRadius =
    143;

  const pocketPaths = [];
  const numberLabels = [];
  const separators = [];

  pockets.forEach(
    (
      pocket,
      index
    ) => {
      const centreAngle =
        index * step;

      const startAngle =
        centreAngle -
        step / 2;

      const endAngle =
        centreAngle +
        step / 2;

      const path =
        annularSectorPath(
          cx,
          cy,
          pocketInner,
          pocketOuter,
          startAngle,
          endAngle
        );

      pocketPaths.push(`
        <path
          class="
            roulette-wheel-pocket
            ${pocketColour(pocket)}
          "
          data-wheel-pocket="${normalisePocket(pocket)}"
          d="${path}"
        ></path>
      `);

      const textPoint =
        polarPoint(
          cx,
          cy,
          numberRadius,
          centreAngle
        );

      /*
       * Rotate each number so its baseline follows the radial
       * direction while remaining readable from outside the wheel.
       */

      let textRotation =
        centreAngle;

      if (
        textRotation > 90 &&
        textRotation < 270
      ) {
        textRotation += 180;
      }

      numberLabels.push(`
        <text
          class="
            roulette-wheel-number
          "
          x="${textPoint.x}"
          y="${textPoint.y}"
          font-size="${
            normalisePocket(pocket)
              .length > 1
              ? 10
              : 11.5
          }"
          transform="
            rotate(
              ${textRotation}
              ${textPoint.x}
              ${textPoint.y}
            )
          "
        >
          ${normalisePocket(pocket)}
        </text>
      `);

      const separatorOuter =
        polarPoint(
          cx,
          cy,
          pocketOuter,
          startAngle
        );

      const separatorInner =
        polarPoint(
          cx,
          cy,
          pocketInner,
          startAngle
        );

      separators.push(`
        <line
          class="
            roulette-wheel-separator
          "
          x1="${separatorInner.x}"
          y1="${separatorInner.y}"
          x2="${separatorOuter.x}"
          y2="${separatorOuter.y}"
        ></line>
      `);
    }
  );

  rotor.innerHTML = `
    <svg
      class="
        roulette-wheel-svg
      "
      viewBox="0 0 360 360"
      aria-label="Roulette wheel"
    >

      <defs>

        <radialGradient
          id="rouletteHubGradient"
          cx="40%"
          cy="35%"
          r="70%"
        >
          <stop
            offset="0%"
            stop-color="#f4d267"
          ></stop>

          <stop
            offset="40%"
            stop-color="#c28a1d"
          ></stop>

          <stop
            offset="100%"
            stop-color="#604006"
          ></stop>
        </radialGradient>

        <radialGradient
          id="rouletteHubInnerGradient"
          cx="40%"
          cy="35%"
          r="70%"
        >
          <stop
            offset="0%"
            stop-color="#ffe98d"
          ></stop>

          <stop
            offset="45%"
            stop-color="#d7a532"
          ></stop>

          <stop
            offset="100%"
            stop-color="#7b4d08"
          ></stop>
        </radialGradient>

      </defs>


      <!-- dark outer rotor -->

      <circle
        cx="180"
        cy="180"
        r="173"
        fill="#15120c"
        stroke="#d7a72d"
        stroke-width="5"
      ></circle>


      <!-- pocket ring -->

      ${pocketPaths.join("")}

      ${separators.join("")}

      ${numberLabels.join("")}


      <!-- inner gold ring -->

      <circle
        class="
          roulette-wheel-inner-ring
        "
        cx="180"
        cy="180"
        r="116"
      ></circle>


      <!-- hub -->

      <circle
        class="
          roulette-wheel-hub-ring
        "
        cx="180"
        cy="180"
        r="91"
      ></circle>

      <circle
        class="
          roulette-wheel-hub
        "
        cx="180"
        cy="180"
        r="43"
      ></circle>


      <!-- decorative spindle -->

      <line
        class="
          roulette-wheel-cross
        "
        x1="180"
        y1="101"
        x2="180"
        y2="259"
      ></line>

      <line
        class="
          roulette-wheel-cross
        "
        x1="101"
        y1="180"
        x2="259"
        y2="180"
      ></line>


      <text
        class="
          roulette-wheel-logo
        "
        x="180"
        y="180"
      >
        ETG
      </text>

    </svg>
  `;
}


/* ================================================================
   TABLE NUMBER CELLS
   ================================================================ */

function numberCell(number) {
  return `
    <div
      class="
        roulette-number
        ${pocketColour(number)}
      "
      data-wager="straight_${number}"
      data-pocket="${number}"
      data-covers="${number}"
    >
      ${number}
    </div>
  `;
}

function zeroCell(pocket) {
  return `
    <div
      class="
        roulette-zero
      "
      data-wager="straight_${pocket}"
      data-pocket="${pocket}"
      data-covers="${pocket}"
    >
      ${pocket}
    </div>
  `;
}


/* ================================================================
   NUMBER GRID
   ================================================================ */

function numberAt(
  column,
  row
) {
  if (row === 0) {
    return (
      3 *
      (
        column + 1
      )
    );
  }

  if (row === 1) {
    return (
      3 *
      (
        column + 1
      ) -
      1
    );
  }

  return (
    3 *
    (
      column + 1
    ) -
    2
  );
}


/* ================================================================
   GENERIC HOTSPOT
   ================================================================ */

function hotspotHTML(
  wager,
  covers,
  className,
  left,
  top
) {
  return `
    <div
      class="
        roulette-hotspot
        ${className}
      "
      data-wager="${wager}"
      data-covers="${covers.join(",")}"
      style="
        left:${left}%;
        top:${top}%;
      "
      title="${wager}"
    ></div>
  `;
}


/* ================================================================
   STANDARD 1–36 HOTSPOTS
   ================================================================ */

function renderStandardHotspots() {
  const hotspots = [];

  /*
   * Splits between rows in the same street.
   */

  for (
    let column = 0;
    column < 12;
    column++
  ) {
    const x =
      (
        column +
        .5
      ) /
      12 *
      100;

    for (
      let boundary = 1;
      boundary <= 2;
      boundary++
    ) {
      const first =
        numberAt(
          column,
          boundary - 1
        );

      const second =
        numberAt(
          column,
          boundary
        );

      const y =
        boundary /
        3 *
        100;

      hotspots.push(
        hotspotHTML(
          numericWager(
            "split",
            [
              first,
              second,
            ]
          ),
          [
            first,
            second,
          ],
          "split-vertical",
          x,
          y
        )
      );
    }
  }


  /*
   * Splits between adjacent streets.
   */

  for (
    let column = 0;
    column < 11;
    column++
  ) {
    const x =
      (
        column +
        1
      ) /
      12 *
      100;

    for (
      let row = 0;
      row < 3;
      row++
    ) {
      const first =
        numberAt(
          column,
          row
        );

      const second =
        numberAt(
          column + 1,
          row
        );

      const y =
        (
          row +
          .5
        ) /
        3 *
        100;

      hotspots.push(
        hotspotHTML(
          numericWager(
            "split",
            [
              first,
              second,
            ]
          ),
          [
            first,
            second,
          ],
          "split-horizontal",
          x,
          y
        )
      );
    }
  }


  /*
   * Corners.
   */

  for (
    let column = 0;
    column < 11;
    column++
  ) {
    const x =
      (
        column +
        1
      ) /
      12 *
      100;

    for (
      let row = 0;
      row < 2;
      row++
    ) {
      const covers = [
        numberAt(
          column,
          row
        ),

        numberAt(
          column,
          row + 1
        ),

        numberAt(
          column + 1,
          row
        ),

        numberAt(
          column + 1,
          row + 1
        ),
      ];

      const y =
        (
          row +
          1
        ) /
        3 *
        100;

      hotspots.push(
        hotspotHTML(
          numericWager(
            "corner",
            covers
          ),
          covers,
          "corner",
          x,
          y
        )
      );
    }
  }


  /*
   * Streets.
   */

  for (
    let column = 0;
    column < 12;
    column++
  ) {
    const covers = [
      numberAt(
        column,
        0
      ),
      numberAt(
        column,
        1
      ),
      numberAt(
        column,
        2
      ),
    ];

    const x =
      (
        column +
        .5
      ) /
      12 *
      100;

    hotspots.push(
      hotspotHTML(
        numericWager(
          "street",
          covers
        ),
        covers,
        "street",
        x,
        100
      )
    );
  }


  /*
   * Six Lines.
   */

  for (
    let column = 0;
    column < 11;
    column++
  ) {
    const covers = [];

    for (
      const currentColumn of [
        column,
        column + 1,
      ]
    ) {
      for (
        let row = 0;
        row < 3;
        row++
      ) {
        covers.push(
          numberAt(
            currentColumn,
            row
          )
        );
      }
    }

    const x =
      (
        column +
        1
      ) /
      12 *
      100;

    hotspots.push(
      hotspotHTML(
        numericWager(
          "sixline",
          covers
        ),
        covers,
        "sixline",
        x,
        100
      )
    );
  }

  return hotspots.join("");
}


/* ================================================================
   ZERO-AREA HOTSPOT HELPERS
   ================================================================ */

function zeroHotspot(
  wager,
  covers,
  className,
  left,
  top
) {
  return `
    <div
      class="
        roulette-zero-hotspot
        ${className}
      "
      data-wager="${wager}"
      data-covers="${covers.join(",")}"
      style="
        left:${left}%;
        top:${top}%;
      "
      title="${wager}"
    ></div>
  `;
}


/* ================================================================
   ZERO-AREA PHYSICAL BETTING ZONES
   ================================================================ */

function renderZeroHotspots() {
  const spots = [];

  /*
   * Coordinates are relative to .roulette-inside.
   *
   * The zero region occupies the left side and the 1/2/3 street
   * begins immediately to its right.
   *
   * These targets therefore physically sit on the appropriate
   * shared borders/intersections instead of living in a separate
   * special-bet list.
   */

  if (
    GAME ===
    "roulette_single_zero"
  ) {
    /*
     * 0 / 3
     * 0 / 2
     * 0 / 1
     *
     * Shared zero-number boundary.
     */

    spots.push(
      zeroHotspot(
        "split_0_3",
        ["0", "3"],
        "edge",
        7.25,
        16.67
      ),

      zeroHotspot(
        "split_0_2",
        ["0", "2"],
        "edge",
        7.25,
        50
      ),

      zeroHotspot(
        "split_0_1",
        ["0", "1"],
        "edge",
        7.25,
        83.33
      ),

      /*
       * 0 / 1 / 2 / 3
       *
       * Casino basket/four-number intersection.
       */

      zeroHotspot(
        "corner_0_1_2_3",
        ["0", "1", "2", "3"],
        "intersection",
        7.25,
        100
      )
    );
  }


  else if (
    GAME ===
    "roulette_double_zero"
  ) {
    /*
     * Physical zero stack:
     *
     * 0
     * 00
     */

    spots.push(
      zeroHotspot(
        "split_0_00",
        ["0", "00"],
        "horizontal-edge",
        3.6,
        50
      ),

      zeroHotspot(
        "split_0_3",
        ["0", "3"],
        "edge",
        7.25,
        16.67
      ),

      zeroHotspot(
        "split_0_2",
        ["0", "2"],
        "edge",
        7.25,
        50
      ),

      zeroHotspot(
        "split_0_1",
        ["0", "1"],
        "edge",
        7.25,
        83.33
      ),

      zeroHotspot(
        "street_0_2_3",
        ["0", "2", "3"],
        "street-zone",
        7.25,
        33.33
      ),

      zeroHotspot(
        "street_0_1_2",
        ["0", "1", "2"],
        "street-zone",
        7.25,
        66.67
      ),

      zeroHotspot(
        "corner_0_1_2_3",
        ["0", "1", "2", "3"],
        "intersection",
        7.25,
        100
      ),

      zeroHotspot(
        "corner_0_00_1_2",
        ["0", "00", "1", "2"],
        "intersection",
        5.55,
        66.67
      ),

      zeroHotspot(
        "corner_0_00_2_3",
        ["0", "00", "2", "3"],
        "intersection",
        5.55,
        33.33
      )
    );
  }


  else if (
    GAME ===
    "roulette_sands"
  ) {
    /*
     * Physical Sands zero stack:
     *
     * S
     * 00
     * 0
     */

    spots.push(
      zeroHotspot(
        "split_S_00",
        ["S", "00"],
        "horizontal-edge",
        3.6,
        33.33
      ),

      zeroHotspot(
        "split_00_0",
        ["00", "0"],
        "horizontal-edge",
        3.6,
        66.67
      ),

      /*
       * S / 0 is a Sands-specific accepted wager.
       * It gets its own central zero-area intersection.
       */

      zeroHotspot(
        "split_S_0",
        ["S", "0"],
        "intersection",
        3.6,
        50
      ),

      zeroHotspot(
        "split_00_3",
        ["00", "3"],
        "edge",
        7.25,
        16.67
      ),

      zeroHotspot(
        "split_00_2",
        ["00", "2"],
        "edge",
        7.25,
        50
      ),

      zeroHotspot(
        "split_0_2",
        ["0", "2"],
        "edge",
        7.25,
        66.67
      ),

      zeroHotspot(
        "split_0_1",
        ["0", "1"],
        "edge",
        7.25,
        83.33
      ),

      zeroHotspot(
        "street_S_00_0",
        ["S", "00", "0"],
        "street-zone",
        3.6,
        100
      ),

      zeroHotspot(
        "street_00_0_2",
        ["00", "0", "2"],
        "street-zone",
        6.15,
        66.67
      ),

      zeroHotspot(
        "street_0_1_2",
        ["0", "1", "2"],
        "street-zone",
        7.25,
        83.33
      ),

      zeroHotspot(
        "street_00_2_3",
        ["00", "2", "3"],
        "street-zone",
        7.25,
        33.33
      ),

      zeroHotspot(
        "corner_S_00_0_2",
        ["S", "00", "0", "2"],
        "intersection",
        5.25,
        66.67
      ),

      zeroHotspot(
        "corner_00_0_2_3",
        ["00", "0", "2", "3"],
        "intersection",
        6.2,
        50
      ),

      /*
       * Keep this wager ID EXACTLY as accepted by the Sands
       * backend. Do not sort it.
       */

      zeroHotspot(
        "corner_0_1_2_00",
        ["0", "1", "2", "00"],
        "intersection",
        6.2,
        83.33
      )
    );
  }

  return spots.join("");
}


/* ================================================================
   BOARD
   ================================================================ */

function renderBoard() {
  const numbers = [];

  /*
   * Physical table order:
   *
   * 3  6  9 ... 36
   * 2  5  8 ... 35
   * 1  4  7 ... 34
   */

  for (
    let row = 0;
    row < 3;
    row++
  ) {
    for (
      let column = 0;
      column < 12;
      column++
    ) {
      numbers.push(
        numberCell(
          numberAt(
            column,
            row
          )
        )
      );
    }
  }


  let zeroClass =
    "single";

  let zeroHTML =
    zeroCell("0");


  if (
    GAME ===
    "roulette_double_zero"
  ) {
    zeroClass =
      "double";

    zeroHTML = `
      ${zeroCell("0")}
      ${zeroCell("00")}
    `;
  }


  else if (
    GAME ===
    "roulette_sands"
  ) {
    zeroClass =
      "sands";

    zeroHTML = `
      ${zeroCell("S")}
      ${zeroCell("00")}
      ${zeroCell("0")}
    `;
  }


  const sandsOutside =
    GAME === "roulette_sands"
      ? `
        <div class="roulette-special">

          ${betCell(
            "top_line",
            "<strong>TOP LINE</strong>",
            "S · 00 · 0 · 1 · 2 · 3 · 5:1",
            "",
            [
              "S",
              "00",
              "0",
              "1",
              "2",
              "3",
            ]
          )}

          ${betCell(
            "green",
            "<strong>GREEN</strong>",
            "S · 00 · 0 · 11:1",
            "",
            [
              "S",
              "00",
              "0",
            ]
          )}

        </div>
      `
      : "";


  $("bettingArea")
    .innerHTML = `

      <div
        class="
          roulette-inside
        "
        id="
          rouletteInside
        "
      >

        <div
          class="
            zero-area
            ${zeroClass}
          "
        >
          ${zeroHTML}
        </div>


        <div
          class="
            roulette-number-grid
          "
          id="
            rouletteNumberGrid
          "
        >

          ${numbers.join("")}

          ${renderStandardHotspots()}

        </div>


        <!--
          Zero wagers are now physically integrated into the
          roulette layout. There is intentionally NO detached
          zero-special wager row.
        -->

        ${renderZeroHotspots()}

      </div>


      <div class="roulette-columns">

        ${betCell(
          "column_1",
          "<strong>1st COLUMN</strong>",
          "2:1"
        )}

        ${betCell(
          "column_2",
          "<strong>2nd COLUMN</strong>",
          "2:1"
        )}

        ${betCell(
          "column_3",
          "<strong>3rd COLUMN</strong>",
          "2:1"
        )}

      </div>


      <div class="roulette-dozens">

        ${betCell(
          "dozen_1",
          "<strong>1st 12</strong>",
          "1–12 · 2:1"
        )}

        ${betCell(
          "dozen_2",
          "<strong>2nd 12</strong>",
          "13–24 · 2:1"
        )}

        ${betCell(
          "dozen_3",
          "<strong>3rd 12</strong>",
          "25–36 · 2:1"
        )}

      </div>


      <div class="roulette-outside">

        ${betCell(
          "low",
          "<strong>1–18</strong>",
          "1:1"
        )}

        ${betCell(
          "even",
          "<strong>EVEN</strong>",
          "1:1"
        )}

        ${betCell(
          "red",
          "<strong>RED</strong>",
          "1:1",
          "red-bet"
        )}

        ${betCell(
          "black",
          "<strong>BLACK</strong>",
          "1:1",
          "black-bet"
        )}

        ${betCell(
          "odd",
          "<strong>ODD</strong>",
          "1:1"
        )}

        ${betCell(
          "high",
          "<strong>19–36</strong>",
          "1:1"
        )}

      </div>


      ${sandsOutside}
    `;


  bindWagers();
  bindCoverageHover();
  refresh();
}


/* ================================================================
   COVERAGE HOVER
   ================================================================ */

function clearCoverageHighlight() {
  document
    .querySelectorAll(
      ".covered"
    )
    .forEach(
      (element) =>
        element.classList.remove(
          "covered"
        )
    );
}

function highlightCoverage(covers) {
  clearCoverageHighlight();

  covers.forEach(
    (pocket) => {
      document
        .querySelectorAll(
          `[data-pocket="${pocket}"]`
        )
        .forEach(
          (element) =>
            element.classList.add(
              "covered"
            )
        );
    }
  );
}

function bindCoverageHover() {
  document
    .querySelectorAll(
      "[data-covers]"
    )
    .forEach(
      (element) => {
        element.addEventListener(
          "mouseenter",
          () => {
            const covers =
              String(
                element.dataset.covers ||
                ""
              )
                .split(",")
                .filter(Boolean);

            highlightCoverage(
              covers
            );
          }
        );

        element.addEventListener(
          "mouseleave",
          clearCoverageHighlight
        );
      }
    );
}


/* ================================================================
   CHIPS
   ================================================================ */

function renderChips() {
  const bar =
    $("chipBar");

  bar.innerHTML = "";

  CHIPS.forEach(
    (value) => {
      const button =
        document.createElement(
          "button"
        );

      button.className =
        `chip${
          selectedChip === value
            ? " active"
            : ""
        }`;

      button.textContent =
        chipLabel(value);

      button.style.background =
        `radial-gradient(
          circle at 35% 30%,
          ${CHIP_COLORS[value]},
          #111
        )`;

      button.onclick = () => {
        if (busy) {
          return;
        }

        selectedChip =
          value;

        renderChips();
      };

      bar.appendChild(
        button
      );
    }
  );
}


/* ================================================================
   BETTING
   ================================================================ */

function bindWagers() {
  document
    .querySelectorAll(
      "[data-wager]"
    )
    .forEach(
      (element) => {
        element.addEventListener(
          "click",
          (event) => {
            event.stopPropagation();

            placeBet(
              element.dataset.wager
            );
          }
        );
      }
    );
}

function placeBet(wagerType) {
  if (busy) {
    return;
  }

  if (
    balance <
    selectedChip
  ) {
    return;
  }

  if (
    pendingTotal() +
    selectedChip >
    MAX_BET
  ) {
    return;
  }

  pendingBets[
    wagerType
  ] =
    (
      pendingBets[
        wagerType
      ] || 0
    ) +
    selectedChip;

  balance -=
    selectedChip;

  saveBalance();

  refresh();
}


/* ================================================================
   REFRESH
   ================================================================ */

function refresh() {
  const pending =
    pendingTotal();

  $("pendingTotal")
    .textContent =
      fmt(pending);

  $("stakeMetric")
    .textContent =
      fmt(pending);

  $("spinBtn")
    .disabled =
      busy ||
      pending <= 0;

  $("clearBtn")
    .disabled =
      busy ||
      pending <= 0;


  document
    .querySelectorAll(
      "[data-wager]"
    )
    .forEach(
      (element) => {
        const wager =
          element.dataset.wager;

        const amount =
          Number(
            pendingBets[wager] || 0
          );

        let badge =
          element.querySelector(
            ":scope > .bet-badge, :scope > .hotspot-badge"
          );

        if (
          amount <= 0
        ) {
          if (badge) {
            badge.remove();
          }

          return;
        }

        if (!badge) {
          badge =
            document.createElement(
              "span"
            );

          badge.className =
            (
              element.classList.contains(
                "roulette-hotspot"
              ) ||
              element.classList.contains(
                "roulette-zero-hotspot"
              )
            )
              ? "hotspot-badge"
              : "bet-badge";

          element.appendChild(
            badge
          );
        }

        badge.textContent =
          fmt(amount);
      }
    );
}


/* ================================================================
   CLEAR BETS
   ================================================================ */

function clearBets() {
  if (busy) {
    return;
  }

  balance +=
    pendingTotal();

  pendingBets = {};

  saveBalance();

  refresh();
}

/* ================================================================
   ROTOR / BALL TRANSFORMS
   ================================================================ */

function setRotorAngle(angle) {
  wheelAngle = angle;

  const rotor =
    $("rouletteRotor");

  if (!rotor) {
    return;
  }

  rotor.style.transform =
    `translate(-50%,-50%) rotate(${angle}deg)`;
}

function setBallAngle(
  angle,
  diameter = 316
) {
  ballAngle = angle;

  const orbit =
    $("rouletteBallOrbit");

  if (!orbit) {
    return;
  }

  orbit.style.width =
    `${diameter}px`;

  orbit.style.height =
    `${diameter}px`;

  orbit.style.transform =
    `translate(-50%,-50%) rotate(${angle}deg)`;
}


/* ================================================================
   ANIMATION FRAME CONTROLLER
   ================================================================ */

function cancelSpinAnimation() {
  if (
    animationFrame !== null
  ) {
    cancelAnimationFrame(
      animationFrame
    );

    animationFrame = null;
  }
}

function animateFor(
  duration,
  update
) {
  return new Promise(
    (resolve) => {
      const started =
        performance.now();

      function frame(now) {
        const progress =
          Math.min(
            1,
            (
              now -
              started
            ) /
            duration
          );

        update(progress);

        if (
          progress < 1
        ) {
          animationFrame =
            requestAnimationFrame(
              frame
            );
        } else {
          animationFrame = null;
          resolve();
        }
      }

      animationFrame =
        requestAnimationFrame(
          frame
        );
    }
  );
}

function easeOutCubic(t) {
  return (
    1 -
    Math.pow(
      1 - t,
      3
    )
  );
}

function easeInOutCubic(t) {
  return (
    t < .5
      ? 4 * t * t * t
      : 1 -
        Math.pow(
          -2 * t + 2,
          3
        ) /
        2
  );
}

function easeOutQuint(t) {
  return (
    1 -
    Math.pow(
      1 - t,
      5
    )
  );
}


/* ================================================================
   FREE SPIN

   Slower than the previous version.

   Wheel:
   clockwise.

   Ball:
   counter-clockwise.

   The wheel is intentionally not excessively fast because the
   player should still be able to visually perceive the numbered
   rotor.
   ================================================================ */

async function runFreeSpin() {
  const startWheel =
    wheelAngle;

  const startBall =
    ballAngle;

  await animateFor(
    3400,
    (progress) => {
      const wheelProgress =
        easeInOutCubic(
          progress
        );

      /*
       * Roughly 2.65 wheel revolutions.
       */

      setRotorAngle(
        startWheel +
        wheelProgress *
        955
      );

      /*
       * Ball travels faster than the wheel in the opposite
       * direction, roughly 5.4 revolutions.
       */

      setBallAngle(
        startBall -
        progress *
        1945,
        316
      );
    }
  );
}


/* ================================================================
   POCKET GEOMETRY
   ================================================================ */

function pocketIndex(pocket) {
  const target =
    normalisePocket(
      pocket
    );

  return wheelOrder()
    .findIndex(
      (value) =>
        normalisePocket(
          value
        ) === target
    );
}

function shortestPositiveAngle(angle) {
  return (
    (
      angle %
      360
    ) +
    360
  ) %
  360;
}


/* ================================================================
   LAND BALL ON BACKEND RESULT

   Important geometry:

   The pointer is at the top of the wheel.

   Each SVG pocket is centred on:
       index * step

   Therefore the rotor must finish at:
       -(index * step)

   Once that pocket is under the pointer, the ball is brought
   to the same top position.
   ================================================================ */

   async function landOnPocket(pocket) {
  const order =
    wheelOrder();

  const index =
    pocketIndex(
      pocket
    );

  if (index < 0) {
    throw new Error(
      `Unknown wheel pocket: ${pocket}`
    );
  }

  const step =
    360 / order.length;

  /*
   * Each pocket is drawn with its centre at:
   *
   *     index * step
   *
   * Pocket 0 is at the top of the SVG.
   *
   * To put the winning pocket at the fixed
   * top position, rotate the rotor by the
   * negative of the pocket angle.
   */

  const targetRotorNormal =
    shortestPositiveAngle(
      -(index * step)
    );

  const currentRotorNormal =
    shortestPositiveAngle(
      wheelAngle
    );

  let rotorTravel =
    shortestPositiveAngle(
      targetRotorNormal -
      currentRotorNormal
    );

  /*
   * Continue clockwise for two more turns.
   */

  rotorTravel += 720;

  const startWheel =
    wheelAngle;

  const startBall =
    ballAngle;


  /* ============================================================
     STAGE 1
     WHEEL DECELERATION + BALL SPIRAL
     ============================================================ */

  await animateFor(
    2500,

    (progress) => {
      const wheelProgress =
        easeOutQuint(
          progress
        );

      const ballProgress =
        easeOutCubic(
          progress
        );

      setRotorAngle(
        startWheel +
        rotorTravel *
        wheelProgress
      );


      /*
       * Smoothly move the ball inward.
       *
       * Keep it on the outer rail for the
       * first small part of the slowdown,
       * then gradually descend.
       */

      const dropProgress =
        Math.max(
          0,
          Math.min(
            1,
            (
              progress -
              0.12
            ) /
            0.88
          )
        );

      const smoothDrop =
        dropProgress *
        dropProgress *
        (
          3 -
          2 *
          dropProgress
        );

      const diameter =
        316 -
        48 *
        smoothDrop;


      /*
       * Ball continues counter-clockwise.
       */

      setBallAngle(
        startBall -
        900 *
        ballProgress,
        diameter
      );
    }
  );


  /* ============================================================
     LOCK ROTOR EXACTLY
     ============================================================ */

  /*
   * Do not use Math.round() on the old angle here.
   *
   * Instead calculate an equivalent absolute angle
   * at or beyond the current rotor position.
   */

  const currentTurns =
    Math.floor(
      wheelAngle /
      360
    );

  let exactRotorAngle =
    currentTurns *
    360 +
    targetRotorNormal;

  while (
    exactRotorAngle <
    wheelAngle -
    0.001
  ) {
    exactRotorAngle +=
      360;
  }

  wheelAngle =
    exactRotorAngle;

  setRotorAngle(
    wheelAngle
  );


  /* ============================================================
     STAGE 2
     SEPARATOR RATTLE
     ============================================================ */

  const rattleStartAngle =
    ballAngle;

  await animateFor(
    850,

    (progress) => {
      const travelProgress =
        easeOutCubic(
          progress
        );

      const decay =
        Math.pow(
          1 -
          progress,
          1.6
        );

      /*
       * Continue counter-clockwise.
       */

      const travel =
        -120 *
        travelProgress;


      /*
       * Small separator vibration.
       *
       * This modifies the angular position only
       * slightly instead of producing large jumps.
       */

      const rattle =
        Math.sin(
          progress *
          Math.PI *
          8
        ) *
        4 *
        decay;


      /*
       * Small continuous radial descent.
       */

      const diameter =
        268 -
        10 *
        travelProgress;

      setBallAngle(
        rattleStartAngle +
        travel +
        rattle,
        diameter
      );
    }
  );


  /* ============================================================
     STAGE 3
     APPROACH WINNING POCKET
     ============================================================ */

  /*
   * The winning pocket is now physically at
   * global angle 0.
   *
   * Keep the ball travelling counter-clockwise
   * until it reaches the next equivalent
   * 0-degree position.
   */

  const approachStart =
    ballAngle;

  const approachNormal =
    shortestPositiveAngle(
      approachStart
    );

  let approachTravel =
    -approachNormal;

  /*
   * If we're already very close to zero,
   * don't suddenly stop.
   *
   * Continue around another turn.
   */

  if (
    Math.abs(
      approachTravel
    ) < 45
  ) {
    approachTravel -=
      360;
  }


  await animateFor(
    1050,

    (progress) => {
      const eased =
        easeOutQuint(
          progress
        );

      const decay =
        1 -
        eased;

      /*
       * Very small final pocket-divider vibration.
       */

      const vibration =
        Math.sin(
          progress *
          Math.PI *
          6
        ) *
        1.8 *
        decay;

      const diameter =
        258 -
        8 *
        eased;

      setBallAngle(
        approachStart +
        approachTravel *
        eased +
        vibration,
        diameter
      );
    }
  );


  /* ============================================================
     FINAL POSITION
     ============================================================ */

  /*
   * At this point:
   *
   * rotor winning pocket = angle 0
   * ball                   = angle 0
   *
   * So the displayed result and physical wheel
   * necessarily agree.
   */

  setRotorAngle(
    wheelAngle
  );

  setBallAngle(
    0,
    250
  );

  highlightWheelPocket(
    pocket
  );
}

/* ================================================================
   WHEEL WINNER
   ================================================================ */

function clearWheelWinner() {
  document
    .querySelectorAll(
      ".winning-pocket"
    )
    .forEach(
      (element) =>
        element.classList.remove(
          "winning-pocket"
        )
    );
}

function highlightWheelPocket(
  pocket
) {
  clearWheelWinner();

  const target =
    normalisePocket(
      pocket
    );

  const element =
    document.querySelector(
      `[data-wheel-pocket="${target}"]`
    );

  if (!element) {
    console.error(
      "Winning roulette pocket not found:",
      target
    );

    return;
  }

  element.classList.add(
    "winning-pocket"
  );

  console.log(
    "[ROULETTE]",
    "Backend winner:",
    target,
    "| Wheel index:",
    pocketIndex(target),
    "| Final rotor angle:",
    shortestPositiveAngle(
      wheelAngle
    )
  );
}


/* ================================================================
   TABLE WINNER
   ================================================================ */

function clearWinningCell() {
  document
    .querySelectorAll(
      ".winner"
    )
    .forEach(
      (element) =>
        element.classList.remove(
          "winner"
        )
    );
}

function showWinningCell(pocket) {
  clearWinningCell();

  const target =
    normalisePocket(
      pocket
    );

  const element =
    document.querySelector(
      `[data-pocket="${target}"]`
    );

  if (element) {
    element.classList.add(
      "winner"
    );
  }
}


/* ================================================================
   RESULT DISPLAY
   ================================================================ */

function showResult(pocket) {
  const colour =
    pocketColour(
      pocket
    );

  const result =
    $("resultPocket");

  if (result) {
    result.classList.remove(
      "red",
      "black",
      "green"
    );

    result.classList.add(
      colour
    );
  }

  const resultNumber =
    $("resultNumber");

  if (resultNumber) {
    resultNumber.textContent =
      normalisePocket(
        pocket
      );
  }

  const lastResult =
    $("lastResult");

  if (lastResult) {
    lastResult.textContent =
      pocketLabel(
        pocket
      );
  }

  showWinningCell(
    pocket
  );
}


/* ================================================================
   HISTORY
   ================================================================ */

function addHistory(data) {
  history.unshift({
    number:
      data.outcome.number,

    net:
      Number(
        data.net
      ),
  });

  history =
    history.slice(
      0,
      15
    );

  saveHistory();

  renderHistory();
}

function renderHistory() {
  const area =
    $("history");

  if (!area) {
    return;
  }

  if (
    !history.length
  ) {
    area.innerHTML =
      "<br>No spins yet";

    return;
  }

  area.innerHTML =
    history
      .map(
        (item) => {
          const colour =
            pocketColour(
              item.number
            );

          const textColour =
            colour === "red"
              ? "#ff8d86"
              : colour === "green"
                ? "#65ef8a"
                : "#eee";

          return `
            <div
              style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:6px;
                padding:7px 0;
                border-bottom:
                  1px solid
                  #ffffff12;
              "
            >

              <span>

                <strong
                  style="
                    color:${textColour};
                  "
                >
                  ${normalisePocket(
                    item.number
                  )}
                </strong>

                ${colour.toUpperCase()}

              </span>


              <span
                style="
                  color:${
                    item.net >= 0
                      ? "#65ef8a"
                      : "#ff8d8d"
                  };
                "
              >

                ${
                  item.net > 0
                    ? "+"
                    : ""
                }${fmt(
                  item.net
                )}

              </span>

            </div>
          `;
        }
      )
      .join("");
}


/* ================================================================
   SPIN
   ================================================================ */

async function spinRoulette() {
  if (
    busy ||
    pendingTotal() <= 0
  ) {
    return;
  }

  const wagered =
    pendingTotal();

  const bets =
    Object.entries(
      pendingBets
    )
      .map(
        (
          [
            wager_type,
            amount,
          ]
        ) => ({
          wager_type,
          amount,
        })
      );


  busy = true;

  clearWinningCell();
  clearWheelWinner();

  $("phaseLabel")
    .textContent =
      "SPINNING";

  refresh();


  /*
   * Start animation immediately.
   *
   * Flask request runs in parallel.
   */

  const spinPromise =
    runFreeSpin();


  try {
    const responsePromise =
      fetch(
        "/api/solo/roulette/spin",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              game:
                GAME,

              bets,
            }),
        }
      );


    const [
      response,
    ] =
      await Promise.all([
        responsePromise,
        spinPromise,
      ]);


    const data =
      await response.json();


    if (
      !response.ok
    ) {
      throw new Error(
        data.error ||
        "Roulette spin failed"
      );
    }


    $("phaseLabel")
      .textContent =
        "BALL DROPPING";


    /*
     * Server-selected pocket is authoritative.
     */

    await landOnPocket(
      data.outcome.number
    );


    /*
     * Announce only after physical animation finishes.
     */

    showResult(
      data.outcome.number
    );


    balance +=
      Number(
        data.total_return
      );


    saveBalance();


    $("returnMetric")
      .textContent =
        fmt(
          data.total_return
        );


    $("netMetric")
      .textContent =
        `${
          Number(
            data.net
          ) > 0
            ? "+"
            : ""
        }${fmt(
          data.net
        )}`;


    addHistory(
      data
    );


    pendingBets = {};


  } catch (error) {

    cancelSpinAnimation();


    /*
     * No settlement occurred.
     *
     * Restore wagers that were deducted locally.
     */

    balance +=
      wagered;

    pendingBets = {};

    saveBalance();

    console.error(
      error
    );


  } finally {

    cancelSpinAnimation();

    busy = false;

    $("phaseLabel")
      .textContent =
        "READY";

    refresh();
  }
}


/* ================================================================
   RULES
   ================================================================ */

function renderRules() {
  let rules = [
    "Straight Up pays 35:1.",
    "Split pays 17:1.",
    "Street pays 11:1.",
    "Corner pays 8:1.",
    "Six Line pays 5:1.",
    "Dozens and Columns pay 2:1.",
    "Red/Black, Odd/Even and Low/High pay 1:1.",
    "Place chips directly on number cells, lines and intersections.",
    "Hover a line or intersection to preview all numbers covered by that wager.",
  ];


  if (
    GAME ===
    "roulette_single_zero"
  ) {
    $("rulesTitle")
      .textContent =
        "SINGLE ZERO ROULETTE RULES";

    rules.push(
      "The wheel contains 0 and numbers 1–36."
    );

    rules.push(
      "Zero splits and the 0-1-2-3 four-number wager are placed directly around the zero area."
    );
  }


  else if (
    GAME ===
    "roulette_double_zero"
  ) {
    $("rulesTitle")
      .textContent =
        "DOUBLE ZERO ROULETTE RULES";

    rules.push(
      "The wheel contains 0, 00 and numbers 1–36."
    );

    rules.push(
      "0 and 00 are green pockets."
    );

    rules.push(
      "Zero-area splits, streets and corners are placed directly on the physical zero section."
    );
  }


  else {
    $("rulesTitle")
      .textContent =
        "SANDS ROULETTE RULES";

    rules.push(
      "The wheel contains S, 00, 0 and numbers 1–36."
    );

    rules.push(
      "Green covers S, 00 and 0 and pays 11:1."
    );

    rules.push(
      "Top Line covers S, 00, 0, 1, 2 and 3 and pays 5:1."
    );

    rules.push(
      "Sands zero-area splits, streets and corners are placed directly on the S / 00 / 0 section."
    );
  }


  const columns = [
    [],
    [],
    [],
    [],
  ];


  rules.forEach(
    (
      rule,
      index
    ) => {
      columns[
        index % 4
      ].push(
        rule
      );
    }
  );


  $("rulesBox")
    .innerHTML =
      columns
        .map(
          (column) => `
            <div>

              ${
                column
                  .map(
                    (rule) => `
                      <div
                        style="
                          margin-bottom:
                            7px;
                        "
                      >
                        • ${rule}
                      </div>
                    `
                  )
                  .join("")
              }

            </div>
          `
        )
        .join("");
}


/* ================================================================
   RESET
   ================================================================ */

function resetCredits() {
  if (busy) {
    return;
  }

  if (
    !confirm(
      `Reset credits to ${fmt(
        STARTING_CREDITS
      )}?`
    )
  ) {
    return;
  }

  cancelSpinAnimation();

  balance =
    STARTING_CREDITS;

  pendingBets = {};
  history = [];

  wheelAngle = 0;
  ballAngle = 0;

  localStorage.removeItem(
    BALANCE_KEY
  );

  localStorage.removeItem(
    HISTORY_KEY
  );

  saveBalance();
  saveHistory();

  setRotorAngle(0);

  setBallAngle(
    0,
    316
  );

  clearWinningCell();
  clearWheelWinner();

  const lastResult =
    $("lastResult");

  if (lastResult) {
    lastResult.textContent =
      "—";
  }

  const resultNumber =
    $("resultNumber");

  if (resultNumber) {
    resultNumber.textContent =
      "—";
  }

  const resultPocket =
    $("resultPocket");

  if (resultPocket) {
    resultPocket.className =
      "result-pocket green";
  }

  $("returnMetric")
    .textContent =
      "0";

  $("netMetric")
    .textContent =
      "0";

  renderHistory();

  refresh();
}


/* ================================================================
   INITIALISE
   ================================================================ */

function init() {
  installRouletteStyles();

  saveBalance();

  renderWheel();
  renderBoard();
  renderChips();
  renderHistory();
  renderRules();

  setRotorAngle(0);

  setBallAngle(
    0,
    316
  );

  $("clearBtn")
    .onclick =
      clearBets;

  $("spinBtn")
    .onclick =
      spinRoulette;

  $("resetBtn")
    .onclick =
      resetCredits;

  refresh();
}


/* ================================================================
   START
   ================================================================ */

if (
  document.readyState ===
  "loading"
) {
  document.addEventListener(
    "DOMContentLoaded",
    init
  );
}

else {
  init();
}