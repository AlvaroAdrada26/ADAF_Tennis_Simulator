/**
 * static/js/estrategico/match.js
 * Lógica principal del partido en Modo Estratégico.
 * Gestiona la comunicación con la API, el marcador, la estrategia y los indicadores.
 */

(function () {
  'use strict';

  // ── Session data ────────────────────────────────────────
  const sessionId = sessionStorage.getItem('estrategico_session_id');
  const config = JSON.parse(sessionStorage.getItem('estrategico_config') || '{}');
  if (!sessionId) { window.location.href = '/modo-estrategico'; return; }

  const numSets = parseInt(config.best_of, 10) || 3;
  const coachedPlayer = config.coached_player || 'P1';
  const playerNames = { P1: config.player1_name || 'Jugador 1', P2: config.player2_name || 'Jugador 2' };

  // ── State ───────────────────────────────────────────────
  let currentStrategy = 'neutral';
  let pointIndex = 0;
  let matchFinished = false;
  let streak = { player: null, count: 0 };

  // ── Autoplay state ─────────────────────────────────────
  let autoplayTimer = null;
  let isAutoPlaying = false;
  let speedFactor = 1;
  const BASE_SPEED_MS = 1200;
  const PLAY_PATH = '<path stroke-linecap="round" stroke-linejoin="round" d="M8 5v14l11-7z"/>';
  const PAUSE_PATH = '<path stroke-linecap="round" stroke-linejoin="round" d="M6 4h4v16H6zM14 4h4v16h-4z"/>';

  // ── DOM refs ────────────────────────────────────────────
  const btnPlay = document.getElementById('btn-play-point');
  const btnAutoFinish = document.getElementById('btn-auto-finish');
  const btnAutoplay = document.getElementById('btn-autoplay');
  const pointCounter = document.getElementById('point-counter');
  const stratBadge = document.getElementById('strategy-badge');
  const coachedNameEl = document.getElementById('coached-name');
  const streakDisplay = document.getElementById('streak-display');
  const pointsList = document.getElementById('points-list');
  const lastPointCard = document.getElementById('last-point-card');
  const lastPointContent = document.getElementById('last-point-content');
  const postMatchBar = document.getElementById('post-match-bar');
  const finalWinnerText = document.getElementById('final-winner-text');
  const finalScoreText = document.getElementById('final-score-text');

  // ── Reason labels ───────────────────────────────────────
  const REASON_LABELS = {
    ace:         'Ace',
    doble_falta: 'Doble falta',
    error_resto: 'Error al resto',
    error_golpe: 'Error de golpe',
    no_llega:    'No llega',
    max_rally:   'Final de rally',
  };
  function reasonLabel(reason) {
    return REASON_LABELS[reason] || reason;
  }

  // ── Helpers ─────────────────────────────────────────────
  function getToken() { return localStorage.getItem('access_token') || ''; }

  function showToast(msg, isErr) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'fixed bottom-8 left-1/2 -translate-x-1/2 z-50 px-8 py-4 rounded-xl text-white font-semibold text-lg shadow-2xl toast-show ' +
      (isErr ? 'bg-red-600' : 'bg-green-600');
    setTimeout(function () { t.classList.remove('toast-show'); t.classList.add('toast-hide'); }, 2500);
    setTimeout(function () { t.classList.add('hidden'); }, 3000);
  }

  // ── Init: set player names ──────────────────────────────
  function initUI() {
    document.getElementById('player1-name').textContent = playerNames.P1;
    document.getElementById('player2-name').textContent = playerNames.P2;
    coachedNameEl.textContent = playerNames[coachedPlayer];

    // Indicator names
    document.getElementById('stam-p1-name').textContent = playerNames.P1;
    document.getElementById('stam-p2-name').textContent = playerNames.P2;
    document.getElementById('mom-p1-name').textContent = playerNames.P1;
    document.getElementById('mom-p2-name').textContent = playerNames.P2;
  }

  // ── Scoreboard update ──────────────────────────────────
  function updateScoreboard(score) {
    // Points
    const p1Pts = document.getElementById('p1-points');
    const p2Pts = document.getElementById('p2-points');
    if (p1Pts) p1Pts.textContent = score.points.P1 || '0';
    if (p2Pts) p2Pts.textContent = score.points.P2 || '0';

    // Games in current set
    for (let s = 1; s <= numSets; s++) {
      const p1Cell = document.getElementById('p1-set' + s);
      const p2Cell = document.getElementById('p2-set' + s);
      if (s < score.current_set && score.set_scores[s - 1]) {
        // Finished set
        if (p1Cell) {
          p1Cell.textContent = score.set_scores[s - 1][0];
          p1Cell.className = score.set_scores[s - 1][0] > score.set_scores[s - 1][1] ? 'text-4xl font-bold set-winner' : 'text-4xl font-bold set-loser';
        }
        if (p2Cell) {
          p2Cell.textContent = score.set_scores[s - 1][1];
          p2Cell.className = score.set_scores[s - 1][1] > score.set_scores[s - 1][0] ? 'text-4xl font-bold set-winner' : 'text-4xl font-bold set-loser';
        }
      } else if (s === score.current_set) {
        if (p1Cell) { p1Cell.textContent = score.games.P1; p1Cell.className = 'text-4xl font-bold set-in-game'; }
        if (p2Cell) { p2Cell.textContent = score.games.P2; p2Cell.className = 'text-4xl font-bold set-in-game'; }
      } else {
        if (p1Cell) { p1Cell.textContent = ' '; p1Cell.className = 'text-4xl font-bold'; }
        if (p2Cell) { p2Cell.textContent = ' '; p2Cell.className = 'text-4xl font-bold'; }
      }
    }

    // Serve indicator
    const serveP1 = document.getElementById('serve-p1');
    const serveP2 = document.getElementById('serve-p2');
    if (serveP1) serveP1.className = 'serve-ball' + (score.server_id === 'P1' ? '' : ' off');
    if (serveP2) serveP2.className = 'serve-ball' + (score.server_id === 'P2' ? '' : ' off');

    // Leading player color
    const n1 = document.getElementById('player1-name');
    const n2 = document.getElementById('player2-name');
    if (n1 && n2) {
      const s1 = score.sets.P1, s2 = score.sets.P2;
      if (s1 > s2) {
        n1.className = 'player-leading'; n2.className = 'player-trailing';
      } else if (s2 > s1) {
        n2.className = 'player-leading'; n1.className = 'player-trailing';
      } else {
        n1.className = ''; n2.className = '';
      }
    }
  }

  // ── Indicators update ──────────────────────────────────
  function updateIndicators(data) {
    // Stamina (0-100 scale)
    const s1 = data.stamina_p1 != null ? data.stamina_p1 : 100;
    const s2 = data.stamina_p2 != null ? data.stamina_p2 : 100;
    document.getElementById('stam-p1-val').textContent = Math.round(s1) + '%';
    document.getElementById('stam-p2-val').textContent = Math.round(s2) + '%';
    document.getElementById('stam-p1-bar').style.width = Math.max(0, Math.min(100, s1)) + '%';
    document.getElementById('stam-p2-bar').style.width = Math.max(0, Math.min(100, s2)) + '%';

    // Momentum (can be negative or positive; map to 0-100 for bar)
    const m1 = data.momentum_p1 != null ? data.momentum_p1 : 0;
    const m2 = data.momentum_p2 != null ? data.momentum_p2 : 0;
    document.getElementById('mom-p1-val').textContent = (m1 >= 0 ? '+' : '') + m1.toFixed(1);
    document.getElementById('mom-p2-val').textContent = (m2 >= 0 ? '+' : '') + m2.toFixed(1);

    // Map momentum to a 0-100 bar (clamp ±50 → 0-100%)
    const momBar1 = Math.max(0, Math.min(100, (m1 + 50) / 100 * 100));
    const momBar2 = Math.max(0, Math.min(100, (m2 + 50) / 100 * 100));
    const bar1 = document.getElementById('mom-p1-bar');
    const bar2 = document.getElementById('mom-p2-bar');
    bar1.style.width = momBar1 + '%';
    bar2.style.width = momBar2 + '%';
    bar1.className = 'bar-fill h-full rounded-full ' + (m1 >= 0 ? 'bg-blue-500' : 'bg-red-500');
    bar2.className = 'bar-fill h-full rounded-full ' + (m2 >= 0 ? 'bg-amber-500' : 'bg-red-500');
  }

  // ── Streak ──────────────────────────────────────────────
  function updateStreak(winnerId) {
    if (winnerId === streak.player) {
      streak.count++;
    } else {
      streak.player = winnerId;
      streak.count = 1;
    }
    const name = playerNames[winnerId] || winnerId;
    if (streak.count >= 2) {
      streakDisplay.innerHTML = '<span class="flex items-center gap-1">' + name.split(' ')[0] + ' x' + streak.count + ' <svg class="w-5 h-5 text-yellow-400 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/></svg></span>';
      streakDisplay.className = 'text-lg font-bold text-yellow-400';
    } else {
      streakDisplay.textContent = '—';
      streakDisplay.className = 'text-lg font-bold text-gray-500';
    }
  }

  // ── Last point card ────────────────────────────────────
  function showLastPoint(pointData) {
    lastPointCard.classList.remove('hidden');
    lastPointCard.classList.add('bounce-in');

    const winnerName = pointData.winner_name || playerNames[pointData.winner] || pointData.winner;
    const reason = pointData.reason || '';
    const serverName = playerNames[pointData.server_id] || pointData.server_id || '';
    const isBreak = pointData.is_break_point;
    const isTB = pointData.is_tiebreak;
    const rallyShots = pointData.stats ? pointData.stats.rally_shots : 0;

    let html = '';
    html += '<div class="flex items-center gap-2">';
    html += '<span class="text-yellow-400 font-bold"><svg class="w-4 h-4 inline-block align-middle mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><circle cx="12" cy="12" r="10"/><path stroke-linecap="round" stroke-linejoin="round" d="M2 12c2.5 3 5 4.5 10 4.5S19.5 15 22 12M2 12c2.5-3 5-4.5 10-4.5S19.5 9 22 12"/></svg>' + winnerName + '</span>';
    html += '<span class="text-gray-500">gana el punto</span>';
    html += '</div>';
    if (reason) html += '<p class="text-gray-400 text-xs">Razón: ' + reasonLabel(reason) + '</p>';
    if (serverName) html += '<p class="text-gray-500 text-xs">Saque: ' + serverName + '</p>';
    if (rallyShots) html += '<p class="text-gray-500 text-xs">Rally: ' + rallyShots + ' golpes</p>';

    const badges = [];
    if (isTB) badges.push('<span class="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">Tie-Break</span>');
    if (isBreak) badges.push('<span class="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">Break Point</span>');
    if (pointData.game_end) badges.push('<span class="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/30">Fin de Game</span>');
    if (pointData.set_end) badges.push('<span class="text-xs px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">Fin de Set</span>');
    if (badges.length) html += '<div class="flex gap-2 mt-1 flex-wrap">' + badges.join('') + '</div>';

    lastPointContent.innerHTML = html;

    setTimeout(function() { lastPointCard.classList.remove('bounce-in'); }, 500);
  }

  // ── Points feed ────────────────────────────────────────
  function addToFeed(pointData, idx) {
    const winnerName = pointData.winner_name || playerNames[pointData.winner] || pointData.winner;
    const li = document.createElement('li');
    const isCoached = pointData.winner === coachedPlayer;
    const color = isCoached ? 'text-green-400' : 'text-red-400';
    const icon = isCoached ? '\u2713' : '\u2717';

    let scoreText = '';
    if (pointData.score_after) {
      const sa = pointData.score_after;
      scoreText = ' [' + sa.server_points + '-' + sa.returner_points + ']';
      if (sa.games) {
        scoreText = ' (' + (sa.games.P1 || 0) + '-' + (sa.games.P2 || 0) + ')' + scoreText;
      }
      if (sa.set_scores && sa.set_scores.length) {
        const setStr = sa.set_scores.map(function(s) { return s[0] + '-' + s[1]; }).join(', ');
        scoreText = ' {' + setStr + '}' + scoreText;
      }
    }

    li.className = 'py-1 px-2 rounded ' + (idx % 2 === 0 ? 'bg-slate-800/30' : '');
    li.innerHTML = '<span class="text-gray-500 text-xs mr-2">#' + (idx + 1) + '</span>' +
      '<span class="' + color + ' font-medium">' + icon + ' ' + winnerName + '</span>' +
      '<span class="text-gray-500 text-xs ml-1">' + reasonLabel(pointData.reason || '') + '</span>' +
      '<span class="text-gray-600 text-xs ml-1">' + scoreText + '</span>';

    pointsList.prepend(li);
  }

  // ── Strategy cards ─────────────────────────────────────
  document.querySelectorAll('#strat-cards .strat-card').forEach(function (card) {
    card.addEventListener('click', function () {
      if (matchFinished) return;
      currentStrategy = card.dataset.val;
      document.querySelectorAll('#strat-cards .strat-card').forEach(function (c) { c.classList.remove('active'); });
      card.classList.add('active');
      updateStrategyBadge();

      // Also notify backend
      fetch('/api/estrategico/set-strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getToken() },
        body: JSON.stringify({ session_id: sessionId, strategy: currentStrategy })
      }).catch(function () {});
    });
  });

  function updateStrategyBadge() {
    const labels = { aggressive: 'agresiva', neutral: 'neutral', defensive: 'defensiva' };
    const colors = { aggressive: 'bg-red-500/20 text-red-400 border-red-500/30', neutral: 'bg-blue-500/20 text-blue-400 border-blue-500/30', defensive: 'bg-green-500/20 text-green-400 border-green-500/30' };
    stratBadge.textContent = labels[currentStrategy] || currentStrategy;
    stratBadge.className = 'text-xs font-mono px-3 py-1 rounded-full border ' + (colors[currentStrategy] || colors.neutral);
  }

  // ── Autoplay helpers ────────────────────────────────────
  function setAutoplayIcon(playing) {
    var icon = document.getElementById('icon-autoplay');
    if (icon) icon.innerHTML = playing ? PAUSE_PATH : PLAY_PATH;
  }

  function stopAutoplay() {
    if (autoplayTimer) { clearTimeout(autoplayTimer); autoplayTimer = null; }
    isAutoPlaying = false;
    setAutoplayIcon(false);
    if (!matchFinished) {
      btnPlay.disabled = false;
    }
  }

  async function playOnePoint() {
    var res = await fetch('/api/estrategico/next-point', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getToken() },
      body: JSON.stringify({ session_id: sessionId, strategy: currentStrategy })
    });

    if (!res.ok) {
      var err = await res.json().catch(function () { return {}; });
      showToast(err.detail || 'Error al jugar punto', true);
      return null;
    }

    return await res.json();
  }

  function handlePointData(data) {
    pointIndex = data.point_index + 1;
    updateScoreboard(data.score);
    updateIndicators(data);
    showLastPoint(data.point);
    addToFeed(data.point, data.point_index);
    updateStreak(data.point.winner);
    pointCounter.textContent = 'Punto ' + pointIndex;

    if (data.match_finished) {
      handleMatchEnd(data.winner, data.score);
      return true;
    }
    if (pointIndex >= 10) btnAutoFinish.classList.remove('hidden');
    return false;
  }

  async function autoplayLoop() {
    if (!isAutoPlaying || matchFinished) {
      stopAutoplay();
      return;
    }
    try {
      var data = await playOnePoint();
      if (!data) { stopAutoplay(); return; }
      var ended = handlePointData(data);
      if (ended) { stopAutoplay(); return; }
    } catch (_err) {
      showToast('Error de conexión', true);
      stopAutoplay();
      return;
    }
    if (isAutoPlaying && !matchFinished) {
      autoplayTimer = setTimeout(function () { autoplayLoop(); }, BASE_SPEED_MS / speedFactor);
    }
  }

  // ── Autoplay button ───────────────────────────────────
  if (btnAutoplay) {
    btnAutoplay.addEventListener('click', function () {
      if (matchFinished) return;
      if (isAutoPlaying) {
        stopAutoplay();
      } else {
        isAutoPlaying = true;
        setAutoplayIcon(true);
        btnPlay.disabled = true;
        autoplayLoop();
      }
    });
  }

  // ── Speed buttons ─────────────────────────────────────
  document.querySelectorAll('.coach-speed-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.coach-speed-btn').forEach(function (b) {
        b.classList.remove('bg-yellow-400', 'text-slate-900');
        b.classList.add('text-yellow-300');
      });
      btn.classList.add('bg-yellow-400', 'text-slate-900');
      btn.classList.remove('text-yellow-300');
      speedFactor = parseInt(btn.dataset.speed, 10) || 1;
    });
  });

  // ── Play point ─────────────────────────────────────────
  btnPlay.addEventListener('click', async function () {
    if (matchFinished || isAutoPlaying) return;
    btnPlay.disabled = true;

    try {
      var data = await playOnePoint();
      if (!data) return;
      handlePointData(data);
    } catch (_err) {
      showToast('Error de conexión', true);
    } finally {
      if (!matchFinished) {
        btnPlay.disabled = false;
      }
    }
  });

  // ── Auto finish ────────────────────────────────────────
  btnAutoFinish.addEventListener('click', async function () {
    if (matchFinished) return;
    stopAutoplay();
    btnAutoFinish.disabled = true;
    btnAutoFinish.textContent = 'Simulando...';
    btnPlay.disabled = true;

    try {
      const res = await fetch('/api/estrategico/end', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getToken() },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (!res.ok) {
        const err = await res.json().catch(function () { return {}; });
        showToast(err.detail || 'Error al simular', true);
        return;
      }

      const data = await res.json();
      updateScoreboard(data.score);
      handleMatchEnd(data.winner, data.score);

    } catch (_err) {
      showToast('Error de conexión', true);
    }
  });

  // ── Match end ──────────────────────────────────────────
  function handleMatchEnd(winner, score) {
    matchFinished = true;
    stopAutoplay();
    btnPlay.disabled = true;
    btnPlay.classList.add('opacity-50');
    btnAutoFinish.classList.add('hidden');
    if (btnAutoplay) { btnAutoplay.disabled = true; btnAutoplay.classList.add('opacity-50'); }

    const winnerName = playerNames[winner] || winner;
    finalWinnerText.innerHTML = '<svg class="w-8 h-8 inline-block align-middle mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>' + winnerName + ' gana el partido';

    // Format score
    if (score && score.set_scores) {
      const setsStr = score.set_scores.map(function (s) { return s[0] + '-' + s[1]; }).join(', ');
      finalScoreText.textContent = setsStr;
    }

    // Winner glow on scoreboard
    const winRow = document.getElementById(winner === 'P1' ? 'player1-name' : 'player2-name');
    if (winRow) winRow.classList.add('winner-glow');

    postMatchBar.classList.remove('hidden');
    postMatchBar.scrollIntoView({ behavior: 'smooth' });
  }

  // ── Fetch initial state ────────────────────────────────
  async function fetchState() {
    try {
      const res = await fetch('/api/estrategico/state/' + sessionId, {
        headers: { 'Authorization': 'Bearer ' + getToken() }
      });
      if (!res.ok) {
        showToast('No se pudo cargar la sesión', true);
        setTimeout(function () { window.location.href = '/modo-estrategico'; }, 2000);
        return;
      }
      const data = await res.json();
      updateScoreboard(data.score);
      updateIndicators(data);
      if (data.current_strategy) {
        currentStrategy = data.current_strategy;
        document.querySelectorAll('#strat-cards .strat-card').forEach(function (c) {
          c.classList.toggle('active', c.dataset.val === currentStrategy);
        });
        updateStrategyBadge();
      }
      if (data.match_finished) {
        handleMatchEnd(data.winner, data.score);
      }
    } catch (_err) {
      showToast('Error de conexión', true);
    }
  }

  // ── Boot ───────────────────────────────────────────────
  initUI();
  fetchState();
})();
