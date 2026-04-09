# Plan de Implementación — Modo Big Data

## 1. Resumen

El Modo Big Data permitirá simular **N partidos** (desde decenas hasta miles) entre dos jugadores con la misma configuración, y presentar los resultados como estadísticas agregadas: promedios, distribuciones, porcentajes de victoria, tendencias y rankings de métricas. El flujo del usuario será:

1. **Pantalla de configuración** → elegir jugadores, superficie, formato, nº de partidos y opciones de análisis.
2. **Pantalla de progreso** → barra de carga con feedback en tiempo real mientras se simulan los partidos.
3. **Pantalla de resultados** → dashboard rico con estadísticas agregadas, gráficos comparativos y opción de exportar datos.

---

## 2. Arquitectura actual (puntos clave)

| Capa | Detalle |
|------|---------|
| **Motor de simulación** | `backend/simulator/` — `run_match()` ejecuta 1 partido completo (~0.01-0.05 s por partido). Devuelve `dict` con `timeline`, `set_scores`, `winner_id`, `player_stats`, etc. |
| **Endpoint actual** | `POST /api/simulate_match` — recibe `player1`, `player2`, `config` y devuelve resultado de **1 partido**. |
| **Extracción de stats** | `extract_player_stats(timeline)` agrega: aces, dobles faltas, 1er saque %, winners, UE, break points, puntos ganados. |
| **Frontend** | `partido_rapido.html` → configura → `sessionStorage` → `simulacion2.html` reproduce punto a punto → `resumen.html` muestra stats finales. |
| **Menú** | `menu.html` CARD 3 "Modo Big Data" con `onclick → '#'` (no implementado). |
| **Page router** | `backend/app/routes/pages.py` — rutas Jinja2 para cada template; helper `_placeholder()` para rutas sin implementar. |

---

## 3. Cambios necesarios — Backend

### 3.1 Nuevo endpoint: `POST /api/bigdata/simulate`

**Archivo:** `backend/app/routes/api.py` (o nuevo archivo `backend/app/bigdata/routes.py` + `__init__.py` si se prefiere separar)

**Request body:**
```python
class BigDataRequest(BaseModel):
    player1: PlayerData          # Mismos campos que MatchRequest
    player2: PlayerData
    config: ConfigData           # best_of, tiebreak, superficie
    num_matches: int             # Nº de partidos a simular (10 – 10 000)
    seed: int | None = None      # Semilla global opcional para reproducibilidad
```

**Validaciones:**
- `num_matches` entre 10 y 10 000 (configurable; evitar abuso).
- Misma validación de atributos que `simulate_match`.

**Lógica principal:**
```python
@router.post("/bigdata/simulate")
async def bigdata_simulate(request: BigDataRequest, ...):
    results = []
    for i in range(request.num_matches):
        seed_i = (request.seed + i) if request.seed else None
        cfg = {**request.config.model_dump(exclude={"superficie"}), "seed": seed_i}
        result = run_match(
            player1_data=request.player1.model_dump(),
            player2_data=request.player2.model_dump(),
            config=cfg,
        )
        result["player_stats"] = extract_player_stats(result["timeline"])
        results.append(result)

    aggregated = aggregate_bigdata_stats(results, request.player1.name, request.player2.name)
    return aggregated
```

> **Nota sobre rendimiento:** Cada partido se ejecuta en ~10-50 ms. 10 000 partidos ≈ 100-500 s bloqueando el hilo. Para simulaciones grandes (>500 partidos) se recomiendan dos opciones progresivas:
>
> - **Fase 1 (MVP):** Ejecutar de forma síncrona pero con `StreamingResponse` de progreso (ver §3.3).
> - **Fase 2 (optimización futura):** Usar `concurrent.futures.ProcessPoolExecutor` para paralelizar en N cores. `run_match` ya es puro y sin estado global.

### 3.2 Función de agregación: `aggregate_bigdata_stats()`

**Archivo nuevo:** `backend/app/bigdata/aggregation.py`

Esta función recibe la lista de resultados y calcula las estadísticas Big Data.

