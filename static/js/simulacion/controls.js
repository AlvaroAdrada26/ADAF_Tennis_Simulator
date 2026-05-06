// frontend/assets/js/simulacion/controls.js
/* =========================================================
   CONTROLS.JS — Panel de control completo de la simulación
   Botones: Restart, Previous, Play/Pause, Next, End
   + Velocidad (x1 / x2 / x4)
   ========================================================= */

import {
  getState, nextPoint, previousPoint,
  endMatch, resetState, accumulatePointStats, recomputeStats
} from "./state.js";
import { updateScoreboard, showFinalScore, resetScoreboard, updateLeadingPlayer } from "./scoreboard.js";
import { updatePointsFeed, playPointFeed, clearFeeds, cancelFeed, showPointSummary, updateLiveStatsPanel, updateMomentumBar } from "./liveFeed.js";
import { fetchMatchData, setPlayerNames } from "./api.js";
import { setMatchData } from "./state.js";
import { initLiveFeed } from "./liveFeed.js";

/* ---------- estado interno del reproductor ---------- */
let autoplayTimer = null;   // setTimeout id
let isPlaying    = false;
let speedMs      = 1200;    // ms entre puntos (x1)
let speedFactor  = 1;

const PLAY_PATH  = '<path stroke-linecap="round" stroke-linejoin="round" d="M8 5v14l11-7z" />';
const PAUSE_PATH = '<path stroke-linecap="round" stroke-linejoin="round" d="M6 4h4v16H6zM14 4h4v16h-4z" />';

/* ---------- helpers ---------- */
function setPlayIcon(playing) {
  const icon = document.getElementById("icon-play");
  if (icon) icon.innerHTML = playing ? PAUSE_PATH : PLAY_PATH;
}

function stopAutoplay() {
  if (autoplayTimer) { clearTimeout(autoplayTimer); autoplayTimer = null; }
  isPlaying = false;
  setPlayIcon(false);
}

/** Updates the point counter display */
function updatePointCounter() {
  const { currentPoint } = getState();
  const el = document.getElementById("point-counter");
  if (el) el.textContent = `Punto ${currentPoint}`;
}

/** Avanza un punto con todas las actualizaciones visuales */
async function advanceOnePoint({ playFeed = true } = {}) {
  const { timeline, matchEnded } = getState();
  if (matchEnded || !timeline?.length) { stopAutoplay(); return; }

  const pointData = nextPoint();
  if (!pointData) {
    stopAutoplay();
    endMatch();
    showFinalScore();
    showPostMatchBar();
    return;
  }

  updateScoreboard(pointData);
  updatePointsFeed(pointData);
  accumulatePointStats(pointData);
  updateLiveStatsPanel();
  updateMomentumBar();
  updateLeadingPlayer(pointData);
  updatePointCounter();
  if (playFeed) await playPointFeed(pointData);
}

/** Recursive async autoplay loop using setTimeout */
async function autoplayLoop() {
  const { matchEnded } = getState();
  if (!isPlaying || matchEnded) {
    if (matchEnded) { stopAutoplay(); showPostMatchBar(); }
    return;
  }
  await advanceOnePoint({ playFeed: false });
  // Show summary phrase in feed during autoplay
  const { currentPoint, timeline } = getState();
  if (currentPoint > 0 && currentPoint <= timeline.length) {
    showPointSummary(timeline[currentPoint - 1]);
  }
  if (isPlaying && !getState().matchEnded) {
    autoplayTimer = setTimeout(() => autoplayLoop(), speedMs / speedFactor);
  } else if (getState().matchEnded) {
    stopAutoplay();
    showPostMatchBar();
  }
}

/* ==========================================================
   bindSimulationControls  —  se llama una vez desde app.js
   ========================================================== */
