/**
 * Modo Big Data — Configuración (config.js)
 *
 * Gestiona la selección de jugadores, configuración de partidos,
 * slider de número de partidos, y lanza la simulación.
 */
document.addEventListener('auth:ready', function (e) {
  'use strict';

  // ── Auth guard ────────────────────────────────────────────
  if (!e.detail.authenticated) {
    document.getElementById('state-no-auth').classList.remove('hidden');
    return;
  }

  // ── Estado ────────────────────────────────────────────────
  var players = [];
  var sel1 = null;
  var sel2 = null;

  // ── Helpers ───────────────────────────────────────────────
  function getToken() { return localStorage.getItem('access_token'); }

  function getActiveVal(groupId) {
    var el = document.querySelector('#' + groupId + ' .active[data-val]');
    return el ? el.dataset.val : null;
  }

  function show(id) { document.getElementById(id).classList.remove('hidden'); }
  function hide(id) { document.getElementById(id).classList.add('hidden'); }

  function showToast(msg, isErr) {
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'fixed bottom-8 left-1/2 -translate-x-1/2 z-50 px-8 py-4 rounded-xl text-white font-semibold text-lg shadow-2xl toast-show ' + (isErr ? 'bg-red-600' : 'bg-green-600');
    setTimeout(function () { t.classList.remove('toast-show'); t.classList.add('toast-hide'); }, 2500);
    setTimeout(function () { t.classList.add('hidden'); }, 3000);
  }

  function getNumMatches() {
    return parseInt(document.getElementById('num-matches-input').value) || 100;
  }

  // ── Time estimate ─────────────────────────────────────────
  function updateTimeEstimate() {
    var n = getNumMatches();
    // ~30ms per match average
    var secs = Math.max(1, Math.round(n * 0.03));
    document.getElementById('est-time').textContent = secs;
  }

  // ── Slider / Input sync ───────────────────────────────────
  var slider = document.getElementById('num-matches-slider');
  var numInput = document.getElementById('num-matches-input');

  slider.addEventListener('input', function () {
    numInput.value = slider.value;
    updatePresetHighlight(parseInt(slider.value));
    updateTimeEstimate();
    refreshSummary();
  });

  numInput.addEventListener('input', function () {
    var val = parseInt(numInput.value);
    if (val < 10) val = 10;
    if (val > 10000) val = 10000;
    slider.value = val;
    updatePresetHighlight(val);
    updateTimeEstimate();
    refreshSummary();
  });

  // ── Presets ───────────────────────────────────────────────
  function updatePresetHighlight(val) {
    document.querySelectorAll('#presets .preset-btn').forEach(function (b) {
      b.classList.toggle('active', parseInt(b.dataset.val) === val);
    });
  }

  document.querySelectorAll('#presets .preset-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var val = parseInt(btn.dataset.val);
      slider.value = val;
      numInput.value = val;
      updatePresetHighlight(val);
      updateTimeEstimate();
      refreshSummary();
    });
  });

  // ── Init (auth:ready fires after DOMContentLoaded) ────────
  (async function () {
    var token = getToken();
    if (!token) { show('state-no-auth'); return; }

    show('state-loading');

    try {
      var res = await fetch('/api/players', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      hide('state-loading');

      if (res.status === 401) { show('state-no-auth'); return; }
      if (!res.ok) { showToast('Error al cargar jugadores', true); return; }

      players = await res.json();
      if (players.length === 0) { show('state-no-players'); return; }
      if (players.length < 2) {
        document.getElementById('cnt').textContent = players.length;
        show('state-few-players');
        return;
      }

      show('setup-section');
      renderPlayers();
      updateTimeEstimate();
    } catch (err) {
      hide('state-loading');
      showToast('Error de conexión al cargar jugadores.', true);
    }
  })();

  // ── Render tarjetas ───────────────────────────────────────
  function renderPlayers() {
    var l1 = document.getElementById('p1-list');
    var l2 = document.getElementById('p2-list');
    l1.innerHTML = '';
    l2.innerHTML = '';
    players.forEach(function (p) {
      l1.appendChild(makeCard(p, 1));
      l2.appendChild(makeCard(p, 2));
    });
    refreshCards();
  }

  function makeCard(p, slot) {
    var card = document.createElement('div');
    card.dataset.pid = p.id;
    card.dataset.slot = slot;

    var attrs = [p.attr_primer_saque, p.attr_segundo_saque, p.attr_resto,
      p.attr_derecha, p.attr_reves, p.attr_movilidad,
      p.attr_consistencia, p.attr_clutch, p.attr_fisico];
    var sum = 0;
    for (var i = 0; i < attrs.length; i++) sum += (attrs[i] || 0);
    var avg = Math.round(sum / 9);

    var tierBg, tierGlow, tierBorder, tierText, tierSub;
    if (avg >= 80) {
      tierBg = 'tier-gold'; tierGlow = 'glow-gold'; tierBorder = 'border-yellow-400'; tierText = 'text-yellow-900'; tierSub = 'text-slate-700';
    } else if (avg >= 55) {
      tierBg = 'tier-silver'; tierGlow = 'glow-silver'; tierBorder = 'border-gray-400'; tierText = 'text-gray-800'; tierSub = 'text-gray-600';
    } else {
      tierBg = 'tier-bronze'; tierGlow = 'glow-bronze'; tierBorder = 'border-amber-600'; tierText = 'text-amber-900'; tierSub = 'text-slate-700';
    }

    var hand = p.brazo_bueno === 'L' ? 'Zurdo' : 'Diestro';
    var altura = p.altura_cm || '—';
    var nac = p.nacionalidad || '—';

    card.className = 'player-card w-[200px] ' + tierBg + ' ' + tierGlow + ' text-slate-900 rounded-2xl shadow-xl p-3.5 border-[3px] ' + tierBorder + ' transition-transform duration-300';
    card.innerHTML =
      '<div class="flex items-center justify-between mb-1">' +
      '<div class="text-4xl font-extrabold ' + tierText + ' drop-shadow-sm leading-none">' + avg + '</div>' +
      '<div class="text-[11px] font-semibold ' + tierSub + ' uppercase tracking-wide text-right">' + nac + '</div>' +
      '</div>' +
      '<div class="text-base font-extrabold uppercase tracking-wide ' + tierText + ' truncate">' + p.nombre + ' ' + p.apellido + '</div>' +
      '<div class="text-[11px] ' + tierSub + ' font-medium">' + altura + ' cm · ' + hand + '</div>' +
      '<div class="mt-2 border-t border-current opacity-20"></div>' +
      '<div class="mt-2 grid grid-cols-3 gap-x-1 gap-y-1.5 text-center">' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">1st Srv</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_primer_saque || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">2nd Srv</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_segundo_saque || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">Return</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_resto || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">Forehand</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_derecha || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">Backhand</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_reves || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">Consist.</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_consistencia || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">Movement</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_movilidad || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">Physical</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_fisico || 50) + '</div></div>' +
      '<div><div class="text-[9px] font-semibold ' + tierSub + '">Clutch</div><div class="text-sm font-bold ' + tierText + '">' + (p.attr_clutch || 50) + '</div></div>' +
      '</div>';

    card.addEventListener('click', function () { selectPlayer(p, slot); });
    return card;
  }

  // ── Selección ─────────────────────────────────────────────
  function selectPlayer(p, slot) {
    if (slot === 1) { sel1 = (sel1 && sel1.id === p.id) ? null : p; }
    else { sel2 = (sel2 && sel2.id === p.id) ? null : p; }
    refreshCards();
    refreshSummary();
  }

  function refreshCards() {
    document.querySelectorAll('.player-card').forEach(function (c) {
      var id = Number(c.dataset.pid);
      var slot = Number(c.dataset.slot);
      c.classList.remove('selected', 'disabled');
      if (slot === 1) {
        if (sel1 && sel1.id === id) c.classList.add('selected');
        if (sel2 && sel2.id === id) c.classList.add('disabled');
      } else {
        if (sel2 && sel2.id === id) c.classList.add('selected');
        if (sel1 && sel1.id === id) c.classList.add('disabled');
      }
    });
  }

  function refreshSummary() {
    if (sel1 && sel2) {
      var sets = getActiveVal('opt-sets') || '3';
      var surf = getActiveVal('opt-surface') || 'Dura';
      var tb = getActiveVal('opt-tb') || 'true';
      var num = getNumMatches();

      document.getElementById('s-p1-i').textContent = sel1.nombre.charAt(0);
      document.getElementById('s-p1-n').textContent = sel1.nombre + ' ' + sel1.apellido;
      document.getElementById('s-p2-i').textContent = sel2.nombre.charAt(0);
      document.getElementById('s-p2-n').textContent = sel2.nombre + ' ' + sel2.apellido;
      document.getElementById('s-num').textContent = num.toLocaleString();
      document.getElementById('s-fmt').textContent = sets === '1' ? '1 Set' : 'Mejor de ' + sets;
      document.getElementById('s-surf').textContent = surf;
      document.getElementById('s-tb').textContent = tb === 'true' ? 'Sí' : 'No';
      show('summary-box');
    } else {
      hide('summary-box');
    }
  }

  // ── Radio buttons ─────────────────────────────────────────
  document.querySelectorAll('#opt-sets .radio-opt, #opt-tb .radio-opt').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.parentElement.querySelectorAll('.radio-opt').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      refreshSummary();
    });
  });

  document.querySelectorAll('#opt-surface .surface-card').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.parentElement.querySelectorAll('.surface-card').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      refreshSummary();
    });
  });

  // ── Lanzar simulación ─────────────────────────────────────
  document.getElementById('btn-start').addEventListener('click', function () {
    if (!sel1 || !sel2) { showToast('Selecciona ambos jugadores', true); return; }

    function buildP(p) {
      return {
        name: p.nombre + ' ' + p.apellido,
        id: String(p.id),
        Primer_Saque: p.attr_primer_saque || 50,
        Segundo_Saque: p.attr_segundo_saque || 50,
        Fisico: p.attr_fisico || 50,
        Estamina: p.attr_fisico || 50,
        Consistencia: p.attr_consistencia || 50,
        Clutch: p.attr_clutch || 50,
        Momentum: 0,
        Derecha: p.attr_derecha || 50,
        Reves: p.attr_reves || 50,
        Resto: p.attr_resto || 50,
        Movilidad: p.attr_movilidad || 50
      };
    }

    var sets = Number(getActiveVal('opt-sets') || 3);
    var surf = getActiveVal('opt-surface') || 'Dura';
    var tb = (getActiveVal('opt-tb') || 'true') === 'true';
    var numMatches = getNumMatches();

    var payload = {
      player1: buildP(sel1),
      player2: buildP(sel2),
      config: { best_of: sets, tiebreak: tb, superficie: surf },
      num_matches: numMatches
    };

    // Store names for results page
    sessionStorage.setItem('bigdata_p1_name', sel1.nombre + ' ' + sel1.apellido);
    sessionStorage.setItem('bigdata_p2_name', sel2.nombre + ' ' + sel2.apellido);

    // Update live progress names
    document.getElementById('live-p1-name').textContent = sel1.nombre + ' ' + sel1.apellido;
    document.getElementById('live-p2-name').textContent = sel2.nombre + ' ' + sel2.apellido;
    document.getElementById('progress-total').textContent = numMatches;

    // Switch to progress view
    hide('setup-section');
    show('progress-section');

    // Start streaming simulation
    window.startBigDataSimulation(payload, getToken());
  });
});
