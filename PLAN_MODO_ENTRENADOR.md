# Plan de Implementación: Modo Entrenador

## 1. Resumen Ejecutivo

El **Modo Entrenador** es un nuevo modo de juego donde el usuario "entrena" a uno de los dos jugadores durante un partido simulado. A diferencia del modo actual (que simula todo el partido de golpe y luego lo reproduce visualmente), este modo simula **punto a punto bajo demanda**, permitiendo al usuario cambiar la **estrategia táctica** de su jugador entre puntos. Las decisiones del usuario afectan directamente a las fórmulas del motor de simulación, produciendo diferencias reales y perceptibles en el rendimiento.

---

## 2. Análisis del Sistema Actual

### 2.1 Motor de Simulación (Backend)

El motor se compone de los siguientes módulos en `backend/simulator/`:

| Archivo | Responsabilidad |
|---|---|
| `models.py` | Define `Player`, `Ball`, `PointResult`, `MatchStats`, `Config`, `Action` |
| `point.py` | `PointSimulator` — orquesta un punto completo (saque → resto → rally) |
| `shots.py` | `Serve`, `ReturnShot`, `RallyShot` — fórmulas probabilísticas de cada golpe |
| `scoring.py` | `TennisGame`, `TieBreakGame`, `TennisSet`, `TennisMatch` — gestión de marcador |
| `utils.py` | Funciones auxiliares (`clip`, `rand`, constantes `SACADOR`/`RESTADOR`) |
| `api.py` | `run_match()` — punto de entrada que crea jugadores, ejecuta `TennisMatch.play()` y devuelve JSON |

**Flujo actual:**
1. El frontend envía POST a `/api/simulate_match` con datos de ambos jugadores + config.
2. `run_match()` crea objetos `Player`, instancia `TennisMatch` y ejecuta `.play()`.
3. `TennisMatch.play()` simula **todo el partido de una vez** (sets → games → puntos).
4. Se devuelve un JSON con el `timeline` completo (lista de todos los puntos con marcador, acciones, feed, etc.).
5. El frontend carga ese timeline en `state.js` y lo reproduce visualmente punto a punto con los controles (play/pause/next/prev).

### 2.2 Fórmulas Clave del Motor

Las fórmulas que serán afectadas por la estrategia se encuentran en `shots.py`:

**Saque (`Serve`):**
- `pot_base = 0.5*S1 + 0.35*F + 0.15*E` (primer saque)
- `prec_base = 0.42*S1 + 0.38*C + 0.20*E`
- `p_in1 = 0.5 + 0.25*Score` donde Score depende de potencia y precisión

**Resto (`ReturnShot`):**
- `pot_base = 0.35*RET + 0.25*F + 0.20*E + 0.20*side`
- `prec_base = 0.40*RET + 0.25*C + 0.20*side + 0.15*MOV`

**Rally (`RallyShot`):**
- `pot_base = 0.45*F + 0.25*E + 0.20*side + 0.10*C`
- `prec_base = 0.40*C + 0.30*side + 0.20*MOV + 0.10*E`
- `p_in = clip(0.65 + 0.3*(Q_adj - 0.5), 0.05, 0.99)`

### 2.3 Frontend Actual

- **`partido_rapido.html`**: Pantalla de selección de jugadores y configuración → hace POST → guarda resultado en `sessionStorage` → redirige a `simulacion2.html`.
- **`simulacion2.html`**: Visualización del partido con controles de reproducción (play/pause/next/prev/restart/end, velocidad x1/x2/x4).
- **JS Modules** (`static/js/simulacion/`): `app.js`, `api.js`, `state.js`, `controls.js`, `scoreboard.js`, `liveFeed.js`, `summary.js`, `feed/PointFeedGenerator.js`.

### 2.4 Base de Datos

- `jugadores` — atributos del jugador (0-100)
- `partidos` — resultado del partido (marcador, ganador, superficie, etc.)
- `estadisticas_partido` — estadísticas detalladas por jugador por partido
- `usuarios` — autenticación

---

## 3. Diseño del Modo Entrenador

### 3.1 Concepto de Estrategia Táctica

El usuario elige entre **3 estrategias** para su jugador, que se pueden cambiar entre puntos:

| Estrategia | Descripción | Efecto en el Motor |
|---|---|---|
| **Agresivo** 🔥 | Golpes más potentes, mayor riesgo | ↑ Potencia (+15-20%), ↓ Precisión (-10-15%), ↓ p_in (-8-12%) |
| **Neutro** ⚖️ | Juego equilibrado (por defecto) | Sin modificadores (fórmulas base actuales) |
| **Defensivo** 🛡️ | Prioriza consistencia, bolas seguras | ↓ Potencia (-15-20%), ↑ Precisión (+10-15%), ↑ p_in (+8-12%) |

