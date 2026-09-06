/* ================================================================
   ETG SIM — DICE SOLO

   Stateless / single-roll Dice games:

   - Sic Bo
   - Great Fortune Dice

   Craps is intentionally handled by:
   static/js/craps_solo.js
   ================================================================ */

const GAME =
  window.DICE_GAME;

const MAX_BET =
  Number(
    window.DICE_MAX
  );

const STARTING_CREDITS =
  Number(
    window.DICE_START
  );

const $ = (id) =>
  document.getElementById(id);

const fmt = (value) =>
  Number(value || 0)
    .toLocaleString(
      undefined,
      {
        maximumFractionDigits: 2,
      }
    );


/* ================================================================
   GAME CONFIG
   ================================================================ */

const DICE_COUNT = {

  sicbo: 3,

  great_fortune_dice: 4,

};


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
  `etg_dice_bal_${GAME}`;

const HISTORY_KEY =
  `etg_dice_history_${GAME}`;


/* ================================================================
   STATE
   ================================================================ */

let selectedChip =
  1000;

let pendingBets = {};

let busy = false;

let rollingAnimationTimer =
  null;


let balance =
  Number(
    localStorage.getItem(
      BALANCE_KEY
    ) ??
    STARTING_CREDITS
  );


if (
  !Number.isFinite(
    balance
  )
) {
  balance =
    STARTING_CREDITS;
}


let history = [];

try {

  history =
    JSON.parse(
      localStorage.getItem(
        HISTORY_KEY
      ) || "[]"
    );

} catch {

  history = [];
}


/* ================================================================
   GENERAL HELPERS
   ================================================================ */

function chipLabel(
  value
) {

  return (
    value >= 1000
      ? `${value / 1000}K`
      : String(value)
  );
}


function sleep(ms) {

  return new Promise(
    resolve =>
      setTimeout(
        resolve,
        ms
      )
  );
}


function pendingTotal() {

  return Object
    .values(
      pendingBets
    )
    .reduce(
      (
        total,
        value
      ) =>
        total +
        Number(value),
      0
    );
}


function saveBalance() {

  localStorage.setItem(
    BALANCE_KEY,
    String(balance)
  );


  if (
    $("balanceDisplay")
  ) {

    $("balanceDisplay")
      .textContent =
        fmt(balance);
  }
}


function saveHistory() {

  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(
      history
    )
  );
}


/* ================================================================
   STYLES
   ================================================================ */

