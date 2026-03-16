// frontend/assets/js/simulacion/liveFeed.js
/* Módulo encargado de mostrar el feed en tiempo real y el registro de puntos. */

import { getState } from "./state.js";
import { PointFeedGenerator } from "./feed/PointFeedGenerator.js";

let feedGenerator = null;
let feedVersion = 0;

/* =========================================================
   📘 1. Inicialización de la biblioteca de frases (JSONs)
   ========================================================= */
export async function initLiveFeed() {
  const files = ["serves", "returns", "rally", "reach", "misc"];
  const library = {};

  for (const f of files) {
    try {
      const res = await fetch(`static/js/simulacion/feed_library/${f}.json`);
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
  const feedList = document.getElementById("points-feed-list");
  const feedContainer = document.getElementById("points-feed-container");
  if (!feedList || !pointData) return;

  const setNum = pointData.set || 1;
  const gameNum = pointData.game || 1;
  const rally = pointData.stats?.rally_shots ?? 0;
  const winnerId = pointData.winner;
  const winner = pointData.winner_name || "Jugador desconocido";
  const reason = pointData.reason || "";
  const serverId = pointData.server_id || "";
  const server = serverId === "P1" ? matchData.players.P1 : matchData.players.P2;
  const returner = serverId === "P1" ? matchData.players.P2 : matchData.players.P1;
  const loserId = winnerId === "P1" ? "P2" : "P1";
  const loser = loserId === "P1" ? matchData.players.P1 : matchData.players.P2;

  const score = pointData.score_after || {};
  const games = score.set_games || { P1: 0, P2: 0 };
  const marcadorSet = `${games.P1}-${games.P2}`;
  let marcadorJuego;
  if (pointData.is_tiebreak && score.tiebreak_score) {
    marcadorJuego = `${score.tiebreak_score.P1}-${score.tiebreak_score.P2}`;
  } else {
    marcadorJuego = `${score.server_points || "0"}-${score.returner_points || "0"}`;
  }

  // === Icon + description based on point type ===
  let icon = "🎾";
  let desc = "";
  if (reason.includes("ace")) {
    icon = "🎯";
    desc = `<span class="text-yellow-300 font-semibold">${server}</span> mete un ace por el ${Math.random() > 0.5 ? "centro" : "abierto"}.`;
  } else if (reason.includes("doble_falta")) {
    icon = "⚠️";
    desc = `<span class="text-yellow-300 font-semibold">${server}</span> comete una doble falta.`;
  } else if (reason.includes("error_resto")) {
    icon = "❌";
    desc = `<span class="text-yellow-300 font-semibold">${loser}</span> falla el resto. Punto directo para <span class="text-yellow-300 font-semibold">${winner}</span>.`;
  } else if (reason.includes("error_golpe")) {
    icon = "😬";
    desc = `Error no forzado de <span class="text-yellow-300 font-semibold">${loser}</span> tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  } else if (reason.includes("no_llega")) {
    icon = "🏃";
    desc = `<span class="text-yellow-300 font-semibold">${loser}</span> no alcanza la bola tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  } else {
    desc = `Punto para <span class="text-yellow-300 font-semibold">${winner}</span> tras ${rally} golpe${rally === 1 ? "" : "s"}.`;
  }

  // === Subtle background based on winner ===
  const bgClass = winnerId === "P1"
    ? "border-l-blue-400 bg-blue-950/30"
    : "border-l-amber-400 bg-amber-950/20";

  const li = document.createElement("li");
  li.innerHTML = `
    <div class="border border-blue-800/20 ${bgClass} border-l-2 rounded-lg px-4 py-2.5 shadow-sm">
      <div class="flex items-center gap-2">
        <span class="text-lg leading-none">${icon}</span>
        <span class="text-sm text-gray-200 flex-1">${desc}</span>
      </div>
    </div>
  `;
  li.className = "transition-all duration-300 opacity-0 translate-y-1";

  feedList.prepend(li);
  setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), 10);

  while (feedList.children.length > 8) {
    feedList.removeChild(feedList.lastChild);
  }

  feedContainer.scrollTop = 0;
}

/* =========================================================
   ⏱️ 3. Simulación en tiempo real (feed narrativo punto a punto)
   ========================================================= */
export function cancelFeed() {
  feedVersion++;
  const liveList = document.getElementById("live-feed-list");
  if (liveList) liveList.innerHTML = "";
}