#### 3.1.1 Modificadores Exactos Propuestos

Se propone un sistema de **multiplicadores** que se aplican DESPUÉS del cálculo base de las fórmulas existentes (sin tocar las fórmulas originales, solo multiplicando los resultados):

```
STRATEGY_MODIFIERS = {
    "aggressive": {
        "pot_mult":  1.18,   # +18% potencia en todos los golpes
        "prec_mult": 0.88,   # -12% precisión
        "p_in_mult": 0.90,   # -10% probabilidad de meter la bola
        "reach_mult": 1.05,  # +5% probabilidad de alcanzar (juega más adelantado)
        "sigma_pot_mult": 1.25,  # +25% varianza en potencia (más irregularidad)
        "sigma_prec_mult": 1.30, # +30% varianza en precisión
    },
    "neutral": {
        "pot_mult":  1.00,
        "prec_mult": 1.00,
        "p_in_mult": 1.00,
        "reach_mult": 1.00,
        "sigma_pot_mult": 1.00,
        "sigma_prec_mult": 1.00,
    },
    "defensive": {
        "pot_mult":  0.82,   # -18% potencia
        "prec_mult": 1.12,   # +12% precisión
        "p_in_mult": 1.10,   # +10% probabilidad de meter la bola
        "reach_mult": 1.10,  # +10% alcance (juega más atrás, llega a más bolas)
        "sigma_pot_mult": 0.80,  # -20% varianza (más regular)
        "sigma_prec_mult": 0.75, # -25% varianza (más consistente)
    },
}
```

> **Principio de diseño:** Los modificadores se notan de forma clara pero no rompen el realismo. Un jugador agresivo puede ganar puntos rápidos con winners pero fallará más errores no forzados. Un defensivo mantendrá la bola en juego, prolongando rallies.

#### 3.1.2 Instrucciones Tácticas Adicionales (Extensiones Futuras)

Además de la estrategia general, se pueden añadir instrucciones más específicas que actúen como sublayers:

| Instrucción | Efecto |
|---|---|
| **"Busca el revés"** | Fuerza que >70% de los golpes vayan al revés del rival (`pick_side()` sesgado) |
| **"Sube a la red"** | Bonus de ±5% reach (llega antes) pero +varianza en precisión |
| **"Saque y volea"** | Modifica primera devolución de saque: más agresiva |
| **"Juega largo"** | Reduce la potencia ligeramente pero mejora mucho la p_in (extender rallies) |

> Estas instrucciones se pueden implementar como **flags booleanos opcionales** en el endpoint, para futuras iteraciones.

### 3.2 Arquitectura del Backend (Modo Entrenador)

#### 3.2.1 Nuevo Estado de Sesión en Memoria (sin BD)

Se necesita un **estado de partido en curso** almacenado en el servidor. Se usará un diccionario en memoria (sin persistencia en BD por ahora):

```python
# Estado de un partido de entrenador activo
coach_sessions: Dict[str, CoachSession] = {}

@dataclass
class CoachSession:
    session_id: str
    player1: Player
    player2: Player
    config: Config
    coached_player: str           # "P1" o "P2"
    
    # Estado del marcador
    sets: Dict[str, int]          # {"P1": 0, "P2": 0}
    set_scores: List[Tuple[int, int]]
    current_set: int
    games: Dict[str, int]         # juegos del set actual
    points: Dict[str, int]        # puntos del game actual
    server_flag: int              # alternancia de saque
    tiebreak_active: bool
    tiebreak_points: Dict[str, int]
    tiebreak_server_flag: int
    
    # Estrategia actual del jugador entrenado
    current_strategy: str          # "aggressive" | "neutral" | "defensive"
    
    # Timeline acumulado
    timeline: List[Dict]
    
    # Metadata
    match_finished: bool
    winner: Optional[str]
    created_at: datetime
```

#### 3.2.2 Nuevos Endpoints API