**Estructura de respuesta:**
```python
{
    "meta": {
        "total_matches": 1000,
        "player1": "Nadal",
        "player2": "Federer",
        "config": { "best_of": 3, "tiebreak": true, "superficie": "Arcilla" }
    },

    # ── Resultado general ──
    "win_rate": {
        "P1": { "wins": 583, "pct": 58.3 },
        "P2": { "wins": 417, "pct": 41.7 }
    },

    # ── Distribución de marcadores ──
    "score_distribution": {
        "2-0": 312,   # nº de partidos que acabaron 2-0
        "2-1": 271,
        "0-2": 198,
        "1-2": 219
    },

    # ── Sets ganados totales ──
    "total_sets": {
        "P1": { "won": 1437, "lost": 1120 },
        "P2": { "won": 1120, "lost": 1437 }
    },

    # ── Estadísticas promedio por partido (para cada jugador) ──
    "avg_stats": {
        "P1": {
            "aces": 4.2,
            "dobles_faltas": 1.8,
            "primer_saque_pct": 62.5,
            "puntos_ganados_1er_saque": 18.3,
            "puntos_ganados_2do_saque": 8.1,
            "winners": 12.6,
            "errores_no_forzados": 15.2,
            "puntos_ganados_resto": 14.7,
            "total_puntos_ganados": 41.1,
            "break_points_convertidos": 2.3,
            "break_points_oportunidades": 5.1,
            "bp_conversion_pct": 45.1
        },
        "P2": { ... }
    },

    # ── Estadísticas totales acumuladas ──
    "total_stats": {
        "P1": {
            "aces": 4200,
            "dobles_faltas": 1800,
            ...
        },
        "P2": { ... }
    },

    # ── Métricas de duración ──
    "match_length": {
        "avg_points": 142.3,
        "min_points": 68,
        "max_points": 254,
        "avg_duration_min": 83,
        "avg_sets": 2.49
    },

    # ── Distribución de longitud de rallies ──
    "rally_distribution": {
        "1": 12300,       # aces + dobles faltas
        "2": 8400,        # resto y punto
        "3-5": 31200,
        "6-10": 18900,
        "11+": 5200
    },

    # ── Datos para gráficos de tendencia (win rate acumulativo) ──
    "win_rate_progression": [
        { "match": 100, "p1_pct": 56.0, "p2_pct": 44.0 },
        { "match": 200, "p1_pct": 57.5, "p2_pct": 42.5 },
        ...
    ],

    # ── Top marcadores más frecuentes ──
    "set_score_frequency": {
        "6-4": 423,
        "6-3": 389,
        "7-5": 312,
        "7-6": 287,
        "6-2": 201,
        ...
    }
}
```

### 3.3 Streaming de progreso (opcional pero recomendado)

Para que el frontend pueda mostrar una barra de progreso mientras se simulan miles de partidos, se puede usar **Server-Sent Events (SSE)** con `StreamingResponse`:

**Endpoint alternativo:** `POST /api/bigdata/simulate_stream`

```python
from fastapi.responses import StreamingResponse
import json

async def bigdata_stream(request: BigDataRequest):
    async def generate():
        results = []
        for i in range(request.num_matches):
            result = run_match(...)
            result["player_stats"] = extract_player_stats(result["timeline"])
            results.append(result)

            # Enviar progreso cada 10 partidos o cada 1%
            if (i + 1) % max(1, request.num_matches // 100) == 0:
                progress = {
                    "type": "progress",
                    "current": i + 1,
                    "total": request.num_matches,
                    "pct": round((i + 1) / request.num_matches * 100, 1)
                }
                yield f"data: {json.dumps(progress)}\n\n"

        # Enviar resultado final
        aggregated = aggregate_bigdata_stats(results, ...)
        yield f"data: {json.dumps({'type': 'result', 'data': aggregated})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 3.4 Organización final de archivos backend

```
backend/app/bigdata/
    __init__.py
    routes.py          # Endpoints /api/bigdata/simulate y /api/bigdata/simulate_stream
    aggregation.py     # aggregate_bigdata_stats()
    schemas.py         # BigDataRequest, BigDataResponse (Pydantic models)
