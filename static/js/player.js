/**
 * player.js — player game screen logic.
 *
 * Handles:
 *  - Login / join via lobby
 *  - Bet placement
 *  - Countdown display
 *  - Result display after reveal
 *  - Balance updates
 */

import api from "./api.js";
import { StateManager } from "./state.js";
import {
  renderChipBar as _renderChipBar,
  chipStackHTML, formatWagerLabel, buildMiniCard,
  buildBaccaratBoard, buildSicboBoard, buildRouletteBoard,
  miniDie,
} from "./boards.js";

// ---------------------------------------------------------------- //
// Session storage                                                    //
// ---------------------------------------------------------------- //
let userId    = localStorage.getItem("etg_user_id");
let userName  = localStorage.getItem("etg_user_name");
let balance   = parseFloat(localStorage.getItem("etg_balance") || "0");
let currentRoundId = null;
let selectedChip   = 100;
let countdownTimer = null;
let phase = "IDLE";

const $ = (id) => document.getElementById(id);
const fmtCredits = (n) => Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });

// ---------------------------------------------------------------- //
// Chip bar — markup lives in boards.js; this just wires it to the   //
// module-level `selectedChip` this file already tracks.             //
// ---------------------------------------------------------------- //
function renderChipBar() {
  _renderChipBar($("chipBar"), selectedChip, (v) => { selectedChip = v; renderChipBar(); });
}

// ---------------------------------------------------------------- //
// Countdown                                                          //
// ---------------------------------------------------------------- //
function startCountdown(endsAtStr, serverTimeStr) {
  clearInterval(countdownTimer);
  const endsAt   = new Date(endsAtStr).getTime();
  const serverMs = new Date(serverTimeStr).getTime();
  const localMs  = Date.now();
  const offset   = serverMs - localMs;

  function tick() {
    const remaining = Math.max(0, endsAt - (Date.now() + offset));
    const el = $("countdown");
    if (el) el.textContent = Math.ceil(remaining / 1000) + "s";
    if (remaining <= 0) clearInterval(countdownTimer);
  }
  tick();
  countdownTimer = setInterval(tick, 200);
}

// ---------------------------------------------------------------- //
// Render phase UI                                                    //
// ---------------------------------------------------------------- //
function renderState(state) {
  phase = state.phase;
  currentRoundId = state.round_id;

  const gameLabel  = $("gameLabel");
  const roundLabel = $("roundLabel");
  const phaseLabel = $("phaseLabel");

  if (gameLabel)  gameLabel.textContent = state.game ? state.game.toUpperCase() : "—";
  if (roundLabel) roundLabel.textContent = state.round_number
    ? `Round ${state.round_number}/8` : "—";
  if (phaseLabel) phaseLabel.textContent = state.phase;

  const bettingArea = $("bettingArea");
  const resultArea  = $("resultArea");
  const countdownEl = $("countdownWrap");

  if (state.phase === "BETTING_OPEN") {
    // Clear stale bet totals if round has changed
    if (state.round_id !== currentRoundId) myBetTotals = {};
    if (bettingArea) bettingArea.style.display = "";
    if (resultArea)  resultArea.style.display = "none";
    if (countdownEl) countdownEl.style.display = "";
    if (state.betting_ends_at) startCountdown(state.betting_ends_at, state.server_time);
    renderBettingUI(state);
  } else if (state.phase === "BETTING_LOCKED") {
    if (bettingArea) bettingArea.style.display = "none";
    if (countdownEl) countdownEl.style.display = "none";
    clearInterval(countdownTimer);
    showStatus("warn", "Betting closed", "Waiting for result…");
  } else if (state.phase === "SETTLED" || state.phase === "REVEALING") {
    if (bettingArea) bettingArea.style.display = "none";
    if (countdownEl) countdownEl.style.display = "none";
    if (state.outcome) renderResult(state);
  } else if (state.phase === "GAME_OVER") {
    if (bettingArea) bettingArea.style.display = "none";
    if (countdownEl) countdownEl.style.display = "none";
    showStatus("good", "Event over!", "Final leaderboard below. Thanks for playing!");
    loadLeaderboard();
  } else {
    if (bettingArea) bettingArea.style.display = "none";
    if (countdownEl) countdownEl.style.display = "none";
    showStatus("warn", "Waiting", "Next round starting soon…");
  }
}


// ---------------------------------------------------------------- //
// Chip stack overlays — chipStackHTML() itself lives in boards.js;  //
// this just tracks per-wager totals for the current round and       //
// re-draws them onto the board after every successful bet.          //
// ---------------------------------------------------------------- //
// Per-wager totals for the current round, keyed by wager_type.
// Updated after every successful bet placement.
let myBetTotals = {};   // { wager_type: total_amount }