function installDiceStyles() {

  if (
    document.getElementById(
      "etgDiceStyles"
    )
  ) {
    return;
  }


  const style =
    document.createElement(
      "style"
    );


  style.id =
    "etgDiceStyles";


  style.textContent = `

    /* ============================================================
       PHYSICAL DICE
       ============================================================ */

    .physical-die {

      --die-size: 62px;

      position: relative;

      width:
        var(--die-size);

      height:
        var(--die-size);

      flex:
        0 0
        var(--die-size);

      border-radius:
        13px;

      background:
        linear-gradient(
          145deg,
          #ffffff 0%,
          #f5f0df 58%,
          #d7d0bc 100%
        );

      border:
        1px solid
        rgba(
          0,
          0,
          0,
          .55
        );

      box-shadow:
        inset
        3px 3px 7px
        rgba(
          255,
          255,
          255,
          .95
        ),

        inset
        -4px -5px 8px
        rgba(
          0,
          0,
          0,
          .18
        ),

        0 8px 12px
        rgba(
          0,
          0,
          0,
          .48
        );

      transform-origin:
        center center;

      user-select:
        none;
    }


    .physical-die.mini {

      --die-size: 28px;

      border-radius:
        6px;

      box-shadow:
        inset
        1px 1px 3px
        rgba(
          255,
          255,
          255,
          .95
        ),

        inset
        -2px -2px 3px
        rgba(
          0,
          0,
          0,
          .18
        ),

        0 2px 4px
        rgba(
          0,
          0,
          0,
          .35
        );
    }


    .physical-die.micro {

      --die-size: 22px;

      border-radius:
        5px;

      box-shadow:
        inset
        1px 1px 2px
        rgba(
          255,
          255,
          255,
          .9
        ),

        inset
        -1px -1px 2px
        rgba(
          0,
          0,
          0,
          .18
        ),

        0 1px 3px
        rgba(
          0,
          0,
          0,
          .35
        );
    }


    .die-pip {

      position: absolute;

      width:
        calc(
          var(--die-size) *
          .145
        );

      height:
        calc(
          var(--die-size) *
          .145
        );

      border-radius:
        50%;

      background:
        radial-gradient(
          circle at 35% 30%,
          #343434 0%,
          #080808 65%,
          #000 100%
        );
    }


    .die-pip.red {

      background:
        radial-gradient(
          circle at 35% 30%,
          #e33c37 0%,
          #a00f0c 65%,
          #650604 100%
        );
    }


    .pip-tl {
      left: 20%;
      top: 20%;
    }

    .pip-tc {
      left: 42.75%;
      top: 20%;
    }

    .pip-tr {
      right: 20%;
      top: 20%;
    }

    .pip-ml {
      left: 20%;
      top: 42.75%;
    }

    .pip-mc {
      left: 42.75%;
      top: 42.75%;
    }

    .pip-mr {
      right: 20%;
      top: 42.75%;
    }

    .pip-bl {
      left: 20%;
      bottom: 20%;
    }

    .pip-bc {
      left: 42.75%;
      bottom: 20%;
    }

    .pip-br {
      right: 20%;
      bottom: 20%;
    }


    .dice-visual-row {

      display: flex;

      align-items:
        center;

      justify-content:
        center;

      gap: 4px;

      min-height:
        30px;
    }


    .dice-visual-row.tight {

      gap: 2px;
    }


    /* ============================================================
       ROLL ANIMATION
       ============================================================ */

    .physical-die.rolling {

      animation:
        etg-dice-tumble
        .34s
        linear
        infinite;
    }


    .physical-die.rolling:nth-child(2) {
      animation-delay:
        -.09s;
    }

    .physical-die.rolling:nth-child(3) {
      animation-delay:
        -.17s;
    }

    .physical-die.rolling:nth-child(4) {
      animation-delay:
        -.25s;
    }


    @keyframes etg-dice-tumble {

      0% {

        transform:
          translate(
            0,
            0
          )
          rotate(0deg)
          scale(1);
      }


      20% {

        transform:
          translate(
            -7px,
            -9px
          )
          rotate(70deg)
          scale(.96);
      }


      40% {

        transform:
          translate(
            6px,
            -3px
          )
          rotate(145deg)
          scale(1.05);
      }


      60% {

        transform:
          translate(
            -3px,
            7px
          )
          rotate(220deg)
          scale(.98);
      }


      80% {

        transform:
          translate(
            7px,
            -5px
          )
          rotate(300deg)
          scale(1.04);
      }


      100% {

        transform:
          translate(
            0,
            0
          )
          rotate(360deg)
          scale(1);
      }
    }


    .dice-result-shaking {

      animation:
        etg-dome-shake
        .16s
        linear
        infinite;
    }


    @keyframes etg-dome-shake {

      0% {
        transform:
          translateX(0);
      }

      25% {
        transform:
          translateX(-3px);
      }

      50% {
        transform:
          translateX(3px);
      }

      75% {
        transform:
          translateX(-2px);
      }

      100% {
        transform:
          translateX(0);
      }
    }


    .physical-die.settling {

      animation:
        etg-dice-settle
        .34s
        ease-out;
    }


    @keyframes etg-dice-settle {

      0% {

        transform:
          translateY(-12px)
          rotate(35deg)
          scale(1.08);
      }


      55% {

        transform:
          translateY(4px)
          rotate(-7deg)
          scale(.97);
      }


      75% {

        transform:
          translateY(-2px)
          rotate(3deg)
          scale(1.02);
      }


      100% {

        transform:
          translateY(0)
          rotate(0deg)
          scale(1);
      }
    }


    /* ============================================================
       SIC BO
       ============================================================ */

    .sic-center-grid {

      display: grid;

      grid-template-columns:
        repeat(
          7,
          minmax(
            88px,
            1fr
          )
        );

      grid-template-rows:
        auto auto;

      gap: 4px;
    }


    .sic-any-triple {

      grid-column:
        4;

      grid-row:
        1 / span 2;

      min-height:
        118px;
    }


    .sic-center-grid
    .sic-double-1 {

      grid-column: 1;
      grid-row: 1;
    }


    .sic-center-grid
    .sic-double-2 {

      grid-column: 2;
      grid-row: 1;
    }


    .sic-center-grid
    .sic-double-3 {

      grid-column: 3;
      grid-row: 1;
    }


    .sic-center-grid
    .sic-double-4 {

      grid-column: 5;
      grid-row: 1;
    }


    .sic-center-grid
    .sic-double-5 {

      grid-column: 6;
      grid-row: 1;
    }


    .sic-center-grid
    .sic-double-6 {

      grid-column: 7;
      grid-row: 1;
    }


    .sic-center-grid
    .sic-triple-1 {

      grid-column: 1;
      grid-row: 2;
    }


    .sic-center-grid
    .sic-triple-2 {

      grid-column: 2;
      grid-row: 2;
    }


    .sic-center-grid
    .sic-triple-3 {

      grid-column: 3;
      grid-row: 2;
    }


    .sic-center-grid
    .sic-triple-4 {

      grid-column: 5;
      grid-row: 2;
    }


    .sic-center-grid
    .sic-triple-5 {

      grid-column: 6;
      grid-row: 2;
    }


    .sic-center-grid
    .sic-triple-6 {

      grid-column: 7;
      grid-row: 2;
    }


    .sic-top-new {

      display: grid;

      grid-template-columns:
        minmax(
          120px,
          1fr
        )

        minmax(
          720px,
          6fr
        )

        minmax(
          120px,
          1fr
        );

      gap: 4px;
    }


    .sic-side-stack {

      display: grid;

      grid-template-rows:
        1fr 1fr;

      gap: 4px;
    }


    .sic-totals-increasing {

      display: grid;

      grid-template-columns:
        repeat(
          14,
          minmax(
            58px,
            1fr
          )
        );

      gap: 3px;

      margin-top:
        4px;
    }


    /* ============================================================
       GREAT FORTUNE DICE
       ============================================================ */

    .gfd-casino-board {

      display: grid;

      gap: 4px;
    }


    .gfd-upper {

      display: grid;

      grid-template-columns:
        1.05fr
        1.05fr
        3fr
        3.25fr
        3fr
        1.05fr
        1.05fr;

      grid-template-rows:
        82px
        118px
        118px;

      gap: 4px;
    }


    .gfd-upper > .bet {

      height: 100%;
    }


    .gfd-all-big-left {

      grid-column: 1;
      grid-row: 1;
    }


    .gfd-all-small-left {

      grid-column: 2;
      grid-row: 1;
    }


    .gfd-quads-left {

      grid-column: 3;
      grid-row: 1;
    }


    .gfd-any-quad {

      grid-column: 4;
      grid-row: 1;
    }


    .gfd-quads-right {

      grid-column: 5;
      grid-row: 1;
    }


    .gfd-all-big-right {

      grid-column: 6;
      grid-row: 1;
    }


    .gfd-all-small-right {

      grid-column: 7;
      grid-row: 1;
    }


    .gfd-big-left {

      grid-column: 1;

      grid-row:
        2 / span 2;
    }


    .gfd-small-left {

      grid-column: 2;

      grid-row:
        2 / span 2;
    }


    .gfd-triples-left {

      grid-column: 3;
      grid-row: 2;
    }


    .gfd-any-triple {

      grid-column: 4;
      grid-row: 2;
    }


    .gfd-triples-right {

      grid-column: 5;
      grid-row: 2;
    }


    .gfd-big-right {

      grid-column: 6;

      grid-row:
        2 / span 2;
    }


    .gfd-small-right {

      grid-column: 7;

      grid-row:
        2 / span 2;
    }


    .gfd-doubles-left {

      grid-column: 3;
      grid-row: 3;
    }


    .gfd-two-pair {

      grid-column: 4;
      grid-row: 3;
    }


    .gfd-doubles-right {

      grid-column: 5;
      grid-row: 3;
    }


    .gfd-mini-three {

      display: grid;

      grid-template-columns:
        repeat(
          3,
          minmax(
            0,
            1fr
          )
        );

      gap: 3px;

      height: 100%;
    }


    .gfd-mini-three .bet {

      min-height: 0;

      height: 100%;

      padding: 3px;
    }


    .gfd-total-band {

      display: grid;

      grid-template-columns:
        9fr
        5.4fr
        9fr;

      gap: 4px;

      margin-top: 4px;
    }


    .gfd-total-side {

      display: grid;

      grid-template-columns:
        repeat(
          9,
          minmax(
            45px,
            1fr
          )
        );

      gap: 3px;
    }


    .gfd-total-side .bet {

      min-height:
        92px;
    }


    .gfd-total-side
    .bet strong {

      font-size:
        21px;
    }


    .gfd-fourteen {

      display: grid;

      grid-template-rows:
        40px
        1fr;

      gap: 3px;
    }


    .gfd-fourteen-title {

      border:
        1px solid
        #a78628;

      border-radius:
        6px;

      display: flex;

      align-items:
        center;

      justify-content:
        center;

      background:
        #06492b;

      color:
        #f5e8b0;

      font-size:
        28px;

      font-weight:
        900;
    }


    .gfd-fourteen
    .gfd-fourteen-title {

      min-height: 0;

      height: 40px;

      padding: 3px;
    }


    .gfd-fourteen-title span {

      font-size:
        11px;

      margin:
        0 18px;

      color:
        #eadc8a;
    }


    .gfd-fourteen-groups {

      display: grid;

      grid-template-columns:
        repeat(
          4,
          1fr
        );

      gap: 3px;
    }


    .gfd-fourteen-groups
    .bet {

      min-height:
        49px;
    }


    .gfd-bottom {

      display: grid;

      grid-template-columns:
        1.45fr
        5.7fr
        3fr
        1.45fr;

      gap: 4px;

      margin-top:
        4px;
    }


    .gfd-straight-box {

      min-height:
        154px;
    }


    .gfd-straight-patterns {

      margin-top:
        7px;

      font-size:
        12px;

      line-height:
        1.6;

      color:
        #eadc8a;
    }


    .gfd-combination-box,
    .gfd-five-box {

      border:
        1px solid
        #9d7e26;

      border-radius:
        6px;

      padding:
        4px;
    }


    .gfd-combination-grid {

      display: grid;

      grid-template-columns:
        repeat(
          5,
          1fr
        );

      grid-template-rows:
        repeat(
          3,
          1fr
        );

      gap: 3px;
    }


    .gfd-combination-grid
    .bet {

      min-height:
        48px;
    }


    .gfd-five-grid {

      display: grid;

      grid-template-columns:
        repeat(
          3,
          1fr
        );

      grid-template-rows:
        repeat(
          2,
          1fr
        );

      gap: 3px;

      height:
        calc(
          100% - 20px
        );
    }


    .gfd-five-grid .bet {

      min-height:
        58px;
    }


    .gfd-large-label {

      font-size:
        23px !important;

      line-height:
        1.05;
    }


    .gfd-chinese {

      display: block;

      font-size:
        30px;

      color:
        #e6bf44;

      margin-bottom:
        3px;
    }

  `;


  document.head.appendChild(
    style
  );
}


