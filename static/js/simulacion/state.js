// frontend/assets/js/simulacion/state.js
/* =========================================================
   STATE.JS — Estado central de la simulación de tenis
   Gestiona el partido actual, progreso de puntos, y banderas.
   ========================================================= */

const state = {
  matchData: null,     // JSON completo devuelto por el backend
  timeline: [],        // Array de puntos (cada punto = una acción completa)
  currentPoint: 0,     // Índice actual en el timeline
  matchLoaded: false,  // Evita recargar el partido varias veces
  matchEnded: false,   // Bandera de fin de partido
  feedGenerator: null, // Instancia de PointFeedGenerator (se inicializa en liveFeed.js)
  liveStats: { P1: { aces: 0, doubleFaults: 0, unforcedErrors: 0, pointsWon: 0 }, P2: { aces: 0, doubleFaults: 0, unforcedErrors: 0, pointsWon: 0 } },
  recentWinners: []  // últimos 25 ganadores para momentum visual
};

/* =========================================================
   GETTERS (lectura segura del estado)
   ========================================================= */

/**
 * Devuelve el objeto de estado completo (solo lectura).
 * No modificar directamente fuera de este módulo.
 */
export function getState() {
  return state;
}

/**
 * Devuelve el punto actual del timeline (si existe).
 */
export function getCurrentPoint() {
  return state.timeline[state.currentPoint] || null;
}

/**
 * Devuelve el nombre del jugador según su ID (P1/P2).
 */
export function getPlayerName(id) {
  if (!state.matchData?.players) return id;
  return state.matchData.players[id] || id;
}

/* =========================================================
   SETTERS (mutación controlada del estado)
   ========================================================= */

/**
 * Guarda los datos completos del partido simulados por el backend.
 */
export function setMatchData(data) {
  if (!data) return;
  state.matchData = data;
  state.timeline = data.timeline || [];
  state.matchLoaded = true;
  state.currentPoint = 0;
  state.matchEnded = false;
  console.log("Match data guardado en estado:", data);
}

/**
 * Avanza al siguiente punto si existe.
 * @returns {Object|null} El siguiente punto o null si no hay más.
 */
export function nextPoint() {
  if (state.currentPoint < state.timeline.length) {
    const point = state.timeline[state.currentPoint];
    state.currentPoint++;
    if (state.currentPoint >= state.timeline.length) state.matchEnded = true;
    return point;
  }
  return null;
}

/**
 * Retrocede al punto anterior.
 * @returns {Object|null} El punto anterior o null si ya está al inicio.
 */
export function previousPoint() {
  if (state.currentPoint > 0) {
    state.currentPoint--;
    state.matchEnded = false;
    // Return the point whose score_after should be displayed,
    // i.e. the point BEFORE the new currentPoint position.
    return state.currentPoint > 0 ? state.timeline[state.currentPoint - 1] : null;
  }
  return null;
}

/**
 * Marca el partido como finalizado.
 */
export function endMatch() {
  state.matchEnded = true;
}

/**
 * Reinicia el estado completo de la simulación (por si se recarga).
 */
export function resetState() {
  state.matchData = null;
  state.timeline = [];
  state.currentPoint = 0;
  state.matchLoaded = false;
  state.matchEnded = false;
  state.feedGenerator = null;
  state.liveStats = { P1: { aces: 0, doubleFaults: 0, unforcedErrors: 0, pointsWon: 0 }, P2: { aces: 0, doubleFaults: 0, unforcedErrors: 0, pointsWon: 0 } };
  state.recentWinners = [];
  console.log("🔄 Estado reiniciado.");
}

/* ── Acumulación de estadísticas en tiempo real ── */
function _accumulateOne(pt) {
  const reason = pt.reason || "";
  const winnerId = pt.winner;
  const loserId = winnerId === "P1" ? "P2" : "P1";
  const serverId = pt.server_id || "P1";
  if (reason.includes("ace"))         state.liveStats[serverId].aces++;
  if (reason.includes("doble_falta")) state.liveStats[serverId].doubleFaults++;
  if (reason.includes("error_golpe") || reason.includes("error_resto"))
    state.liveStats[loserId].unforcedErrors++;
  state.liveStats[winnerId].pointsWon++;
  state.recentWinners.push(winnerId);
}

export function accumulatePointStats(pointData) {
  _accumulateOne(pointData);
  if (state.recentWinners.length > 25) state.recentWinners.shift();
}

export function recomputeStats() {
  state.liveStats = { P1: { aces: 0, doubleFaults: 0, unforcedErrors: 0, pointsWon: 0 }, P2: { aces: 0, doubleFaults: 0, unforcedErrors: 0, pointsWon: 0 } };
  state.recentWinners = [];
  for (let i = 0; i < state.currentPoint; i++) _accumulateOne(state.timeline[i]);
  if (state.recentWinners.length > 25) state.recentWinners = state.recentWinners.slice(-25);
}

/* =========================================================
   Helpers opcionales para otros módulos
   ========================================================= */

/**
 * Comprueba si el partido ya está cargado.
 */
export function isMatchLoaded() {
  return state.matchLoaded;
}

/**
 * Comprueba si el partido ha finalizado.
 */
export function isMatchEnded() {
  return state.matchEnded;
}

/**
 * Devuelve el número total de puntos del timeline.
 */
export function getTotalPoints() {
  return state.timeline.length;
}

/**
 * Guarda el feed generator compartido (una sola instancia global).
 */
export function setFeedGenerator(generator) {
  state.feedGenerator = generator;
}

/**
 * Devuelve el feed generator actual (si ya fue inicializado).
 */
export function getFeedGenerator() {
  return state.feedGenerator;
}
