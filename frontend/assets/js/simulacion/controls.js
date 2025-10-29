// frontend/assets/js/simulacion/controls.js
/* Módulo de control de simulación de tenis:
   Maneja los botones (Next, Previous, End) y actualiza el flujo de la simulación. */

import { getState, nextPoint, previousPoint, endMatch } from "./state.js";
import { updateScoreboard, showFinalScore } from "./scoreboard.js";
import { updatePointsFeed, playPointFeed } from "./liveFeed.js";

/**
 * Vincula los botones del panel de simulación (siguiente, anterior, finalizar)
 * y gestiona el avance del timeline punto a punto.
 */
export function bindSimulationControls() {
  const nextBtn = document.getElementById("btn-next");
  const prevBtn = document.getElementById("btn-previous");
  const endBtn = document.getElementById("btn-end");

  if (!nextBtn || !prevBtn || !endBtn) {
    console.warn("⚠️ No se encontraron los botones de simulación en el DOM.");
    return;
  }

  console.log("🎮 Controles de simulación inicializados");

  // ▶ Siguiente punto
  nextBtn.addEventListener("click", async () => {
    const { timeline, matchEnded } = getState();
    if (matchEnded) return;
    if (!timeline?.length) {
      console.warn("No hay puntos cargados todavía.");
      return;
    }

    const pointData = nextPoint(); // avanza en el timeline
    if (!pointData) {
      console.log(" Fin del partido");
      showFinalScore();
      endMatch();
      return;
    }

    // Actualiza todo paso a paso
    updateScoreboard(pointData);
    updatePointsFeed(pointData);
    await playPointFeed(pointData);
  });

  //  Punto anterior
  prevBtn.addEventListener("click", () => {
    const pointData = previousPoint();
    if (pointData) {
      updateScoreboard(pointData);
    } else {
      console.log("Inicio del partido");
    }
  });

  //  Terminar simulación
  endBtn.addEventListener("click", () => {
    endMatch();
    showFinalScore();
  });
}