Se crearán bajo un nuevo router `backend/app/coach/routes.py` montado en `/api/coach`:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/coach/start` | Crea una sesión de entrenador, inicializa jugadores y marcador. Devuelve `session_id` + estado inicial. |
| `POST` | `/api/coach/next-point` | Simula el siguiente punto con la estrategia actual. Devuelve el resultado del punto + marcador actualizado. |
| `POST` | `/api/coach/set-strategy` | Cambia la estrategia del jugador entrenado (`aggressive`/`neutral`/`defensive`). |
| `GET` | `/api/coach/state/{session_id}` | Devuelve el estado completo actual de la sesión (marcador, timeline, estrategia, etc.). |
| `POST` | `/api/coach/end` | Finaliza la sesión (simula los puntos restantes o abandona). Opcionalmente guarda como partido normal. |
| `DELETE` | `/api/coach/session/{session_id}` | Elimina la sesión de memoria. |

##### Detalle de Request/Response:

**POST `/api/coach/start`**
```json
// Request
{
  "player1": { /* PlayerData igual que simulate_match */ },
  "player2": { /* PlayerData */ },
  "coached_player": "P1",  // cual de los dos controla el usuario
  "config": { "best_of": 3, "tiebreak": true, "superficie": "Dura" }
}

// Response
{
  "session_id": "uuid-xxx",
  "coached_player": "P1",
  "current_strategy": "neutral",
  "score": {
    "sets": {"P1": 0, "P2": 0},
    "games": {"P1": 0, "P2": 0},
    "points": {"server": "0", "returner": "0"},
    "server_id": "P1",
    "current_set": 1
  },
  "players": {"P1": "Nombre J1", "P2": "Nombre J2"}
}
```

**POST `/api/coach/next-point`**
```json
// Request
{
  "session_id": "uuid-xxx",
  "strategy": "aggressive"  // opcional: cambiar estrategia antes de este punto
}

// Response
{
  "point": { /* PointResult.to_dict() — mismo formato que el timeline actual */ },
  "score": {
    "sets": {"P1": 1, "P2": 0},
    "set_scores": [[6, 3]],
    "games": {"P1": 2, "P2": 1},
    "points": {"server": "30", "returner": "15"},
    "server_id": "P2",
    "current_set": 2,
    "is_tiebreak": false
  },
  "current_strategy": "aggressive",
  "match_finished": false,
  "winner": null,
  "point_index": 42,
  "coached_player_momentum": 12.5,
  "opponent_momentum": -8.3
}
```

#### 3.2.3 Integración con el Motor de Simulación

El punto **clave** es que las fórmulas existentes no se modifican. En su lugar, se crea un wrapper que aplica los modificadores de estrategia.

**Opción elegida: Inyectar modificadores en el `PointSimulator`**

Se añade un parámetro opcional `strategy_modifiers` al `PointSimulator` y a las clases de golpes (`Shot` base). Si están presentes, se aplican como multiplicadores al final de cada cálculo base.

Archivos a modificar:

1. **`backend/simulator/shots.py`** — En `Shot.__init__()`, añadir `strategy: dict | None = None`. En cada método de cálculo (`_sample_pot_prec_first`, `produce_ball`, etc.), si `strategy` está presente, multiplicar `pot_out *= strategy["pot_mult"]`, `prec_out *= strategy["prec_mult"]`, `p_final *= strategy["p_in_mult"]`, `sigma_p *= strategy["sigma_pot_mult"]`, `sigma_r *= strategy["sigma_prec_mult"]`.

2. **`backend/simulator/point.py`** — En `PointSimulator.__init__()`, añadir `server_strategy: dict | None, returner_strategy: dict | None`. Pasar la estrategia correspondiente a cada instancia de `Serve`, `ReturnShot` y `RallyShot`.

3. **NO se toca**: `scoring.py`, `models.py`, `utils.py`, `api.py` (el `run_match()` sigue funcionando exactamente igual, ya que las estrategias serán `None`).

```
   ┌─────────────────────────────────────────────┐
   │         MODO ACTUAL (sin cambios)            │
   │  run_match() → TennisMatch.play()            │
   │  → TennisGame → PointSimulator(strategy=None)│
   │  → Serve/ReturnShot/RallyShot sin modifiers  │
   └─────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────┐
   │         MODO ENTRENADOR (nuevo)              │
   │  CoachSession mantiene estado del partido    │
   │  Cada POST /next-point:                      │
   │  → PointSimulator(strategy=AGGRESSIVE/etc)   │
   │  → Se aplican multiplicadores                │
   │  → Se devuelve resultado + marcador          │
   │  → Se actualiza el estado de la sesión       │
   └─────────────────────────────────────────────┘
