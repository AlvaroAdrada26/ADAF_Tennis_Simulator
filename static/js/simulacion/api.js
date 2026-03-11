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
  // ── 1. Resultado ya simulado (desde partido_rapido.html) ──
  const cached = sessionStorage.getItem("match_result");
  if (cached) {
    try {
      const data = JSON.parse(cached);
      console.log("✅ Partido cargado desde sessionStorage (match_result):", data);
      return data;
    } catch (e) {
      console.warn("⚠️ Error parseando match_result, continuando...", e);
    }
  }

  // ── 2. Payload crudo para simular (desde crear_partido.html) ──
  const stored = sessionStorage.getItem("matchPayload");
  let inputData = null;
  if (stored) {
    try {
      inputData = JSON.parse(stored);
      console.log("📦 Payload leído de sessionStorage (matchPayload):", inputData);
    } catch (e) {
      console.warn("⚠️ Error parseando matchPayload, usando datos de demo", e);
    }
  }

  // ── 3. Fallback: datos de demo ──
  if (!inputData) {
    console.log("⚠️ No hay partido en sessionStorage. Usando datos de demo.");
    inputData = {
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
  }

  // ── 4. Merge surface from sessionStorage if present ──
  const storedSurface = sessionStorage.getItem("matchSurface");
  if (storedSurface && inputData.config) {
    inputData.config.superficie = storedSurface;
  }

  // ── 5. Llamar al backend con el payload (include JWT if available) ──
  const url = "/api/simulate_match";
  console.log(`📡 Solicitando simulación a ${url}`);

  const token = localStorage.getItem("access_token") || "";
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(inputData)
    });

    if (!res.ok) throw new Error(`Error HTTP ${res.status}`);

    const data = await res.json();
    console.log("✅ Partido recibido del backend:", data);

    // ── 6. Store result so refresh doesn't re-simulate ──
    sessionStorage.setItem("match_result", JSON.stringify(data));
    sessionStorage.removeItem("matchPayload");

    // ── 7. Build match_config for the save button ──
    if (inputData.player1 && inputData.player2) {
      const mc = {
        surface: inputData.config?.superficie || storedSurface || "Dura",
        best_of: inputData.config?.best_of || 3,
        tiebreak: inputData.config?.tiebreak !== undefined ? inputData.config.tiebreak : true,
        player1_name: inputData.player1.name,
        player2_name: inputData.player2.name,
        db_player1_id: parseInt(inputData.player1.id) || null,
        db_player2_id: parseInt(inputData.player2.id) || null
      };
      sessionStorage.setItem("match_config", JSON.stringify(mc));
    }

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
