/* =================================================================
   SUMMARY.JS — Página de resumen post-partido
   Lee sessionStorage["match_result"] / ["match_config"] y genera:
     · Banner del ganador con confetti
     · Tabla ATP-style de comparación de estadísticas
     · 4 gráficas Chart.js (doughnut, barras, radar, histograma)
   ================================================================= */

/* ── Traducciones inline (para etiquetas de Chart.js) ────────── */
var SUMMARY_T = {
  es: {
    summaryChampion:         "CAMPEÓN",
    summaryWins:             "Gana el Partido",
    summaryMatchStats:       "Estadísticas del Partido",
    summaryVersus:           "vs",
    /* Secciones */
    summarySectionServe:     "Saque",
    summarySectionReturn:    "Resto",
    summarySectionPoints:    "Puntos",
    /* Saque */
    summaryAces:             "Aces",
    summaryDoubleFaults:     "Dobles Faltas",
    summaryFirstServePct:    "1.er Saque %",
    summaryPtsOn1st:         "Pts. en 1.er Saque %",
    summaryPtsOn2nd:         "Pts. en 2.º Saque %",
    summaryServicePtsWon:    "Pts. de Saque Ganados %",
    /* Resto */
    summaryReturnPtsWon:     "Pts. de Resto Ganados %",
    summaryBreakPoints:      "Break Points",
    summaryBPSaved:          "Break Points Salvados",
    /* Puntos */
    summaryTotalPtsPlayed:   "Puntos Jugados",
    summaryTotalPoints:      "Puntos Ganados",
    summaryTotalPtsWonPct:   "Puntos Ganados %",
    summaryWinners:          "Winners",
    summaryUnforcedErrors:   "Err. No Forzados",
    summaryWinnerUERatio:    "Ratio Winners / ENF",
    summaryAvgRally:         "Media de Rally",
    summaryMaxRally:         "Rally Más Largo",
    /* Charts */
    summaryReturnPts:        "Puntos de Resto",
    summaryFirstServe:       "1.er Saque %",
    summaryPtsOn1stServe:    "Pts. 1.er Saque %",
    summaryPtsOn2ndServe:    "Pts. 2.º Saque %",
    summaryReturnWon:        "Puntos Resto %",
    summaryRallyChart:       "Duración del Punto",
    summaryShots:            "golpes",
    /* Momentum */
    summaryMomentumChart:    "Momentum del Partido",
    summaryMomentumP1:       "Momentum",
    summaryMomentumP2:       "Momentum",
    summaryMomentumTooltipSet:    "Set",
    summaryMomentumTooltipGame:   "Game",
    summaryMomentumTooltipPoint:  "Punto",
    summaryMomentumTooltipWinner: "Ganador",
    summaryMomentumTooltipScore:  "Marcador",
    summaryMomentumTooltipEndSet: "Fin del Set",
    summaryMomentumTooltipEndGame: "✅ Fin del Game",
  },
  en: {
    summaryChampion:         "CHAMPION",
    summaryWins:             "Wins the Match",
    summaryMatchStats:       "Match Statistics",
    summaryVersus:           "vs",
    /* Sections */
    summarySectionServe:     "Serve",
    summarySectionReturn:    "Return",
    summarySectionPoints:    "Points",
    /* Serve */
    summaryAces:             "Aces",
    summaryDoubleFaults:     "Double Faults",
    summaryFirstServePct:    "1st Serve %",
    summaryPtsOn1st:         "Pts. on 1st Serve %",
    summaryPtsOn2nd:         "Pts. on 2nd Serve %",
    summaryServicePtsWon:    "Service Pts. Won %",
    /* Return */
    summaryReturnPtsWon:     "Return Pts. Won %",
    summaryBreakPoints:      "Break Points",
    summaryBPSaved:          "Break Points Saved",
    /* Points */
    summaryTotalPtsPlayed:   "Points Played",
    summaryTotalPoints:      "Points Won",
    summaryTotalPtsWonPct:   "Points Won %",
    summaryWinners:          "Winners",
    summaryUnforcedErrors:   "Unforced Errors",
    summaryWinnerUERatio:    "Winner / UE Ratio",
    summaryAvgRally:         "Avg. Rally Length",
    summaryMaxRally:         "Longest Rally",
    /* Charts */
    summaryReturnPts:        "Return Points",
    summaryFirstServe:       "1st Serve %",
    summaryPtsOn1stServe:    "Pts. on 1st Serve %",
    summaryPtsOn2ndServe:    "Pts. on 2nd Serve %",
    summaryReturnWon:        "Return Points %",
    summaryRallyChart:       "Rally Length",
    summaryShots:            "shots",
    /* Momentum */
    summaryMomentumChart:    "Match Momentum",
    summaryMomentumP1:       "Momentum",
    summaryMomentumP2:       "Momentum",
    summaryMomentumTooltipSet:    "Set",
    summaryMomentumTooltipGame:   "Game",
    summaryMomentumTooltipPoint:  "Point",
    summaryMomentumTooltipWinner: "Winner",
    summaryMomentumTooltipScore:  "Score",
    summaryMomentumTooltipEndSet: "Set End",
    summaryMomentumTooltipEndGame: "✅ Game End",
  },
};