```

#### 3.2.4 Gestión del Marcador Punto a Punto

En el modo actual, `TennisGame.play()` ejecuta un game entero en un bucle. Para el modo entrenador necesitamos **avanzar punto a punto**. La lógica de gestión de marcador (puntos → games → sets → match) se extraerá a una clase `MatchScorekeeper`:

```python
class MatchScorekeeper:
    """Gestiona el marcador de un partido punto a punto, sin simular."""
    
    def __init__(self, best_of: int, tiebreak: bool):
        self.best_of = best_of
        self.tiebreak_enabled = tiebreak
        self.sets = {"P1": 0, "P2": 0}
        self.set_scores = []
        self.current_set = 1
        self.games = {"P1": 0, "P2": 0}
        self.points = {"SACADOR": 0, "RESTADOR": 0}
        self.server_flag = 0
        self.is_tiebreak = False
        self.tb_points = {"P1": 0, "P2": 0}
        self.tb_server_flag = 0
        self.match_finished = False
        self.winner = None
    
    def register_point(self, winner: str, server_id: str, returner_id: str) -> dict:
        """
        Registra un punto ganado y actualiza el marcador.
        Devuelve un dict con los eventos que ocurrieron:
        - game_end, set_end, match_end
        - nuevo marcador de puntos, juegos, sets
        """
        ...
    
    def get_server_returner(self) -> tuple[str, str]:
        """Devuelve (server_id, returner_id) para el próximo punto."""
        ...
    
    def is_clutch_point(self) -> bool:
        """Determina si el punto actual es de presión."""
        ...
    
    def get_score_snapshot(self) -> dict:
        """Devuelve el estado completo del marcador."""
        ...
