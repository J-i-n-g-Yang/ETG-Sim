/**
 * boards.js — shared, game-agnostic betting-board builders.
 *
 * Extracted out of player.js so both the multiplayer table (player.js)
 * and the single-player solo table (solo.js) can render identical
 * felt layouts (baccarat / sic bo / roulette) plus the chip bar and
 * chip-stack/mini-card helpers, without duplicating ~700 lines of
 * markup-building logic in two places.
 *
 * Nothing in this file touches the DOM outside of the containers it is
 * explicitly given, and nothing here knows about rounds, SSE, or the
 * server — it only turns data into HTML strings / DOM nodes.
 */

// ---------------------------------------------------------------- //
// Chip bar                                                           //
// ---------------------------------------------------------------- //
export const CHIPS = [100, 250, 500, 1000, 2500, 5000, 10000, 20000];

// Colour identity per chip denomination
export const CHIP_COLORS = {
  100:   { idle: ["#3a6080","#1e3d55"], bright: "#4a90d9", text: "#aaccee" },
  250:   { idle: ["#3a5a30","#1e3a14"], bright: "#5aaa3a", text: "#88cc88" },
  500:   { idle: ["#6a2a2a","#3a0e0e"], bright: "#d94040", text: "#ee9999" },
  1000:  { idle: ["#404070","#20204a"], bright: "#7070d9", text: "#9999ee" },
  2500:  { idle: ["#604010","#3a2008"], bright: "#c07020", text: "#ddaa77" },
  5000:  { idle: ["#2a5a5a","#0e3a3a"], bright: "#30b0b0", text: "#88dddd" },
  10000: { idle: ["#5a2060","#38103a"], bright: "#aa40c0", text: "#cc88ee" },
  20000: { idle: ["#505020","#303010"], bright: "#c0a800", text: "#e8d060" },
};

export function chipLabel(v) {
  return v >= 1000 ? (v / 1000) + "K" : String(v);
}

/**
 * Render the chip-value picker into `container`.
 *   selectedChip — the currently active denomination
 *   onSelect(v)  — called with the new denomination when the user taps a chip
 * The caller owns `selectedChip` state and re-invokes this after it changes
 * (mirrors how player.js drove its own re-render on selection).
 */
export function renderChipBar(container, selectedChip, onSelect) {
  if (!container) return;
  container.innerHTML = "";
  CHIPS.forEach(v => {
    const isActive = v === selectedChip;
    const col = CHIP_COLORS[v] || CHIP_COLORS[100];
    const c0  = isActive ? col.bright : col.idle[0];
    const c1  = isActive ? col.idle[1] : col.idle[1];
    const sectors = `conic-gradient(${c0} 0deg 30deg, ${c1} 30deg 60deg, ${c0} 60deg 90deg, ${c1} 90deg 120deg, ${c0} 120deg 150deg, ${c1} 150deg 180deg, ${c0} 180deg 210deg, ${c1} 210deg 240deg, ${c0} 240deg 270deg, ${c1} 270deg 300deg, ${c0} 300deg 330deg, ${c1} 330deg 360deg)`;
    const d = document.createElement("div");
    d.className = "chip" + (isActive ? " active" : "");
    d.style.background   = sectors;
    d.style.borderColor  = isActive ? col.bright : col.idle[0];
    d.style.color        = isActive ? "#fff" : col.text;
    d.style.boxShadow    = isActive ? `0 0 16px ${col.bright}88, 0 2px 8px rgba(0,0,0,0.4)` : "0 2px 8px rgba(0,0,0,0.4)";
    d.textContent = chipLabel(v);
    d.onclick = () => onSelect(v);
    container.appendChild(d);
  });
}

export const ROULETTE_RED = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);
export const TOTAL_PAY = { 4:60,17:60, 5:30,16:30, 6:17,15:17, 7:12,14:12, 8:8,13:8, 9:6,12:6, 10:6,11:6 };

// ---------------------------------------------------------------- //
// Mini dice — real pip-faced dice (matches the projector's dice)     //
// instead of tiny unicode glyphs, so results/board icons are        //
// actually easy to read at a glance.                                //
// ---------------------------------------------------------------- //
export const DOT_LAYOUTS = {
  1: [[1,1]],
  2: [[0,0],[2,2]],
  3: [[0,0],[1,1],[2,2]],
  4: [[0,0],[0,2],[2,0],[2,2]],
  5: [[0,0],[0,2],[1,1],[2,0],[2,2]],
  6: [[0,0],[0,2],[1,0],[1,2],[2,0],[2,2]],
};
export function dieFaceHTML(value) {
  const dots = DOT_LAYOUTS[value] || [];
  const cells = Array(9).fill("<div></div>");
  dots.forEach(([r, c]) => { cells[r * 3 + c] = '<div class="pip"></div>'; });
  return cells.join("");
}
export function miniDie(value, sizeClass = "") {
  return `<div class="mini-die ${sizeClass}">${dieFaceHTML(value)}</div>`;
}

