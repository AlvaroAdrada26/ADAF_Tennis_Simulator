/**
 * Modo Big Data — Simulación SSE (simulation.js)
 *
 * Conecta al endpoint streaming, actualiza la barra de progreso
 * y redirige a resultados cuando termina.
 * Soporta abortar con AbortController (botón o salida de página).
 */
(function () {
  'use strict';

  var _abortController = null;
  var _aborted = false;

  // Expuesto globalmente para el botón y el evento beforeunload
  window.abortBigDataSimulation = function () {
    if (_abortController) {
      _aborted = true;
      _abortController.abort();
    }
  };

  // Abortar si el usuario navega fuera de la página mientras simula
  window.addEventListener('beforeunload', function () {
    if (_abortController) {
      _aborted = true;
      _abortController.abort();
    }
  });

  window.startBigDataSimulation = async function (payload, token) {
    var progressFill = document.getElementById('progress-fill');
    var progressPct = document.getElementById('progress-pct');
    var progressCurrent = document.getElementById('progress-current');
    var liveP1Pct = document.getElementById('live-p1-pct');
    var liveP2Pct = document.getElementById('live-p2-pct');
    var liveP1Bar = document.getElementById('live-p1-bar');
    var liveP2Bar = document.getElementById('live-p2-bar');

    _aborted = false;
    _abortController = new AbortController();

    try {
      var headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = 'Bearer ' + token;

      var response = await fetch('/api/bigdata/simulate_stream', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload),
        signal: _abortController.signal
      });

      if (!response.ok) {
        var errData = {};
        try { errData = await response.json(); } catch (e) { /* ignore */ }
        alert(errData.detail || 'Error en la simulación Big Data');
        window.location.href = '/modo-big-data';
        return;
      }

      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';

      while (true) {
        var readResult = await reader.read();
        if (readResult.done) break;

        buffer += decoder.decode(readResult.value, { stream: true });

        // Parse SSE lines
        var lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (var i = 0; i < lines.length; i++) {
          var line = lines[i].trim();
          if (!line.startsWith('data: ')) continue;

          var jsonStr = line.substring(6);
          var msg;
          try { msg = JSON.parse(jsonStr); } catch (e) { continue; }

          if (msg.type === 'progress') {
            // Update progress bar
            progressFill.style.width = msg.pct + '%';
            progressPct.textContent = msg.pct;
            progressCurrent.textContent = msg.current;

            // Update live win rate
            liveP1Pct.textContent = msg.p1_pct;
            liveP2Pct.textContent = msg.p2_pct;
            liveP1Bar.style.width = msg.p1_pct + '%';
            liveP2Bar.style.width = msg.p2_pct + '%';

          } else if (msg.type === 'result') {
            // Store result & redirect
            _abortController = null;
            sessionStorage.setItem('bigdata_result', JSON.stringify(msg.data));
            window.location.href = '/modo-big-data/resultados';
            return;
          }
        }
      }

      // If we get here without a result message, something went wrong
      if (!_aborted) {
        alert('La simulación terminó sin resultados.');
        window.location.href = '/modo-big-data';
      }

    } catch (err) {
      _abortController = null;
      if (_aborted) {
        // Abort voluntario: volver al setup sin mensaje de error
        window.location.href = '/modo-big-data';
        return;
      }
      alert('Error de conexión durante la simulación: ' + err.message);
      window.location.href = '/modo-big-data';
    }
  };
})();