```

Esta clase encapsula TODA la lógica de marcador que hoy está dispersa entre `TennisGame`, `TennisSet`, `TennisMatch` y `TieBreakGame`.

---

### 3.3 Diseño del Frontend (Modo Entrenador)

#### 3.3.1 Nueva Pantalla: Configuración del Modo Entrenador

**Ruta:** `/modo-entrenador` → `templates/modo_entrenador_setup.html`

Funcionalidad:
- Selección de jugadores (igual que `partido_rapido.html`)
- Selección de **qué jugador entrenas** (P1 o P2) — con un selector visual grande
- Configuración del partido (superficie, formato, tiebreak)
- Botón "Comenzar Entrenamiento"

**Flujo al pulsar "Comenzar":**
1. POST a `/api/coach/start` con los datos
2. Guardar `session_id` en `sessionStorage`
3. Redirigir a `/modo-entrenador/partido`

#### 3.3.2 Nueva Pantalla: Partido en Modo Entrenador

**Ruta:** `/modo-entrenador/partido` → `templates/modo_entrenador_partido.html`

Esta pantalla es la más compleja y es el corazón del modo. Tiene los siguientes elementos:

```
┌────────────────────────────────────────────────────────────────────┐
│  HEADER: "🎓 Modo Entrenador — Estás entrenando a [Nombre]"       │
├──────────────────────────────────────────┬─────────────────────────┤
│                                          │                         │
│  ┌──────────────────────────────────┐    │  PANEL DE ESTRATEGIA    │
│  │       MARCADOR (scoreboard)     │    │  ┌───────────────────┐  │
│  │   Igual que simulacion2.html    │    │  │ 🔥 AGRESIVO       │  │
│  │   Pero sin controles de         │    │  │  [btn seleccion]  │  │
│  │   play/pause/velocidad          │    │  ├───────────────────┤  │
│  └──────────────────────────────────┘    │  │ ⚖️ NEUTRO         │  │
│                                          │  │  [btn seleccion]  │  │
│  ┌──────────────────────────────────┐    │  ├───────────────────┤  │
│  │  [  ▶ JUGAR SIGUIENTE PUNTO  ]  │    │  │ 🛡️ DEFENSIVO      │  │
│  │    (botón grande y principal)    │    │  │  [btn seleccion]  │  │
│  └──────────────────────────────────┘    │  └───────────────────┘  │
│                                          │                         │
│  ┌──────────────────────────────────┐    │  INDICADORES:           │
│  │   FEED NARRATIVO DEL PUNTO      │    │  - Momentum actual      │
│  │   (animado como en simulacion2) │    │  - Estamina de tu jugador│
│  └──────────────────────────────────┘    │  - Puntos consecutivos  │
│                                          │  - Racha actual          │
├──────────────────────────────────────────┴─────────────────────────┤
│  HISTORIAL DE PUNTOS RECIENTES (igual que simulacion2)             │
│  + Barra de momentum                                              │
└────────────────────────────────────────────────────────────────────┘
```

**Elementos principales:**

1. **Marcador** — Mismo diseño que `simulacion2.html` pero sin controles de reproducción (no tiene sentido ya que no hay timeline pregrabado).

2. **Botón "Jugar Siguiente Punto"** — El control principal. Al pulsarlo:
   - Envía POST a `/api/coach/next-point` con el `session_id` + la estrategia seleccionada
   - Recibe el resultado del punto
   - Actualiza marcador
   - Muestra el feed narrativo animado del punto
   - Actualiza estadísticas, momentum, etc.

3. **Panel de Estrategia** — 3 tarjetas grandes y visuales para seleccionar la estrategia actual:
   - **Agresivo 🔥**: Fondo rojo/naranja sutil. Descripción: "Golpes más potentes pero con mayor riesgo de error. Ideal para forzar winners y puntos rápidos."
   - **Neutro ⚖️**: Fondo azul/gris. Descripción: "Juego equilibrado. Tu jugador jugará con su estilo natural."
   - **Defensivo 🛡️**: Fondo verde/azul. Descripción: "Prioriza la consistencia y mantener la bola en juego. Menos potencia pero menos errores."
   
   La tarjeta seleccionada se resalta con borde brillante. El cambio de estrategia es inmediato (se aplica al siguiente punto).

4. **Indicadores del Estado del Jugador** (panel lateral o debajo de la estrategia):
   - **Momentum**: Barra visual (-50 a +50) con colores (rojo negativo, verde positivo)
   - **Estamina**: Barra de vida estilo videojuego (100% → 0%)
   - **Racha**: "🔥 3 puntos seguidos" o "❄️ Perdidos 2 seguidos"
   - **Última estrategia usada**: Recordatorio visual

5. **Feed Narrativo** — Usa el mismo `PointFeedGenerator.js` que en `simulacion2.html`. Tras cada punto se muestra la narración animada.

6. **Historial de Puntos** — Lista de puntos recientes con íconos y descripciones, igual que el actual.

7. **Barra de Estadísticas en Tiempo Real** — Aces, dobles faltas, errores no forzados, puntos ganados (misma que `simulacion2.html`).

#### 3.3.3 Fin del Partido

Cuando el backend devuelve `match_finished: true`:
- Se muestra un banner de ganador similar al actual
- Aparece un panel con opciones:
  - "📊 Ver Resumen Completo" → Navega a `resumen.html` (reutiliza la página existente)
  - "💾 Guardar Partido" → POST a `/api/coach/save` que convierte la sesión en un partido normal de BD
  - "🔄 Jugar Otro" → Volver a la configuración
  - "🏠 Volver al Menú"

#### 3.3.4 Nuevos Archivos JS del Modo Entrenador

```
static/js/entrenador/
├── app.js          # Inicialización del modo entrenador
├── api.js          # Llamadas a /api/coach/*
├── state.js        # Estado local (session_id, estrategia, puntos acumulados)
├── strategy.js     # Lógica de selección/display de estrategia
├── controls.js     # Botón "jugar siguiente punto" + interacciones
└── indicators.js   # Momentum, estamina, racha — indicadores visuales
```

Se reutilizarán los módulos existentes:
- `scoreboard.js` → Se reutiliza directamente (misma estructura de marcador)
- `liveFeed.js` → Se reutiliza `initLiveFeed()`, `playPointFeed()`, `updatePointsFeed()`
- `feed/PointFeedGenerator.js` → Sin cambios

---

### 3.4 Integración con el Menú Principal

En `templates/menu.html`, se añade una **5ª tarjeta** (o se reordena) en el grid de modos:

```html
<!-- CARD: Modo Entrenador -->
<div class="mode-card ..." onclick="window.location.href='/modo-entrenador'">
  <div class="card-icon ...">
    <!-- Icono de silbato/pizarra -->
    <svg ...>🎓</svg>
  </div>
  <div>
    <h3>Modo Entrenador</h3>
    <p>Conviértete en entrenador y dirige a tu jugador durante el partido.
       Cambia de estrategia entre puntos y observa cómo afecta al resultado.
       ¿Podrás llevar a tu jugador a la victoria?</p>
    <span class="card-btn">Entrenar</span>
  </div>