/** Muestra solo la frase resumen del punto (para autoplay) */
export function showPointSummary(pointData) {
  const header = document.getElementById("live-feed-header");
  if (header) header.textContent = `Set ${pointData.set || 1} \u00b7 Juego ${pointData.game || 1}`;

  const liveList = document.getElementById("live-feed-list");
  if (!liveList || !feedGenerator) return;

  const { matchData } = getState();
  const players = matchData.players || { P1: "Jugador 1", P2: "Jugador 2" };
  const readableFeed = feedGenerator.generateFeedForPoint(pointData, players);
  const lastSentence = readableFeed[readableFeed.length - 1] || "";
  liveList.innerHTML = "";
  const li = document.createElement("li");
  li.className = "text-yellow-400 font-semibold text-base text-center py-4";
  li.textContent = lastSentence;
  liveList.appendChild(li);
}

export async function playPointFeed(pointData) {
  feedVersion++;
  const myVersion = feedVersion;

  const liveList = document.getElementById("live-feed-list");
  liveList.innerHTML = "";

  // Update feed header with current set/game
  const header = document.getElementById("live-feed-header");
  if (header) header.textContent = `Set ${pointData.set || 1} \u00b7 Juego ${pointData.game || 1}`;

  if (!feedGenerator) {
    console.warn("FeedGenerator aún no inicializado");
    return;
  }
  const { matchData } = getState();
  const players = matchData.players || { P1: "Jugador 1", P2: "Jugador 2" };
  const readableFeed = feedGenerator.generateFeedForPoint(pointData, players);

  for (let i = 0; i < readableFeed.length - 1; i++) {
    if (feedVersion !== myVersion) return;

    const sentence = readableFeed[i];
    const li = document.createElement("li");
    li.textContent = sentence;
    li.className = "opacity-0 translate-y-1 transition-all duration-300";
    liveList.appendChild(li);
    setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), 10);
    await new Promise(r => setTimeout(r, 800));

    if (feedVersion !== myVersion) return;
  }

  if (feedVersion !== myVersion) return;
  const lastSentence = readableFeed[readableFeed.length - 1] || "(Fin del punto)";
  const li = document.createElement("li");
  li.className = "text-yellow-400 font-semibold mt-3";
  li.textContent = lastSentence;
  liveList.appendChild(li);
}

/* =========================================================
   🧹 4. Limpiar ambos feeds (para reinicio)
   ========================================================= */
export function clearFeeds() {
  cancelFeed();
  const pointsList = document.getElementById("points-feed-list");
  const feedHeader = document.getElementById("live-feed-header");
  const momentumBar = document.getElementById("momentum-bar");
  if (pointsList) pointsList.innerHTML = "";
  if (feedHeader) feedHeader.textContent = "";
  if (momentumBar) momentumBar.innerHTML = "";
}

/* =========================================================
   📊 5. Panel de estadísticas en tiempo real
   ========================================================= */
export function updateLiveStatsPanel() {
  const { liveStats, matchData } = getState();
  const n1 = document.getElementById("stats-p1-name");
  const n2 = document.getElementById("stats-p2-name");
  if (n1 && matchData?.players?.P1) n1.textContent = matchData.players.P1;
  if (n2 && matchData?.players?.P2) n2.textContent = matchData.players.P2;
  const map = [
    ["stat-p1-pts", liveStats.P1.pointsWon], ["stat-p2-pts", liveStats.P2.pointsWon],
    ["stat-p1-aces", liveStats.P1.aces],  ["stat-p2-aces", liveStats.P2.aces],
    ["stat-p1-df", liveStats.P1.doubleFaults], ["stat-p2-df", liveStats.P2.doubleFaults],
    ["stat-p1-ue", liveStats.P1.unforcedErrors], ["stat-p2-ue", liveStats.P2.unforcedErrors],
  ];
  for (const [id, val] of map) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }
}

/* =========================================================
   🟢🟡 6. Barra de momentum (últimos 15 puntos)
   ========================================================= */
export function updateMomentumBar() {
  const { recentWinners, matchData } = getState();
  const bar = document.getElementById("momentum-bar");
  if (!bar) return;
  bar.innerHTML = "";
  for (const w of recentWinners) {
    const dot = document.createElement("div");
    dot.className = w === "P1"
      ? "w-3.5 h-3.5 rounded-sm bg-blue-500 shadow-[0_0_4px_rgba(59,130,246,0.5)] transition-all duration-300"
      : "w-3.5 h-3.5 rounded-sm bg-amber-400 shadow-[0_0_4px_rgba(251,191,36,0.5)] transition-all duration-300";
    bar.appendChild(dot);
  }
  const n1 = document.getElementById("momentum-p1-name");
  const n2 = document.getElementById("momentum-p2-name");
  if (n1 && matchData?.players?.P1) n1.textContent = matchData.players.P1;
  if (n2 && matchData?.players?.P2) n2.textContent = matchData.players.P2;
}
