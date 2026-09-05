/**
 * solo.js — single-player game screen logic.
 *
 * Games: baccarat, sicbo, roulette, craps, great_fortune_dice
 *
 * Craps is the only stateful game: the Point is tracked in-page across
 * rolls so that Pass Line / Don't Pass resolve correctly over multiple
 * throws. The board re-renders after each roll to show the current Point.
 * All other games are fully stateless (one spin → one outcome → settled).
 */

import api from "./api.js";
import {
  renderChipBar, chipStackHTML, buildMiniCard, miniDie,
  buildBaccaratBoard, buildSicboBoard, buildRouletteBoard,
  buildCrapsBoard, buildGFDBoard,
} from "./boards.js";
import {
  renderAnimation, renderSicbo, renderCraps, renderGFD,
} from "./animations.js";

const GAME             = window.SOLO_GAME;
const MAX_BET          = window.SOLO_MAX_BET;
const STARTING_CREDITS = window.SOLO_STARTING_CREDITS;
const BALANCE_KEY      = `etg_solo_balance_${GAME}`;
const HISTORY_KEY      = `etg_solo_history_${GAME}`;
const CRAPS_POINT_KEY  = `etg_solo_craps_point_${GAME}`;

const $ = (id) => document.getElementById(id);
const fmtCredits = (n) => Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });

// ─────────────────────────────────────── state ────────────────────────────────
let balance      = parseFloat(localStorage.getItem(BALANCE_KEY) ?? String(STARTING_CREDITS));
let selectedChip = 100;
let pendingBets  = {};    // { wager_type: amount }
let spinning     = false;
let history      = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");

// Craps-specific: persist the Point across rolls
let crapsPoint = (() => {
  const v = localStorage.getItem(CRAPS_POINT_KEY);
  return v === "null" || v === null ? null : parseInt(v, 10);
})();

function saveCrapsPoint(p) {
  crapsPoint = p;
  localStorage.setItem(CRAPS_POINT_KEY, JSON.stringify(p));
}

function saveBalance() { localStorage.setItem(BALANCE_KEY, String(balance)); }
function saveHistory() { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-20))); }

function pendingTotal() {
  return Object.values(pendingBets).reduce((s, v) => s + v, 0);
}

// ─────────────────────────────────────── rendering ───────────────────────────
function renderBalance() {
  const el = $("balanceDisplay");
  if (el) el.textContent = fmtCredits(balance);
}

function renderChips() {
  renderChipBar($("chipBar"), selectedChip, (v) => { selectedChip = v; renderChips(); });
}

function renderBoard() {
  const area = $("bettingArea");
  if (!area) return;
  area.className = "";

  if (GAME === "baccarat") {
    area.classList.add("board-baccarat");
    area.innerHTML = buildBaccaratBoard();
  } else if (GAME === "sicbo") {
    area.classList.add("board-sicbo");
    area.innerHTML = buildSicboBoard();
  } else if (GAME === "roulette") {
    area.classList.add("board-roulette");
    area.innerHTML = buildRouletteBoard();
  } else if (GAME === "craps") {
    area.classList.add("board-craps");
    area.innerHTML = buildCrapsBoard(crapsPoint);
  } else if (GAME === "great_fortune_dice") {
    area.classList.add("board-gfd");
    area.innerHTML = buildGFDBoard();
  }

  area.querySelectorAll("[data-wager]").forEach(el => {
    el.addEventListener("click", () => onSpotClick(el));
  });
  refreshStacks();
}

function refreshStacks() {
  document.querySelectorAll("#bettingArea [data-wager]").forEach(el => {
    el.querySelectorAll(".chip-stack").forEach(s => s.remove());
    const total = pendingBets[el.dataset.wager] || 0;
    if (total > 0) el.insertAdjacentHTML("beforeend", chipStackHTML(total));
  });
  const totalEl = $("pendingTotal");
  if (totalEl) totalEl.textContent = fmtCredits(pendingTotal());
  const spinBtn = $("spinBtn");
  if (spinBtn) {
    const label = GAME === "craps" ? "Throw" : "Spin";
    spinBtn.textContent = label;
    spinBtn.disabled = spinning || pendingTotal() <= 0;
  }
}

