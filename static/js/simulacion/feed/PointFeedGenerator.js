// frontend/assets/js/simulacion/feed/PointFeedGenerator.js
/* ==============================================================
   Generador de frases legibles a partir de acciones del punto.
   Compatible con JSONs de estructura:
   {
     "FIRST_SERVE": { "IN": [...], "FAULT": [...] },
     "SECOND_SERVE": { "IN": [...], "DOUBLE_FAULT": [...] },
     "RETURN": { "FH": { "IN": [...], "OUT": [...] }, "BH": {...} },
     "RALLY_SHOT": { "FH": { "IN": [...], "OUT": [...] }, "BH": {...} },
     "REACH": { "REACHED": [...], "NOT_REACHED": [...] },
     "POINT_END": { "ace": [...], "doble_falta": [...], "error_golpe": [...] }
   }
   ============================================================== */

export class PointFeedGenerator {
  constructor(library) {
    this.library = library;
  }

  generateFeedForPoint(pointData, players) {
    if (!pointData?.actions?.length) return ["(Sin información del punto)"];

    const feed = [];

    for (const action of pointData.actions) {
      const text = this._getPhraseForAction(action, players);
      if (text) feed.push(text);
    }

    // 🏁 Frase final según la razón del punto
    const endReason = pointData.reason?.toLowerCase() || "";

    // Compatibilidad: winner_id (nuevo) o winner (antiguo, ej. "P1")
    const winnerId = pointData.winner_id || pointData.winner;
    const winnerName =
      players[winnerId] || pointData.winner_name || "Jugador";

    // Si gana el sacador, perdedor es el otro; si gana el restador, perdedor es el servidor
    const loserId =
      pointData.server_id === winnerId
        ? this._otherId(winnerId)
        : pointData.server_id;
    const loserName = players[loserId] || "Jugador";

    const endPhrase = this._getPointEndPhrase(endReason, winnerName, loserName);
    if (endPhrase) feed.push(endPhrase);

    return feed;
  }

  /* ==============================================================
     Selección de frase por tipo de acción (con fallbacks)
     ============================================================== */
  _getPhraseForAction(action, players) {
  const name = players[action.actor_id] || "Jugador";
  const type = action.action_type?.toUpperCase();
  const outcome = action.outcome?.toUpperCase() || "";
  const shotType = action.shot_type?.toUpperCase() || "";
  let section = null;

  switch (type) {
    case "FIRST_SERVE":
    case "SECOND_SERVE":
      section = this.library?.serves?.[type]?.[outcome];
      if (!section) section = this.library?.serves?.[type];
      break;

    case "RETURN":
      section = this.library?.returns?.[shotType]?.[outcome];
      if (!section) section = this.library?.returns?.[shotType];
      break;

    case "RALLY_SHOT":
      section = this.library?.rally?.[shotType]?.[outcome];
      if (!section) section = this.library?.rally_shot?.[shotType];
      break;

    case "REACH":
      section = outcome.includes("NOT_REACHED")
        ? this.library?.reach?.NOT_REACHED
        : this.library?.reach?.REACHED;
      break;

    case "POINT_END":
      section = this.library?.point_end?.[outcome];
      break;

    case "MISC":
      section = this.library?.misc;
      break;

    default:
      return null;
  }

  const phrase = this._pickRandom(section);
  const finalText = phrase ? phrase.replace("{name}", name) : null;

  // 🪄 DEBUG LOG: muestra qué frase se eligió para cada acción
  console.log(
    `🧩 Acción: ${type} (${shotType || "-"}) | Outcome: ${outcome} | Jugador: ${name}`,
    "\n→ Frase elegida:",
    finalText || "(ninguna frase encontrada)"
  );

  return finalText;
}


  /* ==============================================================
     Frase final del punto (POINT_END)
     ============================================================== */
  _getPointEndPhrase(reason, winner, loser) {
    if (!reason || !this.library?.misc?.POINT_END) {
      console.warn("⚠️ No se encontró POINT_END en misc o no hay reason:", reason);
      return null;
    }

    const pe = this.library.misc.POINT_END;
    const r = reason.toLowerCase();
    let key = null;

    if (r.includes("ace")) key = "ace";
    else if (r.includes("doble_falta")) key = "doble_falta";
    else if (r.includes("error_resto")) key = "error_resto";
    else if (r.includes("error_golpe")) key = "error_golpe";
    else if (r.includes("no_llega")) key = "no_llega";


    // Si no hay clave exacta, buscar ignorando mayúsculas
    const realKey = Object.keys(pe).find(
      k => k.toLowerCase().trim() === key?.toLowerCase().trim()
    );

    if (!realKey) {
      console.warn("⚠️ Clave no encontrada en POINT_END:", key);
      return `🎾 Punto para ${winner}.`;
    }

    const phrases = pe[realKey];
    if (!Array.isArray(phrases) || !phrases.length) {
      console.warn("⚠️ No hay frases en POINT_END para clave:", realKey);
      return `🎾 Punto para ${winner}.`;
    }

    // Si es error/fallo, el nombre en la frase es el perdedor
    const nameToUse = realKey.includes("error") || realKey === "no_llega" || realKey === "doble_falta" ? loser : winner;
    const phrase = this._pickRandom(phrases);
    const final = phrase ? phrase.replace("{name}", nameToUse) : `🎾 Punto para ${winner}.`;

    return final;
  }

  /* ==============================================================
     Utilidades
     ============================================================== */
  _pickRandom(arr) {
    if (!arr || !arr.length) return null;
    return arr[Math.floor(Math.random() * arr.length)];
  }

  _otherId(id) {
    return id === "P1" ? "P2" : "P1";
  }
}
