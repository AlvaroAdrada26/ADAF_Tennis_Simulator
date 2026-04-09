// lang.js
const translations = {
  es: {
    // ********************************
    // ********** INDEX.HTML **********
    // ********************************

    // =============================
    // SIDEBAR Y HEADER
    // =============================
    sidebarMenu: "Menú",
    sidebarHome: "Inicio",
    sidebarSimulacion: "Simulación",
    sidebarJugadores: "Jugadores",
    sidebarEstadisticas: "Estadísticas",
    sidebarConfiguracion: "Configuración",
    sidebarConfiguracionGeneral: "General",
    sidebarConfiguracionAvanzado: "Avanzado",
    sidebarConfiguracionLogout: "Salir",
    sidebarLogout: "Salir",
    sidebarNuevaSimulacion: "Nueva Simulación",
    sidebarHistorial: "Historial",
    headerDocumentacion: "Documentación del modelo",
    headerCreditos: "Créditos / Sobre el TFG",
    hero_desc: "Simulador avanzado de tenis basado en atributos realistas de los jugadores.\nExplora cómo la técnica, la condición física y la fortaleza mental influyen en cada punto.",
    hero_button: "Comenzar Simulación",

    // =============================
    // SECCIÓN "CARACTERÍSTICAS"
    // =============================
    caracteristicasTitle: "Características Principales",
    caracteristicasDesc: "Un simulador avanzado que combina estadística, física y psicología del tenis para recrear el juego profesional con realismo.",
    caracteristica1Title: "Análisis Estadístico",
    caracteristica1Desc: "Modelo probabilístico que evalúa el rendimiento punto a punto según factores técnicos, físicos y mentales.",
    caracteristica2Title: "Parámetros Ajustables",
    caracteristica2Desc: "Modifica atributos como saque, consistencia o mentalidad y crea simulaciones personalizadas.",
    caracteristica3Title: "Simulación en Tiempo Real",
    caracteristica3Desc: "Observa cada punto, juego y set con visualizaciones dinámicas y métricas instantáneas.",
    
    // =============================
    // SECCIÓN "CÓMO FUNCIONA"
    // =============================
    comoFuncionaTitle: "¿Cómo Funciona?",
    comoFuncionaDesc: "Tres pasos simples para crear y ejecutar tu simulación.",
    paso1Title: "Configura los Jugadores",
    paso1Desc: "Define los atributos técnicos, físicos y mentales de cada jugador, o utiliza valores de ejemplo inspirados en tenistas profesionales.",
    paso2Title: "Ajusta las Condiciones",
    paso2Desc: "Elige el formato del partido, tipo de pista y factores externos que influyen en el rendimiento.",
    paso3Title: "Observa y Analiza",
    paso3Desc: "Ejecuta la simulación punto a punto y consulta estadísticas detalladas al final del partido.",

    // =============================
    // SECCIÓN "ESTADÍSTICAS"
    // =============================
    estadisticasTitle: "Impulsado por Simulación Realista",
    estadisticasAttr: "Atributos por jugador",
    estadisticasMatches: "Partidos simulados",
    estadisticasConsistencia: "Consistencia estadística",
    estadisticasConsistenciaAlta: "Alta",
    estadisticasDisponible: "Disponible en cualquier momento",

    // =============================
    // SECCIÓN "CALL TO ACTION FINAL"
    // =============================
    ctaTitle: "¿Listo para Comenzar?",
    ctaDesc: "Descubre cómo los factores técnicos, físicos y mentales influyen en cada punto del partido.",
    ctaButton: "Iniciar Simulación Ahora",

    // =============================
    // FOOTER
    // =============================
    footerRecursos: "Recursos",
    footerProyecto: "Proyecto",
    footerEnlaces: "Enlaces Útiles",
    footerLegal: "Legal",

    footerDocModelo: "Documentación del Modelo",
    footerTutoriales: "Tutoriales",
    footerAnalisis: "Análisis de Resultados",
    footerAPI: "API Documentación",
    footerEjemplos: "Ejemplos de Uso",

    footerSobreTFG: "Sobre el TFG",
    footerCreditos: "Créditos",
    footerMetodologia: "Metodología",

    footerContacto: "Contacto",
    footerFAQs: "FAQs",
    footerSoporte: "Soporte",

    footerPrivacidad: "Privacidad",
    footerTerminos: "Términos de Uso",
    footerLicencia: "Licencia",

    footerCopyright: "© 2025 ADAF Tennis Simulator · Trabajo Fin de Grado · Universidad Complutense de Madrid",

    // =============================
    // RESUMEN DEL PARTIDO
    // =============================
    summaryChampion:         "CAMPEÓN",
    summaryWins:             "Gana el Partido",
    summaryMatchStats:       "Estadísticas del Partido",
    summaryVersus:           "vs",
    /* Secciones */
    summarySectionServe:     "Saque",
    summarySectionReturn:    "Resto",
    summarySectionPoints:    "Puntos",
    /* Saque */
    summaryAces:             "Aces",
    summaryDoubleFaults:     "Dobles Faltas",
    summaryFirstServePct:    "1.er Saque %",
    summaryPtsOn1st:         "Puntos en 1.er Saque %",
    summaryPtsOn2nd:         "Puntos en 2.º Saque %",
    summaryServicePtsWon:    "Pts. de Saque Ganados %",
    /* Resto */
    summaryReturnPtsWon:     "Pts. de Resto Ganados %",
    summaryBreakPoints:      "Break Points",
    summaryBPSaved:          "Break Points Salvados",
    /* Puntos */
    summaryTotalPtsPlayed:   "Puntos Jugados",
    summaryTotalPoints:      "Puntos Ganados",
    summaryTotalPtsWonPct:   "Puntos Ganados %",
    summaryWinners:          "Winners",
    summaryUnforcedErrors:   "Errores No Forzados",
    summaryWinnerUERatio:    "Ratio Winners / ENF",
    summaryAvgRally:         "Media de Rally",
    summaryMaxRally:         "Rally Más Largo",
    /* Gráficas */
    summaryReturnPts:        "Puntos de Resto",
    summaryPointsChart:      "Distribución de Puntos",
    summaryKeyStatsChart:    "Estadísticas Clave",
    summaryServeReturnChart: "Saque & Resto",
    summaryRallyChart:       "Duración de los Puntos",
    summaryShots:            "golpes",
    summaryBtnNewMatch:      "Nueva Simulación",
    summaryBtnViewSim:       "Ver Simulación",
    summaryBtnGoToSummary:   "Ver Resumen del Partido",
    summaryNoData:           "No hay datos de partido disponibles.",
    summaryReturnToSim:      "Volver a la Simulación",

    // =============================
    // MODO BIG DATA
    // =============================
    sidebarBigData:          "Modo Big Data",
    bigdataTitle:            "Modo Big Data",
    bigdataSubtitle:         "Simula cientos o miles de partidos y analiza patrones estadísticos.",
    bigdataConfigTitle:      "Configuración de la Simulación",
    bigdataNumMatches:       "Número de Partidos",
    bigdataTimeEstimate:     "Tiempo estimado",
    bigdataStartBtn:         "Iniciar Simulación Masiva",
    bigdataSimulating:       "Simulando...",
    bigdataComplete:         "¡Simulación Completada!",
    bigdataResultsTitle:     "Resultados Big Data",
    bigdataNoData:           "No hay datos de simulación. Ejecuta una simulación primero.",
    bigdataNewSim:           "Nueva Simulación",
    bigdataGoMenu:           "Volver al Menú",
    bigdataExportCSV:        "Exportar CSV",
    bigdataWinDistribution:  "Distribución de Victorias",
    bigdataScoreDistribution:"Distribución de Resultados",
    bigdataSetScores:        "Marcadores de Sets Más Frecuentes",
    bigdataCompStats:        "Estadísticas Comparativas (Promedio por Partido)",
    bigdataWinProgression:   "Progresión del Win Rate",
    bigdataRadar:            "Comparativa General",
    bigdataRallyDist:        "Distribución de Duración de Puntos",
    bigdataKeyTotals:        "Totales Acumulados",
    bigdataPerMatch:         "por partido",
    bigdataAvgPoints:        "Puntos Promedio",
    bigdataAvgSets:          "Sets Promedio",

  },
  en: {
    // ********************************
    // ********** INDEX.HTML **********
    // ********************************

    // =============================
    // SIDEBAR Y HEADER
    // =============================
    sidebarMenu: "Menu",
    sidebarHome: "Home",
    sidebarSimulacion: "Simulation",
    sidebarJugadores: "Players",
    sidebarEstadisticas: "Statistics",
    sidebarConfiguracion: "Settings",
    sidebarConfiguracionGeneral: "General",
    sidebarConfiguracionAvanzado: "Advanced",
    sidebarConfiguracionLogout: "Exit",
    sidebarLogout: "Exit",
    sidebarNuevaSimulacion: "New Simulation",
    sidebarHistorial: "History",
    headerDocumentacion: "Model Documentation",
    headerCreditos: "Credits / About Project",
    hero_desc: "Advanced tennis simulator powered by realistic player attributes.\nExperience how technique, fitness, and mental strength shape\nevery point.",
    hero_button: "Start Simulation",

    // =============================
    // SECCIÓN "CARACTERÍSTICAS"
    // =============================
    caracteristicasTitle: "Key Features",
    caracteristicasDesc: "An advanced simulator that blends statistics, physics, and psychology to recreate professional tennis with realism.",
    caracteristica1Title: "Statistical Analysis",
    caracteristica1Desc: "Probabilistic model evaluating point-by-point performance from technical, physical, and mental factors.",
    caracteristica2Title: "Adjustable Parameters",
    caracteristica2Desc: "Edit attributes like serve, consistency, or mindset to create custom simulations.",
    caracteristica3Title: "Real-Time Simulation",
    caracteristica3Desc: "Follow every point, game, and set with dynamic visuals and instant feedback.",

    // =============================
    // SECCIÓN "CÓMO FUNCIONA"
    // =============================
    comoFuncionaTitle: "How It Works",
    comoFuncionaDesc: "Three simple steps to create and run your simulation.",
    paso1Title: "Set the Players",
    paso1Desc: "Define each player's technical, physical, and mental attributes, or use example values inspired by professional players.",
    paso2Title: "Adjust the Conditions",
    paso2Desc: "Choose match format, court surface, and external factors that affect performance.",
    paso3Title: "Watch and Analyze",
    paso3Desc: "Run the point-by-point simulation and explore detailed stats after the match.",

    // =============================
    // SECCIÓN "ESTADÍSTICAS"
    // =============================
    estadisticasTitle: "Powered by Realistic Simulation",
    estadisticasAttr: "Attributes per player",
    estadisticasMatches: "Matches simulated",
    estadisticasConsistencia: "Statistical consistency",
    estadisticasConsistenciaAlta: "High",
    estadisticasDisponible: "Available anytime",

    // =============================
    // SECCIÓN "CALL TO ACTION FINAL"
    // =============================
    ctaTitle: "Ready to Get Started?",
    ctaDesc: "Explore how technical, physical, and mental factors influence every point.",
    ctaButton: "Start Simulation Now",

    // =============================
    // FOOTER
    // =============================
    footerRecursos: "Resources",
    footerProyecto: "Project",
    footerEnlaces: "Helpful Links",
    footerLegal: "Legal",

    footerDocModelo: "Model Documentation",
    footerTutoriales: "Tutorials",
    footerAnalisis: "Results Analysis",
    footerAPI: "API Documentation",
    footerEjemplos: "Usage Examples",

    footerSobreTFG: "About the Project",
    footerCreditos: "Credits",
    footerMetodologia: "Methodology",

    footerContacto: "Contact",
    footerFAQs: "FAQs",
    footerSoporte: "Support",

    footerPrivacidad: "Privacy",
    footerTerminos: "Terms of Use",
    footerLicencia: "License",

    footerCopyright: "© 2025 ADAF Tennis Simulator · Final Degree Project · UCM",

    // =============================
    // RESUMEN DEL PARTIDO
    // =============================
    summaryChampion:         "CHAMPION",
    summaryWins:             "Wins the Match",
    summaryMatchStats:       "Match Statistics",
    summaryVersus:           "vs",
    /* Sections */
    summarySectionServe:     "Serve",
    summarySectionReturn:    "Return",
    summarySectionPoints:    "Points",
    /* Serve */
    summaryAces:             "Aces",
    summaryDoubleFaults:     "Double Faults",
    summaryFirstServePct:    "1st Serve %",
    summaryPtsOn1st:         "Points on 1st Serve %",
    summaryPtsOn2nd:         "Points on 2nd Serve %",
    summaryServicePtsWon:    "Service Pts. Won %",
    /* Return */
    summaryReturnPtsWon:     "Return Pts. Won %",
    summaryBreakPoints:      "Break Points",
    summaryBPSaved:          "Break Points Saved",
    /* Points */
    summaryTotalPtsPlayed:   "Points Played",
    summaryTotalPoints:      "Points Won",
    summaryTotalPtsWonPct:   "Points Won %",
    summaryWinners:          "Winners",
    summaryUnforcedErrors:   "Unforced Errors",
    summaryWinnerUERatio:    "Winner / UE Ratio",
    summaryAvgRally:         "Avg. Rally Length",
    summaryMaxRally:         "Longest Rally",
    /* Charts */
    summaryReturnPts:        "Return Points",
    summaryPointsChart:      "Points Distribution",
    summaryKeyStatsChart:    "Key Statistics",
    summaryServeReturnChart: "Serve & Return",
    summaryRallyChart:       "Rally Length",
    summaryShots:            "shots",
    summaryBtnNewMatch:      "New Simulation",
    summaryBtnViewSim:       "Watch Simulation",
    summaryBtnGoToSummary:   "View Match Summary",
    summaryNoData:           "No match data available.",
    summaryReturnToSim:      "Back to Simulation",

    // =============================
    // BIG DATA MODE
    // =============================
    sidebarBigData:          "Big Data Mode",
    bigdataTitle:            "Big Data Mode",
    bigdataSubtitle:         "Simulate hundreds or thousands of matches and analyze statistical patterns.",
    bigdataConfigTitle:      "Simulation Configuration",
    bigdataNumMatches:       "Number of Matches",
    bigdataTimeEstimate:     "Estimated time",
    bigdataStartBtn:         "Start Mass Simulation",
    bigdataSimulating:       "Simulating...",
    bigdataComplete:         "Simulation Complete!",
    bigdataResultsTitle:     "Big Data Results",
    bigdataNoData:           "No simulation data. Run a simulation first.",
    bigdataNewSim:           "New Simulation",
    bigdataGoMenu:           "Back to Menu",
    bigdataExportCSV:        "Export CSV",
    bigdataWinDistribution:  "Win Distribution",
    bigdataScoreDistribution:"Score Distribution",
    bigdataSetScores:        "Most Frequent Set Scores",
    bigdataCompStats:        "Comparative Stats (Avg. per Match)",
    bigdataWinProgression:   "Win Rate Progression",
    bigdataRadar:            "Overall Comparison",
    bigdataRallyDist:        "Rally Length Distribution",
    bigdataKeyTotals:        "Cumulative Totals",
    bigdataPerMatch:         "per match",
    bigdataAvgPoints:        "Avg. Points",
    bigdataAvgSets:          "Avg. Sets",

  }
};

// Selección de idioma
const langButtons = {
  es: document.getElementById("lang-es"),
  en: document.getElementById("lang-en")
};

function setLanguage(lang) {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (translations[lang][key]) {
      el.innerText = translations[lang][key];
    }
  });
  localStorage.setItem("lang", lang);
  document.documentElement.lang = lang;

  // Cambia el estilo de la bandera activa
  langButtons.es.classList.toggle("border-2", lang === "es");
  langButtons.es.classList.toggle("border-yellow-400", lang === "es");
  langButtons.en.classList.toggle("border-2", lang === "en");
  langButtons.en.classList.toggle("border-yellow-400", lang === "en");
}

// Listeners
langButtons.es.addEventListener("click", () => setLanguage("es"));
langButtons.en.addEventListener("click", () => setLanguage("en"));

// Cargar idioma guardado
const savedLang = localStorage.getItem("lang") || "es";
setLanguage(savedLang);