function renderHistory() {
  const el = $("soloHistory");
  if (!el) return;
  el.innerHTML = history.slice().reverse().map(h => {
    if (GAME === "roulette") {
      return `<span class="hist-badge ${h.color}" title="${h.number}">${h.number}</span>`;
    }
    if (GAME === "baccarat") {
      const cls = h.winner === "player" ? "blue" : h.winner === "banker" ? "red" : "green";
      return `<span class="hist-badge ${cls}">${h.winner[0].toUpperCase()}</span>`;
    }
    if (GAME === "sicbo") {
      return `<span class="hist-badge" title="Total ${h.total}">${h.total}</span>`;
    }
    if (GAME === "craps") {
      const cls = h.event === "natural" || h.event === "point_hit" ? "green"
                : h.event === "craps" || h.event === "seven_out"  ? "red"
                : h.event === "point_set" ? "blue" : "";
      return `<span class="hist-badge ${cls}" title="${h.event}">${h.total}</span>`;
    }
    if (GAME === "great_fortune_dice") {
      return `<span class="hist-badge" title="Total ${h.total}">${h.total}</span>`;
    }
    return "";
  }).join("");
}

function showStatus(type, title, msg = "") {
  const bar = $("statusBar");
  if (!bar) return;
  bar.className = `status ${type}`;
  bar.innerHTML = `<strong>${title}</strong><div>${msg}</div>`;
}

function updateCrapsStatusBar() {
  if (GAME !== "craps") return;
  if (crapsPoint) {
    showStatus("warn", `Point is ${crapsPoint}`, `Roll ${crapsPoint} again to win, or 7 to seven out.`);
  } else {
    showStatus("", "Come-Out Roll", "Roll 7 or 11 to win, 2/3/12 to crap out.");
  }
}

// ─────────────────────────────────────── betting ─────────────────────────────
function onSpotClick(el) {
  if (spinning) return;

  const wager = el.dataset.wager;
  const current = pendingBets[wager] || 0;
  const wouldBeTotal = pendingTotal() - current + (current + selectedChip);

  if (current + selectedChip > MAX_BET) {
    showStatus("warn", "Bet capped", `A single spot can take at most ${fmtCredits(MAX_BET)} credits.`);
    return;
  }
  if (wouldBeTotal > MAX_BET) {
    showStatus("warn", "Spin capped", `Total stake per spin can't exceed ${fmtCredits(MAX_BET)} credits.`);
    return;
  }
  if (wouldBeTotal > balance) {
    showStatus("bad", "Not enough credits", `You have ${fmtCredits(balance)} credits available.`);
    return;
  }

  pendingBets[wager] = current + selectedChip;
  el.classList.add("spot-flash");
  setTimeout(() => el.classList.remove("spot-flash"), 500);
  refreshStacks();

  const niceLabel = wager.replace(/_/g, " ");
  showStatus("good", "Bet placed", `${fmtCredits(selectedChip)} on ${niceLabel}`);
}

function clearBets() {
  if (spinning) return;
  pendingBets = {};
  refreshStacks();
  showStatus("warn", "Bets cleared", "Place a new bet whenever you're ready.");
}

