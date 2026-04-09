/**
 * static/js/entrenador/setup.js
 * Lógica de la página de configuración del Modo Entrenador.
 * Selección de jugadores, jugador entrenado, config del partido y POST /api/coach/start.
 */

document.addEventListener('auth:ready', function (e) {
  'use strict';

  // ── Auth guard ──────────────────────────────────────────
  if (!e.detail.authenticated) {
    show('state-no-auth');
    return;
  }

  // ── State ───────────────────────────────────────────────
  let players = [];
  let sel1 = null;
  let sel2 = null;
  let coached = null; // "P1" | "P2"

  // ── Helpers ─────────────────────────────────────────────
  function getToken() { return localStorage.getItem('access_token'); }

  function getActiveVal(groupId) {
    const el = document.querySelector('#' + groupId + ' .active[data-val]');
    return el ? el.dataset.val : null;
  }

  function show(id) { document.getElementById(id).classList.remove('hidden'); }
  function hide(id) { document.getElementById(id).classList.add('hidden'); }

  function showToast(msg, isErr) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'fixed bottom-8 left-1/2 -translate-x-1/2 z-50 px-8 py-4 rounded-xl text-white font-semibold text-lg shadow-2xl toast-show ' +
      (isErr ? 'bg-red-600' : 'bg-green-600');
    setTimeout(function () { t.classList.remove('toast-show'); t.classList.add('toast-hide'); }, 2500);
    setTimeout(function () { t.classList.add('hidden'); }, 3000);
  }

  // ── Init: cargar jugadores ──────────────────────────────
  (async function init() {
    const token = getToken();
    if (!token) { show('state-no-auth'); return; }

    show('state-loading');

    try {
      const res = await fetch('/api/players', {
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

      show('match-setup');
      renderPlayers();

    } catch (_err) {
      hide('state-loading');
      showToast('Error de conexión al cargar jugadores.', true);
    }
  })();

  // ── Render tarjetas ─────────────────────────────────────
  function renderPlayers() {
    const l1 = document.getElementById('p1-list');
    const l2 = document.getElementById('p2-list');
    l1.innerHTML = '';
    l2.innerHTML = '';
    players.forEach(function (p) {
      l1.appendChild(makeCard(p, 1));
      l2.appendChild(makeCard(p, 2));
    });
    refreshCards();
  }

  function makeCard(p, slot) {
    const card = document.createElement('div');
    card.dataset.pid = p.id;
    card.dataset.slot = slot;

    const attrs = [p.attr_primer_saque, p.attr_segundo_saque, p.attr_resto,
      p.attr_derecha, p.attr_reves, p.attr_movilidad,
      p.attr_consistencia, p.attr_clutch, p.attr_fisico];
    let sum = 0;
    for (let i = 0; i < attrs.length; i++) sum += (attrs[i] || 0);
    const avg = Math.round(sum / 9);

    let tierBg, tierGlow, tierBorder, tierText, tierSub;
    if (avg >= 80) {
      tierBg = 'tier-gold'; tierGlow = 'glow-gold';
      tierBorder = 'border-yellow-400'; tierText = 'text-yellow-900'; tierSub = 'text-slate-700';
    } else if (avg >= 55) {
      tierBg = 'tier-silver'; tierGlow = 'glow-silver';
      tierBorder = 'border-gray-400'; tierText = 'text-gray-800'; tierSub = 'text-gray-600';
    } else {
      tierBg = 'tier-bronze'; tierGlow = 'glow-bronze';
      tierBorder = 'border-amber-600'; tierText = 'text-amber-900'; tierSub = 'text-slate-700';
    }

    const hand = p.brazo_bueno === 'L' ? 'Zurdo' : 'Diestro';
    const altura = p.altura_cm || '—';
    const nac = p.nacionalidad || '—';

    card.className = 'player-card w-[200px] ' + tierBg + ' ' + tierGlow +
      ' text-slate-900 rounded-2xl shadow-xl p-3.5 border-[3px] ' + tierBorder +
      ' transition-transform duration-300';

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
      '</div>' +
      '<div class="mt-2 flex items-center justify-center">' +
        '<span class="text-[8px] uppercase tracking-wider ' + tierSub + ' font-semibold opacity-60">ADAF Tennis Simulator</span>' +
      '</div>';

    card.addEventListener('click', function () { selectPlayer(p, slot); });
    return card;
  }

  // ── Selección de jugador ────────────────────────────────
  function selectPlayer(p, slot) {
    if (slot === 1) {
      sel1 = (sel1 && sel1.id === p.id) ? null : p;
    } else {
      sel2 = (sel2 && sel2.id === p.id) ? null : p;
    }
    coached = null; // reset coach pick on player change
    refreshCards();
    refreshCoachPick();
    refreshSummary();
  }

  function refreshCards() {
    document.querySelectorAll('.player-card').forEach(function (c) {
      const id = Number(c.dataset.pid);
      const slot = Number(c.dataset.slot);
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

  // ── Coach pick ──────────────────────────────────────────
  function refreshCoachPick() {
    if (sel1 && sel2) {
      document.getElementById('cp1-initial').textContent = sel1.nombre.charAt(0);
      document.getElementById('cp1-name').textContent = sel1.nombre + ' ' + sel1.apellido;
      document.getElementById('cp2-initial').textContent = sel2.nombre.charAt(0);
      document.getElementById('cp2-name').textContent = sel2.nombre + ' ' + sel2.apellido;
      show('coach-pick-section');

      document.getElementById('coach-p1').classList.toggle('active', coached === 'P1');
      document.getElementById('coach-p2').classList.toggle('active', coached === 'P2');
    } else {
      hide('coach-pick-section');
    }
  }

  document.getElementById('coach-p1').addEventListener('click', function () {
    coached = coached === 'P1' ? null : 'P1';
    refreshCoachPick();
    refreshSummary();
  });

  document.getElementById('coach-p2').addEventListener('click', function () {
    coached = coached === 'P2' ? null : 'P2';
    refreshCoachPick();
    refreshSummary();
  });

  // ── Summary ─────────────────────────────────────────────
  function refreshSummary() {
    if (sel1 && sel2 && coached) {
      const sets = getActiveVal('opt-sets') || '3';
      const surf = getActiveVal('opt-surface') || 'Dura';
      const tb = getActiveVal('opt-tb') || 'true';

      document.getElementById('s-p1-i').textContent = sel1.nombre.charAt(0);
      document.getElementById('s-p1-n').textContent = sel1.nombre + ' ' + sel1.apellido;
      document.getElementById('s-p2-i').textContent = sel2.nombre.charAt(0);
      document.getElementById('s-p2-n').textContent = sel2.nombre + ' ' + sel2.apellido;
      document.getElementById('s-fmt').textContent = sets === '1' ? '1 Set' : 'Mejor de ' + sets;
      document.getElementById('s-surf').textContent = surf;
      document.getElementById('s-tb').textContent = tb === 'true' ? 'Sí' : 'No';

      // Coach badge
      const badge1 = document.getElementById('s-p1-coach');
      const badge2 = document.getElementById('s-p2-coach');
      if (coached === 'P1') {
        badge1.classList.remove('hidden');
        badge2.classList.add('hidden');
      } else {
        badge1.classList.add('hidden');
        badge2.classList.remove('hidden');
      }

      show('summary-box');
    } else {
      hide('summary-box');
    }
  }

  // ── Radio buttons ───────────────────────────────────────
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

  // ── Start match ─────────────────────────────────────────
  document.getElementById('btn-start').addEventListener('click', async function () {
    if (!sel1 || !sel2) { showToast('Selecciona ambos jugadores', true); return; }
    if (!coached) { showToast('Selecciona a quién quieres entrenar', true); return; }

    const btn = document.getElementById('btn-start');
    const origHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">' +
      '<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>' +
      '<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Iniciando...';

    const sets = Number(getActiveVal('opt-sets') || 3);
    const surf = getActiveVal('opt-surface') || 'Dura';
    const tb = (getActiveVal('opt-tb') || 'true') === 'true';

    function buildP(p, tag) {
      return {
        name: p.nombre + ' ' + p.apellido,
        id: tag,
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

    try {
      const token = getToken() || '';
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = 'Bearer ' + token;

      const res = await fetch('/api/coach/start', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          player1: buildP(sel1, 'P1'),
          player2: buildP(sel2, 'P2'),
          coached_player: coached,
          config: { best_of: sets, tiebreak: tb, superficie: surf }
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(function () { return {}; });
        showToast(errData.detail || 'Error al iniciar sesión de entrenador', true);
        return;
      }

      const data = await res.json();

      // Guardar datos en sessionStorage para la página del partido
      sessionStorage.setItem('coach_session_id', data.session_id);
      sessionStorage.setItem('coach_config', JSON.stringify({
        coached_player: coached,
        surface: surf,
        best_of: sets,
        tiebreak: tb,
        player1_name: sel1.nombre + ' ' + sel1.apellido,
        player2_name: sel2.nombre + ' ' + sel2.apellido,
        db_player1_id: sel1.id,
        db_player2_id: sel2.id,
      }));

      window.location.href = '/modo-entrenador/partido';

    } catch (_err) {
      showToast('Error de conexión. Inténtalo de nuevo.', true);
    } finally {
      btn.disabled = false;
      btn.innerHTML = origHTML;
    }
  });
});