/* ================================================================
   DICE HELPERS
   ================================================================ */

const PIP_MAP = {

  1: [
    "mc",
  ],

  2: [
    "tl",
    "br",
  ],

  3: [
    "tl",
    "mc",
    "br",
  ],

  4: [
    "tl",
    "tr",
    "bl",
    "br",
  ],

  5: [
    "tl",
    "tr",
    "mc",
    "bl",
    "br",
  ],

  6: [
    "tl",
    "tr",
    "ml",
    "mr",
    "bl",
    "br",
  ],

};


function physicalDieHTML(
  value,
  size = "main",
  extraClass = ""
) {

  const safeValue =
    Math.min(
      6,
      Math.max(
        1,
        Number(value) || 1
      )
    );


  const sizeClass =
    size === "mini"
      ? "mini"
      : size === "micro"
        ? "micro"
        : "";


  const pips =
    PIP_MAP[
      safeValue
    ]
      .map(
        position => {

          const red =
            (
              safeValue === 1 &&
              position === "mc"
            ) ||
            (
              safeValue === 5 &&
              position === "mc"
            );


          return `
            <span
              class="
                die-pip
                pip-${position}
                ${
                  red
                    ? "red"
                    : ""
                }
              "
            ></span>
          `;
        }
      )
      .join("");


  return `
    <div
      class="
        physical-die
        ${sizeClass}
        ${extraClass}
      "
    >
      ${pips}
    </div>
  `;
}


