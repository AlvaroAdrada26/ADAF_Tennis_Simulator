// assets/js/simulacion/api.js
/**
 * Módulo API del simulador ADAF
 * Responsable de comunicar con el backend local (simulate_match)
 */

export async function fetchMatchData() {
  const inputData = {
    player1: {
      name: "Alvaro",
      id: "P1",
      Primer_Saque: 82, Segundo_Saque: 80, Fisico: 88, Estamina: 90,
      Consistencia: 85, Clutch: 87, Momentum: 0, Derecha: 90, Reves: 86,
      Resto: 83, Movilidad: 89
    },
    player2: {
      name: "Diego",
      id: "P2",
      Primer_Saque: 83, Segundo_Saque: 81, Fisico: 86, Estamina: 88,
      Consistencia: 84, Clutch: 85, Momentum: 0, Derecha: 88, Reves: 90,
      Resto: 82, Movilidad: 86
    },
    config: { best_of: 3, tiebreak: true }
  };

  const url = "http://127.0.0.1:8000/simulate_match";
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

    // Retornamos el JSON completo del partido
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