export function bindSimulationControls() {
  const nextBtn    = document.getElementById("btn-next");
  const prevBtn    = document.getElementById("btn-previous");
  const endBtn     = document.getElementById("btn-end");
  const playBtn    = document.getElementById("btn-play");
  const restartBtn = document.getElementById("btn-restart");

  if (!nextBtn || !prevBtn || !endBtn || !playBtn || !restartBtn) {
    console.warn("⚠️ No se encontraron todos los botones de simulación.");
    return;
  }

  console.log("🎮 Controles de simulación inicializados");

  /* ───── ▶ / ⏸  Play / Pause ───── */
  playBtn.addEventListener("click", () => {
    const { matchEnded } = getState();
    if (matchEnded) return;

    if (isPlaying) {
      stopAutoplay();
    } else {
      isPlaying = true;
      setPlayIcon(true);
      cancelFeed();
      autoplayLoop();
    }
  });

  /* ───── ⏭ Siguiente ───── */
  nextBtn.addEventListener("click", async () => {
    stopAutoplay();
    cancelFeed();
    await advanceOnePoint();
  });

  /* ───── ⏮ Anterior ───── */
  prevBtn.addEventListener("click", () => {
    stopAutoplay();
    cancelFeed();
    const pointData = previousPoint();
    if (pointData) {
      updateScoreboard(pointData);
      updateLeadingPlayer(pointData);
    } else {
      resetScoreboard();
    }
    recomputeStats();
    updateLiveStatsPanel();
    updateMomentumBar();
    updatePointCounter();
  });

  /* ───── ⏩ Ir al Final ───── */
  endBtn.addEventListener("click", () => {
    stopAutoplay();
    cancelFeed();
    let pt;
    while ((pt = nextPoint())) {
      updateScoreboard(pt);
      updatePointsFeed(pt);
      accumulatePointStats(pt);
    }
    updateLiveStatsPanel();
    updateMomentumBar();
    updatePointCounter();
    endMatch();
    showFinalScore();
    showPostMatchBar();
  });

  /* ───── ⏪⏪ Reiniciar ───── */
  restartBtn.addEventListener("click", async () => {
    stopAutoplay();
    cancelFeed();
    resetState();
    resetScoreboard();
    clearFeeds();

    try {
      const data = await fetchMatchData();
      setMatchData(data);
      setPlayerNames(data.players);
      updateLiveStatsPanel();
      updateMomentumBar();
      updatePointCounter();
      console.log("🔄 Simulación reiniciada");
    } catch (e) {
      console.error("Error reiniciando simulación:", e);
    }
  });

  /* ───── 🏎️ Velocidad ───── */
  document.querySelectorAll(".speed-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      // Visual: resaltar botón activo
      document.querySelectorAll(".speed-btn").forEach(b => {
        b.classList.remove("bg-yellow-400", "text-slate-900");
        b.classList.add("text-yellow-300");
      });
      btn.classList.add("bg-yellow-400", "text-slate-900");
      btn.classList.remove("text-yellow-300");

      speedFactor = parseInt(btn.dataset.speed) || 1;
      console.log(`🏎️ Velocidad: x${speedFactor}`);
    });
  });
}

/* ==========================================================
   Funciones auxiliares de UI post-partido
   ========================================================== */
function showPostMatchBar() {
  const isGuest = !localStorage.getItem('access_token');

  if (isGuest) {
    const guestBar = document.getElementById("post-match-bar-guest");
    if (guestBar) guestBar.classList.remove("hidden");
    return;
  }

  const bar = document.getElementById("post-match-bar");
  if (bar) bar.classList.remove("hidden");

  // Show auto-save status from backend
  const result = JSON.parse(sessionStorage.getItem("match_result") || "{}");
  const statusEl = document.getElementById("save-status");
  if (statusEl) {
    if (result.match_db_id) {
      statusEl.textContent = "Partido guardado automáticamente";
      statusEl.className = "text-sm text-green-400/80";
    } else {
      statusEl.textContent = "";
    }
  }
}