function _t(key) {
  var lang = "es"; //Siempre en español
  return (SUMMARY_T[lang] && SUMMARY_T[lang][key]) ? SUMMARY_T[lang][key] : key;
}

/* ── Entry point ────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  var result = null;
  try { result = JSON.parse(sessionStorage.getItem("match_result") || "null"); } catch (e) {}

  if (!result || !result.player_stats) {
    var noData  = document.getElementById("no-data-msg");
    var content = document.getElementById("summary-content");
    if (noData)  { noData.classList.remove("hidden"); noData.classList.add("flex"); }
    if (content) { content.classList.add("hidden"); }
    return;
  }

  var p1Name    = (result.players && result.players.P1) || "Jugador 1";
  var p2Name    = (result.players && result.players.P2) || "Jugador 2";
  var winnerId  = result.winner_id  || "P1";
  var winnerName = result.winner_name || (winnerId === "P1" ? p1Name : p2Name);
  var s1        = result.player_stats.P1 || {};
  var s2        = result.player_stats.P2 || {};
  var setScores = result.set_scores || [];

  /* 1. Banner */
  fillWinnerBanner(winnerName, p1Name, p2Name, winnerId, setScores);

  /* 2. Player name headers */
  document.querySelectorAll(".p1-header").forEach(function (el) { el.textContent = p1Name; });
  document.querySelectorAll(".p2-header").forEach(function (el) { el.textContent = p2Name; });

  /* 3. Comparison table */
  buildComparisonRows(s1, s2, result.timeline || []);

  /* 4. Charts */
  buildMomentumChart(result.timeline || [], p1Name, p2Name);
  buildPointsDonut(s1, s2, p1Name, p2Name);
  buildKeyStatsBar(s1, s2, p1Name, p2Name);
  buildServeReturnRadar(s1, s2, p1Name, p2Name);
  buildRallyHistogram(result.timeline || []);

  /* 5. Re-apply i18n so data-i18n on dynamic elements get filled */
  if (typeof setLanguage === "function") {
    setLanguage("es"); //Siempre en espanol
  }

  /* 5b. Set momentum legend names */
  var momLabelP1 = document.getElementById("momentum-p1-label");
  var momLabelP2 = document.getElementById("momentum-p2-label");
  if (momLabelP1) momLabelP1.textContent = p1Name;
  if (momLabelP2) momLabelP2.textContent = p2Name;

  /* 6. Animate bars after a short delay */
  setTimeout(animateBars, 350);

  /* 7. Confetti */
  launchConfetti();
});

/* ══════════════════════════════════════════════════════════════
   1. WINNER BANNER
   ══════════════════════════════════════════════════════════════ */
function fillWinnerBanner(winnerName, p1Name, p2Name, winnerId, setScores) {
  var winEl   = document.getElementById("winner-name-display");
  var vsEl    = document.getElementById("match-vs-title");
  var scoreEl = document.getElementById("set-scores-display");

  if (winEl)  winEl.textContent = winnerName;
  if (vsEl)   vsEl.textContent  = p1Name + " vs " + p2Name;

  if (scoreEl && setScores.length) {
    scoreEl.innerHTML = setScores.map(function (pair, i) {
      var g1 = pair[0], g2 = pair[1];
      var setWinner = g1 > g2 ? "P1" : (g2 > g1 ? "P2" : "");
      var c1 = setWinner === "P1"
        ? "text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.9)]"
        : (setWinner === "P2" ? "text-slate-500" : "text-white");
      var c2 = setWinner === "P2"
        ? "text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.9)]"
        : (setWinner === "P1" ? "text-slate-500" : "text-white");

      return '<div class="set-badge flex flex-col items-center" style="animation-delay:' + (i * 0.18) + 's">' +
               '<span class="text-slate-600 text-[10px] uppercase tracking-widest font-bold mb-1">Set ' + (i + 1) + '</span>' +
               '<div class="flex items-center gap-2 text-4xl md:text-5xl font-black leading-none">' +
                 '<span class="' + c1 + '">' + g1 + '</span>' +
                 '<span class="text-slate-700 text-2xl">–</span>' +
                 '<span class="' + c2 + '">' + g2 + '</span>' +
               '</div>' +
             '</div>';
    }).join('');
  }
}

/* ══════════════════════════════════════════════════════════════
   2. COMPARISON ROWS  (ATP broadcast style)
   ══════════════════════════════════════════════════════════════ */
