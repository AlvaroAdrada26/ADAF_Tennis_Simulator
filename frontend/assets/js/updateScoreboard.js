import { PointFeedGenerator } from "./PointFeedGenerator.js";

let matchData = null;
let timeline = [];
let currentPoint = 0;
let matchLoaded = false;
let matchEnded = false;

let feedGenerator = null;

async function initFeedGenerator() {
  const files = ["serves", "returns", "rally", "reach", "misc"];
  const library = {};

  for (const f of files) {
    const res = await fetch(`./assets/js/feed_library/${f}.json`);
    const data = await res.json();
    Object.assign(library, data);
  }

  feedGenerator = new PointFeedGenerator(library);
  console.log("Biblioteca de frases cargada");
}

// Cargar automáticamente al iniciar el archivo
initFeedGenerator();


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

      const pointData = timeline[currentPoint];
      updateScoreboard(pointData);
      updatePointsFeed(pointData);
      playPointFeed(pointData);
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

function updatePointsFeed(pointData) {
  const feedList = document.getElementById("feed-list");
  const feedContainer = document.getElementById("points-feed");
  if (!feedList || !pointData) return;

  const setNum = pointData.set || 1;
  const gameNum = pointData.game || 1;
  const rally = pointData.stats?.rally_shots ?? 0;
  const winner = pointData.winner_name || "Jugador desconocido";
  const reason = pointData.reason || "";
  const serverId = pointData.server_id || "";
  const server = serverId === "P1" ? matchData.players.P1 : matchData.players.P2;
  const returner = serverId === "P1" ? matchData.players.P2 : matchData.players.P1;

  const score = pointData.score_after || {};
  const games = score.set_games || { P1: 0, P2: 0 };
  const marcadorSet = `${games.P1}–${games.P2}`;
  const marcadorJuego = `${score.server_points || "0"}–${score.returner_points || "0"}`;

  // === 🎯 Generar descripción de la jugada ===
  let desc = "";

  // Analizar tipo de punto
  if (reason.includes("ace")) {
    desc = `🎯 <span class="text-yellow-300 font-semibold">${server}</span> mete un ace por el ${Math.random() > 0.5 ? "centro" : "abierto"}.`;
  } else if (reason.includes("doble_falta")) {
    desc = `⚠️ <span class="text-yellow-300 font-semibold">${server}</span> comete una doble falta en un momento delicado.`;
  } else if (reason.includes("error_resto")) {
    desc = `❌ <span class="text-yellow-300 font-semibold">${returner}</span> falla el resto. Punto directo para ${server}.`;
  } else if (reason.includes("error_golpe")) {
    desc = `😬 Error no forzado de <span class="text-yellow-300 font-semibold">${returner}</span> tras un peloteo corto.`;
  } else if (reason.includes("no_llega")) {
    desc = `🏃‍♂️ <span class="text-yellow-300 font-semibold">${returner}</span> no logra alcanzar la bola tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  } else if (reason.includes("winner")) {
    desc = `🔥 <span class="text-yellow-300 font-semibold">${winner}</span> gana el punto con un golpe ganador tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  } else {
    desc = `🎾 Punto para <span class="text-yellow-300 font-semibold">${winner}</span> tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  }

  // === 🧩 Añadir mini resumen del punto ===
  const extraFeed = pointData.feed?.slice(-2)?.join("<br>") || "";
  const resumen = `<div class="text-xs text-gray-400 mt-1">${extraFeed}</div>`;

  // === 🏷️ Montar elemento del feed ===
  const li = document.createElement("li");
  li.innerHTML = `
    <div class="border border-blue-800/30 bg-slate-900/60 rounded-lg px-3 py-2 shadow-sm">
      <div class="flex justify-between items-center mb-1">
        <span class="text-gray-400 text-xs font-mono">Set ${setNum}, Juego ${gameNum}</span>
        <span class="text-gray-500 text-xs font-mono">[${marcadorSet} | ${marcadorJuego}]</span>
      </div>
      <div class="text-sm text-gray-200">${desc}</div>
      ${resumen}
    </div>
  `;
  li.className = "transition-all duration-300 opacity-0 translate-y-1";

  // Insertar arriba
  feedList.prepend(li);

  // Animación
  setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), 10);

  // Limitar a 8-10 jugadas
  while (feedList.children.length > 25) {
    feedList.removeChild(feedList.lastChild);
  }

  // Scroll arriba
  feedContainer.scrollTop = 0;
}

async function playPointFeed(pointData) {
  const liveList = document.getElementById("live-feed-list");
  liveList.innerHTML = "";

  const rawFeed = pointData.feed || [];
  const readableFeed = generateReadableFeed(rawFeed, pointData);

  for (const sentence of readableFeed) {
    const li = document.createElement("li");
    li.textContent = sentence;
    li.className = "opacity-0 translate-y-1 transition-all duration-300";
    liveList.appendChild(li);

    setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), 10);
    await new Promise(r => setTimeout(r, 800)); // ritmo natural
  }

  const summary = `Punto para ${pointData.winner_name}.`;
  const li = document.createElement("li");
  li.className = "text-yellow-400 font-semibold mt-3";
  li.textContent = summary;
  liveList.appendChild(li);
}


function generateReadableFeed(rawFeed, pointData) {
  const readable = [];
  const server = pointData.server_id === "P1" ? matchData.players.P1 : matchData.players.P2;
  const returner = pointData.server_id === "P1" ? matchData.players.P2 : matchData.players.P1;

  const extractValue = (text, key) => {
    const regex = new RegExp(`${key}=([0-9.]+)`);
    const match = text.match(regex);
    return match ? parseFloat(match[1]) : null;
  };

  for (const line of rawFeed) {
    const l = line.toLowerCase();

    // === SAQUES ===
    if (l.includes("primer saque")) {
      const pot = extractValue(line, "Pot");
      const prec = extractValue(line, "Prec");
      const inServe = l.includes("→ in");

      let phrase = `${server} inicia con un primer saque `;
      if (pot > 0.45) phrase += "muy potente";
      else if (pot > 0.3) phrase += "con buena velocidad";
      else phrase += "más conservador";

      if (prec > 0.4) phrase += " y bastante preciso";
      else if (prec > 0.2) phrase += " pero algo irregular";
      else phrase += " con poca colocación";

      phrase += inServe ? "." : ", que termina en falta.";
      readable.push(phrase);

    } else if (l.includes("segundo saque")) {
      const pot = extractValue(line, "Pot");
      const prec = extractValue(line, "Prec");
      const inServe = l.includes("→ in");

      let phrase = `${server} ejecuta un segundo servicio `;
      if (pot > 0.45) phrase += "agresivo";
      else if (pot > 0.3) phrase += "sólido";
      else phrase += "seguro";

      phrase += prec > 0.3 ? " y bien colocado" : " con poca precisión";
      phrase += inServe ? "." : ", que se marcha fuera.";
      readable.push(phrase);
    }

    // === RESTOS / GOLPES ===
    else if (l.includes("golpea")) {
      const pot = extractValue(line, "Pot");
      const prec = extractValue(line, "Prec");
      const result = l.includes("dentro")
        ? "la bola entra con margen."
        : l.includes("fuera")
        ? "la bola se va fuera."
        : "mantiene el intercambio.";

      const player = l.includes("diego") ? returner : server;
      let phrase = `${player} golpea `;
      if (pot > 0.45) phrase += "con mucha potencia";
      else if (pot > 0.3) phrase += "con buena intensidad";
      else phrase += "de forma más defensiva";

      phrase += prec > 0.35 ? " y control." : " pero sin demasiada precisión.";
      phrase += " " + result;
      readable.push(phrase);
    }

    // === INTENTOS DE ALCANZAR ===
    else if (l.includes("intenta alcanzar")) {
      const player = l.includes("diego") ? returner : server;
      if (l.includes("no llega")) readable.push(`${player} no logra alcanzar la bola.`);
      else readable.push(`${player} llega justo a tiempo para devolver la pelota.`);
    }

    // === RESULTADO FINAL ===
    else if (l.includes("resultado")) {
      if (l.includes("doble falta")) readable.push(`${server} comete una doble falta, punto para ${returner}.`);
      else if (l.includes("error de resto")) readable.push(`${returner} falla el resto, punto para ${server}.`);
      else if (l.includes("punto para sacador")) readable.push(`Punto para ${server}.`);
      else if (l.includes("punto para restador")) readable.push(`Gran resto, punto para ${returner}.`);
    }
  }

  return readable.length ? readable : ["(Sin detalles disponibles para este punto)"];
}
