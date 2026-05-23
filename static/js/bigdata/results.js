/**
 * Modo Big Data — Results Dashboard (results.js)
 *
 * Lee los datos de sessionStorage y renderiza el dashboard completo
 * con Chart.js gráficos y tabla de estadísticas.
 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var raw = sessionStorage.getItem('bigdata_result');
    if (!raw) {
      document.getElementById('no-data').classList.remove('hidden');
      return;
    }

    var data;
    try { data = JSON.parse(raw); } catch (e) {
      document.getElementById('no-data').classList.remove('hidden');
      return;
    }

    document.getElementById('dashboard').classList.remove('hidden');
    renderDashboard(data);
  });

  function renderDashboard(d) {
    var p1 = d.meta.player1;
    var p2 = d.meta.player2;
    var cfg = d.meta.config || {};
    var n = d.meta.total_matches;

    // -- Subtitle --
    var surfLabel = cfg.superficie || 'Dura';
    var fmtLabel = cfg.best_of === 1 ? '1 Set' : 'Bo' + (cfg.best_of || 3);
    document.getElementById('results-subtitle').textContent =
      n.toLocaleString() + ' partidos · ' + p1 + ' vs ' + p2 + ' · ' + surfLabel + ' · ' + fmtLabel;

    // -- KPIs --
    document.getElementById('kpi-p1-winrate').textContent = d.win_rate.P1.pct + '%';
    document.getElementById('kpi-p1-wins').textContent = p1 + ': ' + d.win_rate.P1.wins + ' victorias';
    document.getElementById('kpi-p2-winrate').textContent = d.win_rate.P2.pct + '%';
    document.getElementById('kpi-p2-wins').textContent = p2 + ': ' + d.win_rate.P2.wins + ' victorias';
    document.getElementById('kpi-avg-points').textContent = d.match_length.avg_points;
    document.getElementById('kpi-avg-sets').textContent = d.match_length.avg_sets;
    document.getElementById('kpi-duration').textContent = '~' + d.match_length.avg_duration_min + ' min';

    // -- Player names for comparison --
    document.getElementById('cmp-p1-name').textContent = p1;
    document.getElementById('cmp-p2-name').textContent = p2;

    // -- Charts --
    renderWinRateDonut(d, p1, p2);
    renderScoreDistribution(d);
    renderSetScores(d);
    renderStatsTable(d, p1, p2);
    renderProgression(d, p1, p2);
    renderRadar(d, p1, p2);
    renderRallyDistribution(d);
    renderTotals(d, p1, p2);

    // -- CSV Export --
    document.getElementById('btn-export-csv').addEventListener('click', function () {
      exportCSV(d, p1, p2);
    });
  }

  //Charts
  var COLORS = { p1: '#f59e0b', p2: '#3b82f6', p1bg: 'rgba(245,158,11,0.2)', p2bg: 'rgba(59,130,246,0.2)' };

  function chartDefaults() {
    return {
      color: '#94a3b8',
      borderColor: 'rgba(59,130,246,0.15)',
      plugins: { legend: { labels: { color: '#94a3b8' } } },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' } }
      }
    };
  }

  function renderWinRateDonut(d, p1, p2) {
    new Chart(document.getElementById('chart-winrate'), {
      type: 'doughnut',
      data: {
        labels: [p1, p2],
        datasets: [{
          data: [d.win_rate.P1.wins, d.win_rate.P2.wins],
          backgroundColor: [COLORS.p1, COLORS.p2],
          borderColor: ['rgba(245,158,11,0.6)', 'rgba(59,130,246,0.6)'],
          borderWidth: 2
        }]
      },
      options: {
        responsive: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 20, font: { size: 14 } } },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var total = d.meta.total_matches;
                var pct = ((ctx.raw / total) * 100).toFixed(1);
                return ctx.label + ': ' + ctx.raw + ' (' + pct + '%)';
              }
            }
          }
        }
      }
    });
  }

  function renderScoreDistribution(d) {
    var labels = Object.keys(d.score_distribution);
    var values = Object.values(d.score_distribution);
    new Chart(document.getElementById('chart-scores'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Partidos',
          data: values,
          backgroundColor: labels.map(function (l) {
            return l.charAt(0) > l.charAt(2) ? COLORS.p1 : COLORS.p2;
          }),
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' } }
        }
      }
    });
  }

  function renderSetScores(d) {
    var labels = Object.keys(d.set_score_frequency);
    var values = Object.values(d.set_score_frequency);
    new Chart(document.getElementById('chart-set-scores'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Sets',
          data: values,
          backgroundColor: 'rgba(250,204,21,0.6)',
          borderColor: '#facc15',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { display: false } }
        }
      }
    });
  }

  function renderProgression(d, p1, p2) {
    var prog = d.win_rate_progression || [];
    new Chart(document.getElementById('chart-progression'), {
      type: 'line',
      data: {
        labels: prog.map(function (p) { return p.match; }),
        datasets: [
          {
            label: p1,
            data: prog.map(function (p) { return p.p1_pct; }),
            borderColor: COLORS.p1,
            backgroundColor: COLORS.p1bg,
            tension: 0.3,
            fill: false,
            pointRadius: 2
          },
          {
            label: p2,
            data: prog.map(function (p) { return p.p2_pct; }),
            borderColor: COLORS.p2,
            backgroundColor: COLORS.p2bg,
            tension: 0.3,
            fill: false,
            pointRadius: 2
          }
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: '#94a3b8' } } },
        scales: {
          x: { title: { display: true, text: 'Partidos', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' } },
          y: { title: { display: true, text: 'Win Rate (%)', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' }, min: 0, max: 100 }
        }
      }
    });
  }

  function renderRadar(d, p1, p2) {
    var avg1 = d.avg_stats.P1;
    var avg2 = d.avg_stats.P2;
    var radarLabels = ['Aces', '1er Saque %', 'Winners', 'Pts Resto', 'BP Conv %'];
    var data1 = [avg1.aces, avg1.primer_saque_pct || 0, avg1.winners, avg1.puntos_ganados_resto, avg1.bp_conversion_pct || 0];
    var data2 = [avg2.aces, avg2.primer_saque_pct || 0, avg2.winners, avg2.puntos_ganados_resto, avg2.bp_conversion_pct || 0];

    new Chart(document.getElementById('chart-radar'), {
      type: 'radar',
      data: {
        labels: radarLabels,
        datasets: [
          { label: p1, data: data1, borderColor: COLORS.p1, backgroundColor: COLORS.p1bg, pointBackgroundColor: COLORS.p1 },
          { label: p2, data: data2, borderColor: COLORS.p2, backgroundColor: COLORS.p2bg, pointBackgroundColor: COLORS.p2 }
        ]
      },
      options: {
        responsive: false,
        plugins: { legend: { labels: { color: '#94a3b8' } } },
        scales: {
          r: {
            ticks: { color: '#94a3b8', backdropColor: 'transparent' },
            grid: { color: 'rgba(59,130,246,0.15)' },
            angleLines: { color: 'rgba(59,130,246,0.15)' },
            pointLabels: { color: '#94a3b8', font: { size: 12 } }
          }
        }
      }
    });
  }

  function renderRallyDistribution(d) {
    var labels = Object.keys(d.rally_distribution);
    var values = Object.values(d.rally_distribution);
    new Chart(document.getElementById('chart-rally'), {
      type: 'bar',
      data: {
        labels: labels.map(function (l) { return l + ' golpes'; }),
        datasets: [{
          label: 'Puntos',
          data: values,
          backgroundColor: ['#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6'],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' } }
        }
      }
    });
  }

  function renderTotals(d, p1, p2) {
    var t1 = d.total_stats.P1;
    var t2 = d.total_stats.P2;
    new Chart(document.getElementById('chart-totals'), {
      type: 'bar',
      data: {
        labels: ['Aces', 'Dobles Faltas', 'Winners', 'Errores NF', 'BP Conv.'],
        datasets: [
          { label: p1, data: [t1.aces, t1.dobles_faltas, t1.winners, t1.errores_no_forzados, t1.break_points_convertidos], backgroundColor: COLORS.p1, borderRadius: 4 },
          { label: p2, data: [t2.aces, t2.dobles_faltas, t2.winners, t2.errores_no_forzados, t2.break_points_convertidos], backgroundColor: COLORS.p2, borderRadius: 4 }
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: '#94a3b8' } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(59,130,246,0.1)' } }
        }
      }
    });
  }

  //Stats Table
  function renderStatsTable(d, p1Name, p2Name) {
    var container = document.getElementById('stats-table');
    var avg1 = d.avg_stats.P1;
    var avg2 = d.avg_stats.P2;

    var rows = [
      { label: 'Aces', k: 'aces' },
      { label: 'Dobles Faltas', k: 'dobles_faltas' },
      { label: '1er Saque %', k: 'primer_saque_pct', pct: true },
      { label: 'Pts Ganados 1er Saque', k: 'puntos_ganados_1er_saque' },
      { label: 'Pts Ganados 2do Saque', k: 'puntos_ganados_2do_saque' },
      { label: 'Winners', k: 'winners' },
      { label: 'Errores No Forzados', k: 'errores_no_forzados' },
      { label: 'Puntos Resto', k: 'puntos_ganados_resto' },
      { label: 'Total Puntos Ganados', k: 'total_puntos_ganados' },
      { label: 'Break Points Conv.', k: 'break_points_convertidos' },
      { label: 'BP Oportunidades', k: 'break_points_oportunidades' },
      { label: 'BP Conversión %', k: 'bp_conversion_pct', pct: true }
    ];

    var html = '';
    rows.forEach(function (row) {
      var v1 = avg1[row.k] !== undefined ? avg1[row.k] : 0;
      var v2 = avg2[row.k] !== undefined ? avg2[row.k] : 0;
      var suffix = row.pct ? '%' : '';
      var maxVal = Math.max(v1, v2, 0.1);
      var pct1 = Math.round((v1 / maxVal) * 100);
      var pct2 = Math.round((v2 / maxVal) * 100);

      html += '<div class="stat-row">' +
        '<div class="text-right"><div class="bar-container"><div class="bar-fill-p1" style="width:' + pct1 + '%;float:right"></div></div></div>' +
        '<div class="text-right text-sm font-bold text-yellow-400">' + v1 + suffix + '</div>' +
        '<div class="text-center text-xs text-gray-400 font-medium">' + row.label + '</div>' +
        '<div class="text-left text-sm font-bold text-blue-400">' + v2 + suffix + '</div>' +
        '<div class="text-left"><div class="bar-container"><div class="bar-fill-p2" style="width:' + pct2 + '%"></div></div></div>' +
        '</div>';
    });

    container.innerHTML = html;
  }

  //CSV Export
  function exportCSV(d, p1, p2) {
    var lines = [];
    lines.push('Modo Big Data - ADAF Tennis Simulator');
    lines.push('Partidos,' + d.meta.total_matches);
    lines.push('Jugador 1,' + p1);
    lines.push('Jugador 2,' + p2);
    lines.push('');

    //Win rate
    lines.push('Win Rate');
    lines.push('Jugador,Victorias,Porcentaje');
    lines.push(p1 + ',' + d.win_rate.P1.wins + ',' + d.win_rate.P1.pct + '%');
    lines.push(p2 + ',' + d.win_rate.P2.wins + ',' + d.win_rate.P2.pct + '%');
    lines.push('');

    //Avg stats
    lines.push('Estadísticas Promedio por Partido');
    var keys = Object.keys(d.avg_stats.P1);
    lines.push('Stat,' + p1 + ',' + p2);
    keys.forEach(function (k) {
      lines.push(k + ',' + d.avg_stats.P1[k] + ',' + d.avg_stats.P2[k]);
    });
    lines.push('');

    //Match length
    lines.push('Duración de Partidos');
    lines.push('Promedio puntos,' + d.match_length.avg_points);
    lines.push('Min puntos,' + d.match_length.min_points);
    lines.push('Max puntos,' + d.match_length.max_points);
    lines.push('Promedio sets,' + d.match_length.avg_sets);

    var csv = lines.join('\n');
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'bigdata_' + p1.replace(/\s/g, '_') + '_vs_' + p2.replace(/\s/g, '_') + '.csv';
    a.click();
    URL.revokeObjectURL(url);
  }
})();