function buildComparisonRows(s1, s2, timeline) {
  var safeDiv = function (a, b) { return b > 0 ? (a / b) * 100 : 0; };
  var fmt     = function (v) { return Math.round(v || 0); };
  var fmtPct  = function (v) { return (v || 0).toFixed(2) + "%"; };
  var fmtDec  = function (v) { return (v || 0).toFixed(2); };

  var p1SecondIn = (s1.primeros_saques_total || 0) - (s1.primeros_saques_in || 0);
  var p2SecondIn = (s2.primeros_saques_total || 0) - (s2.primeros_saques_in || 0);

  /* Service points won = pts on 1st + pts on 2nd */
  var p1SvcWon = (s1.puntos_ganados_1er_saque || 0) + (s1.puntos_ganados_2do_saque || 0);
  var p2SvcWon = (s2.puntos_ganados_1er_saque || 0) + (s2.puntos_ganados_2do_saque || 0);

  /* Total points played */
  var totalPtsPlayed = (s1.total_puntos_ganados || 0) + (s2.total_puntos_ganados || 0);

  /* Break points saved: opponent's BP opportunities minus opponent's BP converted */
  var p1BPFaced = s2.break_points_oportunidades || 0;
  var p1BPSaved = p1BPFaced - (s2.break_points_convertidos || 0);
  var p2BPFaced = s1.break_points_oportunidades || 0;
  var p2BPSaved = p2BPFaced - (s1.break_points_convertidos || 0);

  /* Rally stats from timeline */
  var rallyLengths = [];
  if (timeline && timeline.length) {
    timeline.forEach(function (pt) {
      var n = (pt.actions && pt.actions.length) ? pt.actions.length : 1;
      rallyLengths.push(n);
    });
  }
  var maxRally = rallyLengths.length > 0
    ? Math.max.apply(null, rallyLengths)
    : 0;
  var avgRally = rallyLengths.length > 0
    ? rallyLengths.reduce(function (a, b) { return a + b; }, 0) / rallyLengths.length
    : 0;

  /* Winner/UE ratio */
  var p1WUE = (s1.errores_no_forzados || 0) > 0
    ? (s1.winners || 0) / s1.errores_no_forzados
    : (s1.winners || 0);
  var p2WUE = (s2.errores_no_forzados || 0) > 0
    ? (s2.winners || 0) / s2.errores_no_forzados
    : (s2.winners || 0);

  /* ── Sections with rows ─────────────────────────────────── */
  var sections = [
    {
      header: "summarySectionServe",
      rows: [
        {
          key: "summaryAces",
          v1: s1.aces || 0,
          v2: s2.aces || 0,
          d1: fmt(s1.aces),
          d2: fmt(s2.aces),
          lowerBetter: false,
        },
        {
          key: "summaryDoubleFaults",
          v1: s1.dobles_faltas || 0,
          v2: s2.dobles_faltas || 0,
          d1: fmt(s1.dobles_faltas),
          d2: fmt(s2.dobles_faltas),
          lowerBetter: true,
        },
        {
          key: "summaryFirstServePct",
          v1: safeDiv(s1.primeros_saques_in, s1.primeros_saques_total),
          v2: safeDiv(s2.primeros_saques_in, s2.primeros_saques_total),
          d1: fmtPct(safeDiv(s1.primeros_saques_in, s1.primeros_saques_total)),
          d2: fmtPct(safeDiv(s2.primeros_saques_in, s2.primeros_saques_total)),
          lowerBetter: false,
        },
        {
          key: "summaryPtsOn1st",
          v1: safeDiv(s1.puntos_ganados_1er_saque, s1.primeros_saques_in),
          v2: safeDiv(s2.puntos_ganados_1er_saque, s2.primeros_saques_in),
          d1: fmtPct(safeDiv(s1.puntos_ganados_1er_saque, s1.primeros_saques_in)),
          d2: fmtPct(safeDiv(s2.puntos_ganados_1er_saque, s2.primeros_saques_in)),
          lowerBetter: false,
        },
        {
          key: "summaryPtsOn2nd",
          v1: safeDiv(s1.puntos_ganados_2do_saque, p1SecondIn),
          v2: safeDiv(s2.puntos_ganados_2do_saque, p2SecondIn),
          d1: fmtPct(safeDiv(s1.puntos_ganados_2do_saque, p1SecondIn)),
          d2: fmtPct(safeDiv(s2.puntos_ganados_2do_saque, p2SecondIn)),
          lowerBetter: false,
        },
        {
          key: "summaryServicePtsWon",
          v1: safeDiv(p1SvcWon, s1.primeros_saques_total),
          v2: safeDiv(p2SvcWon, s2.primeros_saques_total),
          d1: fmtPct(safeDiv(p1SvcWon, s1.primeros_saques_total)),
          d2: fmtPct(safeDiv(p2SvcWon, s2.primeros_saques_total)),
          lowerBetter: false,
        },
      ],
    },
    {
      header: "summarySectionReturn",
      rows: [
        {
          key: "summaryReturnPtsWon",
          v1: safeDiv(s1.puntos_ganados_resto, s2.primeros_saques_total),
          v2: safeDiv(s2.puntos_ganados_resto, s1.primeros_saques_total),
          d1: fmtPct(safeDiv(s1.puntos_ganados_resto, s2.primeros_saques_total)),
          d2: fmtPct(safeDiv(s2.puntos_ganados_resto, s1.primeros_saques_total)),
          lowerBetter: false,
        },
        {
          key: "summaryBreakPoints",
          v1: s1.break_points_convertidos || 0,
          v2: s2.break_points_convertidos || 0,
          d1: (s1.break_points_convertidos || 0) + "/" + (s1.break_points_oportunidades || 0),
          d2: (s2.break_points_convertidos || 0) + "/" + (s2.break_points_oportunidades || 0),
          lowerBetter: false,
        },
        {
          key: "summaryBPSaved",
          v1: p1BPSaved,
          v2: p2BPSaved,
          d1: p1BPSaved + "/" + p1BPFaced,
          d2: p2BPSaved + "/" + p2BPFaced,
          lowerBetter: false,
        },
      ],
    },
    {
      header: "summarySectionPoints",
      rows: [
        {
          key: "summaryTotalPtsPlayed",
          v1: totalPtsPlayed,
          v2: totalPtsPlayed,
          d1: String(totalPtsPlayed),
          d2: String(totalPtsPlayed),
          lowerBetter: false,
          shared: true,
        },
        {
          key: "summaryTotalPoints",
          v1: s1.total_puntos_ganados || 0,
          v2: s2.total_puntos_ganados || 0,
          d1: fmt(s1.total_puntos_ganados),
          d2: fmt(s2.total_puntos_ganados),
          lowerBetter: false,
        },
        {
          key: "summaryTotalPtsWonPct",
          v1: safeDiv(s1.total_puntos_ganados, totalPtsPlayed),
          v2: safeDiv(s2.total_puntos_ganados, totalPtsPlayed),
          d1: fmtPct(safeDiv(s1.total_puntos_ganados, totalPtsPlayed)),
          d2: fmtPct(safeDiv(s2.total_puntos_ganados, totalPtsPlayed)),
          lowerBetter: false,
        },
        {
          key: "summaryWinners",
          v1: s1.winners || 0,
          v2: s2.winners || 0,
          d1: fmt(s1.winners),
          d2: fmt(s2.winners),
          lowerBetter: false,
        },
        {
          key: "summaryUnforcedErrors",
          v1: s1.errores_no_forzados || 0,
          v2: s2.errores_no_forzados || 0,
          d1: fmt(s1.errores_no_forzados),
          d2: fmt(s2.errores_no_forzados),
          lowerBetter: true,
        },
        {
          key: "summaryWinnerUERatio",
          v1: p1WUE,
          v2: p2WUE,
          d1: fmtDec(p1WUE),
          d2: fmtDec(p2WUE),
          lowerBetter: false,
        },
        {
          key: "summaryAvgRally",
          v1: avgRally,
          v2: avgRally,
          d1: fmtDec(avgRally),
          d2: fmtDec(avgRally),
          lowerBetter: false,
          shared: true,
        },
        {
          key: "summaryMaxRally",
          v1: maxRally,
          v2: maxRally,
          d1: String(maxRally),
          d2: String(maxRally),
          lowerBetter: false,
          shared: true,
        },
      ],
    },
  ];

  var container = document.getElementById("comparison-rows");
  if (!container) return;

  var html = "";

  sections.forEach(function (section) {
    /* Section header */
    var headerLabel = _t(section.header);
    html += '<div class="stat-section-header" data-i18n="' + section.header + '">' + headerLabel + '</div>';

    /* Rows */
    html += section.rows.map(function (row) {
      /* For "shared" stats (same value both sides), center the value */
      if (row.shared) {
        var label = _t(row.key);
        return '<div class="stat-row">' +
          '<div class="bar-p1"></div>' +
          '<span class="font-black text-base text-right text-white tabular-nums">' + row.d1 + '</span>' +
          '<span class="text-center text-[0.68rem] font-bold uppercase tracking-wider text-slate-400 leading-tight px-1"' +
                ' data-i18n="' + row.key + '">' + label + '</span>' +
          '<span class="font-black text-base text-left text-white tabular-nums">' + row.d2 + '</span>' +
          '<div class="bar-p2"></div>' +
        '</div>';
      }

      var total    = (row.v1 || 0) + (row.v2 || 0);
      var p1Width  = total > 0 ? Math.round((row.v1 / total) * 100) : 50;
      var p2Width  = total > 0 ? Math.round((row.v2 / total) * 100) : 50;

      var p1Better = row.lowerBetter ? (row.v1 < row.v2) : (row.v1 > row.v2);
      var p2Better = row.lowerBetter ? (row.v2 < row.v1) : (row.v2 > row.v1);
      var equal    = (row.v1 === row.v2);

      var c1     = equal ? "text-white"      : (p1Better ? "text-yellow-400" : "text-slate-400");
      var c2     = equal ? "text-white"      : (p2Better ? "text-yellow-400" : "text-slate-400");
      var grad1  = (p1Better && !equal) ? "bg-gradient-to-l from-yellow-500 to-amber-400"
                                        : "bg-gradient-to-l from-blue-600 to-blue-500";
      var grad2  = (p2Better && !equal) ? "bg-gradient-to-r from-amber-400 to-yellow-500"
                                        : "bg-gradient-to-r from-blue-500 to-blue-600";

      var label  = _t(row.key);

      return '<div class="stat-row">' +
        '<div class="bar-p1 flex items-center justify-end" style="">' +
          '<div class="bar-fill bar-fill-p1 ' + grad1 + '" style="width:0%"' +
               ' data-target="' + p1Width + '%"></div>' +
        '</div>' +
        '<span class="font-black text-base text-right ' + c1 + ' tabular-nums">' + row.d1 + '</span>' +
        '<span class="text-center text-[0.68rem] font-bold uppercase tracking-wider text-slate-400 leading-tight px-1"' +
              ' data-i18n="' + row.key + '">' + label + '</span>' +
        '<span class="font-black text-base text-left ' + c2 + ' tabular-nums">' + row.d2 + '</span>' +
        '<div class="bar-p2">' +
          '<div class="bar-fill bar-fill-p2 ' + grad2 + '" style="width:0%"' +
               ' data-target="' + p2Width + '%"></div>' +
        '</div>' +
      '</div>';
    }).join('');
  });

  container.innerHTML = html;
}

