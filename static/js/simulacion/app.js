import { fetchMatchData, setPlayerNames } from "./api.js";
import { setMatchData } from "./state.js";
import { bindSimulationControls } from "./controls.js";
import { initLiveFeed, updateLiveStatsPanel, updateMomentumBar } from "./liveFeed.js";

async function initSimulation() {
  try {
    //Inicializa el generador de texto dinámico
    await initLiveFeed();

    //Llama al backend local
    const data = await fetchMatchData();

    //Guarda el estado global
    setMatchData(data);

    //Pinta nombres
    setPlayerNames(data.players);

    //Inicializa paneles en tiempo real
    updateLiveStatsPanel();
    updateMomentumBar();

    //Inicializa contador de puntos
    const counterEl = document.getElementById("point-counter");
    if (counterEl) counterEl.textContent = `Punto 0`;

    //Activa controles de simulacion
    bindSimulationControls();

    console.log("Simulación lista para comenzar");
  } catch (err) {
    console.error("Error inicializando simulación:", err);
    const panel = document.getElementById("scoreboard-panel");
    if (panel) {
      const msg = document.createElement("div");
      msg.className = "text-xl text-red-400 font-bold mt-4 text-center";
      msg.textContent = "⚠️ Error al iniciar simulación. Revisa la consola.";
      panel.appendChild(msg);
    }
  }
}

initSimulation();