// Baccarat felt — matches the reference screenshot layout:
// Top row: Player (score) | Tie 8:1 | Banker (score) with 0.95:1
// Second row: Dragon Tiger strip across full width
// Third row: Sm Dragon | Big Dragon | Sm Tiger | Big Tiger (4 columns)
export function buildBaccaratBoard() {
  return `
    <div class="bacc-board">
      <div class="bacc-felt">

        <!-- Main betting row: PLAYER | TIE | BANKER -->
        <div class="bacc-main-row">
          <div class="bet-spot bacc-spot player" data-wager="player">
            <div class="spot-title">Player</div>
            <div class="spot-odds">Pays 1:1</div>
            <div class="bacc-score-badge player" id="baccScoreP">—</div>
          </div>
          <div class="bet-spot bacc-spot tie" data-wager="tie">
            <div class="spot-title">Tie</div>
            <div class="spot-odds">8:1</div>
          </div>
          <div class="bet-spot bacc-spot banker" data-wager="banker">
            <div class="spot-title">Banker</div>
            <div class="spot-odds">Pays 1:1 (½ on 6)</div>
            <div class="bacc-score-badge banker" id="baccScoreB">—</div>
          </div>
        </div>

        <!-- Dragon Tiger full-width strip -->
        <div class="bet-spot bacc-spot dragon-tiger" data-wager="dragon_tiger">
          <div class="bacc-dt-inner">
            <span class="bacc-dt-label">Dragon Tiger</span>
            <span class="bacc-dt-odds">Player 7 beats Banker 6 — up to 100:1</span>
          </div>
        </div>

        <!-- Side bets: 3-column grid, 2 rows -->
        <div class="bacc-side-grid">
          <div class="bet-spot bacc-spot side" data-wager="small_dragon">
            <span>Small Dragon</span><small>15:1</small>
          </div>
          <div class="bet-spot bacc-spot side" data-wager="big_dragon">
            <span>Big Dragon</span><small>30:1</small>
          </div>
          <div class="bet-spot bacc-spot side" data-wager="tiger_tie">
            <span>Tiger Tie</span><small>35:1</small>
          </div>
          <div class="bet-spot bacc-spot side" data-wager="small_tiger">
            <span>Small Tiger</span><small>22:1</small>
          </div>
          <div class="bet-spot bacc-spot side" data-wager="big_tiger">
            <span>Big Tiger</span><small>50:1</small>
          </div>
          <div class="bet-spot bacc-spot side" data-wager="immortal_dragon">
            <span>Immortal Dragon</span><small>25:1</small>
          </div>
        </div>

      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// SIC BO TABLE — faithful to Appendix A felt layout
//
// Layout (top → bottom):
//   Row 1:  EVEN | Doubles 1-6 | ANY TRIPLE | BIG | ODD
//   Row 2:  SMALL (left) | Specific Triples 1-6 (centre) | BIG repeat (right)
//   Row 3:  Totals 17→4 (single row, 14 cells)
//   Row 4:  Two-dice combos (15 cells, 1 PAYS 6)
//   Row 5:  Single die × 6  (1:1 / 2:1 / 12:1)
// ─────────────────────────────────────────────────────────────────────────────
export function buildSicboBoard() {
  // Updated payout table — audit-corrected
  const TOTAL_PAY_FIXED = {
    4:62,17:62, 5:30,16:30, 6:18,15:18,
    7:12,14:12, 8:8,13:8, 9:6,12:6, 10:6,11:6
  };

  // ── Row 1: EVEN | Doubles | ANY TRIPLE | BIG | ODD ──────────────────────
  const doubles = [1,2,3,4,5,6].map(n =>
    `<div class="bet-spot sb-double" data-wager="double_${n}">
      <div class="sb-dice-row">${miniDie(n,"sm")}${miniDie(n,"sm")}</div>
      <small>1 PAYS 11</small>
    </div>`
  ).join("");

  // ── Row 2: SMALL left | Specific Triples centre | specific-triple right ──
  // Triples are shown with three dice icons, label = the face value
  const triples = [1,2,3,4,5,6].map(n =>
    `<div class="bet-spot sb-triple" data-wager="triple_${n}">
      <div class="sb-dice-row">${miniDie(n,"sm")}${miniDie(n,"sm")}${miniDie(n,"sm")}</div>
      <small>1 PAYS 180</small>
    </div>`
  ).join("");

  // ── Row 3: Totals 17 → 4 ────────────────────────────────────────────────
  const totals = [];
  for (let t = 17; t >= 4; t--) {
    totals.push(
      `<div class="bet-spot sb-total" data-wager="total_${t}">
        <span class="sb-total-num">${t}</span>
        <small>1P ${TOTAL_PAY_FIXED[t]}</small>
      </div>`
    );
  }

  // ── Row 4: Two-dice combos ───────────────────────────────────────────────
  const combos = [];
  for (let a = 1; a <= 6; a++) {
    for (let b = a + 1; b <= 6; b++) {
      combos.push(
        `<div class="bet-spot sb-combo" data-wager="combo_${a}${b}">
          <div class="sb-dice-row">${miniDie(a,"sm")}${miniDie(b,"sm")}</div>
          <small>1P 6</small>
        </div>`
      );
    }
  }

  // ── Row 5: Single die ────────────────────────────────────────────────────
  const singles = [1,2,3,4,5,6].map(n =>
    `<div class="bet-spot sb-single" data-wager="single_${n}">
      <div class="sb-dice-row">${miniDie(n,"sm")}</div>
      <small>1:1 · 2:1 · 12:1</small>
    </div>`
  ).join("");

  // ── LEFT PANEL: Appendix-A side grids ───────────────────────────────────
  //   Top block  (1 PAYS 50): Double + Single combos  — double_single_NNS
  //   Bottom block (1 PAYS 30): Three Single Number combos — three_single_ABC
  // Both use the raw digit-code as the on-felt label, matching the printed
  // felt in Appendix A (e.g. "113", "126").
  const doubleSingleCells = [];
  for (let pair = 1; pair <= 6; pair++) {
    for (let single = 1; single <= 6; single++) {
      if (single === pair) continue;
      doubleSingleCells.push(
        `<div class="bet-spot sb-side-cell" data-wager="double_single_${pair}${pair}${single}">${pair}${pair}${single}</div>`
      );
    }
  }

  const threeSingleCombos = [];
  for (let a = 1; a <= 6; a++) {
    for (let b = a + 1; b <= 6; b++) {
      for (let c = b + 1; c <= 6; c++) {
        threeSingleCombos.push([a, b, c]);
      }
    }
  }
  const threeSingleCells = threeSingleCombos.map(([a, b, c]) =>
    `<div class="bet-spot sb-side-cell" data-wager="three_single_${a}${b}${c}">${a}${b}${c}</div>`
  ).join("");

  const sidePanel = `
    <div class="sb-side">
      <div class="sb-side-block">
        <div class="sb-side-grid sb-side-grid-50">${doubleSingleCells.join("")}</div>
        <div class="sb-side-label">1 PAYS 50</div>
      </div>
      <div class="sb-side-block">
        <div class="sb-side-grid sb-side-grid-30">${threeSingleCells}</div>
        <div class="sb-side-label">1 PAYS 30</div>
      </div>
    </div>`;

  // ── Four-dice "specific combination" spots (1 PAYS 7) ───────────────────
  // Matches Appendix A: four fixed four-number groups, each backed by the
  // existing three_from_four_ABCD wager type (7:1).
  const FOUR_DICE_SPOTS = [
    { label: "6543", key: "three_from_four_3456" },
    { label: "6532", key: "three_from_four_2356" },
    { label: "5432", key: "three_from_four_2345" },
    { label: "4321", key: "three_from_four_1234" },
  ];
  const fourDiceCells = FOUR_DICE_SPOTS.map(({ label, key }) =>
    `<div class="bet-spot sb-fourdice" data-wager="${key}">
      <span class="sb-fourdice-label">${label}</span>
      <small>1 PAYS 7</small>
    </div>`
  ).join("");

  return `
    <div class="sb-board">
      ${sidePanel}
      <div class="sb-felt">

        <!-- ── ROW 1+2 combined: EVEN/SMALL | Doubles/Triples | ANY TRIPLE (spans) | ODD/BIG ── -->
        <div class="sb-rows12">
          <div class="bet-spot sb-even-odd sb-even" data-wager="even">
            <span class="sb-eo-title">EVEN</span>
            <small>1 PAYS 1</small>
            <small class="sb-eo-note">Any Triple Loses</small>
          </div>
          <div class="sb-doubles-strip">${doubles}</div>
          <div class="bet-spot sb-any-triple" data-wager="any_triple">
            <div class="sb-at-title">ANY<br>TRIPLE</div>
            <small>1 PAYS 31</small>
          </div>
          <div class="bet-spot sb-even-odd sb-odd" data-wager="odd">
            <span class="sb-eo-title">ODD</span>
            <small>1 PAYS 1</small>
            <small class="sb-eo-note">Any Triple Loses</small>
          </div>

          <div class="bet-spot sb-bigsmall sb-small" data-wager="small">
            <span class="sb-bs-title">SMALL</span>
            <span class="sb-bs-zh">小</span>
            <small>4–10 · 1P 1</small>
            <small class="sb-eo-note">Triple Loses</small>
          </div>
          <div class="sb-triples-strip">${triples}</div>
          <div class="bet-spot sb-bigsmall sb-big" data-wager="big">
            <span class="sb-bs-title">BIG</span>
            <span class="sb-bs-zh">大</span>
            <small>11–17 · 1P 1</small>
            <small class="sb-eo-note">Triple Loses</small>
          </div>
        </div>

        <!-- ── ROW 3: Totals 17 → 4 ── -->
        <div class="sb-totals-row">${totals.join("")}</div>

        <!-- ── ROW 4: Two-dice combos (1 PAYS 6) ── -->
        <div class="sb-combos-header">
          <span class="sb-pays-badge">1 PAYS 6</span>
        </div>
        <div class="sb-combos-row">${combos.join("")}</div>

        <!-- ── ROW 4b: Four-dice specific combinations (1 PAYS 7) ── -->
        <div class="sb-fourdice-row">${fourDiceCells}</div>

        <!-- ── ROW 5: Single die (1:1 / 2:1 / 12:1) ── -->
        <div class="sb-singles-row">${singles}</div>
        <div class="sb-single-legend">
          <span>1 TO 1 ON ONE DICE</span>
          <span>···</span>
          <span>2 TO 1 ON TWO DICE</span>
          <span>···</span>
          <span>12 TO 1 ON THREE DICE</span>
        </div>

      </div>
    </div>`;
}

// Numeric ascending sort + join, matching the server's wager-key format.
function _wkey(prefix, nums) {
  return `${prefix}_${nums.slice().sort((a, b) => a - b).join("_")}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// TRUE ROULETTE TABLE  — everything inside one unified CSS grid / gold border.
//
// Grid column mapping (26 columns total):
//   col 1   = zero cell
//   col 2   = zero-split lane
//   col 3   = number-col 1  (c=1)
//   col 4   = divider lane  (between c=1 and c=2)
//   col 5   = number-col 2  (c=2)
//   ...
//   col 25  = number-col 12 (c=12)  ← no divider after the last number col
//
// Grid row mapping (9 rows total):
//   row 1  = number top   (3c)       \
//   row 2  = h-split lane             > inner grid
//   row 3  = number mid   (3c-1)     |
//   row 4  = h-split lane             |
//   row 5  = number bot   (3c-2)    /
//   row 6  = street lane
//   row 7  = six-line lane
//   row 8  = dozens  (1st/2nd/3rd 12)
//   row 9  = even-money (1-18 / Even / Red / Black / Odd / 19-36)
//
// Zero spans rows 1-5 (all number rows + the two split lanes between them).
// Dozens and even-money bets span the full number-column range (cols 3-25).
// ─────────────────────────────────────────────────────────────────────────────
export function buildRouletteBoard() {
  // Column index helpers
  const numCol = (c) => 3 + 2 * (c - 1);   // c=1..12  →  3,5,7,...,25
  const divCol = (c) => numCol(c) + 1;      // divider right of column c

  const cells = [];

  // ── helper: push one grid cell ──────────────────────────────────────────
  const cell = (wager, gc, gr, cls, label = "") =>
    cells.push(
      `<div class="roul-cell ${cls}" data-wager="${wager}"` +
      ` style="grid-column:${gc};grid-row:${gr};">${label}</div>`
    );

  // ── Outside cell helper (dozens + even-money) ───────────────────────────
  const outside = (wager, gc, gr, cls, label) =>
    cells.push(
      `<div class="roul-cell roul-outside-cell ${cls}" data-wager="${wager}"` +
      ` style="grid-column:${gc};grid-row:${gr};">${label}</div>`
    );

  // ── ZERO — spans all 5 number + split rows ───────────────────────────────
  cell("straight_0", 1, "1 / 6", "roul-zero-cell", "0");

  // Zero-split lane: three invisible hot-zones, one per number row
  cell(_wkey("split", [0, 3]), 2, 1, "roul-split");
  cell(_wkey("split", [0, 2]), 2, 3, "roul-split");
  cell(_wkey("split", [0, 1]), 2, 5, "roul-split");

  // ── NUMBER COLUMNS ───────────────────────────────────────────────────────
  for (let c = 1; c <= 12; c++) {
    const top = 3 * c,     mid = 3 * c - 1,   bot = 3 * c - 2;
    const col = numCol(c);

    // Straight-up numbers (rows 1, 3, 5)
    cell(`straight_${top}`, col, 1, `roul-num-cell ${ROULETTE_RED.has(top)?"red":"black"}`, top);
    cell(`straight_${mid}`, col, 3, `roul-num-cell ${ROULETTE_RED.has(mid)?"red":"black"}`, mid);
    cell(`straight_${bot}`, col, 5, `roul-num-cell ${ROULETTE_RED.has(bot)?"red":"black"}`, bot);

    // Horizontal splits within this column (rows 2, 4)
    cell(_wkey("split", [top, mid]), col, 2, "roul-split");
    cell(_wkey("split", [mid, bot]), col, 4, "roul-split");

    // Street (row 6) — full column of 3
    cell(_wkey("street", [top, mid, bot]), col, 6, "roul-street");

    // Divider column → splits to next col, corners, six-line
    if (c < 12) {
      const dc   = divCol(c);
      const nTop = 3*(c+1), nMid = 3*(c+1)-1, nBot = 3*(c+1)-2;

      // Vertical splits across the boundary (rows 1, 3, 5)
      cell(_wkey("split",  [top,  nTop]),                   dc, 1, "roul-split");
      cell(_wkey("split",  [mid,  nMid]),                   dc, 3, "roul-split");
      cell(_wkey("split",  [bot,  nBot]),                   dc, 5, "roul-split");

      // Corners (rows 2, 4)
      cell(_wkey("corner", [top, mid, nTop, nMid]),         dc, 2, "roul-corner");
      cell(_wkey("corner", [mid, bot, nMid, nBot]),         dc, 4, "roul-corner");

      // Six-line (row 7) — spans this col AND next col including divider
      cell(`sixline_${bot}_${nTop}`, `${col} / ${numCol(c+1)+1}`, 7, "roul-sixline");
    }
  }

  // ── DOZENS (row 8) — span the full number-column range ──────────────────
  // Cols 3..25 = numCol(1) to numCol(12) inclusive (all 12 cols + 11 dividers)
  const numStart = numCol(1);          // 3
  const numEnd   = numCol(12) + 1;     // 26  (exclusive end for grid-column span)
  const numSpan  = `${numStart} / ${numEnd}`;

  // Dozens divide the number range into three equal spans of 4 columns each
  // (4 number cols + 4 divider cols = 8 grid cols per dozen).
  outside("dozen1", `${numCol(1)} / ${numCol(5)}`,  8, "", "1st 12");
  outside("dozen2", `${numCol(5)} / ${numCol(9)}`,  8, "", "2nd 12");
  outside("dozen3", `${numCol(9)} / ${numEnd}`,     8, "", "3rd 12");

  // ── EVEN-MONEY (row 9) — 6 cells across the full number-column range ────
  // Divide the 22-column span (numEnd-numStart = 22 grid cols) into 6 equal
  // parts of approx 3-4 grid cols each.  We use pre-computed breakpoints so
  // the borders line up cleanly with the dozen borders above them.
  const em = [
    ["low",   "1-18",  ""],
    ["even",  "EVEN",  ""],
    ["red",   "RED",   "red-spot"],
    ["black", "BLACK", "black-spot"],
    ["odd",   "ODD",   ""],
    ["high",  "19-36", ""],
  ];
  // Each even-money cell gets an equal share of the 22 available grid cols.
  // Computed breakpoints (0-indexed within the number range, so add numStart):
  const emWidth = (numEnd - numStart) / 6;  // 22/6 ≈ 3.67 — rounded below
  em.forEach(([wager, label, cls], i) => {
    const gcStart = Math.round(numStart + i * emWidth);
    const gcEnd   = i < 5 ? Math.round(numStart + (i+1) * emWidth) : numEnd;
    outside(wager, `${gcStart} / ${gcEnd}`, 9, cls, label);
  });

  // ── COLUMN BETS (Col1/Col2/Col3) — same grid, right next to the number
  // columns. Sized identically to a single number cell (rows 1, 3, 5), NOT
  // spanning down through the street/six-line/dozens/even-money rows.
  const colBetCol = numCol(12) + 2;   // one divider lane past the last number col
  const colBet = (wager, gr, label) =>
    cells.push(
      `<div class="roul-cell roul-col-cell" data-wager="${wager}"` +
      ` style="grid-column:${colBetCol};grid-row:${gr};">${label}<br><small style="font-size:9px;opacity:0.7">2:1</small></div>`
    );
  colBet("col3", 1, "Col3");   // top row   → numbers 3,6,9…36
  colBet("col2", 3, "Col2");   // mid row   → numbers 2,5,8…35
  colBet("col1", 5, "Col1");   // bottom row→ numbers 1,4,7…34

  return `
    <div class="roul-board">
      <div class="roul-felt">
        <div class="roul-table-grid">${cells.join("")}</div>
      </div>
    </div>`;
}


// ---------------------------------------------------------------- //
// Chip stack overlays — decompose an amount into a visual stack of  //
// chip discs, largest denomination first, capped at 5 visible discs.//
// ---------------------------------------------------------------- //
export function chipStackHTML(totalAmount) {
  if (!totalAmount || totalAmount <= 0) return "";

  const denomOrder = [20000, 10000, 5000, 2500, 1000, 500, 250, 100];
  const discs = [];
  let rem = totalAmount;
  for (const d of denomOrder) {
    while (rem >= d && discs.length < 5) {
      discs.push(d);
      rem -= d;
    }
    if (discs.length >= 5) break;
  }
  if (discs.length === 0 && totalAmount > 0) discs.push(100); // fallback

  const lbl = totalAmount >= 1000
    ? (totalAmount / 1000 % 1 === 0 ? (totalAmount/1000)+"K" : (totalAmount/1000).toFixed(1)+"K")
    : String(totalAmount);

  const chipHTML = discs.map(d => {
    const col = CHIP_COLORS[d] || CHIP_COLORS[100];
    const c0  = col.idle[0], c1 = col.idle[1];
    const sectors = `conic-gradient(${c0} 0deg 30deg,${c1} 30deg 60deg,${c0} 60deg 90deg,${c1} 90deg 120deg,${c0} 120deg 150deg,${c1} 150deg 180deg,${c0} 180deg 210deg,${c1} 210deg 240deg,${c0} 240deg 270deg,${c1} 270deg 300deg,${c0} 300deg 330deg,${c1} 330deg 360deg)`;
    return `<div class="cstack-chip" style="background:${sectors};border-color:${c0};">${chipLabel(d)}</div>`;
  }).join("");

  return `<div class="chip-stack"><span class="cstack-total">${lbl}</span>${chipHTML}</div>`;
}

// ---------------------------------------------------------------- //
// Fallback label for wager types without a dedicated on-table spot  //
// ---------------------------------------------------------------- //
export function formatWagerLabel(w) {
  const KIND_LABELS = { split: "Split", street: "Street", corner: "Corner", sixline: "Six Line", straight: "Straight" };
  const [kind, ...nums] = w.split("_");
  if (KIND_LABELS[kind] && nums.length) return `${KIND_LABELS[kind]} ${nums.join("-")}`;
  return w.replace(/_/g, " ");
}

// ---------------------------------------------------------------- //
// Mini playing cards (baccarat result strip)                        //
// ---------------------------------------------------------------- //
export const SUIT_SYMBOLS = { S: "♠", H: "♥", D: "♦", C: "♣" };
export const RED_SUITS    = new Set(["H", "D"]);

export function buildMiniCard(c) {
  const suitSym = SUIT_SYMBOLS[c.suit] || c.suit;
  const isRed   = RED_SUITS.has(c.suit);
  return `<div class="mini-card ${isRed ? "red" : "black"}">
    <div class="mc-rank">${c.rank}</div>
    <div class="mc-suit">${suitSym}</div>
  </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// CRAPS TABLE — faithful to Appendix B felt layout
//
// Layout (top → bottom, left → right):
//   Section A (top):  Don't Come Bar | Point boxes: 4 5 SIX 8 NINE 10
//   Section B (mid):  PASS LINE (left vertical) | COME + FIELD (centre) | DON'T PASS (right vertical)
//   Section C:        One-roll props strip: Any Craps | 2 | 3 | 11 | 12 | Horn | C&E | Any 7
//   Section D:        FIELD full width
//   Section E (bot):  Hardways (left) | Place bets (right)
// ─────────────────────────────────────────────────────────────────────────────
export function buildCrapsBoard(point = null) {
  const pointLabel = point
    ? `<span style="color:var(--gold-soft);font-weight:700;">Point: ${point}</span>`
    : `<span style="color:var(--muted);">Come-Out Roll</span>`;

  // Point number boxes — top strip
  const pointBoxes = [4, 5, 6, 8, 9, 10].map(n => {
    const label = n === 6 ? "SIX" : n === 9 ? "NINE" : String(n);
    const isPoint = point === n;
    return `<div class="craps-point-box${isPoint ? " craps-point-active" : ""}" data-wager="place_${n}">
      <div class="craps-point-num">${label}</div>
      <div class="craps-point-odds">${n===4||n===10?"9:5":n===5||n===9?"7:5":"7:6"}</div>
    </div>`;
  }).join("");

  // Hardways
  const hardways = [4, 6, 8, 10].map(n =>
    `<div class="bet-spot craps-hard" data-wager="hard_${n}">
      <div class="craps-hard-dice">${miniDie(n/2,"sm")}${miniDie(n/2,"sm")}</div>
      <div class="craps-hard-label">Hard ${n}</div>
      <small>${n===4||n===10?"7:1":"9:1"}</small>
    </div>`
  ).join("");

  return `
    <div class="craps-board">
      <div class="craps-felt">

        <!-- POINT STATUS BAR -->
        <div class="craps-status-bar">${pointLabel}</div>

        <!-- ── SECTION A: Don't Come + Point Boxes ── -->
        <div class="craps-top-strip">
          <div class="bet-spot craps-dont-come" data-wager="dont_come">
            <div class="craps-dc-label">DON'T<br>COME<br>BAR</div>
            <small>1:1</small>
          </div>
          <div class="craps-point-boxes">${pointBoxes}</div>
        </div>

        <!-- ── SECTION B: PASS LINE | COME + FIELD | DON'T PASS ── -->
        <div class="craps-mid-section">
          <div class="bet-spot craps-pass-line" data-wager="pass_line">
            <span class="craps-rotated-label">PASS LINE</span>
            <small>1:1</small>
          </div>
          <div class="craps-come-field">
            <div class="bet-spot craps-come" data-wager="come">
              <span class="craps-come-title">COME</span>
              <small>1:1</small>
            </div>
            <div class="bet-spot craps-field" data-wager="field">
              <div class="craps-field-title">FIELD</div>
              <div class="craps-field-nums">
                <span class="craps-field-dbl">②</span>
                <span> 3 · 4 · 9 · 10 · 11 </span>
                <span class="craps-field-dbl">⑫</span>
              </div>
              <small>PAYS DOUBLE ON 2 &amp; 12</small>
            </div>
          </div>
          <div class="bet-spot craps-dont-pass" data-wager="dont_pass">
            <span class="craps-rotated-label">DON'T PASS BAR</span>
            <small>1:1</small>
          </div>
        </div>

        <!-- ── SECTION C: One-Roll Props strip ── -->
        <div class="craps-props-strip">
          <div class="bet-spot craps-prop craps-any-craps" data-wager="any_craps">
            <small>ANY CRAPS</small><strong>7:1</strong>
          </div>
          <div class="bet-spot craps-prop craps-prop-dark" data-wager="two_crap">
            <div class="sb-dice-row">${miniDie(1,"sm")}${miniDie(1,"sm")}</div>
            <strong>30:1</strong>
          </div>
          <div class="bet-spot craps-prop craps-prop-dark" data-wager="three_crap">
            <div class="sb-dice-row">${miniDie(1,"sm")}${miniDie(2,"sm")}</div>
            <strong>15:1</strong>
          </div>
          <div class="bet-spot craps-prop craps-prop-dark" data-wager="eleven">
            <div class="sb-dice-row">${miniDie(5,"sm")}${miniDie(6,"sm")}</div>
            <strong>15:1</strong>
          </div>
          <div class="bet-spot craps-prop craps-prop-dark" data-wager="twelve_crap">
            <div class="sb-dice-row">${miniDie(6,"sm")}${miniDie(6,"sm")}</div>
            <strong>30:1</strong>
          </div>
          <div class="craps-prop-horn-label">HORN<br>BET</div>
          <div class="bet-spot craps-prop craps-ce" data-wager="craps_eleven">
            <small>C &amp; E</small>
            <strong>C:3:1 / E:7:1</strong>
          </div>
          <div class="bet-spot craps-prop craps-any7" data-wager="any_seven">
            <small>ANY 7</small><strong>4:1</strong>
          </div>
        </div>

        <!-- ── SECTION D: Hardways + Buy/Lay ── -->
        <div class="craps-bot-section">
          <div class="craps-hardways">
            <div class="craps-hw-title">HARDWAYS</div>
            <div class="craps-hw-grid">${hardways}</div>
          </div>
          <div class="craps-place-panel">
            <div class="craps-place-title">PLACE BETS</div>
            <div class="craps-place-grid">
              ${[4,5,6,8,9,10].map(n=>`
                <div class="bet-spot craps-place" data-wager="place_${n}">
                  <span class="craps-place-num">${n===6?"SIX":n===9?"NINE":n}</span>
                  <small>${n===4||n===10?"9:5":n===5||n===9?"7:5":"7:6"}</small>
                </div>`).join("")}
            </div>
          </div>
        </div>

      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// GREAT FORTUNE DICE TABLE — faithful to MBS Appendix A felt layout
//
// Outer columns (mirrored left/right): ALL BIG | ALL SMALL | BIG | SMALL
// Centre panel rows (top → bottom):
//   Row A:  Spec Quad ×6 | ANY TRIPLE | ANY QUAD | TWO PAIR | Spec Quad ×6
//   Row B:  Specific Triples ×6 (1 PAYS 55)
//   Row C:  Specific Doubles ×6 (1 PAYS 6)
//   Row D:  Totals 23→5 with 14 highlighted in centre (1 PAYS 7)
//   Row E:  Four Specific-14 groups
//   Row F:  Two-dice combos ×15 (1 PAYS 3)
//   Row G:  Straights (1234/2345/3456 · 1 PAYS 15)
// ─────────────────────────────────────────────────────────────────────────────
export function buildGFDBoard() {

  const GFD_PAY = {
    5:280,23:280, 6:120,22:120, 7:55,21:55,
    8:30,20:30,   9:20,19:20,  10:13,18:13,
    11:10,17:10, 12:8,16:8,   13:7,15:7, 14:7
  };

  // ── Specific Quads (for top strip) ──────────────────────────────────────
  const specQuads = [1,2,3,4,5,6].map(n =>
    `<div class="bet-spot gfd-spec-quad" data-wager="specific_quadruple_${n}">
      <div class="sb-dice-row">${miniDie(n,"sm")}${miniDie(n,"sm")}${miniDie(n,"sm")}${miniDie(n,"sm")}</div>
      <small>1P 1000</small>
    </div>`
  ).join("");

  // ── Specific Triples ─────────────────────────────────────────────────────
  const specTriples = [1,2,3,4,5,6].map(n =>
    `<div class="bet-spot gfd-spec-triple" data-wager="specific_triple_${n}">
      <div class="sb-dice-row">${miniDie(n,"sm")}${miniDie(n,"sm")}${miniDie(n,"sm")}</div>
      <small>1P 55</small>
    </div>`
  ).join("");

  // ── Specific Doubles ─────────────────────────────────────────────────────
  const specDoubles = [1,2,3,4,5,6].map(n =>
    `<div class="bet-spot gfd-spec-double" data-wager="specific_double_${n}">
      <div class="sb-dice-row">${miniDie(n,"sm")}${miniDie(n,"sm")}</div>
      <small>1P 6</small>
    </div>`
  ).join("");

  // ── Totals (23 down to 5, 14 in the centre highlighted) ─────────────────
  const totals = [];
  for (let t = 23; t >= 5; t--) {
    const cls = t === 14 ? "gfd-total gfd-total-14" : "gfd-total";
    totals.push(
      `<div class="bet-spot ${cls}" data-wager="total_${t}">
        <span class="gfd-total-num">${t}</span>
        <small>1P ${GFD_PAY[t]}</small>
      </div>`
    );
  }

  // ── Specific-14 groups ───────────────────────────────────────────────────
  const s14 = [
    { k:"specific14_A", combos:"1256 · 1346 · 2345", pay:"15:1" },
    { k:"specific14_B", combos:"1355 · 1445 · 2246", pay:"30:1" },
    { k:"specific14_C", combos:"2336 · 1166 · 2255", pay:"45:1" },
    { k:"specific14_D", combos:"3344 · 2444 · 3335", pay:"80:1" },
  ];
  const s14Tiles = s14.map(({k,combos,pay}) =>
    `<div class="bet-spot gfd-s14" data-wager="${k}">
      <div class="gfd-s14-combos">${combos}</div>
      <small>${pay}</small>
    </div>`
  ).join("");

  // ── Two-dice combos ──────────────────────────────────────────────────────
  const combos = [];
  for (let a = 1; a <= 6; a++) {
    for (let b = a+1; b <= 6; b++) {
      combos.push(
        `<div class="bet-spot gfd-combo" data-wager="combo_${a}${b}">
          <div class="sb-dice-row">${miniDie(a,"sm")}${miniDie(b,"sm")}</div>
          <small>1P 3</small>
        </div>`
      );
    }
  }

  // ── Straights ────────────────────────────────────────────────────────────
  const straights = ["1234","2345","3456"].map(s =>
    `<div class="bet-spot gfd-straight" data-wager="straight_${s}">
      <div class="gfd-straight-label">${s.split("").join("-")}</div>
      <small>1P 15</small>
    </div>`
  ).join("");

  // ── Four dice from five possible numbers (1 PAYS 9) ─────────────────────
  const fourFromFive = [
    "12345","12346","12356","12456","13456","23456"
  ].map(s =>
    `<div class="bet-spot gfd-fff" data-wager="four_from_five_${s}">
      <span class="gfd-fff-label">${s}</span>
      <small>1 PAYS 9</small>
    </div>`
  ).join("");

  return `
    <div class="gfd-board">
      <div class="gfd-felt">

        <!-- ── OUTER COLUMNS + CENTRE ── -->
        <div class="gfd-main-grid">

          <!-- LEFT OUTER -->
          <div class="gfd-outer-col">
            <div class="bet-spot gfd-all-big" data-wager="all_big">
              <div class="gfd-outer-title">ALL BIG</div>
              <small>4-5-6</small><small>1 PAYS 14</small>
            </div>
            <div class="bet-spot gfd-all-small" data-wager="all_small">
              <div class="gfd-outer-title">ALL SMALL</div>
              <small>1-2-3</small><small>1 PAYS 14</small>
            </div>
            <div class="bet-spot gfd-big" data-wager="big">
              <div class="gfd-bs-zh">大</div>
              <div class="gfd-outer-title">BIG</div>
              <small>15–24 · 1P 1</small>
            </div>
            <div class="bet-spot gfd-small" data-wager="small">
              <div class="gfd-bs-zh">小</div>
              <div class="gfd-outer-title">SMALL</div>
              <small>4–13 · 1P 1</small>
            </div>
          </div>

          <!-- CENTRE PANEL -->
          <div class="gfd-centre">

            <!-- ROW A: Spec Quads | ANY TRIPLE | ANY QUAD | TWO PAIR -->
            <div class="gfd-row-a">
              <div class="gfd-spec-quads-strip">${specQuads}</div>
              <div class="gfd-row-a-specials">
                <div class="bet-spot gfd-any-triple" data-wager="any_triple">
                  <div class="gfd-special-title">ANY TRIPLE</div>
                  <small>1 PAYS 8</small>
                </div>
                <div class="bet-spot gfd-any-quad" data-wager="any_quadruple">
                  <div class="gfd-special-title">ANY QUADRUPLE</div>
                  <small>1 PAYS 200</small>
                </div>
                <div class="bet-spot gfd-two-pair" data-wager="two_pair">
                  <div class="gfd-special-title">TWO PAIR</div>
                  <small>1 PAYS 11</small>
                </div>
              </div>
            </div>

            <!-- ROW B: Specific Triples -->
            <div class="gfd-specifics-row">${specTriples}</div>

            <!-- ROW C: Specific Doubles -->
            <div class="gfd-specifics-row">${specDoubles}</div>

            <!-- ROW D: Totals -->
            <div class="gfd-totals-row">${totals.join("")}</div>

            <!-- ROW E: Specific 14 groups -->
            <div class="gfd-s14-row">${s14Tiles}</div>

            <!-- ROW F: Two-dice combos (1 PAYS 3) -->
            <div class="gfd-combos-header"><span class="sb-pays-badge">1 PAYS 3</span></div>
            <div class="gfd-combos-row">${combos.join("")}</div>

            <!-- ROW G: Straights -->
            <div class="gfd-straights-row">
              <div class="gfd-straight-label-cell">
                <span class="gfd-straight-title">STRAIGHT</span>
                <small>1 PAYS 15</small>
              </div>
              ${straights}
            </div>

          </div><!-- /centre -->

          <!-- RIGHT OUTER (mirror) -->
          <div class="gfd-outer-col">
            <div class="bet-spot gfd-all-big" data-wager="all_big">
              <div class="gfd-outer-title">ALL BIG</div>
              <small>4-5-6</small><small>1 PAYS 14</small>
            </div>
            <div class="bet-spot gfd-all-small" data-wager="all_small">
              <div class="gfd-outer-title">ALL SMALL</div>
              <small>1-2-3</small><small>1 PAYS 14</small>
            </div>
            <div class="bet-spot gfd-big" data-wager="big">
              <div class="gfd-bs-zh">大</div>
              <div class="gfd-outer-title">BIG</div>
              <small>15–24 · 1P 1</small>
            </div>
            <div class="bet-spot gfd-small" data-wager="small">
              <div class="gfd-bs-zh">小</div>
              <div class="gfd-outer-title">SMALL</div>
              <small>4–13 · 1P 1</small>
            </div>
          </div>

        </div><!-- /gfd-main-grid -->

        <!-- ── ROW H: Four dice from five possible numbers (1 PAYS 9) ── -->
        <div class="gfd-fff-row">${fourFromFive}</div>
      </div>
    </div>`;
}