/* ── Animate bar widths ────────────────────────────────────── */
function animateBars() {
  var bars = document.querySelectorAll("[data-target]");
  bars.forEach(function (bar, i) {
    setTimeout(function () {
      bar.style.transition = "width 0.85s cubic-bezier(0.4, 0, 0.2, 1)";
      bar.style.width = bar.getAttribute("data-target");
    }, i * 60);
  });
}

/* ══════════════════════════════════════════════════════════════
   3. CHART: Line – Match Momentum (P1 & P2)
   ══════════════════════════════════════════════════════════════ */
function buildMomentumChart(timeline, p1Name, p2Name) {
  console.log("[Momentum] START – timeline length:", timeline ? timeline.length : "null");
  var canvas = document.getElementById("chart-momentum");
  if (!canvas) { console.error("[Momentum] canvas #chart-momentum NOT FOUND"); return; }
  if (!timeline || !timeline.length) { console.error("[Momentum] timeline empty"); return; }

  var ctx2d = canvas.getContext("2d");
  console.log("[Momentum] Canvas:", canvas.clientWidth, "x", canvas.clientHeight,
              "| Parent:", canvas.parentElement.clientWidth, "x", canvas.parentElement.clientHeight);

  /* ── Build data arrays ──────────────────────────────────── */
  var labels       = [];
  var dataP1       = [];
  var dataP2       = [];
  var pointMeta    = [];
  var setBoundaries = [];

  var hasBackendMomentum = timeline.some(function (pt) {
    return typeof pt.momentum_p1 === "number" && pt.momentum_p1 !== 0;
  });
  console.log("[Momentum] Backend momentum:", hasBackendMomentum);

  /* Fallback state */
  var fMom1 = 0, fMom2 = 0, fStreak1 = 0, fStreak2 = 0;

  for (var i = 0; i < timeline.length; i++) {
    var pt = timeline[i];
    labels.push(i + 1);

    if (hasBackendMomentum) {
      var m1 = (typeof pt.momentum_p1 === "number") ? pt.momentum_p1 : 0;
      var m2 = (typeof pt.momentum_p2 === "number") ? pt.momentum_p2 : 0;
      dataP1.push(Math.round(m1 * 10) / 10);
      dataP2.push(Math.round(m2 * 10) / 10);
    } else {
      var w = pt.winner || "";
      if (w === "P1") {
        fStreak1 = Math.max(1, fStreak1 + 1);
        fStreak2 = Math.min(-1, fStreak2 - 1);
        fMom1 = Math.min(50, fMom1 + 2 * Math.abs(fStreak1));
        fMom2 = Math.max(-50, fMom2 - 2 * Math.abs(fStreak2));
      } else if (w === "P2") {
        fStreak2 = Math.max(1, fStreak2 + 1);
        fStreak1 = Math.min(-1, fStreak1 - 1);
        fMom2 = Math.min(50, fMom2 + 2 * Math.abs(fStreak2));
        fMom1 = Math.max(-50, fMom1 - 2 * Math.abs(fStreak1));
      }
      fMom1 *= 0.97;
      fMom2 *= 0.97;
      if (pt.game_end) {
        if (w === "P1") { fMom1 = Math.min(50, fMom1 + 8); fMom2 = Math.max(-50, fMom2 - 8); }
        else if (w === "P2") { fMom2 = Math.min(50, fMom2 + 8); fMom1 = Math.max(-50, fMom1 - 8); }
      }
      if (pt.set_end) {
        if (w === "P1") { fMom1 = Math.min(50, fMom1 + 15); fMom2 = Math.max(-50, fMom2 - 15); }
        else if (w === "P2") { fMom2 = Math.min(50, fMom2 + 15); fMom1 = Math.max(-50, fMom1 - 15); }
      }
      dataP1.push(Math.round(fMom1 * 10) / 10);
      dataP2.push(Math.round(fMom2 * 10) / 10);
    }

    /* Score label for tooltip */
    var scoreLabel = "";
    var sa = pt.score_after || {};
    if (sa.set_games) {
      scoreLabel = (sa.set_games.P1 || 0) + "\u2013" + (sa.set_games.P2 || 0);
    }
    var pointScore = "";
    if (sa.tiebreak_score) {
      pointScore = "TB " + sa.tiebreak_score.P1 + "\u2013" + sa.tiebreak_score.P2;
    } else if (sa.server_points !== undefined) {
      var sp = sa.server_points, rp = sa.returner_points;
      if (pt.server_id === "P1") pointScore = sp + "\u2013" + rp;
      else pointScore = rp + "\u2013" + sp;
    }

    pointMeta.push({
      set: pt.set,
      game: pt.game,
      winner: pt.winner_name || pt.winner,
      reason: pt.reason,
      gameScore: scoreLabel,
      pointScore: pointScore,
      gameEnd: pt.game_end,
      setEnd: pt.set_end,
      isTiebreak: pt.is_tiebreak
    });

    if (pt.set_end) setBoundaries.push(i);
  }

  /* ── Debug summary ───────────────────────────────────────── */
  var p1Min = Math.min.apply(null, dataP1), p1Max = Math.max.apply(null, dataP1);
  var p2Min = Math.min.apply(null, dataP2), p2Max = Math.max.apply(null, dataP2);
  console.log("[Momentum] P1 [" + p1Min + " .. " + p1Max + "]  P2 [" + p2Min + " .. " + p2Max + "]");

  /* ── Y axis range ────────────────────────────────────────── */
  var absMax = Math.max(Math.abs(p1Min), Math.abs(p1Max), Math.abs(p2Min), Math.abs(p2Max), 10);
  var yLimit = Math.ceil(absMax / 5) * 5 + 5;

  /* ── Create chart ────────────────────────────────────────── */
  try {
    new Chart(ctx2d, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: p1Name,
            data: dataP1,
            borderColor: "#fbbf24",
            backgroundColor: "rgba(250,204,21,0.10)",
            borderWidth: 2.5,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "#fbbf24",
            pointHoverBorderColor: "#fff",
            pointHoverBorderWidth: 2,
            tension: 0.35,
            fill: "origin"
          },
          {
            label: p2Name,
            data: dataP2,
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59,130,246,0.10)",
            borderWidth: 2.5,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "#3b82f6",
            pointHoverBorderColor: "#fff",
            pointHoverBorderWidth: 2,
            tension: 0.35,
            fill: "origin"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(2,6,23,0.92)",
            titleColor: "#f8fafc",
            bodyColor: "#cbd5e1",
            borderColor: "rgba(250,204,21,0.3)",
            borderWidth: 1,
            cornerRadius: 10,
            padding: 12,
            titleFont: { size: 13, weight: "bold" },
            bodyFont: { size: 11 },
            displayColors: true,
            boxWidth: 10,
            boxHeight: 10,
            callbacks: {
              title: function (items) {
                if (!items.length) return "";
                var idx = items[0].dataIndex;
                var m = pointMeta[idx];
                if (!m) return _t("summaryMomentumTooltipPoint") + " #" + (idx + 1);
                return _t("summaryMomentumTooltipSet") + " " + m.set +
                       "  |  " + _t("summaryMomentumTooltipGame") + " " + m.game +
                       "  |  " + _t("summaryMomentumTooltipPoint") + " " + (idx + 1);
              },
              afterTitle: function (items) {
                if (!items.length) return "";
                var idx = items[0].dataIndex;
                var m = pointMeta[idx];
                if (!m) return "";
                var parts = [];
                if (m.gameScore) parts.push(_t("summaryMomentumTooltipScore") + ": " + m.gameScore +
                                            (m.pointScore ? "  (" + m.pointScore + ")" : ""));
                if (m.winner) parts.push(_t("summaryMomentumTooltipWinner") + ": " + m.winner);
                if (m.setEnd) parts.push(_t("summaryMomentumTooltipEndSet"));
                else if (m.gameEnd) parts.push(_t("summaryMomentumTooltipEndGame"));
                return parts.join("\n");
              },
              label: function (tipItem) {
                var lbl = tipItem.dataset.label || "";
                var val = tipItem.parsed.y;
                return "  " + lbl + ": " + (val >= 0 ? "+" : "") + val.toFixed(1);
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            ticks: {
              color: "#475569",
              font: { size: 9 },
              maxTicksLimit: 20,
              callback: function (value, index) {
                var m = pointMeta[index];
                if (m && (m.gameEnd || index === 0)) return index + 1;
                return "";
              }
            },
            grid: { color: "rgba(255,255,255,0.02)" },
            title: {
              display: true,
              text: _t("summaryMomentumTooltipPoint"),
              color: "#475569",
              font: { size: 10, weight: "bold" }
            }
          },
          y: {
            min: -yLimit,
            max: yLimit,
            ticks: {
              color: "#475569",
              font: { size: 9 },
              stepSize: 10,
              callback: function (val) {
                if (val === 0) return "0";
                return (val > 0 ? "+" : "") + val;
              }
            },
            grid: { color: "rgba(255,255,255,0.04)" },
            title: {
              display: true,
              text: "Momentum",
              color: "#475569",
              font: { size: 10, weight: "bold" }
            }
          }
        },
        animation: { duration: 2000, easing: "easeOutQuart" }
      },
      plugins: [
        /* Zero line */
        {
          id: "momentumZeroLine",
          afterDraw: function (chart) {
            var yA = chart.scales.y, xA = chart.scales.x;
            if (!yA || !xA) return;
            var y0 = yA.getPixelForValue(0);
            var c = chart.ctx;
            c.save();
            c.beginPath();
            c.strokeStyle = "rgba(148,163,184,0.22)";
            c.lineWidth = 1;
            c.setLineDash([4, 4]);
            c.moveTo(xA.left, y0);
            c.lineTo(xA.right, y0);
            c.stroke();
            c.restore();
          }
        },
        /* Set boundaries */
        {
          id: "momentumSetBounds",
          afterDraw: function (chart) {
            var xA = chart.scales.x, yA = chart.scales.y;
            if (!xA || !yA) return;
            var c = chart.ctx;
            setBoundaries.forEach(function (idx) {
              if (idx >= timeline.length - 1) return;
              var x = xA.getPixelForValue(idx);
              c.save();
              c.beginPath();
              c.setLineDash([6, 4]);
              c.strokeStyle = "rgba(250,204,21,0.35)";
              c.lineWidth = 1.5;
              c.moveTo(x, yA.top);
              c.lineTo(x, yA.bottom);
              c.stroke();
              c.fillStyle = "rgba(250,204,21,0.55)";
              c.font = "bold 9px system-ui";
              c.textAlign = "center";
              c.fillText("Set " + (pointMeta[idx] ? pointMeta[idx].set : ""), x, yA.top + 12);
              c.restore();
            });
          }
        }
      ]
    });
    console.log("[Momentum] Chart created OK");
  } catch (err) {
    console.error("[Momentum] Chart FAILED:", err);
  }
}