// Re-draw all chip stacks on every visible bet spot after each bet.
function refreshChipStacks() {
  document.querySelectorAll("[data-wager]").forEach(el => {
    // Remove any existing stack
    el.querySelectorAll(".chip-stack").forEach(s => s.remove());

    const wager = el.dataset.wager;
    const total = myBetTotals[wager] || 0;
    if (total > 0) {
      el.insertAdjacentHTML("beforeend", chipStackHTML(total));
    }
  });
}

// Fetch this player's bets for the current round and refresh stacks.
async function syncMyBets() {
  if (!userId || !currentRoundId) return;
  try {
    const r = await fetch(`api/player/${encodeURIComponent(userId)}/bets/${currentRoundId}`);
    const d = await r.json();
    // Aggregate by wager_type (player may have bet the same spot multiple times)
    myBetTotals = {};
    (d.bets || []).forEach(b => {
      myBetTotals[b.wager_type] = (myBetTotals[b.wager_type] || 0) + b.amount;
    });
    refreshChipStacks();
  } catch (_) {}
}

// ==================== MORE / OVERFLOW BETS ====================

// formatWagerLabel() — imported from boards.js. Kept as a fallback only;
// with the full table above, every roulette wager type now has a real
// on-table hot-zone, so this path is effectively unused for roulette.

function renderBettingUI(state) {
  const opts = state.wager_options || [];
  const area = $("bettingArea");
  if (!area) return;

  area.innerHTML = "";
  area.className = "";

  let boardHTML = "";
  if (state.game === "baccarat") {
    area.classList.add("board-baccarat");
    boardHTML = buildBaccaratBoard();
  } else if (state.game === "sicbo") {
    area.classList.add("board-sicbo");
    boardHTML = buildSicboBoard();
  } else if (state.game === "roulette") {
    area.classList.add("board-roulette");
    boardHTML = buildRouletteBoard();
  } else {
    area.classList.add("board-flat");
    opts.forEach(wager => {
      const btn = document.createElement("button");
      btn.className = "wagerBtn";
      btn.textContent = wager.replace(/_/g, " ");
      btn.onclick = () => placeBet(wager);
      area.appendChild(btn);
    });
    return;
  }

  area.innerHTML = boardHTML;

  // Refresh chip stacks from server (covers re-entry after page reload)
  syncMyBets();

  // Wire up every visual spot on the board
  const covered = new Set();
  area.querySelectorAll("[data-wager]").forEach(el => {
    covered.add(el.dataset.wager);
    el.addEventListener("click", () => {
      el.classList.add("spot-flash");
      setTimeout(() => el.classList.remove("spot-flash"), 500);
      placeBet(el.dataset.wager);
    });
  });

  // Any wager type the board doesn't visualise (roulette's inside combo bets:
  // splits / streets / corners / six lines) still needs to be reachable.
  const leftover = opts.filter(w => !covered.has(w));
  if (leftover.length) {
    const wrap = document.createElement("div");
    wrap.className = "more-bets";
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "more-bets-toggle";
    toggle.textContent = `More inside bets (${leftover.length}) ▾`;
    const list = document.createElement("div");
    list.className = "more-bets-list";
    list.style.display = "none";
    leftover.forEach(w => {
      const b = document.createElement("button");
      b.className = "wagerBtn small";
      b.textContent = formatWagerLabel(w);
      b.onclick = () => placeBet(w);
      list.appendChild(b);
    });
    toggle.onclick = () => {
      const open = list.style.display !== "none";
      list.style.display = open ? "none" : "";
      toggle.textContent = `More inside bets (${leftover.length}) ${open ? "▾" : "▴"}`;
    };
    wrap.appendChild(toggle);
    wrap.appendChild(list);
    area.appendChild(wrap);
  }
}

// buildMiniCard() — imported from boards.js.

