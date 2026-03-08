import { fetchMatchData, setPlayerNames } from "./api.js?v=2";
import { setMatchData } from "./state.js";
import { bindSimulationControls } from "./controls.js";
import { initLiveFeed } from "./liveFeed.js";

async function initSimulation() {
  try {
    // Inicializa el generador de texto dinámico
    await initLiveFeed();

    // Llama al backend local
    const data = await fetchMatchData();

    // Guarda el estado global
    setMatchData(data);

    // Pinta nombres
    setPlayerNames(data.players);

    // Activa controles de simulación
    bindSimulationControls();

    console.log("Simulación lista para comenzar");
  } catch (err) {
    console.error("Error inicializando simulación:", err);
    document.getElementById("winnerMsg").textContent =
      "Error al iniciar simulación.";
  }
}

initSimulation();
