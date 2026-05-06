// frontend/assets/js/simulacion/scoreboard.js
/* Módulo de actualización del marcador en la simulación de tenis */

import { getState } from "./state.js";  // importante para acceder a matchData del estado global

/** Número máximo de sets según la configuración del partido */
function _getNumSets() {
  try {
    var cfg = JSON.parse(sessionStorage.getItem('match_config') || '{}');
    return parseInt(cfg.best_of, 10) || 3;
  } catch (e) { return 3; }
}

export function updateScoreboard(pointData) {
  const { matchData } = getState();
  const numSets = _getNumSets();

  const setNum = pointData.set;
  const games = pointData.score_after?.set_games || { P1: 0, P2: 0 };
  const serverId = pointData.server_id;
  const isTiebreak = pointData.is_tiebreak || false;

  // === 1. Juegos por set: anteriores, actual, futuros ===
  for (let s = 1; s <= numSets; s++) {
    const el1 = document.getElementById(`p1-set${s}`);
    const el2 = document.getElementById(`p2-set${s}`);
    if (!el1 || !el2) continue;

    // Remove previous active-set highlights
    el1.classList.remove("set-in-game");
    el2.classList.remove("set-in-game");

    if (s < setNum) {
      const sc = matchData?.set_scores?.[s - 1];
      el1.textContent = sc ? sc[0] : "";
      el2.textContent = sc ? sc[1] : "";
    } else if (s === setNum) {
      el1.textContent = games.P1;
      el2.textContent = games.P2;
      // Highlight active set column
      el1.classList.add("set-in-game");
      el2.classList.add("set-in-game");
    } else {
      el1.textContent = "";
      el2.textContent = "";
    }
  }

  // === 2. Puntos (juego normal o tie-break) ===
  const ptsP1 = document.getElementById("p1-points");
  const ptsP2 = document.getElementById("p2-points");

  if (isTiebreak) {
    const tb = pointData.score_after?.tiebreak_score || { P1: 0, P2: 0 };
    ptsP1.textContent = tb.P1;
    ptsP2.textContent = tb.P2;
  } else {
    const serverPts = pointData.score_after?.server_points || "0";
    const returnerPts = pointData.score_after?.returner_points || "0";
    if (serverId === "P1") {
      ptsP1.textContent = serverPts;
      ptsP2.textContent = returnerPts;
    } else {
      ptsP1.textContent = returnerPts;
      ptsP2.textContent = serverPts;
    }
  }

  // === 3. Indicador de saque (con animate-pulse) ===
  const serveP1 = document.getElementById("serve-p1");
  const serveP2 = document.getElementById("serve-p2");
  if (serverId === "P1") {
    serveP1.classList.remove("off");
    serveP1.classList.add("animate-pulse");
    serveP2.classList.add("off");
    serveP2.classList.remove("animate-pulse");
  } else {
    serveP2.classList.remove("off");
    serveP2.classList.add("animate-pulse");
    serveP1.classList.add("off");
    serveP1.classList.remove("animate-pulse");
  }

  // === 4. Fin de juego: resetear puntos ===
  if (pointData.game_end && !isTiebreak) {
    ptsP1.textContent = "0";
    ptsP2.textContent = "0";
  }
}

/** Resalta el nombre del jugador que va ganando el partido */
export function updateLeadingPlayer(pointData) {
  const { matchData } = getState();
  const p1Name = document.getElementById("player1-name");
  const p2Name = document.getElementById("player2-name");
  if (!p1Name || !p2Name) return;

  let p1Sets = 0, p2Sets = 0;
  for (let i = 0; i < (pointData.set - 1); i++) {
    const sc = matchData?.set_scores?.[i];
    if (sc) { if (sc[0] > sc[1]) p1Sets++; else if (sc[1] > sc[0]) p2Sets++; }
  }
  const games = pointData.score_after?.set_games || { P1: 0, P2: 0 };

  let leader = null;
  if (p1Sets > p2Sets) leader = "P1";
  else if (p2Sets > p1Sets) leader = "P2";
  else if (games.P1 > games.P2) leader = "P1";
  else if (games.P2 > games.P1) leader = "P2";

  p1Name.classList.remove("player-leading", "player-trailing");
  p2Name.classList.remove("player-leading", "player-trailing");
  if (leader === "P1") {
    p1Name.classList.add("player-leading");
    p2Name.classList.add("player-trailing");
  } else if (leader === "P2") {
    p2Name.classList.add("player-leading");
    p1Name.classList.add("player-trailing");
  }
}


export function showFinalScore() {
  const { matchData } = getState(); // ✅ también aquí
  const finalSets = matchData.set_scores;
  const winnerName = matchData.winner_name;

  // Poner juegos finales de cada set
  const numSets = _getNumSets();
  for (let i = 0; i < numSets; i++) {
    const p1El = document.getElementById(`p1-set${i + 1}`);
    const p2El = document.getElementById(`p2-set${i + 1}`);
    if (!p1El || !p2El) continue;
    if (finalSets[i]) {
      p1El.textContent = finalSets[i][0];
      p2El.textContent = finalSets[i][1];
    } else {
      p1El.textContent = "";
      p2El.textContent = "";
    }
  }

  // Reset puntos y saque
  document.getElementById("p1-points").textContent = "0";
  document.getElementById("p2-points").textContent = "0";
  document.getElementById("serve-p1").classList.add("off");
  document.getElementById("serve-p1").classList.remove("animate-pulse");
  document.getElementById("serve-p2").classList.add("off");
  document.getElementById("serve-p2").classList.remove("animate-pulse");

  // Mensaje final
  console.log(`🏆 Partido finalizado: gana ${winnerName}`);
  // Animate winner's name in scoreboard
  const winnerId = matchData.winner_id || matchData.winner;
  const winnerEl = winnerId === "P1"
    ? document.getElementById("player1-name")
    : document.getElementById("player2-name");
  if (winnerEl) winnerEl.classList.add("winner-glow");
  // Remove any existing winner message to avoid duplicates
  const existing = document.getElementById("winner-msg");
  if (existing) existing.remove();

  const panel = document.getElementById("scoreboard-panel");
  const msg = document.createElement("div");
  msg.id = "winner-msg";
  msg.className = "text-3xl text-yellow-400 font-bold mt-4 animate-pulse";
  msg.textContent = `Partido finalizado — Ganador: ${winnerName}`;
  panel.appendChild(msg);
}

/**
 * Reinicia el marcador visual a su estado inicial (todo a 0 / vacío).
 */
export function resetScoreboard() {
  const numSets = _getNumSets();
  for (let s = 1; s <= numSets; s++) {
    const p1 = document.getElementById(`p1-set${s}`);
    const p2 = document.getElementById(`p2-set${s}`);
    if (p1) { p1.textContent = s === 1 ? "0" : ""; p1.classList.remove("set-in-game"); }
    if (p2) { p2.textContent = s === 1 ? "0" : ""; p2.classList.remove("set-in-game"); }
  }
  document.getElementById("p1-points").textContent = "0";
  document.getElementById("p2-points").textContent = "0";
  const sp1 = document.getElementById("serve-p1");
  const sp2 = document.getElementById("serve-p2");
  sp1?.classList.remove("off", "animate-pulse");
  sp2?.classList.add("off");
  sp2?.classList.remove("animate-pulse");
  const msg = document.getElementById("winner-msg");
  if (msg) msg.remove();
  const p1n = document.getElementById("player1-name");
  const p2n = document.getElementById("player2-name");
  p1n?.classList.remove("player-leading", "player-trailing", "winner-glow");
  p2n?.classList.remove("player-leading", "player-trailing", "winner-glow");
}