/* ══════════════════════════════════════════════════════════════
   4. CHART: Doughnut – Points distribution
   ══════════════════════════════════════════════════════════════ */
function buildPointsDonut(s1, s2, p1Name, p2Name) {
  var canvas = document.getElementById("chart-points");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");
  var v1  = s1.total_puntos_ganados || 0;
  var v2  = s2.total_puntos_ganados || 0;
  var tot = v1 + v2 || 1;

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: [p1Name, p2Name],
      datasets: [{
        data: [v1, v2],
        backgroundColor: ["rgba(250,204,21,0.88)", "rgba(59,130,246,0.88)"],
        borderColor:     ["#fbbf24", "#2563eb"],
        borderWidth: 2,
        hoverOffset: 14,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#94a3b8", font: { size: 11, family: "system-ui" }, padding: 14 },
        },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return "  " + ctx.label + ": " + ctx.raw + " pts (" + (ctx.raw / tot * 100).toFixed(2) + "%)";
            },
          },
        },
      },
      animation: { animateRotate: true, duration: 1300 },
    },
  });
}

/* ══════════════════════════════════════════════════════════════
   5. CHART: Grouped bar – Aces / DF / Winners / UE
   ══════════════════════════════════════════════════════════════ */
function buildKeyStatsBar(s1, s2, p1Name, p2Name) {
  var canvas = document.getElementById("chart-keystats");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");

  var labels = [
    _t("summaryAces"),
    _t("summaryDoubleFaults"),
    _t("summaryWinners"),
    _t("summaryUnforcedErrors"),
  ];

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: p1Name,
          data: [s1.aces||0, s1.dobles_faltas||0, s1.winners||0, s1.errores_no_forzados||0],
          backgroundColor: "rgba(250,204,21,0.82)",
          borderColor:     "#fbbf24",
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false,
        },
        {
          label: p2Name,
          data: [s2.aces||0, s2.dobles_faltas||0, s2.winners||0, s2.errores_no_forzados||0],
          backgroundColor: "rgba(59,130,246,0.82)",
          borderColor:     "#3b82f6",
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#94a3b8", font: { size: 11 }, padding: 12 },
        },
        tooltip: { mode: "index", intersect: false },
      },
      scales: {
        x: {
          ticks: { color: "#64748b", font: { size: 11 } },
          grid:  { color: "rgba(255,255,255,0.04)" },
        },
        y: {
          ticks: { color: "#64748b", stepSize: 1, font: { size: 10 } },
          grid:  { color: "rgba(255,255,255,0.04)" },
          beginAtZero: true,
        },
      },
      animation: { duration: 1200 },
    },
  });
}