function renderResult(state) {
  const area = $("resultArea");
  if (!area) return;
  area.style.display = "";

  const o = state.outcome;
  let html = `<div class="result-box">`;
  if (state.game === "baccarat") {
    html += `<div class="result-winner ${o.winner}">${o.winner.toUpperCase()}</div>`;
    html += `<div class="result-sub">Player ${o.player_total} — Banker ${o.banker_total}</div>`;
    // Mini cards with suit symbols
    if (o.player_cards && o.banker_cards) {
      html += `<div class="result-cards">
        <div class="result-hand">
          <div class="result-hand-label player">Player</div>
          <div class="result-hand-cards">${o.player_cards.map(buildMiniCard).join("")}</div>
        </div>
        <div class="result-hand">
          <div class="result-hand-label banker">Banker</div>
          <div class="result-hand-cards">${o.banker_cards.map(buildMiniCard).join("")}</div>
        </div>
      </div>`;
    }
  } else if (state.game === "roulette") {
    const cls = o.color === "red" ? "red" : o.color === "black" ? "black" : "green";
    html += `<div class="result-winner ${cls}">● ${o.number}</div>`;
    html += `<div class="result-sub">${o.color.toUpperCase()}</div>`;
  } else if (state.game === "sicbo") {
    html += `<div class="mini-die-row">${o.dice.map(d => miniDie(d, "lg")).join("")}</div>`;
    html += `<div>Total: <b>${o.total}</b>${o.triple ? " — TRIPLE!" : ""}</div>`;
  }
  html += `</div>`;
  area.innerHTML = html;

  // Refresh balance
  if (userId) {
    api.state().then(s => {
      // balance updated server-side; re-fetch
      fetch(`api/leaderboard?top=100`).then(r => r.json()).then(data => {
        const me = data.players.find(p => p.display_name === userName);
        if (me) updateBalance(me.credits);
      });
    });
  }
}

// ---------------------------------------------------------------- //
// Place bet                                                          //
// ---------------------------------------------------------------- //
async function placeBet(wager_type) {
  if (phase !== "BETTING_OPEN") { showStatus("warn", "Betting closed", ""); return; }
  if (!userId) return;

  const bet_uid = `${userId}-${currentRoundId}-${wager_type}-${Date.now()}`;
  try {
    const r = await api.bet({
      user_id: userId, round_id: currentRoundId,
      game: $("gameLabel")?.textContent.toLowerCase(),
      wager_type, amount: selectedChip, bet_uid,
    });
    updateBalance(r.balance);
    showStatus("good", `Bet placed: ${wager_type}`, `${selectedChip} credits — Balance: ${fmtCredits(r.balance)}`);
    // Update local totals optimistically then confirm from server
    myBetTotals[wager_type] = (myBetTotals[wager_type] || 0) + selectedChip;
    refreshChipStacks();
    syncMyBets(); // confirm from server (catches any server-side rounding)
  } catch (err) {
    showStatus("bad", "Bet rejected", err.message);
  }
}

// ---------------------------------------------------------------- //
// Balance                                                             //
// ---------------------------------------------------------------- //
function updateBalance(v) {
  balance = parseFloat(v);
  localStorage.setItem("etg_balance", balance);
  const el = $("balanceDisplay");
  if (el) el.textContent = fmtCredits(balance);
}

// ---------------------------------------------------------------- //
// Leaderboard                                                        //
// ---------------------------------------------------------------- //
async function loadLeaderboard() {
  const data = await api.leaderboard(15);
  const el = $("leaderboardList");
  if (!el) return;
  el.innerHTML = data.players.map((p, i) =>
    `<div class="lb-row ${p.display_name === userName ? "me" : ""}">
      <span class="lb-rank">${i + 1}</span>
      <span class="lb-name">${p.display_name}</span>
      <span class="lb-credits">${fmtCredits(p.credits)}</span>
    </div>`
  ).join("");
}

// ---------------------------------------------------------------- //
// Status bar                                                          //
// ---------------------------------------------------------------- //
function showStatus(type, title, msg) {
  const el = $("statusBar");
  if (!el) return;
  el.className = `status ${type}`;
  el.innerHTML = `<strong>${title}</strong><div>${msg}</div>`;
}

// ---------------------------------------------------------------- //
// Boot                                                                //
// ---------------------------------------------------------------- //
document.addEventListener("DOMContentLoaded", () => {
  renderChipBar();
  const nameEl = $("playerName");
  if (nameEl && userName) nameEl.textContent = userName;
  updateBalance(balance);

  const sm = new StateManager();
  sm.on("state",        renderState);
  sm.on("phase_change", renderState);
  sm.on("settled",      renderState);
  sm.on("reveal",       (data) => {
    // Merge outcome into current state and render
    api.state().then(renderState);
  });
  sm.on("leaderboard_update", loadLeaderboard);
  sm.on("event_reset", () => {
    // The event was fully reset server-side — everyone's credits went back
    // to the starting amount. Drop the cached balance and pull the real
    // number from the server instead of trusting localStorage, which is
    // what used to leave the header balance out of sync with the (correctly
    // refreshed) leaderboard after a reset.
    if (userId) {
      api.player(userId).then(p => updateBalance(p.credits)).catch(() => {});
    }
    loadLeaderboard();
  });
  sm.start();

  // Initial state fetch
  api.state().then(renderState).catch(() => {});
  loadLeaderboard();
});
