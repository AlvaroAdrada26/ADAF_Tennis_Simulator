// assets/js/simulacion/api.js
/**
 * Módulo API del simulador ADAF
 * Responsable de obtener los datos del partido simulado.
 *
 * Flujo principal:
 *   1. partido_rapido.html hace POST /api/simulate_match y guarda el resultado
 *      en sessionStorage("match_result").
 *   2. simulacion2.html llama a fetchMatchData(), que lee sessionStorage.
 *   3. Si no hay datos en sessionStorage (acceso directo), se hace un POST
 *      con datos de demo como fallback.
 */

export async function fetchMatchData() {
  // ── 1. Intentar leer resultado pre-simulado de sessionStorage ──
  const cached = sessionStorage.getItem("match_result");
  if (cached) {
    try {
      const data = JSON.parse(cached);
      console.log("✅ Partido cargado desde sessionStorage:", data);
      // No limpiamos para poder recargar la página sin perder el partido
      return data;
    } catch (e) {
      console.warn("⚠️ Error parseando match_result de sessionStorage, fallback a API", e);
    }
  }

  // ── 2. Fallback: simular con datos de demo ──
  console.log("⚠️ No hay partido en sessionStorage. Usando datos de demo.");

  const inputData = {
    player1: {
      name: "Demo Jugador 1",
      id: "P1",
      Primer_Saque: 82, Segundo_Saque: 80, Fisico: 88, Estamina: 90,
      Consistencia: 85, Clutch: 87, Momentum: 0, Derecha: 90, Reves: 86,
      Resto: 83, Movilidad: 89
    },
    player2: {
      name: "Demo Jugador 2",
      id: "P2",
      Primer_Saque: 83, Segundo_Saque: 81, Fisico: 86, Estamina: 88,
      Consistencia: 84, Clutch: 85, Momentum: 0, Derecha: 88, Reves: 90,
      Resto: 82, Movilidad: 86
    },
    config: { best_of: 3, tiebreak: true }
  };

  const url = "/api/simulate_match";
  console.log(`📡 Solicitando simulación a ${url}`);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(inputData)
    });

    if (!res.ok) throw new Error(`Error HTTP ${res.status}`);

    const data = await res.json();
    console.log("✅ Partido recibido del backend:", data);
    return data;
  } catch (err) {
    console.error("❌ Error al obtener datos del backend:", err);
    throw err;
  }
}

/**
 * Inicializa los nombres de jugadores en el marcador (puede llamarse tras cargar el partido)
 */
export function setPlayerNames(players) {
  if (!players) return;
  const p1 = document.getElementById("player1-name");
  const p2 = document.getElementById("player2-name");
  if (p1) p1.textContent = players.P1 || "Jugador 1";
  if (p2) p2.textContent = players.P2 || "Jugador 2";
}
