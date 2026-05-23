//lang.js
const translations = {
  es: {
    //********************************
    //********** INDEX.HTML **********
    //********************************

    //SIDEBAR Y HEADER
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

    //SECCION "CARACTERÍSTICAS"
    caracteristicasTitle: "Características Principales",
    caracteristicasDesc: "Un simulador avanzado que combina estadística, física y psicología del tenis para recrear el juego profesional con realismo.",
    caracteristica1Title: "Análisis Estadístico",
    caracteristica1Desc: "Modelo probabilístico que evalúa el rendimiento punto a punto según factores técnicos, físicos y mentales.",
    caracteristica2Title: "Parámetros Ajustables",
    caracteristica2Desc: "Modifica atributos como saque, consistencia o mentalidad y crea simulaciones personalizadas.",
    caracteristica3Title: "Simulación en Tiempo Real",
    caracteristica3Desc: "Observa cada punto, juego y set con visualizaciones dinámicas y métricas instantáneas.",
    
    //SECCION "CÓMO FUNCIONA"
    comoFuncionaTitle: "¿Cómo Funciona?",
    comoFuncionaDesc: "Tres pasos simples para crear y ejecutar tu simulación.",
    paso1Title: "Configura los Jugadores",
    paso1Desc: "Define los atributos técnicos, físicos y mentales de cada jugador, o utiliza valores de ejemplo inspirados en tenistas profesionales.",
    paso2Title: "Ajusta las Condiciones",
    paso2Desc: "Elige el formato del partido, tipo de pista y factores externos que influyen en el rendimiento.",
    paso3Title: "Observa y Analiza",
    paso3Desc: "Ejecuta la simulación punto a punto y consulta estadísticas detalladas al final del partido.",

    //SECCION "ESTADÍSTICAS"
    estadisticasTitle: "Impulsado por Simulación Realista",
    estadisticasAttr: "Atributos por jugador",
    estadisticasMatches: "Partidos simulados",
    estadisticasConsistencia: "Consistencia estadística",
    estadisticasConsistenciaAlta: "Alta",
    estadisticasDisponible: "Disponible en cualquier momento",

    //SECCION "CALL TO ACTION FINAL"
    ctaTitle: "¿Listo para Comenzar?",
    ctaDesc: "Descubre cómo los factores técnicos, físicos y mentales influyen en cada punto del partido.",
    ctaButton: "Iniciar Simulación Ahora",

    //FOOTER
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

    //RESUMEN DEL PARTIDO
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

    //MODO BIG DATA
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
    bigdataAvgSets:          "Sets Promedio"
  }
};

function setLanguage(lang) {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (translations[lang] && translations[lang][key]) {
      el.innerText = translations[lang][key];
    }
  });
  localStorage.setItem("lang", "es"); //Force es
  document.documentElement.lang = "es";
}

//Cargar idioma - SIEMPRE EN ESPAÑOL
setLanguage("es");