// ─────────────────────────────────────── spin / throw ────────────────────────
async function spin() {
  const total = pendingTotal();
  if (spinning || total <= 0) return;
  if (total > balance) {
    showStatus("bad", "Not enough credits", `You have ${fmtCredits(balance)} credits available.`);
    return;
  }

  spinning = true;
  $("spinBtn").disabled = true;
  $("clearBtn").disabled = true;
  $("phaseLabel").textContent = GAME === "craps" ? "ROLLING…" : "SPINNING…";

  const label = GAME === "craps" ? "Dice in the air…" : "No more bets…";
  showStatus("warn", label, "");

  const resultArea = $("resultArea");
  if (resultArea) { resultArea.style.display = "none"; resultArea.innerHTML = ""; }

  const bets = Object.entries(pendingBets).map(([wager_type, amount]) => ({ wager_type, amount }));

  // For Craps, send the current point so the server can resolve correctly
  const payload = GAME === "craps"
    ? { game: GAME, bets, state: { point: crapsPoint } }
    : { game: GAME, bets };

  let r;
  try {
    r = await api.solo.spin(GAME, bets, GAME === "craps" ? { point: crapsPoint } : undefined);
  } catch (err) {
    showStatus("bad", "Spin failed", err.message || "Something went wrong — your bets were not charged.");
    spinning = false;
    $("clearBtn").disabled = false;
    $("phaseLabel").textContent = "READY";
    renderBoard();
    return;
  }

  // ── Animation ────────────────────────────────────────────────────────────
  const animArea = $("animArea");
  if (animArea) animArea.style.display = "";

  if (GAME === "craps") {
    await renderCraps(animArea, r.outcome);
  } else if (GAME === "great_fortune_dice") {
    await renderGFD(animArea, r.outcome);
  } else {
    const outcomeForAnim = r.lightning ? { ...r.outcome, lightning: r.lightning } : r.outcome;
    await renderAnimation(GAME, outcomeForAnim, animArea);
  }

  // ── Settle locally ────────────────────────────────────────────────────────
  balance = balance - r.total_wager + r.total_return;
  saveBalance();
  renderBalance();

  // Update Craps point
  if (GAME === "craps") {
    saveCrapsPoint(r.outcome.point_out ?? null);
  }

  history.push(r.outcome);
  saveHistory();
  renderHistory();

  renderResult(r);

  pendingBets = {};
  spinning = false;
  $("clearBtn").disabled = false;
  $("phaseLabel").textContent = "READY";
  renderBoard();  // re-render board (Craps: updates point label)

  if (GAME === "craps") updateCrapsStatusBar();
}

function renderResult(r) {
  const area = $("resultArea");
  if (!area) return;
  area.style.display = "";

  const netTotal = r.net;
  let html = `<div class="result-breakdown">`;
  r.results.forEach(res => {
    const netAmt = res.return - res.amount;
    html += `<div class="result-breakdown-row ${res.win ? "win" : ""}">
      <span>${res.wager_type.replace(/_/g, " ")} — ${fmtCredits(res.amount)}</span>
      <span class="amt">${netAmt >= 0 ? "+" : ""}${fmtCredits(netAmt)}</span>
    </div>`;
  });
  html += `</div>`;
  html += `<div class="result-sub" style="margin-top:8px;text-align:center;">
    Net: <b style="color:${netTotal >= 0 ? "#8fffb0" : "#ff9b9b"}">${netTotal >= 0 ? "+" : ""}${fmtCredits(netTotal)}</b>
    &nbsp;·&nbsp; Balance: ${fmtCredits(balance)}
  </div>`;
  area.innerHTML = html;

  showStatus(netTotal >= 0 ? "good" : "bad",
    netTotal >= 0 ? "You won!" : "No luck this time",
    `Net this spin: ${netTotal >= 0 ? "+" : ""}${fmtCredits(netTotal)} credits`);
}

// ─────────────────────────────────────── reset ───────────────────────────────
function resetBalance() {
  if (spinning) return;
  balance = STARTING_CREDITS;
  saveBalance();
  renderBalance();
  pendingBets = {};
  if (GAME === "craps") saveCrapsPoint(null);
  refreshStacks();
  showStatus("good", "Balance reset", `Back to ${fmtCredits(STARTING_CREDITS)} credits.`);
  renderBoard();
}

// ─────────────────────────────────────── api.solo patch ──────────────────────
// Extend the existing api.solo.spin to accept an optional state param.
// We monkey-patch here since api.js may not expose a state param.
const _origSpin = api.solo.spin.bind(api.solo);
api.solo.spin = async (game, bets, state) => {
  const body = { game, bets };
  if (state) body.state = state;
  const r = await fetch("/api/solo/spin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${r.status}`);
  }
  return r.json();
};

// ─────────────────────────────────────── init ────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  renderBalance();
  renderChips();
  renderBoard();
  renderHistory();

  $("spinBtn")?.addEventListener("click", spin);
  $("clearBtn")?.addEventListener("click", clearBets);
  $("resetBtn")?.addEventListener("click", resetBalance);

  $("resultArea").style.display = "none";

  if (GAME === "craps") updateCrapsStatusBar();
});
