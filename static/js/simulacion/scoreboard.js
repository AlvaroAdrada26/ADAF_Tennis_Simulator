// frontend/assets/js/simulacion/scoreboard.js
/* Módulo de actualización del marcador en la simulación de tenis */

import { getState } from "./state.js";  // importante para acceder a matchData del estado global

export function updateScoreboard(pointData) {
  const { matchData } = getState(); // obtienes matchData desde el estado

  const setNum = pointData.set;
  const games = pointData.score_after.set_games || { P1: 0, P2: 0 };
  const serverPts = pointData.score_after.server_points || "0";
  const returnerPts = pointData.score_after.returner_points || "0";
  const serverId = pointData.server_id;
  const winnerId = pointData.winner_id;

  // =========================
  // 1. Actualizar juegos por set (sin spoilers)
  // =========================
  const setEls = [
    ["p1-set1", "p2-set1"],
    ["p1-set2", "p2-set2"],
    ["p1-set3", "p2-set3"],
  ];

  // Limpiar todos los sets
  setEls.forEach(([p1, p2]) => {
    const el1 = document.getElementById(p1);
    const el2 = document.getElementById(p2);
    if (el1 && el2) {
      el1.textContent = "";
      el2.textContent = "";
    }
  });

  let games_actualSet_p1 = pointData.score_after.set_games.P1;
  let games_actualSet_p2 = pointData.score_after.set_games.P2;

  if (pointData.game_end) {
    if (winnerId === "P1") games_actualSet_p1 += 1;
    else if (winnerId === "P2") games_actualSet_p2 += 1;
  }

  // =========================
  // 2. Mostrar el set actual y los anteriores
  // =========================
  if (setNum === 1) {
    document.getElementById("p1-set1").textContent = games.P1;
    document.getElementById("p2-set1").textContent = games.P2;
  } else if (setNum === 2) {
    document.getElementById("p1-set1").textContent = matchData.set_scores[0]?.[0] || 0;
    document.getElementById("p2-set1").textContent = matchData.set_scores[0]?.[1] || 0;
    document.getElementById("p1-set2").textContent = games.P1;
    document.getElementById("p2-set2").textContent = games.P2;
  } else if (setNum === 3) {
    document.getElementById("p1-set1").textContent = matchData.set_scores[0]?.[0] || 0;
    document.getElementById("p2-set1").textContent = matchData.set_scores[0]?.[1] || 0;
    document.getElementById("p1-set2").textContent = matchData.set_scores[1]?.[0] || 0;
    document.getElementById("p2-set2").textContent = matchData.set_scores[1]?.[1] || 0;
    document.getElementById("p1-set3").textContent = games.P1;
    document.getElementById("p2-set3").textContent = games.P2;
  }

  // =========================
  // 3. Actualizar puntos del juego actual
  // =========================
  if (serverId === "P1") {
    document.getElementById("p1-points").textContent = serverPts;
    document.getElementById("p2-points").textContent = returnerPts;
  } else {
    document.getElementById("p1-points").textContent = returnerPts;
    document.getElementById("p2-points").textContent = serverPts;
  }

  // =========================
  // 4. Mostrar quién saca
  // =========================
  const serveP1 = document.getElementById("serve-p1");
  const serveP2 = document.getElementById("serve-p2");
  if (serverId === "P1") {
    serveP1.classList.remove("off");
    serveP2.classList.add("off");
  } else {
    serveP2.classList.remove("off");
    serveP1.classList.add("off");
  }

  // =========================
  // 5. Si termina el juego, resetear puntos y corregir juegos
  // =========================
  if (pointData.game_end) {
    // Reset puntos
    document.getElementById("p1-points").textContent = "0";
    document.getElementById("p2-points").textContent = "0";

    // Corregir marcador tras breve delay
    setTimeout(() => {
      if (winnerId === "P1") {
        const el = document.getElementById(`p1-set${setNum}`);
        el.textContent = parseInt(el.textContent || "0") + 1;
      } else if (winnerId === "P2") {
        const el = document.getElementById(`p2-set${setNum}`);
        el.textContent = parseInt(el.textContent || "0") + 1;
      }

      console.log(`🎾 Fin del juego. Gana ${pointData.winner_name}`);
    }, 50);

    // Cambiar servidor
    const nextServer = serverId === "P1" ? "P2" : "P1";
    if (nextServer === "P1") {
      serveP1.classList.remove("off");
      serveP2.classList.add("off");
    } else {
      serveP2.classList.remove("off");
      serveP1.classList.add("off");
    }
  }
}


export function showFinalScore() {
  const { matchData } = getState(); // ✅ también aquí
  const finalSets = matchData.set_scores;
  const winnerName = matchData.winner_name;

  // Poner juegos finales de cada set
  for (let i = 0; i < 3; i++) {
    const p1El = document.getElementById(`p1-set${i + 1}`);
    const p2El = document.getElementById(`p2-set${i + 1}`);
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
  document.getElementById("serve-p2").classList.add("off");

  // Mensaje final
  console.log(`🏆 Partido finalizado: gana ${winnerName}`);

  const panel = document.getElementById("scoreboard-panel");
  const msg = document.createElement("div");
  msg.id = "winner-msg";
  msg.className = "text-3xl text-yellow-400 font-bold mt-4 animate-pulse";
  msg.textContent = `🏆 Partido finalizado — Ganador: ${winnerName}`;
  panel.appendChild(msg);
}

/**
 * Reinicia el marcador visual a su estado inicial (todo a 0 / vacío).
 */
export function resetScoreboard() {
  // Sets
  for (let s = 1; s <= 3; s++) {
    const p1 = document.getElementById(`p1-set${s}`);
    const p2 = document.getElementById(`p2-set${s}`);
    if (p1) p1.textContent = s === 1 ? "0" : "";
    if (p2) p2.textContent = s === 1 ? "0" : "";
  }
  // Puntos
  document.getElementById("p1-points").textContent = "0";
  document.getElementById("p2-points").textContent = "0";
  // Saque: P1 saca por defecto
  document.getElementById("serve-p1")?.classList.remove("off");
  document.getElementById("serve-p2")?.classList.add("off");
  // Quitar mensaje de ganador si existe
  const msg = document.getElementById("winner-msg");
  if (msg) msg.remove();
}
