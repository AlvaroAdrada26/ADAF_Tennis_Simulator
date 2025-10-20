let matchData = null;
let timeline = [];
let currentPoint = 0;
let matchLoaded = false;
let matchEnded = false;

document.addEventListener("DOMContentLoaded", () => {
  const nextBtn = document.getElementById("btn-next");
  const previousBtn = document.getElementById("btn-previous");
  const endBtn = document.getElementById("btn-end");

  // 🚀 1. Cargar el partido desde backend solo una vez
  if (!matchLoaded) {
    matchLoaded = true;
    loadMatchData();
  }

  // 🎾 2. Botón siguiente punto
  nextBtn.addEventListener("click", () => {
    if (!timeline.length) return;

    if (currentPoint < timeline.length) {
      updateScoreboard(timeline[currentPoint]);
      currentPoint++;
    } else {
      if (!matchEnded) {
        matchEnded = true;
        showFinalScore();
      }
    }
  });

  // ⏪ 3. Botón punto anterior
  previousBtn.addEventListener("click", () => {
    if (!timeline.length) return;

    if (currentPoint > 0) {
      updateScoreboard(timeline[currentPoint]);
      currentPoint--;
    } else {
      console.log("Inicio del partido");
    }
  });

  endBtn.addEventListener("click", () => {
      currentPoint = timeline.length - 1;
      if (!matchEnded) {
        matchEnded = true;
        showFinalScore();
      }
  });
});


// ========================
// FUNCIONES AUXILIARES
// ========================

// Fetch al backend
function loadMatchData() {
  const inputData = {
    player1: {
      name: "Alvaro",
      Primer_Saque: 82, Segundo_Saque: 80, Fisico: 88, Estamina: 90,
      Consistencia: 85, Clutch: 87, Momentum: 0, Derecha: 90, Reves: 86,
      Resto: 83, Movilidad: 89
    },
    player2: {
      name: "Diego",
      Primer_Saque: 83, Segundo_Saque: 81, Fisico: 86, Estamina: 88,
      Consistencia: 84, Clutch: 85, Momentum: 0, Derecha: 88, Reves: 90,
      Resto: 82, Movilidad: 86
    },
    config: { best_of: 3, tiebreak: true, }
  };

  fetch("http://127.0.0.1:8000/simulate_match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(inputData)
  })
    .then(res => res.json())
    .then(data => {
      matchData = data;
      timeline = data.timeline;
      console.log("Datos recibidos:", data);
      console.log("Total puntos:", timeline.length);

      // Inicializar nombres
      document.getElementById("player1-name").textContent = data.players.P1;
      document.getElementById("player2-name").textContent = data.players.P2;
    })
    .catch(err => console.error("Error al obtener el partido:", err));
}

