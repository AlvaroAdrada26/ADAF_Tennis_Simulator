// frontend/assets/js/simulacion/controls.js
/* =========================================================
   CONTROLS.JS — Panel de control completo de la simulación
   Botones: Restart, Previous, Play/Pause, Next, End
   + Velocidad (x1 / x2 / x4)
   ========================================================= */

import {
  getState, nextPoint, previousPoint,
  endMatch, resetState
} from "./state.js";
import { updateScoreboard, showFinalScore, resetScoreboard } from "./scoreboard.js";
import { updatePointsFeed, playPointFeed, clearFeeds } from "./liveFeed.js";
import { fetchMatchData, setPlayerNames } from "./api.js";
import { setMatchData } from "./state.js";
import { initLiveFeed } from "./liveFeed.js";

/* ---------- estado interno del reproductor ---------- */
let autoplayTimer = null;   // setInterval id
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
  if (autoplayTimer) { clearInterval(autoplayTimer); autoplayTimer = null; }
  isPlaying = false;
  setPlayIcon(false);
}

/** Avanza un punto con todas las actualizaciones visuales */
async function advanceOnePoint() {
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
  await playPointFeed(pointData);
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
      // Primer punto inmediato, luego intervalo
      advanceOnePoint();
      autoplayTimer = setInterval(() => {
        const { matchEnded } = getState();
        if (matchEnded) { stopAutoplay(); showPostMatchBar(); return; }
        advanceOnePoint();
      }, speedMs / speedFactor);
    }
  });

  /* ───── ⏭ Siguiente ───── */
  nextBtn.addEventListener("click", async () => {
    stopAutoplay();
    await advanceOnePoint();
  });

  /* ───── ⏮ Anterior ───── */
  prevBtn.addEventListener("click", () => {
    stopAutoplay();
    const pointData = previousPoint();
    if (pointData) {
      updateScoreboard(pointData);
    } else {
      // We're back at the very beginning
      resetScoreboard();
    }
  });

  /* ───── ⏩ Ir al Final ───── */
  endBtn.addEventListener("click", () => {
    stopAutoplay();
    // Avanza todos los puntos restantes de golpe
    const { timeline } = getState();
    let pt;
    while ((pt = nextPoint())) {
      updateScoreboard(pt);
      updatePointsFeed(pt);
    }
    endMatch();
    showFinalScore();
    showPostMatchBar();
  });

  /* ───── ⏪⏪ Reiniciar ───── */
  restartBtn.addEventListener("click", async () => {
    stopAutoplay();
    resetState();
    resetScoreboard();
    clearFeeds();

    // Recargar datos y reiniciar
    try {
      const data = await fetchMatchData();
      setMatchData(data);
      setPlayerNames(data.players);
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

      // Si está reproduciéndose, reiniciar el intervalo con la nueva velocidad
      if (isPlaying) {
        clearInterval(autoplayTimer);
        autoplayTimer = setInterval(() => {
          const { matchEnded } = getState();
          if (matchEnded) { stopAutoplay(); showPostMatchBar(); return; }
          advanceOnePoint();
        }, speedMs / speedFactor);
      }
    });
  });

  /* ───── 💾 Guardar partido en BD ───── */
  const saveBtn = document.getElementById("btn-save-match");
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      saveBtn.disabled = true;
      saveBtn.textContent = "⏳ Guardando…";

      try {
        const config = JSON.parse(sessionStorage.getItem("match_config") || "{}");
        const result = JSON.parse(sessionStorage.getItem("match_result") || "{}");

        // Si simulate_match ya guardó automáticamente, no hacer doble POST
        if (result.match_db_id) {
          showSaveStatus(`✅ Partido ya guardado automáticamente (ID: ${result.match_db_id}).`);
          saveBtn.textContent = "✅ Guardado";
          return;
        }

        if (!config.db_player1_id || !config.db_player2_id) {
          showSaveStatus("⚠️ No se encontraron los IDs de jugadores. No se puede guardar.", true);
          saveBtn.disabled = false;
          saveBtn.textContent = "💾 Guardar";
          return;
        }

        const payload = {
          id_jugador_1: config.db_player1_id,
          id_jugador_2: config.db_player2_id,
          id_usuario_creador: null,
          winner_id: result.winner_id,
          set_scores: result.set_scores,
          config: {
            surface: config.surface || "Dura",
            best_of: config.best_of || 3,
            tiebreak: config.tiebreak !== undefined ? config.tiebreak : true,
          },
          timeline: result.timeline || [],
        };

        const res = await fetch("/api/matches/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          const data = await res.json();
          showSaveStatus(`✅ Partido guardado (ID: ${data.partido_id}). Marcador: ${data.marcador}`);
          saveBtn.textContent = "✅ Guardado";
        } else {
          const err = await res.json().catch(() => ({}));
          showSaveStatus(`❌ Error: ${err.detail || "No se pudo guardar"}`, true);
          saveBtn.disabled = false;
          saveBtn.textContent = "💾 Reintentar";
        }
      } catch (e) {
        showSaveStatus("❌ Error de conexión al guardar", true);
        saveBtn.disabled = false;
        saveBtn.textContent = "💾 Reintentar";
      }
    });
  }
}

/* ==========================================================
   Funciones auxiliares de UI post-partido
   ========================================================== */
function showPostMatchBar() {
  const bar = document.getElementById("post-match-bar");
  if (bar) bar.classList.remove("hidden");
}

function showSaveStatus(msg, isError = false) {
  const el = document.getElementById("save-status");
  if (!el) return;
  el.textContent = msg;
  el.className = `text-lg font-medium ${isError ? "text-red-400" : "text-green-400"}`;
}