```

Registrar en `main.py`:
```python
from backend.app.bigdata.routes import router as bigdata_router
app.include_router(bigdata_router, prefix="/api/bigdata", tags=["bigdata"])
```

### 3.5 Base de datos (opcional, fase futura)

Para una primera versión **no es necesario guardar** cada partido individual en la BD todos las miles de simulaciones. Pero sí se podría añadir una tabla para guardar **sesiones Big Data**:

```sql
CREATE TABLE bigdata_sesiones (
    id            SERIAL PRIMARY KEY,
    id_usuario    INT REFERENCES usuarios(id),
    id_jugador_1  INT REFERENCES jugadores(id),
    id_jugador_2  INT REFERENCES jugadores(id),
    num_partidos  INT NOT NULL,
    superficie    VARCHAR(20),
    formato_sets  INT,
    resultados    JSONB NOT NULL,    -- JSON con todo el aggregated
    fecha_creado  TIMESTAMP DEFAULT NOW()
);
```

Esto permitiría guardar y consultar sesiones anteriores para comparar. Es **opcional para la versión 1**.

---

## 4. Cambios necesarios — Frontend

### 4.1 Nueva ruta de página

**Archivo:** `backend/app/routes/pages.py`

```python
@router.get("/bigdata", response_class=HTMLResponse)
def bigdata(request: Request):
    return templates.TemplateResponse(
        "bigdata.html", {"request": request, "active_page": "bigdata"}
    )

@router.get("/bigdata/resultados", response_class=HTMLResponse)
def bigdata_resultados(request: Request):
    return templates.TemplateResponse(
        "bigdata_resultados.html", {"request": request, "active_page": "bigdata"}
    )
```

### 4.2 Actualizar menú

**Archivo:** `templates/menu.html`

Cambiar CARD 3:
```html
onclick="window.location.href='/bigdata'"
```

### 4.3 Template de configuración: `templates/bigdata.html`

**Layout:** Sigue `layouts/base.html` con sidebar.

**Estructura de la página:**

```
┌──────────────────────────────────────────────────────┐
│  HEADER: "Modo Big Data" + icono gráfico             │
│  Subtítulo: "Simulación masiva para análisis         │
│             estadístico profundo"                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────┐    ┌────────────────┐            │
│  │  JUGADOR 1     │ VS │  JUGADOR 2     │            │
│  │  (selección)   │    │  (selección)   │            │
│  │  Card FIFA     │    │  Card FIFA     │            │
│  └────────────────┘    └────────────────┘            │
│                                                      │
│  ── Configuración del Análisis ──                    │
│                                                      │
│  Nº de partidos:  [slider + input: 100-10000]        │
│  Presets rápidos:  [100] [500] [1000] [5000] [10000] │
│                                                      │
│  Superficie:   [Dura] [Arcilla] [Hierba]             │
│  Formato:       [1 set] [3 sets] [5 sets]            │
│  Tiebreak:      [toggle]                             │
│                                                      │
│  ┌──────────────────────────────────────┐            │
│  │  Resumen: "5000 partidos al mejor   │            │
│  │  de 3 sets en Arcilla"              │            │
│  │                                      │            │
│  │  [🚀 Iniciar Simulación Big Data]    │            │
│  └──────────────────────────────────────┘            │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Componentes reutilizables:** La selección de jugadores y configuración de superficie/formato se puede modelar igual que en `partido_rapido.html` (grids de cards con selección, cards FIFA tier-color, botones de superficie). Reutilizar los mismos estilos Tailwind.

**Componente nuevo:** Slider numérico para nº de partidos con presets rápidos (botones que setean valores predefinidos) y actualización en tiempo real de la estimación: *"Tiempo estimado: ~25 segundos"*.

### 4.4 Template de progreso/carga (integrado en `bigdata.html`)

Cuando el usuario pulsa "Iniciar Simulación", el contenido de la página se transforma en una vista de progreso (sin cambio de URL, misma página):

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│         ⚡ Simulando partidos...                     │
│                                                      │
│    ███████████████████░░░░░░░░░░░  67%               │
│                                                      │
│    3350 / 5000 partidos completados                  │
│                                                      │
│    ┌─────────────────────────────────┐               │
│    │  🏆 P1 lidera: 58.2% - 41.8%  │               │
│    │  ⏱  Duración media: 142 pts   │               │
│    │  🎯 Aces media: 4.2 / 3.1     │               │
│    └─────────────────────────────────┘               │
│                                                      │
│    Estadísticas en vivo actualizándose...            │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Implementación SSE en JavaScript:**
```javascript
const evtSource = new EventSource('/api/bigdata/simulate_stream', { ... });
// O bien fetch + ReadableStream para POST requests:

const response = await fetch('/api/bigdata/simulate_stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(payload)
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const text = decoder.decode(value);
    // Parsear líneas SSE, actualizar barra de progreso y stats en vivo
}
```