function updateScoreboard(pointData) {
  const setNum = pointData.set;
  const games = pointData.score_after.set_games || { P1: 0, P2: 0 };
  const serverPts = pointData.score_after.server_points || "0";
  const returnerPts = pointData.score_after.returner_points || "0";
  const serverId = pointData.server_id;
  const winnerId = pointData.winner_id;

  // =========================
  // 🟡 1. Actualizar juegos por set (sin spoilers)
  // =========================
  const setEls = [
    ["p1-set1", "p2-set1"],
    ["p1-set2", "p2-set2"],
    ["p1-set3", "p2-set3"],
  ];

  // Limpiar todos los sets a vacío
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
    if (winnerId === "P1") {
        games_actualSet_p1 += 1;
      } else if (winnerId === "P2") {
        games_actualSet_p2 += 1;
      }
  }

  // Mostrar el set actual y los anteriores
  if (setNum === 1) {
    // Solo el primer set con progreso actual
    document.getElementById("p1-set1").textContent = games.P1;
    document.getElementById("p2-set1").textContent = games.P2;
  } else if (setNum === 2) {
    // Mostrar resultado final del set 1
    document.getElementById("p1-set1").textContent = matchData.set_scores[0]?.[0] || 0;
    document.getElementById("p2-set1").textContent = matchData.set_scores[0]?.[1] || 0;
    // Mostrar progreso del set actual
    document.getElementById("p1-set2").textContent = games.P1;
    document.getElementById("p2-set2").textContent = games.P2;
  } else if (setNum === 3) {
    // Mostrar resultado final de sets previos
    document.getElementById("p1-set1").textContent = matchData.set_scores[0]?.[0] || 0;
    document.getElementById("p2-set1").textContent = matchData.set_scores[0]?.[1] || 0;
    document.getElementById("p1-set2").textContent = matchData.set_scores[1]?.[0] || 0;
    document.getElementById("p2-set2").textContent = matchData.set_scores[1]?.[1] || 0;
    // Mostrar progreso del set actual
    document.getElementById("p1-set3").textContent = games.P1;
    document.getElementById("p2-set3").textContent = games.P2;
  }

  // =========================
  // 🟢 2. Actualizar puntos del juego actual
  // =========================
  if (serverId === "P1") {
    document.getElementById("p1-points").textContent = serverPts;
    document.getElementById("p2-points").textContent = returnerPts;
  } else {
    document.getElementById("p1-points").textContent = returnerPts;
    document.getElementById("p2-points").textContent = serverPts;
  }

  // =========================
  // 🎾 3. Mostrar quién saca
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
  // 🔁 4. Si termina el juego, resetear puntos y corregir juegos
  // =========================
  if (pointData.game_end) {
    // Resetear puntos a 0–0
    document.getElementById("p1-points").textContent = "0";
    document.getElementById("p2-points").textContent = "0";

    // Esperar un pequeño momento para asegurar que los juegos base ya se pintaron
    setTimeout(() => {
      // 🧮 Corregir marcador de juegos (backend lo actualiza 1 punto después)
      if (winnerId === "P1") {
        const el = document.getElementById(`p1-set${setNum}`);
        el.textContent = parseInt(el.textContent || "0") + 1;
      } else if (winnerId === "P2") {
        const el = document.getElementById(`p2-set${setNum}`);
        el.textContent = parseInt(el.textContent || "0") + 1;
      }

      console.log(`🎾 Fin del juego. Gana ${pointData.winner_name}`);
    }, 50); // ← un mini delay (50ms) evita que se sobreescriba

    // 🔄 Cambiar el servidor para el siguiente juego (frontend lo anticipa)
    const nextServer = serverId === "P1" ? "P2" : "P1";
    const serveP1 = document.getElementById("serve-p1");
    const serveP2 = document.getElementById("serve-p2");

    if (nextServer === "P1") {
      serveP1.classList.remove("off");
      serveP2.classList.add("off");
    } else {
      serveP2.classList.remove("off");
      serveP1.classList.add("off");
    }
  }
}
/*
function updateScoreboard(pointData) {
  // =========================
  // 🎾 1. Extraer datos base
  // =========================
  const setNum = pointData.set || 1;
  const score = pointData.score_after || {};
  const serverId = pointData.server_id || score.server || "P1";
  const winnerId = pointData.winner_id || null;
  const isTiebreak = pointData.is_tiebreak || false;
  const gameEnded = pointData.game_end || false;

  // =========================
  // 🧮 2. Juegos del set actual
  // =========================
  let games_p1 = score.set_games?.P1 ?? 0;
  let games_p2 = score.set_games?.P2 ?? 0;

  // Si el juego ha terminado, añadir +1 al ganador
  if (gameEnded) {
    if (winnerId === "P1") games_p1 += 1;
    else if (winnerId === "P2") games_p2 += 1;
  }

  // =========================
  // 💾 3. Sets anteriores (finalizados)
  // =========================
  const set1_final = matchData.set_scores?.[0] || [null, null];
  const set2_final = matchData.set_scores?.[1] || [null, null];
  const set3_final = matchData.set_scores?.[2] || [null, null];

  // =========================
  // 🎯 4. Puntos actuales del juego o tie-break
  // =========================
  let points_p1 = "0";
  let points_p2 = "0";

  if (isTiebreak && score.tiebreak_score) {
    // Si es un tie-break, usar el marcador interno
    points_p1 = score.tiebreak_score.P1 ?? 0;
    points_p2 = score.tiebreak_score.P2 ?? 0;
  } else {
    // Normal: mostrar 0–15–30–40–Ad
    const serverPts = score.server_points || "0";
    const returnerPts = score.returner_points || "0";

    if (serverId === "P1") {
      points_p1 = serverPts;
      points_p2 = returnerPts;
    } else {
      points_p1 = returnerPts;
      points_p2 = serverPts;
    }
  }

  // Si terminó el juego → resetear puntos a 0–0
  if (gameEnded) {
    points_p1 = "0";
    points_p2 = "0";
  }

  // =========================
  // 🧩 5. Aplicar al DOM
  // =========================

  // --- Juegos ---
  if (setNum === 1) {
    document.getElementById("p1-set1").textContent = games_p1;
    document.getElementById("p2-set1").textContent = games_p2;
  } else if (setNum === 2) {
    document.getElementById("p1-set1").textContent = set1_final[0] ?? "";
    document.getElementById("p2-set1").textContent = set1_final[1] ?? "";
    document.getElementById("p1-set2").textContent = games_p1;
    document.getElementById("p2-set2").textContent = games_p2;
  } else if (setNum === 3) {
    document.getElementById("p1-set1").textContent = set1_final[0] ?? "";
    document.getElementById("p2-set1").textContent = set1_final[1] ?? "";
    document.getElementById("p1-set2").textContent = set2_final[0] ?? "";
    document.getElementById("p2-set2").textContent = set2_final[1] ?? "";
    document.getElementById("p1-set3").textContent = games_p1;
    document.getElementById("p2-set3").textContent = games_p2;
  }

  // --- Puntos ---
  document.getElementById("p1-points").textContent = points_p1;
  document.getElementById("p2-points").textContent = points_p2;

  // --- Saque ---
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
  // 🧾 6. Log opcional
  // =========================
  console.log("📊 Estado marcador:", {
    setNum,
    games_p1,
    games_p2,
    points_p1,
    points_p2,
    serverId,
    winnerId,
    isTiebreak,
    gameEnded,
  });
}
*/

function showFinalScore() {
  // Obtener resultados finales del JSON completo
  const finalSets = matchData.set_scores;
  const winnerName = matchData.winner_name;

  // Poner los juegos finales de cada set
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

  // Resetear puntos a 0
  document.getElementById("p1-points").textContent = "0";
  document.getElementById("p2-points").textContent = "0";

  // Apagar indicador de saque (ya no hay siguiente punto)
  document.getElementById("serve-p1").classList.add("off");
  document.getElementById("serve-p2").classList.add("off");

  // Mostrar un texto de partido finalizado
  console.log(`🏆 Partido finalizado: gana ${winnerName}`);

  // Opcional: mostrar mensaje visual sobre el marcador
  const panel = document.getElementById("scoreboard-panel");
  const msg = document.createElement("div");
  msg.className = "text-3xl text-yellow-400 font-bold mt-4 animate-pulse";
  msg.textContent = `🏆 Partido finalizado — Ganador: ${winnerName}`;
  panel.appendChild(msg);
  
}
