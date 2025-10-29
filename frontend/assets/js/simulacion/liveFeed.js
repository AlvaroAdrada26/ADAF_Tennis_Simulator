// frontend/assets/js/simulacion/liveFeed.js
/* Módulo encargado de mostrar el feed en tiempo real y el registro de puntos. */

import { getState } from "./state.js";
import { PointFeedGenerator } from "./feed/PointFeedGenerator.js";

let feedGenerator = null;

/* =========================================================
   📘 1. Inicialización de la biblioteca de frases (JSONs)
   ========================================================= */
export async function initLiveFeed() {
  const files = ["serves", "returns", "rally", "reach", "misc"];
  const library = {};

  for (const f of files) {
    try {
      const res = await fetch(`/frontend/assets/js/simulacion/feed_library/${f}.json`);
      const data = await res.json();
      library[f] = data;
    } catch (err) {
      console.error(`Error cargando ${f}.json:`, err);
    }
  }

  feedGenerator = new PointFeedGenerator(library);
  console.log("📚 Biblioteca de frases cargada para feed dinámico");
  console.log(`La biblioteca de frases es: `, library);
}

/* =========================================================
   🎾 2. Feed de resumen de puntos (parte inferior)
   ========================================================= */
export function updatePointsFeed(pointData) {
  const { matchData } = getState();
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
  const marcadorSet = `${games.P1}-${games.P2}`;
  const marcadorJuego = `${score.server_points || "0"}-${score.returner_points || "0"}`;

  // === 🎯 Descripción general del punto ===
  let desc = "";
  if (reason.includes("ace")) {
    desc = `🎯 <span class="text-yellow-300 font-semibold">${server}</span> mete un ace por el ${Math.random() > 0.5 ? "centro" : "abierto"}.`;
  } else if (reason.includes("doble_falta")) {
    desc = `⚠️ <span class="text-yellow-300 font-semibold">${server}</span> comete una doble falta.`;
  } else if (reason.includes("error_resto")) {
    desc = `❌ <span class="text-yellow-300 font-semibold">${returner}</span> falla el resto. Punto directo para ${server}.`;
  } else if (reason.includes("error_golpe")) {
    desc = `😬 Error no forzado de <span class="text-yellow-300 font-semibold">${returner}</span> tras un intercambio corto.`;
  } else if (reason.includes("no_llega")) {
    desc = `🏃‍♂️ <span class="text-yellow-300 font-semibold">${returner}</span> no logra alcanzar la bola tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  } else {
    desc = `🎾 Punto para <span class="text-yellow-300 font-semibold">${winner}</span> tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  }

  // === 🧩 Mini resumen (últimas líneas del feed del backend) ===
  const extraFeed = pointData.feed?.slice(-2)?.join("<br>") || "";
  const resumen = `<div class="text-xs text-gray-400 mt-1">${extraFeed}</div>`;

  // === 🏷️ Renderizado visual ===
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

  feedList.prepend(li);
  setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), 10);

  while (feedList.children.length > 25) {
    feedList.removeChild(feedList.lastChild);
  }

  feedContainer.scrollTop = 0;
}

/* =========================================================
   ⏱️ 3. Simulación en tiempo real (feed narrativo punto a punto)
   ========================================================= */
export async function playPointFeed(pointData) {
  const liveList = document.getElementById("live-feed-list");
  liveList.innerHTML = "";

  // Asegurarse de que el generador esté listo
  if (!feedGenerator) {
    console.warn("FeedGenerator aún no inicializado");
    return;
  }
  console.log("Generando feed para punto:", pointData);
  const { matchData } = getState();
  const players = matchData.players || { P1: "Jugador 1", P2: "Jugador 2" };

  //  Generar frases legibles con PointFeedGenerator
  const readableFeed = feedGenerator.generateFeedForPoint(pointData, players);

  // Mostrar frase por frase con animación natural
  for (let i = 0; i < readableFeed.length - 1; i++) {
    const sentence = readableFeed[i];
    const li = document.createElement("li");
    li.textContent = sentence;
    li.className = "opacity-0 translate-y-1 transition-all duration-300";
    liveList.appendChild(li);

    // Animación de aparición
    setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), 10);
    await new Promise(r => setTimeout(r, 800));
  }

  // 🏁 Última frase (resumen o cierre narrativo)
  const lastSentence = readableFeed[readableFeed.length - 1] || "(Fin del punto)";
  const li = document.createElement("li");
  li.className = "text-yellow-400 font-semibold mt-3";
  li.textContent = lastSentence;
  liveList.appendChild(li);
}