/* ══════════════════════════════════════════════════════════════
   6. CHART: Radar – Serve & Return
   ══════════════════════════════════════════════════════════════ */
function buildServeReturnRadar(s1, s2, p1Name, p2Name) {
  var canvas = document.getElementById("chart-serve-return");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");

  var safeDiv = function (a, b) { return b > 0 ? Math.round((a / b) * 100) : 0; };
  var p1Sec   = (s1.primeros_saques_total || 0) - (s1.primeros_saques_in || 0);
  var p2Sec   = (s2.primeros_saques_total || 0) - (s2.primeros_saques_in || 0);
  var p2Total = s2.primeros_saques_total || 1;
  var p1Total = s1.primeros_saques_total || 1;

  var labels = [
    _t("summaryFirstServe"),
    _t("summaryPtsOn1stServe"),
    _t("summaryPtsOn2ndServe"),
    _t("summaryReturnWon"),
  ];

  new Chart(ctx, {
    type: "radar",
    data: {
      labels: labels,
      datasets: [
        {
          label: p1Name,
          data: [
            safeDiv(s1.primeros_saques_in, p1Total),
            safeDiv(s1.puntos_ganados_1er_saque, s1.primeros_saques_in),
            safeDiv(s1.puntos_ganados_2do_saque, p1Sec),
            safeDiv(s1.puntos_ganados_resto, p2Total),
          ],
          backgroundColor:    "rgba(250,204,21,0.16)",
          borderColor:        "#fbbf24",
          borderWidth: 2,
          pointBackgroundColor: "#fbbf24",
          pointBorderColor:     "rgba(250,204,21,0.5)",
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: p2Name,
          data: [
            safeDiv(s2.primeros_saques_in, p2Total),
            safeDiv(s2.puntos_ganados_1er_saque, s2.primeros_saques_in),
            safeDiv(s2.puntos_ganados_2do_saque, p2Sec),
            safeDiv(s2.puntos_ganados_resto, p1Total),
          ],
          backgroundColor:    "rgba(59,130,246,0.16)",
          borderColor:        "#3b82f6",
          borderWidth: 2,
          pointBackgroundColor: "#3b82f6",
          pointBorderColor:     "rgba(59,130,246,0.5)",
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#94a3b8", font: { size: 11 }, padding: 10 },
        },
      },
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: {
            color: "#475569",
            stepSize: 25,
            backdropColor: "transparent",
            font: { size: 9 },
          },
          grid:       { color: "rgba(255,255,255,0.07)" },
          angleLines: { color: "rgba(255,255,255,0.07)" },
          pointLabels: {
            color: "#94a3b8",
            font: { size: 10, weight: "600" },
          },
        },
      },
      animation: { duration: 1200 },
    },
  });
}