</div>
```

El grid pasa de 2x2 a tener espacio para la nueva card (puede ser 2x3 o dar más protagonismo al modo entrenador como card grande en la primera fila).

---

## 4. Plan de Pasos de Implementación

### Fase 1: Backend — Motor de Simulación con Estrategia

| # | Tarea | Archivos | Descripción |
|---|---|---|---|
| 1.1 | Definir constantes de estrategia | `backend/simulator/strategy.py` (nuevo) | Crear diccionario `STRATEGY_MODIFIERS` con los 3 modos y sus multiplicadores |
| 1.2 | Añadir parámetro `strategy` a `Shot` base | `backend/simulator/shots.py` | Añadir `strategy: dict | None = None` a `Shot.__init__()` |
| 1.3 | Aplicar modificadores en `Serve` | `backend/simulator/shots.py` | Multiplicar pot/prec/p_in/sigma por los factores de estrategia en `_sample_pot_prec_first()`, `_sample_pot_prec_second()`, `_prob_in_first()`, `_prob_in_second()` |
| 1.4 | Aplicar modificadores en `ReturnShot` | `backend/simulator/shots.py` | Idem en `attempt_reach()` (reach_mult) y `produce_ball()` (pot/prec/p_in/sigma) |
| 1.5 | Aplicar modificadores en `RallyShot` | `backend/simulator/shots.py` | Idem en `attempt_reach()` y `produce_ball()` |
| 1.6 | Pasar estrategia a través de `PointSimulator` | `backend/simulator/point.py` | Añadir `server_strategy` y `returner_strategy` al constructor, pasarlos a cada `Serve`, `ReturnShot` y `RallyShot` |
| 1.7 | Tests unitarios del motor con estrategia | `backend/test_strategy.py` (nuevo) | Verificar que Agresivo → más potencia/menos precisión, Defensivo → lo contrario, Neutro → sin cambios |

### Fase 2: Backend — Gestión de Sesión del Entrenador

| # | Tarea | Archivos | Descripción |
|---|---|---|---|
| 2.1 | Crear `MatchScorekeeper` | `backend/simulator/scorekeeper.py` (nuevo) | Clase que gestiona el marcador punto a punto (extraer lógica de `TennisGame`/`TennisSet`/`TennisMatch`) |
| 2.2 | Crear modelo `CoachSession` | `backend/app/coach/models.py` (nuevo) | Dataclass con todo el estado de una sesión activa |
| 2.3 | Crear almacén en memoria | `backend/app/coach/store.py` (nuevo) | Diccionario `coach_sessions` con creación, lectura, eliminación y limpieza por timeout |
| 2.4 | Crear schemas Pydantic | `backend/app/coach/schemas.py` (nuevo) | `CoachStartRequest`, `CoachNextPointRequest`, `CoachSetStrategyRequest`, modelos de respuesta |
| 2.5 | Implementar endpoint `POST /start` | `backend/app/coach/routes.py` (nuevo) | Crea sesión, inicializa jugadores + scorekeeper, devuelve session_id |
| 2.6 | Implementar endpoint `POST /next-point` | `backend/app/coach/routes.py` | Simula un punto con `PointSimulator` + estrategia, actualiza `MatchScorekeeper`, devuelve resultado |
| 2.7 | Implementar endpoint `POST /set-strategy` | `backend/app/coach/routes.py` | Actualiza la estrategia en la sesión |
| 2.8 | Implementar endpoint `GET /state/{id}` | `backend/app/coach/routes.py` | Devuelve snapshot completo del estado |
| 2.9 | Implementar endpoint `POST /end` | `backend/app/coach/routes.py` | Simula puntos restantes (o marca fin) y devuelve resultado final |
| 2.10 | Implementar endpoint `POST /save` | `backend/app/coach/routes.py` | Convierte sesión en partido de BD (reutiliza `_try_save_match` de `api.py`) |
| 2.11 | Registrar router en `main.py` | `backend/app/main.py` | `app.include_router(coach_router, prefix="/api")` |
| 2.12 | Tests de endpoints | `backend/test_coach_api.py` (nuevo) | Tests de integración de los endpoints |

### Fase 3: Frontend — Pantalla de Setup del Entrenador

| # | Tarea | Archivos | Descripción |
|---|---|---|---|
| 3.1 | Template de setup | `templates/modo_entrenador_setup.html` (nuevo) | Selección de jugadores + quién entrenas + config del partido |
| 3.2 | Ruta en pages.py | `backend/app/routes/pages.py` | Añadir GET `/modo-entrenador` que renderiza el template |
| 3.3 | JS de setup | `static/js/entrenador/setup.js` (nuevo) | Carga jugadores, selección, POST a /api/coach/start, redirect |
| 3.4 | Añadir card al menú | `templates/menu.html` | Añadir tarjeta del Modo Entrenador al grid de modos |

### Fase 4: Frontend — Pantalla de Partido del Entrenador

| # | Tarea | Archivos | Descripción |
|---|---|---|---|
| 4.1 | Template de partido | `templates/modo_entrenador_partido.html` (nuevo) | Layout completo con marcador, estrategia, feed, indicadores |
| 4.2 | Ruta en pages.py | `backend/app/routes/pages.py` | Añadir GET `/modo-entrenador/partido` |
| 4.3 | `entrenador/app.js` | `static/js/entrenador/app.js` (nuevo) | Inicialización del modo |
| 4.4 | `entrenador/api.js` | `static/js/entrenador/api.js` (nuevo) | Funciones para llamar a `/api/coach/*` |
| 4.5 | `entrenador/state.js` | `static/js/entrenador/state.js` (nuevo) | Estado local: session_id, estrategia, stats acumuladas |
| 4.6 | `entrenador/strategy.js` | `static/js/entrenador/strategy.js` (nuevo) | Renderización y lógica del panel de estrategia |
| 4.7 | `entrenador/controls.js` | `static/js/entrenador/controls.js` (nuevo) | Botón "jugar punto" + fin de partido |
| 4.8 | `entrenador/indicators.js` | `static/js/entrenador/indicators.js` (nuevo) | Barras de momentum, estamina, racha |
| 4.9 | Reutilizar scoreboard.js | Importación directa | El marcador se reutiliza sin cambios |
| 4.10 | Reutilizar liveFeed.js y PointFeedGenerator.js | Importación directa | Feed narrativo reutilizado |
| 4.11 | Integrar resumen final | Reutilizar `resumen.html` | Al terminar, guardar resultado en sessionStorage y redirigir a resumen |

### Fase 5: Pulido y Testing

| # | Tarea | Descripción |
|---|---|---|
| 5.1 | Estilos CSS del modo entrenador | Adaptar `styles.css` o añadir estilos inline en el template |
| 5.2 | Internacionalización (i18n) | Añadir traducciones ES/EN para los textos del modo entrenador en `lang.js` |
| 5.3 | Limpieza de sesiones expiradas | Implementar limpieza automática de sesiones con más de X horas |
| 5.4 | Test end-to-end manual | Probar flujo completo: menú → setup → partido → cambio de estrategia → fin → resumen |
| 5.5 | Responsive / Mobile | Asegurar que el layout del partido funciona en móvil |

---

## 5. Estructura de Archivos Nuevos

```
backend/
  simulator/
    strategy.py          ← NUEVO: Constantes STRATEGY_MODIFIERS
    scorekeeper.py       ← NUEVO: MatchScorekeeper (marcador punto a punto)
  app/
    coach/
      __init__.py        ← NUEVO
      models.py          ← NUEVO: CoachSession dataclass
      store.py           ← NUEVO: Almacén en memoria de sesiones
      schemas.py         ← NUEVO: Schemas Pydantic de request/response
      routes.py          ← NUEVO: Endpoints /api/coach/*
    main.py              ← MODIFICAR: Registrar coach_router
    routes/
      pages.py           ← MODIFICAR: Añadir rutas /modo-entrenador y /modo-entrenador/partido

templates/
  menu.html                        ← MODIFICAR: Añadir tarjeta del Modo Entrenador
  modo_entrenador_setup.html       ← NUEVO
  modo_entrenador_partido.html     ← NUEVO

static/js/
  entrenador/
    app.js               ← NUEVO
    api.js               ← NUEVO
    state.js             ← NUEVO
    strategy.js          ← NUEVO
    controls.js          ← NUEVO
    indicators.js        ← NUEVO
    setup.js             ← NUEVO
```

## 6. Archivos Existentes a Modificar

| Archivo | Cambio |
|---|---|
| `backend/simulator/shots.py` | Añadir parámetro `strategy` a `Shot.__init__()` y aplicar multiplicadores en `Serve`, `ReturnShot`, `RallyShot` |
| `backend/simulator/point.py` | Añadir `server_strategy`/`returner_strategy` a `PointSimulator` y pasarlos a los golpes |
| `backend/app/main.py` | Registrar `coach_router` con `prefix="/api"` |
| `backend/app/routes/pages.py` | Añadir rutas para las dos páginas nuevas |
| `templates/menu.html` | Añadir 5ª tarjeta de modo entrenador al grid |

**Nota importante:** Los archivos `scoring.py`, `models.py`, `utils.py`, `api.py` y todos los JS de `simulacion/` NO se modifican. El modo actual sigue funcionando exactamente igual.

---

## 7. Consideraciones Técnicas

### 7.1 ¿Por qué sesiones en memoria y no en BD?

- **Simplicidad**: Evita diseñar un esquema de BD para partidos a medias.
- **Rendimiento**: Cada `next-point` es una operación rápida sin acceso a disco.
- **Temporal**: El partido solo existe mientras dura la sesión. Si el usuario cierra el navegador, se pierde (acceptable para un MVP).
- **Futuro**: Se puede migrar a Redis o BD si se quiere persistir sesiones.
- **Limpieza**: Un background task limpia sesiones con más de 2 horas de inactividad.

### 7.2 ¿Cómo se garantiza que las fórmulas son las mismas?

Los multiplicadores se aplican **después** de los cálculos base. Cuando `strategy=None` (modo normal), los multiplicadores no se aplican. Cuando `strategy="neutral"`, todos los multiplicadores son `1.0`, produciendo exactamente los mismos resultados que sin estrategia.

### 7.3 ¿Se perciben los cambios de estrategia?

Sí. Los multiplicadores están diseñados para ser **claramente perceptibles**:

- **Agresivo**: Se verán más winners (bolas potentes que no alcanzan) pero también más errores no forzados (bolas fuera por exceso de potencia). Los rallies serán más cortos.
- **Defensivo**: Los rallies serán más largos. Menos errores no forzados pero también menos winners directos. El rival se cansará más (más golpes por punto → más fatiga).
- **Neutro**: Comportamiento base del jugador.

### 7.4 Gestión de Estamina y Momentum

La lógica de actualización de estamina y momentum (actualmente en `TennisGame.play()` y `TennisSet.play()`) se replica en el `MatchScorekeeper` o en la lógica del endpoint `next-point`. Es crucial mantener exactamente las mismas fórmulas:

```python
# Fatiga tras cada punto
fatiga = 0.08 * (rally_shots / 10) * (1 - jugador.Fisico / 100)
jugador.Estamina = max(0.0, jugador.Estamina - fatiga)

# Momentum
ganador.streak = max(1, ganador.streak + 1)
perdedor.streak = min(-1, perdedor.streak - 1)
ganador.Momentum = min(50.0, ganador.Momentum + 2 * abs(ganador.streak))
perdedor.Momentum = max(-50.0, perdedor.Momentum - 2 * abs(perdedor.streak))
ganador.Momentum *= 0.97
perdedor.Momentum *= 0.97

# Recuperación tras game
rec = 2 + 8 * (jugador.Fisico / 100)
jugador.Estamina = min(100.0, jugador.Estamina + rec)

# Bonus momentum por game ganado
ganador_game.Momentum += 8.0
perdedor_game.Momentum -= 8.0

# Recuperación tras set
rec_set = 10 + 20 * (jugador.Fisico / 100)
jugador.Estamina = min(100.0, jugador.Estamina + rec_set)

# Bonus momentum por set
ganador_set.Momentum += 15.0
perdedor_set.Momentum -= 15.0
```

### 7.5 Concurrencia

Al usar un diccionario en memoria, se debe considerar la posibilidad de múltiples usuarios simultáneos. Para el MVP con un solo servidor uvicorn, no hay problema de concurrencia real (es single-threaded async). Si se escala, se puede usar `asyncio.Lock` por sesión.

---

## 8. Orden Recomendado de Desarrollo

```
1. strategy.py (constantes de modificadores)
2. shots.py (parámetro strategy + aplicar multiplicadores)
3. point.py (pasar estrategia al PointSimulator)
4. Tests del motor con estrategia
5. scorekeeper.py (gestión de marcador punto a punto)
6. coach/models.py + store.py + schemas.py
7. coach/routes.py (endpoints)
8. main.py + pages.py (registro de rutas)
9. modo_entrenador_setup.html + setup.js
10. modo_entrenador_partido.html + JS modules
11. menu.html (añadir tarjeta)
12. Pulido, testing, i18n
```

---

## 9. Resumen de Impacto

| Aspecto | Impacto |
|---|---|
| Motor de simulación | Mínimo: solo se añade un parámetro opcional con multiplicadores |
| Modo actual | **Cero impacto**: sigue funcionando exactamente igual |
| Nuevos endpoints | 6 endpoints nuevos bajo `/api/coach/` |
| Nuevas pantallas | 2 templates HTML nuevos |
| Nuevos módulos JS | ~7 archivos nuevos en `static/js/entrenador/` |
| Base de datos | Sin cambios (de momento) |
| Archivos modificados | 5 archivos existentes con cambios pequeños y retrocompatibles |
| Archivos nuevos | ~15 archivos nuevos |