### 4.5 Template de resultados: `templates/bigdata_resultados.html`

**Dashboard completo de resultados.** Es la pantalla "estrella" del modo. Se accede automáticamente cuando termina la simulación (se guardan datos en `sessionStorage` y se redirige, o se renderiza en la misma página).

**Layout del dashboard:**

```
┌──────────────────────────────────────────────────────────────┐
│  HEADER: "Resultados Big Data"                               │
│  "5000 partidos · Nadal vs Federer · Arcilla · Bo3"          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ── SECCIÓN 1: RESUMEN GENERAL ──                            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  WIN RATE  │  │ AVG PUNTOS │  │ AVG SETS   │             │
│  │  P1: 58.3% │  │   142.3    │  │   2.49     │             │
│  │  P2: 41.7% │  │            │  │            │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                              │
│  ┌─────────────────────────────────────────────┐             │
│  │  GRÁFICO DONUT: Victoria P1 vs P2           │             │
│  │  (grande, centrado, con porcentajes)        │             │
│  └─────────────────────────────────────────────┘             │
│                                                              │
│  ── SECCIÓN 2: DISTRIBUCIÓN DE MARCADORES ──                 │
│                                                              │
│  ┌──────────────────────────────────────────┐                │
│  │  GRÁFICO BARRAS: Frecuencia de resultados│                │
│  │  2-0 ████████████████  31.2%             │                │
│  │  2-1 ████████████      27.1%             │                │
│  │  0-2 ██████████        19.8%             │                │
│  │  1-2 ███████████       21.9%             │                │
│  └──────────────────────────────────────────┘                │
│                                                              │
│  ┌──────────────────────────────────────────┐                │
│  │  GRÁFICO BARRAS: Marcadores parciales    │                │
│  │  más frecuentes                          │                │
│  │  6-4: ████████  423                      │                │
│  │  6-3: ███████   389                      │                │
│  │  7-5: ██████    312                      │                │
│  │  7-6: █████     287                      │                │
│  │  6-2: ████      201                      │                │
│  └──────────────────────────────────────────┘                │
│                                                              │
│  ── SECCIÓN 3: ESTADÍSTICAS COMPARATIVAS ──                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  TABLA ATP-STYLE (como resumen.html pero con medias) │    │
│  │  Stat              P1 (avg)    P2 (avg)              │    │
│  │  ─────────────────────────────────────────           │    │
│  │  Aces              4.2         3.1                   │    │
│  │  Dobles faltas     1.8         2.3                   │    │
│  │  1er Saque %       62.5%       59.8%                 │    │
│  │  Pts 1er saque     18.3        16.9                  │    │
│  │  Pts 2do saque     8.1         7.4                   │    │
│  │  Winners           12.6        11.8                  │    │
│  │  Errores NF        15.2        16.7                  │    │
│  │  Pts resto          14.7        13.2                  │    │
│  │  BP convertidos    2.3         1.9                   │    │
│  │  BP oportunidades  5.1         4.8                   │    │
│  │  BP conv. %        45.1%       39.6%                 │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ── SECCIÓN 4: GRÁFICOS AVANZADOS ──                         │
│                                                              │
│  ┌───────────────────────┐ ┌───────────────────────┐         │
│  │ LÍNEA: Win rate       │ │ RADAR: Comparación    │         │
│  │ acumulativo a lo      │ │ media de stats de     │         │
│  │ largo de los N        │ │ ambos jugadores       │         │
│  │ partidos              │ │ (saque, resto...)     │         │
│  └───────────────────────┘ └───────────────────────┘         │
│                                                              │
│  ┌───────────────────────┐ ┌───────────────────────┐         │
│  │ HISTOGRAMA: Distrib.  │ │ BARRAS AGRUPADAS:     │         │
│  │ de longitud de rally  │ │ Totales acumulados    │         │
│  │ (1, 2, 3-5, 6-10,11+)│ │ (aces, UE, winners)   │         │
│  └───────────────────────┘ └───────────────────────┘         │
│                                                              │
│  ── SECCIÓN 5: ACCIONES ──                                   │
│                                                              │
│  [📊 Exportar CSV]  [🔄 Nueva Simulación]  [🏠 Menú]       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Gráficos:** Usar **Chart.js** (ya es dependencia del proyecto, usado en `resumen.html`).

### 4.6 Archivos JavaScript nuevos

```
static/js/bigdata/
    config.js        # Lógica de la página de configuración (selección jugadores, slider, validaciones)
    simulation.js    # Conexión SSE/fetch streaming, actualización de barra de progreso
    results.js       # Renderizado del dashboard de resultados (gráficos, tablas, datos)