/* ══════════════════════════════════════════════════════════════
   7. CHART: Bar – Rally length histogram
   ══════════════════════════════════════════════════════════════ */
function buildRallyHistogram(timeline) {
  var canvas = document.getElementById("chart-rally");
  if (!canvas || !timeline.length) return;
  var ctx = canvas.getContext("2d");

  var shots = _t("summaryShots");
  var bucketKeys   = ["1", "2–3", "4–6", "7–10", "11+"];
  var bucketValues = [0, 0, 0, 0, 0];

  timeline.forEach(function (pt) {
    var n = (pt.actions && pt.actions.length) ? pt.actions.length : 1;
    if      (n <= 1)  bucketValues[0]++;
    else if (n <= 3)  bucketValues[1]++;
    else if (n <= 6)  bucketValues[2]++;
    else if (n <= 10) bucketValues[3]++;
    else              bucketValues[4]++;
  });

  var colors = [
    "rgba(250,204,21,0.85)",
    "rgba(251,191,36,0.85)",
    "rgba(245,158,11,0.85)",
    "rgba(59,130,246,0.85)",
    "rgba(37,99,235,0.85)",
  ];

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: bucketKeys.map(function (k) { return k + " " + shots; }),
      datasets: [{
        label: _t("summaryRallyChart"),
        data: bucketValues,
        backgroundColor: colors,
        borderColor:     "rgba(255,255,255,0.06)",
        borderWidth: 1,
        borderRadius: 8,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { color: "#64748b", font: { size: 11 } },
          grid:  { color: "rgba(255,255,255,0.04)" },
        },
        y: {
          ticks: { color: "#64748b", stepSize: 1, font: { size: 10 } },
          grid:  { color: "rgba(255,255,255,0.04)" },
          beginAtZero: true,
        },
      },
      animation: { duration: 1200 },
    },
  });
}

