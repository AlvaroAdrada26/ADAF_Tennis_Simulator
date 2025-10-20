async function simulateMatch() {
  // Datos de prueba (puedes reemplazarlos por inputs más adelante)
  const payload = {
    player1: {
      name: "C. Alcaraz",
      Primer_Saque: 80,
      Segundo_Saque: 80,
      Fisico: 80,
      Estamina: 80,
      Consistencia: 80,
      Clutch: 80,
      Momentum: 0,
      Derecha: 80,
      Reves: 80,
      Resto: 80,
      Movilidad: 80,
    },
    player2: {
      name: "N. Djokovic",
      Primer_Saque: 80,
      Segundo_Saque: 80,
      Fisico: 80,
      Estamina: 80,
      Consistencia: 80,
      Clutch: 80,
      Momentum: 0,
      Derecha: 80,
      Reves: 80,
      Resto: 80,
      Movilidad: 80,
    },
    config: {
      best_of: 3,
      tiebreak: true,
      seed: 42,
    },
  };

  // Mostrar mensaje temporal mientras simula
  document.getElementById("winnerMsg").innerText = "⏳ Simulando partido...";

  try {
    const res = await fetch("http://127.0.0.1:8000/simulate_match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("Error en la API");

    const result = await res.json();
    console.log("✅ Resultado del partido:", result);

    // Actualizar nombres
    document.getElementById("player1Name").innerText = payload.player1.name;
    document.getElementById("player2Name").innerText = payload.player2.name;

    // Actualizar sets (puede haber menos de 3 sets, así que comprobamos)
    for (let i = 0; i < 3; i++) {
      const p1 = result.set_scores[i]?.[0] ?? "-";
      const p2 = result.set_scores[i]?.[1] ?? "-";
      document.getElementById(`p1set${i + 1}`).innerText = p1;
      document.getElementById(`p2set${i + 1}`).innerText = p2;
    }

    // Mostrar ganador
    document.getElementById("winnerMsg").innerText = `🏆 Ganador: ${result.winner}`;
  } 
  catch (err) {
    console.error("❌ Error:", err);
    document.getElementById("winnerMsg").innerText = "⚠️ Error al conectar con el backend.";
  }
}