```

### 4.7 Actualizar sidebar

**Archivo:** `templates/partials/sidebar.html`

Añadir enlace "Big Data" / "Análisis Masivo" bajo la sección de simulación, con el icono de barras:

```html
<a href="/bigdata" class="sidebar-item" data-page="bigdata">
    <svg ...><!-- bar chart icon --></svg>
    <span data-i18n="sidebarBigData">Análisis Masivo</span>
</a>
```

### 4.8 Actualizar i18n

**Archivo:** `static/js/lang.js`

Añadir traducciones para todas las claves nuevas del modo Big Data (títulos, labels de stats, botones, etc.) tanto en `es` como en `en`.

---

## 5. Orden de implementación (fases)

### Fase 1 — Backend core (sin streaming)

| # | Tarea | Archivos |
|---|-------|----------|
| 1.1 | Crear módulo `backend/app/bigdata/` con `__init__.py`, `schemas.py` | Nuevos |
| 1.2 | Implementar `aggregate_bigdata_stats()` en `aggregation.py` | Nuevo |
| 1.3 | Implementar endpoint `POST /api/bigdata/simulate` (síncrono) | `bigdata/routes.py` |
| 1.4 | Registrar router en `main.py` | `backend/app/main.py` |
| 1.5 | Test manual: `curl` o script Python enviando 100 partidos | Verificación |

### Fase 2 — Frontend: configuración

| # | Tarea | Archivos |
|---|-------|----------|
| 2.1 | Crear `templates/bigdata.html` con layout de configuración | Nuevo |
| 2.2 | Crear `static/js/bigdata/config.js` (selección jugadores, sliders) | Nuevo |
| 2.3 | Añadir ruta `/bigdata` en `pages.py` | `routes/pages.py` |
| 2.4 | Actualizar `onclick` en CARD 3 del menú | `menu.html` |
| 2.5 | Actualizar sidebar con enlace Big Data | `sidebar.html` |

### Fase 3 — Frontend: progreso + resultados

| # | Tarea | Archivos |
|---|-------|----------|
| 3.1 | Crear `static/js/bigdata/simulation.js` (fetch + barra progreso) | Nuevo |
| 3.2 | Añadir vista de progreso en `bigdata.html` (toggle con JS) | `bigdata.html` |
| 3.3 | Crear `templates/bigdata_resultados.html` (dashboard) | Nuevo |
| 3.4 | Crear `static/js/bigdata/results.js` (Chart.js graphs, tablas) | Nuevo |
| 3.5 | Añadir ruta `/bigdata/resultados` en `pages.py` | `routes/pages.py` |

### Fase 4 — Streaming de progreso (mejora)

| # | Tarea | Archivos |
|---|-------|----------|
| 4.1 | Implementar `POST /api/bigdata/simulate_stream` con SSE | `bigdata/routes.py` |
| 4.2 | Actualizar `simulation.js` para usar `ReadableStream` | `simulation.js` |
| 4.3 | Mostrar stats parciales en vivo durante la carga | `bigdata.html` |

### Fase 5 — Pulido y extras

| # | Tarea | Archivos |
|---|-------|----------|
| 5.1 | Añadir traducciones i18n | `lang.js` |
| 5.2 | Animaciones de entrada y transiciones | `styles.css` |
| 5.3 | Exportar resultados a CSV | `results.js` |
| 5.4 | (Opcional) Guardar sesiones Big Data en BD | `bigdata/models.py`, `newDB.sql` |
| 5.5 | Tests automatizados del endpoint | `test_bigdata.py` |

---

## 6. Estimación de estructura de archivos nuevos

```
backend/app/bigdata/
    __init__.py
    routes.py              # Endpoints simulate y simulate_stream
    schemas.py             # BigDataRequest, BigDataResponse
    aggregation.py         # aggregate_bigdata_stats()