function diceVisual(
  values,
  size = "mini"
) {

  return `
    <div
      class="
        dice-visual-row
        ${
          values.length >= 3
            ? "tight"
            : ""
        }
      "
    >

      ${
        values
          .map(
            value =>
              physicalDieHTML(
                value,
                size
              )
          )
          .join("")
      }

    </div>
  `;
}


function dicePair(
  first,
  second
) {

  return diceVisual(
    [
      first,
      second,
    ],
    "mini"
  );
}


function diceTriple(
  first,
  second,
  third
) {

  return diceVisual(
    [
      first,
      second,
      third,
    ],
    "micro"
  );
}


function diceQuadStack(
  value
) {

  return `
    <div
      style="
        display:grid;
        grid-template-columns:
          repeat(2,22px);
        grid-template-rows:
          repeat(2,22px);
        gap:3px;
        justify-content:center;
        align-items:center;
      "
    >

      ${physicalDieHTML(
        value,
        "micro"
      )}

      ${physicalDieHTML(
        value,
        "micro"
      )}

      ${physicalDieHTML(
        value,
        "micro"
      )}

      ${physicalDieHTML(
        value,
        "micro"
      )}

    </div>
  `;
}


/* ================================================================
   BET CELL
   ================================================================ */

function betCell(
  wager,
  main,
  sub = "",
  extraClass = ""
) {

  return `
    <div
      class="
        bet
        ${extraClass}
      "
      data-wager="${wager}"
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
   SIC BO
   ================================================================ */

function renderSicBoBoard() {

  const totalOdds = {

    4: 62,

    5: 31,

    6: 18,

    7: 12,

    8: 8,

    9: 7,

    10: 6,

    11: 6,

    12: 7,

    13: 8,

    14: 12,

    15: 18,

    16: 31,

    17: 62,

  };


  const centerCells = [];


  for (
    let number = 1;
    number <= 6;
    number++
  ) {

    centerCells.push(
      betCell(
        `double_${number}`,

        dicePair(
          number,
          number
        ),

        "1 PAYS 11",

        `sic-double-${number}`
      )
    );


    centerCells.push(
      betCell(
        `triple_${number}`,

        diceTriple(
          number,
          number,
          number
        ),

        "1 PAYS 180",

        `sic-triple-${number}`
      )
    );
  }


  centerCells.push(
    betCell(
      "any_triple",

      `
        <strong>
          ANY
          <br>
          TRIPLE
        </strong>
      `,

      "1 PAYS 31",

      "sic-any-triple"
    )
  );


  const totals = [];


  for (
    let number = 4;
    number <= 17;
    number++
  ) {

    totals.push(
      betCell(
        `total_${number}`,

        `
          <strong>
            ${number}
          </strong>
        `,

        `1 PAYS ${
          totalOdds[
            number
          ]
        }`
      )
    );
  }


  const twoDice = [];


  for (
    let first = 1;
    first <= 6;
    first++
  ) {

    for (
      let second =
        first + 1;

      second <= 6;

      second++
    ) {

      twoDice.push(
        betCell(
          `combo_${first}${second}`,

          dicePair(
            first,
            second
          ),

          `${first}-${second} · 1 PAYS 6`
        )
      );
    }
  }


  const threeSingles = [];


  for (
    let first = 1;
    first <= 4;
    first++
  ) {

    for (
      let second =
        first + 1;

      second <= 5;

      second++
    ) {

      for (
        let third =
          second + 1;

        third <= 6;

        third++
      ) {

        threeSingles.push(
          betCell(
            `three_single_${first}${second}${third}`,

            diceTriple(
              first,
              second,
              third
            ),

            `${first}-${second}-${third} · 30:1`
          )
        );
      }
    }
  }


  const doubleSingle = [];


  for (
    let pair = 1;
    pair <= 6;
    pair++
  ) {

    for (
      let single = 1;
      single <= 6;
      single++
    ) {

      if (
        pair === single
      ) {
        continue;
      }


      doubleSingle.push(
        betCell(
          `double_single_${pair}${pair}${single}`,

          diceTriple(
            pair,
            pair,
            single
          ),

          `${pair}-${pair}-${single} · 50:1`
        )
      );
    }
  }


  const fourGroups =
    [
      "1234",
      "2345",
      "2356",
      "3456",
    ]
      .map(
        group => {

          const values =
            group
              .split("")
              .map(Number);


          return betCell(
            `three_from_four_${group}`,

            diceVisual(
              values,
              "micro"
            ),

            `${group
              .split("")
              .join("-")} · 7:1`
          );
        }
      )
      .join("");


  const names = [
    "ONE",
    "TWO",
    "THREE",
    "FOUR",
    "FIVE",
    "SIX",
  ];


  const singles =
    [
      1,
      2,
      3,
      4,
      5,
      6,
    ]
      .map(
        number =>
          betCell(
            `single_${number}`,

            `
              ${diceVisual(
                [number],
                "mini"
              )}

              <strong>
                ${
                  names[
                    number - 1
                  ]
                }
              </strong>
            `,

            "1:1 / 2:1 / 12:1"
          )
      )
      .join("");


  $("bettingArea")
    .innerHTML = `

      <div
        class="
          sic-top-new
        "
      >

        <div
          class="
            sic-side-stack
          "
        >

          ${betCell(
            "even",

            `
              <strong>
                EVEN
              </strong>
            `,

            "1 PAYS 1 · ANY TRIPLE LOSES"
          )}


          ${betCell(
            "small",

            `
              <strong>
                SMALL
              </strong>
            `,

            "4–10 · 1 PAYS 1 · TRIPLE LOSES"
          )}

        </div>


        <div
          class="
            sic-center-grid
          "
        >
          ${centerCells.join("")}
        </div>


        <div
          class="
            sic-side-stack
          "
        >

          ${betCell(
            "odd",

            `
              <strong>
                ODD
              </strong>
            `,

            "1 PAYS 1 · ANY TRIPLE LOSES"
          )}


          ${betCell(
            "big",

            `
              <strong>
                BIG
              </strong>
            `,

            "11–17 · 1 PAYS 1 · TRIPLE LOSES"
          )}

        </div>

      </div>


      <div
        class="
          sic-totals-increasing
        "
      >
        ${totals.join("")}
      </div>


      <div
        class="
          sic-lower
        "
      >

        <div class="group">

          <div
            class="
              group-title
            "
          >
            TWO DICE COMBINATIONS
          </div>

          <div
            class="
              combo-grid
            "
          >
            ${twoDice.join("")}
          </div>

        </div>


        <div class="group">

          <div
            class="
              group-title
            "
          >
            THREE SINGLE DICE COMBINATIONS
          </div>

          <div
            class="
              triple-combo-grid
            "
          >
            ${threeSingles.join("")}
          </div>

        </div>


        <div class="group">

          <div
            class="
              group-title
            "
          >
            DOUBLE + SINGLE DICE COMBINATIONS
          </div>

          <div
            class="
              double-single-grid
            "
          >
            ${doubleSingle.join("")}
          </div>

        </div>


        <div class="group">

          <div
            class="
              group-title
            "
          >
            THREE DICE FROM FOUR NUMBERS
          </div>

          <div
            class="
              fourgroup
            "
          >
            ${fourGroups}
          </div>

        </div>

      </div>


      <div
        class="group"
        style="
          margin-top:4px;
        "
      >

        <div
          class="
            group-title
          "
        >
          SINGLE DIE
        </div>

        <div
          class="
            single-die
          "
        >
          ${singles}
        </div>

      </div>
    `;
}


/* ================================================================
   GREAT FORTUNE DICE
   ================================================================ */

function renderGfdBoard() {

  function quadGroup(
    numbers
  ) {

    return `
      <div
        class="
          gfd-mini-three
        "
      >

        ${
          numbers
            .map(
              number =>
                betCell(
                  `specific_quadruple_${number}`,

                  diceQuadStack(
                    number
                  ),

                  "1 PAYS 1000"
                )
            )
            .join("")
        }

      </div>
    `;
  }


  function tripleGroup(
    numbers
  ) {

    return `
      <div
        class="
          gfd-mini-three
        "
      >

        ${
          numbers
            .map(
              number =>
                betCell(
                  `specific_triple_${number}`,

                  diceTriple(
                    number,
                    number,
                    number
                  ),

                  "1 PAYS 55"
                )
            )
            .join("")
        }

      </div>
    `;
  }


  function doubleGroup(
    numbers
  ) {

    return `
      <div
        class="
          gfd-mini-three
        "
      >

        ${
          numbers
            .map(
              number =>
                betCell(
                  `specific_double_${number}`,

                  dicePair(
                    number,
                    number
                  ),

                  "1 PAYS 6"
                )
            )
            .join("")
        }

      </div>
    `;
  }


  const totalOdds = {

    5: 280,

    6: 120,

    7: 55,

    8: 30,

    9: 20,

    10: 13,

    11: 10,

    12: 8,

    13: 7,

    15: 7,

    16: 8,

    17: 10,

    18: 13,

    19: 20,

    20: 30,

    21: 55,

    22: 120,

    23: 280,

  };


  const highTotals = [];


  for (
    let number = 15;
    number <= 23;
    number++
  ) {

    highTotals.push(
      betCell(
        `total_${number}`,

        `
          <strong>
            ${number}
          </strong>
        `,

        `1 PAYS ${
          totalOdds[
            number
          ]
        }`
      )
    );
  }


  const lowTotals = [];


  for (
    let number = 5;
    number <= 13;
    number++
  ) {

    lowTotals.push(
      betCell(
        `total_${number}`,

        `
          <strong>
            ${number}
          </strong>
        `,

        `1 PAYS ${
          totalOdds[
            number
          ]
        }`
      )
    );
  }


  const fourteenGroups = [

    {
      id: "A",

      lines: [
        "1256",
        "1346",
        "2345",
      ],

      odds: 15,
    },


    {
      id: "B",

      lines: [
        "1355",
        "1445",
        "2246",
      ],

      odds: 30,
    },


    {
      id: "C",

      lines: [
        "2336",
        "1166",
        "2255",
      ],

      odds: 45,
    },


    {
      id: "D",

      lines: [
        "3344",
        "2444",
        "3335",
      ],

      odds: 80,
    },

  ];


  const fourteenHTML =
    fourteenGroups
      .map(
        group =>
          betCell(
            `specific14_${group.id}`,

            `
              <strong>
                ${group.lines.join(
                  "<br>"
                )}
              </strong>
            `,

            `1 PAYS ${group.odds}`
          )
      )
      .join("");


  const combinations = [];


  for (
    let first = 1;
    first <= 6;
    first++
  ) {

    for (
      let second =
        first + 1;

      second <= 6;

      second++
    ) {

      combinations.push(
        betCell(
          `combo_${first}${second}`,

          dicePair(
            first,
            second
          ),

          `${first}-${second} · 1 PAYS 3`
        )
      );
    }
  }


  const fiveGroups = [
    "12345",
    "12346",
    "12356",
    "12456",
    "13456",
    "23456",
  ];


  const fiveGroupHTML =
    fiveGroups
      .map(
        group => {

          const values =
            group
              .split("")
              .map(Number);


          return betCell(
            `four_from_five_${group}`,

            `
              ${diceVisual(
                values,
                "micro"
              )}

              <strong>
                ${group}
              </strong>
            `,

            "1 PAYS 9"
          );
        }
      )
      .join("");


  function straightBox() {

    return betCell(
      "straight",

      `
        <strong
          class="
            gfd-large-label
          "
        >
          STRAIGHT
        </strong>

        <div
          class="
            gfd-straight-patterns
          "
        >
          1-2-3-4
          <br>
          2-3-4-5
          <br>
          3-4-5-6
        </div>
      `,

      "1 PAYS 15",

      "gfd-straight-box"
    );
  }


  $("bettingArea")
    .innerHTML = `

      <div
        class="
          gfd-casino-board
        "
      >

        <div
          class="
            gfd-upper
          "
        >

          ${betCell(
            "all_big",

            `
              <strong>
                ALL BIG
              </strong>
            `,

            "4-5-6 · 1 PAYS 14",

            "gfd-all-big-left"
          )}


          ${betCell(
            "all_small",

            `
              <strong>
                ALL SMALL
              </strong>
            `,

            "1-2-3 · 1 PAYS 14",

            "gfd-all-small-left"
          )}


          <div
            class="
              gfd-quads-left
            "
          >
            ${quadGroup(
              [
                1,
                2,
                3,
              ]
            )}
          </div>


          ${betCell(
            "any_quadruple",

            `
              <strong
                class="
                  gfd-large-label
                "
              >
                ANY QUADRUPLE
              </strong>
            `,

            "1 PAYS 200",

            "gfd-any-quad"
          )}


          <div
            class="
              gfd-quads-right
            "
          >
            ${quadGroup(
              [
                4,
                5,
                6,
              ]
            )}
          </div>


          ${betCell(
            "all_big",

            `
              <strong>
                ALL BIG
              </strong>
            `,

            "4-5-6 · 1 PAYS 14",

            "gfd-all-big-right"
          )}


          ${betCell(
            "all_small",

            `
              <strong>
                ALL SMALL
              </strong>
            `,

            "1-2-3 · 1 PAYS 14",

            "gfd-all-small-right"
          )}


          ${betCell(
            "big",

            `
              <span
                class="
                  gfd-chinese
                "
              >
                大
              </span>

              <strong
                class="
                  gfd-large-label
                "
              >
                BIG
              </strong>
            `,

            "15 TO 24 · 1 PAYS 1",

            "gfd-big-left"
          )}


          ${betCell(
            "small",

            `
              <span
                class="
                  gfd-chinese
                "
              >
                小
              </span>

              <strong
                class="
                  gfd-large-label
                "
              >
                SMALL
              </strong>
            `,

            "4 TO 13 · 1 PAYS 1",

            "gfd-small-left"
          )}


          <div
            class="
              gfd-triples-left
            "
          >
            ${tripleGroup(
              [
                1,
                2,
                3,
              ]
            )}
          </div>


          ${betCell(
            "any_triple",

            `
              <strong
                class="
                  gfd-large-label
                "
              >
                ANY TRIPLE
              </strong>
            `,

            "1 PAYS 8",

            "gfd-any-triple"
          )}


          <div
            class="
              gfd-triples-right
            "
          >
            ${tripleGroup(
              [
                4,
                5,
                6,
              ]
            )}
          </div>


          ${betCell(
            "big",

            `
              <span
                class="
                  gfd-chinese
                "
              >
                大
              </span>

              <strong
                class="
                  gfd-large-label
                "
              >
                BIG
              </strong>
            `,

            "15 TO 24 · 1 PAYS 1",

            "gfd-big-right"
          )}


          ${betCell(
            "small",

            `
              <span
                class="
                  gfd-chinese
                "
              >
                小
              </span>

              <strong
                class="
                  gfd-large-label
                "
              >
                SMALL
              </strong>
            `,

            "4 TO 13 · 1 PAYS 1",

            "gfd-small-right"
          )}


          <div
            class="
              gfd-doubles-left
            "
          >
            ${doubleGroup(
              [
                1,
                2,
                3,
              ]
            )}
          </div>


          ${betCell(
            "two_pair",

            `
              <strong
                class="
                  gfd-large-label
                "
              >
                TWO PAIR
              </strong>
            `,

            "1 PAYS 11",

            "gfd-two-pair"
          )}


          <div
            class="
              gfd-doubles-right
            "
          >
            ${doubleGroup(
              [
                4,
                5,
                6,
              ]
            )}
          </div>

        </div>


        <div
          class="
            gfd-total-band
          "
        >

          <div
            class="
              gfd-total-side
            "
          >
            ${highTotals.join("")}
          </div>

          <div
            class="
              gfd-fourteen
            "
          >

            ${betCell(
              "fourteen",

              `
                <strong>
                  14
                </strong>
              `,

              "1 PAYS 7",

              "gfd-fourteen-title"
            )}


            <div
              class="
                gfd-fourteen-groups
              "
            >
              ${fourteenHTML}
            </div>

          </div>

          <div
            class="
              gfd-total-side
            "
          >
            ${lowTotals.join("")}
          </div>

        </div>


        <div
          class="
            gfd-bottom
          "
        >

          ${straightBox()}


          <div
            class="
              gfd-combination-box
            "
          >

            <div
              class="
                group-title
              "
            >
              TWO DICE COMBINATIONS
              · 1 PAYS 3
            </div>


            <div
              class="
                gfd-combination-grid
              "
            >
              ${combinations.join("")}
            </div>

          </div>


          <div
            class="
              gfd-five-box
            "
          >

            <div
              class="
                group-title
              "
            >
              FOUR DICE FROM
              FIVE NUMBERS
              · 1 PAYS 9
            </div>


            <div
              class="
                gfd-five-grid
              "
            >
              ${fiveGroupHTML}
            </div>

          </div>


          ${straightBox()}

        </div>

      </div>
    `;
}


/* ================================================================
   BOARD
   ================================================================ */

function renderBoard() {

  if (
    GAME === "sicbo"
  ) {

    renderSicBoBoard();

  } else if (
    GAME ===
    "great_fortune_dice"
  ) {

    renderGfdBoard();

  } else {

    console.error(
      `dice_solo.js cannot handle game: ${GAME}`
    );

    return;
  }


  bindWagers();
}


/* ================================================================
   CHIPS
   ================================================================ */

function renderChips() {

  const bar =
    $("chipBar");


  bar.innerHTML = "";


  CHIPS.forEach(
    value => {

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
      element => {

        element.addEventListener(
          "click",
          () =>
            placeBet(
              element.dataset.wager
            )
        );
      }
    );
}


function placeBet(
  wagerType
) {

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


  $("rollBtn")
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
      element => {

        const amount =
          pendingBets[
            element.dataset.wager
          ] || 0;


        let badge =
          element.querySelector(
            ".badge"
          );


        if (!amount) {

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
            "badge";


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
   RESULT DICE
   ================================================================ */

function renderResultDice(
  dice,
  extraClass = ""
) {

  const area =
    $("diceResult");


  area.innerHTML =
    dice
      .map(
        value =>
          physicalDieHTML(
            value,
            "main",
            extraClass
          )
      )
      .join("");
}


function renderFinalRoll(
  dice
) {

  const area =
    $("diceResult");


  area.classList.remove(
    "dice-result-shaking"
  );


  renderResultDice(
    dice,
    "settling"
  );


  $("currentRoll")
    .textContent =
      dice.join("-");
}


/* ================================================================
   ROLL ANIMATION
   ================================================================ */

function startRollingAnimation() {

  const area =
    $("diceResult");


  area.classList.add(
    "dice-result-shaking"
  );


  const count =
    DICE_COUNT[
      GAME
    ];


  const initial =
    Array.from(
      {
        length:
          count,
      },
      () =>
        1 +
        Math.floor(
          Math.random() * 6
        )
    );


  renderResultDice(
    initial,
    "rolling"
  );


  rollingAnimationTimer =
    window.setInterval(
      () => {

        const animationDice =
          Array.from(
            {
              length:
                count,
            },
            () =>
              1 +
              Math.floor(
                Math.random() * 6
              )
          );


        renderResultDice(
          animationDice,
          "rolling"
        );

      },
      115
    );
}


function stopRollingAnimation() {

  if (
    rollingAnimationTimer !==
    null
  ) {

    clearInterval(
      rollingAnimationTimer
    );


    rollingAnimationTimer =
      null;
  }
}


/* ================================================================
   HISTORY
   ================================================================ */

function historyDiceHTML(
  dice
) {

  return `
    <span
      style="
        display:inline-flex;
        gap:3px;
        vertical-align:middle;
      "
    >

      ${
        dice
          .map(
            value =>
              physicalDieHTML(
                value,
                "micro"
              )
          )
          .join("")
      }

    </span>
  `;
}


function addHistory(
  data
) {

  history.unshift({

    dice:
      data.outcome.dice,

    net:
      Number(
        data.net
      ),

  });


  history =
    history.slice(
      0,
      12
    );


  saveHistory();

  renderHistory();
}


function renderHistory() {

  if (
    !history.length
  ) {

    $("history")
      .innerHTML =
        "<br>No rounds yet";

    return;
  }


  $("history")
    .innerHTML =
      history
        .map(
          item => `

            <div
              style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:5px;
                padding:7px 0;
                border-bottom:
                  1px solid
                  #ffffff12;
              "
            >

              ${historyDiceHTML(
                item.dice
              )}


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
          `
        )
        .join("");
}


/* ================================================================
   ROLL
   ================================================================ */

async function rollDice() {

  if (
    busy ||
    pendingTotal() <= 0
  ) {
    return;
  }


  const wagered =
    pendingTotal();


  const bets =
    Object
      .entries(
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


  $("phaseLabel")
    .textContent =
      "ROLLING";


  refresh();


  startRollingAnimation();


  const animationStarted =
    performance.now();


  try {

    const response =
      await fetch(
        "/api/solo/dice/roll",
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

              state: {},

            }),

        }
      );


    const data =
      await response.json();


    if (
      !response.ok
    ) {

      throw new Error(
        data.error ||
        "Roll failed"
      );
    }


    const elapsed =
      performance.now() -
      animationStarted;


    const minimumAnimation =
      1250;


    if (
      elapsed <
      minimumAnimation
    ) {

      await sleep(
        minimumAnimation -
        elapsed
      );
    }


    stopRollingAnimation();


    renderFinalRoll(
      data.outcome.dice
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
          Number(data.net) > 0
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

    stopRollingAnimation();


    $("diceResult")
      .classList
      .remove(
        "dice-result-shaking"
      );


    balance +=
      wagered;


    pendingBets = {};


    saveBalance();


    console.error(
      error
    );


  } finally {

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

  let rules = [];


  if (
    GAME === "sicbo"
  ) {

    $("rulesTitle")
      .textContent =
        "SIC BO RULES";


    rules = [

      "Standard 3 dice game. All payouts are “to 1”.",

      "Small (4–10) and Big (11–17) lose on Any Triple.",

      "Odd and Even lose on Any Triple.",

      "Specific doubles pay 11:1.",

      "Specific triples pay 180:1.",

      "Any Triple pays 31:1.",

      "Three Dice Totals 4–17 also qualify when the outcome is a triple.",

      "Single die: 1:1 / 2:1 / 12:1.",

      "Two dice combinations pay 6:1.",

      "Three single combinations pay 30:1.",

      "Double + Single pays 50:1.",

      "Three Dice From Four Numbers pays 7:1.",

    ];

  } else {

    $("rulesTitle")
      .textContent =
        "GREAT FORTUNE DICE RULES";


    rules = [

      "Four dice are used.",

      "Small totals 4–13; Big totals 15–24.",

      "All Small and All Big pay 14:1.",

      "Any Triple pays 8:1.",

      "Any Quadruple pays 200:1.",

      "Specific Triple pays 55:1.",

      "Specific Quadruple pays 1000:1.",

      "Two Pair pays 11:1.",

      "Straight pays 15:1.",

      "Two-dice combinations pay 3:1.",

      "Four Dice From Five Numbers pays 9:1.",

    ];
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
          column => `

            <div>

              ${
                column
                  .map(
                    rule => `

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


  balance =
    STARTING_CREDITS;


  pendingBets = {};

  history = [];


  localStorage.removeItem(
    BALANCE_KEY
  );


  localStorage.removeItem(
    HISTORY_KEY
  );


  saveBalance();

  saveHistory();


  $("currentRoll")
    .textContent =
      "—";


  $("returnMetric")
    .textContent =
      "0";


  $("netMetric")
    .textContent =
      "0";


  renderResultDice(
    Array.from(
      {
        length:
          DICE_COUNT[
            GAME
          ],
      },
      () => 1
    )
  );


  renderHistory();

  refresh();
}


/* ================================================================
   INITIALISE
   ================================================================ */

function init() {

  if (
    !DICE_COUNT[
      GAME
    ]
  ) {

    console.error(
      `Unsupported Dice game: ${GAME}`
    );

    return;
  }


  installDiceStyles();


  $("diceCount")
    .textContent =
      DICE_COUNT[
        GAME
      ];


  saveBalance();


  renderBoard();

  renderChips();

  renderHistory();

  renderRules();


  $("clearBtn")
    .onclick =
      clearBets;


  $("rollBtn")
    .onclick =
      rollDice;


  $("resetBtn")
    .onclick =
      resetCredits;


  renderResultDice(
    Array.from(
      {
        length:
          DICE_COUNT[
            GAME
          ],
      },
      () => 1
    )
  );


  refresh();
}


if (
  document.readyState ===
  "loading"
) {

  document.addEventListener(
    "DOMContentLoaded",
    init
  );

} else {

  init();
}