/* ══════════════════════════════════════════════════════════════
   8.  CONFETTI
   ══════════════════════════════════════════════════════════════ */
function launchConfetti() {
  var container = document.getElementById("confetti-container");
  if (!container) return;

  var colors = [
    "#fbbf24", "#f59e0b", "#fde68a",
    "#3b82f6", "#60a5fa", "#93c5fd",
    "#10b981", "#f472b6", "#a78bfa", "#34d399",
  ];

  var fragment = document.createDocumentFragment();
  for (var i = 0; i < 100; i++) {
    var el     = document.createElement("div");
    var color  = colors[Math.floor(Math.random() * colors.length)];
    var size   = Math.random() * 11 + 5;
    var isRect = Math.random() > 0.42;
    var delay  = Math.random() * 1.8;
    var dur    = 1.6 + Math.random() * 2.4;

    el.style.cssText =
      "position:absolute;" +
      "left:" + (Math.random() * 100) + "%;" +
      "top:-22px;" +
      "width:" + size + "px;" +
      "height:" + (isRect ? size * 0.42 : size) + "px;" +
      "background:" + color + ";" +
      "border-radius:" + (isRect ? "3px" : "50%") + ";" +
      "animation:confetti-fall " + dur + "s ease-in " + delay + "s both;" +
      "opacity:0.92;" +
      "transform:rotate(" + Math.floor(Math.random() * 360) + "deg);";

    fragment.appendChild(el);
  }
  container.appendChild(fragment);

  setTimeout(function () {
    if (container) container.innerHTML = "";
  }, 8000);
}