templates/
    bigdata.html           # Configuración + vista de progreso
    bigdata_resultados.html  # Dashboard de resultados

static/js/bigdata/
    config.js              # Lógica de configuración
    simulation.js          # Fetch/SSE + progreso
    results.js             # Gráficos y tablas de resultados

# Archivos modificados:
backend/app/main.py         # Registrar bigdata_router
backend/app/routes/pages.py # Nuevas rutas /bigdata y /bigdata/resultados
templates/menu.html         # CARD 3 onclick → '/bigdata'
templates/partials/sidebar.html  # Nuevo enlace
static/js/lang.js           # Traducciones
```

---

## 7. Consideraciones técnicas

### 7.1 Rendimiento

- **`run_match()` es puro** (sin I/O, sin estado global mutable compartido entre llamadas). Cada llamada crea sus propios objetos `Player` con `reset_dynamic_state()`. Esto lo hace **seguro para paralelizar**.
- Para la fase MVP (síncrono), 1000 partidos tardarán ~10-50 s. Aceptable con barra de progreso.
- Para >2000 partidos, considerar `ProcessPoolExecutor` con `asyncio.run_in_executor()`.
- **No enviar timelines completos** al frontend en Big Data. Solo enviar estadísticas agregadas. Un timeline de 1000 partidos × 150 puntos × acciones sería gigabytes de JSON.

### 7.2 Memoria

- Cada resultado de `run_match()` se puede procesar y descartar inmediatamente (acumular stats e ir soltando el dict). Si se procesan en streaming, el pico de memoria será bajo.
- Alternativa más eficiente: acumular stats incrementalmente sin guardar todos los results:

```python
accum = BigDataAccumulator()
for i in range(num_matches):
    result = run_match(...)
    stats = extract_player_stats(result["timeline"])
    accum.add(result, stats)  # Solo suma contadores; no retiene el dict
final = accum.finalize()  # Calcula promedios
```

### 7.3 Semillas y reproducibilidad

- Si el usuario proporciona una semilla, cada partido usa `seed + i` para ser reproducible pero diferente entre sí.
- Sin semilla → resultados aleatorios puros (cada partido con seed distinta internamente).

### 7.4 Seguridad

- Limitar `num_matches` a un máximo de 10 000 para evitar ataques DoS.
- Rate limiting recomendado (1 simulación Big Data simultánea por usuario).
- No guardar timelines individuales en la respuesta (ahorro de ancho de banda y prevención de abuso).

---

## 8. Dependencias

| Dependencia | Estado | Uso |
|-------------|--------|-----|
| FastAPI | Ya instalada | Backend API |
| Chart.js | Ya cargada (CDN en resumen.html) | Gráficos del dashboard |
| Tailwind CSS | Ya cargada | Estilos |
| Pydantic | Ya instalada | Schemas |
| concurrent.futures | Stdlib Python | Paralelización futura |

**No se necesitan dependencias nuevas.**

---

## 9. Notas de diseño visual

- Seguir el mismo design system existente: fondo `slate-950`, cards `slate-800/50` con `backdrop-blur`, acentos `yellow-400`, bordes `blue-800/30`.
- Gráficos Chart.js con paleta consistente: azul (#3b82f6) para P1, ámbar (#f59e0b) para P2.
- Página de resultados inspirada en dashboards de analytics deportivos (estilo ATP Stats, tennis abstract).
- Animaciones `fade-in-up` escalonadas como en `menu.html`.
- Barra de progreso con degradado amarillo y efecto de brillo (consistent con botones).
- Cards resumen con números grandes y labels pequeños (patrón KPI dashboard).
